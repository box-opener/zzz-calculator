from __future__ import annotations

import json
import re
from pathlib import Path

from core.application.characters.nanoka_compiler import raw_move_index
from core.application.moves import MultiplierRelation
from core.presentation.registry import _norma_additional_ability_eligibility
from core.application.characters.norma import (
    NORMA_ID,
    NORMA_REVIEWED_MAPPING,
    NormaCompileConfig,
    compile_norma,
    load_raw_record,
)
from core.application.characters.norma.reviewed import (
    CINEMA1_RESISTANCE_REDUCTION_ACTIVE,
    CINEMA6_MISSILE_CURRENT_HIT,
    CURRENT_TECH_GAP_STACKS,
    EN_NI_BARRAGE_ACTIVE,
    EX_TARGET_NOT_STUNNED,
    EX_TARGET_STUNNED,
    EXTRA_TECH_GAP_RULE_ID,
    NORMA_FRIENDLY_ACTOR_CURVES,
    TERM_1000012_ACTIVE,
)
from core.application.rules import RuleEligibility
from core.application.scenario import ParameterResolution
from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterId,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectTarget,
    Element,
    EventTemplateIdFilter,
    PanelStatDerivedValue,
    RuleStackCondition,
    ScenarioParameterDerivedValue,
    SkillGroup,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "norma.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1571.json"


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _compiled(config: NormaCompileConfig | None = None):
    raw = load_raw_record(_source_data())
    return raw, compile_norma(config or NormaCompileConfig(), raw)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1571:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _rule(definition, key: str):
    rule_id = f"rule:character:1571:{key}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _first_modifier(rule):
    return next(item for item in rule.effects if hasattr(item, "result"))


def _value(variant) -> float:
    return variant.multiplier.value.value


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def test_norma_live_source_identity_and_provenance_are_preserved() -> None:
    data = _source_data()
    raw = load_raw_record(data)

    assert raw.character_id == NORMA_ID
    assert (raw.name, raw.code_name, raw.rarity) == ("诺姆", "Norma", 4)
    assert (raw.specialty, raw.element, raw.faction, raw.icon) == (
        "击破",
        "火属性",
        "罗斯凯利法",
        "IconRole65",
    )
    assert (raw.source_version, raw.source_url) == (SOURCE_VERSION, SOURCE_URL)
    assert (data["source_version"], data["source_url"]) == (SOURCE_VERSION, SOURCE_URL)
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6


def test_extra_eligibility_uses_reviewed_attack_rupture_and_raw_faction_ids() -> None:
    norma = CharacterId("character:1571")
    assert not _norma_additional_ability_eligibility((norma,))
    assert _norma_additional_ability_eligibility(
        (norma, CharacterId("character:1111"))
    )
    assert _norma_additional_ability_eligibility(
        (norma, CharacterId("character:1051"))
    )
    # Norma and Velina both use Nanoka camp key 16 (罗斯凯利法).
    assert _norma_additional_ability_eligibility(
        (norma, CharacterId("character:1561"))
    )
    assert not _norma_additional_ability_eligibility(
        (norma, CharacterId("character:1031"))
    )


def test_every_reviewed_norma_damage_curve_matches_its_raw_parameter_and_id() -> None:
    raw, definition = _compiled()
    raw_moves = raw_move_index(raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}

    assert len(NORMA_REVIEWED_MAPPING.moves) == 18
    for spec in NORMA_REVIEWED_MAPPING.moves:
        entry = entries[f"move-entry:character:1571:{spec.entry_key}"]
        parameter_spec = spec.parameters[0]
        parameter = next(
            item
            for item in raw_moves[spec.source_name].parameters
            if item.name == parameter_spec.parameter_name
        )
        source_ratio = parameter.value_for_level(12, parameter_spec.source_skill_id)
        assert source_ratio is not None
        assert len(entry.multiplier_variants) == 1
        assert _value(entry.multiplier_variants[0]) == source_ratio / 100.0
        assert entry.skill_group is spec.skill_group
        assert entry.damage_tags == spec.damage_tags
        assert entry.main_damage_event.element is Element.FIRE
        if spec.entry_key in {"ex-armor-shell", "ex-extended-armor-per-second"}:
            assert entry.condition_ids == (EX_TARGET_NOT_STUNNED,)
        elif spec.entry_key in {"ex-high-explosive-shell", "ex-extended-high-explosive-per-second"}:
            assert entry.condition_ids == (EX_TARGET_STUNNED,)


