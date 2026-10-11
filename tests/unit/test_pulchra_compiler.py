from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_source import NanokaRawMoveRecord
from core.application.characters.pulchra import (
    PULCHRA_ID,
    PulchraCompileConfig,
    compile_pulchra,
    load_raw_record,
)
from core.application.characters.pulchra.reviewed import (
    PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT,
    PULCHRA_CINEMA6_NIGHTMARE_RULE_ID,
    PULCHRA_EXTRA_ABILITY_RULE_ID,
    PULCHRA_HUNTER_STEP_ACTIVE,
    PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT,
    PULCHRA_PURSUIT_MARK_ACTIVE,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.application.moves import MultiplierRelation
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import (
    CharacterId,
    DamageTag,
    Element,
    FixedMultiplier,
    Resolved,
    SkillGroup,
    Unresolved,
    WEngineId,
)
from web.api import app


client = TestClient(app)

_MAIN = "move-entry:pulchra:1351:nightmare-shadow-main"
_EXTRA_ABILITY = str(PULCHRA_EXTRA_ABILITY_RULE_ID)
_C6_NIGHTMARE = str(PULCHRA_CINEMA6_NIGHTMARE_RULE_ID)
_C6_PURSUIT = "rule:character:1351:cinema6:pursuit-non-follow-up"
_NIGHTMARE_BASE_COUNT = str(PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT)
_C6_EXTRA_COUNT = str(PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT)
_HUNTER_STEP_RULE = "rule:character:1351:cinema2:hunter-step-attack"
_NIGHTMARE_REPEAT_RULE = "rule:character:1351:nightmare-repeat-packets"
_C1_RULE = "rule:character:1351:cinema1:pursuit-crit-rate"


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
    pulchra_cinema: int = 6,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    stacks: dict[str, int] | None = None,
    parameters: dict[str, int] | None = None,
    pulchra_skill_level: int | None = None,
) -> dict[str, object]:
    team = [primary, *(character_id for character_id in supporting if character_id != primary)]
    configs: dict[str, dict[str, object]] = {}
    for character_id in team:
        configs[character_id] = {"core_level": 7, "cinema_level": 0}
        if character_id == "character:1351":
            configs[character_id]["cinema_level"] = pulchra_cinema
            if pulchra_skill_level is not None:
                configs[character_id]["skill_levels"] = {"special-attack": pulchra_skill_level}
        if character_id == "character:1261":
            configs[character_id]["potential_level"] = 0
    payload: dict[str, object] = {
        "primary_character_id": primary,
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
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
            "enemy_id": "enemy:pulchra-test",
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
    return payload


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _event(result: dict[str, object], semantic_fragment: str) -> dict[str, object]:
    return next(item for item in result["events"] if semantic_fragment in item["semantic_id"])


def _normal_bonus(event: dict[str, object]) -> float:
    return next(
        item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    )


def _node(event: dict[str, object], node_id: str) -> float:
    return next(
        item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == node_id
    )


def test_pulchra_live_source_registry_signature_and_defaults() -> None:
    raw = load_raw_record(load_character_record(str(PULCHRA_ID)))
    assert (raw.name, raw.code_name, raw.rarity) == ("波可娜", "Pulchra", 3)
    assert (raw.specialty, raw.element, raw.faction) == ("击破", "物理", "卡吕冬之子")
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1351.json",
    )
    assert str(PULCHRA_ID) in supported_character_ids()
    assert character_base_stats(PULCHRA_ID).attack.value == pytest.approx(665.8333)
    assert PulchraCompileConfig().core_level == 7
    assert PulchraCompileConfig().cinema_level == 6
    assert PulchraCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16

    registration = registration_for(PULCHRA_ID)
    assert registration.catalog.rarity == "A"
    assert registration.catalog.code_name == "Pulchra"
    defaults = {
        item.field_id: item.value
        for item in registration.config_fields({}, (PULCHRA_ID,))
    }
    assert defaults["core_level"] == 7
    assert defaults["cinema_level"] == 6
    assert defaults["skill_level:ultimate"] == 16
    catalog_item = next(
        item for item in supported_character_catalog() if item.character_id == str(PULCHRA_ID)
    )
    assert catalog_item.code_name == "Pulchra"
    assert SIGNATURE_WENGINE_BY_CHARACTER[PULCHRA_ID] == WEngineId("wengine:13135")
    assert load_wengine_raw_record("wengine:13135").icon == "Weapon_A_1351"

    build_preview = client.post(
        "/api/v1/builds/preview",
        json={
            "character_id": str(PULCHRA_ID),
            "level": 60,
            "wengine_id": "wengine:13135",
            "wengine_level": 60,
            "wengine_refinement": 5,
            "drive_discs": [],
        },
    )
    assert build_preview.status_code == 200, build_preview.text
    preview = build_preview.json()
    assert preview["complete"] is True
    assert preview["out_of_combat_stats"]["attack"] == pytest.approx(665.8333 + 624)


