from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.lighter import (
    LIGHTER_ID,
    LighterCompileConfig,
    compile_lighter,
    load_raw_record,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog, supported_wengine_catalog
from core.presentation.registry import (
    _lighter_additional_ability_eligibility,
    registration_for,
)
from core.types import CharacterId, DamageTag, Element, SkillGroup
from web.api import app


client = TestClient(app)

LIGHTER = str(LIGHTER_ID)
SOLDIER11 = "character:1041"
YANG_RULE = "rule:character:1161:extra-ability:yang-stacks"
IMPACT_RULE = "rule:character:1161:core:morale-impact-stacks"
CORE_RES_RULE = "rule:character:1161:core:fire-ice-resistance-reduction"
C1_RES_RULE = "rule:character:1161:cinema1:core-resistance-reduction"
C2_STUN_RULE = "rule:character:1161:cinema2:blight-stun-vulnerability"
C6_NORMAL_RULE = "rule:character:1161:cinema6:fire-impact-on-current-move"
C6_EXTRA_RULE = "rule:character:1161:cinema6:morale-finisher-extra-fire-impact"
MORALE_ACTIVE = "condition:lighter:morale-brawl-active"
MORALE_IMPACT_ACTIVE = "condition:lighter:morale-impact-buff-active"
CORE_RES_ACTIVE = "condition:lighter:core-fire-ice-resistance-debuff-active"
BLIGHT_ACTIVE = "condition:lighter:blight-active"
YANG_ACTIVE = "condition:lighter:yang-active"
MORALE_FINISHER_ACTIVE = "condition:lighter:morale-exhausted-finisher-active"


def _stats_for(character_id: str) -> dict:
    panel = character_base_stats(CharacterId(character_id))
    return {
        "hp": panel.hp.value,
        "attack": panel.attack.value,
        "defense": panel.defense.value,
        "impact": panel.impact.value,
        "crit_rate": panel.crit_rate.value,
        "crit_damage": panel.crit_damage.value,
        "anomaly_mastery": panel.anomaly_mastery.value,
        "anomaly_proficiency": panel.anomaly_proficiency.value,
        "energy_regen": panel.energy_regen.value,
        "penetration_rate": panel.penetration_rate.value,
        "penetration_flat": panel.penetration_flat.value,
        "element_damage_bonus": {
            str(element.value): value.value
            for element, value in panel.element_damage_bonus.items()
        },
    }


def _payload(
    move_entry_id: str,
    *,
    team: tuple[str, ...] = (LIGHTER,),
    primary: str = LIGHTER,
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: list[str] | None = None,
    stacks: dict[str, int] | None = None,
    impact: float | None = None,
    wengine_id: str | None = None,
    refinement: int = 1,
    stunned: bool = False,
    enemy_stun_vulnerability_bonus: float = 0.0,
) -> dict:
    builds = {}
    for character_id in team:
        stats = _stats_for(character_id)
        if character_id == LIGHTER and impact is not None:
            stats["impact"] = impact
        builds[character_id] = {
            "level": 60,
            "build_mode": "equipment-build",
            "base_stats": stats,
            "wengine_id": wengine_id if character_id == LIGHTER else None,
            "wengine_level": 60,
            "wengine_refinement": refinement,
            "drive_discs": [],
        }
    return {
        "primary_character_id": primary,
        "supporting_character_ids": [item for item in team if item != primary],
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": {
            item: {
                "core_level": 7,
                "cinema_level": cinema if item == LIGHTER else 0,
            }
            for item in team
        },
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": enabled or [],
        "selected_trigger_inputs": [],
        "rule_stack_counts": stacks or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:lighter-test",
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
            "stun_vulnerability_bonus": enemy_stun_vulnerability_bonus,
            "is_stunned": stunned,
        },
    }


def _result(*args, **kwargs) -> dict:
    response = client.post("/api/v1/moves/calculate", json=_payload(*args, **kwargs))
    assert response.status_code == 200, response.text
    return response.json()


def _ratio(entry) -> float:
    return entry.multiplier_variants[0].multiplier.value.value


def _expected(result: dict) -> float:
    value = result["totals"]["expected"]["value"]
    assert value is not None
    return value


