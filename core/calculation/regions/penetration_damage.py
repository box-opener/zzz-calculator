"""Pure regions used only by penetration damage."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class PenetrationForceInput:
    current_attack: float
    current_max_hp: float
    additional_force: float = 0.0


@dataclass(frozen=True, slots=True)
class PenetrationDamageBonusRegionInput:
    damage_bonus: float = 0.0


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def calculate_penetration_force(
    input: PenetrationForceInput,
) -> CalculationResult:
    force = (
        input.current_attack * 0.30
        + input.current_max_hp * 0.10
        + input.additional_force
    )
    breakdown = [
        _node(CalculationNode.CHARACTER_CURRENT_ATTACK, input.current_attack),
        _node(CalculationNode.CHARACTER_CURRENT_MAX_HP, input.current_max_hp),
    ]
    if input.additional_force != 0.0:
        breakdown.append(
            _node(CalculationNode.PENETRATION_FORCE_BONUS, input.additional_force)
        )
    breakdown.append(_node(CalculationNode.PENETRATION_FORCE, force))
    return CalculationResult(
        value=force,
        breakdown=tuple(breakdown),
    )


def calculate_penetration_damage_bonus_region(
    input: PenetrationDamageBonusRegionInput,
) -> CalculationResult:
    region = 1.0 + input.damage_bonus
    return CalculationResult(
        value=region,
        breakdown=(
            _node(CalculationNode.PENETRATION_DAMAGE_BONUS, input.damage_bonus),
            _node(CalculationNode.PENETRATION_DAMAGE_BONUS_REGION, region),
        ),
    )
