from __future__ import annotations

from dataclasses import replace

import pytest

from core.application import (
    CalculationScenario,
    ConditionResolution,
    CalculationRuleItem,
    MoveCalculationEntry,
    MultiplierRelation,
    RuleEligibility,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
    element_scope_filter,
)
from core.application.characters import (
    CharacterCalculationDefinition,
    CharacterSkillLevel,
)
from core.application.characters.ye_shunguang import (
    YE_SHUNGUANG_REVIEWED_MAPPING,
    YeShunguangCompileConfig,
    YeShunguangRawRecord,
    compile_ye_shunguang,
    load_raw_record,
)
from core.data.loader import load_character_record
from core.types import (
    AnyFilter,
    BattleStateId,
    CharacterId,
    CharacterRole,
    CalculationContext,
    CalculationNode,
    CharacterSnapshot,
    CharacterStats,
    DamageTag,
    DamageType,
    DamageEventId,
    DamageEventMetadata,
    DirectDamageEvent,
    EnemyId,
    EnemySnapshot,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventTemplateId,
    ModifierEffect,
    ModifierResult,
    MoveId,
    MoveIdFilter,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    SkillGroup,
)
from core.application.matching import (
    CharacterMatchProfile,
    EffectMatchContext,
    EffectMatchStatus,
    EffectMatcher,
    EnemyMatchProfile,
)


def _definition(
    *,
    cinema_level: int = 0,
    mingxin_active: bool = True,
    entry_move_uses_linren: bool = True,
    core_level: int = 1,
) -> CharacterCalculationDefinition:
    config = YeShunguangCompileConfig(
        cinema_level=cinema_level,
        mingxin_active=mingxin_active,
        entry_move_uses_linren=entry_move_uses_linren,
        core_level=core_level,
    )
    return compile_ye_shunguang(config, _raw_fixture())


def _raw_fixture() -> YeShunguangRawRecord:
    return load_raw_record(load_character_record("character:1431"))


def _event_for_entry(
    definition: CharacterCalculationDefinition,
    suffix: str,
) -> DirectDamageEvent:
    entry = _entry(definition, suffix)
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == entry.main_damage_event
    )
    return DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId(f"damage:test:{suffix}"),
            battle_state_id=BattleStateId("battle:test"),
            damage_dealer=definition.character_id,
            target_enemy=EnemyId("enemy:test"),
            element=template.element,
            created_at=0.0,
            skill_group=entry.skill_group,
            move_id=entry.move_id,
            damage_tags=entry.damage_tags,
        ),
        base_settlement_data_source=template.base_source,
        multiplier=entry.multiplier_variants[0].multiplier,
        crit_rule=template.crit_rule,
    )


def _matcher_context(
    event: DirectDamageEvent,
    definition: CharacterCalculationDefinition,
) -> EffectMatchContext:
    stats = CharacterStats(
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
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )
    return EffectMatchContext(
        current_event=event,
        calculation_context=CalculationContext(
            event=event,
            battle_state_id=event.metadata.battle_state_id,
            character_snapshots=(
                CharacterSnapshot(definition.character_id, 60, stats),
            ),
            target_snapshot=EnemySnapshot(
                enemy_id=event.metadata.target_enemy,
                level=70,
                initial_defense=Resolved(794.0),
                damage_resistance={Element.PHYSICAL: Resolved(0.0)},
                anomaly_buildup_resistance={},
                daze_resistance=Resolved(0.0),
                damage_reduction=Resolved(0.0),
            ),
        ),
        scenario=CalculationScenario(
            scenario_id="scenario:test",
            current_operator=definition.character_id,
            conditions=definition.scenario_conditions,
            enabled_rule_item_ids=frozenset(
                item.rule_id for item in definition.rule_items
            ),
        ),
        team=(
            CharacterMatchProfile(
                definition.character_id,
                definition.role,
            ),
        ),
        target=EnemyMatchProfile(event.metadata.target_enemy),
    )


def _entry(definition: CharacterCalculationDefinition, suffix: str) -> MoveCalculationEntry:
    return next(
        item for item in definition.move_entries if str(item.entry_id).endswith(suffix)
    )


