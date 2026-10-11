from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.sigrid import (
    SIGRID_ID,
    SIGRID_REVIEWED_MAPPING,
    SigridCompileConfig,
    compile_sigrid,
    load_raw_record,
)
from core.application.characters.sigrid.compiler import (
    SIGRID_CINEMA1_OVERFLOW_ACTIVE,
    SIGRID_CORE_CRIT_BUFF_ACTIVE,
    SIGRID_ENEMY_WINDED,
    SIGRID_SKY_RIDER_STATE_ACTIVE,
)
from core.application.execution import DirectMoveApplicationService, MoveCalculationRequest
from core.application.ids import RuleItemId
from core.application.matching import CharacterMatchProfile, EnemyMatchProfile
from core.application.output import CritDisplayMode
from core.application.rules import RuleEligibility
from core.application.scenario import CalculationScenario
from core.application.equipment.wengine import SIGNATURE_WENGINE_BY_CHARACTER
from core.application.equipment.wengine_ids import WENGINE_CAVALRY_PRAISE_ID
from core.data.loader import load_character_record
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    build_registered_build_preview,
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import (
    AnyFilter,
    BattleStateId,
    CalculationNode,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    DamageDealerFilter,
    DamageType,
    DamageTypeFilter,
    EffectOperation,
    Element,
    ElementFilter,
    EnemyId,
    EnemySnapshot,
    EventTemplateIdFilter,
    OperationState,
    Resolved,
    SkillGroup,
    StateId,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "sigrid.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1591.json"


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _definition(
    *,
    core_level: int = 7,
    cinema_level: int = 0,
    character_level: int = 60,
    additional_ability_eligible: bool = False,
    sky_rider_state_active: bool = False,
    core_crit_buff_active: bool = False,
    enemy_winded: bool = False,
    chain_damage_buff_active: bool = False,
    cinema4_damage_buff_active: bool = False,
    cinema1_overflow_attack_active: bool = False,
):
    raw = load_raw_record(_source_data())
    config = SigridCompileConfig(
        core_level=core_level,
        cinema_level=cinema_level,
        character_level=character_level,
        additional_ability_eligible=additional_ability_eligible,
        sky_rider_state_active=sky_rider_state_active,
        core_crit_buff_active=core_crit_buff_active,
        enemy_winded=enemy_winded,
        chain_damage_buff_active=chain_damage_buff_active,
        cinema4_damage_buff_active=cinema4_damage_buff_active,
        cinema1_overflow_attack_active=cinema1_overflow_attack_active,
    )
    return raw, config, compile_sigrid(config, raw)


def _rule(definition, suffix: str):
    rule_id = f"rule:character:1591:{suffix}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _entry(definition, key: str):
    entry_id = f"move-entry:character:1591:{key}"
    return next(item for item in definition.move_entries if str(item.entry_id) == entry_id)


def _template_ids(effect) -> set[str]:
    found: set[str] = set()
    for item in effect.rule.filters:
        if isinstance(item, EventTemplateIdFilter):
            found.add(str(item.template_id))
        elif isinstance(item, AnyFilter):
            found.update(
                str(nested.template_id)
                for nested in item.filters
                if isinstance(nested, EventTemplateIdFilter)
            )
    return found


def _stats() -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.0),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.ICE: Resolved(0.0), Element.PHYSICAL: Resolved(0.0)},
    )


