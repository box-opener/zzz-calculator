from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import raw_move_index
from core.application.characters.yinhu import (
    YINHU_ID,
    YINHU_REVIEWED_MAPPING,
    YinhuCompileConfig,
    compile_yinhu,
    load_raw_record,
)
from core.application.characters.yinhu.reviewed import YINHU_QI_JUE_ACTIVE
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    load_wengine_raw_record,
)
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import (
    CharacterId,
    DamageType,
    DamageTypeFilter,
    EffectTarget,
    Element,
    NotCondition,
    RuleStackCondition,
    SkillGroup,
)
from web.api import app


YINHU = str(YINHU_ID)
YIDHARI = "character:1051"
YIXUAN = "character:1371"
ANBY = "character:1011"
_RAW_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1421.json"
_CORE_RULE = "rule:character:1421:core:tongqiao-penetration-force:character-1051"
_CINEMA6_RULE = "rule:character:1421:cinema6:core-enhanced-selection"
_QI_JUE_CONDITION = str(YINHU_QI_JUE_ACTIVE)


def _raw():
    return load_raw_record(load_character_record(YINHU))


def _stats(attack: float) -> dict[str, object]:
    return {
        "hp": 12000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": 0.05,
        "crit_damage": 0.50,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 90.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.0, "ice": 0.0},
    }


def _payload(
    primary: str,
    supports: tuple[str, ...],
    move_entry_id: str,
    *,
    yinhu_core: int = 7,
    yinhu_cinema: int = 6,
    yinhu_attack: float = 4000.0,
    condition_values: dict[str, bool] | None = None,
    enabled_rules: tuple[str, ...] = (),
) -> dict[str, object]:
    team = (primary, *supports)
    builds: dict[str, dict[str, object]] = {}
    configs: dict[str, dict[str, int]] = {}
    for character_id in team:
        attack = yinhu_attack if character_id == YINHU else 1000.0
        builds[character_id] = {
            "level": 60,
            "out_of_combat_stats": _stats(attack),
        }
        configs[character_id] = (
            {"core_level": yinhu_core, "cinema_level": yinhu_cinema}
            if character_id == YINHU
            else {"core_level": 7, "cinema_level": 0}
        )
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supports),
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": condition_values or {},
        "parameter_values": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:yinhu-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.0, "ice": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rules),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    return calculate_payload(payload)


def _node(
    event: dict[str, object], node_id: str, *, default: float | None = None
) -> float:
    rows = event["modes"]["expected"]["calculation_breakdown"]
    row = next((row for row in rows if row["node"] == node_id), None)
    if row is None:
        if default is not None:
            return default
        raise AssertionError(f"calculation breakdown has no {node_id} node")
    return row["value"]


