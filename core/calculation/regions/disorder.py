"""Pure disorder-damage-bonus-region calculation by dynamic identity."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class DisorderDamageBonusRegionInput:
    trigger_damage_bonus: float = 0.0
    settled_contributor_damage_bonus: float = 0.0


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def calculate_disorder_damage_bonus_region(
    input: DisorderDamageBonusRegionInput,
) -> CalculationResult:
    region = (
        1.0
        + input.trigger_damage_bonus
        + input.settled_contributor_damage_bonus
    )
    breakdown = (
        _node(
            CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
            input.trigger_damage_bonus,
        ),
        _node(
            CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
            input.settled_contributor_damage_bonus,
        ),
        _node(CalculationNode.DISORDER_DAMAGE_BONUS_REGION, region),
    )
    return CalculationResult(value=region, breakdown=breakdown)
