from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    load_wengine_raw_record,
    signature_wengine_id_for,
)
from core.application.characters.banyue import (
    BANYUE_ID,
    BANYUE_REVIEWED_MAPPING,
    BanYueCompileConfig,
    compile_banyue,
    load_raw_record,
)
from core.application.characters.banyue.compiler import BANYUE_MINGWANG_STACK_COUNT
from core.application.characters.banyue.reviewed import BANYUE_BASIC_QINGSHAN_MOVE_ID
from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.moves import MultiplierRelation
from core.application.rules import RuleEligibility
from core.application.scenario import ConditionResolution, ParameterResolution
from core.application.characters.templates import PenetrationDamageEventTemplate
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import (
    _banyue_additional_ability_eligibility,
    compile_registered_definition,
    config_fields_for,
    equipment_capabilities_for_definition,
    registration_for,
)
from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterId,
    CharacterRole,
    CurrentPenetrationForceValueSource,
    DamageDealerFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    Element,
    ElementFilter,
    EquipmentDamageScope,
    EffectTarget,
    EventCreationEffect,
    EventTemplateId,
    EventTemplateIdFilter,
    MoveIdFilter,
    PanelStatDerivedValue,
    ScenarioParameterRangeCondition,
    ScenarioParameterDerivedValue,
    SkillGroup,
    WEngineId,
    UnresolvedEffect,
)
from web.api import app


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "banyue.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1471.json"
client = TestClient(app)


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _definition(config: BanYueCompileConfig | None = None):
    raw = load_raw_record(_source_data())
    return raw, compile_banyue(config or BanYueCompileConfig(), raw)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1471:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _rule(definition, key: str):
    rule_id = f"rule:character:1471:{key}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _resolved_multiplier(variant) -> float:
    return variant.multiplier.value.value


def _effects(rule):
    return {str(item.rule.effect_id): item for item in rule.effects}


def _move_ids(effect) -> set[str]:
    filters = effect.rule.filters
    found: set[str] = set()
    for item in filters:
        if isinstance(item, MoveIdFilter):
            found.add(str(item.move_id))
        elif isinstance(item, AnyFilter):
            found.update(
                str(nested.move_id)
                for nested in item.filters
                if isinstance(nested, MoveIdFilter)
            )
    return found


def test_banyue_identity_raw_provenance_role_and_base_panels_are_preserved() -> None:
    data = _source_data()
    raw = load_raw_record(data)

    assert data["source_version"] == SOURCE_VERSION
    assert data["source_url"] == SOURCE_URL
    assert raw.source_version == SOURCE_VERSION
    assert raw.source_url == SOURCE_URL
    assert raw.character_id == BANYUE_ID
    assert raw.name == "般岳"
    assert raw.code_name == "BanYue"
    assert raw.rarity == 4
    assert raw.specialty == "命破"
    assert raw.element == "火属性"
    assert raw.faction == "坎卜斯黑枝"
    assert raw.icon == "IconRole53"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6

    stats = data["stats"]
    assert stats["hp_max"] == 683
    assert stats["attack"] == 124
    assert stats["defence"] == 36
    max_ascension = data["level"]["6"]
    assert max_ascension["hp_max"] == 2344
    assert max_ascension["attack"] == 221
    assert max_ascension["defence"] == 123

    definition = compile_banyue(BanYueCompileConfig(), raw)
    assert definition.character_id == BANYUE_ID
    assert definition.role is CharacterRole.RUPTURE
    assert definition.base_element is Element.FIRE
    assert len(definition.move_entries) == 24