def test_yinhu_live_source_provenance_panel_catalog_signature_and_skill_curves() -> None:
    raw = _raw()
    assert raw.source_version == "3.2"
    assert raw.source_url == _RAW_URL
    assert raw.character_id == YINHU_ID
    assert raw.name == "潘引壶"
    assert raw.code_name == "Yinhu"
    assert raw.rarity == 3
    assert raw.specialty == "防护"
    assert raw.element == "物理"
    assert YINHU in supported_character_ids()

    panel = character_base_stats(YINHU_ID)
    assert panel.hp.value == pytest.approx(8453.7942)
    assert panel.attack.value == pytest.approx(661.9158)
    assert panel.defense.value == pytest.approx(712.9433)
    assert panel.impact.value == pytest.approx(94.0)
    assert panel.energy_regen.value == pytest.approx(1.56)

    registration = registration_for(YINHU_ID)
    assert registration.role.value == "defense"
    assert registration.base_element is Element.PHYSICAL
    catalog_item = next(
        item for item in supported_character_catalog() if item.character_id == YINHU
    )
    assert (catalog_item.display_name, catalog_item.rarity, catalog_item.specialty) == (
        "潘引壶",
        "A",
        "defense",
    )
    assert str(SIGNATURE_WENGINE_BY_CHARACTER[YINHU_ID]) == "wengine:13142"
    weapon = load_wengine_raw_record("wengine:13142")
    assert weapon.name == "震元奇枢"

    fields = {item.field_id: item for item in config_fields_for(YINHU_ID, {}, (YINHU,))}
    assert fields["core_level"].value == 7
    assert fields["cinema_level"].value == 6
    assert all(
        fields[f"skill_level:{group.value}"].value == 16
        for group in SkillGroup
    )

    definition = compile_yinhu(YinhuCompileConfig(), raw)
    raw_moves = raw_move_index(raw)
    assert len(definition.move_entries) == len(YINHU_REVIEWED_MAPPING.moves) == 15
    assert len(definition.damage_event_templates) == 15
    assert not definition.diagnostics
    for spec, entry in zip(YINHU_REVIEWED_MAPPING.moves, definition.move_entries):
        parameter_spec = spec.parameters[0]
        source_parameter = next(
            item
            for item in raw_moves[spec.source_name].parameters
            if item.name == parameter_spec.parameter_name
        )
        expected = source_parameter.value_for_level(
            16, parameter_spec.source_skill_id
        )
        assert expected is not None
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(
            expected / 100.0
        )
        assert entry.main_damage_event.damage_type is DamageType.DIRECT
        assert entry.main_damage_event.element is Element.PHYSICAL
        assert entry.damage_tags == spec.damage_tags

    assert not any(
        item.main_damage_event.damage_type in {DamageType.ANOMALY, DamageType.DISORDER}
        for item in definition.move_entries
    )
    assert {item.skill_group for item in definition.move_entries} >= {
        SkillGroup.BASIC_ATTACK,
        SkillGroup.DODGE,
        SkillGroup.SPECIAL_ATTACK,
        SkillGroup.CHAIN_ATTACK,
        SkillGroup.ULTIMATE,
        SkillGroup.ASSIST,
    }


def test_yinhu_cinema3_skill_bonus_caps_at_sixteen_and_resource_cinemas_are_omitted() -> None:
    raw = _raw()
    basic_spec = next(
        item for item in YINHU_REVIEWED_MAPPING.moves if item.entry_key == "basic-stage-1"
    )
    source_parameter = next(
        item
        for item in raw_move_index(raw)[basic_spec.source_name].parameters
        if item.name == basic_spec.parameters[0].parameter_name
    )
    selected = CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 12)
    at_cinema_zero = compile_yinhu(
        YinhuCompileConfig(cinema_level=0, skill_levels=(selected,)), raw
    )
    at_cinema_three = compile_yinhu(
        YinhuCompileConfig(cinema_level=3, skill_levels=(selected,)), raw
    )
    at_cinema_five = compile_yinhu(
        YinhuCompileConfig(cinema_level=5, skill_levels=(selected,)), raw
    )
    at_level_sixteen = compile_yinhu(
        YinhuCompileConfig(
            cinema_level=3,
            skill_levels=(CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 16),),
        ),
        raw,
    )
    zero_multiplier = at_cinema_zero.move_entries[0].multiplier_variants[0].multiplier.value.value
    three_multiplier = at_cinema_three.move_entries[0].multiplier_variants[0].multiplier.value.value
    five_multiplier = at_cinema_five.move_entries[0].multiplier_variants[0].multiplier.value.value
    capped_multiplier = at_level_sixteen.move_entries[0].multiplier_variants[0].multiplier.value.value
    assert zero_multiplier == pytest.approx(
        source_parameter.value_for_level(12, "1421001") / 100.0
    )
    assert three_multiplier == pytest.approx(
        source_parameter.value_for_level(14, "1421001") / 100.0
    )
    assert five_multiplier == pytest.approx(
        source_parameter.value_for_level(16, "1421001") / 100.0
    )
    assert capped_multiplier == pytest.approx(
        source_parameter.value_for_level(16, "1421001") / 100.0
    )
    rule_ids = {str(item.rule_id) for item in at_cinema_three.rule_items}
    assert not any(":cinema2:" in item or ":cinema4:" in item for item in rule_ids)
    cinema6_rule = next(
        item for item in at_cinema_three.rule_items
        if str(item.rule_id) == _CINEMA6_RULE
    )
    assert cinema6_rule.eligibility.value == "ineligible"
    assert (cinema6_rule.stack_count, cinema6_rule.stack_min, cinema6_rule.stack_max) == (
        1,
        1,
        1,
    )
    assert not any(item.blocking for item in at_cinema_three.diagnostics)


