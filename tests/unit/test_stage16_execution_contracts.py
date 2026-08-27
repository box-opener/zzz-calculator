from __future__ import annotations

from dataclasses import replace

import pytest

from core.application import (
    CalculationRuleItem,
    CalculationScenario,
    CharacterMatchProfile,
    DamageEventSemanticId,
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
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
from core.data.loader import load_character_record
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
    DamageTagFilter,
    DamageType,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EnemyId,
    EnemySnapshot,
    EventTemplateId,
    DynamicIdentity,
    DynamicIdentityFilter,
    EventCreationEffect,
    EventCreationResult,
    EventSelector,
    FixedMultiplier,
    CurrentAttackValueSource,
    InitialCharacterSnapshot,
    ModifierEffect,
    ModifierResult,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    StandardCritRule,
)
from core.application.characters.templates import DirectDamageEventTemplate


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


def _ye_definition(*, cinema_level: int = 0):
    raw = load_raw_record(load_character_record("character:1431"))
    return compile_ye_shunguang(
        YeShunguangCompileConfig(
            cinema_level=cinema_level,
            core_level=1,
            mingxin_active=True,
            entry_move_uses_linren=True,
            enemy_stun_vulnerability_bonus=1.5,
        ),
        raw,
    )


def _ye_request(definition, suffix: str) -> MoveCalculationRequest:
    target = EnemyId(f"enemy:stage16:{suffix}")
    move = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith(suffix)
    )
    scenario = CalculationScenario(
        scenario_id=f"scenario:stage16:{suffix}",
        current_operator=definition.character_id,
        conditions=tuple(definition.scenario_conditions),
        parameters=tuple(definition.scenario_parameters),
    )
    return MoveCalculationRequest(
        definition=definition,
        move_entry_id=move.entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId(f"battle:stage16:{suffix}"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(definition.character_id, 60, _stats()),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(definition.character_id, CharacterRole.ATTACK),
        ),
        target_profile=EnemyMatchProfile(target),
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


def _event_lane_definition() -> CharacterCalculationDefinition:
    owner = CharacterId("character:stage16-lane-support")
    common_rule = dict(
        source=_source("event lane source"),
        owner=owner,
        target=EffectTarget.TEAM,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        filters=(DamageTagFilter(DamageTag.BASIC_ATTACK),),
    )
    stat_effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16:lane:crit"),
            **common_rule,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            operation=EffectOperation.ADD,
            value=Resolved(0.8),
        ),
    )
    multiplier_effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16:lane:multiplier"),
            **common_rule,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_SKILL_MULTIPLIER,
            operation=EffectOperation.MULTIPLY,
            value=Resolved(2.0),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=RuleItemId("rule:stage16:lane"),
        owner=owner,
        source=_source("event lane rule"),
        display_name="Event lanes",
        original_text="Event lanes",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(stat_effect, multiplier_effect),
    )
    return CharacterCalculationDefinition(
        character_id=owner,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=_source("stage16 event lane definition"),
        move_entries=(),
        rule_items=(rule,),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(),
    )


def _recipient_panel_definition() -> CharacterCalculationDefinition:
    owner = CharacterId("character:stage16-recipient-support")
    effect_id = EffectId("effect:stage16:recipient-panel")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=_source("recipient panel effect"),
            owner=owner,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
            filters=(
                DynamicIdentityFilter(DynamicIdentity.SUPPORT_ENTRY_CHARACTER),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(100.0),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=RuleItemId("rule:stage16:recipient-panel"),
        owner=owner,
        source=_source("recipient panel rule"),
        display_name="Recipient panel",
        original_text="Recipient panel",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
    )
    return CharacterCalculationDefinition(
        character_id=owner,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=_source("stage16 recipient definition"),
        move_entries=(),
        rule_items=(rule,),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(),
    )


def _self_panel_definition() -> CharacterCalculationDefinition:
    owner = CharacterId("character:stage16-self-panel-support")
    rule_id = RuleItemId("rule:stage16:self-panel")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16:self-panel"),
            source=_source("self panel effect"),
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=PanelStatDerivedValue(
                source_character_id=owner,
                source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
                coefficient=Resolved(0.22),
                cap_max=Resolved(1200.0),
            ),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=rule_id,
        owner=owner,
        source=_source("self panel rule"),
        display_name="Self panel",
        original_text="Self panel",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
    )
    return CharacterCalculationDefinition(
        character_id=owner,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=_source("stage16 self panel definition"),
        move_entries=(),
        rule_items=(rule,),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(),
    )


