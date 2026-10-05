"""Shared primitives for the spec-v1 domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, NewType, TypeAlias, TypeVar


CharacterId = NewType("CharacterId", str)
EnemyId = NewType("EnemyId", str)
DamageEventId = NewType("DamageEventId", str)
BattleEventId = NewType("BattleEventId", str)
BattleOutcomeId = NewType("BattleOutcomeId", str)
BattleStateId = NewType("BattleStateId", str)
AnomalyRecordId = NewType("AnomalyRecordId", str)
LuminanceSpecialSourceId = NewType("LuminanceSpecialSourceId", str)
StateId = NewType("StateId", str)
EffectId = NewType("EffectId", str)
RuleSourceId = NewType("RuleSourceId", str)
MoveId = NewType("MoveId", str)
HitId = NewType("HitId", str)
EventTemplateId = NewType("EventTemplateId", str)
ResourceId = NewType("ResourceId", str)
WEngineId = NewType("WEngineId", str)
DriveDiscSetId = NewType("DriveDiscSetId", str)

Ratio: TypeAlias = float
Multiplier: TypeAlias = float
Seconds: TypeAlias = float
BattleTime: TypeAlias = float


class UnresolvedReason(StrEnum):
    AMBIGUOUS_TEXT = "ambiguous-text"
    AMBIGUOUS_IDENTITY = "ambiguous-identity"
    AMBIGUOUS_ORDERING = "ambiguous-ordering"
    MISSING_SPEC_RULE = "missing-spec-rule"
    NOT_IMPLEMENTED_IN_SPEC = "not-implemented-in-spec"
    MISSING_DATA = "missing-data"


@dataclass(frozen=True, slots=True)
class Unresolved:
    """Unknown data that downstream code is forbidden to guess."""

    reason: UnresolvedReason
    notes: str
    original_text: str | None = None
    candidates: tuple[str, ...] = ()


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Resolved(Generic[T]):
    value: T


Resolvable: TypeAlias = Resolved[T] | Unresolved


@dataclass(frozen=True, slots=True)
class CharacterRef:
    character_id: CharacterId


@dataclass(frozen=True, slots=True)
class EnemyRef:
    enemy_id: EnemyId


@dataclass(frozen=True, slots=True)
class BattleEnvironmentRef:
    pass


EntityRef: TypeAlias = CharacterRef | EnemyRef | BattleEnvironmentRef
