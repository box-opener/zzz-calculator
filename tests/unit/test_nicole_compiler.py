from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters import CharacterSkillLevel
from core.application.characters.nicole import (
    NICOLE_ID,
    NicoleCompileConfig,
    compile_nicole,
    load_raw_record,
)
from core.application.equipment import signature_wengine_id_for
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import CalculationNode, CharacterId, CharacterRole, DamageType, Element, Resolved, SkillGroup
from web.api import app


client = TestClient(app)
_SKILL_GROUPS = (
    "basic-attack",
    "dodge",
    "special-attack",
    "chain-attack",
    "assist",
    "ultimate",
)


def _skills(level: int = 12) -> dict[str, int]:
    return {group: level for group in _SKILL_GROUPS}


def _stats(*, ether: float = 0.0) -> dict[str, object]:
    return {
        "hp": 8145.8433,
        "attack": 1000.0,
        "defense": 622.6159,
        "impact": 88.0,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "anomaly_mastery": 90.0,
        "anomaly_proficiency": 93.0,
        "energy_regen": 1.56,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"ether": ether, "physical": 0.0},
    }


def _payload(
    move_entry_id: str,
    *,
    core_level: int = 1,
    cinema_level: int = 0,
    supports: tuple[str, ...] = (),
    conditions: dict[str, bool] | None = None,
    parameters: dict[str, int] | None = None,
    enabled: tuple[str, ...] = (),
    skill_level: int = 12,
    equipment_builds: dict[str, dict] | None = None,
) -> dict:
    team_ids = ["character:1031", *supports]
    compile_configs: dict[str, dict] = {
        "character:1031": {
            "core_level": core_level,
            "cinema_level": cinema_level,
            "skill_levels": _skills(skill_level),
        }
    }
    builds: dict[str, dict] = {
        "character:1031": {
            "level": 60,
            "out_of_combat_stats": _stats(),
        }
    }
    for character_id in supports:
        if character_id == "character:1031":
            continue
        compile_configs[character_id] = {"core_level": 1, "cinema_level": 0}
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
                "element_damage_bonus": {"ether": 0.0, "physical": 0.0},
            },
        }
    for character_id, build in (equipment_builds or {}).items():
        builds[character_id] = build
    return {
        "primary_character_id": "character:1031",
        "supporting_character_ids": list(supports),
        "team_character_ids": team_ids,
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": {
            "condition:nicole:enhanced-ammo-active": False,
            "condition:nicole:core-defense-down-active": False,
            "condition:nicole:ex-charged-hit-occurred": False,
            "condition:nicole:ex-energy-field-hit-occurred": False,
            "condition:nicole:chain-energy-field-hit-occurred": False,
            "condition:nicole:ultimate-energy-field-hit-occurred": False,
            "condition:nicole:cinema6-target-crit-active": False,
            **(conditions or {}),
        },
        "parameter_values": parameters or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:nicole-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"ether": 0.2, "physical": 0.2},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
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


