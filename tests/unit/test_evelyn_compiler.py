from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.evelyn import EvelynCompileConfig, compile_evelyn, load_raw_record
from core.application.characters.templates import DirectDamageEventTemplate
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, compile_wengine
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import registration_for
from core.types import CharacterId, DamageTag, Element, SkillGroup, WEngineBuildInput, WEngineId
from web.api import app


client = TestClient(app)
_ID = "character:1321"
_CORE_CR = "rule:character:1321:core:constraint-crit-rate"
_C1_IGNORE = "rule:character:1321:cinema1:imprisoned-defense-ignore"
_C2_ATTACK = "rule:character:1321:cinema2:attack"
_EXTRA = "rule:character:1321:extra-ability:chain-ultimate"
_C6 = "rule:character:1321:cinema6:shadow-edge"


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
    config_overrides: dict[str, object] | None = None,
    enabled: tuple[str, ...] = (),
    conditions: dict[str, bool] | None = None,
    resistance: float = 0.0,
    signature_refinement: int | None = None,
    crit_rate_override: float | None = None,
) -> dict[str, object]:
    team = [_ID, *(item for item in supporting if item != _ID)]
    compile_configs: dict[str, dict[str, object]] = {
        character_id: {
            "core_level": 7,
            "cinema_level": cinema if character_id == _ID else 0,
        }
        for character_id in team
    }
    if config_overrides:
        compile_configs[_ID].update(config_overrides)
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        builds[character_id] = {
            "level": 60,
            "build_mode": "equipment-build",
            "base_stats": _panel_stats(character_id),
            "drive_discs": [],
        }
        if character_id == _ID and crit_rate_override is not None:
            builds[character_id]["base_stats"]["crit_rate"] = crit_rate_override
        if character_id == _ID and signature_refinement is not None:
            builds[character_id]["wengine_id"] = "wengine:14132"
            builds[character_id]["wengine_refinement"] = signature_refinement
    return {
        "primary_character_id": _ID,
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": entry_id,
        "compile_configs": compile_configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:evelyn-test",
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


def _event_value(result: dict[str, object]) -> float:
    return result["events"][0]["modes"]["expected"]["value"]


def _ratio(definition, key: str) -> float:
    entry = next(item for item in definition.move_entries if str(item.entry_id).endswith(key))
    return entry.multiplier_variants[0].multiplier.value.value


def test_evelyn_live_identity_panel_and_signature() -> None:
    raw_data = load_character_record(_ID)
    raw = load_raw_record(raw_data)
    assert (raw.name, raw.code_name, raw.rarity) == ("伊芙琳", "Evelyn", 4)
    assert (raw.specialty, raw.element, raw.faction, raw.icon) == (
        "强攻",
        "火属性",
        "天琴座",
        "IconRole37",
    )
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1321.json",
    )
    assert EvelynCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12
    assert _ratio(compile_evelyn(EvelynCompileConfig(cinema_level=3), raw), "ultimate-sound") == pytest.approx(43.389)
    assert _ratio(compile_evelyn(EvelynCompileConfig(cinema_level=5), raw), "ultimate-sound") == pytest.approx(47.005)
    assert _ID in supported_character_ids()
    assert registration_for(CharacterId(_ID)).base_element is Element.FIRE
    catalog = next(item for item in supported_character_catalog() if item.character_id == _ID)
    assert (catalog.display_name, catalog.code_name, catalog.rarity) == ("伊芙琳", "Evelyn", "S")

    panel = character_base_stats(CharacterId(_ID))
    assert panel.attack.value == pytest.approx(929.7586)
    assert panel.hp.value == pytest.approx(7788.6961)
    assert panel.defense.value == pytest.approx(612.6038)
    assert panel.crit_rate.value == pytest.approx(0.194)
    assert panel.energy_regen.value == pytest.approx(1.2)
    assert SIGNATURE_WENGINE_BY_CHARACTER[CharacterId(_ID)] == WEngineId("wengine:14132")

    engine = compile_wengine(
        WEngineBuildInput(
            wengine_id=WEngineId("wengine:14132"),
            equipped_character_id=CharacterId(_ID),
            refinement=1,
        ),
        owner_capabilities=registration_for(CharacterId(_ID)).equipment_capabilities,
    )
    assert engine.contributions


def test_evelyn_reviewed_curves_and_basic_element_groups() -> None:
    raw = load_raw_record(load_character_record(_ID))
    definition = compile_evelyn(EvelynCompileConfig(), raw)
    expected = {
        "basic-stage-1": 1.029,
        "basic-stage-2": 1.248,
        "basic-stage-3": 1.574,
        "basic-stage-4": 3.737,
        "basic-stage-5": 4.478,
        "basic-stage-3-after-cancel": 1.574,
        "strangle-i": 4.530,
        "strangle-ii": 4.905,
        "dash-attack": 1.210,
        "dodge-counter": 4.214,
        "special-lock": 1.051,
        "chain-attack": 16.587,
        "ultimate-sound": 39.773,
        "ultimate-shadow": 39.773,
        "quick-assist": 1.552,
        "assist-strike": 5.842,
        "special-rupture-i-full": 1.492,
        "ex-special-rupture-final-full": 12.025,
    }
    for key, ratio in expected.items():
        assert _ratio(definition, key) == pytest.approx(ratio)
    stage_elements = {
        f"move-entry:character:1321:basic-stage-{stage}": (
            Element.PHYSICAL if stage <= 3 else Element.FIRE
        )
        for stage in range(1, 6)
    }
    for entry_id, element in stage_elements.items():
        entry = next(item for item in definition.move_entries if str(item.entry_id) == entry_id)
        assert entry.main_damage_event.element is element

    result = _calculate(_payload("move-entry:character:1321:basic-stage-4"))
    assert len(result["events"]) == 1
    assert result["events"][0]["element"] == "fire"
    assert result["totals"]["expected"]["complete"] is True
    cancelled_third = _calculate(
        _payload("move-entry:character:1321:basic-stage-3-after-cancel")
    )
    assert cancelled_third["events"][0]["element"] == "fire"


