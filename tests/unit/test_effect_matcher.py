from __future__ import annotations

from dataclasses import fields, replace

import pytest

from core.application import (
    CalculationRuleItem,
    CalculationScenario,
    ConditionResolution,
    RuleEligibility,
    RuleItemId,
    ScenarioCondition,
    ScenarioConditionId,
    ScenarioRuleStack,
    ScenarioTriggerFact,
)
from core.application.matching import (
    CharacterMatchProfile,
    DynamicIdentityResolver,
    EffectMatchContext,
    EffectMatchStatus,
    EffectMatcher,
    EnemyMatchProfile,
)
from core.calculation import CalculationNode
from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AllCondition,
    AnyCondition,
    AnyFilter,
    AlwaysCondition,
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    BattleEventKind,
    BattleStateId,
    CalculationContext,
    CharacterFilter,
    CharacterId,
    CharacterRole,
    CharacterRoleFilter,
    CharacterSnapshot,
    CharacterStats,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DamageEvent,
    DamageDealerIdentityFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    DirectDamageEvent,
    DisorderDamageEvent,
    PolarDisorderDamageEvent,
    DischargeDamageEvent,
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
    LuminanceDamageEvent,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoAnomalyCrit,
    NotFilter,
    NoCritRule,
    OperationState,
    OperationStateFilter,
    PanelStatThresholdCondition,
    Resolved,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SkillGroupFilter,
    SnapshotRule,
    StateId,
    RuleStackCondition,
    StatePresentCondition,
    StandardCritRule,
    TurbulenceDamageEvent,
    Unresolved,
    UnresolvedEffect,
    UnresolvedReason,
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


def _record(
    record_id: AnomalyRecordId,
    triggerer: CharacterId,
) -> AnomalyRecord:
    contribution = AnomalyContribution(
        contributor=triggerer,
        actual_written_buildup=100.0,
        anomaly_effect_strength=Resolved(1000.0),
        impact_strength=Resolved(100.0),
        occurred_at=1.0,
    )
    return AnomalyRecord(
        record_id=record_id,
        target_enemy=EnemyId("enemy:matcher"),
        element=Element.PHYSICAL,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[Element.PHYSICAL],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[Element.PHYSICAL],
        weighted_anomaly_effect_strength=Resolved(1000.0),
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=Resolved(1.0),
        contributors=(triggerer,),
        anomaly_triggerer=triggerer,
        crit_capability=NoAnomalyCrit(),
        triggered_at=1.0,
        duration=Resolved(10.0),
        contributions=(contribution,),
    )


def _context(
    event: DamageEvent,
    scenario: CalculationScenario,
    *,
    owner: CharacterId = CharacterId("character:owner"),
    owner_role: CharacterRole = CharacterRole.SUPPORT,
    enemy_states: frozenset[StateId] = frozenset(),
    owner_states: frozenset[StateId] = frozenset(),
    history_records: tuple[AnomalyRecord, ...] = (),
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
            history_records=history_records,
        ),
        scenario=scenario,
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


def test_rule_stack_condition_follows_the_resolved_stack_not_a_second_boolean() -> None:
    effect = _effect(
        "stacked",
        owner=CharacterId("character:operator"),
        target=EffectTarget.SELF,
        condition=RuleStackCondition("rule:stacked", 2),
    )
    event = _event()
    scenario = _scenario(enabled=("stacked",))
    rule = _rule(effect, scenario)
    scenario = replace(
        scenario,
        rule_stack_counts=(ScenarioRuleStack(rule_item_id=rule.rule_id, value=1),),
    )
    result = EffectMatcher().match_rule_item(rule, _context(event, scenario))
    assert result.status is EffectMatchStatus.NOT_MATCHED

    scenario = replace(
        scenario,
        rule_stack_counts=(ScenarioRuleStack(rule_item_id=rule.rule_id, value=2),),
    )
    result = EffectMatcher().match_rule_item(rule, _context(event, scenario))
    assert result.status is EffectMatchStatus.MATCHED
    assert len(result.matched_effects) == 1

    self_effect = _effect("effect:self", target=EffectTarget.SELF)
    self_result = EffectMatcher().match_rule_item(
        _rule(self_effect, _scenario(enabled=("effect:self",))),
        _context(event, _scenario(enabled=("effect:self",))),
    )
    assert self_result.status is EffectMatchStatus.NOT_MATCHED


