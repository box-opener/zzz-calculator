from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.burnice import (
    BURNICE_ID,
    BurniceCompileConfig,
    compile_burnice,
    load_raw_record,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    load_wengine_raw_record,
)
from core.application.characters.templates import DischargeDamageEventTemplate
from core.application.execution.event_factory import instantiate_damage_event
from core.application.moves import DamageEventTemplateRef
from core.application.ids import DamageEventSemanticId
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.assembler import build_character_editor_view
from core.presentation.calculation_service import _reviewed_anomaly_source_element_options
from core.presentation.registry import compile_registered_definition, registration_for
from core.types import (
    AnomalyRecordId,
    AnomalySourceChoice,
    BattleStateId,
    CharacterId,
    DamageSubtype,
    DamageTag,
    DamageType,
    DischargeDamageEvent,
    Element,
    EnemyId,
    FixedMultiplier,
    NoCritRule,
    Resolved,
    SkillGroup,
    WEngineId,
)
from web.api import app


client = TestClient(app)

_BURN_ACTIVE = "condition:burnice:target-is-burning"
_SCORCHED_ACTIVE = "condition:burnice:target-is-scorched"
_DOUBLE_EX_ACTIVE = "condition:burnice:double-ex-state-active"
_CORE_EMBER_RULE = "rule:character:1171:core:ember-current-proficiency-damage"
_P1_BLENDER_EMBER_RULE = "rule:character:1171:potential1:blender-extra-ember"
_P1_THROW_DISCHARGE_RULE = "rule:character:1171:potential1:special-throw-discharge"
_C6_SPECIAL_RULE = "rule:character:1171:cinema6:special-ember"
_C6_BURN_RULE = "rule:character:1171:cinema6:double-ex-extra-burn-tick"
_C6_RES_RULE = "rule:character:1171:cinema6:fire-resistance-ignore-state"
_CAESAR_SHIELD_ATTACK_RULE = "rule:character:1071:core:shield-holder-attack"
_CAESAR_SHIELD_ATTACK_ACTIVE = "condition:caesar:shield-holder-attack-buff-active"


def _stats_for(character_id: str, *, energy_regen: float | None = None) -> dict:
    panel = character_base_stats(CharacterId(character_id))
    result = {
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
    if energy_regen is not None:
        result["energy_regen"] = energy_regen
    return result


def _payload(
    move_entry_id: str,
    *,
    potential: int = 0,
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    source: dict[str, str] | None = None,
    energy_regen: float | None = None,
    resistance: float = 0.0,
) -> dict:
    team = [str(BURNICE_ID)]
    if source is not None and source["source_character_id"] not in team:
        team.append(source["source_character_id"])
    builds = {}
    for character_id in team:
        stats = _stats_for(
            character_id,
            energy_regen=energy_regen if character_id == str(BURNICE_ID) else None,
        )
        if character_id == str(BURNICE_ID) and energy_regen is not None:
            builds[character_id] = {
                "level": 60,
                "build_mode": "manual-panel",
                "out_of_combat_stats": stats,
            }
        else:
            builds[character_id] = {
                "level": 60,
                "build_mode": "equipment-build",
                "base_stats": stats,
                "drive_discs": [],
            }
    compile_configs = {}
    for character_id in team:
        compile_config = {
            "core_level": 7,
            "cinema_level": cinema if character_id == str(BURNICE_ID) else 0,
        }
        if character_id == str(BURNICE_ID):
            compile_config["potential_level"] = potential
        compile_configs[character_id] = compile_config
    payload = {
        "primary_character_id": str(BURNICE_ID),
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:burnice-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": resistance,
                "fire": resistance,
                "ice": resistance,
                "electric": resistance,
                "ether": resistance,
                "wind": resistance,
                "luminance": resistance,
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
    }
    if source is not None:
        payload["burnice_anomaly_source"] = source
    return payload


def _calculate(payload: dict) -> dict:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _event(result: dict, semantic_suffix: str) -> dict:
    return next(
        item
        for item in result["events"]
        if semantic_suffix in item["semantic_id"]
    )


def _breakdown(event: dict, node: str) -> dict:
    return next(
        item for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == node
    )


def test_burnice_source_identity_registry_and_signature() -> None:
    raw_data = load_character_record(str(BURNICE_ID))
    raw = load_raw_record(raw_data, potential_level=0)
    assert raw.name == "柏妮思"
    assert raw.code_name == "Burnice"
    assert raw.rarity == 4
    assert raw.specialty == "异常"
    assert raw.element == "火属性"
    assert raw.faction == "卡吕冬之子"
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1171.json",
    )
    assert str(BURNICE_ID) in supported_character_ids()

    stats = character_base_stats(BURNICE_ID)
    assert stats.attack.value == pytest.approx(863.4528)
    assert stats.hp.value == pytest.approx(7368.1929)
    assert stats.defense.value == pytest.approx(600.5916)
    assert stats.anomaly_proficiency.value == pytest.approx(120.0)
    assert stats.anomaly_mastery.value == pytest.approx(118.0)
    assert BurniceCompileConfig().core_level == 7
    assert BurniceCompileConfig().cinema_level == 0
    assert BurniceCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(BURNICE_ID)
    assert registration.catalog.rarity == "S"
    assert SIGNATURE_WENGINE_BY_CHARACTER[BURNICE_ID] == WEngineId("wengine:14117")
    assert load_wengine_raw_record("wengine:14117").icon == "Weapon_S_1171"