def test_ye_shunguang_compiles_identity_and_usable_move_entries() -> None:
    definition = _definition()

    assert not hasattr(definition, "compile_config")
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


def test_raw_fixture_is_loaded_separately_from_reviewed_semantic_mapping() -> None:
    raw = _raw_fixture()
    assert str(raw.character_id) == "character:1431"
    assert raw.name == "叶瞬光"
    assert len(raw.moves) == 23

    definition = compile_ye_shunguang(
        YeShunguangCompileConfig(mingxin_active=True),
        raw_record=raw,
    )
    assert len(definition.move_entries) == 28
    with pytest.raises(ValueError, match="character name"):
        compile_ye_shunguang(
            YeShunguangCompileConfig(mingxin_active=True),
            raw_record=replace(raw, name="不是叶瞬光"),
        )


def test_raw_fixture_values_and_texts_drive_compilation() -> None:
    raw = _raw_fixture()
    fast = next(item for item in raw.moves if item.name == "普通攻击：快剑")
    first_parameter = fast.parameters[0]
    assert first_parameter.value_for_level(12) == pytest.approx(159.7)
    assert fast.description
    assert all(item.description for item in raw.mindscapes)
    assert all(item.description for item in raw.core_levels)
    assert not hasattr(YE_SHUNGUANG_REVIEWED_MAPPING, "core_damage_levels")
    assert not hasattr(YE_SHUNGUANG_REVIEWED_MAPPING.moves[0], "original_text")
    assert not hasattr(YE_SHUNGUANG_REVIEWED_MAPPING.moves[0].parameters[0], "levels")

    changed_parameter = replace(
        first_parameter,
        values=((12, 999.0), (14, 999.0), (16, 999.0)),
    )
    changed_move = replace(
        fast,
        parameters=(changed_parameter, *fast.parameters[1:]),
    )
    changed_raw = replace(
        raw,
        moves=tuple(
            changed_move if item.name == fast.name else item
            for item in raw.moves
        ),
    )
    definition = compile_ye_shunguang(
        YeShunguangCompileConfig(mingxin_active=True),
        changed_raw,
    )
    compiled_fast = _entry(definition, "basic-fast-1")
    assert compiled_fast.multiplier_variants[0].multiplier.value.value == pytest.approx(9.99)  # type: ignore[union-attr]
    assert compiled_fast.original_text == changed_move.description


def test_definition_rejects_dangling_contract_references() -> None:
    definition = _definition(cinema_level=6)

    rule = definition.rule_items[0]
    with pytest.raises(ValueError, match="unknown scenario conditions"):
        replace(
            definition,
            rule_items=(
                replace(
                    rule,
                    condition_ids=(ScenarioConditionId("condition:missing"),),
                ),
                *definition.rule_items[1:],
            ),
        )

    cloud = _entry(definition, "basic-cloud")
    bad_variant = replace(
        cloud.multiplier_variants[0],
        repeat_count_parameter_id=ScenarioParameterId("parameter:missing"),
    )
    bad_cloud = replace(cloud, multiplier_variants=(bad_variant,))
    with pytest.raises(ValueError, match="repeat-count parameter"):
        replace(
            definition,
            move_entries=(
                bad_cloud,
                *(
                    item
                    for item in definition.move_entries
                    if item.entry_id != cloud.entry_id
                ),
            ),
        )

    c6 = next(
        item
        for item in definition.rule_items
        if str(item.rule_id).endswith("cinema6")
    )
    creation = next(
        effect for effect in c6.effects if isinstance(effect, EventCreationEffect)
    )
    ghost_creation = replace(
        creation,
        result=replace(
            creation.result,
            event_template_id=EventTemplateId("template:ghost"),
        ),
    )
    with pytest.raises(ValueError, match="unknown event template"):
        replace(
            definition,
            rule_items=(
                *(
                    item
                    for item in definition.rule_items
                    if item.rule_id != c6.rule_id
                ),
                replace(c6, effects=(ghost_creation, c6.effects[1])),
            ),
        )

    derived = _entry(
        definition,
        "special-mingxin-guichen",
    ).derived_damage_events[0]
    duplicate_entry = replace(
        definition.move_entries[0],
        derived_damage_events=(derived,),
    )
    with pytest.raises(ValueError, match="one multiplier reference"):
        replace(
            definition,
            move_entries=(
                duplicate_entry,
                *definition.move_entries[1:],
            ),
        )


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


