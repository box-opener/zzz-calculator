from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.nangongyu import (
    NANGONGYU_ID,
    NangongYuCompileConfig,
    compile_nangongyu,
    load_raw_record,
)
from core.application.rules import RuleEligibility
from core.presentation.calculation_service import calculate_payload
from core.application.characters.templates import (
    DischargeDamageEventTemplate,
    PolarDisorderDamageEventTemplate,
)
from core.types import (
    AnyFilter,
    BASE_ELEMENT_BY_ELEMENT,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageDealerIdentityFilter,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    DynamicIdentity,
    EffectTarget,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    NotCondition,
    PanelStatDerivedValue,
    Resolved,
    RuleStackCondition,
    ScenarioParameterDerivedValue,
    ScenarioParameterRangeCondition,
    SkillGroup,
    DamageSubtype,
    DamageSubtypeFilter,
    EnemyStateFilter,
    StateId,
    UnresolvedEffect,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "core" / "data" / "characters" / "nangongyu.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1511.json"
_VOICE_STACKS = "parameter:character:1511:voice-stacks"


def _raw():
    return load_raw_record(json.loads(SOURCE_PATH.read_text(encoding="utf-8")))


def _definition(config: NangongYuCompileConfig | None = None):
    raw = _raw()
    return raw, compile_nangongyu(config or NangongYuCompileConfig(), raw)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1511:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _rule(definition, key: str):
    rule_id = f"rule:character:1511:{key}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _modifier(rule, effect_id: str | None = None) -> ModifierEffect:
    modifiers = tuple(item for item in rule.effects if isinstance(item, ModifierEffect))
    if effect_id is not None:
        modifiers = tuple(item for item in modifiers if str(item.rule.effect_id) == effect_id)
    assert modifiers
    return modifiers[0]


def _api_payload(
    move_entry_id: str,
    *,
    primary: str = "character:1511",
    supporting: tuple[str, ...] = ("character:1221",),
    cinema: int = 0,
    conditions: dict | None = None,
    parameters: dict | None = None,
    enabled_rules: tuple[str, ...] = (),
    enemy_stunned: bool = False,
    polar_source: dict | None = None,
    discharge_source: dict | None = None,
) -> dict:
    team = (primary, *supporting)
    payload = {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": {
            character_id: {
                "core_level": 7,
                "cinema_level": cinema if character_id == "character:1511" else 0,
            }
            for character_id in team
        },
        "character_builds": {
            character_id: {
                "level": 60,
                "build_mode": "equipment-build",
                "drive_discs": [],
            }
            for character_id in team
        },
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled_rules),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "enemy": {
            "enemy_id": "enemy:nangong-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": enemy_stunned,
        },
    }
    if polar_source is not None:
        payload["polarity_anomaly_source"] = polar_source
    if discharge_source is not None:
        payload["discharge_anomaly_source"] = discharge_source
    return payload


def _resolved_multiplier(entry) -> float:
    multiplier = entry.multiplier_variants[0].multiplier
    assert isinstance(multiplier, FixedMultiplier)
    assert isinstance(multiplier.value, Resolved)
    return multiplier.value.value


def test_source_identity_provenance_and_reviewed_charge_curves() -> None:
    raw, definition = _definition()
    assert raw.source_version == SOURCE_VERSION
    assert raw.source_url == SOURCE_URL
    assert raw.character_id == NANGONGYU_ID
    assert raw.name == "南宫羽"
    assert definition.role is CharacterRole.STUN
    assert definition.base_element is Element.ETHER

    charge = next(item for item in raw.moves if item.name == "普通攻击：可爱地雷飞天撞")
    cooperative_curve = next(
        item for item in charge.parameters if item.name == "三段伤害倍率（协同）"
    )
    expected = sum(
        cooperative_curve.value_for_level(12, source_id) / 100.0
        for source_id in ("1511006", "1511018")
    )
    cooperative_entry = _entry(definition, "basic-charge-strike-3-cooperative")
    assert _resolved_multiplier(cooperative_entry) == pytest.approx(expected)
    assert _resolved_multiplier(cooperative_entry) == pytest.approx(11.76)
    assert cooperative_entry.stage_index is None
    assert _entry(definition, "basic-charge-strike-1").stage_index == 1
    assert _entry(definition, "basic-charge-strike-2").stage_index == 2
    assert _entry(definition, "basic-charge-strike-3").stage_index == 3


