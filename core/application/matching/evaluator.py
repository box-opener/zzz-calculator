"""Pure target, trigger, condition, and filter predicates."""

from __future__ import annotations

from core.types import (
    AllCondition,
    AlwaysCondition,
    AnyCondition,
    AnyFilter,
    CharacterFilter,
    CharacterRoleFilter,
    CalculationNode,
    CreatedByEffectFilter,
    DamageDealerIdentityFilter,
    DamageSubtypeFilter,
    DamageTagFilter,
    DamageTypeFilter,
    DamageDealerFilter,
    DynamicIdentityCondition,
    DynamicIdentityFilter,
    EffectFilter,
    EffectTarget,
    ElementFilter,
    EnemyStateFilter,
    FieldPositionFilter,
    MoveIdFilter,
    NotCondition,
    NotFilter,
    OperationStateFilter,
    PanelStatThresholdCondition,
    Resolved,
    StatePresentCondition,
    RuleStackCondition,
    SkillGroupFilter,
    Unresolved,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..ids import RuleItemId
from .context import EffectMatchContext
from .identity import DynamicIdentityResolver
from .result import EffectMatchStatus


def diagnostic(
    effect_id: str,
    suffix: str,
    kind: DiagnosticKind,
    message: str,
    *,
    blocking: bool,
    original_text: str | None = None,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"{effect_id}:{suffix}"),
        kind=kind,
        message=message,
        blocking=blocking,
        original_text=original_text,
    )


MatchEvaluation = tuple[
    EffectMatchStatus,
    tuple[CalculationDiagnostic, ...],
]


def combine_conjunction(
    evaluations: tuple[MatchEvaluation, ...],
) -> MatchEvaluation:
    statuses = tuple(item[0] for item in evaluations)
    if EffectMatchStatus.NOT_MATCHED in statuses:
        return EffectMatchStatus.NOT_MATCHED, _non_blocking_diagnostics(evaluations)
    if EffectMatchStatus.BLOCKED in statuses:
        return EffectMatchStatus.BLOCKED, _all_diagnostics(evaluations)
    return EffectMatchStatus.MATCHED, _all_diagnostics(evaluations)


def combine_disjunction(
    evaluations: tuple[MatchEvaluation, ...],
) -> MatchEvaluation:
    statuses = tuple(item[0] for item in evaluations)
    if EffectMatchStatus.MATCHED in statuses:
        return EffectMatchStatus.MATCHED, _non_blocking_diagnostics(evaluations)
    if EffectMatchStatus.BLOCKED in statuses:
        return EffectMatchStatus.BLOCKED, _all_diagnostics(evaluations)
    return EffectMatchStatus.NOT_MATCHED, _all_diagnostics(evaluations)


def match_target(
    target: EffectTarget,
    owner,
    context: EffectMatchContext,
    effect_id: str,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    if owner is not None and context.character(owner) is None:
        return EffectMatchStatus.NOT_MATCHED, ()
    if target is EffectTarget.SELF:
        if owner is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    diagnostic(
                        effect_id,
                        "missing-owner",
                        DiagnosticKind.MISSING_DATA,
                        "self-targeted Effect has no owner",
                        blocking=True,
                    ),
                ),
            )
        if owner != context.current_operator:
            return EffectMatchStatus.NOT_MATCHED, ()
    elif target in {EffectTarget.TEAM, EffectTarget.TEAM_OTHER}:
        if target is EffectTarget.TEAM_OTHER and owner is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    diagnostic(
                        effect_id,
                        "missing-owner",
                        DiagnosticKind.MISSING_DATA,
                        "team-other Effect requires an owner to exclude",
                        blocking=True,
                    ),
                ),
            )
        if context.current_operator not in {
            profile.character_id for profile in context.team
        }:
            return EffectMatchStatus.BLOCKED, ()
    return EffectMatchStatus.MATCHED, ()


