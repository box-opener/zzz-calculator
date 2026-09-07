from __future__ import annotations

from fastapi.testclient import TestClient

from core.application.equipment.wengine import (
    WENGINE_ALICE_ID,
    WENGINE_TRIGGER_ID,
    WENGINE_YUZUHA_ID,
)
from web.api import app


client = TestClient(app)


def _stats(element: str) -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": 1000.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 80.0,
        "anomaly_proficiency": 130.0,
        "energy_regen": 1.2,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: 0.0},
    }


def _payload(
    *,
    primary: str,
    move: str,
    element: str,
    primary_build: dict[str, object],
    supporting: tuple[str, ...] = (),
    supporting_builds: dict[str, dict[str, object]] | None = None,
    conditions: dict[str, bool] | None = None,
    enabled: list[str] | None = None,
    enemy_resistances: dict[str, float] | None = None,
) -> dict[str, object]:
    team = (primary, *supporting)
    builds = {primary: primary_build}
    builds.update(supporting_builds or {})
    resistances = enemy_resistances or {element: 0.2}
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move,
        "compile_configs": {
            character_id: {"core_level": 1, "cinema_level": 0}
            for character_id in team
        },
        "condition_values": conditions or {},
        "parameter_values": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:signature-golden",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": resistances,
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": enabled or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def test_alice_signature_applies_to_current_polar_anomaly_calculation() -> None:
    weapon_rule = "rule:wengine:14140:owner:1401:physical-damage"
    mastery_rule = "rule:wengine:14140:owner:1401:anomaly-mastery"
    payload = _payload(
        primary="character:1401",
        move="move-entry:alice:1401:polar-assault",
        element="physical",
        primary_build={
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": str(WENGINE_ALICE_ID),
            "wengine_level": 60,
            "wengine_refinement": 1,
            "drive_discs": [],
        },
        conditions={
            "condition:alice:polar-assault-active": True,
            "condition:wengine:14140:owner:1401:strong-assault-active": True,
        },
        enabled=[mastery_rule, weapon_rule],
    )

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    event = result["events"][0]
    assert event["modes"]["expected"]["status"] == "calculated"
    assert any(
        trace["effect_id"] == "effect:wengine:14140:owner:1401:anomaly-mastery"
        and trace["resolved_value"] == 60.0
        for trace in result["panel_traces"]
    )
    assert any(
        modifier["effect_id"] == "effect:wengine:14140:owner:1401:physical-damage"
        and modifier["value"] == 0.4
        for modifier in event["common_application_trace"]["applied_modifiers"]
    )


def test_yuzuha_signature_team_anomaly_proficiency_changes_alice_polar_damage() -> None:
    weapon_rule = "rule:wengine:14141:owner:1411:team-anomaly-proficiency"
    payload = _payload(
        primary="character:1401",
        move="move-entry:alice:1401:polar-assault",
        element="physical",
        primary_build={
            "level": 60,
            "out_of_combat_stats": _stats("physical"),
        },
        supporting=("character:1411",),
        supporting_builds={
            "character:1411": {
                "level": 60,
                "build_mode": "equipment-build",
                "wengine_id": str(WENGINE_YUZUHA_ID),
                "wengine_level": 60,
                "wengine_refinement": 1,
                "drive_discs": [],
            }
        },
        conditions={
            "condition:alice:polar-assault-active": True,
            "condition:wengine:14141:owner:1411:team-anomaly-proficiency-active": True,
        },
        enabled=[weapon_rule],
    )

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    alice_snapshot = next(
        item
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    assert alice_snapshot["stats"]["anomaly_proficiency"] == 190.0
    assert result["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert len(result["panel_traces"]) == 2


def test_trigger_signature_additional_attack_identity_applies_enemy_defense_debuff() -> None:
    weapon_rule = "rule:wengine:14136:owner:1361:defense-reduction"
    payload = _payload(
        primary="character:1361",
        move="move-entry:trigger:1361:basic-concerto-sniping",
        element="electric",
        primary_build={
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": str(WENGINE_TRIGGER_ID),
            "wengine_level": 60,
            "wengine_refinement": 1,
            "drive_discs": [],
        },
        conditions={"condition:trigger:follow-up-active": True},
        enabled=[weapon_rule],
    )

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    breakdown = result["events"][0]["modes"]["expected"]["calculation_breakdown"]
    assert next(
        item["value"]
        for item in breakdown
        if item["node"] == "defense.enemy-reduction"
    ) == 0.25
