from __future__ import annotations

from copy import deepcopy

import pytest

from core.application.characters.miyabi import (
    MIYABI_C6_SLASH_COUNT_PARAMETER_ID,
    MiyabiCompileConfig,
    compile_miyabi,
    load_raw_record as load_miyabi_raw_record,
)
from core.application.characters.miyabi.reviewed import (
    FROSTBURN_BREAK_READY,
    FROSTMOON_CHARGE_1,
    FROSTMOON_CHARGE_2,
    FROSTMOON_CHARGE_3,
    FROSTSCORCH_ACTIVE,
    FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE,
    ICEFIRE_ACTIVE,
    MIYABI_ID,
    MIYABI_REVIEWED_MAPPING,
    MIYABI_UNRESOLVED_MULTIPLIERS,
    NEXT_FROSTMOON_AFTER_DISORDER,
    ULTIMATE_ICE_BONUS_ACTIVE,
)
from core.application.characters.nanoka_compiler import raw_move_index
from core.application.rules import RuleEligibility
from core.application.execution.event_factory import instantiate_direct_damage_event
from core.application.execution.router import CalculationRouter
from core.application.output import EventCalculationStatus
from core.data.loader import load_character_record
from core.calculation import CalculationResult
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import compile_registered_definition
from core.types import (
    Element,
    Resolved,
    Unresolved,
    UnresolvedReason,
)


MIYABI = str(MIYABI_ID)
ANOMALY_ENTRY = "move-entry:character:1091:lieshuang-anomaly"
DISORDER_ENTRY = "move-entry:character:1091:lieshuang-disorder"
FROSTMOON_ENTRY = "move-entry:character:1091:frostmoon-charge"
KAZAHANA_1_ENTRY = "move-entry:character:1091:kazahana-1"
ICEFIRE_RULE = "rule:character:1091:core:icefire-buildup"
FROSTBURN_RULE = "rule:character:1091:core:frostburn-break"
C2_RULE = "rule:character:1091:cinema2"
C4_RULE = "rule:character:1091:cinema4"
C6_FROSTMOON_RULE = "rule:character:1091:cinema6:frostmoon-damage"
CORE_BREACH_EFFECT = "effect:character:1091:core:frostburn-break"


def _stats(
    element: str,
    *,
    attack: float = 1000.0,
    crit_rate: float = 0.70,
    crit_damage: float = 0.50,
    anomaly_mastery: float = 116.0,
    anomaly_proficiency: float = 238.0,
    element_damage_bonus: float = 0.0,
):
    return {
        "hp": 10000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "anomaly_mastery": anomaly_mastery if element == "ice" else 100.0,
        "anomaly_proficiency": anomaly_proficiency if element == "ice" else 100.0,
        "energy_regen": 1.2,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: element_damage_bonus},
    }


