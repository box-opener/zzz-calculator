from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from core.application.characters.vivian import (
    VIVIAN_ID,
    VIVIAN_REVIEWED_MAPPING,
    VivianCompileConfig,
    compile_vivian,
    load_raw_record,
)
from core.application.characters.vivian.reviewed import BASIC_BLOSSOMS_MOVE_ID, C6_FEATHER_COUNT
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import (
    _synthetic_panel_source_entry,
    calculate_payload,
)
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import CharacterId, CharacterRole, DamageSubtype, DamageTag, DamageType, Element


VIVIAN = str(VIVIAN_ID)
ASTRA = "character:1311"
YIXUAN = "character:1371"
ANOMALY_ENTRY = "move-entry:character:1331:ether-corrosion"
FALL_ENTRY = "move-entry:character:1331:basic-skirt-float-fall"
BLOSSOMS_ENTRY = "move-entry:character:1331:basic-feathering-blossoms"
MIXED_ENTRY = "move-entry:character:1331:basic-feather-flurry-1"
YIXUAN_XUANMO_ANOMALY = "move-entry:character:1371:xuanmo-anomaly"
CORE_MUTATION_RULE = "rule:character:1331:core:anomaly-mutation:ether"
C2_RULE = "rule:character:1331:cinema2:anomaly-proficiency-and-resistance"
EXTRA_ABILITY_RULE = "rule:character:1331:extra-ability:feathering-blossoms"
EXTRA_CORROSION_RULE = "rule:character:1331:extra-ability:corrosion-damage"
C4_GUARANTEE_RULE = "rule:character:1331:cinema4:basic-guaranteed-crit"
MUTATION_CONDITION = "condition:vivian:mutation-triggered"
FEATHER_CONDITION = "condition:vivian:protective-feather-available"
TARGET_ANOMALY_CONDITION = "condition:vivian:target-has-anomaly"
PROPHECY_TICK_COUNT = "parameter:vivian:prophecy-tick-count"


