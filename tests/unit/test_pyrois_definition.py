from __future__ import annotations

import json
from pathlib import Path
from dataclasses import replace

import pytest

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.pyrois import (
    PYROIS_ID,
    PYROIS_REVIEWED_MAPPING,
    PyroisCompileConfig,
    compile_pyrois,
    load_raw_record,
)
from core.application.characters.pyrois.compiler import (
    PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE,
    PYROIS_LEFT_CORE_EXTRA_ACTIVE,
    PYROIS_RIGHT_CORE_EXTRA_ACTIVE,
    PYROIS_SUNFLAME_ACTIVE,
    PYROIS_SUNFLARE_ACTIVE,
)
from core.application.execution import DirectMoveApplicationService, MoveCalculationRequest
from core.application.ids import RuleItemId
from core.application.matching import CharacterMatchProfile, EnemyMatchProfile
from core.application.output import CritDisplayMode
from core.application.rules import RuleEligibility
from core.presentation.registry import config_fields_for
from core.application.scenario import CalculationScenario, ConditionResolution
from core.types import (
    BattleStateId,
    BattleEventKind,
    CalculationNode,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    EffectTarget,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    EnemyId,
    EnemySnapshot,
    Element,
    EnemyStateFilter,
    EventCreationEffect,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    Resolved,
    SkillGroup,
    OperationState,
    StateId,
    Unresolved,
)


_ROOT = Path(__file__).resolve().parents[2]
_RAW_PATH = _ROOT / "core" / "data" / "characters" / "pyrois.json"
_SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1551.json"


def _source_data() -> dict[str, object]:
    return json.loads(_RAW_PATH.read_text(encoding="utf-8"))


def _definition(**kwargs):
    raw = load_raw_record(_source_data())
    return raw, compile_pyrois(PyroisCompileConfig(**kwargs), raw)


def _rule(definition, suffix: str):
    return next(
        item
        for item in definition.rule_items
        if str(item.rule_id).endswith(f":{suffix}")
    )


def _template_filters(effect) -> set[str]:
    return {
        str(item.template_id)
        for item in effect.rule.filters
        if isinstance(item, EventTemplateIdFilter)
    }


def _execute(
    definition,
    entry_suffix: str,
    *,
    enabled_rule_suffixes: tuple[str, ...] = (),
    active_conditions=(),
    enemy_stunned: bool = False,
    crit_display_mode: CritDisplayMode = CritDisplayMode.FULL_CRIT,
):
    entry = next(
        item
        for item in definition.move_entries
        if str(item.entry_id).endswith(f":{entry_suffix}")
    )
    conditions = tuple(
        replace(item, value=item.condition_id in set(active_conditions))
        for item in definition.scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id=f"scenario:pyrois:{entry_suffix}",
        current_operator=PYROIS_ID,
        conditions=conditions,
        enabled_rule_item_ids=frozenset(
            RuleItemId(f"rule:character:1551:{suffix}")
            for suffix in enabled_rule_suffixes
        ),
    )
    enemy_id = EnemyId(f"enemy:pyrois:{entry_suffix}")
    stats = CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(2000.0),
        defense=Resolved(800.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.2),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
    )
    request = MoveCalculationRequest(
        definition=definition,
        move_entry_id=entry.entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId(f"battle:pyrois:{entry_suffix}"),
        battle_time=0.0,
        base_character_snapshots=(CharacterSnapshot(PYROIS_ID, 60, stats),),
        target_snapshot=EnemySnapshot(
            enemy_id=enemy_id,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.ETHER: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
            is_stunned=enemy_stunned,
        ),
        team_profiles=(
            CharacterMatchProfile(
                PYROIS_ID,
                CharacterRole.ATTACK,
                operation_state=OperationState.OPERATED,
            ),
        ),
        target_profile=EnemyMatchProfile(
            enemy_id,
            states=(frozenset({StateId("state:enemy:stunned")}) if enemy_stunned else frozenset()),
        ),
        crit_display_mode=crit_display_mode,
    )
    return DirectMoveApplicationService().calculate(request)