def test_turret_curves_use_separate_friendly_actor_panels() -> None:
    raw_moves = raw_move_index(load_raw_record(_source_data()))
    assert {item.source_skill_id for item in NORMA_FRIENDLY_ACTOR_CURVES} == {
        "1571013",
        "1571014",
        "1571015",
    }
    assert all(item.move_id is None for item in NORMA_FRIENDLY_ACTOR_CURVES)
    assert all(item.authored_skill_group is None for item in NORMA_FRIENDLY_ACTOR_CURVES)
    assert all(not item.authored_damage_tags for item in NORMA_FRIENDLY_ACTOR_CURVES)
    _, definition = _compiled(NormaCompileConfig(cinema_level=6))
    entries = {str(item.entry_id): item for item in definition.move_entries}
    templates = {str(item.ref.template_id): item for item in definition.damage_event_templates}
    for candidate in NORMA_FRIENDLY_ACTOR_CURVES:
        parameter = next(
            item
            for item in raw_moves[candidate.source_name].parameters
            if item.name == candidate.parameter_name
        )
        assert parameter.value_for_level(12, candidate.source_skill_id) is not None
        entry = entries[f"move-entry:character:1571:{candidate.entry_key}"]
        assert entry.multiplier_relation is MultiplierRelation.COMPLETE
        assert entry.skill_group is None and not entry.damage_tags
        template = templates[str(entry.main_damage_event.template_id)]
        assert template.damage_dealer != NORMA_ID
        assert template.friendly_actor_owner_id == NORMA_ID
        assert template.base_source.character_id == template.damage_dealer
        assert template.crit_rule.stat_owner == template.damage_dealer

    _, definition = _compiled()
    actor_notes = tuple(
        item for item in definition.diagnostics if ":actor:" in str(item.diagnostic_id)
    )
    assert len(actor_notes) == 3
    assert all(not item.blocking for item in actor_notes)
    assert not any("打靶练习" in item.display_name for item in definition.move_entries)
    assert not any("火力实验" in item.display_name for item in definition.move_entries)


def test_basic_hat_counter_chain_and_quick_assist_have_reviewed_move_identity() -> None:
    _, definition = _compiled()
    expected = {
        "basic-hat-trick": ("move:norma:basic-hat-trick", SkillGroup.BASIC_ATTACK, DamageTag.BASIC_ATTACK),
        "dodge-counter-compliance-test": (
            "move:norma:dodge-counter-compliance-test",
            SkillGroup.DODGE,
            DamageTag.DODGE_COUNTER,
        ),
        "chain-impact-drilling": (
            "move:norma:chain-impact-drilling",
            SkillGroup.CHAIN_ATTACK,
            DamageTag.CHAIN_ATTACK,
        ),
        "quick-assist-rumble-support": (
            "move:norma:quick-assist-rumble-support",
            SkillGroup.ASSIST,
            DamageTag.ASSIST,
        ),
    }
    for key, (move_id, group, tag) in expected.items():
        entry = _entry(definition, key)
        assert str(entry.move_id) == move_id
        assert entry.skill_group is group
        assert entry.damage_tags == frozenset({tag})


