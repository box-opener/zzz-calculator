from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.anton import (
    ANTON_ID,
    AntonCompileConfig,
    compile_anton,
    load_raw_record,
)
from core.application.characters.config import CharacterSkillLevel
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import (
    _anton_additional_ability_eligibility,
    compile_registered_definition,
    registration_for,
)
from core.types import CharacterId, DamageTag, Element, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)

_CORE_RULE = "rule:character:1111:core:pile-driver-and-drill-damage"
_C4_RULE = "rule:character:1111:cinema4:team-crit-rate"
_C6_RULE = "rule:character:1111:cinema6:burst-basic-and-counter-damage-stacks"
_C4_CONDITION = "condition:anton:cinema4-team-crit-active"
_BURST_CONDITION = "condition:anton:burst-state-active"


def _anton_payload(
    move_entry_id: str,
    *,
    cinema_level: int = 0,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: list[str] | None = None,
    rule_stack_counts: dict[str, int] | None = None,
) -> dict:
    return {
        "primary_character_id": str(ANTON_ID),
        "supporting_character_ids": [],
        "team_character_ids": [str(ANTON_ID)],
        "formation_character_ids": [str(ANTON_ID)],
        "move_entry_id": move_entry_id,
        "compile_configs": {
            str(ANTON_ID): {"core_level": 7, "cinema_level": cinema_level}
        },
        "condition_values": condition_values or {},
        "parameter_values": {},
        "enabled_rule_item_ids": enabled_rule_item_ids or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
        "character_builds": {
            str(ANTON_ID): {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 7219.0996,
                    "attack": 1000.0,
                    "defense": 622.6159,
                    "impact": 95.0,
                    "crit_rate": 0.194,
                    "crit_damage": 0.5,
                    "anomaly_mastery": 86.0,
                    "anomaly_proficiency": 90.0,
                    "energy_regen": 1.2,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"physical": 0.0, "electric": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:anton-test",
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


def _anton_r5_engine_payload(move_entry_id: str) -> dict:
    payload = _anton_payload(
        move_entry_id,
        condition_values={
            _BURST_CONDITION: True,
            "condition:wengine:13111:owner:1111:ex-special-or-chain-electric-buff-active": True,
        },
        enabled_rule_item_ids=["rule:wengine:13111:owner:1111:basic-dash-electric-damage"],
    )
    payload["character_builds"][str(ANTON_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:13111",
        "wengine_level": 60,
        "wengine_refinement": 5,
        "base_stats": {
            "hp": 7219.0996,
            "attack": 791.6483,
            "defense": 622.6159,
            "impact": 95.0,
            "crit_rate": 0.194,
            "crit_damage": 0.5,
            "anomaly_mastery": 86.0,
            "anomaly_proficiency": 90.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0, "electric": 0.0},
        },
        "drive_discs": [],
    }
    return payload


def test_anton_raw_panel_a_rank_signature_and_catalog_are_registered() -> None:
    raw_data = load_character_record(str(ANTON_ID))
    raw = load_raw_record(raw_data)
    assert raw.name == "安东"
    assert raw.code_name == "Anton"
    assert raw.rarity == 3
    assert raw.specialty == "强攻"
    assert raw.element == "电属性"
    assert raw.faction == "白祇重工"
    assert raw.potential_details == ()
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1111.json",
    )

    panel = character_base_stats(ANTON_ID)
    assert panel.attack.value == pytest.approx(791.6483)
    assert panel.hp.value == pytest.approx(7219.0996)
    assert panel.defense.value == pytest.approx(622.6159)
    assert panel.impact.value == pytest.approx(95.0)
    assert panel.crit_rate.value == pytest.approx(0.194)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    assert panel.anomaly_mastery.value == pytest.approx(86.0)
    assert AntonCompileConfig().core_level == 7
    assert AntonCompileConfig().cinema_level == 0
    assert AntonCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16

    assert SIGNATURE_WENGINE_BY_CHARACTER[ANTON_ID] == WEngineId("wengine:13111")
    assert load_wengine_raw_record("wengine:13111").icon == "Weapon_A_1111"
    engine_catalog = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert engine_catalog["wengine:13111"].signature_character_id == str(ANTON_ID)
    character_catalog = {item.character_id: item for item in supported_character_catalog()}
    assert character_catalog[str(ANTON_ID)].code_name == "Anton"
    assert character_catalog[str(ANTON_ID)].image_path == "/characters/portrait-placeholder.svg"
    assert (Path(__file__).parents[2] / "frontend/public/characters/portrait-placeholder.svg").is_file()
    assert registration_for(ANTON_ID).base_element is Element.ELECTRIC
    assert registration_for(ANTON_ID).role.value == "attack"


def test_anton_direct_curves_use_source_curve_ids_tags_elements_and_skill_defaults() -> None:
    raw = load_raw_record(load_character_record(str(ANTON_ID)))
    definition = compile_anton(AntonCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert len(definition.move_entries) == 20
    assert entries["move-entry:character:1111:basic-normal-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.608)
    assert entries["move-entry:character:1111:basic-normal-4"].multiplier_variants[0].multiplier.value.value == pytest.approx(5.426)
    assert entries["move-entry:character:1111:basic-burst-2"].multiplier_variants[0].multiplier.value.value == pytest.approx(11.097)
    assert entries["move-entry:character:1111:ex-special-pile-driver"].multiplier_variants[0].multiplier.value.value == pytest.approx(4.621)
    assert entries["move-entry:character:1111:burst-special-pile-driver"].multiplier_variants[0].multiplier.value.value == pytest.approx(5.479)
    assert entries["move-entry:character:1111:ultimate-pile-driver"].multiplier_variants[0].multiplier.value.value == pytest.approx(42.944)
    assert entries["move-entry:character:1111:basic-normal-4"].main_damage_event.element == Element.PHYSICAL
    assert entries["move-entry:character:1111:basic-burst-2"].main_damage_event.element == Element.ELECTRIC
    assert entries["move-entry:character:1111:basic-burst-2"].condition_ids
    assert entries["move-entry:character:1111:ex-special-pile-driver"].damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})
    assert entries["move-entry:character:1111:special-pile-driver"].damage_tags == frozenset({DamageTag.SPECIAL_ATTACK})
    assert entries["move-entry:character:1111:assist-strike-drill-pile"].damage_tags == frozenset({DamageTag.ASSIST})

    level_12 = compile_anton(
        AntonCompileConfig(
            skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
            cinema_level=3,
        ),
        raw,
    )
    ultimate = next(item for item in level_12.move_entries if str(item.entry_id) == "move-entry:character:1111:ultimate-pile-driver")
    assert ultimate.multiplier_variants[0].multiplier.value.value == pytest.approx(39.64)


def test_anton_core_mode_bonuses_match_only_source_classified_actions() -> None:
    normal_first = "move-entry:character:1111:basic-normal-1"
    normal_pile = "move-entry:character:1111:basic-normal-4"
    burst_drill = "move-entry:character:1111:basic-burst-2"
    burst_pile = "move-entry:character:1111:basic-burst-3"
    enabled = [_CORE_RULE]

    base = _noncrit(_event(_anton_payload(normal_first)))
    assert _noncrit(_event(_anton_payload(normal_first, enabled_rule_item_ids=enabled))) == pytest.approx(base)

    pile_base = _noncrit(_event(_anton_payload(normal_pile)))
    pile_active = _noncrit(_event(_anton_payload(normal_pile, enabled_rule_item_ids=enabled)))
    assert pile_active == pytest.approx(pile_base * 1.24)

    burst_conditions = {_BURST_CONDITION: True}
    drill_base = _noncrit(_event(_anton_payload(burst_drill, condition_values=burst_conditions)))
    drill_active = _noncrit(
        _event(_anton_payload(burst_drill, condition_values=burst_conditions, enabled_rule_item_ids=enabled))
    )
    assert drill_active == pytest.approx(drill_base * 1.40)
    burst_pile_base = _noncrit(_event(_anton_payload(burst_pile, condition_values=burst_conditions)))
    burst_pile_active = _noncrit(
        _event(_anton_payload(burst_pile, condition_values=burst_conditions, enabled_rule_item_ids=enabled))
    )
    assert burst_pile_active == pytest.approx(burst_pile_base * 1.24)


def test_anton_mixed_assist_core_gap_is_local_to_selected_entry() -> None:
    entry = "move-entry:character:1111:assist-strike-drill-pile"
    plain = client.post("/api/v1/moves/calculate", json=_anton_payload(entry))
    assert plain.status_code == 200, plain.text
    assert len(plain.json()["events"]) == 1
    assert plain.json()["events"][0]["modes"]["expected"]["status"] == "calculated"

    with_core = client.post(
        "/api/v1/moves/calculate",
        json=_anton_payload(entry, enabled_rule_item_ids=[_CORE_RULE]),
    )
    assert with_core.status_code == 200, with_core.text
    assert len(with_core.json()["events"]) == 1
    parent = with_core.json()["events"][0]
    assert parent["semantic_id"] == "event:character:1111:assist-strike-drill-pile:main"
    assert parent["modes"]["expected"]["status"] == "calculated"
    assert any(
        item["blocking"] and "no per-component ratios" in item["message"]
        for item in with_core.json()["diagnostics"]
    )


def test_anton_extra_shock_is_a_local_triggered_child_without_timeline_replay() -> None:
    payload = _anton_payload("move-entry:character:1111:basic-normal-1")
    payload["supporting_character_ids"] = ["character:1011"]
    payload["team_character_ids"] = [str(ANTON_ID), "character:1011"]
    payload["formation_character_ids"] = [str(ANTON_ID), "character:1011"]
    payload["compile_configs"]["character:1011"] = {
        "core_level": 7,
        "cinema_level": 0,
    }
    payload["character_builds"]["character:1011"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 7500.0,
            "attack": 1000.0,
            "defense": 600.0,
            "impact": 136.0,
            "crit_rate": 0.05,
            "crit_damage": 0.5,
            "anomaly_mastery": 94.0,
            "anomaly_proficiency": 93.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0, "electric": 0.0},
        },
    }
    rule = "rule:character:1111:extra-ability:shock-extra-hit"
    payload["enabled_rule_item_ids"] = [rule]
    not_ready = client.post("/api/v1/moves/calculate", json=payload)
    assert not_ready.status_code == 200, not_ready.text
    assert len(not_ready.json()["events"]) == 1
    assert not not_ready.json()["diagnostics"]

    condition_values = {
        _BURST_CONDITION: True,
        "condition:anton:extra-shock-ready": True,
        "condition:anton:enemy-shocked": True,
    }
    payload["condition_values"] = condition_values
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    events = response.json()["events"]
    assert events[0]["semantic_id"] == "event:character:1111:basic-normal-1:main"
    assert events[0]["modes"]["expected"]["status"] == "calculated"
    assert any(
        "0.5625" in item["message"]
        for item in response.json()["diagnostics"]
    )