def test_lighter_live_identity_panel_engine_and_source_defaults_are_registered() -> None:
    source = load_character_record(LIGHTER)
    raw = load_raw_record(source)
    assert LIGHTER in supported_character_ids()
    assert raw.name == "莱特"
    assert raw.code_name == "Lighter"
    assert raw.icon == "IconRole26"
    assert raw.rarity == 4
    assert raw.specialty == "击破"
    assert raw.element == "火属性"
    assert raw.faction == "卡吕冬之子"
    assert raw.potential_details == ()
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1161.json",
    )

    panel = character_base_stats(LIGHTER_ID)
    assert panel.hp.value == pytest.approx(8253.2915)
    assert panel.attack.value == pytest.approx(797.9569)
    assert panel.defense.value == pytest.approx(612.6038)
    assert panel.impact.value == pytest.approx(137.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_mastery.value == pytest.approx(91.0)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    assert panel.energy_regen.value == pytest.approx(1.2)

    assert SIGNATURE_WENGINE_BY_CHARACTER[LIGHTER_ID] == "wengine:14116"
    engine = load_wengine_raw_record("wengine:14116")
    assert engine.name == "焰心桂冠"
    assert engine.icon == "Weapon_S_1161"
    assert engine.base_attack == pytest.approx(713.0)
    assert engine.advanced_stat_value == pytest.approx(0.18)
    catalog = {item.character_id: item for item in supported_character_catalog()}
    assert catalog[LIGHTER].code_name == "Lighter"
    assert catalog[LIGHTER].image_path == "/characters/portrait-placeholder.svg"
    engine_catalog = {item.wengine_id: item for item in supported_wengine_catalog()}
    assert engine_catalog["wengine:14116"].signature_character_id == LIGHTER
    assert registration_for(LIGHTER_ID).role.value == "stun"
    assert LighterCompileConfig().core_level == 7
    assert LighterCompileConfig().cinema_level == 0
    assert LighterCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12


def test_lighter_raw_curves_keep_action_elements_skill_levels_and_tags_exact() -> None:
    raw = load_raw_record(load_character_record(LIGHTER))
    base = compile_lighter(LighterCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in base.move_entries}
    assert _ratio(entries["move-entry:character:1161:basic-1"]) == pytest.approx(0.788)
    assert _ratio(entries["move-entry:character:1161:basic-continuous-combo-1"]) == pytest.approx(1.738)
    assert _ratio(entries["move-entry:character:1161:basic-4"]) == pytest.approx(1.581)
    assert _ratio(entries["move-entry:character:1161:basic-5-jab-start"]) == pytest.approx(3.275)
    assert _ratio(entries["move-entry:character:1161:basic-5-jab-combo"]) == pytest.approx(2.461)
    assert _ratio(entries["move-entry:character:1161:basic-5-morale-strong-finisher"]) == pytest.approx(8.71)
    assert _ratio(entries["move-entry:character:1161:dash-attack"]) == pytest.approx(1.801)
    assert _ratio(entries["move-entry:character:1161:dodge-counter"]) == pytest.approx(3.733)
    assert _ratio(entries["move-entry:character:1161:special-uppercut"]) == pytest.approx(0.726)
    assert _ratio(entries["move-entry:character:1161:ex-special-main"]) == pytest.approx(9.736)
    assert _ratio(entries["move-entry:character:1161:ex-special-followup"]) == pytest.approx(5.864)
    assert _ratio(entries["move-entry:character:1161:chain-attack"]) == pytest.approx(14.249)
    assert _ratio(entries["move-entry:character:1161:ultimate"]) == pytest.approx(30.161)
    assert _ratio(entries["move-entry:character:1161:quick-assist"]) == pytest.approx(1.401)
    assert _ratio(entries["move-entry:character:1161:assist-strike"]) == pytest.approx(4.398)
    assert len(base.move_entries) == 29
    assert entries["move-entry:character:1161:basic-1"].main_damage_event.element is Element.PHYSICAL
    assert entries["move-entry:character:1161:basic-4"].main_damage_event.element is Element.FIRE

    ex = entries["move-entry:character:1161:ex-special-main"].main_damage_event
    assert ex.damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})
    assert DamageTag.SPECIAL_ATTACK not in ex.damage_tags

    at_level_16 = compile_lighter(
        LighterCompileConfig(
            skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
            cinema_level=5,
        ),
        raw,
    )
    ultimate = next(
        item
        for item in at_level_16.move_entries
        if str(item.entry_id) == "move-entry:character:1161:ultimate"
    )
    assert _ratio(ultimate) == pytest.approx(35.645)

    at_level_14 = compile_lighter(
        LighterCompileConfig(
            skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
            cinema_level=3,
        ),
        raw,
    )
    ultimate_14 = next(
        item
        for item in at_level_14.move_entries
        if str(item.entry_id) == "move-entry:character:1161:ultimate"
    )
    assert _ratio(ultimate_14) == pytest.approx(32.903)

    no_dash_c6 = compile_lighter(LighterCompileConfig(cinema_level=6), raw)
    c6_entries = {str(item.entry_id): item for item in no_dash_c6.move_entries}
    dash = c6_entries["move-entry:character:1161:dash-attack"]
    assert dash.derived_damage_events == ()
    basic = c6_entries["move-entry:character:1161:basic-1"]
    assert len(basic.derived_damage_events) == 1
    child = next(
        item
        for item in no_dash_c6.damage_event_templates
        if item.ref.template_id == basic.derived_damage_events[0].template.template_id
    )
    assert child.ref.skill_group == basic.main_damage_event.skill_group
    assert child.ref.damage_tags == basic.main_damage_event.damage_tags
    assert child.ref.element is Element.FIRE
    assert child.move_id is None
    parent_template = next(
        item
        for item in no_dash_c6.damage_event_templates
        if item.ref.template_id == basic.main_damage_event.template_id
    )
    assert child.crit_rule == parent_template.crit_rule
    assert child.base_source == parent_template.base_source
    for key in (
        "basic-2",
        "dodge-counter",
        "special-uppercut",
        "ex-special-main",
        "quick-assist",
        "assist-strike",
        "chain-attack",
        "ultimate",
    ):
        assert len(c6_entries[f"move-entry:character:1161:{key}"].derived_damage_events) == 1
    strong_finisher = c6_entries["move-entry:character:1161:basic-5-morale-strong-finisher"]
    assert len(strong_finisher.derived_damage_events) == 2
    assert not any("heavy-hit" in str(item.condition_id) for item in no_dash_c6.scenario_conditions)


