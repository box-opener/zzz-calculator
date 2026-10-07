from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.billy import (
    BILLY_ID,
    BillyCompileConfig,
    compile_billy,
    load_raw_record,
)
from core.application.characters.config import CharacterSkillLevel
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import compile_registered_definition
from core.types import CharacterId, DamageTag, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)

_CROUCH_RULE = "rule:character:1081:core:crouch-shooting-damage"
_CINEMA4_RULE = "rule:character:1081:cinema4:ex-crit-rate"
_CINEMA4_PARAMETER = "parameter:billy:cinema4-ex-current-crit-rate-bonus-percent"
_CINEMA6_RULE = "rule:character:1081:cinema6:current-damage-stacks"


def _billy_payload(
    move_entry_id: str,
    *,
    cinema_level: int = 0,
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: list[str] | None = None,
    rule_stack_counts: dict[str, int] | None = None,
) -> dict:
    return {
        "primary_character_id": str(BILLY_ID),
        "supporting_character_ids": [],
        "team_character_ids": [str(BILLY_ID)],
        "formation_character_ids": [str(BILLY_ID)],
        "move_entry_id": move_entry_id,
        "compile_configs": {
            str(BILLY_ID): {"core_level": 7, "cinema_level": cinema_level}
        },
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "enabled_rule_item_ids": enabled_rule_item_ids or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
        "character_builds": {
            str(BILLY_ID): {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 6907.2636,
                    "attack": 1000.0,
                    "defense": 606.5977,
                    "impact": 120.0,
                    "crit_rate": 0.194,
                    "crit_damage": 0.5,
                    "anomaly_mastery": 92.0,
                    "anomaly_proficiency": 91.0,
                    "energy_regen": 1.2,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"physical": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:billy-test",
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


def _billy_equipped_payload(move_entry_id: str, **kwargs) -> dict:
    payload = _billy_payload(move_entry_id, **kwargs)
    payload["character_builds"][str(BILLY_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:13108",
        "wengine_level": 60,
        "wengine_refinement": 5,
        "base_stats": {
            "hp": 6907.2636,
            "attack": 787.2765,
            "defense": 606.5977,
            "impact": 120.0,
            "crit_rate": 0.194,
            "crit_damage": 0.5,
            "anomaly_mastery": 92.0,
            "anomaly_proficiency": 91.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0},
        },
        "drive_discs": [],
    }
    return payload


def _event(response: dict) -> dict:
    return response["events"][0]


def _breakdown(event: dict, mode: str, node: str) -> float:
    return next(
        item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
        if item["node"] == node
    )


def test_billy_live_identity_panel_signature_and_catalog_are_registered() -> None:
    raw_data = load_character_record(str(BILLY_ID))
    raw = load_raw_record(raw_data)
    assert raw.name == "比利"
    assert raw.code_name == "Billy"
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1081.json",
    )
    assert raw.rarity == 3
    assert raw.specialty == "强攻"
    assert raw.element == "物理"
    assert raw.faction == "狡兔屋"
    assert raw.potential_details == ()

    panel = character_base_stats(BILLY_ID)
    assert panel.attack.value == pytest.approx(787.2765)
    assert panel.hp.value == pytest.approx(6907.2636)
    assert panel.defense.value == pytest.approx(606.5977)
    assert panel.crit_rate.value == pytest.approx(0.194)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_mastery.value == pytest.approx(92.0)
    assert panel.anomaly_proficiency.value == pytest.approx(91.0)
    assert BillyCompileConfig().core_level == 7
    assert BillyCompileConfig().cinema_level == 0
    assert BillyCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16

    assert SIGNATURE_WENGINE_BY_CHARACTER[BILLY_ID] == WEngineId("wengine:13108")
    assert load_wengine_raw_record("wengine:13108").icon == "Weapon_A_1081"
    wengine = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert wengine["wengine:13108"].signature_character_id == str(BILLY_ID)
    registration = compile_registered_definition(
        BILLY_ID, {"core_level": 7, "cinema_level": 0}, (BILLY_ID,), strict=True
    )
    assert registration.character_id == BILLY_ID
    catalog = {item.character_id: item for item in supported_character_catalog()}
    assert catalog[str(BILLY_ID)].code_name == "Billy"
    assert catalog[str(BILLY_ID)].image_path == "/characters/portrait-placeholder.svg"
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "characters"
    assert (asset_root / "portrait-placeholder.svg").is_file()


def test_billy_reviewed_curves_keep_action_tags_and_a_rank_skill_defaults() -> None:
    raw = load_raw_record(load_character_record(str(BILLY_ID)))
    definition = compile_billy(BillyCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert entries["move-entry:character:1081:basic-standing-fire"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.61)
    assert entries["move-entry:character:1081:ex-cleanup-time"].multiplier_variants[0].multiplier.value.value == pytest.approx(12.863)
    assert entries["move-entry:character:1081:ultimate-star-emblem"].multiplier_variants[0].multiplier.value.value == pytest.approx(37.772)
    assert entries["move-entry:character:1081:special-stay-still-2"].stage_index == 2
    assert entries["move-entry:character:1081:assist-strike-vital-shot"].damage_tags == frozenset({DamageTag.ASSIST})
    assert entries["move-entry:character:1081:ex-cleanup-time"].damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})

    selected_level_12 = BillyCompileConfig(
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
        core_level=7,
        cinema_level=3,
    )
    level_14 = compile_billy(selected_level_12, raw)
    ult = next(
        item
        for item in level_14.move_entries
        if str(item.entry_id) == "move-entry:character:1081:ultimate-star-emblem"
    )
    assert ult.multiplier_variants[0].multiplier.value.value == pytest.approx(34.866)


def test_billy_cinema4_crit_rate_is_event_only_and_uses_bounded_current_input() -> None:
    raw = load_raw_record(load_character_record(str(BILLY_ID)))
    c0 = compile_billy(BillyCompileConfig(cinema_level=0), raw)
    assert all(str(item.parameter_id) != _CINEMA4_PARAMETER for item in c0.scenario_parameters)
    c4 = compile_billy(BillyCompileConfig(cinema_level=4), raw)
    parameter = next(item for item in c4.scenario_parameters if str(item.parameter_id) == _CINEMA4_PARAMETER)
    assert (parameter.value, parameter.minimum, parameter.maximum) == (32, 0, 32)

    ex_entry = "move-entry:character:1081:ex-cleanup-time"
    base = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            ex_entry,
            cinema_level=4,
            parameter_values={_CINEMA4_PARAMETER: 0},
            enabled_rule_item_ids=[_CINEMA4_RULE],
        ),
    )
    close_range_max = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            ex_entry,
            cinema_level=4,
            parameter_values={_CINEMA4_PARAMETER: 32},
            enabled_rule_item_ids=[_CINEMA4_RULE],
        ),
    )
    default_max = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            ex_entry,
            cinema_level=4,
            enabled_rule_item_ids=[_CINEMA4_RULE],
        ),
    )
    assert base.status_code == close_range_max.status_code == default_max.status_code == 200
    base_event = _event(base.json())
    max_event = _event(close_range_max.json())
    assert _breakdown(base_event, "expected", "character.current.crit-rate") == pytest.approx(0.194)
    assert _breakdown(max_event, "expected", "character.current.crit-rate") == pytest.approx(0.514)
    assert _breakdown(base_event, "expected", "damage.standard-crit-region") == pytest.approx(1.097)
    assert _breakdown(max_event, "expected", "damage.standard-crit-region") == pytest.approx(1.257)
    assert _breakdown(_event(default_max.json()), "expected", "character.current.crit-rate") == pytest.approx(0.514)
    assert _event(close_range_max.json())["modes"]["non-crit"]["value"] == pytest.approx(
        _event(base.json())["modes"]["non-crit"]["value"]
    )
    assert close_range_max.json()["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(0.194)

    other_move = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            "move-entry:character:1081:basic-standing-fire",
            cinema_level=4,
            parameter_values={_CINEMA4_PARAMETER: 32},
            enabled_rule_item_ids=[_CINEMA4_RULE],
        ),
    )
    assert other_move.status_code == 200
    assert _breakdown(_event(other_move.json()), "expected", "character.current.crit-rate") == pytest.approx(0.194)

    out_of_range = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            ex_entry,
            cinema_level=4,
            parameter_values={_CINEMA4_PARAMETER: 33},
            enabled_rule_item_ids=[_CINEMA4_RULE],
        ),
    )
    assert out_of_range.status_code == 400


