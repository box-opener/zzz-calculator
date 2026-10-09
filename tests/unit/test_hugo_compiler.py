from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters import CharacterSkillLevel
from core.application.characters.hugo import HUGO_ID, HugoCompileConfig, compile_hugo, load_raw_record
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, compile_wengine, load_wengine_raw_record
from core.application.characters.templates import DirectDamageEventTemplate
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.application.rules import RuleEligibility
from core.types import (
    CharacterId,
    DamageTag,
    Element,
    SkillGroup,
    WEngineBuildInput,
    WEngineId,
)
from web.api import app


client = TestClient(app)

_DARK_ECHO_ACTIVE = "condition:hugo:dark-echo-active"
_TARGET_IS_NORMAL = "condition:hugo:target-is-normal-enemy"
_C4_ICE_IGNORE_ACTIVE = "condition:hugo:cinema4:ice-resistance-ignore-active"
_CURRENT_STUN_SECONDS = "parameter:hugo:current-stun-remaining-seconds"
_CORE_DECISION_EX_RULE = "rule:character:1291:core:decision-ex-finisher-multiplier"
_C6_NONSTUN_RULE = "rule:character:1291:cinema6:ex-nonstunned-decision"
_CORE_STUN_ATTACK_RULE = "rule:character:1291:core:stun-teammate-attack"
_EXTRA_CHAIN_RULE = "rule:character:1291:extra-ability:chain-damage"
_EXTRA_NORMAL_CHAIN_RULE = "rule:character:1291:extra-ability:chain-normal-enemy-damage"


def _panel_stats(character_id: str) -> dict[str, object]:
    panel = character_base_stats(CharacterId(character_id))
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
        element.value: value.value for element, value in panel.element_damage_bonus.items()
    }
    return result


def _payload(
    entry_id: str,
    *,
    supporting: tuple[str, ...] = (),
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    parameters: dict[str, int] | None = None,
    enabled: tuple[str, ...] = (),
    resistance: float = 0.0,
) -> dict[str, object]:
    team = [str(HUGO_ID), *(item for item in supporting if item != str(HUGO_ID))]
    return {
        "primary_character_id": str(HUGO_ID),
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": entry_id,
        "compile_configs": {
            character_id: {
                "core_level": 7,
                "cinema_level": cinema if character_id == str(HUGO_ID) else 0,
            }
            for character_id in team
        },
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
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
            "enemy_id": "enemy:hugo-test",
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


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _event(result: dict[str, object], semantic_fragment: str) -> dict[str, object]:
    return next(
        item for item in result["events"]
        if semantic_fragment in item["semantic_id"]
    )


def _breakdown(event: dict[str, object], node: str, mode: str = "expected") -> float:
    return next(
        item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
        if item["node"] == node
    )


def test_hugo_live_identity_panel_and_verified_signature() -> None:
    raw = load_raw_record(load_character_record(str(HUGO_ID)))
    assert (raw.name, raw.code_name, raw.rarity) == ("雨果", "Hugo", 4)
    assert (raw.specialty, raw.element, raw.faction) == ("强攻", "冰属性", "反舌鸟")
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1291.json",
    )
    assert str(HUGO_ID) in supported_character_ids()
    panel = character_base_stats(HUGO_ID)
    assert panel.attack.value == pytest.approx(919.3011)
    assert panel.hp.value == pytest.approx(7940.7128)
    assert panel.defense.value == pytest.approx(616.6098)
    assert panel.crit_rate.value == pytest.approx(0.194)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    assert panel.anomaly_mastery.value == pytest.approx(86.0)
    assert HugoCompileConfig().core_level == 7
    assert HugoCompileConfig().cinema_level == 0
    assert HugoCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(HUGO_ID)
    catalog = next(item for item in supported_character_catalog() if item.character_id == str(HUGO_ID))
    assert catalog.code_name == "Hugo"
    assert catalog.rarity == "S"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert SIGNATURE_WENGINE_BY_CHARACTER[HUGO_ID] == WEngineId("wengine:14129")
    weapon = load_wengine_raw_record("wengine:14129")
    assert weapon.name == "千面日陨"
    assert weapon.icon == "Weapon_S_1291"
    assert weapon.source_url == "https://static.nanoka.cc/zzz/3.2/zh/weapon/14129.json"
    result = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14129"), HUGO_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert result.complete is True
    assert result.raw.base_attack == pytest.approx(713.0)
    assert result.raw.advanced_stat_value == pytest.approx(0.24)