def test_lighter_additional_ability_eligibility_uses_attack_role_or_own_faction() -> None:
    assert _lighter_additional_ability_eligibility((LIGHTER_ID, CharacterId(SOLDIER11)))
    assert _lighter_additional_ability_eligibility((LIGHTER_ID, CharacterId("character:1081")))
    assert not _lighter_additional_ability_eligibility((LIGHTER_ID,))


def test_lighter_yang_uses_continuous_impact_scaling_and_cinema2_applies_120_percent_once(
) -> None:
    entry_id = "move-entry:character:1161:basic-4"
    team = (LIGHTER, SOLDIER11)
    base = _payload(
        entry_id,
        team=team,
        cinema=0,
        conditions={YANG_ACTIVE: True},
        enabled=[YANG_RULE],
        stacks={YANG_RULE: 20},
        wengine_id="wengine:14116",
    )
    unbuffed = _payload(
        entry_id,
        team=team,
        cinema=0,
        conditions={YANG_ACTIVE: False},
        enabled=[],
        wengine_id="wengine:14116",
    )
    unbuffed_result = client.post("/api/v1/moves/calculate", json=unbuffed)
    assert unbuffed_result.status_code == 200, unbuffed_result.text
    base_value = _expected(unbuffed_result.json())

    base_result = client.post("/api/v1/moves/calculate", json=base)
    assert base_result.status_code == 200, base_result.text
    assert _expected(base_result.json()) / base_value == pytest.approx(1.25)

    c2 = _payload(
        entry_id,
        team=team,
        cinema=2,
        conditions={YANG_ACTIVE: True},
        enabled=[YANG_RULE],
        stacks={YANG_RULE: 20},
        wengine_id="wengine:14116",
    )
    c2_result = client.post("/api/v1/moves/calculate", json=c2)
    assert c2_result.status_code == 200, c2_result.text
    assert _expected(c2_result.json()) / base_value == pytest.approx(1.30)

    physical_base = _payload(
        "move-entry:character:1161:basic-1",
        team=team,
        cinema=0,
        conditions={YANG_ACTIVE: False},
        enabled=[],
        wengine_id="wengine:14116",
    )
    physical_with_yang = _payload(
        "move-entry:character:1161:basic-1",
        team=team,
        cinema=0,
        conditions={YANG_ACTIVE: True},
        enabled=[YANG_RULE],
        stacks={YANG_RULE: 20},
        wengine_id="wengine:14116",
    )
    physical_off = client.post("/api/v1/moves/calculate", json=physical_base)
    physical_on = client.post("/api/v1/moves/calculate", json=physical_with_yang)
    assert physical_off.status_code == physical_on.status_code == 200
    assert _expected(physical_on.json()) / _expected(physical_off.json()) == pytest.approx(1.0)

    for move_id in (
        "move-entry:character:1161:fire-anomaly",
        "move-entry:character:1161:fire-disorder",
    ):
        source_off = _payload(
            move_id,
            team=team,
            cinema=0,
            conditions={YANG_ACTIVE: False},
            enabled=[],
        )
        source_on = _payload(
            move_id,
            team=team,
            cinema=0,
            conditions={YANG_ACTIVE: True},
            enabled=[YANG_RULE],
            stacks={YANG_RULE: 20},
        )
        source_off["parameter_values"]["parameter:lighter:fire-disorder-remaining-seconds"] = 10
        source_on["parameter_values"]["parameter:lighter:fire-disorder-remaining-seconds"] = 10
        result_off = client.post("/api/v1/moves/calculate", json=source_off)
        result_on = client.post("/api/v1/moves/calculate", json=source_on)
        assert result_off.status_code == result_on.status_code == 200
        assert _expected(result_on.json()) / _expected(result_off.json()) == pytest.approx(1.25)

    impact_conditions = {
        YANG_ACTIVE: True,
        MORALE_IMPACT_ACTIVE: True,
    }
    impact_enabled = [YANG_RULE, IMPACT_RULE]
    impact_stacks = {YANG_RULE: 20, IMPACT_RULE: 10}
    c0_with_impact = _payload(
        entry_id,
        team=team,
        cinema=0,
        conditions=impact_conditions,
        enabled=impact_enabled,
        stacks=impact_stacks,
        wengine_id="wengine:14116",
    )
    c0_impact_result = client.post("/api/v1/moves/calculate", json=c0_with_impact)
    assert c0_impact_result.status_code == 200, c0_impact_result.text
    assert _expected(c0_impact_result.json()) / base_value == pytest.approx(1.36996)

    c2_with_impact = _payload(
        entry_id,
        team=team,
        cinema=2,
        conditions=impact_conditions,
        enabled=impact_enabled,
        stacks=impact_stacks,
        wengine_id="wengine:14116",
    )
    c2_impact_result = client.post("/api/v1/moves/calculate", json=c2_with_impact)
    assert c2_impact_result.status_code == 200, c2_impact_result.text
    assert _expected(c2_impact_result.json()) / base_value == pytest.approx(1.443952)

    snapshot = next(
        item for item in c2_impact_result.json()["resolved_character_snapshots"]
        if item["character_id"] == LIGHTER
    )
    assert snapshot["stats"]["impact"] == pytest.approx(193.992)

    capped_base = _payload(
        entry_id,
        team=team,
        cinema=0,
        conditions=impact_conditions,
        enabled=impact_enabled,
        stacks=impact_stacks,
        impact=200.0,
        wengine_id="wengine:14116",
    )
    capped_base_result = client.post("/api/v1/moves/calculate", json=capped_base)
    assert capped_base_result.status_code == 200, capped_base_result.text
    assert _expected(capped_base_result.json()) / base_value == pytest.approx(1.75)

    capped_c2 = _payload(
        entry_id,
        team=team,
        cinema=2,
        conditions=impact_conditions,
        enabled=impact_enabled,
        stacks=impact_stacks,
        impact=200.0,
        wengine_id="wengine:14116",
    )
    capped_c2_result = client.post("/api/v1/moves/calculate", json=capped_c2)
    assert capped_c2_result.status_code == 200, capped_c2_result.text
    assert _expected(capped_c2_result.json()) / base_value == pytest.approx(1.90)

    fractional_impact_off = _payload(
        entry_id,
        team=team,
        cinema=0,
        conditions={YANG_ACTIVE: False},
        enabled=[],
        stacks={},
        impact=175.0,
    )
    fractional_impact_on = _payload(
        entry_id,
        team=team,
        cinema=0,
        conditions={YANG_ACTIVE: True},
        enabled=[YANG_RULE],
        stacks={YANG_RULE: 20},
        impact=175.0,
    )
    fractional_off = client.post("/api/v1/moves/calculate", json=fractional_impact_off)
    fractional_on = client.post("/api/v1/moves/calculate", json=fractional_impact_on)
    assert fractional_off.status_code == fractional_on.status_code == 200
    assert _expected(fractional_on.json()) / _expected(fractional_off.json()) == pytest.approx(1.275)


