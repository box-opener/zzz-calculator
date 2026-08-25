"""Construct an AnomalyRecord from one completed gauge."""

from __future__ import annotations

import math

from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AnomalyBuildupEvent,
    AnomalyContribution,
    AnomalyGauge,
    AnomalyRecord,
    AnomalyTriggerSnapshot,
    Resolvable,
    Resolved,
    Unresolved,
    UnresolvedReason,
)


def _weighted_value(
    contributions: tuple[AnomalyContribution, ...],
    attribute: str,
    label: str,
) -> Resolvable[float]:
    unresolved_values: list[Unresolved] = []
    weighted_sum = 0.0
    total_written = 0.0
    for contribution in contributions:
        value = getattr(contribution, attribute)
        if isinstance(value, Resolved) and math.isfinite(value.value):
            weighted_sum += contribution.actual_written_buildup * value.value
        else:
            if isinstance(value, Unresolved):
                unresolved_values.append(value)
            else:
                unresolved_values.append(
                    Unresolved(
                        reason=UnresolvedReason.MISSING_DATA,
                        notes=f"{label} contains a non-finite resolved value",
                    )
                )
        total_written += contribution.actual_written_buildup

    if unresolved_values:
        return Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=f"cannot calculate weighted {label}",
            candidates=tuple(item.notes for item in unresolved_values),
        )
    return Resolved(weighted_sum / total_written)


def build_anomaly_record(
    gauge: AnomalyGauge,
    event: AnomalyBuildupEvent,
    trigger_snapshot: AnomalyTriggerSnapshot,
    contributions: tuple[AnomalyContribution, ...],
) -> AnomalyRecord:
    if event.target_enemy != gauge.target_enemy:
        raise ValueError("record event target does not match gauge target")
    if event.element != gauge.element:
        raise ValueError("record event element does not match gauge element")
    if not contributions:
        raise ValueError("completed anomaly gauge requires contributions")
    total_written = sum(
        contribution.actual_written_buildup for contribution in contributions
    )
    if not math.isclose(
        total_written,
        gauge.capacity,
        rel_tol=1e-9,
        abs_tol=1e-9,
    ):
        raise ValueError("anomaly record requires one completed gauge")
    if contributions[-1].contributor != event.contributor:
        raise ValueError("final contribution must belong to anomaly triggerer")
    contributors = tuple(
        dict.fromkeys(contribution.contributor for contribution in contributions)
    )
    return AnomalyRecord(
        record_id=trigger_snapshot.record_id,
        target_enemy=gauge.target_enemy,
        element=gauge.element,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[gauge.element],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[gauge.element],
        weighted_anomaly_effect_strength=_weighted_value(
            contributions,
            "anomaly_effect_strength",
            "anomaly effect strength",
        ),
        weighted_impact_strength=_weighted_value(
            contributions,
            "impact_strength",
            "impact strength",
        ),
        anomaly_damage_bonus_region=trigger_snapshot.anomaly_damage_bonus_region,
        contributors=contributors,
        anomaly_triggerer=event.contributor,
        crit_capability=trigger_snapshot.crit_capability,
        triggered_at=event.metadata.occurred_at,
        duration=trigger_snapshot.duration,
        contributions=contributions,
    )