def test_default_core_uses_proficiency_and_initial_mastery_threshold_correctly() -> None:
    _, definition = _definition()
    core = _rule(definition, "core:mastery-and-impact")
    proficiency = _modifier(
        core,
        "effect:character:1511:core:anomaly-mastery",
    )
    assert proficiency.result.modifier_path is (
        CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS
    )
    assert proficiency.result.value == Resolved(120.0)

    impact = _modifier(core, "effect:character:1511:core:impact-from-initial-anomaly-mastery")
    assert impact.result.modifier_path is CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS
    assert isinstance(impact.result.value, PanelStatDerivedValue)
    assert impact.result.value.source_node is CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY
    assert impact.result.value.threshold == Resolved(110.0)
    assert impact.result.value.step_size == Resolved(1.0)
    assert not any(
        isinstance(effect, ModifierEffect)
        and effect.result.modifier_path
        in {
            CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
            CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS,
        }
        for rule in definition.rule_items
        for effect in rule.effects
    )

    ether_disorder = _entry(definition, "ether-disorder")
    disorder_multiplier = ether_disorder.multiplier_variants[0]
    assert disorder_multiplier.multiplier == FixedMultiplier(Resolved(4.5))
    assert disorder_multiplier.parameter_base_value == 4.5
    assert disorder_multiplier.parameter_coefficient == 0.625
    assert "450% + floor(t/0.5)" in ether_disorder.original_text

    c4 = _rule(compile_nangongyu(NangongYuCompileConfig(cinema_level=4), _raw()), "cinema4:anomaly-mastery")
    c4_effect = _modifier(c4)
    assert c4_effect.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS
    assert c4_effect.result.value == Resolved(40.0)


def test_core_ratio_source_curves_are_stable_across_all_core_levels() -> None:
    low = compile_nangongyu(NangongYuCompileConfig(core_level=1), _raw())
    high = compile_nangongyu(NangongYuCompileConfig(core_level=7), _raw())
    assert _modifier(_rule(low, "core:mastery-and-impact")).result.value == Resolved(60.0)
    assert _modifier(_rule(high, "core:mastery-and-impact")).result.value == Resolved(120.0)
    assert _modifier(_rule(low, "core:team-current-damage-bonus")).result.value == Resolved(0.13)
    assert _modifier(_rule(high, "core:team-current-damage-bonus")).result.value == Resolved(0.25)
    expected_source_rates = (7.2, 3.6, 9.0, 0.63, 0.9, 0.36)
    for definition in (low, high):
        templates = tuple(
            item
            for item in definition.damage_event_templates
            if isinstance(item, DischargeDamageEventTemplate)
        )
        assert len(templates) == 1
        assert templates[0].source_multiplier_by_element == tuple(
            zip(
                (Element.ETHER, Element.ELECTRIC, Element.FIRE, Element.PHYSICAL, Element.ICE, Element.WIND),
                expected_source_rates,
            )
        )
        normal = _rule(definition, "core:voice-discharge")
        for effect in normal.effects:
            assert isinstance(effect, ModifierEffect)
            assert isinstance(effect.result.value, ScenarioParameterDerivedValue)
            assert effect.result.value.base == Resolved(1.0)
            assert effect.result.value.coefficient == Resolved(0.25)
            assert effect.result.value.parameter_id == _VOICE_STACKS


