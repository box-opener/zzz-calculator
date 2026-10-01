"""Immutable state and outputs for one enemy-element anomaly gauge."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .anomaly_record import (
    AnomalyContribution,
    AnomalyCritCapability,
    AnomalyEffectStrengthTrace,
    AnomalyRecord,
)
from .battle_event import AnomalyBuildupEvent
from .common import (
    AnomalyRecordId,
    EnemyId,
    Multiplier,
    Resolvable,
    Seconds,
    Unresolved,
)
from .enums import ANOMALY_ELEMENTS, Element


@dataclass(frozen=True, slots=True)
class AnomalyGauge:
    target_enemy: EnemyId
    element: Element
    capacity: float
    current_buildup: float = 0.0
    contributions: tuple[AnomalyContribution, ...] = ()

    def __post_init__(self) -> None:
        if self.element not in ANOMALY_ELEMENTS:
            raise ValueError("luminance has no ordinary anomaly gauge")
        if not math.isfinite(self.capacity) or self.capacity <= 0:
            raise ValueError("anomaly gauge capacity must be a finite positive number")
        if not math.isfinite(self.current_buildup) or not (
            0.0 <= self.current_buildup < self.capacity
        ):
            raise ValueError(
                "current anomaly buildup must be finite and within [0, capacity)"
            )
        contribution_total = sum(
            contribution.actual_written_buildup
            for contribution in self.contributions
        )
        if not math.isclose(
            contribution_total,
            self.current_buildup,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "current anomaly buildup must equal actual written contributions"
            )


@dataclass(frozen=True, slots=True)
class AnomalyTriggerSnapshot:
    record_id: AnomalyRecordId
    anomaly_damage_bonus_region: Resolvable[Multiplier]
    crit_capability: AnomalyCritCapability
    duration: Resolvable[Seconds]


@dataclass(frozen=True, slots=True)
class AnomalyBuildupApplicationContext:
    event: AnomalyBuildupEvent
    anomaly_effect_strength: Resolvable[float]
    impact_strength: Resolvable[float]
    anomaly_effect_strength_trace: AnomalyEffectStrengthTrace | None = None


@dataclass(frozen=True, slots=True)
class AnomalyGaugeApplication:
    gauge_before: AnomalyGauge
    gauge_after: AnomalyGauge
    contribution: AnomalyContribution | None
    triggered_record: AnomalyRecord | None
    discarded_buildup: float
    unresolved: tuple[Unresolved, ...] = ()