def test_rule_stack_condition_does_not_survive_when_source_rule_is_disabled() -> None:
    effect = _effect(
        "stack-dependent",
        owner=CharacterId("character:operator"),
        target=EffectTarget.SELF,
        condition=RuleStackCondition("rule:stack-source", 2),
    )
    rule = replace(_rule(effect, _scenario()), rule_id=RuleItemId("rule:stack-dependent"))
    scenario = replace(
        _scenario(enabled=("stack-dependent",)),
        rule_stack_counts=(ScenarioRuleStack(RuleItemId("rule:stack-source"), 2),),
    )

    result = EffectMatcher().match_rule_item(rule, _context(_event(), scenario))

    assert result.status is EffectMatchStatus.NOT_MATCHED


def test_move_id_filter_matches_semantic_move_identity_only() -> None:
    event = _event()
    matching = _effect(
        "effect:move-id",
        filters=(MoveIdFilter(MoveId("move:current")),),
    )
    non_matching = _effect(
        "effect:other-move-id",
        filters=(MoveIdFilter(MoveId("move:other")),),
    )

    assert (
        EffectMatcher()
        .match_rule_item(
            _rule(matching, _scenario(enabled=("effect:move-id",))),
            _context(event, _scenario(enabled=("effect:move-id",))),
        )
        .status
        is EffectMatchStatus.MATCHED
    )
    assert (
        EffectMatcher()
        .match_rule_item(
            _rule(non_matching, _scenario(enabled=("effect:other-move-id",))),
            _context(event, _scenario(enabled=("effect:other-move-id",))),
        )
        .status
        is EffectMatchStatus.NOT_MATCHED
    )


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


def test_damage_dealer_identity_filter_matches_support_entry_actor_not_operator() -> None:
    operator = CharacterId("character:operator")
    holder = CharacterId("character:entry-holder")
    effect_id = EffectId("effect:entry-holder")
    scenario = _scenario(
        enabled=(str(effect_id),),
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=effect_id,
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=holder,
            ),
        ),
    )
    effect = _effect(
        str(effect_id),
        owner=holder,
        target=EffectTarget.TEAM,
        trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
        filters=(
            DamageDealerIdentityFilter(DynamicIdentity.SUPPORT_ENTRY_CHARACTER),
        ),
    )

    holder_event = replace(
        _event(),
        metadata=replace(_event().metadata, damage_dealer=holder),
    )
    matched = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(holder_event, scenario, owner=holder),
    )
    assert matched.status is EffectMatchStatus.MATCHED
    assert scenario.current_operator == operator
    assert holder != operator

    operator_event = _event()
    not_matched = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(operator_event, scenario, owner=holder),
    )
    assert not_matched.status is EffectMatchStatus.NOT_MATCHED


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


def test_attribute_anomaly_trigger_uses_event_but_contributors_require_history() -> None:
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
    assert result.status is EffectMatchStatus.MATCHED

    contributor_effect = _effect(
        "effect:history-contributors",
        owner=actor,
        target=EffectTarget.SELF,
        condition=DynamicIdentityCondition(DynamicIdentity.ANOMALY_CONTRIBUTORS),
    )
    contributor_scenario = _scenario(enabled=("effect:history-contributors",))
    contributor_context = replace(context, scenario=contributor_scenario)
    contributor_result = EffectMatcher().match_rule_item(
        _rule(contributor_effect, contributor_scenario),
        contributor_context,
    )
    assert contributor_result.status is EffectMatchStatus.BLOCKED


def test_current_operator_has_one_scenario_source_of_truth() -> None:
    scenario = _scenario()
    context = _context(_event(), scenario)

    assert context.current_operator == scenario.current_operator
    assert "current_operator" not in {
        item.name for item in fields(EffectMatchContext)
    }

    mismatched = replace(
        scenario,
        current_operator=CharacterId("character:not-in-team"),
    )
    with pytest.raises(ValueError, match="current_operator"):
        _context(_event(), mismatched)


def test_enemy_target_keeps_character_side_filters_independent() -> None:
    operator = CharacterId("character:operator")
    effect = _effect(
        "effect:enemy-character-filter",
        target=EffectTarget.ENEMY,
        filters=(
            CharacterFilter(operator),
            CharacterRoleFilter(CharacterRole.ATTACK),
            FieldPositionFilter(FieldPosition.FRONT),
            OperationStateFilter(OperationState.OPERATED),
        ),
    )
    scenario = _scenario(enabled=("effect:enemy-character-filter",))
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(_event(), scenario),
    )

    assert result.status is EffectMatchStatus.MATCHED