def test_evelyn_core_and_cinema_states_are_scoped() -> None:
    dash_id = "move-entry:character:1321:dash-attack"
    base = _calculate(_payload(dash_id))
    core = _calculate(
        _payload(
            dash_id,
            config_overrides={"constraint_crit_active": True},
            enabled=(_CORE_CR,),
        )
    )
    base_snapshot = base["resolved_character_snapshots"][0]["stats"]
    core_snapshot = core["resolved_character_snapshots"][0]["stats"]
    assert core_snapshot["crit_rate"] == pytest.approx(base_snapshot["crit_rate"] + 0.25)

    attack_c2 = _calculate(
        _payload(
            dash_id,
            cinema=2,
            enabled=(_C2_ATTACK,),
        )
    )
    c2_snapshot = attack_c2["resolved_character_snapshots"][0]["stats"]
    assert c2_snapshot["attack"] == pytest.approx(base_snapshot["attack"] * 1.15)

    direct = _calculate(
        _payload(
            dash_id,
            cinema=1,
            config_overrides={"target_imprisoned": True},
            enabled=(_C1_IGNORE,),
            resistance=0.0,
        )
    )
    assert next(
        item["value"]
        for item in direct["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "defense.damage-ignore"
    ) == pytest.approx(0.12)

    unbound_target = _calculate(
        _payload(
            dash_id,
            cinema=1,
            enabled=(_C1_IGNORE,),
            resistance=0.0,
        )
    )
    assert next(
        item["value"]
        for item in unbound_target["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "defense.damage-ignore"
    ) == pytest.approx(0.0)

    shielded = _calculate(
        _payload(
            dash_id,
            cinema=4,
            config_overrides={"cinema4_shield_active": True},
            enabled=("rule:character:1321:cinema4:shield-crit-damage",),
        )
    )
    shielded_stats = shielded["resolved_character_snapshots"][0]["stats"]
    assert shielded_stats["crit_damage"] == pytest.approx(0.9)


def test_evelyn_extra_ability_and_c6_child_are_single_and_typed() -> None:
    chain = _calculate(
        _payload(
            "move-entry:character:1321:chain-attack",
            supporting=("character:1141",),
            enabled=(_EXTRA,),
        )
    )
    assert next(
        item["value"]
        for item in chain["events"][0]["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    ) == pytest.approx(0.30)

    dash = _calculate(
        _payload(
            "move-entry:character:1321:dash-attack",
            cinema=6,
            config_overrides={"cinema6_shadow_edge_active": True},
            enabled=(_C6,),
        )
    )
    assert len(dash["events"]) == 2
    parent, child = dash["events"]
    assert parent["element"] == "physical"
    assert child["element"] == "fire"
    assert child["damage_type"] == "direct"
    assert child["modes"]["expected"]["value"] is not None
    definition = compile_evelyn(
        EvelynCompileConfig(cinema_level=6, cinema6_shadow_edge_active=True),
        load_raw_record(load_character_record(_ID)),
    )
    child_template = next(
        item
        for item in definition.damage_event_templates
        if "cinema6-shadow-edge-child:dash-attack" in str(item.ref.template_id)
    )
    assert isinstance(child_template, DirectDamageEventTemplate)
    assert child_template.ref.skill_group is SkillGroup.CHAIN_ATTACK
    assert child_template.ref.damage_tags == frozenset({DamageTag.CHAIN_ATTACK})

    supported_dash = _calculate(
        _payload(
            "move-entry:character:1321:dash-attack",
            supporting=("character:1141",),
            cinema=6,
            config_overrides={"cinema6_shadow_edge_active": True},
            enabled=(_C6, _EXTRA),
        )
    )
    child = supported_dash["events"][1]
    child_normal_bonus = next(
        item["value"]
        for item in child["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    )
    assert child_normal_bonus == pytest.approx(0.30)
    assert len(_calculate(_payload("move-entry:character:1321:chain-attack", cinema=6, config_overrides={"cinema6_shadow_edge_active": True}, enabled=(_C6,)))["events"]) == 1

    base_chain = _calculate(
        _payload(
            "move-entry:character:1321:chain-attack",
            supporting=("character:1141",),
            crit_rate_override=0.8,
        )
    )
    high_crit_chain = _calculate(
        _payload(
            "move-entry:character:1321:chain-attack",
            supporting=("character:1141",),
            crit_rate_override=0.8,
            enabled=(_EXTRA,),
        )
    )
    below_threshold_chain = _calculate(
        _payload(
            "move-entry:character:1321:chain-attack",
            supporting=("character:1141",),
            crit_rate_override=0.79,
            enabled=(_EXTRA,),
        )
    )
    base_chain_below_threshold = _calculate(
        _payload(
            "move-entry:character:1321:chain-attack",
            supporting=("character:1141",),
            crit_rate_override=0.79,
        )
    )
    assert _event_value(high_crit_chain) / _event_value(base_chain) == pytest.approx(1.625)
    assert _event_value(below_threshold_chain) / _event_value(base_chain_below_threshold) == pytest.approx(1.3)

    standalone = _calculate(
        _payload(
            "move-entry:character:1321:cinema6-shadow-edge-single",
            cinema=6,
        )
    )
    assert len(standalone["events"]) == 1
    assert standalone["events"][0]["element"] == "fire"
