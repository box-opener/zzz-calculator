from __future__ import annotations

import json

import pytest

from core.application.characters.yixuan import (
    YIXUAN_ID,
    YIXUAN_REVIEWED_MAPPING,
    YixuanCompileConfig,
    compile_yixuan,
    load_raw_record,
)
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import DamageType, Element


YIXUAN = str(YIXUAN_ID)
ASTRA = "character:1311"
TRIGGER = "character:1361"
BASIC_ONE = "move-entry:character:1371:basic-xiaoyun-jin-1"
CLOUD_ENTRY = "move-entry:character:1371:ex-condense-cloud-technique"
ANOMALY_ENTRY = "move-entry:character:1371:xuanmo-anomaly"
DISORDER_ENTRY = "move-entry:character:1371:xuanmo-disorder"


def _stats(
    element: str = "ether",
    *,
    hp: float = 12000.0,
    attack: float = 1000.0,
    crit_rate: float = 0.70,
    crit_damage: float = 1.10,
    element_bonus: float = 0.40,
) -> dict[str, object]:
    return {
        "hp": hp,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: element_bonus},
    }


def _drive_discs():
    def substats(*keys: str):
        return [{"stat": key, "roll_count": 2} for key in keys]

    return [
        {"slot": 1, "set_id": "drive-disc:31000", "main_stat": "hp-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 2, "set_id": "drive-disc:31000", "main_stat": "attack-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 3, "set_id": "drive-disc:31000", "main_stat": "defense-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 4, "set_id": "drive-disc:31000", "main_stat": "attack-percent", "substats": substats("crit-rate", "crit-damage", "anomaly-proficiency-flat", "penetration-flat")},
        {"slot": 5, "set_id": "drive-disc:31000", "main_stat": "ether-damage-bonus", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 6, "set_id": "drive-disc:31000", "main_stat": "hp-percent", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
    ]


def _payload(
    *,
    move_entry_id: str = BASIC_ONE,
    core_level: int = 1,
    cinema_level: int = 0,
    supporting: tuple[str, ...] = (),
    primary: str = YIXUAN,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    rule_stack_counts: dict[str, int] | None = None,
    is_stunned: bool = False,
    initial_defense: float = 1000.0,
    equipment_build: bool = False,
) -> dict[str, object]:
    team = (primary, *supporting)
    compile_configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        if character_id == YIXUAN:
            compile_configs[character_id] = {
                "core_level": core_level,
                "cinema_level": cinema_level,
            }
            builds[character_id] = (
                {"level": 60, "build_mode": "equipment-build", "drive_discs": _drive_discs()}
                if equipment_build
                else {"level": 60, "out_of_combat_stats": _stats()}
            )
        elif character_id == ASTRA:
            compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": _stats(
                    crit_rate=0.50,
                    crit_damage=0.30,
                    element_bonus=0.0,
                ),
            }
        elif character_id == TRIGGER:
            compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": _stats(crit_rate=0.50, element_bonus=0.0),
            }
        else:
            raise AssertionError(f"missing test build for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": condition_values or {},
        "parameter_values": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:yixuan-test",
            "level": 60,
            "initial_defense": initial_defense,
            "damage_resistance": {"ether": 0.20},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": is_stunned,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
    }


def _event(result: dict[str, object], semantic_id: str | None = None):
    events = result["events"]
    assert isinstance(events, list)
    return (
        next(item for item in events if item["semantic_id"] == semantic_id)
        if semantic_id is not None
        else events[0]
    )


def _breakdown(event, mode: str = "expected"):
    return event["modes"][mode]["calculation_breakdown"]


def _node(event, name: str, mode: str = "expected"):
    return next(item for item in _breakdown(event, mode) if item["node"] == name)


def _applied(event):
    return event["common_application_trace"]["applied_modifiers"]


def _modifier(event, effect_id: str):
    return next(item for item in _applied(event) if item["effect_id"] == effect_id)