def test_identity_provenance_raw_sentinel_and_reviewed_damage_entry_count() -> None:
    data = _source_data()
    raw, definition = _definition()

    assert data["source_version"] == raw.source_version == "3.2"
    assert data["source_url"] == raw.source_url == _SOURCE_URL
    assert raw.character_id == PYROIS_ID
    assert (raw.name, raw.code_name, raw.rarity) == ("佩洛伊斯", "Pyrois", 4)
    assert (raw.specialty, raw.element, raw.faction, raw.icon) == (
        "强攻",
        "以太",
        "法厄同",
        "IconRole63",
    )
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert len(PYROIS_REVIEWED_MAPPING.moves) == 18
    assert len(definition.move_entries) == 18
    assert len(definition.damage_event_templates) == 21
    assert all(item.ref.damage_type is DamageType.DIRECT for item in definition.damage_event_templates)
    assert all(item.ref.element is Element.ETHER for item in definition.damage_event_templates)
    assert not any(
        item.ref.damage_type in {DamageType.ANOMALY, DamageType.DISORDER}
        for item in definition.damage_event_templates
    )

    # Preserve the received source in full; the compiler parser only skips its
    # empty special-prose sentinel and never promotes it to a move entry.
    assert any(
        item.get("name") == "" and not item.get("param")
        for item in data["skill"]["special"]["description"]
    )
    assert all(item.name for item in raw.moves)
    assert not any("招架支援" in item.display_name for item in definition.move_entries)
    assert raw.mindscapes[5].description == "影画效果未揭示"
    assert not any("cinema6" in str(item.rule_id) for item in definition.rule_items)


def test_each_reviewed_direct_move_reads_its_own_raw_curve_at_effective_skill_level() -> None:
    raw, definition = _definition()
    raw_moves = {item.name: item for item in raw.moves}
    entries = {str(item.entry_id): item for item in definition.move_entries}
    config = PyroisCompileConfig()

    for spec in PYROIS_REVIEWED_MAPPING.moves:
        entry = entries[f"move-entry:character:1551:{spec.entry_key}"]
        parameter_spec = spec.parameters[0]
        source_move = raw_moves[spec.source_name]
        parameter = next(
            item for item in source_move.parameters if item.name == parameter_spec.parameter_name
        )
        level = effective_skill_level(
            config,
            spec.parameter_skill_group or spec.skill_group,
        )
        raw_value = parameter.value_for_level(level, parameter_spec.source_skill_id)
        assert raw_value is not None, spec.entry_key
        multiplier = entry.multiplier_variants[0].multiplier
        assert isinstance(multiplier, FixedMultiplier), spec.entry_key
        assert isinstance(multiplier.value, Resolved), spec.entry_key
        assert multiplier.value.value == pytest.approx(float(raw_value) / 100.0), spec.entry_key
        assert entry.main_damage_event.damage_type is DamageType.DIRECT
        assert entry.main_damage_event.element is Element.ETHER
        assert entry.stage_index == spec.stage_index

    basics = [
        item
        for item in definition.move_entries
        if item.stage_index is not None
    ]
    assert len(basics) == 7
    assert sorted(item.stage_index for item in basics) == [1, 1, 2, 2, 3, 3, 4]


@pytest.mark.parametrize(
    ("core_level", "sunflare_percent", "left_percent", "right_percent"),
    [
        (1, 20.0, 450.0, 1125.0),
        (2, 23.4, 525.0, 1312.0),
        (3, 26.8, 600.0, 1499.0),
        (4, 30.2, 675.0, 1686.0),
        (5, 33.6, 750.0, 1873.0),
        (6, 37.0, 825.0, 2060.0),
        (7, 40.0, 900.0, 2250.0),
    ],
)
def test_core_level_effects_retain_source_ratio_and_current_state_scopes(
    core_level: int,
    sunflare_percent: float,
    left_percent: float,
    right_percent: float,
) -> None:
    raw, definition = _definition(core_level=core_level)
    sunflare = _rule(definition, "core:sunflare-normal-damage-bonus")
    sunflare_effect = sunflare.effects[0]
    assert isinstance(sunflare_effect, ModifierEffect)
    assert sunflare.condition_ids == (PYROIS_SUNFLARE_ACTIVE,)
    assert sunflare_effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert sunflare_effect.result.value == Resolved(sunflare_percent / 100.0)
    assert sunflare_effect.rule.target is EffectTarget.SELF

    for suffix, proc_condition, ratio in (
        ("core:left-core-extra-damage", PYROIS_LEFT_CORE_EXTRA_ACTIVE, left_percent),
        ("core:right-core-extra-damage", PYROIS_RIGHT_CORE_EXTRA_ACTIVE, right_percent),
    ):
        rule = _rule(definition, suffix)
        assert rule.condition_ids == (proc_condition,)
        effect = rule.effects[0]
        assert isinstance(effect, EventCreationEffect)
        assert effect.result.event_kind is BattleEventKind.DAMAGE
        assert effect.result.event_template_id is not None
        assert effect.result.unresolved_template is None
        child = next(
            item for item in definition.damage_event_templates
            if item.ref.template_id == effect.result.event_template_id
        )
        assert child.element is Element.ETHER
        assert child.ref.skill_group is SkillGroup.ULTIMATE
        assert child.ref.damage_tags == frozenset({DamageTag.ULTIMATE})
        derived = next(
            item for item in definition.independent_derived_damage_events
            if item.template.template_id == child.ref.template_id
        )
        assert derived.multiplier.value.value == pytest.approx(ratio / 100.0)
        assert effect.result.unique_per_source_event is True
        assert any(isinstance(item, DamageTypeFilter) and item.damage_type is DamageType.DIRECT for item in effect.rule.filters)

    right_effect = _rule(definition, "core:right-core-extra-damage").effects[0]
    assert any(isinstance(item, EnemyStateFilter) for item in right_effect.rule.filters)


