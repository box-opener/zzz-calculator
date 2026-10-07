from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.caesar import (
    CAESAR_ID,
    CaesarCompileConfig,
    compile_caesar,
    load_raw_record,
)
from core.application.characters.config import CharacterSkillLevel
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import compile_registered_definition, registration_for
from core.types import CharacterRole, DamageTag, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)


def _stats(element: str = "physical") -> dict:
    return {
        "hp": 9526.2299,
        "attack": 1000.0,
        "defense": 753.862,
        "impact": 123.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 87.0,
        "anomaly_proficiency": 90.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: 0.0},
    }


def _caesar_payload(
    move_entry_id: str,
    *,
    primary: str = "character:1071",
    team: list[str] | None = None,
    formation: list[str] | None = None,
    core_level: int = 7,
    cinema_level: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled_rules: list[str] | None = None,
    enemy_resistance: float = 0.0,
    enemy_stunned: bool = False,
) -> dict:
    team_ids = team or [primary]
    compile_configs = {
        item: {"core_level": 7, "cinema_level": 0}
        for item in team_ids
        if item != "character:1071"
    }
    compile_configs["character:1071"] = {
        "core_level": core_level,
        "cinema_level": cinema_level,
    }
    return {
        "primary_character_id": primary,
        "supporting_character_ids": [item for item in team_ids if item != primary],
        "team_character_ids": team_ids,
        "formation_character_ids": formation or team_ids,
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": enabled_rules or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {item: {"level": 60, "out_of_combat_stats": _stats()} for item in team_ids},
        "enemy": {
            "enemy_id": "enemy:caesar-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": enemy_resistance,
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


def _event(result: dict) -> dict:
    return result["events"][0]


def _node(event: dict, node: str, mode: str = "expected") -> float:
    return next(
        row["value"]
        for row in event["modes"][mode]["calculation_breakdown"]
        if row["node"] == node
    )


def test_caesar_source_panel_signature_and_defense_role_are_exact() -> None:
    raw_data = load_character_record(str(CAESAR_ID))
    raw = load_raw_record(raw_data)
    assert raw.name == "凯撒"
    assert raw.code_name == "Caesar"
    assert raw.specialty == "防护"
    assert raw.element == "物理"
    assert raw.rarity == 4
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1071.json"
    assert not raw.potential_details

    panel = character_base_stats(CAESAR_ID)
    assert panel.hp.value == pytest.approx(9526.2299)
    assert panel.attack.value == pytest.approx(711.6899)
    assert panel.defense.value == pytest.approx(753.862)
    assert panel.impact.value == pytest.approx(123.0)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    assert panel.anomaly_mastery.value == pytest.approx(87.0)

    assert SIGNATURE_WENGINE_BY_CHARACTER[CAESAR_ID] == WEngineId("wengine:14107")
    assert load_wengine_raw_record("wengine:14107").icon == "Weapon_S_1071"
    registration = registration_for(CAESAR_ID)
    assert registration.role is CharacterRole.DEFENSE
    assert registration.role is not CharacterRole.VANGUARD
    catalog = {item.character_id: item for item in supported_character_catalog()}
    assert catalog["character:1071"].code_name == "Caesar"
    assert catalog["character:1071"].image_path == "/characters/IconRole25.webp"
    assert (Path(__file__).parents[2] / "frontend/public/characters/IconRole25.webp").is_file()


def test_caesar_direct_curves_keep_skill_list_move_and_raw_curve_namespaces_separate() -> None:
    raw = load_raw_record(load_character_record(str(CAESAR_ID)))
    config = CaesarCompileConfig()
    definition = compile_caesar(config, raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert entries["move-entry:character:1071:basic-slash-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(0.945)
    assert entries["move-entry:character:1071:basic-slash-stage3-derived"].multiplier_variants[0].multiplier.value.value == pytest.approx(2.372)
    assert entries["move-entry:character:1071:dash-attack"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.25)
    assert entries["move-entry:character:1071:ultimate-tyrant-blow"].multiplier_variants[0].multiplier.value.value == pytest.approx(40.253)
    assert entries["move-entry:character:1071:ex-super-strong-shield-bash"].damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})
    assert entries["move-entry:character:1071:assist-strike-support-edge"].damage_tags == frozenset({DamageTag.ASSIST})

    explicit_12 = CaesarCompileConfig(
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
        core_level=7,
        cinema_level=3,
    )
    at_14 = compile_caesar(explicit_12, raw)
    ult14 = next(item for item in at_14.move_entries if str(item.entry_id) == "move-entry:character:1071:ultimate-tyrant-blow")
    assert ult14.multiplier_variants[0].multiplier.value.value == pytest.approx(43.913)


def test_caesar_static_physical_anomaly_and_disorder_are_nocrit() -> None:
    anomaly = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload("move-entry:character:1071:physical-anomaly"),
    )
    disorder = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload("move-entry:character:1071:physical-disorder"),
    )
    assert anomaly.status_code == disorder.status_code == 200
    anomaly_event = _event(anomaly.json())
    disorder_event = _event(disorder.json())
    assert anomaly_event["damage_type"] == "anomaly"
    assert _node(anomaly_event, "anomaly.attribute.multiplier") == pytest.approx(7.13)
    assert anomaly_event["modes"]["expected"]["value"] == pytest.approx(anomaly_event["modes"]["non-crit"]["value"])
    assert disorder_event["damage_type"] == "disorder"
    assert _node(disorder_event, "disorder.total-multiplier") == pytest.approx(5.25)
    assert disorder_event["modes"]["expected"]["value"] == pytest.approx(disorder_event["modes"]["non-crit"]["value"])