def test_yinhu_recipient_configuration_rejects_the_owner() -> None:
    with pytest.raises(ValueError, match="cannot be selected as a next-agent recipient"):
        YinhuCompileConfig(penetration_recipient_ids=(YINHU_ID,))


@pytest.mark.parametrize(
    ("core_level", "cinema_enabled", "core_enabled", "expected"),
    (
        (1, False, True, 360.0),
        (2, False, True, 420.0),
        (3, False, True, 480.0),
        (4, False, True, 540.0),
        (5, False, True, 540.0),
        (6, False, True, 540.0),
        (7, False, True, 540.0),
        (1, True, True, 600.0),
        (7, True, True, 720.0),
        (7, True, False, 0.0),
    ),
)
def test_yinhu_penetration_force_uses_exact_core_and_cinema6_cap(
    core_level: int,
    cinema_enabled: bool,
    core_enabled: bool,
    expected: float,
) -> None:
    enabled = []
    if core_enabled:
        enabled.append(_CORE_RULE)
    if cinema_enabled:
        enabled.append(_CINEMA6_RULE)
    result = _calculate(
        _payload(
            YIDHARI,
            (YINHU,),
            "move-entry:character:1051:basic-shattered-strike-1",
            yinhu_core=core_level,
            yinhu_cinema=6,
            condition_values={
                "condition:yinhu:core:tongqiao-active:character-1051": True
            },
            enabled_rules=tuple(enabled),
        )
    )
    event = result["events"][0]
    assert event["damage_type"] == "penetration"
    assert _node(event, "penetration.force-bonus", default=0.0) == pytest.approx(expected)
    assert result["totals"]["expected"]["complete"] is True


def test_yinhu_locked_cinema6_cannot_select_the_enhanced_core_branch() -> None:
    result = _calculate(
        _payload(
            YIDHARI,
            (YINHU,),
            "move-entry:character:1051:basic-shattered-strike-1",
            yinhu_core=7,
            yinhu_cinema=5,
            condition_values={
                "condition:yinhu:core:tongqiao-active:character-1051": True
            },
            enabled_rules=(_CORE_RULE, _CINEMA6_RULE),
        )
    )
    assert _node(result["events"][0], "penetration.force-bonus") == pytest.approx(540.0)


def test_yinhu_penetration_force_is_explicitly_scoped_to_selected_recipient_and_damage_type() -> None:
    team = (YIDHARI, YINHU)
    definition = compile_registered_definition(
        YINHU,
        {"core_level": 7, "cinema_level": 6},
        team,
    )
    core_rule = next(
        item for item in definition.rule_items if str(item.rule_id) == _CORE_RULE
    )
    base_effect, cinema_effect = core_rule.effects
    assert base_effect.rule.recipient_character_id == CharacterId(YIDHARI)
    assert cinema_effect.rule.recipient_character_id == CharacterId(YIDHARI)
    assert base_effect.rule.target is EffectTarget.RECIPIENT
    assert cinema_effect.rule.target is EffectTarget.RECIPIENT
    assert base_effect.rule.filters == (DamageTypeFilter(DamageType.PENETRATION),)
    assert cinema_effect.rule.filters == (DamageTypeFilter(DamageType.PENETRATION),)
    assert isinstance(base_effect.rule.condition, NotCondition)
    assert isinstance(base_effect.rule.condition.condition, RuleStackCondition)
    assert base_effect.rule.condition.condition.requires_rule_enabled is True
    assert isinstance(cinema_effect.rule.condition, RuleStackCondition)
    assert cinema_effect.rule.condition.requires_rule_enabled is True
    assert definition.scenario_conditions[0].value is False

    direct_definition = compile_registered_definition(
        ANBY,
        {"core_level": 7, "cinema_level": 0},
        (ANBY, YINHU),
    )
    direct_move = next(
        item
        for item in direct_definition.move_entries
        if item.main_damage_event.damage_type is DamageType.DIRECT
    )
    result = _calculate(
        _payload(
            ANBY,
            (YINHU,),
            str(direct_move.entry_id),
            condition_values={
                "condition:yinhu:core:tongqiao-active:character-1011": True
            },
            enabled_rules=(
                "rule:character:1421:core:tongqiao-penetration-force:character-1011",
            ),
        )
    )
    event = result["events"][0]
    assert event["damage_type"] == "direct"
    assert not any(
        item["effect_id"].startswith("effect:character:1421:core:tongqiao")
        for item in event["common_application_trace"]["applied_modifiers"]
    )