def test_core_crit_damage_uses_initial_crit_rate_and_raw_level_curve() -> None:
    raw = load_raw_record(_source_data())
    for level, core in enumerate(raw.core_levels, start=1):
        definition = compile_norma(NormaCompileConfig(core_level=level), raw)
        effect = _first_modifier(_rule(definition, "core:initial-crit-damage"))
        derived = effect.result.value
        text = _plain(core.description)
        per_point = float(
            re.search(r"每超过1%，暴击伤害提升([\d.]+)%", text).group(1)
        )
        cap = float(
            re.search(r"暴击伤害.*?最多额外提升([\d.]+)%", text).group(1)
        ) / 100.0
        assert isinstance(derived, PanelStatDerivedValue)
        assert derived.source_node is CalculationNode.CHARACTER_INITIAL_CRIT_RATE
        assert derived.coefficient.value == per_point
        assert derived.threshold.value == 0.50
        assert derived.cap_max.value == cap
        assert effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE


def test_penetration_force_conversion_is_source_resolved_by_execution() -> None:
    _, definition = _compiled()
    rule = _rule(definition, "core:penetration-force-atk")
    assert rule.effects == ()
    assert "1.25" in rule.display_name


def test_extra_ability_current_technical_gap_stacks_and_cinema2_replacement_scope() -> None:
    _, definition = _compiled(
        NormaCompileConfig(additional_ability_eligible=True, cinema_level=2)
    )
    parameter = next(item for item in definition.scenario_parameters if item.parameter_id == CURRENT_TECH_GAP_STACKS)
    assert (parameter.value, parameter.minimum, parameter.maximum) == (10, 0, 10)
    assert parameter.resolution is ParameterResolution.USER_SELECTED

    base = _rule(definition, "extra-ability:technical-gap-stacks")
    base_value = _first_modifier(base).result.value
    assert isinstance(base_value, ScenarioParameterDerivedValue)
    assert base_value.coefficient.value == 0.03
    assert base_value.cap_max.value == 0.30
    assert base.eligibility is RuleEligibility.ELIGIBLE
    assert base.stack_count == 1

    c2 = _rule(definition, "cinema2:technical-gap-stun-vulnerability")
    c2_effect = _first_modifier(c2)
    c2_value = c2_effect.result.value
    assert isinstance(c2_value, ScenarioParameterDerivedValue)
    assert c2_value.coefficient.value == 0.03
    assert c2_value.cap_max.value == 0.30
    assert isinstance(c2_effect.rule.condition, RuleStackCondition)
    assert c2_effect.rule.condition.rule_item_id == str(EXTRA_TECH_GAP_RULE_ID)
    assert c2_effect.rule.condition.requires_rule_enabled

    _, ineligible = _compiled(NormaCompileConfig(additional_ability_eligible=False, cinema_level=2))
    assert _rule(ineligible, "extra-ability:technical-gap-stacks").eligibility is RuleEligibility.INELIGIBLE
    ineligible_c2 = _rule(ineligible, "cinema2:technical-gap-stun-vulnerability")
    assert ineligible_c2.eligibility is RuleEligibility.INELIGIBLE
    assert not ineligible_c2.effects

    _, locked = _compiled(NormaCompileConfig(additional_ability_eligible=True, cinema_level=0))
    assert _rule(locked, "cinema2:technical-gap-stun-vulnerability").eligibility is RuleEligibility.INELIGIBLE
    assert not _rule(locked, "cinema2:technical-gap-stun-vulnerability").effects


def test_term_condition_is_separate_from_technical_gap_and_uses_source_level60_cap() -> None:
    _, definition = _compiled(NormaCompileConfig(additional_ability_eligible=True))
    assert TERM_1000012_ACTIVE == EN_NI_BARRAGE_ACTIVE
    assert len(definition.scenario_parameters) == 1
    assert definition.scenario_parameters[0].parameter_id == CURRENT_TECH_GAP_STACKS
    assert any(item.condition_id == TERM_1000012_ACTIVE for item in definition.scenario_conditions)

    term_rule = _rule(definition, "extra-ability:term-1000012-attack")
    assert term_rule.condition_ids == (TERM_1000012_ACTIVE,)
    term_value = _first_modifier(term_rule).result.value
    assert term_value.value == 870.0
    assert "44" in term_rule.original_text and "每级增加14" in term_rule.original_text
    assert "最多提升870" in term_rule.original_text
    assert term_rule.stack_count is None

    team_rule = _rule(definition, "extra-ability:en-ni-barrage-team-damage")
    team_effect = _first_modifier(team_rule)
    assert team_rule.condition_ids == (EN_NI_BARRAGE_ACTIVE,)
    assert team_effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert team_effect.result.value.value == 0.20
    assert team_effect.rule.target is EffectTarget.TEAM


