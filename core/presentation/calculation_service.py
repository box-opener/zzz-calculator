"""Translate named browser inputs into the existing application request."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from core.application import (
    CalculationScenario,
    CharacterMatchProfile,
    CritDisplayMode,
    EnemyMatchProfile,
    MoveCalculationRequest,
    ScenarioRuleStack,
    ScenarioTriggerFact,
    assemble_build,
    calculate_move,
    compile_wengine,
    compile_drive_discs,
    stable_set_id,
)
from core.application.characters.definition import CharacterCalculationDefinition
from core.application.ids import MoveEntryId, RuleItemId
from core.application.rules import CalculationRuleItem
from core.application.scenario import ScenarioCondition
from core.types import (
    BattleEventKind,
    BattleStateId,
    BuildMode,
    BuildStatContribution,
    CharacterBuildDefinition,
    CharacterId,
    BuildContributionTrace,
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
    WEngineBuildInput,
    WEngineId,
    DriveDiscBuildInput,
    DriveDiscSlot,
    DriveDiscStatKey,
    DriveDiscSubstatRoll,
    EquippedDriveDisc,
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


@dataclass(frozen=True, slots=True)
class _BuiltCharacterRecord:
    snapshot: CharacterSnapshot
    initial_snapshot: InitialCharacterSnapshot
    rule_items: tuple[CalculationRuleItem, ...] = ()
    scenario_conditions: tuple[ScenarioCondition, ...] = ()
    provenance: tuple[BuildContributionTrace, ...] = ()


def calculate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the three display modes and return one presentation response."""

    view_request = _presentation_request(payload)
    definitions = _compile_definitions(payload)
    primary = definitions[0]
    supplied_operator = payload.get("current_operator")
    if supplied_operator is not None and str(supplied_operator) != str(
        primary.character_id
    ):
        raise ValueError(
            "current_operator must equal primary_character_id for Direct UI"
        )
    raw_team_ids = payload.get("team_character_ids")
    if not isinstance(raw_team_ids, (list, tuple)):
        raise ValueError("team_character_ids is required")
    team_ids = tuple(CharacterId(str(item)) for item in raw_team_ids)
    if not team_ids or len(set(team_ids)) != len(team_ids):
        raise ValueError("team_character_ids must be a non-empty unique array")
    expected_team_ids = (
        primary.character_id,
        *tuple(
            CharacterId(str(item))
            for item in payload.get("supporting_character_ids", ())
        ),
    )
    if team_ids != expected_team_ids:
        raise ValueError(
            "team_character_ids must exactly equal primary plus supporting character IDs"
        )
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
    additional_rule_items = tuple(
        rule for record in build_records for rule in record.rule_items
    )
    additional_scenario_conditions = tuple(
        condition
        for record in build_records
        for condition in record.scenario_conditions
    )
    build_provenance = tuple(
        trace for record in build_records for trace in record.provenance
    )
    enemy_snapshot, enemy_profile, base_modifiers = _enemy_inputs(view_request.enemy)
    scenario = _scenario(
        payload,
        definitions,
        current_operator,
        team_ids,
        additional_rule_items=additional_rule_items,
        additional_scenario_conditions=additional_scenario_conditions,
    )
    move_entry_id = view_request.move_entry_id
    base_snapshots = tuple(item.snapshot for item in build_records)
    initial_snapshots = tuple(item.initial_snapshot for item in build_records)
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
            battle_state_id=BattleStateId(
                str(payload.get("battle_state_id", "battle:ui"))
            ),
            battle_time=float(payload.get("battle_time", 0.0)),
            base_character_snapshots=base_snapshots,
            initial_character_snapshots=initial_snapshots,
            target_snapshot=enemy_snapshot,
            team_profiles=team_profiles,
            target_profile=enemy_profile,
            additional_rule_items=additional_rule_items,
            additional_scenario_conditions=additional_scenario_conditions,
            base_calculation_modifiers=base_modifiers,
            crit_display_mode=mode,
        )
        executions[mode] = calculate_move(request)
    source_labels = {
        str(rule.rule_id): rule.display_name
        for definition in definitions
        for rule in definition.rule_items
    }
    source_labels.update(
        {str(rule.rule_id): rule.display_name for rule in additional_rule_items}
    )
    source_labels.update(
        {
            str(effect.rule.effect_id): effect.rule.source.label
            for definition in definitions
            for rule in definition.rule_items
            for effect in rule.effects
        }
    )
    source_labels.update(
        {
            str(effect.rule.effect_id): effect.rule.source.label
            for rule in additional_rule_items
            for effect in rule.effects
        }
    )
    source_types = {
        str(rule.rule_id): rule.source.source_type.value
        for definition in definitions
        for rule in definition.rule_items
    }
    source_types.update(
        {
            str(rule.rule_id): rule.source.source_type.value
            for rule in additional_rule_items
        }
    )
    source_types.update(
        {
            str(effect.rule.effect_id): effect.rule.source.source_type.value
            for definition in definitions
            for rule in definition.rule_items
            for effect in rule.effects
        }
    )
    source_types.update(
        {
            str(effect.rule.effect_id): effect.rule.source.source_type.value
            for rule in additional_rule_items
            for effect in rule.effects
        }
    )
    return to_jsonable(
        build_move_calculation_view(
            executions,
            source_labels,
            build_provenance=build_provenance,
            source_types=source_types,
        )
    )


