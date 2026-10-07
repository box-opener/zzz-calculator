from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.ben import BEN_ID, BenCompileConfig, compile_ben, load_raw_record
from core.application.characters.config import CharacterSkillLevel
from core.application.characters.koleda import KoledaCompileConfig, compile_koleda, load_raw_record as load_koleda_raw
from core.application.characters.koleda.reviewed import (
    BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,
    BEN_ENHANCED_FOLLOWUP_ACTIVE,
    BEN_ID as KOLEDA_BEN_ID,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
    load_wengine_raw_record,
)
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import (
    _ben_additional_ability_eligibility,
    registration_for,
)
from core.types import (
    CalculationNode,
    CharacterId,
    CurrentDefenseValueSource,
    DamageTag,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SnapshotRule,
    WEngineId,
    WEngineBuildInput,
)
from core.application.execution.modifiers import _resolve_effect_value
from core.types import InitialCharacterSnapshot, ModifierEffect, ModifierResult
from core.application.characters.koleda import KOLEDA_ID
from web.api import app


client = TestClient(app)

_C4_RULE = "rule:character:1121:cinema4:counter-damage"
_C2_RULE = "rule:character:1121:cinema2:counter-defense-extra-damage"
_CORE_RULE = "rule:character:1121:core:initial-defense-to-attack"
_C4_CONDITION = "condition:ben:cinema4-counter-bonus-current"
_GUARD_CONDITION = "condition:ben:special-guard-counter-current"
_SHIELD_CONDITION = "condition:ben:core-shield-current"


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


def _ben_payload(
    move_entry_id: str,
    *,
    cinema_level: int = 0,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: list[str] | None = None,
    parameter_values: dict[str, int] | None = None,
) -> dict:
    ben_stats = _stats_for(BEN_ID)
    return {
        "primary_character_id": str(BEN_ID),
        "supporting_character_ids": [],
        "team_character_ids": [str(BEN_ID)],
        "formation_character_ids": [str(BEN_ID)],
        "move_entry_id": move_entry_id,
        "compile_configs": {
            str(BEN_ID): {"core_level": 7, "cinema_level": cinema_level}
        },
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "enabled_rule_item_ids": enabled_rule_item_ids or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            str(BEN_ID): {"level": 60, "out_of_combat_stats": ben_stats}
        },
        "enemy": {
            "enemy_id": "enemy:ben-test",
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
            "is_stunned": False,
        },
    }


def _koleda_ben_payload(
    move_entry_id: str,
    *,
    potential_level: int = 0,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: list[str] | None = None,
) -> dict:
    return {
        "primary_character_id": str(KOLEDA_ID),
        "supporting_character_ids": [str(BEN_ID)],
        "team_character_ids": [str(KOLEDA_ID), str(BEN_ID)],
        "formation_character_ids": [str(KOLEDA_ID), str(BEN_ID)],
        "move_entry_id": move_entry_id,
        "compile_configs": {
            str(KOLEDA_ID): {
                "core_level": 7,
                "cinema_level": 0,
                "potential_level": potential_level,
            },
            str(BEN_ID): {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": condition_values or {},
        "parameter_values": {},
        "enabled_rule_item_ids": enabled_rule_item_ids or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            str(KOLEDA_ID): {
                "level": 60,
                "out_of_combat_stats": _stats_for(KOLEDA_ID),
            },
            str(BEN_ID): {
                "level": 60,
                "out_of_combat_stats": _stats_for(BEN_ID),
            },
        },
        "enemy": {
            "enemy_id": "enemy:ben-koleda-test",
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
            "is_stunned": False,
        },
    }


def _event(payload: dict) -> dict:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["events"][0]


def _noncrit(event: dict) -> float:
    return event["modes"]["non-crit"]["value"]


def test_ben_raw_identity_panel_rank_and_signature_are_registered() -> None:
    data = load_character_record(str(BEN_ID))
    raw = load_raw_record(data)
    assert raw.name == "本"
    assert raw.code_name == "Ben"
    assert raw.rarity == 3
    assert raw.specialty == "防护"
    assert raw.element == "火属性"
    assert raw.faction == "白祇重工"
    assert raw.potential_details == ()
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1121.json",
    )

    panel = character_base_stats(BEN_ID)
    assert panel.attack.value == pytest.approx(653.0866)
    assert panel.defense.value == pytest.approx(724.0351)
    assert panel.hp.value == pytest.approx(8577.5504)
    assert panel.impact.value == pytest.approx(95.0)
    assert panel.energy_regen.value == pytest.approx(1.56)
    assert BenCompileConfig().core_level == 7
    assert BenCompileConfig().cinema_level == 0
    assert BenCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16

    assert SIGNATURE_WENGINE_BY_CHARACTER[BEN_ID] == WEngineId("wengine:13112")
    assert load_wengine_raw_record("wengine:13112").icon == "Weapon_A_1121"
    engines = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert engines["wengine:13112"].signature_character_id == str(BEN_ID)
    catalog = {item.character_id: item for item in supported_character_catalog()}
    assert catalog[str(BEN_ID)].code_name == "Ben"
    assert catalog[str(BEN_ID)].image_path == "/characters/portrait-placeholder.svg"
    assert (Path(__file__).parents[2] / "frontend/public/characters/portrait-placeholder.svg").is_file()
    registration = registration_for(BEN_ID)
    assert registration.role.value == "defense"
    assert registration.base_element.value == "fire"
    assert registration.equipment_capabilities.native_element.value == "fire"