def _yixuan_raw():
    return load_raw_record(load_character_record(YIXUAN))


def test_yixuan_live_raw_mapping_and_level_60_equipment_panel() -> None:
    raw_dict = load_character_record(YIXUAN)
    raw = load_raw_record(raw_dict)
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1371.json"
    assert raw.name == "仪玄"
    assert raw.element == "以太"
    assert raw.special_element == "玄墨"
    assert raw.character_id == YIXUAN_ID
    assert YIXUAN in supported_character_ids()

    # Every raw damage curve is represented.  The three guard-support curves
    # are daze-only and intentionally never become DamageMove entries.
    reviewed = {
        (spec.source_name, parameter.parameter_name, parameter.source_skill_id)
        for spec in YIXUAN_REVIEWED_MAPPING.moves
        for parameter in spec.parameters
    }
    raw_damage_curves = {
        (move.name, parameter.name, skill_id)
        for move in raw.moves
        for parameter in move.parameters
        if parameter.format == "%"
        and "伤害倍率" in parameter.name
        for skill_id, _values in parameter.source_curves
    }
    derived = {
        ("普通攻击：霄云劲", "五段伤害倍率", "1371006"),
        ("普通攻击：青溟震击", "伤害倍率", "1371007"),
        ("强化特殊技：墨烬影消", "伤害倍率", "1371026"),
        ("强化特殊技：墨痕化形", "蓄力完成追加伤害倍率", "1371024"),
    }
    assert raw_damage_curves == reviewed | derived
    assert not any("招架支援：清霄劲" in item.source_name for item in YIXUAN_REVIEWED_MAPPING.moves)

    registration = registration_for(YIXUAN)
    assert registration.role.value == "rupture"
    assert registration.base_element is Element.ETHER
    assert registration.equipment_capabilities.possible_elements == {
        Element.ETHER,
        Element.XUANMO,
    }
    base = character_base_stats(YIXUAN)
    assert base.hp.value == pytest.approx(8373.8621)
    assert base.attack.value == pytest.approx(872.5748)
    assert base.crit_rate.value == pytest.approx(0.194)
    assert base.anomaly_mastery.value == pytest.approx(92.0)
    assert base.anomaly_proficiency.value == pytest.approx(90.0)

    fields = config_fields_for(YIXUAN, {"core_level": 6, "cinema_level": 4}, (YIXUAN,))
    assert {field.field_id for field in fields} >= {"core_level", "cinema_level", "skill_level:ultimate"}


def test_real_calculate_payload_uses_current_yixuan_penetration_force_and_no_defense() -> None:
    low_defense = calculate_payload(_payload(initial_defense=1000.0))
    high_defense = calculate_payload(_payload(initial_defense=100000.0))
    event = _event(low_defense)
    high_event = _event(high_defense)
    assert event["damage_type"] == DamageType.PENETRATION.value
    assert event["modes"]["non-crit"]["value"] == pytest.approx(1494.08)
    assert event["modes"]["expected"]["value"] == pytest.approx(2644.5216)
    assert event["modes"]["full-crit"]["value"] == pytest.approx(3137.568)
    assert _node(event, "penetration.force")["value"] == pytest.approx(1450.0)
    assert _node(event, "damage.skill-multiplier")["value"] == pytest.approx(0.92)
    assert _node(event, "resistance.region")["value"] == pytest.approx(0.80)
    assert event["modes"]["expected"]["value"] == pytest.approx(
        high_event["modes"]["expected"]["value"]
    )
    assert not any("defense" in item["node"] for item in _breakdown(event))
    assert [item["read_rule"] for item in _breakdown(event) if item["node"] == "penetration.force"] == ["settlement"]


