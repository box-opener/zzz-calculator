from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.application.characters.seed import SeedCompileConfig, compile_seed
from core.application.characters.seed.compiler import load_raw_record
from core.application.characters.seed.reviewed import (
    CINEMA2_ENERGY_INTERVALS_SPENT,
    CINEMA6_LASER_PROC_ACTIVE,
    PARTNER_EX_BUFF_ACTIVE,
    PARTNER_SURROUND_HUNT_ACTIVE,
    SEED_EX_BUFF_ACTIVE,
    SEED_SURROUND_HUNT_ACTIVE,
)
from core.application.scenario import ConditionResolution
from core.application.moves import MultiplierRelation
from core.application.rules import RuleEligibility
from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterId,
    DamageDealerFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectTarget,
    Element,
    EventCreationEffect as TypedEventCreationEffect,
    EventTemplateIdFilter,
    ModifierEffect,
    Resolved,
    ScenarioParameterDerivedValue,
    SkillGroup,
    Unresolved,
    UnresolvedEffect,
)


_SEED_ID = CharacterId("character:1461")
_PARTNER_ID = CharacterId("character:1111")
_SECOND_PARTNER_ID = CharacterId("character:1081")
_RAW_PATH = Path(__file__).parents[2] / "core" / "data" / "characters" / "seed.json"


@pytest.fixture(scope="module")
def raw_record():
    data = json.loads(_RAW_PATH.read_text(encoding="utf-8"))
    return load_raw_record(data)


def _entry(definition, key: str):
    suffix = f":{key}"
    return next(item for item in definition.move_entries if str(item.entry_id).endswith(suffix))


def _rule(definition, key: str):
    suffix = f":{key}"
    return next(item for item in definition.rule_items if str(item.rule_id).endswith(suffix))


def _modifiers(rule):
    return tuple(item for item in rule.effects if isinstance(item, ModifierEffect))


def _resolved(effect) -> float:
    assert isinstance(effect.result.value, Resolved)
    return effect.result.value.value


def test_seed_raw_identity_and_default_curves(raw_record) -> None:
    assert (
        raw_record.name,
        raw_record.code_name,
        raw_record.rarity,
        raw_record.specialty,
        raw_record.element,
        raw_record.faction,
        raw_record.icon,
    ) == ("「席德」", "Seed", 4, "强攻", "电属性", "新艾利都防卫军", "IconRole48")
    assert (raw_record.source_version, raw_record.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1461.json",
    )

    config = SeedCompileConfig()
    assert all(config.skill_level_for(group) == 12 for group in SkillGroup)
    definition = compile_seed(config, raw_record)
    expected = {
        "basic-stage-1": 0.938,
        "basic-stage-2": 2.484,
        "basic-stage-3": 1.444,
        "basic-stage-4": 7.172,
        "heavy-strike": 3.338,
        "falling-crash-1": 10.574,
        "falling-crash-2": 19.794,
        "dash-attack": 1.291,
        "dodge-counter": 6.402,
        "special": 0.961,
        "ex-special-rain": 13.676,
        "ex-special-release": 0.371,
        "chain-attack": 14.690,
        "ultimate": 65.002,
        "quick-assist": 3.080,
        "assist-strike": 9.125,
    }
    assert len(definition.move_entries) == len(expected)
    for key, ratio in expected.items():
        entry = _entry(definition, key)
        if key.startswith("basic-stage-"):
            assert entry.multiplier_relation is MultiplierRelation.SEQUENTIAL_STAGE
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(ratio)

    stage_elements = (Element.PHYSICAL, Element.PHYSICAL, Element.ELECTRIC, Element.ELECTRIC)
    for stage, expected_element in enumerate(stage_elements, start=1):
        entry = _entry(definition, f"basic-stage-{stage}")
        assert entry.main_damage_event.element is expected_element
        assert entry.skill_group is SkillGroup.BASIC_ATTACK
        assert entry.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert not any(
        template.ref.damage_type in {DamageType.ANOMALY, DamageType.DISORDER}
        for template in definition.damage_event_templates
    )


def test_seed_cinema_skill_bonuses_include_ultimate(raw_record) -> None:
    c3 = compile_seed(SeedCompileConfig(cinema_level=3), raw_record)
    c5 = compile_seed(SeedCompileConfig(cinema_level=5), raw_record)
    assert _entry(c3, "ultimate").multiplier_variants[0].multiplier.value.value == pytest.approx(70.912)
    assert _entry(c5, "ultimate").multiplier_variants[0].multiplier.value.value == pytest.approx(76.822)
    for level in (3, 5):
        rule = _rule(c5, f"cinema{level}:skill-levels")
        assert rule.eligibility is RuleEligibility.ELIGIBLE
        assert "终结技" in rule.display_name


