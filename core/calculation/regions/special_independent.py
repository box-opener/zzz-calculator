"""Pure special-independent-region calculation."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class SpecialIndependentRegionInput:
    independent_bonus: float = 0.0


def calculate_special_independent_region(
    input: SpecialIndependentRegionInput,
) -> CalculationResult:
    region = 1.0 + input.independent_bonus
    breakdown = (
        CalculationNodeValue(
            node=CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION,
            value=Resolved(region),
            read_rule=SnapshotRule.SETTLEMENT,
        ),
    )
    return CalculationResult(value=region, breakdown=breakdown)