def test_voice_discharge_is_one_explicit_dynamic_query_not_anomaly_event_child() -> None:
    _, definition = _definition(NangongYuCompileConfig(cinema_level=6))
    templates = tuple(
        item
        for item in definition.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
    )
    assert len(templates) == 1
    template = templates[0]
    assert template.source_multiplier_by_element == (
        (Element.ETHER, 7.2),
        (Element.ELECTRIC, 3.6),
        (Element.FIRE, 9.0),
        (Element.PHYSICAL, 0.63),
        (Element.ICE, 0.9),
        (Element.WIND, 0.36),
    )
    assert template.history_record_source is None
    assert template.multiplier_from_source_event is False
    assert template.ref.skill_group is None
    assert not template.ref.damage_tags

    entry = _entry(definition, "core:voice-discharge")
    assert entry.main_damage_event == template.ref
    assert entry.skill_group is None
    assert not entry.damage_tags
    assert entry.condition_ids == (
        "condition:character:1511:voice-discharge-ready",
        "condition:character:1511:target-has-active-anomaly",
    )
    assert "所选原异常记录" in entry.display_name
    assert "不由普通异常事件自动触发" in entry.original_text
    assert not any(
        isinstance(effect, EventCreationEffect)
        and effect.result.event_template_id == template.ref.template_id
        for item in definition.rule_items
        for effect in item.effects
    )


def test_voice_discharge_stack_ratios_and_c2_are_relative_to_selected_source_record() -> None:
    _, definition = _definition(NangongYuCompileConfig(cinema_level=2))
    template = next(
        item
        for item in definition.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
    )
    normal = _rule(definition, "core:voice-discharge")
    assert normal.stack_count == normal.stack_min == normal.stack_max == 1
    normal_guard = _rule(definition, "core:voice-discharge-disabled-guard")
    normal_unresolved = next(
        item for item in normal_guard.effects if isinstance(item, UnresolvedEffect)
    )
    assert isinstance(normal_unresolved.rule.condition, NotCondition)
    assert isinstance(normal_unresolved.rule.condition.condition, RuleStackCondition)
    assert normal_unresolved.rule.condition.condition.rule_item_id == str(normal.rule_id)
    c2 = _rule(definition, "cinema2:normal-voice-ratio")
    assert c2.eligibility is RuleEligibility.ELIGIBLE
    assert c2.condition_not_ids == ("condition:character:1511:voice-changed-mode",)
    for element in (Element.ETHER, Element.ELECTRIC, Element.FIRE, Element.PHYSICAL, Element.ICE, Element.WIND):
        suffix = element.value.replace(":", "-")
        normal_effect = _modifier(
            normal,
            f"effect:character:1511:core:voice-discharge:stack-ratio:{suffix}",
        )
        c2_effect = _modifier(
            c2,
            f"effect:character:1511:cinema2:normal-voice-ratio:{suffix}",
        )
        assert isinstance(normal_effect.result.value, ScenarioParameterDerivedValue)
        assert normal_effect.result.value.base == Resolved(1.0)
        assert normal_effect.result.value.coefficient == Resolved(0.25)
        assert isinstance(c2_effect.result.value, ScenarioParameterDerivedValue)
        assert c2_effect.result.value.base == Resolved(0.0)
        assert c2_effect.result.value.coefficient == Resolved(0.10)
        assert all(
            any(
                isinstance(item, EventTemplateIdFilter)
                and item.template_id == template.ref.template_id
                for item in effect.rule.filters
            )
            for effect in (normal_effect, c2_effect)
        )
        family_scope = next(
            item
            for item in normal_effect.rule.filters
            if isinstance(item, (AnyFilter, ElementFilter))
        )
        actual_family = (
            {item.element for item in family_scope.filters}
            if isinstance(family_scope, AnyFilter)
            else {family_scope.element}
        )
        assert actual_family == {
            candidate
            for candidate, base in BASE_ELEMENT_BY_ELEMENT.items()
            if base is element
        }

    voice_stacks = next(
        item for item in definition.scenario_parameters if item.parameter_id == _VOICE_STACKS
    )
    assert voice_stacks.minimum == 1
    assert voice_stacks.maximum == 4


