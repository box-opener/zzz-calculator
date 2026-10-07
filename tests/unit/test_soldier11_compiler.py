from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.soldier11 import (
    SOLDIER11_ID,
    Soldier11CompileConfig,
    compile_soldier11,
    load_raw_record,
)
from core.application.characters.nanoka_compiler import raw_move_index
from core.data.loader import load_character_record, supported_character_ids
from core.application.equipment import signature_wengine_id_for
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import CharacterRole, Element
from web.api import app


client = TestClient(app)


def _payload(
    move_entry_id: str,
    *,
    core_level: int = 7,
    cinema_level: int = 0,
    potential_level: int = 0,
    enemy_stunned: bool = False,
    charges: int | None = None,
    c2_stacks: int | None = None,
    enabled: tuple[str, ...] = (),
    supports: tuple[str, ...] = (),
) -> dict:
    team = [str(SOLDIER11_ID), *supports]
    builds = {
        str(SOLDIER11_ID): {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 500.0,
                "impact": 93.0,
                "crit_rate": 0.70,
                "crit_damage": 1.10,
                "anomaly_mastery": 94.0,
                "anomaly_proficiency": 93.0,
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"physical": 0.20, "fire": 0.20},
            },
        }
    }
    configs = {
        str(SOLDIER11_ID): {
            "core_level": core_level,
            "cinema_level": cinema_level,
            "potential_level": potential_level,
        }
    }
    for character_id in supports:
        builds[character_id] = {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 800.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.20,
                "crit_damage": 0.50,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"physical": 0.0, "fire": 0.0},
            },
        }
        configs[character_id] = {"core_level": 1, "cinema_level": 0}
    parameters: dict[str, int] = {}
    if charges is not None:
        if potential_level > 0:
            parameters["parameter:soldier11:potential-current-fire-suppression-uses"] = charges
        if cinema_level >= 6:
            parameters["parameter:soldier11:cinema6-current-charges"] = charges
    stacks: dict[str, int] = {}
    if c2_stacks is not None:
        stacks["rule:character:1041:cinema2:current-stacks"] = c2_stacks
    return {
        "primary_character_id": str(SOLDIER11_ID),
        "supporting_character_ids": list(supports),
        "team_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": {},
        "parameter_values": parameters,
        "rule_stack_counts": stacks,
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:soldier11-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.20,
                "fire": 0.20,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": enemy_stunned,
        },
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
    }


def _breakdown(event: dict, node: str, mode: str = "expected") -> float:
    return next(
        row["value"]
        for row in event["modes"][mode]["calculation_breakdown"]
        if row["node"] == node
    )


def _calculate(payload: dict) -> dict:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True, result
    return result


