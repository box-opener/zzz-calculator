from __future__ import annotations

from dataclasses import replace

import pytest

from core.application import (
    CalculationRuleItem,
    CalculationScenario,
    ConditionResolution,
    RuleEligibility,
    RuleItemId,
    ScenarioCondition,
    ScenarioConditionId,
    ScenarioTriggerFact,
)
from core.application.matching import (
    CharacterMatchProfile,
    EffectMatchContext,
    EffectMatchStatus,
    EffectMatcher,
    EnemyMatchProfile,
)
from core.calculation import CalculationNode
from core.types import (
    AllCondition,
    AnyFilter,
    AlwaysCondition,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    BattleEventKind,
    BattleStateId,
    CalculationContext,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    DirectDamageEvent,
    DynamicIdentity,
    DynamicIdentityCondition,
    DynamicIdentityFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EnemyId,
    EnemySnapshot,
    EventSelector,
    EnemyStateFilter,
    FieldPosition,
    FieldPositionFilter,
    FixedMultiplier,
    MoveId,
    ModifierEffect,
    ModifierResult,
    NotFilter,
    NoCritRule,
    OperationState,
    OperationStateFilter,
    Resolved,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SkillGroupFilter,
    SnapshotRule,
    StateId,
    StatePresentCondition,
    StandardCritRule,
    Unresolved,
)


def _source() -> RuleSource:
    return RuleSource(
        source_id=RuleSourceId("source:matcher-test"),
        source_type=EffectSourceType.SKILL,
        label="matcher test",
    )


def _stats() -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.0),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.FIRE: Resolved(0.0)},
    )


def _event(
    *,
    element: Element = Element.FIRE,
    skill_group: SkillGroup | None = SkillGroup.DODGE,
    tags: frozenset[DamageTag] = frozenset({DamageTag.DODGE_COUNTER}),
) -> DirectDamageEvent:
    dealer = CharacterId("character:operator")
    return DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:matcher"),
            battle_state_id=BattleStateId("battle:matcher"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:matcher"),
            element=element,
            created_at=1.0,
            skill_group=skill_group,
            move_id=MoveId("move:current"),
            damage_tags=tags,
        ),
        base_settlement_data_source=CurrentAttackValueSource(dealer),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(dealer),
    )


def _context(
    event: DirectDamageEvent,
    scenario: CalculationScenario,
    *,
    owner: CharacterId = CharacterId("character:owner"),
    owner_role: CharacterRole = CharacterRole.SUPPORT,
    enemy_states: frozenset[StateId] = frozenset(),
    owner_states: frozenset[StateId] = frozenset(),
) -> EffectMatchContext:
    operator = CharacterId("character:operator")
    target = EnemyId("enemy:matcher")
    snapshots = [CharacterSnapshot(operator, 60, _stats())]
    profiles = [
        CharacterMatchProfile(
            operator,
            CharacterRole.ATTACK,
            states=owner_states if owner == operator else frozenset(),
            field_position=FieldPosition.FRONT,
            operation_state=OperationState.OPERATED,
        )
    ]
    if owner != operator:
        snapshots.append(CharacterSnapshot(owner, 60, _stats()))
        profiles.append(
            CharacterMatchProfile(
                owner,
                owner_role,
                states=owner_states,
                field_position=FieldPosition.BACK,
                operation_state=OperationState.NOT_OPERATED,
            )
        )
    return EffectMatchContext(
        current_event=event,
        calculation_context=CalculationContext(
            event=event,
            battle_state_id=BattleStateId("battle:matcher"),
            character_snapshots=tuple(snapshots),
            target_snapshot=EnemySnapshot(
                enemy_id=target,
                level=70,
                initial_defense=Resolved(794.0),
                damage_resistance={Element.FIRE: Resolved(0.0)},
                anomaly_buildup_resistance={},
                daze_resistance=Resolved(0.0),
                damage_reduction=Resolved(0.0),
            ),
        ),
        scenario=scenario,
        current_operator=operator,
        team=tuple(profiles),
        target=EnemyMatchProfile(target, enemy_states),
    )