def _compile_definitions(
    payload: Mapping[str, Any]
) -> tuple[CharacterCalculationDefinition, ...]:
    primary_id = str(payload.get("primary_character_id", ""))
    if not primary_id:
        raise ValueError("primary_character_id is required")
    supporting = tuple(
        str(item) for item in payload.get("supporting_character_ids", ())
    )
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
    supporting_ids = tuple(
        str(item) for item in payload.get("supporting_character_ids", ())
    )
    team_ids = (primary_id, *supporting_ids)
    supplied_team_ids = payload.get("team_character_ids")
    if not isinstance(supplied_team_ids, (list, tuple)):
        raise ValueError("team_character_ids is required")
    if tuple(str(item) for item in supplied_team_ids) != team_ids:
        raise ValueError(
            "team_character_ids must exactly equal primary plus supporting character IDs"
        )
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
        try:
            build_mode = BuildMode(
                str(raw.get("build_mode", BuildMode.MANUAL_PANEL.value))
            )
        except ValueError as exc:
            raise ValueError(f"unsupported build_mode: {character_id}") from exc
        if build_mode is BuildMode.EQUIPMENT_BUILD:
            base_stats = raw.get("base_stats")
            if not isinstance(base_stats, Mapping):
                raise ValueError(f"base_stats must be an object: {character_id}")
            stats = raw.get("out_of_combat_stats", base_stats)
        else:
            base_stats = None
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
                build_mode=build_mode,
                base_stats=base_stats,
                wengine_id=(
                    str(raw["wengine_id"])
                    if raw.get("wengine_id") is not None
                    else None
                ),
                wengine_level=int(raw.get("wengine_level", 60)),
                wengine_refinement=int(raw.get("wengine_refinement", 1)),
                drive_discs=_parse_drive_discs(raw.get("drive_discs", ())),
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
        raise ValueError(f"enemy fields are missing: {sorted(missing_enemy_fields)}")
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
            actor_id=(
                str(item["actor_id"]) if item.get("actor_id") is not None else None
            ),
        )
        for item in selected
        if isinstance(item, Mapping)
    )
    if len(selected_inputs) != len(selected):
        raise ValueError("selected trigger input must be an object")
    if any(
        item.actor_id is None or not item.actor_id.strip() for item in selected_inputs
    ):
        raise ValueError(
            "an unspecified trigger must be omitted instead of sending an empty actor"
        )
    selected_conditions = payload.get("condition_values", {})
    selected_parameters = payload.get("parameter_values", {})
    if not isinstance(selected_conditions, Mapping) or not isinstance(
        selected_parameters, Mapping
    ):
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
        enabled_rule_item_ids=frozenset(
            str(item) for item in payload.get("enabled_rule_item_ids", ())
        ),
        selected_trigger_inputs=selected_inputs,
        rule_stack_counts=(
            {
                str(key): int(value)
                for key, value in payload.get("rule_stack_counts", {}).items()
            }
            if isinstance(payload.get("rule_stack_counts", {}), Mapping)
            else {}
        ),
    )