def test_three_valued_short_circuit_discards_irrelevant_blocking_diagnostics() -> None:
    operator = CharacterId("character:operator")
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes="unknown condition",
        original_text="unknown",
    )
    false_and_unknown = _effect(
        "effect:false-and-unknown",
        owner=operator,
        target=EffectTarget.SELF,
        condition=AllCondition(
            (
                StatePresentCondition(
                    EffectTarget.SELF,
                    StateId("state:absent"),
                ),
                unresolved,
            )
        ),
    )
    false_scenario = _scenario(enabled=("effect:false-and-unknown",))
    false_result = EffectMatcher().match_rule_item(
        _rule(false_and_unknown, false_scenario),
        _context(_event(), false_scenario, owner=operator),
    )
    assert false_result.status is EffectMatchStatus.NOT_MATCHED
    assert not any(item.blocking for item in false_result.diagnostics)

    true_or_unknown = _effect(
        "effect:true-or-unknown",
        condition=AnyCondition((AlwaysCondition(), unresolved)),
    )
    true_scenario = _scenario(enabled=("effect:true-or-unknown",))
    true_result = EffectMatcher().match_rule_item(
        _rule(true_or_unknown, true_scenario),
        _context(_event(), true_scenario),
    )
    assert true_result.status is EffectMatchStatus.MATCHED
    assert not any(item.blocking for item in true_result.diagnostics)

    irrelevant_self = _effect(
        "effect:irrelevant-self",
        target=EffectTarget.SELF,
        condition=unresolved,
    )
    irrelevant_scenario = _scenario(enabled=("effect:irrelevant-self",))
    irrelevant_result = EffectMatcher().match_rule_item(
        _rule(irrelevant_self, irrelevant_scenario),
        _context(_event(), irrelevant_scenario),
    )
    assert irrelevant_result.status is EffectMatchStatus.NOT_MATCHED
    assert not any(item.blocking for item in irrelevant_result.diagnostics)

    false_rule_condition = ScenarioCondition(
        condition_id=ScenarioConditionId("condition:false"),
        label="false",
        original_text="false",
        resolution=ConditionResolution.STATIC,
        value=False,
    )
    unknown_rule_condition = ScenarioCondition(
        condition_id=ScenarioConditionId("condition:unknown"),
        label="unknown",
        original_text="unknown",
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )
    rule_effect = _effect("effect:rule-short-circuit")
    rule_scenario = _scenario(
        enabled=("effect:rule-short-circuit",),
        conditions=(false_rule_condition, unknown_rule_condition),
    )
    rule_result = EffectMatcher().match_rule_item(
        _rule(
            rule_effect,
            rule_scenario,
            eligibility=RuleEligibility.SCENARIO_REQUIRED,
            condition_ids=(
                false_rule_condition.condition_id,
                unknown_rule_condition.condition_id,
            ),
        ),
        _context(_event(), rule_scenario),
    )
    assert rule_result.status is EffectMatchStatus.NOT_MATCHED
    assert not any(item.blocking for item in rule_result.diagnostics)


def test_unresolved_effect_only_blocks_after_known_gates_match() -> None:
    base_rule = EffectRule(
        effect_id=EffectId("effect:unresolved-irrelevant"),
        source=_source(),
        owner=CharacterId("character:owner"),
        target=EffectTarget.TEAM,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        filters=(DamageTagFilter(DamageTag.BASIC_ATTACK),),
    )
    unresolved_effect = UnresolvedEffect(
        rule=base_rule,
        unresolved=Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_TEXT,
            notes="unknown result",
        ),
    )
    scenario = _scenario(enabled=("effect:unresolved-irrelevant",))
    item = CalculationRuleItem(
        rule_id=RuleItemId("rule:effect:unresolved-irrelevant"),
        owner=base_rule.owner,
        source=_source(),
        display_name="unresolved irrelevant",
        original_text="unresolved irrelevant",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(unresolved_effect,),
    )
    result = EffectMatcher().match_rule_item(
        item,
        _context(_event(), scenario),
    )

    assert result.status is EffectMatchStatus.NOT_MATCHED
    assert not any(item.blocking for item in result.diagnostics)


