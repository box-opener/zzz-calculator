from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.nekomata import (
    NEKOMATA_ID,
    NekomataCompileConfig,
    compile_nekomata,
    load_raw_record,
)
from core.application.equipment import compile_wengine, signature_wengine_id_for
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import (
    CalculationNode,
    CharacterId,
    CharacterRole,
    Element,
    Resolved,
    WEngineBuildInput,
    WEngineId,
)
from web.api import app


client = TestClient(app)


def _payload(
    move_entry_id: str,
    *,
    cinema_level: int = 0,
    core_level: int = 1,
    potential_level: int = 0,
    enemy_stunned: bool = False,
    conditions: dict[str, bool] | None = None,
    parameters: dict[str, int] | None = None,
    enabled: tuple[str, ...] = (),
    equipment_build: bool = False,
    supports: tuple[str, ...] = (),
) -> dict:
    team_ids = ["character:1021", *supports]
    owner_build = (
        {
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": "wengine:14102",
            "wengine_level": 60,
            "wengine_refinement": 1,
            "drive_discs": [],
        }
        if equipment_build
        else {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 7560.1902,
                "attack": 1000.0,
                "defense": 587.5794,
                "impact": 92.0,
                "crit_rate": 0.194,
                "crit_damage": 0.5,
                "anomaly_mastery": 97.0,
                "anomaly_proficiency": 96.0,
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"physical": 0.2},
            },
        }
    )
    builds = {"character:1021": owner_build}
    for character_id in supports:
        builds[character_id] = {
            "level": 60,
            "out_of_combat_stats": {
                "hp": 10000.0,
                "attack": 1000.0,
                "defense": 600.0,
                "impact": 100.0,
                "crit_rate": 0.2,
                "crit_damage": 0.5,
                "anomaly_mastery": 100.0,
                "anomaly_proficiency": 100.0,
                "energy_regen": 1.2,
                "penetration_rate": 0.0,
                "penetration_flat": 0.0,
                "element_damage_bonus": {"physical": 0.0},
            },
        }
    return {
        "primary_character_id": "character:1021",
        "supporting_character_ids": list(supports),
        "team_character_ids": team_ids,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            "character:1021": {
                "core_level": core_level,
                "cinema_level": cinema_level,
                "potential_level": potential_level,
            },
            **{
                character_id: {
                    "core_level": 1,
                    "cinema_level": 0,
                    "mingxin_active": False,
                    "entry_move_uses_linren": False,
                }
                for character_id in supports
            },
        },
        "condition_values": {
            "condition:nekomata:core-damage-buff-active": False,
            "condition:nekomata:back-hit-active": False,
            **(conditions or {}),
        },
        "parameter_values": parameters or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:nekomata-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": enemy_stunned,
        },
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
    }


def _node(event: dict, node: CalculationNode, mode: str = "expected") -> float:
    return next(
        row["value"]
        for row in event["modes"][mode]["calculation_breakdown"]
        if row["node"] == node.value
    )


def test_nekomata_live_baseline_raw_build_and_all_direct_sources_are_reviewed() -> None:
    raw_full = load_character_record(str(NEKOMATA_ID))
    raw = load_raw_record(raw_full)
    assert str(NEKOMATA_ID) in supported_character_ids()
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1021.json"
    assert raw.name == "猫又"
    assert raw.code_name == "Nekomata"
    assert raw.rarity == 4
    assert raw.specialty == "强攻"
    assert raw.element == "物理"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert len(raw.moves) == 12
    assert "potential_detail" in raw_full and len(raw_full["potential_detail"]) == 6
    assert raw_full["passive"]["level"]["1021508"]["potential"][0] == 102100
    assert "闪避反击：绒爪穿刺" not in {move.name for move in raw.moves}

    stats = character_base_stats(NEKOMATA_ID)
    assert stats.hp.value == pytest.approx(7560.1902)
    assert stats.attack.value == pytest.approx(910.5958)
    assert stats.defense.value == pytest.approx(587.5794)
    assert stats.impact == Resolved(92.0)
    assert stats.crit_rate == Resolved(0.194)
    assert stats.crit_damage == Resolved(0.5)
    assert stats.anomaly_proficiency == Resolved(96.0)
    assert stats.anomaly_mastery == Resolved(97.0)
    assert stats.energy_regen == Resolved(1.2)

    definition = compile_nekomata(NekomataCompileConfig(), raw)
    direct = [entry for entry in definition.move_entries if entry.skill_group is not None]
    assert len(direct) == 14
    assert all(entry.main_damage_event.element is Element.PHYSICAL for entry in direct)
    assert [entry.stage_index for entry in direct[:5]] == [1, 2, 3, 4, 5]
    multipliers = {entry.display_name: entry.multiplier_variants[0].multiplier.value.value for entry in direct}
    assert multipliers["普通攻击：猫猫爪刺（1段）"] == pytest.approx(1.113)
    assert multipliers["普通攻击：猫猫爪刺（5段）"] == pytest.approx(2.479)
    assert multipliers["普通攻击：赤色之刃"] == pytest.approx(1.444)
    assert multipliers["强化特殊技：超~凶奇袭！"] == pytest.approx(10.798)
    assert multipliers["终结技：刃爪强袭"] == pytest.approx(31.43)
    assert all(item.blocking is False for item in definition.diagnostics)


