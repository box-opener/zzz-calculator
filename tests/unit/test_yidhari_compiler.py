from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import raw_move_index
from core.application.characters.yidhari import (
    YIDHARI_ID,
    YidhariCompileConfig,
    compile_yidhari,
    load_raw_record,
)
from core.application.equipment import signature_wengine_id_for
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import CharacterRole, DamageType, Element, SkillGroup
from web.api import app


client = TestClient(app)


def _payload(
    move_entry_id: str,
    *,
    core_level: int = 7,
    cinema_level: int = 0,
    hp: float = 12000.0,
    attack: float = 1000.0,
    curtain: bool = False,
    hp_below_50: bool = False,
    max_hp_bonus_active: bool = False,
    insight_active: bool = False,
    current_hp_damage_bonus: int | None = 0,
    disorder_seconds: int = 10,
    enabled: tuple[str, ...] = (),
    supports: tuple[str, ...] = (),
) -> dict:
    builds: dict[str, dict] = {
        str(YIDHARI_ID): {
            "level": 60,
            "out_of_combat_stats": {
                "hp": hp,
                "attack": attack,
                "defense": 500.0,
                "impact": 95.0,
                "crit_rate": 0.70,
                "crit_damage": 1.10,
                "anomaly_mastery": 87.0,
                "anomaly_proficiency": 90.0,
                "energy_regen": 0.0,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"ice": 0.20},
            },
        }
    }
    configs = {
        str(YIDHARI_ID): {"core_level": core_level, "cinema_level": cinema_level}
    }
    for character_id in supports:
        builds[character_id] = {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 777.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.12,
                "crit_damage": 0.50,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"ice": 0.0},
            },
        }
        configs[character_id] = {"core_level": 1, "cinema_level": 0}
    parameters: dict[str, int] = {
        "parameter:yidhari:ice-disorder-remaining-seconds": disorder_seconds
    }
    if current_hp_damage_bonus is not None:
        parameters["parameter:yidhari:core-current-hp-damage-bonus-percent"] = (
            current_hp_damage_bonus
        )
    conditions = {
        "condition:yidhari:ether-curtain-active": curtain,
        "condition:yidhari:hp-below-50-active": hp_below_50,
        "condition:yidhari:core-max-hp-damage-bonus-active": max_hp_bonus_active,
        "condition:yidhari:cinema6-insight-active": insight_active,
    }
    return {
        "primary_character_id": str(YIDHARI_ID),
        "supporting_character_ids": list(supports),
        "team_character_ids": [str(YIDHARI_ID), *supports],
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": conditions,
        "parameter_values": parameters,
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:yidhari-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ice": 0.20},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _calculate(payload: dict) -> dict:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _breakdown(event: dict, node: str, mode: str = "expected") -> float:
    return next(
        row["value"]
        for row in event["modes"][mode]["calculation_breakdown"]
        if row["node"] == node
    )


def _owner(result: dict, character_id: str = str(YIDHARI_ID)) -> dict:
    return next(
        item
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == character_id
    )


def test_yidhari_live_raw_panel_role_signature_and_default_config_are_reviewed() -> None:
    source = load_character_record(str(YIDHARI_ID))
    raw = load_raw_record(source)
    assert str(YIDHARI_ID) in supported_character_ids()
    assert raw.name == "伊德海莉"
    assert raw.code_name == "Yidhari"
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1051.json"
    assert raw.rarity == 4
    assert raw.specialty == "命破"
    assert raw.element == "冰属性"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert raw.potential_details == ()

    stats = character_base_stats(YIDHARI_ID)
    assert stats.hp.value == pytest.approx(8497.1437)
    assert stats.attack.value == pytest.approx(859.9099)
    assert stats.defense.value == pytest.approx(448.4451)
    assert stats.impact.value == pytest.approx(95.0)
    assert stats.crit_rate.value == pytest.approx(0.194)
    assert stats.crit_damage.value == pytest.approx(0.5)
    assert stats.anomaly_mastery.value == pytest.approx(87.0)
    assert stats.anomaly_proficiency.value == pytest.approx(90.0)
    assert stats.energy_regen.value == pytest.approx(0.0)
    assert stats.element_damage_bonus[Element.ICE].value == pytest.approx(0.0)

    registration = registration_for(YIDHARI_ID)
    assert registration.role is CharacterRole.RUPTURE
    assert registration.base_element is Element.ICE
    assert registration.catalog.rarity == "S"
    assert registration.catalog.element == "ice"
    assert registration.catalog.specialty == "rupture"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert str(signature_wengine_id_for(YIDHARI_ID)) == "wengine:14105"

    fields = {
        item.field_id: item
        for item in config_fields_for(YIDHARI_ID, {}, [YIDHARI_ID])
    }
    assert fields["core_level"].value == 7
    assert fields["cinema_level"].value == 0
    assert fields["core_level"].field_type == "slider"
    assert fields["cinema_level"].field_type == "slider"
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


def test_yidhari_all_reviewed_moves_compile_from_source_ids_and_skill_levels() -> None:
    raw = load_raw_record(load_character_record(str(YIDHARI_ID)))
    definition = compile_yidhari(YidhariCompileConfig(), raw)
    assert len(definition.move_entries) == 22
    assert all(
        entry.main_damage_event.damage_type is DamageType.PENETRATION
        for entry in definition.move_entries
        if entry.skill_group is not None
    )
    assert all(not item.blocking for item in definition.diagnostics)

    raw_index = raw_move_index(raw)
    raw_basic = next(
        item for item in raw_index["普通攻击：碎惘沉击"].parameters if item.name == "一段伤害倍率"
    )
    raw_ultimate = next(
        item for item in raw_index["终结技：终幕·惘事渡却"].parameters if item.name == "伤害倍率"
    )
    boosted = compile_yidhari(
        YidhariCompileConfig(
            cinema_level=5,
            skill_levels=(
                CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 12),
                CharacterSkillLevel(SkillGroup.ULTIMATE, 12),
            ),
        ),
        raw,
    )
    entries = {str(item.entry_id): item for item in boosted.move_entries}
    assert entries["move-entry:character:1051:basic-shattered-strike-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(
        raw_basic.value_for_level(16, "1051001") / 100.0
    )
    assert entries["move-entry:character:1051:ultimate-final-act"].multiplier_variants[0].multiplier.value.value == pytest.approx(
        raw_ultimate.value_for_level(12, "1051016") / 100.0
    )


