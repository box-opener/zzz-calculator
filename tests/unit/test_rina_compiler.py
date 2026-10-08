from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.rina import (
    RINA_ID,
    RinaCompileConfig,
    compile_rina,
    load_raw_record,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
    load_wengine_raw_record,
)
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import CalculationNode, CharacterId, Element, SkillGroup, WEngineBuildInput, WEngineId
from core.application.moves import MultiplierRelation
from web.api import app


client = TestClient(app)


def _stats(character_id: CharacterId) -> dict[str, object]:
    panel = character_base_stats(character_id)
    result: dict[str, object] = {
        name: getattr(panel, name).value
        for name in (
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
    result["element_damage_bonus"] = {
        element.value: value.value
        for element, value in panel.element_damage_bonus.items()
    }
    return result


def _payload(
    move_entry_id: str,
    *,
    potential: int = 0,
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    supporting: tuple[str, ...] = (),
) -> dict[str, object]:
    primary = str(RINA_ID)
    team = [primary, *supporting]
    configs = {
        item: (
            {"core_level": 7, "cinema_level": cinema, "potential_level": potential}
            if item == primary
            else {"core_level": 7, "cinema_level": 0}
        )
        for item in team
    }
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _stats(CharacterId(item))}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:rina-test",
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
            "stun_vulnerability_bonus": 1.0,
            "is_stunned": False,
        },
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_rina_source_registration_panel_defaults_and_signature() -> None:
    source = load_raw_record(load_character_record(str(RINA_ID)), potential_level=0)
    assert source.name == "丽娜"
    assert source.code_name == "Rina"
    assert source.rarity == 4
    assert source.specialty == "支援"
    assert source.element == "电属性"
    assert source.faction == "维多利亚家政"
    assert source.source_version == "3.2"
    assert source.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1211.json"
    assert str(RINA_ID) in supported_character_ids()

    panel = character_base_stats(RINA_ID)
    assert panel.hp.value == pytest.approx(8609.2122)
    assert panel.attack.value == pytest.approx(717.1859)
    assert panel.defense.value == pytest.approx(600.5916)
    assert panel.penetration_rate.value == pytest.approx(0.144)

    config = RinaCompileConfig()
    assert config.core_level == 7
    assert config.cinema_level == 0
    assert config.potential_level == 0
    assert config.skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(RINA_ID)
    assert registration.catalog.rarity == "S"
    assert registration.catalog.code_name == "Rina"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    editor_defaults = {
        item.field_id: item.value
        for item in registration.config_fields({}, (RINA_ID,))
    }
    assert all(
        editor_defaults[f"skill_level:{group}"] == 12
        for group in ("basic-attack", "dodge", "special-attack", "chain-attack", "assist", "ultimate")
    )
    assert SIGNATURE_WENGINE_BY_CHARACTER[RINA_ID] == WEngineId("wengine:14121")
    weapon = load_wengine_raw_record("wengine:14121")
    assert weapon.icon == "Weapon_S_1211"
    engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14121"), RINA_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert engine.complete is True
    assert engine.contributions[0].value.value == pytest.approx(684.0)
    assert engine.contributions[1].value.value == pytest.approx(0.24)
    off_field = next(
        item for item in engine.rule_items
        if str(item.rule_id).endswith(":off-field-energy-regen")
    )
    assert off_field.effects[0].result.modifier_path is CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS
    increment = next(
        item for item in engine.rule_items
        if str(item.rule_id).endswith(":damage-buff-increment")
    )
    assert (increment.stack_count, increment.stack_min, increment.stack_max) == (6, 0, 6)

    payload = _payload(
        "move-entry:character:1211:special-electric",
        enabled=(
            "rule:wengine:14121:owner:1211:off-field-energy-regen",
            "rule:wengine:14121:owner:1211:damage-buff-base",
            "rule:wengine:14121:owner:1211:damage-buff-increment",
        ),
        conditions={
            "condition:wengine:14121:owner:1211:off-field-energy-regen-active": True,
            "condition:wengine:14121:owner:1211:damage-buff-active": True,
        },
    )
    payload["character_builds"][str(RINA_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14121",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }
    result = _calculate(payload)
    snapshot = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == str(RINA_ID)
    )
    assert snapshot["stats"]["attack"] == pytest.approx(1401.1859)
    assert snapshot["stats"]["penetration_rate"] == pytest.approx(0.384)
    assert snapshot["stats"]["energy_regen"] == pytest.approx(1.8)
    normal_bonus = next(
        item["value"]
        for item in result["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    )
    assert normal_bonus == pytest.approx(0.202)


def test_rina_reviewed_direct_curves_and_unknown_elements_stay_local() -> None:
    raw = load_raw_record(load_character_record(str(RINA_ID)), potential_level=0)
    definition = compile_rina(RinaCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    expected_ratios = {
        "basic-hold-electric": 6.308,
        "dash-physical": 2.106,
        "dodge-counter-electric": 4.553,
        "special-electric": 1.229,
        "ex-electric": 10.927,
        "chain-electric": 20.261,
        "ultimate-electric": 42.342,
        "quick-assist-electric": 2.458,
        "assist-strike-electric": 6.992,
    }
    for key, expected in expected_ratios.items():
        entry = entries[f"move-entry:character:1211:{key}"]
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(expected)
    assert entries["move-entry:character:1211:basic-hold-electric"].main_damage_event.element is Element.ELECTRIC
    for stage in range(1, 5):
        entry = entries[f"move-entry:character:1211:basic-stage-{stage}-element-unresolved"]
        assert entry.multiplier_relation is MultiplierRelation.UNRESOLVED_RELATION

    for stage in range(1, 5):
        result = _calculate(_payload(f"move-entry:character:1211:basic-stage-{stage}-element-unresolved"))
        assert result["events"] == []
        assert result["totals"]["expected"]["complete"] is False


def test_rina_morning_and_midnight_sweep_are_potential_one_current_state_entries() -> None:
    source = load_character_record(str(RINA_ID))
    raw0 = load_raw_record(source, potential_level=0)
    raw1 = load_raw_record(source, potential_level=1)
    p0 = compile_rina(RinaCompileConfig(potential_level=0), raw0)
    p1 = compile_rina(RinaCompileConfig(potential_level=1), raw1)
    p0_entries = {str(item.entry_id) for item in p0.move_entries}
    p1_entries = {str(item.entry_id) for item in p1.move_entries}
    assert "move-entry:character:1211:potential1-midnight-sweep" not in p0_entries
    assert "move-entry:character:1211:potential1-midnight-sweep" in p1_entries
    assert all(
        f"move-entry:character:1211:potential1-morning-sweep-hit-{stage}-element-unresolved"
        in p1_entries
        for stage in range(1, 4)
    )

    unresolved = _calculate(
        _payload("move-entry:character:1211:potential1-morning-sweep-hit-1-element-unresolved", potential=1)
    )
    assert unresolved["events"] == []
    assert unresolved["totals"]["expected"]["complete"] is False

    midnight_without_stacks = _calculate(
        _payload("move-entry:character:1211:potential1-midnight-sweep", potential=1)
    )
    assert midnight_without_stacks["events"] == []
    assert midnight_without_stacks["totals"]["expected"]["complete"] is False

    midnight_ready = _calculate(
        _payload(
            "move-entry:character:1211:potential1-midnight-sweep",
            potential=1,
            conditions={"condition:rina:fear-stacks-full": True},
        )
    )
    assert len(midnight_ready["events"]) == 1
    assert midnight_ready["events"][0]["element"] == "electric"
    assert midnight_ready["totals"]["expected"]["complete"] is True


def test_rina_core_current_penetration_buff_targets_teammates_and_extra_ability_is_electric() -> None:
    support = ("character:1181",)
    enabled = (
        "rule:character:1211:core:other-agents-penetration-rate",
        "rule:character:1211:extra-ability:team-electric-damage-while-shocked",
    )
    conditions = {
        "condition:rina:core-pen-buff-active": True,
        "condition:rina:target-shocked": True,
    }
    electric = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            conditions=conditions,
            enabled=enabled,
            supporting=support,
        )
    )
    snapshots = {item["character_id"]: item["stats"] for item in electric["resolved_character_snapshots"]}
    assert snapshots["character:1211"]["penetration_rate"] == pytest.approx(0.144)
    assert snapshots["character:1181"]["penetration_rate"] == pytest.approx(0.156)
    electric_breakdown = {
        item["node"]: item["value"]
        for item in electric["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    assert electric_breakdown["damage.normal-bonus"] == pytest.approx(0.10)

    physical = _calculate(
        _payload(
            "move-entry:character:1211:dash-physical",
            conditions=conditions,
            enabled=enabled,
            supporting=support,
        )
    )
    physical_breakdown = {
        item["node"]: item["value"]
        for item in physical["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    assert physical_breakdown["damage.normal-bonus"] == pytest.approx(0.0)


def test_rina_cinema_one_nearby_state_replaces_base_core_pen_value_with_130_percent() -> None:
    result = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            cinema=1,
            conditions={
                "condition:rina:core-pen-buff-active": True,
                "condition:rina:dolls-nearby-bonus-active": True,
            },
            enabled=(
                "rule:character:1211:core:other-agents-penetration-rate",
                "rule:character:1211:core:other-agents-penetration-rate-enhanced",
            ),
            supporting=("character:1181",),
        )
    )
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots["character:1181"]["penetration_rate"] == pytest.approx(0.2028)


def test_rina_potential_two_adds_penetration_and_team_stats_only_while_core_buff_is_active() -> None:
    rules = (
        "rule:character:1211:potential2-6:self-penetration-rate",
        "rule:character:1211:potential2-6:team-atk-def-from-pen",
        "rule:character:1211:core:other-agents-penetration-rate",
    )
    support = ("character:1181",)
    active = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            potential=2,
            conditions={"condition:rina:core-pen-buff-active": True},
            enabled=rules,
            supporting=support,
        )
    )
    snapshots = {item["character_id"]: item for item in active["resolved_character_snapshots"]}
    assert snapshots["character:1211"]["stats"]["penetration_rate"] == pytest.approx(0.16)
    assert snapshots["character:1181"]["stats"]["penetration_rate"] == pytest.approx(0.16)
    assert snapshots["character:1211"]["stats"]["attack"] == pytest.approx(765.1859)
    assert snapshots["character:1181"]["stats"]["attack"] == pytest.approx(
        character_base_stats(CharacterId("character:1181")).attack.value + 48.0
    )

    inactive = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            potential=2,
            conditions={"condition:rina:core-pen-buff-active": False},
            enabled=rules,
            supporting=support,
        )
    )
    inactive_snapshots = {item["character_id"]: item for item in inactive["resolved_character_snapshots"]}
    assert inactive_snapshots["character:1211"]["stats"]["penetration_rate"] == pytest.approx(0.16)
    assert inactive_snapshots["character:1181"]["stats"]["penetration_rate"] == pytest.approx(0.0)
    assert inactive_snapshots["character:1181"]["stats"]["attack"] == pytest.approx(
        character_base_stats(CharacterId("character:1181")).attack.value
    )


