"""Pure elemental resistance-region calculation."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class ResistanceRegionInput:
    base_resistance: float
    resistance_ignore: float = 0.0
    resistance_reduction: float = 0.0


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def calculate_resistance_region(input: ResistanceRegionInput) -> CalculationResult:
    initial_region = 1.0 - input.base_resistance
    region = max(
        0.0,
        initial_region + input.resistance_ignore + input.resistance_reduction,
    )
    breakdown = (
        _node(CalculationNode.ENEMY_INITIAL_RESISTANCE_REGION, initial_region),
        _node(CalculationNode.DAMAGE_RESISTANCE_IGNORE, input.resistance_ignore),
        _node(CalculationNode.ENEMY_RESISTANCE_REDUCTION, input.resistance_reduction),
        _node(CalculationNode.DAMAGE_RESISTANCE_REGION, region),
    )
    return CalculationResult(value=region, breakdown=breakdown)