def test_burnice_reviewed_elements_tags_levels_and_potential_options() -> None:
    raw_data = load_character_record(str(BURNICE_ID))
    p0 = compile_burnice(
        BurniceCompileConfig(core_level=7, cinema_level=0, potential_level=0),
        load_raw_record(raw_data, potential_level=0),
    )
    p1 = compile_burnice(
        BurniceCompileConfig(core_level=7, cinema_level=0, potential_level=1),
        load_raw_record(raw_data, potential_level=1),
    )
    by_key = {str(entry.entry_id): entry for entry in p0.move_entries}
    assert by_key["move-entry:character:1171:basic-stage-1"].main_damage_event.element is Element.PHYSICAL
    assert by_key["move-entry:character:1171:basic-stage-2"].main_damage_event.element is Element.PHYSICAL
    for stage in (3, 4, 5):
        assert by_key[f"move-entry:character:1171:basic-stage-{stage}"].main_damage_event.element is Element.FIRE
    assert by_key["move-entry:character:1171:dodge-counter"].main_damage_event.element is Element.FIRE
    assert by_key["move-entry:character:1171:quick-assist"].main_damage_event.element is Element.FIRE
    assert by_key["move-entry:character:1171:quick-assist"].damage_tags == frozenset({DamageTag.ASSIST})
    assert not any("special-throw" in str(item.entry_id) for item in p0.move_entries)
    throw = next(item for item in p1.move_entries if str(item.entry_id).endswith(":special-throw"))
    assert throw.main_damage_event.element is Element.FIRE
    assert throw.skill_group is SkillGroup.SPECIAL_ATTACK
    assert throw.damage_tags == frozenset({DamageTag.EX_SPECIAL_ATTACK})
    blender = next(item for item in p1.move_entries if str(item.entry_id).endswith(":blender-finisher"))
    assert blender.damage_tags == frozenset({DamageTag.BASIC_ATTACK, DamageTag.ASSIST})
    assert any(str(item.template.template_id).endswith("potential1:blender-finisher-ember") for item in blender.derived_damage_events)

    c0 = _calculate(_payload("move-entry:character:1171:ultimate", potential=0, cinema=0))
    c3 = _calculate(_payload("move-entry:character:1171:ultimate", potential=0, cinema=3))
    c5 = _calculate(_payload("move-entry:character:1171:ultimate", potential=0, cinema=5))
    assert _breakdown(_event(c0, "ultimate:main"), "damage.skill-multiplier")["value"] == pytest.approx(40.252)
    assert _breakdown(_event(c3, "ultimate:main"), "damage.skill-multiplier")["value"] == pytest.approx(43.912)
    assert _breakdown(_event(c5, "ultimate:main"), "damage.skill-multiplier")["value"] == pytest.approx(47.572)


