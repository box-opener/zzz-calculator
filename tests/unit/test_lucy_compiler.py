from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.lucy import (
    LUCY_ID,
    LUCY_REVIEWED_MAPPING,
    LucyCompileConfig,
    compile_lucy,
    load_raw_record,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    load_wengine_raw_record,
)
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    _lucy_additional_ability_eligibility,
    config_fields_for,
)
from core.types import (
    CharacterId,
    CharacterRole,
    DamageTag,
    EffectTarget,
    Element,
    PanelStatDerivedValue,
    Resolved,
    SkillGroup,
)
from web.api import app


client = TestClient(app)


def _definition(*, cinema: int = 0, skills=(), eligible: bool = False):
    return compile_lucy(
        LucyCompileConfig(
            cinema_level=cinema,
            skill_levels=tuple(skills),
            additional_ability_eligible=eligible,
        ),
        load_raw_record(load_character_record(str(LUCY_ID))),
    )


def _entries(definition):
    return {
        str(item.entry_id).rsplit(":", 1)[-1]: item for item in definition.move_entries
    }


def _ratio(entry) -> float:
    value = entry.multiplier_variants[0].multiplier.value
    assert isinstance(value, Resolved)
    return value.value


def _api_stats(character_id: str) -> dict:
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
            element.value: value.value
            for element, value in panel.element_damage_bonus.items()
        },
    }