def test_ex_special_entries_retain_the_special_attack_parent_tag() -> None:
    definition = _definition()
    for suffix in ("special-dingfengbo", "special-mingxin-guichen"):
        entry = _entry(definition, suffix)
        assert entry.damage_tags == frozenset(
            {
                DamageTag.SPECIAL_ATTACK,
                DamageTag.EX_SPECIAL_ATTACK,
            }
        )


def test_mutually_exclusive_variants_are_explicit_and_conditioned() -> None:
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


def test_entry_element_condition_is_independent_from_mingxin_condition() -> None:
    definition = _definition(
        mingxin_active=False,
        entry_move_uses_linren=True,
    )
    conditions = {
        item.condition_id: item for item in definition.scenario_conditions
    }
    assert conditions[ScenarioConditionId("condition:ye:mingxin-active")].value is False
    assert (
        conditions[ScenarioConditionId("condition:ye:entry-move-uses-linren")].value
        is True
    )
    assert (
        _entry(definition, "ultimate-zhuyunjingting").main_damage_event.element
        is Element.LINREN
    )


def test_variant_conditions_are_the_single_selection_source() -> None:
    definition = _definition()
    shatter = _entry(definition, "basic-mingxin-zhanliuguang-mie")
    yin = _entry(definition, "special-yin-canglan")
    values = {
        condition_id: False
        for item in definition.scenario_conditions
        if "variant:" in str(item.condition_id)
        for condition_id in (item.condition_id,)
    }
    values[shatter.multiplier_variants[0].condition_ids[0]] = True
    values[yin.multiplier_variants[1].condition_ids[0]] = True
    scenario = CalculationScenario(
        scenario_id="scenario:ye-variants",
        current_operator=definition.character_id,
        conditions=tuple(
            replace(
                item,
                value=values.get(item.condition_id, item.value),
            )
            for item in definition.scenario_conditions
        ),
        parameters=definition.scenario_parameters,
    )
    definition.validate_scenario(scenario)

    with pytest.raises(ValueError, match="multiple mutually exclusive variants"):
        definition.validate_scenario(
            replace(
                scenario,
                conditions=tuple(
                    replace(item, value=True)
                    if item.condition_id
                    == shatter.multiplier_variants[1].condition_ids[0]
                    else item
                    for item in scenario.conditions
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


def test_compiled_ye_definition_feeds_matcher_without_cross_move_cinema_effects() -> None:
    definition = _definition(cinema_level=6)
    c6 = next(item for item in definition.rule_items if str(item.rule_id).endswith("cinema6"))
    veil = next(item for item in definition.rule_items if str(item.rule_id).endswith("veil"))
    matcher = EffectMatcher()

    veil_result = matcher.match_rule_item(
        veil,
        _matcher_context(
            _event_for_entry(definition, "ultimate-zhuyunjingting"),
            definition,
        ),
    )
    assert veil_result.status is EffectMatchStatus.MATCHED

    expected = {
        "special-mingxin-guichen": "effect:ye:1431:cinema6:guichen-extra",
        "ultimate-zhanwangkaitian": "effect:ye:1431:cinema6:zhanwang-extra",
        "basic-fast-1": None,
    }
    for suffix, expected_effect_id in expected.items():
        event = _event_for_entry(definition, suffix)
        result = matcher.match_rule_item(c6, _matcher_context(event, definition))
        assert result.status is (
            EffectMatchStatus.MATCHED
            if expected_effect_id is not None
            else EffectMatchStatus.NOT_MATCHED
        )
        assert tuple(str(effect.rule.effect_id) for effect in result.matched_effects) == (
            (expected_effect_id,) if expected_effect_id is not None else ()
        )


def test_veil_policy_matches_damage_dealer_not_current_operator() -> None:
    definition = _definition(cinema_level=0)
    veil = next(item for item in definition.rule_items if str(item.rule_id).endswith("veil"))
    own_event = _event_for_entry(definition, "basic-fast-1")
    own_result = EffectMatcher().match_rule_item(
        veil,
        _matcher_context(own_event, definition),
    )
    assert own_result.status is EffectMatchStatus.MATCHED

    other = CharacterId("character:other")
    other_event = replace(
        own_event,
        metadata=replace(own_event.metadata, damage_dealer=other),
    )
    own_context = _matcher_context(other_event, definition)
    own_snapshot = own_context.calculation_context.character_snapshots[0]
    other_context = replace(
        own_context,
        calculation_context=replace(
            own_context.calculation_context,
            character_snapshots=(own_snapshot, CharacterSnapshot(other, 60, own_snapshot.settlement_stats)),
        ),
        team=own_context.team
        + (CharacterMatchProfile(other, CharacterRole.ATTACK),),
    )
    other_result = EffectMatcher().match_rule_item(veil, other_context)
    assert other_result.status is EffectMatchStatus.NOT_MATCHED


def test_derived_cinema_template_has_no_source_move_identity_and_cannot_recurse() -> None:
    definition = _definition(cinema_level=6)
    zhanwang = _entry(definition, "ultimate-zhanwangkaitian")
    derived = zhanwang.derived_damage_events[0]
    template = next(
        item
        for item in definition.damage_event_templates
        if item.ref == derived.template
    )
    event = DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:test:derived"),
            battle_state_id=BattleStateId("battle:test"),
            damage_dealer=definition.character_id,
            target_enemy=EnemyId("enemy:test"),
            element=template.element,
            created_at=0.0,
            skill_group=template.ref.skill_group,
            move_id=template.move_id,
            damage_tags=template.ref.damage_tags,
        ),
        base_settlement_data_source=template.base_source,
        multiplier=derived.multiplier,
        crit_rule=template.crit_rule,
    )
    c6 = next(item for item in definition.rule_items if str(item.rule_id).endswith("cinema6"))
    result = EffectMatcher().match_rule_item(c6, _matcher_context(event, definition))
    assert result.status is EffectMatchStatus.NOT_MATCHED
    assert result.matched_effects == ()


def test_element_scope_expands_physical_rules_to_include_linren() -> None:
    expanded = element_scope_filter(Element.PHYSICAL)
    assert isinstance(expanded, AnyFilter)
    assert {
        item.element
        for item in expanded.filters
        if isinstance(item, ElementFilter)
    } == {Element.PHYSICAL, Element.LINREN}
    definition = _definition(mingxin_active=True)
    event = _event_for_entry(definition, "ultimate-zhuyunjingting")
    assert event.metadata.element is Element.LINREN
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:test:physical-scope"),
            source=RuleSource(
                source_id=RuleSourceId("source:test:physical-scope"),
                source_type=EffectSourceType.SKILL,
                label="physical scope",
            ),
            owner=definition.character_id,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(expanded,),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.1),
        ),
    )
    rule = CalculationRuleItem(
        rule_id=RuleItemId("rule:test:physical-scope"),
        owner=definition.character_id,
        source=effect.rule.source,
        display_name="physical scope",
        original_text="physical damage bonus",
        eligibility=RuleEligibility.ELIGIBLE,
        effects=(effect,),
    )
    context = _matcher_context(event, definition)
    context = replace(
        context,
        scenario=replace(
            context.scenario,
            enabled_rule_item_ids=frozenset({rule.rule_id}),
        ),
    )
    assert EffectMatcher().match_rule_item(rule, context).status is EffectMatchStatus.MATCHED


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
        ),
        _raw_fixture(),
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
    base = _definition(cinema_level=0)
    c4 = _definition(cinema_level=4)
    base_veil = next(item for item in base.rule_items if str(item.rule_id).endswith("veil"))
    c4_veil = next(item for item in c4.rule_items if str(item.rule_id).endswith("veil"))
    assert isinstance(base_veil.effects[0], ModifierEffect)
    assert isinstance(c4_veil.effects[0], ModifierEffect)
    assert base_veil.effects[0].result.operation is EffectOperation.SET
    assert base_veil.effects[0].result.modifier_path is CalculationNode.DAMAGE_VEIL_VULNERABILITY_CAP
    assert base_veil.effects[0].result.value.value == pytest.approx(1.1)  # type: ignore[union-attr]
    assert c4_veil.effects[0].result.value.value == pytest.approx(2.0)  # type: ignore[union-attr]