def test_billy_crouch_damage_state_applies_to_all_billy_damage_once() -> None:
    direct = "move-entry:character:1081:ex-cleanup-time"
    baseline = client.post("/api/v1/moves/calculate", json=_billy_payload(direct))
    crouched = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            direct,
            condition_values={"condition:billy:crouch-shooting-damage-active": True},
            enabled_rule_item_ids=[_CROUCH_RULE],
        ),
    )
    assert baseline.status_code == crouched.status_code == 200
    assert _breakdown(_event(baseline.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.0)
    assert _breakdown(_event(crouched.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.5)

    anomaly = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            "move-entry:character:1081:physical-anomaly",
            condition_values={"condition:billy:crouch-shooting-damage-active": True},
            enabled_rule_item_ids=[_CROUCH_RULE],
        ),
    )
    assert anomaly.status_code == 200
    trace = _event(anomaly.json())["modes"]["non-crit"]["anomaly_effect_strength_trace"]
    assert trace["normal_bonus"] == pytest.approx(0.5)
    assert trace["final_strength"] == pytest.approx(2730.0)


def test_billy_additional_ability_requires_same_element_or_faction_not_evade_tag() -> None:
    config = {"core_level": 7, "cinema_level": 0}
    same_camp = compile_registered_definition(
        BILLY_ID,
        config,
        (BILLY_ID, CharacterId("character:1031")),
        strict=True,
    )
    assert next(
        item for item in same_camp.rule_items
        if str(item.rule_id) == "rule:character:1081:extra-ability:ultimate-after-chain"
    ).eligibility.value == "eligible"

    evade_only = compile_registered_definition(
        BILLY_ID,
        config,
        (BILLY_ID, CharacterId("character:1361")),
        strict=True,
    )
    assert next(
        item for item in evade_only.rule_items
        if str(item.rule_id) == "rule:character:1081:extra-ability:ultimate-after-chain"
    ).eligibility.value == "ineligible"

    caesar_id = CharacterId("character:1071")
    caesar = compile_registered_definition(
        caesar_id,
        config,
        (caesar_id, BILLY_ID),
        strict=True,
    )
    assert next(
        item for item in caesar.rule_items
        if str(item.rule_id) == "rule:character:1071:extra-ability:enemy-normal-vulnerability"
    ).eligibility.value == "ineligible"