def test_hugo_reviewed_direct_curves_and_full_ex_component_sum() -> None:
    raw = load_raw_record(load_character_record(str(HUGO_ID)))
    definition = compile_hugo(HugoCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert len(entries) == 26
    expected = {
        "move-entry:character:1291:basic-stage-1": 0.871,
        "move-entry:character:1291:basic-stage-2": 1.489,
        "move-entry:character:1291:basic-stage-3": 3.401,
        "move-entry:character:1291:basic-fourth-slash": 2.987,
        "move-entry:character:1291:basic-fourth-shot": 1.18,
        "move-entry:character:1291:basic-fourth-charged-shot": 2.368,
        "move-entry:character:1291:dash-attack": 1.87,
        "move-entry:character:1291:dodge-counter": 4.923,
        "move-entry:character:1291:dodge-counter-shot": 3.249,
        "move-entry:character:1291:dodge-counter-charged-shot": 4.244,
        "move-entry:character:1291:special": 1.711,
        "move-entry:character:1291:ex-special-spin": 0.374,
        "move-entry:character:1291:ex-special-finisher": 7.098,
        "move-entry:character:1291:chain-attack": 14.029,
        "move-entry:character:1291:ultimate": 30.55,
        "move-entry:character:1291:quick-assist": 2.09,
        "move-entry:character:1291:quick-assist-shot": 2.501,
        "move-entry:character:1291:quick-assist-charged-shot": 3.271,
        "move-entry:character:1291:assist-strike": 5.843,
    }
    for entry_id, ratio in expected.items():
        assert entries[entry_id].multiplier_variants[0].multiplier.value.value == pytest.approx(ratio)
    full_ex = entries["move-entry:character:1291:ex-special-full"]
    assert len(full_ex.derived_damage_events) == 1
    assert full_ex.multiplier_variants[0].multiplier.value.value == pytest.approx(0.374)
    assert full_ex.derived_damage_events[0].multiplier.value.value == pytest.approx(7.098)
    for stage in (1, 2, 3):
        entry = entries[f"move-entry:character:1291:basic-stage-{stage}"]
        assert entry.main_damage_event.element is Element.PHYSICAL
        assert isinstance(
            next(item for item in definition.damage_event_templates
                 if item.ref.template_id == entry.main_damage_event.template_id),
            DirectDamageEventTemplate,
        )
    for key in ("basic-fourth-slash", "basic-fourth-shot", "basic-fourth-charged-shot"):
        assert entries[f"move-entry:character:1291:{key}"].main_damage_event.element is Element.ICE
    assert "move-entry:character:1291:basic-fourth-full-shot" not in entries
    assert "move-entry:character:1291:basic-fourth-full-charged-shot" not in entries
    assert entries["move-entry:character:1291:dodge-counter-shot"].skill_group is SkillGroup.BASIC_ATTACK
    assert entries["move-entry:character:1291:dodge-counter-shot"].damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    chain_full = entries["move-entry:character:1291:chain-full"]
    assert len(chain_full.derived_damage_events) == 1
    assert chain_full.derived_damage_events[0].required is True
    assert chain_full.derived_damage_events[0].multiplier.value.value == pytest.approx(2.368)


def test_hugo_source_curve_skill_level_is_separate_from_damage_group() -> None:
    raw = load_raw_record(load_character_record(str(HUGO_ID)))
    config = HugoCompileConfig(
        skill_levels=(
            CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 16),
            CharacterSkillLevel(SkillGroup.DODGE, 1),
            CharacterSkillLevel(SkillGroup.ASSIST, 2),
            CharacterSkillLevel(SkillGroup.CHAIN_ATTACK, 1),
        )
    )
    entries = {
        str(item.entry_id): item
        for item in compile_hugo(config, raw).move_entries
    }
    counter_shot = entries["move-entry:character:1291:dodge-counter-shot"]
    quick_shot = entries["move-entry:character:1291:quick-assist-shot"]
    assert counter_shot.multiplier_variants[0].multiplier.value.value == pytest.approx(1.621)
    assert quick_shot.multiplier_variants[0].multiplier.value.value == pytest.approx(1.361)
    assert counter_shot.skill_group is quick_shot.skill_group is SkillGroup.BASIC_ATTACK
    assert counter_shot.damage_tags == quick_shot.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
    chain_base = entries["move-entry:character:1291:chain-attack"]
    chain_full = entries["move-entry:character:1291:chain-full"]
    charged_basic = entries["move-entry:character:1291:basic-fourth-charged-shot"]
    assert chain_full.multiplier_variants[0].multiplier.value.value == pytest.approx(
        chain_base.multiplier_variants[0].multiplier.value.value
    )
    assert chain_full.derived_damage_events[0].multiplier.value.value == pytest.approx(
        charged_basic.multiplier_variants[0].multiplier.value.value
    )
    assert chain_full.derived_damage_events[0].template.skill_group is SkillGroup.BASIC_ATTACK
    assert chain_full.derived_damage_events[0].template.damage_tags == frozenset({DamageTag.BASIC_ATTACK})


