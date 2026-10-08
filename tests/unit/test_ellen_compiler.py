from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.ellen import (
    ELLEN_ID,
    EllenCompileConfig,
    compile_ellen,
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
from core.types import CharacterId, Element, SkillGroup, WEngineBuildInput, WEngineId
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
) -> dict[str, object]:
    team = [str(ELLEN_ID)]
    return {
        "primary_character_id": str(ELLEN_ID),
        "supporting_character_ids": [],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": {
            str(ELLEN_ID): {
                "core_level": 7,
                "cinema_level": cinema,
                "potential_level": potential,
            }
        },
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            str(ELLEN_ID): {
                "level": 60,
                "out_of_combat_stats": _stats(ELLEN_ID),
            }
        },
        "enemy": {
            "enemy_id": "enemy:ellen-test",
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


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _multi_character_payload(
    primary: str,
    supporting: list[str],
    move_entry_id: str,
    *,
    enabled: tuple[str, ...],
    conditions: dict[str, bool] | None = None,
    parameters: dict[str, int] | None = None,
) -> dict[str, object]:
    team = [primary, *supporting]
    ellen_config = {"core_level": 7, "cinema_level": 0, "potential_level": 2}
    configs = {
        character_id: (
            ellen_config
            if character_id == str(ELLEN_ID)
            else {"core_level": 7, "cinema_level": 0}
        )
        for character_id in team
    }
    return {
        "primary_character_id": primary,
        "supporting_character_ids": supporting,
        "team_character_ids": team,
        "formation_character_ids": [str(ELLEN_ID), "character:1141"],
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            character_id: {"level": 60, "out_of_combat_stats": _stats(CharacterId(character_id))}
            for character_id in team
        },
        "enemy": {
            "enemy_id": "enemy:ellen-team-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                "physical": 0.0,
                "fire": 0.0,
                "ice": 0.5,
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


def test_ellen_source_identity_defaults_and_signature_are_registered() -> None:
    raw = load_raw_record(load_character_record(str(ELLEN_ID)), potential_level=0)
    assert raw.name == "艾莲"
    assert raw.code_name == "Ellen"
    assert raw.rarity == 4
    assert raw.specialty == "强攻"
    assert raw.element == "冰属性"
    assert raw.faction == "维多利亚家政"
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1191.json"
    assert str(ELLEN_ID) in supported_character_ids()
    assert character_base_stats(ELLEN_ID).attack.value == pytest.approx(938.2102)
    assert character_base_stats(ELLEN_ID).hp.value == pytest.approx(7673.7042)
    assert character_base_stats(ELLEN_ID).defense.value == pytest.approx(606.5977)
    assert character_base_stats(ELLEN_ID).crit_rate.value == pytest.approx(0.194)
    assert EllenCompileConfig().core_level == 7
    assert EllenCompileConfig().cinema_level == 0
    assert EllenCompileConfig().potential_level == 0
    assert EllenCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    registration = registration_for(ELLEN_ID)
    assert registration.catalog.rarity == "S"
    assert next(item for item in supported_character_catalog() if item.character_id == str(ELLEN_ID)).code_name == "Ellen"
    assert registration.catalog.image_path == "/characters/portrait-placeholder.svg"
    assert SIGNATURE_WENGINE_BY_CHARACTER[ELLEN_ID] == WEngineId("wengine:14119")
    weapon = load_wengine_raw_record("wengine:14119")
    assert weapon.icon == "Weapon_S_1191"
    engine = compile_wengine(
        WEngineBuildInput(WEngineId("wengine:14119"), ELLEN_ID, refinement=1),
        owner_capabilities=registration.equipment_capabilities,
    )
    assert engine.complete is True
    assert engine.contributions[0].value.value == pytest.approx(713.0)
    assert engine.contributions[1].value.value == pytest.approx(0.24)


def test_ellen_reviewed_curves_and_potential_projection() -> None:
    source = load_character_record(str(ELLEN_ID))
    p0_raw = load_raw_record(source, potential_level=0)
    p1_raw = load_raw_record(source, potential_level=1)
    p6_raw = load_raw_record(source, potential_level=6)
    p0 = compile_ellen(EllenCompileConfig(), p0_raw)
    p1 = compile_ellen(EllenCompileConfig(potential_level=1), p1_raw)
    p6 = compile_ellen(EllenCompileConfig(potential_level=6), p6_raw)
    p0_entries = {str(item.entry_id): item for item in p0.move_entries}
    p1_entries = {str(item.entry_id): item for item in p1.move_entries}
    assert "move-entry:character:1191:potential1-ice-blade-wave-1" not in p0_entries
    assert "move-entry:character:1191:potential1-ice-blade-wave-1" in p1_entries
    assert p0_entries["move-entry:character:1191:basic-physical-1"].main_damage_event.element is Element.PHYSICAL
    assert p0_entries["move-entry:character:1191:basic-ice-1"].main_damage_event.element is Element.ICE
    assert p0_entries["move-entry:character:1191:basic-physical-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(0.983)
    assert p0_entries["move-entry:character:1191:ultimate-endless-winter"].multiplier_variants[0].multiplier.value.value == pytest.approx(37.817)
    assert p0_entries["move-entry:character:1191:dash-ice-quick-full"].multiplier_variants[0].multiplier.value.value > 0
    assert p0_entries["move-entry:character:1191:dash-ice-charged-full"].multiplier_variants[0].multiplier.value.value > p0_entries["move-entry:character:1191:dash-ice-quick-full"].multiplier_variants[0].multiplier.value.value
    assert len(p1_entries["move-entry:character:1191:basic-ice-3"].derived_damage_events) == 3
    assert p1_entries["move-entry:character:1191:basic-ice-3"].derived_damage_events[0].template.element is Element.ICE
    assert len(p6.rule_items) > len(p0.rule_items)


def test_ellen_p1_frost_edge_size_is_local_partial_and_never_a_fake_hit() -> None:
    entry = "move-entry:character:1191:basic-ice-3"
    rule = "rule:character:1191:potential1:frost-edge-follow-up"
    conditions = {"condition:ellen:ice-mode-active": True}
    unknown = _calculate(_payload(
        entry,
        potential=1,
        conditions=conditions,
        enabled=(rule,),
    ))
    assert unknown["events"][0]["damage_type"] == "direct"
    assert len(unknown["events"]) == 1
    assert unknown["totals"]["expected"]["complete"] is False
    assert any("霜锋" in item["message"] for item in unknown["diagnostics"])

    known = _calculate(_payload(
        entry,
        potential=1,
        conditions=conditions,
        parameters={"parameter:ellen:frost-edge-target-size": 2},
        enabled=(rule,),
    ))
    assert len(known["events"]) == 2
    assert known["events"][1]["damage_type"] == "direct"
    assert known["events"][1]["element"] == "ice"
    assert known["totals"]["expected"]["complete"] is True


def test_ellen_c2_charge_crit_damage_is_scoped_to_ex_special_only() -> None:
    rule = "rule:character:1191:cinema2:ex-current-charge-crit-damage"
    charges = "parameter:ellen:current-chill-charges-for-ex"
    ex_zero = _calculate(_payload(
        "move-entry:character:1191:ex-sweep",
        cinema=2,
        parameters={charges: 0},
        enabled=(rule,),
    ))
    ex_three = _calculate(_payload(
        "move-entry:character:1191:ex-sweep",
        cinema=2,
        parameters={charges: 3},
        enabled=(rule,),
    ))
    ex_six = _calculate(_payload(
        "move-entry:character:1191:ex-sweep",
        cinema=2,
        parameters={charges: 6},
        enabled=(rule,),
    ))
    basic_three = _calculate(_payload(
        "move-entry:character:1191:basic-physical-1",
        cinema=2,
        parameters={charges: 3},
        enabled=(rule,),
    ))
    assert ex_zero["events"][0]["modes"]["expected"]["value"] < ex_three["events"][0]["modes"]["expected"]["value"]
    assert ex_six["events"][0]["modes"]["expected"]["value"] == pytest.approx(ex_three["events"][0]["modes"]["expected"]["value"])
    assert basic_three["events"][0]["modes"]["expected"]["value"] == pytest.approx(
        _calculate(_payload("move-entry:character:1191:basic-physical-1", cinema=2))["events"][0]["modes"]["expected"]["value"]
    )


def test_ellen_charged_dash_core_and_c6_cover_the_complete_action() -> None:
    core_rule = "rule:character:1191:core:charged-moves-crit-damage"
    full_base = _calculate(_payload("move-entry:character:1191:dash-ice-charged-full"))
    full_combo = _calculate(_payload(
        "move-entry:character:1191:dash-ice-charged-full",
        enabled=(core_rule,),
    ))
    charged_shear = _calculate(_payload(
        "move-entry:character:1191:dash-ice-charged-shear",
        enabled=(core_rule,),
    ))
    assert len(full_combo["events"]) == 1
    assert full_combo["totals"]["expected"]["complete"] is True
    assert len(charged_shear["events"]) == 1
    assert charged_shear["totals"]["expected"]["complete"] is True
    assert full_combo["events"][0]["modes"]["expected"]["value"] > full_base["events"][0]["modes"]["expected"]["value"]

    c6_rule = "rule:character:1191:cinema6:charged-dash-feast-damage"
    full_c6_base = _calculate(_payload(
        "move-entry:character:1191:dash-ice-charged-full",
        cinema=6,
        parameters={"parameter:ellen:cinema6-feast-stacks": 3},
    ))
    full_combo_c6 = _calculate(_payload(
        "move-entry:character:1191:dash-ice-charged-full",
        cinema=6,
        parameters={"parameter:ellen:cinema6-feast-stacks": 3},
        enabled=(c6_rule,),
    ))
    charged_shear_c6 = _calculate(_payload(
        "move-entry:character:1191:dash-ice-charged-shear",
        cinema=6,
        parameters={"parameter:ellen:cinema6-feast-stacks": 3},
        enabled=(c6_rule,),
    ))
    assert full_combo_c6["totals"]["expected"]["complete"] is True
    assert charged_shear_c6["totals"]["expected"]["complete"] is True
    assert charged_shear_c6["events"][0]["modes"]["expected"]["value"] > charged_shear["events"][0]["modes"]["expected"]["value"]
    assert full_combo_c6["events"][0]["modes"]["expected"]["value"] > full_c6_base["events"][0]["modes"]["expected"]["value"]


def test_ellen_additional_ability_uses_ice_faction_or_potential_stun_eligibility() -> None:
    def preview(team: list[str], potential: int) -> dict[str, object]:
        response = client.post(
            "/api/v1/definitions/preview",
            json={
                "character_id": str(ELLEN_ID),
                "team_character_ids": team,
                "compile_config": {"core_level": 7, "cinema_level": 0, "potential_level": potential},
                "condition_values": {},
            },
        )
        assert response.status_code == 200, response.text
        return response.json()

    key = "rule:character:1191:extra-ability:subsequent-ice-damage"
    solo = preview([str(ELLEN_ID)], 0)
    same_element = preview([str(ELLEN_ID), "character:1131"], 0)
    stun_via_potential = preview([str(ELLEN_ID), "character:1141"], 1)
    assert next(item for item in solo["rule_items"] if item["rule_id"] == key)["eligibility"] == "ineligible"
    assert next(item for item in same_element["rule_items"] if item["rule_id"] == key)["eligibility"] == "eligible"
    assert next(item for item in stun_via_potential["rule_items"] if item["rule_id"] == key)["eligibility"] == "eligible"


def test_ellen_potential_ice_resistance_ignore_applies_only_to_ellen_events() -> None:
    rule = "rule:character:1191:potential2:extra-ability-stacks"
    parameters = {"parameter:ellen:extra-ability-ice-stacks": 10}
    own = _calculate(_multi_character_payload(
        str(ELLEN_ID),
        ["character:1141"],
        "move-entry:character:1191:basic-ice-1",
        enabled=(rule,),
        conditions={"condition:ellen:ice-mode-active": True},
        parameters=parameters,
    ))
    peer = _calculate(_multi_character_payload(
        "character:1141",
        [str(ELLEN_ID)],
        "move-entry:character:1141:basic-charge-ice-1",
        enabled=(rule,),
        parameters=parameters,
    ))
    own_modifiers = own["events"][0]["common_application_trace"]["applied_modifiers"]
    peer_modifiers = peer["events"][0]["common_application_trace"]["applied_modifiers"]
    assert any(item["effect_id"] == "effect:character:1191:potential2:ten-stack-ice-resistance-ignore" for item in own_modifiers)
    assert not any(item["effect_id"] == "effect:character:1191:potential2:ten-stack-ice-resistance-ignore" for item in peer_modifiers)
