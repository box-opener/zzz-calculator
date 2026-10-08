from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.zhu_yuan import (
    ZHU_YUAN_ID,
    ZhuYuanCompileConfig,
    compile_zhu_yuan,
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
from core.types import CharacterId, SkillGroup, WEngineBuildInput, WEngineId
from web.api import app


client = TestClient(app)


def _stats(character_id: CharacterId) -> dict[str, object]:
    panel = character_base_stats(character_id)
    result: dict[str, object] = {
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
    result["element_damage_bonus"] = {
        element.value: value.value
        for element, value in panel.element_damage_bonus.items()
    }
    return result


def _payload(
    move_entry_id: str,
    *,
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    supporting: tuple[str, ...] = (),
    enemy_stunned: bool = False,
    shell_counts: dict[str, int] | None = None,
) -> dict[str, object]:
    primary = str(ZHU_YUAN_ID)
    team = [primary, *supporting]
    configs = {
        item: (
            {"core_level": 7, "cinema_level": cinema}
            if item == primary
            else {"core_level": 7, "cinema_level": 0}
        )
        for item in team
    }
    return {
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
        "rule_stack_counts": shell_counts or {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _stats(CharacterId(item))}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:zhu-yuan-test",
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
            "is_stunned": enemy_stunned,
        },
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _expected_breakdown(event: dict[str, object]) -> dict[str, float]:
    return {
        item["node"]: item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
    }


def test_zhu_yuan_source_registration_panel_defaults_and_signature() -> None:
    source = load_raw_record(load_character_record(str(ZHU_YUAN_ID)))
    assert source.name == "朱鸢"
    assert source.code_name == "Zhu Yuan"
    assert source.rarity == 4
    assert source.specialty == "强攻"
    assert source.element == "以太"
    assert source.faction == "新艾利都治安局"
    assert source.source_version == "3.2"
    assert source.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1241.json"
    assert str(ZHU_YUAN_ID) in supported_character_ids()

    panel = character_base_stats(ZHU_YUAN_ID)
    assert panel.attack.value == pytest.approx(919.3011)
    assert panel.hp.value == pytest.approx(7482.7069)
    assert panel.defense.value == pytest.approx(600.5916)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.788)
    assert panel.anomaly_proficiency.value == pytest.approx(92.0)
    assert panel.anomaly_mastery.value == pytest.approx(93.0)

    config = ZhuYuanCompileConfig()
    assert config.core_level == 7
    assert config.cinema_level == 0
    assert config.skill_level_for(SkillGroup.ULTIMATE) == 12
    registration = registration_for(ZHU_YUAN_ID)
    assert registration.catalog.rarity == "S"
    assert registration.catalog.code_name == "Zhu Yuan"
    editor_defaults = {
        item.field_id: item.value
        for item in registration.config_fields({}, (ZHU_YUAN_ID,))
    }
    assert all(
        editor_defaults[f"skill_level:{group}"] == 12
        for group in ("basic-attack", "dodge", "special-attack", "chain-attack", "assist", "ultimate")
    )
    assert "potential_level" not in editor_defaults

    assert SIGNATURE_WENGINE_BY_CHARACTER[ZHU_YUAN_ID] == WEngineId("wengine:14124")
    weapon = load_wengine_raw_record("wengine:14124")
    assert weapon.icon == "Weapon_S_1241"
    engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14124"), ZHU_YUAN_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert engine.complete is True
    assert engine.contributions[0].value.value == pytest.approx(713.0)
    assert engine.contributions[1].value.value == pytest.approx(0.48)


def test_zhu_yuan_known_direct_curves_and_unresolved_basic_and_assist_are_local() -> None:
    raw = load_raw_record(load_character_record(str(ZHU_YUAN_ID)))
    definition = compile_zhu_yuan(ZhuYuanCompileConfig(), raw)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    ratios = {
        "dash-firepower-raid": 1.112,
        "pressure-basic-physical-1": 1.076,
        "pressure-basic-physical-2": 1.076,
        "pressure-basic-physical-3": 3.226,
        "pressure-basic-ether-1": 2.723,
        "pressure-basic-ether-2": 2.723,
        "pressure-basic-ether-3": 8.158,
        "pressure-dash-physical": 1.076,
        "pressure-dash-ether": 2.723,
        "dodge-counter-ether": 3.539,
        "special-ether-single-shot": 0.371,
        "ex-ether": 11.748,
        "chain-ether": 11.760,
        "ultimate-ether": 39.554,
        "quick-assist-ether": 1.031,
    }
    for key, expected in ratios.items():
        entry = entries[f"move-entry:character:1241:{key}"]
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(expected)
    for stage, expected in enumerate((0.871, 2.529, 2.748, 3.028, 3.250), start=1):
        entry = entries[f"move-entry:character:1241:assault-basic-stage-{stage}-element-unresolved"]
        assert entry.multiplier_relation is MultiplierRelation.UNRESOLVED_RELATION
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(expected)
    assist = entries["move-entry:character:1241:assist-strike-mixed-element-unresolved"]
    assert assist.multiplier_variants[0].multiplier.value.value == pytest.approx(7.122)

    for stage in range(1, 6):
        result = _calculate(_payload(f"move-entry:character:1241:assault-basic-stage-{stage}-element-unresolved"))
        assert result["events"] == []
        assert result["totals"]["expected"]["complete"] is False
    mixed_assist = _calculate(_payload("move-entry:character:1241:assist-strike-mixed-element-unresolved"))
    assert mixed_assist["events"] == []
    assert mixed_assist["totals"]["expected"]["complete"] is False


def test_zhu_yuan_suppression_components_and_shell_scoped_core_effects() -> None:
    no_shell = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-physical-1",
            conditions={"condition:zhu-yuan:suppression-mode-active": True},
        )
    )
    assert len(no_shell["events"]) == 1
    assert _expected_breakdown(no_shell["events"][0])["damage.normal-bonus"] == pytest.approx(0.0)

    shell_spent_rule = "rule:character:1241:core:pressure-spent-shell-damage-bonus"
    stunned_rule = "rule:character:1241:core:pressure-stunned-target-extra-damage-bonus"
    shell = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-physical-1",
            conditions={
                "condition:zhu-yuan:suppression-mode-active": True,
                "condition:zhu-yuan:enhanced-shell-consumed": True,
            },
            enabled=(shell_spent_rule,),
        )
    )
    assert len(shell["events"]) == 1
    assert _expected_breakdown(shell["events"][0])["damage.normal-bonus"] == pytest.approx(0.40)

    stunned = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-physical-1",
            conditions={
                "condition:zhu-yuan:suppression-mode-active": True,
                "condition:zhu-yuan:enhanced-shell-consumed": True,
            },
            enabled=(shell_spent_rule, stunned_rule),
            enemy_stunned=True,
        )
    )
    assert _expected_breakdown(stunned["events"][0])["damage.normal-bonus"] == pytest.approx(0.80)

    c2_rule = "rule:character:1241:cinema2:ethereal-remnant-ether-damage"
    physical = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-physical-1",
            cinema=2,
            conditions={"condition:zhu-yuan:suppression-mode-active": True},
            enabled=(c2_rule,),
            shell_counts={c2_rule: 5},
        )
    )
    ether = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-ether-1",
            cinema=2,
            conditions={
                "condition:zhu-yuan:suppression-mode-active": True,
                "condition:zhu-yuan:enhanced-shell-consumed": True,
            },
            enabled=(c2_rule,),
            shell_counts={c2_rule: 5},
        )
    )
    assert _expected_breakdown(physical["events"][0])["damage.normal-bonus"] == pytest.approx(0.0)
    assert _expected_breakdown(ether["events"][0])["damage.normal-bonus"] == pytest.approx(0.50)

    c4_rule = "rule:character:1241:cinema4:pressure-spent-shell-ether-resistance-ignore"
    c4_ether = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-ether-1",
            cinema=4,
            conditions={
                "condition:zhu-yuan:suppression-mode-active": True,
                "condition:zhu-yuan:enhanced-shell-consumed": True,
            },
            enabled=(c4_rule,),
        )
    )
    assert len(c4_ether["events"]) == 1
    assert _expected_breakdown(c4_ether["events"][0])["resistance.damage-ignore"] == pytest.approx(0.25)


