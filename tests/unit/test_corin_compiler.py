from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.corin import (
    CORIN_ID,
    CorinCompileConfig,
    compile_corin,
    load_raw_record,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import compile_registered_definition, registration_for
from core.types import DamageTag, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)


def _corin_payload(
    move_entry_id: str,
    *,
    cinema_level: int = 0,
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: list[str] | None = None,
    rule_stack_counts: dict[str, int] | None = None,
    enemy_stunned: bool = False,
    physical_resistance: float = 0.0,
    team_character_ids: list[str] | None = None,
) -> dict:
    team = team_character_ids or ["character:1061"]
    return {
        "primary_character_id": "character:1061",
        "supporting_character_ids": [item for item in team if item != "character:1061"],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            "character:1061": {"core_level": 7, "cinema_level": cinema_level},
            **{
                item: {"core_level": 7, "cinema_level": 0}
                for item in team
                if item != "character:1061"
            },
        },
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "enabled_rule_item_ids": enabled_rule_item_ids or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
        "character_builds": {
            item: {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 6976.9443,
                    "attack": 1000.0,
                    "defense": 604.5976,
                    "impact": 120.0,
                    "crit_rate": 0.05,
                    "crit_damage": 0.788,
                    "anomaly_mastery": 93.0,
                    "anomaly_proficiency": 96.0,
                    "energy_regen": 1.2,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"physical": 0.0},
                },
            }
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:corin-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": physical_resistance,
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
    }


def _event(response: dict) -> dict:
    return response["events"][0]


def _breakdown(event: dict, node: str) -> float:
    return next(
        item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == node
    )


def test_corin_raw_identity_a_rank_defaults_and_signature_are_registered() -> None:
    raw_data = load_character_record(str(CORIN_ID))
    raw = load_raw_record(raw_data)
    assert raw.name == "可琳"
    assert raw.code_name == "Corin"
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1061.json",
    )
    assert raw.rarity == 3
    panel = character_base_stats(CORIN_ID)
    assert panel.hp.value == pytest.approx(6976.9443)
    assert panel.attack.value == pytest.approx(807.1414)
    assert panel.defense.value == pytest.approx(604.5976)
    assert panel.crit_damage.value == pytest.approx(0.788)
    assert panel.anomaly_mastery.value == pytest.approx(93.0)
    assert panel.anomaly_proficiency.value == pytest.approx(96.0)
    assert CorinCompileConfig().cinema_level == 0
    assert CorinCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16
    assert SIGNATURE_WENGINE_BY_CHARACTER[CORIN_ID] == WEngineId("wengine:13106")
    from core.application.equipment import load_wengine_raw_record

    assert load_wengine_raw_record("wengine:13106").icon == "Weapon_A_1061"
    registration = registration_for(CORIN_ID)
    assert registration.catalog.rarity == "A"
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "characters"
    assert (asset_root / "IconRole09.webp").is_file()
    catalog = {item.character_id: item for item in supported_character_catalog()}
    assert catalog["character:1061"].code_name == "Corin"


def test_corin_reviewed_direct_curves_use_a_rank_level_and_correct_skill_tags() -> None:
    raw = load_raw_record(load_character_record(str(CORIN_ID)))
    definition = compile_corin(CorinCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    special = entries[
        "move-entry:character:1061:special-full-maximum-continuous-saw"
    ]
    ex = entries[
        "move-entry:character:1061:ex-special-full-maximum-continuous-saw"
    ]
    assert special.multiplier_variants[0].multiplier.value.value == pytest.approx(3.077)
    assert ex.multiplier_variants[0].multiplier.value.value == pytest.approx(40.804)
    assert ex.damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})
    assert entries["move-entry:character:1061:assist-strike-quick-cleaning"].damage_tags == frozenset(
        {DamageTag.ASSIST}
    )

    selected_12 = CorinCompileConfig(
        skill_levels=(CharacterSkillLevel(SkillGroup.SPECIAL_ATTACK, 12),),
        core_level=7,
        cinema_level=3,
    )
    level_14 = compile_corin(selected_12, raw)
    ex_at_14 = next(
        item
        for item in level_14.move_entries
        if str(item.entry_id)
        == "move-entry:character:1061:ex-special-full-maximum-continuous-saw"
    )
    assert ex_at_14.multiplier_variants[0].multiplier.value.value == pytest.approx(37.664)


def test_corin_api_static_physical_anomaly_and_disorder_use_nocrit_and_time_formula() -> None:
    anomaly = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload("move-entry:character:1061:physical-anomaly"),
    )
    disorder = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload("move-entry:character:1061:physical-disorder"),
    )
    assert anomaly.status_code == disorder.status_code == 200
    anomaly_event = _event(anomaly.json())
    disorder_event = _event(disorder.json())
    assert anomaly_event["damage_type"] == "anomaly"
    assert _breakdown(anomaly_event, "anomaly.attribute.multiplier") == pytest.approx(7.13)
    assert anomaly_event["modes"]["expected"]["value"] == pytest.approx(
        anomaly_event["modes"]["non-crit"]["value"]
    )
    assert disorder_event["damage_type"] == "disorder"
    assert _breakdown(disorder_event, "disorder.total-multiplier") == pytest.approx(5.25)
    assert disorder_event["modes"]["expected"]["value"] == pytest.approx(
        disorder_event["modes"]["non-crit"]["value"]
    )


