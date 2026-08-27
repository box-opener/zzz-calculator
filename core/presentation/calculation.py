"""Browser-facing calculation result views.

The assembler deliberately preserves one result envelope per crit mode.  It
never recomputes totals or node values; it only converts application objects
to stable JSON-shaped presentation data.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.application.execution.contracts import DamageEventExecutionTrace
from core.application.output import CritDisplayMode, DamageEventCalculationOutput
from core.calculation.nodes import CalculationNodeValue
from core.types import CharacterSnapshot, Resolved, Unresolved

from .diagnostics import DiagnosticView


@dataclass(frozen=True, slots=True)
class CalculationNodeValueView:
    node: str
    value: float | None
    read_rule: str
    unresolved: str | None = None


@dataclass(frozen=True, slots=True)
class ModifierView:
    effect_id: str
    modifier_path: str
    operation: str
    value: float | None
    unresolved: str | None = None
    recipient_character_id: str | None = None


@dataclass(frozen=True, slots=True)
class EffectMatchView:
    effect_id: str
    status: str
    diagnostics: tuple[DiagnosticView, ...]


@dataclass(frozen=True, slots=True)
class RuleMatchView:
    rule_id: str
    status: str
    effects: tuple[EffectMatchView, ...]
    diagnostics: tuple[DiagnosticView, ...]


@dataclass(frozen=True, slots=True)
class EventTraceView:
    semantic_id: str
    rule_matches: tuple[RuleMatchView, ...]
    applied_modifiers: tuple[ModifierView, ...]
    event_stat_modifiers: tuple[ModifierView, ...]
    event_multiplier_modifiers: tuple[ModifierView, ...]
    created_by_effect_id: str | None
    diagnostics: tuple[DiagnosticView, ...]


@dataclass(frozen=True, slots=True)
class PanelSnapshotView:
    character_id: str
    level: int
    stats: dict[str, float | None]


@dataclass(frozen=True, slots=True)
class PanelTraceView:
    recipient_character_id: str
    owner_character_id: str | None
    rule_item_id: str | None
    effect_id: str
    modifier_path: str
    operation: str
    resolved_value: float
    stack_count: int


@dataclass(frozen=True, slots=True)
class DamageEventModeView:
    value: float | None
    known_value: float | None
    status: str
    diagnostics: tuple[DiagnosticView, ...]
    unresolved: tuple[str, ...]
    calculation_breakdown: tuple[CalculationNodeValueView, ...]


@dataclass(frozen=True, slots=True)
class DamageEventView:
    semantic_id: str
    label: str
    damage_type: str
    damage_subtype: str | None
    repeat_count: int
    modes: dict[str, DamageEventModeView]
    common_application_trace: EventTraceView | None


@dataclass(frozen=True, slots=True)
class MoveTotalsView:
    value: float | None
    complete: bool
    diagnostics: tuple[DiagnosticView, ...]


@dataclass(frozen=True, slots=True)
class CalculationView:
    schema_version: str
    move_entry_id: str
    events: tuple[DamageEventView, ...]
    totals: dict[str, MoveTotalsView]
    resolved_character_snapshots: tuple[PanelSnapshotView, ...]
    panel_traces: tuple[PanelTraceView, ...]
    diagnostics: tuple[DiagnosticView, ...]


MoveCalculationView = CalculationView


def calculation_node_view(value: CalculationNodeValue) -> CalculationNodeValueView:
    numeric, unresolved = _resolvable_view(value.value)
    return CalculationNodeValueView(
        node=value.node.value,
        value=numeric,
        read_rule=value.read_rule.value,
        unresolved=unresolved,
    )


def modifier_view(modifier, *, recipient_character_id: str | None = None) -> ModifierView:
    numeric, unresolved = _resolvable_view(modifier.value)
    return ModifierView(
        effect_id=str(modifier.effect_id),
        modifier_path=modifier.modifier_path.value,
        operation=modifier.operation.value,
        value=numeric,
        unresolved=unresolved,
        recipient_character_id=recipient_character_id,
    )


def event_trace_view(trace: DamageEventExecutionTrace) -> EventTraceView:
    return EventTraceView(
        semantic_id=str(trace.semantic_id),
        rule_matches=tuple(
            RuleMatchView(
                rule_id=str(match.rule_id),
                status=match.status.value,
                effects=tuple(
                    EffectMatchView(
                        effect_id=str(effect.effect_id),
                        status=effect.status.value,
                        diagnostics=tuple(
                            DiagnosticView(
                                diagnostic_id=str(item.diagnostic_id),
                                kind=item.kind.value,
                                message=item.message,
                                blocking=item.blocking,
                                original_text=item.original_text,
                                candidates=item.candidates,
                            )
                            for item in effect.diagnostics
                        ),
                    )
                    for effect in match.effects
                ),
                diagnostics=tuple(
                    DiagnosticView(
                        diagnostic_id=str(item.diagnostic_id),
                        kind=item.kind.value,
                        message=item.message,
                        blocking=item.blocking,
                        original_text=item.original_text,
                        candidates=item.candidates,
                    )
                    for item in match.diagnostics
                ),
            )
            for match in trace.rule_matches
        ),
        applied_modifiers=tuple(modifier_view(item) for item in trace.applied_modifiers),
        event_stat_modifiers=tuple(
            modifier_view(
                item.as_modifier(),
                recipient_character_id=str(item.recipient),
            )
            for item in trace.event_stat_modifiers
        ),
        event_multiplier_modifiers=tuple(
            modifier_view(item) for item in trace.event_multiplier_modifiers
        ),
        created_by_effect_id=(
            str(trace.created_by_effect_id)
            if trace.created_by_effect_id is not None
            else None
        ),
        diagnostics=tuple(
            DiagnosticView(
                diagnostic_id=str(item.diagnostic_id),
                kind=item.kind.value,
                message=item.message,
                blocking=item.blocking,
                original_text=item.original_text,
                candidates=item.candidates,
            )
            for item in trace.diagnostics
        ),
    )


def panel_snapshot_view(snapshot: CharacterSnapshot) -> PanelSnapshotView:
    stats = snapshot.settlement_stats
    values = {
        "hp": stats.hp,
        "attack": stats.attack,
        "defense": stats.defense,
        "impact": stats.impact,
        "crit_rate": stats.crit_rate,
        "crit_damage": stats.crit_damage,
        "anomaly_mastery": stats.anomaly_mastery,
        "anomaly_proficiency": stats.anomaly_proficiency,
        "penetration_rate": stats.penetration_rate,
        "penetration_flat": stats.penetration_flat,
        "energy_regen": stats.energy_regen,
    }
    return PanelSnapshotView(
        character_id=str(snapshot.character_id),
        level=snapshot.level,
        stats={key: _resolvable_view(value)[0] for key, value in values.items()},
    )


def _mode_view(item: DamageEventCalculationOutput) -> DamageEventModeView:
    result = item.result
    return DamageEventModeView(
        value=result.value if result is not None else None,
        known_value=item.known_value,
        status=item.status.value,
        diagnostics=tuple(
            DiagnosticView(
                diagnostic_id=str(diagnostic.diagnostic_id),
                kind=diagnostic.kind.value,
                message=diagnostic.message,
                blocking=diagnostic.blocking,
                original_text=diagnostic.original_text,
                candidates=diagnostic.candidates,
            )
            for diagnostic in item.diagnostics
        ),
        unresolved=(
            tuple(unresolved.notes for unresolved in result.unresolved)
            if result is not None
            else ()
        ),
        calculation_breakdown=(
            tuple(calculation_node_view(value) for value in result.breakdown)
            if result is not None
            else ()
        ),
    )


def _resolvable_view(value) -> tuple[float | None, str | None]:
    if isinstance(value, Resolved):
        return float(value.value), None
    if isinstance(value, Unresolved):
        return None, value.notes
    return None, "unknown unresolved value"


__all__ = [
    "CalculationNodeValueView",
    "CalculationView",
    "DamageEventModeView",
    "DamageEventView",
    "EffectMatchView",
    "EventTraceView",
    "MoveCalculationView",
    "MoveTotalsView",
    "PanelSnapshotView",
    "PanelTraceView",
    "RuleMatchView",
    "calculation_node_view",
    "event_trace_view",
    "panel_snapshot_view",
]