def _stats(
    *,
    attack: float = 1000.0,
    ap: float = 200.0,
    am: float = 90.0,
    crit_rate: float = 0.20,
    crit_damage: float = 0.50,
    element: str = "ether",
    element_bonus: float = 0.20,
) -> dict[str, object]:
    return {
        "hp": 10000.0,
        "attack": attack,
        "defense": 500.0,
        "impact": 100.0,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "anomaly_mastery": am,
        "anomaly_proficiency": ap,
        "energy_regen": 1.20,
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
    primary: str = VIVIAN,
    supporting: tuple[str, ...] = (),
    move_entry_id: str = ANOMALY_ENTRY,
    core_level: int = 1,
    cinema_level: int = 0,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    parameter_values: dict[str, int] | None = None,
    equipment_build: bool = False,
    manual_stats: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    team = (primary, *supporting)
    configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        if character_id == VIVIAN:
            configs[character_id] = {"core_level": core_level, "cinema_level": cinema_level}
            builds[character_id] = (
                {"level": 60, "build_mode": "equipment-build", "drive_discs": _drive_discs()}
                if equipment_build
                else {"level": 60, "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats())}
            )
        elif character_id == ASTRA:
            configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats(attack=800.0, ap=120.0, am=100.0)),
            }
        elif character_id == YIXUAN:
            configs[character_id] = {"core_level": 1, "cinema_level": 0}
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats(attack=1000.0, ap=100.0, am=90.0)),
            }
        else:
            raise AssertionError(f"missing test build for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:vivian-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"ether": 0.20, "physical": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _event(result: dict[str, object], semantic_id: str):
    return next(item for item in result["events"] if item["semantic_id"] == semantic_id)


def _node(event: dict[str, object], name: str):
    return next(item for item in event["modes"]["expected"]["calculation_breakdown"] if item["node"] == name)


def test_vivian_raw_curves_registration_and_level_60_base_panel() -> None:
    raw_json = load_character_record(VIVIAN)
    raw = load_raw_record(raw_json)
    definition = compile_vivian(VivianCompileConfig(), raw)
    raw_damage_curves = {
        source_skill_id
        for move in raw.moves
        for parameter in move.parameters
        if parameter.format == "%" and "伤害倍率" in parameter.name and (parameter.main or 0) > 0
        for source_skill_id, _curve in parameter.source_curves
    }
    mapped_curves = {
        parameter.source_skill_id
        for move in VIVIAN_REVIEWED_MAPPING.moves
        for parameter in move.parameters
    }
    assert mapped_curves == raw_damage_curves == {
        "1331001", "1331002", "1331003", "1331004", "1331005", "1331006",
        "1331008", "1331009", "1331010", "1331011", "1331012", "1331013",
        "1331014", "1331015", "1331019",
    }
    assert len([item for item in definition.move_entries if item.skill_group is not None]) == 15
    assert raw.rarity == 4
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1331.json"
    assert VIVIAN in supported_character_ids()

    registration = registration_for(VIVIAN)
    assert registration.role is CharacterRole.ANOMALY
    assert registration.base_element is Element.ETHER
    assert registration.catalog.rarity == "S"
    assert registration.catalog.element == "ether"
    assert registration.catalog.image_path == "/characters/IconRole41.webp"
    assert (Path(__file__).parents[2] / "frontend" / "public" / "characters" / "IconRole41.webp").is_file()
    stats = character_base_stats(VIVIAN)
    assert stats.hp.value == pytest.approx(7673.7042)
    assert stats.attack.value == pytest.approx(880.6952)
    assert stats.anomaly_mastery.value == pytest.approx(144.0)
    assert stats.anomaly_proficiency.value == pytest.approx(118.0)
    fields = config_fields_for(VIVIAN, {"core_level": 7, "cinema_level": 6}, (VIVIAN, ASTRA))
    assert {item.field_id for item in fields} >= {"core_level", "cinema_level", "skill_level:basic-attack"}


def test_registered_additional_ability_eligibility_uses_other_anomaly_or_same_element() -> None:
    eligible_ether = compile_registered_definition(
        VIVIAN, {"core_level": 1, "cinema_level": 0}, (VIVIAN, ASTRA)
    )
    eligible_anomaly = compile_registered_definition(
        VIVIAN, {"core_level": 1, "cinema_level": 0}, (VIVIAN, "character:1401")
    )
    ineligible = compile_registered_definition(
        VIVIAN, {"core_level": 1, "cinema_level": 0}, (VIVIAN, "character:1361")
    )
    by_id = {str(item.rule_id): item for item in eligible_ether.rule_items}
    assert by_id[EXTRA_CORROSION_RULE].eligibility.value == "eligible"
    assert any(item.display_name.startswith("额外能力") and item.eligibility.value == "eligible" for item in eligible_anomaly.rule_items)
    ineligible_rule = next(item for item in ineligible.rule_items if item.rule_id == by_id[EXTRA_CORROSION_RULE].rule_id)
    assert ineligible_rule.eligibility.value == "ineligible"


def test_core7_mutation_reads_current_ap_and_c2_is_a_separate_optional_multiplier() -> None:
    common = dict(
        core_level=7,
        cinema_level=2,
        condition_values={MUTATION_CONDITION: True},
        enabled_rule_item_ids=(CORE_MUTATION_RULE,),
    )
    c0 = calculate_payload(_payload(**common))
    c0_event = _event(c0, "event:character:1331:core-anomaly-mutation:ether")
    assert c0_event["damage_type"] == DamageType.ANOMALY.value
    assert c0_event["damage_subtype"] == DamageSubtype.DISCHARGE.value
    assert c0_event["modes"]["expected"]["status"] == "calculated"
    assert _node(c0_event, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert _node(c0_event, "anomaly.discharge.total-multiplier")["value"] == pytest.approx(15.375)
    assert _node(c0_event, "damage.base-value")["value"] == pytest.approx(73800.0)
    source_event = _event(c0, "event:character:1331:ether-corrosion")
    assert source_event["repeat_count"] == 20
    assert _node(source_event, "anomaly.attribute.multiplier")["value"] == pytest.approx(0.625)
    assert _node(source_event, "damage.base-value")["value"] == pytest.approx(3000.0)
    assert source_event["modes"]["expected"]["known_value"] == pytest.approx(
        source_event["modes"]["expected"]["value"] * 20
    )
    assert _node(c0_event, "resistance.region")["value"] == pytest.approx(0.8)
    assert c0_event["modes"]["expected"]["anomaly_record_id"] == "anomaly:vivian:ether"

    c2 = calculate_payload(
        _payload(**{**common, "enabled_rule_item_ids": (CORE_MUTATION_RULE, C2_RULE)})
    )
    c2_event = _event(c2, "event:character:1331:core-anomaly-mutation:ether")
    assert c2_event["modes"]["expected"]["status"] == "calculated"
    assert _node(c2_event, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.599)
    assert _node(c2_event, "anomaly.discharge.total-multiplier")["value"] == pytest.approx(19.9875)
    assert _node(c2_event, "damage.base-value")["value"] == pytest.approx(95940.0)
    assert _node(c2_event, "resistance.damage-ignore")["value"] == pytest.approx(0.15)
    assert _node(c2_event, "resistance.region")["value"] == pytest.approx(0.95)
    trace = c2_event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["character_id"] == VIVIAN
    assert trace["anomaly_proficiency"] == pytest.approx(200.0)
    assert trace["final_strength"] == pytest.approx(4800.0)
    assert c2_event["modes"]["expected"]["known_value"] > c0_event["modes"]["expected"]["known_value"]
    assert c2["totals"]["expected"]["complete"] is True


def test_discharge_uses_the_source_teammates_historical_record_and_vivian_current_ap() -> None:
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(VIVIAN,),
            move_entry_id=YIXUAN_XUANMO_ANOMALY,
            core_level=7,
            cinema_level=2,
            condition_values={MUTATION_CONDITION: True},
            enabled_rule_item_ids=(
                "rule:character:1331:core:anomaly-mutation:ether:xuanmo",
            ),
        )
    )
    source = _event(result, "event:character:1371:xuanmo-anomaly")
    mutation = _event(result, "event:character:1331:core-anomaly-mutation:ether-xuanmo")
    assert source["modes"]["expected"]["anomaly_record_id"] == "anomaly:yixuan:xuanmo-current"
    assert mutation["modes"]["expected"]["anomaly_record_id"] == "anomaly:yixuan:xuanmo-current"
    assert mutation["damage_type"] == DamageType.ANOMALY.value
    assert mutation["damage_subtype"] == DamageSubtype.DISCHARGE.value
    assert mutation["modes"]["expected"]["anomaly_effect_strength_trace"]["character_id"] == YIXUAN
    assert _node(mutation, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert result["totals"]["expected"]["complete"] is True


def test_vivian_discharge_shows_separate_current_panel_sources_without_joining_move_total() -> None:
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(VIVIAN,),
            move_entry_id=YIXUAN_XUANMO_ANOMALY,
            core_level=7,
            cinema_level=4,
            condition_values={
                MUTATION_CONDITION: True,
                "condition:vivian:mind4-attack-buff-active": True,
            },
            enabled_rule_item_ids=(
                "rule:character:1331:core:anomaly-mutation:ether:xuanmo",
                "rule:character:1331:core:anomaly-mutation:ether",
                "rule:character:1331:cinema4:prophecy-attack",
            ),
            manual_stats={
                YIXUAN: _stats(attack=777.0, ap=100.0, am=92.0, element="ether", element_bonus=0.4),
                VIVIAN: _stats(attack=1000.0, ap=200.0, am=144.0, element="ether", element_bonus=0.3),
            },
        )
    )
    sources = {
        (item["source_character_id"], item["element"]): item
        for item in result["panel_source_results"]
    }
    yixuan = sources[(YIXUAN, "ether:xuanmo")]
    vivian = sources[(VIVIAN, "ether")]
    yixuan_trace = yixuan["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]
    vivian_trace = vivian["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert yixuan_trace["character_id"] == YIXUAN
    assert yixuan_trace["attack"] == pytest.approx(777.0)
    assert yixuan_trace["anomaly_proficiency"] == pytest.approx(100.0)
    assert yixuan_trace["final_strength"] == pytest.approx(2175.6)
    assert vivian_trace["character_id"] == VIVIAN
    assert vivian_trace["attack"] == pytest.approx(1120.0)
    assert vivian_trace["anomaly_proficiency"] == pytest.approx(200.0)
    assert vivian_trace["final_strength"] == pytest.approx(5824.0)
    vivian_panel = next(
        item for item in result["resolved_character_snapshots"] if item["character_id"] == VIVIAN
    )
    assert vivian_panel["stats"]["attack"] == pytest.approx(1120.0)
    assert _node(yixuan["events"][0], "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert _node(vivian["events"][0], "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert result["totals"]["expected"]["value"] == pytest.approx(
        sum(item["modes"]["expected"]["known_value"] for item in result["events"])
    )
    assert result["totals"]["expected"]["value"] != pytest.approx(
        result["totals"]["expected"]["value"]
        + yixuan["totals"]["expected"]["value"]
        + vivian["totals"]["expected"]["value"]
    )


def test_vivian_panel_sources_cover_active_roles_without_anomaly_entries_and_report_zero_when_disabled() -> None:
    ye = "character:1431"
    astra = "character:1311"
    synthetic_entry, synthetic_template = _synthetic_panel_source_entry(
        CharacterId(ye), Element.PHYSICAL
    )
    assert synthetic_entry.move_id is None
    assert synthetic_entry.skill_group is None
    assert synthetic_entry.damage_tags == frozenset()
    assert synthetic_template.move_id is None

    def active_stats(*, attack: float, ap: float, am: float, physical: float, ether: float):
        return {
            "hp": 10000.0,
            "attack": attack,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.2,
            "crit_damage": 0.5,
            "anomaly_mastery": am,
            "anomaly_proficiency": ap,
            "energy_regen": 1.2,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "element_damage_bonus": {"physical": physical, "ether": ether},
        }

    payload = {
        "primary_character_id": ye,
        "supporting_character_ids": [astra, VIVIAN],
        "team_character_ids": [ye, astra, VIVIAN],
        "move_entry_id": "move-entry:ye:1431:basic-fast-1",
        "compile_configs": {
            ye: {"core_level": 1, "cinema_level": 0, "mingxin_active": False, "entry_move_uses_linren": False},
            astra: {"core_level": 1, "cinema_level": 0},
            VIVIAN: {"core_level": 7, "cinema_level": 2},
        },
        "condition_values": {MUTATION_CONDITION: True},
        "parameter_values": {},
        "character_builds": {
            ye: {"level": 60, "out_of_combat_stats": active_stats(attack=1000, ap=120, am=100, physical=0.2, ether=0.1)},
            astra: {"level": 60, "out_of_combat_stats": active_stats(attack=800, ap=150, am=100, physical=0.1, ether=0.4)},
            VIVIAN: {"level": 60, "out_of_combat_stats": active_stats(attack=1000, ap=200, am=144, physical=0.1, ether=0.3)},
        },
        "enemy": {
            "enemy_id": "enemy:vivian-panel-source",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2, "ether": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "enabled_rule_item_ids": [
            "rule:character:1331:core:anomaly-mutation:physical",
            "rule:character:1331:core:anomaly-mutation:ether",
        ],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }

    result = calculate_payload(payload)
    sources = {
        (item["source_character_id"], item["element"]): item
        for item in result["panel_source_results"]
    }
    ye_source = sources[(ye, "physical")]
    astra_source = sources[(astra, "ether")]
    vivian_source = sources[(VIVIAN, "ether")]
    assert ye_source["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]["anomaly_proficiency"] == pytest.approx(120)
    assert astra_source["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]["anomaly_proficiency"] == pytest.approx(150)
    assert vivian_source["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]["anomaly_proficiency"] == pytest.approx(200)
    assert all(item["totals"]["expected"]["complete"] for item in (ye_source, astra_source, vivian_source))
    assert result["totals"]["expected"]["value"] == pytest.approx(
        sum(item["modes"]["expected"]["known_value"] for item in result["events"])
    )

    payload["condition_values"][MUTATION_CONDITION] = False
    payload["enabled_rule_item_ids"] = []
    disabled = calculate_payload(payload)
    assert len(disabled["panel_source_results"]) == 3
    assert all(item["events"] == [] for item in disabled["panel_source_results"])
    assert all(item["totals"]["expected"]["value"] == 0.0 for item in disabled["panel_source_results"])
    assert all(item["totals"]["expected"]["complete"] for item in disabled["panel_source_results"])
    assert all(item["diagnostics"] == [] for item in disabled["panel_source_results"])

    blossom_payload = deepcopy(payload)
    blossom_payload["primary_character_id"] = VIVIAN
    blossom_payload["supporting_character_ids"] = [ye, astra]
    blossom_payload["team_character_ids"] = [VIVIAN, ye, astra]
    blossom_payload["move_entry_id"] = BLOSSOMS_ENTRY
    blossom_payload["compile_configs"][VIVIAN]["cinema_level"] = 6
    blossom_payload["condition_values"][MUTATION_CONDITION] = True
    blossom_payload["parameter_values"] = {"parameter:vivian:cinema6-feather-count": None}
    blossom_payload["enabled_rule_item_ids"] = [
        "rule:character:1331:core:anomaly-mutation:physical",
        "rule:character:1331:core:anomaly-mutation:ether",
        "rule:character:1331:cinema6:max-feather-mutation:physical",
        "rule:character:1331:cinema6:max-feather-mutation:ether",
    ]
    blossom_result = calculate_payload(blossom_payload)
    assert blossom_result["totals"]["expected"]["complete"] is True
    assert len(blossom_result["events"]) == 1
    assert blossom_result["events"][0]["damage_type"] == "direct"
    assert {item["source_character_id"] for item in blossom_result["panel_source_results"]} == {
        VIVIAN, ye, astra
    }
    assert any(
        not item["totals"]["expected"]["complete"] and item["diagnostics"]
        for item in blossom_result["panel_source_results"]
    )

    disabled_blossom = deepcopy(blossom_payload)
    disabled_blossom["condition_values"][MUTATION_CONDITION] = False
    disabled_blossom["enabled_rule_item_ids"] = [
        "rule:character:1331:core:anomaly-mutation:physical",
        "rule:character:1331:core:anomaly-mutation:ether",
    ]
    disabled_blossom_result = calculate_payload(disabled_blossom)
    assert disabled_blossom_result["totals"]["expected"]["complete"] is True
    assert all(
        item["totals"]["expected"]["value"] == 0.0
        and item["totals"]["expected"]["complete"]
        and not item["diagnostics"]
        for item in disabled_blossom_result["panel_source_results"]
    )


def test_wengine_stack_defaults_to_max_and_explicit_zero_or_middle_stack_is_kept() -> None:
    rule_id = "rule:wengine:13003:owner:1331:attack-per-energy-stack"

    def run(stack_count: int | None):
        payload = _payload(move_entry_id="move-entry:character:1331:basic-feather-flurry-1")
        payload["character_builds"][VIVIAN] = {
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": "wengine:13003",
            "wengine_level": 60,
            "wengine_refinement": 1,
            "drive_discs": [],
        }
        payload["enabled_rule_item_ids"] = [rule_id]
        if stack_count is not None:
            payload["rule_stack_counts"] = {rule_id: stack_count}
        return calculate_payload(payload)

    default = run(None)
    zero = run(0)
    middle = run(4)
    default_stack = next(item for item in default["panel_traces"] if item["rule_item_id"] == rule_id)
    middle_stack = next(item for item in middle["panel_traces"] if item["rule_item_id"] == rule_id)
    default_attack = next(item["stats"]["attack"] for item in default["resolved_character_snapshots"] if item["character_id"] == VIVIAN)
    zero_attack = next(item["stats"]["attack"] for item in zero["resolved_character_snapshots"] if item["character_id"] == VIVIAN)
    middle_attack = next(item["stats"]["attack"] for item in middle["resolved_character_snapshots"] if item["character_id"] == VIVIAN)
    assert default_stack["stack_count"] == 10
    assert middle_stack["stack_count"] == 4
    assert default_attack > middle_attack > zero_attack
    assert middle_attack - zero_attack == pytest.approx((default_attack - zero_attack) * 0.4)


def test_vivian_current_ap_changes_only_the_mutation_ratio_not_teammate_history() -> None:
    yixuan_stats = _stats(attack=777.0, ap=100.0, am=92.0)

    def run(vivian_ap: float):
        return calculate_payload(
            _payload(
                primary=YIXUAN,
                supporting=(VIVIAN,),
                move_entry_id=YIXUAN_XUANMO_ANOMALY,
                core_level=7,
                condition_values={MUTATION_CONDITION: True},
                enabled_rule_item_ids=(
                    "rule:character:1331:core:anomaly-mutation:ether:xuanmo",
                ),
                manual_stats={
                    YIXUAN: yixuan_stats,
                    VIVIAN: _stats(attack=1000.0, ap=vivian_ap, am=144.0),
                },
            )
        )

    ap200 = run(200.0)
    ap300 = run(300.0)
    source200 = _event(ap200, "event:character:1371:xuanmo-anomaly")
    source300 = _event(ap300, "event:character:1371:xuanmo-anomaly")
    mutation200 = _event(ap200, "event:character:1331:core-anomaly-mutation:ether-xuanmo")
    mutation300 = _event(ap300, "event:character:1331:core-anomaly-mutation:ether-xuanmo")
    source_trace200 = source200["modes"]["expected"]["anomaly_effect_strength_trace"]
    source_trace300 = source300["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert source_trace200["character_id"] == YIXUAN
    assert source_trace300["character_id"] == YIXUAN
    assert source_trace200["attack"] == source_trace300["attack"] == pytest.approx(777.0)
    assert source_trace200["anomaly_proficiency"] == source_trace300["anomaly_proficiency"] == pytest.approx(100.0)
    assert source_trace200["final_strength"] == source_trace300["final_strength"] == pytest.approx(1864.8)
    assert _node(mutation200, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert _node(mutation300, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.845)
    assert _node(mutation200, "anomaly.discharge.total-multiplier")["value"] == pytest.approx(15.375)
    assert _node(mutation300, "anomaly.discharge.total-multiplier")["value"] == pytest.approx(23.0625)
    assert _node(mutation200, "damage.base-value")["value"] == pytest.approx(28671.3)
    assert _node(mutation300, "damage.base-value")["value"] == pytest.approx(43006.95)
    assert source200["modes"]["expected"]["known_value"] == source300["modes"]["expected"]["known_value"]


def test_direct_blossom_keeps_known_hit_complete_and_shows_static_panel_sources_separately() -> None:
    result = calculate_payload(
        _payload(
            move_entry_id=BLOSSOMS_ENTRY,
            condition_values={
                TARGET_ANOMALY_CONDITION: True,
                MUTATION_CONDITION: True,
            },
            enabled_rule_item_ids=(CORE_MUTATION_RULE,),
        )
    )
    assert len(result["events"]) == 1
    main = result["events"][0]
    assert main["semantic_id"] == "event:character:1331:basic-feathering-blossoms:main"
    assert main["modes"]["expected"]["known_value"] is not None
    assert result["totals"]["expected"]["complete"] is True
    assert sum(item["modes"]["expected"]["known_value"] for item in result["events"]) == pytest.approx(
        result["totals"]["expected"]["value"]
    )
    source = next(
        item for item in result["panel_source_results"]
        if item["source_character_id"] == VIVIAN and item["element"] == "ether"
    )
    assert source["totals"]["expected"]["complete"] is True
    assert source["totals"]["expected"]["value"] > 0
    assert result["totals"]["expected"]["value"] != pytest.approx(
        result["totals"]["expected"]["value"] + source["totals"]["expected"]["value"]
    )

    definition = compile_vivian(
        VivianCompileConfig(),
        load_raw_record(load_character_record(VIVIAN)),
    )
    core_rule = next(
        item for item in definition.rule_items
        if str(item.rule_id) == "rule:character:1331:core:anomaly-mutation:ether"
    )
    explicit_history_placeholder = next(
        effect
        for effect in core_rule.effects
        if str(effect.rule.effect_id)
        == "effect:character:1331:core:direct-blossom-mutation-source"
    )
    assert explicit_history_placeholder.result.unresolved_template is not None


def test_extra_ability_creates_real_blossoms_hit_and_prophecy_ticks_from_other_anomaly_source() -> None:
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(VIVIAN,),
            move_entry_id=YIXUAN_XUANMO_ANOMALY,
            core_level=7,
            cinema_level=4,
            condition_values={
                FEATHER_CONDITION: True,
                MUTATION_CONDITION: True,
                TARGET_ANOMALY_CONDITION: True,
            },
            parameter_values={PROPHECY_TICK_COUNT: 2},
            enabled_rule_item_ids=(
                EXTRA_ABILITY_RULE,
                EXTRA_CORROSION_RULE,
                "rule:character:1331:core:anomaly-mutation:ether:xuanmo",
                "rule:character:1331:core:prophecy-ticks",
                C4_GUARANTEE_RULE,
            ),
        )
    )
    blossom = _event(result, "event:character:1331:extra-ability:feathering-blossoms")
    tick = _event(result, "event:character:1331:prophecy-tick")
    mutation = _event(result, "event:character:1331:core-anomaly-mutation:ether-xuanmo")
    definition = compile_registered_definition(
        VIVIAN,
        {"core_level": 7, "cinema_level": 4},
        (YIXUAN, VIVIAN),
    )
    extra_template = next(
        item for item in definition.damage_event_templates
        if str(item.ref.semantic_id) == "event:character:1331:extra-ability:feathering-blossoms"
    )
    tick_template = next(
        item for item in definition.damage_event_templates
        if str(item.ref.semantic_id) == "event:character:1331:prophecy-tick"
    )
    assert extra_template.move_id == BASIC_BLOSSOMS_MOVE_ID
    assert extra_template.ref.skill_group.value == "basic-attack"
    assert extra_template.ref.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert extra_template.damage_dealer == VIVIAN_ID
    assert tick_template.move_id is None
    assert tick_template.ref.damage_tags == frozenset()
    assert blossom["modes"]["expected"]["known_value"] == pytest.approx(blossom["modes"]["full-crit"]["known_value"])
    assert "effect:character:1331:cinema4:basic-guaranteed-crit" in blossom["common_application_trace"]["guaranteed_crit_effect_ids"]
    assert tick["repeat_count"] == 2
    assert _node(tick, "damage.skill-multiplier")["value"] == pytest.approx(0.55)
    assert mutation["modes"]["expected"]["anomaly_record_id"] == "anomaly:yixuan:xuanmo-current"
    assert result["totals"]["expected"]["complete"] is True


def test_c4_attack_buff_is_separate_from_prophecy_and_c6_feather_count_scales_linearly() -> None:
    c4 = calculate_payload(
        _payload(
            move_entry_id=BLOSSOMS_ENTRY,
            cinema_level=4,
            condition_values={"condition:vivian:mind4-attack-buff-active": True, "condition:vivian:prophecy-active": False},
            enabled_rule_item_ids=("rule:character:1331:cinema4:prophecy-attack",),
        )
    )
    snapshot = next(item for item in c4["resolved_character_snapshots"] if item["character_id"] == VIVIAN)
    assert snapshot["stats"]["attack"] == pytest.approx(1120.0)

    definition = compile_vivian(VivianCompileConfig(cinema_level=6), load_raw_record(load_character_record(VIVIAN)))
    feather_parameter = next(item for item in definition.scenario_parameters if item.parameter_id == C6_FEATHER_COUNT)
    assert feather_parameter.value == 5
    assert feather_parameter.minimum == 0
    assert feather_parameter.maximum == 5

    one_feather = calculate_payload(
        _payload(
            move_entry_id=ANOMALY_ENTRY,
            core_level=7,
            cinema_level=6,
            condition_values={MUTATION_CONDITION: True},
            parameter_values={str(C6_FEATHER_COUNT): 1},
            enabled_rule_item_ids=("rule:character:1331:cinema6:max-feather-mutation:ether",),
        )
    )
    five_feathers = calculate_payload(
        _payload(
            move_entry_id=ANOMALY_ENTRY,
            core_level=7,
            cinema_level=6,
            condition_values={MUTATION_CONDITION: True},
            enabled_rule_item_ids=("rule:character:1331:cinema6:max-feather-mutation:ether",),
        )
    )
    one_event = _event(one_feather, "event:character:1331:cinema6-max-feather-mutation:ether")
    five_event = _event(five_feathers, "event:character:1331:cinema6-max-feather-mutation:ether")
    assert one_event["repeat_count"] == 1
    assert five_event["repeat_count"] == 5
    assert _node(one_event, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert _node(five_event, "discharge.proficiency-multiplier")["value"] == pytest.approx(1.23)
    assert five_event["modes"]["expected"]["known_value"] == pytest.approx(
        one_event["modes"]["expected"]["known_value"] * 5
    )
    zero_feathers = calculate_payload(
        _payload(
            move_entry_id=ANOMALY_ENTRY,
            core_level=7,
            cinema_level=6,
            condition_values={MUTATION_CONDITION: True},
            parameter_values={str(C6_FEATHER_COUNT): 0},
            enabled_rule_item_ids=("rule:character:1331:cinema6:max-feather-mutation:ether",),
        )
    )
    assert len(zero_feathers["events"]) == 1
    assert zero_feathers["totals"]["expected"]["complete"] is True


def test_additional_ability_corrosion_bonus_does_not_require_feather_and_c1_hits_disorder_lane() -> None:
    result = calculate_payload(
        _payload(
            supporting=(ASTRA,),
            move_entry_id="move-entry:character:1331:ether-corrosion-disorder",
            cinema_level=1,
            condition_values={"condition:vivian:prophecy-active": True},
            enabled_rule_item_ids=(
                EXTRA_CORROSION_RULE,
                "rule:character:1331:cinema1:prophecy-disorder-damage",
            ),
        )
    )
    event = _event(result, "event:character:1331:ether-corrosion-disorder")
    assert _node(event, "disorder.trigger.damage-bonus")["value"] == pytest.approx(0.28)
    assert _node(event, "disorder.damage-bonus-region")["value"] == pytest.approx(1.28)
    assert _node(event, "disorder.total-multiplier")["value"] == pytest.approx(17.0)
    assert _node(event, "damage.base-value")["value"] == pytest.approx(81600.0)
    assert event["modes"]["expected"]["status"] == "calculated"
    assert result["totals"]["expected"]["complete"] is True


def test_c6_ether_bonus_is_a_vivian_owned_normal_lane_modifier_only() -> None:
    common = dict(
        supporting=(ASTRA,),
        move_entry_id="move-entry:character:1331:basic-lady-dance",
        cinema_level=6,
    )
    without = calculate_payload(_payload(**common))
    with_bonus = calculate_payload(
        _payload(
            **common,
            enabled_rule_item_ids=("rule:character:1331:cinema6:ether-damage-and-feather-resource",),
        )
    )
    baseline_event = _event(without, "event:character:1331:basic-lady-dance:main")
    event = _event(with_bonus, "event:character:1331:basic-lady-dance:main")
    assert _node(baseline_event, "damage.normal-bonus-region")["value"] == pytest.approx(1.2)
    assert _node(event, "damage.normal-bonus-region")["value"] == pytest.approx(1.6)
    assert event["modes"]["expected"]["known_value"] > baseline_event["modes"]["expected"]["known_value"]
    applied = event["common_application_trace"]["applied_modifiers"]
    assert any(item["effect_id"] == "effect:character:1331:cinema6:ether-normal-damage" for item in applied)
    snapshots = {item["character_id"]: item for item in with_bonus["resolved_character_snapshots"]}
    assert snapshots[ASTRA]["stats"]["attack"] == pytest.approx(800.0)

    own_disorder = calculate_payload(
        _payload(
            supporting=(ASTRA,),
            move_entry_id="move-entry:character:1331:ether-corrosion-disorder",
            cinema_level=6,
            enabled_rule_item_ids=("rule:character:1331:cinema6:ether-damage-and-feather-resource",),
        )
    )
    disorder_event = _event(own_disorder, "event:character:1331:ether-corrosion-disorder")
    source_trace = disorder_event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert source_trace["normal_bonus"] == pytest.approx(0.40)
    assert source_trace["final_strength"] == pytest.approx(6400.0)
    assert _node(disorder_event, "damage.base-value")["value"] == pytest.approx(108800.0)


def test_prophecy_missing_tick_count_is_partial_and_zero_ticks_add_no_event() -> None:
    active = calculate_payload(
        _payload(move_entry_id=FALL_ENTRY, condition_values={TARGET_ANOMALY_CONDITION: True}, enabled_rule_item_ids=("rule:character:1331:core:prophecy-ticks",))
    )
    assert active["totals"]["expected"]["complete"] is False
    assert not any(item["semantic_id"] == "event:character:1331:prophecy-tick" for item in active["events"])

    zero = calculate_payload(
        _payload(
            move_entry_id=FALL_ENTRY,
            condition_values={TARGET_ANOMALY_CONDITION: True},
            parameter_values={PROPHECY_TICK_COUNT: 0},
            enabled_rule_item_ids=("rule:character:1331:core:prophecy-ticks",),
        )
    )
    assert zero["totals"]["expected"]["complete"] is True
    assert not any(item["semantic_id"] == "event:character:1331:prophecy-tick" for item in zero["events"])


def test_prophecy_tick_is_selectable_with_explicit_count_and_no_time_replay() -> None:
    result = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1331:core-prophecy-tick",
            condition_values={TARGET_ANOMALY_CONDITION: True},
            parameter_values={PROPHECY_TICK_COUNT: 2},
        )
    )
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["repeat_count"] == 2
    assert event["damage_type"] == "direct"

    default = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1331:core-prophecy-tick",
            condition_values={TARGET_ANOMALY_CONDITION: True},
        )
    )
    assert default["totals"]["expected"]["complete"] is True
    assert default["events"][0]["repeat_count"] == 1

    explicit_zero = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1331:core-prophecy-tick",
            condition_values={TARGET_ANOMALY_CONDITION: True},
            parameter_values={PROPHECY_TICK_COUNT: 0},
        )
    )
    assert explicit_zero["totals"]["expected"]["complete"] is True
    assert explicit_zero["events"][0]["repeat_count"] == 0
    assert explicit_zero["totals"]["expected"]["value"] == pytest.approx(0.0)


def test_vivian_basic_element_stages_and_remaining_mixed_named_moves_are_ether() -> None:
    definition = compile_vivian(VivianCompileConfig(), load_raw_record(load_character_record(VIVIAN)))
    templates = {str(item.ref.template_id): item for item in definition.damage_event_templates}
    for stage in (1, 2):
        template = templates[f"template:character:1331:basic-feather-flurry-{stage}:main"]
        assert template.element is Element.PHYSICAL
        result = calculate_payload(_payload(move_entry_id=f"move-entry:character:1331:basic-feather-flurry-{stage}"))
        assert result["totals"]["expected"]["complete"] is True
    for stage in (3, 4):
        template = templates[f"template:character:1331:basic-feather-flurry-{stage}:main"]
        assert template.element is Element.ETHER
        result = calculate_payload(_payload(move_entry_id=f"move-entry:character:1331:basic-feather-flurry-{stage}"))
        assert result["totals"]["expected"]["complete"] is True
    assert templates["template:character:1331:dash-silver-thorn:main"].element is Element.PHYSICAL
    for entry_id in (
        "move-entry:character:1331:dodge-feather-blade-counter",
        "move-entry:character:1331:special-silver-aria",
        "move-entry:character:1331:quick-assist-feather-guard",
    ):
        assert calculate_payload(_payload(move_entry_id=entry_id))["totals"]["expected"]["complete"] is True


def test_equipment_build_includes_vivian_level_60_base_anomaly_stats() -> None:
    result = calculate_payload(_payload(move_entry_id=FALL_ENTRY, equipment_build=True))
    snapshot = next(item for item in result["resolved_character_snapshots"] if item["character_id"] == VIVIAN)
    assert snapshot["stats"]["attack"] > 880.6952
    assert snapshot["stats"]["anomaly_proficiency"] > 118.0
    assert snapshot["stats"]["anomaly_mastery"] == pytest.approx(144.0)
    assert result["build_provenance"]


def test_c6_normal_ether_bonus_does_not_rewrite_teammate_history_or_mutation_lane() -> None:
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(VIVIAN,),
            move_entry_id=YIXUAN_XUANMO_ANOMALY,
            core_level=7,
            cinema_level=6,
            condition_values={MUTATION_CONDITION: True},
            enabled_rule_item_ids=(
                "rule:character:1331:core:anomaly-mutation:ether:xuanmo",
                "rule:character:1331:cinema6:ether-damage-and-feather-resource",
            ),
        )
    )
    source = _event(result, "event:character:1371:xuanmo-anomaly")
    mutation = _event(result, "event:character:1331:core-anomaly-mutation:ether-xuanmo")
    trace = source["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["character_id"] == YIXUAN
    assert trace["normal_bonus"] == pytest.approx(0.0)
    assert _node(mutation, "anomaly.discharge.damage-bonus-region")["value"] == pytest.approx(1.0)
    assert not any(
        item["effect_id"] == "effect:character:1331:cinema6:ether-normal-damage"
        for item in mutation["common_application_trace"]["applied_modifiers"]
    )