def test_cinema6_changed_voice_uses_relative_base_and_locked_disable_guard() -> None:
    _, c0 = _definition()
    mode = next(
        item
        for item in c0.scenario_conditions
        if str(item.condition_id) == "condition:character:1511:voice-changed-mode"
    )
    assert mode.value is False
    assert mode.resolution.value == "static"
    assert _rule(c0, "cinema6:changed-voice-discharge").eligibility is RuleEligibility.INELIGIBLE
    assert _rule(c0, "core:voice-discharge").condition_not_ids == (mode.condition_id,)

    _, c6 = _definition(NangongYuCompileConfig(cinema_level=6))
    mode6 = next(item for item in c6.scenario_conditions if item.condition_id == mode.condition_id)
    assert mode6.resolution.value == "user-selected"
    changed = _rule(c6, "cinema6:changed-voice-discharge")
    assert changed.eligibility is RuleEligibility.ELIGIBLE
    assert mode.condition_id in changed.condition_ids
    assert changed.stack_count == changed.stack_min == changed.stack_max == 1
    normal_rates = (7.2, 3.6, 9.0, 0.63, 0.9, 0.36)
    changed_rates = (8.0, 4.0, 10.0, 0.7, 1.0, 0.4)
    elements = (Element.ETHER, Element.ELECTRIC, Element.FIRE, Element.PHYSICAL, Element.ICE, Element.WIND)
    for element, normal, changed_rate in zip(elements, normal_rates, changed_rates):
        suffix = element.value.replace(":", "-")
        effect = _modifier(
            changed,
            f"effect:character:1511:cinema6:changed-voice-discharge:stack-ratio:{suffix}",
        )
        k = changed_rate / normal
        assert isinstance(effect.result.value, ScenarioParameterDerivedValue)
        assert effect.result.value.parameter_id == _VOICE_STACKS
        assert effect.result.value.base == Resolved(k)
        assert effect.result.value.coefficient == Resolved(k * 0.25)

    guard = _rule(c6, "cinema6:changed-voice-disabled-guard")
    unresolved = next(item for item in guard.effects if isinstance(item, UnresolvedEffect))
    assert guard.condition_ids == changed.condition_ids
    assert isinstance(unresolved.rule.condition, NotCondition)
    assert isinstance(unresolved.rule.condition.condition, RuleStackCondition)
    assert unresolved.rule.condition.condition.rule_item_id == str(changed.rule_id)


