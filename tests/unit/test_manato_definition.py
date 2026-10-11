from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.manato import (
    MANATO_ID,
    MANATO_REVIEWED_MAPPING,
    ManatoCompileConfig,
    compile_manato,
    load_raw_record,
)
from core.application.characters.nanoka_compiler import (
    effective_skill_level,
    raw_move_index,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    load_wengine_raw_record,
    signature_wengine_id_for,
)
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import (
    character_base_stat_contributions,
    character_base_stats,
)
from core.presentation.catalog import (
    supported_character_catalog,
    supported_wengine_catalog,
)
from core.presentation.registry import (
    _manato_additional_ability_eligibility,
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.application.scenario import ConditionResolution, ParameterResolution
from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterRole,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    Element,
    ElementFilter,
    EffectTarget,
    CurrentAttackValueSource,
    CurrentPenetrationForceValueSource,
    EventTemplateIdFilter,
    MoveIdFilter,
    PanelStatDerivedValue,
    ScenarioParameterDerivedValue,
    SkillGroup,
    CharacterId,
    WEngineId,
)
from web.api import app


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "manato.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1441.json"
client = TestClient(app)


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _definition(config: ManatoCompileConfig | None = None):
    raw = load_raw_record(_source_data())
    return raw, compile_manato(config or ManatoCompileConfig(), raw)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1441:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _rule(definition, key: str):
    rule_id = f"rule:character:1441:{key}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _resolved_multiplier(variant) -> float:
    return variant.multiplier.value.value


def _modifier(rule):
    assert len(rule.effects) == 1
    return rule.effects[0]


def test_manato_source_identity_and_complete_provenance_are_reviewed() -> None:
    data = _source_data()
    raw = load_raw_record(data)

    assert data["source_version"] == SOURCE_VERSION
    assert data["source_url"] == SOURCE_URL
    assert raw.source_version == SOURCE_VERSION
    assert raw.source_url == SOURCE_URL
    assert raw.character_id == MANATO_ID
    assert raw.name == "真斗"
    assert raw.code_name == "Manato"
    assert raw.rarity == 3
    assert raw.specialty == "命破"
    assert raw.element == "火属性"
    assert raw.faction == "怪啖屋"
    assert raw.icon == "IconRole51"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert raw.potential_details == ()

    definition = compile_manato(ManatoCompileConfig(), raw)
    assert definition.character_id == MANATO_ID
    assert definition.role is CharacterRole.RUPTURE
    assert definition.base_element is Element.FIRE


