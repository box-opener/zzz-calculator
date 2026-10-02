from __future__ import annotations

from dataclasses import replace

import pytest

from core.application import (
    CalculationScenario,
    RuleEligibility,
    RuleItemId,
    ScenarioRuleStack,
)
from core.application.equipment import compile_drive_discs, stable_set_id
from core.application.execution import (
    MatchedEffectApplication,
    apply_global_panel_effects,
    apply_matched_modifiers,
)
from core.types import (
    CalculationNode,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    DamageTag,
    DriveDiscBuildInput,
    DriveDiscSlot,
    DriveDiscStatKey,
    DriveDiscSubstatRoll,
    EffectTarget,
    Element,
    EquipmentOwnerCapabilities,
    EquippedDriveDisc,
    InitialCharacterSnapshot,
    PanelStatThresholdCondition,
    Resolved,
    RuleStackCondition,
    SkillGroup,
)


def _stats(
    *, attack=1000.0, defense=500.0, mastery=100.0, crit_rate=0.05, crit_damage=0.50
):
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(defense),
        impact=Resolved(100.0),
        crit_rate=Resolved(crit_rate),
        crit_damage=Resolved(crit_damage),
        anomaly_mastery=Resolved(mastery),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={},
    )


def _disc(slot: int, set_id: str, main: DriveDiscStatKey):
    attack_substat = (
        DriveDiscStatKey.ATTACK_PERCENT
        if main is DriveDiscStatKey.ATTACK_FLAT
        else DriveDiscStatKey.ATTACK_FLAT
    )
    return EquippedDriveDisc(
        DriveDiscSlot(slot),
        stable_set_id(set_id),
        main,
        (
            DriveDiscSubstatRoll(attack_substat, 2),
            DriveDiscSubstatRoll(DriveDiscStatKey.CRIT_RATE, 2),
            DriveDiscSubstatRoll(DriveDiscStatKey.CRIT_DAMAGE, 2),
            DriveDiscSubstatRoll(DriveDiscStatKey.PENETRATION_FLAT, 2),
        ),
    )


def _resolution(set_id: str, owner: CharacterId, role=CharacterRole.ATTACK):
    return compile_drive_discs(
        DriveDiscBuildInput(
            owner,
            (
                _disc(1, set_id, DriveDiscStatKey.HP_FLAT),
                _disc(2, set_id, DriveDiscStatKey.ATTACK_FLAT),
                _disc(3, set_id, DriveDiscStatKey.DEFENSE_FLAT),
                _disc(4, set_id, DriveDiscStatKey.ATTACK_PERCENT),
            ),
        ),
        owner_capabilities=EquipmentOwnerCapabilities(
            owner,
            role,
            possible_elements=frozenset(Element),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
        ),
    )


def _scenario(owner, resolution, *, enabled=None, stacks=(), conditions=()):
    return CalculationScenario(
        scenario_id="scenario:drive-rules",
        current_operator=owner,
        conditions=conditions or resolution.scenario_conditions,
        enabled_rule_item_ids=frozenset(
            enabled
            if enabled is not None
            else (item.rule_id for item in resolution.rule_items)
        ),
        rule_stack_counts=tuple(stacks),
    )


def test_initial_mastery_threshold_is_automatic_not_a_user_boolean() -> None:
    owner = CharacterId("character:branch")
    resolution = _resolution("32700", owner)
    rule = next(
        item
        for item in resolution.rule_items
        if item.rule_id.endswith("mastery-crit-damage")
    )
    effect = rule.effects[0]
    assert isinstance(effect.rule.condition, PanelStatThresholdCondition)
    assert (
        effect.rule.condition.source_node
        is CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY
    )
    assert not rule.condition_ids

    def result(initial_mastery: float, current_mastery: float):
        initial_stats = _stats(mastery=initial_mastery)
        current_stats = _stats(mastery=current_mastery)
        return apply_global_panel_effects(
            (CharacterSnapshot(owner, 60, current_stats),),
            (InitialCharacterSnapshot(owner, 60, initial_stats),),
            resolution.rule_items,
            _scenario(owner, resolution, enabled=(rule.rule_id,)),
        )

    assert result(115, 114).character_snapshots[
        0
    ].settlement_stats.crit_damage == Resolved(0.50)
    assert result(100, 115).character_snapshots[
        0
    ].settlement_stats.crit_damage == Resolved(0.80)


