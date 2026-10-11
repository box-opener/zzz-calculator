from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.aria import (
    ARIA_ID,
    ARIA_REVIEWED_MAPPING,
    AriaCompileConfig,
    compile_aria,
    load_raw_record,
)
from core.application.characters.aria.reviewed import ARIA_THIRD_CHARGE_ANOMALY_HIT
from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import (
    effective_skill_level,
    raw_move_index,
)
from core.application.rules import RuleEligibility
from core.application.ids import ScenarioConditionId
from core.application.characters.templates import DischargeDamageEventTemplate
from core.application.execution import MatchedEffectApplication, apply_matched_modifiers
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import build_registered_editor_view
from core.types import (
    ANOMALY_ELEMENTS,
    AnyFilter,
    BASE_ELEMENT_BY_ELEMENT,
    CalculationNode,
    CharacterSnapshot,
    CharacterRole,
    CharacterStats,
    CreatedByEffectFilter,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    SkillGroup,
    SnapshotRule,
    InitialCharacterSnapshot,
    Unresolved,
    UnresolvedEffect,
)
from web.api import app


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "aria.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1501.json"
api_client = TestClient(app)


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _definition(config: AriaCompileConfig | None = None):
    raw = load_raw_record(_source_data())
    return raw, compile_aria(config or AriaCompileConfig(), raw)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1501:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _rule(definition, key: str):
    rule_id = f"rule:character:1501:{key}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _effect(rule) -> ModifierEffect | UnresolvedEffect:
    assert len(rule.effects) == 1
    effect = rule.effects[0]
    assert isinstance(effect, (ModifierEffect, UnresolvedEffect))
    return effect


def _stats(*, attack: float, anomaly_mastery: float, anomaly_proficiency: float) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.99),
        crit_damage=Resolved(4.0),
        anomaly_mastery=Resolved(anomaly_mastery),
        anomaly_proficiency=Resolved(anomaly_proficiency),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.ETHER: Resolved(0.0)},
    )


def _resolved_multiplier(entry) -> float:
    value = entry.multiplier_variants[0].multiplier
    assert isinstance(value, FixedMultiplier)
    assert isinstance(value.value, Resolved)
    return value.value.value


def _event_breakdown_value(event: dict[str, object], node: str) -> float:
    breakdown = event["modes"]["expected"]["calculation_breakdown"]
    return next(item["value"] for item in breakdown if item["node"] == node)


def test_aria_source_identity_and_complete_provenance_are_reviewed() -> None:
    data = _source_data()
    raw = load_raw_record(data)

    assert data["source_version"] == SOURCE_VERSION
    assert data["source_url"] == SOURCE_URL
    assert raw.source_version == SOURCE_VERSION
    assert raw.source_url == SOURCE_URL
    assert raw.character_id == ARIA_ID
    assert raw.name == "爱芮"
    assert raw.code_name == "Aria"
    assert raw.rarity == 4
    assert raw.specialty == "异常"
    assert raw.element == "以太"
    assert raw.faction == "妄想天使"
    assert raw.icon == "IconRole57"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert raw.potential_details == ()

    definition = compile_aria(AriaCompileConfig(), raw)
    assert definition.character_id == ARIA_ID
    assert definition.role is CharacterRole.ANOMALY
    assert definition.base_element is Element.ETHER
    assert len(definition.move_entries) == 21
    assert not any(
        entry.main_damage_event.damage_type is DamageType.ANOMALY
        and entry.main_damage_event.damage_subtype is DamageSubtype.DISORDER
        for entry in definition.move_entries
        if entry.move_id is not None
    )