def _drive_discs():
    def substats(*keys: str):
        return [{"stat": key, "roll_count": 2} for key in keys]

    return [
        {"slot": 1, "set_id": "drive-disc:31000", "main_stat": "hp-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 2, "set_id": "drive-disc:31000", "main_stat": "attack-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 3, "set_id": "drive-disc:31000", "main_stat": "defense-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 4, "set_id": "drive-disc:31000", "main_stat": "attack-percent", "substats": substats("crit-rate", "crit-damage", "anomaly-proficiency-flat", "penetration-flat")},
        {"slot": 5, "set_id": "drive-disc:31000", "main_stat": "ice-damage-bonus", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 6, "set_id": "drive-disc:31000", "main_stat": "anomaly-mastery-percent", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
    ]


def _miyabi_payload(
    *,
    move_entry_id: str = KAZAHANA_1_ENTRY,
    core_level: int = 1,
    cinema_level: int = 0,
    supporting: tuple[str, ...] = (),
    primary: str = MIYABI,
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    crit_rate: float = 0.70,
    crit_damage: float = 0.50,
    anomaly_mastery: float = 116.0,
    anomaly_proficiency: float = 238.0,
    ice_damage_bonus: float = 0.0,
    equipment_build: bool = False,
) -> dict[str, object]:
    team = (primary, *supporting)
    compile_configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        if character_id == MIYABI:
            compile_configs[character_id] = {
                "core_level": core_level,
                "cinema_level": cinema_level,
            }
            if equipment_build:
                builds[character_id] = {
                    "level": 60,
                    "build_mode": "equipment-build",
                    "drive_discs": _drive_discs(),
                }
            else:
                builds[character_id] = {
                    "level": 60,
                    "out_of_combat_stats": _stats(
                        "ice",
                        crit_rate=crit_rate,
                        crit_damage=crit_damage,
                        anomaly_mastery=anomaly_mastery,
                        anomaly_proficiency=anomaly_proficiency,
                        element_damage_bonus=ice_damage_bonus,
                    ),
                }
        elif character_id == "character:1401":
            compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": _stats("physical", crit_rate=0.50),
            }
        elif character_id == "character:1311":
            compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": _stats("ether", crit_rate=0.50),
            }
        else:
            raise AssertionError(f"test helper has no build fixture for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:miyabi-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {
                "ice": 0.20,
                "physical": 0.20,
                "ether": 0.20,
                "fire": 0.20,
                "electric": 0.20,
                "wind": 0.20,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _event(result: dict[str, object], semantic_id: str) -> dict[str, object]:
    return next(item for item in result["events"] if item["semantic_id"] == semantic_id)  # type: ignore[index,return-value]


def _mode(event: dict[str, object], mode: str = "expected") -> dict[str, object]:
    return event["modes"][mode]  # type: ignore[index,return-value]


def _trace(event: dict[str, object]) -> dict[str, object]:
    return event["common_application_trace"]  # type: ignore[return-value]


def _modifier(event: dict[str, object], effect_id: str) -> dict[str, object]:
    return next(item for item in _trace(event)["applied_modifiers"] if item["effect_id"] == effect_id)  # type: ignore[index]


def _break_result(
    core_level: int,
    *,
    cinema_level: int = 0,
    enabled=(),
    crit_rate: float = 0.0,
    crit_damage: float = 0.50,
    anomaly_proficiency: float = 238.0,
    ice_damage_bonus: float = 0.0,
):
    payload = _miyabi_payload(
        move_entry_id=ANOMALY_ENTRY,
        core_level=core_level,
        cinema_level=cinema_level,
        condition_values={str(ICEFIRE_ACTIVE): True, str(FROSTBURN_BREAK_READY): True},
        enabled_rule_item_ids=(FROSTBURN_RULE, *enabled),
        crit_rate=crit_rate,
        crit_damage=crit_damage,
        anomaly_proficiency=anomaly_proficiency,
        ice_damage_bonus=ice_damage_bonus,
    )
    return calculate_payload(payload)


def test_miyabi_raw_provenance_and_level_60_panel_normalization() -> None:
    record = load_character_record(MIYABI)
    raw = load_miyabi_raw_record(record)
    stats = character_base_stats(MIYABI)

    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1091.json"
    assert raw.character_id == MIYABI_ID
    assert stats.attack == Resolved(880.6952)
    assert stats.anomaly_mastery == Resolved(116.0)
    assert stats.anomaly_proficiency == Resolved(238.0)
    assert stats.element_damage_bonus[Element.ICE] == Resolved(0.0)


def test_nanoka_curve_loader_keeps_every_source_skill_id() -> None:
    raw = load_miyabi_raw_record(load_character_record(MIYABI))
    moves = raw_move_index(raw)
    fly_snow_slash = next(
        item for item in moves["强化特殊技：飞雪"].parameters if item.name == "斩击伤害倍率"
    )
    spring_call = next(
        item for item in moves["连携技：春临"].parameters if item.name == "伤害倍率"
    )

    assert [source for source, _ in fly_snow_slash.source_curves] == ["1091009", "1091010"]
    assert fly_snow_slash.value_for_level(12, "1091009") == pytest.approx(315.8)
    assert fly_snow_slash.value_for_level(12, "1091010") == pytest.approx(472.5)
    assert [source for source, _ in spring_call.source_curves] == ["1091015", "1091016", "1091017"]
    assert [spring_call.value_for_level(12, item) for item in ("1091015", "1091016", "1091017")] == pytest.approx([377.6, 377.6, 503.1])


def test_reviewed_mapping_covers_all_raw_direct_damage_curves() -> None:
    raw = load_miyabi_raw_record(load_character_record(MIYABI))
    raw_damage_skill_ids = {
        source_id
        for move in raw.moves
        for parameter in move.parameters
        if "伤害倍率" in parameter.name
        for source_id, _ in parameter.source_curves
    }
    reviewed_skill_ids = {
        parameter.source_skill_id
        for move in MIYABI_REVIEWED_MAPPING.moves
        for parameter in move.parameters
        if parameter.source_skill_id is not None
    }
    reviewed_skill_ids.update(
        source_id
        for spec in MIYABI_UNRESOLVED_MULTIPLIERS
        for source_id in spec.source_skill_ids
    )

    assert raw_damage_skill_ids == reviewed_skill_ids
    assert "1091025" in reviewed_skill_ids  # 支援突击：花辞
    assert not any("招架支援：花筏" in item.display_name for item in compile_miyabi(MiyabiCompileConfig(), raw).move_entries)


def test_unresolved_curve_entries_do_not_block_unrelated_moves() -> None:
    raw = load_miyabi_raw_record(load_character_record(MIYABI))
    definition = compile_miyabi(MiyabiCompileConfig(), raw)
    assert definition.diagnostics == ()
    blocked_entries = [item for item in definition.move_entries if item.multiplier_relation.value == "unresolved-relation"]
    assert {item.display_name for item in blocked_entries} == {
        "强化特殊技：飞雪·斩击",
        "强化特殊技：飞雪·追击",
        "连携技：春临",
    }

    clear = calculate_payload(_miyabi_payload(move_entry_id=KAZAHANA_1_ENTRY))
    assert clear["totals"]["expected"]["complete"] is True  # type: ignore[index]
    unresolved = calculate_payload(
        _miyabi_payload(move_entry_id="move-entry:character:1091:ex-special-strike")
    )
    assert unresolved["totals"]["expected"]["complete"] is False  # type: ignore[index]
    assert unresolved["events"] == []  # type: ignore[comparison-overlap]
    assert any(
        "1091009" in candidate
        for diagnostic in unresolved["diagnostics"]  # type: ignore[assignment]
        for candidate in diagnostic.get("candidates", ())
    )


def test_c3_and_c5_skill_bonuses_resolve_from_raw_curve_level_once() -> None:
    raw = load_miyabi_raw_record(load_character_record(MIYABI))
    c0 = compile_miyabi(MiyabiCompileConfig(), raw)
    c3 = compile_miyabi(MiyabiCompileConfig(cinema_level=3), raw)
    c5 = compile_miyabi(MiyabiCompileConfig(cinema_level=5), raw)
    entry_id = KAZAHANA_1_ENTRY
    values = [
        next(item for item in definition.move_entries if str(item.entry_id) == entry_id)
        .multiplier_variants[0]
        .multiplier.value.value
        for definition in (c0, c3, c5)
    ]

    assert values == pytest.approx([0.544, 0.594, 0.644])


def test_core_level_scales_only_frostburn_break_from_raw_text() -> None:
    panel = {
        "crit_rate": 0.70,
        "crit_damage": 1.10,
        "anomaly_proficiency": 200.0,
        "ice_damage_bonus": 0.40,
    }
    level_1 = _break_result(1, **panel)
    level_7 = _break_result(7, **panel)
    level_1_break = next(item for item in level_1["events"] if item["label"].endswith("霜灼·破"))  # type: ignore[index]
    level_7_break = next(item for item in level_7["events"] if item["label"].endswith("霜灼·破"))  # type: ignore[index]

    assert _mode(level_1_break)["status"] == "calculated"
    assert _mode(level_1_break)["value"] == pytest.approx(6580.37458194)
    assert _mode(level_7_break)["value"] == pytest.approx(13160.74916388)
    level_1_shatter = _event(level_1, "event:character:1091:lieshuang-anomaly")
    level_7_shatter = _event(level_7, "event:character:1091:lieshuang-anomaly")
    assert _mode(level_1_shatter)["value"] == pytest.approx(9913.93534002)
    assert _mode(level_7_shatter)["value"] == pytest.approx(_mode(level_1_shatter)["value"])
    assert _trace(level_7_break)["created_by_effect_id"] == CORE_BREACH_EFFECT
    for result in (level_1, level_7):
        snapshot = result["resolved_character_snapshots"][0]  # type: ignore[index]
        assert snapshot["stats"]["attack"] == pytest.approx(1000.0)  # type: ignore[index]
        assert snapshot["stats"]["anomaly_proficiency"] == pytest.approx(200.0)  # type: ignore[index]


def test_c2_crit_panel_is_read_before_capped_icefire_buildup_efficiency() -> None:
    result = calculate_payload(
        _miyabi_payload(
            move_entry_id=ANOMALY_ENTRY,
            core_level=1,
            cinema_level=2,
            condition_values={str(ICEFIRE_ACTIVE): True},
            enabled_rule_item_ids=(ICEFIRE_RULE, C2_RULE),
            crit_rate=0.70,
        )
    )
    event = result["events"][0]  # type: ignore[index]
    snapshot = next(item for item in result["resolved_character_snapshots"] if item["character_id"] == MIYABI)  # type: ignore[index]
    buildup = _modifier(event, "effect:character:1091:core:icefire-buildup-efficiency")

    assert snapshot["stats"]["crit_rate"] == pytest.approx(0.85)  # type: ignore[index]
    assert snapshot["stats"]["attack"] == pytest.approx(1000.0)  # type: ignore[index]
    assert snapshot["stats"]["anomaly_mastery"] == pytest.approx(116.0)  # type: ignore[index]
    assert snapshot["stats"]["anomaly_proficiency"] == pytest.approx(238.0)  # type: ignore[index]
    assert buildup["modifier_path"] == "anomaly-buildup.efficiency"
    assert buildup["value"] == pytest.approx(0.80)


def test_icefire_buildup_efficiency_matches_only_miyabi_lieshuang_hits() -> None:
    enabled_rules = (ICEFIRE_RULE, C2_RULE)
    condition_values = {str(ICEFIRE_ACTIVE): True}
    frost_hit = calculate_payload(
        _miyabi_payload(
            move_entry_id="move-entry:character:1091:kazahana-3",
            cinema_level=2,
            condition_values=condition_values,
            enabled_rule_item_ids=enabled_rules,
            crit_rate=0.70,
        )
    )
    frost_event = frost_hit["events"][0]  # type: ignore[index]
    frost_modifier = _modifier(
        frost_event,
        "effect:character:1091:core:icefire-buildup-efficiency",
    )
    without_rule = calculate_payload(
        _miyabi_payload(
            move_entry_id="move-entry:character:1091:kazahana-3",
            cinema_level=2,
            condition_values=condition_values,
            enabled_rule_item_ids=(C2_RULE,),
            crit_rate=0.70,
        )
    )
    physical_hit = calculate_payload(
        _miyabi_payload(
            move_entry_id=KAZAHANA_1_ENTRY,
            cinema_level=2,
            condition_values=condition_values,
            enabled_rule_item_ids=enabled_rules,
            crit_rate=0.70,
        )
    )
    teammate_hit = calculate_payload(
        _miyabi_payload(
            primary="character:1401",
            supporting=(MIYABI,),
            move_entry_id="move-entry:alice:1401:basic-star-opera-1",
            cinema_level=2,
            condition_values=condition_values,
            enabled_rule_item_ids=enabled_rules,
        )
    )

    assert frost_modifier["modifier_path"] == "anomaly-buildup.efficiency"
    assert frost_modifier["value"] == pytest.approx(0.80)
    assert _mode(frost_event)["value"] == pytest.approx(
        _mode(without_rule["events"][0])["value"]  # type: ignore[index]
    )
    assert not any(
        item["effect_id"] == "effect:character:1091:core:icefire-buildup-efficiency"
        for item in _trace(physical_hit["events"][0])["applied_modifiers"]  # type: ignore[index]
    )
    assert not any(
        item["effect_id"] == "effect:character:1091:core:icefire-buildup-efficiency"
        for item in _trace(teammate_hit["events"][0])["applied_modifiers"]  # type: ignore[index]
    )


@pytest.mark.parametrize(
    ("charge", "expected_ignore", "condition_id"),
    (
        (1, 0.12, FROSTMOON_CHARGE_1),
        (2, 0.24, FROSTMOON_CHARGE_2),
        (3, 0.36, FROSTMOON_CHARGE_3),
    ),
)
def test_c1_defense_ignore_uses_frostmoon_charge_points(
    charge: int,
    expected_ignore: float,
    condition_id,
) -> None:
    stage_conditions = {
        str(FROSTMOON_CHARGE_1): charge == 1,
        str(FROSTMOON_CHARGE_2): charge == 2,
        str(FROSTMOON_CHARGE_3): charge == 3,
    }
    rule_id = f"rule:character:1091:cinema1:frostmoon-defense-ignore-{charge}"
    result = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            cinema_level=1,
            condition_values=stage_conditions,
            enabled_rule_item_ids=(rule_id,),
        )
    )
    event = result["events"][0]  # type: ignore[index]
    effective_defense = next(
        item["value"]
        for item in _mode(event)["calculation_breakdown"]
        if item["node"] == "defense.enemy-current-effective"
    )
    effect = _modifier(event, f"effect:character:1091:cinema1:frostmoon-defense-ignore-{charge}")

    assert effective_defense == pytest.approx(1000.0 * (1.0 - expected_ignore))
    assert effect["value"] == pytest.approx(expected_ignore)
    assert condition_id in (FROSTMOON_CHARGE_1, FROSTMOON_CHARGE_2, FROSTMOON_CHARGE_3)