def test_non_stacking_threshold_panel_effects_keep_owner_specific_conditions() -> None:
    owners = (CharacterId("character:stun-a"), CharacterId("character:stun-b"))
    resolutions = tuple(_resolution("33200", owner, role=CharacterRole.STUN) for owner in owners)
    team_rules = tuple(
        next(
            rule
            for rule in resolution.rule_items
            if rule.rule_id.endswith("team-crit-damage")
        )
        for resolution in resolutions
    )
    conditions = tuple(
        replace(condition, value=True)
        for resolution, rule in zip(resolutions, team_rules)
        for condition in resolution.scenario_conditions
        if condition.condition_id in rule.condition_ids
    )
    scenario = CalculationScenario(
        scenario_id="scenario:legacy-non-stacking-threshold",
        current_operator=owners[0],
        conditions=conditions,
        enabled_rule_item_ids=frozenset(rule.rule_id for rule in team_rules),
    )
    stats = tuple(_stats(crit_rate=0.05) for _ in owners)
    result = apply_global_panel_effects(
        tuple(CharacterSnapshot(owner, 60, value) for owner, value in zip(owners, stats)),
        tuple(InitialCharacterSnapshot(owner, 60, value) for owner, value in zip(owners, stats)),
        team_rules,
        scenario,
        frozenset(owners),
    )

    assert not any(
        item.diagnostic_id.endswith("conflicting-panel-values")
        for item in result.diagnostics
    )
    assert tuple(item.settlement_stats.crit_damage for item in result.character_snapshots) == (
        Resolved(0.65),
        Resolved(0.65),
    )

def test_thorned_rose_threshold_tiers_add_eight_then_sixteen_percent() -> None:
    owner = CharacterId("character:thorn")
    resolution = _resolution("34200", owner)
    threshold_rules = tuple(
        item for item in resolution.rule_items if "defense-" in item.rule_id
    )

    def crit_rate(defense: float) -> float:
        stats = _stats(defense=defense)
        result = apply_global_panel_effects(
            (CharacterSnapshot(owner, 60, stats),),
            (InitialCharacterSnapshot(owner, 60, stats),),
            threshold_rules,
            _scenario(
                owner,
                resolution,
                enabled=tuple(item.rule_id for item in threshold_rules),
            ),
        )
        return result.character_snapshots[0].settlement_stats.crit_rate.value

    assert crit_rate(999) == pytest.approx(0.05)
    assert crit_rate(1000) == pytest.approx(0.13)
    assert crit_rate(1800) == pytest.approx(0.21)


def test_yunkui_full_stack_effect_reuses_the_same_rule_stack_truth() -> None:
    owner = CharacterId("character:yunkui")
    resolution = _resolution("33100", owner)
    stack_rule = next(
        item for item in resolution.rule_items if item.rule_id.endswith("crit-stacks")
    )
    full_rule = next(
        item
        for item in resolution.rule_items
        if item.rule_id.endswith("full-stack-penetration")
    )
    condition = full_rule.effects[0].rule.condition
    assert isinstance(condition, RuleStackCondition)
    assert condition.rule_item_id == str(stack_rule.rule_id)
    assert condition.required_value == 3
    assert not resolution.scenario_conditions


def test_base_element_scopes_explicitly_include_variant_elements() -> None:
    owner = CharacterId("character:scope")
    resolution = _resolution("34000", owner)
    ether_rule = next(
        item
        for item in resolution.rule_items
        if item.rule_id.endswith("ether-crit-damage")
    )
    ether_effect = ether_rule.effects[0]
    assert ether_effect.rule.target is EffectTarget.SELF
    assert ether_effect.rule.filters == ()
    assert ether_effect.rule.condition is None
    assert ether_effect.rule.trigger is None

    physical = _resolution("33500", owner)
    set_bonus = next(
        item for item in physical.contributions if item.contribution_id.endswith(":2pc")
    )
    assert set_bonus.element is Element.PHYSICAL


