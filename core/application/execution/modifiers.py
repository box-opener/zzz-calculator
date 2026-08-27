"""Resolve matched Effects into settlement snapshots and calculator Modifiers."""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.types import (
    AlwaysCondition,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    EffectId,
    EffectOperation,
    Modifier,
    ModifierEffect,
    Effect,
    Resolved,
    Unresolved,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..ids import RuleItemId


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
    for application in matched_effects:
        if isinstance(application, MatchedEffectApplication):
            effect = application.effect
            stack_count = application.stack_count
        else:
            effect = application
            stack_count = 1
        if not isinstance(effect, ModifierEffect):
            continue
        if effect.result.modifier_path in _PANEL_NODES and apply_panel:
            panel_effects.append((effect, stack_count))
            continue
        if effect.result.modifier_path in _PANEL_NODES:
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
        applied_panel_effect_ids=applied_panel_ids,
        diagnostics=tuple(diagnostics),
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
        if effect.rule.trigger is not None:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "event-triggered-panel",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "event-triggered panel Effects are not supported in this stage",
                )
            )
            continue
        if effect.rule.condition is not None and not isinstance(
            effect.rule.condition, AlwaysCondition
        ):
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "conditional-panel",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "conditional panel Effects are not supported in this stage",
                )
            )
            continue
        if effect.rule.filters:
            diagnostics.append(
                _diagnostic(
                    str(effect.rule.effect_id),
                    "event-dependent-panel",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "event-dependent panel Effects are not supported in this stage",
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
