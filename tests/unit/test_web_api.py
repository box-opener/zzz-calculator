from __future__ import annotations

from fastapi.testclient import TestClient

from web.api import app


client = TestClient(app)


def test_catalog_uses_production_ids_and_assets() -> None:
    response = client.get("/api/v1/characters")
    assert response.status_code == 200
    payload = response.json()
    assert {item["character_id"] for item in payload} == {
        "character:1311",
        "character:1431",
    }
    assert all(item["image_path"].startswith("/characters/") for item in payload)
    assert client.get("/characters/IconRole36.webp").status_code == 200


def test_definition_preview_returns_versioned_editor_view() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1311",
            "team_character_ids": ["character:1311", "character:1431"],
            "cinema_level": 6,
            "additional_ability_eligible": True,
            "condition_values": {
                "condition:astra:aria-active": True,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "presentation-v1"
    assert payload["character_id"] == "character:1311"
    assert payload["moves"]
    assert payload["rule_items"]


def test_invalid_requests_are_structured() -> None:
    invalid = client.post("/api/v1/definitions/preview", json={"character_id": "unknown"})
    assert invalid.status_code == 400
    assert invalid.json()["diagnostics"][0]["blocking"] is True

    invalid_calculation = client.post("/api/v1/moves/calculate", json={})
    assert invalid_calculation.status_code == 400
    assert invalid_calculation.json()["diagnostics"][0]["blocking"] is True


def test_root_static_mount_does_not_swallow_api_routes() -> None:
    assert client.get("/api/health").json() == {
        "status": "ok",
        "schema_version": "presentation-v1",
    }


def test_move_calculation_executes_all_three_display_modes() -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json={
            "primary_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "current_operator": "character:1431",
            "move_entry_id": "move-entry:ye:1431:basic-fast-1",
            "compile_configs": {
                "character:1431": {
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                    "enemy_stun_vulnerability_bonus": 1.5,
                }
            },
            "character_builds": {
                "character:1431": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1200.0,
                        "crit_rate": 0.65,
                        "crit_damage": 0.5,
                    },
                }
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2},
                "stun_vulnerability_bonus": 1.5,
            },
            "enabled_rule_item_ids": [],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload["totals"]) == {"non-crit", "expected", "full-crit"}
    assert payload["events"]
    assert set(payload["events"][0]["modes"]) == {
        "non-crit",
        "expected",
        "full-crit",
    }


def test_move_calculation_accepts_astra_as_cross_character_support() -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json={
            "primary_character_id": "character:1431",
            "supporting_character_ids": ["character:1311"],
            "team_character_ids": ["character:1431", "character:1311"],
            "current_operator": "character:1431",
            "move_entry_id": "move-entry:ye:1431:basic-fast-1",
            "compile_configs": {
                "character:1431": {
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                    "enemy_stun_vulnerability_bonus": 1.5,
                },
                "character:1311": {
                    "core_level": 1,
                    "cinema_level": 0,
                },
            },
            "condition_values": {
                "condition:astra:core-attack-buff-active": True,
            },
            "character_builds": {
                "character:1431": {"level": 60, "out_of_combat_stats": {"attack": 1200.0}},
                "character:1311": {"level": 60, "out_of_combat_stats": {"attack": 1500.0}},
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2},
                "stun_vulnerability_bonus": 1.5,
            },
            "enabled_rule_item_ids": [
                "rule:astra:1311:core-passive-self",
                "rule:astra:1311:core-passive-entry",
            ],
            "selected_trigger_inputs": [
                {
                    "input_id": "scenario-trigger:effect:astra:1311:core-entry-attack:actor",
                    "actor_id": "character:1431",
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recipients = {item["recipient_character_id"] for item in payload["panel_traces"]}
    assert recipients == {"character:1431", "character:1311"}
    assert payload["resolved_character_snapshots"]
