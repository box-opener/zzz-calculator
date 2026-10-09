from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.piper import (
    PIPER_ID,
    PiperCompileConfig,
    compile_piper,
    load_raw_record,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import CharacterId, DamageTag, Element, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)

_POWER_STACKS_RULE = "rule:character:1281:core:current-power-stacks"
_C2_SLAM_RULE = "rule:character:1281:cinema2:power-stack-slam-damage"
_C2_RECORD_RULE = "rule:character:1281:cinema2:physical-record-normal-bonus"
_C2_RECORD_ACTIVE = "condition:piper:cinema2:physical-anomaly-record-bonus-active"
_BURNICE_THROW_DISCHARGE_RULE = "rule:character:1171:potential1:special-throw-discharge"


def _panel_stats(character_id: str) -> dict[str, object]:
    panel = character_base_stats(CharacterId(character_id))
    stats: dict[str, object] = {
        key: getattr(panel, key).value
        for key in (
            "hp",
            "attack",
            "defense",
            "impact",
            "crit_rate",
            "crit_damage",
            "anomaly_mastery",
            "anomaly_proficiency",
            "energy_regen",
            "penetration_rate",
            "penetration_flat",
        )
    }
    stats["element_damage_bonus"] = {
        element.value: value.value for element, value in panel.element_damage_bonus.items()
    }
    return stats


def _payload(
    primary: str,
    entry_id: str,
    *,
    supporting: tuple[str, ...] = (),
    cinema: int = 0,
    potential: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    stacks: dict[str, int] | None = None,
    anomaly_source: dict[str, str] | None = None,
) -> dict[str, object]:
    team = [primary, *(item for item in supporting if item != primary)]
    if anomaly_source is not None and anomaly_source["source_character_id"] not in team:
        team.append(anomaly_source["source_character_id"])
    configs = {
        character_id: {
            "core_level": 7,
            "cinema_level": cinema if character_id == primary else 0,
        }
        for character_id in team
    }
    if primary == "character:1171":
        configs[primary]["potential_level"] = potential
    payload: dict[str, object] = {
        "primary_character_id": primary,
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": stacks or {},
        "character_builds": {
            character_id: {
                "level": 60,
                "build_mode": "equipment-build",
                "base_stats": _panel_stats(character_id),
                "drive_discs": [],
            }
            for character_id in team
        },
        "enemy": {
            "enemy_id": "enemy:piper-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.0,
                "fire": 0.0,
                "ice": 0.0,
                "electric": 0.0,
                "ether": 0.0,
                "wind": 0.0,
                "luminance": 0.0,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
    }
    if anomaly_source is not None:
        payload["burnice_anomaly_source"] = anomaly_source
    return payload


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _event(result: dict[str, object], semantic_suffix: str) -> dict[str, object]:
    return next(
        item for item in result["events"]
        if semantic_suffix in item["semantic_id"]
    )


def _normal_bonus(event: dict[str, object], mode: str = "expected") -> float:
    return next(
        item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    )


def test_piper_live_source_registry_signature_panel_and_defaults() -> None:
    raw = load_raw_record(load_character_record(str(PIPER_ID)))
    assert (raw.name, raw.code_name, raw.rarity) == ("派派", "Piper", 3)
    assert (raw.specialty, raw.element, raw.faction) == ("异常", "物理", "卡吕冬之子")
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1281.json",
    )
    assert str(PIPER_ID) in supported_character_ids()
    panel = character_base_stats(PIPER_ID)
    assert panel.attack.value == pytest.approx(758.4172)
    assert panel.hp.value == pytest.approx(6976.9443)
    assert panel.defense.value == pytest.approx(612.6038)
    assert panel.anomaly_proficiency.value == pytest.approx(118.0)
    assert panel.anomaly_mastery.value == pytest.approx(116.0)
    assert PiperCompileConfig().core_level == 7
    assert PiperCompileConfig().cinema_level == 0
    assert PiperCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16

    registration = registration_for(PIPER_ID)
    assert registration.catalog.rarity == "A"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert next(
        item for item in supported_character_catalog()
        if item.character_id == str(PIPER_ID)
    ).code_name == "Piper"
    assert SIGNATURE_WENGINE_BY_CHARACTER[PIPER_ID] == WEngineId("wengine:13128")
    assert load_wengine_raw_record("wengine:13128").icon == "Weapon_A_1281"


