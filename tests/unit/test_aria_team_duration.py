from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from web.api import app


client = TestClient(app)

ARIA_EXTRA_RULE = "rule:character:1501:extra-ability:ether-corrosion-duration"
DISORDER_REMAINING = "parameter:aria:ether-disorder-remaining-half-seconds"


def _stats(element: str) -> dict[str, object]:
    return {
        "hp": 9000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: 0.0},
    }


def _payload(
    primary: str,
    support: str | tuple[str, ...],
    move_entry: str,
    *,
    extra_enabled: bool,
    parameter_values: dict[str, int] | None = None,
) -> dict[str, object]:
    supporting = [support] if isinstance(support, str) else list(support)
    team = [primary, *supporting]
    elements = {
        "character:1331": "ether",
        "character:1501": "ether",
        "character:1371": "ether:xuanmo",
    }
    return {
        "primary_character_id": primary,
        "current_operator": primary,
        "supporting_character_ids": supporting,
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry,
        "compile_configs": {
            character_id: {"core_level": 7, "cinema_level": 0}
            for character_id in team
        },
        "condition_values": {},
        "parameter_values": parameter_values or {},
        "character_builds": {
            character_id: {
                "level": 60,
                "out_of_combat_stats": _stats(elements[character_id]),
            }
            for character_id in team
        },
        "enemy": {
            "enemy_id": "enemy:aria-duration-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.0,
                "ether": 0.0,
                "ether:xuanmo": 0.0,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [ARIA_EXTRA_RULE] if extra_enabled else [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _post(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _breakdown_value(event: dict[str, object], node: str) -> float:
    values = event["modes"]["expected"]["calculation_breakdown"]
    return next(item["value"] for item in values if item["node"] == node)


def _aria_duration_effect(event: dict[str, object]) -> dict[str, object] | None:
    return next(
        (
            item
            for item in event["common_application_trace"]["applied_modifiers"]
            if item["effect_id"] == "effect:character:1501:extra-ability:ether-corrosion-duration"
        ),
        None,
    )


def test_aria_team_extra_extends_vivian_ether_anomaly_record_to_13_seconds() -> None:
    entry = "move-entry:character:1331:ether-corrosion"
    off = _post(
        _payload("character:1331", "character:1501", entry, extra_enabled=False)
    )
    on = _post(
        _payload("character:1331", "character:1501", entry, extra_enabled=True)
    )

    off_event, on_event = off["events"][0], on["events"][0]
    assert off["totals"]["expected"]["complete"] is True
    assert on["totals"]["expected"]["complete"] is True
    assert off_event["repeat_count"] == 20
    assert on_event["repeat_count"] == 26
    assert _aria_duration_effect(off_event) is None
    duration_modifier = _aria_duration_effect(on_event)
    assert duration_modifier is not None
    assert duration_modifier["modifier_path"] == "anomaly.attribute.duration-bonus"
    assert duration_modifier["value"] == pytest.approx(3.0)
    assert off_event["element"] == on_event["element"] == "ether"
    assert off_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:vivian:ether"
    )
    assert on_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:vivian:ether"
    )


def test_aria_team_extra_scales_vivian_disorder_but_preserves_selected_remaining_time() -> None:
    entry = "move-entry:character:1331:ether-corrosion-disorder"
    off = _post(
        _payload("character:1331", "character:1501", entry, extra_enabled=False)
    )
    full = _post(
        _payload("character:1331", "character:1501", entry, extra_enabled=True)
    )
    off_event, full_event = off["events"][0], full["events"][0]

    assert off["totals"]["expected"]["complete"] is True
    assert full["totals"]["expected"]["complete"] is True
    assert _breakdown_value(off_event, "disorder.total-multiplier") == pytest.approx(17.0)
    assert _breakdown_value(full_event, "disorder.total-multiplier") == pytest.approx(20.75)
    assert off_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:vivian:ether"
    )
    assert full_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:vivian:ether"
    )

    aria_entry = "move-entry:character:1501:ether-disorder"
    selected = _post(
        _payload(
            "character:1501",
            "character:1331",
            aria_entry,
            extra_enabled=True,
            parameter_values={DISORDER_REMAINING: 24},
        )
    )
    selected_event = selected["events"][0]
    assert selected["totals"]["expected"]["complete"] is True
    assert _breakdown_value(selected_event, "disorder.total-multiplier") == pytest.approx(
        19.5
    )
    assert selected_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:character:1501:ether-corruption"
    )

    too_long = _post(
        _payload(
            "character:1501",
            "character:1331",
            aria_entry,
            extra_enabled=False,
            parameter_values={DISORDER_REMAINING: 26},
        )
    )
    too_long_event = too_long["events"][0]
    assert too_long_event["modes"]["expected"]["status"] == "blocked"
    assert too_long["totals"]["expected"]["complete"] is False
    assert any(
        "remaining-time-exceeds-active-duration" in item["diagnostic_id"]
        for item in too_long_event["modes"]["expected"]["diagnostics"]
    )


def test_aria_team_extra_includes_yixuan_xuanmo_anomaly_with_its_own_record() -> None:
    entry = "move-entry:character:1371:xuanmo-anomaly"
    ineligible = _post(
        _payload("character:1371", "character:1501", entry, extra_enabled=True)
    )
    off = _post(
        _payload(
            "character:1371",
            ("character:1501", "character:1331"),
            entry,
            extra_enabled=False,
        )
    )
    on = _post(
        _payload(
            "character:1371",
            ("character:1501", "character:1331"),
            entry,
            extra_enabled=True,
        )
    )
    ineligible_event = ineligible["events"][0]
    off_event, on_event = off["events"][0], on["events"][0]

    assert ineligible["totals"]["expected"]["complete"] is True
    assert ineligible_event["repeat_count"] == 20
    assert _aria_duration_effect(ineligible_event) is None
    assert any(
        item["diagnostic_id"] == f"{ARIA_EXTRA_RULE}:ineligible-rule"
        for item in ineligible_event["modes"]["expected"]["diagnostics"]
    )
    assert off["totals"]["expected"]["complete"] is True
    assert on["totals"]["expected"]["complete"] is True
    assert off_event["repeat_count"] == 20
    assert on_event["repeat_count"] == 26
    duration_modifier = _aria_duration_effect(on_event)
    assert duration_modifier is not None
    assert duration_modifier["modifier_path"] == "anomaly.attribute.duration-bonus"
    assert duration_modifier["value"] == pytest.approx(3.0)
    assert off_event["element"] == on_event["element"] == "ether:xuanmo"
    assert off_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:yixuan:xuanmo-current"
    )
    assert on_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:yixuan:xuanmo-current"
    )
