from core.calculation import (
    CALCULATION_NODE_DEFINITIONS,
    CalculationNode,
    CalculationNodeValue,
    ModifierAggregation,
    ModifierContribution,
    NodeKind,
    NodeUnit,
)
from core.types import (
    CalculationNode as DomainCalculationNode,
    EffectId,
    EffectOperation,
    Resolved,
    SnapshotRule,
)


def test_every_calculation_node_has_metadata() -> None:
    assert CalculationNode is DomainCalculationNode
    assert set(CALCULATION_NODE_DEFINITIONS) == set(CalculationNode)


def test_same_modifier_node_uses_linear_sum_metadata() -> None:
    definition = CALCULATION_NODE_DEFINITIONS[CalculationNode.DAMAGE_NORMAL_BONUS]

    assert definition.kind is NodeKind.MODIFIER
    assert definition.modifier_aggregation is ModifierAggregation.SUM


def test_percent_and_flat_character_modifiers_are_different_nodes() -> None:
    percent = CALCULATION_NODE_DEFINITIONS[
        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS
    ]
    flat = CALCULATION_NODE_DEFINITIONS[
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS
    ]

    assert percent.unit is NodeUnit.RATIO
    assert flat.unit is NodeUnit.FLAT
    assert percent.node is not flat.node


def test_formula_region_is_not_itself_a_buff_collection() -> None:
    definition = CALCULATION_NODE_DEFINITIONS[
        CalculationNode.DAMAGE_NORMAL_BONUS_REGION
    ]

    assert definition.kind is NodeKind.REGION
    assert definition.modifier_aggregation is None


def test_penetration_force_bonus_and_region_keep_distinct_node_roles() -> None:
    force = CALCULATION_NODE_DEFINITIONS[CalculationNode.PENETRATION_FORCE]
    force_bonus = CALCULATION_NODE_DEFINITIONS[
        CalculationNode.PENETRATION_FORCE_BONUS
    ]
    bonus = CALCULATION_NODE_DEFINITIONS[
        CalculationNode.PENETRATION_DAMAGE_BONUS
    ]
    region = CALCULATION_NODE_DEFINITIONS[
        CalculationNode.PENETRATION_DAMAGE_BONUS_REGION
    ]

    assert force.kind is NodeKind.DERIVED
    assert force_bonus.kind is NodeKind.MODIFIER
    assert force_bonus.unit is NodeUnit.FLAT
    assert force_bonus.modifier_aggregation is ModifierAggregation.SUM
    assert bonus.kind is NodeKind.MODIFIER
    assert bonus.modifier_aggregation is ModifierAggregation.SUM
    assert region.kind is NodeKind.REGION
    assert region.modifier_aggregation is None


def test_calculation_node_value_preserves_modifier_contributions() -> None:
    contribution = ModifierContribution(
        effect_id=EffectId("effect:normal-damage"),
        operation=EffectOperation.ADD,
        value=Resolved(0.75),
    )
    node_value = CalculationNodeValue(
        node=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=Resolved(0.75),
        read_rule=SnapshotRule.SETTLEMENT,
        contributions=(contribution,),
    )
    assert node_value.value == Resolved(0.75)
    assert node_value.contributions == (contribution,)
