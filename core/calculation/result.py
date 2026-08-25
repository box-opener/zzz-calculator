"""White-box output returned by every future calculator."""

from __future__ import annotations

from dataclasses import dataclass

from core.types.common import Unresolved

from .nodes import CalculationNodeValue


@dataclass(frozen=True, slots=True)
class CalculationResult:
    value: float | None
    breakdown: tuple[CalculationNodeValue, ...]
    unresolved: tuple[Unresolved, ...] = ()

    def __post_init__(self) -> None:
        if self.value is None and not self.unresolved:
            raise ValueError("value=None requires at least one unresolved reason")
