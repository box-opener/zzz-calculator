from __future__ import annotations

from dataclasses import replace

import pytest

from core.application import (
    CalculationScenario,
    ConditionResolution,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariantId,
    RuleEligibility,
    RuleItemId,
)
from core.application.characters import (
    CharacterCalculationDefinition,
    CharacterSkillLevel,
    YeShunguangCompileConfig,
)
from core.application.characters.ye_shunguang import compile_ye_shunguang
from core.types import (
    DamageTag,
    DamageType,
    EffectOperation,
    Element,
    EventCreationEffect,
    ModifierEffect,
    MoveId,
    MoveIdFilter,
    SkillGroup,
)


def _definition(
    *,
    cinema_level: int = 0,
    mingxin_active: bool = True,
    entry_move_uses_linren: bool = True,
    enemy_stun_vulnerability_bonus: float = 1.5,
    core_level: int = 1,
) -> CharacterCalculationDefinition:
    config = YeShunguangCompileConfig(
        cinema_level=cinema_level,
        mingxin_active=mingxin_active,
        entry_move_uses_linren=entry_move_uses_linren,
        enemy_stun_vulnerability_bonus=enemy_stun_vulnerability_bonus,
        core_level=core_level,
    )
    return compile_ye_shunguang(config)


def _entry(definition: CharacterCalculationDefinition, suffix: str) -> MoveCalculationEntry:
    return next(
        item for item in definition.move_entries if str(item.entry_id).endswith(suffix)
    )


def test_ye_shunguang_compiles_identity_and_usable_move_entries() -> None:
    definition = _definition()

    assert str(definition.character_id) == "character:1431"
    assert definition.role.value == "attack"
    assert definition.base_element is Element.PHYSICAL
    assert len(definition.move_entries) == 28
    assert all(
        item.main_damage_event.damage_type is DamageType.DIRECT
        for item in definition.move_entries
    )
    assert all(
        item.main_damage_event.element is Element.LINREN
        for item in definition.move_entries
        if item.condition_ids
    )
    assert not any(
        item.move_id == MoveId("move:special-mingxin-feiguang")
        for item in definition.move_entries
    )
    assert any(item.kind.value == "data-quality" for item in definition.diagnostics)


def test_sequential_stage_and_unit_repeat_entries_preserve_move_identity() -> None:
    definition = _definition()
    fast = [item for item in definition.move_entries if item.move_id == MoveId("move:basic-fast")]
    assert len(fast) == 4
    assert {item.stage_index for item in fast} == {1, 2, 3, 4}
    assert all(
        item.multiplier_relation is MultiplierRelation.SEQUENTIAL_STAGE
        for item in fast
    )

    cloud = _entry(definition, "basic-cloud")
    assert cloud.multiplier_relation is MultiplierRelation.UNIT_REPEAT
    assert cloud.multiplier_variants[0].repeat_count_parameter_id is not None


def test_dodge_entries_keep_independent_dodge_damage_tags() -> None:
    definition = _definition()
    dash = _entry(definition, "dodge-dash")
    counter = _entry(definition, "dodge-counter")

    assert dash.skill_group is SkillGroup.DODGE
    assert dash.damage_tags == frozenset({DamageTag.DASH_ATTACK})
    assert counter.skill_group is SkillGroup.DODGE
    assert counter.damage_tags == frozenset({DamageTag.DODGE_COUNTER})
    assert DamageTag.BASIC_ATTACK not in dash.damage_tags | counter.damage_tags


def test_mutually_exclusive_variants_are_explicit_and_selectable_by_id() -> None:
    definition = _definition()
    shatter = _entry(definition, "basic-mingxin-zhanliuguang-mie")
    assert shatter.multiplier_relation is MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT
    assert len(shatter.multiplier_variants) == 2
    assert len({item.variant_id for item in shatter.multiplier_variants}) == 2
    assert all(item.condition_ids for item in shatter.multiplier_variants)

    yin = _entry(definition, "special-yin-canglan")
    assert yin.multiplier_relation is MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT
    assert len(yin.multiplier_variants) == 2
    assert yin.multiplier_variants[1].condition_ids


def test_static_conditions_are_compilation_outputs_and_cannot_be_overridden() -> None:
    definition = _definition(mingxin_active=True, entry_move_uses_linren=True)
    static = [
        item
        for item in definition.scenario_conditions
        if item.resolution is ConditionResolution.STATIC
    ]
    assert len(static) == 2
    scenario = CalculationScenario(
        scenario_id="scenario:ye-default",
        current_operator=definition.character_id,
        conditions=definition.scenario_conditions,
        parameters=definition.scenario_parameters,
    )
    definition.validate_scenario(scenario)

    overridden = replace(
        scenario,
        conditions=(replace(static[0], value=False), static[1], *scenario.conditions[2:]),
    )
    with pytest.raises(ValueError, match="static compilation condition"):
        definition.validate_scenario(overridden)


def test_definition_validates_variant_selection_against_its_registry() -> None:
    definition = _definition()
    scenario = CalculationScenario(
        scenario_id="scenario:ye-variants",
        current_operator=definition.character_id,
        conditions=definition.scenario_conditions,
        parameters=definition.scenario_parameters,
        selected_multiplier_variant_ids=frozenset(
            {
                definition.move_entries[0].multiplier_variants[0].variant_id,
            }
        ),
    )
    definition.validate_scenario(scenario)

    with pytest.raises(ValueError, match="unknown multiplier variants"):
        definition.validate_scenario(
            replace(
                scenario,
                selected_multiplier_variant_ids=frozenset(
                    {MultiplierVariantId("variant:does-not-exist")}
                ),
            )
        )


