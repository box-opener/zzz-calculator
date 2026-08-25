"""Apply a pre-calculated anomaly buildup event to an immutable gauge."""

from __future__ import annotations

import math

from core.types import (
    AnomalyBuildupApplicationContext,
    AnomalyContribution,
    AnomalyGauge,
    AnomalyGaugeApplication,
    AnomalyTriggerSnapshot,
    Resolved,
)

from .record import build_anomaly_record


def apply_anomaly_buildup(
    gauge: AnomalyGauge,
    application_context: AnomalyBuildupApplicationContext,
    trigger_snapshot: AnomalyTriggerSnapshot,
) -> AnomalyGaugeApplication:
    event = application_context.event
    if event.target_enemy != gauge.target_enemy:
        raise ValueError("anomaly buildup target does not match gauge target")
    if event.element != gauge.element:
        raise ValueError("anomaly buildup element does not match gauge element")
    if not isinstance(event.calculated_buildup, Resolved):
        return AnomalyGaugeApplication(
            gauge_before=gauge,
            gauge_after=gauge,
            contribution=None,
            triggered_record=None,
            discarded_buildup=0.0,
            unresolved=(event.calculated_buildup,),
        )

    calculated_buildup = event.calculated_buildup.value
    if not math.isfinite(calculated_buildup) or calculated_buildup < 0:
        raise ValueError("calculated anomaly buildup must be finite and non-negative")
    if calculated_buildup == 0:
        return AnomalyGaugeApplication(
            gauge_before=gauge,
            gauge_after=gauge,
            contribution=None,
            triggered_record=None,
            discarded_buildup=0.0,
        )

    remaining = gauge.capacity - gauge.current_buildup
    actual_written = min(calculated_buildup, remaining)
    discarded = calculated_buildup - actual_written
    contribution = AnomalyContribution(
        contributor=event.contributor,
        actual_written_buildup=actual_written,
        anomaly_effect_strength=application_context.anomaly_effect_strength,
        impact_strength=application_context.impact_strength,
        occurred_at=event.metadata.occurred_at,
    )
    contributions = (*gauge.contributions, contribution)
    if calculated_buildup >= remaining:
        record = build_anomaly_record(
            gauge,
            event,
            trigger_snapshot,
            contributions,
        )
        gauge_after = AnomalyGauge(
            target_enemy=gauge.target_enemy,
            element=gauge.element,
            capacity=gauge.capacity,
        )
    else:
        record = None
        gauge_after = AnomalyGauge(
            target_enemy=gauge.target_enemy,
            element=gauge.element,
            capacity=gauge.capacity,
            current_buildup=gauge.current_buildup + actual_written,
            contributions=contributions,
        )
    return AnomalyGaugeApplication(
        gauge_before=gauge,
        gauge_after=gauge_after,
        contribution=contribution,
        triggered_record=record,
        discarded_buildup=discarded,
    )