def test_current_support_scopes_and_exact_polarity_sources_are_preserved() -> None:
    _, definition = _definition(
        NangongYuCompileConfig(cinema_level=2, additional_ability_eligible=True, aria_in_team=True)
    )
    current_bonus = _rule(definition, "core:team-current-damage-bonus")
    effect = _modifier(current_bonus)
    assert effect.rule.target is EffectTarget.TEAM
    assert effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert effect.result.value == Resolved(0.25)
    assert current_bonus.condition_ids == ("condition:character:1511:core-status-active",)
    assert not effect.rule.filters

    c1 = _rule(compile_nangongyu(NangongYuCompileConfig(cinema_level=1), _raw()), "cinema1:resistance-reduction")
    assert _modifier(c1).rule.target is EffectTarget.ENEMY
    assert _modifier(c1).result.modifier_path is CalculationNode.ENEMY_RESISTANCE_REDUCTION
    assert c1.condition_ids == ("condition:character:1511:cinema1-resistance-reduction-active",)

    stumble = _rule(definition, "cinema2:stumble-vulnerability")
    assert _modifier(stumble).result.modifier_path is CalculationNode.ENEMY_STUN_VULNERABILITY
    assert _modifier(stumble).result.value == Resolved(0.30)
    assert stumble.condition_ids == ("condition:character:1511:stumble-active",)

    c2 = _rule(definition, "cinema2:chain-polar-disorder")
    creation = next(item for item in c2.effects if isinstance(item, EventCreationEffect))
    assert any(isinstance(item, DamageDealerIdentityFilter) and item.identity is DynamicIdentity.CURRENT_OPERATOR for item in creation.rule.filters)
    assert any(isinstance(item, DamageTypeFilter) and item.damage_type is DamageType.DIRECT for item in creation.rule.filters)
    assert any(isinstance(item, DamageTagFilter) and item.damage_tag is DamageTag.CHAIN_ATTACK for item in creation.rule.filters)
    assert any(isinstance(item, EnemyStateFilter) and item.state_id == StateId("state:enemy:stunned") for item in creation.rule.filters)
    chain_event = next(
        item
        for item in definition.damage_event_templates
        if isinstance(item, PolarDisorderDamageEventTemplate)
        and str(item.ref.template_id)
        == "template:character:1511:cinema2:chain-polar-disorder"
    )
    assert chain_event.base_polarity_multiplier == 0.25
    assert chain_event.anomaly_proficiency_coefficient == 0.0

    extra = _rule(definition, "extra-ability:polar-disorder")
    extra_creation = next(item for item in extra.effects if isinstance(item, EventCreationEffect))
    assert isinstance(extra_creation.rule.condition, ScenarioParameterRangeCondition)
    assert extra_creation.rule.condition.parameter_id == "parameter:character:1511:dance-all-night-stacks"
    assert extra_creation.rule.condition.minimum == 1
    assert any(
        isinstance(item, EventTemplateIdFilter)
        and str(item.template_id) == "template:character:1511:ex-special:main"
        for item in extra_creation.rule.filters[2].filters
    )
    assert definition.scenario_parameters[1].parameter_id == _VOICE_STACKS
    assert any(item.parameter_id == "parameter:character:1511:dance-all-night-stacks" for item in definition.scenario_parameters)

    aria = _rule(definition, "extra-ability:aria-polar-disorder")
    aria_creation = next(item for item in aria.effects if isinstance(item, EventCreationEffect))
    source_ids = {
        str(item.template_id)
        for item in aria_creation.rule.filters[2].filters
        if isinstance(item, EventTemplateIdFilter)
    }
    assert source_ids == {
        "template:character:1501:basic-absolute-pitch-charge-3:main",
        "template:character:1501:basic-absolute-pitch-charge-3-cooperative:main",
        "template:character:1501:basic-absolute-pitch-enhanced:main",
    }
    assert any("aria-full-participation" in str(value) for value in aria.condition_ids)


def test_cinema3_and_5_skill_levels_include_ultimate_and_cap_at_16() -> None:
    config = NangongYuCompileConfig(
        cinema_level=5,
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 15),),
    )
    assert effective_skill_level(config, SkillGroup.ULTIMATE) == 16
    assert effective_skill_level(config, SkillGroup.BASIC_ATTACK) == 16


def _api_breakdown(event: dict, node: str, mode: str = "expected") -> float:
    values = {
        item["node"]: item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
    }
    assert values[node] is not None
    return values[node]