def test_banyue_registry_panel_catalog_signature_and_team_eligibility_are_connected() -> None:
    raw = load_raw_record(load_character_record(str(BANYUE_ID)))
    assert raw.code_name == "BanYue"
    assert raw.source_url == SOURCE_URL
    assert str(BANYUE_ID) in supported_character_ids()

    panel = character_base_stats(BANYUE_ID)
    assert panel.hp.value == pytest.approx(8497.1437)
    assert panel.attack.value == pytest.approx(859.9099)
    assert panel.crit_rate.value == pytest.approx(0.194)

    definition = compile_registered_definition(
        BANYUE_ID,
        {"core_level": 7, "cinema_level": 0},
        (BANYUE_ID,),
    )
    registration = registration_for(BANYUE_ID)
    capabilities = equipment_capabilities_for_definition(definition)
    assert registration.role is CharacterRole.RUPTURE
    assert registration.base_element is Element.FIRE
    assert capabilities.role is CharacterRole.RUPTURE
    assert capabilities.possible_elements == frozenset({Element.FIRE})
    assert capabilities.skill_groups == frozenset(
        spec.skill_group for spec in BANYUE_REVIEWED_MAPPING.moves
    )
    assert capabilities.damage_tags == frozenset(
        tag for spec in BANYUE_REVIEWED_MAPPING.moves for tag in spec.damage_tags
    )
    assert capabilities.damage_scopes == frozenset(
        EquipmentDamageScope(spec.element, spec.skill_group, spec.damage_tags)
        for spec in BANYUE_REVIEWED_MAPPING.moves
    )
    assert capabilities.mechanisms == frozenset({"rupture-vajra"})

    assert _banyue_additional_ability_eligibility(
        (BANYUE_ID, CharacterId("character:1311"))
    )
    assert _banyue_additional_ability_eligibility(
        (BANYUE_ID, CharacterId("character:1361"))
    )
    assert not _banyue_additional_ability_eligibility(
        (BANYUE_ID, CharacterId("character:1421"))
    )

    signature = WEngineId("wengine:14147")
    assert SIGNATURE_WENGINE_BY_CHARACTER[BANYUE_ID] == signature
    assert signature_wengine_id_for(BANYUE_ID) == signature
    weapon_raw = load_wengine_raw_record(signature)
    assert weapon_raw.icon == "Weapon_S_1471"
    engine_catalog = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert engine_catalog[str(signature)].signature_character_id == str(BANYUE_ID)
    character_catalog = {
        item.character_id: item for item in supported_character_catalog()
    }
    assert character_catalog[str(BANYUE_ID)].code_name == "BanYue"
    assert character_catalog[str(BANYUE_ID)].rarity == "S"
    assert character_catalog[str(BANYUE_ID)].specialty == "rupture"

    fields = {
        item.field_id: item
        for item in config_fields_for(BANYUE_ID, {}, (BANYUE_ID,))
    }
    assert fields["core_level"].value == 7
    assert fields["cinema_level"].value == 0
    assert fields["skill_level:basic-attack"].value == 12
    assert "additional_ability_eligible" not in fields
    with pytest.raises(ValueError, match="additional_ability_eligible"):
        compile_registered_definition(
            BANYUE_ID,
            {
                "core_level": 7,
                "cinema_level": 0,
                "additional_ability_eligible": True,
            },
            (BANYUE_ID,),
        )

    weapon_preview = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": str(signature),
            "equipped_character_id": str(BANYUE_ID),
            "team_character_ids": [str(BANYUE_ID)],
            "level": 60,
            "refinement": 1,
            "condition_values": {},
        },
    )
    assert weapon_preview.status_code == 200, weapon_preview.text
    weapon_rules = {
        item["rule_id"]: item for item in weapon_preview.json()["rule_items"]
    }
    vajra_rule_id = "rule:wengine:14147:owner:1471:fire-penetration-damage-per-stack"
    assert weapon_rules[vajra_rule_id]["eligibility"] == "eligible"
    assert weapon_rules[vajra_rule_id]["source_type"] == "weapon"


