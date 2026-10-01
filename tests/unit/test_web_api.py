from __future__ import annotations

from pathlib import Path
from copy import deepcopy

import pytest
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


def _ye_primary_astra_support_payload(*, aria: bool) -> dict:
    ye_stats = {
        "hp": 10000.0,
        "attack": 1000.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0},
    }
    astra_stats = {**ye_stats, "element_damage_bonus": {"ether": 0.0}}
    return {
        "primary_character_id": "character:1431",
        "supporting_character_ids": ["character:1311"],
        "team_character_ids": ["character:1431", "character:1311"],
        "move_entry_id": "move-entry:ye:1431:assist-yuanshou",
        "compile_configs": {
            "character:1431": {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            },
            "character:1311": {"core_level": 1, "cinema_level": 0},
        },
        # Energy is intentionally explicit here so the comparison isolates
        # ARIA. The trigger actor is also explicit because this is a support
        # entry event, not a free-standing toggle.
        "condition_values": {
            "condition:astra:aria-active": aria,
            "condition:astra:energy-derived-active": True,
        },
        "parameter_values": {},
        "character_builds": {
            "character:1431": {"level": 60, "out_of_combat_stats": ye_stats},
            "character:1311": {"level": 60, "out_of_combat_stats": astra_stats},
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
        "enabled_rule_item_ids": (
            ["rule:astra:1311:extra-ability-entry"] if aria else []
        ),
        "selected_trigger_inputs": [
            {
                "input_id": "scenario-trigger:effect:astra:1311:extra-entry-tremolo:actor",
                "actor_id": "character:1431",
            },
            {
                "input_id": "scenario-trigger:effect:astra:1311:extra-entry-cluster:actor",
                "actor_id": "character:1431",
            },
        ]
        if aria
        else [],
        "rule_stack_counts": {},
    }


def _ye_primary_astra_aria_team_buff_payload(*, aria: bool) -> dict:
    """A production-shaped payload with ARIA as its only scenario gate."""

    payload = _ye_primary_astra_support_payload(aria=aria)
    payload["move_entry_id"] = "move-entry:ye:1431:basic-fast-1"
    payload["condition_values"] = {
        "condition:astra:aria-active": aria,
    }
    payload["enabled_rule_item_ids"] = (
        ["rule:astra:1311:aria-team-buff"] if aria else []
    )
    payload["selected_trigger_inputs"] = []
    return payload


def _astra_aria_payload(*, aria: bool, cinema_level: int = 0) -> dict:
    return {
        "primary_character_id": "character:1311",
        "team_character_ids": ["character:1311"],
        "move_entry_id": "move-entry:astra:1311:basic-interlude-1",
        "compile_configs": {
            "character:1311": {
                "core_level": 1,
                "cinema_level": cinema_level,
            }
        },
        "condition_values": {"condition:astra:aria-active": aria},
        "parameter_values": {},
        "character_builds": {
            "character:1311": {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 10000.0,
                    "attack": 1000.0,
                    "defense": 500.0,
                    "impact": 100.0,
                    "anomaly_mastery": 100.0,
                    "anomaly_proficiency": 100.0,
                    "energy_regen": 1.2,
                    "crit_rate": 0.5,
                    "crit_damage": 0.5,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"ether": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:ui",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"ether": 0.2},
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
        "character:1401",
        "character:1411",
        "character:1361",
    }
    assert all(item["image_path"].startswith("/characters/") for item in payload)
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "characters"
    assert (asset_root / "IconRole36.webp").is_file()
    assert (asset_root / "IconRole55.webp").is_file()
    assert (asset_root / "IconRole46.webp").is_file()
    assert (asset_root / "IconRole47.webp").is_file()
    assert (asset_root / "IconRole39.webp").is_file()


def test_calculation_accepts_a_primary_and_two_supporting_characters() -> None:
    payload = _valid_calculation_payload()
    primary = "character:1431"
    supports = ["character:1311", "character:1401"]
    payload["supporting_character_ids"] = supports
    payload["team_character_ids"] = [primary, *supports]
    payload["compile_configs"].update({
        "character:1311": {"core_level": 1, "cinema_level": 0},
        "character:1401": {"core_level": 1, "cinema_level": 0},
    })
    astra_build = deepcopy(payload["character_builds"][primary])
    astra_build["out_of_combat_stats"]["element_damage_bonus"] = {"ether": 0.0}
    alice_build = deepcopy(payload["character_builds"][primary])
    payload["character_builds"].update({
        "character:1311": astra_build,
        "character:1401": alice_build,
    })
    # Alice's mutually-exclusive Star Dance variants are intentionally all
    # false: she is only supporting this Ye calculation and her unselected
    # entry must not block the primary move.
    payload["condition_values"] = {
        "condition:alice:star-dance-charge-1": False,
        "condition:alice:star-dance-charge-2": False,
        "condition:alice:star-dance-charge-3": False,
        "condition:alice:physical-anomaly-active": True,
        "condition:alice:polar-assault-active": False,
        "condition:alice:victory-state-active": False,
    }
    payload["enemy"]["damage_resistance"]["ether"] = 0.2

    for character_id in [primary, *supports]:
        definition_response = client.post(
            "/api/v1/definitions/preview",
            json={
                "character_id": character_id,
                "team_character_ids": [primary, *supports],
                "compile_config": payload["compile_configs"][character_id],
            },
        )
        assert definition_response.status_code == 200, definition_response.text
        build_response = client.post(
            "/api/v1/builds/preview",
            json={"character_id": character_id, "level": 60, "drive_discs": []},
        )
        assert build_response.status_code == 200, build_response.text

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["events"]
    assert {item["character_id"] for item in result["resolved_character_snapshots"]} == {
        primary,
        *supports,
    }


def test_alice_attribute_anomaly_exposes_generated_strength_provenance() -> None:
    stats = {
        "hp": 10000.0,
        "attack": 1234.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 234.0,
        "energy_regen": 1.2,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.17},
    }
    response = client.post(
        "/api/v1/moves/calculate",
        json={
            "primary_character_id": "character:1401",
            "team_character_ids": ["character:1401"],
            "move_entry_id": "move-entry:alice:1401:physical-anomaly",
            "compile_configs": {"character:1401": {"core_level": 1, "cinema_level": 0}},
            "condition_values": {},
            "parameter_values": {},
            "character_builds": {"character:1401": {"level": 42, "out_of_combat_stats": stats}},
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
        },
    )

    assert response.status_code == 200, response.text
    event = response.json()["events"][0]
    trace = event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["level"] == 42
    assert trace["attack"] == 1234.0
    assert trace["anomaly_proficiency"] == 234.0
    assert trace["element_bonus"] == 0.17
    assert trace["normal_bonus"] == 0.0
    assert trace["mutation"] == 1.0
    assert trace["final_strength"] == pytest.approx(
        trace["level_coefficient"]
        * trace["anomaly_proficiency_factor"]
        * (1 + trace["element_bonus"] + trace["normal_bonus"])
        * trace["attack"]
        * trace["mutation"]
    )
    assert {item["source_label"] for item in trace["factors"]} >= {
        "角色等级系数",
        "有效异常精通",
        "对应属性增伤",
        "异化系数（当前实现）",
    }


def test_wengine_catalog_exposes_the_reviewed_wengine_validation_set() -> None:
    response = client.get("/api/v1/wengines")

    assert response.status_code == 200
    catalog = response.json()
    assert {item["wengine_id"] for item in catalog} == {
        "wengine:12006",
        "wengine:13103",
        "wengine:14102",
        "wengine:14104",
        "wengine:14119",
        "wengine:14120",
        "wengine:14121",
        "wengine:14124",
        "wengine:14131",
        "wengine:14143",
        "wengine:14145",
        "wengine:14149",
        "wengine:14136",
        "wengine:14140",
        "wengine:14141",
    }
    assert {item["specialty"] for item in catalog} == {"attack", "support", "anomaly", "stun"}
    assert (
        next(item for item in catalog if item["wengine_id"] == "wengine:14131")[
            "signature_character_id"
        ]
        == "character:1311"
    )
    assert all("rule_item_ids" not in item for item in catalog)
    assert {
        (item["wengine_id"], item["signature_character_id"])
        for item in catalog
        if item["signature_character_id"] is not None
    } >= {
        ("wengine:14136", "character:1361"),
        ("wengine:14140", "character:1401"),
        ("wengine:14141", "character:1411"),
    }


def test_drive_disc_catalog_and_editor_cover_the_frozen_thirty_sets() -> None:
    catalog_response = client.get("/api/v1/drive-discs")
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert len(catalog) == 30
    assert {item["set_id"] for item in catalog} >= {
        "drive-disc:31000",
        "drive-disc:34100",
        "drive-disc:34200",
    }
    assert all(
        item["two_piece_disposition"]
        in {"static-contribution", "calculation-rule", "ignored-non-damage"}
        and item["four_piece_disposition"] in {"calculation-rule", "ignored-non-damage"}
        for item in catalog
    )
    proto = next(item for item in catalog if item["set_id"] == "drive-disc:31900")
    assert proto["two_piece_disposition"] == "ignored-non-damage"
    assert "护盾" in proto["ignored_two_piece_reason"]
    asset_root = Path(__file__).parents[2] / "frontend" / "public" / "drive-discs"
    assert all(
        (asset_root / Path(item["icon_path"]).name).is_file() for item in catalog
    )

    preview = client.post(
        "/api/v1/drive-discs/preview",
        json={
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "discs": [],
            "condition_context": {},
        },
    )
    assert preview.status_code == 200
    payload = preview.json()
    assert [item["slot"] for item in payload["slot_schemas"]] == [1, 2, 3, 4, 5, 6]
    attack_flat = next(
        item for item in payload["substat_options"] if item["stat_key"] == "attack-flat"
    )
    assert attack_flat["value_per_roll"] == 19.0


def test_drive_disc_preview_exposes_owner_qualified_four_piece_rules() -> None:
    substats = [
        {"stat": "attack-flat", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    slot_two_substats = [
        {"stat": "attack-percent", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    response = client.post(
        "/api/v1/drive-discs/preview",
        json={
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "discs": [
                {
                    "slot": 1,
                    "set_id": "drive-disc:31000",
                    "main_stat": "hp-flat",
                    "substats": substats,
                },
                {
                    "slot": 2,
                    "set_id": "drive-disc:31000",
                    "main_stat": "attack-flat",
                    "substats": slot_two_substats,
                },
                {
                    "slot": 3,
                    "set_id": "drive-disc:31000",
                    "main_stat": "defense-flat",
                    "substats": substats,
                },
                {
                    "slot": 4,
                    "set_id": "drive-disc:31000",
                    "main_stat": "attack-percent",
                    "substats": substats,
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["set_counts"] == [{"set_id": "drive-disc:31000", "count": 4}]
    rule = payload["rule_items"][0]
    assert rule["source_type"] == "drive-disc"
    assert "owner:character_1431" in rule["rule_id"]
    assert rule["stack"] == {"default": 3, "minimum": 0, "maximum": 3}


def test_drive_disc_preview_preserves_partial_input_as_a_blocking_diagnostic() -> None:
    response = client.post(
        "/api/v1/drive-discs/preview",
        json={
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "discs": [
                {
                    "slot": 4,
                    "set_id": "drive-disc:31000",
                    "main_stat": None,
                    "substats": [],
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["diagnostics"]
    assert all(item["blocking"] for item in payload["diagnostics"])


def test_drive_disc_incomplete_input_blocks_formal_calculation() -> None:
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "base_stats": {
            "hp": 10000.0,
            "attack": 1200.0,
            "defense": 500.0,
            "impact": 100.0,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "energy_regen": 1.2,
            "crit_rate": 0.65,
            "crit_damage": 0.5,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0},
        },
        "drive_discs": [
            {
                "slot": 4,
                "set_id": "drive-disc:31000",
                "main_stat": None,
                "substats": [],
            }
        ],
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "requires four substats" in response.json()["diagnostics"][0]["message"]


def test_drive_disc_static_and_four_piece_rules_reach_move_execution() -> None:
    payload = _valid_calculation_payload()
    stats = {
        "hp": 10000.0,
        "attack": 1200.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": 0.65,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0},
    }
    substats = [
        {"stat": "attack-flat", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    slot_two_substats = [
        {"stat": "attack-percent", "roll_count": 2},
        {"stat": "crit-rate", "roll_count": 2},
        {"stat": "crit-damage", "roll_count": 2},
        {"stat": "penetration-flat", "roll_count": 2},
    ]
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "base_stats": stats,
        "drive_discs": [
            {
                "slot": 1,
                "set_id": "drive-disc:31000",
                "main_stat": "hp-flat",
                "substats": substats,
            },
            {
                "slot": 2,
                "set_id": "drive-disc:31000",
                "main_stat": "attack-flat",
                "substats": slot_two_substats,
            },
            {
                "slot": 3,
                "set_id": "drive-disc:31000",
                "main_stat": "defense-flat",
                "substats": substats,
            },
            {
                "slot": 4,
                "set_id": "drive-disc:31000",
                "main_stat": "attack-percent",
                "substats": substats,
            },
        ],
    }
    rule_id = "rule:drive-disc:31000:owner:character_1431:4pc:attack-stacks"
    payload["enabled_rule_item_ids"] = [rule_id]
    payload["rule_stack_counts"] = {rule_id: 2}

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    snapshot = result["resolved_character_snapshots"][0]
    assert snapshot["stats"]["attack"] == pytest.approx(2433.16)
    assert snapshot["stats"]["crit_rate"] == pytest.approx(0.922)
    assert any(
        item["source_type"] == "drive-disc-set"
        and item["contribution_id"].endswith(":2pc")
        for item in result["build_provenance"]
    )
    assert any(
        item["effect_id"].endswith(":attack") and item["source_type"] == "drive-disc"
        for item in result["panel_traces"]
    )


def test_equipment_calculation_uses_reviewed_character_base_stats_when_omitted() -> (
    None
):
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14143",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    stats = response.json()["resolved_character_snapshots"][0]["stats"]
    assert stats["attack"] == pytest.approx(1681.2102)
    assert stats["crit_rate"] == pytest.approx(0.194)
    assert stats["crit_damage"] == pytest.approx(0.98)


def test_wengine_preview_exposes_owner_qualified_rules_for_the_editor() -> None:
    response = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14131",
            "equipped_character_id": "character:1311",
            "team_character_ids": ["character:1431", "character:1311"],
            "level": 60,
            "refinement": 1,
            "condition_values": {},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["equipped_character_id"] == "character:1311"
    assert payload["rule_items"][0]["rule_id"] == (
        "rule:wengine:14131:owner:1311:team-damage"
    )
    assert payload["rule_items"][0]["source_type"] == "weapon"
    assert payload["scenario_conditions"][0]["editable"] is True


def test_wengine_preview_uses_resolved_external_static_condition_context() -> None:
    def preview(value: bool):
        return client.post(
            "/api/v1/wengines/preview",
            json={
                "wengine_id": "wengine:14143",
                "equipped_character_id": "character:1431",
                "team_character_ids": ["character:1431"],
                "condition_context": {
                    "condition:ye:mingxin-active": value,
                },
            },
        ).json()

    active = preview(True)
    inactive = preview(False)
    active_veil = next(
        item for item in active["rule_items"] if item["rule_id"].endswith(":veil")
    )
    inactive_veil = next(
        item for item in inactive["rule_items"] if item["rule_id"].endswith(":veil")
    )
    assert active_veil["availability"] == "available"
    assert inactive_veil["availability"] == "unavailable"
    assert all(
        item["condition_id"] != "condition:ye:mingxin-active"
        for item in active["scenario_conditions"]
    )


def test_wengine_preview_marks_impossible_owner_mechanics_ineligible() -> None:
    deep_sea = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14119",
            "equipped_character_id": "character:1431",
            "team_character_ids": ["character:1431"],
        },
    ).json()
    dash_rule = next(
        item
        for item in deep_sea["rule_items"]
        if item["rule_id"].endswith(":dash-crit-buff")
    )
    assert dash_rule["eligibility"] == "ineligible"

    dream = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:14145",
            "equipped_character_id": "character:1311",
            "team_character_ids": ["character:1311"],
        },
    ).json()
    assert dream["rule_items"][0]["eligibility"] == "ineligible"


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


def test_astra_aria_condition_controls_preview_availability_and_move_execution() -> None:
    previews = {
        aria: client.post(
            "/api/v1/definitions/preview",
            json={
                "character_id": "character:1311",
                "team_character_ids": ["character:1311", "character:1431"],
                "compile_config": {"core_level": 1, "cinema_level": 6},
                "condition_values": {"condition:astra:aria-active": aria},
            },
        ).json()
        for aria in (False, True)
    }
    false_rules = {item["rule_id"]: item for item in previews[False]["rule_items"]}
    true_rules = {item["rule_id"]: item for item in previews[True]["rule_items"]}
    aria_rule_ids = {
        "rule:astra:1311:aria-team-buff",
        "rule:astra:1311:finale-derived",
        "rule:astra:1311:extra-ability",
        "rule:astra:1311:extra-ability-entry",
        "rule:astra:1311:cinema2",
        "rule:astra:1311:cinema4",
        "rule:astra:1311:cinema6",
    }
    assert all(false_rules[item]["availability"] == "unavailable" for item in aria_rule_ids)
    assert all(
        true_rules[item]["availability"] == "available"
        for item in {
            "rule:astra:1311:aria-team-buff",
            "rule:astra:1311:cinema2",
            "rule:astra:1311:cinema4",
            "rule:astra:1311:cinema6",
        }
    )
    # ARIA is a separate prerequisite from energy: an ARIA-only RuleItem is
    # available, while an ARIA+energy RuleItem remains blocked until energy is
    # explicitly selected.
    assert true_rules["rule:astra:1311:finale-derived"]["availability"] == "blocked"
    assert true_rules["rule:astra:1311:extra-ability"]["availability"] == "blocked"
    assert true_rules["rule:astra:1311:extra-ability-entry"]["availability"] == "blocked"
    assert all(
        item["condition_id"] == "condition:astra:aria-active"
        for item in previews[True]["scenario_conditions"][:1]
    )

    false_result = client.post(
        "/api/v1/moves/calculate",
        json=_astra_aria_payload(aria=False),
    )
    true_result = client.post(
        "/api/v1/moves/calculate",
        json=_astra_aria_payload(aria=True),
    )
    assert false_result.status_code == true_result.status_code == 200
    assert false_result.json()["events"] == []
    assert true_result.json()["events"][0]["semantic_id"].endswith(
        "basic-interlude-1:main"
    )


def test_astra_aria_calculation_keeps_independent_rule_switch_and_trace_lanes() -> None:
    from core.presentation.calculation_service import _presentation_request, _scenario
    from core.presentation.registry import compile_registered_definition

    payload = _astra_aria_payload(aria=True, cinema_level=6)
    request_view = _presentation_request(payload)
    assert request_view.selected_condition_values["condition:astra:aria-active"] is True
    definition = compile_registered_definition(
        "character:1311",
        {"core_level": 1, "cinema_level": 6},
        ("character:1311",),
    )
    scenario = _scenario(
        payload,
        (definition,),
        definition.character_id,
        (definition.character_id,),
    )
    assert next(
        item for item in scenario.conditions
        if str(item.condition_id) == "condition:astra:aria-active"
    ).value is True

    enabled = "rule:astra:1311:cinema6"
    payload["enabled_rule_item_ids"] = [enabled]
    with_rule = client.post("/api/v1/moves/calculate", json=payload)
    assert with_rule.status_code == 200, with_rule.text
    with_trace = with_rule.json()["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:astra:1311:cinema6:multiplier"
        for item in with_trace["event_multiplier_modifiers"]
    )

    payload["enabled_rule_item_ids"] = []
    without_rule = client.post("/api/v1/moves/calculate", json=payload)
    assert without_rule.status_code == 200, without_rule.text
    without_trace = without_rule.json()["events"][0]["common_application_trace"]
    assert not any(
        item["effect_id"] == "effect:astra:1311:cinema6:multiplier"
        for item in without_trace["event_multiplier_modifiers"]
    )


def test_unrelated_character_preview_does_not_gain_astra_aria_condition() -> None:
    response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1431",
            "team_character_ids": ["character:1431"],
            "compile_config": {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            },
            "condition_values": {"condition:astra:aria-active": True},
        },
    )
    assert response.status_code == 200
    assert all(
        item["condition_id"] != "condition:astra:aria-active"
        for item in response.json()["scenario_conditions"]
    )


def test_production_ye_primary_astra_support_aria_changes_entry_trace_and_events() -> None:
    inactive = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_support_payload(aria=False),
    )
    active = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_support_payload(aria=True),
    )
    assert inactive.status_code == active.status_code == 200

    inactive_payload = inactive.json()
    active_payload = active.json()
    assert [item["semantic_id"] for item in inactive_payload["events"]] == [
        "damage:ye:1431:assist-yuanshou:main"
    ]
    assert [item["semantic_id"] for item in active_payload["events"]] == [
        "damage:ye:1431:assist-yuanshou:main",
        "event:astra:1311:entry-tremolo",
        "event:astra:1311:entry-cluster",
    ]
    entry_trace = active_payload["events"][0]["common_application_trace"]
    aria_rule = next(
        item
        for item in entry_trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:extra-ability-entry"
    )
    assert aria_rule["status"] == "matched"
    assert {item["status"] for item in aria_rule["effects"]} == {"matched"}
    assert {item["effect_id"] for item in aria_rule["effects"]} == {
        "effect:astra:1311:extra-entry-tremolo",
        "effect:astra:1311:extra-entry-cluster",
    }
    assert active_payload["totals"]["expected"]["value"] != inactive_payload[
        "totals"
    ]["expected"]["value"]


def test_production_ye_primary_astra_aria_team_buff_changes_damage_and_team_crit_panel() -> None:
    inactive = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_aria_team_buff_payload(aria=False),
    )
    active = client.post(
        "/api/v1/moves/calculate",
        json=_ye_primary_astra_aria_team_buff_payload(aria=True),
    )
    assert inactive.status_code == active.status_code == 200

    inactive_payload = inactive.json()
    active_payload = active.json()
    assert [item["semantic_id"] for item in inactive_payload["events"]] == [
        "damage:ye:1431:basic-fast-1:main"
    ]
    assert [item["semantic_id"] for item in active_payload["events"]] == [
        "damage:ye:1431:basic-fast-1:main"
    ]

    inactive_trace = inactive_payload["events"][0]["common_application_trace"]
    active_trace = active_payload["events"][0]["common_application_trace"]
    inactive_rule = next(
        item
        for item in inactive_trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:aria-team-buff"
    )
    active_rule = next(
        item
        for item in active_trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:aria-team-buff"
    )
    assert inactive_rule["status"] == "not-matched"
    assert active_rule["status"] == "matched"
    assert {item["status"] for item in active_rule["effects"]} == {"matched"}
    assert {item["effect_id"] for item in active_rule["effects"]} == {
        "effect:astra:1311:aria-team-damage",
        "effect:astra:1311:aria-team-crit-damage",
    }
    damage_modifiers = [
        item
        for item in active_trace["applied_modifiers"]
        if item["effect_id"] == "effect:astra:1311:aria-team-damage"
    ]
    assert len(damage_modifiers) == 1
    assert damage_modifiers[0]["modifier_path"] == "damage.normal-bonus"
    assert damage_modifiers[0]["value"] == pytest.approx(0.20)

    crit_panel_traces = [
        item
        for item in active_payload["panel_traces"]
        if item["effect_id"] == "effect:astra:1311:aria-team-crit-damage"
    ]
    assert {item["recipient_character_id"] for item in crit_panel_traces} == {
        "character:1431",
        "character:1311",
    }
    assert all(
        item["modifier_path"] == "character.current.crit-damage"
        for item in crit_panel_traces
    )
    assert all(
        item["resolved_value"] == pytest.approx(0.25)
        for item in crit_panel_traces
    )

    inactive_snapshots = {
        item["character_id"]: item
        for item in inactive_payload["resolved_character_snapshots"]
    }
    active_snapshots = {
        item["character_id"]: item
        for item in active_payload["resolved_character_snapshots"]
    }
    assert (
        inactive_snapshots["character:1431"]["stats"]["crit_damage"]
        == pytest.approx(0.5)
    )
    assert (
        inactive_snapshots["character:1311"]["stats"]["crit_damage"]
        == pytest.approx(0.5)
    )
    assert (
        active_snapshots["character:1431"]["stats"]["crit_damage"]
        == pytest.approx(0.75)
    )
    assert (
        active_snapshots["character:1311"]["stats"]["crit_damage"]
        == pytest.approx(0.75)
    )
    assert active_payload["totals"]["expected"]["value"] != inactive_payload[
        "totals"
    ]["expected"]["value"]


def test_production_aria_team_buff_rule_switch_is_independent_from_active_state() -> None:
    payload = _ye_primary_astra_aria_team_buff_payload(aria=True)
    enabled = client.post("/api/v1/moves/calculate", json=payload)
    payload["enabled_rule_item_ids"] = []
    disabled = client.post("/api/v1/moves/calculate", json=payload)
    assert enabled.status_code == disabled.status_code == 200
    enabled_payload = enabled.json()
    disabled_payload = disabled.json()
    enabled_trace = enabled_payload["events"][0]["common_application_trace"]
    disabled_trace = disabled_payload["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:astra:1311:aria-team-damage"
        for item in enabled_trace["applied_modifiers"]
    )
    assert not any(
        item["effect_id"] == "effect:astra:1311:aria-team-damage"
        for item in disabled_trace["applied_modifiers"]
    )
    assert not any(
        item["effect_id"] == "effect:astra:1311:aria-team-crit-damage"
        for item in disabled_payload["panel_traces"]
    )
    assert enabled_payload["totals"]["expected"]["value"] != disabled_payload[
        "totals"
    ]["expected"]["value"]


def test_production_aria_trace_explains_missing_trigger_without_faking_a_match() -> None:
    payload = _ye_primary_astra_support_payload(aria=True)
    payload["selected_trigger_inputs"] = []
    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    result = response.json()
    trace = result["events"][0]["common_application_trace"]
    aria_rule = next(
        item
        for item in trace["rule_matches"]
        if item["rule_id"] == "rule:astra:1311:extra-ability-entry"
    )
    assert aria_rule["status"] == "blocked"
    assert all(item["status"] == "blocked" for item in aria_rule["effects"])
    assert any(
        "no scenario trigger fact" in diagnostic["message"]
        for effect in aria_rule["effects"]
        for diagnostic in effect["diagnostics"]
    )


def test_invalid_requests_are_structured() -> None:
    invalid = client.post(
        "/api/v1/definitions/preview", json={"character_id": "unknown"}
    )
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
    assert payload["build_provenance"]
    assert all(
        item["source_type"] == "manual-panel" for item in payload["build_provenance"]
    )


def test_unselected_move_variant_returns_structured_blocking_diagnostic() -> None:
    payload = _valid_calculation_payload()
    payload["move_entry_id"] = "move-entry:ye:1431:basic-mingxin-zhanliuguang-mie"
    payload["compile_configs"]["character:1431"]["mingxin_active"] = True
    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    result = response.json()
    assert all(item["complete"] is False for item in result["totals"].values())
    messages = [item["message"] for item in result["diagnostics"]]
    assert any("明心境·斩流光 灭" in message for message in messages)
    assert any("condition:ye:variant:mingxin-zhanliuguang-mie" in message for message in messages)
    assert all(item["blocking"] is True for item in result["diagnostics"])


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
                "character:1431": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1200.0,
                        "crit_rate": 0.5,
                        "crit_damage": 0.5,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"physical": 0.0},
                    },
                },
                "character:1311": {
                    "level": 60,
                    "out_of_combat_stats": {
                        "attack": 1500.0,
                        "crit_rate": 0.5,
                        "crit_damage": 0.5,
                        "penetration_rate": 0.0,
                        "penetration_flat": 0.0,
                        "element_damage_bonus": {"ether": 0.0},
                    },
                },
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
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recipients = {item["recipient_character_id"] for item in payload["panel_traces"]}
    assert recipients == {"character:1431", "character:1311"}
    core_traces = [
        item
        for item in payload["panel_traces"]
        if item["effect_id"] == "effect:astra:1311:core-self-attack"
    ]
    assert len(core_traces) == 2
    assert payload["resolved_character_snapshots"]


def test_calculation_api_does_not_fill_missing_formal_inputs() -> None:
    import copy

    missing_enemy_state = _valid_calculation_payload()
    del missing_enemy_state["enemy"]["is_stunned"]
    response = client.post("/api/v1/moves/calculate", json=missing_enemy_state)
    assert response.status_code == 400
    assert "is_stunned" in response.json()["diagnostics"][0]["message"]

    missing_attack = _valid_calculation_payload()
    del missing_attack["character_builds"]["character:1431"]["out_of_combat_stats"][
        "attack"
    ]
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


def test_wengine_equipment_build_reaches_build_assembly_and_execution() -> None:
    payload = _valid_calculation_payload()
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14143",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.5,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"physical": 0.0},
        },
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14143:owner:1431:resistance-ignore",
    ]
    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    snapshot = response.json()["resolved_character_snapshots"][0]
    assert snapshot["stats"]["attack"] == 1743.0
    assert snapshot["stats"]["crit_damage"] == 0.98
    provenance = response.json()["build_provenance"]
    assert any(
        item["source_id"] == "wengine:14143"
        and item["stat"] == "attack"
        and item["layer"] == "white-value"
        for item in provenance
    )
    payload["enabled_rule_item_ids"] = []
    disabled_response = client.post("/api/v1/moves/calculate", json=payload)
    assert disabled_response.status_code == 200
    disabled_payload = disabled_response.json()
    assert (
        disabled_payload["resolved_character_snapshots"][0]["stats"]["attack"] == 1743.0
    )
    assert not any(
        item["effect_id"].endswith("resistance-ignore")
        for item in disabled_payload["events"][0]["common_application_trace"][
            "applied_modifiers"
        ]
    )