def test_caesar_current_operator_target_moves_holder_atk_only_to_the_active_operator() -> None:
    caesar_rule = "rule:character:1071:core:shield-holder-attack"
    condition = "condition:caesar:shield-holder-attack-buff-active"
    for primary, team, move in (
        (
            "character:1021",
            ["character:1021", "character:1071"],
            "move-entry:character:1021:basic-cat-claw-1",
        ),
        (
            "character:1071",
            ["character:1071", "character:1021"],
            "move-entry:character:1071:ultimate-tyrant-blow",
        ),
    ):
        payload = _caesar_payload(
            move,
            primary=primary,
            team=team,
            formation=["character:1021", "character:1071"],
            conditions={condition: True},
            enabled_rules=[caesar_rule],
        )
        response = client.post("/api/v1/moves/calculate", json=payload)
        assert response.status_code == 200, response.text
        snapshots = {item["character_id"]: item["stats"] for item in response.json()["resolved_character_snapshots"]}
        assert snapshots[primary]["attack"] == pytest.approx(2000.0)
        other = next(item for item in team if item != primary)
        assert snapshots[other]["attack"] == pytest.approx(1000.0)

    disabled = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1021:basic-cat-claw-1",
            primary="character:1021",
            team=["character:1021", "character:1071"],
            formation=["character:1021", "character:1071"],
            conditions={condition: True},
        ),
    )
    assert disabled.status_code == 200, disabled.text
    assert disabled.json()["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(1000.0)


def test_caesar_c2_attack_increase_and_cinema1_enemy_resistance_are_separate() -> None:
    current_holder_attack = "condition:caesar:shield-holder-attack-buff-active"
    shield_active = "condition:caesar:glory-shield-active"
    c2_rule = "rule:character:1071:cinema2:shield-holder-attack-increase"
    c1_rule = "rule:character:1071:cinema1:enemy-resistance-reduction"
    holder = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            cinema_level=2,
            conditions={current_holder_attack: True, shield_active: True},
            enabled_rules=[
                "rule:character:1071:core:shield-holder-attack",
                c2_rule,
            ],
        ),
    )
    assert holder.status_code == 200, holder.text
    assert holder.json()["resolved_character_snapshots"][0]["stats"]["attack"] == pytest.approx(2500.0)

    baseline = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            cinema_level=1,
            enemy_resistance=0.2,
        ),
    )
    reduced = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            cinema_level=1,
            enemy_resistance=0.2,
            conditions={"condition:caesar:cinema1-target-resistance-debuff-active": True},
            enabled_rules=[c1_rule],
        ),
    )
    assert baseline.status_code == reduced.status_code == 200
    assert _node(_event(baseline.json()), "resistance.region") == pytest.approx(0.8)
    assert _node(_event(reduced.json()), "resistance.region") == pytest.approx(0.95)