def test_each_reviewed_damage_parameter_uses_its_exact_source_name_and_curve() -> None:
    raw, definition = _definition()
    raw_moves = {item.name: item for item in raw.moves}

    assert len(BANYUE_REVIEWED_MAPPING.moves) == 24
    for spec in BANYUE_REVIEWED_MAPPING.moves:
        entry = _entry(definition, spec.entry_key)
        assert entry.display_name == spec.display_name
        assert entry.move_id == spec.move_id
        assert entry.skill_group is spec.skill_group
        assert entry.damage_tags == spec.damage_tags
        assert entry.main_damage_event.damage_type is DamageType.PENETRATION
        assert entry.main_damage_event.element is Element.FIRE
        assert entry.original_text == raw_moves[spec.source_name].description
        assert len(spec.parameters) == len(entry.multiplier_variants) == 1

        parameter_spec = spec.parameters[0]
        parameter = next(
            item
            for item in raw_moves[spec.source_name].parameters
            if item.name == parameter_spec.parameter_name
        )
        assert parameter.format == "%"
        assert parameter_spec.source_skill_id is not None
        assert parameter.value_for_level(
            12, parameter_spec.source_skill_id
        ) == pytest.approx(parameter.value_for_level(12))
        assert entry.multiplier_relation is spec.multiplier_relation
        assert _resolved_multiplier(entry.multiplier_variants[0]) == pytest.approx(
            parameter.value_for_level(12) / 100
        )

    for key, expected_ids in (
        ("basic-zhengrong-stage-1", "1471001"),
        ("basic-zhengrong-stage-2", "1471002"),
        ("basic-zhengrong-stage-3", "1471003"),
        ("basic-zhengrong-stage-4", "1471004"),
        ("basic-cuiwei-stage-1", "1471005"),
        ("basic-cuiwei-stage-2", "1471006"),
        ("basic-cuiwei-stage-3", "1471007"),
        ("basic-cuiwei-stage-4", "1471008"),
    ):
        spec = next(item for item in BANYUE_REVIEWED_MAPPING.moves if item.entry_key == key)
        assert spec.parameters[0].source_skill_id == expected_ids
        assert spec.multiplier_relation is MultiplierRelation.SEQUENTIAL_STAGE

    non_damage_sources = {
        "普通攻击：引火",
        "闪避：不动如山",
        "招架支援：铁壁",
    }
    assert non_damage_sources.isdisjoint(
        {item.source_name for item in BANYUE_REVIEWED_MAPPING.moves}
    )


def test_all_authored_damage_templates_use_fire_penetration_force_without_defense() -> None:
    _, definition = _definition()
    assert definition.damage_event_templates
    for template in definition.damage_event_templates:
        assert isinstance(template, PenetrationDamageEventTemplate)
        assert template.ref.damage_type is DamageType.PENETRATION
        assert template.element is Element.FIRE
        assert isinstance(template.base_source, CurrentPenetrationForceValueSource)
        assert template.base_source.character_id == BANYUE_ID
        assert template.damage_dealer == BANYUE_ID

    core_rule = _rule(definition, "core:max-hp-penetration-force")
    effect = core_rule.effects[0]
    assert effect.rule.target is EffectTarget.SELF
    assert effect.result.modifier_path is CalculationNode.PENETRATION_FORCE_BONUS
    assert isinstance(effect.result.value, PanelStatDerivedValue)
    assert effect.result.value.source_node is CalculationNode.CHARACTER_CURRENT_MAX_HP
    assert effect.result.value.source_character_id == BANYUE_ID
    assert effect.result.value.coefficient.value == pytest.approx(0.1)
    assert any(
        isinstance(item, DamageTypeFilter)
        and item.damage_type is DamageType.PENETRATION
        for item in effect.rule.filters
    )


def test_core_buffs_are_user_selected_and_apply_across_all_fire_penetration_hits() -> None:
    _, definition = _definition()
    core = _rule(definition, "core:enhanced-special-assist-buffs")
    core_condition = next(
        item
        for item in definition.scenario_conditions
        if str(item.condition_id) == "condition:banyue:core-enhanced-special-or-assist-buff-active"
    )
    assert core_condition.resolution is ConditionResolution.USER_SELECTED
    assert core_condition.value is False
    assert "强化特殊技" in core_condition.original_text
    assert "支援突击" in core_condition.original_text

    effects = list(_effects(core).values())
    force = next(item for item in effects if item.result.modifier_path is CalculationNode.PENETRATION_FORCE_BONUS)
    fire = next(item for item in effects if item.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS)
    crit = next(item for item in effects if item.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE)
    assert force.result.value.value == pytest.approx(300)
    assert fire.result.value.value == pytest.approx(0.36)
    assert crit.result.value.value == pytest.approx(0.36)
    assert core.condition_ids == (core_condition.condition_id,)
    assert not _move_ids(force)
    assert any(
        isinstance(item, ElementFilter) and item.element is Element.FIRE
        for item in fire.rule.filters
    )