def test_sunflame_crit_bonus_is_ultimate_only_and_requires_current_stun() -> None:
    _, definition = _definition(core_level=7)
    rule = _rule(definition, "core:sunflame-ultimate-crit-damage")
    effect = rule.effects[0]
    assert isinstance(effect, ModifierEffect)
    assert rule.condition_ids == (PYROIS_SUNFLAME_ACTIVE,)
    assert effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
    assert effect.result.value == Resolved(0.40)
    assert any(
        isinstance(item, DamageTagFilter) and item.damage_tag is DamageTag.ULTIMATE
        for item in effect.rule.filters
    )
    assert any(isinstance(item, EnemyStateFilter) for item in effect.rule.filters)
    assert any(
        condition.condition_id == PYROIS_SUNFLAME_ACTIVE
        and condition.resolution is ConditionResolution.USER_SELECTED
        and condition.value is False
        for condition in definition.scenario_conditions
    )


def test_additional_ability_and_cinema_one_eligibility_are_explicit() -> None:
    _, locked = _definition(additional_ability_eligible=False, cinema_level=0)
    raw, eligible = _definition(additional_ability_eligible=True, cinema_level=1)

    locked_extra = _rule(locked, "extra-ability:team-stun-or-support-crit-damage")
    active_extra = _rule(eligible, "extra-ability:team-stun-or-support-crit-damage")
    assert locked_extra.eligibility is RuleEligibility.INELIGIBLE
    assert active_extra.eligibility is RuleEligibility.ELIGIBLE
    assert active_extra.original_text == raw.extra_ability_description
    extra_effect = active_extra.effects[0]
    assert isinstance(extra_effect, ModifierEffect)
    assert extra_effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
    assert extra_effect.result.value == Resolved(0.40)
    assert extra_effect.rule.target is EffectTarget.SELF

    c1_locked = _rule(locked, "cinema1:crit-rate")
    c1_active = _rule(eligible, "cinema1:crit-rate")
    assert c1_locked.eligibility is RuleEligibility.INELIGIBLE
    assert c1_active.eligibility is RuleEligibility.ELIGIBLE
    c1_effect = c1_active.effects[0]
    assert isinstance(c1_effect, ModifierEffect)
    assert c1_effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
    assert c1_effect.result.value == Resolved(0.08)


