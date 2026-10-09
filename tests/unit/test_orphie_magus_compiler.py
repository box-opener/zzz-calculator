from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.orphie_magus import (
    ORPHIE_MAGUS_ID,
    OrphieMagusCompileConfig,
    compile_orphie_magus,
    load_raw_record,
)
from core.application.moves import MultiplierRelation
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
    load_wengine_raw_record,
)
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import CharacterId, DamageTag, Element, SkillGroup, WEngineBuildInput, WEngineId
from web.api import app


client = TestClient(app)

_FOCUS_ACTIVE = "condition:orphie-magus:team-focus-active"
_ULTIMATE_ATTACK_BUFF_ACTIVE = "condition:orphie-magus:ultimate-attack-buff-active"


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
        element.value: value.value
        for element, value in panel.element_damage_bonus.items()
    }
    return result


def _payload(
    entry_id: str,
    *,
    supporting: tuple[str, ...] = (),
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    resistance: float = 0.0,
    energy_regen_overrides: dict[str, float] | None = None,
    signature_refinement: int | None = None,
) -> dict[str, object]:
    team = [str(ORPHIE_MAGUS_ID), *(item for item in supporting if item != str(ORPHIE_MAGUS_ID))]
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        stats = _panel_stats(character_id)
        if energy_regen_overrides and character_id in energy_regen_overrides:
            stats["energy_regen"] = energy_regen_overrides[character_id]
        builds[character_id] = {
            "level": 60,
            "build_mode": "equipment-build",
            "base_stats": stats,
            "drive_discs": [],
        }
        if character_id == str(ORPHIE_MAGUS_ID) and signature_refinement is not None:
            builds[character_id]["wengine_id"] = "wengine:14130"
            builds[character_id]["wengine_refinement"] = signature_refinement
    return {
        "primary_character_id": str(ORPHIE_MAGUS_ID),
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": entry_id,
        "compile_configs": {
            character_id: {
                "core_level": 7,
                "cinema_level": cinema if character_id == str(ORPHIE_MAGUS_ID) else 0,
            }
            for character_id in team
        },
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:orphie-test",
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


def _breakdown(event: dict[str, object], node: str, mode: str = "expected") -> float:
    return next(
        item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
        if item["node"] == node
    )


def test_orphie_live_identity_panel_and_signature() -> None:
    raw = load_raw_record(load_character_record(str(ORPHIE_MAGUS_ID)))
    assert (raw.name, raw.code_name, raw.rarity) == ("奥菲丝&「鬼火」", "Orphie & Magus", 4)
    assert (raw.specialty, raw.element, raw.faction, raw.icon) == (
        "强攻",
        "火属性",
        "新艾利都防卫军",
        "IconRole49",
    )
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1301.json",
    )
    assert str(ORPHIE_MAGUS_ID) in supported_character_ids()
    panel = character_base_stats(ORPHIE_MAGUS_ID)
    assert panel.attack.value == pytest.approx(929.7586)
    assert panel.hp.value == pytest.approx(7788.6961)
    assert panel.defense.value == pytest.approx(612.6038)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    assert panel.anomaly_mastery.value == pytest.approx(92.0)
    assert panel.energy_regen.value == pytest.approx(1.56)
    assert OrphieMagusCompileConfig().core_level == 7
    assert OrphieMagusCompileConfig().cinema_level == 0
    assert OrphieMagusCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(ORPHIE_MAGUS_ID)
    catalog = next(
        item for item in supported_character_catalog()
        if item.character_id == str(ORPHIE_MAGUS_ID)
    )
    assert catalog.code_name == "Orphie & Magus"
    assert catalog.rarity == "S"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert SIGNATURE_WENGINE_BY_CHARACTER[ORPHIE_MAGUS_ID] == WEngineId("wengine:14130")

    weapon = load_wengine_raw_record("wengine:14130")
    assert weapon.name == "嚣枪喧焰"
    assert weapon.icon == "Weapon_S_1301"
    assert weapon.source_url == "https://static.nanoka.cc/zzz/3.2/zh/weapon/14130.json"
    result = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14130"), ORPHIE_MAGUS_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert result.complete is True
    assert result.raw.base_attack == pytest.approx(713.0)
    assert result.raw.advanced_stat_value == pytest.approx(0.6)


