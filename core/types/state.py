"""Persistent State objects; Effects remain separate rule objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .common import EntityRef, Resolvable, Seconds, StateId, Unresolved
from .effect import Effect
from .enums import BattleEventKind, StateKind
from .source import RuleSource


@dataclass(frozen=True, slots=True)
class TimedDuration:
    total_seconds: Resolvable[Seconds]
    remaining_seconds: Resolvable[Seconds]


@dataclass(frozen=True, slots=True)
class UntilEventDuration:
    event_kind: BattleEventKind


Duration: TypeAlias = TimedDuration | UntilEventDuration | Unresolved | None


@dataclass(frozen=True, slots=True)
class StackingRule:
    max_stacks: Resolvable[int]
    independent_duration_per_stack: Resolvable[bool]
    refreshes_duration: Resolvable[bool]


@dataclass(frozen=True, slots=True)
class State:
    state_id: StateId
    kind: StateKind
    holder: EntityRef
    source: RuleSource
    duration: Duration
    stacking: StackingRule | None
    current_stacks: int
    effects: tuple[Effect, ...] = ()

    def __post_init__(self) -> None:
        if self.current_stacks < 1:
            raise ValueError("a persisted State must have at least one active stack")
