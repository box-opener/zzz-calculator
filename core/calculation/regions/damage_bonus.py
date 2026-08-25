"""Pure normal-damage-bonus-region calculation."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class NormalDamageBonusRegionInput:
    element_damage_bonus: float = 0.0
    matched_damage_bonus: float = 0.0
    generic_damage_bonus: float = 0.0


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def calculate_normal_damage_bonus_region(
    input: NormalDamageBonusRegionInput,
) -> CalculationResult:
    normal_bonus = input.matched_damage_bonus + input.generic_damage_bonus
    region = 1.0 + input.element_damage_bonus + normal_bonus
    breakdown = (
        _node(
            CalculationNode.CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS,
            input.element_damage_bonus,
        ),
        _node(CalculationNode.DAMAGE_NORMAL_BONUS, normal_bonus),
        _node(CalculationNode.DAMAGE_NORMAL_BONUS_REGION, region),
    )
    return CalculationResult(value=region, breakdown=breakdown)