def test_voice_discharge_api_preserves_normal_c2_and_c6_source_ratios() -> None:
    common_conditions = {
        "condition:character:1511:voice-discharge-ready": True,
        "condition:character:1511:target-has-active-anomaly": True,
    }
    stacks = {"parameter:character:1511:voice-stacks": 4}
    core_rule = "rule:character:1511:core:voice-discharge"

    normal = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            conditions=common_conditions,
            parameters=stacks,
            enabled_rules=(core_rule,),
            enemy_stunned=True,
        )
    )
    assert normal["totals"]["expected"]["complete"] is True
    normal_event = next(item for item in normal["events"] if item["damage_type"] == "anomaly")
    assert _api_breakdown(normal_event, "anomaly.discharge.total-multiplier") == pytest.approx(9.0)
    assert normal_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1511:ether"
    )

    c2_rule = "rule:character:1511:cinema2:normal-voice-ratio"
    c2 = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            cinema=2,
            conditions=common_conditions,
            parameters=stacks,
            enabled_rules=(core_rule, c2_rule),
            enemy_stunned=True,
            discharge_source={"source_character_id": "character:1221", "element": "electric"},
        )
    )
    assert c2["totals"]["expected"]["complete"] is True
    c2_event = next(item for item in c2["events"] if item["damage_type"] == "anomaly")
    assert c2_event["element"] == "electric"
    assert c2_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1221:electric"
    )
    assert _api_breakdown(c2_event, "anomaly.discharge.total-multiplier") == pytest.approx(10.8)

    c2_disabled = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            cinema=2,
            conditions=common_conditions,
            parameters=stacks,
            enabled_rules=(core_rule,),
            enemy_stunned=True,
        )
    )
    assert c2_disabled["totals"]["expected"]["complete"] is True
    c2_disabled_event = next(
        item for item in c2_disabled["events"] if item["damage_type"] == "anomaly"
    )
    assert _api_breakdown(
        c2_disabled_event,
        "anomaly.discharge.total-multiplier",
    ) == pytest.approx(9.0)

    c6 = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            cinema=6,
            conditions={
                **common_conditions,
                "condition:character:1511:voice-changed-mode": True,
            },
            parameters={"parameter:character:1511:voice-stacks": 1},
            enabled_rules=(
                core_rule,
                "rule:character:1511:cinema6:changed-voice-discharge",
            ),
            enemy_stunned=True,
        )
    )
    assert c6["totals"]["expected"]["complete"] is True
    c6_event = next(item for item in c6["events"] if item["damage_type"] == "anomaly")
    assert _api_breakdown(c6_event, "anomaly.discharge.total-multiplier") == pytest.approx(6.25)


def test_voice_discharge_api_inherits_janes_selected_record_crit_once() -> None:
    payload = _api_payload(
        "move-entry:character:1511:core:voice-discharge",
        supporting=("character:1261",),
        conditions={
            "condition:character:1511:voice-discharge-ready": True,
            "condition:character:1511:target-has-active-anomaly": True,
            "condition:jane-doe:gnawing-active": True,
        },
        parameters={"parameter:character:1511:voice-stacks": 4},
        enabled_rules=(
            "rule:character:1511:core:voice-discharge",
            "rule:character:1261:core:gnawing-strong-anomaly-crit",
        ),
        enemy_stunned=True,
        discharge_source={"source_character_id": "character:1261", "element": "physical"},
    )
    payload["character_builds"]["character:1261"] = {
        "level": 60,
        "out_of_combat_stats": {
            "hp": 10000.0,
            "attack": 1400.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.99,
            "crit_damage": 0.5,
            "anomaly_mastery": 90.0,
            "anomaly_proficiency": 90.0,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": 0.0},
        },
    }
    result = calculate_payload(payload)
    assert result["totals"]["expected"]["complete"] is True
    event = next(item for item in result["events"] if item["damage_type"] == "anomaly")
    assert event["crit_capability"] == "anomaly-independent"
    assert event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1261:physical"
    )
    assert _api_breakdown(event, "anomaly.discharge.crit-region") == pytest.approx(1.272)


@pytest.mark.parametrize(
    ("cinema", "changed", "stunned", "layers", "expected_complete"),
    (
        (0, False, True, 1, False),
        (0, False, True, 4, True),
        (0, False, False, 1, True),
        (6, True, True, 1, True),
        (6, True, False, 1, False),
        (0, True, True, 1, False),
    ),
)
def test_voice_discharge_api_blocks_impossible_mode_or_stun_stack_combinations(
    cinema: int,
    changed: bool,
    stunned: bool,
    layers: int,
    expected_complete: bool,
) -> None:
    conditions = {
        "condition:character:1511:voice-discharge-ready": True,
        "condition:character:1511:target-has-active-anomaly": True,
    }
    if changed or cinema >= 6:
        conditions["condition:character:1511:voice-changed-mode"] = changed
    enabled = (
        "rule:character:1511:cinema6:changed-voice-discharge",
    ) if changed and cinema == 6 else (
        "rule:character:1511:core:voice-discharge",
    )
    result = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            cinema=cinema,
            conditions=conditions,
            parameters={"parameter:character:1511:voice-stacks": layers},
            enabled_rules=enabled,
            enemy_stunned=stunned,
        )
    )
    assert result["totals"]["expected"]["complete"] is expected_complete


