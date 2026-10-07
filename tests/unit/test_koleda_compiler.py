from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.koleda import (
    KoledaCompileConfig,
    KOLEDA_ID,
    compile_koleda,
    load_raw_record,
)
from core.application.characters.koleda.reviewed import (
    BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,
    BEN_ENHANCED_FOLLOWUP_ACTIVE,
    BEN_ID,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import (
    _koleda_additional_ability_eligibility,
    registration_for,
)
from core.types import CharacterId, DamageTag, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)

_POTENTIAL1_BUFF_CONDITION = "condition:koleda:potential1-team-damage-active"
_POTENTIAL1_STACKS = "parameter:koleda:potential1-enhanced-basic-consumed-furnace-layers"
_EXTRA_MARK = "condition:koleda:extra-ability-target-mark-active"
_C4_STACKS = "parameter:koleda:cinema4-current-furnace-layers"
_C4_RULE = "rule:character:1101:cinema4:chain-ultimate-current-furnace-damage"
_POTENTIAL1_TEAM_RULE = "rule:character:1101:potential1:team-damage-state"
_POTENTIAL1_STACK_RULE = "rule:character:1101:potential1:enhanced-basic-stage2-per-consumed-layer"
_EXTRA_ABILITY_RULE = "rule:character:1101:extra-ability:chain-vulnerability"
_C6_RULE = "rule:character:1101:cinema6:explosion-extra-damage"


def _stats_for(character_id: CharacterId) -> dict:
    panel = character_base_stats(character_id)
    return {
        "hp": panel.hp.value,
        "attack": panel.attack.value,
        "defense": panel.defense.value,
        "impact": panel.impact.value,
        "crit_rate": panel.crit_rate.value,
        "crit_damage": panel.crit_damage.value,
        "anomaly_mastery": panel.anomaly_mastery.value,
        "anomaly_proficiency": panel.anomaly_proficiency.value,
        "energy_regen": panel.energy_regen.value,
        "penetration_rate": panel.penetration_rate.value,
        "penetration_flat": panel.penetration_flat.value,
        "element_damage_bonus": {
            str(element.value): value.value
            for element, value in panel.element_damage_bonus.items()
        },
    }


def _koleda_payload(
    move_entry_id: str,
    *,
    cinema_level: int = 0,
    potential_level: int = 0,
    primary_character_id: str = "character:1101",
    team_character_ids: tuple[str, ...] = ("character:1101",),
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: list[str] | None = None,
    rule_stack_counts: dict[str, int] | None = None,
    is_stunned: bool = False,
    stun_vulnerability_bonus: float = 0.0,
) -> dict:
    return {
        "primary_character_id": primary_character_id,
        "supporting_character_ids": [
            item for item in team_character_ids if item != primary_character_id
        ],
        "team_character_ids": list(team_character_ids),
        "formation_character_ids": list(team_character_ids),
        "move_entry_id": move_entry_id,
        "compile_configs": {
            character_id: (
                {
                    "core_level": 7,
                    "cinema_level": cinema_level,
                    "potential_level": potential_level,
                }
                if character_id == "character:1101"
                else {"core_level": 7, "cinema_level": 0}
            )
            for character_id in team_character_ids
        },
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "enabled_rule_item_ids": enabled_rule_item_ids or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
        "character_builds": {
            character_id: {
                "level": 60,
                "out_of_combat_stats": _stats_for(CharacterId(character_id)),
            }
            for character_id in team_character_ids
        },
        "enemy": {
            "enemy_id": "enemy:koleda-test",
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
            "stun_vulnerability_bonus": stun_vulnerability_bonus,
            "is_stunned": is_stunned,
        },
    }


def _event(response: dict, *, label_contains: str | None = None) -> dict:
    events = response["events"]
    if label_contains is None:
        return events[0]
    return next(item for item in events if label_contains in item["label"])


def _breakdown(event: dict, mode: str, node: str) -> float:
    return next(
        item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
        if item["node"] == node
    )


