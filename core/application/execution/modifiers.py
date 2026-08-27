"""Resolve matched Effects into settlement snapshots and calculator Modifiers."""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.types import (
    AlwaysCondition,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    DirectDamageEvent,
    DynamicIdentity,
    DynamicIdentityFilter,
    EffectId,
    EffectOperation,
    EventCreationEffect,
    Modifier,
    ModifierEffect,
    Effect,
    EffectTarget,
    InitialCharacterSnapshot,
    PanelStatDerivedValue,
    Resolved,
    StandardCritRule,
    Unresolved,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..ids import RuleItemId
from .contracts import EventStatModifier


@dataclass(frozen=True, slots=True)
class MatchedEffectApplication:
    """A matched Effect together with its owning RuleItem's stack count."""

    effect: Effect
    rule_item_id: RuleItemId | None = None
    stack_count: int = 1

    def __post_init__(self) -> None:
        if self.stack_count < 0:
            raise ValueError("matched Effect stack_count must be non-negative")


_PANEL_NODES = frozenset(
    {
        CalculationNode.CHARACTER_CURRENT_MAX_HP,
        CalculationNode.CHARACTER_CURRENT_ATTACK,
        CalculationNode.CHARACTER_CURRENT_DEFENSE,
        CalculationNode.CHARACTER_CURRENT_IMPACT,
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
        CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_FLAT,
        CalculationNode.CHARACTER_CURRENT_ENERGY_REGEN,
        CalculationNode.CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
    }
)


@dataclass(frozen=True, slots=True)
class ModifierApplicationResult:
    character_snapshots: tuple[CharacterSnapshot, ...]
    event_modifiers: tuple[Modifier, ...]
    event_stat_modifiers: tuple[Modifier, ...] = ()
    event_multiplier_modifiers: tuple[Modifier, ...] = ()
    applied_panel_effect_ids: frozenset[EffectId] = frozenset()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


def apply_matched_modifiers(
    base_character_snapshots: tuple[CharacterSnapshot, ...],
    base_calculation_modifiers: tuple[Modifier, ...],
    matched_effects: tuple[object, ...],
    current_operator: CharacterId,
    *,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...] = (),
    event: object | None = None,
    apply_panel: bool = True,
    applied_panel_effect_ids: frozenset[EffectId] = frozenset(),
) -> ModifierApplicationResult:
    """Apply event-independent panel Effects and normalize event modifiers.

    Effects have already passed target/condition/filter matching.  This layer
    therefore applies only their declared result operations; it never searches
    BattleState or resolves why an Effect matched.
    """

    diagnostics: list[CalculationDiagnostic] = []
    snapshots = tuple(base_character_snapshots)
    for modifier in base_calculation_modifiers:
        if modifier.operation is not EffectOperation.ADD:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "base-operation",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "base calculation modifiers must already use ADD",
                )
            )
        if modifier.modifier_path in _PANEL_NODES:
            diagnostics.append(
                _diagnostic(
                    str(modifier.effect_id),
                    "base-panel-node",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "base calculation modifiers cannot contain panel nodes",
                )
            )

    panel_effects: list[tuple[ModifierEffect, int]] = []
    rule_modifiers: list[Modifier] = []
    event_stat_modifiers: list[EventStatModifier] = []
    event_multiplier_modifiers: list[Modifier] = []
    for application in matched_effects:
        if isinstance(application, MatchedEffectApplication):
            effect = application.effect
            stack_count = application.stack_count
        else:
            effect = application
            stack_count = 1
        if not isinstance(effect, ModifierEffect):
            if stack_count != 1 and not isinstance(effect, EventCreationEffect):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "stack-effect",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "stacked non-Modifier effects are unsupported",
                    )
                )
            continue
        effect = _resolve_effect_value(
            effect,
            initial_character_snapshots,
            diagnostics,
        )
        if effect is None:
            continue
        if effect.result.modifier_path in _PANEL_NODES and apply_panel:
            if _is_recipient_panel_effect(effect):
                panel_effects.append((effect, stack_count))
                continue
            event_stat = _event_stat_modifier(
                effect,
                event,
                stack_count,
                diagnostics,
            )
            if event_stat is not None:
                event_stat_modifiers.append(event_stat)
            continue
        if effect.result.modifier_path in _PANEL_NODES:
            if _is_recipient_panel_effect(effect):
                if effect.rule.effect_id not in applied_panel_effect_ids:
                    diagnostics.append(
                        _diagnostic(
                            str(effect.rule.effect_id),
                            "derived-panel",
                            DiagnosticKind.UNSUPPORTED_CALCULATOR,
                            "a panel Effect matched a derived event but was not applied globally",
                        )
                    )
                continue
            event_stat = _event_stat_modifier(
                effect,
                event,
                stack_count,
                diagnostics,
            )
            if event_stat is not None:
                event_stat_modifiers.append(event_stat)
            continue
        if effect.result.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER:
            event_multiplier = _event_multiplier_modifier(
                effect,
                diagnostics,
                stack_count,
            )
            if event_multiplier is not None:
                event_multiplier_modifiers.append(event_multiplier)
            continue
        event_modifier = _event_modifier(effect, diagnostics, stack_count)
        if event_modifier is not None:
            rule_modifiers.append(event_modifier)

    snapshots, applied_panel_ids = _apply_panel_effects(
        snapshots,
        panel_effects,
        current_operator,
        diagnostics,
    )
    event_modifiers = _normalize_event_modifiers(
        base_calculation_modifiers,
        rule_modifiers,
        diagnostics,
    )
    return ModifierApplicationResult(
        character_snapshots=snapshots,
        event_modifiers=event_modifiers,
        event_stat_modifiers=tuple(event_stat_modifiers),
        event_multiplier_modifiers=tuple(event_multiplier_modifiers),
        applied_panel_effect_ids=applied_panel_ids,
        diagnostics=tuple(diagnostics),
    )


