from __future__ import annotations

import re

import pytest

from core.application import assemble_build
from core.application.equipment import compile_wengine, load_wengine_raw_record
from core.application.equipment.wengine import (
    ASTRA_DAMAGE_BUFF_CONDITION_ID,
    WENGINE_ALICE_ID,
    WENGINE_ASTRA_ID,
    WENGINE_TRIGGER_ID,
    WENGINE_YE_ID,
    WENGINE_YUZUHA_ID,
    SIGNATURE_WENGINE_BY_CHARACTER,
    YE_VEIL_ACTIVE_CONDITION_ID,
    signature_wengine_id_for,
)
from core.application.equipment.wengine_ids import (
    WENGINE_ELECTRO_STORM_I_ID,
    WENGINE_ELECTRO_STORM_II_ID,
    WENGINE_ELECTRO_STORM_III_ID,
    WENGINE_IDENTITY_STANDARD_ID,
    WENGINE_IDENTITY_ALTERNATE_ID,
    WENGINE_ASH_COBALT_BLUE_ID,
    WENGINE_LUNAR_DECRESCENT_ID,
    WENGINE_LUNAR_NOVILUNA_ID,
    WENGINE_LUNAR_PLENILUNA_ID,
    WENGINE_LUNAR_STRING_ID,
    WENGINE_REVERB_MARK_I_ID,
    WENGINE_REVERB_MARK_II_ID,
    WENGINE_TURBULENCE_ARROW_ID,
    WENGINE_TURBULENCE_AXE_ID,
    WENGINE_TURBULENCE_CANNON_ID,
    WENGINE_STREET_SUPERSTAR_ID,
    WENGINE_TIME_SLICE_ID,
    WENGINE_RAINFOREST_GOURMAND_ID,
    WENGINE_STARLIGHT_ENGINE_ID,
    WENGINE_HUMAN_IS_MEAT_ID,
    WENGINE_ATTACK_SAMPLE_IDS,
    WENGINE_SUPPORT_SAMPLE_IDS,
)
from core.presentation.registry import registration_for
from core.data.wengines.loader import load_wengine_record, supported_wengine_ids
from core.application.rules import RuleEligibility
from core.types import (
    BuildContributionLayer,
    BuildMode,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    CharacterId,
    CharacterBuildDefinition,
    CharacterStats,
    CharacterRole,
    CharacterStat,
    DamageTag,
    AnyFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTypeFilter,
    DamageType,
    EquipmentOwnerCapabilities,
    EffectOperation,
    Element,
    ElementFilter,
    Resolved,
    RuleStackCondition,
    CalculationNode,
    SkillGroup,
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


def test_first_nanoka_catalog_wengine_has_lossless_live_source_and_all_refinements() -> None:
    record = load_wengine_record(str(WENGINE_LUNAR_PLENILUNA_ID))
    raw = load_wengine_raw_record(str(WENGINE_LUNAR_PLENILUNA_ID))
    assert raw.name == "「月相」-望"
    assert raw.rarity == "B"
    assert raw.specialty is CharacterRole.ATTACK
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/weapon/12001.json"
    assert record["source_index_url"] == "https://static.nanoka.cc/zzz/3.2/weapon.json"
    assert record["raw_nanoka_detail"]["level"]["60"]["rate"] == 94090
    assert record["catalog"]["atk"] == 475
    assert (raw.base_attack, raw.advanced_stat_name, raw.advanced_stat_value) == (
        475.0,
        "攻击力",
        0.20,
    )
    assert str(WENGINE_LUNAR_PLENILUNA_ID) in supported_wengine_ids()

    owner = CharacterId("character:1431")
    capabilities = registration_for(owner).equipment_capabilities
    expected_bonus = (0.12, 0.14, 0.16, 0.18, 0.20)
    contributions = []
    for refinement, bonus in enumerate(expected_bonus, start=1):
        result = compile_wengine(
            WEngineBuildInput(
                WENGINE_LUNAR_PLENILUNA_ID,
                owner,
                level=60,
                refinement=refinement,
            ),
            owner_capabilities=capabilities,
        )
        assert result.complete is True
        assert result.rule_items[0].eligibility is RuleEligibility.ELIGIBLE
        assert result.contributions[0].value == Resolved(475.0)
        assert result.contributions[0].layer is BuildContributionLayer.WHITE_VALUE
        assert result.contributions[1].stat is CharacterStat.ATTACK
        assert result.contributions[1].layer is BuildContributionLayer.OUT_OF_COMBAT_PERCENT
        assert result.contributions[1].value == Resolved(0.20)
        effect = result.rule_items[0].effects[0]
        assert effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
        assert effect.result.value == Resolved(bonus)
        assert {item.damage_tag for item in effect.rule.filters[1].filters} == {
            DamageTag.BASIC_ATTACK,
            DamageTag.DASH_ATTACK,
            DamageTag.DODGE_COUNTER,
        }
        contributions.append(result.contributions)
    assert contributions[0] == contributions[-1]

    wrong_owner = compile_wengine(
        WEngineBuildInput(WENGINE_LUNAR_PLENILUNA_ID, CharacterId("character:1251")),
        owner_capabilities=registration_for("character:1251").equipment_capabilities,
    )
    assert wrong_owner.contributions
    assert all(item.eligibility is RuleEligibility.INELIGIBLE for item in wrong_owner.rule_items)

    unsupported_level = compile_wengine(
        WEngineBuildInput(WENGINE_LUNAR_PLENILUNA_ID, owner, level=50),
        owner_capabilities=capabilities,
    )
    assert unsupported_level.complete is False
    assert unsupported_level.contributions == ()
    assert unsupported_level.rule_items == ()


def test_next_nanoka_catalog_wengine_batch_preserves_sources_build_stats_and_refinements() -> None:
    cases = (
        (
            WENGINE_LUNAR_DECRESCENT_ID,
            "「月相」-晦",
            CharacterRole.ATTACK,
            CharacterStat.ATTACK,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.20,
            CharacterId("character:1431"),
            CalculationNode.DAMAGE_NORMAL_BONUS,
            "damage_bonus",
            (0.15, 0.175, 0.20, 0.225, 0.25),
        ),
        (
            WENGINE_LUNAR_NOVILUNA_ID,
            "「月相」-朔",
            CharacterRole.ATTACK,
            CharacterStat.CRIT_RATE,
            BuildContributionLayer.DIRECT_RATIO,
            0.16,
            CharacterId("character:1431"),
            None,
            "energy_restore",
            (3, 3.5, 4, 4.5, 5),
        ),
        (
            WENGINE_REVERB_MARK_I_ID,
            "「残响」-Ⅰ型",
            CharacterRole.SUPPORT,
            CharacterStat.ATTACK,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.20,
            CharacterId("character:1311"),
            CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
            "team_impact_percent",
            (0.08, 0.09, 0.10, 0.11, 0.12),
        ),
        (
            WENGINE_REVERB_MARK_II_ID,
            "「残响」-Ⅱ型",
            CharacterRole.SUPPORT,
            CharacterStat.ENERGY_REGEN,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.40,
            CharacterId("character:1311"),
            CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
            "team_anomaly_mastery_flat",
            (10, 12, 13, 15, 16),
        ),
        (
            WENGINE_TURBULENCE_CANNON_ID,
            "「湍流」-铳型",
            CharacterRole.STUN,
            CharacterStat.ATTACK,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.20,
            CharacterId("character:1361"),
            CalculationNode.DAZE_OUTGOING_BONUS,
            "ex_daze_bonus",
            (0.10, 0.115, 0.13, 0.145, 0.16),
        ),
        (
            WENGINE_TURBULENCE_ARROW_ID,
            "「湍流」-矢型",
            CharacterRole.STUN,
            CharacterStat.IMPACT,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.12,
            CharacterId("character:1361"),
            CalculationNode.DAZE_OUTGOING_BONUS,
            "primary_target_daze_bonus",
            (0.08, 0.09, 0.10, 0.11, 0.12),
        ),
        (
            WENGINE_TURBULENCE_AXE_ID,
            "「湍流」-斧型",
            CharacterRole.STUN,
            CharacterStat.ENERGY_REGEN,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.40,
            CharacterId("character:1361"),
            CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
            "impact_percent",
            (0.09, 0.10, 0.11, 0.12, 0.13),
        ),
        (
            WENGINE_ELECTRO_STORM_I_ID,
            "「电磁暴」-壹式",
            CharacterRole.ANOMALY,
            CharacterStat.ATTACK,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.20,
            CharacterId("character:1401"),
            CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
            "anomaly_mastery_flat",
            (25, 28, 32, 36, 40),
        ),
        (
            WENGINE_ELECTRO_STORM_II_ID,
            "「电磁暴」-贰式",
            CharacterRole.ANOMALY,
            CharacterStat.ANOMALY_PROFICIENCY,
            BuildContributionLayer.OUT_OF_COMBAT_FLAT,
            60.0,
            CharacterId("character:1401"),
            CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
            "anomaly_proficiency_flat",
            (25, 28, 32, 36, 40),
        ),
        (
            WENGINE_ELECTRO_STORM_III_ID,
            "「电磁暴」-叁式",
            CharacterRole.ANOMALY,
            CharacterStat.PENETRATION_RATE,
            BuildContributionLayer.DIRECT_RATIO,
            0.16,
            CharacterId("character:1401"),
            None,
            "energy_restore",
            (3.5, 4, 4.5, 5, 5.5),
        ),
        (
            WENGINE_IDENTITY_STANDARD_ID,
            "「恒等式」-本格",
            CharacterRole.DEFENSE,
            CharacterStat.DEFENSE,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.32,
            CharacterId("character:1341"),
            CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
            "defense_percent",
            (0.20, 0.23, 0.26, 0.29, 0.32),
        ),
        (
            WENGINE_IDENTITY_ALTERNATE_ID,
            "「恒等式」-变格",
            CharacterRole.DEFENSE,
            CharacterStat.DEFENSE,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.32,
            CharacterId("character:1341"),
            None,
            "enemy_damage_reduction",
            (0.06, 0.07, 0.08, 0.09, 0.10),
        ),
        (
            WENGINE_ASH_COBALT_BLUE_ID,
            "「灰烬」-钴蓝",
            CharacterRole.RUPTURE,
            CharacterStat.HP,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.20,
            CharacterId("character:1371"),
            CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
            "attack_percent",
            (0.072, 0.082, 0.093, 0.104, 0.115),
        ),
        (
            WENGINE_STREET_SUPERSTAR_ID,
            "街头巨星",
            CharacterRole.ATTACK,
            CharacterStat.ATTACK,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.25,
            CharacterId("character:1431"),
            CalculationNode.DAMAGE_NORMAL_BONUS,
            "ultimate_bonus_per_charge",
            (0.15, 0.172, 0.195, 0.217, 0.24),
        ),
        (
            WENGINE_RAINFOREST_GOURMAND_ID,
            "雨林饕客",
            CharacterRole.ANOMALY,
            CharacterStat.ANOMALY_PROFICIENCY,
            BuildContributionLayer.OUT_OF_COMBAT_FLAT,
            75.0,
            CharacterId("character:1401"),
            CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
            "attack_percent_per_stack",
            (0.025, 0.028, 0.032, 0.036, 0.04),
        ),
        (
            WENGINE_STARLIGHT_ENGINE_ID,
            "星徽引擎",
            CharacterRole.ATTACK,
            CharacterStat.ATTACK,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.25,
            CharacterId("character:1431"),
            CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
            "attack_percent",
            (0.12, 0.138, 0.156, 0.174, 0.192),
        ),
        (
            WENGINE_HUMAN_IS_MEAT_ID,
            "人为刀俎",
            CharacterRole.STUN,
            CharacterStat.ENERGY_REGEN,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            0.50,
            CharacterId("character:1361"),
            CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
            "impact_percent_per_energy_stack",
            (0.02, 0.023, 0.026, 0.029, 0.032),
        ),
    )
    for (
        wengine_id,
        name,
        role,
        stat,
        layer,
        advanced_value,
        owner,
        effect_path,
        numeric_key,
        expected_values,
    ) in cases:
        record = load_wengine_record(str(wengine_id))
        raw = load_wengine_raw_record(str(wengine_id))
        numeric_id = str(wengine_id).split(":")[-1]
        expected_base = 475.0 if numeric_id.startswith("12") else 594.0
        assert raw.name == name
        assert raw.rarity == ("A" if numeric_id.startswith("13") else "B")
        assert raw.specialty is role
        assert raw.base_stat is CharacterStat.ATTACK
        assert raw.source_version == "3.2"
        assert raw.source_url == f"https://static.nanoka.cc/zzz/3.2/zh/weapon/{numeric_id}.json"
        assert record["source_index_url"] == "https://static.nanoka.cc/zzz/3.2/weapon.json"
        assert record["raw_nanoka_detail"]["id"] == int(numeric_id)
        assert record["catalog"]["atk"] == expected_base
        assert raw.base_attack == expected_base
        assert (raw.advanced_stat_name, raw.advanced_stat_value) == (
            record["nanoka_detail_fields"]["rand_property"]["name"],
            advanced_value,
        )
        assert tuple(item.refinement for item in raw.talents) == (1, 2, 3, 4, 5)
        assert tuple(item.numeric_values[numeric_key] for item in raw.talents) == expected_values
        capabilities = registration_for(owner).equipment_capabilities
        for refinement, value in enumerate(expected_values, start=1):
            talent = raw.talents[refinement - 1]
            assert talent.text == record["raw_nanoka_detail"]["talents"][
                str(refinement)
            ]["desc"]
            plain_text = re.sub(r"<[^>]+>", "", talent.text)
            if numeric_key in {
                "damage_bonus",
                "team_impact_percent",
                "ex_daze_bonus",
                "primary_target_daze_bonus",
                "impact_percent",
                "defense_percent",
                "enemy_damage_reduction",
                "attack_percent",
                "ultimate_bonus_per_charge",
                "attack_percent_per_stack",
                "impact_percent_per_energy_stack",
            }:
                text_value = float(re.search(r"([\d.]+)%", plain_text).group(1)) / 100
            elif numeric_key == "energy_restore":
                text_value = float(re.search(r"回复\s*([\d.]+)", plain_text).group(1))
            else:
                text_value = float(re.search(r"提升\s*([\d.]+)", plain_text).group(1))
            assert talent.numeric_values[numeric_key] == pytest.approx(text_value)
            if numeric_key == "team_anomaly_mastery_flat":
                assert talent.numeric_values["team_anomaly_proficiency_flat"] == pytest.approx(
                    text_value
                )
            if numeric_key == "ultimate_bonus_per_charge":
                assert talent.numeric_values["max_charges"] == 3
            if numeric_key in {"attack_percent_per_stack", "impact_percent_per_energy_stack"}:
                assert talent.numeric_values["energy_per_stack"] == 10
                assert talent.numeric_values["max_stacks"] == (
                    10 if numeric_key == "attack_percent_per_stack" else 8
                )
            result = compile_wengine(
                WEngineBuildInput(wengine_id, owner, refinement=refinement),
                owner_capabilities=capabilities,
            )
            assert result.complete is True
            assert result.contributions[0].value == Resolved(expected_base)
            assert result.contributions[1].stat is stat
            assert result.contributions[1].layer is layer
            assert result.contributions[1].value == Resolved(advanced_value)
            if effect_path is None:
                assert len(result.rule_items) == 1
                assert result.rule_items[0].effects == ()
                assert any(not item.blocking for item in result.diagnostics)
                assert result.rule_items[0].diagnostics[0].original_text == talent.text
                continue
            effect = result.rule_items[0].effects[0]
            assert effect.result.modifier_path is effect_path
            assert effect.result.value == Resolved(value)
            if numeric_key == "ultimate_bonus_per_charge":
                assert (result.rule_items[0].stack_count, result.rule_items[0].stack_min, result.rule_items[0].stack_max) == (
                    0,
                    0,
                    3,
                )
            if numeric_key == "attack_percent_per_stack":
                assert result.rule_items[0].stack_max == 10
            if numeric_key == "impact_percent_per_energy_stack":
                assert result.rule_items[0].stack_max == 8

    reverb = compile_wengine(
        WEngineBuildInput(WENGINE_REVERB_MARK_II_ID, CharacterId("character:1311")),
        owner_capabilities=registration_for("character:1311").equipment_capabilities,
    ).rule_items[0]
    assert reverb.effects[1].result.modifier_path is (
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS
    )
    assert reverb.non_stacking_group_id == "wengine:12005:sound-wave-team-anomaly-stats"


def test_vanguard_lunar_string_uses_white_defense_then_additive_defense_percent() -> None:
    owner = CharacterId("character:vanguard-test")
    capabilities = EquipmentOwnerCapabilities(
        owner,
        CharacterRole.VANGUARD,
        skill_groups=frozenset({SkillGroup.BASIC_ATTACK}),
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
    )
    expected_bonuses = (0.18, 0.21, 0.24, 0.27, 0.30)
    weapons = tuple(
        compile_wengine(
            WEngineBuildInput(WENGINE_LUNAR_STRING_ID, owner, refinement=refinement),
            owner_capabilities=capabilities,
        )
        for refinement in range(1, 6)
    )
    weapon = weapons[-1]
    record = load_wengine_record(str(WENGINE_LUNAR_STRING_ID))

    assert weapon.raw.base_attack == 0.0
    assert weapon.raw.base_stat is CharacterStat.DEFENSE
    assert weapon.raw.static_base_value == 282.0
    assert record["catalog"]["atk"] == 282
    assert record["resolved_level_60"]["base_stat_key"] == "defense"
    assert record["resolved_level_60"]["base_stat_value"] == 282.0
    assert record["raw_nanoka_detail"][
        "base_property"
    ]["name"] == "基础防御力"
    assert tuple((item.stat, item.layer, item.value) for item in weapon.contributions) == (
        (CharacterStat.DEFENSE, BuildContributionLayer.WHITE_VALUE, Resolved(282.0)),
        (
            CharacterStat.DEFENSE,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            Resolved(0.32),
        ),
    )
    assert weapon.rule_items[0].eligibility is RuleEligibility.ELIGIBLE
    assert weapon.rule_items[0].effects[0].result.value == Resolved(0.30)
    assert any("no Vanguard owner" in item.message for item in weapon.diagnostics)
    assert tuple(result.rule_items[0].effects[0].result.value for result in weapons) == tuple(
        Resolved(value) for value in expected_bonuses
    )
    assert tuple(result.raw.talents[index].text for index, result in enumerate(weapons)) == tuple(
        record["raw_nanoka_detail"]["talents"][str(index + 1)]["desc"]
        for index in range(5)
    )

    defense_disc = BuildStatContribution(
        contribution_id="drive-disc:vanguard-test:defense-percent",
        source=BuildSource(
            source_id="drive-disc:test-defense-percent",
            source_type=BuildSourceType.DRIVE_DISC,
            label="Test DEF% Drive Disc",
        ),
        stat=CharacterStat.DEFENSE,
        layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        value=Resolved(0.30),
    )
    build = assemble_build(
        CharacterBuildDefinition(
            character_id=owner,
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(attack=1000.0),
            contributions=(*weapon.contributions, defense_disc),
        )
    )
    assert build.initial_stats.attack == Resolved(1000.0)
    assert build.initial_stats.defense.value == pytest.approx(1266.84)

    fixed_defense = BuildStatContribution(
        contribution_id="drive-disc:vanguard-test:defense-flat",
        source=BuildSource(
            source_id="drive-disc:test-defense-flat",
            source_type=BuildSourceType.DRIVE_DISC,
            label="Test flat DEF Drive Disc",
        ),
        stat=CharacterStat.DEFENSE,
        layer=BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        value=Resolved(50.0),
    )
    with_fixed_defense = assemble_build(
        CharacterBuildDefinition(
            character_id=owner,
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(attack=1000.0),
            contributions=(*weapon.contributions, defense_disc, fixed_defense),
        )
    )
    assert with_fixed_defense.initial_stats.defense.value == pytest.approx(1316.84)
    assert with_fixed_defense.initial_stats.attack == Resolved(1000.0)

    wrong_role = compile_wengine(
        WEngineBuildInput(WENGINE_LUNAR_STRING_ID, CharacterId("character:1431")),
        owner_capabilities=registration_for("character:1431").equipment_capabilities,
    )
    assert wrong_role.contributions[0].stat is CharacterStat.DEFENSE
    assert wrong_role.contributions[0].value == Resolved(282.0)
    assert all(item.eligibility is RuleEligibility.INELIGIBLE for item in wrong_role.rule_items)


def test_time_slice_numeric_values_are_extracted_by_trigger_and_refinement() -> None:
    expected = {
        "dodge_counter_decibel": (20, 23, 26, 29, 32),
        "ex_special_decibel": (25, 28.5, 32, 35.5, 40),
        "assist_attack_decibel": (30, 34.5, 39, 43.5, 48),
        "chain_attack_decibel": (35, 40, 45, 50, 55),
        "energy_restore": (0.7, 0.8, 0.9, 1.0, 1.1),
    }
    owner = CharacterId("character:1311")
    capabilities = registration_for(owner).equipment_capabilities
    for refinement in range(1, 6):
        record = load_wengine_record(str(WENGINE_TIME_SLICE_ID))
        raw = load_wengine_raw_record(str(WENGINE_TIME_SLICE_ID))
        talent = raw.talents[refinement - 1]
        plain_text = re.sub(r"<[^>]+>", "", talent.text)
        source_values = tuple(float(item) for item in re.findall(r"[\d.]+", plain_text))
        assert tuple(source_values[:5]) == tuple(
            values[refinement - 1] for values in expected.values()
        )
        assert {
            key: talent.numeric_values[key] for key in expected
        } == {
            key: values[refinement - 1] for key, values in expected.items()
        }
        assert talent.text == record["raw_nanoka_detail"]["talents"][
            str(refinement)
        ]["desc"]
        result = compile_wengine(
            WEngineBuildInput(WENGINE_TIME_SLICE_ID, owner, refinement=refinement),
            owner_capabilities=capabilities,
        )
        assert result.rule_items[0].effects == ()
        assert result.rule_items[0].diagnostics[0].original_text == talent.text


def test_live_raw_advanced_stats_apply_max_star_growth_for_percent_and_flat_values() -> None:
    ids = (
        "12001",
        "12002",
        "12003",
        "12004",
        "12005",
        "12007",
        "12008",
        "12009",
        "12010",
        "12011",
        "12012",
        "12013",
        "12014",
        "12015",
        "12016",
        "13001",
        "13002",
        "13003",
        "13004",
        "13005",
    )
    for numeric_id in ids:
        record = load_wengine_record(f"wengine:{numeric_id}")
        raw_detail = record["raw_nanoka_detail"]
        rand_property = raw_detail["rand_property"]
        max_star_rate = raw_detail["stars"]["5"]["rand_rate"]
        grown_value = rand_property["value"] * (1 + max_star_rate / 10_000)
        expected = grown_value / 10_000 if "%" in rand_property["format"] else grown_value
        assert record["resolved_level_60"]["advanced_stat_value"] == pytest.approx(
            expected
        )


def test_new_signature_raw_records_use_resolved_level_60_percentages() -> None:
    alice = load_wengine_raw_record(str(WENGINE_ALICE_ID))
    yuzuha = load_wengine_raw_record(str(WENGINE_YUZUHA_ID))
    trigger = load_wengine_raw_record(str(WENGINE_TRIGGER_ID))

    assert (alice.base_attack, alice.advanced_stat_name, alice.advanced_stat_value) == (
        713.0,
        "攻击力",
        0.30,
    )
    assert (yuzuha.base_attack, yuzuha.advanced_stat_name, yuzuha.advanced_stat_value) == (
        713.0,
        "能量自动回复",
        0.60,
    )
    assert (trigger.base_attack, trigger.advanced_stat_name, trigger.advanced_stat_value) == (
        713.0,
        "暴击率",
        0.24,
    )
    assert tuple(item.refinement for item in alice.talents) == (1, 2, 3, 4, 5)
    assert tuple(item.refinement for item in yuzuha.talents) == (1, 2, 3, 4, 5)
    assert tuple(item.refinement for item in trigger.talents) == (1, 2, 3, 4, 5)


def test_signature_mapping_is_explicit_and_not_name_derived() -> None:
    assert SIGNATURE_WENGINE_BY_CHARACTER[CharacterId("character:1311")] == WENGINE_ASTRA_ID
    assert signature_wengine_id_for(CharacterId("character:1431")) == WENGINE_YE_ID
    assert signature_wengine_id_for(CharacterId("character:1401")) == WENGINE_ALICE_ID
    assert signature_wengine_id_for(CharacterId("character:1411")) == WENGINE_YUZUHA_ID
    assert signature_wengine_id_for(CharacterId("character:1361")) == WENGINE_TRIGGER_ID


def test_new_signature_compilers_keep_static_values_and_owner_qualified_rules() -> None:
    cases = (
        (WENGINE_ALICE_ID, CharacterId("character:1401"), CharacterRole.ANOMALY, 0.30),
        (WENGINE_YUZUHA_ID, CharacterId("character:1411"), CharacterRole.SUPPORT, 0.60),
        (WENGINE_TRIGGER_ID, CharacterId("character:1361"), CharacterRole.STUN, 0.24),
    )
    for wengine_id, owner, role, advanced_value in cases:
        result = compile_wengine(
            WEngineBuildInput(wengine_id, owner),
            equipped_character_role=role,
        )
        assert result.complete is True
        assert result.contributions[0].value == Resolved(713.0)
        assert result.contributions[1].value == Resolved(advanced_value)
        assert all(str(item.rule_id).endswith(f"owner:{owner.rsplit(':', 1)[-1]}:{str(item.rule_id).rsplit(':', 1)[-1]}") for item in result.rule_items)


def test_new_signature_passives_are_ineligible_for_wrong_owner_roles_but_keep_stats() -> None:
    for wengine_id, owner, role in (
        (WENGINE_ALICE_ID, CharacterId("character:1411"), CharacterRole.SUPPORT),
        (WENGINE_YUZUHA_ID, CharacterId("character:1401"), CharacterRole.ANOMALY),
        (WENGINE_TRIGGER_ID, CharacterId("character:1401"), CharacterRole.ANOMALY),
    ):
        result = compile_wengine(
            WEngineBuildInput(wengine_id, owner),
            equipped_character_role=role,
        )
        assert result.contributions
        assert result.rule_items
        assert all(item.eligibility is RuleEligibility.INELIGIBLE for item in result.rule_items)


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


def test_new_signature_passive_filters_keep_each_textual_damage_scope_explicit() -> None:
    alice = compile_wengine(
        WEngineBuildInput(WENGINE_ALICE_ID, CharacterId("character:1401")),
        equipped_character_role=CharacterRole.ANOMALY,
    )
    alice_damage = next(
        item
        for item in alice.rule_items
        if str(item.rule_id).endswith(":physical-damage")
    )
    filters = alice_damage.effects[0].rule.filters
    type_scope = next(
        item
        for item in filters
        if isinstance(item, AnyFilter)
        and any(
            isinstance(child, (DamageTypeFilter, DamageSubtypeFilter))
            for child in item.filters
        )
    )
    assert {
        (item.damage_type if isinstance(item, DamageTypeFilter) else item.damage_subtype)
        for item in type_scope.filters
        if isinstance(item, (DamageTypeFilter, DamageSubtypeFilter))
    } == {
        DamageType.DIRECT,
        DamageType.DISORDER,
        DamageSubtype.ATTRIBUTE_ANOMALY,
    }

    yuzuha = compile_wengine(
        WEngineBuildInput(WENGINE_YUZUHA_ID, CharacterId("character:1411")),
        owner_capabilities=registration_for("character:1411").equipment_capabilities,
    )
    physical_rule = next(
        item
        for item in yuzuha.rule_items
        if str(item.rule_id).endswith(":anomaly-mastery")
    )
    assert physical_rule.eligibility is RuleEligibility.ELIGIBLE


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


def test_equipment_effect_eligibility_uses_owner_capabilities_not_only_role() -> None:
    ye_capabilities = registration_for("character:1431").equipment_capabilities
    deep_sea = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14119"), CharacterId("character:1431")),
        owner_capabilities=ye_capabilities,
    )
    dash_rule = next(
        item for item in deep_sea.rule_items if str(item.rule_id).endswith("dash-crit-buff")
    )
    assert dash_rule.eligibility is RuleEligibility.INELIGIBLE

    astra_capabilities = registration_for("character:1311").equipment_capabilities
    dream = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14145"), CharacterId("character:1311")),
        owner_capabilities=astra_capabilities,
    )
    assert dream.rule_items[0].eligibility is RuleEligibility.INELIGIBLE

    song = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14149"), CharacterId("character:1311")),
        owner_capabilities=astra_capabilities,
    )
    assert all(item.eligibility is RuleEligibility.INELIGIBLE for item in song.rule_items)

    song_owner = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14149"), CharacterId("character:1311")),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    assert len(song_owner.scenario_conditions) == 1
    assert isinstance(
        song_owner.rule_items[1].effects[0].rule.condition,
        RuleStackCondition,
    )
    dream_owner = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14145"), CharacterId("character:1311")),
        equipped_character_role=CharacterRole.SUPPORT,
    )
    assert dream_owner.rule_items[0].effects[0].rule.target.value == "team"
    assert all(
        effect.rule.target.value == "team"
        for rule in song_owner.rule_items
        for effect in rule.effects
    )


def test_wengine_element_filters_expand_base_elements_to_variants() -> None:
    for wengine_id, suffix, expected in (
        ("wengine:14119", "ice-damage", {Element.ICE, Element.LIESHUANG}),
        ("wengine:14124", "charged-ether-damage", {Element.ETHER, Element.XUANMO}),
    ):
        result = compile_wengine(
            WEngineBuildInput(WEngineId(wengine_id), CharacterId("character:1431")),
            equipped_character_role=CharacterRole.ATTACK,
        )
        rule = next(item for item in result.rule_items if str(item.rule_id).endswith(suffix))
        element_scope = next(
            item
            for item in rule.effects[0].rule.filters
            if isinstance(item, AnyFilter)
            and all(isinstance(child, ElementFilter) for child in item.filters)
        )
        assert {
            item.element for item in element_scope.filters if isinstance(item, ElementFilter)
        } == expected