def test_corin_cinema6_charge_is_one_extra_attack_ratio_per_explosion() -> None:
    entry_id = "move-entry:character:1061:ex-special-saw-explosion"
    base = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(entry_id, cinema_level=6),
    )
    charged = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry_id,
            cinema_level=6,
            parameter_values={"parameter:corin:cinema6-current-chainsaw-charges": 40},
        ),
    )
    assert base.status_code == charged.status_code == 200
    base_event = _event(base.json())
    charged_event = _event(charged.json())
    assert _breakdown(base_event, "damage.skill-multiplier") == pytest.approx(8.161)
    assert _breakdown(charged_event, "damage.skill-multiplier") == pytest.approx(9.361)


def test_corin_target_and_enemy_state_rules_keep_separate_scopes() -> None:
    move_entry_id = "move-entry:character:1061:ultimate-very-sorry"
    c1_rule = "rule:character:1061:cinema1:current-target-damage"
    core_rule = "rule:character:1061:core:chainsaw-continuous-damage"
    extra_rule = "rule:character:1061:extra-ability:stunned-target-damage"
    baseline = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(move_entry_id, cinema_level=1, team_character_ids=["character:1061", "character:1021"]),
    )
    target_buff = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            move_entry_id,
            cinema_level=1,
            condition_values={"condition:corin:cinema1-target-damage-active": True},
            enabled_rule_item_ids=[c1_rule],
            team_character_ids=["character:1061", "character:1021"],
        ),
    )
    assert baseline.status_code == target_buff.status_code == 200
    base_region = _breakdown(_event(baseline.json()), "damage.normal-bonus-region")
    c1_region = _breakdown(_event(target_buff.json()), "damage.normal-bonus-region")
    assert c1_region == pytest.approx(base_region + 0.12)

    stunned = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            move_entry_id,
            team_character_ids=["character:1061", "character:1021"],
            enemy_stunned=True,
            condition_values={"condition:corin:chainsaw-continuous-active": True},
            enabled_rule_item_ids=[core_rule, extra_rule],
        ),
    )
    assert stunned.status_code == 200, stunned.text
    bonus_region = _breakdown(_event(stunned.json()), "damage.normal-bonus-region")
    assert bonus_region == pytest.approx(1.725)


def test_corin_cinema2_physical_resistance_layers_are_enemy_scoped() -> None:
    entry = "move-entry:character:1061:ex-special-saw-explosion"
    rule = "rule:character:1061:cinema2:current-physical-resistance-stacks"
    baseline = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry,
            cinema_level=2,
            physical_resistance=0.20,
        ),
    )
    reduced = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry,
            cinema_level=2,
            physical_resistance=0.20,
            enabled_rule_item_ids=[rule],
        ),
    )
    zero = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry,
            cinema_level=2,
            physical_resistance=0.20,
            enabled_rule_item_ids=[rule],
            rule_stack_counts={rule: 0},
        ),
    )
    half = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry,
            cinema_level=2,
            physical_resistance=0.20,
            enabled_rule_item_ids=[rule],
            rule_stack_counts={rule: 10},
        ),
    )
    assert baseline.status_code == reduced.status_code == zero.status_code == half.status_code == 200
    assert _breakdown(_event(baseline.json()), "resistance.region") == pytest.approx(0.8)
    assert _breakdown(_event(reduced.json()), "resistance.region") == pytest.approx(0.9)
    assert _breakdown(_event(zero.json()), "resistance.region") == pytest.approx(0.8)
    assert _breakdown(_event(half.json()), "resistance.region") == pytest.approx(0.85)


def test_corin_additional_ability_is_ineligible_without_matching_teammate() -> None:
    solo = compile_registered_definition(
        CORIN_ID,
        {"core_level": 7, "cinema_level": 0},
        [CORIN_ID],
    )
    with_physical_teammate = compile_registered_definition(
        CORIN_ID,
        {"core_level": 7, "cinema_level": 0},
        [CORIN_ID, "character:1021"],
    )
    solo_rule = next(
        item for item in solo.rule_items
        if str(item.rule_id) == "rule:character:1061:extra-ability:stunned-target-damage"
    )
    team_rule = next(
        item for item in with_physical_teammate.rule_items
        if str(item.rule_id) == "rule:character:1061:extra-ability:stunned-target-damage"
    )
    assert solo_rule.eligibility.value == "ineligible"
    assert team_rule.eligibility.value == "eligible"


def test_corin_stunned_target_bonus_is_captured_once_in_her_anomaly_source() -> None:
    entry = "move-entry:character:1061:physical-anomaly"
    rule = "rule:character:1061:extra-ability:stunned-target-damage"
    team = ["character:1061", "character:1021"]
    not_stunned = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry,
            team_character_ids=team,
            enabled_rule_item_ids=[rule],
            enemy_stunned=False,
        ),
    )
    stunned = client.post(
        "/api/v1/moves/calculate",
        json=_corin_payload(
            entry,
            team_character_ids=team,
            enabled_rule_item_ids=[rule],
            enemy_stunned=True,
        ),
    )
    assert not_stunned.status_code == stunned.status_code == 200
    before = _event(not_stunned.json())["modes"]["expected"]["value"]
    after = _event(stunned.json())["modes"]["expected"]["value"]
    assert after == pytest.approx(before * 1.35)
