from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.jane_doe import (
    JANE_DOE_ID,
    JaneDoeCompileConfig,
    compile_jane_doe,
    load_raw_record,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
    load_wengine_raw_record,
)
from core.application.moves import MultiplierRelation
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import registration_for
from core.types import CharacterId, DamageTag, SkillGroup, WEngineBuildInput, WEngineId
from web.api import app


client = TestClient(app)


def _stats(character_id: CharacterId) -> dict[str, object]:
    panel = character_base_stats(character_id)
    return {
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


def _payload(
    move_entry_id: str,
    *,
    primary: str = "character:1261",
    supporting: tuple[str, ...] = (),
    cinema: int = 0,
    potential: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    stats_overrides: dict[str, dict[str, object]] | None = None,
    burnice_source: dict[str, str] | None = None,
) -> dict[str, object]:
    team = [primary, *supporting]
    configs: dict[str, dict[str, int]] = {}
    for character_id in team:
        if character_id == "character:1261":
            configs[character_id] = {
                "core_level": 7,
                "cinema_level": cinema,
                "potential_level": potential,
            }
        elif character_id == "character:1021":
            configs[character_id] = {
                "core_level": 7,
                "cinema_level": 0,
                "potential_level": 0,
            }
        elif character_id == "character:1171":
            configs[character_id] = {
                "core_level": 7,
                "cinema_level": 0,
                "potential_level": 0,
            }
        else:
            configs[character_id] = {"core_level": 7, "cinema_level": 0}
    builds = {}
    for character_id in team:
        stats = _stats(CharacterId(character_id))
        if stats_overrides and character_id in stats_overrides:
            stats.update(stats_overrides[character_id])
        builds[character_id] = {"level": 60, "out_of_combat_stats": stats}
    payload = {
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
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:jane-doe-test",
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
    if burnice_source is not None:
        payload["burnice_anomaly_source"] = burnice_source
    return payload


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _breakdown(event: dict[str, object]) -> dict[str, float]:
    return {
        item["node"]: item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
    }


def test_jane_doe_source_panel_potential_defaults_and_signature() -> None:
    source = load_raw_record(load_character_record(str(JANE_DOE_ID)))
    assert source.name == "简"
    assert source.code_name == "Jane"
    assert source.rarity == 4
    assert source.specialty == "异常"
    assert source.element == "物理"
    assert source.faction == "新艾利都治安局"
    assert source.source_version == "3.2"
    assert source.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1261.json"
    assert str(JANE_DOE_ID) in supported_character_ids()

    panel = character_base_stats(JANE_DOE_ID)
    assert panel.attack.value == pytest.approx(880.6952)
    assert panel.hp.value == pytest.approx(7788.6961)
    assert panel.defense.value == pytest.approx(606.5977)
    assert panel.impact.value == pytest.approx(86.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(114.0)
    assert panel.anomaly_mastery.value == pytest.approx(148.0)

    config = JaneDoeCompileConfig()
    assert config.core_level == 7
    assert config.cinema_level == 0
    assert config.potential_level == 0
    assert config.skill_level_for(SkillGroup.ULTIMATE) == 12
    registration = registration_for(JANE_DOE_ID)
    assert registration.catalog.rarity == "S"
    assert registration.catalog.code_name == "Jane"
    editor_defaults = {
        item.field_id: item.value
        for item in registration.config_fields({}, (JANE_DOE_ID,))
    }
    assert editor_defaults["core_level"] == 7
    assert editor_defaults["cinema_level"] == 0
    assert editor_defaults["potential_level"] == 0
    assert all(
        editor_defaults[f"skill_level:{group}"] == 12
        for group in (
            "basic-attack",
            "dodge",
            "special-attack",
            "chain-attack",
            "assist",
            "ultimate",
        )
    )

    assert SIGNATURE_WENGINE_BY_CHARACTER[JANE_DOE_ID] == WEngineId("wengine:14126")
    weapon = load_wengine_raw_record("wengine:14126")
    assert weapon.icon == "Weapon_S_1261"
    engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14126"), JANE_DOE_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert engine.complete is True
    assert engine.contributions[0].value.value == pytest.approx(713.0)
    assert engine.contributions[1].value.value == pytest.approx(90.0)


def test_jane_doe_direct_curves_and_potential_sahoff_source_variant() -> None:
    raw = load_raw_record(load_character_record(str(JANE_DOE_ID)))
    p0 = compile_jane_doe(JaneDoeCompileConfig(), raw)
    p1 = compile_jane_doe(JaneDoeCompileConfig(potential_level=1), raw)
    p0_entries = {str(item.entry_id): item for item in p0.move_entries}
    p1_entries = {str(item.entry_id): item for item in p1.move_entries}
    expected = {
        "basic-footwork-1": 0.724,
        "basic-footwork-2": 1.250,
        "basic-footwork-3": 1.671,
        "basic-footwork-4": 3.273,
        "basic-footwork-5": 1.978,
        "basic-footwork-6": 5.828,
        "sahoff-jump-continuous": 6.022,
        "sahoff-jump-finisher": 3.230,
        "dash-blade-hop-first-dodge": 1.430,
        "dash-blade-hop-second-dodge": 1.430,
        "dash-phantom-thrust": 2.090,
        "dodge-counter-shadow-first-dodge": 6.833,
        "dodge-counter-shadow-second-dodge": 6.833,
        "dodge-counter-shadow-dance": 7.742,
        "special-skybreaker": 1.161,
        "ex-skybreaker-sweep": 11.500,
        "ex-skybreaker-rush": 11.902,
        "chain-sins-in-bloom": 12.662,
        "ultimate-final-act": 29.413,
        "quick-assist-barb": 2.391,
        "quick-assist-hook-jump": 2.750,
        "assist-strike-gale-sweep": 6.920,
    }
    for key, ratio in expected.items():
        entry = p0_entries[f"move-entry:character:1261:{key}"]
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(ratio)
    assert p1_entries[
        "move-entry:character:1261:sahoff-jump-continuous"
    ].multiplier_variants[0].multiplier.value.value == pytest.approx(9.650)
    assert p0_entries[
        "move-entry:character:1261:sahoff-jump-full"
    ].multiplier_variants[0].multiplier.value.value == pytest.approx(9.252)
    assert p1_entries[
        "move-entry:character:1261:sahoff-jump-full"
    ].multiplier_variants[0].multiplier.value.value == pytest.approx(12.880)
    assert p0_entries[
        "move-entry:character:1261:basic-footwork-6"
    ].damage_tags == frozenset({DamageTag.BASIC_ATTACK, DamageTag.DASH_ATTACK})


def test_jane_doe_bite_gates_her_anomaly_crit_and_cinema2_scope() -> None:
    core_crit = "rule:character:1261:core:gnawing-strong-anomaly-crit"
    bite = "condition:jane-doe:gnawing-active"
    strong = "move-entry:character:1261:physical-assault"
    with_bite = _calculate(
        _payload(strong, conditions={bite: True}, enabled=(core_crit,))
    )
    assert len(with_bite["events"]) == 1
    assert _breakdown(with_bite["events"][0])["anomaly.attribute.crit-region"] == pytest.approx(1.2912)

    without_bite = _calculate(_payload(strong, enabled=(core_crit,)))
    assert len(without_bite["events"]) == 1
    assert _breakdown(without_bite["events"][0])["anomaly.attribute.crit-region"] == pytest.approx(1.0)

    disorder = _calculate(
        _payload(strong.replace("physical-assault", "physical-disorder"), conditions={bite: True}, enabled=(core_crit,))
    )
    assert len(disorder["events"]) == 1
    assert disorder["events"][0]["crit_capability"] == "none"

    c2_anomaly = _calculate(
        _payload(
            "move-entry:character:1261:physical-assault",
            cinema=2,
            conditions={bite: True},
            enabled=(
                core_crit,
                "rule:character:1261:cinema2:gnawing-target-defense-ignore",
            ),
        )
    )
    assert _breakdown(c2_anomaly["events"][0])["anomaly.attribute.crit-region"] == pytest.approx(1.5824)
    assert _breakdown(c2_anomaly["events"][0])["defense.damage-ignore"] == pytest.approx(0.15)

    c2 = _calculate(
        _payload(
            "move-entry:character:1261:basic-footwork-1",
            cinema=2,
            conditions={bite: True},
            enabled=("rule:character:1261:cinema2:gnawing-target-defense-ignore",),
        )
    )
    assert _breakdown(c2["events"][0])["defense.damage-ignore"] == pytest.approx(0.15)

    peer_direct_payload = _payload(
        "move-entry:character:1021:basic-cat-claw-1",
        primary="character:1021",
        supporting=("character:1261",),
        conditions={bite: True},
        enabled=("rule:character:1261:cinema2:gnawing-target-defense-ignore",),
    )
    peer_direct_payload["compile_configs"]["character:1261"]["cinema_level"] = 2
    peer_direct = _calculate(peer_direct_payload)
    assert _breakdown(peer_direct["events"][0]).get("defense.damage-ignore", 0.0) == pytest.approx(0.0)


def test_jane_doe_current_frenzy_ap_attack_and_cinema1_bonus() -> None:
    attack_rule = "rule:character:1261:core:frenzy-ap-to-attack"
    c1_bonus_rule = "rule:character:1261:cinema1:frenzy-ap-damage-bonus"
    payload = _payload(
        "move-entry:character:1261:basic-footwork-1",
        cinema=1,
        conditions={"condition:jane-doe:frenzy-active": True},
        enabled=(attack_rule, c1_bonus_rule),
        stats_overrides={"character:1261": {"anomaly_proficiency": 151.0}},
    )
    result = _calculate(payload)
    jane_snapshot = next(
        item
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == "character:1261"
    )
    assert jane_snapshot["stats"]["attack"] == pytest.approx(942.6952)
    assert _breakdown(result["events"][0])["damage.normal-bonus"] == pytest.approx(0.151)


def test_jane_doe_cinema4_anomaly_bonus_is_captured_in_the_record() -> None:
    result = _calculate(
        _payload(
            "move-entry:character:1261:physical-assault",
            cinema=4,
            conditions={"condition:jane-doe:cinema4-anomaly-bonus-active": True},
            enabled=("rule:character:1261:cinema4:team-anomaly-damage-bonus",),
        )
    )
    assert _breakdown(result["events"][0])["anomaly.attribute.damage-bonus-region"] == pytest.approx(1.18)


def test_jane_doe_core_bite_crit_uses_jane_ap_for_teammate_physical_source() -> None:
    result = _calculate(
        _payload(
            "move-entry:character:1021:physical-anomaly",
            primary="character:1021",
            supporting=("character:1261",),
            conditions={"condition:jane-doe:gnawing-active": True},
            enabled=("rule:character:1261:core:gnawing-strong-anomaly-crit",),
            stats_overrides={"character:1261": {"anomaly_proficiency": 200.0}},
        )
    )
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["crit_capability"] == "anomaly-independent"
    assert _breakdown(event)["anomaly.attribute.crit-region"] == pytest.approx(1.36)
    trace = event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["character_id"] == "character:1021"
    assert trace["anomaly_proficiency"] == pytest.approx(96.0)


def test_jane_doe_strong_crit_record_flows_to_teammate_discharge() -> None:
    payload = _payload(
        "move-entry:character:1171:special-throw",
        primary="character:1171",
        supporting=("character:1021", "character:1261"),
        conditions={"condition:jane-doe:gnawing-active": True},
        enabled=(
            "rule:character:1261:core:gnawing-strong-anomaly-crit",
            "rule:character:1171:potential1:special-throw-discharge",
        ),
        stats_overrides={"character:1261": {"anomaly_proficiency": 200.0}},
        burnice_source={"source_character_id": "character:1021", "element": "physical"},
    )
    payload["compile_configs"]["character:1171"]["potential_level"] = 1
    result = _calculate(payload)
    discharge = next(
        event for event in result["events"] if event["damage_subtype"] == "discharge"
    )
    assert discharge["crit_capability"] == "anomaly-independent"
    assert _breakdown(discharge)["anomaly.discharge.crit-region"] == pytest.approx(1.36)


def test_jane_doe_cinema_six_extra_attack_remains_local_without_fake_event() -> None:
    raw = load_raw_record(load_character_record(str(JANE_DOE_ID)))
    definition = compile_jane_doe(JaneDoeCompileConfig(cinema_level=6), raw)
    entry_id = "move-entry:character:1261:cinema6-extra-assault-identity-unresolved"
    entry = next(item for item in definition.move_entries if str(item.entry_id) == entry_id)
    assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(16.0)
    standalone = _calculate(_payload(entry_id, cinema=6))
    assert standalone["events"] == []
    assert standalone["totals"]["expected"]["complete"] is False

    parent = _calculate(
        _payload(
            "move-entry:character:1261:physical-assault",
            cinema=6,
            conditions={
                "condition:jane-doe:cinema6-assault-crit-triggered": True,
                "condition:jane-doe:gnawing-active": True,
            },
            enabled=("rule:character:1261:cinema6:strong-crit-extra-attack-identity-unresolved",),
        )
    )
    assert len(parent["events"]) == 1
    assert parent["totals"]["expected"]["complete"] is False
