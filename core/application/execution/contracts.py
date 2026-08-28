"""Immutable inputs and provenance returned by the application execution layer."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import (
    AnomalyRecord,
    BattleStateId,
    BattleTime,
    CharacterId,
    CharacterSnapshot,
    CalculationNode,
    DamageEvent,
    EffectId,
    EffectOperation,
    EnemySnapshot,
    EventTemplateId,
    InitialCharacterSnapshot,
    Modifier,
    Resolvable,
    SnapshotRule,
)

from ..characters.definition import CharacterCalculationDefinition
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
from ..rules import CalculationRuleItem


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

    def __post_init__(self) -> None:
        self.definition.validate_scenario(self.scenario)
        definitions = (self.definition, *self.supporting_definitions)
        definition_character_ids = tuple(
            item.character_id for item in definitions
        )
        if len(set(definition_character_ids)) != len(definition_character_ids):
            raise ValueError(
                "primary and supporting definitions must have unique character IDs"
            )
        for definition in self.supporting_definitions:
            definition.validate_scenario(self.scenario)
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
            rule
            for definition in definitions
            for rule in definition.rule_items
        ) + tuple(self.additional_rule_items)
        rule_ids = tuple(item.rule_id for item in rule_items)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError(
                "primary and supporting definitions must have unique RuleItem IDs"
            )
        rule_map = {item.rule_id: item for item in rule_items}
        known_condition_ids = set(condition_ids)
        for rule in self.additional_rule_items:
            unknown = set(rule.condition_ids) - known_condition_ids
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
        for selection in self.scenario.rule_stack_counts:
            rule = rule_map.get(selection.rule_item_id)
            if rule is None:
                raise ValueError(
                    "scenario stack selection references an unknown RuleItem"
                )
            if rule.stack_count is None:
                raise ValueError(
                    "scenario stack selection references a non-stacked RuleItem"
                )
            if rule.stack_min is not None and selection.value < rule.stack_min:
                raise ValueError("scenario stack selection is below the rule minimum")
            if rule.stack_max is not None and selection.value > rule.stack_max:
                raise ValueError("scenario stack selection exceeds the rule maximum")

        effects = tuple(
            effect
            for rule in rule_items
            for effect in rule.effects
        )
        effect_ids = tuple(effect.rule.effect_id for effect in effects)
        if len(set(effect_ids)) != len(effect_ids):
            raise ValueError(
                "primary and supporting definitions must have unique Effect IDs"
            )
        templates = tuple(
            template
            for definition in definitions
            for template in definition.damage_event_templates
        )
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
    created_by_effect_id: EffectId | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


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
