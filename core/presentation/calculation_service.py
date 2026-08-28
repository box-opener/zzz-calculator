"""Translate named browser inputs into the existing application request."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from core.application import (
    CalculationScenario,
    CharacterMatchProfile,
    CritDisplayMode,
    EnemyMatchProfile,
    MoveCalculationRequest,
    ScenarioRuleStack,
    ScenarioTriggerFact,
    calculate_move,
)
from core.application.characters.definition import CharacterCalculationDefinition
from core.application.ids import MoveEntryId, RuleItemId
from core.types import (
    BattleEventKind,
    BattleStateId,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    CalculationNode,
    EffectId,
    Element,
    EnemyId,
    EnemySnapshot,
    InitialCharacterSnapshot,
    Modifier,
    EffectOperation,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from core.presentation.assembler import build_move_calculation_view
from core.presentation.requests import (
    CharacterBuildInput,
    EnemyInput,
    MoveCalculationViewRequest,
    SelectedTriggerInput,
)
from core.presentation.serialization import to_jsonable
from core.presentation.registry import (
    registration_for,
    compile_registered_definition,
)


def calculate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the three display modes and return one presentation response."""

    view_request = _presentation_request(payload)
    definitions = _compile_definitions(payload)
    primary = definitions[0]
    supplied_operator = payload.get("current_operator")
    if supplied_operator is not None and str(supplied_operator) != str(primary.character_id):
        raise ValueError("current_operator must equal primary_character_id for Direct UI")
    raw_team_ids = payload.get("team_character_ids")
    if not isinstance(raw_team_ids, (list, tuple)):
        raise ValueError("team_character_ids is required")
    team_ids = tuple(
        CharacterId(str(item))
        for item in raw_team_ids
    )
    if not team_ids or len(set(team_ids)) != len(team_ids):
        raise ValueError("team_character_ids must be a non-empty unique array")
    for character_id in team_ids:
        registration_for(character_id)
    definition_ids = {definition.character_id for definition in definitions}
    if not set(team_ids).issubset(definition_ids):
        raise ValueError("every team character must have a compiled definition")
    required_resistances = {
        registration_for(definition.character_id).base_element.value
        for definition in definitions
    }
    missing_resistances = required_resistances - set(
        payload.get("enemy", {}).get("damage_resistance", {})
        if isinstance(payload.get("enemy"), Mapping)
        else ()
    )
    if missing_resistances:
        raise ValueError(
            f"enemy damage_resistance is missing: {sorted(missing_resistances)}"
        )
    current_operator = CharacterId(primary.character_id)
    if current_operator not in set(team_ids):
        raise ValueError("current_operator must be a team member")

    build_records = _build_records(view_request.character_builds)
    enemy_snapshot, enemy_profile, base_modifiers = _enemy_inputs(view_request.enemy)
    scenario = _scenario(payload, definitions, current_operator, team_ids)
    move_entry_id = view_request.move_entry_id
    base_snapshots = tuple(item[0] for item in build_records)
    initial_snapshots = tuple(item[1] for item in build_records)
    team_profiles = tuple(
        CharacterMatchProfile(
            character_id=character_id,
            role=registration_for(character_id).role,
        )
        for character_id in team_ids
    )
    executions = {}
    for mode in (
        CritDisplayMode.NON_CRIT,
        CritDisplayMode.EXPECTED,
        CritDisplayMode.FULL_CRIT,
    ):
        request = MoveCalculationRequest(
            definition=primary,
            supporting_definitions=definitions[1:],
            move_entry_id=MoveEntryId(move_entry_id),
            scenario=scenario,
            battle_state_id=BattleStateId(str(payload.get("battle_state_id", "battle:ui"))),
            battle_time=float(payload.get("battle_time", 0.0)),
            base_character_snapshots=base_snapshots,
            initial_character_snapshots=initial_snapshots,
            target_snapshot=enemy_snapshot,
            team_profiles=team_profiles,
            target_profile=enemy_profile,
            base_calculation_modifiers=base_modifiers,
            crit_display_mode=mode,
        )
        executions[mode] = calculate_move(request)
    return to_jsonable(build_move_calculation_view(executions))