def test_soldier11_live_raw_role_build_and_default_config_are_reviewed() -> None:
    raw_source = load_character_record(str(SOLDIER11_ID))
    raw = load_raw_record(raw_source)
    assert str(SOLDIER11_ID) in supported_character_ids()
    assert raw.name == "「11号」"
    assert raw.code_name == "Soldier 11"
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1041.json"
    assert raw.rarity == 4
    assert raw.specialty == "强攻"
    assert raw.element == "火属性"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert len(raw.potential_details) == 6

    stats = character_base_stats(SOLDIER11_ID)
    assert stats.hp.value == pytest.approx(7673.7042)
    assert stats.attack.value == pytest.approx(888.5686)
    assert stats.defense.value == pytest.approx(612.6038)
    assert stats.impact.value == pytest.approx(93.0)
    assert stats.crit_rate.value == pytest.approx(0.194)
    assert stats.crit_damage.value == pytest.approx(0.5)
    assert stats.anomaly_mastery.value == pytest.approx(94.0)
    assert stats.anomaly_proficiency.value == pytest.approx(93.0)
    assert stats.energy_regen.value == pytest.approx(1.2)
    assert stats.element_damage_bonus[Element.FIRE].value == pytest.approx(0.0)

    registration = registration_for(SOLDIER11_ID)
    assert registration.role is CharacterRole.ATTACK
    assert registration.base_element is Element.FIRE
    assert registration.catalog.rarity == "S"
    assert registration.catalog.element == "fire"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert str(signature_wengine_id_for(SOLDIER11_ID)) == "wengine:14104"

    fields = {
        item.field_id: item
        for item in config_fields_for(SOLDIER11_ID, {}, [SOLDIER11_ID])
    }
    assert fields["core_level"].value == 7
    assert fields["cinema_level"].value == 0
    assert fields["potential_level"].value == 0
    assert fields["potential_level"].field_type == "slider"
    assert fields["potential_level"].minimum == 0
    assert fields["potential_level"].maximum == 6
    assert {
        key: fields[key].value
        for key in fields
        if key.startswith("skill_level:")
    } == {
        "skill_level:basic-attack": 12,
        "skill_level:dodge": 12,
        "skill_level:special-attack": 12,
        "skill_level:chain-attack": 12,
        "skill_level:assist": 12,
        "skill_level:ultimate": 12,
    }
    preview_response = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": str(SOLDIER11_ID),
            "team_character_ids": [str(SOLDIER11_ID)],
            "compile_config": {},
            "condition_values": {},
        },
    )
    assert preview_response.status_code == 200, preview_response.text
    preview = preview_response.json()
    preview_fields = {
        item["field_id"]: item["value"]
        for item in preview["compile_config_fields"]
    }
    assert preview_fields["core_level"] == 7
    assert preview_fields["cinema_level"] == 0
    assert preview_fields["potential_level"] == 0
    assert len(preview["moves"]) == 19


def test_soldier11_potential_views_retain_selected_curves_and_unlock_entries() -> None:
    source = load_character_record(str(SOLDIER11_ID))
    base = load_raw_record(source, potential_level=0)
    potential_one = load_raw_record(source, potential_level=1)
    potential_six = load_raw_record(source, potential_level=6)
    assert "普通攻击:火力迸发" not in {item.name for item in base.moves}
    assert "普通攻击:火力迸发" in {item.name for item in potential_one.moves}
    assert "普通攻击：火力镇压" in {item.name for item in potential_six.moves}
    assert len(source["potential_detail"]) == 6

    definition = compile_soldier11(
        Soldier11CompileConfig(core_level=7, cinema_level=0, potential_level=0),
        base,
    )
    assert len(definition.move_entries) == 19
    assert not any("fifth" in str(item.entry_id) or "fireburst" in str(item.entry_id) for item in definition.move_entries)

    potential_definition = compile_soldier11(
        Soldier11CompileConfig(core_level=7, cinema_level=0, potential_level=1),
        potential_one,
    )
    ids = {str(item.entry_id) for item in potential_definition.move_entries}
    assert "move-entry:character:1041:basic-fire-suppression-fifth" in ids
    assert "move-entry:character:1041:basic-fire-suppression-fifth-enhanced" in ids
    assert "move-entry:character:1041:potential-fireburst" in ids
    enhanced = next(
        item
        for item in potential_definition.move_entries
        if str(item.entry_id)
        == "move-entry:character:1041:basic-fire-suppression-fifth-enhanced"
    )
    variant = enhanced.multiplier_variants[0]
    assert variant.parameter_value_id is not None
    assert variant.parameter_base_value == pytest.approx(8.839)
    assert variant.parameter_coefficient == pytest.approx(1.664)

    cinema_five = compile_soldier11(
        Soldier11CompileConfig(core_level=7, cinema_level=5, potential_level=1),
        potential_one,
    )
    entries = {str(item.entry_id): item for item in cinema_five.move_entries}
    source_moves = raw_move_index(potential_one)
    fire_stage_curve = next(
        item
        for item in source_moves["普通攻击：火力镇压"].parameters
        if item.name == "一段伤害倍率"
    )
    ultimate_curve = next(
        item
        for item in source_moves["终结技：轰鸣烈焰"].parameters
        if item.name == "伤害倍率"
    )
    assert (
        entries["move-entry:character:1041:basic-fire-suppression-1"]
        .multiplier_variants[0]
        .multiplier.value.value
        == pytest.approx(fire_stage_curve.value_for_level(16, "1041002") / 100.0)
    )
    assert (
        entries["move-entry:character:1041:ultimate-roaring-flames"]
            .multiplier_variants[0]
            .multiplier.value.value
            == pytest.approx(ultimate_curve.value_for_level(16, "1041017") / 100.0)
    )

    fields = {
        item.field_id: item.value
        for item in config_fields_for(
            SOLDIER11_ID,
            {"core_level": 4, "cinema_level": 2, "potential_level": 3},
            [SOLDIER11_ID],
        )
    }
    assert (fields["core_level"], fields["cinema_level"], fields["potential_level"]) == (
        4,
        2,
        3,
    )