@pytest.mark.parametrize(("core_level", "expected_bonus"), ((1, 0.14), (7, 0.20)))
def test_core_frostscorch_increase_is_traced_without_changing_direct_damage(
    core_level: int,
    expected_bonus: float,
) -> None:
    result = calculate_payload(
        _miyabi_payload(
            move_entry_id=KAZAHANA_1_ENTRY,
            core_level=core_level,
            condition_values={str(FROSTSCORCH_ACTIVE): True},
            enabled_rule_item_ids=("rule:character:1091:core:frostscorch-buildup",),
            crit_rate=0.0,
        )
    )
    event = result["events"][0]  # type: ignore[index]
    buildup = _modifier(
        event,
        "effect:character:1091:core:frostscorch-anomaly-buildup-increase",
    )
    snapshot = result["resolved_character_snapshots"][0]  # type: ignore[index]

    assert buildup["modifier_path"] == "anomaly-buildup.increase"
    assert buildup["value"] == pytest.approx(expected_bonus)
    assert _mode(event)["calculation_breakdown"]
    assert snapshot["stats"]["attack"] == pytest.approx(1000.0)  # type: ignore[index]
    assert snapshot["stats"]["anomaly_mastery"] == pytest.approx(116.0)  # type: ignore[index]
    assert snapshot["stats"]["anomaly_proficiency"] == pytest.approx(238.0)  # type: ignore[index]