def test_manato_registry_level_60_panel_catalog_and_signature_are_connected() -> None:
    assert str(MANATO_ID) in supported_character_ids()
    raw = load_raw_record(load_character_record(str(MANATO_ID)))
    assert raw.code_name == "Manato"
    assert raw.source_url == SOURCE_URL

    panel = character_base_stats(MANATO_ID)
    assert panel.hp.value == pytest.approx(7724.8563)
    assert panel.attack.value == pytest.approx(755.2106)
    assert panel.defense.value == pytest.approx(443.56)
    assert panel.impact.value == pytest.approx(95.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.50)
    assert panel.anomaly_mastery.value == pytest.approx(87.0)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    hp_percent = next(
        item
        for item in character_base_stat_contributions(MANATO_ID)
        if item.stat.value == "hp"
    )
    assert hp_percent.value.value == pytest.approx(0.18)

    registration = registration_for(MANATO_ID)
    assert registration.role is CharacterRole.RUPTURE
    assert registration.base_element is Element.FIRE
    assert registration.equipment_capabilities.possible_elements == frozenset(
        {Element.PHYSICAL, Element.FIRE}
    )
    assert registration.equipment_capabilities.damage_tags == frozenset(
        tag for move in MANATO_REVIEWED_MAPPING.moves for tag in move.damage_tags
    )

    assert _manato_additional_ability_eligibility(
        (MANATO_ID, CharacterId("character:1311"))
    )  # Astra is Support.
    assert _manato_additional_ability_eligibility(
        (MANATO_ID, CharacterId("character:1361"))
    )  # Trigger is Stun.
    assert not _manato_additional_ability_eligibility(
        (MANATO_ID, CharacterId("character:1421"))
    )

    weapon_id = WEngineId("wengine:13144")
    assert SIGNATURE_WENGINE_BY_CHARACTER[MANATO_ID] == weapon_id
    assert signature_wengine_id_for(MANATO_ID) == weapon_id
    weapon_raw = load_wengine_raw_record(weapon_id)
    weapon_data = json.loads(
        (PROJECT_ROOT / "core" / "data" / "wengines" / "13144.json").read_text(
            encoding="utf-8"
        )
    )
    assert weapon_data["raw_nanoka_detail"]["code_name"] == "Weapon_A_1441"
    assert weapon_raw.wengine_id == weapon_id
    engine_catalog = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert engine_catalog[str(weapon_id)].signature_character_id == str(MANATO_ID)
    character_catalog = {
        item.character_id: item for item in supported_character_catalog()
    }
    assert character_catalog[str(MANATO_ID)].code_name == "Manato"
    assert character_catalog[str(MANATO_ID)].rarity == "A"
    assert character_catalog[str(MANATO_ID)].specialty == "rupture"

    fields = {
        item.field_id: item
        for item in config_fields_for(MANATO_ID, {}, (MANATO_ID,))
    }
    assert fields["core_level"].value == 7
    assert fields["cinema_level"].value == 6
    assert "additional_ability_eligible" not in fields
    assert len(compile_registered_definition(
        MANATO_ID,
        {"core_level": 7, "cinema_level": 6},
        (MANATO_ID,),
    ).move_entries) == 19