def test_astra_signature_wengine_adds_team_damage_from_equipment_build() -> None:
    payload = _valid_calculation_payload()
    payload["supporting_character_ids"] = ["character:1311"]
    payload["team_character_ids"] = ["character:1431", "character:1311"]
    payload["compile_configs"]["character:1311"] = {
        "core_level": 1,
        "cinema_level": 0,
    }
    payload["character_builds"]["character:1311"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14131",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.5,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"ether": 0.0},
        },
    }
    payload["enemy"]["damage_resistance"]["ether"] = 0.2
    payload["condition_values"] = {
        "condition:wengine:14131:owner:1311:damage-buff-active": True,
    }
    payload["enabled_rule_item_ids"] = ["rule:wengine:14131:owner:1311:team-damage"]
    payload["rule_stack_counts"] = {"rule:wengine:14131:owner:1311:team-damage": 2}

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    event_trace = response.json()["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:wengine:14131:owner:1311:team-damage"
        and item["value"] == 0.2
        for item in event_trace["applied_modifiers"]
    )


def test_ye_signature_wengine_uses_the_existing_mingxin_condition_for_veil_effects() -> (
    None
):
    payload = _valid_calculation_payload()
    payload["compile_configs"]["character:1431"]["mingxin_active"] = True
    payload["character_builds"]["character:1431"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14143",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "base_stats": {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.5,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"physical": 0.0},
        },
    }
    payload["enabled_rule_item_ids"] = [
        "rule:wengine:14143:owner:1431:resistance-ignore",
        "rule:wengine:14143:owner:1431:veil",
    ]

    response = client.post("/api/v1/moves/calculate", json=payload)

    assert response.status_code == 200
    event_trace = response.json()["events"][0]["common_application_trace"]
    assert any(
        item["effect_id"] == "effect:wengine:14143:owner:1431:veil-damage"
        for item in event_trace["applied_modifiers"]
    )
    assert any(
        item["effect_id"] == "effect:wengine:14143:owner:1431:veil-crit-damage"
        for item in response.json()["panel_traces"]
    )
    assert all(
        item["source_type"] == "weapon"
        for item in response.json()["panel_traces"]
        if item["effect_id"].startswith("effect:wengine:14143:")
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