def test_ben_signature_engine_uses_its_native_fire_event_for_big_cylinder_proc() -> None:
    capabilities = registration_for(BEN_ID).equipment_capabilities
    result = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:13112"), BEN_ID, level=60, refinement=5),
        owner_capabilities=capabilities,
    )
    assert result.damage_event_templates
    template = result.damage_event_templates[0]
    assert template.ref.element.value == "fire"
    assert isinstance(template.base_source, CurrentDefenseValueSource)
    assert template.crit_rule.guaranteed is True


def test_ben_direct_curves_and_complete_source_actions_keep_exact_units() -> None:
    raw = load_raw_record(load_character_record(str(BEN_ID)))
    definition = compile_ben(BenCompileConfig(), raw)
    entries = {str(entry.entry_id): entry for entry in definition.move_entries}
    assert len(definition.move_entries) == 20
    expected = {
        "basic-1": 1.559,
        "special-active": 0.987,
        "special-counter": 5.529,
        "ex-special-main": 10.370,
        "ex-special-followup": 10.370,
        "ex-special-counter": 11.830,
        "ex-special-counter-followup": 13.042,
        "ex-special-complete-followup": 20.740,
        "ex-special-complete-successful-counter": 24.872,
    }
    for key, value in expected.items():
        assert entries[f"move-entry:character:1121:{key}"].multiplier_variants[0].multiplier.value.value == pytest.approx(value)
    assert entries["move-entry:character:1121:basic-1"].main_damage_event.element.value == "physical"
    assert entries["move-entry:character:1121:dodge-counter"].main_damage_event.element.value == "fire"
    assert entries["move-entry:character:1121:ex-special-main"].damage_tags == frozenset(
        {DamageTag.EX_SPECIAL_ATTACK}
    )
    assert entries["move-entry:character:1121:ex-special-complete-followup"].condition_ids
    assert BenCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16

    selected_12 = compile_ben(
        BenCompileConfig(
            skill_levels=(
                CharacterSkillLevel(SkillGroup.ULTIMATE, 12),
            ),
            cinema_level=3,
        ),
        raw,
    )
    ultimate = next(
        item for item in selected_12.move_entries if str(item.entry_id) == "move-entry:character:1121:ultimate"
    )
    assert ultimate.multiplier_variants[0].multiplier.value.value == pytest.approx(35.852)


def test_ben_cinema4_is_current_and_only_affects_guard_counter_damage() -> None:
    counter = "move-entry:character:1121:special-counter"
    active = {
        _GUARD_CONDITION: True,
        _C4_CONDITION: True,
    }
    base = _noncrit(_event(_ben_payload(counter, cinema_level=4, condition_values={_GUARD_CONDITION: True})))
    boosted = _noncrit(
        _event(
            _ben_payload(
                counter,
                cinema_level=4,
                condition_values=active,
                enabled_rule_item_ids=[_C4_RULE],
            )
        )
    )
    assert boosted == pytest.approx(base * 1.30)

    ordinary = "move-entry:character:1121:special-active"
    ordinary_base = _noncrit(_event(_ben_payload(ordinary, cinema_level=4)))
    ordinary_boosted = _noncrit(
        _event(
            _ben_payload(
                ordinary,
                cinema_level=4,
                condition_values=active,
                enabled_rule_item_ids=[_C4_RULE],
            )
        )
    )
    assert ordinary_boosted == pytest.approx(ordinary_base)