def test_nekomata_registry_defaults_and_signature_selection_are_s_rank_attack() -> None:
    registration = registration_for(NEKOMATA_ID)
    assert registration.role is CharacterRole.ATTACK
    assert registration.base_element is Element.PHYSICAL
    assert registration.catalog.rarity == "S"
    assert registration.catalog.element == "physical"
    assert registration.catalog.specialty == "attack"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert signature_wengine_id_for(NEKOMATA_ID) == "wengine:14102"
    catalog_row = next(
        item for item in client.get("/api/v1/characters").json()
        if item["character_id"] == "character:1021"
    )
    assert catalog_row["rarity"] == "S"
    engine_row = next(
        item for item in client.get("/api/v1/wengines").json()
        if item["wengine_id"] == "wengine:14102"
    )
    assert engine_row["signature_character_id"] == "character:1021"

    fields = {item.field_id: item for item in config_fields_for(NEKOMATA_ID, {}, [NEKOMATA_ID])}
    assert fields["core_level"].value == 7
    assert fields["core_level"].field_type == "slider"
    assert fields["cinema_level"].value == 0
    assert fields["cinema_level"].field_type == "slider"
    assert fields["potential_level"].field_type == "slider"
    assert fields["potential_level"].value == 0
    assert fields["potential_level"].minimum == 0
    assert fields["potential_level"].maximum == 6
    assert {key: fields[key].value for key in fields if key.startswith("skill_level:")} == {
        "skill_level:basic-attack": 12,
        "skill_level:dodge": 12,
        "skill_level:special-attack": 12,
        "skill_level:chain-attack": 12,
        "skill_level:assist": 12,
        "skill_level:ultimate": 12,
    }
    definition = compile_registered_definition(
        NEKOMATA_ID,
        {"core_level": 7, "cinema_level": 6},
        [NEKOMATA_ID],
        strict=False,
    )
    assert len(definition.move_entries) == 16


def test_nekomata_stack_parameters_default_full_and_keep_zero_or_partial_selection() -> None:
    definition = compile_nekomata(
        NekomataCompileConfig(cinema_level=6),
        load_raw_record(load_character_record(str(NEKOMATA_ID))),
    )
    defaults = {str(item.parameter_id): item.value for item in definition.scenario_parameters}
    assert defaults["parameter:nekomata:extra-ability-ex-damage-stacks"] == 2
    assert defaults["parameter:nekomata:cinema4-crit-rate-stacks"] == 2
    assert defaults["parameter:nekomata:cinema6-crit-damage-stacks"] == 3

    enabled = (
        "rule:character:1021:cinema4:current-crit-rate-stacks",
        "rule:character:1021:cinema6:current-crit-damage-stacks",
    )
    def panel(parameters):
        response = client.post(
            "/api/v1/moves/calculate",
            json=_payload(
                "move-entry:character:1021:ex-special-super-ferocious-ambush",
                cinema_level=6,
                parameters=parameters,
                enabled=enabled,
            ),
        )
        assert response.status_code == 200, response.text
        return next(
            item["stats"]
            for item in response.json()["resolved_character_snapshots"]
            if item["character_id"] == "character:1021"
        )

    maximum = panel({})
    zero = panel(
        {
            "parameter:nekomata:cinema4-crit-rate-stacks": 0,
            "parameter:nekomata:cinema6-crit-damage-stacks": 0,
        }
    )
    middle = panel(
        {
            "parameter:nekomata:cinema4-crit-rate-stacks": 1,
            "parameter:nekomata:cinema6-crit-damage-stacks": 2,
        }
    )
    assert (maximum["crit_rate"], maximum["crit_damage"]) == pytest.approx((0.334, 1.04))
    assert (zero["crit_rate"], zero["crit_damage"]) == pytest.approx((0.194, 0.5))
    assert (middle["crit_rate"], middle["crit_damage"]) == pytest.approx((0.264, 0.86))