def test_sunflare_cinema1_and_extra_ability_modify_only_the_selected_real_calculation() -> None:
    _, base = _definition(core_level=1, cinema_level=0)
    _, c1 = _definition(core_level=1, cinema_level=1)
    _, extra = _definition(core_level=1, additional_ability_eligible=True)

    normal_base = _execute(base, "basic-afterglow-stage-1", crit_display_mode=CritDisplayMode.NON_CRIT)
    normal_buffed = _execute(
        base,
        "basic-afterglow-stage-1",
        enabled_rule_suffixes=("core:sunflare-normal-damage-bonus",),
        active_conditions=(PYROIS_SUNFLARE_ACTIVE,),
        crit_display_mode=CritDisplayMode.NON_CRIT,
    )
    assert normal_base.output.complete and normal_buffed.output.complete
    assert normal_base.output.known_total and normal_buffed.output.known_total
    assert normal_buffed.output.known_total / normal_base.output.known_total == pytest.approx(1.2)

    expected_base = _execute(base, "basic-afterglow-stage-1", crit_display_mode=CritDisplayMode.EXPECTED)
    expected_c1 = _execute(
        c1,
        "basic-afterglow-stage-1",
        enabled_rule_suffixes=("cinema1:crit-rate",),
        crit_display_mode=CritDisplayMode.EXPECTED,
    )
    assert expected_base.output.complete and expected_c1.output.complete
    assert expected_base.output.known_total and expected_c1.output.known_total
    assert expected_c1.output.known_total / expected_base.output.known_total == pytest.approx(
        (1.0 + 0.28 * 0.5) / (1.0 + 0.2 * 0.5)
    )

    expected_extra = _execute(
        extra,
        "basic-afterglow-stage-1",
        enabled_rule_suffixes=("extra-ability:team-stun-or-support-crit-damage",),
        crit_display_mode=CritDisplayMode.EXPECTED,
    )
    assert expected_base.output.known_total and expected_extra.output.known_total
    assert expected_extra.output.known_total / expected_base.output.known_total == pytest.approx(
        (1.0 + 0.2 * 0.9) / (1.0 + 0.2 * 0.5)
    )


def test_sunflame_ultimate_bonus_requires_its_state_stun_and_ultimate_identity() -> None:
    _, definition = _definition()
    base = _execute(
        definition,
        "ultimate-military-execution",
        enemy_stunned=True,
        crit_display_mode=CritDisplayMode.EXPECTED,
    )
    buffed = _execute(
        definition,
        "ultimate-military-execution",
        enabled_rule_suffixes=("core:sunflame-ultimate-crit-damage",),
        active_conditions=(PYROIS_SUNFLAME_ACTIVE,),
        enemy_stunned=True,
        crit_display_mode=CritDisplayMode.EXPECTED,
    )
    assert base.output.complete and buffed.output.complete
    assert base.output.known_total and buffed.output.known_total
    assert buffed.output.known_total / base.output.known_total == pytest.approx(
        (1.0 + 0.2 * 0.9) / (1.0 + 0.2 * 0.5)
    )

    not_stunned = _execute(
        definition,
        "ultimate-military-execution",
        enabled_rule_suffixes=("core:sunflame-ultimate-crit-damage",),
        active_conditions=(PYROIS_SUNFLAME_ACTIVE,),
        enemy_stunned=False,
        crit_display_mode=CritDisplayMode.EXPECTED,
    )
    assert base.output.known_total and not_stunned.output.known_total
    assert not_stunned.output.known_total == pytest.approx(base.output.known_total)


def test_core_and_battle_order_children_are_typed_and_only_created_on_their_exact_trigger() -> None:
    _, definition = _definition(core_level=7)
    left_parent = _execute(definition, "ultimate-unbound-sword")
    left_child = _execute(
        definition,
        "ultimate-unbound-sword",
        enabled_rule_suffixes=("core:left-core-extra-damage",),
        active_conditions=(PYROIS_LEFT_CORE_EXTRA_ACTIVE,),
    )
    unrelated = _execute(
        definition,
        "basic-afterglow-stage-1",
        enabled_rule_suffixes=("core:left-core-extra-damage",),
        active_conditions=(PYROIS_LEFT_CORE_EXTRA_ACTIVE,),
    )
    assert left_parent.output.complete and left_parent.output.known_total
    assert left_child.output.complete
    assert left_child.output.known_total > left_parent.output.known_total
    assert unrelated.output.complete

    upper_ult = _execute(
        definition,
        "ultimate-military-execution",
        enabled_rule_suffixes=("skill:special-battle-order-ultimate-trigger",),
    )
    assert upper_ult.output.complete
    assert upper_ult.output.known_total is not None and upper_ult.output.known_total > 0

    ex_without_proc = _execute(
        definition,
        "ex-sunflower",
        enabled_rule_suffixes=("skill:special-battle-order-ex-trigger",),
    )
    ex_with_proc = _execute(
        definition,
        "ex-sunflower",
        enabled_rule_suffixes=("skill:special-battle-order-ex-trigger",),
        active_conditions=(PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE,),
    )
    assert ex_without_proc.output.complete
    assert ex_with_proc.output.complete
    assert ex_with_proc.output.known_total > ex_without_proc.output.known_total