def test_astral_voice_stack_is_a_static_team_damage_bonus() -> None:
    owner = CharacterId("character:astral")
    teammate = CharacterId("character:ally")
    resolution = _resolution("32800", owner)
    rule = next(
        item for item in resolution.rule_items if item.rule_id.endswith("team-damage")
    )
    effect = rule.effects[0]
    assert effect.rule.target is EffectTarget.TEAM
    assert effect.rule.filters == ()
    assert effect.rule.trigger is None
    assert effect.rule.condition is None
    assert not resolution.scenario_conditions

    def team_damage(stack: int):
        result = apply_matched_modifiers(
            (
                CharacterSnapshot(owner, 60, _stats()),
                CharacterSnapshot(teammate, 60, _stats()),
            ),
            (),
            (
                MatchedEffectApplication(
                    effect=effect,
                    rule_item_id=rule.rule_id,
                    stack_count=stack,
                ),
            ),
            owner,
        )
        return result

    assert team_damage(0).event_modifiers[0].value == Resolved(0.0)
    assert team_damage(1).event_modifiers[0].value == Resolved(0.08)
    assert team_damage(3).event_modifiers[0].value == Resolved(0.24)


def test_sky_ablaze_ether_eligibility_grants_a_global_self_crit_damage_panel_buff() -> (
    None
):
    owner = CharacterId("character:sky")
    resolution = _resolution("34000", owner)
    rule = next(
        item
        for item in resolution.rule_items
        if item.rule_id.endswith("ether-crit-damage")
    )
    stats = _stats(crit_damage=0.50)
    result = apply_global_panel_effects(
        (CharacterSnapshot(owner, 60, stats),),
        (InitialCharacterSnapshot(owner, 60, stats),),
        (rule,),
        _scenario(owner, resolution, enabled=(rule.rule_id,)),
    )
    assert not result.diagnostics
    assert result.character_snapshots[0].settlement_stats.crit_damage == Resolved(0.80)
    assert len(result.panel_traces) == 1
    assert result.panel_traces[0].resolved_value == pytest.approx(0.30)

    physical_only = compile_drive_discs(
        DriveDiscBuildInput(
            owner,
            (
                _disc(1, "34000", DriveDiscStatKey.HP_FLAT),
                _disc(2, "34000", DriveDiscStatKey.ATTACK_FLAT),
                _disc(3, "34000", DriveDiscStatKey.DEFENSE_FLAT),
                _disc(4, "34000", DriveDiscStatKey.ATTACK_PERCENT),
            ),
        ),
        owner_capabilities=EquipmentOwnerCapabilities(
            owner,
            CharacterRole.ATTACK,
            possible_elements=frozenset({Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
        ),
    )
    physical_rule = next(
        item
        for item in physical_only.rule_items
        if item.rule_id.endswith("ether-crit-damage")
    )
    assert physical_rule.eligibility is RuleEligibility.INELIGIBLE


def test_same_set_on_two_owners_has_unique_instances_and_shared_non_stack_group() -> (
    None
):
    first = _resolution("31600", CharacterId("character:first"), CharacterRole.SUPPORT)
    second = _resolution(
        "31600", CharacterId("character:second"), CharacterRole.SUPPORT
    )
    first_rule = first.rule_items[0]
    second_rule = second.rule_items[0]
    assert first_rule.rule_id != second_rule.rule_id
    assert first_rule.effects[0].rule.effect_id != second_rule.effects[0].rule.effect_id
    assert first_rule.non_stacking_group_id == second_rule.non_stacking_group_id
    assert first_rule.non_stacking_group_id is not None


def test_team_panel_threshold_reads_current_crit_and_targets_the_team() -> None:
    owner = CharacterId("character:stun")
    teammate = CharacterId("character:ally")
    resolution = _resolution("33200", owner, CharacterRole.STUN)
    rule = resolution.rule_items[0]
    assert all(effect.rule.target is EffectTarget.TEAM for effect in rule.effects)
    conditions = tuple(
        replace(item, value=True) for item in resolution.scenario_conditions
    )
    owner_stats = _stats(crit_rate=0.50)
    ally_stats = _stats(crit_rate=0.10)
    result = apply_global_panel_effects(
        (
            CharacterSnapshot(owner, 60, owner_stats),
            CharacterSnapshot(teammate, 60, ally_stats),
        ),
        (
            InitialCharacterSnapshot(owner, 60, owner_stats),
            InitialCharacterSnapshot(teammate, 60, ally_stats),
        ),
        (rule,),
        _scenario(owner, resolution, enabled=(rule.rule_id,), conditions=conditions),
        team_character_ids=frozenset({owner, teammate}),
    )
    assert [
        item.settlement_stats.crit_damage.value for item in result.character_snapshots
    ] == pytest.approx([0.80, 0.80])
