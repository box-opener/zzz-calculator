from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import raw_move_index
from core.application.characters.remielle import (
    REMIELLE_ID,
    REMIELLE_REVIEWED_MAPPING,
    RemielleCompileConfig,
    compile_remielle,
    load_raw_record,
)
from core.application.execution.static_records import static_attribute_anomaly_record
from core.application.equipment import signature_wengine_id_for
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    build_registered_editor_view,
    compile_registered_definition,
    config_fields_for,
    equipment_capabilities_for_scene,
    registration_for,
)
from core.types import (
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    BattleStateId,
    CharacterId,
    CharacterRole,
    CalculationNode,
    DamageEventId,
    DamageEventMetadata,
    DamageTag,
    EffectId,
    EffectOperation,
    Element,
    FixedMultiplier,
    Modifier,
    NoCritRule,
    Resolved,
    SkillGroup,
    SnapshotRule,
    Unresolved,
)
from tests.unit.calculation._historical_anomaly_helpers import (
    modifier as anomaly_modifier,
    record as anomaly_record,
    snapshot as anomaly_snapshot,
)
from web.api import app


client = TestClient(app)


def test_remielle_live_raw_panel_signature_and_default_config_are_reviewed() -> None:
    source = load_character_record(str(REMIELLE_ID))
    raw = load_raw_record(source)

    assert str(REMIELLE_ID) in supported_character_ids()
    assert raw.name == "蕾米埃尔"
    assert raw.code_name == "Remielle"
    assert raw.source_version == "3.2"
    assert raw.source_url == (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1581.json"
    )
    assert raw.rarity == 4
    assert raw.specialty == "异常"
    assert raw.element == "流明"
    assert raw.potential_details == ()

    stats = character_base_stats(REMIELLE_ID)
    assert stats.hp.value == pytest.approx(7482.7069)
    assert stats.attack.value == pytest.approx(823.4626)
    assert stats.defense.value == pytest.approx(600.5916)
    assert stats.impact.value == pytest.approx(83.0)
    assert stats.crit_rate.value == pytest.approx(0.05)
    assert stats.crit_damage.value == pytest.approx(0.5)
    assert stats.anomaly_mastery.value == pytest.approx(115.0)
    assert stats.anomaly_proficiency.value == pytest.approx(170.0)
    assert stats.element_damage_bonus[Element.LUMINANCE].value == pytest.approx(0.0)

    registration = registration_for(REMIELLE_ID)
    assert registration.role is CharacterRole.ANOMALY
    assert registration.base_element is Element.LUMINANCE
    assert registration.catalog.rarity == "S"
    assert registration.catalog.element == "luminance"
    assert registration.catalog.specialty == "anomaly"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert str(signature_wengine_id_for(REMIELLE_ID)) == "wengine:14158"

    weapon_source = json.loads(Path("core/data/wengines/14158.json").read_text())
    assert weapon_source["id"] == "14158"
    assert weapon_source["raw_nanoka_detail"]["code_name"] == "Weapon_S_1581"
    assert weapon_source["raw_nanoka_detail"]["icon"].endswith("Weapon_S_1581.png")

    fields = {
        item.field_id: item
        for item in config_fields_for(REMIELLE_ID, {}, [REMIELLE_ID])
    }
    assert fields["core_level"].value == 7
    assert fields["core_level"].field_type == "slider"
    assert fields["cinema_level"].value == 0
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


