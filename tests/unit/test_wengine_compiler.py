from __future__ import annotations

from core.application import assemble_build
from core.application.equipment import compile_wengine, load_wengine_raw_record
from core.application.equipment.wengine import (
    ASTRA_DAMAGE_BUFF_CONDITION_ID,
    WENGINE_ASTRA_ID,
    WENGINE_YE_ID,
    SIGNATURE_WENGINE_BY_CHARACTER,
    YE_VEIL_ACTIVE_CONDITION_ID,
    signature_wengine_id_for,
)
from core.application.equipment.wengine_ids import (
    WENGINE_ATTACK_SAMPLE_IDS,
    WENGINE_SUPPORT_SAMPLE_IDS,
)
from core.application.rules import RuleEligibility
from core.types import (
    BuildContributionLayer,
    BuildMode,
    CharacterId,
    CharacterBuildDefinition,
    CharacterStats,
    CharacterRole,
    CharacterStat,
    EffectOperation,
    Element,
    ElementFilter,
    AnyFilter,
    Resolved,
    CalculationNode,
    WEngineBuildInput,
    WEngineId,
)


def _base_stats(*, attack: float = 1000.0) -> CharacterStats:
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


def test_signature_wengine_raw_records_keep_confirmed_max_level_values() -> None:
    astra = load_wengine_raw_record(str(WENGINE_ASTRA_ID))
    ye = load_wengine_raw_record(str(WENGINE_YE_ID))

    assert astra.base_attack == 713.0
    assert astra.advanced_stat_name == "攻击力"
    assert astra.advanced_stat_value == 0.30
    assert ye.base_attack == 743.0
    assert ye.advanced_stat_name == "暴击伤害"
    assert ye.advanced_stat_value == 0.48


def test_signature_mapping_is_explicit_and_not_name_derived() -> None:
    assert SIGNATURE_WENGINE_BY_CHARACTER[CharacterId("character:1311")] == WENGINE_ASTRA_ID
    assert signature_wengine_id_for(CharacterId("character:1431")) == WENGINE_YE_ID


def test_astra_signature_compiles_white_attack_and_attack_percent() -> None:
    result = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:1311")),
        equipped_character_role=CharacterRole.SUPPORT,
    )

    assert result.complete is True
    assert [item.layer for item in result.contributions] == [
        BuildContributionLayer.WHITE_VALUE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
    ]
    assert result.contributions[0].value.value == 713.0
    assert result.contributions[1].stat is CharacterStat.ATTACK
    assert result.contributions[1].value.value == 0.30
    assert result.rule_items[0].condition_ids == (ASTRA_DAMAGE_BUFF_CONDITION_ID,)
    assert result.rule_items[0].stack_count == 2
    assert result.rule_items[0].stack_min == 0
    assert result.rule_items[0].stack_max == 2
    assert result.scenario_conditions[0].value is False


def test_astra_passive_is_ineligible_for_a_non_support_character() -> None:
    result = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:wrong")),
        equipped_character_role=CharacterRole.ATTACK,
    )

    assert result.contributions
    assert result.rule_items[0].eligibility is RuleEligibility.INELIGIBLE


def test_signature_static_values_flow_through_build_assembly() -> None:
    weapon = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:1311")),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:1311"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
            contributions=weapon.contributions,
        ),
        rule_items=weapon.rule_items,
    )

    assert result.complete is True
    assert result.initial_stats.attack == Resolved((1000.0 + 713.0) * 1.30)
    assert result.rule_items == weapon.rule_items


def test_refinement_changes_only_reviewed_passive_values_not_static_identity() -> None:
    astra_r1 = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:1311"), refinement=1),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    astra_r5 = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:1311"), refinement=5),
        equipped_character_role=CharacterRole.SUPPORT,
    )

    assert astra_r1.contributions == astra_r5.contributions
    assert astra_r1.rule_items[0].effects[0].result.value.value == 0.10
    assert astra_r5.rule_items[0].effects[0].result.value.value == 0.16
    assert astra_r1.rule_items[0].rule_id == astra_r5.rule_items[0].rule_id


def test_equipment_instance_ids_include_the_equipped_owner() -> None:
    first = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:1311")),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    second = compile_wengine(
        WEngineBuildInput(WENGINE_ASTRA_ID, CharacterId("character:1431")),
        equipped_character_role=CharacterRole.ATTACK,
    )

    assert {
        item.rule_id for item in first.rule_items
    }.isdisjoint({item.rule_id for item in second.rule_items})
    assert {
        effect.rule.effect_id
        for item in first.rule_items
        for effect in item.effects
    }.isdisjoint(
        {
            effect.rule.effect_id
            for item in second.rule_items
            for effect in item.effects
        }
    )
    assert {
        item.contribution_id for item in first.contributions
    }.isdisjoint({item.contribution_id for item in second.contributions})
    assert first.scenario_conditions[0].condition_id != second.scenario_conditions[0].condition_id