def test_editor_exposes_selected_disorder_duration_metadata() -> None:
    view = build_registered_editor_view(
        str(ARIA_ID),
        {"core_level": 7},
        [str(ARIA_ID)],
    )
    disorder = next(
        item
        for item in view.moves
        if item.entry_id == "move-entry:character:1501:ether-disorder"
    )
    parameter = next(
        item
        for item in view.scenario_parameters
        if item.parameter_id == "parameter:aria:ether-disorder-remaining-half-seconds"
    )

    assert disorder.damage_type == "disorder"
    assert disorder.element == "ether"
    assert disorder.variants[0].parameter_value_id == parameter.parameter_id
    assert "剩余时间" in parameter.original_text


def test_direct_curves_use_source_components_without_duplicate_cooperative_child() -> None:
    raw, definition = _definition()
    raw_moves = raw_move_index(raw)
    level = effective_skill_level(AriaCompileConfig(), SkillGroup.BASIC_ATTACK)
    raw_charge = raw_moves["普通攻击：绝对音准"]
    cooperative_parameter = next(
        item
        for item in raw_charge.parameters
        if item.name == "三段蓄力攻击伤害倍率（协同）"
    )
    expected = sum(
        cooperative_parameter.value_for_level(level, skill_id)
        for skill_id in ("1501007", "1501022")
    ) / 100.0

    cooperative = _entry(definition, "basic-absolute-pitch-charge-3-cooperative")
    assert _resolved_multiplier(cooperative) == pytest.approx(expected)
    assert cooperative.multiplier_variants[0].parameter_name == "三段蓄力攻击伤害倍率（协同）"
    assert cooperative.main_damage_event.skill_group is SkillGroup.BASIC_ATTACK
    assert cooperative.main_damage_event.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert not cooperative.derived_damage_events
    assert not any(
        "cooperative" in str(item.template.template_id)
        for item in definition.independent_derived_damage_events
    )

    enhanced = _entry(definition, "basic-absolute-pitch-enhanced")
    assert _resolved_multiplier(enhanced) > _resolved_multiplier(cooperative)
    assert enhanced.condition_ids == (ScenarioConditionId("condition:aria:delusion-active"),)


def test_core_panel_and_elemental_discharge_rules_keep_known_scopes() -> None:
    _, definition = _definition(AriaCompileConfig(core_level=7))
    ap_effect = _effect(_rule(definition, "core:anomaly-proficiency"))
    assert isinstance(ap_effect, ModifierEffect)
    assert ap_effect.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS
    assert ap_effect.result.value.value == pytest.approx(90.0)

    discharge_rule = _rule(definition, "core:anomaly-discharge")
    creation = [item for item in discharge_rule.effects if isinstance(item, EventCreationEffect)]
    ratio_effects = [item for item in discharge_rule.effects if isinstance(item, ModifierEffect)]
    assert len(creation) == 1
    assert len(ratio_effects) == 12
    expected = {
        Element.ETHER: 27.5,
        Element.ELECTRIC: 14.3,
        Element.FIRE: 35.7,
        Element.PHYSICAL: 2.5,
        Element.ICE: 3.6,
        Element.WIND: 1.4,
    }
    assert ARIA_THIRD_CHARGE_ANOMALY_HIT in discharge_rule.condition_ids
    source_move_filter = next(
        item for item in creation[0].rule.filters if isinstance(item, AnyFilter)
    )
    assert {
        item.template_id
        for item in source_move_filter.filters
        if isinstance(item, EventTemplateIdFilter)
    } == {
        "template:character:1501:basic-absolute-pitch-charge-3:main",
        "template:character:1501:basic-absolute-pitch-charge-3-cooperative:main",
    }
    for element, rate in expected.items():
        base = next(
            item
            for item in ratio_effects
            if f"{element.value}:initial-mastery-ratio" in str(item.rule.effect_id)
        )
        assert isinstance(base.result.value, PanelStatDerivedValue)
        assert base.result.value.source_node is CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY
        assert base.result.value.coefficient == Resolved(rate / 1000.0)
        stunned = next(
            item
            for item in ratio_effects
            if f"{element.value}:stunned-target-ratio" in str(item.rule.effect_id)
        )
        assert isinstance(stunned.result.value, PanelStatDerivedValue)
        assert stunned.result.value.coefficient == Resolved(rate / 2000.0)
        assert any(isinstance(filter_, DamageSubtypeFilter) and filter_.damage_subtype is DamageSubtype.DISCHARGE for filter_ in base.rule.filters)
        assert any(
            isinstance(filter_, CreatedByEffectFilter)
            and filter_.effect_id == creation[0].rule.effect_id
            for filter_ in base.rule.filters
        )
        family_filter = next(
            filter_
            for filter_ in base.rule.filters
            if isinstance(filter_, AnyFilter)
            and any(isinstance(item, ElementFilter) for item in filter_.filters)
        )
        family_elements = {
            item.element for item in family_filter.filters if isinstance(item, ElementFilter)
        }
        assert family_elements == {
            candidate
            for candidate in ANOMALY_ELEMENTS
            if BASE_ELEMENT_BY_ELEMENT[candidate] is element
        }

    assert not any(
        "紊乱" in item.display_name or "侵蚀" in item.display_name
        for item in definition.move_entries
        if item.move_id is not None
    )