def _execute(
    definition,
    key: str,
    *,
    enabled_rules: tuple[str, ...] = (),
    parameter_values: dict[str, int] | None = None,
    enemy_stunned: bool = False,
):
    parameters = tuple(
        replace(item, value=parameter_values[str(item.parameter_id)])
        if parameter_values is not None and str(item.parameter_id) in parameter_values
        else item
        for item in definition.scenario_parameters
    )
    scenario = CalculationScenario(
        scenario_id=f"scenario:sigrid:{key}",
        current_operator=SIGRID_ID,
        conditions=definition.scenario_conditions,
        parameters=parameters,
        enabled_rule_item_ids=frozenset(
            RuleItemId(f"rule:character:1591:{suffix}") for suffix in enabled_rules
        ),
    )
    enemy_id = EnemyId(f"enemy:sigrid:{key}")
    request = MoveCalculationRequest(
        definition=definition,
        move_entry_id=_entry(definition, key).entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId(f"battle:sigrid:{key}"),
        battle_time=0.0,
        base_character_snapshots=(CharacterSnapshot(SIGRID_ID, 60, _stats()),),
        target_snapshot=EnemySnapshot(
            enemy_id=enemy_id,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.ICE: Resolved(0.0), Element.PHYSICAL: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
            is_stunned=enemy_stunned,
        ),
        team_profiles=(
            CharacterMatchProfile(
                SIGRID_ID,
                CharacterRole.ATTACK,
                operation_state=OperationState.OPERATED,
            ),
        ),
        target_profile=EnemyMatchProfile(
            enemy_id,
            states=(
                frozenset({StateId("state:enemy:stunned")})
                if enemy_stunned
                else frozenset()
            ),
        ),
        crit_display_mode=CritDisplayMode.NON_CRIT,
    )
    return DirectMoveApplicationService().calculate(request)


def _api_payload(
    *,
    move_entry_id: str,
    cinema_level: int = 0,
    conditions: dict[str, bool] | None = None,
    parameters: dict[str, int] | None = None,
    enabled_rules: tuple[str, ...] = (),
    enemy_stunned: bool = False,
    team_character_ids: tuple[str, ...] = ("character:1591",),
    wengine_id: str | None = None,
    rule_stack_counts: dict[str, int] | None = None,
    enemy_resistance: float = 0.0,
) -> dict[str, object]:
    primary = str(SIGRID_ID)
    compile_configs = {
        character_id: {"core_level": 7, "cinema_level": cinema_level}
        if character_id == primary
        else {}
        for character_id in team_character_ids
    }
    builds = {}
    for character_id in team_character_ids:
        stats = {
            "hp": 10000.0,
            "attack": 1000.0,
            "defense": 500.0,
            "impact": 100.0,
            "crit_rate": 0.0,
            "crit_damage": 0.5,
            "anomaly_mastery": 100.0,
            "anomaly_proficiency": 100.0,
            "penetration_rate": 0.0,
            "penetration_flat": 0.0,
            "energy_regen": 1.2,
            "element_damage_bonus": {"ice": 0.0, "physical": 0.0},
        }
        if character_id == primary and wengine_id is not None:
            builds[character_id] = {
                "level": 60,
                "build_mode": "equipment-build",
                "wengine_id": wengine_id,
                "wengine_level": 60,
                "wengine_refinement": 1,
                "base_stats": stats,
            }
        else:
            builds[character_id] = {"level": 60, "out_of_combat_stats": stats}
    supporting = tuple(item for item in team_character_ids if item != primary)
    return {
        "primary_character_id": primary,
        "team_character_ids": list(team_character_ids),
        "supporting_character_ids": list(supporting),
        "formation_character_ids": list(team_character_ids),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:sigrid-api",
            "level": 70,
            "initial_defense": 794.0,
            "damage_resistance": {"ice": enemy_resistance, "physical": enemy_resistance},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": enemy_stunned,
        },
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled_rules),
        "rule_stack_counts": rule_stack_counts or {},
        "selected_trigger_inputs": [],
    }


def _api_total(response: dict[str, object]) -> float:
    return float(response["totals"]["non-crit"]["value"])


def _api_breakdown(response: dict[str, object], mode: str = "non-crit") -> dict[str, float]:
    event = response["events"][0]
    return {
        item["node"]: item["value"]
        for item in event["modes"][mode]["calculation_breakdown"]
    }