def test_c1_team_buildup_bonus_uses_its_current_state_condition() -> None:
    result = calculate_payload(
        _miyabi_payload(
            move_entry_id=KAZAHANA_1_ENTRY,
            cinema_level=1,
            condition_values={str(FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE): True},
            enabled_rule_item_ids=("rule:character:1091:cinema1:team-buildup-efficiency",),
            crit_rate=0.0,
        )
    )
    event = result["events"][0]  # type: ignore[index]
    modifier = _modifier(event, "effect:character:1091:cinema1:team-anomaly-buildup-efficiency")

    assert modifier["modifier_path"] == "anomaly-buildup.efficiency"
    assert modifier["value"] == pytest.approx(0.20)


def test_additional_ability_and_post_disorder_resistance_ignore_are_scoped_to_frostmoon() -> None:
    conditions = {
        str(FROSTMOON_CHARGE_1): True,
        str(FROSTMOON_CHARGE_2): False,
        str(FROSTMOON_CHARGE_3): False,
        str(NEXT_FROSTMOON_AFTER_DISORDER): True,
    }
    enabled = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            supporting=("character:1401",),
            condition_values=conditions,
            enabled_rule_item_ids=(
                "rule:character:1091:extra-ability:frostmoon-damage",
                "rule:character:1091:extra-ability:post-disorder-frostmoon-resistance-ignore",
            ),
            crit_rate=0.0,
        )
    )
    event = enabled["events"][0]  # type: ignore[index]

    assert _modifier(event, "effect:character:1091:extra-ability:frostmoon-damage")["value"] == pytest.approx(0.60)
    assert _modifier(event, "effect:character:1091:extra-ability:post-disorder-frostmoon-resistance-ignore")["value"] == pytest.approx(0.30)

    not_after_disorder = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            supporting=("character:1401",),
            condition_values={**conditions, str(NEXT_FROSTMOON_AFTER_DISORDER): False},
            enabled_rule_item_ids=(
                "rule:character:1091:extra-ability:frostmoon-damage",
                "rule:character:1091:extra-ability:post-disorder-frostmoon-resistance-ignore",
            ),
            crit_rate=0.0,
        )
    )
    other_event = not_after_disorder["events"][0]  # type: ignore[index]
    assert _modifier(other_event, "effect:character:1091:extra-ability:frostmoon-damage")["value"] == pytest.approx(0.60)
    assert not any(
        item["effect_id"] == "effect:character:1091:extra-ability:post-disorder-frostmoon-resistance-ignore"
        for item in _trace(other_event)["applied_modifiers"]
    )


