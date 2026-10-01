from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from core.application.characters.alice import (
    AliceCompileConfig,
    compile_alice,
    load_raw_record as load_alice_raw,
)
from core.application.characters.yuzuha import (
    YuzuhaCompileConfig,
    compile_yuzuha,
    load_raw_record as load_yuzuha_raw,
)
from core.application import (
    CalculationScenario,
    CharacterMatchProfile,
    EffectMatchContext,
    EffectMatcher,
    EnemyMatchProfile,
)
from core.application.execution.event_factory import instantiate_damage_event
from core.data.loader import load_character_record
from core.presentation.calculation_service import calculate_payload
from core.types import (
    BattleStateId,
    CalculationContext,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    Element,
    EnemyId,
    EnemySnapshot,
    FixedMultiplier,
    Resolved,
)


_ELEMENT_BY_CHARACTER = {
    "character:1401": "physical",
    "character:1411": "physical",
    "character:1311": "ether",
    "character:1361": "electric",
    "character:1431": "physical",
}


def _stats(
    element: str,
    *,
    attack: float = 100.0,
    anomaly_mastery: float = 200.0,
) -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": anomaly_mastery,
        "anomaly_proficiency": 100.0,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "energy_regen": 1.2,
        "element_damage_bonus": {element: 0.0},
    }


def _payload(
    *,
    primary: str,
    supporting: tuple[str, ...] = (),
    move_entry_id: str,
    compile_configs: dict[str, dict[str, object]],
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    rule_stack_counts: dict[str, int] | None = None,
    character_builds: dict[str, dict[str, object]] | None = None,
    is_stunned: bool = False,
) -> dict[str, object]:
    team = (primary, *supporting)
    builds = character_builds or {
        character_id: {
            "level": 60,
            "out_of_combat_stats": _stats(
                _ELEMENT_BY_CHARACTER[character_id]
            ),
        }
        for character_id in team
    }
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:confirmed-semantics",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {
                "physical": 0.2,
                "ether": 0.2,
                "electric": 0.2,
                "fire": 0.2,
                "ice": 0.2,
                "wind": 0.2,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": is_stunned,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
    }


def _event(result: dict[str, object], semantic_id: str) -> dict[str, object]:
    return next(item for item in result["events"] if item["semantic_id"] == semantic_id)  # type: ignore[index]


def _breakdown(event: dict[str, object]) -> dict[str, float]:
    return {
        item["node"]: item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
    }


def _trace(event: dict[str, object]) -> dict[str, object]:
    return event["common_application_trace"]  # type: ignore[return-value]


def _alice_conditions(*, victory: bool = False) -> dict[str, bool]:
    return {
        "condition:alice:star-dance-charge-1": False,
        "condition:alice:star-dance-charge-2": False,
        "condition:alice:star-dance-charge-3": False,
        "condition:alice:physical-anomaly-active": True,
        "condition:alice:polar-assault-active": False,
        "condition:alice:victory-state-active": victory,
    }


def test_trigger_core_c1_use_nonstun_lane_and_respect_ye_veil_cap() -> None:
    configs = {
        "character:1431": {
            "core_level": 1,
            "cinema_level": 0,
            "mingxin_active": True,
            "entry_move_uses_linren": True,
        },
        "character:1361": {"core_level": 7, "cinema_level": 1},
    }
    enabled = (
        "rule:trigger:1361:core-passive",
        "rule:trigger:1361:cinema1",
    )
    common = dict(
        primary="character:1431",
        supporting=("character:1361",),
        move_entry_id="move-entry:ye:1431:basic-fast-1",
        compile_configs=configs,
        enabled_rule_item_ids=enabled,
    )
    unstunned = calculate_payload(_payload(**common, is_stunned=False))
    stunned = calculate_payload(_payload(**common, is_stunned=True))

    nonstun_values = _breakdown(
        _event(unstunned, "damage:ye:1431:basic-fast-1:main")
    )
    stun_values = _breakdown(
        _event(stunned, "damage:ye:1431:basic-fast-1:main")
    )
    assert nonstun_values["vulnerability.enemy-stun"] == pytest.approx(1.5)
    assert nonstun_values["vulnerability.effective-stun"] == pytest.approx(0.0)
    assert nonstun_values["vulnerability.enemy-normal"] == pytest.approx(0.55)
    assert stun_values["vulnerability.effective-stun"] == pytest.approx(1.5)
    assert stun_values["vulnerability.enemy-normal"] == pytest.approx(0.55)

    veil_payload = dict(common)
    veil_payload["enabled_rule_item_ids"] = ("rule:ye:1431:veil", *enabled)
    veil = calculate_payload(_payload(**veil_payload, is_stunned=False))
    veil_values = _breakdown(
        _event(veil, "damage:ye:1431:basic-fast-1:main")
    )
    assert veil_values["vulnerability.effective-bonus"] == pytest.approx(1.10)