def test_nicole_live_raw_base_stats_and_formula_curves_are_complete() -> None:
    raw_data = load_character_record(str(NICOLE_ID))
    raw = load_raw_record(raw_data)
    assert str(NICOLE_ID) in supported_character_ids()
    assert raw_data["source_version"] == raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1031.json"
    assert raw.name == "妮可"
    assert raw.code_name == "Nicole"
    assert raw.rarity == 3
    assert raw.specialty == "支援"
    assert raw.element == "以太"
    assert raw.faction == "狡兔屋"
    assert not raw_data["potential"] and not raw_data["potential_detail"]
    assert len(raw.core_levels) == 7 and len(raw.mindscapes) == 6

    stats = character_base_stats(NICOLE_ID)
    assert stats.hp.value == pytest.approx(8145.8433)
    assert stats.attack.value == pytest.approx(649.1691)
    assert stats.defense.value == pytest.approx(622.6159)
    assert stats.impact == Resolved(88.0)
    assert stats.crit_rate == Resolved(0.05)
    assert stats.crit_damage == Resolved(0.5)
    assert stats.anomaly_mastery == Resolved(90.0)
    assert stats.anomaly_proficiency == Resolved(93.0)
    assert stats.energy_regen == Resolved(1.56)

    level12 = tuple(CharacterSkillLevel(group, 12) for group in (
        SkillGroup.BASIC_ATTACK,
        SkillGroup.DODGE,
        SkillGroup.SPECIAL_ATTACK,
        SkillGroup.CHAIN_ATTACK,
        SkillGroup.ASSIST,
        SkillGroup.ULTIMATE,
    ))
    definition = compile_nicole(
        NicoleCompileConfig(core_level=1, cinema_level=0, skill_levels=level12),
        raw,
    )
    direct = {entry.display_name: entry for entry in definition.move_entries if entry.skill_group is not None}
    assert len(direct) == 16
    expected = {
        "普通攻击：狡兔连打（一段）": 1.331,
        "普通攻击：狡兔连打（二段）": 1.44,
        "普通攻击：狡兔连打（三段）": 6.094,
        "普通攻击：为所欲为（一段强化弹）": 1.774,
        "普通攻击：为所欲为（二段强化弹）": 2.034,
        "普通攻击：为所欲为（三段强化弹）": 9.076,
        "冲刺攻击：惊喜开箱（前闪）": 3.18,
        "冲刺攻击：惊喜开箱（后闪）": 1.205,
        "冲刺攻击：为所欲为（前闪强化弹）": 3.18,
        "闪避反击：牵制炮击": 3.65,
        "特殊技：糖衣炮弹": 1.054,
        "强化特殊技：夹心糖衣炮弹（炮击）": 4.306,
        "连携技：高价以太爆弹（炮击）": 4.208,
        "终结技：特制以太榴弹（炮击）": 12.936,
        "快速支援：救急炮击": 1.272,
        "支援突击：趁虚而入": 7.544,
    }
    for label, multiplier in expected.items():
        assert direct[label].multiplier_variants[0].multiplier.value.value == pytest.approx(multiplier)
    assert [direct[f"普通攻击：为所欲为（{stage}段强化弹）"].condition_ids for stage in ("一", "二", "三")] == [
        ("condition:nicole:enhanced-ammo-active",),
        ("condition:nicole:enhanced-ammo-active",),
        ("condition:nicole:enhanced-ammo-active",),
    ]


def test_nicole_registered_a_rank_defaults_signature_and_v2_catalog() -> None:
    registration = registration_for(NICOLE_ID)
    assert registration.role is CharacterRole.SUPPORT
    assert registration.base_element is Element.ETHER
    assert registration.catalog.rarity == "A"
    assert registration.catalog.specialty == "support"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert signature_wengine_id_for(NICOLE_ID) == "wengine:13103"

    character_row = next(
        row for row in client.get("/api/v1/characters").json()
        if row["character_id"] == "character:1031"
    )
    assert character_row["rarity"] == "A"
    assert character_row["element"] == "ether"
    engine_row = next(
        row for row in client.get("/api/v1/wengines").json()
        if row["wengine_id"] == "wengine:13103"
    )
    assert engine_row["signature_character_id"] == "character:1031"

    fields = {item.field_id: item for item in config_fields_for(NICOLE_ID, {}, [NICOLE_ID])}
    assert fields["core_level"].value == 1
    assert fields["cinema_level"].value == 6
    assert {key: fields[key].value for key in fields if key.startswith("skill_level:")} == {
        f"skill_level:{group}": 16 for group in _SKILL_GROUPS
    }
    definition = compile_registered_definition(
        NICOLE_ID,
        {},
        [NICOLE_ID],
        strict=False,
    )
    assert len(definition.move_entries) == 18
    assert next(
        item for item in definition.rule_items
        if str(item.rule_id) == "rule:character:1031:extra-ability:target-ether-damage"
    ).eligibility.value == "ineligible"


def test_nicole_core_debuff_and_ether_extra_ability_apply_to_another_active_dealer() -> None:
    payload = _payload(
        "move-entry:character:1331:basic-lady-dance",
        core_level=7,
        cinema_level=0,
        supports=("character:1331",),
        conditions={"condition:nicole:core-defense-down-active": True},
        enabled=(
            "rule:character:1031:core:target-defense-down",
            "rule:character:1031:extra-ability:target-ether-damage",
        ),
    )
    payload["compile_configs"]["character:1331"] = {"core_level": 1, "cinema_level": 0}
    payload["primary_character_id"] = "character:1331"
    payload["supporting_character_ids"] = ["character:1031"]
    payload["team_character_ids"] = ["character:1331", "character:1031"]
    payload["move_entry_id"] = "move-entry:character:1331:basic-lady-dance"
    payload["compile_configs"]["character:1031"] = {
        "core_level": 7,
        "cinema_level": 0,
        "skill_levels": _skills(12),
    }
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    event = result["events"][0]
    assert event["damage_type"] == "direct"
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS) == pytest.approx(0.25)
    assert _node(event, CalculationNode.ENEMY_DEFENSE_REDUCTION) == pytest.approx(0.40)
    assert event["modes"]["expected"]["status"] == "calculated"


