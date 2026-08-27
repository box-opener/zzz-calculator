from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.application import (
    CalculationDiagnostic,
    CalculationScenario,
    CalculationRouter,
    CharacterMatchProfile,
    CritDisplayMode,
    EnemyMatchProfile,
    EffectMatchStatus,
    RuleItemId,
    ScenarioParameterId,
)
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record,
)
from core.application.execution import MoveCalculationRequest, calculate_move
from core.application.execution.event_factory import instantiate_direct_damage_event
from core.application.execution.modifiers import apply_matched_modifiers
from core.application.execution.service import DirectMoveApplicationService
from core.application.output import EventCalculationStatus
from core.calculation import CalculationNode
from core.types import (
    BattleStateId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    EffectId,
    EffectOperation,
    Element,
    EnemyId,
    EnemySnapshot,
    EventCreationEffect,
    ModifierEffect,
    Modifier,
    OperationState,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
    UnresolvedSharpExplosionDamageEvent,
)


def _raw_record():
    fixture = (
        Path(__file__).parents[1] / "fixtures" / "characters" / "ye_shunguang.json"
    )
    return load_raw_record(json.loads(fixture.read_text(encoding="utf-8")))


def _definition(*, cinema_level: int = 0, core_level: int = 1):
    return compile_ye_shunguang(
        YeShunguangCompileConfig(
            cinema_level=cinema_level,
            core_level=core_level,
            mingxin_active=True,
            entry_move_uses_linren=True,
            enemy_stun_vulnerability_bonus=1.5,
        ),
        _raw_record(),
    )


def _entry(definition, suffix: str):
    return next(
        item for item in definition.move_entries if str(item.entry_id).endswith(suffix)
    )


def _stats(*, attack: float = 1000.0, crit_rate: float = 0.5) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(crit_rate),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )


def _scenario(
    definition,
    *,
    enabled: tuple[str, ...] = (),
    condition_values: dict[str, bool | None] | None = None,
    flowing_cloud_count: int | None = None,
) -> CalculationScenario:
    values = condition_values or {}
    conditions = tuple(
        replace(
            condition,
            value=values.get(str(condition.condition_id), condition.value),
        )
        for condition in definition.scenario_conditions
    )
    parameters = tuple(
        (
            replace(parameter, value=flowing_cloud_count)
            if parameter.parameter_id
            == ScenarioParameterId("parameter:ye:flowing-cloud-sword-count")
            and flowing_cloud_count is not None
            else parameter
        )
        for parameter in definition.scenario_parameters
    )
    return CalculationScenario(
        scenario_id="scenario:ye-application",
        current_operator=definition.character_id,
        conditions=conditions,
        parameters=parameters,
        enabled_rule_item_ids=frozenset(RuleItemId(item) for item in enabled),
    )


def _request(
    definition,
    suffix: str,
    *,
    enabled: tuple[str, ...] = (),
    condition_values: dict[str, bool | None] | None = None,
    flowing_cloud_count: int | None = None,
    base_modifiers: tuple[Modifier, ...] = (),
    mode: CritDisplayMode = CritDisplayMode.EXPECTED,
) -> MoveCalculationRequest:
    target = EnemyId("enemy:application")
    battle = BattleStateId("battle:application")
    scenario = _scenario(
        definition,
        enabled=enabled,
        condition_values=condition_values,
        flowing_cloud_count=flowing_cloud_count,
    )
    stats = _stats()
    return MoveCalculationRequest(
        definition=definition,
        move_entry_id=_entry(definition, suffix).entry_id,
        scenario=scenario,
        battle_state_id=battle,
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(definition.character_id, 60, stats),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(
                definition.character_id,
                CharacterRole.ATTACK,
                operation_state=OperationState.OPERATED,
            ),
        ),
        target_profile=EnemyMatchProfile(target),
        base_calculation_modifiers=base_modifiers,
        crit_display_mode=mode,
    )


def _stun_modifier(value: float) -> Modifier:
    return Modifier(
        effect_id=EffectId("environment:stun-vulnerability"),
        modifier_path=CalculationNode.ENEMY_STUN_VULNERABILITY,
        operation=EffectOperation.ADD,
        value=Resolved(value),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )


def _calculated_value(event) -> float:
    assert event.result is not None
    assert event.result.value is not None
    return event.result.value


def _breakdown(event):
    assert event.result is not None
    return event.result.breakdown


def _known_value(event) -> float:
    assert event.known_value is not None
    return event.known_value


def test_direct_move_application_uses_panel_snapshot_before_calculation() -> None:
    definition = _definition()
    request = _request(
        definition,
        "basic-fast-1",
        enabled=("rule:ye:1431:hedao",),
    )
    execution = calculate_move(request)

    assert execution.output.complete is True
    event = execution.output.events[0]
    assert event.status is EventCalculationStatus.CALCULATED
    assert event.repeat_count == 1
    assert event.known_value == pytest.approx(_calculated_value(event))
    snapshot = execution.resolved_character_snapshots[0]
    assert snapshot.settlement_stats.crit_rate == Resolved(0.65)
    assert any(
        item.rule_id == RuleItemId("rule:ye:1431:hedao")
        for item in execution.event_traces[0].rule_matches
    )


