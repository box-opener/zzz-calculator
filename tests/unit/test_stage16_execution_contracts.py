from __future__ import annotations

import json
from pathlib import Path

from core.application import (
    CalculationRuleItem,
    CalculationScenario,
    CharacterMatchProfile,
    EnemyMatchProfile,
    MoveCalculationRequest,
    RuleEligibility,
    RuleItemId,
    ScenarioRuleStack,
    ScenarioTriggerFact,
)
from core.application.characters.definition import CharacterCalculationDefinition
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record,
)
from core.application.execution import (
    MatchedEffectApplication,
    apply_matched_modifiers,
    instantiate_direct_damage_event,
)
from core.application.matching import EffectMatchContext, EffectMatcher, EffectMatchStatus
from core.calculation import CalculationNode
from core.types import (
    BattleEventKind,
    BattleStateId,
    CalculationContext,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    DamageTag,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EnemyId,
    EnemySnapshot,
    DynamicIdentity,
    DynamicIdentityFilter,
    ModifierEffect,
    ModifierResult,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
)


def _source(label: str = "stage 16 test") -> RuleSource:
    return RuleSource(
        source_id=RuleSourceId(f"source:{label.replace(' ', '-')}"),
        source_type=EffectSourceType.SKILL,
        label=label,
    )


def _stats(attack: float = 1000.0) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.5),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )


def _ye_definition():
    fixture = (
        Path(__file__).parents[1] / "fixtures" / "characters" / "ye_shunguang.json"
    )
    raw = load_raw_record(json.loads(fixture.read_text(encoding="utf-8")))
    return compile_ye_shunguang(
        YeShunguangCompileConfig(
            cinema_level=0,
            core_level=1,
            mingxin_active=True,
            entry_move_uses_linren=True,
            enemy_stun_vulnerability_bonus=1.5,
        ),
        raw,
    )


def _support_definition(*, stacked: bool = False) -> CharacterCalculationDefinition:
    owner = CharacterId("character:stage16-support")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16-support:resistance"),
            source=_source("support resistance"),
            owner=owner,
            target=EffectTarget.ENEMY,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.ENEMY_RESISTANCE_REDUCTION,
            operation=EffectOperation.ADD,
            value=Resolved(0.06),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=RuleItemId("rule:stage16-support:resistance"),
        owner=owner,
        source=_source("support resistance rule"),
        display_name="Support resistance",
        original_text="Support resistance",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
        stack_count=3 if stacked else None,
        stack_min=0 if stacked else None,
        stack_max=3 if stacked else None,
    )
    return CharacterCalculationDefinition(
        character_id=owner,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=_source("stage16 supporting definition"),
        move_entries=(),
        rule_items=(rule,),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(),
    )


def test_stage16_vocabulary_has_support_and_mechanism_tags() -> None:
    assert BattleEventKind.SUPPORT_ENTRY.value == "support-entry"
    assert DamageTag.TREMOLO.value == "tremolo-damage"
    assert DamageTag.CLUSTER.value == "cluster-damage"


def test_scenario_rule_stack_is_immutable_and_selected_by_rule_id() -> None:
    scenario = CalculationScenario(
        scenario_id="scenario:stage16-stack",
        current_operator=CharacterId("character:operator"),
        rule_stack_counts=(
            ScenarioRuleStack(
                rule_item_id=RuleItemId("rule:stacked"),
                value=3,
            ),
        ),
    )

    assert scenario.selected_stack(RuleItemId("rule:stacked")) == 3
    assert scenario.selected_stack(RuleItemId("rule:other")) is None


def test_stacked_add_modifier_keeps_rule_item_provenance_and_scales_value() -> None:
    owner = CharacterId("character:operator")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16:stacked"),
            source=_source("stacked effect"),
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.02),
        ),
    )
    application = apply_matched_modifiers(
        (CharacterSnapshot(owner, 60, _stats()),),
        (),
        (
            MatchedEffectApplication(
                effect=effect,
                rule_item_id=RuleItemId("rule:stage16:stacked"),
                stack_count=3,
            ),
        ),
        owner,
    )

    assert not application.diagnostics
    assert application.event_modifiers[0].value == Resolved(0.06)


def test_request_applies_rules_from_supporting_definition() -> None:
    definition = _ye_definition()
    support = _support_definition()
    target = EnemyId("enemy:stage16-support")
    battle = BattleStateId("battle:stage16-support")
    move = next(
        item for item in definition.move_entries if str(item.entry_id).endswith("basic-fast-1")
    )
    conditions = tuple(definition.scenario_conditions)
    scenario = CalculationScenario(
        scenario_id="scenario:stage16-support",
        current_operator=definition.character_id,
        conditions=conditions,
        parameters=tuple(definition.scenario_parameters),
        enabled_rule_item_ids=frozenset(
            {RuleItemId("rule:stage16-support:resistance")}
        ),
    )
    request = MoveCalculationRequest(
        definition=definition,
        supporting_definitions=(support,),
        move_entry_id=move.entry_id,
        scenario=scenario,
        battle_state_id=battle,
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(definition.character_id, 60, _stats()),
            CharacterSnapshot(support.character_id, 60, _stats(800.0)),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.2)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(
                definition.character_id,
                CharacterRole.ATTACK,
            ),
            CharacterMatchProfile(
                support.character_id,
                CharacterRole.SUPPORT,
            ),
        ),
        target_profile=EnemyMatchProfile(target),
    )

    from core.application.execution import calculate_move

    execution = calculate_move(request)
    trace = execution.event_traces[0]
    support_match = next(
        item
        for item in trace.rule_matches
        if item.rule_id == RuleItemId("rule:stage16-support:resistance")
    )
    assert support_match.matched_effects
    assert any(
        item.modifier_path is CalculationNode.ENEMY_RESISTANCE_REDUCTION
        for item in trace.applied_modifiers
    )


