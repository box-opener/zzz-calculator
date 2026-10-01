from __future__ import annotations

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from web.api import app


client = TestClient(app)

_DEFENSE_RULE = "rule:wengine:14136:owner:1361:defense-reduction"
_DEFENSE_CONDITION = "condition:wengine:14136:owner:1361:defense-reduction-active"


def _stats(element: str, *, attack: float = 1000.0) -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: 0.0},
    }


def _trigger_build(*, refinement: int = 1) -> dict[str, object]:
    return {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14136",
        "wengine_level": 60,
        "wengine_refinement": refinement,
        "base_stats": _stats("electric"),
        "drive_discs": [],
    }


def _payload(
    *,
    primary: str,
    move_entry_id: str,
    primary_build: dict[str, object],
    compile_configs: dict[str, dict[str, object]],
    supporting: tuple[str, ...] = (),
    supporting_builds: dict[str, dict[str, object]] | None = None,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (_DEFENSE_RULE,),
) -> dict[str, object]:
    team = (primary, *supporting)
    builds = {primary: primary_build, **(supporting_builds or {})}
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": condition_values or {_DEFENSE_CONDITION: True},
        "parameter_values": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:spectral-gaze-scope",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {
                "physical": 0.2,
                "electric": 0.2,
                "ether": 0.2,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _defense_value(result: dict[str, object]) -> float:
    breakdown = result["events"][0]["modes"]["expected"]["calculation_breakdown"]  # type: ignore[index]
    return next(
        item["value"]
        for item in breakdown
        if item["node"] == "defense.enemy-current-effective"
    )


@pytest.mark.parametrize(
    ("primary", "move", "compile_configs", "supporting", "supporting_builds"),
    (
        (
            "character:1361",
            "move-entry:trigger:1361:basic-concerto-sniping",
            {"character:1361": {"core_level": 1, "cinema_level": 0}},
            (),
            {},
        ),
        (
            "character:1361",
            "move-entry:trigger:1361:basic-cold-chamber-1",
            {"character:1361": {"core_level": 1, "cinema_level": 0}},
            (),
            {},
        ),
        (
            "character:1431",
            "move-entry:ye:1431:basic-fast-1",
            {
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                },
                "character:1361": {"core_level": 1, "cinema_level": 0},
            },
            ("character:1361",),
            {"character:1361": _trigger_build()},
        ),
        (
            "character:1431",
            "move-entry:ye:1431:ultimate-zhuyunjingting",
            {
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": True,
                    "entry_move_uses_linren": True,
                },
                "character:1361": {"core_level": 1, "cinema_level": 0},
            },
            ("character:1361",),
            {"character:1361": _trigger_build()},
        ),
    ),
)
def test_active_spectral_gaze_defense_debuff_benefits_all_following_damage(
    primary: str,
    move: str,
    compile_configs: dict[str, dict[str, object]],
    supporting: tuple[str, ...],
    supporting_builds: dict[str, dict[str, object]],
) -> None:
    if primary == "character:1361":
        primary_build = _trigger_build()
        condition_values = {
            _DEFENSE_CONDITION: True,
            "condition:trigger:follow-up-active": True,
        }
    else:
        primary_build = {
            "level": 60,
            "out_of_combat_stats": _stats("physical"),
        }
        condition_values = {_DEFENSE_CONDITION: True}
    result = _calculate(
        _payload(
            primary=primary,
            move_entry_id=move,
            primary_build=primary_build,
            compile_configs=compile_configs,
            supporting=supporting,
            supporting_builds=supporting_builds,
            condition_values=condition_values,
        )
    )
    assert _defense_value(result) == pytest.approx(750.0)


def test_spectral_gaze_state_or_rule_disabled_removes_defense_debuff() -> None:
    base = _payload(
        primary="character:1361",
        move_entry_id="move-entry:trigger:1361:basic-concerto-sniping",
        primary_build=_trigger_build(),
        compile_configs={"character:1361": {"core_level": 1, "cinema_level": 0}},
        condition_values={
            _DEFENSE_CONDITION: False,
            "condition:trigger:follow-up-active": True,
        },
    )
    state_off = _calculate(base)
    assert _defense_value(state_off) == pytest.approx(1000.0)
    disabled = deepcopy(base)
    disabled["enabled_rule_item_ids"] = []
    disabled_result = _calculate(disabled)
    assert _defense_value(disabled_result) == pytest.approx(1000.0)


def test_spectral_gaze_refinement_five_uses_forty_percent_reduction() -> None:
    result = _calculate(
        _payload(
            primary="character:1361",
            move_entry_id="move-entry:trigger:1361:basic-concerto-sniping",
            primary_build=_trigger_build(refinement=5),
            compile_configs={"character:1361": {"core_level": 1, "cinema_level": 0}},
            condition_values={
                _DEFENSE_CONDITION: True,
                "condition:trigger:follow-up-active": True,
            },
        )
    )
    assert _defense_value(result) == pytest.approx(600.0)


def test_spectral_gaze_capability_eligibility_cannot_be_forced_by_enabled_rule() -> None:
    invalid_build = _trigger_build()
    invalid_build["base_stats"] = _stats("physical")
    payload = _payload(
        primary="character:1401",
        move_entry_id="move-entry:alice:1401:basic-star-opera-1",
        primary_build=invalid_build,
        compile_configs={"character:1401": {"core_level": 1, "cinema_level": 0}},
        condition_values={
            "condition:wengine:14136:owner:1401:defense-reduction-active": True
        },
        enabled_rule_item_ids=(
            "rule:wengine:14136:owner:1401:defense-reduction",
        ),
    )
    result = _calculate(payload)
    assert _defense_value(result) == pytest.approx(1000.0)


def test_spectral_gaze_stacks_with_an_independent_defense_reduction() -> None:
    payload = _payload(
        primary="character:1361",
        move_entry_id="move-entry:trigger:1361:basic-concerto-sniping",
        primary_build=_trigger_build(),
        compile_configs={
            "character:1361": {"core_level": 1, "cinema_level": 0},
            "character:1401": {"core_level": 1, "cinema_level": 1},
        },
        supporting=("character:1401",),
        supporting_builds={
            "character:1401": {
                "level": 60,
                "out_of_combat_stats": _stats("physical"),
            }
        },
        condition_values={
            _DEFENSE_CONDITION: True,
            "condition:trigger:follow-up-active": True,
        },
        enabled_rule_item_ids=(
            _DEFENSE_RULE,
            "rule:alice:1401:cinema1",
        ),
    )
    result = _calculate(payload)
    assert _defense_value(result) == pytest.approx(550.0)