def test_rina_cinema_four_energy_regen_uses_the_current_dolls_away_state() -> None:
    rule = "rule:character:1211:cinema4:energy-regen-while-dolls-away"
    active = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            cinema=4,
            conditions={"condition:rina:cinema4-dolls-away": True},
            enabled=(rule,),
        )
    )
    active_rina = next(
        item for item in active["resolved_character_snapshots"]
        if item["character_id"] == str(RINA_ID)
    )
    assert active_rina["stats"]["energy_regen"] == pytest.approx(1.7)

    inactive = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            cinema=4,
            enabled=(rule,),
        )
    )
    inactive_rina = next(
        item for item in inactive["resolved_character_snapshots"]
        if item["character_id"] == str(RINA_ID)
    )
    assert inactive_rina["stats"]["energy_regen"] == pytest.approx(1.2)


def test_rina_cinema_damage_bonuses_follow_self_and_electric_scopes() -> None:
    c2 = _calculate(
        _payload(
            "move-entry:character:1211:dash-physical",
            cinema=2,
            conditions={"condition:rina:cinema2-damage-bonus-active": True},
            enabled=("rule:character:1211:cinema2:self-damage-bonus",),
        )
    )
    c2_breakdown = {
        item["node"]: item["value"]
        for item in c2["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    assert c2_breakdown["damage.normal-bonus"] == pytest.approx(0.15)

    c6_electric = _calculate(
        _payload(
            "move-entry:character:1211:special-electric",
            cinema=6,
            conditions={"condition:rina:cinema6-electric-damage-bonus-active": True},
            enabled=("rule:character:1211:cinema6:team-electric-damage-bonus",),
        )
    )
    c6_physical = _calculate(
        _payload(
            "move-entry:character:1211:dash-physical",
            cinema=6,
            conditions={"condition:rina:cinema6-electric-damage-bonus-active": True},
            enabled=("rule:character:1211:cinema6:team-electric-damage-bonus",),
        )
    )
    electric_breakdown = {
        item["node"]: item["value"]
        for item in c6_electric["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    physical_breakdown = {
        item["node"]: item["value"]
        for item in c6_physical["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    assert electric_breakdown["damage.normal-bonus"] == pytest.approx(0.15)
    assert physical_breakdown["damage.normal-bonus"] == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("rina_ticks", "lucy_ticks", "expected"),
    ((6, 0, 0.202), (0, 6, 0.398)),
)
def test_crying_cradle_same_name_buff_uses_the_max_complete_instance(
    rina_ticks: int,
    lucy_ticks: int,
    expected: float,
) -> None:
    support = ("character:1151",)
    payload = _payload(
        "move-entry:character:1211:special-electric",
        supporting=support,
        conditions={
            "condition:wengine:14121:owner:1211:damage-buff-active": True,
            "condition:wengine:14121:owner:1151:damage-buff-active": True,
        },
        enabled=(
            "rule:wengine:14121:owner:1211:damage-buff-base",
            "rule:wengine:14121:owner:1211:damage-buff-increment",
            "rule:wengine:14121:owner:1151:damage-buff-base",
            "rule:wengine:14121:owner:1151:damage-buff-increment",
        ),
    )
    for character_id, refinement in ((str(RINA_ID), 1), ("character:1151", 5)):
        payload["character_builds"][character_id] = {
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": "wengine:14121",
            "wengine_level": 60,
            "wengine_refinement": refinement,
            "drive_discs": [],
        }
    payload["rule_stack_counts"] = {
        "rule:wengine:14121:owner:1211:damage-buff-increment": rina_ticks,
        "rule:wengine:14121:owner:1151:damage-buff-increment": lucy_ticks,
    }
    result = _calculate(payload)
    breakdown = {
        item["node"]: item["value"]
        for item in result["events"][0]["modes"]["expected"]["calculation_breakdown"]
    }
    assert breakdown["damage.normal-bonus"] == pytest.approx(expected)


@pytest.mark.parametrize(
    ("move_entry_id", "element"),
    (
        ("move-entry:character:1211:special-electric", "electric"),
        ("move-entry:character:1211:dash-physical", "physical"),
    ),
)
def test_rina_known_direct_moves_calculate_as_single_complete_events(move_entry_id: str, element: str) -> None:
    result = _calculate(_payload(move_entry_id))
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    assert result["events"][0]["element"] == element


def test_rina_static_electric_shock_and_disorder_use_current_record_contract() -> None:
    shock = _calculate(_payload("move-entry:character:1211:electric-shock"))
    assert shock["totals"]["expected"]["complete"] is True
    assert len(shock["events"]) == 1
    assert shock["events"][0]["repeat_count"] == 10
    assert shock["events"][0]["element"] == "electric"
    assert shock["events"][0]["modes"]["expected"]["value"] == pytest.approx(857.378731087882)
    assert shock["totals"]["expected"]["value"] == pytest.approx(8573.787310878819)

    disorder = _calculate(_payload("move-entry:character:1211:electric-disorder"))
    assert disorder["totals"]["expected"]["complete"] is True
    assert len(disorder["events"]) == 1
    ratio = next(
        item["value"]
        for item in disorder["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "disorder.total-multiplier"
    )
    assert ratio == pytest.approx(17.0)