def test_soldier11_core_c2_and_stunned_target_bonuses_match_real_direct_events() -> None:
    core_rule = "rule:character:1041:core:fire-suppression-damage"
    fire_entry = "move-entry:character:1041:basic-fire-suppression-1"
    c1 = _calculate(
        _payload(fire_entry, core_level=1, enabled=(core_rule,))
    )["events"][0]
    c7 = _calculate(
        _payload(fire_entry, core_level=7, enabled=(core_rule,))
    )["events"][0]
    assert _breakdown(c1, "damage.normal-bonus") == pytest.approx(0.35)
    assert _breakdown(c7, "damage.normal-bonus") == pytest.approx(0.70)

    physical_warmup = _calculate(
        _payload(
            "move-entry:character:1041:basic-warmup-1",
            core_level=7,
            enabled=(core_rule,),
        )
    )["events"][0]
    assert _breakdown(physical_warmup, "damage.normal-bonus") == pytest.approx(0.0)

    c2_rule = "rule:character:1041:cinema2:current-stacks"
    dash = "move-entry:character:1041:dash-physical-blazing-fire"
    by_stack = []
    for count in (0, 6, 12):
        event = _calculate(
            _payload(
                dash,
                core_level=1,
                cinema_level=2,
                c2_stacks=count,
                enabled=(c2_rule,),
            )
        )["events"][0]
        by_stack.append(_breakdown(event, "damage.normal-bonus"))
    assert by_stack == pytest.approx([0.0, 0.18, 0.36])

    fire_bonus = "rule:character:1041:extra-ability:fire-damage"
    stunned_bonus = "rule:character:1041:extra-ability:stunned-target-fire-damage"
    extra_entry = "move-entry:character:1041:basic-fire-suppression-1"
    normal = _calculate(
        _payload(
            extra_entry,
            core_level=1,
            enemy_stunned=False,
            supports=("character:1361",),
            enabled=(fire_bonus, stunned_bonus),
        )
    )["events"][0]
    stunned = _calculate(
        _payload(
            extra_entry,
            core_level=1,
            enemy_stunned=True,
            supports=("character:1361",),
            enabled=(fire_bonus, stunned_bonus),
        )
    )["events"][0]
    assert _breakdown(normal, "damage.normal-bonus") == pytest.approx(0.10)
    assert _breakdown(stunned, "damage.normal-bonus") == pytest.approx(0.325)