def test_identity_provenance_and_all_reviewed_source_curves() -> None:
    data = _source_data()
    raw, _, definition = _definition()
    assert data["source_version"] == raw.source_version == SOURCE_VERSION
    assert data["source_url"] == raw.source_url == SOURCE_URL
    assert raw.character_id == SIGRID_ID
    assert raw.name == "希格莉德"
    assert raw.code_name == "Sigrid"
    assert raw.rarity == 4
    assert raw.specialty == "强攻"
    assert raw.element == "冰属性"
    assert raw.faction == "罗斯凯利法"
    assert raw.icon == "IconRole66"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert len(SIGRID_REVIEWED_MAPPING.moves) == 16
    assert len(definition.move_entries) == len(definition.damage_event_templates) == 16
    assert definition.role is CharacterRole.ATTACK
    assert definition.base_element is Element.ICE
    assert not definition.independent_derived_damage_events
    assert not any("anomaly" in str(entry.main_damage_event.damage_type).lower() for entry in definition.move_entries)

    source_parameters = {
        (parameter.source_skill_id, parameter.name): parameter
        for move in raw.moves
        for parameter in move.parameters
    }
    entries = {str(item.entry_id): item for item in definition.move_entries}
    for spec in SIGRID_REVIEWED_MAPPING.moves:
        parameter_spec = spec.parameters[0]
        source_parameter = source_parameters[(parameter_spec.source_skill_id, parameter_spec.parameter_name)]
        selected_source_ratio = dict(source_parameter.values)[12] / 100.0
        entry = entries[f"move-entry:character:1591:{spec.entry_key}"]
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(selected_source_ratio)
        assert entry.main_damage_event.damage_type is DamageType.DIRECT
        expected_element = Element.PHYSICAL if spec.entry_key == "dash-chasing-wind" else Element.ICE
        assert entry.main_damage_event.element is expected_element
    assert "parry-assist" not in " ".join(spec.entry_key for spec in SIGRID_REVIEWED_MAPPING.moves)