def test_cinema1_is_a_current_enemy_resistance_reduction_with_locked_rule_retained() -> None:
    _, unlocked = _compiled(NormaCompileConfig(cinema_level=1))
    rule = _rule(unlocked, "cinema1:all-resistance-reduction")
    assert rule.eligibility is RuleEligibility.ELIGIBLE
    assert rule.condition_ids == (CINEMA1_RESISTANCE_REDUCTION_ACTIVE,)
    effect = _first_modifier(rule)
    assert effect.result.modifier_path is CalculationNode.ENEMY_RESISTANCE_REDUCTION
    assert effect.result.value.value == 0.15
    assert effect.rule.target is EffectTarget.ENEMY

    _, locked = _compiled(NormaCompileConfig(cinema_level=0))
    locked_rule = _rule(locked, "cinema1:all-resistance-reduction")
    assert locked_rule.eligibility is RuleEligibility.INELIGIBLE
    assert not locked_rule.effects


def test_cinema3_and_5_raise_ultimate_and_all_other_skills_with_cap_16() -> None:
    raw = load_raw_record(_source_data())
    for cinema, expected in ((0, 12), (3, 14), (5, 16), (6, 16)):
        config = NormaCompileConfig(cinema_level=cinema)
        definition = compile_norma(config, raw)
        ultimate = _entry(definition, "ultimate-firepower-doctrine")
        raw_move = next(item for item in raw.moves if item.name == "终结技：优势火力学说")
        parameter = next(item for item in raw_move.parameters if item.name == "伤害倍率")
        source_value = parameter.value_for_level(expected, "1571019")
        assert source_value is not None
        assert _value(ultimate.multiplier_variants[0]) == source_value / 100.0


def test_cinema6_exposes_one_current_missile_packet_and_high_explosive_scope() -> None:
    _, definition = _compiled(NormaCompileConfig(cinema_level=6))
    missile = _entry(definition, "cinema6-current-missile")
    assert missile.move_id is None
    assert missile.skill_group is SkillGroup.ULTIMATE
    assert missile.damage_tags == frozenset({DamageTag.ULTIMATE})
    assert missile.condition_ids == (CINEMA6_MISSILE_CURRENT_HIT,)
    assert _value(missile.multiplier_variants[0]) == 2.0
    assert missile.multiplier_variants[0].repeat_count is None

    c6 = _rule(definition, "cinema6:high-explosive-damage")
    assert c6.eligibility is RuleEligibility.ELIGIBLE
    effect = _first_modifier(c6)
    assert effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert effect.result.value.value == 0.30
    assert effect.rule.target is EffectTarget.TEAM
    template_filter = next(item for item in effect.rule.filters if isinstance(item, AnyFilter))
    assert {
        str(item.template_id)
        for item in template_filter.filters
        if isinstance(item, EventTemplateIdFilter)
    } == {
        "template:character:1571:ex-high-explosive-shell:main",
        "template:character:1571:ex-extended-high-explosive-per-second:main",
        "template:character:1571:friendly-construct:ex-firepower-high-explosive-shell:main",
    }


def test_norma_does_not_publish_anomaly_disorder_or_daze_only_damage() -> None:
    _, definition = _compiled(NormaCompileConfig(cinema_level=6))
    assert all(item.main_damage_event.damage_type is DamageType.DIRECT for item in definition.move_entries)
    assert all(
        str(item.move_id) not in {
            "move:norma:parry-assist-light-daze",
            "move:norma:parry-assist-heavy-daze",
            "move:norma:parry-assist-continuous-daze",
        }
        for item in definition.move_entries
    )
