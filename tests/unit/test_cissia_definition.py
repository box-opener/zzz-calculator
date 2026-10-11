from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from core.application.characters.cissia import (
    CISSIA_ID,
    CissiaCompileConfig,
    compile_cissia,
    load_raw_record,
)
from core.application.characters.cissia.reviewed import CISSIA_REVIEWED_MAPPING
from core.application.characters.banyue import (
    BANYUE_ID,
    BanYueCompileConfig,
    compile_banyue,
    load_raw_record as load_banyue_raw_record,
)
from core.application.characters.nanoka_compiler import raw_move_index
from core.application.execution.modifiers import _resolve_effect_value
from core.application.execution.modifiers import _resolve_panel_effect_condition
from core.application.execution import MoveCalculationRequest, calculate_move
from core.application.diagnostics import CalculationDiagnostic
from core.application.ids import RuleItemId
from core.data.loader import load_character_record
from core.presentation.registry import compile_registered_definition, registration_for
from core.application.equipment.wengine import SIGNATURE_WENGINE_BY_CHARACTER
from core.application.matching import (
    CharacterMatchProfile,
    EffectMatchContext,
    EffectMatchStatus,
    EffectMatcher,
    EnemyMatchProfile,
)
from core.application.scenario import CalculationScenario, ScenarioRuleStack
from core.types import CharacterStats, InitialCharacterSnapshot, Resolved
from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AnyFilter,
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    BattleStateId,
    CharacterId,
    CalculationContext,
    CharacterSnapshot,
    CalculationNode,
    CharacterRole,
    DamageType,
    DamageTypeFilter,
    DamageEventId,
    DamageEventMetadata,
    Element,
    EnemyId,
    EnemySnapshot,
    EventTemplateIdFilter,
    FixedMultiplier,
    MoveIdFilter,
    NoAnomalyCrit,
    NoCritRule,
    NotFilter,
    PanelStatDerivedValue,
    RuleStackCondition,
    ScenarioParameterRangeCondition,
)
from core.application.rules import RuleEligibility


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "cissia.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1521.json"


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _definition(config: CissiaCompileConfig | None = None):
    raw = load_raw_record(_source_data())
    return raw, compile_cissia(config or CissiaCompileConfig(), raw)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1521:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _rule(definition, key: str):
    rule_id = f"rule:character:1521:{key}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _ratio(modifier) -> float:
    return modifier.result.value.value


def _initial_snapshot(energy_regen: float) -> InitialCharacterSnapshot:
    return InitialCharacterSnapshot(
        character_id=CISSIA_ID,
        level=60,
        initial_stats=CharacterStats(
            hp=Resolved(10000.0),
            attack=Resolved(1000.0),
            defense=Resolved(1000.0),
            impact=Resolved(100.0),
            crit_rate=Resolved(0.05),
            crit_damage=Resolved(0.5),
            anomaly_mastery=Resolved(100.0),
            anomaly_proficiency=Resolved(100.0),
            penetration_rate=Resolved(0.0),
            penetration_flat=Resolved(0.0),
            energy_regen=Resolved(energy_regen),
        ),
    )


