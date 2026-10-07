from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.lycaon import (
    LYCAON_ID,
    LycaonCompileConfig,
    compile_lycaon,
    load_raw_record,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.registry import (
    _lycaon_additional_ability_eligibility,
    config_fields_for,
)
from core.types import (
    CharacterId,
    CharacterRole,
    DamageTag,
    Element,
    EffectTarget,
    EnemyStateFilter,
    NotCondition,
    Resolved,
    SkillGroup,
)
from web.api import app


client = TestClient(app)


def _definition(*, potential: int = 0, cinema: int = 0, skills=(), eligible: bool = False):
    raw = load_raw_record(
        load_character_record(str(LYCAON_ID)),
        potential_level=potential,
    )
    return compile_lycaon(
        LycaonCompileConfig(
            cinema_level=cinema,
            potential_level=potential,
            skill_levels=tuple(skills),
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


def test_lycaon_source_metadata_stats_signature_and_rank_defaults_are_reviewed() -> None:
    source = load_character_record(str(LYCAON_ID))
    raw = load_raw_record(source)
    assert str(LYCAON_ID) in supported_character_ids()
    assert raw.name == "莱卡恩"
    assert raw.code_name == "Lycaon"
    assert raw.specialty == "击破"
    assert raw.element == "冰属性"
    assert raw.faction == "维多利亚家政"
    assert raw.icon == "IconRole18"
    assert raw.rarity == 4
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1141.json",
    )
    assert tuple(item.level for item in raw.potential_details) == (1, 2, 3, 4, 5, 6)

    panel = character_base_stats(LYCAON_ID)
    assert panel.attack.value == pytest.approx(728.5933)
    assert panel.hp.value == pytest.approx(8416.2915)
    assert panel.defense.value == pytest.approx(606.5977)
    assert panel.impact.value == pytest.approx(137.0)
    assert panel.crit_rate.value == pytest.approx(0.05)
    assert panel.crit_damage.value == pytest.approx(0.5)
    assert panel.anomaly_proficiency.value == pytest.approx(90.0)
    assert panel.anomaly_mastery.value == pytest.approx(91.0)

    assert SIGNATURE_WENGINE_BY_CHARACTER[LYCAON_ID] == "wengine:14114"
    engine = load_wengine_raw_record("wengine:14114")
    assert engine.name == "拘缚者"
    assert engine.icon == "Weapon_S_1141"
    assert engine.specialty is CharacterRole.STUN
    assert engine.base_attack == pytest.approx(684.0)
    assert engine.advanced_stat_value == pytest.approx(0.18)
    assert LycaonCompileConfig().core_level == 7
    assert LycaonCompileConfig().cinema_level == 0
    assert LycaonCompileConfig().potential_level == 0
    assert LycaonCompileConfig().skill_level_for(SkillGroup.ULTIMATE) == 12

    config_fields = {
        item.field_id: item
        for item in config_fields_for(LYCAON_ID, {}, [LYCAON_ID])
    }
    assert config_fields["core_level"].value == 7
    assert config_fields["cinema_level"].value == 0
    assert config_fields["potential_level"].value == 0
    assert config_fields["potential_level"].field_type == "slider"
    assert config_fields["potential_level"].minimum == 0
    assert config_fields["potential_level"].maximum == 6


def test_lycaon_direct_moves_use_their_raw_skill_curves_and_summed_special_components() -> None:
    base = _entries(_definition())
    assert len(base) == 23
    assert _ratio(base["basic-physical-1"]) == pytest.approx(0.589)
    assert _ratio(base["basic-physical-5"]) == pytest.approx(3.622)
    assert _ratio(base["basic-charge-ice-1"]) == pytest.approx(0.745)
    assert _ratio(base["basic-charge-ice-stage5-tier1"]) == pytest.approx(5.559)
    assert _ratio(base["basic-charge-ice-stage5-tier2"]) == pytest.approx(7.121)
    assert base["basic-physical-1"].main_damage_event.element is Element.PHYSICAL
    assert base["basic-charge-ice-1"].main_damage_event.element is Element.ICE
    assert "physical-anomaly" not in base
    assert "physical-disorder" not in base
    assert _ratio(base["special-hunting-hour-normal"]) == pytest.approx(1.552)
    assert _ratio(base["special-hunting-hour-charged"]) == pytest.approx(2.673)
    assert _ratio(base["ex-special-hunting-hour-normal"]) == pytest.approx(10.70)
    assert _ratio(base["ex-special-hunting-hour-charged"]) == pytest.approx(15.804)
    assert DamageTag.EX_SPECIAL_ATTACK in base["ex-special-hunting-hour-normal"].damage_tags
    assert DamageTag.SPECIAL_ATTACK not in base["ex-special-hunting-hour-normal"].damage_tags

    ultimate_12 = _entries(
        _definition(skills=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),))
    )["ultimate-unblemished-duty"]
    ultimate_14 = _entries(
        _definition(
            cinema=3,
            skills=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
        )
    )["ultimate-unblemished-duty"]
    ultimate_16 = _entries(
        _definition(
            cinema=5,
            skills=(CharacterSkillLevel(SkillGroup.ULTIMATE, 12),),
        )
    )["ultimate-unblemished-duty"]
    assert _ratio(ultimate_12) == pytest.approx(33.892)
    assert _ratio(ultimate_14) == pytest.approx(36.974)
    assert _ratio(ultimate_16) == pytest.approx(40.056)