def test_one_rule_item_preserves_matched_not_matched_and_blocked_effects() -> None:
    matched = _effect("effect:multi-matched")
    not_matched = _effect(
        "effect:multi-not-matched",
        filters=(DamageTagFilter(DamageTag.BASIC_ATTACK),),
    )
    blocked = _effect(
        "effect:multi-blocked",
        condition=Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes="missing condition data",
        ),
    )
    rule_id = RuleItemId("rule:multi")
    scenario = CalculationScenario(
        scenario_id="scenario:multi",
        current_operator=CharacterId("character:operator"),
        enabled_rule_item_ids=frozenset({rule_id}),
    )
    rule = CalculationRuleItem(
        rule_id=rule_id,
        owner=CharacterId("character:owner"),
        source=_source(),
        display_name="multi effect rule",
        original_text="multi effect rule",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(matched, not_matched, blocked),
    )
    result = EffectMatcher().match_rule_item(
        rule,
        _context(_event(), scenario),
    )

    assert result.status is EffectMatchStatus.BLOCKED
    assert result.matched_effects == (matched,)
    assert tuple(item.status for item in result.effects) == (
        EffectMatchStatus.MATCHED,
        EffectMatchStatus.NOT_MATCHED,
        EffectMatchStatus.BLOCKED,
    )


def test_all_typed_trigger_identities_resolve_from_their_events() -> None:
    actor = CharacterId("character:operator")
    record_id = AnomalyRecordId("anomaly:identity")
    record = _record(record_id, actor)
    metadata = DamageEventMetadata(
        event_id=DamageEventId("damage:identity"),
        battle_state_id=BattleStateId("battle:matcher"),
        damage_dealer=actor,
        target_enemy=EnemyId("enemy:matcher"),
        element=Element.PHYSICAL,
        created_at=1.0,
    )
    events_and_identities = (
        (
            DisorderDamageEvent(
                metadata,
                actor,
                AnomalyRecordValueSource(record_id),
                record_id,
                FixedMultiplier(Resolved(1.0)),
                NoCritRule(),
            ),
            DynamicIdentity.DISORDER_TRIGGER,
        ),
        (
            TurbulenceDamageEvent(
                metadata,
                actor,
                AnomalyRecordValueSource(record_id),
                record_id,
                FixedMultiplier(Resolved(1.0)),
                NoCritRule(),
            ),
            DynamicIdentity.WIND_ANOMALY_TRIGGER,
        ),
        (
            LuminanceDamageEvent(
                metadata,
                actor,
                AnomalyRecordValueSource(record_id),
                record_id,
                FixedMultiplier(Resolved(1.0)),
                NoCritRule(),
            ),
            DynamicIdentity.LUMINANCE_TRIGGER,
        ),
        (
            DischargeDamageEvent(
                metadata,
                actor,
                AnomalyRecordValueSource(record_id),
                record_id,
                FixedMultiplier(Resolved(1.0)),
                NoCritRule(),
            ),
            DynamicIdentity.DISCHARGE_TRIGGER,
        ),
    )
    scenario = _scenario()

    for event, identity in events_and_identities:
        context = _context(
            event,
            scenario,
            owner=actor,
            owner_role=CharacterRole.ATTACK,
            history_records=(record,),
        )
        resolution = DynamicIdentityResolver().resolve(identity, context)
        assert resolution.identities == frozenset({actor})


def test_polar_disorder_resolves_triggerer_and_selected_record_identities() -> None:
    yanagi = CharacterId("character:1221")
    source = CharacterId("character:source")
    record_id = AnomalyRecordId("anomaly:polar-source")
    record = _record(record_id, source)
    event = PolarDisorderDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:polar-identity"),
            battle_state_id=BattleStateId("battle:matcher"),
            damage_dealer=yanagi,
            target_enemy=record.target_enemy,
            element=record.element,
            created_at=2.0,
        ),
        disorder_triggerer=yanagi,
        source_anomaly_character_id=source,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        polarity_multiplier=0.15,
        anomaly_proficiency_coefficient=32.0,
        crit_rule=NoCritRule(),
    )
    scenario = _scenario()
    context = _context(
        event,
        scenario,
        owner=yanagi,
        owner_role=CharacterRole.ANOMALY,
        history_records=(record,),
    )

    assert DynamicIdentityResolver().resolve(
        DynamicIdentity.DISORDER_TRIGGER, context
    ).identities == frozenset({yanagi})
    assert DynamicIdentityResolver().resolve(
        DynamicIdentity.ANOMALY_TRIGGER, context
    ).identities == frozenset({source})
    assert DynamicIdentityResolver().resolve(
        DynamicIdentity.ANOMALY_CONTRIBUTORS, context
    ).identities == frozenset({source})