def test_hugo_basic_sources_have_reviewed_elements_and_complete_single_events() -> None:
    for entry_id, element in (
        ("move-entry:character:1291:basic-stage-1", "physical"),
        ("move-entry:character:1291:basic-stage-2", "physical"),
        ("move-entry:character:1291:basic-stage-3", "physical"),
        ("move-entry:character:1291:basic-fourth-slash", "ice"),
        ("move-entry:character:1291:basic-fourth-shot", "ice"),
        ("move-entry:character:1291:basic-fourth-charged-shot", "ice"),
    ):
        result = _calculate(_payload(entry_id))
        assert len(result["events"]) == 1
        assert result["events"][0]["element"] == element
        assert result["totals"]["expected"]["complete"] is True


def test_hugo_chain_full_has_required_basic_charged_shot_once() -> None:
    base = _calculate(_payload("move-entry:character:1291:chain-attack"))
    assert len(base["events"]) == 1
    assert base["totals"]["expected"]["complete"] is True

    charged_shot = _calculate(
        _payload("move-entry:character:1291:basic-fourth-charged-shot")
    )
    definition = compile_hugo(
        HugoCompileConfig(),
        load_raw_record(load_character_record(str(HUGO_ID))),
    )
    enabled_rules = tuple(
        str(rule.rule_id)
        for rule in definition.rule_items
        if rule.eligibility is RuleEligibility.ELIGIBLE
    )
    for enabled in ((), enabled_rules):
        full = _calculate(
            _payload("move-entry:character:1291:chain-full", enabled=enabled)
        )
        assert len(full["events"]) == 2
        assert full["totals"]["expected"]["complete"] is True
        assert full["events"][0]["modes"]["expected"]["value"] == pytest.approx(
            base["events"][0]["modes"]["expected"]["value"]
        )
        assert full["events"][1]["modes"]["expected"]["value"] == pytest.approx(
            charged_shot["events"][0]["modes"]["expected"]["value"]
        )
        assert full["totals"]["expected"]["value"] == pytest.approx(
            base["totals"]["expected"]["value"]
            + charged_shot["totals"]["expected"]["value"]
        )