def _compile_definitions(payload: Mapping[str, Any]) -> tuple[CharacterCalculationDefinition, ...]:
    primary_id = str(payload.get("primary_character_id", ""))
    if not primary_id:
        raise ValueError("primary_character_id is required")
    supporting = tuple(str(item) for item in payload.get("supporting_character_ids", ()))
    ids = (primary_id, *supporting)
    if len(set(ids)) != len(ids):
        raise ValueError("primary and supporting character IDs must be unique")
    configs = payload.get("compile_configs", {})
    if not isinstance(configs, Mapping):
        raise ValueError("compile_configs must be an object")
    definitions = []
    for character_id in ids:
        config = configs.get(character_id, {})
        if not isinstance(config, Mapping):
            raise ValueError(f"compile config must be an object: {character_id}")
        definitions.append(
            compile_registered_definition(character_id, dict(config), ids)
        )
    return tuple(definitions)


def _presentation_request(payload: Mapping[str, Any]) -> MoveCalculationViewRequest:
    """Validate the browser-shaped request before domain assembly."""

    primary_id = str(payload.get("primary_character_id", ""))
    if not primary_id:
        raise ValueError("primary_character_id is required")
    supporting_ids = tuple(str(item) for item in payload.get("supporting_character_ids", ()))
    team_ids = (primary_id, *supporting_ids)
    raw_builds = payload.get("character_builds")
    if not isinstance(raw_builds, Mapping):
        raise ValueError("character_builds must be an object keyed by character ID")
    builds = []
    for character_id in team_ids:
        if character_id not in raw_builds:
            raise ValueError(f"character build is required: {character_id}")
        raw = raw_builds[character_id]
        if not isinstance(raw, Mapping):
            raise ValueError(f"character build must be an object: {character_id}")
        if "level" not in raw:
            raise ValueError(f"character build level is required: {character_id}")
        stats = raw.get("out_of_combat_stats", raw.get("stats"))
        if not isinstance(stats, Mapping):
            raise ValueError(f"out_of_combat_stats must be an object: {character_id}")
        required_stats = {
            "attack",
            "crit_rate",
            "crit_damage",
            "penetration_rate",
            "penetration_flat",
            "element_damage_bonus",
        }
        missing_stats = required_stats - set(stats)
        if missing_stats:
            raise ValueError(
                f"character build stats are missing for {character_id}: "
                f"{sorted(missing_stats)}"
            )
        element_key = registration_for(character_id).base_element.value
        element_bonus = stats["element_damage_bonus"]
        if not isinstance(element_bonus, Mapping) or element_key not in element_bonus:
            raise ValueError(
                f"element_damage_bonus is missing {element_key}: {character_id}"
            )
        builds.append(
            CharacterBuildInput(
                character_id=character_id,
                level=int(raw["level"]),
                out_of_combat_stats=stats,
            )
        )
    raw_enemy = payload.get("enemy")
    if not isinstance(raw_enemy, Mapping):
        raise ValueError("enemy must be an object")
    resistances = raw_enemy.get("damage_resistance", {})
    if not isinstance(resistances, Mapping):
        raise ValueError("enemy damage_resistance must be an object")
    required_enemy_fields = {
        "enemy_id",
        "level",
        "initial_defense",
        "damage_resistance",
        "damage_reduction",
        "stun_vulnerability_bonus",
        "is_stunned",
    }
    missing_enemy_fields = required_enemy_fields - set(raw_enemy)
    if missing_enemy_fields:
        raise ValueError(
            f"enemy fields are missing: {sorted(missing_enemy_fields)}"
        )
    if not isinstance(raw_enemy["is_stunned"], bool):
        raise ValueError("enemy is_stunned must be a boolean")
    enemy = EnemyInput(
        enemy_id=str(raw_enemy["enemy_id"]),
        level=int(raw_enemy["level"]),
        initial_defense=float(raw_enemy["initial_defense"]),
        damage_resistance=resistances,
        damage_reduction=float(raw_enemy["damage_reduction"]),
        stun_vulnerability_bonus=float(raw_enemy["stun_vulnerability_bonus"]),
        is_stunned=raw_enemy["is_stunned"],
    )
    selected = payload.get("selected_trigger_inputs", ())
    if not isinstance(selected, (list, tuple)):
        raise ValueError("selected_trigger_inputs must be an array")
    selected_inputs = tuple(
        SelectedTriggerInput(
            input_id=str(item.get("input_id", "")),
            actor_id=(str(item["actor_id"]) if item.get("actor_id") is not None else None),
        )
        for item in selected
        if isinstance(item, Mapping)
    )
    if len(selected_inputs) != len(selected):
        raise ValueError("selected trigger input must be an object")
    selected_conditions = payload.get("condition_values", {})
    selected_parameters = payload.get("parameter_values", {})
    if not isinstance(selected_conditions, Mapping) or not isinstance(selected_parameters, Mapping):
        raise ValueError("condition_values and parameter_values must be objects")
    move_entry_id = str(payload.get("move_entry_id", ""))
    if not move_entry_id.strip():
        raise ValueError("move_entry_id is required")
    return MoveCalculationViewRequest(
        primary_character_id=primary_id,
        supporting_character_ids=supporting_ids,
        move_entry_id=move_entry_id,
        character_builds=tuple(builds),
        enemy=enemy,
        selected_condition_values=selected_conditions,
        selected_parameter_values=selected_parameters,
        enabled_rule_item_ids=frozenset(str(item) for item in payload.get("enabled_rule_item_ids", ())),
        selected_trigger_inputs=selected_inputs,
        rule_stack_counts={str(key): int(value) for key, value in payload.get("rule_stack_counts", {}).items()} if isinstance(payload.get("rule_stack_counts", {}), Mapping) else {},
    )