@pytest.mark.parametrize(
    ("cinema", "changed_mode", "layers"),
    ((0, False, 4), (6, True, 1)),
)
def test_voice_discharge_api_does_not_bypass_disabled_selected_mode_rule(
    cinema: int,
    changed_mode: bool,
    layers: int,
) -> None:
    conditions = {
        "condition:character:1511:voice-discharge-ready": True,
        "condition:character:1511:target-has-active-anomaly": True,
    }
    if changed_mode:
        conditions["condition:character:1511:voice-changed-mode"] = True
    result = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            cinema=cinema,
            conditions=conditions,
            parameters={"parameter:character:1511:voice-stacks": layers},
            enabled_rules=(),
            enemy_stunned=True,
        )
    )
    assert result["totals"]["expected"]["complete"] is False


def test_disabled_voice_rule_keeps_stale_source_selection_local_partial():
    result = calculate_payload(
        _api_payload(
            "move-entry:character:1511:core:voice-discharge",
            conditions={
                "condition:character:1511:voice-discharge-ready": True,
                "condition:character:1511:target-has-active-anomaly": True,
            },
            parameters={"parameter:character:1511:voice-stacks": 4},
            enabled_rules=(),
            enemy_stunned=True,
            discharge_source={
                "source_character_id": "character:1261",
                "element": "physical",
            },
        )
    )
    assert result["totals"]["expected"]["complete"] is False


def test_polar_source_api_accepts_only_matching_team_direct_triggers() -> None:
    active_anomaly = {"condition:character:1511:target-has-active-anomaly": True}
    extra = calculate_payload(
        _api_payload(
            "move-entry:character:1511:ex-special",
            conditions=active_anomaly,
            parameters={"parameter:character:1511:dance-all-night-stacks": 2},
            enabled_rules=("rule:character:1511:extra-ability:polar-disorder",),
            enemy_stunned=True,
        )
    )
    assert extra["totals"]["expected"]["complete"] is True
    extra_polar = next(item for item in extra["events"] if item["damage_type"] == "disorder")
    assert extra_polar["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1511:ether"
    )

    selected_polar = calculate_payload(
        _api_payload(
            "move-entry:character:1511:ex-special",
            conditions=active_anomaly,
            parameters={"parameter:character:1511:dance-all-night-stacks": 2},
            enabled_rules=("rule:character:1511:extra-ability:polar-disorder",),
            enemy_stunned=True,
            polar_source={"source_character_id": "character:1221", "element": "electric"},
        )
    )
    assert selected_polar["totals"]["expected"]["complete"] is True
    selected_event = next(
        item for item in selected_polar["events"] if item["damage_type"] == "disorder"
    )
    assert selected_event["element"] == "electric"
    assert selected_event["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1221:electric"
    )

    chain = calculate_payload(
        _api_payload(
            "move-entry:character:1511:chain-attack",
            cinema=2,
            conditions={
                **active_anomaly,
                "condition:character:1511:cinema2-chain-polarity-available": True,
            },
            enabled_rules=("rule:character:1511:cinema2:chain-polar-disorder",),
            enemy_stunned=True,
        )
    )
    assert chain["totals"]["expected"]["complete"] is True
    chain_polar = next(item for item in chain["events"] if item["damage_type"] == "disorder")
    assert chain_polar["modes"]["expected"]["anomaly_record_id"] == (
        "anomaly:static-source:character:1511:ether"
    )

    ordinary_anomaly = calculate_payload(
        _api_payload(
            "move-entry:character:1511:ether-anomaly",
            conditions=active_anomaly,
        )
    )
    assert not any(item["damage_type"] == "disorder" for item in ordinary_anomaly["events"])
    invalid_source = _api_payload(
        "move-entry:character:1511:ether-anomaly",
        conditions=active_anomaly,
        polar_source={"source_character_id": "character:1221", "element": "electric"},
    )
    with pytest.raises(ValueError, match="only valid for Yanagi or a direct hit"):
        calculate_payload(invalid_source)