def test_pulchra_reviewed_direct_curves_and_cinema_skill_levels() -> None:
    raw = load_raw_record(load_character_record(str(PULCHRA_ID)))
    definition = compile_pulchra(PulchraCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert len(entries) == 13
    expected_level16 = {
        "basic-jab-1": 0.852,
        "basic-jab-2": 2.231,
        "basic-jab-3": 3.971,
        "basic-leaping-slash": 3.195,
        "dash-attack": 1.143,
        "dodge-counter": 4.778,
        "special-claw-strike": 0.596,
        "nightmare-shadow-main": 1.108,
        "ex-step": 8.232,
        "chain-attack": 12.631,
        "ultimate": 32.958,
        "quick-assist": 1.863,
        "assist-strike": 7.271,
    }
    assert {
        str(entry.entry_id).rsplit(":", 1)[-1]: entry.multiplier_variants[0].multiplier.value.value
        for entry in entries.values()
    } == pytest.approx(expected_level16)
    assert entries["move-entry:pulchra:1351:basic-jab-1"].multiplier_relation is MultiplierRelation.SEQUENTIAL_STAGE
    assert entries["move-entry:pulchra:1351:basic-jab-2"].multiplier_variants[0].multiplier.value.value == pytest.approx(2.231)
    assert entries["move-entry:pulchra:1351:basic-leaping-slash"].multiplier_variants[0].multiplier.value.value == pytest.approx(3.195)
    assert entries[_MAIN].main_damage_event.damage_tags == frozenset(
        {DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}
    )
    assert entries["move-entry:pulchra:1351:ex-step"].main_damage_event.damage_tags == frozenset(
        {DamageTag.EX_SPECIAL_ATTACK}
    )
    assert entries["move-entry:pulchra:1351:ultimate"].skill_group is SkillGroup.ULTIMATE
    assert len(definition.independent_derived_damage_events) == 14
    assert len(definition.scenario_parameters) == 2
    assert not any("daze" in str(item).lower() for item in definition.scenario_conditions)

    skill_levels = tuple(CharacterSkillLevel(group, 12) for group in SkillGroup)
    base12 = compile_pulchra(
        PulchraCompileConfig(cinema_level=0, skill_levels=skill_levels), raw
    )
    c3 = compile_pulchra(
        PulchraCompileConfig(cinema_level=3, skill_levels=skill_levels), raw
    )
    c5 = compile_pulchra(
        PulchraCompileConfig(cinema_level=5, skill_levels=skill_levels), raw
    )
    level_entries = [
        {str(item.entry_id): item for item in definition.move_entries}
        for definition in (base12, c3, c5)
    ]
    assert {entry.skill_group for entry in level_entries[0].values()} == set(SkillGroup)
    for entry_id in entries:
        selected_values = [
            item[entry_id].multiplier_variants[0].multiplier.value.value
            for item in level_entries
        ]
        assert len(set(selected_values)) == 3, entry_id


@pytest.mark.parametrize(
    ("skill_level", "ordinary", "finisher"),
    ((12, 0.936, 1.074), (14, 1.022, 1.172), (16, 1.108, 1.270)),
)
def test_pulchra_nightmare_child_packets_use_selected_special_skill_level(
    skill_level: int,
    ordinary: float,
    finisher: float,
) -> None:
    result = _calculate(
        _payload(
            "character:1351",
            _MAIN,
            pulchra_cinema=0,
            pulchra_skill_level=skill_level,
            enabled=(_NIGHTMARE_REPEAT_RULE,),
            parameters={_NIGHTMARE_BASE_COUNT: 2, _C6_EXTRA_COUNT: 0},
        )
    )
    assert len(result["events"]) == 3
    assert _node(_event(result, "nightmare-extra-1:ordinary"), "damage.skill-multiplier") == pytest.approx(ordinary)
    assert _node(_event(result, "nightmare-extra-2:finisher"), "damage.skill-multiplier") == pytest.approx(finisher)


def test_pulchra_missing_finisher_curve_is_localized_to_nightmare_children() -> None:
    raw = load_raw_record(load_character_record(str(PULCHRA_ID)))
    nightmare_move = next(move for move in raw.moves if move.name == "特殊技：噬爪·噩梦袭影")
    missing_finisher = replace(
        nightmare_move,
        parameters=tuple(
            parameter
            for parameter in nightmare_move.parameters
            if parameter.name != "终结一击伤害倍率"
        ),
    )
    degraded_raw = replace(
        raw,
        moves=tuple(
            missing_finisher if move.name == missing_finisher.name else move
            for move in raw.moves
        ),
    )
    definition = compile_pulchra(
        PulchraCompileConfig(cinema_level=0), degraded_raw
    )

    finisher_refs = [
        item for item in definition.independent_derived_damage_events
        if ":finisher" in str(item.template.semantic_id)
    ]
    ordinary_refs = [
        item for item in definition.independent_derived_damage_events
        if ":ordinary" in str(item.template.semantic_id)
    ]
    assert len(finisher_refs) == len(ordinary_refs) == 7
    assert all(isinstance(item.multiplier, Unresolved) for item in finisher_refs)
    assert all(
        isinstance(item.multiplier, FixedMultiplier)
        and isinstance(item.multiplier.value, Resolved)
        for item in ordinary_refs
    )
    repeat_rule = next(
        item for item in definition.rule_items if str(item.rule_id) == _NIGHTMARE_REPEAT_RULE
    )
    assert len(repeat_rule.diagnostics) == 1
    assert repeat_rule.diagnostics[0].blocking is False
    assert "data:character:1351:nightmare-finisher:missing-curve" in str(
        repeat_rule.diagnostics[0].diagnostic_id
    )
    basic = next(
        item for item in definition.move_entries
        if str(item.entry_id).endswith(":basic-jab-1")
    )
    assert isinstance(basic.multiplier_variants[0].multiplier.value, Resolved)


def test_pulchra_cinema6_mark_rule_is_locked_by_cinema_and_extra_eligibility() -> None:
    raw = load_raw_record(load_character_record(str(PULCHRA_ID)))
    c6_ineligible_extra = compile_pulchra(
        PulchraCompileConfig(cinema_level=6, additional_ability_eligible=False), raw
    )
    rule = next(
        item
        for item in c6_ineligible_extra.rule_items
        if str(item.rule_id) == _C6_PURSUIT
    )
    assert rule.eligibility.value == "ineligible"
    assert not rule.effects

    c6_eligible_extra = compile_pulchra(
        PulchraCompileConfig(cinema_level=6, additional_ability_eligible=True), raw
    )
    rule = next(
        item
        for item in c6_eligible_extra.rule_items
        if str(item.rule_id) == _C6_PURSUIT
    )
    assert rule.eligibility.value != "ineligible"
    assert len(rule.effects) == 1

    c5_eligible_extra = compile_pulchra(
        PulchraCompileConfig(cinema_level=5, additional_ability_eligible=True), raw
    )
    rule = next(
        item
        for item in c5_eligible_extra.rule_items
        if str(item.rule_id) == _C6_PURSUIT
    )
    assert rule.eligibility.value == "ineligible"
    assert not rule.effects


def test_pulchra_cinema6_repeat_count_falls_back_cleanly_when_disabled() -> None:
    base = _calculate(
        _payload(
            "character:1351",
            _MAIN,
            enabled=(_NIGHTMARE_REPEAT_RULE, _EXTRA_ABILITY, _C6_NIGHTMARE),
            parameters={_NIGHTMARE_BASE_COUNT: 5, _C6_EXTRA_COUNT: 2},
            stacks={_EXTRA_ABILITY: 1, _C6_NIGHTMARE: 1},
        )
    )
    assert len(base["events"]) == 8  # main + six ordinary repeats + one finisher
    assert any("extra-7:finisher" in item["semantic_id"] for item in base["events"])

    c6_disabled = _calculate(
        _payload(
            "character:1351",
            _MAIN,
            enabled=(_NIGHTMARE_REPEAT_RULE,),
            parameters={_NIGHTMARE_BASE_COUNT: 5, _C6_EXTRA_COUNT: 2},
            stacks={_EXTRA_ABILITY: 1, _C6_NIGHTMARE: 1},
        )
    )
    assert len(c6_disabled["events"]) == 6  # main + four ordinary repeats + finisher
    assert any("extra-5:finisher" in item["semantic_id"] for item in c6_disabled["events"])
    assert not any("extra-6:" in item["semantic_id"] or "extra-7:" in item["semantic_id"] for item in c6_disabled["events"])
    assert _normal_bonus(_event(base, "nightmare-shadow-main")) == pytest.approx(0.15)
    assert _normal_bonus(_event(base, "nightmare-extra-7:finisher")) == pytest.approx(0.15)


def test_pulchra_pursuit_mark_and_hunter_step_are_separate_current_states() -> None:
    baseline = _calculate(_payload("character:1351", "move-entry:pulchra:1351:basic-jab-1", pulchra_cinema=1))
    marked = _calculate(
        _payload(
            "character:1351",
            "move-entry:pulchra:1351:basic-jab-1",
            pulchra_cinema=1,
            conditions={str(PULCHRA_PURSUIT_MARK_ACTIVE): True},
            enabled=(_C1_RULE,),
        )
    )
    marked_event = _event(marked, "basic-jab-1")
    baseline_event = _event(baseline, "basic-jab-1")
    assert _node(marked_event, "character.current.crit-rate") == pytest.approx(
        _node(baseline_event, "character.current.crit-rate") + 0.10
    )
    assert marked["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(
        baseline["resolved_character_snapshots"][0]["stats"]["crit_rate"]
    )

    hunter_unselected = _calculate(
        _payload("character:1351", "move-entry:pulchra:1351:basic-jab-1", pulchra_cinema=2)
    )
    hunter_selected = _calculate(
        _payload(
            "character:1351",
            "move-entry:pulchra:1351:basic-jab-1",
            pulchra_cinema=2,
            conditions={str(PULCHRA_HUNTER_STEP_ACTIVE): True},
            enabled=(_HUNTER_STEP_RULE,),
        )
    )
    assert hunter_selected["events"][0]["modes"]["expected"]["value"] > hunter_unselected["events"][0]["modes"]["expected"]["value"]

    # Manual-panel input is already the final out-of-combat value. Cinema 2
    # applies its separate combat-state increase once to that value.
    final_panel = _payload(
        "character:1351",
        "move-entry:pulchra:1351:basic-jab-1",
        pulchra_cinema=2,
        conditions={str(PULCHRA_HUNTER_STEP_ACTIVE): True},
        enabled=(_HUNTER_STEP_RULE,),
    )
    manual_build = final_panel["character_builds"]["character:1351"]
    manual_stats = _panel_stats("character:1351")
    manual_stats["attack"] = 1234.0
    manual_build.clear()
    manual_build.update(
        {
            "level": 60,
            "build_mode": "manual-panel",
            "out_of_combat_stats": manual_stats,
        }
    )
    manual_result = _calculate(final_panel)
    pulchra_snapshot = next(
        item
        for item in manual_result["resolved_character_snapshots"]
        if item["character_id"] == "character:1351"
    )
    assert pulchra_snapshot["stats"]["attack"] == pytest.approx(1234.0 * 1.10)


def test_pulchra_cinema6_mark_expansion_changes_real_jane_disorder_only_when_eligible() -> None:
    jane_disorder = "move-entry:character:1261:physical-disorder"
    team = ("character:1351", "character:1111")
    base = _calculate(_payload("character:1261", jane_disorder, supporting=team))
    marked = _calculate(
        _payload(
            "character:1261",
            jane_disorder,
            supporting=team,
            conditions={str(PULCHRA_PURSUIT_MARK_ACTIVE): True},
            enabled=(_EXTRA_ABILITY, _C6_PURSUIT),
            stacks={_EXTRA_ABILITY: 1, _C6_PURSUIT: 1},
        )
    )
    assert len(base["events"]) == len(marked["events"]) == 1
    assert _event(marked, "physical-disorder")["modes"]["expected"]["value"] == pytest.approx(
        _event(base, "physical-disorder")["modes"]["expected"]["value"] * 1.30
    )
    assert marked["totals"]["expected"]["complete"] is True

    extra_disabled = _calculate(
        _payload(
            "character:1261",
            jane_disorder,
            supporting=team,
            conditions={str(PULCHRA_PURSUIT_MARK_ACTIVE): True},
            enabled=(_C6_PURSUIT,),
            stacks={_EXTRA_ABILITY: 1, _C6_PURSUIT: 1},
        )
    )
    assert _event(extra_disabled, "physical-disorder")["modes"]["expected"]["value"] == pytest.approx(
        _event(base, "physical-disorder")["modes"]["expected"]["value"]
    )

    # Jane does not satisfy Pulchra's Attack/Rupture or same-faction Extra condition.
    ineligible = _calculate(
        _payload(
            "character:1261",
            jane_disorder,
            supporting=("character:1351",),
            conditions={str(PULCHRA_PURSUIT_MARK_ACTIVE): True},
            enabled=(_EXTRA_ABILITY, _C6_PURSUIT),
            stacks={_EXTRA_ABILITY: 1, _C6_PURSUIT: 1},
        )
    )
    assert _event(ineligible, "physical-disorder")["modes"]["expected"]["value"] == pytest.approx(
        _event(base, "physical-disorder")["modes"]["expected"]["value"]
    )

    # Cinema 6 locked at C5 cannot be forced on by an enabled-rule payload.
    locked = _calculate(
        _payload(
            "character:1261",
            jane_disorder,
            supporting=team,
            pulchra_cinema=5,
            conditions={str(PULCHRA_PURSUIT_MARK_ACTIVE): True},
            enabled=(_EXTRA_ABILITY, _C6_PURSUIT),
            stacks={_EXTRA_ABILITY: 1, _C6_PURSUIT: 1},
        )
    )
    assert _event(locked, "physical-disorder")["modes"]["expected"]["value"] == pytest.approx(
        _event(base, "physical-disorder")["modes"]["expected"]["value"]
    )


def test_pulchra_c6_nonfollow_bonus_does_not_double_followup_extra_bonus() -> None:
    result = _calculate(
        _payload(
            "character:1351",
            _MAIN,
            supporting=("character:1111",),
            conditions={str(PULCHRA_PURSUIT_MARK_ACTIVE): True},
            enabled=(
                _NIGHTMARE_REPEAT_RULE,
                _EXTRA_ABILITY,
                _C6_NIGHTMARE,
                _C6_PURSUIT,
            ),
            stacks={_EXTRA_ABILITY: 1, _C6_NIGHTMARE: 1, _C6_PURSUIT: 1},
            parameters={_NIGHTMARE_BASE_COUNT: 1, _C6_EXTRA_COUNT: 0},
        )
    )
    nightmare = _event(result, "nightmare-shadow-main")
    assert _normal_bonus(nightmare) == pytest.approx(0.45)