def test_burnice_full_blender_and_ex_entries_sum_each_known_curve_once() -> None:
    raw_data = load_character_record(str(BURNICE_ID))
    p0 = compile_burnice(
        BurniceCompileConfig(core_level=7, cinema_level=0, potential_level=0),
        load_raw_record(raw_data, potential_level=0),
    )
    full_ratios = {
        str(entry.entry_id): entry.multiplier_variants[0].multiplier.value.value
        for entry in p0.move_entries
        if str(entry.entry_id)
        in {
            "move-entry:character:1171:blender-full",
            "move-entry:character:1171:ex-single-full",
            "move-entry:character:1171:ex-double-full",
        }
    }
    assert full_ratios["move-entry:character:1171:blender-full"] == pytest.approx(7.168)
    assert full_ratios["move-entry:character:1171:ex-single-full"] == pytest.approx(12.818)
    assert full_ratios["move-entry:character:1171:ex-double-full"] == pytest.approx(24.904)

    p1 = compile_burnice(
        BurniceCompileConfig(core_level=7, cinema_level=0, potential_level=1),
        load_raw_record(raw_data, potential_level=1),
    )
    full_blender = next(
        item for item in p1.move_entries
        if str(item.entry_id) == "move-entry:character:1171:blender-full"
    )
    assert len(full_blender.derived_damage_events) == 1


def test_burnice_core_ember_cinema1_and_current_ap_bonus() -> None:
    entry = "move-entry:character:1171:core-ember"
    base = _calculate(
        _payload(
            entry,
            conditions={_SCORCHED_ACTIVE: True},
            enabled=(_CORE_EMBER_RULE,),
        )
    )
    c1 = _calculate(
        _payload(
            entry,
            cinema=1,
            conditions={_SCORCHED_ACTIVE: True},
            enabled=(_CORE_EMBER_RULE,),
        )
    )
    base_event = _event(base, "core-ember")
    c1_event = _event(c1, "core-ember")
    assert _breakdown(base_event, "damage.skill-multiplier")["value"] == pytest.approx(3.5)
    assert _breakdown(base_event, "damage.normal-bonus")["value"] == pytest.approx(0.12)
    assert _breakdown(c1_event, "damage.skill-multiplier")["value"] == pytest.approx(4.5)
    assert base["totals"]["expected"]["complete"] is True
    assert c1["totals"]["expected"]["complete"] is True


def test_burnice_cinema6_special_ember_inherits_resistance_state_and_is_a_single_hit() -> None:
    double_spray = _calculate(
        _payload(
            "move-entry:character:1171:ex-double-spray",
            cinema=6,
            conditions={_DOUBLE_EX_ACTIVE: True},
            enabled=(_C6_SPECIAL_RULE, _C6_RES_RULE),
            resistance=0.25,
        )
    )
    assert len(double_spray["events"]) == 2
    special = _event(double_spray, "cinema6:special-ember-child")
    assert special["damage_type"] == "direct"
    assert special["repeat_count"] == 1
    assert special["damage_subtype"] is None
    assert special["element"] == "fire"
    assert _breakdown(special, "resistance.damage-ignore")["value"] == pytest.approx(0.25)


def test_burnice_cinema6_burn_extra_is_one_no_crit_tick_only_on_burning_impact() -> None:
    result = _calculate(
        _payload(
            "move-entry:character:1171:ex-double-impact",
            cinema=6,
            conditions={_DOUBLE_EX_ACTIVE: True, _BURN_ACTIVE: True},
            enabled=(_C6_SPECIAL_RULE, _C6_BURN_RULE, _C6_RES_RULE),
            resistance=0.25,
        )
    )
    assert len(result["events"]) == 3
    burn = _event(result, "cinema6:extra-burn-tick-child")
    assert burn["damage_type"] == "anomaly"
    assert burn["damage_subtype"] == "attribute-anomaly"
    assert burn["repeat_count"] == 1
    assert _breakdown(burn, "anomaly.attribute.multiplier")["value"] == pytest.approx(9.0)
    assert _breakdown(burn, "resistance.damage-ignore")["value"] == pytest.approx(0.25)
    assert result["totals"]["expected"]["complete"] is True

    no_burn = _calculate(
        _payload(
            "move-entry:character:1171:ex-double-impact",
            cinema=6,
            conditions={_DOUBLE_EX_ACTIVE: True, _BURN_ACTIVE: False},
            enabled=(_C6_SPECIAL_RULE, _C6_BURN_RULE, _C6_RES_RULE),
        )
    )
    assert len(no_burn["events"]) == 2
    assert not any(event["semantic_id"].endswith("extra-burn-tick-child") for event in no_burn["events"])

    full = _calculate(
        _payload(
            "move-entry:character:1171:ex-double-full",
            cinema=6,
            conditions={_DOUBLE_EX_ACTIVE: True, _BURN_ACTIVE: True},
            enabled=(_C6_SPECIAL_RULE, _C6_BURN_RULE, _C6_RES_RULE),
            resistance=0.25,
        )
    )
    assert len(full["events"]) == 3
    assert _breakdown(_event(full, "ex-double-full:main"), "damage.skill-multiplier")["value"] == pytest.approx(29.432)
    assert _breakdown(_event(full, "cinema6:special-ember-full-child"), "resistance.damage-ignore")["value"] == pytest.approx(0.25)
    assert _breakdown(_event(full, "cinema6:extra-burn-tick-full-child"), "resistance.damage-ignore")["value"] == pytest.approx(0.25)


