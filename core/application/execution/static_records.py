"""Explicit static-mode construction of one-character anomaly records.

The normal application contract consumes ``AnomalyRecord`` values supplied by
the caller.  The browser-facing calculator is intentionally different: the
v1 specification defines a single-character, full-gauge assumption.  This
module contains that narrow adapter so that the rest of the execution service
does not infer history from arbitrary record IDs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AnomalyContribution,
    AnomalyEffectStrengthTrace,
    AnomalyStrengthFactor,
    AnomalyRecord,
    AttributeAnomalyDamageEvent,
    AnomalyRecordValueSource,
    CalculationNode,
    CharacterSnapshot,
    DamageEvent,
    DamageSubtype,
    DisorderDamageEvent,
    EffectOperation,
    Element,
    IndependentAnomalyCrit,
    FixedMultiplier,
    NoAnomalyCrit,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolved,
    Unresolved,
    UnresolvedReason,
)

from core.calculation.anomaly import (
    anomaly_effect_strength_with_trace,
    anomaly_impact_strength,
)
from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId


# Maximum static duration for the ordinary anomaly records described by the
# calculation specification.  The current Alice path uses physical (10s),
# but keeping the table element-based keeps this helper independent of role or
# character IDs.
_ANOMALY_DURATION_SECONDS: dict[Element, float] = {
    Element.PHYSICAL: 10.0,
    Element.LINREN: 10.0,
    Element.ICE: 10.0,
    Element.LIESHUANG: 20.0,
    Element.ETHER: 10.0,
    Element.XUANMO: 10.0,
    Element.FIRE: 10.0,
    Element.ELECTRIC: 10.0,
    Element.WIND: 30.0,
}


@dataclass(frozen=True, slots=True)
class StaticAnomalyRecordAssembly:
    """One record plus non-fatal diagnostics produced during assembly."""

    record: AnomalyRecord | None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class StaticAnomalyStrengthAssembly:
    """One source-generation strength value without creating an AnomalyRecord.

    Remielle's special virtual void can use Luminance flow while remaining a
    separate source type from an ordinary attribute AnomalyRecord.
    """

    effect_strength: Resolved[float] | Unresolved
    trace: AnomalyEffectStrengthTrace
    penetration_rate: Resolved[float] | Unresolved
    penetration_flat: Resolved[float] | Unresolved
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


def static_attribute_anomaly_record(
    event: DamageEvent,
    snapshots: tuple[CharacterSnapshot, ...],
    modifiers=(),
    modifier_sources=None,
) -> StaticAnomalyRecordAssembly | None:
    """Build the static one-character record for a typed anomaly event.

    ``modifiers`` are the already matched event modifiers.  The first pass
    uses an empty tuple only to establish record identities for matching; the
    second pass supplies the formal event bonuses.  Explicit records are
    resolved by the caller and therefore never reach this helper.
    """

    if isinstance(event, DisorderDamageEvent):
        # Static browser mode has one explicit full-gauge assumption.  A
        # disorder event carries the source record identity and triggerer but
        # not a second anomaly snapshot, so reuse this narrow adapter through
        # a typed synthetic attribute-anomaly view.  This does not infer a
        # record for arbitrary event IDs in EXPLICIT mode, and it leaves the
        # disorder-specific modifiers on the disorder settlement lane.
        event = AttributeAnomalyDamageEvent(
            metadata=event.metadata,
            anomaly_triggerer=event.disorder_triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(
                event.history_record_source
            ),
            history_record_source=event.history_record_source,
            multiplier=FixedMultiplier(Resolved(1.0)),
            crit_rule=NoCritRule(),
        )
    if not isinstance(event, AttributeAnomalyDamageEvent):
        return None

    if event.metadata.element not in ANOMALY_DAMAGE_KIND_BY_ELEMENT:
        return StaticAnomalyRecordAssembly(
            record=None,
            diagnostics=(
                _diagnostic(
                    event,
                    "static-record-element",
                    "static single-character records do not support luminance "
                    "attribute anomalies",
                ),
            ),
        )

    if event.metadata.damage_dealer != event.anomaly_triggerer:
        return StaticAnomalyRecordAssembly(
            record=None,
            diagnostics=(
                _diagnostic(
                    event,
                    "static-record-triggerer",
                    "static single-character anomaly assembly requires the damage "
                    "dealer and anomaly triggerer to be the same character",
                ),
            ),
        )

    snapshot = next(
        (
            item
            for item in snapshots
            if item.character_id == event.metadata.damage_dealer
        ),
        None,
    )
    if snapshot is None:
        # Keep a typed record for identity matching.  Its numeric fields stay
        # unresolved so the calculator returns a structured DATA_INSUFFICIENT
        # result instead of silently treating absent panel values as zero.
        unresolved = _unresolved(
            f"missing settlement snapshot for anomaly triggerer "
            f"{event.anomaly_triggerer}"
        )
        level = None
        element_bonus = unresolved
        attack = unresolved
        proficiency = unresolved
        impact = unresolved
        penetration_rate = unresolved
        penetration_flat = unresolved
    else:
        level = snapshot.level
        stats = snapshot.settlement_stats
        element_bonus = stats.element_damage_bonus.get(
            event.metadata.element,
            stats.element_damage_bonus.get(
                _base_element(event.metadata.element),
                None,
            ),
        )
        attack = stats.attack
        proficiency = stats.anomaly_proficiency
        impact = stats.impact
        penetration_rate = stats.penetration_rate
        penetration_flat = stats.penetration_flat
        if element_bonus is None:
            element_bonus = _unresolved(
                f"missing element damage bonus for {event.metadata.element.value}"
            )

    normal_bonus, normal_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        event,
    )
    normal_factors = _normal_factors(modifiers, modifier_sources or {})
    mutation, mutation_factors, mutation_diagnostics = _mutation_coefficient(
        modifiers,
        event,
        modifier_sources or {},
    )
    anomaly_bonus, anomaly_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.ANOMALY_DAMAGE_BONUS,
        event,
    )
    anomaly_crit_rate, anomaly_crit_rate_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.ANOMALY_CRIT_RATE,
        event,
    )
    anomaly_crit_damage, anomaly_crit_damage_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.ANOMALY_CRIT_DAMAGE,
        event,
    )
    if isinstance(anomaly_crit_rate, Resolved) and anomaly_crit_rate.value > 0.0:
        inherited_by = (
            (DamageSubtype.DISCHARGE, DamageSubtype.TURBULENCE)
            if event.metadata.element in {Element.PHYSICAL, Element.LINREN}
            else ()
        )
        crit_capability = IndependentAnomalyCrit(
            crit_rate=anomaly_crit_rate,
            crit_damage=anomaly_crit_damage,
            inherited_by=inherited_by,
        )
    elif not isinstance(anomaly_crit_rate, Resolved):
        crit_capability = anomaly_crit_rate
    elif (
        isinstance(event.crit_rule, RecordedAnomalyCritRule)
        and isinstance(event.crit_rule.capability, IndependentAnomalyCrit)
    ):
        crit_capability = event.crit_rule.capability
    else:
        crit_capability = NoAnomalyCrit()
    effect_strength, effect_trace = _effect_strength(
        level,
        attack,
        proficiency,
        element_bonus,
        normal_bonus,
        event,
        normal_factors,
        mutation,
        mutation_factors,
    )
    impact_strength = _impact_strength(level, impact)
    duration = _ANOMALY_DURATION_SECONDS.get(event.metadata.element)
    duration_value = (
        Resolved(duration)
        if duration is not None
        else _unresolved(
            f"no static anomaly duration is defined for "
            f"{event.metadata.element.value}"
        )
    )
    contribution = AnomalyContribution(
        contributor=event.anomaly_triggerer,
        # The static assumption is one complete gauge.  The absolute gauge
        # unit is not consumed downstream; using one keeps the weighted value
        # equal to the sole contribution without simulating accumulation.
        actual_written_buildup=1.0,
        anomaly_effect_strength=effect_strength,
        impact_strength=impact_strength,
        occurred_at=event.metadata.created_at,
        anomaly_effect_strength_trace=effect_trace,
    )
    record = AnomalyRecord(
        record_id=event.history_record_source,
        target_enemy=event.metadata.target_enemy,
        element=event.metadata.element,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[event.metadata.element],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[event.metadata.element],
        weighted_anomaly_effect_strength=effect_strength,
        weighted_impact_strength=impact_strength,
        anomaly_damage_bonus_region=_region(anomaly_bonus),
        contributors=(event.anomaly_triggerer,),
        anomaly_triggerer=event.anomaly_triggerer,
        crit_capability=crit_capability,
        triggered_at=event.metadata.created_at,
        duration=duration_value,
        contributions=(contribution,),
        anomaly_effect_strength_trace=effect_trace,
        penetration_rate=penetration_rate,
        penetration_flat=penetration_flat,
    )
    return StaticAnomalyRecordAssembly(
        record=record,
        diagnostics=(
            *normal_diagnostics,
            *anomaly_diagnostics,
            *anomaly_crit_rate_diagnostics,
            *anomaly_crit_damage_diagnostics,
            *mutation_diagnostics,
        ),
    )


def static_anomaly_effect_strength_source(
    event: AttributeAnomalyDamageEvent,
    snapshots: tuple[CharacterSnapshot, ...],
    modifiers=(),
    modifier_sources=None,
) -> StaticAnomalyStrengthAssembly:
    """Capture the common effect-strength formula without materializing history.

    This adapter intentionally does not check ``ANOMALY_ELEMENTS`` or return an
    ``AnomalyRecord``. It is for a separate typed source such as Remielle's
    special virtual void, and preserves its element-specific panel/penetration
    inputs and normal/mutation factors.
    """

    snapshot = next(
        (item for item in snapshots if item.character_id == event.anomaly_triggerer),
        None,
    )
    if snapshot is None:
        notes = f"missing settlement snapshot for source actor {event.anomaly_triggerer}"
        unresolved = _unresolved(notes)
        trace = AnomalyEffectStrengthTrace(
            character_id=event.anomaly_triggerer,
            level=None,
            level_coefficient=None,
            anomaly_proficiency=None,
            anomaly_proficiency_factor=None,
            attack=None,
            element_bonus=None,
            normal_bonus=None,
            mutation=None,
            final_strength=None,
            element=event.metadata.element,
            unresolved=notes,
        )
        return StaticAnomalyStrengthAssembly(
            unresolved,
            trace,
            unresolved,
            unresolved,
            (_diagnostic(event, "static-source-snapshot", notes),),
        )

    stats = snapshot.settlement_stats
    element_bonus = stats.element_damage_bonus.get(
        event.metadata.element,
        stats.element_damage_bonus.get(_base_element(event.metadata.element)),
    )
    if element_bonus is None:
        element_bonus = _unresolved(
            f"missing element damage bonus for {event.metadata.element.value}"
        )
    normal_bonus, normal_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        event,
    )
    mutation, mutation_factors, mutation_diagnostics = _mutation_coefficient(
        modifiers,
        event,
        modifier_sources or {},
    )
    effect_strength, trace = _effect_strength(
        snapshot.level,
        stats.attack,
        stats.anomaly_proficiency,
        element_bonus,
        normal_bonus,
        event,
        _normal_factors(modifiers, modifier_sources or {}),
        mutation,
        mutation_factors,
    )
    diagnostics = (*normal_diagnostics, *mutation_diagnostics)
    return StaticAnomalyStrengthAssembly(
        effect_strength,
        trace,
        stats.penetration_rate,
        stats.penetration_flat,
        diagnostics,
    )


def _base_element(element: Element) -> Element:
    if element in {Element.LINREN}:
        return Element.PHYSICAL
    if element is Element.LIESHUANG:
        return Element.ICE
    if element is Element.XUANMO:
        return Element.ETHER
    return element


def _effect_strength(
    level: int | None,
    attack,
    proficiency,
    element_bonus,
    normal_bonus,
    event: AttributeAnomalyDamageEvent,
    normal_factors: tuple[AnomalyStrengthFactor, ...],
    mutation,
    mutation_factors: tuple[AnomalyStrengthFactor, ...],
):
    values = (attack, proficiency, element_bonus, normal_bonus, mutation)
    if level is None or any(not isinstance(item, Resolved) for item in values):
        notes = "cannot calculate static anomaly effect strength"
        return _unresolved(notes), AnomalyEffectStrengthTrace(
            character_id=event.anomaly_triggerer,
            level=level,
            level_coefficient=(1.0 + (level - 1) / 59.0) if level is not None else None,
            anomaly_proficiency=proficiency.value if isinstance(proficiency, Resolved) else None,
            anomaly_proficiency_factor=(proficiency.value / 100.0) if isinstance(proficiency, Resolved) else None,
            attack=attack.value if isinstance(attack, Resolved) else None,
            element_bonus=element_bonus.value if isinstance(element_bonus, Resolved) else None,
            normal_bonus=normal_bonus.value if isinstance(normal_bonus, Resolved) else None,
            mutation=mutation.value if isinstance(mutation, Resolved) else None,
            final_strength=None,
            element=event.metadata.element,
            factors=(*normal_factors, *mutation_factors),
            unresolved=notes,
        )
    value, trace = anomaly_effect_strength_with_trace(
        character_id=event.anomaly_triggerer,
        level=level,
        attack=attack.value,
        anomaly_proficiency=proficiency.value,
        element_damage_bonus=element_bonus.value,
        normal_damage_bonus=normal_bonus.value,
        mutation=mutation.value,
        element=event.metadata.element,
        normal_factors=normal_factors,
        mutation_factors=mutation_factors,
    )
    if not math.isfinite(value):
        notes = "static anomaly effect strength is not finite"
        return _unresolved(notes), replace_trace_unresolved(trace, notes)
    return Resolved(value), trace


def replace_trace_unresolved(
    trace: AnomalyEffectStrengthTrace,
    notes: str,
) -> AnomalyEffectStrengthTrace:
    return AnomalyEffectStrengthTrace(
        character_id=trace.character_id,
        level=trace.level,
        level_coefficient=trace.level_coefficient,
        anomaly_proficiency=trace.anomaly_proficiency,
        anomaly_proficiency_factor=trace.anomaly_proficiency_factor,
        attack=trace.attack,
        element_bonus=trace.element_bonus,
        normal_bonus=trace.normal_bonus,
        mutation=trace.mutation,
        final_strength=None,
        element=trace.element,
        factors=trace.factors,
        unresolved=notes,
        contributor_traces=trace.contributor_traces,
    )


def _normal_factors(modifiers, modifier_sources):
    factors: list[AnomalyStrengthFactor] = []
    for modifier in modifiers:
        if modifier.modifier_path is not CalculationNode.DAMAGE_NORMAL_BONUS:
            continue
        value = modifier.value.value if isinstance(modifier.value, Resolved) else None
        source_id = str(modifier.effect_id)
        source_label, owner = modifier_sources.get(source_id, (None, None))
        factors.append(
            AnomalyStrengthFactor(
                factor="normal-bonus",
                value=value,
                source_id=source_id,
                source_label=source_label,
                owner_character_id=owner,
                unresolved=(modifier.value.notes if not isinstance(modifier.value, Resolved) else None),
            )
        )
    return tuple(factors)


def _mutation_coefficient(modifiers, event, modifier_sources):
    multiplier = 1.0
    additive = 0.0
    factors: list[AnomalyStrengthFactor] = []
    diagnostics: list[CalculationDiagnostic] = []
    for modifier in modifiers:
        if modifier.modifier_path is not CalculationNode.ANOMALY_MUTATION_COEFFICIENT:
            continue
        source_id = str(modifier.effect_id)
        source_label, owner = modifier_sources.get(source_id, (None, None))
        if modifier.operation not in {EffectOperation.MULTIPLY, EffectOperation.ADD}:
            diagnostics.append(
                _diagnostic(
                    event,
                    "static-record-mutation-operation",
                    "static anomaly record supports MULTIPLY and ADD for anomaly mutation coefficient",
                )
            )
            value = None
            unresolved = f"unsupported mutation operation: {modifier.operation.value}"
        elif not isinstance(modifier.value, Resolved):
            diagnostics.append(
                _diagnostic(event, "static-record-mutation-value", modifier.value.notes)
            )
            value = None
            unresolved = modifier.value.notes
        else:
            value = modifier.value.value
            unresolved = None
            if modifier.operation is EffectOperation.MULTIPLY:
                multiplier *= value
            else:
                additive += value
        factors.append(
            AnomalyStrengthFactor(
                factor=(
                    "mutation"
                    if modifier.operation is EffectOperation.MULTIPLY
                    else "mutation-additive"
                ),
                value=value,
                source_id=source_id,
                source_label=source_label,
                owner_character_id=owner,
                unresolved=unresolved,
            )
        )
        if value is None:
            return _unresolved("cannot calculate static anomaly mutation coefficient"), tuple(factors), tuple(diagnostics)
    return Resolved(multiplier + additive), tuple(factors), tuple(diagnostics)


def _impact_strength(level: int | None, impact):
    if level is None or not isinstance(impact, Resolved):
        return _unresolved("cannot calculate static anomaly impact strength")
    value = anomaly_impact_strength(level, impact.value)
    if not math.isfinite(value):
        return _unresolved("static anomaly impact strength is not finite")
    return Resolved(value)


def _modifier_total(
    modifiers,
    node: CalculationNode,
    event: AttributeAnomalyDamageEvent,
):
    total = 0.0
    diagnostics: list[CalculationDiagnostic] = []
    for modifier in modifiers:
        if modifier.modifier_path is not node:
            continue
        if modifier.operation is not EffectOperation.ADD:
            return (
                _unresolved(
                    f"static anomaly record does not support "
                    f"{modifier.operation.value} for {node.value}"
                ),
                (
                    _diagnostic(
                        event,
                        f"static-record-{node.value}-operation",
                        f"static anomaly record requires ADD for {node.value}",
                    ),
                ),
            )
        if not isinstance(modifier.value, Resolved):
            return (
                modifier.value,
                (
                    _diagnostic(
                        event,
                        f"static-record-{node.value}-value",
                        modifier.value.notes,
                    ),
                ),
            )
        total += modifier.value.value
    return Resolved(total), tuple(diagnostics)


def _region(value):
    if not isinstance(value, Resolved):
        return value
    return Resolved(1.0 + value.value)


def _unresolved(notes: str) -> Unresolved:
    return Unresolved(reason=UnresolvedReason.MISSING_DATA, notes=notes)


def _diagnostic(
    event: AttributeAnomalyDamageEvent,
    suffix: str,
    message: str,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"static-record:{event.history_record_source}:{suffix}"),
        kind=DiagnosticKind.MISSING_DATA,
        message=message,
        blocking=True,
    )


__all__ = [
    "StaticAnomalyRecordAssembly",
    "StaticAnomalyStrengthAssembly",
    "static_anomaly_effect_strength_source",
    "static_attribute_anomaly_record",
]