def test_ben_extra_ability_uses_real_team_element_or_faction_and_core_shield_state() -> None:
    assert not _ben_additional_ability_eligibility((BEN_ID,))
    assert _ben_additional_ability_eligibility((BEN_ID, CharacterId("character:1101")))
    assert not _ben_additional_ability_eligibility((BEN_ID, CharacterId("character:1011")))

    compile_config = BenCompileConfig(additional_ability_eligible=True)
    definition = compile_ben(
        compile_config,
        load_raw_record(load_character_record(str(BEN_ID))),
    )
    extra = next(
        rule
        for rule in definition.rule_items
        if str(rule.rule_id) == "rule:character:1121:extra-ability:team-crit-rate-while-core-shielded"
    )
    assert extra.eligibility.value == "eligible"
    assert extra.condition_ids


def test_ben_cinema2_counter_child_is_local_unresolved_not_a_fake_damage_hit() -> None:
    payload = _ben_payload(
        "move-entry:character:1121:special-counter",
        cinema_level=2,
        condition_values={_GUARD_CONDITION: True},
        enabled_rule_item_ids=[_C2_RULE],
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["events"]) == 1
    assert result["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert any(
        item["blocking"] and "300%" in item["message"]
        for item in result["diagnostics"]
    )


def test_initial_defense_can_be_resolved_as_a_panel_derived_source() -> None:
    initial_stats = character_base_stats(BEN_ID)
    source = RuleSource(
        source_id=RuleSourceId("source:test:initial-defense"),
        source_type=EffectSourceType.CORE_PASSIVE,
        label="Ben Initial DEF test",
        raw_text="test",
    )
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:test:initial-defense"),
            source=source,
            owner=BEN_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=PanelStatDerivedValue(
                source_character_id=BEN_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_DEFENSE,
                coefficient=Resolved(0.8),
            ),
        ),
    )
    resolved = _resolve_effect_value(
        effect,
        (InitialCharacterSnapshot(BEN_ID, 60, initial_stats),),
        [],
    )
    assert resolved is not None
    assert isinstance(resolved.result.value, Resolved)
    assert resolved.result.value.value == pytest.approx(579.22808)


def test_ben_core_defense_to_attack_layer_is_visible_but_not_guessed() -> None:
    move = "move-entry:character:1121:basic-1"
    base = _event(_ben_payload(move))
    with_core = client.post(
        "/api/v1/moves/calculate",
        json=_ben_payload(move, enabled_rule_item_ids=[_CORE_RULE]),
    )
    assert with_core.status_code == 200, with_core.text
    result = with_core.json()
    assert result["events"][0]["modes"]["non-crit"]["value"] == pytest.approx(
        base["modes"]["non-crit"]["value"]
    )
    diagnostic = next(item for item in result["diagnostics"] if item["diagnostic_id"].endswith("initial-defense-to-attack-layer"))
    assert diagnostic["blocking"] is False
    assert "初始攻击力随初始防御力提升" in diagnostic["original_text"]


def test_koleda_ben_synergy_selects_the_actual_teammate_curves_and_states() -> None:
    raw = load_koleda_raw(
        load_character_record(str(KOLEDA_ID)),
        potential_level=0,
    )
    p0_with_ben = compile_koleda(
        KoledaCompileConfig(ben_in_team=True),
        raw,
    )
    p0_stage2 = next(
        entry
        for entry in p0_with_ben.move_entries
        if str(entry.entry_id) == "move-entry:character:1101:enhanced-basic-stage2"
    )
    assert "本协同" in p0_stage2.display_name
    source_move = next(move for move in raw.moves if move.name == "普通攻击：砸扁，粉碎")
    coordinated_curve = next(
        parameter
        for parameter in source_move.parameters
        if parameter.name == "强化普攻二段伤害倍率（协同）"
    )
    assert p0_stage2.multiplier_variants[0].multiplier.value.value == pytest.approx(
        coordinated_curve.value_for_level(12, "1101007") / 100
    )
    assert any(
        str(item.entry_id) == "move-entry:character:1101:ultimate"
        and "本协同" in item.display_name
        for item in p0_with_ben.move_entries
    )

    p1_with_ben = compile_koleda(
        KoledaCompileConfig(potential_level=1, ben_in_team=True),
        load_koleda_raw(load_character_record(str(KOLEDA_ID)), potential_level=1),
    )
    p1_stage2 = next(
        entry
        for entry in p1_with_ben.move_entries
        if str(entry.entry_id) == "move-entry:character:1101:enhanced-basic-stage2"
    )
    p1_coop_stage2 = next(
        entry
        for entry in p1_with_ben.move_entries
        if str(entry.entry_id) == "move-entry:character:1101:enhanced-basic-stage2-ben-coordinated"
    )
    assert "本协同" not in p1_stage2.display_name
    assert p1_coop_stage2.condition_ids == (BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,)

    assert _ben_additional_ability_eligibility((BEN_ID, KOLEDA_ID))