def test_lighter_cinema6_fire_impact_scales_from_current_impact_and_follows_parent_scope() -> None:
    base = _payload(
        "move-entry:character:1161:basic-1",
        cinema=6,
        enabled=[C6_NORMAL_RULE],
        wengine_id="wengine:14116",
    )
    no_core_impact = client.post("/api/v1/moves/calculate", json=base)
    assert no_core_impact.status_code == 200, no_core_impact.text
    assert len(no_core_impact.json()["events"]) == 2
    assert no_core_impact.json()["events"][1]["element"] == "fire"
    assert no_core_impact.json()["events"][1]["common_application_trace"]["event_multiplier_modifiers"][0]["value"] == pytest.approx(1.0)

    with_core_impact = _payload(
        "move-entry:character:1161:basic-1",
        cinema=6,
        conditions={MORALE_IMPACT_ACTIVE: True},
        enabled=[C6_NORMAL_RULE, IMPACT_RULE],
        stacks={IMPACT_RULE: 10},
        wengine_id="wengine:14116",
    )
    scaled = client.post("/api/v1/moves/calculate", json=with_core_impact)
    assert scaled.status_code == 200, scaled.text
    child = scaled.json()["events"][1]
    assert child["common_application_trace"]["event_multiplier_modifiers"][0]["value"] == pytest.approx(1.47984)

    capped = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1161:basic-1",
            cinema=6,
            enabled=[C6_NORMAL_RULE],
            impact=300.0,
            wengine_id="wengine:14116",
        ),
    )
    assert capped.status_code == 200, capped.text
    assert capped.json()["events"][1]["common_application_trace"]["event_multiplier_modifiers"][0]["value"] == pytest.approx(3.0)

    dash = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1161:dash-attack",
            cinema=6,
            enabled=[C6_NORMAL_RULE],
            wengine_id="wengine:14116",
        ),
    )
    assert dash.status_code == 200, dash.text
    assert len(dash.json()["events"]) == 1

    strong_finisher = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1161:basic-5-morale-strong-finisher",
            cinema=6,
            conditions={MORALE_ACTIVE: True, MORALE_FINISHER_ACTIVE: True},
            enabled=[C6_NORMAL_RULE, C6_EXTRA_RULE],
            wengine_id="wengine:14116",
        ),
    )
    assert strong_finisher.status_code == 200, strong_finisher.text
    assert strong_finisher.json()["totals"]["expected"]["complete"] is True
    assert len(strong_finisher.json()["events"]) == 3
    assert sum("火焰冲击" in event["label"] for event in strong_finisher.json()["events"]) == 2


