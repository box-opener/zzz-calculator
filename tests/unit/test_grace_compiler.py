from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.grace import (
    GRACE_ID,
    GraceCompileConfig,
    compile_grace,
    load_raw_record,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, compile_wengine, load_wengine_raw_record
from core.application.execution.event_factory import instantiate_damage_event
from core.application.characters.templates import DischargeDamageEventTemplate
from core.data.loader import load_character_record, supported_character_ids
from core.application.characters.velina import VelinaCompileConfig, compile_velina, load_raw_record as load_velina_raw_record
from core.application.characters.burnice import BurniceCompileConfig, compile_burnice, load_raw_record as load_burnice_raw_record
from core.types import AnomalyRecordId, AnomalySourceChoice, BattleStateId, EnemyId, FixedMultiplier, Resolved, WEngineBuildInput
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import CharacterId, DamageTag, Element, SkillGroup, WEngineId
from web.api import app


client = TestClient(app)


def _panel_stats(character_id: CharacterId) -> dict[str, object]:
    panel = character_base_stats(character_id)
    result: dict[str, object] = {
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
    source: dict[str, str] | None = None,
    supporting: tuple[str, ...] = (),
    stacks: dict[str, int] | None = None,
) -> dict[str, object]:
    team = [str(GRACE_ID)]
    for character_id in supporting:
        if character_id not in team:
            team.append(character_id)
    if source is not None and source["source_character_id"] not in team:
        team.append(source["source_character_id"])
    builds = {
        character_id: {
            "level": 60,
            "out_of_combat_stats": _panel_stats(CharacterId(character_id)),
        }
        for character_id in team
    }
    configs = {}
    for character_id in team:
        configs[character_id] = {
            "core_level": 7,
            "cinema_level": cinema if character_id == str(GRACE_ID) else 0,
        }
        if character_id == str(GRACE_ID):
            configs[character_id]["potential_level"] = potential
    payload: dict[str, object] = {
        "primary_character_id": str(GRACE_ID),
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": stacks or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:grace-test",
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
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
    }
    if source is not None:
        payload["grace_anomaly_source"] = source
    return payload


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_grace_live_source_registry_signature_and_panel() -> None:
    raw = load_raw_record(load_character_record(str(GRACE_ID)), potential_level=0)
    assert raw.name == "格莉丝"
    assert raw.code_name == "Grace"
    assert raw.rarity == 4
    assert raw.specialty == "异常"
    assert raw.element == "电属性"
    assert raw.faction == "白祇重工"
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1181.json"
    assert str(GRACE_ID) in supported_character_ids()
    assert character_base_stats(GRACE_ID).attack.value == pytest.approx(825.9679)
    assert character_base_stats(GRACE_ID).hp.value == pytest.approx(7482.7069)
    assert character_base_stats(GRACE_ID).anomaly_proficiency.value == pytest.approx(116.0)
    assert character_base_stats(GRACE_ID).anomaly_mastery.value == pytest.approx(151.0)
    assert GraceCompileConfig().core_level == 7
    assert GraceCompileConfig().cinema_level == 0
    assert GraceCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(GRACE_ID)
    assert registration.catalog.rarity == "S"
    assert next(item for item in supported_character_catalog() if item.character_id == str(GRACE_ID)).code_name == "Grace"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert SIGNATURE_WENGINE_BY_CHARACTER[GRACE_ID] == WEngineId("wengine:14118")
    weapon = load_wengine_raw_record("wengine:14118")
    assert weapon.icon == "Weapon_S_1181"
    assert weapon.source_url == "https://static.nanoka.cc/zzz/3.2/zh/weapon/14118.json"
    engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14118"), GRACE_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert engine.complete is True
    assert engine.contributions[0].value == Resolved(684.0)
    assert engine.contributions[1].value == Resolved(0.24)


def test_grace_direct_curves_potential_unlocks_and_ultimate_leveling() -> None:
    source = load_character_record(str(GRACE_ID))
    p0 = compile_grace(
        GraceCompileConfig(core_level=7, cinema_level=0, potential_level=0),
        load_raw_record(source, potential_level=0),
    )
    p1 = compile_grace(
        GraceCompileConfig(core_level=7, cinema_level=0, potential_level=1),
        load_raw_record(source, potential_level=1),
    )
    p3 = compile_grace(
        GraceCompileConfig(core_level=7, cinema_level=3, potential_level=0),
        load_raw_record(source, potential_level=0),
    )
    p6 = compile_grace(
        GraceCompileConfig(core_level=7, cinema_level=5, potential_level=6),
        load_raw_record(source, potential_level=6),
    )
    p0_entries = {str(item.entry_id): item for item in p0.move_entries}
    p1_entries = {str(item.entry_id): item for item in p1.move_entries}
    raw_p0 = load_raw_record(source, potential_level=0)
    raw_p1 = load_raw_record(source, potential_level=1)

    assert "其他<color=#FFFFFF>[异常]</color>角色" not in raw_p0.core_levels[0].extra_ability_description
    assert "其他<color=#FFFFFF>[异常]</color>角色" in raw_p1.core_levels[0].extra_ability_description
    assert "move-entry:character:1181:potential1-pulse-grenade" not in p0_entries
    assert "move-entry:character:1181:potential1-pulse-grenade" in p1_entries
    assert p0_entries["move-entry:character:1181:dodge-counter"].main_damage_event.element is Element.ELECTRIC
    assert p0_entries["move-entry:character:1181:dash-attack"].main_damage_event.element is Element.PHYSICAL
    assert p0_entries["move-entry:character:1181:basic-step-shot"].main_damage_event.element is Element.PHYSICAL
    assert p0_entries["move-entry:character:1181:assist-strike"].damage_tags == frozenset({DamageTag.ASSIST})
    for stage in (1, 2, 3):
        entry = p0_entries[f"move-entry:character:1181:basic-stage-{stage}"]
        assert entry.main_damage_event.element is Element.PHYSICAL
        assert entry.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    stage4 = p0_entries["move-entry:character:1181:basic-stage-4"]
    assert stage4.main_damage_event.element is Element.ELECTRIC
    assert stage4.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    assert tuple(
        p0_entries[f"move-entry:character:1181:basic-stage-{stage}"].multiplier_variants[0].multiplier.value.value
        for stage in range(1, 5)
    ) == pytest.approx((1.112, 1.202, 2.502, 3.733))
    assert p0_entries["move-entry:character:1181:ex-special-two-grenades"].multiplier_variants[0].multiplier.value.value == pytest.approx(6.682)
    assert p1_entries["move-entry:character:1181:potential1-cycle-single-throw"].multiplier_variants[0].multiplier.value.value == pytest.approx((563.4 + 11 * 51.3) / 29 / 100)
    assert p1_entries["move-entry:character:1181:potential1-vortex-grenade"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.755)
    assert p1_entries["move-entry:character:1181:potential1-pulse-grenade"].multiplier_variants[0].multiplier.value.value == pytest.approx(0.849)
    ult0 = p0_entries["move-entry:character:1181:ultimate"].multiplier_variants[0].multiplier.value.value
    ult3 = next(item for item in p3.move_entries if str(item.entry_id) == "move-entry:character:1181:ultimate").multiplier_variants[0].multiplier.value.value
    ult5 = next(item for item in p6.move_entries if str(item.entry_id) == "move-entry:character:1181:ultimate").multiplier_variants[0].multiplier.value.value
    assert ult0 == pytest.approx(29.583)
    assert ult3 == pytest.approx(32.273)
    assert ult5 == pytest.approx(34.963)


def test_grace_potential1_discharge_uses_one_selected_current_panel_record() -> None:
    result = _calculate(_payload(
        "move-entry:character:1181:potential1-pulse-grenade",
        potential=1,
        conditions={"condition:grace:pulse-grenade-ready": True},
        enabled=("rule:character:1181:potential1:pulse-discharge",),
        source={"source_character_id": "character:1011", "element": "electric"},
    ))
    events = result["events"]
    assert len(events) == 2
    assert events[0]["damage_type"] == "direct"
    assert events[1]["damage_type"] == "anomaly"
    assert events[1]["damage_subtype"] == "discharge"
    assert "potential1:pulse-discharge" in events[1]["semantic_id"]
    assert events[1]["modes"]["expected"]["status"] == "calculated"
    assert events[0]["modes"]["expected"]["value"] == pytest.approx(345.6751454435706)
    assert events[1]["modes"]["expected"]["value"] == pytest.approx(2063.0582650393703)
    assert events[1]["modes"]["expected"]["anomaly_record_id"] == "anomaly:static-source:character:1011:electric"
    self_result = _calculate(_payload(
        "move-entry:character:1181:potential1-pulse-grenade",
        potential=1,
        conditions={"condition:grace:pulse-grenade-ready": True},
        enabled=("rule:character:1181:potential1:pulse-discharge",),
        source={"source_character_id": str(GRACE_ID), "element": "electric"},
    ))
    assert self_result["events"][1]["modes"]["expected"]["value"] == pytest.approx(3225.4671849254996)

    alias_result = _calculate(_payload(
        "move-entry:character:1181:potential1-pulse-grenade",
        potential=1,
        conditions={"condition:grace:pulse-grenade-ready": True},
        enabled=("rule:character:1181:potential1:pulse-discharge",),
        source={"source_character_id": "character:1371", "element": "ether:xuanmo"},
    ))
    assert alias_result["events"][1]["element"] == "ether:xuanmo"
    assert alias_result["events"][1]["modes"]["expected"]["status"] == "calculated"


def test_grace_source_picker_rejects_actor_without_reviewed_anomaly_template() -> None:
    payload = _payload(
        "move-entry:character:1181:potential1-pulse-grenade",
        potential=1,
        conditions={"condition:grace:pulse-grenade-ready": True},
        source={"source_character_id": "character:1431", "element": "physical"},
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 400
    assert "no reviewed ordinary anomaly source" in response.text


def test_grace_cinema2_resistance_and_potential_electric_bonus_are_scoped() -> None:
    resistance_base = _payload("move-entry:character:1181:special-tap")
    resistance_base["enemy"]["damage_resistance"]["electric"] = 0.20
    base_result = _calculate(resistance_base)
    resistance_active = _payload(
        "move-entry:character:1181:special-tap",
        cinema=2,
        conditions={"condition:grace:target-electrically-breached": True},
        enabled=("rule:character:1181:cinema2:electric-resistance-debuff",),
    )
    resistance_active["enemy"]["damage_resistance"]["electric"] = 0.20
    reduced_result = _calculate(resistance_active)
    base_value = base_result["events"][0]["modes"]["expected"]["value"]
    reduced_event = reduced_result["events"][0]
    assert reduced_event["modes"]["expected"]["value"] > base_value
    resistance_node = next(
        item for item in reduced_event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "resistance.enemy-reduction"
    )
    assert resistance_node["value"] == pytest.approx(0.085)

    potential_base = _payload("move-entry:character:1181:special-tap", potential=2)
    potential_active = _payload(
        "move-entry:character:1181:special-tap",
        potential=2,
        conditions={"condition:grace:electric-energy-empowered": True},
        enabled=("rule:character:1181:potential2:electric-damage-bonus",),
    )
    base_potential_value = _calculate(potential_base)["events"][0]["modes"]["expected"]["value"]
    active_potential_value = _calculate(potential_active)["events"][0]["modes"]["expected"]["value"]
    assert active_potential_value == pytest.approx(base_potential_value * 1.10)


def test_grace_cycle_only_adds_pulse_and_discharge_when_pulse_grenade_is_ready() -> None:
    base = _payload(
        "move-entry:character:1181:potential1-cycle-single-throw",
        potential=1,
        conditions={"condition:grace:pulse-state-active": True},
    )
    without_pulse = _calculate(base)
    assert len(without_pulse["events"]) == 1
    assert "cycle-single-throw" in without_pulse["events"][0]["semantic_id"]
    assert without_pulse["events"][0]["modes"]["expected"]["value"] == pytest.approx(158.32738780582207)

    ready = _payload(
        "move-entry:character:1181:potential1-cycle-single-throw",
        potential=1,
        conditions={
            "condition:grace:pulse-state-active": True,
            "condition:grace:pulse-grenade-ready": True,
        },
        enabled=(
            "rule:character:1181:potential1:cycle-pulse-grenade",
            "rule:character:1181:potential1:pulse-discharge",
        ),
        source={"source_character_id": str(GRACE_ID), "element": "electric"},
    )
    with_pulse = _calculate(ready)
    assert len(with_pulse["events"]) == 3
    assert sum(event["damage_type"] == "direct" for event in with_pulse["events"]) == 2
    assert sum(event["damage_subtype"] == "discharge" for event in with_pulse["events"]) == 1
    values = [event["modes"]["expected"]["value"] for event in with_pulse["events"]]
    assert sorted(values) == pytest.approx(sorted((158.32738780582207, 345.6751454435706, 3225.4671849254996)))

    c6_cycle = _calculate(_payload(
        "move-entry:character:1181:potential1-cycle-single-throw",
        potential=1,
        cinema=6,
        conditions={
            "condition:grace:pulse-state-active": True,
            "condition:grace:pulse-grenade-ready": True,
            "condition:grace:cinema6-energy-consumed": True,
        },
        enabled=(
            "rule:character:1181:potential1:cycle-pulse-grenade",
            "rule:character:1181:potential1:pulse-discharge",
            "rule:character:1181:cinema6:grenade-double-and-extra",
        ),
        source={"source_character_id": str(GRACE_ID), "element": "electric"},
    ))
    assert len(c6_cycle["events"]) == 4
    assert sum(event["damage_type"] == "direct" for event in c6_cycle["events"]) == 3
    assert sum(event["damage_subtype"] == "discharge" for event in c6_cycle["events"]) == 1


def test_grace_extra_ability_captures_anomaly_bonus_for_shock_and_discharge_only() -> None:
    rule_id = "rule:character:1181:extra-ability:shock-record-anomaly-bonus"
    stack = {rule_id: 2}
    enabled = (rule_id,)
    team = ("character:1011",)

    shock_base = _calculate(_payload("move-entry:character:1181:electric-shock", supporting=team))
    shock_zero = _calculate(_payload(
        "move-entry:character:1181:electric-shock",
        supporting=team,
        enabled=enabled,
        stacks={rule_id: 0},
    ))
    shock_buffed = _calculate(_payload(
        "move-entry:character:1181:electric-shock",
        supporting=team,
        enabled=enabled,
        stacks=stack,
    ))
    assert shock_buffed["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        shock_base["events"][0]["modes"]["expected"]["value"] * 1.36
    )
    assert shock_buffed["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]["final_strength"] == pytest.approx(
        shock_base["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]["final_strength"]
    )
    assert shock_zero["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        shock_base["events"][0]["modes"]["expected"]["value"]
    )

    disorder_base = _calculate(_payload("move-entry:character:1181:electric-disorder", supporting=team))
    disorder_buffed = _calculate(_payload(
        "move-entry:character:1181:electric-disorder",
        supporting=team,
        enabled=enabled,
        stacks=stack,
    ))
    assert disorder_buffed["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        disorder_base["events"][0]["modes"]["expected"]["value"]
    )

    direct_base = _calculate(_payload("move-entry:character:1181:special-tap", supporting=team))
    direct_buffed = _calculate(_payload(
        "move-entry:character:1181:special-tap",
        supporting=team,
        enabled=enabled,
        stacks=stack,
    ))
    assert direct_buffed["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        direct_base["events"][0]["modes"]["expected"]["value"]
    )

    discharge_base = _calculate(_payload(
        "move-entry:character:1181:potential1-pulse-grenade",
        potential=1,
        conditions={"condition:grace:pulse-grenade-ready": True},
        enabled=("rule:character:1181:potential1:pulse-discharge",),
        source={"source_character_id": "character:1011", "element": "electric"},
        supporting=team,
    ))
    discharge_buffed = _calculate(_payload(
        "move-entry:character:1181:potential1-pulse-grenade",
        potential=1,
        conditions={"condition:grace:pulse-grenade-ready": True},
        enabled=("rule:character:1181:potential1:pulse-discharge", rule_id),
        source={"source_character_id": "character:1011", "element": "electric"},
        supporting=team,
        stacks=stack,
    ))
    assert discharge_buffed["events"][1]["modes"]["expected"]["value"] == pytest.approx(
        discharge_base["events"][1]["modes"]["expected"]["value"] * 1.36
    )


def test_grace_cinema6_extra_grenade_is_one_separate_hit_and_doubles_each_grenade() -> None:
    result = _calculate(_payload(
        "move-entry:character:1181:special-tap",
        cinema=6,
        conditions={"condition:grace:cinema6-energy-consumed": True},
        enabled=("rule:character:1181:cinema6:grenade-double-and-extra",),
    ))
    events = result["events"]
    assert len(events) == 2
    assert events[0]["damage_type"] == events[1]["damage_type"] == "direct"
    parent = events[0]["modes"]["expected"]["value"]
    child = events[1]["modes"]["expected"]["value"]
    assert child == pytest.approx(parent)


def test_grace_cinema6_only_changes_main_potential1_cycle_grenade() -> None:
    base = _calculate(_payload(
        "move-entry:character:1181:potential1-vortex-grenade",
        potential=1,
        cinema=6,
        conditions={
            "condition:grace:potential1-vortex-active": True,
            "condition:grace:cinema6-energy-consumed": True,
        },
    ))
    result = _calculate(_payload(
        "move-entry:character:1181:potential1-vortex-grenade",
        potential=1,
        cinema=6,
        conditions={
            "condition:grace:potential1-vortex-active": True,
            "condition:grace:cinema6-energy-consumed": True,
        },
        enabled=("rule:character:1181:cinema6:grenade-double-and-extra",),
    ))
    assert len(result["events"]) == 1
    assert result["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        base["events"][0]["modes"]["expected"]["value"]
    )
    assert result["totals"]["expected"]["complete"] is True
    assert result["diagnostics"] == []


def test_grace_source_choice_does_not_override_other_dynamic_or_fixed_discharge_templates() -> None:
    grace_choice = AnomalySourceChoice(
        source_character_id=GRACE_ID,
        element=Element.ELECTRIC,
    )
    burnice_raw = load_character_record("character:1171")
    burnice = compile_burnice(
        BurniceCompileConfig(core_level=7, cinema_level=0, potential_level=1),
        load_burnice_raw_record(burnice_raw, potential_level=1),
    )
    burnice_template = next(
        item for item in burnice.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
        and item.source_multiplier_by_element
    )
    fixed_multiplier = FixedMultiplier(Resolved(0.28))
    burnice_event = instantiate_damage_event(
        burnice_template,
        fixed_multiplier,
        battle_state_id=BattleStateId("battle:grace-source-scope"),
        target_enemy=EnemyId("enemy:scope"),
        created_at=0.0,
        source_history_record_id=AnomalyRecordId("anomaly:character:1171:fire-burn"),
        grace_anomaly_source_choice=grace_choice,
    ).event
    assert burnice_event.metadata.element is Element.FIRE
    assert burnice_event.history_record_source == AnomalyRecordId("anomaly:character:1171:fire-burn")
    assert burnice_event.multiplier == fixed_multiplier

    velina_raw = load_character_record("character:1561")
    velina = compile_velina(
        VelinaCompileConfig(core_level=7, cinema_level=0),
        load_velina_raw_record(velina_raw),
    )
    velina_template = next(
        item for item in velina.damage_event_templates
        if isinstance(item, DischargeDamageEventTemplate)
        and not item.source_multiplier_by_element
    )
    velina_event = instantiate_damage_event(
        velina_template,
        fixed_multiplier,
        battle_state_id=BattleStateId("battle:grace-source-scope"),
        target_enemy=EnemyId("enemy:scope"),
        created_at=0.0,
        grace_anomaly_source_choice=grace_choice,
    ).event
    assert velina_event.metadata.element is velina_template.element
    assert velina_event.history_record_source == velina_template.history_record_source
    assert velina_event.multiplier == fixed_multiplier