def test_additional_ability_and_c6_mingwang_share_defaulted_current_stack_input() -> None:
    _, c0 = _definition(BanYueCompileConfig(additional_ability_eligible=False))
    assert not c0.scenario_parameters
    base_mingwang_c0 = _rule(c0, "extra-ability:mingwang-fire-damage")
    assert base_mingwang_c0.eligibility is RuleEligibility.INELIGIBLE
    c0_c6_rule = _rule(c0, "cinema6:mingwang-fire-damage-increase")
    assert c0_c6_rule.eligibility is RuleEligibility.INELIGIBLE
    assert not any(isinstance(item, UnresolvedEffect) for item in c0_c6_rule.effects)

    raw, c6 = _definition(
        BanYueCompileConfig(cinema_level=6, additional_ability_eligible=False)
    )
    parameter = next(
        item
        for item in c6.scenario_parameters
        if item.parameter_id == BANYUE_MINGWANG_STACK_COUNT
    )
    assert parameter.resolution is ParameterResolution.USER_SELECTED
    assert parameter.value == 3
    assert parameter.minimum == 0
    assert parameter.maximum == 3
    assert "提升5%" in parameter.original_text
    assert len(c6.scenario_parameters) == 1

    extra = _rule(c6, "extra-ability:mingwang-fire-damage")
    assert extra.eligibility is RuleEligibility.INELIGIBLE
    extra_modifier = extra.effects[0]
    assert isinstance(extra_modifier.result.value, ScenarioParameterDerivedValue)
    assert extra_modifier.result.value.parameter_id == str(BANYUE_MINGWANG_STACK_COUNT)
    assert extra_modifier.result.value.coefficient.value == pytest.approx(0.05)
    assert extra_modifier.result.value.cap_max.value == pytest.approx(0.15)
    assert "提升5%" in extra.original_text

    c6_buff = _rule(c6, "cinema6:mingwang-fire-damage-increase")
    assert c6_buff.eligibility is RuleEligibility.ELIGIBLE
    c6_modifier = c6_buff.effects[0]
    assert isinstance(c6_modifier.result.value, ScenarioParameterDerivedValue)
    assert c6_modifier.result.value.parameter_id == str(BANYUE_MINGWANG_STACK_COUNT)
    assert c6_modifier.result.value.coefficient.value == pytest.approx(0.08)
    assert c6_modifier.result.value.cap_max.value == pytest.approx(0.24)
    uncertain_base = next(
        item for item in c6_buff.effects if isinstance(item, UnresolvedEffect)
    )
    assert uncertain_base.unresolved.reason.value == "ambiguous-text"
    assert isinstance(
        uncertain_base.rule.condition, ScenarioParameterRangeCondition
    )
    assert uncertain_base.rule.condition.parameter_id == str(BANYUE_MINGWANG_STACK_COUNT)
    assert uncertain_base.rule.condition.minimum == 1
    assert any(
        isinstance(item, DamageDealerFilter) and item.character_id == BANYUE_ID
        for item in uncertain_base.rule.filters
    )
    assert any(
        isinstance(item, DamageTypeFilter)
        and item.damage_type is DamageType.PENETRATION
        for item in uncertain_base.rule.filters
    )
    assert any(
        isinstance(item, ElementFilter) and item.element is Element.FIRE
        for item in uncertain_base.rule.filters
    )
    assert c6_buff.original_text == raw.mindscapes[5].description

    _, eligible_c6 = _definition(
        BanYueCompileConfig(cinema_level=6, additional_ability_eligible=True)
    )
    assert _rule(
        eligible_c6, "extra-ability:mingwang-fire-damage"
    ).eligibility is RuleEligibility.ELIGIBLE
    eligible_c6_rule = _rule(
        eligible_c6, "cinema6:mingwang-fire-damage-increase"
    )
    assert not any(isinstance(item, UnresolvedEffect) for item in eligible_c6_rule.effects)
    eligible_base = next(
        item
        for item in _rule(eligible_c6, "extra-ability:mingwang-fire-damage").effects
        if hasattr(item, "result")
    )
    eligible_c6_bonus = next(
        item for item in eligible_c6_rule.effects if hasattr(item, "result")
    )
    assert eligible_base.result.value.coefficient.value == pytest.approx(0.05)
    assert eligible_c6_bonus.result.value.coefficient.value == pytest.approx(0.08)
    assert (
        eligible_base.result.value.coefficient.value
        + eligible_c6_bonus.result.value.coefficient.value
    ) == pytest.approx(0.13)

    c6_event_rule = _rule(c6, "cinema6:cuiyue-fire-burst")
    assert c6_event_rule.eligibility is RuleEligibility.ELIGIBLE
    c6_event = next(
        item
        for item in c6.damage_event_templates
        if item.ref.template_id
        == EventTemplateId("template:character:1471:cinema6-cuiyue-fire-burst")
    )
    assert c6_event.move_id is None
    assert c6_event.ref.skill_group is None
    assert not c6_event.ref.damage_tags
    assert c6_event.element is Element.FIRE
    c6_ratio = next(
        item
        for item in c6.independent_derived_damage_events
        if item.template.template_id == c6_event.ref.template_id
    )
    assert c6_ratio.multiplier.value.value == pytest.approx(6.0)
    creation = next(
        effect
        for effect in c6_event_rule.effects
        if isinstance(effect, EventCreationEffect)
    )
    parent_filter = next(
        item
        for item in creation.rule.filters
        if isinstance(item, EventTemplateIdFilter)
    )
    assert parent_filter.template_id == EventTemplateId(
        "template:character:1471:basic-cuiyue:main"
    )
    assert "600%" in c6_event_rule.original_text

    core = _rule(c6, "core:enhanced-special-assist-buffs")
    core_fire_effect = next(
        item
        for item in core.effects
        if item.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    )
    assert any(
        isinstance(item, DamageTypeFilter)
        and item.damage_type is DamageType.PENETRATION
        for item in core_fire_effect.rule.filters
    )
    assert any(
        isinstance(item, ElementFilter) and item.element is Element.FIRE
        for item in core_fire_effect.rule.filters
    )
    assert not _move_ids(core_fire_effect)
    assert not any(
        isinstance(item, EventTemplateIdFilter)
        for item in core_fire_effect.rule.filters
    )