def test_core_proficiency_bonus_does_not_change_initial_mastery_derived_effects() -> None:
    _, definition = _definition(AriaCompileConfig(core_level=7, cinema_level=1))
    ap_effect = _effect(_rule(definition, "core:anomaly-proficiency"))
    core_rule = _rule(definition, "core:anomaly-discharge")
    core_ratio = next(
        item
        for item in core_rule.effects
        if isinstance(item, ModifierEffect)
        and str(item.rule.effect_id).endswith("ether:initial-mastery-ratio")
    )
    cinema_rate = next(
        item
        for item in _rule(definition, "cinema1:discharge-independent-crit").effects
        if isinstance(item, ModifierEffect)
        and item.result.modifier_path is CalculationNode.DISCHARGE_CRIT_RATE_OVERRIDE
    )
    assert isinstance(ap_effect, ModifierEffect)
    assert isinstance(core_ratio.result.value, PanelStatDerivedValue)
    assert isinstance(cinema_rate.result.value, PanelStatDerivedValue)

    initial = InitialCharacterSnapshot(
        ARIA_ID,
        60,
        _stats(attack=8000.0, anomaly_mastery=101.0, anomaly_proficiency=360.0),
    )
    observed = []
    for current in (
        _stats(attack=20000.0, anomaly_mastery=900.0, anomaly_proficiency=200.0),
        _stats(attack=40000.0, anomaly_mastery=50.0, anomaly_proficiency=9000.0),
    ):
        application = apply_matched_modifiers(
            (CharacterSnapshot(ARIA_ID, 60, current),),
            (),
            (
                MatchedEffectApplication(ap_effect),
                MatchedEffectApplication(core_ratio),
                MatchedEffectApplication(cinema_rate),
            ),
            ARIA_ID,
            initial_character_snapshots=(initial,),
        )
        assert not application.diagnostics
        assert application.character_snapshots[0].settlement_stats.anomaly_proficiency == Resolved(
            current.anomaly_proficiency.value + 90.0
        )
        assert application.character_snapshots[0].settlement_stats.anomaly_mastery == current.anomaly_mastery
        observed.append(
            {item.effect_id: item.value for item in application.event_modifiers}
        )

    assert observed[0] == observed[1]
    assert observed[0][core_ratio.rule.effect_id] == Resolved(0.0275 * 101.0)
    assert observed[0][cinema_rate.rule.effect_id] == Resolved(0.255)

    raw = load_raw_record(_source_data())
    elements = (
        Element.ETHER,
        Element.ELECTRIC,
        Element.FIRE,
        Element.PHYSICAL,
        Element.ICE,
        Element.WIND,
    )
    for level, source_core in enumerate(raw.core_levels, start=1):
        text = re.sub(r"<[^>]*>", "", source_core.description)
        match = re.search(
            r"每10点初始异常掌控\s*([\d.]+)%/([\d.]+)%/([\d.]+)%/"
            r"([\d.]+)%/([\d.]+)%/([\d.]+)%",
            text,
        )
        assert match is not None
        source_rates = tuple(float(item) for item in match.groups())

        level_raw, level_definition = _definition(AriaCompileConfig(core_level=level))
        level_core = level_raw.core_levels[level - 1]
        panel_match = re.search(
            r"异常精通提升\s*([\d.]+)\s*点",
            re.sub(r"<[^>]*>", "", level_core.description),
        )
        assert panel_match is not None
        panel_effect = _effect(_rule(level_definition, "core:anomaly-proficiency"))
        assert isinstance(panel_effect, ModifierEffect)
        assert panel_effect.result.value.value == pytest.approx(float(panel_match.group(1)))

        level_discharge = _rule(level_definition, "core:anomaly-discharge")
        for element, source_rate in zip(elements, source_rates):
            effect = next(
                item
                for item in level_discharge.effects
                if isinstance(item, ModifierEffect)
                and str(item.rule.effect_id).endswith(
                    f"{element.value}:initial-mastery-ratio"
                )
            )
            assert isinstance(effect.result.value, PanelStatDerivedValue)
            assert effect.result.value.source_node is CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY
            assert effect.result.value.coefficient == Resolved(source_rate / 1000.0)