def _build_records(
    builds: tuple[CharacterBuildInput, ...],
) -> tuple[tuple[CharacterSnapshot, InitialCharacterSnapshot], ...]:
    records = []
    for build in builds:
        character_id = CharacterId(build.character_id)
        registration_for(character_id)
        stats = _character_stats(build.out_of_combat_stats, character_id)
        records.append(
            (
                CharacterSnapshot(character_id, build.level, stats),
                InitialCharacterSnapshot(character_id, build.level, stats),
            )
        )
    return tuple(records)


def _character_stats(raw: Mapping[str, Any], character_id: CharacterId) -> CharacterStats:
    values = dict(raw)
    element_bonus = raw.get("element_damage_bonus", {})
    if not isinstance(element_bonus, Mapping):
        raise ValueError(f"element_damage_bonus must be an object: {character_id}")
    bonuses = {
        _element(key): Resolved(float(value))
        for key, value in element_bonus.items()
    }
    bonuses.setdefault(registration_for(character_id).base_element, Resolved(0.0))
    def stat(name: str):
        if name in values:
            return Resolved(float(values[name]))
        return Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=f"character stat is not supplied: {name}",
        )

    return CharacterStats(
        hp=stat("hp"),
        attack=stat("attack"),
        defense=stat("defense"),
        impact=stat("impact"),
        crit_rate=stat("crit_rate"),
        crit_damage=stat("crit_damage"),
        anomaly_mastery=stat("anomaly_mastery"),
        anomaly_proficiency=stat("anomaly_proficiency"),
        penetration_rate=stat("penetration_rate"),
        penetration_flat=stat("penetration_flat"),
        energy_regen=stat("energy_regen"),
        element_damage_bonus=bonuses,
    )


def _enemy_inputs(enemy: EnemyInput):
    enemy_id = EnemyId(enemy.enemy_id)
    snapshot = EnemySnapshot(
        enemy_id=enemy_id,
        level=enemy.level,
        initial_defense=Resolved(enemy.initial_defense),
        damage_resistance={
            _element(key): Resolved(float(value))
            for key, value in enemy.damage_resistance.items()
        },
        anomaly_buildup_resistance={},
        daze_resistance=Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes="daze resistance is not supplied by the Direct UI",
        ),
        damage_reduction=Resolved(enemy.damage_reduction),
        is_stunned=enemy.is_stunned,
    )
    profile = EnemyMatchProfile(enemy_id=enemy_id)
    base = Modifier(
        effect_id=EffectId("base:ui:enemy-stun-vulnerability"),
        modifier_path=CalculationNode.ENEMY_STUN_VULNERABILITY,
        operation=EffectOperation.ADD,
        value=Resolved(enemy.stun_vulnerability_bonus),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )
    return snapshot, profile, (base,)