def test_seed_core_targets_resolved_partner_and_keeps_each_dealer_scope(raw_record) -> None:
    definition = compile_seed(
        SeedCompileConfig(
            core_level=7,
            partner_character_id=_PARTNER_ID,
            additional_ability_eligible=True,
            partner_ex_buff_active=True,
            seed_ex_buff_active=True,
            seed_surround_hunt_active=True,
            partner_surround_hunt_active=True,
        ),
        raw_record,
    )
    conditions = {str(item.condition_id): item for item in definition.scenario_conditions}
    for condition_id, selected in (
        (PARTNER_EX_BUFF_ACTIVE, True),
        (SEED_EX_BUFF_ACTIVE, True),
        (SEED_SURROUND_HUNT_ACTIVE, True),
        (PARTNER_SURROUND_HUNT_ACTIVE, True),
    ):
        condition = conditions[str(condition_id)]
        assert condition.resolution is ConditionResolution.USER_SELECTED
        assert condition.value is selected
    seed_buff = _rule(definition, "core:seed-strong-assault")
    assert seed_buff.condition_ids == (PARTNER_EX_BUFF_ACTIVE,)
    for effect in _modifiers(seed_buff):
        assert effect.rule.owner == _SEED_ID
        assert effect.rule.target is EffectTarget.RECIPIENT
        assert effect.rule.recipient_character_id == _SEED_ID
    seed_panel = {effect.result.modifier_path: _resolved(effect) for effect in _modifiers(seed_buff)}
    assert seed_panel == {
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS: 1000,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE: 0.30,
    }

    partner_buff = _rule(definition, "core:partner-bright-attack")
    assert partner_buff.condition_ids == (SEED_EX_BUFF_ACTIVE,)
    assert all(effect.rule.owner == _SEED_ID for effect in _modifiers(partner_buff))
    assert all(effect.rule.target is EffectTarget.RECIPIENT for effect in _modifiers(partner_buff))
    assert all(effect.rule.recipient_character_id == _PARTNER_ID for effect in _modifiers(partner_buff))

    seed_hunt = _rule(definition, "core:seed-surround-hunt")
    partner_hunt = _rule(definition, "core:partner-surround-hunt")
    assert seed_hunt.condition_ids == (SEED_SURROUND_HUNT_ACTIVE,)
    assert partner_hunt.condition_ids == (PARTNER_SURROUND_HUNT_ACTIVE,)
    assert _resolved(_modifiers(seed_hunt)[0]) == pytest.approx(0.25)
    assert _resolved(_modifiers(partner_hunt)[0]) == pytest.approx(0.25)
    for rule, expected_dealer in ((seed_hunt, _SEED_ID), (partner_hunt, _PARTNER_ID)):
        filters = _modifiers(rule)[0].rule.filters
        assert DamageDealerFilter(expected_dealer) in filters
        assert not any(isinstance(item, DamageTypeFilter) for item in filters)