def _api_payload(*, cheer_active: bool) -> dict:
    lucy = str(LUCY_ID)
    teammate = "character:1051"
    team = (lucy, teammate)
    return {
        "primary_character_id": lucy,
        "supporting_character_ids": [teammate],
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": "move-entry:character:1151:chain-attack",
        "compile_configs": {
            lucy: {"core_level": 7, "cinema_level": 4},
            teammate: {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {"condition:lucy:cheer-on-active": cheer_active},
        "parameter_values": {"parameter:lucy:fire-disorder-remaining-seconds": 10},
        "enabled_rule_item_ids": [
            "rule:character:1151:cheer-on:team-attack",
            "rule:character:1151:cinema4:cheer-on-team-crit-damage",
        ],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _api_stats(item)}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:lucy-test",
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


def test_lucy_source_panel_signature_and_defaults_are_reviewed() -> None:
    source = load_character_record(str(LUCY_ID))
    assert set(source) == {
        "id",
        "icon",
        "name",
        "code_name",
        "rarity",
        "weapon_type",
        "element_type",
        "special_element_type",
        "hit_type",
        "camp",
        "gender",
        "partner_info",
        "skin",
        "stats",
        "level",
        "extra_level",
        "level_exp",
        "skill",
        "skill_priority",
        "skill_list",
        "passive",
        "talent",
        "fairy_recommend",
        "strategy",
        "potential",
        "potential_detail",
        "source_version",
        "source_url",
    }
    raw = load_raw_record(source)
    assert str(LUCY_ID) in supported_character_ids()
    assert raw.name == "露西"
    assert raw.code_name == "Lucy"
    assert raw.specialty == "支援"
    assert raw.element == "火属性"
    assert raw.faction == "卡吕冬之子"
    assert raw.icon == "IconRole27"
    assert raw.rarity == 3
    assert raw.potential_details == ()
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1151.json",
    )

    panel = character_base_stats(LUCY_ID)
    assert panel.attack.value == pytest.approx(658.957)
    assert panel.hp.value == pytest.approx(8025.9663)
    assert panel.defense.value == pytest.approx(612.6038)
    assert panel.impact.value == pytest.approx(86.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(93.0)
    assert panel.anomaly_mastery.value == pytest.approx(94.0)
    assert panel.energy_regen.value == pytest.approx(1.56)

    assert SIGNATURE_WENGINE_BY_CHARACTER[LUCY_ID] == "wengine:13115"
    engine = load_wengine_raw_record("wengine:13115")
    assert engine.name == "好斗的阿炮"
    assert engine.icon == "Weapon_A_1151"
    assert engine.specialty is CharacterRole.SUPPORT
    assert engine.base_attack == pytest.approx(624.0)
    assert engine.advanced_stat_value == pytest.approx(0.5)
    assert LucyCompileConfig().core_level == 7
    assert LucyCompileConfig().cinema_level == 0
    assert LucyCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16
    assert {item.entry_key for item in LUCY_REVIEWED_MAPPING.moves} == {
        "basic-1",
        "basic-2",
        "basic-3",
        "basic-3-derived",
        "basic-4",
        "dash-attack",
        "dodge-counter",
        "special-straight-ball",
        "special-fly-ball",
        "ex-special-straight-ball",
        "ex-special-fly-ball",
        "chain-attack",
        "ultimate",
        "quick-assist",
        "assist-strike",
    }

    fields = {
        item.field_id: item for item in config_fields_for(LUCY_ID, {}, (LUCY_ID,))
    }
    assert fields["core_level"].value == 7
    assert fields["cinema_level"].value == 0
    assert fields["skill_level:ultimate"].value == 16


def test_lucy_direct_curves_keep_source_elements_and_curve_expression_once() -> None:
    entries = _entries(_definition())
    assert len(entries) == 21
    assert [
        _ratio(entries[f"basic-{stage}"]) for stage in ("1", "2", "3", "3-derived", "4")
    ] == pytest.approx([1.346, 1.843, 4.469, 5.01, 6.446])
    assert entries["basic-1"].main_damage_event.element is Element.PHYSICAL
    assert entries["basic-2"].main_damage_event.element is Element.PHYSICAL
    assert entries["basic-3"].main_damage_event.element is Element.FIRE
    assert "属性待确认" in entries["basic-3-derived"].display_name
    assert entries["basic-3-derived"].multiplier_relation.value == "unresolved-relation"
    assert entries["basic-3-derived"].diagnostics[0].blocking is True
    assert entries["basic-4"].main_damage_event.element is Element.FIRE
    assert _ratio(entries["dash-attack"]) == pytest.approx(1.864)
    assert entries["dash-attack"].main_damage_event.element is Element.PHYSICAL
    assert _ratio(entries["dodge-counter"]) == pytest.approx(7.28)
    assert entries["dodge-counter"].main_damage_event.element is Element.FIRE
    assert _ratio(entries["special-straight-ball"]) == pytest.approx(1.472)
    assert _ratio(entries["special-fly-ball"]) == pytest.approx(1.637)
    assert _ratio(entries["ex-special-straight-ball"]) == pytest.approx(12.029)
    assert _ratio(entries["ex-special-fly-ball"]) == pytest.approx(12.684)
    assert (
        DamageTag.EX_SPECIAL_ATTACK in entries["ex-special-straight-ball"].damage_tags
    )
    assert (
        DamageTag.SPECIAL_ATTACK not in entries["ex-special-straight-ball"].damage_tags
    )
    # The raw /3*3 descriptions resolve to one curve value; they are not three repeated hits.
    assert _ratio(entries["chain-attack"]) == pytest.approx(11.644)
    assert _ratio(entries["ultimate"]) == pytest.approx(40.631)
    assert _ratio(entries["quick-assist"]) == pytest.approx(3.79)
    assert _ratio(entries["assist-strike"]) == pytest.approx(8.261)
    assert _ratio(entries["fire-anomaly"]) == pytest.approx(0.5)
    assert entries["fire-anomaly"].multiplier_variants[0].repeat_count == 20
    assert _ratio(entries["pig-random-bat"]) == pytest.approx(2.2)
    assert _ratio(entries["pig-random-gloves"]) == pytest.approx(3.015)
    assert _ratio(entries["pig-random-slingshot"]) == pytest.approx(4.15)
    assert _ratio(entries["pig-revolving-swing"]) == pytest.approx(5.92)
    assert all(
        entries[key].multiplier_relation.value == "unresolved-relation"
        and entries[key].main_damage_event.skill_group is None
        and entries[key].damage_tags == frozenset()
        for key in (
            "pig-random-bat",
            "pig-random-gloves",
            "pig-random-slingshot",
            "pig-revolving-swing",
        )
    )


def test_lucy_ultimate_levels_follow_c3_and_c5_caps() -> None:
    levels = []
    for cinema in (0, 3, 5):
        definition = _definition(
            cinema=cinema,
            skills=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
        )
        levels.append(_ratio(_entries(definition)["ultimate"]))
    assert levels == pytest.approx([34.379, 37.505, 40.631])


def test_lucy_basic3_derived_retains_source_curve_without_guessing_its_element() -> (
    None
):
    payload = _api_payload(cheer_active=False)
    payload["move_entry_id"] = "move-entry:character:1151:basic-3-derived"
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["events"] == []
    assert result["totals"]["expected"]["complete"] is False
    assert any(
        item["diagnostic_id"] == "review:character:1151:basic-3-derived-element"
        for item in result["totals"]["expected"]["diagnostics"]
    )


def test_lucy_cheer_on_uses_special_skill_level_and_team_scopes() -> None:
    definition = _definition(cinema=4)
    rules = {str(item.rule_id): item for item in definition.rule_items}
    cheer = rules["rule:character:1151:cheer-on:team-attack"]
    assert cheer.effects[0].rule.target is EffectTarget.TEAM
    assert (
        cheer.effects[0].result.modifier_path.value
        == "character.combat.attack-flat-bonus"
    )
    assert isinstance(cheer.effects[0].result.value, PanelStatDerivedValue)
    assert cheer.effects[0].result.value.source_node.value == "character.initial.attack"
    assert cheer.effects[0].result.value.coefficient == Resolved(0.258)
    assert cheer.effects[0].result.value.base == Resolved(104.0)
    assert cheer.effects[0].result.value.cap_max == Resolved(600.0)
    assert str(cheer.condition_ids[0]) == "condition:lucy:cheer-on-active"

    c4 = rules["rule:character:1151:cinema4:cheer-on-team-crit-damage"]
    assert c4.eligibility.value == "eligible"
    assert c4.effects[0].rule.target is EffectTarget.TEAM
    assert c4.effects[0].result.modifier_path.value == "character.current.crit-damage"
    assert c4.effects[0].result.value == Resolved(0.10)

    level12 = _definition(skills=(CharacterSkillLevel(SkillGroup.SPECIAL_ATTACK, 12),))
    level12_cheer = (
        next(
            item
            for item in level12.rule_items
            if str(item.rule_id) == "rule:character:1151:cheer-on:team-attack"
        )
        .effects[0]
        .result.value
    )
    assert isinstance(level12_cheer, PanelStatDerivedValue)
    assert level12_cheer.coefficient == Resolved(0.226)
    assert level12_cheer.base == Resolved(88.0)


def test_lucy_extra_ability_uses_actual_team_eligibility() -> None:
    assert _lucy_additional_ability_eligibility(
        (LUCY_ID, CharacterId("character:1071"))
    )
    assert _lucy_additional_ability_eligibility(
        (LUCY_ID, CharacterId("character:1051"))
    )
    assert _lucy_additional_ability_eligibility(
        (LUCY_ID, CharacterId("character:1101"))
    )
    assert not _lucy_additional_ability_eligibility(
        (LUCY_ID, CharacterId("character:1111"))
    )
    assert not _lucy_additional_ability_eligibility(
        (LUCY_ID, CharacterId("character:1141"))
    )


def test_lucy_cinema6_keeps_followers_local_and_does_not_forge_direct_hits() -> None:
    c0 = _definition(cinema=0)
    c6 = _definition(cinema=6)
    c0_rule = next(
        item
        for item in c0.rule_items
        if str(item.rule_id) == "rule:character:1151:cinema6:pig-followup"
    )
    assert c0_rule.eligibility.value == "ineligible"
    assert c0_rule.effects == ()
    rule = next(
        item
        for item in c6.rule_items
        if str(item.rule_id) == "rule:character:1151:cinema6:pig-followup"
    )
    assert rule.eligibility.value == "eligible"
    assert len(rule.effects) == 2
    assert all(effect.result.unresolved_template is not None for effect in rule.effects)
    # The selected Lucy direct entries remain their source ratios, with no pig attacks
    # fabricated as extra Direct events from a random/follower hit history.
    entries = _entries(c6)
    assert len(entries) == 23
    assert _ratio(entries["cinema6-pig-explosion"]) == pytest.approx(3.0)
    assert _ratio(entries["cinema6-pig-revolving-swing"]) == pytest.approx(5.92)
    assert (
        entries["cinema6-pig-explosion"].multiplier_relation.value
        == "unresolved-relation"
    )


def test_lucy_cheer_on_and_c4_apply_to_party_current_panels_and_direct_damage() -> None:
    off_response = client.post(
        "/api/v1/moves/calculate", json=_api_payload(cheer_active=False)
    )
    assert off_response.status_code == 200, off_response.text
    on_response = client.post(
        "/api/v1/moves/calculate", json=_api_payload(cheer_active=True)
    )
    assert on_response.status_code == 200, on_response.text
    off = off_response.json()
    on = on_response.json()
    assert off["totals"]["expected"]["complete"] is True
    assert on["totals"]["expected"]["complete"] is True

    attack_in = {
        item["character_id"]: item["stats"]["attack"]
        for item in on["resolved_character_snapshots"]
    }
    attack_off = {
        item["character_id"]: item["stats"]["attack"]
        for item in off["resolved_character_snapshots"]
    }
    buff = 0.258 * 658.957 + 104.0
    assert attack_in[str(LUCY_ID)] - attack_off[str(LUCY_ID)] == pytest.approx(buff)
    assert attack_in["character:1051"] - attack_off["character:1051"] == pytest.approx(
        buff
    )
    assert on["events"][0]["damage_type"] == "direct"
    assert on["events"][0]["element"] == "fire"
    off_crit = next(
        item["value"]
        for item in off["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.standard-crit-region"
    )
    on_crit = next(
        item["value"]
        for item in on["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.standard-crit-region"
    )
    assert off_crit == pytest.approx(1.025)
    assert on_crit == pytest.approx(1.03)


def test_lucy_basic4_only_reports_pig_followup_when_pigs_are_selected_on_field() -> (
    None
):
    rule = "rule:character:1151:skill:basic-four-pig-swing"
    false_payload = _api_payload(cheer_active=False)
    false_payload["move_entry_id"] = "move-entry:character:1151:basic-4"
    false_payload["condition_values"]["condition:lucy:bodyguard-pigs-active"] = False
    false_payload["enabled_rule_item_ids"].append(rule)
    false_response = client.post("/api/v1/moves/calculate", json=false_payload)
    assert false_response.status_code == 200, false_response.text
    assert false_response.json()["totals"]["expected"]["complete"] is True

    true_payload = _api_payload(cheer_active=False)
    true_payload["move_entry_id"] = "move-entry:character:1151:basic-4"
    true_payload["condition_values"]["condition:lucy:bodyguard-pigs-active"] = True
    true_payload["enabled_rule_item_ids"].append(rule)
    true_response = client.post("/api/v1/moves/calculate", json=true_payload)
    assert true_response.status_code == 200, true_response.text
    true_result = true_response.json()
    assert len(true_result["events"]) == 1
    assert true_result["totals"]["expected"]["complete"] is False
    assert any(
        item["diagnostic_id"]
        == "application:effect:character:1151:basic-four-pig-swing:unresolved-template"
        for item in true_result["totals"]["expected"]["diagnostics"]
    )


def test_lucy_selectable_pig_source_entries_do_not_emit_synthetic_direct_events() -> (
    None
):
    payload = _api_payload(cheer_active=False)
    payload["move_entry_id"] = "move-entry:character:1151:pig-random-bat"
    payload["condition_values"]["condition:lucy:bodyguard-pigs-active"] = True
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["events"] == []
    assert result["totals"]["expected"]["complete"] is False
    assert any(
        item["diagnostic_id"]
        == "source:character:1151:pig-random-bat:follower-identity"
        for item in result["totals"]["expected"]["diagnostics"]
    )


def test_lucy_cinema6_scopes_children_to_teammate_ex_including_penetration() -> None:
    lucy = str(LUCY_ID)
    teammate = "character:1371"
    team = (teammate, lucy)
    payload = {
        "primary_character_id": teammate,
        "supporting_character_ids": [lucy],
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": "move-entry:character:1371:ex-mark-transformation",
        "compile_configs": {
            teammate: {"core_level": 7, "cinema_level": 0},
            lucy: {"core_level": 7, "cinema_level": 6},
        },
        "condition_values": {"condition:lucy:cheer-on-active": True},
        "parameter_values": {"parameter:lucy:fire-disorder-remaining-seconds": 10},
        "enabled_rule_item_ids": ["rule:character:1151:cinema6:pig-followup"],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _api_stats(item)}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:lucy-cinema6-test",
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
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert len(result["events"]) == 1
    assert result["events"][0]["damage_type"] == "penetration"
    assert result["totals"]["expected"]["value"] > 0
    assert result["totals"]["expected"]["complete"] is False
    assert (
        sum(
            diagnostic["diagnostic_id"].startswith(
                "application:effect:character:1151:cinema6"
            )
            for diagnostic in result["totals"]["expected"]["diagnostics"]
        )
        == 2
    )

    self_payload = {
        "primary_character_id": lucy,
        "supporting_character_ids": [teammate],
        "team_character_ids": [lucy, teammate],
        "formation_character_ids": [lucy, teammate],
        "move_entry_id": "move-entry:character:1151:ex-special-straight-ball",
        "compile_configs": {
            lucy: {"core_level": 7, "cinema_level": 6},
            teammate: {"core_level": 7, "cinema_level": 0},
        },
        "condition_values": {"condition:lucy:cheer-on-active": True},
        "parameter_values": {"parameter:lucy:fire-disorder-remaining-seconds": 10},
        "enabled_rule_item_ids": ["rule:character:1151:cinema6:pig-followup"],
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _api_stats(item)}
            for item in (lucy, teammate)
        },
        "enemy": {
            "enemy_id": "enemy:lucy-cinema6-self-test",
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
    self_response = client.post("/api/v1/moves/calculate", json=self_payload)
    assert self_response.status_code == 200, self_response.text
    self_result = self_response.json()
    assert self_result["totals"]["expected"]["complete"] is True
    assert len(self_result["events"]) == 1