def _independent_event_definition() -> CharacterCalculationDefinition:
    owner = CharacterId("character:stage16-independent-support")
    rule_id = RuleItemId("rule:stage16:independent-event")
    effect_id = EffectId("effect:stage16:independent-event")
    template_id = EventTemplateId("template:stage16:independent-event")
    semantic_id = DamageEventSemanticId("event:stage16:independent-event")
    template_ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label="Independent event",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.ETHER,
        source_rule_item_id=rule_id,
    )
    typed_template = DirectDamageEventTemplate(
        ref=template_ref,
        damage_dealer=owner,
        element=Element.ETHER,
        base_source=CurrentAttackValueSource(owner),
        crit_rule=StandardCritRule(owner),
        move_id=None,
    )
    effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=_source("independent event effect"),
            owner=owner,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(DamageTagFilter(DamageTag.BASIC_ATTACK),),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_id,
        ),
    )
    rule = CalculationRuleItem(
        rule_id=rule_id,
        owner=owner,
        source=_source("independent event rule"),
        display_name="Independent event",
        original_text="Independent event",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
    )
    return CharacterCalculationDefinition(
        character_id=owner,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=_source("stage16 independent event definition"),
        move_entries=(),
        rule_items=(rule,),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(typed_template,),
        independent_derived_damage_events=(
            DerivedDamageEventTemplateRef(
                template=template_ref,
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=3,
            ),
        ),
    )


def test_stage16_vocabulary_has_support_and_mechanism_tags() -> None:
    assert BattleEventKind.SUPPORT_ENTRY.value == "support-entry"
    assert DamageTag.TREMOLO.value == "tremolo-damage"
    assert DamageTag.CLUSTER.value == "cluster-damage"


def test_global_panel_prepass_applies_support_self_effect_to_support_snapshot() -> None:
    definition = _ye_definition()
    support = _self_panel_definition()
    request = _ye_request(definition, "basic-fast-1")
    request = replace(
        request,
        supporting_definitions=(support,),
        scenario=replace(
            request.scenario,
            enabled_rule_item_ids=frozenset(
                {RuleItemId("rule:stage16:self-panel")}
            ),
        ),
        base_character_snapshots=(
            *request.base_character_snapshots,
            CharacterSnapshot(support.character_id, 60, _stats(800.0)),
        ),
        initial_character_snapshots=(
            InitialCharacterSnapshot(support.character_id, 60, _stats(6000.0)),
        ),
        team_profiles=(
            *request.team_profiles,
            CharacterMatchProfile(support.character_id, CharacterRole.SUPPORT),
        ),
    )

    from core.application.execution import calculate_move

    execution = calculate_move(request)
    support_snapshot = next(
        item
        for item in execution.resolved_character_snapshots
        if item.character_id == support.character_id
    )
    assert support_snapshot.settlement_stats.attack == Resolved(2000.0)


def test_definition_level_independent_derived_event_can_be_created_without_move() -> None:
    definition = _ye_definition()
    support = _independent_event_definition()
    request = _ye_request(definition, "basic-fast-1")
    rule_id = RuleItemId("rule:stage16:independent-event")
    request = replace(
        request,
        supporting_definitions=(support,),
        scenario=replace(
            request.scenario,
            enabled_rule_item_ids=frozenset({rule_id}),
        ),
        base_character_snapshots=(
            *request.base_character_snapshots,
            CharacterSnapshot(support.character_id, 60, _stats(800.0)),
        ),
        team_profiles=(
            *request.team_profiles,
            CharacterMatchProfile(support.character_id, CharacterRole.SUPPORT),
        ),
    )

    from core.application.execution import calculate_move

    execution = calculate_move(request)
    assert len(execution.output.events) == 2
    derived = execution.output.events[1]
    assert derived.repeat_count == 3
    assert execution.event_traces[1].created_by_effect_id == EffectId(
        "effect:stage16:independent-event"
    )


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


def test_panel_stat_derived_value_reads_initial_attack_and_applies_cap() -> None:
    owner = CharacterId("character:operator")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16:derived-panel"),
            source=_source("derived panel effect"),
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=PanelStatDerivedValue(
                source_character_id=owner,
                source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
                coefficient=Resolved(0.22),
                cap_max=Resolved(1200.0),
            ),
        ),
    )
    application = apply_matched_modifiers(
        (CharacterSnapshot(owner, 60, _stats(1000.0)),),
        (),
        (MatchedEffectApplication(effect=effect),),
        owner,
        initial_character_snapshots=(
            InitialCharacterSnapshot(owner, 60, _stats(6000.0)),
        ),
    )

    assert not application.diagnostics
    assert application.character_snapshots[0].settlement_stats.attack == Resolved(
        2200.0
    )


def test_panel_stat_derived_value_does_not_fall_back_to_settlement_attack() -> None:
    owner = CharacterId("character:operator")
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:stage16:missing-derived-panel"),
            source=_source("missing derived panel effect"),
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=PanelStatDerivedValue(
                source_character_id=owner,
                source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
                coefficient=Resolved(0.22),
                cap_max=Resolved(1200.0),
            ),
        ),
    )
    application = apply_matched_modifiers(
        (CharacterSnapshot(owner, 60, _stats(1000.0)),),
        (),
        (MatchedEffectApplication(effect=effect),),
        owner,
    )

    assert application.diagnostics
    assert application.diagnostics[0].kind.value == "missing-data"
    assert application.character_snapshots[0].settlement_stats.attack == Resolved(
        1000.0
    )


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