def test_lycaon_potential_projection_unlocks_ice_dance_and_levels_off_field_impact() -> None:
    p0 = _entries(_definition(potential=0))
    p1_definition = _definition(potential=1)
    p1 = _entries(p1_definition)
    assert "assist-strike-ice-dance" not in p0
    assert "assist-strike-ice-dance" in p1
    assert _ratio(p1["assist-strike-ice-dance"]) == pytest.approx(8.221)
    assert "hunt-off-field-basic-sequence" in p1
    assert "hunt-counter-basic3-followup" in p1
    assert len(p1_definition.independent_derived_damage_events) == 3

    expected = {2: 0.05, 3: 0.075, 4: 0.10, 5: 0.125, 6: 0.15}
    for potential, bonus in expected.items():
        definition = _definition(potential=potential)
        rule = next(
            item
            for item in definition.rule_items
            if str(item.rule_id)
            == f"rule:character:1141:potential{potential}:off-field-impact"
        )
        effect = rule.effects[0]
        assert effect.result.value == Resolved(bonus)
        assert effect.result.modifier_path.value == "character.combat.impact-percent-bonus"
        assert isinstance(effect.rule.condition, NotCondition)
    assert _definition(potential=2).scenario_conditions[0].condition_id is not None


def test_lycaon_core_extra_ability_and_cinema_scopes_are_typed() -> None:
    definition = _definition(potential=1, cinema=6, eligible=True)
    rules = {str(item.rule_id): item for item in definition.rule_items}
    ice_res = rules["rule:character:1141:core:enemy-ice-resistance-reduction"]
    assert ice_res.effects[0].result.value == Resolved(0.25)
    assert ice_res.effects[0].rule.target is EffectTarget.ENEMY
    assert len(ice_res.effects[0].rule.filters) == 1
    assert "ice:lieshuang" in str(ice_res.effects[0].rule.filters)

    other_vulnerability = rules["rule:character:1141:potential-core:other-element-vulnerability"]
    assert other_vulnerability.effects[0].result.value == Resolved(0.30)
    assert other_vulnerability.effects[0].result.modifier_path.value == "vulnerability.enemy-normal"

    extra = rules["rule:character:1141:extra-ability:enemy-stun-vulnerability"]
    assert extra.eligibility.value == "eligible"
    assert extra.effects[0].result.value == Resolved(0.35)
    assert extra.effects[0].result.modifier_path.value == "vulnerability.enemy-stun"
    assert isinstance(extra.effects[0].rule.filters[0], EnemyStateFilter)

    cinema6 = rules["rule:character:1141:cinema6:current-damage-bonus-stacks"]
    assert cinema6.stack_count == 5
    assert cinema6.stack_min == 0
    assert cinema6.stack_max == 5
    assert cinema6.effects[0].result.value == Resolved(0.10)
    assert cinema6.effects[0].result.modifier_path.value == "damage.normal-bonus"