def test_burnice_potential_er_uses_initial_panel_continuous_excess() -> None:
    result = _calculate(
        _payload(
            "move-entry:character:1171:basic-stage-1",
            potential=3,
            energy_regen=1.85,
            enabled=("rule:character:1171:potential3:initial-er-bonuses",),
        )
    )
    snapshot = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == str(BURNICE_ID)
    )
    assert snapshot["stats"]["anomaly_mastery"] == pytest.approx(118.65)


def test_burnice_p1_discharge_reads_one_selected_source_record_without_switching_operator() -> None:
    result = _calculate(
        _payload(
            "move-entry:character:1171:special-throw",
            potential=1,
            source={"source_character_id": "character:1371", "element": "ether:xuanmo"},
            enabled=(_P1_THROW_DISCHARGE_RULE,),
        )
    )
    assert len(result["events"]) == 2
    discharge = _event(result, "potential1:special-throw-discharge")
    assert discharge["damage_subtype"] == "discharge"
    assert discharge["element"] == "ether:xuanmo"
    assert discharge["repeat_count"] == 1
    assert (
        discharge["modes"]["expected"]["anomaly_effect_strength_trace"]["character_id"]
        == "character:1371"
    )
    assert result["totals"]["expected"]["complete"] is True
    snapshots = {item["character_id"] for item in result["resolved_character_snapshots"]}
    assert snapshots == {"character:1171", "character:1371"}


def test_burnice_source_generation_keeps_current_operator_panel_recipient() -> None:
    payload = _payload(
        "move-entry:character:1171:special-throw",
        potential=1,
        source={"source_character_id": "character:1371", "element": "ether:xuanmo"},
        enabled=(_P1_THROW_DISCHARGE_RULE, _CAESAR_SHIELD_ATTACK_RULE),
        conditions={_CAESAR_SHIELD_ATTACK_ACTIVE: True},
    )
    payload["supporting_character_ids"].append("character:1071")
    payload["team_character_ids"].append("character:1071")
    payload["compile_configs"]["character:1071"] = {
        "core_level": 7,
        "cinema_level": 0,
    }
    payload["character_builds"]["character:1071"] = {
        "level": 60,
        "build_mode": "equipment-build",
        "base_stats": _stats_for("character:1071"),
        "drive_discs": [],
    }

    result = _calculate(payload)
    snapshots = {
        item["character_id"]: item["stats"]
        for item in result["resolved_character_snapshots"]
    }
    assert snapshots["character:1171"]["attack"] == pytest.approx(
        _stats_for("character:1171")["attack"] + 1000.0
    )
    assert snapshots["character:1371"]["attack"] == pytest.approx(
        _stats_for("character:1371")["attack"]
    )
    discharge = _event(result, "potential1:special-throw-discharge")
    assert discharge["modes"]["expected"]["anomaly_effect_strength_trace"]["character_id"] == "character:1371"