def test_unlocked_cinema_items_remain_ineligible_but_templates_exist() -> None:
    definition = _definition(cinema_level=0)
    rules = {item.rule_id: item for item in definition.rule_items}
    assert rules[RuleItemId("rule:ye:1431:cinema1")].eligibility is RuleEligibility.INELIGIBLE
    assert rules[RuleItemId("rule:ye:1431:cinema2")].eligibility is RuleEligibility.INELIGIBLE
    assert rules[RuleItemId("rule:ye:1431:cinema6")].eligibility is RuleEligibility.INELIGIBLE

    guichen = _entry(definition, "special-mingxin-guichen")
    zhanwang = _entry(definition, "ultimate-zhanwangkaitian")
    assert len(guichen.derived_damage_events) == 1
    assert len(zhanwang.derived_damage_events) == 1
    assert all(
        item.template.element is Element.LINREN
        and item.template.skill_group is None
        and item.template.damage_tags == frozenset()
        and item.template.source_rule_item_id
        == rules[RuleItemId("rule:ye:1431:cinema6")].rule_id
        and item.template.template_id in {
            creation.result.event_template_id
            for effect in rules[RuleItemId("rule:ye:1431:cinema6")].effects
            if isinstance(effect, EventCreationEffect)
            for creation in (effect,)
        }
        and item.multiplier.value.value == 15.0  # type: ignore[union-attr]
        for item in (
            guichen.derived_damage_events[0],
            zhanwang.derived_damage_events[0],
        )
    )


def test_cinema_effects_keep_move_filters_and_rule_scope() -> None:
    definition = _definition(cinema_level=6)
    c2 = next(item for item in definition.rule_items if str(item.rule_id).endswith("cinema2"))
    c6 = next(item for item in definition.rule_items if str(item.rule_id).endswith("cinema6"))

    c2_move_filters = {
        effect.rule.filters[0].move_id
        for effect in c2.effects
        if isinstance(effect, ModifierEffect)
        and isinstance(effect.rule.filters[0], MoveIdFilter)
    }
    assert MoveId("move:special-mingxin-feiguang") in c2_move_filters
    assert MoveId("move:ultimate-zhanwangkaitian") in c2_move_filters
    assert all(
        isinstance(effect, EventCreationEffect)
        and isinstance(effect.rule.filters[0], MoveIdFilter)
        for effect in c6.effects
    )
    c6_by_template = {
        effect.result.event_template_id: effect.rule.filters[0].move_id
        for effect in c6.effects
        if isinstance(effect, EventCreationEffect)
        and isinstance(effect.rule.filters[0], MoveIdFilter)
    }
    assert c6_by_template == {
        item.template.template_id: move_id
        for item, move_id in zip(
            (
                _entry(definition, "special-mingxin-guichen").derived_damage_events[0],
                _entry(definition, "ultimate-zhanwangkaitian").derived_damage_events[0],
            ),
            (
                MoveId("move:special-mingxin-guichen"),
                MoveId("move:ultimate-zhanwangkaitian"),
            ),
        )
    }


def test_core_level_and_entry_element_are_compiled_from_config() -> None:
    levels = tuple(
        CharacterSkillLevel(group, 14)
        for group in SkillGroup
    )
    definition = compile_ye_shunguang(
        YeShunguangCompileConfig(
            skill_levels=levels,
            core_level=7,
            mingxin_active=True,
            entry_move_uses_linren=True,
        )
    )
    fast = _entry(definition, "basic-fast-1")
    assert fast.multiplier_variants[0].multiplier.value.value == pytest.approx(1.743)  # type: ignore[union-attr]
    hed = next(item for item in definition.rule_items if str(item.rule_id).endswith("hedao"))
    assert isinstance(hed.effects[0], ModifierEffect)
    assert isinstance(hed.effects[1], ModifierEffect)
    assert hed.effects[0].result.value.value == pytest.approx(0.30)  # type: ignore[union-attr]
    assert hed.effects[1].result.value.value == pytest.approx(0.25)  # type: ignore[union-attr]
    assert _entry(definition, "ultimate-zhuyunjingting").main_damage_event.element is Element.LINREN
    physical_entry = _definition(
        mingxin_active=False,
        entry_move_uses_linren=False,
    )
    assert (
        _entry(physical_entry, "ultimate-zhuyunjingting").main_damage_event.element
        is Element.PHYSICAL
    )


def test_veil_bonus_uses_bonus_units_and_cinema_cap() -> None:
    base = _definition(cinema_level=0, enemy_stun_vulnerability_bonus=1.5)
    c4 = _definition(cinema_level=4, enemy_stun_vulnerability_bonus=3.0)
    base_veil = next(item for item in base.rule_items if str(item.rule_id).endswith("veil"))
    c4_veil = next(item for item in c4.rule_items if str(item.rule_id).endswith("veil"))
    assert isinstance(base_veil.effects[0], ModifierEffect)
    assert isinstance(c4_veil.effects[0], ModifierEffect)
    assert base_veil.effects[0].result.operation is EffectOperation.OVERRIDE
    assert base_veil.effects[0].result.value.value == pytest.approx(1.1)  # type: ignore[union-attr]
    assert c4_veil.effects[0].result.value.value == pytest.approx(2.0)  # type: ignore[union-attr]