def test_yidhari_force_reads_current_max_hp_and_damage_uses_penetration_not_defense() -> None:
    force_rule = "rule:character:1051:core:extra-penetration-force-from-current-max-hp"
    entry = "move-entry:character:1051:basic-shattered-strike-1"
    lower_hp = _calculate(_payload(entry, hp=12000.0, enabled=(force_rule,)))
    higher_hp = _calculate(_payload(entry, hp=15000.0, enabled=(force_rule,)))
    lower_event = lower_hp["events"][0]
    higher_event = higher_hp["events"][0]
    assert lower_hp["totals"]["expected"]["complete"] is True
    assert higher_hp["totals"]["expected"]["complete"] is True
    assert _breakdown(lower_event, "penetration.force-bonus") == pytest.approx(1200.0)
    assert _breakdown(lower_event, "penetration.force") == pytest.approx(2700.0)
    assert _breakdown(lower_event, "damage.base-value") == pytest.approx(2700.0 * 1.223)
    assert _breakdown(higher_event, "penetration.force") == pytest.approx(3300.0)
    assert not any(
        row["node"] == "defense.enemy-current-effective"
        for row in lower_event["modes"]["expected"]["calculation_breakdown"]
    )


def test_yidhari_cinema_and_veil_effects_use_their_own_typed_lanes() -> None:
    core_force = "rule:character:1051:core:extra-penetration-force-from-current-max-hp"
    core_damage = "rule:character:1051:core:intermediate-low-hp-damage-increase"
    core_max_damage = "rule:character:1051:core:maximum-low-hp-damage-increase"
    c1_rule = "rule:character:1051:cinema1:ice-resistance-ignore-and-flash-source"
    c2_rule = "rule:character:1051:cinema2:crit-damage"
    c4_rule = "rule:character:1051:cinema4:veil-max-hp-bonus"
    c6_rule = "rule:character:1051:cinema6:insight-penetration-bonus"
    basic = "move-entry:character:1051:basic-shattered-strike-1"
    normal_special = "move-entry:character:1051:special-broken-thought"
    enabled = (core_force, core_damage, c1_rule)
    base = _calculate(
        _payload(basic, core_level=1, cinema_level=1, current_hp_damage_bonus=0, enabled=enabled)
    )["events"][0]
    assert _breakdown(base, "resistance.damage-ignore") == pytest.approx(0.20)
    special = _calculate(
        _payload(
            normal_special,
            core_level=1,
            cinema_level=1,
            current_hp_damage_bonus=0,
            enabled=enabled,
        )
    )["events"][0]
    assert _breakdown(special, "resistance.damage-ignore") == pytest.approx(0.0)
    ex_special = _calculate(
        _payload(
            "move-entry:character:1051:ex-special-frost-wrap",
            core_level=1,
            cinema_level=1,
            current_hp_damage_bonus=0,
            enabled=enabled,
        )
    )["events"][0]
    assert _breakdown(ex_special, "resistance.damage-ignore") == pytest.approx(0.20)

    c6_entry = _calculate(
        _payload(
            basic,
            core_level=1,
            cinema_level=6,
            current_hp_damage_bonus=0,
            insight_active=True,
            enabled=(core_force, core_damage, c6_rule),
        )
    )["events"][0]
    assert _breakdown(c6_entry, "penetration.damage-bonus-region") == pytest.approx(1.25)

    curtain = _calculate(
        _payload(
            basic,
            core_level=1,
            cinema_level=4,
            hp=12000,
            curtain=True,
            current_hp_damage_bonus=0,
            enabled=(core_force, core_damage, c4_rule),
        )
    )
    assert _owner(curtain)["stats"]["hp"] == pytest.approx(12600.0)
    assert _breakdown(curtain["events"][0], "penetration.force") == pytest.approx(2820.0)

    max_hp_state = _calculate(
        _payload(
            basic,
            core_level=1,
            max_hp_bonus_active=True,
            enabled=(core_force, core_max_damage),
        )
    )["events"][0]
    assert _breakdown(max_hp_state, "damage.normal-bonus") == pytest.approx(0.50)

    missing_intermediate = _calculate(
        _payload(
            basic,
            core_level=1,
            current_hp_damage_bonus=None,
            enabled=(core_force, core_damage),
        )
    )
    assert missing_intermediate["totals"]["expected"]["complete"] is False
    assert any(
        "parameter:yidhari:core-current-hp-damage-bonus-percent"
        in item["message"]
        for item in missing_intermediate["diagnostics"]
    )

    c2 = _calculate(
        _payload(
            basic,
            core_level=1,
            cinema_level=2,
            current_hp_damage_bonus=0,
            supports=("character:1361",),
            enabled=(core_force, core_damage, "rule:character:1051:cinema2:crit-damage"),
        )
    )
    assert _owner(c2)["stats"]["crit_damage"] == pytest.approx(1.50)
    assert _owner(c2, "character:1361")["stats"]["crit_damage"] == pytest.approx(0.50)