def test_burnice_source_picker_rejects_unreviewed_elements_and_inactive_actors() -> None:
    unsupported_element = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1171:special-throw",
            potential=1,
            source={"source_character_id": "character:1371", "element": "physical"},
            enabled=(_P1_THROW_DISCHARGE_RULE,),
        ),
    )
    assert unsupported_element.status_code == 400
    assert "not available" in unsupported_element.json()["diagnostics"][0]["message"]

    inactive_payload = _payload(
        "move-entry:character:1171:special-throw",
        potential=1,
        enabled=(_P1_THROW_DISCHARGE_RULE,),
    )
    inactive_payload["burnice_anomaly_source"] = {
        "source_character_id": "character:1431",
        "element": "physical",
    }
    inactive_actor = client.post(
        "/api/v1/moves/calculate",
        json=inactive_payload,
    )
    assert inactive_actor.status_code == 400
    assert "active teammate" in inactive_actor.json()["diagnostics"][0]["message"]

    unreviewed_actor = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1171:special-throw",
            potential=1,
            source={"source_character_id": "character:1431", "element": "physical"},
            enabled=(_P1_THROW_DISCHARGE_RULE,),
        ) | {
            "supporting_character_ids": ["character:1431"],
            "team_character_ids": ["character:1171", "character:1431"],
            "formation_character_ids": ["character:1171", "character:1431"],
            "compile_configs": {
                "character:1171": {"core_level": 7, "cinema_level": 0, "potential_level": 1},
                "character:1431": {"core_level": 7, "cinema_level": 0},
            },
            "character_builds": {
                "character:1171": {"level": 60, "build_mode": "equipment-build", "base_stats": _stats_for("character:1171"), "drive_discs": []},
                "character:1431": {"level": 60, "build_mode": "equipment-build", "base_stats": _stats_for("character:1431"), "drive_discs": []},
            },
        },
    )
    assert unreviewed_actor.status_code == 400
    assert "no reviewed ordinary anomaly source" in unreviewed_actor.json()["diagnostics"][0]["message"]


def test_burnice_source_choice_does_not_override_other_discharge_templates() -> None:
    ref = DamageEventTemplateRef(
        template_id="template:character:1561:discharge-compat-test",
        semantic_id=DamageEventSemanticId("event:character:1561:discharge-compat-test"),
        label="Existing static Discharge",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        element=Element.WIND,
    )
    template = DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=CharacterId("character:1561"),
        element=Element.WIND,
        discharge_triggerer=CharacterId("character:1561"),
        history_record_source=AnomalyRecordId("anomaly:original"),
        crit_rule=NoCritRule(),
        move_id=None,
    )
    instantiated = instantiate_damage_event(
        template,
        FixedMultiplier(Resolved(1.45)),
        battle_state_id=BattleStateId("battle:compat"),
        target_enemy=EnemyId("enemy:compat"),
        created_at=0.0,
        burnice_anomaly_source_choice=AnomalySourceChoice(
            CharacterId("character:1171"), Element.FIRE
        ),
    )
    assert isinstance(instantiated.event, DischargeDamageEvent)
    assert instantiated.event.metadata.element is Element.WIND
    assert instantiated.event.history_record_source == AnomalyRecordId("anomaly:original")
    assert isinstance(instantiated.event.multiplier, FixedMultiplier)
    assert isinstance(instantiated.event.multiplier.value, Resolved)
    assert instantiated.event.multiplier.value.value == pytest.approx(1.45)


def test_burnice_source_picker_uses_reviewed_anomaly_templates_without_base_fallback() -> None:
    burnice = compile_registered_definition(
        BURNICE_ID,
        {"core_level": 7, "cinema_level": 0, "potential_level": 1},
        (BURNICE_ID, CharacterId("character:1431")),
    )
    ye = compile_registered_definition(
        "character:1431",
        {
            "core_level": 1,
            "cinema_level": 0,
            "mingxin_active": False,
            "entry_move_uses_linren": False,
        },
        (BURNICE_ID, CharacterId("character:1431")),
    )
    burnice_editor = build_character_editor_view(
        burnice,
        team_character_ids=(BURNICE_ID, CharacterId("character:1431")),
    )
    ye_editor = build_character_editor_view(
        ye,
        team_character_ids=(BURNICE_ID, CharacterId("character:1431")),
    )
    assert burnice_editor.reviewed_anomaly_source_elements == ("fire",)
    assert ye_editor.anomaly_source_elements == ("physical",)
    assert ye_editor.reviewed_anomaly_source_elements == ()
    options = _reviewed_anomaly_source_element_options((burnice, ye))
    assert options[str(BURNICE_ID)] == (Element.FIRE,)
    assert options["character:1431"] == ()