def test_cinema1_override_is_rule_controlled_and_falls_back_to_source_record() -> None:
    _, c0 = _definition(AriaCompileConfig(cinema_level=0))
    _, c1 = _definition(AriaCompileConfig(cinema_level=1))
    c0_rule = _rule(c0, "cinema1:discharge-independent-crit")
    c1_rule = _rule(c1, "cinema1:discharge-independent-crit")
    assert c0_rule.eligibility is RuleEligibility.INELIGIBLE
    assert c1_rule.eligibility is RuleEligibility.ELIGIBLE
    assert len(c1_rule.effects) == 2
    rate_effect, damage_effect = c1_rule.effects
    assert isinstance(rate_effect, ModifierEffect)
    assert isinstance(damage_effect, ModifierEffect)
    assert rate_effect.result.modifier_path is CalculationNode.DISCHARGE_CRIT_RATE_OVERRIDE
    assert damage_effect.result.modifier_path is CalculationNode.DISCHARGE_CRIT_DAMAGE_OVERRIDE
    assert rate_effect.result.operation.value == "override"
    assert damage_effect.result.operation.value == "override"
    assert isinstance(rate_effect.result.value, PanelStatDerivedValue)
    assert rate_effect.result.value.source_node is CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY
    assert rate_effect.result.value.base == Resolved(0.25)
    assert rate_effect.result.value.coefficient == Resolved(0.005)
    assert rate_effect.result.value.threshold == Resolved(100.0)
    assert damage_effect.result.value == Resolved(0.25)
    assert any(
        isinstance(item, DamageDealerFilter) and item.character_id == ARIA_ID
        for item in rate_effect.rule.filters
    )
    assert any(
        isinstance(item, DamageTypeFilter) and item.damage_type is DamageType.ANOMALY
        for item in rate_effect.rule.filters
    )
    assert any(
        isinstance(item, DamageSubtypeFilter)
        and item.damage_subtype is DamageSubtype.DISCHARGE
        for item in rate_effect.rule.filters
    )
    c1_created_by = next(
        item for item in rate_effect.rule.filters if isinstance(item, AnyFilter)
    )
    assert len(c1_created_by.filters) == 1
    assert all(isinstance(item, CreatedByEffectFilter) for item in c1_created_by.filters)

    discharge_templates = [
        item for item in c1.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
    ]
    assert len(discharge_templates) == 1
    assert all(isinstance(item.crit_rule, NoCritRule) for item in discharge_templates)
    assert all(not item.multiplier_from_source_event for item in discharge_templates)
    assert all(item.history_record_source is None for item in discharge_templates)