def test_nicole_cinema1_changes_ex_bonus_and_buildup_not_the_skill_ratio() -> None:
    payload = _payload(
        "move-entry:character:1031:ex-special-candy-bullet-shelling",
        cinema_level=1,
        enabled=("rule:character:1031:cinema1:ex-special-damage-and-buildup",),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    event = response.json()["events"][0]
    assert _node(event, CalculationNode.DAMAGE_SKILL_MULTIPLIER) == pytest.approx(4.306)
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS) == pytest.approx(0.16)
    assert _node(event, CalculationNode.DAMAGE_NORMAL_BONUS_REGION) == pytest.approx(1.16)
    assert any(
        item["modifier_path"] == "anomaly-buildup.efficiency"
        and item["value"] == pytest.approx(0.16)
        for item in event["common_application_trace"]["applied_modifiers"]
    )


def test_nicole_cinema6_is_target_specific_event_crit_and_never_changes_formal_panel() -> None:
    payload = _payload(
        "move-entry:character:1031:ex-special-candy-bullet-shelling",
        cinema_level=6,
        conditions={"condition:nicole:cinema6-target-crit-active": True},
        parameters={"parameter:nicole:cinema6-target-crit-stacks": 10},
        enabled=("rule:character:1031:cinema6:target-crit-rate-stacks",),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    nicole = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == "character:1031"
    )
    assert nicole["stats"]["crit_rate"] == pytest.approx(0.05)
    event = result["events"][0]
    assert _node(event, CalculationNode.CHARACTER_CURRENT_CRIT_RATE) == pytest.approx(0.20)
    assert event["common_application_trace"]["event_stat_modifiers"]

    anomaly_payload = _payload(
        "move-entry:character:1031:ether-corrosion",
        cinema_level=6,
        conditions={"condition:nicole:cinema6-target-crit-active": True},
        parameters={"parameter:nicole:cinema6-target-crit-stacks": 10},
        enabled=("rule:character:1031:cinema6:target-crit-rate-stacks",),
    )
    anomaly_response = client.post("/api/v1/moves/calculate", json=anomaly_payload)
    assert anomaly_response.status_code == 200, anomaly_response.text
    anomaly_result = anomaly_response.json()
    anomaly_event = anomaly_result["events"][0]
    assert anomaly_event["crit_capability"] == "none"
    assert anomaly_event["common_application_trace"]["event_stat_modifiers"] == []
    assert len({mode["value"] for mode in anomaly_event["modes"].values()}) == 1