def test_cuiyue_authored_followup_is_an_independent_basic_event_with_own_curve() -> None:
    raw, definition = _definition()
    cuiyue = _entry(definition, "basic-cuiyue")
    assert cuiyue.derived_damage_events == ()
    followup = next(
        item
        for item in definition.independent_derived_damage_events
        if item.template.template_id
        == EventTemplateId("template:character:1471:basic-cuiyue-auto-qingshan")
    )
    followup_template = next(
        item
        for item in definition.damage_event_templates
        if item.ref.template_id == followup.template.template_id
    )
    assert followup_template.move_id == BANYUE_BASIC_QINGSHAN_MOVE_ID
    assert followup.template.skill_group is SkillGroup.BASIC_ATTACK
    assert followup.template.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert followup.template.element is Element.FIRE
    qingshan_parameter = next(
        item
        for item in next(
            item for item in raw.moves if item.name == "普通攻击：倾山"
        ).parameters
        if item.name == "伤害倍率"
    )
    assert followup.multiplier.value.value == pytest.approx(
        qingshan_parameter.value_for_level(12) / 100
    )
    assert "随后般岳将自动释放" in cuiyue.original_text

    rule = _rule(definition, "skill:cuiyue-qingshan-followup")
    assert rule.eligibility is RuleEligibility.ELIGIBLE
    creation = next(item for item in rule.effects if isinstance(item, EventCreationEffect))
    parent_filter = next(
        item
        for item in creation.rule.filters
        if isinstance(item, EventTemplateIdFilter)
    )
    assert parent_filter.template_id == cuiyue.main_damage_event.template_id
    assert followup_template.move_id != cuiyue.move_id