def test_zhu_yuan_additional_ability_cr_is_current_self_panel_state() -> None:
    rule = "rule:character:1241:extra-ability:self-crit-rate"
    result = _calculate(
        _payload(
            "move-entry:character:1241:pressure-basic-physical-1",
            conditions={
                "condition:zhu-yuan:suppression-mode-active": True,
                "condition:zhu-yuan:additional-ability-crit-active": True,
            },
            enabled=(rule,),
            supporting=("character:1211",),
        )
    )
    snapshot = next(item for item in result["resolved_character_snapshots"] if item["character_id"] == str(ZHU_YUAN_ID))
    assert snapshot["stats"]["crit_rate"] == pytest.approx(0.35)


def test_zhu_yuan_cinema_six_keeps_known_880_percent_local_without_fake_child() -> None:
    c6_entry = "move-entry:character:1241:cinema6-extra-ether-bullets-identity-unresolved"
    raw = load_raw_record(load_character_record(str(ZHU_YUAN_ID)))
    definition = compile_zhu_yuan(ZhuYuanCompileConfig(cinema_level=6), raw)
    entry = next(item for item in definition.move_entries if str(item.entry_id) == c6_entry)
    assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(8.8)

    standalone = _calculate(_payload(c6_entry, cinema=6))
    assert standalone["events"] == []
    assert standalone["totals"]["expected"]["complete"] is False
    c6_rule = "rule:character:1241:cinema6:extra-ether-bullets"
    c6_ex = _calculate(
        _payload(
            "move-entry:character:1241:ex-ether",
            cinema=6,
            conditions={"condition:zhu-yuan:cinema6-ether-afterglow-active": True},
            enabled=(c6_rule,),
        )
    )
    assert len(c6_ex["events"]) == 1
    assert c6_ex["totals"]["expected"]["complete"] is False
    assert sum(event["modes"]["expected"]["known_value"] or 0.0 for event in c6_ex["events"]) > 0.0


def test_zhu_yuan_static_ether_anomaly_and_disorder_are_available() -> None:
    anomaly = _calculate(_payload("move-entry:character:1241:ether-corrosion"))
    assert anomaly["events"][0]["repeat_count"] == 20
    assert anomaly["events"][0]["modes"]["expected"]["value"] > 0.0
    assert anomaly["totals"]["expected"]["complete"] is True
    disorder = _calculate(_payload("move-entry:character:1241:ether-corrosion-disorder"))
    multiplier = _expected_breakdown(disorder["events"][0])["disorder.total-multiplier"]
    assert multiplier == pytest.approx(17.0)
    assert disorder["totals"]["expected"]["complete"] is True