def _resolve_effect_value(
    effect: ModifierEffect,
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...],
    diagnostics: list[CalculationDiagnostic],
) -> ModifierEffect | None:
    value = effect.result.value
    if not isinstance(value, PanelStatDerivedValue):
        return effect

    source = next(
        (
            item
            for item in initial_character_snapshots
            if item.character_id == value.source_character_id
        ),
        None,
    )
    if source is None:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "derived-value-source",
                DiagnosticKind.MISSING_DATA,
                "derived panel value is missing its initial character snapshot",
            )
        )
        return None

    source_attack = source.initial_stats.attack
    coefficient = value.coefficient
    cap_max = value.cap_max
    if not isinstance(source_attack, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "derived-value-attack",
                DiagnosticKind.MISSING_DATA,
                "initial attack is unresolved for a derived panel value",
            )
        )
        return None
    if not isinstance(coefficient, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "derived-value-coefficient",
                DiagnosticKind.MISSING_DATA,
                coefficient.notes,
            )
        )
        return None
    result = source_attack.value * coefficient.value
    if cap_max is not None:
        if not isinstance(cap_max, Resolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "derived-value-cap",
                    DiagnosticKind.MISSING_DATA,
                    cap_max.notes,
                )
            )
            return None
        result = min(result, cap_max.value)
    return replace(
        effect,
        result=replace(effect.result, value=Resolved(result)),
    )


def _is_recipient_panel_effect(effect: ModifierEffect) -> bool:
    rule = effect.rule
    if rule.trigger is None and (
        rule.condition is None or isinstance(rule.condition, AlwaysCondition)
    ) and not rule.filters:
        return True
    return (
        rule.target is EffectTarget.TEAM
        and rule.trigger is not None
        and rule.trigger.event_kind is BattleEventKind.SUPPORT_ENTRY
        and rule.trigger.move_id is None
        and (rule.condition is None or isinstance(rule.condition, AlwaysCondition))
        and bool(rule.filters)
        and all(
            isinstance(item, DynamicIdentityFilter)
            and item.identity is DynamicIdentity.SUPPORT_ENTRY_CHARACTER
            for item in rule.filters
        )
    )