def test_koleda_live_identity_panel_signature_and_potential_source_are_registered() -> None:
    source = load_character_record(str(KOLEDA_ID))
    raw = load_raw_record(source, potential_level=0)
    assert raw.name == "珂蕾妲"
    assert raw.code_name == "Koleda"
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1101.json",
    )
    assert raw.rarity == 4
    assert raw.specialty == "击破"
    assert raw.element == "火属性"
    assert raw.faction == "白祇重工"
    assert tuple(item.level for item in raw.potential_details) == (1, 2, 3, 4, 5, 6)

    panel = character_base_stats(KOLEDA_ID)
    assert panel.hp.value == pytest.approx(8127.3088)
    assert panel.attack.value == pytest.approx(735.8413)
    assert panel.defense.value == pytest.approx(594.5855)
    assert panel.impact.value == pytest.approx(134.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(96.0)
    assert panel.anomaly_mastery.value == pytest.approx(97.0)
    assert KoledaCompileConfig().core_level == 7
    assert KoledaCompileConfig().cinema_level == 0
    assert KoledaCompileConfig().potential_level == 0
    assert KoledaCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    assert SIGNATURE_WENGINE_BY_CHARACTER[KOLEDA_ID] == WEngineId("wengine:14110")
    assert load_wengine_raw_record("wengine:14110").icon == "Weapon_S_1101"
    wengine = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert wengine["wengine:14110"].signature_character_id == str(KOLEDA_ID)
    catalog = {item.character_id: item for item in supported_character_catalog()}
    assert catalog[str(KOLEDA_ID)].code_name == "Koleda"
    assert catalog[str(KOLEDA_ID)].image_path == "/characters/portrait-placeholder.svg"
    assert registration_for(KOLEDA_ID).role.value == "stun"
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "characters"
    assert (asset_root / "portrait-placeholder.svg").is_file()


def test_koleda_reviewed_curves_keep_element_scope_and_potential_projection() -> None:
    source = load_character_record(str(KOLEDA_ID))
    base_raw = load_raw_record(source, potential_level=0)
    base = compile_koleda(KoledaCompileConfig(), base_raw)
    entries = {str(item.entry_id): item for item in base.move_entries}
    assert entries["move-entry:character:1101:basic-physical-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.274)
    assert entries["move-entry:character:1101:enhanced-basic-stage1"].main_damage_event.element == "fire"
    assert entries["move-entry:character:1101:enhanced-basic-stage2"].multiplier_variants[0].multiplier.value.value == pytest.approx(8.108)
    assert entries["move-entry:character:1101:ex-special-impact"].damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})
    assert entries["move-entry:character:1101:ex-special-explosion"].multiplier_variants[0].multiplier.value.value == pytest.approx(12.121)
    assert entries["move-entry:character:1101:special-complete"].multiplier_variants[0].multiplier.value.value == pytest.approx(2.606)
    assert entries["move-entry:character:1101:ex-special-complete"].multiplier_variants[0].multiplier.value.value == pytest.approx(15.173)
    assert entries["move-entry:character:1101:ultimate"].multiplier_variants[0].multiplier.value.value == pytest.approx(30.976)

    selected_12_at_cinema3 = KoledaCompileConfig(
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
        core_level=7,
        cinema_level=3,
    )
    level14 = compile_koleda(selected_12_at_cinema3, base_raw)
    ult14 = next(
        item
        for item in level14.move_entries
        if str(item.entry_id) == "move-entry:character:1101:ultimate"
    )
    assert ult14.multiplier_variants[0].multiplier.value.value == pytest.approx(33.792)

    potential1_raw = load_raw_record(source, potential_level=1)
    assert potential1_raw.core_levels[0].source_id == "1101508"
    potential1 = compile_koleda(KoledaCompileConfig(potential_level=1), potential1_raw)
    potential1_rules = {str(item.rule_id) for item in potential1.rule_items}
    assert "rule:character:1101:potential1:team-damage-state" in potential1_rules
    assert "rule:character:1101:potential1:enhanced-basic-stage2-per-consumed-layer" in potential1_rules

    potential2 = compile_koleda(
        KoledaCompileConfig(potential_level=2),
        load_raw_record(source, potential_level=2),
    )
    p2_rule = next(
        item
        for item in potential2.rule_items
        if str(item.rule_id) == "rule:character:1101:potential2:non-vanguard-team-crit-damage"
    )
    assert p2_rule.effects[0].result.value.value == pytest.approx(0.11)
    assert any("锋御" in item.original_text for item in p2_rule.diagnostics)