def test_nekomata_real_payload_applies_core_cinema_panels_and_c1_enemy_stun_once() -> None:
    payload = _payload(
        "move-entry:character:1021:ex-special-super-ferocious-ambush",
        core_level=7,
        cinema_level=6,
        conditions={
            "condition:nekomata:core-damage-buff-active": True,
            "condition:nekomata:back-hit-active": True,
        },
        parameters={
            "parameter:nekomata:cinema4-crit-rate-stacks": 2,
            "parameter:nekomata:cinema6-crit-damage-stacks": 3,
        },
        enabled=(
            "rule:character:1021:core:current-damage-buff",
            "rule:character:1021:cinema1:back-hit-physical-resistance-ignore",
            "rule:character:1021:cinema1:stunned-target-physical-resistance-ignore",
            "rule:character:1021:cinema4:current-crit-rate-stacks",
            "rule:character:1021:cinema6:current-crit-damage-stacks",
        ),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    event = result["events"][0]
    # The selected S-rank Cinema 6 build receives the +2 Basic/Special/Chain
    # skill-level bonuses from Cinema 3 and Cinema 5, so this EX curve is Lv16.
    assert _node(event, CalculationNode.DAMAGE_SKILL_MULTIPLIER) == pytest.approx(12.762)
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS) == pytest.approx(0.6)
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS_REGION) == pytest.approx(1.8)
    assert _node(event, CalculationNode.DAMAGE_RESISTANCE_IGNORE) == pytest.approx(0.16)
    nekomata = next(item for item in result["resolved_character_snapshots"] if item["character_id"] == "character:1021")
    assert nekomata["stats"]["crit_rate"] == pytest.approx(0.334)
    assert nekomata["stats"]["crit_damage"] == pytest.approx(1.04)

    payload["enemy"]["is_stunned"] = True
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    stunned_event = response.json()["events"][0]
    # C1's ordinary back-hit route is excluded once the target state implies
    # back hits, so the same 16% is never applied twice.
    assert _node(stunned_event, CalculationNode.DAMAGE_RESISTANCE_IGNORE) == pytest.approx(0.16)


def test_nekomata_random_baseline_is_omitted_but_potential_stun_repeats_are_deterministic() -> None:
    baseline = client.post(
        "/api/v1/moves/calculate",
        json=_payload("move-entry:character:1021:basic-cat-claw-5"),
    )
    assert baseline.status_code == 200, baseline.text
    baseline_result = baseline.json()
    assert baseline_result["totals"]["expected"]["complete"] is True
    assert len(baseline_result["events"]) == 1
    assert baseline_result["events"][0]["repeat_count"] == 1

    repeat_rule_ids = (
        "rule:character:1021:potential:basic-cat-claw-final-stun-repeat",
        "rule:character:1021:potential:basic-red-blade-stun-repeat",
    )
    for entry_id, rule_id in (
        ("move-entry:character:1021:basic-cat-claw-5", repeat_rule_ids[0]),
        ("move-entry:character:1021:basic-red-blade", repeat_rule_ids[1]),
    ):
        for stunned, expected_events in ((False, 1), (True, 2)):
            response = client.post(
                "/api/v1/moves/calculate",
                json=_payload(
                    entry_id,
                    potential_level=1,
                    enemy_stunned=stunned,
                    enabled=(rule_id,),
                ),
            )
            assert response.status_code == 200, response.text
            result = response.json()
            assert result["totals"]["expected"]["complete"] is True
            assert len(result["events"]) == expected_events
            assert sum(item["repeat_count"] for item in result["events"]) == (
                3 if stunned else 1
            )
            assert result["totals"]["expected"]["value"] > 0