def _scenario(
    payload: Mapping[str, Any],
    definitions: tuple[CharacterCalculationDefinition, ...],
    current_operator: CharacterId,
    team_ids: tuple[CharacterId, ...],
) -> CalculationScenario:
    condition_values = payload.get("condition_values", {})
    parameter_values = payload.get("parameter_values", {})
    if not isinstance(condition_values, Mapping) or not isinstance(parameter_values, Mapping):
        raise ValueError("condition_values and parameter_values must be objects")
    known_condition_ids = {
        condition.condition_id
        for definition in definitions
        for condition in definition.scenario_conditions
    }
    known_parameter_ids = {
        parameter.parameter_id
        for definition in definitions
        for parameter in definition.scenario_parameters
    }
    unknown_conditions = set(condition_values) - {str(item) for item in known_condition_ids}
    if unknown_conditions:
        raise ValueError(f"unknown scenario conditions: {sorted(unknown_conditions)}")
    unknown_parameters = set(parameter_values) - {str(item) for item in known_parameter_ids}
    if unknown_parameters:
        raise ValueError(f"unknown scenario parameters: {sorted(unknown_parameters)}")
    static_condition_values = {
        str(condition.condition_id): condition.value
        for definition in definitions
        for condition in definition.scenario_conditions
        if condition.resolution.value == "static"
    }
    overridden_static = set(condition_values) & set(static_condition_values)
    if overridden_static:
        raise ValueError(
            "static scenario conditions must not be submitted: "
            f"{sorted(overridden_static)}"
        )
    conditions = []
    parameters = []
    for definition in definitions:
        for condition in definition.scenario_conditions:
            if any(item.condition_id == condition.condition_id for item in conditions):
                continue
            if condition.resolution.value == "static":
                conditions.append(condition)
            else:
                conditions.append(
                    replace(
                        condition,
                        value=condition_values.get(str(condition.condition_id), condition.value),
                    )
                )
        for parameter in definition.scenario_parameters:
            if any(item.parameter_id == parameter.parameter_id for item in parameters):
                continue
            parameters.append(
                replace(
                    parameter,
                    value=parameter_values.get(str(parameter.parameter_id), parameter.value),
                )
            )
    for condition_id, value in condition_values.items():
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"scenario condition must be boolean or null: {condition_id}")
    for parameter_id, value in parameter_values.items():
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise ValueError(f"scenario parameter must be integer or null: {parameter_id}")
    trigger_facts = []
    trigger_inputs = payload.get("selected_trigger_inputs", ())
    if not isinstance(trigger_inputs, (list, tuple)):
        raise ValueError("selected_trigger_inputs must be an array")
    for item in trigger_inputs:
        if not isinstance(item, Mapping):
            raise ValueError("selected trigger input must be an object")
        input_id = str(item.get("input_id", ""))
        prefix = "scenario-trigger:"
        suffix = ":actor"
        if not input_id.startswith(prefix) or not input_id.endswith(suffix):
            raise ValueError(f"invalid presentation trigger input: {input_id}")
        effect_id = EffectId(input_id[len(prefix) : -len(suffix)])
        known_trigger_effect_ids = {
            effect.rule.effect_id
            for definition in definitions
            for rule in definition.rule_items
            for effect in rule.effects
            if effect.rule.trigger is not None
            and effect.rule.trigger.event_kind is BattleEventKind.SUPPORT_ENTRY
        }
        if effect_id not in known_trigger_effect_ids:
            raise ValueError(f"unknown presentation trigger input: {input_id}")
        actor = item.get("actor_id")
        actor_id = CharacterId(str(actor)) if actor is not None else None
        if actor_id is not None and actor_id not in team_ids:
            raise ValueError("trigger actor must be a team member")
        trigger_facts.append(
            ScenarioTriggerFact(
                effect_id=effect_id,
                event_kind=BattleEventKind.SUPPORT_ENTRY,
                actor=actor_id,
            )
        )
    enabled = payload.get("enabled_rule_item_ids")
    if "enabled_rule_item_ids" not in payload:
        raise ValueError("enabled_rule_item_ids is required")
    known_rule_ids = {
        rule.rule_id for definition in definitions for rule in definition.rule_items
    }
    if enabled is None:
        enabled_ids = frozenset(
            rule.rule_id
            for definition in definitions
            for rule in definition.rule_items
            if rule.eligibility.value != "ineligible"
        )
    else:
        if not isinstance(enabled, (list, tuple, set, frozenset)):
            raise ValueError("enabled_rule_item_ids must be an array")
        enabled_ids = frozenset(RuleItemId(str(item)) for item in enabled)
        unknown_enabled = enabled_ids - known_rule_ids
        if unknown_enabled:
            raise ValueError(
                "enabled_rule_item_ids contains unknown rules: "
                f"{sorted(map(str, unknown_enabled))}"
            )
    stack_counts = payload.get("rule_stack_counts", {})
    if not isinstance(stack_counts, Mapping):
        raise ValueError("rule_stack_counts must be an object")
    return CalculationScenario(
        scenario_id=str(payload.get("scenario_id", "ui")),
        current_operator=current_operator,
        conditions=tuple(conditions),
        parameters=tuple(parameters),
        trigger_facts=tuple(trigger_facts),
        enabled_rule_item_ids=enabled_ids,
        rule_stack_counts=tuple(
            ScenarioRuleStack(RuleItemId(str(rule_id)), int(value))
            for rule_id, value in stack_counts.items()
        ),
    )


def _element(value: Any) -> Element:
    try:
        return Element(str(value))
    except ValueError as exc:
        raise ValueError(f"unsupported element value: {value}") from exc


__all__ = ["calculate_payload"]