def test_default_skill_contract_and_cinema_three_five_source_levels() -> None:
    _, _, c0 = _definition()
    _, _, c3 = _definition(cinema_level=3)
    _, _, c5 = _definition(cinema_level=5)
    default = SigridCompileConfig()
    assert default.core_level == 7
    assert default.cinema_level == 0
    assert all(default.skill_level_for(group) == 12 for group in SkillGroup)
    assert all(effective_skill_level(default, group) == 12 for group in SkillGroup)
    assert all(effective_skill_level(SigridCompileConfig(cinema_level=3), group) == 14 for group in SkillGroup)
    assert all(effective_skill_level(SigridCompileConfig(cinema_level=5), group) == 16 for group in SkillGroup)
    assert _entry(c0, "basic-lance-form-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(7.169)
    assert _entry(c3, "basic-lance-form-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(7.821)
    assert _entry(c5, "basic-lance-form-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(8.473)
    assert _entry(c0, "ultimate-frost-sky").multiplier_variants[0].multiplier.value.value == pytest.approx(43.799)
    assert _entry(c3, "ultimate-frost-sky").multiplier_variants[0].multiplier.value.value == pytest.approx(47.781)
    assert _entry(c5, "ultimate-frost-sky").multiplier_variants[0].multiplier.value.value == pytest.approx(51.763)


def test_core_extra_and_current_buff_effects_have_exact_scope() -> None:
    raw, _, base = _definition()
    core_crit_effect = _rule(base, "core:sky-rider-crit-rate").effects[0]
    core_stun_effect = _rule(base, "core:stunned-enemy-stun-vulnerability").effects[0]
    assert core_crit_effect.result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
    assert _rule(base, "core:sky-rider-crit-rate").condition_ids == (SIGRID_CORE_CRIT_BUFF_ACTIVE,)
    assert _rule(base, "core:stunned-enemy-stun-vulnerability").condition_ids == (SIGRID_SKY_RIDER_STATE_ACTIVE,)
    assert any(getattr(item, "state_id", None) is not None and str(item.state_id) == "state:enemy:stunned" for item in core_stun_effect.rule.filters)
    assert all(item.condition_id != SIGRID_CORE_CRIT_BUFF_ACTIVE or item.value is False for item in base.scenario_conditions)

    for level, expected in enumerate((0.33, 0.39, 0.44, 0.50, 0.55, 0.61, 0.66), start=1):
        _, _, definition = _definition(core_level=level)
        effect = _rule(definition, "core:sky-rider-crit-rate").effects[0]
        assert effect.result.value.value == pytest.approx(expected)

    _, _, extra_locked = _definition(additional_ability_eligible=False)
    _, _, extra_ready = _definition(additional_ability_eligible=True, character_level=60, enemy_winded=True)
    assert _rule(extra_locked, "extra-ability:level-scaled-flat-attack").eligibility is RuleEligibility.INELIGIBLE
    attack = _rule(extra_ready, "extra-ability:level-scaled-flat-attack").effects[0]
    assert attack.result.modifier_path is CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS
    assert attack.result.value.value == pytest.approx(840.0)
    extra_damage = _rule(extra_ready, "extra-ability:wended-target-damage").effects[0]
    assert extra_damage.result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert extra_damage.result.value.value == pytest.approx(0.15)
    assert any(isinstance(item, DamageDealerFilter) and item.character_id == SIGRID_ID for item in extra_damage.rule.filters)
    assert any(isinstance(item, DamageTypeFilter) and item.damage_type is DamageType.DIRECT for item in extra_damage.rule.filters)
    assert raw.extra_ability_description == _rule(extra_ready, "extra-ability:wended-target-damage").original_text

    _, _, chain_active = _definition(chain_damage_buff_active=True)
    chain_rule = _rule(chain_active, "chain:current-lance-damage-bonus")
    assert chain_rule.source.source_type.value == "skill"
    assert chain_rule.source.label == "连携技：冰凌卷地"
    assert chain_rule.effects[0].result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert _template_ids(chain_rule.effects[0]) == {
        f"template:character:1591:basic-lance-form-stage-{stage}:main" for stage in (1, 2, 3)
    }
    assert chain_rule.effects[0].result.value.value == pytest.approx(0.20)

    _, _, c4_active = _definition(cinema_level=4, cinema4_damage_buff_active=True)
    c4_effect = _rule(c4_active, "cinema4:sky-rider-damage-bonus").effects[0]
    assert c4_effect.result.value.value == pytest.approx(0.18)
    assert _rule(c4_active, "cinema4:sky-rider-damage-bonus").condition_ids


def test_cinema_two_penetration_rate_only_applies_to_source_listed_moves() -> None:
    _, _, definition = _definition(cinema_level=2)
    rule = _rule(definition, "cinema2:listed-attacks-penetration-rate")
    effect = rule.effects[0]
    assert effect.result.modifier_path is CalculationNode.DAMAGE_PENETRATION_RATE
    assert effect.result.value.value == pytest.approx(0.24)
    assert _template_ids(effect) == {
        f"template:character:1591:{key}:main"
        for key in (
            "basic-fierce-spear-stage-4",
            "dodge-counter-returning-spear",
            "ex-ranqiong",
            "ex-suiyu",
            "chain-ice-curtain",
            "ultimate-frost-sky",
            "assist-strike-ice-feast",
            "basic-lance-form-stage-1",
            "basic-lance-form-stage-2",
            "basic-lance-form-stage-3",
        )
    }


@pytest.mark.parametrize(
    ("stage", "c6_delta"),
    ((1, 0.8), (2, 0.9), (3, 1.0)),
)
def test_cinema_one_and_six_same_zone_deltas_add_once_in_real_damage_execution(stage: int, c6_delta: float) -> None:
    key = f"basic-lance-form-stage-{stage}"
    _, _, definition = _definition(cinema_level=6, cinema1_overflow_attack_active=True)
    base_ratio = _entry(definition, key).multiplier_variants[0].multiplier.value.value
    param = {str(SIGRID_CINEMA1_OVERFLOW_ACTIVE): 1}
    base = _execute(definition, key)
    c1_only = _execute(
        definition,
        key,
        enabled_rules=("cinema1:overflow-last-hit",),
        parameter_values=param,
    )
    c6_only = _execute(
        definition,
        key,
        enabled_rules=("cinema6:combined-last-hit-ratio",),
    )
    both = _execute(
        definition,
        key,
        enabled_rules=("cinema1:overflow-last-hit", "cinema6:combined-last-hit-ratio"),
        parameter_values=param,
    )
    no_overflow = _execute(
        definition,
        key,
        enabled_rules=("cinema1:overflow-last-hit", "cinema6:combined-last-hit-ratio"),
        parameter_values={str(SIGRID_CINEMA1_OVERFLOW_ACTIVE): 0},
    )
    assert all(result.output.complete and result.output.known_total is not None for result in (base, c1_only, c6_only, both, no_overflow))
    assert c1_only.output.known_total / base.output.known_total == pytest.approx((base_ratio + 1.0) / base_ratio, rel=1e-8)
    assert c6_only.output.known_total / base.output.known_total == pytest.approx((base_ratio + c6_delta) / base_ratio, rel=1e-8)
    assert both.output.known_total / base.output.known_total == pytest.approx((base_ratio + 1.0 + c6_delta) / base_ratio, rel=1e-8)
    assert no_overflow.output.known_total == pytest.approx(c6_only.output.known_total)


@pytest.mark.parametrize("cinema", (1, 3))
def test_locked_cinema_six_does_not_suppress_cinema_one_overflow(cinema: int) -> None:
    _, _, definition = _definition(cinema_level=cinema, cinema1_overflow_attack_active=True)
    c6_rule = _rule(definition, "cinema6:combined-last-hit-ratio")
    assert c6_rule.eligibility is RuleEligibility.INELIGIBLE
    key = "basic-lance-form-stage-1"
    base_ratio = _entry(definition, key).multiplier_variants[0].multiplier.value.value
    base = _execute(definition, key)
    overflow = _execute(
        definition,
        key,
        enabled_rules=("cinema1:overflow-last-hit",),
        parameter_values={str(SIGRID_CINEMA1_OVERFLOW_ACTIVE): 1},
    )
    overflow_with_forced_locked_c6 = _execute(
        definition,
        key,
        enabled_rules=(
            "cinema1:overflow-last-hit",
            "cinema6:combined-last-hit-ratio",
        ),
        parameter_values={str(SIGRID_CINEMA1_OVERFLOW_ACTIVE): 1},
    )
    assert base.output.complete and overflow.output.complete
    assert overflow_with_forced_locked_c6.output.complete
    assert base.output.known_total is not None and overflow.output.known_total is not None
    assert overflow_with_forced_locked_c6.output.known_total is not None
    assert overflow.output.known_total / base.output.known_total == pytest.approx((base_ratio + 1.0) / base_ratio, rel=1e-8)
    assert overflow_with_forced_locked_c6.output.known_total == pytest.approx(overflow.output.known_total)


def test_core_stun_vulnerability_uses_real_enemy_state_and_current_sky_rider_state() -> None:
    _, _, definition = _definition(sky_rider_state_active=True)
    key = "basic-fierce-spear-stage-1"
    core_rule = "core:stunned-enemy-stun-vulnerability"
    normal_target = _execute(definition, key, enabled_rules=(core_rule,), enemy_stunned=False)
    stunned_target = _execute(definition, key, enabled_rules=(core_rule,), enemy_stunned=True)
    assert normal_target.output.complete and stunned_target.output.complete
    assert normal_target.output.known_total is not None and stunned_target.output.known_total is not None
    assert stunned_target.output.known_total / normal_target.output.known_total == pytest.approx(1.20, rel=1e-8)


def test_registry_derives_extra_ability_from_team_roles_and_registers_signature() -> None:
    registration = registration_for(SIGRID_ID)
    assert registration.catalog.display_name == "希格莉德"
    assert registration.catalog.rarity == "S"
    assert registration.role is CharacterRole.ATTACK
    assert registration.base_element is Element.ICE
    assert registration.equipment_capabilities.possible_elements == {
        Element.ICE,
        Element.PHYSICAL,
    }
    assert SIGNATURE_WENGINE_BY_CHARACTER[SIGRID_ID] == WENGINE_CAVALRY_PRAISE_ID

    solo_definition = compile_registered_definition(
        SIGRID_ID,
        {"core_level": 7, "cinema_level": 0},
        [SIGRID_ID],
        strict=False,
    )
    team_definition = compile_registered_definition(
        SIGRID_ID,
        {"core_level": 7, "cinema_level": 0},
        [SIGRID_ID, "character:1511"],
        strict=False,
    )
    assert _rule(solo_definition, "extra-ability:level-scaled-flat-attack").eligibility is RuleEligibility.INELIGIBLE
    assert _rule(team_definition, "extra-ability:level-scaled-flat-attack").eligibility is RuleEligibility.ELIGIBLE
    with pytest.raises(ValueError, match="unknown compile config fields"):
        compile_registered_definition(
            SIGRID_ID,
            {"core_level": 7, "cinema_level": 0, "character_level": 60},
            [SIGRID_ID],
            strict=False,
        )
    fields = {item.field_id for item in config_fields_for(SIGRID_ID, {}, [SIGRID_ID])}
    assert not fields.intersection(
        {
            "character_level",
            "sky_rider_state_active",
            "core_crit_buff_active",
            "enemy_winded",
            "chain_damage_buff_active",
            "cinema4_damage_buff_active",
        }
    )

    preview = build_registered_build_preview(
        SIGRID_ID,
        team_character_ids=[SIGRID_ID],
        level=60,
        wengine_id=str(WENGINE_CAVALRY_PRAISE_ID),
        wengine_refinement=1,
    )
    assert preview.complete
    assert preview.out_of_combat_stats["crit_damage"] == pytest.approx(0.98)
    assert any(item.source_id == "wengine:14159" for item in preview.provenance)


def test_formal_api_uses_condition_values_and_actual_stunned_target_state() -> None:
    entry_id = "move-entry:character:1591:basic-fierce-spear-stage-1"
    sky_active = str(SIGRID_SKY_RIDER_STATE_ACTIVE)
    rule = "rule:character:1591:core:stunned-enemy-stun-vulnerability"
    unbuffed = calculate_payload(_api_payload(move_entry_id=entry_id))
    sky_target_not_stunned = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            conditions={sky_active: True},
            enabled_rules=(rule,),
            enemy_stunned=False,
        )
    )
    sky_target_stunned = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            conditions={sky_active: True},
            enabled_rules=(rule,),
            enemy_stunned=True,
        )
    )
    assert unbuffed["totals"]["non-crit"]["complete"]
    assert sky_target_not_stunned["totals"]["non-crit"]["complete"]
    assert sky_target_stunned["totals"]["non-crit"]["complete"]
    assert _api_total(sky_target_not_stunned) == pytest.approx(_api_total(unbuffed))
    assert _api_total(sky_target_stunned) / _api_total(unbuffed) == pytest.approx(1.20, rel=1e-8)

    crit_rule = "rule:character:1591:core:sky-rider-crit-rate"
    crit_inactive = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            conditions={str(SIGRID_CORE_CRIT_BUFF_ACTIVE): False},
            enabled_rules=(crit_rule,),
        )
    )
    crit = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            conditions={str(SIGRID_CORE_CRIT_BUFF_ACTIVE): True},
            enabled_rules=(crit_rule,),
        )
    )
    assert crit["totals"]["non-crit"]["complete"]
    assert crit_inactive["totals"]["non-crit"]["complete"]
    assert crit["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(0.66)
    assert crit_inactive["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(0.0)
    assert _api_breakdown(crit, "expected")["character.current.crit-rate"] == pytest.approx(0.66)
    assert _api_breakdown(crit, "expected")["damage.standard-crit-region"] == pytest.approx(1.33)
    assert _api_breakdown(crit_inactive, "expected")["damage.standard-crit-region"] == pytest.approx(1.0)


@pytest.mark.parametrize(("cinema", "expected_level"), ((3, 14), (5, 16)))
def test_formal_api_preserves_cinema_three_five_base_levels(cinema: int, expected_level: int) -> None:
    entry_id = "move-entry:character:1591:basic-lance-form-stage-1"
    response = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            cinema_level=cinema,
        )
    )
    definition = compile_registered_definition(
        SIGRID_ID,
        {"core_level": 7, "cinema_level": cinema},
        [SIGRID_ID],
        strict=False,
    )
    expected = _entry(definition, "basic-lance-form-stage-1").multiplier_variants[0].multiplier.value.value
    assert response["totals"]["non-crit"]["complete"]
    assert _api_breakdown(response)["damage.skill-multiplier"] == pytest.approx(expected)
    assert expected_level == effective_skill_level(
        SigridCompileConfig(cinema_level=cinema), SkillGroup.BASIC_ATTACK
    )


