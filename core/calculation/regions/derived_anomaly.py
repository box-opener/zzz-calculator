"""Independent damage-bonus regions for historical anomaly damage subtypes."""

from dataclasses import dataclass

from core.types import CalculationNode, Resolved, SnapshotRule

from ..nodes import CalculationNodeValue
from ..result import CalculationResult


@dataclass(frozen=True, slots=True)
class DischargeDamageBonusRegionInput:
    damage_bonus: float = 0.0


@dataclass(frozen=True, slots=True)
class TurbulenceDamageBonusRegionInput:
    damage_bonus: float = 0.0


@dataclass(frozen=True, slots=True)
class LuminanceAnomalyDamageBonusRegionInput:
    anomaly_damage_bonus: float = 0.0


def _region(
    bonus: float,
    bonus_node: CalculationNode,
    region_node: CalculationNode,
) -> CalculationResult:
    value = 1.0 + bonus
    return CalculationResult(
        value=value,
        breakdown=(
            CalculationNodeValue(
                node=bonus_node,
                value=Resolved(bonus),
                read_rule=SnapshotRule.SETTLEMENT,
            ),
            CalculationNodeValue(
                node=region_node,
                value=Resolved(value),
                read_rule=SnapshotRule.SETTLEMENT,
            ),
        ),
    )


def calculate_discharge_damage_bonus_region(
    input: DischargeDamageBonusRegionInput,
) -> CalculationResult:
    return _region(
        input.damage_bonus,
        CalculationNode.DISCHARGE_DAMAGE_BONUS,
        CalculationNode.DISCHARGE_DAMAGE_BONUS_REGION,
    )


def calculate_turbulence_damage_bonus_region(
    input: TurbulenceDamageBonusRegionInput,
) -> CalculationResult:
    return _region(
        input.damage_bonus,
        CalculationNode.TURBULENCE_DAMAGE_BONUS,
        CalculationNode.TURBULENCE_DAMAGE_BONUS_REGION,
    )


def calculate_luminance_anomaly_damage_bonus_region(
    input: LuminanceAnomalyDamageBonusRegionInput,
) -> CalculationResult:
    return _region(
        input.anomaly_damage_bonus,
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS_REGION,
    )