def test_yinhu_qi_jue_bonus_is_conditioned_normal_bonus_for_eligible_team() -> None:
    team = (YIXUAN, YINHU)
    definition = compile_registered_definition(
        YINHU,
        {"core_level": 7, "cinema_level": 1},
        team,
    )
    extra_rule = next(
        item
        for item in definition.rule_items
        if str(item.rule_id) == "rule:character:1421:extra-ability:qi-jue-normal-damage"
    )
    cinema1_rule = next(
        item
        for item in definition.rule_items
        if str(item.rule_id) == "rule:character:1421:cinema1:qi-jue-normal-damage"
    )
    assert extra_rule.eligibility.value == "eligible"
    assert cinema1_rule.eligibility.value == "eligible"
    assert extra_rule.effects[0].result.modifier_path.value == "damage.normal-bonus"
    assert cinema1_rule.effects[0].result.modifier_path.value == "damage.normal-bonus"
    assert extra_rule.effects[0].rule.target is EffectTarget.ENEMY
    assert cinema1_rule.effects[0].rule.target is EffectTarget.ENEMY

    move_entry = "move-entry:character:1371:basic-xuanmo-array"
    active = _calculate(
        _payload(
            YIXUAN,
            (YINHU,),
            move_entry,
            yinhu_cinema=1,
            condition_values={_QI_JUE_CONDITION: True},
            enabled_rules=(
                "rule:character:1421:extra-ability:qi-jue-normal-damage",
                "rule:character:1421:cinema1:qi-jue-normal-damage",
            ),
        )
    )
    inactive = _calculate(
        _payload(
            YIXUAN,
            (YINHU,),
            move_entry,
            yinhu_cinema=1,
            enabled_rules=(
                "rule:character:1421:extra-ability:qi-jue-normal-damage",
                "rule:character:1421:cinema1:qi-jue-normal-damage",
            ),
        )
    )
    active_event = active["events"][0]
    inactive_event = inactive["events"][0]
    assert _node(active_event, "damage.normal-bonus") == pytest.approx(0.30)
    assert _node(inactive_event, "damage.normal-bonus") == pytest.approx(0.0)
    assert all(
        item["modifier_path"] != "vulnerability.enemy-normal"
        for item in active_event["common_application_trace"]["applied_modifiers"]
        if item["effect_id"].startswith("effect:character:1421:")
    )

    solo = compile_registered_definition(
        YINHU,
        {"core_level": 7, "cinema_level": 1},
        (YINHU,),
    )
    solo_extra = next(
        item
        for item in solo.rule_items
        if str(item.rule_id) == "rule:character:1421:extra-ability:qi-jue-normal-damage"
    )
    assert solo_extra.eligibility.value == "ineligible"
    assert not solo.scenario_conditions


def test_yinhu_penetration_request_returns_through_calculate_api() -> None:
    payload = _payload(
        YIDHARI,
        (YINHU,),
        "move-entry:character:1051:basic-shattered-strike-1",
        condition_values={
            "condition:yinhu:core:tongqiao-active:character-1051": True
        },
        enabled_rules=(_CORE_RULE,),
    )
    response = TestClient(app).post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert _node(result["events"][0], "penetration.force-bonus") == pytest.approx(540.0)
