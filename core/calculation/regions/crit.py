"""Pure expected-value crit-region calculation."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class CritRegionInput:
    crit_rate: float
    crit_damage: float


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def calculate_crit_region(input: CritRegionInput) -> CalculationResult:
    region = 1.0 * (1.0 - input.crit_rate) + (
        1.0 + input.crit_damage
    ) * input.crit_rate
    breakdown = (
        _node(CalculationNode.CHARACTER_CURRENT_CRIT_RATE, input.crit_rate),
        _node(CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE, input.crit_damage),
        _node(CalculationNode.DAMAGE_STANDARD_CRIT_REGION, region),
    )
    return CalculationResult(value=region, breakdown=breakdown)