def test_cinema2_cinema6_and_skill_levels_follow_their_authored_scope() -> None:
    _, c2 = _definition(AriaCompileConfig(cinema_level=2))
    c2_effect = _effect(_rule(c2, "cinema2:defense-ignore"))
    c2_delusion = _effect(_rule(c2, "cinema2:delusion-defense-ignore"))
    assert isinstance(c2_effect, ModifierEffect)
    assert isinstance(c2_delusion, ModifierEffect)
    assert c2_effect.result.modifier_path is CalculationNode.DAMAGE_DEFENSE_IGNORE
    assert c2_effect.result.value.value == pytest.approx(0.16)
    assert c2_delusion.result.value.value == pytest.approx(0.08)
    c2_scope = next(item for item in c2_effect.rule.filters if isinstance(item, AnyFilter))
    assert any(isinstance(item, DamageTypeFilter) and item.damage_type is DamageType.DIRECT for item in c2_scope.filters)
    assert any(isinstance(item, DamageSubtypeFilter) and item.damage_subtype is DamageSubtype.DISCHARGE for item in c2_scope.filters)

    config = AriaCompileConfig(
        cinema_level=6,
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 14),),
    )
    raw, c6 = _definition(config)
    c6_rule = _rule(c6, "cinema6:delusion-enhanced-basic-and-ultimate-damage")
    c6_effect = _effect(c6_rule)
    assert isinstance(c6_effect, ModifierEffect)
    assert c6_effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert c6_effect.result.value.value == pytest.approx(0.40)
    template_filters = next(
        item for item in c6_effect.rule.filters if isinstance(item, AnyFilter)
    )
    assert {str(item.template_id) for item in template_filters.filters if isinstance(item, EventTemplateIdFilter)} == {
        "template:character:1501:basic-absolute-pitch-enhanced:main",
        "template:character:1501:ultimate-energy-full:main",
    }
    assert effective_skill_level(config, SkillGroup.ULTIMATE) == 16
    assert effective_skill_level(AriaCompileConfig(cinema_level=3), SkillGroup.ULTIMATE) == 14
    assert len(raw.core_levels) == 7


def test_ordinary_anomaly_and_disorder_are_static_with_user_selected_remaining_time() -> None:
    _, definition = _definition()
    corrosion = _entry(definition, "ether-corruption")
    assert corrosion.multiplier_relation.value == "unit-repeat"
    assert corrosion.multiplier_variants[0].repeat_count == 20
    assert _resolved_multiplier(corrosion) == pytest.approx(0.625)
    assert corrosion.main_damage_event.damage_type is DamageType.ANOMALY
    assert corrosion.main_damage_event.damage_subtype is DamageSubtype.ATTRIBUTE_ANOMALY
    assert corrosion.main_damage_event.element is Element.ETHER

    disorder = _entry(definition, "ether-disorder")
    variant = disorder.multiplier_variants[0]
    assert _resolved_multiplier(disorder) == pytest.approx(4.5)
    assert variant.parameter_base_value == pytest.approx(4.5)
    assert variant.parameter_coefficient == pytest.approx(0.625)
    parameter = definition.scenario_parameters[0]
    assert parameter.value == 20
    assert parameter.minimum == 0
    assert parameter.maximum == 20

    _, eligible = _definition(AriaCompileConfig(additional_ability_eligible=True))
    eligible_parameter = eligible.scenario_parameters[0]
    assert eligible_parameter.value == 26
    assert eligible_parameter.maximum == 26