def test_c2_damage_bonus_is_limited_to_kazahana_and_dodge_counter() -> None:
    kazahana = calculate_payload(
        _miyabi_payload(
            move_entry_id=KAZAHANA_1_ENTRY,
            cinema_level=2,
            enabled_rule_item_ids=(C2_RULE,),
            crit_rate=0.0,
        )
    )
    assert _modifier(
        kazahana["events"][0],  # type: ignore[index]
        "effect:character:1091:cinema2:kazahana-damage",
    )["value"] == pytest.approx(0.30)

    frostmoon = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            cinema_level=2,
            condition_values={
                str(FROSTMOON_CHARGE_1): True,
                str(FROSTMOON_CHARGE_2): False,
                str(FROSTMOON_CHARGE_3): False,
            },
            enabled_rule_item_ids=(C2_RULE,),
            crit_rate=0.0,
        )
    )
    frostmoon_trace = _trace(frostmoon["events"][0])  # type: ignore[index]
    assert not any(
        item["effect_id"] == "effect:character:1091:cinema2:kazahana-damage"
        for item in frostmoon_trace["applied_modifiers"]
    )


def test_ultimate_ice_damage_bonus_is_current_state_and_base_element_scoped() -> None:
    state_active = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            condition_values={
                str(FROSTMOON_CHARGE_1): True,
                str(FROSTMOON_CHARGE_2): False,
                str(FROSTMOON_CHARGE_3): False,
                str(ULTIMATE_ICE_BONUS_ACTIVE): True,
            },
            enabled_rule_item_ids=("rule:character:1091:ultimate:ice-damage-bonus-state",),
            crit_rate=0.0,
        )
    )
    assert _modifier(
        state_active["events"][0],  # type: ignore[index]
        "effect:character:1091:ultimate:ice-damage-bonus-state",
    )["value"] == pytest.approx(0.30)

    physical = calculate_payload(
        _miyabi_payload(
            move_entry_id=KAZAHANA_1_ENTRY,
            condition_values={str(ULTIMATE_ICE_BONUS_ACTIVE): True},
            enabled_rule_item_ids=("rule:character:1091:ultimate:ice-damage-bonus-state",),
            crit_rate=0.0,
        )
    )
    assert not any(
        item["effect_id"] == "effect:character:1091:ultimate:ice-damage-bonus-state"
        for item in _trace(physical["events"][0])["applied_modifiers"]  # type: ignore[index]
    )


