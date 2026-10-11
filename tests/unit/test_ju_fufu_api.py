from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from core.application.characters.ju_fufu import (
    JuFufuCompileConfig,
    compile_ju_fufu,
    load_raw_record,
)
from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.ju_fufu.reviewed import JU_FUFU_REVIEWED_MAPPING
from core.application import CalculationScenario
from core.application.execution import apply_global_panel_effects
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, compile_wengine
from core.data.loader import load_character_record
from core.presentation.registry import registration_for
from core.types import (
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    DamageTag,
    Element,
    InitialCharacterSnapshot,
    Resolved,
    SkillGroup,
    WEngineBuildInput,
    WEngineId,
)
from web.api import app


JU_FUFU = "character:1391"
PULCHRA = "character:1351"
CLIENT = TestClient(app)
FIRE_SPIN_ENTRY = f"move-entry:{JU_FUFU}:dash-tiger-cauldron-fire"
PHYSICAL_SPIN_ENTRY = f"move-entry:{JU_FUFU}:dash-tiger-cauldron-physical"
TIGER_MIGHT_THROW_ENTRY = f"move-entry:{JU_FUFU}:dash-tiger-cauldron-tiger-might"
CINEMA6_POPCORN_RULE = f"rule:{JU_FUFU}:cinema6:fire-spin-popcorn"


def _stats(attack: float = 1000.0) -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0, "fire": 0.0},
    }


def _wengine_build(wengine_id: str, refinement: int) -> dict[str, object]:
    return {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": wengine_id,
        "wengine_level": 60,
        "wengine_refinement": refinement,
        "base_stats": _stats(),
        "drive_discs": [],
    }


def _character_stats(attack: float) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.5),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={
            Element.PHYSICAL: Resolved(0.0),
            Element.FIRE: Resolved(0.0),
        },
    )


def _payload(
    move_entry_id: str,
    *,
    primary: str = JU_FUFU,
    team: tuple[str, ...] = (JU_FUFU,),
    cinema: int = 0,
    tiger_roar_active: bool = False,
    c1_target_debuff_active: bool = False,
    enemy_stunned: bool = False,
    attacks: dict[str, float] | None = None,
    enabled_rules: tuple[str, ...] = (),
    stack_counts: dict[str, int] | None = None,
) -> dict[str, object]:
    support = [item for item in team if item != primary]
    configs = {
        item: {"core_level": 7, "cinema_level": cinema if item == JU_FUFU else 0}
        for item in team
    }
    configs[JU_FUFU].update(
        {
            "tiger_roar_active": tiger_roar_active,
            "c1_target_debuff_active": c1_target_debuff_active,
        }
    )
    return {
        "primary_character_id": primary,
        "supporting_character_ids": support,
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": {},
        "parameter_values": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _stats((attacks or {}).get(item, 1000.0))}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:ju-fufu-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.0,
                "fire": 0.0,
                "ice": 0.0,
                "electric": 0.0,
                "ether": 0.0,
                "wind": 0.0,
                "luminance": 0.0,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": enemy_stunned,
        },
        "enabled_rule_item_ids": list(enabled_rules),
        "selected_trigger_inputs": [],
        "rule_stack_counts": stack_counts or {},
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = CLIENT.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _applied(event: dict[str, object]) -> dict[str, float]:
    return {
        str(item["effect_id"]): float(item["value"])
        for item in event["common_application_trace"]["applied_modifiers"]
    }


def _entry(definition, entry_key: str):
    entry_id = f"move-entry:{JU_FUFU}:{entry_key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def test_ju_fufu_reviewed_curves_and_cinema_skill_caps_match_source() -> None:
    raw_data = load_character_record(JU_FUFU)
    assert raw_data["source_version"] == "3.2"
    assert raw_data["source_url"] == "https://static.nanoka.cc/zzz/3.2/zh/character/1391.json"
    assert len(JU_FUFU_REVIEWED_MAPPING.moves) == 17

    level_12 = compile_ju_fufu(
        JuFufuCompileConfig(), load_raw_record(raw_data)
    )
    level_16 = compile_ju_fufu(
        JuFufuCompileConfig(cinema_level=5), load_raw_record(raw_data)
    )
    goldens = {
        "ex-descending-tiger": (10.534, 12.45),
        "chain-tiger-cauldron-collapse": (13.369, 15.801),
        "chain-tiger-cauldron-shake": (7.098, 8.39),
        "ultimate-tiger-bloom": (33.281, 39.333),
        "assist-strike-flame-jaw": (8.153, 9.637),
    }
    for key, (at_12, at_16) in goldens.items():
        assert _entry(level_12, key).multiplier_variants[0].multiplier.value.value == pytest.approx(at_12)
        assert _entry(level_16, key).multiplier_variants[0].multiplier.value.value == pytest.approx(at_16)

    raised = JuFufuCompileConfig(
        cinema_level=3,
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 15),),
    )
    assert effective_skill_level(raised, SkillGroup.ULTIMATE) == 16
    assert effective_skill_level(raised, SkillGroup.BASIC_ATTACK) == 14
    assert _entry(level_12, "dash-tiger-cauldron-physical").multiplier_variants[0].multiplier.value.value == pytest.approx(0.371)
    assert _entry(level_12, "dash-tiger-cauldron-fire").multiplier_variants[0].multiplier.value.value == pytest.approx(0.390)
    assert _entry(level_12, "dash-tiger-cauldron-tiger-might").multiplier_variants[0].multiplier.value.value == pytest.approx(1.848)