def _effect(
    effect_id: str,
    *,
    owner: CharacterId = CharacterId("character:owner"),
    target: EffectTarget = EffectTarget.TEAM,
    trigger=None,
    condition=None,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(effect_id),
            source=_source(),
            owner=owner,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            trigger=trigger,
            condition=condition,
            filters=filters,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.2),
        ),
    )


def _rule(
    effect: ModifierEffect,
    scenario: CalculationScenario,
    *,
    eligibility: RuleEligibility = RuleEligibility.ELIGIBLE,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:{effect.rule.effect_id}"),
        owner=effect.rule.owner,
        source=_source(),
        display_name="matcher rule",
        original_text="matcher rule text",
        eligibility=eligibility,
        condition_ids=condition_ids,
        effects=(effect,),
    )


def _scenario(
    *,
    enabled: tuple[str, ...] = ("effect:test",),
    conditions: tuple[ScenarioCondition, ...] = (),
    trigger_facts: tuple[ScenarioTriggerFact, ...] = (),
) -> CalculationScenario:
    return CalculationScenario(
        scenario_id="scenario:matcher",
        current_operator=CharacterId("character:operator"),
        conditions=conditions,
        trigger_facts=trigger_facts,
        enabled_rule_item_ids=frozenset(RuleItemId(f"rule:{item}") for item in enabled),
    )


def test_target_and_current_event_filters_are_separate() -> None:
    event = _event()
    effect = _effect(
        "effect:test",
        filters=(
            ElementFilter(Element.FIRE),
            DamageTypeFilter(DamageType.DIRECT),
            SkillGroupFilter(SkillGroup.DODGE),
            DamageTagFilter(DamageTag.DODGE_COUNTER),
        ),
    )
    result = EffectMatcher().match_rule_item(
        _rule(effect, _scenario()),
        _context(event, _scenario()),
    )
    assert result.status is EffectMatchStatus.MATCHED
    assert len(result.matched_effects) == 1

    self_effect = _effect("effect:self", target=EffectTarget.SELF)
    self_result = EffectMatcher().match_rule_item(
        _rule(self_effect, _scenario(enabled=("effect:self",))),
        _context(event, _scenario(enabled=("effect:self",))),
    )
    assert self_result.status is EffectMatchStatus.NOT_MATCHED


def test_trigger_fact_matches_trigger_event_not_settlement_event() -> None:
    effect = _effect(
        "effect:triggered",
        trigger=EventSelector(
            event_kind=BattleEventKind.SKILL_HIT,
            move_id=MoveId("move:trigger"),
        ),
    )
    scenario = _scenario(
        enabled=("effect:triggered",),
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:triggered"),
                event_kind=BattleEventKind.SKILL_HIT,
                move_id=MoveId("move:trigger"),
            ),
        ),
    )
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(_event(skill_group=SkillGroup.ULTIMATE), scenario),
    )
    assert result.status is EffectMatchStatus.MATCHED

    missing = _scenario(enabled=("effect:triggered",))
    missing_result = EffectMatcher().match_rule_item(
        _rule(effect, missing),
        _context(_event(), missing),
    )
    assert missing_result.status is EffectMatchStatus.BLOCKED


def test_trigger_selector_mismatch_is_not_match() -> None:
    effect = _effect(
        "effect:wrong-trigger",
        trigger=EventSelector(event_kind=BattleEventKind.SKILL_HIT),
    )
    scenario = _scenario(
        enabled=("effect:wrong-trigger",),
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:wrong-trigger"),
                event_kind=BattleEventKind.DAMAGE,
            ),
        ),
    )
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(_event(), scenario),
    )
    assert result.status is EffectMatchStatus.NOT_MATCHED


