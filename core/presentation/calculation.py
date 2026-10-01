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
from core.types import (
    AnomalyEffectStrengthTrace,
    AnomalyStrengthFactor,
    BuildContributionTrace,
    CharacterSnapshot,
    Resolved,
    Unresolved,
)

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
    source_label: str | None
    modifier_path: str
    operation: str
    value: float | None
    unresolved: str | None = None
    recipient_character_id: str | None = None
    source_type: str | None = None


@dataclass(frozen=True, slots=True)
class EffectMatchView:
    effect_id: str
    source_label: str | None
    status: str
    diagnostics: tuple[DiagnosticView, ...]
    source_type: str | None = None


@dataclass(frozen=True, slots=True)
class RuleMatchView:
    rule_id: str
    source_label: str | None
    status: str
    effects: tuple[EffectMatchView, ...]
    diagnostics: tuple[DiagnosticView, ...]
    source_type: str | None = None


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
    stats: dict[str, object]


@dataclass(frozen=True, slots=True)
class PanelTraceView:
    recipient_character_id: str
    owner_character_id: str | None
    rule_item_id: str | None
    effect_id: str
    source_label: str | None
    modifier_path: str
    operation: str
    resolved_value: float
    stack_count: int
    source_type: str | None = None


@dataclass(frozen=True, slots=True)
class BuildContributionView:
    character_id: str
    contribution_id: str
    source_id: str
    source_type: str
    source_label: str
    stat: str
    layer: str
    value: float | None
    element: str | None
    unresolved: str | None = None


@dataclass(frozen=True, slots=True)
class DamageEventModeView:
    value: float | None
    known_value: float | None
    status: str
    diagnostics: tuple[DiagnosticView, ...]
    unresolved: tuple[str, ...]
    calculation_breakdown: tuple[CalculationNodeValueView, ...]
    anomaly_effect_strength_trace: "AnomalyEffectStrengthTraceView | None" = None
    anomaly_record_id: str | None = None


@dataclass(frozen=True, slots=True)
class AnomalyStrengthFactorView:
    factor: str
    value: float | None
    source_id: str | None
    source_label: str | None
    owner_character_id: str | None
    unresolved: str | None


@dataclass(frozen=True, slots=True)
class AnomalyContributorStrengthTraceView:
    contributor_character_id: str
    actual_written_buildup: float
    trace: "AnomalyEffectStrengthTraceView"


@dataclass(frozen=True, slots=True)
class AnomalyEffectStrengthTraceView:
    character_id: str
    level: int | None
    level_coefficient: float | None
    anomaly_proficiency: float | None
    anomaly_proficiency_factor: float | None
    attack: float | None
    element_bonus: float | None
    normal_bonus: float | None
    mutation: float | None
    final_strength: float | None
    element: str | None
    factors: tuple[AnomalyStrengthFactorView, ...]
    unresolved: str | None
    contributor_traces: tuple[AnomalyContributorStrengthTraceView, ...]


@dataclass(frozen=True, slots=True)
class DamageEventView:
    semantic_id: str
    label: str
    damage_type: str
    damage_subtype: str | None
    repeat_count: int
    modes: dict[str, DamageEventModeView]
    common_application_trace: EventTraceView | None
    crit_capability: str = "standard"
    display_modes: tuple[str, ...] = ("non-crit", "expected", "full-crit")


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
    build_provenance: tuple[BuildContributionView, ...]
    diagnostics: tuple[DiagnosticView, ...]
    display_modes: tuple[str, ...] = ("non-crit", "expected", "full-crit")


MoveCalculationView = CalculationView


def calculation_node_view(value: CalculationNodeValue) -> CalculationNodeValueView:
    numeric, unresolved = _resolvable_view(value.value)
    return CalculationNodeValueView(
        node=value.node.value,
        value=numeric,
        read_rule=value.read_rule.value,
        unresolved=unresolved,
    )


def modifier_view(
    modifier,
    *,
    recipient_character_id: str | None = None,
    source_labels: dict[str, str] | None = None,
    source_types: dict[str, str] | None = None,
) -> ModifierView:
    numeric, unresolved = _resolvable_view(modifier.value)
    return ModifierView(
        effect_id=str(modifier.effect_id),
        source_label=(source_labels or {}).get(str(modifier.effect_id)),
        modifier_path=modifier.modifier_path.value,
        operation=modifier.operation.value,
        value=numeric,
        unresolved=unresolved,
        recipient_character_id=recipient_character_id,
        source_type=(source_types or {}).get(str(modifier.effect_id)),
    )