def test_nekomata_potential_slider_selects_source_moves_and_pounce_stats() -> None:
    raw_full = load_character_record(str(NEKOMATA_ID))
    for potential_level in range(7):
        raw = load_raw_record(raw_full, potential_level=potential_level)
        definition = compile_nekomata(
            NekomataCompileConfig(potential_level=potential_level), raw
        )
        names = {entry.display_name for entry in definition.move_entries}
        assert ("潜能解锁：闪避反击：绒爪穿刺" in names) is (potential_level > 0)
        assert raw.core_levels[0].source_id == (
            "1021501" if potential_level == 0 else "1021508"
        )
        crit_rule = next(
            (
                item
                for item in definition.rule_items
                if str(item.rule_id)
                == "rule:character:1021:potential:pounce-crit-damage"
            ),
            None,
        )
        assert (crit_rule is not None) is (potential_level >= 2)

    for potential_level, expected_bonus in ((2, 0.20), (3, 0.30), (4, 0.40), (5, 0.50), (6, 0.60)):
        response = client.post(
            "/api/v1/moves/calculate",
            json=_payload(
                "move-entry:character:1021:basic-cat-claw-1",
                potential_level=potential_level,
                conditions={"condition:nekomata:potential-pounce-active": True},
                enabled=("rule:character:1021:potential:pounce-crit-damage",),
            ),
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["totals"]["expected"]["complete"] is True
        snapshot = next(
            item
            for item in result["resolved_character_snapshots"]
            if item["character_id"] == "character:1021"
        )
        assert snapshot["stats"]["crit_damage"] == pytest.approx(0.5 + expected_bonus)

    unlocked_move = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1021:potential-dodge-counter-fluffy-claw",
            potential_level=1,
        ),
    )
    assert unlocked_move.status_code == 200, unlocked_move.text
    assert unlocked_move.json()["totals"]["expected"]["complete"] is True
    assert _node(unlocked_move.json()["events"][0], CalculationNode.DAMAGE_SKILL_MULTIPLIER) == pytest.approx(25.278)


def test_nekomata_potential_pounce_mark_is_one_owner_physical_direct_child() -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1021:basic-cat-claw-1",
            potential_level=1,
            conditions={"condition:nekomata:potential-pounce-active": True},
            enabled=("rule:character:1021:potential:super-furry-mark",),
        ),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 2
    mark = next(item for item in result["events"] if "超凶爪印" in item["label"])
    assert mark["repeat_count"] == 1
    assert _node(mark, CalculationNode.DAMAGE_SKILL_MULTIPLIER) == pytest.approx(0.30)
    assert _node(mark, CalculationNode.DAMAGE_BASE_VALUE) == pytest.approx(300.0)

    definition = compile_registered_definition(
        NEKOMATA_ID,
        {"core_level": 1, "cinema_level": 0, "potential_level": 1},
        [NEKOMATA_ID],
        strict=False,
    )
    mark_template = next(
        item for item in definition.damage_event_templates if "super-furry-mark" in str(item.ref.template_id)
    )
    assert mark_template.element is Element.PHYSICAL
    assert mark_template.move_id is None


def test_nekomata_potential_mark_is_selectable_without_recursive_mark_child() -> None:
    response = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1021:potential-super-furry-mark",
            potential_level=1,
            conditions={"condition:nekomata:potential-pounce-active": True},
            enabled=("rule:character:1021:potential:super-furry-mark",),
        ),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert len(result["events"]) == 1
    mark = result["events"][0]
    assert mark["semantic_id"] == "event:character:1021:potential:super-furry-mark"
    assert mark["damage_type"] == "direct"
    assert _node(mark, CalculationNode.DAMAGE_SKILL_MULTIPLIER) == pytest.approx(0.30)
    assert _node(mark, CalculationNode.DAMAGE_BASE_VALUE) == pytest.approx(300.0)
    definition = compile_registered_definition(
        NEKOMATA_ID,
        {"core_level": 1, "cinema_level": 0, "potential_level": 1},
        [NEKOMATA_ID],
        strict=False,
    )
    entry = next(
        item for item in definition.move_entries
        if str(item.entry_id) == "move-entry:character:1021:potential-super-furry-mark"
    )
    assert entry.move_id is None
    assert entry.skill_group is None
    assert entry.damage_tags == frozenset()


def test_nekomata_additional_ability_uses_current_explicit_stacks_and_real_roster_gate() -> None:
    definition = compile_registered_definition(
        NEKOMATA_ID,
        {"core_level": 1, "cinema_level": 0},
        [NEKOMATA_ID, CharacterId("character:1431")],
        strict=False,
    )
    extra = next(item for item in definition.rule_items if str(item.rule_id) == "rule:character:1021:extra-ability:ex-current-stacks")
    assert extra.eligibility.value == "eligible"

    payload = _payload(
        "move-entry:character:1021:ex-special-super-ferocious-ambush",
        parameters={"parameter:nekomata:extra-ability-ex-damage-stacks": 2},
        enabled=("rule:character:1021:extra-ability:ex-current-stacks",),
        supports=("character:1431",),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    event = response.json()["events"][0]
    assert response.json()["totals"]["expected"]["complete"] is True
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS) == pytest.approx(0.7)
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS_REGION) == pytest.approx(1.9)


