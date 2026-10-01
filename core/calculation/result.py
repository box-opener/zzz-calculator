"""White-box output returned by every future calculator."""

from __future__ import annotations

from dataclasses import dataclass

from core.types.common import Unresolved
from core.types.anomaly_record import AnomalyEffectStrengthTrace

from .nodes import CalculationNodeValue


@dataclass(frozen=True, slots=True)
class CalculationResult:
    value: float | None
    breakdown: tuple[CalculationNodeValue, ...]
    unresolved: tuple[Unresolved, ...] = ()
    anomaly_effect_strength_trace: AnomalyEffectStrengthTrace | None = None
    anomaly_record_id: str | None = None

    def __post_init__(self) -> None:
        if self.value is None and not self.unresolved:
            raise ValueError("value=None requires at least one unresolved reason")