def test_manato_registered_api_preview_and_fire_penetration_calculation() -> None:
    preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": str(MANATO_ID),
            "team_character_ids": [str(MANATO_ID)],
            "compile_config": {"core_level": 7, "cinema_level": 6},
        },
    )
    assert preview.status_code == 200, preview.text
    preview_payload = preview.json()
    assert preview_payload["schema_version"] == "presentation-v1"
    assert preview_payload["character_id"] == str(MANATO_ID)
    assert len(preview_payload["moves"]) == 19
    field_ids = {item["field_id"] for item in preview_payload["compile_config_fields"]}
    assert {"core_level", "cinema_level"}.issubset(field_ids)
    assert "additional_ability_eligible" not in field_ids

    payload = {
        "primary_character_id": str(MANATO_ID),
        "supporting_character_ids": [],
        "team_character_ids": [str(MANATO_ID)],
        "move_entry_id": "move-entry:character:1441:basic-ember-stage-1",
        "compile_configs": {
            str(MANATO_ID): {"core_level": 7, "cinema_level": 6}
        },
        "condition_values": {"condition:manato:ember-edge-active": True},
        "parameter_values": {},
        "character_builds": {
            str(MANATO_ID): {
                "level": 60,
                "out_of_combat_stats": {
                    "hp": 10000.0,
                    "attack": 1000.0,
                    "defense": 500.0,
                    "impact": 95.0,
                    "crit_rate": 0.5,
                    "crit_damage": 0.5,
                    "anomaly_mastery": 87.0,
                    "anomaly_proficiency": 90.0,
                    "energy_regen": 0.0,
                    "penetration_rate": 0.0,
                    "penetration_flat": 0.0,
                    "element_damage_bonus": {"fire": 0.0},
                },
            }
        },
        "enemy": {
            "enemy_id": "enemy:manato-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"fire": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["damage_type"] == "penetration"
    assert event["element"] == "fire"
    assert event["modes"]["expected"]["status"] == "calculated"
    snapshot = next(
        item
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == str(MANATO_ID)
    )
    assert snapshot["stats"]["hp"] == pytest.approx(10000.0)
    assert snapshot["stats"]["attack"] == pytest.approx(1000.0)

    weapon_preview = client.post(
        "/api/v1/wengines/preview",
        json={
            "wengine_id": "wengine:13144",
            "equipped_character_id": str(MANATO_ID),
            "team_character_ids": [str(MANATO_ID)],
            "level": 60,
            "refinement": 1,
            "condition_values": {},
        },
    )
    assert weapon_preview.status_code == 200, weapon_preview.text
    fire_rule = next(
        item
        for item in weapon_preview.json()["rule_items"]
        if item["rule_id"] == "rule:wengine:13144:owner:1441:fire-damage"
    )
    assert fire_rule["eligibility"] == "eligible"


def test_every_reviewed_damage_variant_uses_its_source_curve_and_typed_event() -> None:
    raw, definition = _definition()
    raw_moves = raw_move_index(raw)
    typed_templates = {
        item.ref.template_id: item for item in definition.damage_event_templates
    }

    assert len(definition.move_entries) == len(MANATO_REVIEWED_MAPPING.moves) == 19
    assert len(definition.damage_event_templates) == len(definition.move_entries) + 1
    assert not definition.independent_derived_damage_events
    assert all(not item.blocking for item in definition.diagnostics)

    for spec in MANATO_REVIEWED_MAPPING.moves:
        entry = _entry(definition, spec.entry_key)
        raw_move = raw_moves[spec.source_name]
        assert entry.original_text == raw_move.description
        assert entry.move_id == spec.move_id
        assert entry.skill_group is spec.skill_group
        assert entry.damage_tags == spec.damage_tags
        assert entry.multiplier_relation is spec.multiplier_relation
        assert entry.main_damage_event.skill_group is spec.skill_group
        assert entry.main_damage_event.damage_tags == spec.damage_tags
        assert entry.main_damage_event.element is spec.element

        template = typed_templates[entry.main_damage_event.template_id]
        assert template.move_id == spec.move_id
        if spec.element is Element.PHYSICAL:
            assert entry.main_damage_event.damage_type is DamageType.DIRECT
            assert isinstance(template.base_source, CurrentAttackValueSource)
        else:
            assert spec.element is Element.FIRE
            assert entry.main_damage_event.damage_type is DamageType.PENETRATION
            assert isinstance(template.base_source, CurrentPenetrationForceValueSource)

        expected_level = effective_skill_level(
            ManatoCompileConfig(), spec.parameter_skill_group or spec.skill_group
        )
        for parameter_spec, variant in zip(spec.parameters, entry.multiplier_variants):
            parameter = next(
                item
                for item in raw_move.parameters
                if item.name == parameter_spec.parameter_name
            )
            if parameter_spec.source_skill_components:
                expected = sum(
                    parameter.value_for_level(expected_level, skill_id) * coefficient
                    for skill_id, coefficient in parameter_spec.source_skill_components
                )
            else:
                expected = parameter.value_for_level(
                    expected_level, parameter_spec.source_skill_id
                )
            assert expected is not None
            assert _resolved_multiplier(variant) == pytest.approx(expected / 100.0)


def test_ember_edge_is_a_whole_fire_basic_variant_using_the_explicit_sum() -> None:
    raw, definition = _definition()
    raw_basic = raw_move_index(raw)["普通攻击：炽风斩"]
    assert "烬风" in raw_basic.description
    assert "在每一段攻击的发动阶段" in raw_basic.description
    assert "使此次攻击造成更高" in raw_basic.description
    assert "火属性伤害" in raw_basic.description

    for stage, source_ids in (
        (1, ("1441001", "1441006")),
        (2, ("1441002", "1441007")),
        (3, ("1441004", "1441008")),
    ):
        regular = _entry(definition, f"basic-stage-{stage}")
        ember = _entry(definition, f"basic-ember-stage-{stage}")
        assert ember.move_id == regular.move_id
        assert ember.skill_group is regular.skill_group is SkillGroup.BASIC_ATTACK
        assert ember.damage_tags == regular.damage_tags == regular.main_damage_event.damage_tags
        assert ember.main_damage_event.element is Element.FIRE
        assert ember.main_damage_event.damage_type is DamageType.PENETRATION
        assert len(ember.multiplier_variants) == 1
        assert ember.multiplier_relation.value == "sequential-stage"
        spec = next(
            item
            for item in MANATO_REVIEWED_MAPPING.moves
            if item.entry_key == f"basic-ember-stage-{stage}"
        )
        assert tuple(skill_id for skill_id, _ in spec.parameters[0].source_skill_components) == source_ids
        assert ember.derived_damage_events == ()


def test_support_followup_uses_only_the_two_explicit_mutually_exclusive_curves() -> None:
    raw, definition = _definition()
    entry = _entry(definition, "support-follow-up-breaking-fang")
    assert entry.multiplier_relation.value == "mutually-exclusive-variant"
    assert len(entry.multiplier_variants) == 2
    assert all(item.condition_ids for item in entry.multiplier_variants)
    assert entry.multiplier_variants[0].parameter_name == "伤害倍率"
    assert entry.multiplier_variants[1].parameter_name == "连打最大伤害倍率"
    assert entry.multiplier_variants[1].label == "连打模式起手斩击倍率"
    assert entry.multiplier_variants[1].condition_ids != entry.multiplier_variants[0].condition_ids
    assert len(entry.derived_damage_events) == 1
    continuous = entry.derived_damage_events[0]
    assert str(continuous.template.source_rule_item_id) == (
        "rule:character:1441:skill:support-follow-up-continuous-slashes"
    )
    assert str(continuous.template.template_id) == (
        "template:character:1441:support-follow-up-continuous-slashes"
    )
    assert str(continuous.template.semantic_id) == (
        "event:character:1441:support-follow-up-continuous-slashes"
    )
    continuous_typed_template = next(
        item
        for item in definition.damage_event_templates
        if item.ref.template_id == continuous.template.template_id
    )
    assert continuous_typed_template.move_id is None
    assert str(continuous.template.skill_group.value) == "assist"
    assert {item.value for item in continuous.template.damage_tags} == {
        "assist-damage",
        "follow-up-attack-damage",
    }
    assert continuous.template.element is Element.FIRE
    assert continuous.template.damage_type is DamageType.PENETRATION
    assert continuous.multiplier.value.value == pytest.approx(
        next(
            item.value_for_level(16, "1441025") / 100.0
            for item in raw_move_index(raw)["支援突击：孤影·断獠"].parameters
            if item.name == "连打最大伤害倍率"
        )
    )
    assert not definition.independent_derived_damage_events


@pytest.mark.parametrize(
    ("core_level", "fire_bonus", "hp_spend_crit_damage"),
    ((1, 0.10, 0.25), (7, 0.20, 0.50)),
)
def test_core_level_curves_are_read_from_the_selected_raw_level(
    core_level: int,
    fire_bonus: float,
    hp_spend_crit_damage: float,
) -> None:
    raw = load_raw_record(_source_data())
    definition = compile_manato(
        ManatoCompileConfig(core_level=core_level, cinema_level=0), raw
    )
    core = raw.core_levels[core_level - 1]

    force_effect = _modifier(
        _rule(definition, "core:extra-penetration-force-from-current-max-hp")
    )
    force_value = force_effect.result.value
    assert isinstance(force_value, PanelStatDerivedValue)
    assert force_value.source_node is CalculationNode.CHARACTER_CURRENT_MAX_HP
    assert force_value.coefficient.value == pytest.approx(0.10)
    assert force_effect.rule.target is EffectTarget.SELF
    assert force_effect.rule.filters == (DamageTypeFilter(DamageType.PENETRATION),)

    ember = _rule(definition, "core:ember-edge-fire-damage")
    fire_effect = _modifier(ember)
    assert ember.original_text == core.description
    assert fire_effect.result.value.value == pytest.approx(fire_bonus)
    assert fire_effect.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert fire_effect.rule.filters == (
        DamageTypeFilter(DamageType.PENETRATION),
        ElementFilter(Element.FIRE),
    )

    crit_effect = _modifier(_rule(definition, "core:ember-edge-crit-rate"))
    assert crit_effect.result.value.value == pytest.approx(0.10)
    assert _rule(definition, "core:ember-edge-crit-rate").condition_ids

    spending = _rule(definition, "core:hp-spending-attack-crit-damage")
    spending_effect = _modifier(spending)
    assert spending.original_text == core.description
    assert spending_effect.result.value.value == pytest.approx(hp_spend_crit_damage)
    assert "condition:manato:hp-spending-attack-active" in spending.condition_ids
    spending_scope = next(
        item for item in spending_effect.rule.filters if isinstance(item, AnyFilter)
    )
    assert {
        str(item.move_id)
        for item in spending_scope.filters
        if isinstance(item, MoveIdFilter)
    } == {"move:manato:basic-blazing-wind-hidden-cut"}
    assert EventTemplateIdFilter(
        "template:character:1441:support-follow-up-continuous-slashes"
    ) in spending_scope.filters


def test_user_selected_state_and_cinema_parameters_do_not_guess_combat_history() -> None:
    raw, definition = _definition(ManatoCompileConfig(cinema_level=6))
    conditions = {str(item.condition_id): item for item in definition.scenario_conditions}
    assert conditions["condition:manato:ember-edge-active"].resolution is ConditionResolution.USER_SELECTED
    assert conditions["condition:manato:ember-edge-active"].value is False
    assert conditions["condition:manato:hp-spending-attack-active"].resolution is ConditionResolution.USER_SELECTED
    assert conditions["condition:manato:hp-spending-attack-active"].value is False

    parameters = {str(item.parameter_id): item for item in definition.scenario_parameters}
    c1 = parameters["parameter:character:1441:cinema1:accumulated-hp-loss-basis-points"]
    assert c1.resolution is ParameterResolution.USER_SELECTED
    assert c1.value is None
    assert (c1.minimum, c1.maximum) == (0, 5000)
    assert "历史累计已损失" in c1.original_text
    assert "不是当前生命值比例" in c1.original_text
    assert "每单位0.01%" in c1.original_text

    c1_rule = _rule(definition, "cinema1:accumulated-hp-loss-fire-damage")
    c1_effect = _modifier(c1_rule)
    c1_value = c1_effect.result.value
    assert isinstance(c1_value, ScenarioParameterDerivedValue)
    assert c1_value.coefficient.value == pytest.approx(0.00004)
    assert c1_value.cap_max.value == pytest.approx(0.20)
    assert c1_effect.rule.filters[:2] == (
        DamageTypeFilter(DamageType.PENETRATION),
        ElementFilter(Element.FIRE),
    )
    c1_any_filter = next(item for item in c1_effect.rule.filters if isinstance(item, AnyFilter))
    assert {item.damage_tag for item in c1_any_filter.filters if isinstance(item, DamageTagFilter)} == {
        DamageTag.BASIC_ATTACK,
        DamageTag.FOLLOW_UP_ATTACK,
    }
    assert c1_rule.original_text == raw.mindscapes[0].description

    c6 = parameters["parameter:character:1441:cinema6:fire-damage-stacks"]
    assert c6.resolution is ParameterResolution.USER_SELECTED
    assert c6.value is None
    assert (c6.minimum, c6.maximum) == (0, 5)
    assert c6.original_text == raw.mindscapes[5].description


def test_cinemas_have_source_scoped_effects_and_no_seed_c6_leakage() -> None:
    raw = load_raw_record(_source_data())
    definition = compile_manato(ManatoCompileConfig(cinema_level=6), raw)

    c2 = _rule(definition, "cinema2:ember-edge-fire-resistance-ignore")
    c2_effect = _modifier(c2)
    assert c2.original_text == raw.mindscapes[1].description
    assert c2_effect.result.value.value == pytest.approx(0.08)
    assert c2_effect.result.modifier_path is CalculationNode.DAMAGE_RESISTANCE_IGNORE
    assert c2_effect.rule.target is EffectTarget.ENEMY
    assert "condition:manato:ember-edge-active" in c2.condition_ids
    assert DamageTypeFilter(DamageType.PENETRATION) in c2_effect.rule.filters
    assert ElementFilter(Element.FIRE) in c2_effect.rule.filters

    c4 = _rule(definition, "cinema4:max-hp-bonus")
    assert c4.original_text == raw.mindscapes[3].description
    assert _modifier(c4).result.modifier_path is CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS
    assert _modifier(c4).result.value.value == pytest.approx(0.08)
    assert "致命伤害" in c4.original_text  # kept source-only; no fabricated event rule

    c6_rule = _rule(definition, "cinema6:current-fire-damage-stacks")
    c6_effect = _modifier(c6_rule)
    c6_value = c6_effect.result.value
    assert c6_rule.original_text == raw.mindscapes[5].description
    assert "提升3%" in c6_rule.original_text
    assert "最多叠加5层" in c6_rule.original_text
    assert isinstance(c6_value, ScenarioParameterDerivedValue)
    assert c6_value.coefficient.value == pytest.approx(0.03)
    assert c6_value.cap_max.value == pytest.approx(0.15)
    c6_rule_ids = {
        str(item.rule_id)
        for item in definition.rule_items
        if ":cinema6:" in str(item.rule_id)
    }
    assert c6_rule_ids == {"rule:character:1441:cinema6:current-fire-damage-stacks"}
    assert not any("激光" in item.display_name for item in definition.rule_items)


def test_cinema_skill_bonus_includes_ultimate_and_caps_at_sixteen() -> None:
    raw = load_raw_record(_source_data())
    selected = (CharacterSkillLevel(SkillGroup.ULTIMATE, 12),)
    c3 = ManatoCompileConfig(cinema_level=3, skill_levels=selected)
    c5 = ManatoCompileConfig(cinema_level=5, skill_levels=selected)
    assert effective_skill_level(c3, SkillGroup.ULTIMATE) == 14
    assert effective_skill_level(c5, SkillGroup.ULTIMATE) == 16

    source_parameter = next(
        item
        for item in raw_move_index(raw)["终结技：无想荒魂"].parameters
        if item.name == "伤害倍率"
    )
    for config, level in ((c3, 14), (c5, 16)):
        definition = compile_manato(config, raw)
        ultimate = _entry(definition, "ultimate-unthinking-soul")
        assert _resolved_multiplier(ultimate.multiplier_variants[0]) == pytest.approx(
            source_parameter.value_for_level(level, "1441019") / 100.0
        )
    for level in (3, 5):
        assert _rule(compile_manato(ManatoCompileConfig(cinema_level=level), raw), f"cinema{level}:skill-levels").original_text == raw.mindscapes[level - 1].description


@pytest.mark.parametrize("eligible", (False, True))
def test_extra_ability_source_is_retained_without_empty_resource_rules(eligible: bool) -> None:
    raw = load_raw_record(_source_data())
    definition = compile_manato(ManatoCompileConfig(additional_ability_eligible=eligible), raw)
    assert raw.extra_ability_description
    assert not any("extra-ability" in str(item.rule_id) for item in definition.rule_items)
    assert any("资源和时间不属于静态伤害输出" in item for item in MANATO_REVIEWED_MAPPING.data_quality_notes)