def test_yuzuha_c1_reduces_linren_resistance_under_sweet_scare() -> None:
    result = calculate_payload(
        _payload(
            primary="character:1431",
            supporting=("character:1411",),
            move_entry_id="move-entry:ye:1431:ultimate-zhuyunjingting",
            compile_configs={
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": True,
                    "entry_move_uses_linren": True,
                },
                "character:1411": {"core_level": 1, "cinema_level": 1},
            },
            condition_values={"condition:yuzuha:sweet-scare-active": True},
            enabled_rule_item_ids=("rule:yuzuha:1411:cinema1",),
        )
    )
    values = _breakdown(
        _event(result, "damage:ye:1431:ultimate-zhuyunjingting:main")
    )
    assert values["resistance.enemy-reduction"] == pytest.approx(0.10)


def test_ye_c1_damage_effects_do_not_leak_to_astra_c4_child() -> None:
    payload = _payload(
        primary="character:1431",
        supporting=("character:1311",),
        move_entry_id="move-entry:ye:1431:assist-yuanshou",
        compile_configs={
            "character:1431": {
                "core_level": 1,
                "cinema_level": 1,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            },
            "character:1311": {"core_level": 1, "cinema_level": 4},
        },
        condition_values={"condition:astra:aria-active": True},
        enabled_rule_item_ids=(
            "rule:ye:1431:cinema1",
            "rule:astra:1311:cinema4",
        ),
    )
    payload["selected_trigger_inputs"] = [
        {
            "input_id": "scenario-trigger:effect:astra:1311:cinema4-attack-extra:actor",
            "actor_id": "character:1431",
        }
    ]
    result = calculate_payload(payload)
    main = _event(result, "damage:ye:1431:assist-yuanshou:main")
    child = _event(result, "event:astra:1311:cinema4-attack-extra")
    main_modifiers = {
        item["effect_id"]: item["value"]
        for item in _trace(main)["applied_modifiers"]
    }
    child_effect_ids = {
        item["effect_id"] for item in _trace(child)["applied_modifiers"]
    }
    assert main_modifiers["effect:ye:1431:cinema1:damage"] == pytest.approx(0.10)
    assert main_modifiers["effect:ye:1431:cinema1:defense-ignore"] == pytest.approx(0.20)
    assert "effect:ye:1431:cinema1:damage" not in child_effect_ids
    assert "effect:ye:1431:cinema1:defense-ignore" not in child_effect_ids


