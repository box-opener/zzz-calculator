from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from web.api import app


client = TestClient(app)


def _valid_calculation_payload() -> dict:
    return {
        "primary_character_id": "character:1431",
        "team_character_ids": ["character:1431"],
        "move_entry_id": "move-entry:ye:1431:basic-fast-1",
        "compile_configs": {
            "character:1431": {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            }
        },
        "condition_values": {},
        "parameter_values": {},
        "character_builds": {
            "character:1431": {
                "level": 60,
                "out_of_combat_stats": {
                    "attack": 1200.0,
                    "crit_rate": 0.65,
                    "crit_damage": 0.5,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"physical": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:ui",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def test_catalog_uses_production_ids_and_assets() -> None:
    response = client.get("/api/v1/characters")
    assert response.status_code == 200
    payload = response.json()
    assert {item["character_id"] for item in payload} == {
        "character:1311",
        "character:1431",
    }
    assert all(item["image_path"].startswith("/characters/") for item in payload)
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "characters"
    assert (asset_root / "IconRole36.webp").is_file()
    assert (asset_root / "IconRole55.webp").is_file()


def test_definition_preview_returns_versioned_editor_view() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1311",
            "team_character_ids": ["character:1311", "character:1431"],
            "compile_config": {
                "core_level": 1,
                "cinema_level": 6,
            },
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
    field_ids = {item["field_id"] for item in payload["compile_config_fields"]}
    assert {"core_level", "cinema_level"}.issubset(field_ids)
    assert "additional_ability_eligible" not in field_ids


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
            "move_entry_id": "move-entry:ye:1431:basic-fast-1",
            "compile_configs": {
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                }
            },
            "character_builds": {
                "character:1431": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1200.0,
                        "crit_rate": 0.65,
                        "crit_damage": 0.5,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"physical": 0.0},
                    },
                }
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2, "ether": 0.2},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
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
            "move_entry_id": "move-entry:ye:1431:basic-fast-1",
            "compile_configs": {
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
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
                "character:1431": {"level": 60, "out_of_combat_stats": {"attack": 1200.0, "crit_rate": 0.5, "crit_damage": 0.5, "penetration_rate": 0.0, "penetration_flat": 0.0, "element_damage_bonus": {"physical": 0.0}}},
                "character:1311": {"level": 60, "out_of_combat_stats": {"attack": 1500.0, "crit_rate": 0.5, "crit_damage": 0.5, "penetration_rate": 0.0, "penetration_flat": 0.0, "element_damage_bonus": {"ether": 0.0}}},
            },
            "enemy": {
                "enemy_id": "enemy:ui",
                "level": 60,
                "initial_defense": 1000.0,
                "damage_resistance": {"physical": 0.2, "ether": 0.2},
                "damage_reduction": 0.0,
                "stun_vulnerability_bonus": 1.5,
                "is_stunned": False,
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


def test_calculation_api_does_not_fill_missing_formal_inputs() -> None:
    import copy

    missing_enemy_state = _valid_calculation_payload()
    del missing_enemy_state["enemy"]["is_stunned"]
    response = client.post("/api/v1/moves/calculate", json=missing_enemy_state)
    assert response.status_code == 400
    assert "is_stunned" in response.json()["diagnostics"][0]["message"]

    missing_attack = _valid_calculation_payload()
    del missing_attack["character_builds"]["character:1431"]["out_of_combat_stats"]["attack"]
    response = client.post("/api/v1/moves/calculate", json=missing_attack)
    assert response.status_code == 400
    assert "attack" in response.json()["diagnostics"][0]["message"]

    mismatched_operator = copy.deepcopy(_valid_calculation_payload())
    mismatched_operator["current_operator"] = "character:1311"
    response = client.post("/api/v1/moves/calculate", json=mismatched_operator)
    assert response.status_code == 400
    assert "primary_character_id" in response.json()["diagnostics"][0]["message"]


def test_skill_level_and_integer_parameter_inputs_reach_compiler_and_scenario() -> None:
    payload = _valid_calculation_payload()
    payload["move_entry_id"] = "move-entry:ye:1431:basic-cloud"
    payload["compile_configs"]["character:1431"]["skill_levels"] = {
        "basic-attack": 14,
    }
    payload["parameter_values"] = {
        "parameter:ye:flowing-cloud-sword-count": 5,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200
    event = response.json()["events"][0]
    assert event["repeat_count"] == 5
    assert any(
        item["node"] == "damage.skill-multiplier"
        and abs(item["value"] - 2.558) < 1e-9
        for item in event["modes"]["expected"]["calculation_breakdown"]
    )


def test_team_ids_must_match_compiled_primary_and_supporting_definitions() -> None:
    payload = _valid_calculation_payload()
    payload["supporting_character_ids"] = ["character:1311"]
    payload["compile_configs"]["character:1311"] = {
        "core_level": 1,
        "cinema_level": 0,
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "exactly equal" in response.json()["diagnostics"][0]["message"]


def test_unspecified_trigger_is_omitted_not_encoded_as_empty_actor() -> None:
    payload = _valid_calculation_payload()
    payload["selected_trigger_inputs"] = [
        {
            "input_id": "scenario-trigger:effect:test:actor",
            "actor_id": "",
        }
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "unspecified trigger" in response.json()["diagnostics"][0]["message"]
