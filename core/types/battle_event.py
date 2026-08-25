"""Battle events and their independent, explicitly ordered outcomes."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .common import (
    BattleEventId,
    BattleOutcomeId,
    BattleStateId,
    BattleTime,
    CharacterId,
    EnemyId,
    HitId,
    MoveId,
    ResourceId,
    Resolvable,
    Resolved,
    Unresolved,
)
from .damage_event import DamageEvent
from .effect import EventCreationResult, StateChangeResult
from .enums import ANOMALY_ELEMENTS, Element, ResourceKind, SkillGroup


@dataclass(frozen=True, slots=True)
class BattleEventMetadata:
    event_id: BattleEventId
    battle_state_id: BattleStateId
    occurred_at: BattleTime


@dataclass(frozen=True, slots=True)
class SkillHitEvent:
    metadata: BattleEventMetadata
    actor: CharacterId
    target_enemy: EnemyId
    element: Element
    skill_group: SkillGroup
    move_id: MoveId
    hit_id: HitId
    kind: Literal["skill-hit"] = field(default="skill-hit", init=False)


@dataclass(frozen=True, slots=True)
class AnomalyBuildupEvent:
    metadata: BattleEventMetadata
    contributor: CharacterId
    target_enemy: EnemyId
    element: Element
    calculated_buildup: Resolvable[float]
    anomaly_effect_strength: Resolvable[float]
    impact_strength: Resolvable[float]
    kind: Literal["anomaly-buildup"] = field(
        default="anomaly-buildup", init=False
    )

    def __post_init__(self) -> None:
        if self.element not in ANOMALY_ELEMENTS:
            raise ValueError("luminance has no ordinary anomaly buildup event")
        if isinstance(self.calculated_buildup, Resolved) and (
            not math.isfinite(self.calculated_buildup.value)
            or self.calculated_buildup.value < 0
        ):
            raise ValueError("calculated anomaly buildup must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class DazeEvent:
    metadata: BattleEventMetadata
    daze_source: CharacterId
    target_enemy: EnemyId
    calculated_daze: Resolvable[float]
    kind: Literal["daze"] = field(default="daze", init=False)


BattleEvent: TypeAlias = SkillHitEvent | AnomalyBuildupEvent | DazeEvent | DamageEvent


@dataclass(frozen=True, slots=True)
class DamageEventOutcome:
    outcome_id: BattleOutcomeId
    event: DamageEvent
    kind: Literal["damage-event"] = field(default="damage-event", init=False)


@dataclass(frozen=True, slots=True)
class AnomalyBuildupOutcome:
    outcome_id: BattleOutcomeId
    event: AnomalyBuildupEvent
    kind: Literal["anomaly-buildup"] = field(
        default="anomaly-buildup", init=False
    )


@dataclass(frozen=True, slots=True)
class DazeOutcome:
    outcome_id: BattleOutcomeId
    event: DazeEvent
    kind: Literal["daze"] = field(default="daze", init=False)


@dataclass(frozen=True, slots=True)
class ResourceChangeOutcome:
    """A positive delta gains a resource; a negative delta consumes it."""

    outcome_id: BattleOutcomeId
    target_character: CharacterId
    resource: ResourceKind | ResourceId
    delta: Resolvable[float]
    kind: Literal["resource-change"] = field(
        default="resource-change", init=False
    )


@dataclass(frozen=True, slots=True)
class StateChangeOutcome:
    outcome_id: BattleOutcomeId
    change: StateChangeResult
    kind: Literal["state-change"] = field(default="state-change", init=False)


@dataclass(frozen=True, slots=True)
class EventCreationOutcome:
    outcome_id: BattleOutcomeId
    creation: EventCreationResult
    kind: Literal["event-creation"] = field(default="event-creation", init=False)


BattleEventOutcome: TypeAlias = (
    DamageEventOutcome
    | AnomalyBuildupOutcome
    | DazeOutcome
    | ResourceChangeOutcome
    | StateChangeOutcome
    | EventCreationOutcome
)


@dataclass(frozen=True, slots=True)
class OutcomeDependency:
    before: BattleOutcomeId
    after: BattleOutcomeId


@dataclass(frozen=True, slots=True)
class BattleEventResult:
    """Outcome tuple order is storage-only; dependencies carry order semantics."""

    source_event_id: BattleEventId
    outcomes: tuple[BattleEventOutcome, ...]
    dependencies: tuple[OutcomeDependency, ...] = ()
    unresolved_ordering: Unresolved | None = None

    def __post_init__(self) -> None:
        outcome_ids = tuple(outcome.outcome_id for outcome in self.outcomes)
        if len(set(outcome_ids)) != len(outcome_ids):
            raise ValueError("battle outcome IDs must be unique")

        known_ids = set(outcome_ids)
        dependency_pairs: set[tuple[BattleOutcomeId, BattleOutcomeId]] = set()
        graph = {outcome_id: set() for outcome_id in outcome_ids}
        indegree = {outcome_id: 0 for outcome_id in outcome_ids}
        for dependency in self.dependencies:
            if dependency.before not in known_ids or dependency.after not in known_ids:
                raise ValueError("outcome dependency references an unknown outcome")
            if dependency.before == dependency.after:
                raise ValueError("outcome dependency cannot reference itself")
            pair = (dependency.before, dependency.after)
            if pair in dependency_pairs:
                raise ValueError("duplicate outcome dependency")
            dependency_pairs.add(pair)
            graph[dependency.before].add(dependency.after)
            indegree[dependency.after] += 1

        ready = [outcome_id for outcome_id, degree in indegree.items() if degree == 0]
        visited = 0
        while ready:
            outcome_id = ready.pop()
            visited += 1
            for next_id in graph[outcome_id]:
                indegree[next_id] -= 1
                if indegree[next_id] == 0:
                    ready.append(next_id)
        if visited != len(outcome_ids):
            raise ValueError("outcome dependencies cannot contain a cycle")