def test_formal_api_same_zone_cinema_one_and_six_deltas_add_once() -> None:
    key = "basic-lance-form-stage-2"
    entry_id = f"move-entry:character:1591:{key}"
    definition = compile_registered_definition(
        SIGRID_ID,
        {"core_level": 7, "cinema_level": 6},
        [SIGRID_ID],
        strict=False,
    )
    base = _entry(definition, key).multiplier_variants[0].multiplier.value.value
    overflow_rule = "rule:character:1591:cinema1:overflow-last-hit"
    c6_rule = "rule:character:1591:cinema6:combined-last-hit-ratio"
    parameter = {str(SIGRID_CINEMA1_OVERFLOW_ACTIVE): 1}
    base_response = calculate_payload(_api_payload(move_entry_id=entry_id, cinema_level=6))
    c1_response = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            cinema_level=6,
            parameters=parameter,
            enabled_rules=(overflow_rule,),
        )
    )
    c6_response = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            cinema_level=6,
            enabled_rules=(c6_rule,),
        )
    )
    combined_response = calculate_payload(
        _api_payload(
            move_entry_id=entry_id,
            cinema_level=6,
            parameters=parameter,
            enabled_rules=(overflow_rule, c6_rule),
        )
    )
    assert all(
        item["totals"]["non-crit"]["complete"]
        for item in (base_response, c1_response, c6_response, combined_response)
    )
    baseline = _api_total(base_response)
    assert _api_total(c1_response) / baseline == pytest.approx((base + 1.0) / base, rel=1e-8)
    assert _api_total(c6_response) / baseline == pytest.approx((base + 0.9) / base, rel=1e-8)
    assert _api_total(combined_response) / baseline == pytest.approx((base + 1.9) / base, rel=1e-8)