def test_yidhari_extra_ability_owner_qualification_and_local_tentacle_gap() -> None:
    force_rule = "rule:character:1051:core:extra-penetration-force-from-current-max-hp"
    bonus_rule = "rule:character:1051:core:intermediate-low-hp-damage-increase"
    extra_crit_rule = "rule:character:1051:extra-ability:low-hp-crit-damage"
    basic = "move-entry:character:1051:basic-shattered-strike-1"
    qualified = _calculate(
        _payload(
            basic,
            hp_below_50=True,
            supports=("character:1361",),
            enabled=(force_rule, bonus_rule, extra_crit_rule),
        )
    )
    assert _owner(qualified)["stats"]["crit_damage"] == pytest.approx(1.40)
    assert _owner(qualified, "character:1361")["stats"]["crit_damage"] == pytest.approx(0.50)
    unqualified = _calculate(
        _payload(
            basic,
            hp_below_50=True,
            enabled=(force_rule, bonus_rule, extra_crit_rule),
        )
    )
    assert _owner(unqualified)["stats"]["crit_damage"] == pytest.approx(1.10)

    charge_finisher = _calculate(
        _payload(
            "move-entry:character:1051:basic-frost-charge-three-finisher",
            core_level=1,
            curtain=True,
            current_hp_damage_bonus=0,
            supports=("character:1361",),
            enabled=(
                force_rule,
                bonus_rule,
                "rule:character:1051:extra-ability:ice-tentacle-source-unresolved",
            ),
        )
    )
    assert charge_finisher["events"][0]["modes"]["expected"]["known_value"] is not None
    assert charge_finisher["totals"]["expected"]["complete"] is False
    unrelated = _calculate(
        _payload(
            basic,
            core_level=1,
            curtain=True,
            current_hp_damage_bonus=0,
            supports=("character:1361",),
            enabled=(
                force_rule,
                bonus_rule,
                "rule:character:1051:extra-ability:ice-tentacle-source-unresolved",
            ),
        )
    )
    assert unrelated["totals"]["expected"]["complete"] is True