def match_trigger(
    effect_rule,
    context: EffectMatchContext,
    effect_id: str,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    selector = effect_rule.trigger
    if selector is None:
        return EffectMatchStatus.MATCHED, ()

    facts = [fact for fact in context.trigger_facts if str(fact.effect_id) == effect_id]
    if not facts:
        return (
            EffectMatchStatus.BLOCKED,
            (
                diagnostic(
                    effect_id,
                    "missing-trigger-fact",
                    DiagnosticKind.MISSING_DATA,
                    "Effect trigger has no scenario trigger fact",
                    blocking=True,
                ),
            ),
        )
    for fact in facts:
        if fact.event_kind is selector.event_kind and (
            selector.move_id is None or fact.move_id == selector.move_id
        ):
            return EffectMatchStatus.MATCHED, ()
    return EffectMatchStatus.NOT_MATCHED, ()


def match_condition(
    condition,
    context: EffectMatchContext,
    owner,
    effect_id: str,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    if condition is None or isinstance(condition, AlwaysCondition):
        return EffectMatchStatus.MATCHED, ()
    if isinstance(condition, Unresolved):
        return (
            EffectMatchStatus.BLOCKED,
            (
                diagnostic(
                    effect_id,
                    "unresolved-condition",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    condition.notes,
                    blocking=True,
                    original_text=condition.original_text,
                ),
            ),
        )
    if isinstance(condition, AllCondition):
        return _combine_nested(
            tuple(
                match_condition(item, context, owner, effect_id)
                for item in condition.conditions
            )
        )
    if isinstance(condition, AnyCondition):
        return _combine_any_nested(
            tuple(
                match_condition(item, context, owner, effect_id)
                for item in condition.conditions
            )
        )
    if isinstance(condition, NotCondition):
        status, diagnostics = match_condition(
            condition.condition,
            context,
            owner,
            effect_id,
        )
        if status is EffectMatchStatus.MATCHED:
            return EffectMatchStatus.NOT_MATCHED, diagnostics
        if status is EffectMatchStatus.NOT_MATCHED:
            return EffectMatchStatus.MATCHED, diagnostics
        return status, diagnostics
    if isinstance(condition, StatePresentCondition):
        profiles = _state_profiles(condition.subject, owner, context)
        if profiles is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    diagnostic(
                        effect_id,
                        "missing-state-subject",
                        DiagnosticKind.MISSING_DATA,
                        "cannot resolve StatePresentCondition subject",
                        blocking=True,
                    ),
                ),
            )
        return (
            (
                EffectMatchStatus.MATCHED
                if any(condition.state_id in profile.states for profile in profiles)
                else EffectMatchStatus.NOT_MATCHED
            ),
            (),
        )
    if isinstance(condition, RuleStackCondition):
        if (
            condition.requires_rule_enabled
            and RuleItemId(condition.rule_item_id)
            not in context.scenario.enabled_rule_item_ids
        ):
            return EffectMatchStatus.NOT_MATCHED, ()
        selected = context.scenario.selected_stack(RuleItemId(condition.rule_item_id))
        if selected is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    diagnostic(
                        effect_id,
                        "missing-rule-stack",
                        DiagnosticKind.MISSING_DATA,
                        f"missing resolved RuleItem stack: {condition.rule_item_id}",
                        blocking=True,
                    ),
                ),
            )
        return (
            (
                EffectMatchStatus.MATCHED
                if selected == condition.required_value
                else EffectMatchStatus.NOT_MATCHED
            ),
            (),
        )
    if isinstance(condition, PanelStatThresholdCondition):
        value = _panel_threshold_value(condition, context)
        if value is None:
            return (
                EffectMatchStatus.BLOCKED,
                (
                    diagnostic(
                        effect_id,
                        "missing-panel-threshold-value",
                        DiagnosticKind.MISSING_DATA,
                        f"missing resolved panel value for {condition.source_node.value}",
                        blocking=True,
                    ),
                ),
            )
        return (
            (
                EffectMatchStatus.MATCHED
                if value >= condition.minimum
                else EffectMatchStatus.NOT_MATCHED
            ),
            (),
        )
    if isinstance(condition, DynamicIdentityCondition):
        if owner is None:
            return EffectMatchStatus.NOT_MATCHED, ()
        resolution = DynamicIdentityResolver().resolve(
            condition.identity,
            context,
            effect_id,
        )
        if resolution.identities is None:
            assert resolution.diagnostic is not None
            return EffectMatchStatus.BLOCKED, (resolution.diagnostic,)
        return (
            (
                EffectMatchStatus.MATCHED
                if owner in resolution.identities
                else EffectMatchStatus.NOT_MATCHED
            ),
            (),
        )
    raise TypeError(f"unsupported condition type: {type(condition).__name__}")


def _panel_threshold_value(
    condition: PanelStatThresholdCondition,
    context: EffectMatchContext,
) -> float | None:
    if condition.source_node in {
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
    }:
        current_snapshot = next(
            (
                item
                for item in context.calculation_context.character_snapshots
                if item.character_id == condition.source_character_id
            ),
            None,
        )
        if current_snapshot is None:
            value = None
        elif condition.source_node is CalculationNode.CHARACTER_CURRENT_CRIT_RATE:
            value = current_snapshot.settlement_stats.crit_rate
        elif condition.source_node is CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY:
            value = current_snapshot.settlement_stats.anomaly_proficiency
        else:
            value = current_snapshot.settlement_stats.anomaly_mastery
    else:
        initial_snapshot = next(
            (
                item
                for item in context.initial_character_snapshots
                if item.character_id == condition.source_character_id
            ),
            None,
        )
        if initial_snapshot is None:
            value = None
        elif condition.source_node is CalculationNode.CHARACTER_INITIAL_DEFENSE:
            value = initial_snapshot.initial_stats.defense
        else:
            value = initial_snapshot.initial_stats.anomaly_mastery
    return float(value.value) if isinstance(value, Resolved) else None