def test_core_and_additional_ability_effects_apply_only_to_listed_yixuan_moves() -> None:
    enabled = ("rule:character:1371:core:listed-move-damage",)
    core1 = calculate_payload(
        _payload(move_entry_id=CLOUD_ENTRY, core_level=1, enabled_rule_item_ids=enabled)
    )
    core7 = calculate_payload(
        _payload(move_entry_id=CLOUD_ENTRY, core_level=7, enabled_rule_item_ids=enabled)
    )
    core1_event = _event(core1)
    core7_event = _event(core7)
    assert _node(core1_event, "damage.normal-bonus")["value"] == pytest.approx(0.30)
    assert _node(core7_event, "damage.normal-bonus")["value"] == pytest.approx(0.60)
    assert _node(core7_event, "damage.base-value")["value"] == pytest.approx(1450.0 * 13.439)
    assert not any("defense" in item["node"] for item in _breakdown(core7_event))

    # Ordinary basic and normal-special moves are deliberately outside the
    # named core-passive scope.
    ordinary_basic = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:basic-ink-shadow-gathering",
            core_level=7,
            enabled_rule_item_ids=enabled,
        )
    )
    ordinary_special = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:special-jin-ying-jue",
            core_level=7,
            enabled_rule_item_ids=enabled,
        )
    )
    assert _node(_event(ordinary_basic), "damage.normal-bonus")["value"] == pytest.approx(0.0)
    assert _node(_event(ordinary_special), "damage.normal-bonus")["value"] == pytest.approx(0.0)

    extra_id = "rule:character:1371:extra-ability:stunned-ex-special-damage"
    stunned = calculate_payload(
        _payload(
            move_entry_id=CLOUD_ENTRY,
            core_level=1,
            supporting=(ASTRA,),
            is_stunned=True,
            enabled_rule_item_ids=(extra_id,),
        )
    )
    not_stunned = calculate_payload(
        _payload(
            move_entry_id=CLOUD_ENTRY,
            core_level=1,
            supporting=(ASTRA,),
            is_stunned=False,
            enabled_rule_item_ids=(extra_id,),
        )
    )
    assert _node(_event(stunned), "damage.normal-bonus")["value"] == pytest.approx(0.30)
    assert _node(_event(not_stunned), "damage.normal-bonus")["value"] == pytest.approx(0.0)


def test_cinema_modifiers_keep_their_move_and_damage_type_scopes() -> None:
    c2_rule = "rule:character:1371:cinema2:resistance-ignore"
    c2 = compile_yixuan(
        YixuanCompileConfig(cinema_level=2),
        _yixuan_raw(),
    )
    assert "move-entry:character:1371:cinema2-ex-talisman-break" in {
        str(item.entry_id) for item in c2.move_entries
    }
    c0 = compile_yixuan(YixuanCompileConfig(), _yixuan_raw())
    assert "move-entry:character:1371:cinema2-ex-talisman-break" not in {
        str(item.entry_id) for item in c0.move_entries
    }
    c2_result = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:ultimate-qingming-cloud-shadow",
            cinema_level=2,
            enabled_rule_item_ids=(c2_rule,),
        )
    )
    c2_event = _event(c2_result)
    assert _node(c2_event, "resistance.damage-ignore")["value"] == pytest.approx(0.15)
    assert _node(c2_event, "resistance.region")["value"] == pytest.approx(0.95)
    assert c2_event["modes"]["expected"]["status"] == "calculated"

    c4_rule = "rule:character:1371:cinema4:stillness-damage"
    c4_definition = compile_yixuan(
        YixuanCompileConfig(cinema_level=4),
        _yixuan_raw(),
    )
    c4_compiled_rule = next(
        item for item in c4_definition.rule_items if str(item.rule_id) == c4_rule
    )
    assert (c4_compiled_rule.stack_count, c4_compiled_rule.stack_max) == (2, 2)
    c4 = calculate_payload(
        _payload(
            move_entry_id=CLOUD_ENTRY,
            cinema_level=4,
            enabled_rule_item_ids=(c4_rule,),
        )
    )
    assert _node(_event(c4), "damage.normal-bonus")["value"] == pytest.approx(0.60)
    assert _modifier(
        _event(c4), "effect:character:1371:cinema4:stillness-damage"
    )["value"] == pytest.approx(0.60)

    c6_rule = "rule:character:1371:cinema6:focused-penetration-damage"
    focused = calculate_payload(
        _payload(
            cinema_level=6,
            supporting=(ASTRA,),
            condition_values={"condition:yixuan:focused-mind-active": True},
            enabled_rule_item_ids=(c6_rule,),
        )
    )
    assert _node(_event(focused), "penetration.damage-bonus")["value"] == pytest.approx(0.20)

    ineligible = calculate_payload(
        _payload(
            cinema_level=6,
            condition_values={"condition:yixuan:focused-mind-active": True},
            enabled_rule_item_ids=(c6_rule,),
        )
    )
    assert _node(_event(ineligible), "penetration.damage-bonus")["value"] == pytest.approx(0.0)
    ineligible_rule = next(
        item
        for item in compile_registered_definition(
            YIXUAN,
            {"core_level": 1, "cinema_level": 6},
            (YIXUAN,),
        ).rule_items
        if str(item.rule_id) == c6_rule
    )
    assert ineligible_rule.eligibility is RuleEligibility.INELIGIBLE

    c2_branch = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:cinema2-ex-talisman-break",
            cinema_level=2,
            condition_values={"condition:yixuan:c2-ink-break-ready": True},
            enabled_rule_item_ids=(c2_rule,),
        )
    )
    assert _node(_event(c2_branch), "damage.skill-multiplier")["value"] == pytest.approx(12.0)
    assert _node(_event(c2_branch), "resistance.damage-ignore")["value"] == pytest.approx(0.15)