def test_anton_static_shock_is_per_tick_and_disorder_uses_current_remaining_time() -> None:
    shock = _event(_anton_payload("move-entry:character:1111:electric-shock"))
    assert shock["damage_type"] == "anomaly"
    assert shock["repeat_count"] == 10
    assert shock["modes"]["non-crit"]["value"] * 10 == pytest.approx(
        shock["modes"]["non-crit"]["known_value"]
    )

    disorder_payload = _anton_payload("move-entry:character:1111:electric-disorder")
    disorder_payload["parameter_values"] = {
        "parameter:anton:electric-disorder-remaining-seconds": 5
    }
    disorder = _event(disorder_payload)
    assert disorder["damage_type"] == "disorder"
    assert next(
        item["value"]
        for item in disorder["modes"]["non-crit"]["calculation_breakdown"]
        if item["node"] == "disorder.total-multiplier"
    ) == pytest.approx(10.75)


def test_anton_signature_engine_damage_bonus_is_electric_basic_and_dash_only() -> None:
    engine_rule = "rule:wengine:13111:owner:1111:basic-dash-electric-damage"
    engine_condition = "condition:wengine:13111:owner:1111:ex-special-or-chain-electric-buff-active"
    engine_condition_values = {
        _BURST_CONDITION: True,
        engine_condition: True,
    }

    electric_basic = "move-entry:character:1111:basic-burst-2"
    electric_base = _noncrit(
        _event(
            _anton_r5_engine_payload(electric_basic)
            | {"enabled_rule_item_ids": [], "condition_values": engine_condition_values}
        )
    )
    electric_active = _noncrit(_event(_anton_r5_engine_payload(electric_basic)))
    assert electric_active == pytest.approx(electric_base * 1.80)

    physical_basic = "move-entry:character:1111:basic-normal-1"
    physical_base = _noncrit(
        _event(
            _anton_r5_engine_payload(physical_basic)
            | {"enabled_rule_item_ids": [], "condition_values": engine_condition_values}
        )
    )
    physical_active = _noncrit(_event(_anton_r5_engine_payload(physical_basic)))
    assert physical_active == pytest.approx(physical_base)

    ex_entry = "move-entry:character:1111:ex-special-pile-driver"
    ex_base = _noncrit(
        _event(
            _anton_r5_engine_payload(ex_entry)
            | {"enabled_rule_item_ids": [], "condition_values": engine_condition_values}
        )
    )
    ex_active = _noncrit(_event(_anton_r5_engine_payload(ex_entry)))
    assert ex_active == pytest.approx(ex_base)