def match_filters(
    filters: tuple[EffectFilter, ...],
    context: EffectMatchContext,
    effect_id: str,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    return combine_conjunction(
        tuple(match_filter(item, context, effect_id) for item in filters)
    )


def match_filter(
    item: EffectFilter,
    context: EffectMatchContext,
    effect_id: str,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    if isinstance(item, Unresolved):
        return (
            EffectMatchStatus.BLOCKED,
            (
                diagnostic(
                    effect_id,
                    "unresolved-filter",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    item.notes,
                    blocking=True,
                    original_text=item.original_text,
                ),
            ),
        )
    if isinstance(item, AnyFilter):
        return combine_disjunction(
            tuple(match_filter(child, context, effect_id) for child in item.filters)
        )
    if isinstance(item, NotFilter):
        status, diagnostics = match_filter(item.filter, context, effect_id)
        if status is EffectMatchStatus.MATCHED:
            return EffectMatchStatus.NOT_MATCHED, diagnostics
        if status is EffectMatchStatus.NOT_MATCHED:
            return EffectMatchStatus.MATCHED, diagnostics
        return status, diagnostics

    event = context.current_event
    if isinstance(item, ElementFilter):
        return _bool_decision(event.metadata.element is item.element)
    if isinstance(item, DamageTypeFilter):
        return _bool_decision(event.damage_type is item.damage_type)
    if isinstance(item, DamageSubtypeFilter):
        return _bool_decision(event.damage_subtype is item.damage_subtype)
    if isinstance(item, DamageTagFilter):
        return _bool_decision(item.damage_tag in event.metadata.damage_tags)
    if isinstance(item, SkillGroupFilter):
        return _bool_decision(event.metadata.skill_group is item.skill_group)
    if isinstance(item, MoveIdFilter):
        return _bool_decision(event.metadata.move_id == item.move_id)
    if isinstance(item, EnemyStateFilter):
        return _bool_decision(item.state_id in context.target.states)
    if isinstance(item, CharacterFilter):
        return _bool_decision(context.current_operator is item.character_id)
    if isinstance(item, DamageDealerFilter):
        return _bool_decision(event.metadata.damage_dealer == item.character_id)
    if isinstance(item, CharacterRoleFilter):
        profile = context.character(context.current_operator)
        if profile is None:
            return EffectMatchStatus.BLOCKED, ()
        return _bool_decision(profile.role is item.role)
    if isinstance(item, FieldPositionFilter):
        profile = context.character(context.current_operator)
        if profile is None or profile.field_position is None:
            return EffectMatchStatus.BLOCKED, ()
        return _bool_decision(profile.field_position is item.position)
    if isinstance(item, OperationStateFilter):
        profile = context.character(context.current_operator)
        if profile is None or profile.operation_state is None:
            return EffectMatchStatus.BLOCKED, ()
        return _bool_decision(profile.operation_state is item.operation_state)
    if isinstance(item, DynamicIdentityFilter):
        resolution = DynamicIdentityResolver().resolve(
            item.identity,
            context,
            effect_id,
        )
        if resolution.identities is None:
            assert resolution.diagnostic is not None
            return EffectMatchStatus.BLOCKED, (resolution.diagnostic,)
        return _bool_decision(context.current_operator in resolution.identities)
    if isinstance(item, DamageDealerIdentityFilter):
        resolution = DynamicIdentityResolver().resolve(
            item.identity,
            context,
            effect_id,
        )
        if resolution.identities is None:
            assert resolution.diagnostic is not None
            return EffectMatchStatus.BLOCKED, (resolution.diagnostic,)
        return _bool_decision(event.metadata.damage_dealer in resolution.identities)
    if isinstance(item, CreatedByEffectFilter):
        return _bool_decision(context.created_by_effect_id == item.effect_id)
    raise TypeError(f"unsupported filter type: {type(item).__name__}")


def _bool_decision(
    value: bool,
) -> tuple[EffectMatchStatus, tuple[CalculationDiagnostic, ...]]:
    return (
        EffectMatchStatus.MATCHED if value else EffectMatchStatus.NOT_MATCHED,
        (),
    )


def _state_profiles(subject, owner, context: EffectMatchContext):
    if subject is EffectTarget.ENEMY:
        return (context.target,)
    if subject is EffectTarget.TEAM:
        return context.team
    if subject is EffectTarget.TEAM_OTHER:
        if owner is None:
            return None
        return tuple(item for item in context.team if item.character_id != owner)
    if subject is EffectTarget.SELF:
        if owner is None:
            return None
        profile = context.character(owner)
        return None if profile is None else (profile,)
    raise TypeError(f"unsupported StatePresentCondition subject: {subject}")


def _combine_nested(decisions):
    return combine_conjunction(decisions)


def _combine_any_nested(decisions):
    return combine_disjunction(decisions)


def _all_diagnostics(
    evaluations: tuple[MatchEvaluation, ...],
) -> tuple[CalculationDiagnostic, ...]:
    return tuple(
        diagnostic_item
        for _, item_diagnostics in evaluations
        for diagnostic_item in item_diagnostics
    )


def _non_blocking_diagnostics(
    evaluations: tuple[MatchEvaluation, ...],
) -> tuple[CalculationDiagnostic, ...]:
    return tuple(item for item in _all_diagnostics(evaluations) if not item.blocking)
