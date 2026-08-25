"""Pure defense-region calculation from spec-v1 numeric inputs."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


_DEFENSE_LEVEL_COEFFICIENTS = (
    50,
    54,
    58,
    62,
    66,
    71,
    76,
    82,
    88,
    94,
    100,
    107,
    114,
    121,
    129,
    137,
    145,
    153,
    162,
    172,
    181,
    191,
    201,
    211,
    222,
    233,
    245,
    256,
    268,
    281,
    293,
    306,
    319,
    333,
    347,
    361,
    375,
    390,
    405,
    421,
    436,
    452,
    469,
    485,
    502,
    519,
    537,
    555,
    573,
    592,
    610,
    629,
    649,
    669,
    689,
    709,
    730,
    751,
    772,
    794,
)


@dataclass(frozen=True, slots=True)
class DefenseRegionInput:
    attacker_level: int
    initial_defense: float
    defense_increase: float = 0.0
    defense_reduction: float = 0.0
    defense_ignore: float = 0.0
    penetration_rate: float = 0.0
    penetration_flat: float = 0.0


def defense_level_coefficient(attacker_level: int) -> float:
    if attacker_level < 1:
        raise ValueError("attacker level must be at least 1")
    if attacker_level > len(_DEFENSE_LEVEL_COEFFICIENTS):
        return float(_DEFENSE_LEVEL_COEFFICIENTS[-1])
    return float(_DEFENSE_LEVEL_COEFFICIENTS[attacker_level - 1])


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def calculate_defense_region(input: DefenseRegionInput) -> CalculationResult:
    coefficient = defense_level_coefficient(input.attacker_level)
    effective_defense = max(
        0.0,
        input.initial_defense
        * (
            1.0
            + input.defense_increase
            - input.defense_reduction
            - input.defense_ignore
        )
        * (1.0 - input.penetration_rate)
        - input.penetration_flat,
    )
    region = min(1.0, coefficient / (effective_defense + coefficient))
    breakdown = (
        _node(CalculationNode.DEFENSE_LEVEL_COEFFICIENT, coefficient),
        _node(CalculationNode.ENEMY_INITIAL_DEFENSE, input.initial_defense),
        _node(CalculationNode.ENEMY_DEFENSE_INCREASE, input.defense_increase),
        _node(CalculationNode.ENEMY_DEFENSE_REDUCTION, input.defense_reduction),
        _node(CalculationNode.DAMAGE_DEFENSE_IGNORE, input.defense_ignore),
        _node(CalculationNode.DAMAGE_PENETRATION_RATE, input.penetration_rate),
        _node(CalculationNode.DAMAGE_PENETRATION_FLAT, input.penetration_flat),
        _node(CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE, effective_defense),
        _node(CalculationNode.DAMAGE_DEFENSE_REGION, region),
    )
    return CalculationResult(value=region, breakdown=breakdown)
