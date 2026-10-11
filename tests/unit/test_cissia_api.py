from __future__ import annotations

import json

import pytest

from web.api import calculate_move as calculate_move_api
from web.api import preview_build as preview_build_api
from web.api import preview_definition as preview_definition_api
from web.api import preview_wengine as preview_wengine_api


CISSIA = "character:1521"


def _payload(
    *,
    move_entry_id: str,
    cinema_level: int = 0,
    energy_regen: float = 1.2,
    conditions: dict[str, bool] | None = None,
    enabled_rules: list[str] | None = None,
    parameters: dict[str, int] | None = None,
    stacks: dict[str, int] | None = None,
) -> dict:
    return {
        "primary_character_id": CISSIA,
        "supporting_character_ids": [],
        "team_character_ids": [CISSIA],
        "formation_character_ids": [CISSIA],
        "move_entry_id": move_entry_id,
        "compile_configs": {
            CISSIA: {"core_level": 7, "cinema_level": cinema_level},
        },
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "character_builds": {
            CISSIA: {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 10000.0,
                    "attack": 1000.0,
                    "defense": 800.0,
                    "impact": 100.0,
                    "crit_rate": 0.5,
                    "crit_damage": 0.5,
                    "anomaly_mastery": 100.0,
                    "anomaly_proficiency": 100.0,
                    "energy_regen": energy_regen,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"electric": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:cissia-api-test",
            "level": 70,
            "initial_defense": 794.0,
            "damage_resistance": {"electric": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": enabled_rules or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": stacks or {},
    }


def _json_response(response) -> dict:
    assert response.status_code == 200, response.body.decode("utf-8")
    return json.loads(response.body)


def _applied_values(event: dict, effect_id: str) -> list[float]:
    return [
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["effect_id"] == effect_id
    ]


def test_cissia_preview_defaults_and_additional_ability_roster_rule() -> None:
    solo = _json_response(
        preview_definition_api(
            {"character_id": CISSIA, "team_character_ids": [CISSIA]}
        )
    )
    stun = _json_response(
        preview_definition_api(
            {
                "character_id": CISSIA,
                "team_character_ids": [CISSIA, "character:1511"],
            }
        )
    )
    electric = _json_response(
        preview_definition_api(
            {
                "character_id": CISSIA,
                "team_character_ids": [CISSIA, "character:1221"],
            }
        )
    )
    unrelated = _json_response(
        preview_definition_api(
            {
                "character_id": CISSIA,
                "team_character_ids": [CISSIA, "character:1311"],
            }
        )
    )

    fields = {item["field_id"]: item["value"] for item in solo["compile_config_fields"]}
    assert fields["core_level"] == 7
    assert fields["cinema_level"] == 0
    assert fields["skill_level:ultimate"] == 12

    def eligibility(view: dict) -> str:
        return next(
            item["eligibility"]
            for item in view["rule_items"]
            if item["rule_id"] == "rule:character:1521:extra:toxin-team-crit-damage"
        )

    assert eligibility(solo) == "ineligible"
    assert eligibility(stun) == "eligible"
    assert eligibility(electric) == "eligible"
    assert eligibility(unrelated) == "ineligible"


def test_cissia_signature_is_available_in_build_and_wengine_previews() -> None:
    build = _json_response(
        preview_build_api(
            {
                "character_id": CISSIA,
                "team_character_ids": [CISSIA],
                "level": 60,
                "wengine_id": "wengine:14152",
                "wengine_level": 60,
                "wengine_refinement": 1,
                "drive_discs": [],
            }
        )
    )
    weapon = _json_response(
        preview_wengine_api(
            {
                "wengine_id": "wengine:14152",
                "equipped_character_id": CISSIA,
                "team_character_ids": [CISSIA],
                "level": 60,
                "refinement": 1,
            }
        )
    )

    assert build["character_id"] == CISSIA
    assert build["display_name"] == "希希芙"
    assert build["out_of_combat_stats"]["energy_regen"] > build["base_stats"]["energy_regen"]
    assert weapon["equipped_character_id"] == CISSIA
    assert weapon["display_name"] == "鳞齿寻踪"
    assert weapon["rarity"] == "S"
    assert any(
        item["rule_id"] == "rule:wengine:14152:owner:1521:crit-rate"
        for item in weapon["rule_items"]
    )


def test_cissia_initial_energy_regen_cap_and_c1_resistance_lanes_reach_api() -> None:
    payload = _payload(
        move_entry_id="move-entry:character:1521:basic-snake-kiss",
        cinema_level=1,
        energy_regen=20.0,
        conditions={
            "condition:cissia:snake-shadow-available": True,
            "condition:cissia:toxin-active-or-recent": True,
        },
        enabled_rules=[
            "rule:character:1521:core:bone-erosion-extra-ratio",
            "rule:character:1521:core:toxin-electric-defense-ignore",
            "rule:character:1521:cinema1:core-defense-ignore-increase",
            "rule:character:1521:cinema1:electric-resistance-ignore",
        ],
        stacks={"rule:character:1521:core:toxin-electric-defense-ignore": 1},
    )
    result = _json_response(calculate_move_api(payload))

    assert result["totals"]["expected"]["complete"] is True
    assert result["resolved_character_snapshots"][0]["stats"]["energy_regen"] == 20.0
    parent, bone = result["events"]
    assert _applied_values(parent, "effect:character:1521:core:electric-defense-ignore") == pytest.approx([0.25])
    assert _applied_values(parent, "effect:character:1521:cinema1:core-defense-ignore-increase") == pytest.approx([0.10])
    assert _applied_values(parent, "effect:character:1521:cinema1:team-electric-resistance-ignore") == pytest.approx([0.05])
    assert _applied_values(bone, "effect:character:1521:cinema1:team-electric-resistance-ignore") == pytest.approx([0.05])
    assert _applied_values(bone, "effect:character:1521:cinema1:bone-electric-resistance-ignore") == pytest.approx([0.10])
    assert next(
        item["value"]
        for item in bone["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.skill-multiplier"
    ) == pytest.approx(5.894)

    disabled_core = dict(payload)
    disabled_core["enabled_rule_item_ids"] = [
        "rule:character:1521:cinema1:core-defense-ignore-increase",
        "rule:character:1521:cinema1:electric-resistance-ignore",
    ]
    without_core = _json_response(calculate_move_api(disabled_core))
    assert not _applied_values(
        without_core["events"][0],
        "effect:character:1521:cinema1:core-defense-ignore-increase",
    )
    assert not _applied_values(
        without_core["events"][0],
        "effect:character:1521:core:electric-defense-ignore",
    )


def test_cissia_cinema6_api_creates_one_bone_for_ex_parent_and_extra_hit() -> None:
    payload = _payload(
        move_entry_id="move-entry:character:1521:ex-special",
        cinema_level=6,
        conditions={"condition:cissia:cinema6-mark-proc-active": True},
        enabled_rules=[
            "rule:character:1521:skill:ex-special-extra-hit",
            "rule:character:1521:cinema6:team-bone-erosion",
        ],
        parameters={"parameter:cissia:ex-special-extra-hit-count": 3},
    )
    result = _json_response(calculate_move_api(payload))

    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 3
    assert sum("ex-special-extra-hit" in item["semantic_id"] for item in result["events"]) == 1
    assert sum("cinema6-bone-erosion" in item["semantic_id"] for item in result["events"]) == 1
    ex_extra = next(item for item in result["events"] if "ex-special-extra-hit" in item["semantic_id"])
    assert ex_extra["repeat_count"] == 3