def _aria_static_payload(
    move_entry_id: str,
    *,
    extra_enabled: bool,
    parameter_values: dict[str, int] | None = None,
) -> dict[str, object]:
    aria = str(ARIA_ID)
    anby = "character:1011"
    team = [aria, anby]
    stats = {
        "hp": 10000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
    }
    return {
        "primary_character_id": aria,
        "current_operator": aria,
        "supporting_character_ids": [anby],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            aria: {"core_level": 7, "cinema_level": 0},
            anby: {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {},
        "parameter_values": parameter_values or {},
        "character_builds": {
            aria: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {"ether": 0.0},
                },
            },
            anby: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {"electric": 0.0},
                },
            },
        },
        "enemy": {
            "enemy_id": "enemy:aria-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ether": 0.0, "electric": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": (
            ["rule:character:1501:extra-ability:ether-corrosion-duration"]
            if extra_enabled
            else []
        ),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def test_extra_ability_duration_and_full_corrosion_follow_enabled_rule() -> None:
    corrosion_entry = "move-entry:character:1501:ether-corruption"
    off = calculate_payload(_aria_static_payload(corrosion_entry, extra_enabled=False))
    on = calculate_payload(_aria_static_payload(corrosion_entry, extra_enabled=True))

    assert off["totals"]["expected"]["complete"] is True
    assert on["totals"]["expected"]["complete"] is True
    assert off["events"][0]["repeat_count"] == 20
    assert on["events"][0]["repeat_count"] == 26

    disorder_entry = "move-entry:character:1501:ether-disorder"
    disorder_parameter = "parameter:aria:ether-disorder-remaining-half-seconds"
    disorder_off = calculate_payload(
        _aria_static_payload(disorder_entry, extra_enabled=False)
    )
    disorder_on = calculate_payload(
        _aria_static_payload(disorder_entry, extra_enabled=True)
    )
    disorder_too_long = calculate_payload(
        _aria_static_payload(
            disorder_entry,
            extra_enabled=False,
            parameter_values={disorder_parameter: 26},
        )
    )

    assert disorder_off["totals"]["expected"]["complete"] is True
    assert disorder_on["totals"]["expected"]["complete"] is True
    assert _event_breakdown_value(disorder_off["events"][0], "disorder.total-multiplier") == pytest.approx(17.0)
    assert _event_breakdown_value(disorder_on["events"][0], "disorder.total-multiplier") == pytest.approx(20.75)
    assert disorder_too_long["events"][0]["modes"]["expected"]["status"] == "blocked"
    assert disorder_too_long["totals"]["expected"]["complete"] is False