def test_cinema_1_2_and_4_effects_keep_their_authored_recipient_and_move_scope() -> None:
    _, definition = _definition(BanYueCompileConfig(cinema_level=4))
    c1_resist = _rule(definition, "cinema1:tremor-fire-resistance-reduction")
    resist_effect = c1_resist.effects[0]
    assert resist_effect.rule.target is EffectTarget.ENEMY
    assert resist_effect.result.modifier_path is CalculationNode.ENEMY_RESISTANCE_REDUCTION
    assert resist_effect.result.value.value == pytest.approx(0.1)
    assert c1_resist.condition_ids == (
        next(
            item.condition_id
            for item in definition.scenario_conditions
            if str(item.condition_id) == "condition:banyue:tremor-active"
        ),
    )

    c1_damage = _rule(definition, "cinema1:tremor-listed-move-penetration-damage")
    c1_effect = c1_damage.effects[0]
    assert c1_effect.result.value.value == pytest.approx(0.1)
    assert c1_effect.result.modifier_path is CalculationNode.PENETRATION_DAMAGE_BONUS
    assert _move_ids(c1_effect) == {
        "move:banyue:ex-shizihou",
        "move:banyue:ex-shizihou-rage",
        "move:banyue:ex-shanyao",
        "move:banyue:ex-shanyao-rage",
        "move:banyue:basic-qingshan",
        "move:banyue:basic-cuiyue",
    }
    assert any(
        isinstance(nested, EventTemplateIdFilter)
        and nested.template_id
        == EventTemplateId("template:character:1471:basic-cuiyue-auto-qingshan")
        for item in c1_effect.rule.filters
        if isinstance(item, AnyFilter)
        for nested in item.filters
    )
    assert EventTemplateId("template:character:1471:cinema6-cuiyue-fire-burst") not in {
        nested.template_id
        for item in c1_effect.rule.filters
        if isinstance(item, AnyFilter)
        for nested in item.filters
        if isinstance(nested, EventTemplateIdFilter)
    }

    c2 = _rule(definition, "cinema2:core-buff-increase")
    assert {item.result.modifier_path for item in c2.effects} == {
        CalculationNode.DAMAGE_NORMAL_BONUS,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
    }
    assert all(item.result.value.value == pytest.approx(0.15) for item in c2.effects)
    assert c2.condition_ids == _rule(
        definition, "core:enhanced-special-assist-buffs"
    ).condition_ids

    c4 = _rule(definition, "cinema4:listed-move-damage")
    assert c4.effects[0].result.value.value == pytest.approx(0.3)
    assert _move_ids(c4.effects[0]) == {
        "move:banyue:ex-shizihou-rage",
        "move:banyue:ex-shanyao-rage",
        "move:banyue:basic-qingshan",
        "move:banyue:basic-cuiyue",
    }
    assert EventTemplateId("template:character:1471:cinema6-cuiyue-fire-burst") not in {
        nested.template_id
        for item in c4.effects[0].rule.filters
        if isinstance(item, AnyFilter)
        for nested in item.filters
        if isinstance(nested, EventTemplateIdFilter)
    }


def test_cinema_three_and_five_apply_shared_skill_level_rule_to_ultimate() -> None:
    selected = (CharacterSkillLevel(SkillGroup.ULTIMATE, 12),)
    c3 = BanYueCompileConfig(cinema_level=3, skill_levels=selected)
    c5 = BanYueCompileConfig(cinema_level=5, skill_levels=selected)
    assert effective_skill_level(c3, SkillGroup.ULTIMATE) == 14
    assert effective_skill_level(c5, SkillGroup.ULTIMATE) == 16
    assert effective_skill_level(c5, SkillGroup.BASIC_ATTACK) == 16


def test_config_rejects_wrong_identity_and_out_of_range_levels() -> None:
    with pytest.raises(ValueError, match="character:1471"):
        BanYueCompileConfig(character_id=type(BANYUE_ID)("character:1421"))
    with pytest.raises(ValueError, match="core_level"):
        BanYueCompileConfig(core_level=8)
    with pytest.raises(ValueError, match="cinema_level"):
        BanYueCompileConfig(cinema_level=7)