def test_c4_boost_only_changes_created_frostburn_break() -> None:
    panel = {
        "crit_rate": 0.70,
        "crit_damage": 1.10,
        "anomaly_proficiency": 200.0,
        "ice_damage_bonus": 0.40,
    }
    base = _break_result(7, **panel)
    c4 = _break_result(7, cinema_level=4, enabled=(C4_RULE,), **panel)
    base_break = next(item for item in base["events"] if item["label"].endswith("霜灼·破"))  # type: ignore[index]
    c4_break = next(item for item in c4["events"] if item["label"].endswith("霜灼·破"))  # type: ignore[index]
    main_anomaly = c4["events"][0]  # type: ignore[index]

    assert _mode(base_break)["value"] == pytest.approx(13160.74916388)
    assert _mode(c4_break)["value"] == pytest.approx(15980.90969900)
    assert _mode(c4_break)["value"] == pytest.approx(_mode(base_break)["value"] * 1.7 / 1.4)
    base_shatter = _event(base, "event:character:1091:lieshuang-anomaly")
    c4_shatter = _event(c4, "event:character:1091:lieshuang-anomaly")
    assert _mode(base_shatter)["value"] == pytest.approx(9913.93534002)
    assert _mode(c4_shatter)["value"] == pytest.approx(_mode(base_shatter)["value"])
    assert _modifier(c4_break, "effect:character:1091:cinema4:frostburn-break-damage")["value"] == pytest.approx(0.30)
    assert not any(
        item["effect_id"] == "effect:character:1091:cinema4:frostburn-break-damage"
        for item in _trace(main_anomaly)["applied_modifiers"]
    )