def _aria_c1_discharge_api_payload(
    *,
    cinema_rule_enabled: bool,
    source_character_id: str,
) -> dict[str, object]:
    aria = str(ARIA_ID)
    jane = "character:1261"
    team = [aria, jane]
    stats = {
        "hp": 10000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.99,
        "crit_damage": 0.5,
        "anomaly_mastery": 101.0,
        "anomaly_proficiency": 90.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
    }
    enabled_rules = [
        "rule:character:1501:core:anomaly-discharge",
        "rule:character:1261:core:gnawing-strong-anomaly-crit",
    ]
    if cinema_rule_enabled:
        enabled_rules.append(
            "rule:character:1501:cinema1:discharge-independent-crit"
        )
    return {
        "primary_character_id": aria,
        "current_operator": aria,
        "supporting_character_ids": [jane],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": "move-entry:character:1501:basic-absolute-pitch-charge-3",
        "compile_configs": {
            aria: {"core_level": 7, "cinema_level": 1},
            jane: {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {
            "condition:aria:third-charge-anomaly-hit": True,
            "condition:jane-doe:gnawing-active": True,
        },
        "parameter_values": {},
        "character_builds": {
            aria: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {"ether": 0.0},
                },
            },
            jane: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "anomaly_mastery": 90.0,
                    "element_damage_bonus": {"physical": 0.0},
                },
            },
        },
        "enemy": {
            "enemy_id": "enemy:aria-c1-api-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ether": 0.0, "physical": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": enabled_rules,
        "discharge_anomaly_source": {
            "source_character_id": source_character_id,
            "element": "physical" if source_character_id == jane else "ether",
        },
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _api_discharge_event(payload: dict[str, object]) -> dict[str, object]:
    response = api_client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    return next(
        event for event in body["events"] if event["damage_subtype"] == "discharge"
    )


def _crit_breakdown_value(event: dict[str, object], node: str) -> float:
    details = event["modes"]["expected"]["calculation_breakdown"]
    return next(float(item["value"]) for item in details if item["node"] == node)


def test_c1_discharge_crit_override_and_record_fallback_through_api() -> None:
    c1_event = _api_discharge_event(
        _aria_c1_discharge_api_payload(
            cinema_rule_enabled=True,
            source_character_id=str(ARIA_ID),
        )
    )
    assert c1_event["crit_capability"] == "anomaly-independent"
    assert c1_event["modes"]["expected"]["status"] == "calculated"
    assert _crit_breakdown_value(c1_event, "anomaly.discharge.crit-rate-override") == pytest.approx(0.255)
    assert _crit_breakdown_value(c1_event, "anomaly.discharge.crit-damage-override") == pytest.approx(0.25)
    assert _crit_breakdown_value(c1_event, "anomaly.discharge.crit-region") == pytest.approx(1.06375)

    ordinary_fallback = _api_discharge_event(
        _aria_c1_discharge_api_payload(
            cinema_rule_enabled=False,
            source_character_id=str(ARIA_ID),
        )
    )
    assert ordinary_fallback["crit_capability"] == "none"
    assert ordinary_fallback["modes"]["expected"]["status"] == "calculated"

    jane_fallback = _api_discharge_event(
        _aria_c1_discharge_api_payload(
            cinema_rule_enabled=False,
            source_character_id="character:1261",
        )
    )
    assert jane_fallback["crit_capability"] == "anomaly-independent"
    assert jane_fallback["modes"]["expected"]["status"] == "calculated"
    assert _crit_breakdown_value(jane_fallback, "anomaly.discharge.crit-region") == pytest.approx(1.272)


def _aria_variant_discharge_api_payload(
    source_character_id: str,
    source_element: str,
) -> dict[str, object]:
    aria = str(ARIA_ID)
    team = [aria, source_character_id]
    stats = {
        "hp": 10000.0,
        "attack": 1400.0,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
    }
    payload = {
        "primary_character_id": aria,
        "current_operator": aria,
        "supporting_character_ids": [source_character_id],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": "move-entry:character:1501:basic-absolute-pitch-charge-3",
        "compile_configs": {
            aria: {"core_level": 7, "cinema_level": 0},
            source_character_id: {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {"condition:aria:third-charge-anomaly-hit": True},
        "parameter_values": {},
        "character_builds": {
            aria: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {"ether": 0.0},
                },
            },
            source_character_id: {
                "level": 60,
                "out_of_combat_stats": {
                    **stats,
                    "element_damage_bonus": {source_element: 0.0},
                },
            },
        },
        "enemy": {
            "enemy_id": f"enemy:aria-{source_element.replace(':', '-')}-api-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ether": 0.0, source_element: 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": ["rule:character:1501:core:anomaly-discharge"],
        "discharge_anomaly_source": {
            "source_character_id": source_character_id,
            "element": source_element,
        },
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }
    return payload


@pytest.mark.parametrize(
    ("source_character_id", "source_element", "expected_ratio"),
    (
        ("character:1371", "ether:xuanmo", 2.475),
        ("character:1091", "ice:lieshuang", 0.324),
        ("character:1261", "physical", 0.225),
    ),
)
def test_aria_discharge_uses_real_source_family_ratio_through_api(
    source_character_id: str,
    source_element: str,
    expected_ratio: float,
) -> None:
    event = _api_discharge_event(
        _aria_variant_discharge_api_payload(source_character_id, source_element)
    )

    assert event["element"] == source_element
    assert event["modes"]["expected"]["status"] == "calculated"
    assert _crit_breakdown_value(event, "discharge.proficiency-multiplier") == pytest.approx(expected_ratio)