def test_yidhari_static_ice_anomaly_disorder_and_signature_build_are_real_paths() -> None:
    force_rule = "rule:character:1051:core:extra-penetration-force-from-current-max-hp"
    base_entry = "move-entry:character:1051:basic-shattered-strike-1"
    anomaly = _calculate(_payload("move-entry:character:1051:ice-anomaly"))
    disorder = _calculate(_payload("move-entry:character:1051:ice-disorder"))
    assert anomaly["events"][0]["damage_type"] == "anomaly"
    assert anomaly["events"][0]["modes"]["non-crit"]["status"] == "calculated"
    assert _breakdown(disorder["events"][0], "disorder.total-multiplier") == pytest.approx(5.25)

    payload = _payload(base_entry, enabled=(force_rule,))
    payload["character_builds"][str(YIDHARI_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14105",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }
    payload["enabled_rule_item_ids"].append(
        "rule:wengine:14105:owner:1051:ice-penetration-damage-per-stack"
    )
    result = _calculate(payload)
    assert _owner(result)["stats"]["hp"] > 8497.1437
    assert _breakdown(result["events"][0], "penetration.damage-bonus-region") == pytest.approx(1.18)
    assert result["totals"]["expected"]["complete"] is True


def test_frostbite_crit_damage_defaults_from_primary_and_stays_event_scoped() -> None:
    primary = str(YIDHARI_ID)
    condition_id = f"condition:enemy:frostbite-crit-damage-active:primary:{primary}"
    rule_id = f"rule:enemy:frostbite-crit-damage:primary:{primary}"
    effect_id = f"effect:enemy:frostbite-crit-damage:primary:{primary}"
    basic = "move-entry:character:1051:basic-shattered-strike-1"

    default_enabled = _payload(basic, enabled=(rule_id,))
    default_result = _calculate(default_enabled)
    disabled_input = _payload(basic, enabled=(rule_id,))
    disabled_input["condition_values"][condition_id] = False
    disabled_result = _calculate(disabled_input)

    default_event = default_result["events"][0]
    disabled_event = disabled_result["events"][0]
    assert default_event["modes"]["non-crit"]["known_value"] == pytest.approx(
        disabled_event["modes"]["non-crit"]["known_value"]
    )
    assert default_event["modes"]["expected"]["known_value"] > disabled_event[
        "modes"
    ]["expected"]["known_value"]
    assert default_event["modes"]["full-crit"]["known_value"] == pytest.approx(
        disabled_event["modes"]["full-crit"]["known_value"] * 2.2 / 2.1
    )
    assert _owner(default_result)["stats"]["crit_damage"] == pytest.approx(1.10)
    assert _owner(disabled_result)["stats"]["crit_damage"] == pytest.approx(1.10)
    stat_modifiers = default_event["common_application_trace"][
        "event_stat_modifiers"
    ]
    assert {
        (item["effect_id"], item["recipient_character_id"], item["value"])
        for item in stat_modifiers
    } == {(effect_id, primary, 0.10)}

    anomaly_default = _calculate(
        _payload("move-entry:character:1051:ice-anomaly", enabled=(rule_id,))
    )
    anomaly_disabled_input = _payload(
        "move-entry:character:1051:ice-anomaly", enabled=(rule_id,)
    )
    anomaly_disabled_input["condition_values"][condition_id] = False
    anomaly_disabled = _calculate(anomaly_disabled_input)
    assert anomaly_default["totals"] == anomaly_disabled["totals"]
    assert anomaly_default["events"][0]["common_application_trace"][
        "event_stat_modifiers"
    ] == []


def test_frostbite_control_is_shown_once_and_uses_current_primary_default() -> None:
    frost_condition = "condition:enemy:frostbite-crit-damage-active:primary:character:1051"
    fire_condition = "condition:enemy:frostbite-crit-damage-active:primary:character:1431"
    yidhari_team = [str(YIDHARI_ID), "character:1341"]

    primary_preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": str(YIDHARI_ID),
            "primary_character_id": str(YIDHARI_ID),
            "team_character_ids": yidhari_team,
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    supporting_preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1341",
            "primary_character_id": str(YIDHARI_ID),
            "team_character_ids": yidhari_team,
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert primary_preview.status_code == 200, primary_preview.text
    assert supporting_preview.status_code == 200, supporting_preview.text
    primary_conditions = primary_preview.json()["scenario_conditions"]
    frost_control = next(
        item for item in primary_conditions if item["condition_id"] == frost_condition
    )
    assert frost_control["value"] is True
    frost_rule = next(
        item
        for item in primary_preview.json()["rule_items"]
        if item["rule_id"] == "rule:enemy:frostbite-crit-damage:primary:character:1051"
    )
    assert frost_rule["availability"] == "available"
    assert frost_rule["enabled_by_default"] is True
    assert all(
        item["condition_id"] != frost_condition
        for item in supporting_preview.json()["scenario_conditions"]
    )
    assert sum(
        rule["rule_id"].startswith("rule:enemy:frostbite-crit-damage:")
        for view in (primary_preview.json(), supporting_preview.json())
        for rule in view["rule_items"]
    ) == 1

    switched_primary = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1431",
            "primary_character_id": "character:1431",
            "team_character_ids": ["character:1431", str(YIDHARI_ID)],
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert switched_primary.status_code == 200, switched_primary.text
    fire_control = next(
        item
        for item in switched_primary.json()["scenario_conditions"]
        if item["condition_id"] == fire_condition
    )
    assert fire_control["value"] is False
    assert frost_condition != fire_condition
    explicit_off_preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": str(YIDHARI_ID),
            "primary_character_id": str(YIDHARI_ID),
            "team_character_ids": yidhari_team,
            "condition_values": {frost_condition: False},
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert explicit_off_preview.status_code == 200, explicit_off_preview.text
    assert next(
        item
        for item in explicit_off_preview.json()["scenario_conditions"]
        if item["condition_id"] == frost_condition
    )["value"] is False


def test_frostbite_control_is_hidden_without_ice_and_uses_remielle_flow_element() -> None:
    stale_condition = "condition:enemy:frostbite-crit-damage-active:primary:character:1431"
    no_ice_preview = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": "character:1431",
            "primary_character_id": "character:1431",
            "team_character_ids": ["character:1431", "character:1011"],
            "condition_values": {stale_condition: True},
            "compile_config": {"core_level": 7, "cinema_level": 0},
        },
    )
    assert no_ice_preview.status_code == 200, no_ice_preview.text
    assert all(
        not item["condition_id"].startswith(
            "condition:enemy:frostbite-crit-damage-active:"
        )
        for item in no_ice_preview.json()["scenario_conditions"]
    )
    assert all(
        not item["rule_id"].startswith("rule:enemy:frostbite-crit-damage:")
        for item in no_ice_preview.json()["rule_items"]
    )

    remielle_id = "character:1581"
    remielle_flow_ice = client.post(
        "/api/v1/definitions/preview",
        json={
            "character_id": remielle_id,
            "primary_character_id": remielle_id,
            "team_character_ids": [remielle_id, str(YIDHARI_ID)],
            "compile_config": {
                "core_level": 7,
                "cinema_level": 0,
                "formation_character_ids": [remielle_id, str(YIDHARI_ID)],
            },
        },
    )
    assert remielle_flow_ice.status_code == 200, remielle_flow_ice.text
    remielle_frostbite = next(
        item
        for item in remielle_flow_ice.json()["scenario_conditions"]
        if item["condition_id"]
        == "condition:enemy:frostbite-crit-damage-active:primary:character:1581"
    )
    assert remielle_frostbite["value"] is True