def test_soldier11_c6_fire_ignore_and_potential_fifth_charge_curves_are_live() -> None:
    c6_rule = "rule:character:1041:cinema6:fire-resistance-ignore"
    entry = "move-entry:character:1041:basic-fire-suppression-1"
    base = _calculate(
        _payload(entry, core_level=1, cinema_level=6, charges=0, enabled=(c6_rule,))
    )["events"][0]
    charged = _calculate(
        _payload(entry, core_level=1, cinema_level=6, charges=1, enabled=(c6_rule,))
    )["events"][0]
    assert _breakdown(base, "resistance.damage-ignore") == pytest.approx(0.0)
    assert _breakdown(charged, "resistance.damage-ignore") == pytest.approx(0.25)
    full_charges = _calculate(
        _payload(entry, core_level=1, cinema_level=6, charges=8, enabled=(c6_rule,))
    )["events"][0]
    assert _breakdown(full_charges, "resistance.damage-ignore") == pytest.approx(0.25)

    enhanced = "move-entry:character:1041:basic-fire-suppression-fifth-enhanced"
    zero = _calculate(
        _payload(enhanced, core_level=1, potential_level=1, charges=0)
    )["events"][0]
    three = _calculate(
        _payload(enhanced, core_level=1, potential_level=1, charges=3)
    )["events"][0]
    assert _breakdown(zero, "damage.skill-multiplier") == pytest.approx(8.839)
    assert _breakdown(three, "damage.skill-multiplier") == pytest.approx(13.831)


def test_soldier11_potential_crit_damage_uses_eligibility_and_all_direct_entries_calculate() -> None:
    definition = compile_registered_definition(
        SOLDIER11_ID,
        {"core_level": 7, "cinema_level": 0, "potential_level": 6},
        [SOLDIER11_ID, "character:1361"],
        strict=True,
    )
    assert len(definition.move_entries) == 22
    assert all(
        not diagnostic.blocking
        for diagnostic in definition.diagnostics
    )
    for entry in definition.move_entries:
        result = _calculate(
            _payload(
                str(entry.entry_id),
                core_level=7,
                cinema_level=0,
                potential_level=1,
            )
        )
        assert result["totals"]["expected"]["complete"] is True
        assert all(
            event["modes"]["expected"]["status"] == "calculated"
            for event in result["events"]
        )

    bonus_rule = "rule:character:1041:potential:additional-ability-crit-damage"
    eligible = _calculate(
        _payload(
            "move-entry:character:1041:basic-fire-suppression-1",
            core_level=1,
            potential_level=6,
            supports=("character:1361",),
            enabled=(bonus_rule,),
        )
    )
    soldier = next(
        item
        for item in eligible["resolved_character_snapshots"]
        if item["character_id"] == str(SOLDIER11_ID)
    )
    trigger = next(
        item
        for item in eligible["resolved_character_snapshots"]
        if item["character_id"] == "character:1361"
    )
    assert soldier["stats"]["crit_damage"] == pytest.approx(1.58)
    assert trigger["stats"]["crit_damage"] == pytest.approx(0.50)
    ineligible = _calculate(
        _payload(
            "move-entry:character:1041:basic-fire-suppression-1",
            core_level=1,
            potential_level=6,
            enabled=(bonus_rule,),
        )
    )
    solo_soldier = next(
        item
        for item in ineligible["resolved_character_snapshots"]
        if item["character_id"] == str(SOLDIER11_ID)
    )
    assert solo_soldier["stats"]["crit_damage"] == pytest.approx(1.10)


def test_soldier11_static_burn_and_disorder_use_the_fire_source_formulas() -> None:
    anomaly = _calculate(_payload("move-entry:character:1041:fire-anomaly"))
    disorder = _calculate(_payload("move-entry:character:1041:fire-disorder"))
    assert anomaly["events"][0]["damage_type"] == "anomaly"
    assert anomaly["events"][0]["repeat_count"] == 20
    assert anomaly["events"][0]["modes"]["non-crit"]["status"] == "calculated"
    assert disorder["events"][0]["damage_type"] == "disorder"
    assert disorder["events"][0]["modes"]["non-crit"]["status"] == "calculated"
    assert _breakdown(
        disorder["events"][0], "disorder.total-multiplier"
    ) == pytest.approx(14.5)


def test_soldier11_brimstone_equipment_build_uses_role_and_source_panel() -> None:
    payload = _payload("move-entry:character:1041:basic-fire-suppression-1")
    payload["character_builds"][str(SOLDIER11_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14104",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }
    result = _calculate(payload)
    soldier = next(
        item
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == str(SOLDIER11_ID)
    )
    assert soldier["stats"]["attack"] > 888.5686 + 684.0