def test_seed_core_level_curves_and_unresolved_partner_diagnostic(raw_record) -> None:
    expected_attack = (100, 225, 350, 475, 600, 725, 1000)
    expected_cd = (0.15, 0.175, 0.20, 0.225, 0.25, 0.275, 0.30)
    expected_hunt = (0.125, 0.145, 0.165, 0.185, 0.205, 0.225, 0.25)
    for level, (attack, crit_damage, hunt) in enumerate(
        zip(expected_attack, expected_cd, expected_hunt), start=1
    ):
        definition = compile_seed(
            SeedCompileConfig(
                core_level=level,
                partner_character_id=_PARTNER_ID,
                additional_ability_eligible=True,
            ),
            raw_record,
        )
        attack_effect = next(
            effect
            for effect in _modifiers(_rule(definition, "core:seed-strong-assault"))
            if effect.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS
        )
        cd_effect = next(
            effect
            for effect in _modifiers(_rule(definition, "core:seed-strong-assault"))
            if effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
        )
        assert _resolved(attack_effect) == attack
        assert _resolved(cd_effect) == pytest.approx(crit_damage)
        assert _resolved(_modifiers(_rule(definition, "core:seed-surround-hunt"))[0]) == pytest.approx(hunt)

    unresolved = compile_seed(
        SeedCompileConfig(
            partner_selection_unresolved=True,
            partner_candidate_ids=(_PARTNER_ID, _SECOND_PARTNER_ID),
            additional_ability_eligible=True,
            partner_ex_buff_active=True,
            seed_ex_buff_active=True,
            seed_surround_hunt_active=True,
            partner_surround_hunt_active=True,
        ),
        raw_record,
    )
    assert any("highest Initial ATK" in item.message for item in unresolved.diagnostics)
    assert any(item.rule_id.endswith(":core:seed-strong-assault") for item in unresolved.rule_items)
    partner_buff = _rule(unresolved, "core:partner-bright-attack")
    partner_hunt = _rule(unresolved, "core:partner-surround-hunt")
    assert partner_buff.eligibility is RuleEligibility.ELIGIBLE
    assert partner_buff.condition_ids == (SEED_EX_BUFF_ACTIVE,)
    assert len(partner_buff.effects) == 4
    assert all(isinstance(effect, UnresolvedEffect) for effect in partner_buff.effects)
    assert {
        item.character_id
        for effect in partner_buff.effects
        for item in effect.rule.filters
        if isinstance(item, DamageDealerFilter)
    } == {_PARTNER_ID, _SECOND_PARTNER_ID}
    assert partner_hunt.eligibility is RuleEligibility.ELIGIBLE
    assert partner_hunt.condition_ids == (PARTNER_SURROUND_HUNT_ACTIVE,)
    assert len(partner_hunt.effects) == 2
    assert all(isinstance(effect, UnresolvedEffect) for effect in partner_hunt.effects)
    assert _rule(unresolved, "core:seed-surround-hunt").effects
    assert any(
        condition.condition_id == SEED_EX_BUFF_ACTIVE
        for condition in unresolved.scenario_conditions
    )

    c2_unresolved = compile_seed(
        SeedCompileConfig(
            cinema_level=2,
            partner_selection_unresolved=True,
            partner_candidate_ids=(_PARTNER_ID, _SECOND_PARTNER_ID),
            additional_ability_eligible=True,
            partner_surround_hunt_active=True,
        ),
        raw_record,
    )
    c2_partner = _rule(c2_unresolved, "cinema2:partner-surround-hunt-defense-ignore")
    assert c2_partner.condition_ids == (PARTNER_SURROUND_HUNT_ACTIVE,)
    assert len(c2_partner.effects) == 2
    assert all(isinstance(effect, UnresolvedEffect) for effect in c2_partner.effects)
    assert all(
        DamageTypeFilter(DamageType.DIRECT) in effect.rule.filters
        for effect in c2_partner.effects
    )


