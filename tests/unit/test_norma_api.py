from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from web.api import app


NORMA = "character:1571"
ANTON = "character:1111"
NICOLE = "character:1031"
CLIENT = TestClient(app)


def _payload(
    entry: str = "basic-1",
    *,
    primary: str = NORMA,
    team: tuple[str, ...] = (NORMA, ANTON),
    cinema: int = 0,
    crit_rate: float = 0.60,
    conditions: dict[str, bool] | None = None,
    enabled_rules: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "primary_character_id": primary,
        "supporting_character_ids": [item for item in team if item != primary],
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": f"move-entry:{NORMA}:{entry}"
        if primary == NORMA
        else f"move-entry:{primary}:basic-normal-1",
        "compile_configs": {
            item: {
                "core_level": 7,
                "cinema_level": cinema if item == NORMA else 0,
            }
            for item in team
        },
        "condition_values": conditions or {},
        "parameter_values": {},
        "character_builds": {
            item: {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 10000.0,
                    "attack": 1000.0,
                    "defense": 500.0,
                    "impact": 100.0,
                    "crit_rate": crit_rate,
                    "crit_damage": 0.5,
                    "anomaly_mastery": 100.0,
                    "anomaly_proficiency": 100.0,
                    "energy_regen": 1.2,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"fire": 0.0},
                },
            }
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:norma-api-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"fire": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rules),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = CLIENT.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _event(result: dict[str, object]) -> dict[str, object]:
    events = result["events"]
    assert isinstance(events, list) and events
    return events[0]


def _breakdown(event: dict[str, object], node: str) -> float:
    rows = event["modes"]["non-crit"]["calculation_breakdown"]
    return next(float(row["value"]) for row in rows if row["node"] == node)


def _modifier_values(event: dict[str, object], effect_id: str) -> list[float]:
    return [
        float(item["value"])
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["effect_id"] == effect_id
    ]


def test_norma_preview_uses_source_identity_defaults_and_roster_eligibility() -> None:
    solo = CLIENT.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": NORMA,
            "team_character_ids": [NORMA],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert solo.status_code == 200, solo.text
    solo_view = solo.json()
    fields = {item["field_id"]: item["value"] for item in solo_view["compile_config_fields"]}
    assert fields["core_level"] == 7
    assert fields["cinema_level"] == 0
    assert fields["skill_level:ultimate"] == 12
    assert len(solo_view["moves"]) == 18
    rules = {item["rule_id"]: item for item in solo_view["rule_items"]}
    extra_id = f"rule:{NORMA}:extra-ability:technical-gap-stacks"
    assert rules[extra_id]["eligibility"] == "ineligible"

    attack = CLIENT.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": NORMA,
            "team_character_ids": [NORMA, ANTON],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert attack.status_code == 200, attack.text
    assert next(
        item for item in attack.json()["rule_items"] if item["rule_id"] == extra_id
    )["eligibility"] == "eligible"

    same_camp = CLIENT.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": NORMA,
            "team_character_ids": [NORMA, "character:1561"],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert same_camp.status_code == 200, same_camp.text
    assert next(
        item for item in same_camp.json()["rule_items"] if item["rule_id"] == extra_id
    )["eligibility"] == "eligible"

    forced = CLIENT.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": NORMA,
            "team_character_ids": [NORMA],
            "compile_config": {
                "core_level": 7,
                "cinema_level": 0,
                "additional_ability_eligible": True,
            },
        },
    )
    assert forced.status_code == 400


def test_norma_technical_gap_cinema2_replaces_three_percent_with_six() -> None:
    base_rule = f"rule:{NORMA}:extra-ability:technical-gap-stacks"
    c2_rule = f"rule:{NORMA}:cinema2:technical-gap-stun-vulnerability"
    base = _event(_calculate(_payload(enabled_rules=(base_rule,))))
    assert _breakdown(base, "vulnerability.enemy-stun") == 0.30
    assert _modifier_values(base, f"effect:{NORMA}:extra-ability:technical-gap-stacks") == [0.30]

    c2_disabled = _event(
        _calculate(_payload(cinema=2, enabled_rules=(base_rule,)))
    )
    assert _breakdown(c2_disabled, "vulnerability.enemy-stun") == 0.30

    c2_enabled = _event(
        _calculate(_payload(cinema=2, enabled_rules=(base_rule, c2_rule)))
    )
    assert _breakdown(c2_enabled, "vulnerability.enemy-stun") == 0.60
    assert _modifier_values(
        c2_enabled, f"effect:{NORMA}:cinema2:technical-gap-stun-vulnerability"
    ) == [0.30]

    c2_without_extra = _event(_calculate(_payload(cinema=2, enabled_rules=(c2_rule,))))
    assert _breakdown(c2_without_extra, "vulnerability.enemy-stun") == 0.0

    ineligible = _calculate(
        _payload(
            cinema=2,
            team=(NORMA, NICOLE),
            enabled_rules=(base_rule, c2_rule),
        )
    )
    ineligible_without_rules = _calculate(
        _payload(cinema=2, team=(NORMA, NICOLE))
    )
    assert _breakdown(_event(ineligible), "vulnerability.enemy-stun") == 0.0
    assert _event(ineligible)["modes"]["expected"]["value"] == pytest.approx(
        _event(ineligible_without_rules)["modes"]["expected"]["value"]
    )