def test_c6_extra_ultimate_has_known_force_damage_and_requires_eligibility() -> None:
    rule_id = "rule:character:1371:cinema6:extra-ultimate"
    active = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:ultimate-qingming-cloud-shadow",
            cinema_level=6,
            supporting=(ASTRA,),
            condition_values={"condition:yixuan:c6-extra-ultimate-active": True},
            enabled_rule_item_ids=(rule_id,),
        )
    )
    events = active["events"]
    assert len(events) == 2
    child = events[1]
    assert child["label"] == "6影：调息追加终结技·符法千重"
    assert child["damage_type"] == "penetration"
    assert child["modes"]["expected"]["known_value"] is not None
    assert child["common_application_trace"]["created_by_effect_id"] == (
        "effect:character:1371:cinema6:extra-ultimate"
    )

    ineligible = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:ultimate-qingming-cloud-shadow",
            cinema_level=6,
            condition_values={"condition:yixuan:c6-extra-ultimate-active": True},
            enabled_rule_item_ids=(rule_id,),
        )
    )
    assert len(ineligible["events"]) == 1


def test_focused_mind_is_a_yixuan_panel_buff_and_does_not_change_teammate_crit_damage() -> None:
    rule_id = "rule:character:1371:extra-ability:focused-mind-crit-damage"
    focused = calculate_payload(
        _payload(
            supporting=(ASTRA,),
            condition_values={"condition:yixuan:focused-mind-active": True},
            enabled_rule_item_ids=(rule_id,),
        )
    )
    yixuan_snapshot = next(
        item for item in focused["resolved_character_snapshots"]
        if item["character_id"] == YIXUAN
    )
    assert yixuan_snapshot["stats"]["crit_damage"] == pytest.approx(1.50)
    assert _node(_event(focused), "character.current.crit-damage")["value"] == pytest.approx(1.50)
    assert _event(focused)["common_application_trace"]["event_stat_modifiers"] == []
    assert any(
        item["recipient_character_id"] == YIXUAN
        and item["effect_id"] == "effect:character:1371:extra-ability:focused-mind-crit-damage"
        for item in focused["panel_traces"]
    )

    teammate = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(YIXUAN,),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            condition_values={"condition:yixuan:focused-mind-active": True},
            enabled_rule_item_ids=(rule_id,),
        )
    )
    teammate_event = _event(teammate)
    yixuan_support_snapshot = next(
        item for item in teammate["resolved_character_snapshots"]
        if item["character_id"] == YIXUAN
    )
    astra_snapshot = next(
        item for item in teammate["resolved_character_snapshots"]
        if item["character_id"] == ASTRA
    )
    assert yixuan_support_snapshot["stats"]["crit_damage"] == pytest.approx(1.50)
    assert astra_snapshot["stats"]["crit_damage"] == pytest.approx(0.30)
    assert _node(teammate_event, "character.current.crit-damage")["value"] == pytest.approx(0.30)