def test_current_am_derived_values_and_equipment_order() -> None:
    manual_payload = _payload(
        primary="character:1401",
        supporting=("character:1411",),
        move_entry_id="move-entry:alice:1401:physical-anomaly",
        compile_configs={
            "character:1401": {"core_level": 1, "cinema_level": 0},
            "character:1411": {"core_level": 1, "cinema_level": 0},
        },
        condition_values={
            **_alice_conditions(),
            "condition:yuzuha:tanuki-wish-active": False,
        },
        enabled_rule_item_ids=("rule:alice:1401:extra-ability",),
        character_builds={
            "character:1401": {
                "level": 60,
                "out_of_combat_stats": _stats(
                    "physical", attack=1000.0, anomaly_mastery=200.0
                ),
            },
            "character:1411": {
                "level": 60,
                "out_of_combat_stats": _stats("physical"),
            },
        },
    )
    manual = calculate_payload(manual_payload)
    alice_snapshot = next(
        item
        for item in manual["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    assert alice_snapshot["stats"]["attack"] == pytest.approx(1000.0)
    assert alice_snapshot["stats"]["anomaly_proficiency"] == pytest.approx(196.0)
    manual_without_extra = deepcopy(manual_payload)
    manual_without_extra["enabled_rule_item_ids"] = []
    baseline = calculate_payload(manual_without_extra)
    baseline_event = _event(baseline, "event:alice:1401:physical-anomaly")
    extra_event = _event(manual, "event:alice:1401:physical-anomaly")
    assert _breakdown(extra_event)["anomaly.effect-strength"] > _breakdown(
        baseline_event
    )["anomaly.effect-strength"]

    low_am_payload = deepcopy(manual_payload)
    low_am_payload["character_builds"]["character:1401"]["out_of_combat_stats"] = _stats(
        "physical", attack=1000.0, anomaly_mastery=100.0
    )
    low_am = calculate_payload(low_am_payload)
    low_snapshot = next(
        item
        for item in low_am["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    assert low_snapshot["stats"]["attack"] == pytest.approx(1000.0)
    assert low_snapshot["stats"]["anomaly_proficiency"] == pytest.approx(100.0)

    equipment_builds = {
        "character:1401": {
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": "wengine:14140",
            "wengine_level": 60,
            "wengine_refinement": 1,
            "base_stats": _stats(
                "physical", attack=1000.0, anomaly_mastery=100.0
            ),
        },
        "character:1411": {
            "level": 60,
            "out_of_combat_stats": _stats("physical"),
        },
    }
    equipment_payload = _payload(
        primary="character:1401",
        supporting=("character:1411",),
        move_entry_id="move-entry:alice:1401:physical-anomaly",
        compile_configs={
            "character:1401": {"core_level": 1, "cinema_level": 0},
            "character:1411": {"core_level": 1, "cinema_level": 0},
        },
        condition_values={
            **_alice_conditions(),
            "condition:yuzuha:tanuki-wish-active": False,
            "condition:wengine:14140:owner:1401:strong-assault-active": False,
        },
        enabled_rule_item_ids=(
            "rule:alice:1401:extra-ability",
            "rule:wengine:14140:owner:1401:anomaly-mastery",
        ),
        character_builds=equipment_builds,
    )
    equipment = calculate_payload(equipment_payload)
    equipment_without_extra = deepcopy(equipment_payload)
    equipment_without_extra["enabled_rule_item_ids"] = [
        "rule:wengine:14140:owner:1401:anomaly-mastery"
    ]
    equipment_baseline = calculate_payload(equipment_without_extra)
    alice_snapshot = next(
        item
        for item in equipment["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    baseline_snapshot = next(
        item
        for item in equipment_baseline["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    assert alice_snapshot["stats"]["anomaly_mastery"] == pytest.approx(160.0)
    assert alice_snapshot["stats"]["anomaly_proficiency"] == pytest.approx(132.0)
    assert alice_snapshot["stats"]["attack"] == pytest.approx(
        baseline_snapshot["stats"]["attack"]
    )
    traces = [
        item
        for item in equipment["panel_traces"]
        if item["recipient_character_id"] == "character:1401"
    ]
    assert [item["effect_id"] for item in traces] == [
        "effect:wengine:14140:owner:1401:anomaly-mastery",
        "effect:character:1401:extra-ability:anomaly-mastery-to-proficiency",
    ]
    assert traces[1]["resolved_value"] == pytest.approx(32.0)
    assert traces[1]["modifier_path"] == (
        "character.combat.anomaly-proficiency-flat-bonus"
    )


def test_alice_extra_proficiency_does_not_touch_yuzuha_astra_attack_buffs() -> None:
    builds = {
        "character:1401": {
            "level": 60,
            "out_of_combat_stats": _stats(
                "physical", attack=1000.0, anomaly_mastery=200.0
            ),
        },
        "character:1411": {
            "level": 60,
            "out_of_combat_stats": _stats("physical", attack=100.0),
        },
        "character:1311": {
            "level": 60,
            "out_of_combat_stats": _stats("ether", attack=800.0),
        },
    }
    common = dict(
        primary="character:1401",
        supporting=("character:1411", "character:1311"),
        move_entry_id="move-entry:alice:1401:physical-anomaly",
        compile_configs={
            "character:1401": {"core_level": 1, "cinema_level": 0},
            "character:1411": {"core_level": 1, "cinema_level": 0},
            "character:1311": {"core_level": 1, "cinema_level": 0},
        },
        condition_values={
            **_alice_conditions(),
            "condition:yuzuha:tanuki-wish-active": True,
            "condition:astra:core-attack-buff-active": True,
        },
        character_builds=builds,
    )
    enabled = (
        "rule:yuzuha:1411:core-passive",
        "rule:astra:1311:core-passive-self",
        "rule:alice:1401:extra-ability",
    )
    with_extra = calculate_payload(
        _payload(**common, enabled_rule_item_ids=enabled)
    )
    without_extra_payload = dict(common)
    without_extra = calculate_payload(
        _payload(
            **without_extra_payload,
            enabled_rule_item_ids=enabled[:-1],
        )
    )
    with_snapshot = next(
        item
        for item in with_extra["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    without_snapshot = next(
        item
        for item in without_extra["resolved_character_snapshots"]
        if item["character_id"] == "character:1401"
    )
    assert with_snapshot["stats"]["attack"] == pytest.approx(
        without_snapshot["stats"]["attack"]
    )
    assert with_snapshot["stats"]["anomaly_proficiency"] == pytest.approx(196.0)
    assert without_snapshot["stats"]["anomaly_proficiency"] == pytest.approx(100.0)
    extra_trace = next(
        item
        for item in with_extra["panel_traces"]
        if item["effect_id"]
        == "effect:character:1401:extra-ability:anomaly-mastery-to-proficiency"
    )
    assert extra_trace["modifier_path"] == (
        "character.combat.anomaly-proficiency-flat-bonus"
    )


@pytest.mark.parametrize("anomaly_mastery, expected", ((200.0, 0.26), (80.0, 0.0)))
def test_yuzuha_extra_current_am_lanes_and_threshold(
    anomaly_mastery: float,
    expected: float,
) -> None:
    result = calculate_payload(
        _payload(
            primary="character:1401",
            supporting=("character:1411",),
            move_entry_id="move-entry:alice:1401:physical-anomaly",
            compile_configs={
                "character:1401": {"core_level": 1, "cinema_level": 0},
                "character:1411": {"core_level": 1, "cinema_level": 1},
            },
            condition_values={
                **_alice_conditions(),
                "condition:yuzuha:tanuki-wish-active": True,
            },
            enabled_rule_item_ids=("rule:yuzuha:1411:extra-ability",),
            character_builds={
                "character:1401": {
                    "level": 60,
                    "out_of_combat_stats": _stats("physical"),
                },
                "character:1411": {
                    "level": 60,
                    "out_of_combat_stats": _stats(
                        "physical", anomaly_mastery=anomaly_mastery
                    ),
                },
            },
        )
    )
    modifiers = {
        item["modifier_path"]: item["value"]
        for item in _trace(
            _event(result, "event:alice:1401:physical-anomaly")
        )["applied_modifiers"]
        if "effect:character:1411:extra-ability" in item["effect_id"]
    }
    assert modifiers["anomaly-buildup.efficiency"] == pytest.approx(
        0.20 if anomaly_mastery == 200.0 else 0.0
    )
    assert modifiers["anomaly.attribute.damage-bonus"] == pytest.approx(expected)


def test_alice_c6_direct_only_repeat_zero_and_no_recursive_package() -> None:
    direct = calculate_payload(
        _payload(
            primary="character:1431",
            supporting=("character:1401",),
            move_entry_id="move-entry:ye:1431:basic-fast-1",
            compile_configs={
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                },
                "character:1401": {"core_level": 1, "cinema_level": 6},
            },
            condition_values={
                "condition:alice:victory-state-active": True,
            },
            parameter_values={"parameter:alice:victory-extra-attack-count": 2},
            enabled_rule_item_ids=("rule:alice:1401:cinema6",),
        )
    )
    direct_ids = [item["semantic_id"] for item in direct["events"]]
    assert direct_ids.count("event:alice:1401:cinema6:decisive-extra-attack") == 1
    child = _event(direct, "event:alice:1401:cinema6:decisive-extra-attack")
    assert child["repeat_count"] == 2
    assert child["common_application_trace"]["created_by_effect_id"] == (
        "effect:character:1401:cinema6:decisive-extra-attack"
    )

    zero = calculate_payload(
        _payload(
            primary="character:1431",
            supporting=("character:1401",),
            move_entry_id="move-entry:ye:1431:basic-fast-1",
            compile_configs={
                "character:1431": {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                },
                "character:1401": {"core_level": 1, "cinema_level": 6},
            },
            condition_values={"condition:alice:victory-state-active": True},
            parameter_values={"parameter:alice:victory-extra-attack-count": 0},
            enabled_rule_item_ids=("rule:alice:1401:cinema6",),
        )
    )
    assert _event(
        zero, "event:alice:1401:cinema6:decisive-extra-attack"
    )["modes"]["expected"]["known_value"] == pytest.approx(0.0)

    for move_entry_id in (
        "move-entry:alice:1401:physical-anomaly",
        "move-entry:alice:1401:disorder",
    ):
        anomaly_result = calculate_payload(
            _payload(
                primary="character:1401",
                move_entry_id=move_entry_id,
                compile_configs={"character:1401": {"core_level": 1, "cinema_level": 6}},
                condition_values=_alice_conditions(victory=True),
                parameter_values={"parameter:alice:victory-extra-attack-count": 2},
                enabled_rule_item_ids=("rule:alice:1401:cinema6",),
            )
        )
        assert [item["semantic_id"] for item in anomaly_result["events"]] == [
            "event:alice:1401:physical-anomaly"
            if move_entry_id.endswith("physical-anomaly")
            else "event:alice:1401:disorder"
        ]


def test_trigger_c4_and_c6_event_identity_and_modifier_lane() -> None:
    c4 = calculate_payload(
        _payload(
            primary="character:1361",
            move_entry_id="move-entry:trigger:1361:basic-concerto-sniping",
            compile_configs={"character:1361": {"core_level": 1, "cinema_level": 4}},
            condition_values={"condition:trigger:follow-up-active": True},
            enabled_rule_item_ids=("rule:trigger:1361:cinema4",),
        )
    )
    extra = _event(c4, "event:character:1361:cinema4:severance")
    assert extra["repeat_count"] == 1
    assert extra["common_application_trace"]["created_by_effect_id"] == (
        "effect:character:1361:cinema4:severance"
    )
    assert extra["modes"]["expected"]["value"] is not None

    c6 = calculate_payload(
        _payload(
            primary="character:1361",
            move_entry_id="move-entry:trigger:1361:basic-cold-chamber-1",
            compile_configs={"character:1361": {"core_level": 1, "cinema_level": 6}},
            condition_values={"condition:trigger:sniper-stance-active": True},
            enabled_rule_item_ids=("rule:trigger:1361:cinema6",),
        )
    )
    main = _event(c6, "event:trigger:1361:basic-cold-chamber-1:main")
    bullet = _event(c6, "event:character:1361:cinema6:armor-piercing-round")
    assert not any(
        item["effect_id"] == "effect:character:1361:cinema6:armor-piercing-round-damage"
        for item in _trace(main)["applied_modifiers"]
    )
    assert any(
        item["effect_id"] == "effect:character:1361:cinema6:armor-piercing-round-damage"
        and item["value"] == pytest.approx(0.50)
        for item in _trace(bullet)["applied_modifiers"]
    )


@pytest.mark.parametrize("shell_count", (0, 1, 2))
@pytest.mark.parametrize("sweet_scare", (False, True))
def test_yuzuha_c6_shell_counts_and_sweet_scare_creation(
    shell_count: int,
    sweet_scare: bool,
) -> None:
    result = calculate_payload(
        _payload(
            primary="character:1411",
            supporting=("character:1401",),
            move_entry_id="move-entry:yuzuha:1411:assist-stuffed-candy",
            compile_configs={
                "character:1411": {"core_level": 1, "cinema_level": 6},
                "character:1401": {"core_level": 1, "cinema_level": 0},
            },
            condition_values={
                "condition:yuzuha:sweet-scare-active": sweet_scare,
                "condition:yuzuha:tanuki-wish-active": False,
            },
            parameter_values={
                "parameter:yuzuha:cinema6:strong-shell-count": shell_count
            },
            enabled_rule_item_ids=(
                "rule:yuzuha:1411:cinema6",
                "rule:yuzuha:1411:cinema6-shells",
                "rule:yuzuha:1411:cinema6:sweet-scare-fireworks",
            ),
            rule_stack_counts={"rule:yuzuha:1411:cinema6": 3},
        )
    )
    shell = _event(result, "event:yuzuha:1411:cinema6:strong-shell")
    assert shell["repeat_count"] == shell_count
    fireworks_ids = [
        item["semantic_id"]
        for item in result["events"]
        if item["semantic_id"]
        == "event:yuzuha:1411:cinema6:sweet-scare-fireworks"
    ]
    assert bool(fireworks_ids) is sweet_scare
    if sweet_scare:
        assert _event(
            result, "event:yuzuha:1411:cinema6:sweet-scare-fireworks"
        )["repeat_count"] == shell_count
    assert result["totals"]["expected"]["complete"] is True
    assert not any(
        "stacked EventCreation" in item["message"]
        for item in result["diagnostics"]
    )


def test_alice_c2_physical_scope_is_effective_and_nonphysical_scope_is_not() -> None:
    result = calculate_payload(
        _payload(
            primary="character:1401",
            move_entry_id="move-entry:alice:1401:physical-anomaly",
            compile_configs={"character:1401": {"core_level": 1, "cinema_level": 2}},
            condition_values=_alice_conditions(),
            enabled_rule_item_ids=("rule:alice:1401:cinema2",),
        )
    )
    values = _breakdown(_event(result, "event:alice:1401:physical-anomaly"))
    assert values["anomaly.attribute.damage-bonus-region"] == pytest.approx(1.15)

    definition = compile_alice(
        AliceCompileConfig(cinema_level=2),
        load_alice_raw(load_character_record("character:1401")),
    )
    c2 = next(item for item in definition.rule_items if str(item.rule_id).endswith("cinema2"))
    anomaly_effect, disorder_effect = c2.effects
    assert any(
        getattr(item, "element", None).value == "physical:linren"
        for item in anomaly_effect.rule.filters[2].filters
    )
    assert any(
        getattr(item, "element", None).value == "physical:linren"
        for item in disorder_effect.rule.filters[1].filters
    )


def test_alice_c2_does_not_match_fire_anomaly_or_disorder_events() -> None:
    definition = compile_alice(
        AliceCompileConfig(cinema_level=2),
        load_alice_raw(load_character_record("character:1401")),
    )
    c2 = next(item for item in definition.rule_items if str(item.rule_id).endswith("cinema2"))
    templates = {
        item.ref.template_id: item
        for item in definition.damage_event_templates
        if item.ref.template_id
        in {
            "template:alice:1401:physical-anomaly",
            "template:alice:1401:disorder",
        }
    }
    stats = CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(100.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.5),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(200.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )
    owner = CharacterId("character:1401")
    enemy = EnemyId("enemy:alice-c2-scope")
    snapshot = CharacterSnapshot(owner, 60, stats)
    target = EnemySnapshot(
        enemy_id=enemy,
        level=60,
        initial_defense=Resolved(1000.0),
        damage_resistance={Element.PHYSICAL: Resolved(0.0), Element.FIRE: Resolved(0.0)},
        anomaly_buildup_resistance={},
        daze_resistance=Resolved(0.0),
        damage_reduction=Resolved(0.0),
    )
    scenario = CalculationScenario(
        scenario_id="scenario:alice-c2-scope",
        current_operator=owner,
        conditions=tuple(definition.scenario_conditions),
        enabled_rule_item_ids=frozenset({c2.rule_id}),
    )
    matcher = EffectMatcher()
    for template in templates.values():
        instantiated = instantiate_damage_event(
            template,
            FixedMultiplier(Resolved(1.0)),
            battle_state_id=BattleStateId("battle:alice-c2-scope"),
            target_enemy=enemy,
            created_at=0.0,
        )
        for element, expected in (
            (Element.PHYSICAL, True),
            (Element.FIRE, False),
        ):
            event = replace(
                instantiated.event,
                metadata=replace(instantiated.event.metadata, element=element),
            )
            context = EffectMatchContext(
                current_event=event,
                calculation_context=CalculationContext(
                    event=event,
                    battle_state_id=event.metadata.battle_state_id,
                    character_snapshots=(snapshot,),
                    target_snapshot=target,
                ),
                scenario=scenario,
                team=(CharacterMatchProfile(owner, CharacterRole.ANOMALY),),
                target=EnemyMatchProfile(enemy),
            )
            result = matcher.match_rule_item(c2, context)
            assert (result.status.value == "matched") is expected