def test_orphie_reviewed_curves_and_unresolved_mixed_elements() -> None:
    raw = load_raw_record(load_character_record(str(ORPHIE_MAGUS_ID)))
    definition = compile_orphie_magus(OrphieMagusCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    expected = {
        "move-entry:character:1301:basic-flame-blade": 3.168,
        "move-entry:character:1301:dash-attack": 1.25,
        "move-entry:character:1301:special-hot-loaded": 0.791,
        "move-entry:character:1301:special-light-eater": 9.9,
        "move-entry:character:1301:ex-special-careful": 5.625,
        "move-entry:character:1301:ex-special-red-whirlpool": 13.571,
        "move-entry:character:1301:ex-special-heat-charge": 7.788,
        "move-entry:character:1301:ex-special-blaze-burst": 5.192,
        "move-entry:character:1301:chain-attack": 12.533,
        "move-entry:character:1301:ultimate": 13.983,
        "move-entry:character:1301:ultimate-extension": 9.322,
        "move-entry:character:1301:assist-strike": 7.228,
    }
    for entry_id, ratio in expected.items():
        assert entries[entry_id].multiplier_variants[0].multiplier.value.value == pytest.approx(ratio)

    assert entries["move-entry:character:1301:basic-flame-blade"].main_damage_event.element is Element.FIRE
    assert entries["move-entry:character:1301:ex-special-heat-charge"].main_damage_event.damage_tags == frozenset(
        {DamageTag.EX_SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}
    )
    assert entries["move-entry:character:1301:chain-attack"].main_damage_event.damage_tags == frozenset(
        {DamageTag.CHAIN_ATTACK, DamageTag.FOLLOW_UP_ATTACK}
    )
    assert entries["move-entry:character:1301:ultimate"].main_damage_event.damage_tags == frozenset(
        {DamageTag.ULTIMATE, DamageTag.FOLLOW_UP_ATTACK}
    )
    assert entries["move-entry:character:1301:special-light-eater"].main_damage_event.damage_tags == frozenset(
        {DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}
    )
    assert any(
        "四次激光" in item.message
        for item in entries["move-entry:character:1301:special-light-eater"].diagnostics
    )
    c6_definition = compile_orphie_magus(
        OrphieMagusCompileConfig(cinema_level=6),
        raw,
    )
    c6_packet = next(
        item for item in c6_definition.move_entries
        if str(item.entry_id) == "move-entry:character:1301:cinema6-extra-fire"
    )
    assert c6_packet.multiplier_variants[0].multiplier.value.value == pytest.approx(2.5)
    assert c6_packet.main_damage_event.element is Element.FIRE
    assert c6_packet.skill_group is SkillGroup.SPECIAL_ATTACK
    assert c6_packet.damage_tags == frozenset(
        {DamageTag.EX_SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}
    )
    for key in (
        "basic-stage-1",
        "basic-stage-2",
        "basic-stage-3",
        "basic-stage-4",
        "basic-stage-5",
        "dodge-counter",
        "quick-assist",
    ):
        entry_id = f"move-entry:character:1301:{key}"
        assert entries[entry_id].multiplier_relation is MultiplierRelation.UNRESOLVED_RELATION


def test_orphie_unknown_element_sources_keep_ratios_without_direct_events() -> None:
    for entry_id in (
        "move-entry:character:1301:basic-stage-1",
        "move-entry:character:1301:basic-stage-5",
        "move-entry:character:1301:dodge-counter",
        "move-entry:character:1301:quick-assist",
    ):
        result = _calculate(_payload(entry_id))
        assert result["events"] == []
        assert result["totals"]["expected"]["complete"] is False
        assert any("元素" in item["message"] for item in result["diagnostics"])


def test_orphie_four_follow_up_lasers_keep_one_source_curve_as_local_partial() -> None:
    result = _calculate(_payload("move-entry:character:1301:special-light-eater"))
    assert len(result["events"]) == 1
    assert result["events"][0]["element"] == "fire"
    assert result["events"][0]["modes"]["expected"]["value"] is not None
    assert result["totals"]["expected"]["complete"] is False
    assert any("四次激光追加攻击" in item["message"] for item in result["diagnostics"])

    follow_up = _calculate(
        _payload(
            "move-entry:character:1301:special-light-eater",
            enabled=("rule:character:1301:core:own-crit-and-follow-up",),
        )
    )
    assert _breakdown(follow_up["events"][0], "damage.normal-bonus") == pytest.approx(0.85)
    assert follow_up["totals"]["expected"]["complete"] is False


def test_orphie_focus_panel_uses_owners_initial_regeneration_for_all_recipients() -> None:
    koleda = "character:1101"
    for owner_er, peer_er, bonus in (
        (1.56, 1.8, 280.0),
        (2.16, 1.2, 392.0),
        (1.605, 3.7, 281.0),
        (3.7, 1.56, 700.0),
    ):
        payload = _payload(
            "move-entry:character:1301:dash-attack",
            supporting=(koleda,),
            conditions={_FOCUS_ACTIVE: True},
            enabled=("rule:character:1301:core:focus-attack",),
            energy_regen_overrides={
                "character:1301": owner_er,
                koleda: peer_er,
            },
        )
        result = _calculate(payload)
        snapshots = {
            item["character_id"]: item["stats"]["attack"]
            for item in result["resolved_character_snapshots"]
        }
        assert snapshots["character:1301"] == pytest.approx(929.7586 + bonus)
        assert snapshots[koleda] == pytest.approx(_panel_stats(koleda)["attack"] + bonus)

    signature = _calculate(
        _payload(
            "move-entry:character:1301:dash-attack",
            supporting=(koleda,),
            conditions={_FOCUS_ACTIVE: True},
            enabled=("rule:character:1301:core:focus-attack",),
            signature_refinement=1,
        )
    )
    snapshots = {
        item["character_id"]: item["stats"]
        for item in signature["resolved_character_snapshots"]
    }
    assert snapshots["character:1301"]["energy_regen"] == pytest.approx(2.496)
    assert snapshots["character:1301"]["attack"] == pytest.approx(
        929.7586 + 713.0 + 459.2
    )
    assert snapshots[koleda]["attack"] == pytest.approx(
        _panel_stats(koleda)["attack"] + 459.2
    )


def test_orphie_core_and_additional_follow_up_bonuses_are_scoped() -> None:
    entry_id = "move-entry:character:1301:basic-flame-blade"
    own_core = _calculate(
        _payload(
            entry_id,
            enabled=("rule:character:1301:core:own-crit-and-follow-up",),
        )
    )
    focus_c1 = _calculate(
        _payload(
            entry_id,
            cinema=1,
            conditions={_FOCUS_ACTIVE: True},
            enabled=(
                "rule:character:1301:core:own-crit-and-follow-up",
                "rule:character:1301:cinema1:focus-holder-damage",
            ),
        )
    )
    assert focus_c1["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        own_core["events"][0]["modes"]["expected"]["value"] * (2.05 / 1.85)
    )

    supported = _calculate(
        _payload(
            entry_id,
            supporting=("character:1141",),
            conditions={_FOCUS_ACTIVE: True},
            enabled=("rule:character:1301:extra-ability:focus-follow-up-defense-ignore",),
        )
    )
    assert _breakdown(supported["events"][0], "defense.damage-ignore") == pytest.approx(0.25)

    no_eligibility = compile_orphie_magus(
        OrphieMagusCompileConfig(additional_ability_eligible=False),
        load_raw_record(load_character_record(str(ORPHIE_MAGUS_ID))),
    )
    assert next(
        item for item in no_eligibility.rule_items
        if str(item.rule_id) == "rule:character:1301:extra-ability:focus-follow-up-defense-ignore"
    ).eligibility is RuleEligibility.INELIGIBLE


def test_orphie_cinema_fire_ignore_attack_bonus_and_c6_packet() -> None:
    base_charge = _calculate(
        _payload("move-entry:character:1301:ex-special-heat-charge", cinema=1, resistance=0.25)
    )
    c1_charge = _calculate(
        _payload(
            "move-entry:character:1301:ex-special-heat-charge",
            cinema=1,
            enabled=("rule:character:1301:cinema1:fire-resistance-ignore",),
            resistance=0.25,
        )
    )
    assert _breakdown(c1_charge["events"][0], "resistance.damage-ignore") == pytest.approx(0.15)
    assert c1_charge["totals"]["expected"]["value"] > base_charge["totals"]["expected"]["value"]

    hot_special = _calculate(
        _payload(
            "move-entry:character:1301:special-hot-loaded",
            cinema=1,
            enabled=("rule:character:1301:cinema1:fire-resistance-ignore",),
            resistance=0.25,
        )
    )
    assert _breakdown(hot_special["events"][0], "resistance.damage-ignore") == pytest.approx(0.0)

    four_lasers = _calculate(
        _payload(
            "move-entry:character:1301:special-light-eater",
            cinema=1,
            enabled=("rule:character:1301:cinema1:fire-resistance-ignore",),
            resistance=0.25,
        )
    )
    assert _breakdown(four_lasers["events"][0], "resistance.damage-ignore") == pytest.approx(0.15)
    assert four_lasers["totals"]["expected"]["complete"] is False

    c2_without_buff = _calculate(
        _payload("move-entry:character:1301:special-hot-loaded", cinema=2)
    )
    c2_with_buff = _calculate(
        _payload(
            "move-entry:character:1301:special-hot-loaded",
            cinema=2,
            conditions={_ULTIMATE_ATTACK_BUFF_ACTIVE: True},
            enabled=("rule:character:1301:cinema2:ultimate-attack",),
        )
    )
    base_attack = c2_without_buff["resolved_character_snapshots"][0]["stats"]["attack"]
    boosted_attack = c2_with_buff["resolved_character_snapshots"][0]["stats"]["attack"]
    assert boosted_attack == pytest.approx(base_attack * 1.2)

    no_c4 = _calculate(
        _payload("move-entry:character:1301:ex-special-heat-charge", cinema=4)
    )
    with_c4 = _calculate(
        _payload(
            "move-entry:character:1301:ex-special-heat-charge",
            cinema=4,
            enabled=("rule:character:1301:cinema4:charge-and-ultimate-damage",),
        )
    )
    assert with_c4["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        no_c4["events"][0]["modes"]["expected"]["value"] * 1.4
    )
    base_extension = _calculate(
        _payload("move-entry:character:1301:ultimate-extension", cinema=4)
    )
    c4_extension = _calculate(
        _payload(
            "move-entry:character:1301:ultimate-extension",
            cinema=4,
            enabled=("rule:character:1301:cinema4:charge-and-ultimate-damage",),
        )
    )
    assert c4_extension["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        base_extension["events"][0]["modes"]["expected"]["value"] * 1.4
    )

    c6_packet = _calculate(
        _payload("move-entry:character:1301:cinema6-extra-fire", cinema=6)
    )
    assert len(c6_packet["events"]) == 1
    assert c6_packet["events"][0]["element"] == "fire"
    assert c6_packet["totals"]["expected"]["complete"] is True

    c6_packet_c1 = _calculate(
        _payload(
            "move-entry:character:1301:cinema6-extra-fire",
            cinema=6,
            enabled=("rule:character:1301:cinema1:fire-resistance-ignore",),
            resistance=0.25,
        )
    )
    assert c6_packet_c1["events"][0]["modes"]["expected"]["value"] is not None
    assert c6_packet_c1["totals"]["expected"]["complete"] is False
    assert any("父招式可能为终结技" in item["message"] for item in c6_packet_c1["diagnostics"])

    for key in ("ex-special-heat-charge", "ultimate", "ultimate-extension"):
        c6_parent = _calculate(
            _payload(f"move-entry:character:1301:{key}", cinema=6)
        )
        assert len(c6_parent["events"]) == 1
        assert c6_parent["events"][0]["modes"]["expected"]["value"] is not None
        assert c6_parent["totals"]["expected"]["complete"] is False
        assert any("每0.5秒触发" in item["message"] for item in c6_parent["diagnostics"])
    c6_unaffected = _calculate(_payload("move-entry:character:1301:dash-attack", cinema=6))
    assert c6_unaffected["totals"]["expected"]["complete"] is True

    c6_packet_c4 = _calculate(
        _payload(
            "move-entry:character:1301:cinema6-extra-fire",
            cinema=6,
            enabled=("rule:character:1301:cinema4:charge-and-ultimate-damage",),
        )
    )
    assert c6_packet_c4["events"][0]["modes"]["expected"]["value"] is not None
    assert c6_packet_c4["totals"]["expected"]["complete"] is False
    assert any("是否继承" in item["message"] for item in c6_packet_c4["diagnostics"])


def test_orphie_static_fire_anomaly_and_disorder_are_single_character_models() -> None:
    burn = _calculate(_payload("move-entry:character:1301:fire-anomaly"))
    assert burn["totals"]["expected"]["complete"] is True
    assert burn["events"][0]["repeat_count"] == 20
    assert burn["events"][0]["element"] == "fire"

    disorder = _calculate(_payload("move-entry:character:1301:fire-disorder"))
    assert disorder["totals"]["expected"]["complete"] is True
    assert disorder["events"][0]["element"] == "fire"