def test_norma_core_initial_crit_and_penetration_force_partial_are_local_to_norma_direct() -> None:
    core_crit = f"rule:{NORMA}:core:initial-crit-damage"
    with_core = _event(
        _calculate(_payload(enabled_rules=(core_crit,)))
    )
    assert with_core["modes"]["expected"]["status"] == "calculated"
    assert _breakdown(with_core, "character.current.crit-damage") == pytest.approx(0.67)

    below_threshold = _event(
        _calculate(_payload(crit_rate=0.49, enabled_rules=(core_crit,)))
    )
    assert _breakdown(below_threshold, "character.current.crit-damage") == 0.5
    capped = _event(
        _calculate(_payload(crit_rate=1.10, enabled_rules=(core_crit,)))
    )
    assert _breakdown(capped, "character.current.crit-damage") == pytest.approx(1.35)

    pf_rule = f"rule:{NORMA}:core:penetration-force-atk"
    partial = _calculate(_payload(enabled_rules=(pf_rule,)))
    assert _event(partial)["modes"]["expected"]["status"] == "blocked"
    assert partial["totals"]["expected"]["complete"] is False
    assert any(
        item["diagnostic_id"] == f"effect:{NORMA}:core:penetration-force-atk:unresolved-effect"
        and item["blocking"]
        for item in partial["diagnostics"]
    )

    teammate_payload = _payload(
        primary=ANTON,
        team=(ANTON, NORMA),
        enabled_rules=(pf_rule,),
    )
    teammate = _calculate(teammate_payload)
    assert _event(teammate)["modes"]["expected"]["status"] == "calculated"
    assert teammate["totals"]["expected"]["complete"] is True


def test_norma_term_attack_team_bonus_c1_and_c6_current_conditions() -> None:
    term_rule = f"rule:{NORMA}:extra-ability:term-1000012-attack"
    term_condition = f"condition:{NORMA}:term-1000012-active"
    term = _calculate(
        _payload(
            conditions={term_condition: True},
            enabled_rules=(term_rule,),
        )
    )
    norma_snapshot = next(
        item for item in term["resolved_character_snapshots"] if item["character_id"] == NORMA
    )
    assert norma_snapshot["stats"]["attack"] == 1870.0

    team_rule = f"rule:{NORMA}:extra-ability:en-ni-barrage-team-damage"
    team_condition = f"condition:{NORMA}:en-ni-barrage-active"
    team_damage = _event(
        _calculate(
            _payload(
                conditions={team_condition: True},
                enabled_rules=(team_rule,),
            )
        )
    )
    assert _breakdown(team_damage, "damage.normal-bonus") == 0.20

    c1_rule = f"rule:{NORMA}:cinema1:all-resistance-reduction"
    c1_condition = f"condition:{NORMA}:cinema1-all-resistance-reduction-active"
    c1 = _event(
        _calculate(
            _payload(
                cinema=1,
                conditions={c1_condition: True},
                enabled_rules=(c1_rule,),
            )
        )
    )
    assert _breakdown(c1, "resistance.enemy-reduction") == 0.15

    c6_rule = f"rule:{NORMA}:cinema6:high-explosive-damage"
    stunned = f"condition:{NORMA}:ex-special-target-stunned"
    high_explosive = _event(
        _calculate(
            _payload(
                entry="ex-high-explosive-shell",
                cinema=6,
                conditions={stunned: True},
                enabled_rules=(c6_rule,),
            )
        )
    )
    assert _breakdown(high_explosive, "damage.normal-bonus") == 0.30

    not_stunned = f"condition:{NORMA}:ex-special-target-not-stunned"
    armor_shell = _event(
        _calculate(
            _payload(
                entry="ex-armor-shell",
                cinema=6,
                conditions={not_stunned: True},
                enabled_rules=(c6_rule,),
            )
        )
    )
    assert _modifier_values(
        armor_shell, f"effect:{NORMA}:cinema6:high-explosive-damage"
    ) == []

    missile_condition = f"condition:{NORMA}:cinema6-missile-current-hit"
    missile_result = _calculate(
        _payload(
            entry="cinema6-current-missile",
            cinema=6,
            conditions={missile_condition: True},
        )
    )
    assert len(missile_result["events"]) == 1
    missile = _event(missile_result)
    assert missile["damage_type"] == "direct"
    assert missile["element"] == "fire"
    assert _breakdown(missile, "damage.skill-multiplier") == 2.0
    assert missile["modes"]["expected"]["status"] == "calculated"