def test_anton_and_koleda_team_compiles_through_the_real_calculation_api() -> None:
    payload = _anton_payload("move-entry:character:1111:special-pile-driver")
    payload["supporting_character_ids"] = ["character:1101"]
    payload["team_character_ids"] = ["character:1111", "character:1101"]
    payload["formation_character_ids"] = ["character:1111", "character:1101"]
    payload["compile_configs"]["character:1101"] = {
        "core_level": 7,
        "cinema_level": 0,
        "potential_level": 0,
    }
    payload["character_builds"]["character:1101"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 700.0,
            "impact": 120.0,
            "crit_rate": 0.05,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"fire": 0.0, "physical": 0.0},
        },
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["events"][0]["modes"]["expected"]["status"] == "calculated"


def test_anton_cinema4_is_a_team_current_state_and_cinema6_is_six_manual_stacks() -> None:
    entry = "move-entry:character:1111:basic-burst-1"
    burst = {_BURST_CONDITION: True}
    c4_base = _event(_anton_payload(entry, cinema_level=4, condition_values=burst))
    c4_active = _event(
        _anton_payload(
            entry,
            cinema_level=4,
            condition_values={**burst, _C4_CONDITION: True},
            enabled_rule_item_ids=[_C4_RULE],
        )
    )
    base_cr = next(
        item["value"]
        for item in c4_base["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-rate"
    )
    active_cr = next(
        item["value"]
        for item in c4_active["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-rate"
    )
    assert base_cr == pytest.approx(0.194)
    assert active_cr == pytest.approx(0.294)

    raw = load_raw_record(load_character_record(str(ANTON_ID)))
    c6 = compile_anton(AntonCompileConfig(cinema_level=6), raw)
    stack_rule = next(item for item in c6.rule_items if str(item.rule_id) == _C6_RULE)
    assert (stack_rule.stack_count, stack_rule.stack_min, stack_rule.stack_max) == (6, 0, 6)
    stacks = _C6_RULE
    no_stack = _noncrit(
        _event(
            _anton_payload(
                entry,
                cinema_level=6,
                condition_values=burst,
                enabled_rule_item_ids=[_C6_RULE],
                rule_stack_counts={stacks: 0},
            )
        )
    )
    six_stack = _noncrit(
        _event(
            _anton_payload(
                entry,
                cinema_level=6,
                condition_values=burst,
                enabled_rule_item_ids=[_C6_RULE],
                rule_stack_counts={stacks: 6},
            )
        )
    )
    assert six_stack == pytest.approx(no_stack * 1.24)


def test_anton_additional_ability_uses_real_team_element_or_faction() -> None:
    assert not _anton_additional_ability_eligibility((ANTON_ID,))
    assert _anton_additional_ability_eligibility(
        (ANTON_ID, CharacterId("character:1011"))
    )
    assert _anton_additional_ability_eligibility(
        (ANTON_ID, CharacterId("character:1101"))
    )
    solo = compile_registered_definition(
        ANTON_ID,
        {"core_level": 7, "cinema_level": 0},
        (ANTON_ID,),
        strict=True,
    )
    ability = next(
        item for item in solo.rule_items if str(item.rule_id) == "rule:character:1111:extra-ability:shock-extra-hit"
    )
    assert ability.eligibility.value == "ineligible"