def test_koleda_ben_cooperation_uses_team_membership_and_potential1_no_switch_state() -> None:
    assert _koleda_additional_ability_eligibility((KOLEDA_ID, BEN_ID), 0) is True
    assert _koleda_additional_ability_eligibility(
        (KOLEDA_ID, CharacterId("character:1041")), 0
    ) is True
    assert _koleda_additional_ability_eligibility(
        (KOLEDA_ID, CharacterId("character:1051")), 0
    ) is True
    source = load_character_record(str(KOLEDA_ID))
    base_raw = load_raw_record(source, potential_level=0)
    no_ben = compile_koleda(KoledaCompileConfig(), base_raw)
    with_ben = compile_koleda(
        KoledaCompileConfig(ben_in_team=True, additional_ability_eligible=True),
        base_raw,
    )
    base_entries = {str(item.entry_id): item for item in no_ben.move_entries}
    ben_entries = {str(item.entry_id): item for item in with_ben.move_entries}
    assert base_entries["move-entry:character:1101:enhanced-basic-stage2"].multiplier_variants[0].multiplier.value.value == pytest.approx(8.108)
    assert ben_entries["move-entry:character:1101:enhanced-basic-stage2"].multiplier_variants[0].multiplier.value.value == pytest.approx(10.029)
    assert ben_entries["move-entry:character:1101:ultimate"].multiplier_variants[0].multiplier.value.value == pytest.approx(33.88)
    assert "move-entry:character:1101:special-ben-coordinated-explosion" in ben_entries
    assert "move-entry:character:1101:ex-special-ben-coordinated-explosion" in ben_entries
    assert ben_entries["move-entry:character:1101:special-ben-coordinated-explosion"].condition_ids == (BEN_ENHANCED_FOLLOWUP_ACTIVE,)

    p1_raw = load_raw_record(source, potential_level=1)
    p1_ben = compile_koleda(
        KoledaCompileConfig(potential_level=1, ben_in_team=True, additional_ability_eligible=True),
        p1_raw,
    )
    p1_entries = {str(item.entry_id): item for item in p1_ben.move_entries}
    assert p1_entries["move-entry:character:1101:enhanced-basic-stage2"].multiplier_variants[0].multiplier.value.value == pytest.approx(8.108)
    coop_stage2 = p1_entries["move-entry:character:1101:enhanced-basic-stage2-ben-coordinated"]
    assert coop_stage2.multiplier_variants[0].multiplier.value.value == pytest.approx(10.029)
    assert coop_stage2.condition_ids == (BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,)
    assert p1_entries["move-entry:character:1101:ultimate"].multiplier_variants[0].multiplier.value.value == pytest.approx(33.88)