def test_remielle_reviewed_direct_curve_map_keeps_each_source_entry() -> None:
    raw = load_raw_record(load_character_record(str(REMIELLE_ID)))
    definition = compile_remielle(RemielleCompileConfig(), raw)

    assert len(REMIELLE_REVIEWED_MAPPING.moves) == 17
    support_strike = next(
        item for item in REMIELLE_REVIEWED_MAPPING.moves
        if item.entry_key == "assist-strike-sleepless-dawn"
    )
    assert support_strike.damage_tags == frozenset({DamageTag.ASSIST})
    assert len(definition.move_entries) == 21
    direct_entries = tuple(
        entry for entry in definition.move_entries
        if entry.main_damage_event.damage_type.value == "direct"
    )
    assert len(direct_entries) == 17
    assert all(entry.main_damage_event.element is Element.LUMINANCE for entry in direct_entries)
    assert [entry.stage_index for entry in definition.move_entries[:4]] == [1, 2, 3, 4]

    ratios = {
        entry.entry_id: entry.multiplier_variants[0].multiplier.value.value
        for entry in direct_entries
    }
    assert ratios["move-entry:character:1581:basic-flutter-1"] == pytest.approx(0.631)
    assert ratios["move-entry:character:1581:basic-flutter-4"] == pytest.approx(5.016)
    assert ratios["move-entry:character:1581:basic-surprise"] == pytest.approx(11.945)
    assert ratios["move-entry:character:1581:ultimate-chaotic-finale"] == pytest.approx(40.194)

    level16 = compile_remielle(
        RemielleCompileConfig(
            cinema_level=5,
            skill_levels=(CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 12),),
        ),
        raw,
    )
    level16_ratios = {
        entry.entry_id: entry.multiplier_variants[0].multiplier.value.value
        for entry in level16.move_entries
        if entry.main_damage_event.damage_type.value == "direct"
    }
    assert level16_ratios["move-entry:character:1581:basic-flutter-4"] == pytest.approx(5.928)
    # C3/C5 do not increase the ultimate level.
    assert level16_ratios["move-entry:character:1581:ultimate-chaotic-finale"] == pytest.approx(40.194)

    indexed = raw_move_index(raw)
    assert "特殊技：薄明" in indexed
    assert "终结技：缭乱终幕" in indexed


def test_remielle_flare_entries_use_cal_level_ap_c4_and_c6_sources() -> None:
    raw = load_raw_record(load_character_record(str(REMIELLE_ID)))
    c0 = compile_remielle(RemielleCompileConfig(core_level=7), raw)
    c4 = compile_remielle(RemielleCompileConfig(core_level=7, cinema_level=4), raw)
    c6 = compile_remielle(RemielleCompileConfig(core_level=7, cinema_level=6), raw)

    def selected(definition, key):
        return next(item for item in definition.move_entries if str(item.entry_id).endswith(key))

    vertical = selected(c0, "flare:basic-vertical-rainbow")
    surprise = selected(c0, "flare:basic-surprise")
    ultimate = selected(c0, "flare:ultimate")
    support = selected(c0, "flare:support-flower-dance")
    assert vertical.multiplier_variants[0].multiplier.value.value == pytest.approx(1.60)
    assert surprise.multiplier_variants[0].multiplier.value.value == pytest.approx(3.20)
    assert ultimate.multiplier_variants[0].multiplier.value.value == pytest.approx(3.36)
    assert support.multiplier_variants[0].multiplier.value.value == pytest.approx(3.20)
    ap_rule = next(item for item in c0.rule_items if str(item.rule_id) == "rule:character:1581:core:flare-ap-multiplier")
    ap_effect = ap_rule.effects[0]
    assert ap_effect.result.value.coefficient.value == pytest.approx(0.002)
    c4_rule = next(item for item in c4.rule_items if str(item.rule_id) == "rule:character:1581:cinema4:flare-multiplier")
    assert c4_rule.eligibility.value == "eligible"
    assert c4_rule.effects[0].result.value.value == pytest.approx(1.12)
    c6_vertical = selected(c6, "flare:basic-vertical-rainbow")
    assert c6_vertical.multiplier_variants[0].repeat_count is None
    assert c6_vertical.main_damage_event.template_id in {item.ref.template_id for item in c6.damage_event_templates}
    c6_rule = next(item for item in c6.rule_items if str(item.rule_id) == "rule:character:1581:cinema6:flare-repeat")
    assert c6_rule.eligibility.value == "eligible"


def _rem_payload(
    *,
    team: tuple[str, ...],
    formation: tuple[str, ...],
    move_entry_id: str,
    cinema: int = 0,
    level: int = 60,
    source_slots: list[dict[str, str]] | None = None,
    conditions: dict[str, bool] | None = None,
    enabled_rules: tuple[str, ...] = (),
) -> dict[str, object]:
    supporting = tuple(item for item in team if item != str(REMIELLE_ID))
    payload: dict[str, object] = {
        "primary_character_id": str(REMIELLE_ID),
        "supporting_character_ids": supporting,
        "team_character_ids": (str(REMIELLE_ID), *supporting),
        "formation_character_ids": formation,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            character_id: {"core_level": 7, "cinema_level": cinema}
            for character_id in team
        },
        "condition_values": conditions or {},
        "parameter_values": {},
        "character_builds": {
            character_id: {
                "level": level,
                "build_mode": "equipment-build",
                "drive_discs": [],
            }
            for character_id in team
        },
        "enemy": {
            "enemy_id": "enemy:remielle-flare-test",
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
        "enabled_rule_item_ids": list(enabled_rules),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }
    if source_slots is not None:
        payload["luminance_source_slots"] = source_slots
    return payload