def test_c6_keeps_main_frostmoon_damage_and_zero_count_does_not_create_a_child() -> None:
    conditions = {
        str(FROSTMOON_CHARGE_1): False,
        str(FROSTMOON_CHARGE_2): False,
        str(FROSTMOON_CHARGE_3): True,
    }
    child_rule = "rule:character:1091:cinema6-extra-slash-charge-3"
    params = {str(MIYABI_C6_SLASH_COUNT_PARAMETER_ID): 0}
    enabled = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            cinema_level=6,
            condition_values=conditions,
            parameter_values=params,
            enabled_rule_item_ids=(C6_FROSTMOON_RULE, child_rule),
            crit_rate=0.0,
        )
    )
    baseline = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            cinema_level=6,
            condition_values=conditions,
            parameter_values=params,
            enabled_rule_item_ids=(),
            crit_rate=0.0,
        )
    )
    event = enabled["events"][0]  # type: ignore[index]

    assert len(enabled["events"]) == 1  # type: ignore[arg-type]
    assert enabled["totals"]["expected"]["complete"] is True  # type: ignore[index]
    assert enabled["totals"]["expected"]["value"] == pytest.approx(_mode(event)["value"])  # type: ignore[index]
    assert _mode(event)["value"] == pytest.approx(
        baseline["totals"]["expected"]["value"] * 1.30
    )  # type: ignore[index]
    assert _modifier(event, "effect:character:1091:cinema6:frostmoon-damage")["value"] == pytest.approx(0.30)


def test_c6_unresolved_slash_blocks_only_its_child_event() -> None:
    result = calculate_payload(
        _miyabi_payload(
            move_entry_id=FROSTMOON_ENTRY,
            cinema_level=6,
            condition_values={
                str(FROSTMOON_CHARGE_1): False,
                str(FROSTMOON_CHARGE_2): False,
                str(FROSTMOON_CHARGE_3): True,
            },
            parameter_values={str(MIYABI_C6_SLASH_COUNT_PARAMETER_ID): 2},
            enabled_rule_item_ids=(C6_FROSTMOON_RULE, "rule:character:1091:cinema6-extra-slash-charge-3"),
            crit_rate=0.0,
        )
    )
    main = result["events"][0]  # type: ignore[index]
    slash = result["events"][1]  # type: ignore[index]

    assert len(result["events"]) == 2  # type: ignore[arg-type]
    assert _mode(main)["status"] == "calculated"
    assert _mode(slash)["status"] == "blocked"
    assert slash["repeat_count"] == 2
    assert "没有给出拔刀斩击倍率" in _mode(slash)["diagnostics"][0]["message"]  # type: ignore[index]
    assert result["totals"]["expected"]["complete"] is False  # type: ignore[index]
    assert result["totals"]["expected"]["value"] == pytest.approx(_mode(main)["value"])  # type: ignore[index]
    assert _trace(slash)["created_by_effect_id"] == "effect:character:1091:cinema6:extra-slash-charge-3"


def test_equipment_build_uses_miyabi_level_60_stats_and_drive_disc_sources() -> None:
    result = calculate_payload(
        _miyabi_payload(
            move_entry_id=KAZAHANA_1_ENTRY,
            equipment_build=True,
            crit_rate=0.0,
        )
    )
    snapshot = result["resolved_character_snapshots"][0]  # type: ignore[index]
    provenance = result["build_provenance"]  # type: ignore[assignment]

    assert snapshot["stats"]["attack"] == pytest.approx(880.6952 * 1.60 + 316.0)  # type: ignore[index]
    assert snapshot["stats"]["anomaly_mastery"] == pytest.approx(116.0 * 1.30)  # type: ignore[index]
    assert snapshot["stats"]["anomaly_proficiency"] == pytest.approx(238.0 + 6.0 * 2.0 * 9.0)  # type: ignore[index]
    assert snapshot["stats"]["element_damage_bonus"]["ice"] == pytest.approx(0.30)  # type: ignore[index]
    assert any(item["source_type"] == "drive-disc" for item in provenance)
    assert any(item["source_type"] == "drive-disc-set" for item in provenance)