def test_yixuan_effects_do_not_leak_to_a_teammate_event() -> None:
    core_rule = "rule:character:1371:core:listed-move-damage"
    teammate = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(YIXUAN,),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            core_level=7,
            enabled_rule_item_ids=(core_rule,),
        )
    )
    event = _event(teammate)
    assert event["damage_type"] == "direct"
    assert _node(event, "damage.normal-bonus")["value"] == pytest.approx(0.0)
    assert not any(
        item["effect_id"].startswith("effect:character:1371:")
        for item in _applied(event)
    )


def test_c1_lightning_is_typed_xuanmo_penetration_and_uses_yixuan_force() -> None:
    rule_id = "rule:character:1371:cinema1:lightning"
    yixuan_hit = calculate_payload(
        _payload(
            cinema_level=1,
            enabled_rule_item_ids=(rule_id,),
        )
    )
    assert len(yixuan_hit["events"]) == 2
    assert yixuan_hit["totals"]["expected"]["complete"] is True
    lightning = next(
        item for item in yixuan_hit["events"]
        if item["semantic_id"].startswith("event:character:1371:cinema1-lightning:source:")
    )
    assert lightning["damage_type"] == "penetration"
    assert _node(lightning, "penetration.force")["value"] == pytest.approx(1450.0)
    assert _node(lightning, "damage.base-value")["value"] == pytest.approx(725.0)
    definition = compile_yixuan(YixuanCompileConfig(cinema_level=1), _yixuan_raw())
    lightning_template = next(
        item for item in definition.damage_event_templates
        if str(item.ref.template_id) == "template:character:1371:cinema1-lightning"
    )
    assert lightning_template.damage_dealer == YIXUAN
    assert lightning_template.element is Element.XUANMO
    assert lightning_template.move_id is None
    assert lightning_template.ref.skill_group is None
    assert lightning_template.ref.damage_tags == frozenset()
    assert _node(_event(yixuan_hit), "character.current.crit-rate")["value"] == pytest.approx(0.70)

    team_direct = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(YIXUAN,),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            cinema_level=1,
            enabled_rule_item_ids=(rule_id,),
        )
    )
    assert _event(team_direct)["damage_type"] == "direct"
    assert team_direct["totals"]["expected"]["complete"] is True
    assert len(team_direct["events"]) == 2
    teammate_lightning = next(
        item for item in team_direct["events"]
        if item["semantic_id"].startswith("event:character:1371:cinema1-lightning:source:")
    )
    assert teammate_lightning["damage_type"] == "penetration"
    assert _node(teammate_lightning, "damage.base-value")["value"] == pytest.approx(725.0)

    extra_rule = "rule:character:1371:extra-ability:lightning"
    support_switch = _payload(
        cinema_level=0,
        supporting=(ASTRA,),
        enabled_rule_item_ids=(extra_rule,),
        condition_values={
            "condition:yixuan:perfect-support-switch-out-active": True,
        },
    )
    support_switch["selected_trigger_inputs"] = [
        {
            "input_id": "scenario-trigger:effect:character:1371:extra-ability:lightning:actor",
            "actor_id": ASTRA,
        }
    ]
    support_result = calculate_payload(support_switch)
    assert support_result["totals"]["expected"]["complete"] is True
    assert len(support_result["events"]) == 2
    extra_lightning = _event(support_result, "event:character:1371:extra-ability-lightning")
    assert extra_lightning["damage_type"] == "penetration"
    assert _node(extra_lightning, "damage.base-value")["value"] == pytest.approx(3262.5)