def test_c3_c5_include_ultimate_and_cap_at_skill_level_sixteen() -> None:
    raw, c0 = _definition(cinema_level=0)
    _, c3 = _definition(cinema_level=3)
    _, c5 = _definition(cinema_level=5)
    spec = next(
        item
        for item in PYROIS_REVIEWED_MAPPING.moves
        if item.entry_key == "ultimate-victory-road"
    )
    source_move = next(item for item in raw.moves if item.name == spec.source_name)
    source_parameter = next(
        item for item in source_move.parameters if item.name == spec.parameters[0].parameter_name
    )
    c0_level = effective_skill_level(PyroisCompileConfig(), spec.skill_group)
    c3_level = effective_skill_level(PyroisCompileConfig(cinema_level=3), spec.skill_group)
    c5_level = effective_skill_level(PyroisCompileConfig(cinema_level=5), spec.skill_group)
    assert (c0_level, c3_level, c5_level) == (12, 14, 16)

    def multiplier(definition) -> float:
        entry = next(
            item
            for item in definition.move_entries
            if str(item.entry_id).endswith(":ultimate-victory-road")
        )
        fixed = entry.multiplier_variants[0].multiplier
        assert isinstance(fixed, FixedMultiplier)
        assert isinstance(fixed.value, Resolved)
        return fixed.value.value

    assert multiplier(c0) == pytest.approx(source_parameter.value_for_level(c0_level, "1551014") / 100)
    assert multiplier(c3) == pytest.approx(source_parameter.value_for_level(c3_level, "1551014") / 100)
    assert multiplier(c5) == pytest.approx(source_parameter.value_for_level(c5_level, "1551014") / 100)
    assert multiplier(c0) < multiplier(c3) < multiplier(c5)


def test_unpublished_cinema_six_is_not_selectable_or_accepted() -> None:
    fields = config_fields_for(PYROIS_ID, {"core_level": 7, "cinema_level": 0}, (PYROIS_ID,))
    cinema = next(item for item in fields if item.field_id == "cinema_level")
    assert cinema.maximum == 5
    with pytest.raises(ValueError, match="between 0 and 5"):
        PyroisCompileConfig(cinema_level=6)


def test_battle_order_keeps_known_curve_and_guaranteed_or_current_proc_triggers_local() -> None:
    raw, definition = _definition(cinema_level=0)
    source = next(item for item in raw.moves if item.name == "特殊技：强袭训令")
    parameter = next(item for item in source.parameters if item.name == "伤害倍率")
    level = effective_skill_level(PyroisCompileConfig(), SkillGroup.SPECIAL_ATTACK)
    ratio = parameter.value_for_level(level, "1551022")
    assert ratio is not None

    ultimate_rule = _rule(definition, "skill:special-battle-order-ultimate-trigger")
    assert ultimate_rule.condition_ids == ()
    assert len(ultimate_rule.effects) == 4
    assert {
        template_id
        for effect in ultimate_rule.effects
        for template_id in _template_filters(effect)
    } == {
        "template:character:1551:ultimate-military-execution:main",
        "template:character:1551:ultimate-victory-road:main",
        "template:character:1551:ultimate-unbound-sword:main",
        "template:character:1551:ultimate-eternal-prison:main",
    }
    ex_rule = _rule(definition, "skill:special-battle-order-ex-trigger")
    assert ex_rule.condition_ids == (PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE,)
    assert len(ex_rule.effects) == 1
    assert _template_filters(ex_rule.effects[0]) == {
        "template:character:1551:ex-sunflower:main"
    }
    condition = next(
        item
        for item in definition.scenario_conditions
        if item.condition_id == PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE
    )
    assert condition.value is False

    for effect in (*ultimate_rule.effects, *ex_rule.effects):
        assert isinstance(effect, EventCreationEffect)
        assert effect.result.event_kind is BattleEventKind.DAMAGE
        assert effect.result.event_template_id == EventTemplateId(
            "template:character:1551:special-battle-order:ether"
        )
        assert effect.result.unique_per_source_event is True
        assert effect.result.unresolved_template is None
    order_template = next(
        item for item in definition.damage_event_templates
        if item.ref.template_id
        == EventTemplateId("template:character:1551:special-battle-order:ether")
    )
    assert order_template.damage_dealer == PYROIS_ID
    assert order_template.element is Element.ETHER
    assert order_template.ref.skill_group is SkillGroup.SPECIAL_ATTACK
    assert order_template.ref.damage_tags == frozenset({DamageTag.SPECIAL_ATTACK})
    with pytest.raises(ValueError, match="between 0 and 5"):
        PyroisCompileConfig(cinema_level=6)
