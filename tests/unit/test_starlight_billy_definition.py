from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.starlight_billy import (
    STARLIGHT_BILLY_ID,
    STARLIGHT_BILLY_REVIEWED_MAPPING,
    StarlightBillyCompileConfig,
    compile_starlight_billy,
    load_raw_record,
)
from core.application.characters.starlight_billy.compiler import (
    STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE,
    STARLIGHT_BILLY_C2_TURBO_ACTIVE,
    STARLIGHT_BILLY_C4_SUPPRESSION_STACKS,
    STARLIGHT_BILLY_C6_CONSUMED_STARSHINE,
    STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE,
    STARLIGHT_BILLY_EXTRA_ABILITY_STACKS,
)
from core.application.characters.templates import PenetrationDamageEventTemplate
from core.application.equipment.wengine import (
    SIGNATURE_WENGINE_BY_CHARACTER,
    compile_wengine,
)
from core.application.equipment.wengine_ids import WENGINE_GLOWING_HELM_ID
from core.application.execution import DirectMoveApplicationService, MoveCalculationRequest
from core.application.ids import RuleItemId
from core.application.matching import CharacterMatchProfile, EnemyMatchProfile
from core.application.output import CritDisplayMode
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record
from core.presentation.catalog import supported_character_catalog
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    build_registered_build_preview,
    build_registered_editor_view,
    compile_registered_definition,
    registration_for,
    supported_character_registrations,
)
from core.application.scenario import CalculationScenario, ConditionResolution, ParameterResolution
from core.types import (
    AnyFilter,
    BattleStateId,
    CalculationNode,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    CurrentPenetrationForceValueSource,
    DamageType,
    DamageTypeFilter,
    EffectOperation,
    EffectTarget,
    Element,
    ElementFilter,
    EnemyId,
    EnemySnapshot,
    EventTemplateIdFilter,
    OperationState,
    PanelStatDerivedValue,
    Resolved,
    ScenarioParameterDerivedValue,
    SkillGroup,
    StandardCritRule,
    WEngineBuildInput,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "starlight_billy.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1531.json"


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _definition(
    *,
    core_level: int = 7,
    cinema_level: int = 0,
    additional_ability_eligible: bool = False,
):
    raw = load_raw_record(_source_data())
    return raw, compile_starlight_billy(
        StarlightBillyCompileConfig(
            core_level=core_level,
            cinema_level=cinema_level,
            additional_ability_eligible=additional_ability_eligible,
        ),
        raw,
    )


def _rule(definition, suffix: str):
    rule_id = f"rule:character:1531:{suffix}"
    return next(item for item in definition.rule_items if str(item.rule_id) == rule_id)


def _entry(definition, suffix: str):
    entry_id = f"move-entry:character:1531:{suffix}"
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


def test_identity_source_version_and_reviewed_damage_curve_mapping() -> None:
    data = _source_data()
    raw, definition = _definition()

    assert data["source_version"] == SOURCE_VERSION
    assert data["source_url"] == SOURCE_URL
    assert raw.source_version == SOURCE_VERSION
    assert raw.source_url == SOURCE_URL
    assert raw.character_id == STARLIGHT_BILLY_ID
    assert raw.name == "星徽·比利"
    assert raw.code_name == "Starlight - Billy"
    assert raw.rarity == 4
    assert raw.specialty == "命破"
    assert raw.element == "物理"
    assert raw.faction == "狡兔屋"
    assert raw.icon == "IconRole62"
    assert len(raw.core_levels) == 7
    assert len(raw.mindscapes) == 6
    assert len(STARLIGHT_BILLY_REVIEWED_MAPPING.moves) == 17
    assert len(definition.move_entries) == 17

    expected_level_12_percent = {
        "basic-knights-duel-stage-1": ("一段伤害倍率", "1531001", 100.9),
        "basic-knights-duel-stage-2": ("二段伤害倍率", "1531002", 136.2),
        "basic-knights-duel-stage-3": ("三段伤害倍率", "1531003", 109.5),
        "basic-knights-duel-stage-4": ("四段伤害倍率", "1531004", 412.8),
        "basic-high-mileage-starlight": ("伤害倍率", "1531010", 2087.1),
        "dash-star-emblem-punishment": ("伤害倍率", "1531012", 90.2),
        "dodge-counter-king-of-duel": ("伤害倍率", "1531013", 239.4),
        "dodge-counter-tail-flame-spin": ("伤害倍率", "1531014", 397.8),
        "special-motor-suppression": ("伤害倍率", "1531006", 104.8),
        "special-disengage": ("伤害倍率", "1531007", 144.7),
        "ex-lone-wheel-stunt": ("伤害倍率", "1531008", 780.2),
        "ex-grip-hub": ("伤害倍率", "1531009", 1860.5),
        "ex-swaying-step": ("伤害倍率", "1531011", 1918.2),
        "chain-knight-walk": ("伤害倍率", "1531015", 1326.2),
        "ultimate-knight-flying-kick": ("伤害倍率", "1531016", 3184.9),
        "quick-assist-star-emblem-bond": ("伤害倍率", "1531017", 184.4),
        "assist-villain-exit": ("伤害倍率", "1531021", 459.5),
    }
    specs = {item.entry_key: item for item in STARLIGHT_BILLY_REVIEWED_MAPPING.moves}
    assert set(specs) == set(expected_level_12_percent)
    entries = {str(item.entry_id): item for item in definition.move_entries}
    for entry_key, (parameter_name, source_id, expected_percent) in expected_level_12_percent.items():
        spec = specs[entry_key]
        assert len(spec.parameters) == 1
        assert spec.parameters[0].parameter_name == parameter_name
        assert spec.parameters[0].source_skill_id == source_id
        entry = entries[f"move-entry:character:1531:{entry_key}"]
        assert entry.multiplier_variants[0].multiplier.value.value == pytest.approx(
            expected_percent / 100.0
        )

    basic_stages = tuple(
        item
        for item in STARLIGHT_BILLY_REVIEWED_MAPPING.moves
        if item.entry_key.startswith("basic-knights-duel-stage-")
    )
    assert len(basic_stages) == 4
    assert [item.stage_index for item in basic_stages] == [1, 2, 3, 4]
    assert len({item.move_id for item in basic_stages}) == 1
    assert "招架支援：英雄登台" not in {item.source_name for item in STARLIGHT_BILLY_REVIEWED_MAPPING.moves}


def test_default_contract_is_s_rank_core_seven_and_all_penetration_force() -> None:
    _, definition = _definition()
    config = StarlightBillyCompileConfig()

    assert config.core_level == 7
    assert config.cinema_level == 0
    assert config.skill_level_for(SkillGroup.ULTIMATE) == 12
    assert effective_skill_level(config, SkillGroup.ULTIMATE) == 12
    assert definition.role is CharacterRole.RUPTURE
    assert definition.base_element is Element.PHYSICAL
    assert len(definition.damage_event_templates) == 17
    assert len(definition.independent_derived_damage_events) == 0
    for entry, template in zip(definition.move_entries, definition.damage_event_templates):
        assert isinstance(template, PenetrationDamageEventTemplate)
        assert entry.main_damage_event.damage_type is DamageType.PENETRATION
        assert entry.main_damage_event.element is Element.PHYSICAL
        assert template.ref.damage_type is DamageType.PENETRATION
        assert template.element is Element.PHYSICAL
        assert isinstance(template.base_source, CurrentPenetrationForceValueSource)
        assert template.base_source.character_id == STARLIGHT_BILLY_ID
        assert isinstance(template.crit_rule, StandardCritRule)
        assert template.damage_dealer == STARLIGHT_BILLY_ID

    core_force = _rule(definition, "core:max-hp-penetration-force").effects[0]
    assert core_force.rule.target is EffectTarget.SELF
    assert core_force.result.modifier_path is CalculationNode.PENETRATION_FORCE_BONUS
    assert isinstance(core_force.result.value, PanelStatDerivedValue)
    assert core_force.result.value.source_node is CalculationNode.CHARACTER_CURRENT_MAX_HP
    assert core_force.result.value.source_character_id == STARLIGHT_BILLY_ID
    assert core_force.result.value.coefficient.value == pytest.approx(0.1)
    assert any(
        isinstance(item, DamageTypeFilter) and item.damage_type is DamageType.PENETRATION
        for item in core_force.rule.filters
    )


def test_cinema_three_and_five_raise_basic_and_ultimate_source_levels() -> None:
    _, c0 = _definition()
    _, c3 = _definition(cinema_level=3)
    _, c5 = _definition(cinema_level=5)
    for group in SkillGroup:
        assert effective_skill_level(StarlightBillyCompileConfig(cinema_level=3), group) == 14
        assert effective_skill_level(StarlightBillyCompileConfig(cinema_level=5), group) == 16

    assert _entry(c0, "basic-knights-duel-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(1.009)
    assert _entry(c3, "basic-knights-duel-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(1.101)
    assert _entry(c5, "basic-knights-duel-stage-1").multiplier_variants[0].multiplier.value.value == pytest.approx(1.193)
    assert _entry(c0, "ultimate-knight-flying-kick").multiplier_variants[0].multiplier.value.value == pytest.approx(31.849)
    assert _entry(c3, "ultimate-knight-flying-kick").multiplier_variants[0].multiplier.value.value == pytest.approx(34.745)
    assert _entry(c5, "ultimate-knight-flying-kick").multiplier_variants[0].multiplier.value.value == pytest.approx(37.641)


def test_core_crit_damage_uses_selected_core_curve_and_current_state() -> None:
    expected = (0.45, 0.53, 0.60, 0.68, 0.75, 0.83, 0.90)
    for core_level, expected_bonus in enumerate(expected, start=1):
        _, definition = _definition(core_level=core_level)
        core_rule = _rule(definition, "core:motor-suppression-crit-damage")
        assert core_rule.effects[0].result.value.value == pytest.approx(expected_bonus)
        condition = next(
            item
            for item in definition.scenario_conditions
            if item.condition_id == STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE
        )
        assert condition.resolution is ConditionResolution.USER_SELECTED
        assert condition.value is False
        assert core_rule.condition_ids == (condition.condition_id,)


def test_extra_ability_is_ineligible_without_team_role_and_scopes_six_move_families() -> None:
    raw, locked = _definition(additional_ability_eligible=False)
    locked_rule = _rule(locked, "extra-ability:starshine-damage")
    assert locked_rule.eligibility is RuleEligibility.INELIGIBLE
    assert not locked.scenario_parameters

    _, eligible = _definition(additional_ability_eligible=True)
    rule = _rule(eligible, "extra-ability:starshine-damage")
    parameter = next(
        item
        for item in eligible.scenario_parameters
        if item.parameter_id == STARLIGHT_BILLY_EXTRA_ABILITY_STACKS
    )
    assert rule.eligibility is RuleEligibility.ELIGIBLE
    assert parameter.resolution is ParameterResolution.USER_SELECTED
    assert parameter.value == 2
    assert parameter.minimum == 0
    assert parameter.maximum == 2
    value = rule.effects[0].result.value
    assert isinstance(value, ScenarioParameterDerivedValue)
    assert value.coefficient.value == pytest.approx(0.20)
    assert value.cap_max.value == pytest.approx(0.40)
    assert _template_ids(rule.effects[0]) == {
        "template:character:1531:ex-lone-wheel-stunt:main",
        "template:character:1531:ex-grip-hub:main",
        "template:character:1531:ex-swaying-step:main",
        "template:character:1531:chain-knight-walk:main",
        "template:character:1531:ultimate-knight-flying-kick:main",
        "template:character:1531:basic-high-mileage-starlight:main",
    }
    assert raw.extra_ability_description == rule.original_text
    assert "招架支援：英雄登台" not in rule.original_text


def test_cinema_rules_keep_current_state_and_exact_event_scopes() -> None:
    _, c0 = _definition()
    _, c1 = _definition(cinema_level=1)
    _, c2 = _definition(cinema_level=2)
    _, c4 = _definition(cinema_level=4)
    _, c6 = _definition(cinema_level=6)

    c1_rule = _rule(c1, "cinema1:physical-resistance-ignore")
    assert c1_rule.eligibility is RuleEligibility.ELIGIBLE
    assert c1_rule.condition_ids == (STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE,)
    c1_condition = next(
        item
        for item in c1.scenario_conditions
        if item.condition_id == STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE
    )
    assert c1_condition.value is False
    assert c1_rule.effects[0].result.modifier_path is CalculationNode.DAMAGE_RESISTANCE_IGNORE
    assert c1_rule.effects[0].result.value.value == pytest.approx(0.18)

    c2_rule = _rule(c2, "cinema2:listed-move-damage")
    assert c2_rule.effects[0].result.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert c2_rule.effects[0].result.value.value == pytest.approx(0.50)
    assert _template_ids(c2_rule.effects[0]) == {
        "template:character:1531:basic-high-mileage-starlight:main",
        "template:character:1531:ex-lone-wheel-stunt:main",
        "template:character:1531:ultimate-knight-flying-kick:main",
    }
    turbo_rule = _rule(c2, "cinema2:turbo-lone-wheel-crit-damage")
    assert turbo_rule.condition_ids == (STARLIGHT_BILLY_C2_TURBO_ACTIVE,)
    assert turbo_rule.effects[0].result.modifier_path is CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE
    assert _template_ids(turbo_rule.effects[0]) == {
        "template:character:1531:ex-lone-wheel-stunt:main"
    }

    c4_rule = _rule(c4, "cinema4:motor-suppression-crit-damage-stacks")
    assert c4_rule.eligibility is RuleEligibility.ELIGIBLE
    assert c4_rule.condition_ids == (STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE,)
    c4_value = c4_rule.effects[0].result.value
    assert isinstance(c4_value, ScenarioParameterDerivedValue)
    assert c4_value.parameter_id == str(STARLIGHT_BILLY_C4_SUPPRESSION_STACKS)
    assert c4_value.coefficient.value == pytest.approx(0.08)
    assert c4_value.cap_max.value == pytest.approx(0.16)
    c4_parameter = next(
        item
        for item in c4.scenario_parameters
        if item.parameter_id == STARLIGHT_BILLY_C4_SUPPRESSION_STACKS
    )
    assert c4_parameter.value == 2
    assert c4_parameter.minimum == 0
    assert c4_parameter.maximum == 2

    assert _rule(c0, "cinema1:physical-resistance-ignore").eligibility is RuleEligibility.INELIGIBLE
    assert _rule(c0, "cinema2:listed-move-damage").eligibility is RuleEligibility.INELIGIBLE
    assert _rule(c0, "cinema4:motor-suppression-crit-damage-stacks").eligibility is RuleEligibility.INELIGIBLE
    assert _rule(c0, "cinema6:consumed-starshine-whole-move-ratio").eligibility is RuleEligibility.INELIGIBLE

    c6_penetration = _rule(c6, "cinema6:listed-penetration-damage-bonus")
    assert c6_penetration.effects[0].result.modifier_path is CalculationNode.PENETRATION_DAMAGE_BONUS
    assert c6_penetration.effects[0].result.value.value == pytest.approx(0.18)
    assert _template_ids(c6_penetration.effects[0]) == {
        "template:character:1531:ultimate-knight-flying-kick:main",
        "template:character:1531:basic-high-mileage-starlight:main",
    }
    c6_parameter = next(
        item
        for item in c6.scenario_parameters
        if item.parameter_id == STARLIGHT_BILLY_C6_CONSUMED_STARSHINE
    )
    assert c6_parameter.resolution is ParameterResolution.USER_SELECTED
    assert c6_parameter.value == 2
    assert c6_parameter.minimum == 0
    assert c6_parameter.maximum == 2
    ratio_rule = _rule(c6, "cinema6:consumed-starshine-whole-move-ratio")
    assert len(ratio_rule.effects) == 2
    for effect, entry_key in zip(
        ratio_rule.effects,
        ("ultimate-knight-flying-kick", "basic-high-mileage-starlight"),
    ):
        assert effect.result.modifier_path is CalculationNode.DAMAGE_SKILL_MULTIPLIER
        assert effect.result.operation is EffectOperation.MULTIPLY
        assert effect.result.value.base.value == pytest.approx(1.0)
        assert effect.result.value.coefficient.value == pytest.approx(
            1 / _entry(c6, entry_key).multiplier_variants[0].multiplier.value.value
        )
        assert effect.result.value.cap_max.value == pytest.approx(
            1
            + 2
            / _entry(c6, entry_key).multiplier_variants[0].multiplier.value.value
        )
        assert _template_ids(effect) == {
            f"template:character:1531:{entry_key}:main"
        }
    assert len(c6.damage_event_templates) == 17


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
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )


def _execute_c6_high_mileage(definition, stacks: int, *, rule_enabled: bool = True):
    parameters = tuple(
        replace(item, value=stacks)
        if item.parameter_id == STARLIGHT_BILLY_C6_CONSUMED_STARSHINE
        else item
        for item in definition.scenario_parameters
    )
    scenario = CalculationScenario(
        scenario_id=f"scenario:starlight-billy:c6:{stacks}",
        current_operator=STARLIGHT_BILLY_ID,
        conditions=definition.scenario_conditions,
        parameters=parameters,
        enabled_rule_item_ids=(
            frozenset(
                {RuleItemId("rule:character:1531:cinema6:consumed-starshine-whole-move-ratio")}
            )
            if rule_enabled
            else frozenset()
        ),
    )
    enemy_id = EnemyId("enemy:starlight-billy-c6")
    request = MoveCalculationRequest(
        definition=definition,
        move_entry_id=_entry(definition, "basic-high-mileage-starlight").entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId(f"battle:starlight-billy:c6:{stacks}"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(STARLIGHT_BILLY_ID, 60, _stats()),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=enemy_id,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(
                STARLIGHT_BILLY_ID,
                CharacterRole.RUPTURE,
                operation_state=OperationState.OPERATED,
            ),
        ),
        target_profile=EnemyMatchProfile(enemy_id),
        crit_display_mode=CritDisplayMode.NON_CRIT,
    )
    return DirectMoveApplicationService().calculate(request)


def _execute_starlight_entry(
    definition,
    entry_key: str,
    *,
    enabled_rule_suffixes: tuple[str, ...] = (),
    parameter_overrides: dict[str, int] | None = None,
):
    parameters = tuple(
        replace(item, value=parameter_overrides[str(item.parameter_id)])
        if parameter_overrides is not None
        and str(item.parameter_id) in parameter_overrides
        else item
        for item in definition.scenario_parameters
    )
    scenario = CalculationScenario(
        scenario_id=f"scenario:starlight-billy:{entry_key}",
        current_operator=STARLIGHT_BILLY_ID,
        conditions=definition.scenario_conditions,
        parameters=parameters,
        enabled_rule_item_ids=frozenset(
            RuleItemId(f"rule:character:1531:{suffix}")
            for suffix in enabled_rule_suffixes
        ),
    )
    enemy_id = EnemyId(f"enemy:starlight-billy:{entry_key}")
    request = MoveCalculationRequest(
        definition=definition,
        move_entry_id=_entry(definition, entry_key).entry_id,
        scenario=scenario,
        battle_state_id=BattleStateId(f"battle:starlight-billy:{entry_key}"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(STARLIGHT_BILLY_ID, 60, _stats()),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=enemy_id,
            level=70,
            initial_defense=Resolved(794.0),
            damage_resistance={Element.PHYSICAL: Resolved(0.0)},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(
                STARLIGHT_BILLY_ID,
                CharacterRole.RUPTURE,
                operation_state=OperationState.OPERATED,
            ),
        ),
        target_profile=EnemyMatchProfile(enemy_id),
        crit_display_mode=CritDisplayMode.NON_CRIT,
    )
    return DirectMoveApplicationService().calculate(request)


def _api_payload(
    *,
    primary_character_id: str = str(STARLIGHT_BILLY_ID),
    move_entry_id: str,
    cinema_level: int = 0,
    team_character_ids: tuple[str, ...] | None = None,
    conditions: dict[str, bool | None] | None = None,
    parameters: dict[str, int | None] | None = None,
    enabled_rules: tuple[str, ...] = (),
    hp: float = 10000.0,
) -> dict[str, object]:
    team = team_character_ids or (primary_character_id,)
    compile_configs = {
        character_id: {
            "core_level": 7,
            "cinema_level": cinema_level if character_id == str(STARLIGHT_BILLY_ID) else 0,
        }
        for character_id in team
    }
    builds = {
        character_id: {
            "level": 60,
            "out_of_combat_stats": {
                "hp": hp if character_id == str(STARLIGHT_BILLY_ID) else 10000.0,
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
                "element_damage_bonus": {
                    "physical": 0.0,
                    "electric": 0.0,
                },
            },
        }
        for character_id in team
    }
    return {
        "primary_character_id": primary_character_id,
        "team_character_ids": list(team),
        "supporting_character_ids": [
            item for item in team if item != primary_character_id
        ],
        "formation_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:starlight-billy-api",
            "level": 70,
            "initial_defense": 794.0,
            "damage_resistance": {"physical": 0.0, "electric": 0.0},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 0.0,
            "is_stunned": False,
        },
        "condition_values": conditions or {},
        "parameter_values": parameters or {},
        "enabled_rule_item_ids": list(enabled_rules),
        "rule_stack_counts": {},
        "selected_trigger_inputs": [],
    }


def _api_breakdown(response: dict[str, object]) -> dict[str, float]:
    event = response["events"][0]
    return {
        item["node"]: item["value"]
        for item in event["modes"]["non-crit"]["calculation_breakdown"]
    }


def test_cinema6_current_consumed_stacks_add_to_full_move_multiplier_in_execution() -> None:
    _, definition = _definition(cinema_level=6)
    base_ratio = _entry(definition, "basic-high-mileage-starlight").multiplier_variants[0].multiplier.value.value
    disabled = _execute_c6_high_mileage(definition, 2, rule_enabled=False)
    one = _execute_c6_high_mileage(definition, 0)
    three = _execute_c6_high_mileage(definition, 2)
    assert disabled.output.complete
    assert one.output.complete
    assert three.output.complete
    assert disabled.output.known_total is not None
    assert one.output.known_total is not None
    assert three.output.known_total is not None
    # The 2 consumed stacks add 2.0 to the complete current source multiplier.
    # The separate +18% Penetration Damage Bonus is disabled in both executions.
    assert three.output.known_total / one.output.known_total == pytest.approx(
        (base_ratio + 2.0) / base_ratio,
        rel=1e-8,
    )
    assert one.output.known_total == pytest.approx(disabled.output.known_total)


def test_cinema_three_and_five_raw_skill_levels_drive_penetration_execution() -> None:
    executions = {}
    multipliers = {}
    for cinema_level in (0, 3, 5):
        _, definition = _definition(cinema_level=cinema_level)
        entry = _entry(definition, "basic-high-mileage-starlight")
        multipliers[cinema_level] = entry.multiplier_variants[0].multiplier.value.value
        execution = _execute_starlight_entry(
            definition,
            "basic-high-mileage-starlight",
        )
        assert execution.output.complete
        assert execution.output.known_total is not None
        executions[cinema_level] = execution.output.known_total

    assert multipliers == pytest.approx({0: 20.871, 3: 22.769, 5: 24.667})
    assert executions[3] / executions[0] == pytest.approx(
        multipliers[3] / multipliers[0], rel=1e-8
    )
    assert executions[5] / executions[0] == pytest.approx(
        multipliers[5] / multipliers[0], rel=1e-8
    )


def test_cinema_two_normal_bonus_and_cinema_six_penetration_bonus_are_separate_lanes() -> None:
    _, cinema_two = _definition(cinema_level=2)
    normal_base = _execute_starlight_entry(
        cinema_two,
        "basic-high-mileage-starlight",
    )
    normal_bonus = _execute_starlight_entry(
        cinema_two,
        "basic-high-mileage-starlight",
        enabled_rule_suffixes=("cinema2:listed-move-damage",),
    )
    assert normal_base.output.complete and normal_bonus.output.complete
    assert normal_base.output.known_total is not None
    assert normal_bonus.output.known_total is not None
    assert normal_bonus.output.known_total / normal_base.output.known_total == pytest.approx(1.5)

    _, cinema_six = _definition(cinema_level=6)
    base = _execute_starlight_entry(cinema_six, "basic-high-mileage-starlight")
    penetration_bonus = _execute_starlight_entry(
        cinema_six,
        "basic-high-mileage-starlight",
        enabled_rule_suffixes=("cinema6:listed-penetration-damage-bonus",),
    )
    both = _execute_starlight_entry(
        cinema_six,
        "basic-high-mileage-starlight",
        enabled_rule_suffixes=(
            "cinema6:listed-penetration-damage-bonus",
            "cinema6:consumed-starshine-whole-move-ratio",
        ),
        parameter_overrides={str(STARLIGHT_BILLY_C6_CONSUMED_STARSHINE): 2},
    )
    assert all(item.output.complete for item in (base, penetration_bonus, both))
    assert all(item.output.known_total is not None for item in (base, penetration_bonus, both))
    base_ratio = _entry(cinema_six, "basic-high-mileage-starlight").multiplier_variants[0].multiplier.value.value
    assert penetration_bonus.output.known_total / base.output.known_total == pytest.approx(1.18)
    assert both.output.known_total / base.output.known_total == pytest.approx(
        1.18 * (base_ratio + 2.0) / base_ratio,
        rel=1e-8,
    )


def test_registry_derives_roster_eligibility_and_registers_physical_signature() -> None:
    raw = load_character_record(str(STARLIGHT_BILLY_ID))
    assert raw["source_version"] == SOURCE_VERSION
    assert raw["source_url"] == SOURCE_URL

    registration = registration_for(STARLIGHT_BILLY_ID)
    assert registration.role is CharacterRole.RUPTURE
    assert registration.catalog.display_name == "星徽·比利"
    catalog_item = next(
        item
        for item in supported_character_catalog()
        if item.character_id == str(STARLIGHT_BILLY_ID)
    )
    assert catalog_item.code_name == "Starlight - Billy"
    assert catalog_item.specialty == "rupture"

    rule_suffix = "extra-ability:starshine-damage"
    alone = compile_registered_definition(
        STARLIGHT_BILLY_ID,
        {"core_level": 7, "cinema_level": 0},
        [STARLIGHT_BILLY_ID],
    )
    assert _rule(alone, rule_suffix).eligibility is RuleEligibility.INELIGIBLE
    for role in (CharacterRole.STUN, CharacterRole.DEFENSE, CharacterRole.SUPPORT):
        teammate = next(
            item.character_id
            for item in supported_character_registrations()
            if item.character_id != STARLIGHT_BILLY_ID and item.role is role
        )
        definition = compile_registered_definition(
            STARLIGHT_BILLY_ID,
            {"core_level": 7, "cinema_level": 0},
            [STARLIGHT_BILLY_ID, teammate],
        )
        assert _rule(definition, rule_suffix).eligibility is RuleEligibility.ELIGIBLE

    assert SIGNATURE_WENGINE_BY_CHARACTER[STARLIGHT_BILLY_ID] == WENGINE_GLOWING_HELM_ID
    engine = compile_wengine(
        WEngineBuildInput(WENGINE_GLOWING_HELM_ID, STARLIGHT_BILLY_ID),
        owner_capabilities=registration.equipment_capabilities,
    )
    stack_rule = next(
        item
        for item in engine.rule_items
        if item.rule_id.endswith("physical-penetration-damage-per-stack")
    )
    assert stack_rule.eligibility is RuleEligibility.ELIGIBLE
    assert stack_rule.effects[0].result.modifier_path is CalculationNode.PENETRATION_DAMAGE_BONUS
    assert stack_rule.stack_count == 2
    assert stack_rule.stack_max == 2


def test_registered_editor_and_signature_build_preview_use_defaults_and_panel_values() -> None:
    editor = build_registered_editor_view(
        STARLIGHT_BILLY_ID,
        {},
        [STARLIGHT_BILLY_ID],
    )
    fields = {item.field_id: item.value for item in editor.compile_config_fields}
    assert fields["core_level"] == 7
    assert fields["cinema_level"] == 0
    assert fields["skill_level:ultimate"] == 12
    assert len(editor.moves) == 17
    assert all(item.damage_type == DamageType.PENETRATION.value for item in editor.moves)

    preview = build_registered_build_preview(
        STARLIGHT_BILLY_ID,
        team_character_ids=[STARLIGHT_BILLY_ID],
        level=60,
        wengine_id=str(WENGINE_GLOWING_HELM_ID),
        wengine_refinement=1,
    )
    assert preview.complete
    assert not preview.diagnostics
    assert preview.out_of_combat_stats["hp"] == pytest.approx(
        preview.base_stats["hp"] * 1.3
    )
    assert preview.out_of_combat_stats["attack"] == pytest.approx(
        preview.base_stats["attack"] + 713.0
    )
    assert preview.out_of_combat_stats["penetration_force"] == pytest.approx(
        preview.out_of_combat_stats["attack"]
        * 0.30
        + preview.out_of_combat_stats["hp"] * 0.10
    )


def test_calculation_api_uses_current_max_hp_core_force_and_current_crit_state() -> None:
    entry_id = "move-entry:character:1531:basic-high-mileage-starlight"
    lower_hp = calculate_payload(_api_payload(move_entry_id=entry_id, hp=10000.0))
    higher_hp = calculate_payload(_api_payload(move_entry_id=entry_id, hp=20000.0))
    lower_breakdown = _api_breakdown(lower_hp)
    higher_breakdown = _api_breakdown(higher_hp)
    assert lower_hp["totals"]["non-crit"]["complete"]
    assert higher_hp["totals"]["non-crit"]["complete"]
    assert lower_breakdown["character.current.max-hp"] == pytest.approx(10000.0)
    assert higher_breakdown["character.current.max-hp"] == pytest.approx(20000.0)
    assert higher_breakdown["penetration.force"] - lower_breakdown["penetration.force"] == pytest.approx(
        1000.0
    )
    assert len(lower_hp["events"]) == 1
    assert lower_hp["events"][0]["damage_type"] == DamageType.PENETRATION.value

    crit_entry = "move-entry:character:1531:special-motor-suppression"
    crit_response = calculate_payload(
        _api_payload(
            move_entry_id=crit_entry,
            conditions={str(STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE): True},
            enabled_rules=(
                "rule:character:1531:core:motor-suppression-crit-damage",
            ),
        )
    )
    assert crit_response["totals"]["non-crit"]["complete"]
    assert _api_breakdown(crit_response)["character.current.crit-damage"] == pytest.approx(
        1.4
    )


def test_calculation_api_scopes_c1_c2_and_extra_ability_to_owner_and_selected_moves() -> None:
    c1_entry = "move-entry:character:1531:dash-star-emblem-punishment"
    c1_response = calculate_payload(
        _api_payload(
            move_entry_id=c1_entry,
            cinema_level=1,
            conditions={str(STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE): True},
            enabled_rules=(
                "rule:character:1531:cinema1:physical-resistance-ignore",
            ),
        )
    )
    assert c1_response["totals"]["non-crit"]["complete"]
    assert _api_breakdown(c1_response)["resistance.damage-ignore"] == pytest.approx(0.18)

    c2_condition = {str(STARLIGHT_BILLY_C2_TURBO_ACTIVE): True}
    c2_enabled = ("rule:character:1531:cinema2:turbo-lone-wheel-crit-damage",)
    lone_wheel = calculate_payload(
        _api_payload(
            move_entry_id="move-entry:character:1531:ex-lone-wheel-stunt",
            cinema_level=2,
            conditions=c2_condition,
            enabled_rules=c2_enabled,
        )
    )
    grip_hub = calculate_payload(
        _api_payload(
            move_entry_id="move-entry:character:1531:ex-grip-hub",
            cinema_level=2,
            conditions=c2_condition,
            enabled_rules=c2_enabled,
        )
    )
    assert lone_wheel["totals"]["non-crit"]["complete"]
    assert grip_hub["totals"]["non-crit"]["complete"]
    assert _api_breakdown(lone_wheel)["character.current.crit-damage"] == pytest.approx(1.0)
    assert _api_breakdown(grip_hub)["character.current.crit-damage"] == pytest.approx(0.5)

    extra_parameters = {str(STARLIGHT_BILLY_EXTRA_ABILITY_STACKS): 2}
    extra_rule = ("rule:character:1531:extra-ability:starshine-damage",)
    self_response = calculate_payload(
        _api_payload(
            move_entry_id="move-entry:character:1531:basic-high-mileage-starlight",
            team_character_ids=(str(STARLIGHT_BILLY_ID), "character:1011"),
            parameters=extra_parameters,
            enabled_rules=extra_rule,
        )
    )
    teammate_response = calculate_payload(
        _api_payload(
            primary_character_id="character:1011",
            move_entry_id="move-entry:character:1011:basic-falling-thunder",
            team_character_ids=("character:1011", str(STARLIGHT_BILLY_ID)),
            parameters=extra_parameters,
            enabled_rules=extra_rule,
        )
    )
    assert self_response["totals"]["non-crit"]["complete"]
    assert teammate_response["totals"]["non-crit"]["complete"]
    assert _api_breakdown(self_response)["damage.normal-bonus"] == pytest.approx(0.4)
    assert _api_breakdown(teammate_response)["damage.normal-bonus"] == pytest.approx(0.0)


def test_calculation_api_c6_adds_consumed_layers_to_only_selected_whole_move() -> None:
    _, c6 = _definition(cinema_level=6)
    for entry_key in ("basic-high-mileage-starlight", "ultimate-knight-flying-kick"):
        entry_id = f"move-entry:character:1531:{entry_key}"
        base = calculate_payload(
            _api_payload(move_entry_id=entry_id, cinema_level=6)
        )
        enhanced = calculate_payload(
            _api_payload(
                move_entry_id=entry_id,
                cinema_level=6,
                parameters={str(STARLIGHT_BILLY_C6_CONSUMED_STARSHINE): 2},
                enabled_rules=(
                    "rule:character:1531:cinema6:consumed-starshine-whole-move-ratio",
                    "rule:character:1531:cinema6:listed-penetration-damage-bonus",
                ),
            )
        )
        assert base["totals"]["non-crit"]["complete"]
        assert enhanced["totals"]["non-crit"]["complete"]
        assert len(base["events"]) == len(enhanced["events"]) == 1
        base_ratio = _entry(c6, entry_key).multiplier_variants[0].multiplier.value.value
        expected_ratio = (base_ratio + 2.0) / base_ratio * 1.18
        assert (
            enhanced["totals"]["non-crit"]["value"]
            / base["totals"]["non-crit"]["value"]
            == pytest.approx(expected_ratio, rel=1e-8)
        )
        assert _api_breakdown(enhanced)["damage.skill-multiplier"] == pytest.approx(
            base_ratio + 2.0
        )


def test_core_cinema_configuration_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="character:1531"):
        StarlightBillyCompileConfig(character_id=type(STARLIGHT_BILLY_ID)("character:1421"))
    with pytest.raises(ValueError, match="core_level"):
        StarlightBillyCompileConfig(core_level=8)
    with pytest.raises(ValueError, match="cinema_level"):
        StarlightBillyCompileConfig(cinema_level=7)
    with pytest.raises(ValueError, match="unique"):
        StarlightBillyCompileConfig(
            skill_levels=(
                CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 10),
                CharacterSkillLevel(SkillGroup.BASIC_ATTACK, 11),
            )
        )
