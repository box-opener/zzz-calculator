from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.soukaku import (
    SOUKAKU_ID,
    SOUKAKU_REVIEWED_MAPPING,
    SoukakuCompileConfig,
    compile_soukaku,
    load_raw_record,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER
from core.application.equipment.wengine import load_wengine_raw_record
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    _soukaku_additional_ability_eligibility,
    config_fields_for,
    registration_for,
)
from core.types import (
    CharacterId,
    CharacterRole,
    DamageTag,
    Element,
    EffectTarget,
    PanelStatDerivedValue,
    Resolved,
    SkillGroup,
)
from web.api import app


client = TestClient(app)


def _definition(*, cinema: int = 0, skill_levels=(), eligible: bool = False):
    raw = load_raw_record(load_character_record(str(SOUKAKU_ID)))
    return compile_soukaku(
        SoukakuCompileConfig(
            cinema_level=cinema,
            skill_levels=tuple(skill_levels),
            additional_ability_eligible=eligible,
        ),
        raw,
    )


def _entries(definition):
    return {str(item.entry_id).rsplit(":", 1)[-1]: item for item in definition.move_entries}


def _ratio(entry) -> float:
    value = entry.multiplier_variants[0].multiplier.value
    assert isinstance(value, Resolved)
    return value.value