def test_anomaly_contributors_and_subtype_filter_positive_paths() -> None:
    actor = CharacterId("character:operator")
    record_id = AnomalyRecordId("anomaly:positive")
    record = _record(record_id, actor)
    event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:attribute-positive"),
            battle_state_id=BattleStateId("battle:matcher"),
            damage_dealer=actor,
            target_enemy=EnemyId("enemy:matcher"),
            element=Element.PHYSICAL,
            created_at=1.0,
        ),
        anomaly_triggerer=actor,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    effect = _effect(
        "effect:contributors-positive",
        owner=actor,
        target=EffectTarget.SELF,
        condition=DynamicIdentityCondition(DynamicIdentity.ANOMALY_CONTRIBUTORS),
        filters=(DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),),
    )
    scenario = _scenario(enabled=("effect:contributors-positive",))
    result = EffectMatcher().match_rule_item(
        _rule(effect, scenario),
        _context(
            event,
            scenario,
            owner=actor,
            owner_role=CharacterRole.ATTACK,
            history_records=(record,),
        ),
    )

    assert result.status is EffectMatchStatus.MATCHED


def test_attribute_event_and_record_trigger_mismatch_is_blocking_data_quality() -> None:
    actor = CharacterId("character:operator")
    other = CharacterId("character:other")
    record_id = AnomalyRecordId("anomaly:mismatch")
    record = _record(record_id, other)
    event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:attribute-mismatch"),
            battle_state_id=BattleStateId("battle:matcher"),
            damage_dealer=actor,
            target_enemy=EnemyId("enemy:matcher"),
            element=Element.PHYSICAL,
            created_at=1.0,
        ),
        anomaly_triggerer=actor,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    scenario = _scenario()
    context = _context(
        event,
        scenario,
        owner=other,
        history_records=(record,),
    )
    resolution = DynamicIdentityResolver().resolve(
        DynamicIdentity.ANOMALY_TRIGGER,
        context,
    )

    assert resolution.identities is None
    assert resolution.diagnostic is not None
    assert resolution.diagnostic.blocking is True


def test_timeweaver_disorder_bonus_uses_current_ap_and_actual_disorder_triggerer() -> None:
    from core.application.equipment import compile_wengine
    from core.types import WEngineBuildInput, WEngineId

    owner = CharacterId("character:1401")
    operator = CharacterId("character:operator")
    record_id = AnomalyRecordId("anomaly:timeweaver")
    record = _record(record_id, owner)
    compiled = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14122"), owner, refinement=5),
        equipped_character_role=CharacterRole.ANOMALY,
    )
    rule = next(
        item
        for item in compiled.rule_items
        if str(item.rule_id).endswith("over-threshold-disorder-damage")
    )

    def matching_result(current_ap: float, triggerer: CharacterId):
        event = DisorderDamageEvent(
            metadata=DamageEventMetadata(
                event_id=DamageEventId("damage:timeweaver-disorder"),
                battle_state_id=BattleStateId("battle:matcher"),
                damage_dealer=owner,
                target_enemy=EnemyId("enemy:matcher"),
                element=Element.PHYSICAL,
                created_at=2.0,
            ),
            disorder_triggerer=triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(record_id),
            history_record_source=record_id,
            multiplier=FixedMultiplier(Resolved(5.25)),
            crit_rule=NoCritRule(),
        )
        scenario = CalculationScenario(
            scenario_id="scenario:timeweaver-disorder",
            current_operator=operator,
            enabled_rule_item_ids=frozenset({rule.rule_id}),
        )
        context = _context(
            event,
            scenario,
            owner=owner,
            owner_role=CharacterRole.ANOMALY,
            history_records=(record,),
        )
        snapshots = tuple(
            CharacterSnapshot(
                item.character_id,
                item.level,
                replace(
                    item.settlement_stats,
                    anomaly_proficiency=Resolved(
                        current_ap if item.character_id == owner else 100.0
                    ),
                ),
            )
            for item in context.calculation_context.character_snapshots
        )
        context = replace(
            context,
            calculation_context=replace(
                context.calculation_context,
                character_snapshots=snapshots,
            ),
        )
        return EffectMatcher().match_rule_items((rule,), context)[0]

    assert matching_result(374.99, owner).status is EffectMatchStatus.NOT_MATCHED
    assert matching_result(375.0, owner).status is EffectMatchStatus.MATCHED
    assert matching_result(500.0, operator).status is EffectMatchStatus.NOT_MATCHED
