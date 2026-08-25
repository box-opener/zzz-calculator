"""Calculation interfaces; no concrete formulas belong in this module."""

from typing import Protocol, runtime_checkable

from core.types.calculation_context import CalculationContext

from .result import CalculationResult


@runtime_checkable
class DamageCalculator(Protocol):
    def calculate(self, context: CalculationContext) -> CalculationResult:
        ...