def test_base_stun_vulnerability_is_replaced_by_veil_override() -> None:
    definition = _definition()
    base = _request(
        definition,
        "basic-fast-1",
        enabled=("rule:ye:1431:hedao",),
        base_modifiers=(_stun_modifier(1.5),),
    )
    with_veil = _request(
        definition,
        "basic-fast-1",
        enabled=("rule:ye:1431:hedao", "rule:ye:1431:veil"),
        base_modifiers=(_stun_modifier(1.5),),
    )
    base_execution = calculate_move(base)
    veil_execution = calculate_move(with_veil)

    assert _calculated_value(base_execution.output.events[0]) > _calculated_value(
        veil_execution.output.events[0]
    )
    veil_values = {
        item.node: item.value.value
        for item in _breakdown(veil_execution.output.events[0])
    }
    assert veil_values[CalculationNode.ENEMY_STUN_VULNERABILITY] == pytest.approx(1.1)


def test_unit_repeat_keeps_unit_result_and_repeat_trace_separate() -> None:
    definition = _definition()
    request = _request(
        definition,
        "basic-cloud",
        enabled=("rule:ye:1431:hedao",),
        flowing_cloud_count=5,
    )
    execution = calculate_move(request)

    event = execution.output.events[0]
    assert event.status is EventCalculationStatus.CALCULATED
    assert event.repeat_count == 5
    assert execution.output.known_total == pytest.approx(_calculated_value(event) * 5)
    skill_multiplier = next(
        item.value.value
        for item in _breakdown(event)
        if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    assert skill_multiplier == pytest.approx(2.344)


def test_mutually_exclusive_variant_is_resolved_from_conditions_only() -> None:
    definition = _definition()
    entry = _entry(definition, "basic-mingxin-zhanliuguang-mie")
    with_condition = str(entry.multiplier_variants[0].condition_ids[0])
    without_condition = str(entry.multiplier_variants[1].condition_ids[0])
    request = _request(
        definition,
        "basic-mingxin-zhanliuguang-mie",
        condition_values={with_condition: True, without_condition: False},
    )
    execution = calculate_move(request)
    skill_multiplier = next(
        item.value.value
        for item in _breakdown(execution.output.events[0])
        if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    assert skill_multiplier == pytest.approx(17.833)

    blocked = calculate_move(
        _request(
            definition,
            "basic-mingxin-zhanliuguang-mie",
        )
    )
    assert blocked.output.events == ()
    assert blocked.output.known_total is None
    assert blocked.output.diagnostics


def test_modifier_application_preserves_base_modifier_and_resolves_veil_override() -> (
    None
):
    definition = _definition()
    veil = next(
        item
        for item in definition.rule_items
        if item.rule_id == RuleItemId("rule:ye:1431:veil")
    )
    assert isinstance(veil.effects[0], ModifierEffect)
    effect = veil.effects[0]
    application = apply_matched_modifiers(
        (CharacterSnapshot(definition.character_id, 60, _stats()),),
        (_stun_modifier(1.5),),
        (effect,),
        definition.character_id,
    )
    assert not application.diagnostics
    assert application.event_modifiers[0].operation is EffectOperation.ADD
    assert application.event_modifiers[0].value == Resolved(1.1)


def test_event_dependent_panel_modifier_is_blocked_in_stage_fifteen() -> None:
    definition = _definition()
    veil = next(
        item
        for item in definition.rule_items
        if item.rule_id == RuleItemId("rule:ye:1431:veil")
    )
    # A panel node with an event filter must not become a global snapshot edit.
    assert isinstance(veil.effects[0], ModifierEffect)
    effect = replace(
        veil.effects[0],
        result=replace(
            veil.effects[0].result,
            modifier_path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        ),
    )
    application = apply_matched_modifiers(
        (CharacterSnapshot(definition.character_id, 60, _stats()),),
        (),
        (effect,),
        definition.character_id,
    )
    assert application.diagnostics
    assert application.diagnostics[0].kind.value == "unsupported-calculator"


def test_derived_event_wrapper_keeps_application_identity_outside_domain_event() -> (
    None
):
    definition = _definition(cinema_level=6)
    entry = _entry(definition, "special-mingxin-guichen")
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == entry.main_damage_event
    )
    instantiated = instantiate_direct_damage_event(
        template,
        entry.multiplier_variants[0].multiplier,
        battle_state_id=BattleStateId("battle:wrapper"),
        target_enemy=EnemyId("enemy:wrapper"),
        created_at=0.0,
    )
    assert instantiated.semantic_id == entry.main_damage_event.semantic_id
    assert not hasattr(instantiated.event.metadata, "semantic_id")
    assert not hasattr(instantiated.event.metadata, "source_rule_item_id")


def test_event_cycle_and_duplicate_semantic_events_are_blocking_not_silent() -> None:
    definition = _definition(cinema_level=6)
    request = _request(
        definition,
        "special-mingxin-guichen",
        enabled=("rule:ye:1431:cinema6",),
    )
    service = DirectMoveApplicationService()
    c6 = next(
        item
        for item in definition.rule_items
        if item.rule_id == RuleItemId("rule:ye:1431:cinema6")
    )
    creation = next(
        effect for effect in c6.effects if isinstance(effect, EventCreationEffect)
    )
    target_template_id = creation.result.event_template_id
    assert target_template_id is not None
    cycle = service._create_derived_event(
        request,
        creation,
        (target_template_id,),
        set(),
    )
    assert isinstance(cycle, CalculationDiagnostic)
    assert cycle.message.startswith("EventCreation")
    duplicate = service._create_derived_event(
        request,
        creation,
        (),
        {
            _entry(definition, "special-mingxin-guichen")
            .derived_damage_events[0]
            .semantic_id
        },
    )
    assert isinstance(duplicate, CalculationDiagnostic)
    assert duplicate.message.startswith("the same semantic event")


def test_router_distinguishes_missing_calculator_from_missing_data() -> None:
    definition = _definition()
    entry = _entry(definition, "basic-fast-1")
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == entry.main_damage_event
    )
    direct_event = instantiate_direct_damage_event(
        template,
        entry.multiplier_variants[0].multiplier,
        battle_state_id=BattleStateId("battle:router"),
        target_enemy=EnemyId("enemy:router"),
        created_at=0.0,
    ).event
    unsupported_event = UnresolvedSharpExplosionDamageEvent(
        metadata=direct_event.metadata,
        unresolved=Unresolved(
            reason=UnresolvedReason.NOT_IMPLEMENTED_IN_SPEC,
            notes="sharp explosion is not implemented",
        ),
    )
    result = CalculationRouter().calculate(unsupported_event, None)  # type: ignore[arg-type]
    assert result.status is EventCalculationStatus.UNSUPPORTED_CALCULATOR
    assert result.result is None
    assert result.diagnostics[0].kind.value == "unsupported-calculator"