def _parse_drive_discs(raw_value: object) -> tuple[EquippedDriveDisc, ...]:
    if not isinstance(raw_value, Sequence) or isinstance(raw_value, (str, bytes)):
        raise ValueError("drive_discs must be an array")
    discs = []
    for raw in raw_value:
        if not isinstance(raw, Mapping):
            raise ValueError("Drive Disc must be an object")
        raw_substats = raw.get("substats", ())
        if not isinstance(raw_substats, Sequence) or isinstance(
            raw_substats,
            (str, bytes),
        ):
            raise ValueError("Drive Disc substats must be an array")
        substats = []
        for item in raw_substats:
            if not isinstance(item, Mapping):
                raise ValueError("Drive Disc substat must be an object")
            substats.append(
                DriveDiscSubstatRoll(
                    DriveDiscStatKey(str(item.get("stat", ""))),
                    int(item.get("roll_count", 0)),
                )
            )
        raw_main_stat = raw.get("main_stat")
        main_stat = (
            None
            if raw_main_stat is None or str(raw_main_stat) == ""
            else DriveDiscStatKey(str(raw_main_stat))
        )
        discs.append(
            EquippedDriveDisc(
                slot=DriveDiscSlot(int(raw.get("slot", 0))),
                set_id=stable_set_id(
                    str(raw.get("set_id", "")).removeprefix("drive-disc:")
                ),
                main_stat=main_stat,
                substats=tuple(substats),
            )
        )
    return tuple(discs)


def _build_records(
    builds: tuple[CharacterBuildInput, ...],
) -> tuple[_BuiltCharacterRecord, ...]:
    records = []
    for build in builds:
        character_id = CharacterId(build.character_id)
        registration = registration_for(character_id)
        if build.build_mode is BuildMode.MANUAL_PANEL:
            stats = _character_stats(build.out_of_combat_stats, character_id)
            resolved_build = assemble_build(
                CharacterBuildDefinition(
                    character_id=character_id,
                    level=build.level,
                    mode=BuildMode.MANUAL_PANEL,
                    manual_panel_stats=stats,
                )
            )
            records.append(
                _BuiltCharacterRecord(
                    snapshot=resolved_build.character_snapshot,
                    initial_snapshot=resolved_build.initial_snapshot,
                    provenance=resolved_build.provenance,
                )
            )
            continue

        if build.base_stats is None:
            raise ValueError(f"equipment build base_stats is missing: {character_id}")
        base_stats = _character_stats(build.base_stats, character_id)
        rule_items: tuple[CalculationRuleItem, ...] = ()
        conditions: tuple[ScenarioCondition, ...] = ()
        contributions: tuple[BuildStatContribution, ...] = ()
        if build.wengine_id is not None:
            wengine = compile_wengine(
                WEngineBuildInput(
                    WEngineId(build.wengine_id),
                    character_id,
                    level=build.wengine_level,
                    refinement=build.wengine_refinement,
                ),
                owner_capabilities=registration.equipment_capabilities,
            )
            if not wengine.complete:
                messages = "; ".join(item.message for item in wengine.diagnostics)
                raise ValueError(messages)
            contributions = wengine.contributions
            rule_items = wengine.rule_items
            conditions = wengine.scenario_conditions
        if build.drive_discs:
            drive = compile_drive_discs(
                DriveDiscBuildInput(character_id, build.drive_discs),
                owner_capabilities=registration.equipment_capabilities,
            )
            if not drive.complete:
                messages = "; ".join(item.message for item in drive.diagnostics)
                raise ValueError(messages)
            contributions = (*contributions, *drive.contributions)
            rule_items = (*rule_items, *drive.rule_items)
            conditions = (*conditions, *drive.scenario_conditions)
        resolved_build = assemble_build(
            CharacterBuildDefinition(
                character_id=character_id,
                level=build.level,
                mode=BuildMode.EQUIPMENT_BUILD,
                base_stats=base_stats,
                contributions=contributions,
            ),
            rule_items=rule_items,
        )
        if not resolved_build.complete:
            messages = "; ".join(item.message for item in resolved_build.diagnostics)
            raise ValueError(
                messages or f"equipment build is unresolved: {character_id}"
            )
        records.append(
            _BuiltCharacterRecord(
                snapshot=resolved_build.character_snapshot,
                initial_snapshot=resolved_build.initial_snapshot,
                rule_items=rule_items,
                scenario_conditions=conditions,
                provenance=resolved_build.provenance,
            )
        )
    return tuple(records)


