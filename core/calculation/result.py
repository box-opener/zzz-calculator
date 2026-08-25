"""White-box output returned by every future calculator."""

from dataclasses import dataclass

from core.types.common import Unresolved

from .nodes import CalculationNodeValue


@dataclass(frozen=True, slots=True)
class CalculationResult:
    value: float
    breakdown: tuple[CalculationNodeValue, ...]
    unresolved: tuple[Unresolved, ...] = ()
