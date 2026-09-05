from __future__ import annotations

from dataclasses import replace

import pytest

from core.application import CalculationScenario, RuleItemId, ScenarioRuleStack
from core.application.equipment import compile_drive_discs, stable_set_id
from core.application.execution import apply_global_panel_effects
from core.types import (
    AnyFilter,
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
    ElementFilter,
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
    return EquippedDriveDisc(
        DriveDiscSlot(slot),
        stable_set_id(set_id),
        main,
        (
            DriveDiscSubstatRoll(DriveDiscStatKey.ATTACK_FLAT, 2),
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
    assert not rule.condition_ids

    def result(mastery: float):
        stats = _stats(mastery=mastery)
        return apply_global_panel_effects(
            (CharacterSnapshot(owner, 60, stats),),
            (InitialCharacterSnapshot(owner, 60, stats),),
            resolution.rule_items,
            _scenario(owner, resolution, enabled=(rule.rule_id,)),
        )

    assert result(114).character_snapshots[0].settlement_stats.crit_damage == Resolved(
        0.50
    )
    assert result(115).character_snapshots[0].settlement_stats.crit_damage == Resolved(
        0.80
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
    scoped_effect = next(
        effect
        for rule in resolution.rule_items
        for effect in rule.effects
        if effect.rule.filters
    )
    scope = scoped_effect.rule.filters[0]
    assert isinstance(scope, AnyFilter)
    assert {
        item.element for item in scope.filters if isinstance(item, ElementFilter)
    } == {
        Element.ETHER,
        Element.XUANMO,
    }

    physical = _resolution("33500", owner)
    set_bonus = next(
        item for item in physical.contributions if item.contribution_id.endswith(":2pc")
    )
    assert set_bonus.element is Element.PHYSICAL


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