def test_hugo_ex_full_has_two_real_ice_events_and_decision_uses_selected_stun_time() -> None:
    entry_id = "move-entry:character:1291:ex-special-full"
    definition = compile_hugo(
        HugoCompileConfig(),
        load_raw_record(load_character_record(str(HUGO_ID))),
    )
    enabled_rules = tuple(
        str(rule.rule_id)
        for rule in definition.rule_items
        if rule.eligibility is RuleEligibility.ELIGIBLE
    )
    for enabled in ((), enabled_rules):
        unstunned = _calculate(_payload(entry_id, enabled=enabled))
        assert len(unstunned["events"]) == 2
        assert unstunned["totals"]["expected"]["complete"] is True
        assert sum(
            event["modes"]["expected"]["calculation_breakdown"][0]["value"]
            for event in unstunned["events"]
        ) > 0

    stunned_payload = _payload(
            entry_id,
            parameters={_CURRENT_STUN_SECONDS: 5},
            enabled=(_CORE_DECISION_EX_RULE,),
    )
    stunned_payload["enemy"]["is_stunned"] = True
    stunned = _calculate(stunned_payload)
    terminal = _event(stunned, "ex-special-full:finisher")
    assert _breakdown(terminal, "damage.skill-multiplier") == pytest.approx(31.098)
    assert len(stunned["events"]) == 2
    assert stunned["totals"]["expected"]["complete"] is True

    c6_payload = _payload(
        entry_id,
        cinema=6,
        enabled=(_C6_NONSTUN_RULE,),
    )
    c6 = _calculate(c6_payload)
    c6_terminal = _event(c6, "ex-special-full:finisher")
    assert _breakdown(c6_terminal, "damage.skill-multiplier") == pytest.approx(18.39)
    assert len(c6["events"]) == 2
    assert c6["totals"]["expected"]["value"] is not None
    assert c6["totals"]["expected"]["complete"] is False
    assert any("尚未确认" in item["message"] for item in c6["diagnostics"])


def test_hugo_decision_split_unknowns_mark_only_affected_parent_events_partial() -> None:
    ult_c2 = _payload(
        "move-entry:character:1291:ultimate",
        cinema=2,
        parameters={_CURRENT_STUN_SECONDS: 5},
        enabled=(
            _CORE_DECISION_EX_RULE,
            "rule:character:1291:cinema2:decision-defense-ignore",
        ),
    )
    ult_c2["enemy"]["is_stunned"] = True
    c2_result = _calculate(ult_c2)
    assert len(c2_result["events"]) == 1
    assert c2_result["events"][0]["modes"]["expected"]["value"] is not None
    assert c2_result["totals"]["expected"]["complete"] is False

    ex_c2 = _payload(
        "move-entry:character:1291:ex-special-full",
        cinema=2,
        enabled=("rule:character:1291:cinema2:decision-defense-ignore",),
    )
    ex_c2["enemy"]["is_stunned"] = True
    ex_c2_result = _calculate(ex_c2)
    terminal = _event(ex_c2_result, "ex-special-full:finisher")
    assert _breakdown(terminal, "defense.damage-ignore") == pytest.approx(0.15)
    assert len(ex_c2_result["events"]) == 2
    assert ex_c2_result["totals"]["expected"]["value"] is not None
    assert ex_c2_result["totals"]["expected"]["complete"] is False

    ex_c1 = _payload(
        "move-entry:character:1291:ex-special-full",
        cinema=1,
        conditions={_DARK_ECHO_ACTIVE: True},
        enabled=("rule:character:1291:cinema1:ex-decision-stunned-crit",),
    )
    ex_c1["enemy"]["is_stunned"] = True
    c1_result = _calculate(ex_c1)
    assert len(c1_result["events"]) == 2
    assert all(event["modes"]["expected"]["value"] is not None for event in c1_result["events"])
    assert c1_result["totals"]["expected"]["complete"] is False

    extra_ult = _payload(
        "move-entry:character:1291:ultimate",
        supporting=("character:1141",),
        parameters={_CURRENT_STUN_SECONDS: 5},
        enabled=(
            _CORE_DECISION_EX_RULE,
            "rule:character:1291:extra-ability:ex-decision-stunned-damage",
        ),
    )
    extra_ult["enemy"]["is_stunned"] = True
    extra_result = _calculate(extra_ult)
    assert len(extra_result["events"]) == 1
    assert extra_result["events"][0]["modes"]["expected"]["value"] is not None
    assert extra_result["totals"]["expected"]["complete"] is False