def test_cinema_six_creates_per_event_traces_and_does_not_recurse() -> None:
    definition = _definition(cinema_level=6)
    request = _request(
        definition,
        "special-mingxin-guichen",
        enabled=("rule:ye:1431:hedao", "rule:ye:1431:cinema6"),
        base_modifiers=(_stun_modifier(1.5),),
    )
    execution = calculate_move(request)

    assert len(execution.output.events) == 2
    assert len(execution.event_traces) == 2
    assert execution.output.known_total == pytest.approx(
        sum(item.known_value for item in execution.output.events)  # type: ignore[arg-type]
    )
    main_trace, derived_trace = execution.event_traces
    main_c6 = next(
        item
        for item in main_trace.rule_matches
        if item.rule_id == RuleItemId("rule:ye:1431:cinema6")
    )
    derived_c6 = next(
        item
        for item in derived_trace.rule_matches
        if item.rule_id == RuleItemId("rule:ye:1431:cinema6")
    )
    assert any(item.status is EffectMatchStatus.MATCHED for item in main_c6.effects)
    assert all(
        item.status is EffectMatchStatus.NOT_MATCHED for item in derived_c6.effects
    )
    assert derived_trace.created_by_effect_id == EffectId(
        "effect:ye:1431:cinema6:guichen-extra"
    )
    assert (
        execution.output.events[1].semantic_id != execution.output.events[0].semantic_id
    )


def test_crit_display_mode_uses_temporary_snapshot_only() -> None:
    definition = _definition()
    expected = calculate_move(
        _request(
            definition,
            "basic-fast-1",
            enabled=("rule:ye:1431:hedao",),
            mode=CritDisplayMode.EXPECTED,
        )
    )
    non_crit = calculate_move(
        _request(
            definition,
            "basic-fast-1",
            enabled=("rule:ye:1431:hedao",),
            mode=CritDisplayMode.NON_CRIT,
        )
    )
    full_crit = calculate_move(
        _request(
            definition,
            "basic-fast-1",
            enabled=("rule:ye:1431:hedao",),
            mode=CritDisplayMode.FULL_CRIT,
        )
    )

    assert _known_value(non_crit.output.events[0]) < _known_value(
        expected.output.events[0]
    )
    assert _known_value(expected.output.events[0]) < _known_value(
        full_crit.output.events[0]
    )
    assert expected.resolved_character_snapshots[
        0
    ].settlement_stats.crit_rate == Resolved(0.65)
    assert non_crit.resolved_character_snapshots[
        0
    ].settlement_stats.crit_rate == Resolved(0.65)
