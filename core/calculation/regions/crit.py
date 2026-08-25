"""Pure expected-value crit-region calculation."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class CritRegionInput:
    crit_rate: float
    crit_damage: float


@dataclass(frozen=True, slots=True)
class AnomalyCritRegionInput:
    crit_rate: float
    crit_damage: float


@dataclass(frozen=True, slots=True)
class DischargeCritRegionInput:
    crit_rate: float
    crit_damage: float


@dataclass(frozen=True, slots=True)
class TurbulenceCritRegionInput:
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


def calculate_anomaly_crit_region(
    input: AnomalyCritRegionInput,
) -> CalculationResult:
    region = 1.0 * (1.0 - input.crit_rate) + (
        1.0 + input.crit_damage
    ) * input.crit_rate
    breakdown = (
        _node(CalculationNode.ANOMALY_CRIT_REGION, region),
    )
    return CalculationResult(value=region, breakdown=breakdown)


def _calculate_special_crit_region(
    crit_rate: float,
    crit_damage: float,
    node: CalculationNode,
) -> CalculationResult:
    region = 1.0 * (1.0 - crit_rate) + (1.0 + crit_damage) * crit_rate
    return CalculationResult(
        value=region,
        breakdown=(_node(node, region),),
    )


def calculate_discharge_crit_region(
    input: DischargeCritRegionInput,
) -> CalculationResult:
    return _calculate_special_crit_region(
        input.crit_rate,
        input.crit_damage,
        CalculationNode.DISCHARGE_CRIT_REGION,
    )


def calculate_turbulence_crit_region(
    input: TurbulenceCritRegionInput,
) -> CalculationResult:
    return _calculate_special_crit_region(
        input.crit_rate,
        input.crit_damage,
        CalculationNode.TURBULENCE_CRIT_REGION,
    )