def test_rule_conditions_use_three_valued_logic() -> None:
    condition = ScenarioCondition(
        condition_id=ScenarioConditionId("condition:active"),
        label="active",
        original_text="active",
        resolution=ConditionResolution.USER_SELECTED,
        value=True,
    )
    effect = _effect("effect:condition", condition=AlwaysCondition())
    scenario = _scenario(
        enabled=("effect:condition",),
        conditions=(condition,),
    )
    matching = EffectMatcher().match_rule_item(
        _rule(
            effect,
            scenario,
            eligibility=RuleEligibility.SCENARIO_REQUIRED,
            condition_ids=(condition.condition_id,),
        ),
        _context(_event(), scenario),
    )
    assert matching.status is EffectMatchStatus.MATCHED

    unresolved_condition = replace(condition, value=None)
    unresolved_scenario = replace(scenario, conditions=(unresolved_condition,))
    blocked = EffectMatcher().match_rule_item(
        _rule(
            effect,
            unresolved_scenario,
            eligibility=RuleEligibility.SCENARIO_REQUIRED,
            condition_ids=(condition.condition_id,),
        ),
        _context(_event(), unresolved_scenario),
    )
    assert blocked.status is EffectMatchStatus.BLOCKED

    false_condition = replace(condition, value=False)
    false_scenario = replace(scenario, conditions=(false_condition,))
    not_matched = EffectMatcher().match_rule_item(
        _rule(
            effect,
            false_scenario,
            eligibility=RuleEligibility.SCENARIO_REQUIRED,
            condition_ids=(condition.condition_id,),
        ),
        _context(_event(), false_scenario),
    )
    assert not_matched.status is EffectMatchStatus.NOT_MATCHED


def test_state_position_operation_and_dynamic_identity_filters() -> None:
    owner = CharacterId("character:operator")
    effect = _effect(
        "effect:state-facts",
        owner=owner,
        target=EffectTarget.SELF,
        condition=AllCondition(
            (
                StatePresentCondition(EffectTarget.SELF, StateId("state:owner")),
                DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            )
        ),
        filters=(
            FieldPositionFilter(FieldPosition.FRONT),
            OperationStateFilter(OperationState.OPERATED),
            DynamicIdentityFilter(DynamicIdentity.DAMAGE_DEALER),
        ),
    )
    scenario = _scenario(enabled=("effect:state-facts",))
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(
            _event(),
            scenario,
            owner=owner,
            owner_role=CharacterRole.ATTACK,
            owner_states=frozenset({StateId("state:owner")}),
        ),
    )
    assert result.status is EffectMatchStatus.MATCHED


def test_enemy_state_filter_and_or_not_filters() -> None:
    effect = _effect(
        "effect:enemy-filter",
        filters=(
            EnemyStateFilter(StateId("state:enemy")),
            AnyFilter(
                (
                    DamageTagFilter(DamageTag.BASIC_ATTACK),
                    DamageTagFilter(DamageTag.DODGE_COUNTER),
                )
            ),
            NotFilter(DamageTagFilter(DamageTag.DASH_ATTACK)),
        ),
    )
    scenario = _scenario(enabled=("effect:enemy-filter",))
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(
            _event(tags=frozenset({DamageTag.DODGE_COUNTER})),
            scenario,
            enemy_states=frozenset({StateId("state:enemy")}),
        ),
    )
    assert result.status is EffectMatchStatus.MATCHED


def test_dynamic_identity_requires_history_when_identity_is_history_based() -> None:
    actor = CharacterId("character:operator")
    event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:attribute"),
            battle_state_id=BattleStateId("battle:matcher"),
            damage_dealer=actor,
            target_enemy=EnemyId("enemy:matcher"),
            element=Element.PHYSICAL,
            created_at=1.0,
        ),
        anomaly_triggerer=actor,
        base_settlement_data_source=AnomalyRecordValueSource(
            AnomalyRecordId("anomaly:missing")
        ),
        history_record_source=AnomalyRecordId("anomaly:missing"),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    effect = _effect(
        "effect:history-identity",
        owner=actor,
        target=EffectTarget.SELF,
        condition=DynamicIdentityCondition(DynamicIdentity.ANOMALY_TRIGGER),
    )
    scenario = _scenario(enabled=("effect:history-identity",))
    context = _context(_event(), scenario, owner=actor, owner_role=CharacterRole.ATTACK)
    context = replace(
        context,
        current_event=event,
        calculation_context=replace(context.calculation_context, event=event),
    )
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        context,
    )
    assert result.status is EffectMatchStatus.BLOCKED
