"""Presentation rule for the current enemy Frostbite crit-damage state."""

from core.application.ids import RuleItemId, ScenarioConditionId
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import ConditionResolution, ScenarioCondition
from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterId,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ModifierEffect,
    ModifierResult,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
)


FROSTBITE_CRIT_DAMAGE_TEXT = (
    "霜寒状态下，全角色攻击处于霜寒状态的敌人时造成的暴击伤害提高10%。"
)
FROSTBITE_CONDITION_PREFIX = "condition:enemy:frostbite-crit-damage-active:primary:"
FROSTBITE_RULE_PREFIX = "rule:enemy:frostbite-crit-damage:primary:"


def frostbite_crit_damage_controls(
    primary_character_id: str | CharacterId,
    primary_element: Element,
) -> tuple[ScenarioCondition, CalculationRuleItem]:
    """Build one primary-scoped state control and its event-only effect."""

    primary = CharacterId(str(primary_character_id))
    suffix = str(primary)
    condition_id = ScenarioConditionId(
        f"condition:enemy:frostbite-crit-damage-active:primary:{suffix}"
    )
    rule_id = RuleItemId(f"rule:enemy:frostbite-crit-damage:primary:{suffix}")
    source = RuleSource(
        source_id=RuleSourceId(f"source:enemy:frostbite-crit-damage:primary:{suffix}"),
        source_type=EffectSourceType.STATE,
        label="敌人霜寒状态",
        raw_text=FROSTBITE_CRIT_DAMAGE_TEXT,
    )
    condition = ScenarioCondition(
        condition_id=condition_id,
        label="目标当前处于霜寒状态",
        original_text=FROSTBITE_CRIT_DAMAGE_TEXT,
        resolution=ConditionResolution.USER_SELECTED,
        value=primary_element in {Element.ICE, Element.LIESHUANG},
    )
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:enemy:frostbite-crit-damage:primary:{suffix}"),
            source=source,
            owner=primary,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                AnyFilter(
                    (
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTypeFilter(DamageType.PENETRATION),
                    )
                ),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            operation=EffectOperation.ADD,
            value=Resolved(0.10),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=rule_id,
        owner=primary,
        source=source,
        display_name="霜寒状态：暴击伤害提高10%",
        original_text=FROSTBITE_CRIT_DAMAGE_TEXT,
        eligibility=RuleEligibility.ELIGIBLE,
        condition_ids=(condition_id,),
        effects=(effect,),
    )
    return condition, rule
