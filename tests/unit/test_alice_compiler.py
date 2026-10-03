from __future__ import annotations

import pytest

from core.presentation.calculation_service import calculate_payload


_ALICE_ID = "character:1401"
_YE_ID = "character:1431"
_C1_RULE_ID = "rule:alice:1401:cinema1"
_C4_RULE_ID = "rule:alice:1401:cinema4"
_C1_EFFECT_ID = "effect:character:1401:cinema1:enemy-defense"


def _stats(element: str = "physical") -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": 1000.0,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": 0.0,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: 0.0},
    }


def _payload(
    *,
    primary: str = _ALICE_ID,
    supporting: tuple[str, ...] = (),
    move_entry_id: str = "move-entry:alice:1401:physical-anomaly",
    cinema_level: int = 1,
    enabled_rule_item_ids: tuple[str, ...] = (_C1_RULE_ID,),
) -> dict[str, object]:
    team = (primary, *supporting)
    compile_configs: dict[str, dict[str, object]] = {
        _ALICE_ID: {"core_level": 1, "cinema_level": cinema_level},
    }
    builds: dict[str, dict[str, object]] = {
        _ALICE_ID: {"level": 60, "out_of_combat_stats": _stats()},
    }
    if _YE_ID in team:
        compile_configs[_YE_ID] = {
            "core_level": 1,
            "cinema_level": 0,
            "mingxin_active": False,
            "entry_move_uses_linren": False,
        }
        builds[_YE_ID] = {
            "level": 60,
            "out_of_combat_stats": _stats(),
        }
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": {},
        "parameter_values": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:alice-c1-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _event(result: dict[str, object]) -> dict[str, object]:
    return result["events"][0]  # type: ignore[index,return-value]


def _node(event: dict[str, object], name: str) -> dict[str, object]:
    breakdown = event["modes"]["expected"]["calculation_breakdown"]  # type: ignore[index]
    return next(item for item in breakdown if item["node"] == name)  # type: ignore[return-value]


def _trace(result: dict[str, object]) -> dict[str, object]:
    return _event(result)["common_application_trace"]  # type: ignore[index,return-value]


def _rule_match(result: dict[str, object], rule_id: str) -> dict[str, object]:
    return next(item for item in _trace(result)["rule_matches"] if item["rule_id"] == rule_id)  # type: ignore[index]


def _effective_defense(result: dict[str, object]) -> float:
    breakdown = _event(result)["modes"]["expected"]["calculation_breakdown"]  # type: ignore[index]
    return next(item["value"] for item in breakdown if item["node"] == "defense.enemy-current-effective")  # type: ignore[index]


def _c1_modifier(result: dict[str, object]) -> dict[str, object]:
    modifiers = [
        item
        for item in _trace(result)["applied_modifiers"]  # type: ignore[index]
        if item["effect_id"] == _C1_EFFECT_ID
    ]
    assert len(modifiers) == 1
    return modifiers[0]


@pytest.mark.parametrize(
    ("primary", "supporting", "move_entry_id"),
    (
        (_ALICE_ID, (), "move-entry:alice:1401:physical-anomaly"),
        (_ALICE_ID, (), "move-entry:alice:1401:basic-star-opera-1"),
        (_YE_ID, (_ALICE_ID,), "move-entry:ye:1431:basic-fast-1"),
    ),
)
def test_alice_c1_reduces_enemy_defense_for_anomaly_direct_and_support_events(
    primary: str,
    supporting: tuple[str, ...],
    move_entry_id: str,
) -> None:
    enabled = calculate_payload(
        _payload(
            primary=primary,
            supporting=supporting,
            move_entry_id=move_entry_id,
            enabled_rule_item_ids=(_C1_RULE_ID,),
        )
    )
    disabled = calculate_payload(
        _payload(
            primary=primary,
            supporting=supporting,
            move_entry_id=move_entry_id,
            enabled_rule_item_ids=(),
        )
    )

    assert _rule_match(enabled, _C1_RULE_ID)["status"] == "matched"
    assert _c1_modifier(enabled)["value"] == pytest.approx(0.20)
    assert _effective_defense(enabled) == pytest.approx(800.0)
    assert _effective_defense(disabled) == pytest.approx(1000.0)
    assert enabled["totals"]["expected"]["value"] > disabled["totals"]["expected"]["value"]  # type: ignore[index]


def test_alice_c1_keeps_eligibility_and_rule_switch_contract() -> None:
    forced_c0 = calculate_payload(
        _payload(cinema_level=0, enabled_rule_item_ids=(_C1_RULE_ID,))
    )
    disabled_c1 = calculate_payload(_payload(enabled_rule_item_ids=()))

    assert _rule_match(forced_c0, _C1_RULE_ID)["status"] == "not-matched"
    assert _effective_defense(forced_c0) == pytest.approx(1000.0)
    assert _rule_match(disabled_c1, _C1_RULE_ID)["status"] == "not-matched"
    assert _effective_defense(disabled_c1) == pytest.approx(1000.0)
    assert not any(
        item["effect_id"] == _C1_EFFECT_ID
        for item in _trace(disabled_c1)["applied_modifiers"]  # type: ignore[index]
    )


def test_alice_c4_remains_scoped_to_alice_damage_dealer() -> None:
    alice_result = calculate_payload(
        _payload(
            move_entry_id="move-entry:alice:1401:basic-star-opera-1",
            cinema_level=4,
            enabled_rule_item_ids=(_C4_RULE_ID,),
        )
    )
    teammate_result = calculate_payload(
        _payload(
            primary=_YE_ID,
            supporting=(_ALICE_ID,),
            move_entry_id="move-entry:ye:1431:basic-fast-1",
            cinema_level=4,
            enabled_rule_item_ids=(_C4_RULE_ID,),
        )
    )

    alice_c4 = _rule_match(alice_result, _C4_RULE_ID)
    teammate_c4 = _rule_match(teammate_result, _C4_RULE_ID)
    assert alice_c4["status"] == "matched"
    assert teammate_c4["status"] == "not-matched"


def test_alice_named_passive_damage_entries_keep_their_source_requirements() -> None:
    decisive = calculate_payload(
        _payload(
            move_entry_id="move-entry:alice:1401:cinema6-decisive-extra-attack",
            cinema_level=6,
            enabled_rule_item_ids=("rule:alice:1401:cinema6",),
        )
        | {
            "condition_values": {"condition:alice:victory-state-active": True},
            "parameter_values": {
                "parameter:alice:victory-extra-attack-count": 2,
            },
        }
    )
    decisive_event = _event(decisive)
    assert decisive["totals"]["expected"]["complete"] is True
    assert decisive_event["repeat_count"] == 2
    assert _node(decisive_event, "damage.skill-multiplier")["value"] == pytest.approx(33.0)

    periodic = calculate_payload(
        _payload(move_entry_id="move-entry:alice:1401:core-periodic-extra")
        | {
            "condition_values": {"condition:alice:physical-anomaly-active": True},
            "parameter_values": {
                "parameter:alice:periodic-extra-tick-count": 2,
            },
        }
    )
    periodic_event = _event(periodic)
    assert periodic["totals"]["expected"]["complete"] is False
    assert periodic_event["repeat_count"] == 2
    assert periodic_event["damage_type"] == "anomaly"
    assert periodic_event["damage_subtype"] == "attribute-anomaly"
    diagnostic = periodic["totals"]["expected"]["diagnostics"][0]
    assert diagnostic["message"] == (
        "settled damage value is missing for event:alice:1401:periodic-source"
    )