def test_caesar_cinema6_only_boosts_the_named_bashes_and_uses_current_self_crit_state() -> None:
    c6_rule = "rule:character:1071:cinema6:shield-bash-and-support-strike"
    bash = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ex-super-strong-shield-bash",
            cinema_level=6,
            enabled_rules=[c6_rule],
        ),
    )
    nonqualifying_ex = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ex-parry-counterattack",
            cinema_level=6,
            enabled_rules=[c6_rule],
        ),
    )
    assert bash.status_code == nonqualifying_ex.status_code == 200
    bash_event = _event(bash.json())
    other_event = _event(nonqualifying_ex.json())
    assert _node(bash_event, "damage.normal-bonus") == pytest.approx(1.0)
    assert bash_event["modes"]["expected"]["value"] == pytest.approx(
        bash_event["modes"]["full-crit"]["value"]
    )
    assert _node(other_event, "damage.normal-bonus") == pytest.approx(0.0)

    panel_buff = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            cinema_level=6,
            conditions={"condition:caesar:cinema6-self-crit-buff-active": True},
            enabled_rules=["rule:character:1071:cinema6:self-crit-panel-buff"],
        ),
    )
    assert panel_buff.status_code == 200, panel_buff.text
    current_stats = panel_buff.json()["resolved_character_snapshots"][0]["stats"]
    assert current_stats["crit_rate"] == pytest.approx(0.35)
    assert current_stats["crit_damage"] == pytest.approx(1.1)


def test_caesar_impact_buff_uses_special_skill_effective_level() -> None:
    rule = "rule:character:1071:special:impact-conversion"
    condition = {"condition:caesar:impact-buff-active": True}
    level12 = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            conditions=condition,
            enabled_rules=[rule],
        ),
    )
    level14 = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            cinema_level=3,
            conditions=condition,
            enabled_rules=[rule],
        ),
    )
    assert level12.status_code == level14.status_code == 200
    assert level12.json()["resolved_character_snapshots"][0]["stats"]["impact"] == pytest.approx(147.6)
    assert level14.json()["resolved_character_snapshots"][0]["stats"]["impact"] == pytest.approx(150.06)


def test_caesar_additional_ability_uses_parry_capability_and_enemy_vulnerability_scope() -> None:
    eligible = compile_registered_definition(
        CAESAR_ID,
        {"core_level": 7, "cinema_level": 0},
        [CAESAR_ID, "character:1011"],
    )
    ineligible = compile_registered_definition(
        CAESAR_ID,
        {"core_level": 7, "cinema_level": 0},
        [CAESAR_ID, "character:1311"],
    )
    rule_id = "rule:character:1071:extra-ability:enemy-normal-vulnerability"
    eligible_rule = next(item for item in eligible.rule_items if str(item.rule_id) == rule_id)
    ineligible_rule = next(item for item in ineligible.rule_items if str(item.rule_id) == rule_id)
    assert eligible_rule.eligibility.value == "eligible"
    assert ineligible_rule.eligibility.value == "ineligible"

    base = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload("move-entry:character:1071:ultimate-tyrant-blow"),
    )
    vulnerable = client.post(
        "/api/v1/moves/calculate",
        json=_caesar_payload(
            "move-entry:character:1071:ultimate-tyrant-blow",
            team=["character:1071", "character:1011"],
            conditions={"condition:caesar:extra-ability-target-damage-debuff-active": True},
            enabled_rules=[rule_id],
        ),
    )
    assert base.status_code == vulnerable.status_code == 200
    assert _event(vulnerable.json())["modes"]["expected"]["value"] == pytest.approx(
        _event(base.json())["modes"]["expected"]["value"] * 1.25
    )