def test_koleda_team_compiles_and_uses_ben_cooperation_from_real_team_membership() -> None:
    koleda_raw = load_koleda_raw(
        load_character_record(str(KOLEDA_ID)),
        potential_level=0,
    )
    p0_definition = compile_koleda(
        KoledaCompileConfig(ben_in_team=True),
        koleda_raw,
    )
    p0_stage2 = next(
        entry
        for entry in p0_definition.move_entries
        if str(entry.entry_id) == "move-entry:character:1101:enhanced-basic-stage2"
    )
    source_move = next(move for move in koleda_raw.moves if move.name == "普通攻击：砸扁，粉碎")
    source_curve = next(
        parameter
        for parameter in source_move.parameters
        if parameter.name == "强化普攻二段伤害倍率（协同）"
    )
    expected_p0_multiplier = source_curve.value_for_level(12, "1101007") / 100
    assert "本协同" in p0_stage2.display_name
    assert p0_stage2.multiplier_variants[0].multiplier.value.value == pytest.approx(
        expected_p0_multiplier
    )
    assert any(
        str(item.entry_id) == "move-entry:character:1101:ultimate"
        and "本协同" in item.display_name
        for item in p0_definition.move_entries
    )

    # Exercise the registered team path, not only the standalone Koleda compiler.
    p0_response = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_ben_payload("move-entry:character:1101:enhanced-basic-stage2"),
    )
    assert p0_response.status_code == 200, p0_response.text
    p0_event = p0_response.json()["events"][0]
    assert p0_event["modes"]["expected"]["status"] == "calculated"
    p0_multiplier = next(
        item["value"]
        for item in p0_event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.skill-multiplier"
    )
    assert p0_multiplier == pytest.approx(expected_p0_multiplier)

    p1_coop_response = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_ben_payload(
            "move-entry:character:1101:enhanced-basic-stage2-ben-coordinated",
            potential_level=1,
            condition_values={str(BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH): True},
        ),
    )
    assert p1_coop_response.status_code == 200, p1_coop_response.text
    p1_coop_event = p1_coop_response.json()["events"][0]
    assert p1_coop_event["modes"]["expected"]["status"] == "calculated"
    p1_coop_multiplier = next(
        item["value"]
        for item in p1_coop_event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.skill-multiplier"
    )
    assert p1_coop_multiplier == pytest.approx(expected_p0_multiplier)
    p1_switched = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_ben_payload(
            "move-entry:character:1101:enhanced-basic-stage2-ben-coordinated",
            potential_level=1,
            condition_values={str(BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH): False},
        ),
    )
    assert p1_switched.status_code == 200, p1_switched.text
    assert p1_switched.json()["events"] == []

    quick_followup = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_ben_payload(
            "move-entry:character:1101:special-ben-coordinated-explosion",
            condition_values={str(BEN_ENHANCED_FOLLOWUP_ACTIVE): True},
        ),
    )
    assert quick_followup.status_code == 200, quick_followup.text
    assert quick_followup.json()["events"][0]["modes"]["expected"]["status"] == "calculated"

    # The Core shield recipient effect is team-wide and does not require Ben
    # to be the current operator or the damage dealer for this calculation.
    ben_shielded = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_ben_payload(
            "move-entry:character:1101:basic-physical-1",
            condition_values={_SHIELD_CONDITION: True},
            enabled_rule_item_ids=[
                "rule:character:1121:extra-ability:team-crit-rate-while-core-shielded"
            ],
        ),
    )
    assert ben_shielded.status_code == 200, ben_shielded.text
    shielded_crit = next(
        item["value"]
        for item in ben_shielded.json()["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-rate"
    )
    assert shielded_crit == pytest.approx(0.21)

    ultimate_response = client.post(
        "/api/v1/moves/calculate",
        json=_koleda_ben_payload("move-entry:character:1101:ultimate"),
    )
    assert ultimate_response.status_code == 200, ultimate_response.text
    ultimate_event = ultimate_response.json()["events"][0]
    ultimate_multiplier = next(
        item["value"]
        for item in ultimate_event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.skill-multiplier"
    )
    raw_ultimate = next(move for move in koleda_raw.moves if move.name == "终结技：锤进地心")
    ultimate_curve = next(
        parameter
        for parameter in raw_ultimate.parameters
        if parameter.name == "伤害倍率（协同）"
    )
    assert ultimate_multiplier == pytest.approx(
        ultimate_curve.value_for_level(12, "1101402") / 100
    )