def test_event_stat_and_multiplier_lanes_are_applied_before_calculator() -> None:
    definition = _ye_definition()
    support = _event_lane_definition()
    target = EnemyId("enemy:stage16-lanes")
    move = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith("basic-fast-1")
    )
    rule_id = RuleItemId("rule:stage16:lane")
    scenario = CalculationScenario(
        scenario_id="scenario:stage16-lanes",
        current_operator=definition.character_id,
        conditions=tuple(definition.scenario_conditions),
        parameters=tuple(definition.scenario_parameters),
        enabled_rule_item_ids=frozenset({rule_id}),
    )
    request = MoveCalculationRequest(
        definition=definition,
        supporting_definitions=(support,),
        move_entry_id=move.entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:stage16-lanes"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(definition.character_id, 60, _stats()),
            CharacterSnapshot(support.character_id, 60, _stats(800.0)),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=target,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.0)},
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
    event = execution.output.events[0]
    trace = execution.event_traces[0]
    assert event.status.value == "calculated"
    assert len(trace.event_stat_modifiers) == 1
    assert trace.event_stat_modifiers[0].recipient == definition.character_id
    assert len(trace.event_multiplier_modifiers) == 1
    skill_multiplier = next(
        item.value.value
        for item in event.result.breakdown  # type: ignore[union-attr]
        if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    base_multiplier = move.multiplier_variants[0].multiplier.value.value
    assert skill_multiplier == pytest.approx(base_multiplier * 2.0)
    assert execution.resolved_character_snapshots[0].settlement_stats.crit_rate == Resolved(
        0.5
    )


def test_support_entry_panel_effect_targets_only_the_declared_recipient() -> None:
    definition = _ye_definition()
    support = _recipient_panel_definition()
    rule_id = RuleItemId("rule:stage16:recipient-panel")
    request = _ye_request(definition, "basic-fast-1")
    scenario = replace(
        request.scenario,
        enabled_rule_item_ids=frozenset({rule_id}),
        trigger_facts=(
            ScenarioTriggerFact(
                effect_id=EffectId("effect:stage16:recipient-panel"),
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=definition.character_id,
            ),
        ),
    )
    request = replace(
        request,
        scenario=scenario,
        supporting_definitions=(support,),
        base_character_snapshots=(
            *request.base_character_snapshots,
            CharacterSnapshot(support.character_id, 60, _stats(800.0)),
        ),
        team_profiles=(
            *request.team_profiles,
            CharacterMatchProfile(support.character_id, CharacterRole.SUPPORT),
        ),
    )

    from core.application.execution import calculate_move

    matched = calculate_move(request)
    assert matched.resolved_character_snapshots[0].settlement_stats.attack == Resolved(
        1100.0
    )

    third = CharacterId("character:stage16-third")
    third_request = replace(
        request,
        scenario=replace(request.scenario, current_operator=third),
        base_character_snapshots=(
            *request.base_character_snapshots,
            CharacterSnapshot(third, 60, _stats(700.0)),
        ),
        team_profiles=(
            *request.team_profiles,
            CharacterMatchProfile(third, CharacterRole.ATTACK),
        ),
    )
    not_recipient = calculate_move(third_request)
    third_snapshot = next(
        item
        for item in not_recipient.resolved_character_snapshots
        if item.character_id == third
    )
    assert third_snapshot.settlement_stats.attack == Resolved(700.0)


def test_non_unit_stacked_event_creation_is_blocked() -> None:
    definition = _ye_definition(cinema_level=6)
    c6_id = RuleItemId("rule:ye:1431:cinema6")
    c6 = next(item for item in definition.rule_items if item.rule_id == c6_id)
    assert any(isinstance(effect, EventCreationEffect) for effect in c6.effects)
    stacked_c6 = replace(c6, stack_count=2, stack_min=0, stack_max=2)
    stacked_definition = replace(
        definition,
        rule_items=tuple(
            stacked_c6 if item.rule_id == c6_id else item
            for item in definition.rule_items
        ),
    )
    request = _ye_request(stacked_definition, "special-mingxin-guichen")
    request = replace(
        request,
        scenario=replace(
            request.scenario,
            enabled_rule_item_ids=frozenset({c6_id}),
            rule_stack_counts=(ScenarioRuleStack(c6_id, 2),),
        ),
    )

    from core.application.execution import calculate_move

    execution = calculate_move(request)
    assert len(execution.output.events) == 1
    assert execution.output.complete is False
    assert any(
        "stacked EventCreation effects are unsupported" in item.message
        for item in execution.output.diagnostics
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