def test_missing_optional_curve_blocks_only_its_selected_entry(monkeypatch) -> None:
    import core.presentation.registry as registry_module

    source = load_character_record(JU_FUFU)
    source_for_throw = next(
        item
        for item in source["skill"]["dodge"]["description"]
        if item["name"] == "冲刺攻击：恶虎七式·山君鼎戏·「虎威」"
    )
    damage_curve = next(item for item in source_for_throw["param"] if item["name"] == "伤害倍率")
    del damage_curve["param"]["1391022"]
    original_loader = registry_module.load_character_record

    def load_with_missing_throw_curve(character_id: str):
        if character_id == JU_FUFU:
            return deepcopy(source)
        return original_loader(character_id)

    monkeypatch.setattr(registry_module, "load_character_record", load_with_missing_throw_curve)

    basic = _calculate(_payload(f"move-entry:{JU_FUFU}:basic-stage-1"))
    assert basic["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert basic["totals"]["expected"]["complete"] is True

    missing = _calculate(_payload(TIGER_MIGHT_THROW_ENTRY))
    assert missing["events"] == []
    assert missing["totals"]["expected"]["complete"] is False
    assert any(item["blocking"] for item in missing["diagnostics"]), missing["diagnostics"]
    assert any(
        item["diagnostic_id"]
        == f"{TIGER_MIGHT_THROW_ENTRY}:unresolved-multiplier"
        and item["kind"] == "missing-data"
        for item in missing["diagnostics"]
    )


def test_tiger_roar_cinema_rules_reach_team_recipients_but_c4_stays_owner_only() -> None:
    rules = (
        f"rule:{JU_FUFU}:core:tiger-roar",
        f"rule:{JU_FUFU}:cinema2:tiger-roar-team-crit-damage",
        f"rule:{JU_FUFU}:cinema4:tiger-roar-self-crit-damage",
    )
    result = _calculate(
        _payload(
            "move-entry:pulchra:1351:basic-jab-1",
            primary=PULCHRA,
            team=(PULCHRA, JU_FUFU),
            cinema=4,
            tiger_roar_active=True,
            attacks={PULCHRA: 6000.0, JU_FUFU: 2850.0},
            enabled_rules=rules,
        )
    )
    expected_crit_damage = next(
        item["value"]
        for item in result["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-damage"
    )
    assert expected_crit_damage == pytest.approx(0.945)
    rule_matches = {
        item["rule_id"]: item["status"]
        for item in result["events"][0]["common_application_trace"]["rule_matches"]
    }
    assert rule_matches[f"rule:{JU_FUFU}:core:tiger-roar"] == "matched"
    assert rule_matches[f"rule:{JU_FUFU}:cinema2:tiger-roar-team-crit-damage"] == "matched"
    assert rule_matches[f"rule:{JU_FUFU}:cinema4:tiger-roar-self-crit-damage"] == "not-matched"


@pytest.mark.parametrize(
    ("initial_attack", "expected_crit_damage"),
    (
        (2799.0, 0.70),
        (2800.0, 0.70),
        (2850.0, 0.725),
        (3400.0, 1.0),
        (5000.0, 1.0),
    ),
)
def test_tiger_roar_initial_attack_thresholds_via_api(
    initial_attack: float,
    expected_crit_damage: float,
) -> None:
    result = _calculate(
        _payload(
            f"move-entry:{JU_FUFU}:basic-stage-1",
            tiger_roar_active=True,
            attacks={JU_FUFU: initial_attack},
            enabled_rules=(f"rule:{JU_FUFU}:core:tiger-roar",),
        )
    )
    current_crit_damage = next(
        item["value"]
        for item in result["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-damage"
    )
    assert current_crit_damage == pytest.approx(expected_crit_damage)


def test_tiger_roar_derived_crit_damage_uses_immutable_initial_attack() -> None:
    compiled = compile_ju_fufu(
        JuFufuCompileConfig(tiger_roar_active=True),
        load_raw_record(load_character_record(JU_FUFU)),
    )
    core_rule = next(
        rule
        for rule in compiled.rule_items
        if str(rule.rule_id).endswith(":core:tiger-roar")
    )
    scenario = CalculationScenario(
        scenario_id="scenario:ju-fufu:initial-attack-source",
        current_operator=CharacterId(JU_FUFU),
        conditions=compiled.scenario_conditions,
        enabled_rule_item_ids=frozenset({core_rule.rule_id}),
    )
    applied = apply_global_panel_effects(
        (
            CharacterSnapshot(
                CharacterId(JU_FUFU),
                60,
                _character_stats(50000.0),
            ),
        ),
        (
            InitialCharacterSnapshot(
                CharacterId(JU_FUFU),
                60,
                _character_stats(2850.0),
            ),
        ),
        (core_rule,),
        scenario,
        team_character_ids=frozenset({CharacterId(JU_FUFU)}),
    )

    assert not applied.diagnostics
    assert applied.character_snapshots[0].settlement_stats.attack == Resolved(50000.0)
    assert applied.character_snapshots[0].settlement_stats.crit_damage == Resolved(0.725)


@pytest.mark.parametrize(
    ("stacks", "expected_bonus"),
    ((0, 0.0), (1, 0.10), (2, 0.20)),
)
def test_fox_furnace_from_ju_fufu_support_applies_explicit_team_stacks(
    stacks: int,
    expected_bonus: float,
) -> None:
    team_rule = "rule:wengine:14139:owner:1391:team-damage-per-fire-chain-ultimate-stack"
    payload = _payload(
        "move-entry:pulchra:1351:basic-jab-1",
        primary=PULCHRA,
        team=(PULCHRA, JU_FUFU),
        attacks={PULCHRA: 6000.0, JU_FUFU: 2850.0},
        enabled_rules=(team_rule,),
        stack_counts={team_rule: stacks},
    )
    payload["character_builds"][JU_FUFU] = _wengine_build("wengine:14139", 1)

    result = _calculate(payload)
    normal_bonus = next(
        item["value"]
        for item in result["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    )
    assert normal_bonus == pytest.approx(expected_bonus)
    assert result["totals"]["expected"]["complete"] is True


def test_cinema1_stun_vulnerability_requires_both_mark_and_actual_stun() -> None:
    c1_rule = f"rule:{JU_FUFU}:cinema1:chain-target-stun-vulnerability"
    effect_id = f"effect:{JU_FUFU}:cinema1:chain-target-stun-vulnerability"
    move = f"move-entry:{JU_FUFU}:chain-tiger-cauldron-collapse"

    for marked, stunned, expected in ((True, False, False), (False, True, False), (True, True, True)):
        result = _calculate(
            _payload(
                move,
                cinema=1,
                c1_target_debuff_active=marked,
                enemy_stunned=stunned,
                enabled_rules=(c1_rule,),
            )
        )
        applied = _applied(result["events"][0])
        assert (effect_id in applied) is expected
        if expected:
            assert applied[effect_id] == pytest.approx(0.35)


def test_cinema6_popcorn_is_local_to_enabled_fire_weshi_spin() -> None:
    partial = _calculate(
        _payload(
            FIRE_SPIN_ENTRY,
            cinema=6,
            enabled_rules=(CINEMA6_POPCORN_RULE,),
        )
    )
    assert partial["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert partial["events"][0]["modes"]["expected"]["known_value"] is not None
    assert partial["totals"]["expected"]["complete"] is False
    child_diagnostics = [
        item
        for item in partial["diagnostics"]
        if item["diagnostic_id"].startswith(f"application:effect:{JU_FUFU}:cinema6:popcorn-")
    ]
    assert len(child_diagnostics) == 3
    assert all("1.6" in item["message"] and "element" in item["message"].lower() for item in child_diagnostics)

    for entry_id, cinema, enabled in (
        (FIRE_SPIN_ENTRY, 6, ()),
        (FIRE_SPIN_ENTRY, 5, (CINEMA6_POPCORN_RULE,)),
        (PHYSICAL_SPIN_ENTRY, 6, (CINEMA6_POPCORN_RULE,)),
        (TIGER_MIGHT_THROW_ENTRY, 6, (CINEMA6_POPCORN_RULE,)),
        (f"move-entry:{JU_FUFU}:basic-stage-1", 6, (CINEMA6_POPCORN_RULE,)),
    ):
        result = _calculate(_payload(entry_id, cinema=cinema, enabled_rules=enabled))
        assert result["events"][0]["modes"]["expected"]["status"] == "calculated"
        assert result["totals"]["expected"]["complete"] is True
        assert not any(
            item["diagnostic_id"].startswith(f"application:effect:{JU_FUFU}:cinema6:popcorn-")
            for item in result["diagnostics"]
        )


def test_fox_furnace_signature_is_available_and_fire_trigger_scope_is_capability_gated() -> None:
    ju_fufu_id = CharacterId(JU_FUFU)
    assert str(SIGNATURE_WENGINE_BY_CHARACTER[ju_fufu_id]) == "wengine:14139"
    ju_fufu_capabilities = registration_for(ju_fufu_id).equipment_capabilities
    assert ju_fufu_capabilities.can_produce_damage_scope(
        element=Element.FIRE,
        skill_groups=(SkillGroup.CHAIN_ATTACK,),
        tags=(DamageTag.CHAIN_ATTACK,),
    )
    fire_engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14139"), ju_fufu_id, refinement=5),
        owner_capabilities=ju_fufu_capabilities,
    )
    assert fire_engine.rule_items[1].eligibility.value == "eligible"
    assert fire_engine.rule_items[1].stack_max == 2

    trigger_capabilities = registration_for("character:1361").equipment_capabilities
    electric_engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14139"), CharacterId("character:1361"), refinement=5),
        owner_capabilities=trigger_capabilities,
    )
    assert electric_engine.rule_items[1].eligibility.value == "ineligible"