def test_nekomata_signature_build_has_catalog_and_live_refinement_source() -> None:
    payload = _payload(
        "move-entry:character:1021:basic-cat-claw-1",
        cinema_level=0,
        equipment_build=True,
        conditions={
            "condition:wengine:14102:owner:1021:back-attack-active": True,
        },
        enabled=(
            "rule:wengine:14102:owner:1021:physical-damage",
            "rule:wengine:14102:owner:1021:back-attack-damage",
        ),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    snapshot = next(item for item in result["resolved_character_snapshots"] if item["character_id"] == "character:1021")
    assert snapshot["stats"]["crit_rate"] > 0.194
    assert _node(result["events"][0], CalculationNode.DAMAGE_NORMAL_BONUS_REGION) == pytest.approx(1.45)


def test_nekomata_c1_stun_automatically_counts_as_steel_cushion_back_hit_once() -> None:
    automatic_rule = (
        "rule:wengine:14102:owner:1021:nekomata-c1-stunned-target-back-attack-damage"
    )
    for cinema, stunned, manual_back_hit, expected_region in (
        (1, True, False, 1.45),
        (1, True, True, 1.45),
        (1, False, False, 1.20),
        (1, False, True, 1.45),
        (0, True, False, 1.20),
    ):
        enabled = [
            "rule:wengine:14102:owner:1021:physical-damage",
            "rule:wengine:14102:owner:1021:back-attack-damage",
        ]
        if cinema >= 1:
            enabled.append(automatic_rule)
        response = client.post(
            "/api/v1/moves/calculate",
            json=_payload(
                "move-entry:character:1021:basic-cat-claw-1",
                cinema_level=cinema,
                equipment_build=True,
                enemy_stunned=stunned,
                conditions={
                    "condition:wengine:14102:owner:1021:back-attack-active": manual_back_hit,
                },
                enabled=tuple(enabled),
            ),
        )
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["totals"]["expected"]["complete"] is True
        assert _node(result["events"][0], CalculationNode.DAMAGE_NORMAL_BONUS_REGION) == pytest.approx(expected_region)

    ye_id = CharacterId("character:1431")
    ye_wengine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14102"), ye_id),
        owner_capabilities=registration_for(ye_id).equipment_capabilities,
    )
    assert not any(
        "nekomata-c1-stunned-target-back-attack-damage" in str(item.rule_id)
        for item in ye_wengine.rule_items
    )


def test_nekomata_physical_assault_and_disorder_use_static_nocrit_records() -> None:
    anomaly_response = client.post(
        "/api/v1/moves/calculate",
        json=_payload(
            "move-entry:character:1021:physical-anomaly",
            cinema_level=1,
            conditions={"condition:nekomata:back-hit-active": True},
            enabled=("rule:character:1021:cinema1:back-hit-physical-resistance-ignore",),
        ),
    )
    assert anomaly_response.status_code == 200, anomaly_response.text
    anomaly = anomaly_response.json()
    assert anomaly["totals"]["expected"]["complete"] is True
    anomaly_event = anomaly["events"][0]
    assert anomaly_event["damage_type"] == "anomaly"
    assert anomaly_event["damage_subtype"] == "attribute-anomaly"
    assert anomaly_event["crit_capability"] == "none"
    # Cinema 1 describes a rear-position attack hit; a separately settled
    # physical Anomaly record is not itself such an attack hit.
    assert _node(anomaly_event, CalculationNode.DAMAGE_RESISTANCE_IGNORE) == pytest.approx(0.0)
    assert _node(anomaly_event, CalculationNode.ANOMALY_EFFECT_STRENGTH) == pytest.approx(2304.0)
    assert _node(anomaly_event, CalculationNode.ATTRIBUTE_ANOMALY_MULTIPLIER) == pytest.approx(7.13)
    assert len({row["value"] for row in anomaly_event["modes"].values()}) == 1

    disorder_response = client.post(
        "/api/v1/moves/calculate",
        json=_payload("move-entry:character:1021:physical-disorder"),
    )
    assert disorder_response.status_code == 200, disorder_response.text
    disorder = disorder_response.json()
    assert disorder["totals"]["expected"]["complete"] is True
    disorder_event = disorder["events"][0]
    assert disorder_event["damage_type"] == "disorder"
    assert disorder_event["crit_capability"] == "none"
    assert _node(disorder_event, CalculationNode.DISORDER_TOTAL_MULTIPLIER) == pytest.approx(5.25)
    assert len({row["value"] for row in disorder_event["modes"].values()}) == 1