def test_piper_reviewed_direct_entries_and_level_caps() -> None:
    raw = load_raw_record(load_character_record(str(PIPER_ID)))
    definition = compile_piper(PiperCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert len(entries) == 18
    for stage in range(1, 5):
        entry = entries[f"move-entry:character:1281:basic-stage-{stage}"]
        assert entry.main_damage_event.element is Element.PHYSICAL
        assert entry.skill_group is SkillGroup.BASIC_ATTACK
        assert entry.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert entries["move-entry:character:1281:basic-stage-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.4)
    assert entries["move-entry:character:1281:basic-stage-4"].multiplier_variants[0].multiplier.value.value == pytest.approx(7.586)
    assert entries["move-entry:character:1281:ex-engine-spin-one-circle"].multiplier_variants[0].multiplier.value.value == pytest.approx(2.218)
    assert entries["move-entry:character:1281:ultimate-sit-tight"].multiplier_variants[0].multiplier.value.value == pytest.approx(39.254)


def test_piper_cinema2_direct_slam_bonus_is_user_selectable_0_or_100_percent() -> None:
    stack_counts = {_POWER_STACKS_RULE: 20}
    slam_entries = (
        "move-entry:character:1281:special-very-heavy-charge-1",
        "move-entry:character:1281:special-very-heavy-charge-2",
        "move-entry:character:1281:special-very-heavy-charge-3",
        "move-entry:character:1281:ex-very-heavy",
        "move-entry:character:1281:ultimate-sit-tight",
    )
    for entry_id in slam_entries:
        baseline = _calculate(
            _payload("character:1281", entry_id, cinema=2, stacks=stack_counts)
        )
        enabled = _calculate(
            _payload(
                "character:1281",
                entry_id,
                cinema=2,
                enabled=(_C2_SLAM_RULE,),
                stacks=stack_counts,
            )
        )
        baseline_event = baseline["events"][0]
        enabled_event = enabled["events"][0]
        assert _normal_bonus(baseline_event) == pytest.approx(0.0)
        assert _normal_bonus(enabled_event) == pytest.approx(0.30)
        assert enabled_event["modes"]["expected"]["value"] == pytest.approx(
            baseline_event["modes"]["expected"]["value"] * 1.30
        )
        assert enabled["totals"]["expected"]["complete"] is True

    spin_entry = "move-entry:character:1281:special-tire-spin"
    spin_base = _calculate(
        _payload("character:1281", spin_entry, cinema=2, stacks=stack_counts)
    )
    spin_c2 = _calculate(
        _payload(
            "character:1281",
            spin_entry,
            cinema=2,
            enabled=(_C2_SLAM_RULE,),
            stacks=stack_counts,
        )
    )
    assert spin_c2["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        spin_base["events"][0]["modes"]["expected"]["value"]
    )


def test_piper_cinema2_record_bonus_reaches_disorder_strength_once() -> None:
    entry_id = "move-entry:character:1281:physical-disorder"
    baseline = _calculate(_payload("character:1281", entry_id, cinema=2))
    enabled = _calculate(
        _payload(
            "character:1281",
            entry_id,
            cinema=2,
            conditions={_C2_RECORD_ACTIVE: True},
            enabled=(_C2_RECORD_RULE,),
            stacks={_POWER_STACKS_RULE: 20},
        )
    )
    disabled = _calculate(
        _payload(
            "character:1281",
            entry_id,
            cinema=2,
            conditions={_C2_RECORD_ACTIVE: False},
            enabled=(_C2_RECORD_RULE,),
            stacks={_POWER_STACKS_RULE: 20},
        )
    )
    assert len(baseline["events"]) == len(enabled["events"]) == len(disabled["events"]) == 1
    baseline_event, enabled_event, disabled_event = (
        baseline["events"][0], enabled["events"][0], disabled["events"][0]
    )
    assert enabled_event["modes"]["expected"]["anomaly_effect_strength_trace"]["normal_bonus"] == pytest.approx(0.30)
    assert enabled_event["modes"]["expected"]["value"] == pytest.approx(
        baseline_event["modes"]["expected"]["value"] * 1.30
    )
    assert disabled_event["modes"]["expected"]["value"] == pytest.approx(
        baseline_event["modes"]["expected"]["value"]
    )
    assert enabled["totals"]["expected"]["complete"] is True


def test_piper_cinema2_bonus_is_captured_once_in_piper_record_for_burnice_discharge() -> None:
    entry_id = "move-entry:character:1171:special-throw"
    team = ("character:1281",)
    source = {"source_character_id": "character:1281", "element": "physical"}
    common = {
        "supporting": team,
        "potential": 1,
        "anomaly_source": source,
    }
    base_payload = _payload(
        "character:1171",
        entry_id,
        **common,
        enabled=(_BURNICE_THROW_DISCHARGE_RULE,),
    )
    base_payload["compile_configs"]["character:1281"]["cinema_level"] = 2
    buffed_payload = _payload(
        "character:1171",
        entry_id,
        **common,
        conditions={_C2_RECORD_ACTIVE: True},
        enabled=(_BURNICE_THROW_DISCHARGE_RULE, _C2_RECORD_RULE),
        stacks={_POWER_STACKS_RULE: 20},
    )
    buffed_payload["compile_configs"]["character:1281"]["cinema_level"] = 2
    base = _calculate(base_payload)
    buffed = _calculate(buffed_payload)
    base_discharge = _event(base, "potential1:special-throw-discharge:source")
    buffed_discharge = _event(buffed, "potential1:special-throw-discharge:source")

    assert len(base["events"]) == len(buffed["events"]) == 2
    assert base_discharge["element"] == buffed_discharge["element"] == "physical"
    assert base_discharge["modes"]["expected"]["anomaly_effect_strength_trace"]["character_id"] == "character:1281"
    base_strength = base_discharge["modes"]["expected"]["anomaly_effect_strength_trace"]["final_strength"]
    buffed_strength = buffed_discharge["modes"]["expected"]["anomaly_effect_strength_trace"]["final_strength"]
    assert buffed_strength == pytest.approx(base_strength * 1.30)
    assert buffed_discharge["modes"]["expected"]["value"] == pytest.approx(
        base_discharge["modes"]["expected"]["value"] * 1.30
    )
    assert buffed["totals"]["expected"]["complete"] is True

    disabled_payload = _payload(
        "character:1171",
        entry_id,
        **common,
        conditions={_C2_RECORD_ACTIVE: False},
        enabled=(_BURNICE_THROW_DISCHARGE_RULE, _C2_RECORD_RULE),
        stacks={_POWER_STACKS_RULE: 20},
    )
    disabled_payload["compile_configs"]["character:1281"]["cinema_level"] = 2
    disabled = _calculate(disabled_payload)
    disabled_discharge = _event(disabled, "potential1:special-throw-discharge:source")
    assert disabled_discharge["modes"]["expected"]["value"] == pytest.approx(
        base_discharge["modes"]["expected"]["value"]
    )
    assert disabled["totals"]["expected"]["complete"] is True