def test_seed_additional_ability_and_cinema_scopes_are_exact(raw_record) -> None:
    definition = compile_seed(
        SeedCompileConfig(
            cinema_level=6,
            partner_character_id=_PARTNER_ID,
            additional_ability_eligible=True,
            seed_surround_hunt_active=True,
            partner_surround_hunt_active=False,
            cinema2_energy_intervals_spent=6,
            cinema6_laser_proc_active=True,
        ),
        raw_record,
    )

    extra = _rule(definition, "extra-ability:damage-and-electric-resistance")
    assert extra.eligibility is RuleEligibility.ELIGIBLE
    normal_bonus, resistance_ignore = _modifiers(extra)
    assert normal_bonus.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert resistance_ignore.result.modifier_path is CalculationNode.DAMAGE_RESISTANCE_IGNORE
    assert _resolved(normal_bonus) == pytest.approx(0.30)
    assert _resolved(resistance_ignore) == pytest.approx(0.25)
    expected_entries = {"heavy-strike", "falling-crash-1", "falling-crash-2", "ultimate"}
    allowed_template_ids = {
        _entry(definition, key).main_damage_event.template_id for key in expected_entries
    }
    for effect in (normal_bonus, resistance_ignore):
        assert DamageDealerFilter(_SEED_ID) in effect.rule.filters
        assert DamageTypeFilter(DamageType.DIRECT) in effect.rule.filters
        event_filter = next(item for item in effect.rule.filters if isinstance(item, AnyFilter))
        assert {item.template_id for item in event_filter.filters} == allowed_template_ids

    c1 = _rule(definition, "cinema1:falling-crash-crit-damage")
    c1_effect = _modifiers(c1)[0]
    assert _resolved(c1_effect) == pytest.approx(0.30)
    c1_scope = next(item for item in c1_effect.rule.filters if isinstance(item, AnyFilter))
    assert {item.template_id for item in c1_scope.filters} == {
        _entry(definition, "falling-crash-1").main_damage_event.template_id,
        _entry(definition, "falling-crash-2").main_damage_event.template_id,
    }

    c2_seed = _rule(definition, "cinema2:seed-surround-hunt-defense-ignore")
    assert c2_seed.condition_ids == (SEED_SURROUND_HUNT_ACTIVE,)
    assert _resolved(_modifiers(c2_seed)[0]) == pytest.approx(0.20)
    assert DamageDealerFilter(_SEED_ID) in _modifiers(c2_seed)[0].rule.filters
    c2_partner = _rule(definition, "cinema2:partner-surround-hunt-defense-ignore")
    assert c2_partner.condition_ids == (PARTNER_SURROUND_HUNT_ACTIVE,)
    assert DamageDealerFilter(_PARTNER_ID) in _modifiers(c2_partner)[0].rule.filters
    c2_heavy = _rule(definition, "cinema2:linked-heavy-damage-bonus")
    assert not c2_heavy.condition_ids
    c2_value = _modifiers(c2_heavy)[0].result.value
    assert isinstance(c2_value, ScenarioParameterDerivedValue)
    assert c2_value.parameter_id == str(CINEMA2_ENERGY_INTERVALS_SPENT)
    assert c2_value.coefficient.value == pytest.approx(0.05)
    assert c2_value.cap_max.value == pytest.approx(1.20)
    assert _modifiers(c2_heavy)[0].rule.filters == (
        DamageDealerFilter(_SEED_ID),
        EventTemplateIdFilter(_entry(definition, "heavy-strike").main_damage_event.template_id),
    )
    assert definition.scenario_parameters[0].value == 6
    assert definition.scenario_parameters[0].maximum == 24

    c4 = _rule(definition, "cinema4:surround-hunt-ultimate-damage")
    assert c4.condition_ids == (SEED_SURROUND_HUNT_ACTIVE,)
    assert _resolved(_modifiers(c4)[0]) == pytest.approx(0.20)
    assert EventTemplateIdFilter(
        _entry(definition, "ultimate").main_damage_event.template_id
    ) in _modifiers(c4)[0].rule.filters

    c6_cd = _rule(definition, "cinema6:self-crit-damage")
    assert _resolved(_modifiers(c6_cd)[0]) == pytest.approx(0.50)
    assert _modifiers(c6_cd)[0].rule.target is EffectTarget.SELF

    c6_laser = _rule(definition, "cinema6:heavy-strike-laser-child")
    assert c6_laser.condition_ids == (CINEMA6_LASER_PROC_ACTIVE,)
    assert len(c6_laser.effects) == 1
    assert isinstance(c6_laser.effects[0], TypedEventCreationEffect)
    unresolved = c6_laser.effects[0].result.unresolved_template
    assert isinstance(unresolved, Unresolved)
    assert "count (3)" in unresolved.notes
    assert "165% ATK each" in unresolved.notes
    assert "element, damage tag" in unresolved.notes
    assert "3道激光" in unresolved.original_text

    locked = compile_seed(SeedCompileConfig(), raw_record)
    locked_cinema_rules = (
        "cinema1:falling-crash-crit-damage",
        "cinema2:damage-mechanics",
        "cinema3:skill-levels",
        "cinema4:surround-hunt-ultimate-damage",
        "cinema5:skill-levels",
        "cinema6:self-crit-damage",
        "cinema6:heavy-strike-laser-child",
    )
    for key in locked_cinema_rules:
        item = _rule(locked, key)
        assert item.eligibility is RuleEligibility.INELIGIBLE
        assert not item.effects
    assert not locked.scenario_parameters
    assert not _rule(locked, "cinema6:heavy-strike-laser-child").diagnostics


def test_seed_config_rejects_invalid_identity_and_resource_ranges() -> None:
    with pytest.raises(ValueError, match="requires character:1461"):
        SeedCompileConfig(character_id=CharacterId("character:1462"))
    with pytest.raises(ValueError, match="another character"):
        SeedCompileConfig(
            partner_character_id=_SEED_ID,
            additional_ability_eligible=True,
        )
    with pytest.raises(ValueError, match="unresolved partner selection"):
        SeedCompileConfig(
            partner_character_id=_PARTNER_ID,
            partner_selection_unresolved=True,
            additional_ability_eligible=True,
        )
    with pytest.raises(ValueError, match="0 to 24"):
        SeedCompileConfig(cinema_level=2, cinema2_energy_intervals_spent=25)
    with pytest.raises(ValueError, match="Cinema 2 energy intervals require"):
        SeedCompileConfig(cinema2_energy_intervals_spent=1)
    with pytest.raises(ValueError, match="requires cinema_level 6"):
        SeedCompileConfig(cinema6_laser_proc_active=True)