def test_nicole_energy_field_uncertainty_is_local_and_preserves_the_cannon_hit() -> None:
    entry = "move-entry:character:1031:ex-special-candy-bullet-shelling"
    base = client.post("/api/v1/moves/calculate", json=_payload(entry))
    assert base.status_code == 200, base.text
    assert base.json()["totals"]["expected"]["complete"] is True

    field_rule = "rule:character:1031:ex-special:energy-field-damage-unresolved"
    field_payload = _payload(
        entry,
        conditions={"condition:nicole:ex-energy-field-hit-occurred": True},
        enabled=(field_rule,),
    )
    response = client.post("/api/v1/moves/calculate", json=field_payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is False
    assert result["totals"]["expected"]["value"] > 0
    assert result["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert any(item["blocking"] and item["kind"] == "ambiguous-semantics" for item in result["diagnostics"])

    charge_payload = _payload(
        entry,
        conditions={"condition:nicole:ex-charged-hit-occurred": True},
        enabled=("rule:character:1031:ex-special:charged-damage-unresolved",),
    )
    charge_response = client.post("/api/v1/moves/calculate", json=charge_payload)
    assert charge_response.status_code == 200, charge_response.text
    charge_result = charge_response.json()
    assert charge_result["totals"]["expected"]["complete"] is False
    assert charge_result["events"][0]["modes"]["expected"]["value"] > 0
    assert any(item["blocking"] for item in charge_result["diagnostics"])


def test_nicole_r5_treasure_chest_signature_build_preserves_white_stats_and_current_flat_regen() -> None:
    payload = _payload(
        "move-entry:character:1031:ex-special-candy-bullet-shelling",
        core_level=1,
        cinema_level=0,
        equipment_builds={
            "character:1031": {
                "level": 60,
                "build_mode": "equipment-build",
                "wengine_id": "wengine:13103",
                "wengine_level": 60,
                "wengine_refinement": 5,
                "drive_discs": [],
            }
        },
        conditions={
            "condition:wengine:13103:owner:1031:ether-triggered-buff-active": True,
        },
        enabled=(
            "rule:wengine:13103:owner:1031:all-damage-buff",
            "rule:wengine:13103:owner:1031:energy-regen-flat",
        ),
    )
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    nicole = next(
        item for item in result["resolved_character_snapshots"]
        if item["character_id"] == "character:1031"
    )
    assert nicole["stats"]["attack"] == pytest.approx(1273.1691)
    assert nicole["stats"]["energy_regen"] == pytest.approx(3.14)
    assert _node(result["events"][0], CalculationNode.DAMAGE_NORMAL_BONUS_REGION) == pytest.approx(1.24)


def test_nicole_and_astra_same_r5_treasure_chest_dedupes_team_damage_not_self_regen() -> None:
    payload = _payload(
        "move-entry:character:1031:special-candy-bullet",
        supports=("character:1311",),
        equipment_builds={
            "character:1031": {
                "level": 60,
                "build_mode": "equipment-build",
                "wengine_id": "wengine:13103",
                "wengine_level": 60,
                "wengine_refinement": 5,
                "drive_discs": [],
            },
            "character:1311": {
                "level": 60,
                "build_mode": "equipment-build",
                "wengine_id": "wengine:13103",
                "wengine_level": 60,
                "wengine_refinement": 5,
                "drive_discs": [],
            },
        },
    )
    # Make Astra the active operator while Nicole is the backline engine owner.
    payload["primary_character_id"] = "character:1311"
    payload["supporting_character_ids"] = ["character:1031"]
    payload["team_character_ids"] = ["character:1311", "character:1031"]
    payload["move_entry_id"] = "move-entry:astra:1311:basic-rhapsody-1"
    payload["compile_configs"] = {
        "character:1311": {"core_level": 1, "cinema_level": 0},
        "character:1031": {
            "core_level": 1,
            "cinema_level": 0,
            "skill_levels": _skills(12),
        },
    }
    for owner in ("character:1031", "character:1311"):
        owner_id = owner.split(":")[-1]
        payload["condition_values"][
            f"condition:wengine:13103:owner:{owner_id}:ether-triggered-buff-active"
        ] = True
        payload["enabled_rule_item_ids"].extend(
            (
                f"rule:wengine:13103:owner:{owner_id}:all-damage-buff",
                f"rule:wengine:13103:owner:{owner_id}:energy-regen-flat",
            )
        )

    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True
    assert _node(result["events"][0], CalculationNode.DAMAGE_NORMAL_BONUS) == pytest.approx(0.24)
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots["character:1031"]["energy_regen"] == pytest.approx(3.14)
    assert snapshots["character:1311"]["energy_regen"] == pytest.approx(3.14)
    assert {
        item["recipient_character_id"]
        for item in result["panel_traces"]
        if item["modifier_path"] == "character.combat.energy-regen-flat-bonus"
    } == {"character:1031", "character:1311"}


def test_nicole_ether_corrosion_and_disorder_are_static_nocrit_paths() -> None:
    corrosion_response = client.post(
        "/api/v1/moves/calculate",
        json=_payload("move-entry:character:1031:ether-corrosion"),
    )
    assert corrosion_response.status_code == 200, corrosion_response.text
    corrosion = corrosion_response.json()
    event = corrosion["events"][0]
    assert corrosion["totals"]["expected"]["complete"] is True
    assert event["damage_type"] == "anomaly"
    assert event["crit_capability"] == "none"
    assert event["repeat_count"] == 20
    assert _node(event, CalculationNode.ATTRIBUTE_ANOMALY_MULTIPLIER) == pytest.approx(0.625)
    assert len({mode["value"] for mode in event["modes"].values()}) == 1

    disorder_response = client.post(
        "/api/v1/moves/calculate",
        json=_payload("move-entry:character:1031:ether-corrosion-disorder"),
    )
    assert disorder_response.status_code == 200, disorder_response.text
    disorder = disorder_response.json()
    disorder_event = disorder["events"][0]
    assert disorder["totals"]["expected"]["complete"] is True
    assert disorder_event["damage_type"] == "disorder"
    assert disorder_event["crit_capability"] == "none"
    assert _node(disorder_event, CalculationNode.DISORDER_TOTAL_MULTIPLIER) == pytest.approx(17.0)
    assert len({mode["value"] for mode in disorder_event["modes"].values()}) == 1