def _event_stat_modifier(
    effect: ModifierEffect,
    event: object | None,
    stack_count: int,
    diagnostics: list[CalculationDiagnostic],
) -> EventStatModifier | None:
    if not isinstance(event, DirectDamageEvent) or not isinstance(
        event.crit_rule, StandardCritRule
    ):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-recipient",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "event stat modifiers require a standard-crit damage event",
            )
        )
        return None
    if effect.result.modifier_path is not CalculationNode.CHARACTER_CURRENT_CRIT_RATE:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-node",
                DiagnosticKind.UNSUPPORTED_CALCULATOR,
                "Stage-016 only supports event-level current crit-rate modifiers",
            )
        )
        return None
    if effect.result.operation is not EffectOperation.ADD:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "event-level crit-rate modifiers support ADD only",
            )
        )
        return None
    value = effect.result.value
    if not isinstance(value, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-stat-value",
                DiagnosticKind.MISSING_DATA,
                value.notes,
            )
        )
        return None
    return EventStatModifier(
        effect_id=effect.rule.effect_id,
        recipient=event.crit_rule.stat_owner,
        modifier_path=effect.result.modifier_path,
        operation=effect.result.operation,
        value=Resolved(value.value * stack_count),
        snapshot_rule=effect.rule.snapshot_rule,
    )


def _event_multiplier_modifier(
    effect: ModifierEffect,
    diagnostics: list[CalculationDiagnostic],
    stack_count: int,
) -> Modifier | None:
    if effect.result.operation is not EffectOperation.MULTIPLY:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-multiplier-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "event skill multipliers support MULTIPLY only",
            )
        )
        return None
    if stack_count != 1:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "stack-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "stacked non-ADD modifier operation has no defined semantics",
            )
        )
        return None
    value = effect.result.value
    if not isinstance(value, Resolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "event-multiplier-value",
                DiagnosticKind.MISSING_DATA,
                value.notes,
            )
        )
        return None
    return Modifier(
        effect_id=effect.rule.effect_id,
        modifier_path=effect.result.modifier_path,
        operation=effect.result.operation,
        value=value,
        snapshot_rule=effect.rule.snapshot_rule,
    )


def _event_modifier(
    effect: ModifierEffect,
    diagnostics: list[CalculationDiagnostic],
    stack_count: int = 1,
) -> Modifier | None:
    value = effect.result.value
    if isinstance(value, Unresolved):
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "unresolved-value",
                DiagnosticKind.MISSING_DATA,
                value.notes,
            )
        )
        return None
    if stack_count != 1 and effect.result.operation is not EffectOperation.ADD:
        diagnostics.append(
            _diagnostic(
                str(effect.rule.effect_id),
                "stack-operation",
                DiagnosticKind.AMBIGUOUS_SEMANTICS,
                "stacked non-ADD modifier operation has no defined semantics",
            )
        )
        return None
    if stack_count != 1 and isinstance(value, Resolved):
        value = Resolved(value.value * stack_count)
    return Modifier(
        effect_id=effect.rule.effect_id,
        modifier_path=effect.result.modifier_path,
        operation=effect.result.operation,
        value=value,
        snapshot_rule=effect.rule.snapshot_rule,
    )


