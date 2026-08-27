"""Immutable inputs and provenance returned by the application execution layer."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import (
    AnomalyRecord,
    BattleStateId,
    BattleTime,
    CharacterSnapshot,
    DamageEvent,
    EffectId,
    EnemySnapshot,
    EventTemplateId,
    Modifier,
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
from ..scenario import CalculationScenario


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
    base_calculation_modifiers: tuple[Modifier, ...] = ()
    history_records: tuple[AnomalyRecord, ...] = ()
    crit_display_mode: CritDisplayMode = CritDisplayMode.EXPECTED

    def __post_init__(self) -> None:
        self.definition.validate_scenario(self.scenario)
        if self.target_snapshot.enemy_id != self.target_profile.enemy_id:
            raise ValueError("target snapshot and target profile must match")
        snapshot_ids = tuple(
            item.character_id for item in self.base_character_snapshots
        )
        if len(set(snapshot_ids)) != len(snapshot_ids):
            raise ValueError("base character snapshot IDs must be unique")
        profile_ids = tuple(item.character_id for item in self.team_profiles)
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("team profile IDs must be unique")
        if self.scenario.current_operator not in set(profile_ids):
            raise ValueError("scenario current_operator must be a team member")


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
class DamageEventExecutionTrace:
    semantic_id: DamageEventSemanticId
    rule_matches: tuple[RuleItemMatchResult, ...]
    applied_modifiers: tuple[Modifier, ...] = ()
    created_by_effect_id: EffectId | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class MoveCalculationExecution:
    output: MoveCalculationOutput
    resolved_character_snapshots: tuple[CharacterSnapshot, ...]
    event_traces: tuple[DamageEventExecutionTrace, ...]

    def __post_init__(self) -> None:
        output_ids = tuple(item.semantic_id for item in self.output.events)
        trace_ids = tuple(item.semantic_id for item in self.event_traces)
        if len(set(trace_ids)) != len(trace_ids):
            raise ValueError("event execution trace semantic IDs must be unique")
        if set(output_ids) != set(trace_ids):
            raise ValueError(
                "event traces must correspond exactly to move output events"
            )
