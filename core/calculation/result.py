"""White-box output returned by every future calculator."""

from __future__ import annotations

from dataclasses import dataclass

from core.types.common import Unresolved

from .nodes import CalculationNodeValue


@dataclass(frozen=True, slots=True)
class CalculationResult:
    value: float
    breakdown: tuple[CalculationNodeValue, ...]
    unresolved: tuple[Unresolved, ...] = ()

    @classmethod
    def from_components(
        cls,
        *,
        value: float,
        components: tuple[CalculationResult, ...],
        breakdown: tuple[CalculationNodeValue, ...] = (),
        unresolved: tuple[Unresolved, ...] = (),
    ) -> CalculationResult:
        """Flatten component traces while the caller decides the final value."""

        return cls(
            value=value,
            breakdown=breakdown
            + tuple(
                node_value
                for component in components
                for node_value in component.breakdown
            ),
            unresolved=unresolved
            + tuple(
                item
                for component in components
                for item in component.unresolved
            ),
        )