def test_miyabi_as_support_does_not_leak_self_effects_to_alice() -> None:
    payload = _miyabi_payload(
        primary="character:1401",
        supporting=(MIYABI,),
        move_entry_id="move-entry:alice:1401:basic-star-opera-1",
        cinema_level=6,
        enabled_rule_item_ids=("rule:character:1091:extra-ability:frostmoon-damage", C2_RULE),
    )
    with_buffs = calculate_payload(payload)
    payload_without_rule = deepcopy(payload)
    payload_without_rule["enabled_rule_item_ids"] = []
    baseline = calculate_payload(payload_without_rule)
    event = with_buffs["events"][0]  # type: ignore[index]

    assert _mode(event)["value"] == pytest.approx(
        baseline["events"][0]["modes"]["expected"]["value"]  # type: ignore[index]
    )
    assert not any(
        item["effect_id"].startswith("effect:character:1091:")
        for item in _trace(event)["applied_modifiers"]
    )


def test_additional_ability_is_ineligible_without_a_qualifying_teammate() -> None:
    alone = compile_registered_definition(
        MIYABI,
        {"core_level": 1, "cinema_level": 0},
        [MIYABI],
    )
    with_alice = compile_registered_definition(
        MIYABI,
        {"core_level": 1, "cinema_level": 0},
        [MIYABI, "character:1401"],
    )
    alone_rule = next(item for item in alone.rule_items if item.rule_id == "rule:character:1091:extra-ability:frostmoon-damage")
    team_rule = next(item for item in with_alice.rule_items if item.rule_id == "rule:character:1091:extra-ability:frostmoon-damage")

    assert alone_rule.eligibility is RuleEligibility.INELIGIBLE
    assert team_rule.eligibility is RuleEligibility.ELIGIBLE


@pytest.mark.parametrize(
    ("reason", "expected_status", "expected_diagnostic"),
    (
        (UnresolvedReason.MISSING_DATA, EventCalculationStatus.DATA_INSUFFICIENT, "missing-data"),
        (UnresolvedReason.AMBIGUOUS_TEXT, EventCalculationStatus.BLOCKED, "ambiguous-semantics"),
        (UnresolvedReason.NOT_IMPLEMENTED_IN_SPEC, EventCalculationStatus.UNSUPPORTED_CALCULATOR, "unsupported-calculator"),
        (UnresolvedReason.MISSING_SPEC_RULE, EventCalculationStatus.UNSUPPORTED_CALCULATOR, "unsupported-calculator"),
    ),
)
def test_router_keeps_ambiguous_semantics_distinct_from_missing_and_unsupported(
    monkeypatch,
    reason: UnresolvedReason,
    expected_status: EventCalculationStatus,
    expected_diagnostic: str,
) -> None:
    from core.calculation.calculators import DirectDamageCalculator

    raw = load_miyabi_raw_record(load_character_record(MIYABI))
    definition = compile_miyabi(MiyabiCompileConfig(), raw)
    entry = next(item for item in definition.move_entries if item.entry_id == KAZAHANA_1_ENTRY)
    template = next(item for item in definition.damage_event_templates if item.ref == entry.main_damage_event)
    event = instantiate_direct_damage_event(
        template,
        entry.multiplier_variants[0].multiplier,
        battle_state_id="battle:miyabi-router",
        target_enemy="enemy:miyabi-router",
        created_at=0.0,
    ).event

    def unresolved_calculation(_self, _context):
        return CalculationResult(
            value=None,
            breakdown=(),
            unresolved=(Unresolved(reason=reason, notes=f"router test: {reason.value}"),),
        )

    monkeypatch.setattr(DirectDamageCalculator, "calculate", unresolved_calculation)
    result = CalculationRouter().calculate(event, None)  # type: ignore[arg-type]

    assert result.status is expected_status
    assert result.diagnostics[0].kind.value == expected_diagnostic