def test_lighter_cinema4_energy_regeneration_targets_only_the_frontline_operator() -> None:
    team = (SOLDIER11, LIGHTER)
    result = _result(
        "move-entry:character:1041:basic-fire-suppression-1",
        team=team,
        primary=SOLDIER11,
        cinema=4,
        enabled=["rule:character:1161:cinema4:frontline-energy-regeneration"],
    )
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots[SOLDIER11]["energy_regen"] == pytest.approx(1.32)
    assert snapshots[LIGHTER]["energy_regen"] == pytest.approx(1.2)


def test_lighter_cinema1_resistance_and_cinema2_bligh_vulnerability_are_target_states() -> None:
    fire = _result(
        "move-entry:character:1161:special-uppercut",
        cinema=1,
        conditions={CORE_RES_ACTIVE: True},
        enabled=[CORE_RES_RULE, C1_RES_RULE],
    )
    fire_breakdown = fire["events"][0]["modes"]["expected"]["calculation_breakdown"]
    assert next(item["value"] for item in fire_breakdown if item["node"] == "resistance.enemy-reduction") == pytest.approx(0.25)

    stunned = _result(
        "move-entry:character:1161:special-uppercut",
        cinema=2,
        conditions={BLIGHT_ACTIVE: True},
        enabled=[C2_STUN_RULE],
        stunned=True,
    )
    stun_breakdown = stunned["events"][0]["modes"]["expected"]["calculation_breakdown"]
    assert next(item["value"] for item in stun_breakdown if item["node"] == "vulnerability.enemy-stun") == pytest.approx(0.25)