def test_hugo_current_team_attack_and_chain_additional_ability_scopes() -> None:
    panel = _panel_stats(str(HUGO_ID))
    for supports, bonus in (
        (("character:1141",), 300.0),
        (("character:1141", "character:1101"), 900.0),
    ):
        result = _calculate(
            _payload(
                "move-entry:character:1291:dash-attack",
                supporting=supports,
                enabled=(_CORE_STUN_ATTACK_RULE,),
            )
        )
        snapshot = next(
            item for item in result["resolved_character_snapshots"]
            if item["character_id"] == str(HUGO_ID)
        )
        assert snapshot["stats"]["attack"] == pytest.approx(panel["attack"] + bonus)

    chain_base = _calculate(
        _payload("move-entry:character:1291:chain-attack", supporting=("character:1141",))
    )
    chain_buffed = _calculate(
        _payload(
            "move-entry:character:1291:chain-attack",
            supporting=("character:1141",),
            conditions={_TARGET_IS_NORMAL: True},
            enabled=(_EXTRA_CHAIN_RULE, _EXTRA_NORMAL_CHAIN_RULE),
        )
    )
    assert chain_buffed["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        chain_base["events"][0]["modes"]["expected"]["value"] * 1.50
    )


def test_hugo_cinema4_current_ice_resistance_ignore_is_own_ice_damage_only() -> None:
    base = _calculate(
        _payload("move-entry:character:1291:special", cinema=4, resistance=0.25)
    )
    enabled = _calculate(
        _payload(
            "move-entry:character:1291:special",
            cinema=4,
            conditions={_C4_ICE_IGNORE_ACTIVE: True},
            enabled=("rule:character:1291:cinema4:ice-resistance-ignore",),
            resistance=0.25,
        )
    )
    assert _breakdown(enabled["events"][0], "resistance.damage-ignore") == pytest.approx(0.12)
    assert enabled["totals"]["expected"]["value"] > base["totals"]["expected"]["value"]

    physical = _calculate(
        _payload(
            "move-entry:character:1291:dash-attack",
            cinema=4,
            conditions={_C4_ICE_IGNORE_ACTIVE: True},
            enabled=("rule:character:1291:cinema4:ice-resistance-ignore",),
            resistance=0.25,
        )
    )
    assert _breakdown(physical["events"][0], "resistance.damage-ignore") == pytest.approx(0.0)

    for entry_id in (
        "move-entry:character:1291:ice-shatter",
        "move-entry:character:1291:ice-disorder",
    ):
        own = _calculate(
            _payload(
                entry_id,
                cinema=4,
                conditions={_C4_ICE_IGNORE_ACTIVE: True},
                enabled=("rule:character:1291:cinema4:ice-resistance-ignore",),
                resistance=0.25,
            )
        )
        assert _breakdown(own["events"][0], "resistance.damage-ignore") == pytest.approx(0.12)

    peer_builds = {
        "character:1141": {"level": 60, "build_mode": "equipment-build", "base_stats": _panel_stats("character:1141"), "drive_discs": []},
        "character:1291": {"level": 60, "build_mode": "equipment-build", "base_stats": _panel_stats("character:1291"), "drive_discs": []},
    }
    peer_payload = {
        "primary_character_id": "character:1141",
        "supporting_character_ids": ["character:1291"],
        "team_character_ids": ["character:1141", "character:1291"],
        "formation_character_ids": ["character:1141", "character:1291"],
        "move_entry_id": "move-entry:character:1141:dodge-counter-etiquette-lesson",
        "compile_configs": {
            "character:1141": {"core_level": 7, "cinema_level": 0, "potential_level": 0},
            "character:1291": {"core_level": 7, "cinema_level": 4},
        },
        "condition_values": {_C4_ICE_IGNORE_ACTIVE: True},
        "parameter_values": {},
        "enabled_rule_item_ids": ["rule:character:1291:cinema4:ice-resistance-ignore"],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": peer_builds,
        "enemy": {
            "enemy_id": "enemy:hugo-peer-c4",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {"physical": 0.25, "fire": 0.25, "ice": 0.25, "electric": 0.25, "ether": 0.25, "wind": 0.25, "luminance": 0.25},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
    }
    peer = _calculate(peer_payload)
    assert _breakdown(peer["events"][0], "resistance.damage-ignore") == pytest.approx(0.0)