def test_ye_signature_compiles_physical_resistance_ignore_and_veil_rules() -> None:
    result = compile_wengine(
        WEngineBuildInput(WENGINE_YE_ID, CharacterId("character:1431")),
        equipped_character_role=CharacterRole.ATTACK,
    )

    assert result.complete is True
    assert result.contributions[0].value.value == 743.0
    assert result.contributions[1].stat is CharacterStat.CRIT_DAMAGE
    assert result.contributions[1].value.value == 0.48
    assert len(result.rule_items) == 2
    resistance_rule = result.rule_items[0]
    veil_rule = result.rule_items[1]
    assert resistance_rule.effects[0].result.modifier_path is CalculationNode.DAMAGE_RESISTANCE_IGNORE
    assert resistance_rule.effects[0].result.operation is EffectOperation.ADD
    assert isinstance(resistance_rule.effects[0].rule.filters[0], AnyFilter)
    element_filters = resistance_rule.effects[0].rule.filters[0].filters
    assert {item.element for item in element_filters if isinstance(item, ElementFilter)} == {
        Element.PHYSICAL,
        Element.LINREN,
    }
    assert veil_rule.condition_ids == (YE_VEIL_ACTIVE_CONDITION_ID,)
    assert result.scenario_conditions == ()
    assert {
        effect.result.modifier_path for effect in veil_rule.effects
    } == {
        CalculationNode.DAMAGE_NORMAL_BONUS,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
    }


def test_wengine_level_other_than_reviewed_max_is_explicitly_unresolved() -> None:
    result = compile_wengine(
        WEngineBuildInput(
            WENGINE_YE_ID,
            CharacterId("character:1431"),
            level=59,
        ),
        equipped_character_role=CharacterRole.ATTACK,
    )

    assert result.complete is False
    assert result.contributions == ()
    assert result.rule_items == ()
    assert result.diagnostics[0].blocking is True


def test_stage_18_2_5_sample_catalog_compiles_static_values_and_reviewed_effects() -> None:
    expected = {
        "wengine:14102": (684.0, CharacterStat.CRIT_RATE, 0.24),
        "wengine:14104": (684.0, CharacterStat.ATTACK, 0.30),
        "wengine:14119": (713.0, CharacterStat.CRIT_RATE, 0.24),
        "wengine:14120": (713.0, CharacterStat.CRIT_DAMAGE, 0.48),
        "wengine:14124": (713.0, CharacterStat.CRIT_DAMAGE, 0.48),
        "wengine:12006": (475.0, CharacterStat.HP, 0.20),
        "wengine:13103": (624.0, CharacterStat.ENERGY_REGEN, 0.50),
        "wengine:14121": (684.0, CharacterStat.PENETRATION_RATE, 0.24),
        "wengine:14145": (713.0, CharacterStat.HP, 0.30),
        "wengine:14149": (713.0, CharacterStat.ENERGY_REGEN, 0.60),
    }
    for wengine_id in WENGINE_ATTACK_SAMPLE_IDS + WENGINE_SUPPORT_SAMPLE_IDS:
        raw = load_wengine_raw_record(str(wengine_id))
        owner = CharacterId(
            "character:1431"
            if raw.specialty is CharacterRole.ATTACK
            else "character:1311"
        )
        result = compile_wengine(
            WEngineBuildInput(wengine_id, owner),
            equipped_character_role=raw.specialty,
        )
        base_attack, stat, advanced_value = expected[str(wengine_id)]
        assert result.complete is True
        assert result.contributions[0].value == Resolved(base_attack)
        assert result.contributions[1].stat is stat
        assert result.contributions[1].value == Resolved(advanced_value)
        assert result.rule_items
        assert all(item.effects for item in result.rule_items)


def test_stage_18_2_5_reviewed_effects_keep_damage_filters_and_stack_bounds() -> None:
    owner = CharacterId("character:1431")
    steel = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14102"), owner),
        equipped_character_role=CharacterRole.ATTACK,
    )
    assert steel.rule_items[0].effects[0].result.value == Resolved(0.20)
    assert isinstance(steel.rule_items[0].effects[0].rule.filters[0], AnyFilter)
    assert steel.rule_items[1].condition_ids == (
        steel.scenario_conditions[0].condition_id,
    )

    brimstone = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14104"), owner),
        equipped_character_role=CharacterRole.ATTACK,
    )
    assert brimstone.rule_items[0].stack_count == 8
    assert brimstone.rule_items[0].stack_min == 0
    assert brimstone.rule_items[0].stack_max == 8
    assert brimstone.rule_items[0].effects[0].result.modifier_path is CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS

    cradle = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14121"), CharacterId("character:1311")),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    assert cradle.rule_items[1].stack_count == 6
    assert cradle.rule_items[1].effects[0].result.value == Resolved(0.017)