def test_signature_engine_current_blade_edge_effect_is_ice_only() -> None:
    base_rule = "rule:wengine:14159:owner:1591:crit-damage-per-blade-edge-stack"
    ignore_rule = "rule:wengine:14159:owner:1591:ice-resistance-ignore-at-max-stacks"
    rules = (base_rule, ignore_rule)
    def execute(entry_key: str, stacks: int) -> dict[str, object]:
        return calculate_payload(
            _api_payload(
                move_entry_id=f"move-entry:character:1591:{entry_key}",
                wengine_id=str(WENGINE_CAVALRY_PRAISE_ID),
                enemy_resistance=0.2,
                enabled_rules=rules,
                rule_stack_counts={base_rule: stacks},
            )
        )

    ice_without_buffs = execute("basic-fierce-spear-stage-1", 0)
    ice_with_max_stacks = execute("basic-fierce-spear-stage-1", 2)
    physical_without_buffs = execute("dash-chasing-wind", 0)
    physical_with_max_stacks = execute("dash-chasing-wind", 2)
    for response in (ice_without_buffs, ice_with_max_stacks, physical_without_buffs, physical_with_max_stacks):
        assert response["totals"]["non-crit"]["complete"]
    assert _api_breakdown(ice_without_buffs)["resistance.damage-ignore"] == pytest.approx(0.0)
    assert _api_breakdown(ice_with_max_stacks)["resistance.damage-ignore"] == pytest.approx(0.2)
    assert _api_breakdown(physical_without_buffs)["resistance.damage-ignore"] == pytest.approx(0.0)
    assert _api_breakdown(physical_with_max_stacks)["resistance.damage-ignore"] == pytest.approx(0.0)
    assert _api_total(ice_with_max_stacks) / _api_total(ice_without_buffs) == pytest.approx(1.25, rel=1e-8)
    assert _api_total(physical_with_max_stacks) == pytest.approx(_api_total(physical_without_buffs))