def test_banyue_api_keeps_c6_only_mingwang_base_partial_and_known_c6_bonus() -> None:
    character = str(BANYUE_ID)
    preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": character,
            "team_character_ids": [character],
            "compile_config": {"core_level": 7, "cinema_level": 6},
        },
    )
    assert preview.status_code == 200, preview.text
    preview_payload = preview.json()
    assert len(preview_payload["moves"]) == 24
    field_ids = {item["field_id"] for item in preview_payload["compile_config_fields"]}
    assert {"core_level", "cinema_level"}.issubset(field_ids)
    assert "additional_ability_eligible" not in field_ids
    rules = {item["rule_id"]: item for item in preview_payload["rule_items"]}
    assert rules["rule:character:1471:extra-ability:mingwang-fire-damage"][
        "eligibility"
    ] == "ineligible"
    assert rules["rule:character:1471:cinema6:mingwang-fire-damage-increase"][
        "eligibility"
    ] == "eligible"

    force_enabled = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": character,
            "team_character_ids": [character],
            "compile_config": {
                "core_level": 7,
                "cinema_level": 6,
                "additional_ability_eligible": True,
            },
        },
    )
    assert force_enabled.status_code == 400

    payload = {
        "primary_character_id": character,
        "supporting_character_ids": [],
        "team_character_ids": [character],
        "move_entry_id": "move-entry:character:1471:basic-cuiyue",
        "compile_configs": {character: {"core_level": 7, "cinema_level": 6}},
        "condition_values": {
            "condition:banyue:core-enhanced-special-or-assist-buff-active": False,
            "condition:banyue:tremor-active": False,
        },
        "parameter_values": {
            "parameter:character:1471:mingwang-current-stacks": 3,
        },
        "character_builds": {
            character: {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 10000.0,
                    "attack": 1000.0,
                    "defense": 500.0,
                    "impact": 95.0,
                    "crit_rate": 0.5,
                    "crit_damage": 0.5,
                    "anomaly_mastery": 90.0,
                    "anomaly_proficiency": 89.0,
                    "energy_regen": 0.0,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"fire": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:banyue-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"fire": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [
            "rule:character:1471:cinema6:mingwang-fire-damage-increase",
            "rule:character:1471:cinema6:cuiyue-fire-burst",
        ],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["events"][0]["modes"]["expected"]["status"] == "blocked"
    assert result["totals"]["expected"]["complete"] is False
    base_partial = next(
        item
        for item in result["diagnostics"]
        if "character:1471:cinema6:mingwang-base-bonus-eligibility" in item[
            "diagnostic_id"
        ]
    )
    assert base_partial["blocking"] is True
    fire_burst = next(
        (
            item
            for item in result["events"]
            if item["semantic_id"].startswith(
                "event:character:1471:cinema6-cuiyue-fire-burst:source:event:"
            )
        ),
        None,
    )
    assert fire_burst is not None, [item["semantic_id"] for item in result["events"]]
    assert fire_burst["damage_type"] == "penetration"
    assert fire_burst["element"] == "fire"
    assert fire_burst["modes"]["expected"]["status"] == "blocked"
    assert any(
        modifier["effect_id"]
        == "effect:character:1471:cinema6:mingwang-fire-damage-increase"
        and modifier["value"] == pytest.approx(0.24)
        for modifier in fire_burst["common_application_trace"]["applied_modifiers"]
    )
    known_bonus_applications = [
        modifier
        for event in result["events"]
        for modifier in event["common_application_trace"]["applied_modifiers"]
        if modifier["effect_id"]
        == "effect:character:1471:cinema6:mingwang-fire-damage-increase"
    ]
    assert known_bonus_applications
    assert all(item["value"] == pytest.approx(0.24) for item in known_bonus_applications)

    disabled_payload = {
        **payload,
        "compile_configs": {character: {"core_level": 7, "cinema_level": 0}},
        "enabled_rule_item_ids": [],
        "parameter_values": {},
    }
    disabled_response = client.post(
        "/api/v1/moves/calculate", json=disabled_payload
    )
    assert disabled_response.status_code == 200, disabled_response.text
    disabled_result = disabled_response.json()
    assert disabled_result["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert disabled_result["totals"]["expected"]["complete"] is True
    assert not any(
        "cinema6:mingwang-base-bonus-eligibility" in item["diagnostic_id"]
        for item in disabled_result["diagnostics"]
    )
    with pytest.raises(ValueError, match="unique"):
        BanYueCompileConfig(
            skill_levels=(
                CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 10),
                CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 12),
            )
        )