def test_request_resolves_selected_rule_stack_before_modifier_creation() -> None:
    definition = _ye_definition()
    support = _support_definition(stacked=True)
    target = EnemyId("enemy:stage16-stack-request")
    move = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith("basic-fast-1")
    )
    rule_id = RuleItemId("rule:stage16-support:resistance")
    scenario = CalculationScenario(
        scenario_id="scenario:stage16-stack-request",
        current_operator=definition.character_id,
        conditions=tuple(definition.scenario_conditions),
        parameters=tuple(definition.scenario_parameters),
        enabled_rule_item_ids=frozenset({rule_id}),
        rule_stack_counts=(ScenarioRuleStack(rule_id, 2),),
    )
    request = MoveCalculationRequest(
        definition=definition,
        supporting_definitions=(support,),
        move_entry_id=move.entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:stage16-stack-request"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(definition.character_id, 60, _stats()),
            CharacterSnapshot(support.character_id, 60, _stats(800.0)),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.2)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(definition.character_id, CharacterRole.ATTACK),
            CharacterMatchProfile(support.character_id, CharacterRole.SUPPORT),
        ),
        target_profile=EnemyMatchProfile(target),
    )

    from core.application.execution import calculate_move

    execution = calculate_move(request)
    resistance_modifier = next(
        item
        for item in execution.event_traces[0].applied_modifiers
        if item.modifier_path is CalculationNode.ENEMY_RESISTANCE_REDUCTION
    )
    assert resistance_modifier.value == Resolved(0.12)


def test_derived_event_repeat_count_stays_outside_domain_event() -> None:
    definition = _ye_definition()
    entry = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith("special-mingxin-guichen")
    )
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == entry.derived_damage_events[0].template
    )
    instantiated = instantiate_direct_damage_event(
        template,
        entry.derived_damage_events[0].multiplier,
        battle_state_id=BattleStateId("battle:stage16-repeat"),
        target_enemy=EnemyId("enemy:stage16-repeat"),
        created_at=0.0,
        repeat_count=3,
    )

    assert instantiated.repeat_count == 3
    assert not hasattr(instantiated.event.metadata, "repeat_count")


def test_support_entry_identity_is_resolved_from_effect_trigger_fact() -> None:
    definition = _ye_definition()
    entry = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith("basic-fast-1")
    )
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == entry.main_damage_event
    )
    event = instantiate_direct_damage_event(
        template,
        entry.multiplier_variants[0].multiplier,
        battle_state_id=BattleStateId("battle:stage16-identity"),
        target_enemy=EnemyId("enemy:stage16-identity"),
        created_at=0.0,
    ).event
    support = CharacterId("character:stage16-entry")
    effect_id = EffectId("effect:stage16:entry-recipient")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=_source("support-entry effect"),
            owner=support,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DynamicIdentityFilter(DynamicIdentity.SUPPORT_ENTRY_CHARACTER),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.2),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=RuleItemId("rule:stage16:entry-recipient"),
        owner=support,
        source=_source("support-entry rule"),
        display_name="Support entry recipient",
        original_text="Support entry recipient",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
    )
    target = EnemyId("enemy:stage16-identity")
    scenario = CalculationScenario(
        scenario_id="scenario:stage16-identity",
        current_operator=support,
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=effect_id,
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=support,
            ),
        ),
        enabled_rule_item_ids=frozenset({rule.rule_id}),
    )
    context = EffectMatchContext(
        current_event=event,
        calculation_context=CalculationContext(
            event=event,
            battle_state_id=event.metadata.battle_state_id,
            character_snapshots=(
                CharacterSnapshot(definition.character_id, 60, _stats()),
                CharacterSnapshot(support, 60, _stats(800.0)),
            ),
            target_snapshot=EnemySnapshot(
                enemy_id=target,
                level=70,
                initial_defense=Resolved(794.0),
                damage_resistance={},
                anomaly_buildup_resistance={},
                daze_resistance=Resolved(0.0),
                damage_reduction=Resolved(0.0),
            ),
        ),
        scenario=scenario,
        team=(
            CharacterMatchProfile(definition.character_id, CharacterRole.ATTACK),
            CharacterMatchProfile(support, CharacterRole.SUPPORT),
        ),
        target=EnemyMatchProfile(target),
    )

    result = EffectMatcher().match_rule_item(rule, context)
    assert result.status is EffectMatchStatus.MATCHED