def test_c1_lightning_uses_one_unique_instance_per_source_hit_without_recursion() -> None:
    c1_rule = "rule:character:1371:cinema1:lightning"
    followup_rule = "rule:character:1371:followup:basic-array-qingming-shock"
    result = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1371:basic-xuanmo-array",
            cinema_level=1,
            enabled_rule_item_ids=(c1_rule, followup_rule),
        )
    )
    assert len(result["events"]) == 4
    assert result["totals"]["expected"]["complete"] is True
    lightning = [
        item for item in result["events"]
        if item["semantic_id"].startswith("event:character:1371:cinema1-lightning:source:")
    ]
    assert len(lightning) == 2
    assert lightning[0]["semantic_id"] != lightning[1]["semantic_id"]
    assert all(_node(item, "damage.base-value")["value"] == pytest.approx(725.0) for item in lightning)
    for event in result["events"][:2]:
        trace = event["common_application_trace"]
        matching = [item for item in trace["rule_matches"] if item["rule_id"] == c1_rule]
        assert len(matching) == 1
        assert matching[0]["status"] == "matched"


def test_static_xuanmo_anomaly_and_disorder_use_the_ether_record_not_penetration() -> None:
    core6_rule = "rule:character:1371:core:listed-move-damage"
    c4_rule = "rule:character:1371:cinema4:stillness-damage"
    c6_rule = "rule:character:1371:cinema6:focused-penetration-damage"
    enabled = (core6_rule, c4_rule, c6_rule)
    condition_values = {"condition:yixuan:focused-mind-active": True}
    stacks = {c4_rule: 2}
    anomaly = calculate_payload(
        _payload(
            move_entry_id=ANOMALY_ENTRY,
            core_level=7,
            cinema_level=6,
            supporting=(ASTRA,),
            enabled_rule_item_ids=enabled,
            condition_values=condition_values,
            rule_stack_counts=stacks,
        )
    )
    disorder = calculate_payload(
        _payload(
            move_entry_id=DISORDER_ENTRY,
            core_level=7,
            cinema_level=6,
            supporting=(ASTRA,),
            enabled_rule_item_ids=enabled,
            condition_values=condition_values,
            rule_stack_counts=stacks,
        )
    )
    anomaly_event = _event(anomaly)
    disorder_event = _event(disorder)
    assert anomaly_event["damage_type"] == "anomaly"
    assert anomaly_event["repeat_count"] == 20
    assert _node(anomaly_event, "anomaly.attribute.multiplier")["value"] == pytest.approx(0.625)
    assert _node(anomaly_event, "anomaly.effect-strength")["value"] == pytest.approx(2800.0)
    assert _node(anomaly_event, "resistance.region")["value"] == pytest.approx(0.80)
    assert _node(disorder_event, "disorder.total-multiplier")["value"] == pytest.approx(17.0)
    assert _node(disorder_event, "anomaly.effect-strength")["value"] == pytest.approx(2800.0)
    assert _node(disorder_event, "damage.base-value")["value"] == pytest.approx(47600.0)
    for event in (anomaly_event, disorder_event):
        assert not any(item["node"].startswith("penetration.") for item in _breakdown(event))
        assert not any(
            item["effect_id"].startswith("effect:character:1371:")
            for item in _applied(event)
        )
    assert anomaly["totals"]["expected"]["complete"] is True
    assert disorder["totals"]["expected"]["complete"] is True


def test_equipment_build_includes_yixuan_level_60_base_hp_and_attack() -> None:
    result = calculate_payload(_payload(equipment_build=True))
    resolved = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == YIXUAN
    )
    assert resolved["stats"]["hp"] > 8373.8621
    assert resolved["stats"]["attack"] > 872.5748
    assert result["build_provenance"]