def _apply_panel_effects(
    snapshots: tuple[CharacterSnapshot, ...],
    effects: list[tuple[ModifierEffect, int]],
    current_operator: CharacterId,
    diagnostics: list[CalculationDiagnostic],
) -> tuple[tuple[CharacterSnapshot, ...], frozenset[EffectId]]:
    index = {item.character_id: item for item in snapshots}
    target = index.get(current_operator)
    if target is None and effects:
        diagnostics.append(
            _diagnostic(
                str(current_operator),
                "missing-panel-snapshot",
                DiagnosticKind.MISSING_DATA,
                "matched panel Effect has no current-operator snapshot",
            )
        )
        return snapshots, frozenset()
    if target is None:
        return snapshots, frozenset()

    updated_stats = target.settlement_stats
    applied_effect_ids: set[EffectId] = set()
    for effect, stack_count in effects:
        if not _is_recipient_panel_effect(effect):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-recipient",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "panel Effect does not have a supported recipient scope",
                )
            )
            continue
        if effect.result.operation is not EffectOperation.ADD:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-operation",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "Stage-015 panel Effects support ADD only",
                )
            )
            continue
        value = effect.result.value
        if isinstance(value, Unresolved):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-value",
                    DiagnosticKind.MISSING_DATA,
                    value.notes,
                )
            )
            continue
        if effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_RATE:
            current = updated_stats.crit_rate
            if isinstance(current, Unresolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        "current crit rate is unresolved",
                    )
                )
                continue
            updated_stats = replace(
                updated_stats,
                crit_rate=Resolved(current.value + value.value * stack_count),
            )
            applied_effect_ids.add(effect.rule.effect_id)
        elif effect.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS:
            current = updated_stats.attack
            if isinstance(current, Unresolved):
                diagnostics.append(
                    _diagnostic(
                        str(effect.rule.effect_id),
                        "panel-base-value",
                        DiagnosticKind.MISSING_DATA,
                        "current attack is unresolved",
                    )
                )
                continue
            updated_stats = replace(
                updated_stats,
                attack=Resolved(current.value + value.value * stack_count),
            )
            applied_effect_ids.add(effect.rule.effect_id)
        else:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "panel-node",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    f"Stage-015 does not resolve panel node {effect.result.modifier_path.value}",
                )
            )

    index[current_operator] = replace(
        target,
        settlement_stats=updated_stats,
    )
    return (
        tuple(index[item.character_id] for item in snapshots),
        frozenset(applied_effect_ids),
    )


def _normalize_event_modifiers(
    base_modifiers: tuple[Modifier, ...],
    rule_modifiers: list[Modifier],
    diagnostics: list[CalculationDiagnostic],
) -> tuple[Modifier, ...]:
    by_path: dict[CalculationNode, list[Modifier]] = {}
    for modifier in (*base_modifiers, *rule_modifiers):
        by_path.setdefault(modifier.modifier_path, []).append(modifier)

    normalized: list[Modifier] = []
    for path, modifiers in by_path.items():
        overrides = [
            item for item in modifiers if item.operation is EffectOperation.OVERRIDE
        ]
        if len(overrides) > 1:
            diagnostics.append(
                _diagnostic(
                    path.value,
                    "multiple-overrides",
                    DiagnosticKind.AMBIGUOUS_SEMANTICS,
                    "multiple OVERRIDE modifiers target the same calculation node",
                )
            )
            continue
        if overrides:
            rule_conflicts = [
                item
                for item in rule_modifiers
                if item.modifier_path == path
                and item.operation is not EffectOperation.OVERRIDE
            ]
            if rule_conflicts:
                diagnostics.append(
                    _diagnostic(
                        path.value,
                        "override-operation-conflict",
                        DiagnosticKind.AMBIGUOUS_SEMANTICS,
                        "an OVERRIDE and another rule operation have no defined order",
                    )
                )
                continue
            normalized.append(replace(overrides[0], operation=EffectOperation.ADD))
            continue
        for modifier in modifiers:
            if modifier.operation is EffectOperation.ADD:
                normalized.append(modifier)
            else:
                diagnostics.append(
                    _diagnostic(
                        str(modifier.effect_id),
                        "unsupported-operation",
                        DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        f"unsupported event modifier operation: {modifier.operation.value}",
                    )
                )
    return tuple(normalized)


def _diagnostic(
    subject_id: str,
    suffix: str,
    kind: DiagnosticKind,
    message: str,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"application:{subject_id}:{suffix}"),
        kind=kind,
        message=message,
        blocking=True,
    )