def test_soukaku_live_source_identity_signature_and_level_60_panel() -> None:
    source = load_character_record(str(SOUKAKU_ID))
    raw = load_raw_record(source)
    assert raw.name == "苍角"
    assert raw.code_name == "Soukaku"
    assert raw.specialty == "支援"
    assert raw.element == "冰属性"
    assert raw.faction == "对空洞特别行动部第六课"
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1131.json",
    )
    assert raw.icon == "IconRole17"
    assert raw.rarity == 3
    assert raw.potential_details == ()

    panel = character_base_stats(SOUKAKU_ID)
    assert panel.hp.value == pytest.approx(8025.9663)
    assert panel.attack.value == pytest.approx(665.8333)
    assert panel.defense.value == pytest.approx(597.5915)
    assert panel.impact.value == pytest.approx(86.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(96.0)
    assert panel.anomaly_mastery.value == pytest.approx(93.0)
    assert panel.energy_regen.value == pytest.approx(1.56)

    assert SIGNATURE_WENGINE_BY_CHARACTER[SOUKAKU_ID] == "wengine:13113"
    engine = load_wengine_raw_record("wengine:13113")
    assert engine.name == "含羞恶面"
    assert engine.icon == "Weapon_A_1131"
    assert engine.specialty is CharacterRole.SUPPORT
    assert engine.base_attack == pytest.approx(624.0)
    assert engine.advanced_stat_value == pytest.approx(0.25)
    assert engine.icon == "Weapon_A_1131"
    assert SoukakuCompileConfig().core_level == 7
    assert SoukakuCompileConfig().cinema_level == 0
    assert SoukakuCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 16


def test_soukaku_reviewed_direct_curves_preserve_source_elements_and_expressions() -> None:
    definition = _definition()
    entries = _entries(definition)
    assert len(entries) == 26

    assert [_ratio(entries[f"basic-rice-cake-{stage}"]) for stage in range(1, 4)] == pytest.approx(
        [1.577, 5.118, 6.936]
    )
    assert [_ratio(entries[f"basic-frost-banner-{stage}"]) for stage in range(1, 4)] == pytest.approx(
        [1.816, 5.405, 12.089]
    )
    assert entries["basic-rice-cake-1"].main_damage_event.element is Element.PHYSICAL
    assert entries["basic-frost-banner-1"].main_damage_event.element is Element.ICE
    assert entries["dash-half-share"].main_damage_event.element is Element.PHYSICAL
    assert entries["dash-frost-banner"].main_damage_event.element is Element.ICE
    assert DamageTag.EX_SPECIAL_ATTACK in entries["ex-swat-insects-continuous"].damage_tags
    assert DamageTag.SPECIAL_ATTACK not in entries["ex-swat-insects-continuous"].damage_tags

    # 1131011 is a 620.9% raw L16 curve; Nanoka's parameter desc explicitly divides it by 2.
    assert _ratio(entries["ex-swat-insects-continuous"]) == pytest.approx(3.1045)
    assert _ratio(entries["ex-swat-insects-windfield"]) == pytest.approx(2.416)
    # The source description explicitly sums these two assist-strike curves.
    assert _ratio(entries["assist-strike-sweeping-blow"]) == pytest.approx(8.917)
    assert _ratio(entries["special-cool-lunch-complete"]) == pytest.approx(3.04)
    assert _ratio(entries["flag-attack-and-collect"]) == pytest.approx(11.716)
    assert _ratio(entries["flag-quick-attack-and-collect"]) == pytest.approx(9.116)

    basic_ult = _definition(
        cinema=0,
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
    )
    cinema3_ult = _definition(
        cinema=3,
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
    )
    cinema5_ult = _definition(
        cinema=5,
        skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
    )
    assert _ratio(_entries(basic_ult)["ultimate-large-goose-chicken-slash"]) == pytest.approx(39.797)
    assert _ratio(_entries(cinema3_ult)["ultimate-large-goose-chicken-slash"]) == pytest.approx(43.415)
    assert _ratio(_entries(cinema5_ult)["ultimate-large-goose-chicken-slash"]) == pytest.approx(47.033)


def test_soukaku_core_and_cinema_effects_keep_self_target_and_ice_scopes() -> None:
    definition = _definition(cinema=6, eligible=True)
    rules = {str(item.rule_id): item for item in definition.rule_items}
    core = rules["rule:character:1131:core:flag-attack-self-atk"]
    assert core.condition_ids
    core_effect = core.effects[0]
    assert core_effect.rule.target is EffectTarget.SELF
    assert isinstance(core_effect.result.value, PanelStatDerivedValue)
    assert core_effect.result.value.source_node.value == "character.initial.attack"
    assert core_effect.result.value.coefficient == Resolved(0.20)
    assert core_effect.result.value.cap_max == Resolved(500.0)

    consumed = rules["rule:character:1131:core:flag-attack-consumed-vortex-extra-atk"]
    assert len(consumed.effects) == 1
    assert consumed.effects[0].rule.target is EffectTarget.SELF
    assert isinstance(consumed.effects[0].result.value, PanelStatDerivedValue)

    extra = rules["rule:character:1131:extra-ability:ice-damage"]
    assert extra.eligibility.value == "eligible"
    assert len(extra.effects) == 1
    assert extra.effects[0].rule.target is EffectTarget.TEAM
    assert extra.effects[0].result.modifier_path.value == "damage.normal-bonus"

    cinema4 = rules["rule:character:1131:cinema4:enemy-ice-resistance-reduction"]
    assert cinema4.eligibility.value == "eligible"
    assert cinema4.effects[0].result.value == Resolved(0.10)
    assert cinema4.effects[0].rule.target is EffectTarget.ENEMY
    cinema6 = rules["rule:character:1131:cinema6:frost-banner-enhanced-basic-and-dash"]
    assert cinema6.eligibility.value == "eligible"
    assert cinema6.effects[0].result.value == Resolved(0.45)
    assert cinema6.effects[0].rule.target is EffectTarget.SELF
    assert len(SOUKAKU_REVIEWED_MAPPING.moves) == 20

    cinema0 = {str(item.rule_id): item for item in _definition().rule_items}
    assert cinema0["rule:character:1131:cinema4:enemy-ice-resistance-reduction"].eligibility.value == "ineligible"
    assert cinema0["rule:character:1131:cinema6:frost-banner-enhanced-basic-and-dash"].eligibility.value == "ineligible"


def test_soukaku_additional_ability_uses_another_real_teammate() -> None:
    assert _soukaku_additional_ability_eligibility(
        (SOUKAKU_ID, CharacterId("character:1051"))
    )
    assert not _soukaku_additional_ability_eligibility(
        (SOUKAKU_ID, CharacterId("character:1071"))
    )


def test_soukaku_registry_has_support_role_and_real_element_damage_scopes() -> None:
    registration = registration_for(SOUKAKU_ID)
    assert registration.role is CharacterRole.SUPPORT
    assert registration.base_element is Element.ICE
    assert registration.catalog.display_name == "苍角"
    assert registration.catalog.element == "ice"
    config_fields = {
        item.field_id: item
        for item in config_fields_for(SOUKAKU_ID, {}, [SOUKAKU_ID])
    }
    assert config_fields["core_level"].value == 7
    assert config_fields["cinema_level"].value == 0
    assert config_fields["core_level"].field_type == "slider"
    assert config_fields["cinema_level"].field_type == "slider"
    assert {
        key: item.value
        for key, item in config_fields.items()
        if key.startswith("skill_level:")
    } == {
        f"skill_level:{group.value}": 16
        for group in SkillGroup
        if f"skill_level:{group.value}" in config_fields
    }
    scopes = registration.equipment_capabilities.damage_scopes
    assert any(
        scope.element is Element.PHYSICAL
        and scope.skill_group is SkillGroup.BASIC_ATTACK
        and scope.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
        for scope in scopes
    )
    assert any(
        scope.element is Element.ICE
        and scope.skill_group is SkillGroup.BASIC_ATTACK
        and scope.damage_tags == frozenset({DamageTag.BASIC_ATTACK})
        for scope in scopes
    )


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


def _api_payload(
    move_entry_id: str,
    *,
    extra_active: bool,
    primary_character_id: str = str(SOUKAKU_ID),
    supporting_character_id: str = "character:1051",
) -> dict:
    team = (primary_character_id, supporting_character_id)
    return {
        "primary_character_id": primary_character_id,
        "supporting_character_ids": [supporting_character_id],
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": {
            item: {"core_level": 7, "cinema_level": 0} for item in team
        },
        "condition_values": {
            "condition:soukaku:frost-banner-active": True,
            "condition:soukaku:ice-damage-buff-active": extra_active,
        },
        "parameter_values": {
            "parameter:soukaku:ice-disorder-remaining-seconds": 10,
        },
        "enabled_rule_item_ids": (
            ["rule:character:1131:extra-ability:ice-damage"]
            if extra_active
            else []
        ),
        "selected_trigger_inputs": [],
        "rule_stack_counts": {},
        "character_builds": {
            item: {"level": 60, "out_of_combat_stats": _api_stats(item)}
            for item in team
        },
        "enemy": {
            "enemy_id": "enemy:soukaku-test",
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


def _api_result(
    move_entry_id: str,
    *,
    extra_active: bool,
    primary_character_id: str = str(SOUKAKU_ID),
    supporting_character_id: str = "character:1051",
) -> dict:
    response = client.post(
        "/api/v1/moves/calculate",
        json=_api_payload(
            move_entry_id,
            extra_active=extra_active,
            primary_character_id=primary_character_id,
            supporting_character_id=supporting_character_id,
        ),
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["totals"]["expected"]["complete"] is True, result
    return result


def _expected_value(result: dict) -> float:
    return result["totals"]["expected"]["value"]


def test_soukaku_ice_bonus_is_captured_once_for_anomaly_and_not_reapplied_to_disorder() -> None:
    direct_entry = "move-entry:character:1131:basic-frost-banner-1"
    anomaly_entry = "move-entry:character:1131:ice-anomaly"
    disorder_entry = "move-entry:character:1131:ice-disorder"

    direct_off = _api_result(direct_entry, extra_active=False)
    direct_on = _api_result(direct_entry, extra_active=True)
    assert _expected_value(direct_on) / _expected_value(direct_off) == pytest.approx(1.20)

    anomaly_off = _api_result(anomaly_entry, extra_active=False)
    anomaly_on = _api_result(anomaly_entry, extra_active=True)
    assert _expected_value(anomaly_on) / _expected_value(anomaly_off) == pytest.approx(1.20)

    disorder_off = _api_result(disorder_entry, extra_active=False)
    disorder_on = _api_result(disorder_entry, extra_active=True)
    assert _expected_value(disorder_on) / _expected_value(disorder_off) == pytest.approx(1.20)

    yidhari_entry = "move-entry:character:1051:basic-shattered-strike-1"
    yidhari_off = _api_result(
        yidhari_entry,
        extra_active=False,
        primary_character_id="character:1051",
        supporting_character_id=str(SOUKAKU_ID),
    )
    yidhari_on = _api_result(
        yidhari_entry,
        extra_active=True,
        primary_character_id="character:1051",
        supporting_character_id=str(SOUKAKU_ID),
    )
    assert yidhari_on["events"][0]["damage_type"] == "penetration"
    assert _expected_value(yidhari_on) / _expected_value(yidhari_off) == pytest.approx(1.20)


def test_soukaku_core_initial_atk_buff_is_self_scoped_and_consumption_doubles_it() -> None:
    base_rule = "rule:character:1131:core:flag-attack-self-atk"
    consumed_rule = "rule:character:1131:core:flag-attack-consumed-vortex-extra-atk"
    base_payload = _api_payload(
        "move-entry:character:1131:basic-rice-cake-1",
        extra_active=False,
    )
    base_payload["condition_values"]["condition:soukaku:flag-attack-buff-active"] = True
    base_payload["enabled_rule_item_ids"] = [base_rule]
    base_result = client.post("/api/v1/moves/calculate", json=base_payload)
    assert base_result.status_code == 200, base_result.text
    base_result = base_result.json()

    consumed_payload = _api_payload(
        "move-entry:character:1131:basic-rice-cake-1",
        extra_active=False,
    )
    consumed_payload["condition_values"].update(
        {
            "condition:soukaku:flag-attack-buff-active": True,
            "condition:soukaku:flag-consumed-vortex": True,
        }
    )
    consumed_payload["enabled_rule_item_ids"] = [base_rule, consumed_rule]
    consumed_response = client.post("/api/v1/moves/calculate", json=consumed_payload)
    assert consumed_response.status_code == 200, consumed_response.text
    consumed_result = consumed_response.json()

    def current_attack(result: dict, character_id: str) -> float:
        snapshot = next(
            item
            for item in result["resolved_character_snapshots"]
            if item["character_id"] == character_id
        )
        return snapshot["stats"]["attack"]

    assert current_attack(base_result, str(SOUKAKU_ID)) == pytest.approx(799.0)
    assert current_attack(consumed_result, str(SOUKAKU_ID)) == pytest.approx(932.16662)
    assert current_attack(base_result, "character:1051") == pytest.approx(859.9099)
    assert current_attack(consumed_result, "character:1051") == pytest.approx(859.9099)
