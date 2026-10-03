"""Immutable inputs and provenance returned by the application execution layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.types import (
    AnomalyRecord,
    BattleStateId,
    BattleTime,
    CharacterId,
    CharacterSnapshot,
    CalculationNode,
    DamageEvent,
    EventCreationEffect,
    EffectId,
    EffectOperation,
    EnemySnapshot,
    EventTemplateId,
    InitialCharacterSnapshot,
    Modifier,
    Resolvable,
    SnapshotRule,
    RuleStackCondition,
)

from ..characters.definition import CharacterCalculationDefinition
from ..characters.templates import DamageEventTemplate
from ..diagnostics import CalculationDiagnostic
from ..ids import DamageEventSemanticId, MoveEntryId, RuleItemId
from ..matching import (
    CharacterMatchProfile,
    EnemyMatchProfile,
    RuleItemMatchResult,
)
from ..output import (
    CritDisplayMode,
    MoveCalculationOutput,
)
from ..scenario import CalculationScenario, ConditionResolution, ScenarioCondition
from ..rules import CalculationRuleItem, RuleEligibility
from ..moves import DerivedDamageEventTemplateRef


class HistoryRecordMode(StrEnum):
    """How an execution request obtains anomaly history records.

    ``EXPLICIT`` is the default for callers that own battle history.  The
    presentation calculator can opt into ``STATIC_SINGLE_CHARACTER`` for the
    v1 static-analysis assumption that the typed anomaly triggerer completed
    one gauge alone.  Keeping this choice on the request prevents a generic
    application call from silently inventing records for arbitrary IDs.
    """

    EXPLICIT = "explicit"
    STATIC_SINGLE_CHARACTER = "static-single-character"


@dataclass(frozen=True, slots=True)
class MoveCalculationRequest:
    definition: CharacterCalculationDefinition
    move_entry_id: MoveEntryId
    scenario: CalculationScenario
    battle_state_id: BattleStateId
    battle_time: BattleTime
    base_character_snapshots: tuple[CharacterSnapshot, ...]
    target_snapshot: EnemySnapshot
    team_profiles: tuple[CharacterMatchProfile, ...]
    target_profile: EnemyMatchProfile
    supporting_definitions: tuple[CharacterCalculationDefinition, ...] = ()
    additional_rule_items: tuple[CalculationRuleItem, ...] = ()
    additional_scenario_conditions: tuple[ScenarioCondition, ...] = ()
    initial_character_snapshots: tuple[InitialCharacterSnapshot, ...] = ()
    base_calculation_modifiers: tuple[Modifier, ...] = ()
    history_records: tuple[AnomalyRecord, ...] = ()
    crit_display_mode: CritDisplayMode = CritDisplayMode.EXPECTED
    history_record_mode: HistoryRecordMode = HistoryRecordMode.EXPLICIT
    additional_damage_event_templates: tuple[DamageEventTemplate, ...] = ()
    additional_derived_damage_events: tuple[DerivedDamageEventTemplateRef, ...] = ()

    def __post_init__(self) -> None:
        # Scenario shape/static validation applies to every definition in the
        # request, but mutually-exclusive variant selection belongs only to
        # the move being executed.  The multiplier resolver owns that
        # selected-entry decision so a missing choice can become a structured
        # blocked calculation instead of rejecting unrelated support entries.
        self.definition.validate_scenario(
            self.scenario,
            selected_move_entry_id=self.move_entry_id,
            require_variant_selection=False,
        )
        definitions = (self.definition, *self.supporting_definitions)
        definition_character_ids = tuple(item.character_id for item in definitions)
        if len(set(definition_character_ids)) != len(definition_character_ids):
            raise ValueError(
                "primary and supporting definitions must have unique character IDs"
            )
        for definition in self.supporting_definitions:
            definition.validate_scenario(
                self.scenario,
                require_variant_selection=False,
            )
        definition_conditions = tuple(
            condition
            for definition in definitions
            for condition in definition.scenario_conditions
        )
        all_conditions = (*definition_conditions, *self.additional_scenario_conditions)
        condition_ids = tuple(item.condition_id for item in all_conditions)
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError(
                "primary, supporting, and additional scenario condition IDs must be unique"
            )
        scenario_conditions = {
            item.condition_id: item for item in self.scenario.conditions
        }
        for condition in self.additional_scenario_conditions:
            actual = scenario_conditions.get(condition.condition_id)
            if actual is None:
                raise ValueError(
                    f"scenario is missing additional condition: {condition.condition_id}"
                )
            if actual.resolution is not condition.resolution:
                raise ValueError(
                    "scenario additional condition resolution does not match definition"
                )
            if (
                condition.resolution is ConditionResolution.STATIC
                and actual.value != condition.value
            ):
                raise ValueError(
                    "scenario cannot override a static additional condition"
                )
        if self.target_snapshot.enemy_id != self.target_profile.enemy_id:
            raise ValueError("target snapshot and target profile must match")
        snapshot_ids = tuple(
            item.character_id for item in self.base_character_snapshots
        )
        if len(set(snapshot_ids)) != len(snapshot_ids):
            raise ValueError("base character snapshot IDs must be unique")
        initial_snapshot_ids = tuple(
            item.character_id for item in self.initial_character_snapshots
        )
        if len(set(initial_snapshot_ids)) != len(initial_snapshot_ids):
            raise ValueError("initial character snapshot IDs must be unique")
        if not set(initial_snapshot_ids).issubset(set(snapshot_ids)):
            raise ValueError(
                "initial character snapshots must correspond to base snapshots"
            )
        profile_ids = tuple(item.character_id for item in self.team_profiles)
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("team profile IDs must be unique")
        if self.scenario.current_operator not in set(profile_ids):
            raise ValueError("scenario current_operator must be a team member")

        rule_items = tuple(
            rule for definition in definitions for rule in definition.rule_items
        ) + tuple(self.additional_rule_items)
        rule_ids = tuple(item.rule_id for item in rule_items)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError(
                "primary and supporting definitions must have unique RuleItem IDs"
            )
        rule_map = {item.rule_id: item for item in rule_items}
        known_condition_ids = set(condition_ids)
        for rule in self.additional_rule_items:
            unknown = (
                set(rule.condition_ids) | set(rule.condition_not_ids)
            ) - known_condition_ids
            if unknown:
                raise ValueError(
                    "additional RuleItem references unknown scenario conditions: "
                    f"{sorted(map(str, unknown))}"
                )
        unknown_enabled = set(self.scenario.enabled_rule_item_ids) - set(rule_ids)
        if unknown_enabled:
            raise ValueError(
                "scenario enables unknown RuleItems: "
                f"{sorted(map(str, unknown_enabled))}"
            )
        scenario_condition_values = {
            item.condition_id: item.value for item in self.scenario.conditions
        }
        non_stacking_groups: dict[str, list[CalculationRuleItem]] = {}
        for rule in rule_items:
            if (
                rule.non_stacking_group_id is None
                or rule.rule_id not in self.scenario.enabled_rule_item_ids
                or rule.eligibility is RuleEligibility.INELIGIBLE
                or any(
                    scenario_condition_values.get(condition_id) is not True
                    for condition_id in rule.condition_ids
                )
                or any(
                    scenario_condition_values.get(condition_id) is not False
                    for condition_id in rule.condition_not_ids
                )
            ):
                continue
            non_stacking_groups.setdefault(rule.non_stacking_group_id, []).append(rule)
        for group_id, group_rules in non_stacking_groups.items():
            selected_stacks = {
                (
                    (selected if selected is not None else rule.stack_count)
                    if rule.stack_count is not None
                    else 1
                )
                for rule in group_rules
                for selected in (self.scenario.selected_stack(rule.rule_id),)
            }
            if len(group_rules) > 1 and len(selected_stacks) > 1:
                raise ValueError(
                    f"non-stacking rule group has conflicting active stacks: {group_id}"
                )
        for selection in self.scenario.rule_stack_counts:
            selected_rule = rule_map.get(selection.rule_item_id)
            if selected_rule is None:
                raise ValueError(
                    "scenario stack selection references an unknown RuleItem"
                )
            if selected_rule.stack_count is None:
                raise ValueError(
                    "scenario stack selection references a non-stacked RuleItem"
                )
            if (
                selected_rule.stack_min is not None
                and selection.value < selected_rule.stack_min
            ):
                raise ValueError("scenario stack selection is below the rule minimum")
            if (
                selected_rule.stack_max is not None
                and selection.value > selected_rule.stack_max
            ):
                raise ValueError("scenario stack selection exceeds the rule maximum")

        effects = tuple(effect for rule in rule_items for effect in rule.effects)
        effect_ids = tuple(effect.rule.effect_id for effect in effects)
        if len(set(effect_ids)) != len(effect_ids):
            raise ValueError(
                "primary and supporting definitions must have unique Effect IDs"
            )
        for effect in effects:
            effect_condition = effect.rule.condition
            if isinstance(
                effect_condition, RuleStackCondition
            ) and effect_condition.rule_item_id not in {
                str(rule_id) for rule_id in rule_map
            }:
                raise ValueError(
                    "Effect RuleStackCondition references an unknown RuleItem"
                )
        templates = tuple(
            template
            for definition in definitions
            for template in definition.damage_event_templates
        ) + self.additional_damage_event_templates
        template_ids = tuple(item.ref.template_id for item in templates)
        if len(set(template_ids)) != len(template_ids):
            raise ValueError(
                "primary and supporting definitions must have unique EventTemplate IDs"
            )
        semantic_ids = tuple(item.ref.semantic_id for item in templates)
        if len(set(semantic_ids)) != len(semantic_ids):
            raise ValueError(
                "primary and supporting definitions must have unique DamageEventSemantic IDs"
            )
        additional_template_ids = {
            item.ref.template_id for item in self.additional_damage_event_templates
        }
        additional_creation_ids = {
            effect.result.event_template_id
            for rule in self.additional_rule_items
            for effect in rule.effects
            if isinstance(effect, EventCreationEffect)
            and effect.result.event_template_id is not None
        }
        additional_derived_ids = {
            item.template.template_id
            for item in self.additional_derived_damage_events
        }
        if additional_creation_ids - additional_template_ids:
            raise ValueError(
                "additional EventCreation references an unregistered W-Engine event template"
            )
        if additional_derived_ids != additional_creation_ids:
            raise ValueError(
                "additional W-Engine templates and derived references must match"
            )


@dataclass(frozen=True, slots=True)
class InstantiatedDamageEvent:
    template_id: EventTemplateId
    semantic_id: DamageEventSemanticId
    label: str
    event: DamageEvent
    source_rule_item_id: RuleItemId | None = None
    created_by_effect_id: EffectId | None = None
    repeat_count: int = 1

    def __post_init__(self) -> None:
        if not str(self.template_id) or not str(self.semantic_id):
            raise ValueError("instantiated event IDs must not be empty")
        if not self.label.strip():
            raise ValueError("instantiated event label must not be empty")
        if self.repeat_count < 0:
            raise ValueError("instantiated event repeat_count must be non-negative")


@dataclass(frozen=True, slots=True)
class EventStatModifier:
    """A per-event stat adjustment with an explicit stat recipient."""

    effect_id: EffectId
    recipient: CharacterId
    modifier_path: CalculationNode
    operation: EffectOperation
    value: Resolvable[float]
    snapshot_rule: SnapshotRule

    def __post_init__(self) -> None:
        if not str(self.effect_id) or not str(self.recipient):
            raise ValueError("event stat modifier identities are required")

    def as_modifier(self) -> Modifier:
        return Modifier(
            effect_id=self.effect_id,
            modifier_path=self.modifier_path,
            operation=self.operation,
            value=self.value,
            snapshot_rule=self.snapshot_rule,
        )


@dataclass(frozen=True, slots=True)
class PanelModifierExecutionTrace:
    """Provenance for a panel modifier applied to a concrete recipient."""

    recipient_character_id: CharacterId
    owner_character_id: CharacterId | None
    rule_item_id: RuleItemId | None
    effect_id: EffectId
    modifier_path: CalculationNode
    operation: EffectOperation
    resolved_value: float
    stack_count: int = 1

    def __post_init__(self) -> None:
        if not str(self.recipient_character_id):
            raise ValueError("panel trace recipient is required")
        if not str(self.effect_id):
            raise ValueError("panel trace effect is required")
        if self.stack_count < 0:
            raise ValueError("panel trace stack_count must be non-negative")


@dataclass(frozen=True, slots=True)
class DamageEventExecutionTrace:
    semantic_id: DamageEventSemanticId
    rule_matches: tuple[RuleItemMatchResult, ...]
    applied_modifiers: tuple[Modifier, ...] = ()
    event_stat_modifiers: tuple[EventStatModifier, ...] = ()
    event_multiplier_modifiers: tuple[Modifier, ...] = ()
    guaranteed_crit_effect_ids: tuple[EffectId, ...] = ()
    created_by_effect_id: EffectId | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()
    base_source_character_id: CharacterId | None = None
    base_source_effect_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MoveCalculationExecution:
    output: MoveCalculationOutput
    resolved_character_snapshots: tuple[CharacterSnapshot, ...]
    event_traces: tuple[DamageEventExecutionTrace, ...]
    panel_traces: tuple[PanelModifierExecutionTrace, ...] = ()

    def __post_init__(self) -> None:
        output_ids = tuple(item.semantic_id for item in self.output.events)
        trace_ids = tuple(item.semantic_id for item in self.event_traces)
        if len(set(trace_ids)) != len(trace_ids):
            raise ValueError("event execution trace semantic IDs must be unique")
        if set(output_ids) != set(trace_ids):
            raise ValueError(
                "event traces must correspond exactly to move output events"
            )
