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
    AnomalyRecord,
    AttributeAnomalyDamageEvent,
    AnomalyRecordValueSource,
    CalculationNode,
    CharacterSnapshot,
    DamageEvent,
    DisorderDamageEvent,
    EffectOperation,
    Element,
    FixedMultiplier,
    NoAnomalyCrit,
    NoCritRule,
    Resolved,
    Unresolved,
    UnresolvedReason,
)

from core.calculation.anomaly import anomaly_effect_strength, anomaly_impact_strength
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


def static_attribute_anomaly_record(
    event: DamageEvent,
    snapshots: tuple[CharacterSnapshot, ...],
    modifiers=(),
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
        if element_bonus is None:
            element_bonus = _unresolved(
                f"missing element damage bonus for {event.metadata.element.value}"
            )

    normal_bonus, normal_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        event,
    )
    anomaly_bonus, anomaly_diagnostics = _modifier_total(
        modifiers,
        CalculationNode.ANOMALY_DAMAGE_BONUS,
        event,
    )
    effect_strength = _effect_strength(
        level,
        attack,
        proficiency,
        element_bonus,
        normal_bonus,
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
        crit_capability=NoAnomalyCrit(),
        triggered_at=event.metadata.created_at,
        duration=duration_value,
        contributions=(contribution,),
    )
    return StaticAnomalyRecordAssembly(
        record=record,
        diagnostics=(*normal_diagnostics, *anomaly_diagnostics),
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
):
    values = (attack, proficiency, element_bonus, normal_bonus)
    if level is None or any(not isinstance(item, Resolved) for item in values):
        return _unresolved("cannot calculate static anomaly effect strength")
    value = anomaly_effect_strength(
        level,
        attack.value,
        proficiency.value,
        element_bonus.value,
        normal_bonus.value,
    )
    if not math.isfinite(value):
        return _unresolved("static anomaly effect strength is not finite")
    return Resolved(value)


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


__all__ = ["StaticAnomalyRecordAssembly", "static_attribute_anomaly_record"]