def _execution_request(
    definition,
    entry_key: str,
    *,
    parameter_values: dict[str, int] | None = None,
    condition_values: dict[str, bool | None] | None = None,
    enabled_rules: tuple[str, ...] = (),
    stacks: tuple[tuple[str, int], ...] = (),
    attack: float = 1000.0,
    current_energy_regen: float = 1.2,
    initial_energy_regen: float | None = None,
) -> MoveCalculationRequest:
    parameter_values = parameter_values or {}
    condition_values = condition_values or {}
    scenario = CalculationScenario(
        scenario_id="cissia-execution-test",
        current_operator=CISSIA_ID,
        conditions=tuple(
            replace(
                item,
                value=condition_values.get(str(item.condition_id), item.value),
            )
            for item in definition.scenario_conditions
        ),
        parameters=tuple(
            replace(item, value=parameter_values[str(item.parameter_id)])
            if str(item.parameter_id) in parameter_values
            else item
            for item in definition.scenario_parameters
        ),
        enabled_rule_item_ids=frozenset(RuleItemId(item) for item in enabled_rules),
        rule_stack_counts=tuple(
            ScenarioRuleStack(RuleItemId(rule_id), value)
            for rule_id, value in stacks
        ),
    )
    enemy_id = EnemyId("enemy:cissia-execution")
    stats = CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(1000.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.0),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(current_energy_regen),
        element_damage_bonus={Element.ELECTRIC: Resolved(0.0)},
    )
    return MoveCalculationRequest(
        definition=definition,
        move_entry_id=_entry(definition, entry_key).entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId("battle:cissia-execution"),
        battle_time=0.0,
        base_character_snapshots=(CharacterSnapshot(CISSIA_ID, 60, stats),),
        initial_character_snapshots=(
            (_initial_snapshot(initial_energy_regen),)
            if initial_energy_regen is not None
            else ()
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=enemy_id,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.ELECTRIC: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(CharacterMatchProfile(CISSIA_ID, CharacterRole.ATTACK),),
        target_profile=EnemyMatchProfile(enemy_id),
    )


def test_core_defense_ignore_uses_initial_energy_regen_not_current_energy_regen() -> None:
    _, definition = _definition(CissiaCompileConfig(core_level=7, cinema_level=1))
    core_rule_id = "rule:character:1521:core:toxin-electric-defense-ignore"
    execution = calculate_move(
        _execution_request(
            definition,
            "basic-snake-kiss",
            condition_values={"condition:cissia:toxin-active-or-recent": True},
            enabled_rules=(
                core_rule_id,
                "rule:character:1521:cinema1:core-defense-ignore-increase",
            ),
            stacks=((core_rule_id, 1),),
            current_energy_regen=100.0,
            initial_energy_regen=1.4,
        )
    )

    assert execution.output.complete
    defense_ignore = [
        item.value.value
        for item in execution.event_traces[0].applied_modifiers
        if item.modifier_path is CalculationNode.DAMAGE_DEFENSE_IGNORE
    ]
    assert defense_ignore == pytest.approx([0.06, 0.024])


def test_cissia_raw_identity_and_provenance_are_preserved() -> None:
    data = _source_data()
    raw = load_raw_record(data)
    definition = compile_cissia(CissiaCompileConfig(), raw)

    assert data["source_version"] == SOURCE_VERSION
    assert data["source_url"] == SOURCE_URL
    assert raw.source_version == SOURCE_VERSION
    assert raw.source_url == SOURCE_URL
    assert raw.character_id == CISSIA_ID
    assert raw.code_name == "Cissia"
    assert raw.name == "希希芙"
    assert raw.rarity == 4
    assert raw.specialty == "强攻"
    assert raw.element == "电属性"
    assert raw.faction == "新艾利都治安局"
    assert raw.icon == "IconRole60"
    assert raw.rarity == 4  # The Nanoka S-rank code used by the catalog adapter.
    registration = registration_for(CISSIA_ID)
    assert registration.catalog.rarity == "S"
    assert registration.catalog.specialty == "attack"
    assert registration.catalog.element == "electric"
    assert SIGNATURE_WENGINE_BY_CHARACTER[CISSIA_ID].__str__() == "wengine:14152"
    assert load_character_record(str(CISSIA_ID))["source_url"] == SOURCE_URL
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert definition.character_id == CISSIA_ID
    assert definition.role is CharacterRole.ATTACK
    assert definition.base_element is Element.ELECTRIC
    assert all(
        item.ref.damage_type is DamageType.DIRECT
        and item.ref.element is Element.ELECTRIC
        for item in definition.damage_event_templates
    )
    assert all(
        "异常" not in entry.display_name and "紊乱" not in entry.display_name
        for entry in definition.move_entries
    )


def test_registered_cissia_extra_ability_uses_stun_or_electric_not_camp() -> None:
    values = {"core_level": 7, "cinema_level": 0}

    stun_team = compile_registered_definition(
        CISSIA_ID,
        values,
        [str(CISSIA_ID), "character:1511"],
    )
    electric_team = compile_registered_definition(
        CISSIA_ID,
        values,
        [str(CISSIA_ID), "character:1221"],
    )
    neither_team = compile_registered_definition(
        CISSIA_ID,
        values,
        [str(CISSIA_ID), "character:1311"],
    )

    assert _rule(stun_team, "extra:toxin-team-crit-damage").eligibility is RuleEligibility.ELIGIBLE
    assert _rule(electric_team, "extra:toxin-team-crit-damage").eligibility is RuleEligibility.ELIGIBLE
    assert _rule(neither_team, "extra:toxin-team-crit-damage").eligibility is RuleEligibility.INELIGIBLE


def test_bone_erosion_retains_1521019_base_and_adds_core_ratio_on_same_event() -> None:
    raw = load_raw_record(_source_data())
    moves = raw_move_index(raw)
    bone_source = next(
        item
        for item in moves["蚀骨"].parameters
        if item.name == "伤害倍率" and item.source_skill_id == "1521019"
    )

    for core_level, source_level in enumerate(raw.core_levels, start=1):
        match = re.search(
            r"\[蚀骨\]额外附加自身(?P<value>[\d.]+)%攻击力",
            re.sub(r"<[^>]*>", "", source_level.description),
        )
        assert match is not None
        expected_extra = float(match.group("value")) / 100.0
        _, definition = _definition(CissiaCompileConfig(core_level=core_level))
        snake_kiss = _entry(definition, "basic-snake-kiss")
        bone_event = snake_kiss.derived_damage_events[0]
        raw_base = bone_source.value_for_level(12, "1521019")
        assert raw_base is not None
        expected_base = raw_base / 100.0
        expected_factor = (expected_base + expected_extra) / expected_base
        assert bone_event.multiplier.value.value == pytest.approx(raw_base / 100.0)

        core_ratio_rule = _rule(definition, "core:bone-erosion-extra-ratio")
        core_ratio_effect = core_ratio_rule.effects[0]
        assert core_ratio_effect.result.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER
        assert core_ratio_effect.result.operation.value == "multiply"
        assert _ratio(core_ratio_effect) == pytest.approx(expected_factor)
        bone_filters = core_ratio_effect.rule.filters[0]
        assert isinstance(bone_filters, AnyFilter)
        assert any(
            isinstance(item, EventTemplateIdFilter)
            and item.template_id == bone_event.template.template_id
            for item in bone_filters.filters
        )
        assert bone_event.multiplier.value.value * _ratio(core_ratio_effect) == pytest.approx(
            expected_base + expected_extra
        )

    # The source's maximum Core line is an additive ratio, not a replacement
    # for the 1521019 move curve or a second copied Bone Erosion event.
    _, definition = _definition(CissiaCompileConfig(core_level=7))
    snake_kiss = _entry(definition, "basic-snake-kiss")
    assert len(snake_kiss.derived_damage_events) == 1
    assert snake_kiss.derived_damage_events[0].multiplier.value.value == pytest.approx(2.544)
    assert _ratio(_rule(definition, "core:bone-erosion-extra-ratio").effects[0]) == pytest.approx(
        (2.544 + 3.35) / 2.544
    )


def test_all_reviewed_main_entries_match_their_raw_level_12_curve_and_id() -> None:
    raw, definition = _definition()
    raw_moves = raw_move_index(raw)
    assert len(CISSIA_REVIEWED_MAPPING.moves) == 13
    assert all(
        spec.source_name != "招架支援：牢饭加餐"
        for spec in CISSIA_REVIEWED_MAPPING.moves
    )

    for spec in CISSIA_REVIEWED_MAPPING.moves:
        entry = _entry(definition, spec.entry_key)
        raw_move = raw_moves[spec.source_name]
        for spec_parameter, variant in zip(spec.parameters, entry.multiplier_variants):
            parameter = next(
                item for item in raw_move.parameters
                if item.name == spec_parameter.parameter_name
            )
            expected = parameter.value_for_level(12, spec_parameter.source_skill_id)
            assert expected is not None, (spec.entry_key, spec_parameter.parameter_name)
            assert variant.multiplier.value.value == pytest.approx(expected / 100.0)
        assert entry.skill_group is spec.skill_group
        assert entry.damage_tags == spec.damage_tags
        assert entry.main_damage_event.element is Element.ELECTRIC


def test_core_initial_energy_regen_defense_ignore_is_continuous_and_c1_scales_full_cap() -> None:
    raw, core7 = _definition(CissiaCompileConfig(core_level=7))
    for core_level, source_level in enumerate(raw.core_levels, start=1):
        core_definition = core7 if core_level == 7 else _definition(
            CissiaCompileConfig(core_level=core_level)
        )[1]
        core_rule = _rule(core_definition, "core:toxin-electric-defense-ignore")
        core_value = core_rule.effects[0].result.value
        assert isinstance(core_value, PanelStatDerivedValue)
        base = float(
            re.search(
                r"电属性伤害无视敌人(?P<value>[\d.]+)%防御力",
                re.sub(r"<[^>]*>", "", source_level.description),
            ).group("value")
        ) / 100.0
        per_step = float(
            re.search(
                r"每超过[\d.]+，额外无视敌人(?P<value>[\d.]+)%防御力",
                re.sub(r"<[^>]*>", "", source_level.description),
            ).group("value")
        ) / 100.0
        cap = float(
            re.search(
                r"至多无视敌人(?P<value>[\d.]+)%防御力",
                re.sub(r"<[^>]*>", "", source_level.description),
            ).group("value")
        ) / 100.0
        assert core_value.source_node is CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN
        assert core_value.base.value == pytest.approx(base)
        assert core_value.coefficient.value == pytest.approx(per_step)
        assert core_value.threshold.value == pytest.approx(1.4)
        assert core_value.step_size.value == pytest.approx(0.12)
        assert core_value.cap_max.value == pytest.approx(cap)
        assert core_rule.stack_count == 1

    core_rule = _rule(core7, "core:toxin-electric-defense-ignore")
    core_effect = core_rule.effects[0]
    resolved_values = []
    for energy_regen in (1.4, 1.46, 2.0, 8.0):
        diagnostics: list[CalculationDiagnostic] = []
        resolved = _resolve_effect_value(
            core_effect,
            (_initial_snapshot(energy_regen),),
            diagnostics,
        )
        assert resolved is not None
        assert not diagnostics
        resolved_values.append(resolved.result.value.value)
    assert resolved_values == pytest.approx((0.06, 0.065, 0.11, 0.25))

    _, c1 = _definition(CissiaCompileConfig(core_level=7, cinema_level=1))
    c1_core_rule = _rule(c1, "cinema1:core-defense-ignore-increase")
    c1_delta = c1_core_rule.effects[0]
    c1_value = c1_delta.result.value
    assert isinstance(c1_value, PanelStatDerivedValue)
    assert c1_value.source_node is CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN
    assert c1_value.base.value == pytest.approx(core_value.base.value * 0.4)
    assert c1_value.coefficient.value == pytest.approx(core_value.coefficient.value * 0.4)
    assert c1_value.threshold.value == core_value.threshold.value
    assert c1_value.step_size.value == core_value.step_size.value
    assert c1_value.cap_max.value == pytest.approx(core_value.cap_max.value * 0.4)
    assert isinstance(c1_delta.rule.condition, RuleStackCondition)
    assert c1_delta.rule.condition.requires_rule_enabled
    assert c1_delta.rule.condition.rule_item_id == str(core_rule.rule_id)
    assert c1_delta.rule.condition.required_value == 1
    assert core_value.cap_max.value + c1_value.cap_max.value == pytest.approx(0.35)
    assert _rule(c1, "cinema1:electric-resistance-ignore").eligibility is RuleEligibility.ELIGIBLE

    diagnostics = []
    resolved_c1_delta = _resolve_effect_value(
        c1_delta,
        (_initial_snapshot(8.0),),
        diagnostics,
    )
    assert resolved_c1_delta is not None
    assert not diagnostics
    assert resolved_c1_delta.result.value.value == pytest.approx(0.10)

    core_rule_id = RuleItemId(str(core_rule.rule_id))
    enabled_scenario = CalculationScenario(
        scenario_id="cissia-c1-core-enabled",
        current_operator=CISSIA_ID,
        enabled_rule_item_ids=frozenset({core_rule_id}),
        rule_stack_counts=(ScenarioRuleStack(core_rule_id, 1),),
    )
    disabled_scenario = CalculationScenario(
        scenario_id="cissia-c1-core-disabled",
        current_operator=CISSIA_ID,
        rule_stack_counts=(ScenarioRuleStack(core_rule_id, 1),),
    )
    assert _resolve_panel_effect_condition(c1_delta, enabled_scenario, (), ())[0] is EffectMatchStatus.MATCHED
    assert _resolve_panel_effect_condition(c1_delta, disabled_scenario, (), ())[0] is EffectMatchStatus.NOT_MATCHED

    c1_resistance_effects = _rule(c1, "cinema1:electric-resistance-ignore").effects
    assert [item.result.value.value for item in c1_resistance_effects] == pytest.approx([0.05, 0.10])
    assert all(item.result.modifier_path is CalculationNode.DAMAGE_RESISTANCE_IGNORE for item in c1_resistance_effects)
    assert any(
        isinstance(item, AnyFilter)
        and any(
            isinstance(nested, EventTemplateIdFilter)
            and nested.template_id
            == _entry(c1, "basic-snake-kiss").derived_damage_events[0].template.template_id
            for nested in item.filters
        )
        for item in c1_resistance_effects[1].rule.filters
    )


def test_ex_special_extra_hit_uses_1521009_and_current_count_0_to_3() -> None:
    raw, definition = _definition()
    ex_raw = raw_move_index(raw)["强化特殊技：毒牙"]
    expected = next(
        item
        for item in ex_raw.parameters
        if item.name == "伤害倍率"
    ).value_for_level(12, "1521009")
    assert expected is not None
    assert definition.scenario_parameters[0].value == 3
    assert definition.scenario_parameters[0].minimum == 0
    assert definition.scenario_parameters[0].maximum == 3

    ex = _entry(definition, "ex-special")
    assert len(ex.derived_damage_events) == 1
    extra_hit = ex.derived_damage_events[0]
    assert extra_hit.multiplier.value.value == pytest.approx(expected / 100.0)
    assert extra_hit.repeat_count_parameter_id is not None
    assert extra_hit.template.skill_group is None
    assert extra_hit.template.damage_tags == frozenset()
    assert extra_hit.template.element is Element.ELECTRIC
    ex_rule = _rule(definition, "skill:ex-special-extra-hit")
    assert ex_rule.effects[0].result.event_template_id == extra_hit.template.template_id
    assert isinstance(ex_rule.effects[0].rule.condition, ScenarioParameterRangeCondition)

    _, zero_count = _definition(CissiaCompileConfig(ex_special_extra_hit_count=0))
    assert zero_count.scenario_parameters[0].value == 0
    assert _entry(zero_count, "ex-special").derived_damage_events[0].skip_when_repeat_count_zero


def test_extra_ability_is_automatic_eligibility_input_and_uses_team_plus_self_scope() -> None:
    _, ineligible = _definition(CissiaCompileConfig(additional_ability_eligible=False))
    ineligible_rule = _rule(ineligible, "extra:toxin-team-crit-damage")
    assert ineligible_rule.eligibility is RuleEligibility.INELIGIBLE
    assert not ineligible_rule.effects

    _, eligible = _definition(
        CissiaCompileConfig(additional_ability_eligible=True, toxin_active_or_recent=True)
    )
    extra = _rule(eligible, "extra:toxin-team-crit-damage")
    assert extra.eligibility is RuleEligibility.ELIGIBLE
    assert extra.condition_ids
    team_effect, self_effect = extra.effects
    assert team_effect.result.value.value == pytest.approx(0.40)
    assert team_effect.rule.target.value == "team"
    assert self_effect.result.value.value == pytest.approx(0.10)
    assert self_effect.rule.target.value == "self"


def test_core_and_cinema_rules_do_not_leak_beyond_unlocked_or_selected_scope() -> None:
    _, c0 = _definition(CissiaCompileConfig())
    assert _rule(c0, "cinema1:core-defense-ignore-increase").eligibility is RuleEligibility.INELIGIBLE
    assert not _rule(c0, "cinema1:core-defense-ignore-increase").effects
    assert _rule(c0, "cinema4:special-bone-erosion").eligibility is RuleEligibility.INELIGIBLE
    assert not _rule(c0, "cinema4:special-bone-erosion").effects
    assert _rule(c0, "cinema6:team-bone-erosion").eligibility is RuleEligibility.INELIGIBLE
    assert not _rule(c0, "cinema6:team-bone-erosion").effects
    assert not any(
        item.parameter_id.endswith("cinema4-awareness-stacks")
        for item in c0.scenario_parameters
    )
    assert not any(
        str(item.condition_id).endswith("cinema6-mark-proc-active")
        for item in c0.scenario_conditions
    )

    _, c4 = _definition(CissiaCompileConfig(cinema_level=4))
    assert _rule(c4, "cinema4:special-bone-erosion").eligibility is RuleEligibility.ELIGIBLE
    assert c4.scenario_parameters[-1].value == 3
    assert _rule(c4, "cinema6:team-bone-erosion").eligibility is RuleEligibility.INELIGIBLE
    c4_raw = load_raw_record(_source_data()).mindscapes[3]
    assert "每消耗1层额外触发1次不消耗[毒素]的特殊[蚀骨]" in re.sub(
        r"<[^>]*>", "", c4_raw.description
    )
    assert _entry(c4, "basic-snake-kiss").derived_damage_events[-1].repeat_count_parameter_id is not None
    c4_child = _entry(c4, "basic-snake-kiss").derived_damage_events[-1].template
    assert c4_child.skill_group is None
    assert c4_child.damage_tags == frozenset()
    assert c4_child.element is Element.ELECTRIC
    assert c4_child.damage_type is DamageType.DIRECT
    raw_bone = next(
        item
        for item in raw_move_index(load_raw_record(_source_data()))["蚀骨"].parameters
        if item.name == "伤害倍率" and item.source_skill_id == "1521019"
        ).value_for_level(14, "1521019")
    assert raw_bone is not None
    assert _entry(c4, "basic-snake-kiss").derived_damage_events[-1].multiplier.value.value == pytest.approx(
        raw_bone / 100.0
    )
    c4_core_effect = _rule(c4, "core:bone-erosion-extra-ratio").effects[0]
    assert any(
        isinstance(item, AnyFilter)
        and any(
            isinstance(nested, EventTemplateIdFilter)
            and nested.template_id == c4_child.template_id
            for nested in item.filters
        )
        for item in c4_core_effect.rule.filters
    )

    _, c2 = _definition(CissiaCompileConfig(cinema_level=2))
    c2_effect = _rule(c2, "cinema2:snake-kiss-damage-bonus").effects[0]
    assert c2_effect.result.value.value == pytest.approx(0.35)
    c2_filter = c2_effect.rule.filters[0]
    assert isinstance(c2_filter, EventTemplateIdFilter)
    assert c2_filter.template_id == _entry(c2, "basic-snake-kiss").main_damage_event.template_id

    _, c3 = _definition(CissiaCompileConfig(cinema_level=3))
    ultimate_raw = next(
        item
        for item in raw_move_index(load_raw_record(_source_data()))["终结技：爬行恐惧"].parameters
        if item.name == "伤害倍率"
    )
    for cinema_level, skill_level in ((3, 14), (5, 16)):
        _, cinema = _definition(CissiaCompileConfig(cinema_level=cinema_level))
        expected = ultimate_raw.value_for_level(skill_level, "1521013")
        assert expected is not None
        assert _entry(cinema, "ultimate").multiplier_variants[0].multiplier.value.value == pytest.approx(
            expected / 100.0
        )

    _, c6 = _definition(CissiaCompileConfig(cinema_level=6, cinema6_mark_proc_active=True))
    c6_rule = _rule(c6, "cinema6:team-bone-erosion")
    assert c6_rule.eligibility is RuleEligibility.ELIGIBLE
    assert len(c6_rule.effects) == 1
    creation = c6_rule.effects[0]
    assert creation.result.event_template_id == c6.independent_derived_damage_events[0].template.template_id
    assert c6.independent_derived_damage_events[0].template.skill_group is None
    assert c6.independent_derived_damage_events[0].template.damage_tags == frozenset()
    assert c6.independent_derived_damage_events[0].template.element is Element.ELECTRIC
    assert c6.independent_derived_damage_events[0].template.damage_type is DamageType.DIRECT
    exclusion = next(
        item
        for item in creation.rule.filters
        if isinstance(item, NotFilter) and isinstance(item.filter, AnyFilter)
    )
    assert isinstance(exclusion.filter, AnyFilter)
    assert any(
        isinstance(item, EventTemplateIdFilter)
        and item.template_id == creation.result.event_template_id
        for item in exclusion.filter.filters
    )
    hit_type_filter = next(
        item
        for item in creation.rule.filters
        if isinstance(item, AnyFilter)
        and any(isinstance(nested, DamageTypeFilter) for nested in item.filters)
    )
    assert {
        item.damage_type
        for item in hit_type_filter.filters
        if isinstance(item, DamageTypeFilter)
    } == {DamageType.DIRECT, DamageType.PENETRATION}
    assert any(
        isinstance(item, NotFilter)
        and isinstance(item.filter, MoveIdFilter)
        and item.filter.move_id is None
        for item in creation.rule.filters
    )
    assert any(
        str(item.condition_id).endswith("cinema6-mark-proc-active")
        for item in c6.scenario_conditions
    )
    assert all(
        ref.template.template_id != creation.result.event_template_id
        for entry in c6.move_entries
        for ref in entry.derived_damage_events
    )


def test_c4_execution_repeats_bone_child_and_core_ratio_resolves_in_damage() -> None:
    _, definition = _definition(CissiaCompileConfig(core_level=7, cinema_level=4))
    enabled = (
        "rule:character:1521:core:bone-erosion-extra-ratio",
        "rule:character:1521:cinema4:special-bone-erosion",
    )
    common = {
        "condition:cissia:snake-shadow-available": True,
    }
    zero = calculate_move(
        _execution_request(
            definition,
            "basic-snake-kiss",
            parameter_values={"parameter:cissia:cinema4-awareness-stacks": 0},
            condition_values=common,
            enabled_rules=enabled,
        )
    )
    max_stacks = calculate_move(
        _execution_request(
            definition,
            "basic-snake-kiss",
            parameter_values={"parameter:cissia:cinema4-awareness-stacks": 3},
            condition_values=common,
            enabled_rules=enabled,
        )
    )

    assert zero.output.complete and max_stacks.output.complete
    assert len(zero.output.events) == 2
    assert len(max_stacks.output.events) == 3
    zero_bone, = zero.output.events[1:]
    base_bone = next(
        item
        for item in max_stacks.output.events[1:]
        if "basic-snake-kiss-bone-erosion" in item.semantic_id
    )
    cinema_bone = next(
        item
        for item in max_stacks.output.events[1:]
        if "cinema4-bone-erosion" in item.semantic_id
    )
    assert zero_bone.damage_type is DamageType.DIRECT
    assert base_bone.damage_type is DamageType.DIRECT
    assert cinema_bone.damage_type is DamageType.DIRECT
    assert zero_bone.repeat_count == 1
    assert base_bone.repeat_count == 1
    assert cinema_bone.repeat_count == 3

    core_modifier = next(
        item
        for item in max_stacks.event_traces[1].event_multiplier_modifiers
        if item.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    bone_source = next(
        item
        for item in raw_move_index(load_raw_record(_source_data()))["蚀骨"].parameters
        if item.name == "伤害倍率" and item.source_skill_id == "1521019"
    )
    base_ratio = bone_source.value_for_level(14, "1521019")
    assert base_ratio is not None
    expected_total_ratio = base_ratio / 100.0 + 3.35
    assert core_modifier.value.value == pytest.approx(
        expected_total_ratio / (base_ratio / 100.0)
    )
    final_skill_multiplier = next(
        item.value.value
        for item in base_bone.result.breakdown
        if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
    )
    assert final_skill_multiplier == pytest.approx(expected_total_ratio)
    assert base_bone.known_value == pytest.approx(zero_bone.known_value)
    assert cinema_bone.known_value == pytest.approx(cinema_bone.result.value * 3)
    assert max_stacks.output.known_total - zero.output.known_total == pytest.approx(
        cinema_bone.known_value
    )


def test_bone_core_execution_uses_effective_raw_curves_at_cinema_0_4_and_6() -> None:
    raw = load_raw_record(_source_data())
    bone_source = next(
        item
        for item in raw_move_index(raw)["蚀骨"].parameters
        if item.name == "伤害倍率" and item.source_skill_id == "1521019"
    )
    for cinema_level, skill_level in ((0, 12), (4, 14), (6, 16)):
        _, definition = _definition(
            CissiaCompileConfig(core_level=7, cinema_level=cinema_level)
        )
        execution = calculate_move(
            _execution_request(
                definition,
                "basic-snake-kiss",
                parameter_values={
                    "parameter:cissia:cinema4-awareness-stacks": 0,
                }
                if cinema_level >= 4
                else {},
                enabled_rules=(
                    "rule:character:1521:core:bone-erosion-extra-ratio",
                ),
            )
        )
        assert execution.output.complete
        assert len(execution.output.events) == 2
        bone_event = execution.output.events[1]
        expected_base = bone_source.value_for_level(skill_level, "1521019")
        assert expected_base is not None
        expected_total = expected_base / 100.0 + 3.35
        final_skill_multiplier = next(
            item.value.value
            for item in bone_event.result.breakdown
            if item.node is CalculationNode.DAMAGE_SKILL_MULTIPLIER
        )
        assert final_skill_multiplier == pytest.approx(expected_total)


def test_cinema6_triggers_once_from_teammate_penetration_hit_and_excludes_bone_child() -> None:
    _, cissia = _definition(CissiaCompileConfig(core_level=7, cinema_level=6))
    banyue_raw = load_banyue_raw_record(load_character_record("character:1471"))
    banyue = compile_banyue(BanYueCompileConfig(), banyue_raw)
    penetration_entry = next(
        item
        for item in banyue.move_entries
        if str(item.entry_id).endswith(":basic-fenshen")
    )
    assert penetration_entry.main_damage_event.damage_type is DamageType.PENETRATION

    c6_condition_id = "condition:cissia:cinema6-mark-proc-active"
    scenario = CalculationScenario(
        scenario_id="cissia-c6-penetration-team-hit",
        current_operator=BANYUE_ID,
        conditions=(
            *banyue.scenario_conditions,
            *(
                replace(item, value=True)
                if str(item.condition_id) == c6_condition_id
                else item
                for item in cissia.scenario_conditions
            ),
        ),
        parameters=(*banyue.scenario_parameters, *cissia.scenario_parameters),
        enabled_rule_item_ids=frozenset(
            {RuleItemId("rule:character:1521:cinema6:team-bone-erosion")}
        ),
    )
    target_id = EnemyId("enemy:cissia-c6-team-hit")
    stats = CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(1000.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.0),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.FIRE: Resolved(0.0), Element.ELECTRIC: Resolved(0.0)},
    )
    execution = calculate_move(
        MoveCalculationRequest(
            definition=banyue,
            supporting_definitions=(cissia,),
            move_entry_id=penetration_entry.entry_id,
            scenario=scenario,
            battle_state_id=BattleStateId("battle:cissia-c6-team-hit"),
            battle_time=0.0,
            base_character_snapshots=(
                CharacterSnapshot(BANYUE_ID, 60, stats),
                CharacterSnapshot(CISSIA_ID, 60, stats),
            ),
            target_snapshot=EnemySnapshot(
                enemy_id=target_id,
                level=70,
                initial_defense=Resolved(794.0),
                damage_resistance={
                    Element.FIRE: Resolved(0.0),
                    Element.ELECTRIC: Resolved(0.0),
                },
                anomaly_buildup_resistance={},
                daze_resistance=Resolved(0.0),
                damage_reduction=Resolved(0.0),
            ),
            team_profiles=(
                CharacterMatchProfile(BANYUE_ID, banyue.role),
                CharacterMatchProfile(CISSIA_ID, cissia.role),
            ),
            target_profile=EnemyMatchProfile(target_id),
        )
    )

    assert execution.output.complete
    assert len(execution.output.events) == 2
    assert execution.output.events[0].damage_type is DamageType.PENETRATION
    assert execution.output.events[1].damage_type is DamageType.DIRECT
    assert execution.event_traces[1].created_by_effect_id is not None
    c6_rule_id = RuleItemId("rule:character:1521:cinema6:team-bone-erosion")
    parent_c6 = next(
        item for item in execution.event_traces[0].rule_matches if item.rule_id == c6_rule_id
    )
    child_c6 = next(
        item for item in execution.event_traces[1].rule_matches if item.rule_id == c6_rule_id
    )
    assert any(item.status is EffectMatchStatus.MATCHED for item in parent_c6.effects)
    assert all(item.status is EffectMatchStatus.NOT_MATCHED for item in child_c6.effects)