def test_koleda_cinema4_uses_only_current_chain_and_ultimate_furnace_stacks() -> None:
    chain_entry = "move-entry:character:1101:chain-attack"
    baseline = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(chain_entry, cinema_level=4, enabled_rule_item_ids=[_C4_RULE]),
    )
    one_charge = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            chain_entry,
            cinema_level=4,
            parameter_values={_C4_STACKS: 1},
            enabled_rule_item_ids=[_C4_RULE],
        ),
    )
    two_charges = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            chain_entry,
            cinema_level=4,
            parameter_values={_C4_STACKS: 2},
            enabled_rule_item_ids=[_C4_RULE],
        ),
    )
    assert baseline.status_code == one_charge.status_code == two_charges.status_code == 200
    assert _breakdown(_event(baseline.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.0)
    assert _breakdown(_event(one_charge.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.18)
    assert _breakdown(_event(two_charges.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.36)

    basic = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:basic-physical-1",
            cinema_level=4,
            parameter_values={_C4_STACKS: 2},
            enabled_rule_item_ids=[_C4_RULE],
        ),
    )
    assert basic.status_code == 200
    assert _breakdown(_event(basic.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.0)


def test_koleda_potential1_team_buff_and_consumed_layer_damage_are_current_inputs() -> None:
    stage2 = "move-entry:character:1101:enhanced-basic-stage2"
    active = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            stage2,
            potential_level=1,
            condition_values={_POTENTIAL1_BUFF_CONDITION: True},
            parameter_values={_POTENTIAL1_STACKS: 2},
            enabled_rule_item_ids=[_POTENTIAL1_TEAM_RULE, _POTENTIAL1_STACK_RULE],
        ),
    )
    assert active.status_code == 200, active.text
    assert _breakdown(_event(active.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.55)

    stage1 = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:enhanced-basic-stage1",
            potential_level=1,
            condition_values={_POTENTIAL1_BUFF_CONDITION: True},
            parameter_values={_POTENTIAL1_STACKS: 2},
            enabled_rule_item_ids=[_POTENTIAL1_TEAM_RULE, _POTENTIAL1_STACK_RULE],
        ),
    )
    assert stage1.status_code == 200
    assert _breakdown(_event(stage1.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.35)

    burn = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:fire-anomaly",
            potential_level=1,
            condition_values={_POTENTIAL1_BUFF_CONDITION: True},
            enabled_rule_item_ids=[_POTENTIAL1_TEAM_RULE],
        ),
    )
    assert burn.status_code == 200
    burn_trace = _event(burn.json())["modes"]["non-crit"]["anomaly_effect_strength_trace"]
    assert burn_trace["normal_bonus"] == pytest.approx(0.35)
    bare_burn = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload("move-entry:character:1101:fire-anomaly"),
    )
    assert bare_burn.status_code == 200
    bare_trace = _event(bare_burn.json())["modes"]["non-crit"]["anomaly_effect_strength_trace"]
    assert burn_trace["final_strength"] == pytest.approx(bare_trace["final_strength"] * 1.35)


def test_koleda_potential_crit_damage_uses_each_source_level() -> None:
    entry = "move-entry:character:1101:chain-attack"
    for potential_level, bonus in ((2, 0.11), (3, 0.17), (4, 0.23), (5, 0.29), (6, 0.35)):
        rule = f"rule:character:1101:potential{potential_level}:non-vanguard-team-crit-damage"
        response = client.post(
            "/api/v1/moves/calculate",
            json=_koleda_payload(
                entry,
                potential_level=potential_level,
                enabled_rule_item_ids=[rule],
            ),
        )
        assert response.status_code == 200, response.text
        assert _breakdown(_event(response.json()), "expected", "character.current.crit-damage") == pytest.approx(0.5 + bonus)


def test_koleda_extra_ability_marks_target_for_any_real_chain_dealer() -> None:
    soldier11 = "character:1041"
    team = (soldier11, "character:1101")
    chain = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1041:chain-rising-flames",
            primary_character_id=soldier11,
            team_character_ids=team,
            condition_values={_EXTRA_MARK: True},
            enabled_rule_item_ids=[_EXTRA_ABILITY_RULE],
            is_stunned=True,
            stun_vulnerability_bonus=1.5,
        ),
    )
    assert chain.status_code == 200, chain.text
    chain_event = _event(chain.json())
    assert _breakdown(chain_event, "non-crit", "vulnerability.enemy-normal") == pytest.approx(0.70)
    assert _breakdown(chain_event, "non-crit", "vulnerability.additive-region") == pytest.approx(3.2)

    not_chain = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1041:basic-fire-suppression-1",
            primary_character_id=soldier11,
            team_character_ids=team,
            condition_values={_EXTRA_MARK: True},
            enabled_rule_item_ids=[_EXTRA_ABILITY_RULE],
            is_stunned=True,
            stun_vulnerability_bonus=1.5,
        ),
    )
    assert not_chain.status_code == 200
    assert _breakdown(_event(not_chain.json()), "non-crit", "vulnerability.enemy-normal") == pytest.approx(0.0)


