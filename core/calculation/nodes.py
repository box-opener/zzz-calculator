"""Calculation-node metadata and resolved node-value containers.

This module names nodes and their aggregation semantics. It intentionally does
not implement any formula or collect Effects from a BattleState.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from core.types.calculation_node import CalculationNode

if TYPE_CHECKING:
    from core.types.common import EffectId, Resolvable
    from core.types.enums import EffectOperation, SnapshotRule


class NodeKind(StrEnum):
    INPUT = "input"
    MODIFIER = "modifier"
    REGION = "region"
    DERIVED = "derived"


class NodeUnit(StrEnum):
    FLAT = "flat"
    RATIO = "ratio"
    MULTIPLIER = "multiplier"
    SECONDS = "seconds"


class ModifierAggregation(StrEnum):
    SUM = "sum"


@dataclass(frozen=True, slots=True)
class CalculationNodeDefinition:
    node: CalculationNode
    kind: NodeKind
    unit: NodeUnit
    modifier_aggregation: ModifierAggregation | None


_MODIFIER_NODES = frozenset(
    {
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_FLAT,
        CalculationNode.CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
        CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
        CalculationNode.ANOMALY_DAMAGE_BONUS,
        CalculationNode.DISCHARGE_DAMAGE_BONUS,
        CalculationNode.TURBULENCE_EXTRA_MULTIPLIER,
        CalculationNode.TURBULENCE_DAMAGE_BONUS,
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
        CalculationNode.DISORDER_BASE_MULTIPLIER,
        CalculationNode.DISORDER_EXTRA_MULTIPLIER,
        CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
        CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
        CalculationNode.POLAR_DISORDER_MULTIPLIER,
        CalculationNode.POLAR_DISORDER_ADDITIONAL_EQUIVALENT_MULTIPLIER,
        CalculationNode.PENETRATION_DAMAGE_BONUS,
        CalculationNode.PENETRATION_FORCE_BONUS,
        CalculationNode.ENEMY_DEFENSE_INCREASE,
        CalculationNode.ENEMY_DEFENSE_REDUCTION,
        CalculationNode.DAMAGE_DEFENSE_IGNORE,
        CalculationNode.DAMAGE_PENETRATION_RATE,
        CalculationNode.DAMAGE_PENETRATION_FLAT,
        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
        CalculationNode.ENEMY_STUN_VULNERABILITY,
        CalculationNode.ENEMY_NORMAL_VULNERABILITY,
        CalculationNode.ENEMY_MOVE_VULNERABILITY,
        CalculationNode.ENEMY_DAMAGE_REDUCTION,
        CalculationNode.DAZE_OUTGOING_BONUS,
        CalculationNode.DAZE_INCOMING_BONUS,
        CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
        CalculationNode.ANOMALY_BUILDUP_INCREASE,
        CalculationNode.ANOMALY_BUILDUP_REDUCTION,
        CalculationNode.ANOMALY_BUILDUP_RESISTANCE,
        CalculationNode.ENERGY_RECOVERY_EFFICIENCY,
        CalculationNode.ENERGY_AUTO_REGEN_FLAT,
    }
)

_REGION_NODES = frozenset(node for node in CalculationNode if node.value.endswith("region"))

_RATIO_NODES = frozenset(
    {
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        CalculationNode.CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS,
        CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_PERCENT_BONUS,
        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        CalculationNode.ANOMALY_DAMAGE_BONUS,
        CalculationNode.DISCHARGE_DAMAGE_BONUS,
        CalculationNode.TURBULENCE_DAMAGE_BONUS,
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
        CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
        CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
        CalculationNode.PENETRATION_DAMAGE_BONUS,
        CalculationNode.ENEMY_DEFENSE_INCREASE,
        CalculationNode.ENEMY_DEFENSE_REDUCTION,
        CalculationNode.DAMAGE_DEFENSE_IGNORE,
        CalculationNode.DAMAGE_PENETRATION_RATE,
        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
        CalculationNode.ENEMY_STUN_VULNERABILITY,
        CalculationNode.ENEMY_NORMAL_VULNERABILITY,
        CalculationNode.ENEMY_MOVE_VULNERABILITY,
        CalculationNode.ENEMY_DAMAGE_REDUCTION,
        CalculationNode.DAZE_OUTGOING_BONUS,
        CalculationNode.DAZE_INCOMING_BONUS,
        CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
        CalculationNode.ANOMALY_BUILDUP_INCREASE,
        CalculationNode.ANOMALY_BUILDUP_REDUCTION,
        CalculationNode.ANOMALY_BUILDUP_RESISTANCE,
        CalculationNode.ENERGY_RECOVERY_EFFICIENCY,
    }
)

_MULTIPLIER_MODIFIER_NODES = frozenset(
    {
        CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
        CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
        CalculationNode.TURBULENCE_EXTRA_MULTIPLIER,
        CalculationNode.DISORDER_BASE_MULTIPLIER,
        CalculationNode.DISORDER_EXTRA_MULTIPLIER,
        CalculationNode.POLAR_DISORDER_MULTIPLIER,
        CalculationNode.POLAR_DISORDER_ADDITIONAL_EQUIVALENT_MULTIPLIER,
    }
)


def _definition_for(node: CalculationNode) -> CalculationNodeDefinition:
    if node in _MODIFIER_NODES:
        return CalculationNodeDefinition(
            node=node,
            kind=NodeKind.MODIFIER,
            unit=(
                NodeUnit.MULTIPLIER
                if node in _MULTIPLIER_MODIFIER_NODES
                else NodeUnit.RATIO
                if node in _RATIO_NODES
                else NodeUnit.FLAT
            ),
            modifier_aggregation=ModifierAggregation.SUM,
        )
    if node in _REGION_NODES:
        return CalculationNodeDefinition(
            node=node,
            kind=NodeKind.REGION,
            unit=NodeUnit.MULTIPLIER,
            modifier_aggregation=None,
        )
    return CalculationNodeDefinition(
        node=node,
        kind=NodeKind.DERIVED,
        unit=(
            NodeUnit.MULTIPLIER
            if "multiplier" in node.value or "coefficient" in node.value
            else NodeUnit.FLAT
        ),
        modifier_aggregation=None,
    )


CALCULATION_NODE_DEFINITIONS: Mapping[CalculationNode, CalculationNodeDefinition] = (
    MappingProxyType({node: _definition_for(node) for node in CalculationNode})
)


@dataclass(frozen=True, slots=True)
class ModifierContribution:
    effect_id: EffectId
    operation: EffectOperation
    value: Resolvable[float]


@dataclass(frozen=True, slots=True)
class CalculationNodeValue:
    node: CalculationNode
    value: Resolvable[float]
    read_rule: SnapshotRule
    contributions: tuple[ModifierContribution, ...] = ()