def test_cinema6_ex_special_and_its_generated_hit_consume_one_current_proc() -> None:
    _, cissia = _definition(
        CissiaCompileConfig(cinema_level=6, cinema6_mark_proc_active=True)
    )
    execution = calculate_move(
        _execution_request(
            cissia,
            "ex-special",
            enabled_rules=(
                "rule:character:1521:skill:ex-special-extra-hit",
                "rule:character:1521:cinema6:team-bone-erosion",
            ),
        )
    )

    assert execution.output.complete
    assert len(execution.output.events) == 3
    assert sum(
        "ex-special-extra-hit" in event.semantic_id
        for event in execution.output.events
    ) == 1
    assert sum(
        "cinema6-bone-erosion" in event.semantic_id
        for event in execution.output.events
    ) == 1


def test_cinema6_attack_filter_does_not_treat_anomaly_record_settlement_as_a_hit() -> None:
    _, cissia = _definition(CissiaCompileConfig(cinema_level=6))
    operator = BANYUE_ID
    anomaly_source = CharacterId("character:source-anomaly-test")
    target_id = EnemyId("enemy:cissia-c6-anomaly")
    battle_id = BattleStateId("battle:cissia-c6-anomaly")
    record_id = AnomalyRecordId("anomaly:cissia-c6-anomaly:physical")
    contribution = AnomalyContribution(
        contributor=anomaly_source,
        actual_written_buildup=100.0,
        anomaly_effect_strength=Resolved(1000.0),
        impact_strength=Resolved(100.0),
        occurred_at=0.0,
    )
    record = AnomalyRecord(
        record_id=record_id,
        target_enemy=target_id,
        element=Element.PHYSICAL,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[Element.PHYSICAL],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[Element.PHYSICAL],
        weighted_anomaly_effect_strength=Resolved(1000.0),
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=Resolved(1.0),
        contributors=(anomaly_source,),
        anomaly_triggerer=anomaly_source,
        crit_capability=NoAnomalyCrit(),
        triggered_at=0.0,
        duration=Resolved(10.0),
        contributions=(contribution,),
    )
    event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("event:cissia-c6-anomaly-settlement"),
            battle_state_id=battle_id,
            damage_dealer=anomaly_source,
            target_enemy=target_id,
            element=Element.PHYSICAL,
            created_at=0.0,
        ),
        anomaly_triggerer=anomaly_source,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=NoCritRule(),
    )
    stats = CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(1000.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.0),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
    )
    scenario = CalculationScenario(
        scenario_id="cissia-c6-anomaly-record",
        current_operator=operator,
        conditions=tuple(
            replace(item, value=True)
            if str(item.condition_id) == "condition:cissia:cinema6-mark-proc-active"
            else item
            for item in cissia.scenario_conditions
        ),
        parameters=tuple(cissia.scenario_parameters),
        enabled_rule_item_ids=frozenset(
            {RuleItemId("rule:character:1521:cinema6:team-bone-erosion")}
        ),
    )
    enemy = EnemySnapshot(
        enemy_id=target_id,
        level=70,
        initial_defense=Resolved(794.0),
        damage_resistance={Element.PHYSICAL: Resolved(0.0)},
        anomaly_buildup_resistance={},
        daze_resistance=Resolved(0.0),
        damage_reduction=Resolved(0.0),
    )
    context = EffectMatchContext(
        current_event=event,
        calculation_context=CalculationContext(
            event=event,
            battle_state_id=battle_id,
            character_snapshots=(
                CharacterSnapshot(operator, 60, stats),
                CharacterSnapshot(CISSIA_ID, 60, stats),
                CharacterSnapshot(anomaly_source, 60, stats),
            ),
            target_snapshot=enemy,
            history_records=(record,),
        ),
        scenario=scenario,
        team=(
            CharacterMatchProfile(operator, CharacterRole.VANGUARD),
            CharacterMatchProfile(CISSIA_ID, CharacterRole.ATTACK),
            CharacterMatchProfile(anomaly_source, CharacterRole.ANOMALY),
        ),
        target=EnemyMatchProfile(target_id),
    )
    c6_rule = _rule(cissia, "cinema6:team-bone-erosion")

    assert context.history_records == (record,)
    assert EffectMatcher().match_rule_item(c6_rule, context).status is EffectMatchStatus.NOT_MATCHED