def event_trace_view(
    trace: DamageEventExecutionTrace,
    source_labels: dict[str, str] | None = None,
    source_types: dict[str, str] | None = None,
) -> EventTraceView:
    return EventTraceView(
        semantic_id=str(trace.semantic_id),
        rule_matches=tuple(
            RuleMatchView(
                rule_id=str(match.rule_id),
                source_label=(source_labels or {}).get(str(match.rule_id)),
                status=match.status.value,
                effects=tuple(
                    EffectMatchView(
                        effect_id=str(effect.effect_id),
                        source_label=(source_labels or {}).get(str(effect.effect_id)),
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
                        source_type=(source_types or {}).get(str(effect.effect_id)),
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
                source_type=(source_types or {}).get(str(match.rule_id)),
            )
            for match in trace.rule_matches
        ),
        applied_modifiers=tuple(
            modifier_view(
                item,
                source_labels=source_labels,
                source_types=source_types,
            )
            for item in trace.applied_modifiers
        ),
        event_stat_modifiers=tuple(
            modifier_view(
                item.as_modifier(),
                recipient_character_id=str(item.recipient),
                source_labels=source_labels,
                source_types=source_types,
            )
            for item in trace.event_stat_modifiers
        ),
        event_multiplier_modifiers=tuple(
            modifier_view(
                item,
                source_labels=source_labels,
                source_types=source_types,
            )
            for item in trace.event_multiplier_modifiers
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
        "element_damage_bonus": {
            element.value: value
            for element, value in stats.element_damage_bonus.items()
        },
    }
    return PanelSnapshotView(
        character_id=str(snapshot.character_id),
        level=snapshot.level,
        stats={
            key: (
                {
                    element: _resolvable_view(item)[0]
                    for element, item in value.items()
                }
                if isinstance(value, dict)
                else _resolvable_view(value)[0]
            )
            for key, value in values.items()
        },
    )


def build_contribution_view(trace: BuildContributionTrace) -> BuildContributionView:
    numeric, unresolved = _resolvable_view(trace.applied_value)
    return BuildContributionView(
        character_id=str(trace.character_id),
        contribution_id=trace.contribution_id,
        source_id=trace.source.source_id,
        source_type=trace.source.source_type.value,
        source_label=trace.source.label,
        stat=trace.stat.value,
        layer=trace.layer.value,
        value=numeric,
        element=trace.element.value if trace.element is not None else None,
        unresolved=unresolved,
    )


def anomaly_strength_factor_view(
    factor: AnomalyStrengthFactor,
    source_labels: dict[str, str] | None = None,
    source_owners: dict[str, str] | None = None,
) -> AnomalyStrengthFactorView:
    resolved_label = (
        (source_labels or {}).get(factor.source_id or "")
        if factor.source_id is not None
        else None
    )
    label = resolved_label or factor.source_label
    owner = (
        str(factor.owner_character_id)
        if factor.owner_character_id is not None
        else (source_owners or {}).get(factor.source_id or "")
    )
    return AnomalyStrengthFactorView(
        factor=factor.factor,
        value=factor.value,
        source_id=factor.source_id,
        source_label=label,
        owner_character_id=owner,
        unresolved=factor.unresolved,
    )


def anomaly_effect_strength_trace_view(
    trace: AnomalyEffectStrengthTrace,
    source_labels: dict[str, str] | None = None,
    source_owners: dict[str, str] | None = None,
) -> AnomalyEffectStrengthTraceView:
    return AnomalyEffectStrengthTraceView(
        character_id=str(trace.character_id),
        level=trace.level,
        level_coefficient=trace.level_coefficient,
        anomaly_proficiency=trace.anomaly_proficiency,
        anomaly_proficiency_factor=trace.anomaly_proficiency_factor,
        attack=trace.attack,
        element_bonus=trace.element_bonus,
        normal_bonus=trace.normal_bonus,
        mutation=trace.mutation,
        final_strength=trace.final_strength,
        element=trace.element.value if trace.element is not None else None,
        factors=tuple(
            anomaly_strength_factor_view(item, source_labels, source_owners)
            for item in trace.factors
        ),
        unresolved=trace.unresolved,
        contributor_traces=tuple(
            AnomalyContributorStrengthTraceView(
                contributor_character_id=str(contributor),
                actual_written_buildup=written,
                trace=anomaly_effect_strength_trace_view(item, source_labels, source_owners),
            )
            for contributor, written, item in trace.contributor_traces
        ),
    )


def _mode_view(
    item: DamageEventCalculationOutput,
    source_labels: dict[str, str] | None = None,
    source_owners: dict[str, str] | None = None,
) -> DamageEventModeView:
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
        anomaly_effect_strength_trace=(
            anomaly_effect_strength_trace_view(
                result.anomaly_effect_strength_trace,
                source_labels,
                source_owners,
            )
            if result is not None and result.anomaly_effect_strength_trace is not None
            else None
        ),
        anomaly_record_id=result.anomaly_record_id if result is not None else None,
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
    "BuildContributionView",
    "AnomalyEffectStrengthTraceView",
    "AnomalyStrengthFactorView",
    "AnomalyContributorStrengthTraceView",
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
    "build_contribution_view",
    "anomaly_effect_strength_trace_view",
]