def test_lycaon_additional_ability_eligibility_uses_team_element_faction_and_potential() -> None:
    assert _lycaon_additional_ability_eligibility(
        (LYCAON_ID, CharacterId("character:1051")), 0
    )
    assert _lycaon_additional_ability_eligibility(
        (LYCAON_ID, CharacterId("character:1331")), 1
    )
    assert not _lycaon_additional_ability_eligibility(
        (LYCAON_ID, CharacterId("character:1071")), 0
    )


def _stats_for(character_id: str) -> dict:
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


def _payload(
    move_entry_id: str,
    *,
    potential: int = 0,
    cinema: int = 0,
    enemy_stunned: bool = False,
    enabled: tuple[str, ...] = (),
    conditions: dict[str, bool] | None = None,
    stacks: dict[str, int] | None = None,
    team: tuple[str, ...] = (str(LYCAON_ID),),
    lycaon_signature: bool = False,
) -> dict:
    configs = {
        character_id: {"core_level": 7, "cinema_level": 0}
        for character_id in team
    }
    configs[str(LYCAON_ID)] = {
        "core_level": 7,
        "cinema_level": cinema,
        "potential_level": potential,
    }
    builds = {
        character_id: {"level": 60, "out_of_combat_stats": _stats_for(character_id)}
        for character_id in team
    }
    if lycaon_signature:
        builds[str(LYCAON_ID)] = {
            "level": 60,
            "build_mode": "equipment-build",
            "wengine_id": "wengine:14114",
            "wengine_level": 60,
            "wengine_refinement": 1,
            "drive_discs": [],
        }
    return {
        "primary_character_id": team[0],
        "supporting_character_ids": [item for item in team if item != team[0]],
        "team_character_ids": list(team),
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": {
            "parameter:lycaon:ice-disorder-remaining-seconds": 10,
        },
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": stacks or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:lycaon-test",
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
            "is_stunned": enemy_stunned,
        },
    }


def _calculate(payload: dict) -> dict:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _node(event: dict, node: str, mode: str = "expected") -> float:
    return next(
        row["value"]
        for row in event["modes"][mode]["calculation_breakdown"]
        if row["node"] == node
    )


def test_lycaon_c6_current_stacks_apply_to_own_damage_without_move_restriction() -> None:
    entry = "move-entry:character:1141:basic-physical-1"
    rule = "rule:character:1141:cinema6:current-damage-bonus-stacks"
    zero = _calculate(
        _payload(entry, cinema=6, enabled=(rule,), stacks={rule: 0})
    )
    five = _calculate(
        _payload(entry, cinema=6, enabled=(rule,), stacks={rule: 5})
    )
    assert _node(zero["events"][0], "damage.normal-bonus-region") == pytest.approx(1.0)
    assert _node(five["events"][0], "damage.normal-bonus-region") == pytest.approx(1.5)

    charged = _calculate(
        _payload(
            "move-entry:character:1141:basic-charge-ice-1",
            cinema=6,
            enabled=(rule,),
            stacks={rule: 5},
        )
    )
    assert _node(charged["events"][0], "damage.normal-bonus-region") == pytest.approx(1.5)


def test_lycaon_extra_ability_uses_the_actual_enemy_stun_state() -> None:
    entry = "move-entry:character:1141:dodge-counter-etiquette-lesson"
    rule = "rule:character:1141:extra-ability:enemy-stun-vulnerability"
    team = (str(LYCAON_ID), "character:1051")
    not_stunned = _calculate(
        _payload(entry, enabled=(rule,), enemy_stunned=False, team=team)
    )
    stunned = _calculate(
        _payload(entry, enabled=(rule,), enemy_stunned=True, team=team)
    )
    assert _node(not_stunned["events"][0], "vulnerability.additive-region") == pytest.approx(1.0)
    assert _node(stunned["events"][0], "vulnerability.additive-region") == pytest.approx(1.35)