def test_koleda_cinema6_child_is_once_per_legal_explosion_and_inherits_parent_lane() -> None:
    chain = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:chain-attack",
            cinema_level=6,
            potential_level=1,
            team_character_ids=("character:1101", "character:1041"),
            condition_values={_EXTRA_MARK: True},
            parameter_values={_C4_STACKS: 2},
            enabled_rule_item_ids=[_C6_RULE, _C4_RULE, _EXTRA_ABILITY_RULE],
            is_stunned=True,
            stun_vulnerability_bonus=1.5,
        ),
    )
    assert chain.status_code == 200, chain.text
    assert len(chain.json()["events"]) == 2
    children = [event for event in chain.json()["events"] if "cinema6:chain-explosion-extra" in event["semantic_id"]]
    assert len(children) == 1
    child = children[0]
    assert child["damage_type"] == "direct"
    assert child["element"] == "fire"
    assert _breakdown(child, "non-crit", "damage.skill-multiplier") == pytest.approx(3.6)
    assert _breakdown(child, "non-crit", "damage.normal-bonus-region") == pytest.approx(1.36)
    assert _breakdown(child, "non-crit", "vulnerability.enemy-normal") == pytest.approx(0.70)
    assert _breakdown(child, "non-crit", "vulnerability.additive-region") == pytest.approx(3.2)

    ex_hit = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:ex-special-impact",
            cinema_level=6,
            enabled_rule_item_ids=[_C6_RULE],
        ),
    )
    assert ex_hit.status_code == 200
    assert len(ex_hit.json()["events"]) == 1

    ex_explosion = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:ex-special-explosion",
            cinema_level=6,
            enabled_rule_item_ids=[_C6_RULE],
        ),
    )
    assert ex_explosion.status_code == 200
    assert len(ex_explosion.json()["events"]) == 2

    ultimate = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:ultimate",
            cinema_level=6,
            enabled_rule_item_ids=[_C6_RULE],
        ),
    )
    assert ultimate.status_code == 200
    assert len(ultimate.json()["events"]) == 2

    special = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:special-complete",
            cinema_level=6,
            enabled_rule_item_ids=[_C6_RULE],
        ),
    )
    assert special.status_code == 200
    assert len(special.json()["events"]) == 1

    complete_ex = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload(
            "move-entry:character:1101:ex-special-complete",
            cinema_level=6,
            enabled_rule_item_ids=[_C6_RULE],
        ),
    )
    assert complete_ex.status_code == 200
    assert len(complete_ex.json()["events"]) == 2
    assert complete_ex.json()["totals"]["expected"]["value"] == pytest.approx(
        7810.628727858064
    )

    c0_complete_ex = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload("move-entry:character:1101:ex-special-complete"),
    )
    assert c0_complete_ex.status_code == 200
    assert len(c0_complete_ex.json()["events"]) == 1
    assert c0_complete_ex.json()["totals"]["expected"]["value"] == pytest.approx(
        5503.676667802461
    )


def test_koleda_static_fire_anomaly_and_disorder_use_documented_burn_units() -> None:
    anomaly = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload("move-entry:character:1101:fire-anomaly"),
    )
    disorder = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_payload("move-entry:character:1101:fire-disorder"),
    )
    assert anomaly.status_code == disorder.status_code == 200
    anomaly_event = _event(anomaly.json())
    disorder_event = _event(disorder.json())
    assert anomaly_event["repeat_count"] == 20
    assert _breakdown(anomaly_event, "non-crit", "anomaly.attribute.multiplier") == pytest.approx(0.5)
    assert anomaly_event["modes"]["expected"]["value"] == pytest.approx(
        anomaly_event["modes"]["non-crit"]["value"]
    )
    assert _breakdown(disorder_event, "non-crit", "disorder.total-multiplier") == pytest.approx(14.5)
