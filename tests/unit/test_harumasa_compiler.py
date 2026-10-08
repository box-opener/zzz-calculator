from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.harumasa import (
    HARUMASA_ID,
    HarumasaCompileConfig,
    compile_harumasa,
    load_raw_record,
)
from core.application.equipment import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
    load_wengine_raw_record,
)
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import CharacterId, SkillGroup, WEngineBuildInput, WEngineId
from core.application.moves import MultiplierRelation
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
    potential: int = 0,
    cinema: int = 0,
    conditions: dict[str, bool] | None = None,
    parameters: dict[str, int] | None = None,
    enabled: tuple[str, ...] = (),
    enemy_stunned: bool = False,
    supporting: tuple[str, ...] = (),
) -> dict[str, object]:
    primary = str(HARUMASA_ID)
    team = [primary, *supporting]
    configs = {
        item: (
            {"core_level": 7, "cinema_level": cinema, "potential_level": potential}
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
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _stats(CharacterId(item))}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:harumasa-test",
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


def test_harumasa_live_source_panel_and_signature_are_registered() -> None:
    raw = load_raw_record(load_character_record(str(HARUMASA_ID)), potential_level=0)
    assert raw.name == "悠真"
    assert raw.code_name == "Harumasa"
    assert raw.rarity == 4
    assert raw.specialty == "强攻"
    assert raw.element == "电属性"
    assert raw.faction == "对空洞特别行动部第六课"
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1201.json"
    assert str(HARUMASA_ID) in supported_character_ids()
    panel = character_base_stats(HARUMASA_ID)
    assert panel.attack.value == pytest.approx(915.593)
    assert panel.hp.value == pytest.approx(7405.6956)
    assert panel.defense.value == pytest.approx(600.5916)
    assert panel.crit_rate.value == pytest.approx(0.194)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(95.0)
    assert panel.anomaly_mastery.value == pytest.approx(80.0)
    assert HarumasaCompileConfig().core_level == 7
    assert HarumasaCompileConfig().cinema_level == 0
    assert HarumasaCompileConfig().potential_level == 0
    assert HarumasaCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(HARUMASA_ID)
    assert registration.catalog.rarity == "S"
    assert next(item for item in supported_character_catalog() if item.character_id == str(HARUMASA_ID)).code_name == "Harumasa"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert SIGNATURE_WENGINE_BY_CHARACTER[HARUMASA_ID] == WEngineId("wengine:14120")
    weapon = load_wengine_raw_record("wengine:14120")
    assert weapon.icon == "Weapon_S_1201"
    engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14120"), HARUMASA_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert engine.complete is True
    assert engine.contributions[0].value.value == pytest.approx(713.0)
    assert engine.contributions[1].value.value == pytest.approx(0.48)


def test_harumasa_reviewed_direct_curves_and_potential_unlocks() -> None:
    source = load_character_record(str(HARUMASA_ID))
    raw0 = load_raw_record(source, potential_level=0)
    raw1 = load_raw_record(source, potential_level=1)
    p0 = compile_harumasa(HarumasaCompileConfig(), raw0)
    p1 = compile_harumasa(HarumasaCompileConfig(potential_level=1), raw1)
    entries0 = {str(item.entry_id): item for item in p0.move_entries}
    entries1 = {str(item.entry_id): item for item in p1.move_entries}
    assert "move-entry:character:1201:potential1-julei" not in entries0
    assert "move-entry:character:1201:potential1-julei" in entries1
    assert "move-entry:character:1201:potential1-ex-patrol" not in entries0
    assert "move-entry:character:1201:potential1-ex-patrol" in entries1
    assert entries0["move-entry:character:1201:dash-physical"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.621)
    assert entries0["move-entry:character:1201:dodge-counter-electric"].multiplier_variants[0].multiplier.value.value == pytest.approx(4.396)
    assert entries0["move-entry:character:1201:ex-electric"].multiplier_variants[0].multiplier.value.value == pytest.approx(8.992)
    assert entries0["move-entry:character:1201:chain-electric"].multiplier_variants[0].multiplier.value.value == pytest.approx(10.357)
    assert entries0["move-entry:character:1201:ultimate-electric"].multiplier_variants[0].multiplier.value.value == pytest.approx(39.086)
    for stage in range(1, 6):
        basic = entries0[f"move-entry:character:1201:basic-stage-element-unresolved-{stage}"]
        assert basic.multiplier_relation is MultiplierRelation.UNRESOLVED_RELATION
        assert basic.multiplier_variants[0].multiplier.value.value > 0
    assert tuple(
        entries1[f"move-entry:character:1201:dash-slash-{stage}"].multiplier_variants[0].multiplier.value.value
        for stage in (1, 2, 3)
    ) == pytest.approx((3.251, 3.338, 3.799))
    assert entries1["move-entry:character:1201:potential1-julei"].multiplier_variants[0].multiplier.value.value == pytest.approx(0.830)
    assert entries1["move-entry:character:1201:potential1-ex-patrol"].multiplier_variants[0].multiplier.value.value == pytest.approx(10.268)
    assert len(entries1["move-entry:character:1201:ultimate-electric"].derived_damage_events) == 1
    assert entries1["move-entry:character:1201:ultimate-electric"].derived_damage_events[0].multiplier.value.value == pytest.approx(4.73)
    assert any(
        "五段" in diagnostic.message
        for stage in range(1, 6)
        for diagnostic in entries0[f"move-entry:character:1201:basic-stage-element-unresolved-{stage}"].diagnostics
    )


def test_harumasa_basic_unknown_element_is_selectable_but_never_instantiates_a_fake_hit() -> None:
    result = _calculate(_payload("move-entry:character:1201:basic-stage-element-unresolved-1"))
    assert result["events"] == []
    assert result["totals"]["expected"]["complete"] is False
    assert any("元素映射" in item["message"] for item in result["diagnostics"])


@pytest.mark.parametrize(
    ("move_entry_id", "expected"),
    (
        ("move-entry:character:1201:basic-feather", 1019.213050001296),
        ("move-entry:character:1201:basic-arrow", 156.50475270162082),
        ("move-entry:character:1201:dash-physical", 783.0068028682942),
        ("move-entry:character:1201:dodge-counter-electric", 2123.4410273960652),
        ("move-entry:character:1201:special-electric", 507.6743675598873),
        ("move-entry:character:1201:ex-electric", 4343.489926830168),
        ("move-entry:character:1201:chain-electric", 5002.8386534897745),
        ("move-entry:character:1201:ultimate-electric", 18880.076432393675),
        ("move-entry:character:1201:quick-assist-electric", 816.3365187214172),
        ("move-entry:character:1201:assist-strike-electric", 2971.175104529845),
    ),
)
def test_harumasa_known_direct_golden_values(move_entry_id: str, expected: float) -> None:
    result = _calculate(_payload(move_entry_id))
    assert result["totals"]["expected"]["complete"] is True
    assert result["totals"]["expected"]["value"] == pytest.approx(expected)


def test_harumasa_core_bonus_and_c2_electric_blade_are_current_state_scoped() -> None:
    dash_entry = "move-entry:character:1201:dash-slash-1"
    core_rule = "rule:character:1201:core:dash-crit-buffs"
    stacks = {"parameter:harumasa:current-fengmang-stacks": 6}
    base = _calculate(_payload(
        dash_entry,
        potential=0,
        conditions={"condition:harumasa:target-ten-cross-marked": True},
    ))
    core = _calculate(_payload(
        dash_entry,
        potential=0,
        conditions={"condition:harumasa:target-ten-cross-marked": True},
        parameters=stacks,
        enabled=(core_rule,),
    ))
    assert base["totals"]["expected"]["complete"] is True
    assert core["totals"]["expected"]["complete"] is True
    assert core["events"][0]["modes"]["expected"]["value"] > base["events"][0]["modes"]["expected"]["value"]

    c2_rule = "rule:character:1201:cinema2:electric-blade-dash-slash-damage"
    c2_zero = _calculate(_payload(
        dash_entry,
        cinema=2,
        conditions={"condition:harumasa:target-ten-cross-marked": True},
        parameters={"parameter:harumasa:current-electric-blade-stacks": 0},
        enabled=(c2_rule,),
    ))
    c2_one = _calculate(_payload(
        dash_entry,
        cinema=2,
        conditions={"condition:harumasa:target-ten-cross-marked": True},
        parameters={"parameter:harumasa:current-electric-blade-stacks": 1},
        enabled=(c2_rule,),
    ))
    assert c2_one["events"][0]["modes"]["expected"]["value"] > c2_zero["events"][0]["modes"]["expected"]["value"]


def test_harumasa_potential_attack_and_electric_resistance_ignore_are_scoped() -> None:
    rule = "rule:character:1201:potential2:current-attack-and-dash-res-ignore"
    conditions = {"condition:harumasa:target-ten-cross-marked": True, "condition:harumasa:potential-attack-buff-active": True}
    inactive = {"condition:harumasa:target-ten-cross-marked": True, "condition:harumasa:potential-attack-buff-active": False}
    dash_base = _calculate(_payload(
        "move-entry:character:1201:dash-slash-1",
        potential=2,
        conditions=inactive,
        enabled=(rule,),
    ))
    dash = _calculate(_payload(
        "move-entry:character:1201:dash-slash-1",
        potential=2,
        conditions=conditions,
        enabled=(rule,),
    ))
    special_base = _calculate(_payload(
        "move-entry:character:1201:special-electric",
        potential=2,
        conditions=inactive,
        enabled=(rule,),
    ))
    special = _calculate(_payload(
        "move-entry:character:1201:special-electric",
        potential=2,
        conditions=conditions,
        enabled=(rule,),
    ))
    dash_modifiers = dash["events"][0]["common_application_trace"]["applied_modifiers"]
    special_modifiers = special["events"][0]["common_application_trace"]["applied_modifiers"]
    assert any(item["modifier_path"] == "resistance.damage-ignore" for item in dash_modifiers)
    assert not any(item["modifier_path"] == "resistance.damage-ignore" for item in special_modifiers)
    assert dash["events"][0]["modes"]["expected"]["value"] > dash_base["events"][0]["modes"]["expected"]["value"]
    assert special["events"][0]["modes"]["expected"]["value"] > special_base["events"][0]["modes"]["expected"]["value"]


def test_harumasa_additional_ability_target_status_is_scoped_and_not_double_applied() -> None:
    rule_stunned = "rule:character:1201:extra-ability:stunned-target-damage-bonus"
    rule_anomaly = "rule:character:1201:extra-ability:anomalous-target-damage-bonus"
    entry = "move-entry:character:1201:dash-physical"
    support = ("character:1141",)
    stunned = _calculate(_payload(entry, enabled=(rule_stunned,), enemy_stunned=True, supporting=support))
    anomaly = _calculate(_payload(
        entry,
        enabled=(rule_anomaly,),
        conditions={"condition:harumasa:target-attribute-anomaly-active": True},
        supporting=support,
    ))
    both = _calculate(_payload(
        entry,
        enabled=(rule_stunned, rule_anomaly),
        conditions={"condition:harumasa:target-attribute-anomaly-active": True},
        enemy_stunned=True,
        supporting=support,
    ))
    def haru_bonuses(result: dict[str, object]) -> list[dict[str, object]]:
        return [
            item
            for item in result["events"][0]["common_application_trace"]["applied_modifiers"]
            if item["effect_id"].startswith("effect:character:1201:extra-ability:")
        ]

    assert len(haru_bonuses(stunned)) == 1
    assert len(haru_bonuses(anomaly)) == 1
    assert len(haru_bonuses(both)) == 1
    assert haru_bonuses(stunned)[0]["value"] == pytest.approx(0.4)
    assert haru_bonuses(anomaly)[0]["value"] == pytest.approx(0.4)
    assert haru_bonuses(both)[0]["value"] == pytest.approx(0.4)


def test_harumasa_c6_electromagnetic_child_is_partial_without_fake_direct_event() -> None:
    rule = "rule:character:1201:cinema6:electric-explosion-local-unresolved"
    result = _calculate(_payload(
        "move-entry:character:1201:basic-arrow",
        cinema=6,
        conditions={"condition:harumasa:cinema6-electromagnetic-explosion-ready": True},
        enabled=(rule,),
    ))
    assert len(result["events"]) == 1
    assert result["events"][0]["damage_type"] == "direct"
    assert result["totals"]["expected"]["complete"] is False
    assert any("1500%" in item["message"] or "1500%" in item.get("original_text", "") for item in result["diagnostics"])


def test_harumasa_potential1_julei_is_a_local_partial_on_stunned_dash_slash() -> None:
    rule = "rule:character:1201:potential1:julei-follow-up"
    selected = _calculate(_payload(
        "move-entry:character:1201:dash-slash-1",
        potential=1,
        conditions={"condition:harumasa:target-ten-cross-marked": True},
        enabled=(rule,),
        enemy_stunned=True,
    ))
    not_triggered = _calculate(_payload(
        "move-entry:character:1201:dash-slash-1",
        potential=1,
        conditions={"condition:harumasa:target-ten-cross-marked": True},
        enabled=(rule,),
        enemy_stunned=False,
    ))
    assert len(selected["events"]) == 1
    assert selected["totals"]["expected"]["complete"] is False
    assert len(not_triggered["events"]) == 1
    assert not_triggered["totals"]["expected"]["complete"] is True

    julei = _calculate(_payload("move-entry:character:1201:potential1-julei", potential=1))
    assert julei["events"][0]["modes"]["expected"]["status"] == "calculated"
    assert any("标签限定" in item["message"] for item in julei["diagnostics"])

    equipped = _payload("move-entry:character:1201:potential1-julei", potential=1)
    equipped["character_builds"][str(HARUMASA_ID)] = {
        "level": 60,
        "build_mode": "equipment-build",
        "wengine_id": "wengine:14120",
        "wengine_level": 60,
        "wengine_refinement": 1,
        "drive_discs": [],
    }
    equipped["enabled_rule_item_ids"] = ["rule:wengine:14120:owner:1201:electric-dash-damage"]
    with_signature_rule = _calculate(equipped)
    assert len(with_signature_rule["events"]) == 1
    assert with_signature_rule["totals"]["expected"]["complete"] is False
    assert any("Dash Attack tag" in item["message"] for item in with_signature_rule["diagnostics"])