def test_lycaon_core_ice_resistance_reduction_is_current_and_element_scoped() -> None:
    rule = "rule:character:1141:core:enemy-ice-resistance-reduction"
    condition = "condition:lycaon:core-ice-resistance-debuff-active"
    ice = _calculate(
        _payload(
            "move-entry:character:1141:ex-special-hunting-hour-normal",
            conditions={condition: True},
            enabled=(rule,),
        )
    )
    physical = _calculate(
        _payload(
            "move-entry:character:1141:basic-physical-1",
            conditions={condition: True},
            enabled=(rule,),
        )
    )
    assert _node(ice["events"][0], "resistance.enemy-reduction") == pytest.approx(0.25)
    assert _node(physical["events"][0], "resistance.enemy-reduction") == pytest.approx(0.0)


def test_lycaon_hunt_source_entries_create_only_the_declared_direct_followups() -> None:
    hunt = "condition:lycaon:hunt-off-field-active"
    basic_rule = "rule:character:1141:core:hunt-basic-sequence"
    basic = _calculate(
        _payload(
            "move-entry:character:1141:hunt-off-field-basic-sequence",
            potential=1,
            enabled=(basic_rule,),
            conditions={hunt: True},
        )
    )
    assert len(basic["events"]) == 3
    assert [item["element"] for item in basic["events"]] == [
        "physical",
        "physical",
        "physical",
    ]

    counter_rule = "rule:character:1141:core:hunt-counter-basic3-followup"
    counter = _calculate(
        _payload(
            "move-entry:character:1141:hunt-counter-basic3-followup",
            potential=1,
            enabled=(counter_rule,),
            conditions={hunt: True},
        )
    )
    assert len(counter["events"]) == 2
    assert [item["element"] for item in counter["events"]] == ["ice", "physical"]


def test_lycaon_potential_impact_is_current_only_when_hunt_is_active_off_field() -> None:
    rule = "rule:character:1141:potential6:off-field-impact"
    hunt = "condition:lycaon:hunt-off-field-active"
    active = _calculate(
        _payload(
            "move-entry:character:1051:basic-shattered-strike-1",
            potential=6,
            conditions={hunt: True},
            enabled=(rule,),
            team=("character:1051", str(LYCAON_ID)),
        )
    )
    lycaon = next(
        item
        for item in active["resolved_character_snapshots"]
        if item["character_id"] == str(LYCAON_ID)
    )
    assert lycaon["stats"]["impact"] == pytest.approx(157.55)

    inactive = _calculate(
        _payload(
            "move-entry:character:1051:basic-shattered-strike-1",
            potential=6,
            conditions={hunt: False},
            enabled=(rule,),
            team=("character:1051", str(LYCAON_ID)),
        )
    )
    lycaon_inactive = next(
        item
        for item in inactive["resolved_character_snapshots"]
        if item["character_id"] == str(LYCAON_ID)
    )
    assert lycaon_inactive["stats"]["impact"] == pytest.approx(137.0)


def test_lycaon_signature_14114_build_and_basic_only_stack_scope() -> None:
    rule = "rule:wengine:14114:owner:1141:basic-damage-daze-per-stack"
    basic = _calculate(
        _payload(
            "move-entry:character:1141:basic-physical-1",
            lycaon_signature=True,
            enabled=(rule,),
            stacks={rule: 5},
        )
    )
    lycaon = basic["resolved_character_snapshots"][0]
    assert lycaon["stats"]["attack"] == pytest.approx(1412.5933)
    assert lycaon["stats"]["impact"] == pytest.approx(161.66)
    assert _node(basic["events"][0], "damage.normal-bonus") == pytest.approx(0.30)

    ex_special = _calculate(
        _payload(
            "move-entry:character:1141:ex-special-hunting-hour-normal",
            lycaon_signature=True,
            enabled=(rule,),
            stacks={rule: 5},
        )
    )
    assert _node(ex_special["events"][0], "damage.normal-bonus") == pytest.approx(0.0)