def _character_stats(
    raw: Mapping[str, Any], character_id: CharacterId
) -> CharacterStats:
    values = dict(raw)
    element_bonus = raw.get("element_damage_bonus", {})
    if not isinstance(element_bonus, Mapping):
        raise ValueError(f"element_damage_bonus must be an object: {character_id}")
    bonuses = {
        _element(key): Resolved(float(value)) for key, value in element_bonus.items()
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
    *,
    additional_rule_items: tuple[CalculationRuleItem, ...] = (),
    additional_scenario_conditions: tuple[ScenarioCondition, ...] = (),
) -> CalculationScenario:
    condition_values = payload.get("condition_values", {})
    parameter_values = payload.get("parameter_values", {})
    if not isinstance(condition_values, Mapping) or not isinstance(
        parameter_values, Mapping
    ):
        raise ValueError("condition_values and parameter_values must be objects")
    known_condition_ids = {
        condition.condition_id
        for definition in definitions
        for condition in definition.scenario_conditions
    }
    known_condition_ids.update(
        condition.condition_id for condition in additional_scenario_conditions
    )
    known_parameter_ids = {
        parameter.parameter_id
        for definition in definitions
        for parameter in definition.scenario_parameters
    }
    unknown_conditions = set(condition_values) - {
        str(item) for item in known_condition_ids
    }
    if unknown_conditions:
        raise ValueError(f"unknown scenario conditions: {sorted(unknown_conditions)}")
    unknown_parameters = set(parameter_values) - {
        str(item) for item in known_parameter_ids
    }
    if unknown_parameters:
        raise ValueError(f"unknown scenario parameters: {sorted(unknown_parameters)}")
    static_condition_values = {
        str(condition.condition_id): condition.value
        for definition in definitions
        for condition in definition.scenario_conditions
        if condition.resolution.value == "static"
    }
    static_condition_values.update(
        {
            str(condition.condition_id): condition.value
            for condition in additional_scenario_conditions
            if condition.resolution.value == "static"
        }
    )
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
                        value=condition_values.get(
                            str(condition.condition_id), condition.value
                        ),
                    )
                )
        for parameter in definition.scenario_parameters:
            if any(item.parameter_id == parameter.parameter_id for item in parameters):
                continue
            parameters.append(
                replace(
                    parameter,
                    value=parameter_values.get(
                        str(parameter.parameter_id), parameter.value
                    ),
                )
            )
    for condition in additional_scenario_conditions:
        if any(item.condition_id == condition.condition_id for item in conditions):
            continue
        if condition.resolution.value == "static":
            conditions.append(condition)
        else:
            conditions.append(
                replace(
                    condition,
                    value=condition_values.get(
                        str(condition.condition_id), condition.value
                    ),
                )
            )
    for condition_id, value in condition_values.items():
        if value is not None and not isinstance(value, bool):
            raise ValueError(
                f"scenario condition must be boolean or null: {condition_id}"
            )
    for parameter_id, value in parameter_values.items():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise ValueError(
                f"scenario parameter must be integer or null: {parameter_id}"
            )
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
        known_trigger_effect_ids.update(
            effect.rule.effect_id
            for rule in additional_rule_items
            for effect in rule.effects
            if effect.rule.trigger is not None
            and effect.rule.trigger.event_kind is BattleEventKind.SUPPORT_ENTRY
        )
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
    known_rule_ids.update(rule.rule_id for rule in additional_rule_items)
    if enabled is None:
        enabled_ids = frozenset(
            {
                rule.rule_id
                for definition in definitions
                for rule in definition.rule_items
                if rule.eligibility.value != "ineligible"
            }
            | {
                rule.rule_id
                for rule in additional_rule_items
                if rule.eligibility.value != "ineligible"
            }
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