def test_billy_signature_engine_current_physical_state_uses_r5_value() -> None:
    payload = _billy_equipped_payload("move-entry:character:1081:ex-cleanup-time")
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:13108:owner:1081:distant-physical-damage"
    ]
    payload["condition_values"] = {
        "condition:wengine:13108:owner:1081:distant-physical-hit-buff-active": True
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(
        1764.095625
    )
    assert _breakdown(_event(result), "non-crit", "damage.normal-bonus-region") == pytest.approx(
        1.575
    )


def test_billy_cinema6_default_stack_cap_and_explicit_zero_are_distinct() -> None:
    move = "move-entry:character:1081:ultimate-star-emblem"
    default_max = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            move,
            cinema_level=6,
            enabled_rule_item_ids=[_CINEMA6_RULE],
        ),
    )
    no_stacks = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            move,
            cinema_level=6,
            enabled_rule_item_ids=[_CINEMA6_RULE],
            rule_stack_counts={_CINEMA6_RULE: 0},
        ),
    )
    two_stacks = client.post(
        "/api/v1/moves/calculate",
        json=_billy_payload(
            move,
            cinema_level=6,
            enabled_rule_item_ids=[_CINEMA6_RULE],
            rule_stack_counts={_CINEMA6_RULE: 2},
        ),
    )
    assert default_max.status_code == no_stacks.status_code == two_stacks.status_code == 200
    assert _breakdown(_event(default_max.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.3)
    assert _breakdown(_event(no_stacks.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.0)
    assert _breakdown(_event(two_stacks.json()), "non-crit", "damage.normal-bonus-region") == pytest.approx(1.12)