def test_remielle_parent_hit_includes_each_flare_source_without_repeating_parent() -> None:
    remielle = str(REMIELLE_ID)
    yixuan = "character:1371"
    flare_entry = "move-entry:character:1581:flare:basic-vertical-rainbow"
    payload = _rem_payload(
        team=(remielle, yixuan),
        formation=(remielle, yixuan),
        move_entry_id="move-entry:character:1581:basic-vertical-rainbow",
        source_slots=[{
            "slot_id": "slot-1",
            "kind": "ordinary-anomaly",
            "source_character_id": yixuan,
        }],
        conditions={"condition:remielle:virtual-lights-available": True},
        enabled_rules=(
            "rule:character:1581:core:anomaly-mutation-coefficient",
            "rule:character:1581:cinema6:flare-repeat",
            "rule:character:1581:core:flare-ap-multiplier",
            "rule:character:1581:cinema4:flare-multiplier",
        ),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert [event["damage_type"] for event in result["events"]] == ["direct", "anomaly"]
    parent = result["events"][0]
    flare = result["events"][1]
    assert parent["semantic_id"] == "event:character:1581:basic-vertical-rainbow:main"
    assert parent["repeat_count"] == 1
    assert flare["semantic_id"].endswith(":source-slot:slot-1")
    assert flare["damage_subtype"] == "luminance"
    assert flare["element"] == "ether:xuanmo"
    assert flare["repeat_count"] == 1
    assert result["totals"]["expected"]["value"] == pytest.approx(
        parent["modes"]["expected"]["known_value"]
        + flare["modes"]["expected"]["known_value"]
    )

    no_source = _rem_payload(
        team=(remielle, yixuan),
        formation=(remielle, yixuan),
        move_entry_id="move-entry:character:1581:basic-vertical-rainbow",
        source_slots=[],
        conditions={"condition:remielle:virtual-lights-available": True},
    )
    no_source_response = client.post("/api/v1/moves/calculate", json=no_source)
    assert no_source_response.status_code == 200, no_source_response.text
    no_source_result = no_source_response.json()
    assert len(no_source_result["events"]) == 1
    assert no_source_result["events"][0]["damage_type"] == "direct"
    assert no_source_result["totals"]["expected"]["complete"] is True

    c6_payload = _rem_payload(
        team=(remielle, yixuan),
        formation=(remielle, yixuan),
        move_entry_id="move-entry:character:1581:basic-vertical-rainbow",
        cinema=6,
        source_slots=[{
            "slot_id": "slot-1",
            "kind": "ordinary-anomaly",
            "source_character_id": yixuan,
        }],
        conditions={"condition:remielle:virtual-lights-available": True},
        enabled_rules=(
            "rule:character:1581:core:anomaly-mutation-coefficient",
            "rule:character:1581:core:flare-ap-multiplier",
            "rule:character:1581:cinema6:flare-repeat",
        ),
    )
    c6_response = client.post("/api/v1/moves/calculate", json=c6_payload)
    assert c6_response.status_code == 200, c6_response.text
    c6_result = c6_response.json()
    assert c6_result["totals"]["expected"]["complete"] is True
    assert len(c6_result["events"]) == 2
    assert c6_result["events"][0]["damage_type"] == "direct"
    assert c6_result["events"][0]["repeat_count"] == 1
    assert c6_result["events"][1]["repeat_count"] == 2


def test_remielle_default_source_slots_and_empty_flare_are_not_blocking() -> None:
    remielle = str(REMIELLE_ID)
    yixuan = "character:1371"
    payload = _rem_payload(
        team=(remielle, yixuan),
        formation=(remielle, yixuan),
        move_entry_id="move-entry:character:1581:flare:basic-vertical-rainbow",
        conditions={"condition:remielle:virtual-lights-available": False},
        enabled_rules=(
            "rule:character:1581:core:anomaly-mutation-coefficient",
            "rule:character:1581:core:flare-ap-multiplier",
        ),
    )
    payload.pop("luminance_source_slots", None)
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    assert result["events"][0]["semantic_id"].endswith(
        ":source-slot:ordinary-character:1371"
    )

    empty_payload = _rem_payload(
        team=(remielle,),
        formation=(remielle,),
        move_entry_id="move-entry:character:1581:flare:basic-vertical-rainbow",
        source_slots=[],
    )
    empty_response = client.post("/api/v1/moves/calculate", json=empty_payload)
    assert empty_response.status_code == 200, empty_response.text
    empty_result = empty_response.json()
    assert empty_result["events"] == []
    assert empty_result["totals"]["expected"]["value"] == 0.0
    assert empty_result["totals"]["expected"]["complete"] is True
    assert empty_result["totals"]["expected"]["diagnostics"] == []

    duplicate_slots = [
        {
            "slot_id": f"dup-{index}",
            "kind": "ordinary-anomaly",
            "source_character_id": yixuan,
        }
        for index in range(1, 4)
    ]
    duplicate_payload = _rem_payload(
        team=(remielle, yixuan),
        formation=(remielle, yixuan),
        move_entry_id="move-entry:character:1581:flare:basic-vertical-rainbow",
        source_slots=duplicate_slots,
        enabled_rules=("rule:character:1581:core:anomaly-mutation-coefficient",),
    )
    duplicate_response = client.post("/api/v1/moves/calculate", json=duplicate_payload)
    assert duplicate_response.status_code == 200, duplicate_response.text
    duplicate_result = duplicate_response.json()
    assert duplicate_result["totals"]["expected"]["complete"] is True
    assert len(duplicate_result["events"]) == 3
    assert len({item["semantic_id"] for item in duplicate_result["events"]}) == 3
    unit_values = [item["modes"]["expected"]["known_value"] for item in duplicate_result["events"]]
    assert unit_values[0] == pytest.approx(unit_values[1])
    assert unit_values[1] == pytest.approx(unit_values[2])
    assert duplicate_result["totals"]["expected"]["value"] == pytest.approx(sum(unit_values))


def test_remielle_locked_special_source_is_rejected() -> None:
    remielle = str(REMIELLE_ID)
    payload = _rem_payload(
        team=(remielle,),
        formation=(remielle,),
        move_entry_id="move-entry:character:1581:flare:basic-vertical-rainbow",
        cinema=0,
        source_slots=[{
            "slot_id": "locked-entry",
            "kind": "special-entry",
            "source_character_id": remielle,
        }],
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "requires Remielle cinema 1" in response.json()["diagnostics"][0]["message"]


def test_remielle_special_flare_snapshots_level_pen_and_c6_quarter() -> None:
    remielle = str(REMIELLE_ID)
    payload = _rem_payload(
        team=(remielle,),
        formation=(remielle,),
        move_entry_id="move-entry:character:1581:flare:basic-vertical-rainbow",
        cinema=6,
        level=30,
        source_slots=[{
            "slot_id": "c6-source",
            "kind": "special-basic4",
            "source_character_id": remielle,
        }],
        enabled_rules=(
            "rule:character:1581:core:anomaly-mutation-coefficient",
            "rule:character:1581:core:flare-ap-multiplier",
            "rule:character:1581:cinema4:flare-multiplier",
            "rule:character:1581:cinema6:flare-repeat",
        ),
    )
    payload["character_builds"] = {
        remielle: {
            "level": 30,
            "build_mode": "manual-panel",
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 700.0,
                "impact": 83.0,
                "crit_rate": 0.05,
                "crit_damage": 0.5,
                "anomaly_mastery": 115.0,
                "anomaly_proficiency": 170.0,
                "penetration_rate": 0.24,
                "penetration_flat": 36.0,
                "energy_regen": 1.2,
                "element_damage_bonus": {"luminance": 0.0},
            },
        }
    }
    response = client.post(
        "/api/v1/moves/calculate",
        json=payload,
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    event = result["events"][0]
    assert event["repeat_count"] == 2
    breakdown = {
        item["node"]: item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
    }
    assert breakdown["anomaly.luminance.special-source-multiplier"] == pytest.approx(0.3125)
    assert breakdown["anomaly.luminance.flare-cinema-multiplier"] == pytest.approx(1.12)
    assert breakdown["anomaly.luminance.multiplier"] == pytest.approx(
        (1.8 + breakdown["anomaly.luminance.flare-ap-contribution"]) * 1.12
    )
    assert event["modes"]["expected"]["anomaly_effect_strength_trace"]["level"] == 30

    disabled_payload = dict(payload)
    disabled_payload["enabled_rule_item_ids"] = [
        "rule:character:1581:core:anomaly-mutation-coefficient"
    ]
    disabled_response = client.post("/api/v1/moves/calculate", json=disabled_payload)
    assert disabled_response.status_code == 200, disabled_response.text
    disabled_event = disabled_response.json()["events"][0]
    disabled_breakdown = {
        item["node"]: item["value"]
        for item in disabled_event["modes"]["expected"]["calculation_breakdown"]
    }
    assert disabled_event["repeat_count"] == 1
    assert disabled_breakdown["anomaly.luminance.flare-ap-contribution"] == pytest.approx(0.0)
    assert disabled_breakdown["anomaly.luminance.flare-cinema-multiplier"] == pytest.approx(1.0)


def test_remielle_mixed_source_slots_keep_each_element_and_unique_event_identity() -> None:
    remielle = str(REMIELLE_ID)
    miyabi = "character:1091"
    astra = "character:1311"
    team = (remielle, miyabi, astra)
    response = client.post(
        "/api/v1/moves/calculate",
        json=_rem_payload(
            team=team,
            formation=(miyabi, remielle, astra),
            move_entry_id="move-entry:character:1581:basic-vertical-rainbow",
            cinema=1,
            source_slots=[
                {
                    "slot_id": "ice-source",
                    "kind": "ordinary-anomaly",
                    "source_character_id": miyabi,
                },
                {
                    "slot_id": "flow-source",
                    "kind": "special-entry",
                    "source_character_id": remielle,
                },
            ],
            conditions={
                "condition:remielle:virtual-lights-available": True,
            },
            enabled_rules=(
                "rule:character:1581:core:anomaly-mutation-coefficient",
                "rule:character:1581:cinema1:luminance-flare-resistance-ignore",
            ),
        ),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    flare_events = [item for item in result["events"] if item["damage_subtype"] == "luminance"]
    assert len(flare_events) == 2
    assert [item["semantic_id"].rsplit(":", 1)[-1] for item in flare_events] == [
        "ice-source",
        "flow-source",
    ]
    assert [item["element"] for item in flare_events] == ["ice:lieshuang", "ether"]
    assert all(item["modes"]["expected"]["status"] == "calculated" for item in flare_events)
    assert all(
        any(
            node["node"] == "resistance.damage-ignore"
            and node["value"] == pytest.approx(0.5)
            for node in item["modes"]["expected"]["calculation_breakdown"]
        )
        for item in flare_events
    )


def test_remielle_signature_wengine_luminance_damage_bonus_is_current_and_not_historical() -> None:
    remielle = str(REMIELLE_ID)
    base_rules = (
        "rule:character:1581:core:anomaly-mutation-coefficient",
        "rule:character:1581:core:flare-ap-multiplier",
        "rule:wengine:14158:owner:1581:team-damage-after-mutation-reaction",
        "rule:wengine:14158:owner:1581:luminance-attribute-anomaly-damage",
    )

    def calculate(buffs_active: bool):
        payload = _rem_payload(
            team=(remielle,),
            formation=(remielle,),
            move_entry_id="move-entry:character:1581:flare:basic-vertical-rainbow",
            cinema=1,
            source_slots=[{
                "slot_id": "special-entry",
                "kind": "special-entry",
                "source_character_id": remielle,
            }],
            conditions={
                "condition:wengine:14158:owner:1581:mutation-reaction-buffs-active": buffs_active,
            },
            enabled_rules=base_rules,
        )
        payload["character_builds"][remielle]["wengine_id"] = "wengine:14158"
        response = client.post("/api/v1/moves/calculate", json=payload)
        assert response.status_code == 200, response.text
        return response.json()

    inactive = calculate(False)
    active = calculate(True)
    inactive_event = inactive["events"][0]
    active_event = active["events"][0]
    assert inactive["totals"]["expected"]["complete"] is True
    assert active["totals"]["expected"]["complete"] is True
    inactive_breakdown = {
        item["node"]: item["value"]
        for item in inactive_event["modes"]["expected"]["calculation_breakdown"]
    }
    active_breakdown = {
        item["node"]: item["value"]
        for item in active_event["modes"]["expected"]["calculation_breakdown"]
    }
    assert active_breakdown["anomaly.effect-strength"] == pytest.approx(
        inactive_breakdown["anomaly.effect-strength"] * 1.30
    )
    assert inactive_breakdown["anomaly.luminance.anomaly-damage-bonus-region"] == pytest.approx(1.0)
    assert active_breakdown["anomaly.luminance.anomaly-damage-bonus-region"] == pytest.approx(1.2)
    assert active["totals"]["expected"]["value"] == pytest.approx(
        inactive["totals"]["expected"]["value"] * 1.56
    )


def test_remielle_registry_compiles_equipment_build_without_an_engine() -> None:
    definition = compile_registered_definition(
        REMIELLE_ID,
        {"core_level": 7, "cinema_level": 0},
        [REMIELLE_ID],
    )
    entry = next(
        item
        for item in definition.move_entries
        if str(item.entry_id) == "move-entry:character:1581:basic-flutter-4"
    )
    payload = {
        "primary_character_id": str(REMIELLE_ID),
        "team_character_ids": [str(REMIELLE_ID)],
        "move_entry_id": str(entry.entry_id),
        "compile_configs": {
            str(REMIELLE_ID): {"core_level": 7, "cinema_level": 0}
        },
        "condition_values": {
            "condition:remielle:virtual-lights-available": False,
            "condition:remielle:reflection-state-active": False,
            "condition:remielle:phase-shift-active": False,
            "condition:remielle:enemy-prism-active": False,
        },
        "parameter_values": {},
        "character_builds": {
            str(REMIELLE_ID): {
                "level": 60,
                "build_mode": "equipment-build",
                "drive_discs": [],
            }
        },
        "enemy": {
            "enemy_id": "enemy:remielle-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"luminance": 0.0},
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
    assert result["totals"]["expected"]["complete"] is True
    snapshot = result["resolved_character_snapshots"][0]
    assert snapshot["stats"]["attack"] == pytest.approx(823.4626)
    event = result["events"][0]
    assert event["label"] == "普通攻击：蹁跹（四段）"
    assert event["element"] == Element.LUMINANCE.value
    assert event["modes"]["expected"]["status"] == "calculated"


def test_remielle_api_uses_fixed_formation_flow_for_event_element() -> None:
    remielle = str(REMIELLE_ID)
    team = [remielle, "character:1311", "character:1051"]
    payload = {
        "primary_character_id": remielle,
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": ["character:1311", remielle, "character:1051"],
        "move_entry_id": "move-entry:character:1581:basic-flutter-4",
        "compile_configs": {
            remielle: {"core_level": 7, "cinema_level": 0},
            "character:1311": {"core_level": 7, "cinema_level": 0},
            "character:1051": {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {},
        "parameter_values": {},
        "character_builds": {
            item: {"level": 60, "build_mode": "equipment-build", "drive_discs": []}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:remielle-flow-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"ice": 0.2, "ether": 0.2},
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
    assert result["totals"]["expected"]["complete"] is True
    assert result["events"][0]["element"] == Element.ICE.value


def test_remielle_flow_follows_stable_formation_and_blocks_legacy_ambiguity() -> None:
    remielle = str(REMIELLE_ID)
    astra = "character:1311"
    yidhari = "character:1051"
    team = [remielle, astra, yidhari]
    config = {"core_level": 7, "cinema_level": 0}

    def flow_entry(formation: list[str]):
        definition = compile_registered_definition(
            REMIELLE_ID,
            {**config, "formation_character_ids": formation},
            team,
        )
        return next(
            item
            for item in definition.move_entries
            if str(item.entry_id) == "move-entry:character:1581:basic-flutter-4"
        )

    # The operator-first calculation order is independent of the fixed lineup.
    assert flow_entry([remielle, astra, yidhari]).main_damage_event.element is Element.ETHER
    assert flow_entry([yidhari, remielle, astra]).main_damage_event.element is Element.ETHER
    assert flow_entry([remielle, yidhari, astra]).main_damage_event.element is Element.ICE
    assert equipment_capabilities_for_scene(
        REMIELLE_ID,
        [remielle, astra, yidhari],
        [yidhari, remielle, astra],
    ).possible_elements == frozenset({Element.ETHER})

    two_person = compile_registered_definition(
        REMIELLE_ID,
        {"core_level": 7, "cinema_level": 0},
        [remielle, yidhari],
    )
    two_person_entry = next(
        item
        for item in two_person.move_entries
        if str(item.entry_id) == "move-entry:character:1581:basic-flutter-4"
    )
    assert two_person_entry.main_damage_event.element is Element.ICE

    without_formation = compile_registered_definition(
        REMIELLE_ID,
        config,
        [remielle, astra, yidhari],
    )
    unresolved_entry = next(
        item
        for item in without_formation.move_entries
        if str(item.entry_id) == "move-entry:character:1581:basic-flutter-4"
    )
    unresolved = unresolved_entry.multiplier_variants[0].multiplier
    assert isinstance(unresolved, Unresolved)
    assert unresolved.reason.value == "missing-data"
    assert "formation_character_ids" in unresolved.notes


def test_remielle_editor_preview_uses_flow_for_frostbite_and_native_bonus_scope() -> None:
    remielle = str(REMIELLE_ID)
    yidhari = "character:1051"
    astra = "character:1311"
    team = (remielle, yidhari, astra)
    view = build_registered_editor_view(
        REMIELLE_ID,
        {
            "core_level": 7,
            "cinema_level": 0,
            "formation_character_ids": (remielle, yidhari, astra),
        },
        team,
        primary_character_id=REMIELLE_ID,
    )
    # Nominal identity remains Luminance while the current flow is Ice.
    assert view.base_element == Element.LUMINANCE.value
    assert view.effective_damage_element == Element.ICE.value
    frostbite = next(
        item for item in view.scenario_conditions
        if item.condition_id == "condition:enemy:frostbite-crit-damage-active:primary:character:1581"
    )
    assert frostbite.value is True


def test_static_anomaly_record_keeps_source_penetration_and_additive_mutation_factor() -> None:
    source = CharacterId("character:1431")
    source_record = anomaly_record(
        record_id="anomaly:remielle-source-test",
        triggerer=source,
    )
    event = AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:remielle-source-test"),
            battle_state_id=BattleStateId("battle:remielle-source-test"),
            damage_dealer=source,
            target_enemy=source_record.target_enemy,
            element=Element.PHYSICAL,
            created_at=2.0,
        ),
        anomaly_triggerer=source,
        base_settlement_data_source=AnomalyRecordValueSource(source_record.record_id),
        history_record_source=source_record.record_id,
        multiplier=FixedMultiplier(Resolved(7.13)),
        crit_rule=NoCritRule(),
    )
    source_snapshot = anomaly_snapshot(
        source,
        penetration_rate=0.13,
        penetration_flat=42.0,
    )
    ordinary = static_attribute_anomaly_record(event, (source_snapshot,))

    def mutation_modifier(suffix: str, operation: EffectOperation, value: float) -> Modifier:
        return Modifier(
            effect_id=EffectId(f"effect:remielle:test:{suffix}"),
            modifier_path=CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
            operation=operation,
            value=Resolved(value),
            snapshot_rule=SnapshotRule.SETTLEMENT,
        )

    mutated = static_attribute_anomaly_record(
        event,
        (source_snapshot,),
        (
            mutation_modifier("ap-base", EffectOperation.MULTIPLY, 1.10),
            mutation_modifier("three-anomaly", EffectOperation.ADD, 0.10),
            mutation_modifier("cinema2", EffectOperation.ADD, 0.20),
        ),
    )
    assert ordinary is not None and ordinary.record is not None
    assert mutated is not None and mutated.record is not None
    assert ordinary.record.penetration_rate == Resolved(0.13)
    assert ordinary.record.penetration_flat == Resolved(42.0)
    assert mutated.record.penetration_rate == Resolved(0.13)
    assert mutated.record.penetration_flat == Resolved(42.0)
    assert mutated.record.anomaly_effect_strength_trace.mutation == pytest.approx(1.40)
    assert mutated.record.weighted_anomaly_effect_strength.value == pytest.approx(
        ordinary.record.weighted_anomaly_effect_strength.value * 1.40
    )


def _anomaly_source_payload(
    *,
    anomaly_count: int,
    cinema_level: int = 0,
    disorder: bool = False,
) -> dict:
    team = ["character:1331", str(REMIELLE_ID)]
    if anomaly_count == 3:
        team.append("character:1401")
    builds = {}
    configs = {}
    for character_id in team:
        builds[character_id] = {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 500.0,
                "impact": 100.0,
                "crit_rate": 0.2,
                "crit_damage": 0.5,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": (
                    500.0 if character_id == str(REMIELLE_ID) else 100.0
                ),
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {
                    "physical": 0.1,
                    "luminance": 0.0,
                    "ether": 0.0,
                },
            },
        }
        configs[character_id] = {"core_level": 7, "cinema_level": 0}
    configs[str(REMIELLE_ID)] = {"core_level": 7, "cinema_level": cinema_level}
    enabled = ["rule:character:1581:core:anomaly-mutation-coefficient"]
    if anomaly_count == 3:
        enabled.append("rule:character:1581:core:three-anomaly-mutation-coefficient")
    if cinema_level >= 2:
        enabled.append("rule:character:1581:cinema2:anomaly-mutation-coefficient")
    return {
        "primary_character_id": "character:1331",
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": (
            "move-entry:character:1331:ether-corrosion-disorder"
            if disorder
            else "move-entry:character:1331:ether-corrosion"
        ),
        "compile_configs": configs,
        "condition_values": {},
        "parameter_values": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:remielle-record-test",
            "level": 70,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": enabled,
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


@pytest.mark.parametrize("anomaly_count,cinema,expected", [(2, 0, 1.1), (3, 0, 1.2), (3, 2, 1.4)])
@pytest.mark.parametrize("disorder", [False, True])
def test_remielle_mutation_coefficient_is_source_ap_plus_additive_team_and_c2(
    anomaly_count: int,
    cinema: int,
    expected: float,
    disorder: bool,
) -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json=_anomaly_source_payload(
            anomaly_count=anomaly_count,
            cinema_level=cinema,
            disorder=disorder,
        ),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    event = result["events"][0]
    trace = event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["mutation"] == pytest.approx(expected)
    assert trace["character_id"] == "character:1331"


def test_mutation_coefficients_combine_base_multiplier_and_additive_bonuses() -> None:
    source = CharacterId("character:1431")
    history = anomaly_record(triggerer=source)
    metadata = DamageEventMetadata(
        event_id=DamageEventId("damage:remielle-mutation-test"),
        battle_state_id=BattleStateId("battle:remielle-mutation-test"),
        damage_dealer=source,
        target_enemy=history.target_enemy,
        element=Element.PHYSICAL,
        created_at=2.0,
    )
    event = AttributeAnomalyDamageEvent(
        metadata=metadata,
        anomaly_triggerer=source,
        base_settlement_data_source=AnomalyRecordValueSource(
            AnomalyRecordId("anomaly:remielle-mutation-test")
        ),
        history_record_source=AnomalyRecordId("anomaly:remielle-mutation-test"),
        multiplier=FixedMultiplier(Resolved(7.13)),
        crit_rule=NoCritRule(),
    )
    snapshots = (anomaly_snapshot(source),)
    ordinary = static_attribute_anomaly_record(event, snapshots)
    mutated = static_attribute_anomaly_record(
        event,
        snapshots,
        (
            anomaly_modifier(
                CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
                1.10,
                operation=EffectOperation.MULTIPLY,
            ),
            anomaly_modifier(
                CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
                0.10,
                operation=EffectOperation.ADD,
            ),
            anomaly_modifier(
                CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
                0.20,
                operation=EffectOperation.ADD,
            ),
        ),
    )

    assert ordinary is not None and ordinary.record is not None
    assert mutated is not None and mutated.record is not None
    assert mutated.record.anomaly_effect_strength_trace.mutation == pytest.approx(1.40)
    assert mutated.record.weighted_anomaly_effect_strength.value == pytest.approx(
        ordinary.record.weighted_anomaly_effect_strength.value * 1.40
    )
