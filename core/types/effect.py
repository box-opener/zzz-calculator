"""Declarative Effect structure only; matching and execution are later tickets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypeAlias

from .calculation_node import CalculationNode
from .common import (
    CharacterId,
    EffectId,
    EventTemplateId,
    MoveId,
    Resolvable,
    Resolved,
    StateId,
    Unresolved,
)
from .enums import (
    BattleEventKind,
    CharacterRole,
    DamageSubtype,
    DamageTag,
    DamageType,
    DynamicIdentity,
    EffectOperation,
    EffectTarget,
    Element,
    FieldPosition,
    OperationState,
    SkillGroup,
    SnapshotRule,
    StateChangeAction,
)
from .source import RuleSource

if TYPE_CHECKING:
    from .state import State


@dataclass(frozen=True, slots=True)
class EventSelector:
    event_kind: BattleEventKind
    move_id: MoveId | None = None


@dataclass(frozen=True, slots=True)
class AlwaysCondition:
    kind: Literal["always"] = field(default="always", init=False)


@dataclass(frozen=True, slots=True)
class AllCondition:
    conditions: tuple["Condition", ...]
    kind: Literal["all"] = field(default="all", init=False)


@dataclass(frozen=True, slots=True)
class AnyCondition:
    conditions: tuple["Condition", ...]
    kind: Literal["any"] = field(default="any", init=False)


@dataclass(frozen=True, slots=True)
class NotCondition:
    condition: "Condition"
    kind: Literal["not"] = field(default="not", init=False)


@dataclass(frozen=True, slots=True)
class StatePresentCondition:
    subject: EffectTarget
    state_id: StateId
    kind: Literal["state-present"] = field(default="state-present", init=False)


@dataclass(frozen=True, slots=True)
class DynamicIdentityCondition:
    identity: DynamicIdentity
    kind: Literal["dynamic-identity"] = field(default="dynamic-identity", init=False)


Condition: TypeAlias = (
    AlwaysCondition
    | AllCondition
    | AnyCondition
    | NotCondition
    | StatePresentCondition
    | DynamicIdentityCondition
    | Unresolved
)


@dataclass(frozen=True, slots=True)
class ElementFilter:
    element: Element


@dataclass(frozen=True, slots=True)
class DamageTypeFilter:
    damage_type: DamageType


@dataclass(frozen=True, slots=True)
class DamageSubtypeFilter:
    damage_subtype: DamageSubtype


@dataclass(frozen=True, slots=True)
class DamageTagFilter:
    damage_tag: DamageTag


@dataclass(frozen=True, slots=True)
class SkillGroupFilter:
    skill_group: SkillGroup


@dataclass(frozen=True, slots=True)
class MoveIdFilter:
    move_id: MoveId


@dataclass(frozen=True, slots=True)
class CharacterFilter:
    character_id: CharacterId


@dataclass(frozen=True, slots=True)
class CharacterRoleFilter:
    role: CharacterRole


@dataclass(frozen=True, slots=True)
class DynamicIdentityFilter:
    identity: DynamicIdentity


@dataclass(frozen=True, slots=True)
class CreatedByEffectFilter:
    """Match application provenance carried by an instantiated event wrapper."""

    effect_id: EffectId


@dataclass(frozen=True, slots=True)
class EnemyStateFilter:
    state_id: StateId


@dataclass(frozen=True, slots=True)
class FieldPositionFilter:
    position: FieldPosition


@dataclass(frozen=True, slots=True)
class OperationStateFilter:
    operation_state: OperationState


AtomicFilter: TypeAlias = (
    ElementFilter
    | DamageTypeFilter
    | DamageSubtypeFilter
    | DamageTagFilter
    | SkillGroupFilter
    | MoveIdFilter
    | CharacterFilter
    | CharacterRoleFilter
    | DynamicIdentityFilter
    | CreatedByEffectFilter
    | EnemyStateFilter
    | FieldPositionFilter
    | OperationStateFilter
    | Unresolved
)


@dataclass(frozen=True, slots=True)
class AnyFilter:
    filters: tuple[AtomicFilter, ...]


@dataclass(frozen=True, slots=True)
class NotFilter:
    filter: AtomicFilter


EffectFilter: TypeAlias = AtomicFilter | AnyFilter | NotFilter


@dataclass(frozen=True, slots=True)
class EffectRule:
    """All top-level filters are combined with AND; OR and NOT are explicit."""

    effect_id: EffectId
    source: RuleSource
    owner: CharacterId | None
    target: EffectTarget
    snapshot_rule: SnapshotRule
    trigger: EventSelector | None = None
    condition: Condition | None = None
    filters: tuple[EffectFilter, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PanelStatDerivedValue:
    """A deliberately small value source for build-time panel-derived Effects."""

    source_character_id: CharacterId
    source_node: CalculationNode
    coefficient: Resolvable[float]
    cap_max: Resolvable[float] | None = None
    kind: Literal["panel-stat-derived"] = field(
        default="panel-stat-derived",
        init=False,
    )

    def __post_init__(self) -> None:
        if not str(self.source_character_id):
            raise ValueError("derived panel value source character is required")
        if self.source_node is not CalculationNode.CHARACTER_INITIAL_ATTACK:
            raise ValueError(
                "Stage-016 only supports CHARACTER_INITIAL_ATTACK derived values"
            )
        if isinstance(self.coefficient, Resolved) and self.coefficient.value < 0:
            raise ValueError("derived panel value coefficient must be non-negative")
        if isinstance(self.cap_max, Resolved) and self.cap_max.value < 0:
            raise ValueError("derived panel value cap must be non-negative")


ModifierValue: TypeAlias = Resolvable[float] | PanelStatDerivedValue


@dataclass(frozen=True, slots=True)
class ModifierResult:
    modifier_path: CalculationNode
    operation: EffectOperation
    value: ModifierValue


@dataclass(frozen=True, slots=True)
class StateChangeResult:
    action: StateChangeAction
    state_id: StateId | None = None
    state: "State | Unresolved | None" = None


@dataclass(frozen=True, slots=True)
class EventCreationResult:
    event_kind: BattleEventKind
    event_template_id: EventTemplateId | None = None
    unresolved_template: Unresolved | None = None


@dataclass(frozen=True, slots=True)
class ModifierEffect:
    rule: EffectRule
    result: ModifierResult
    result_kind: Literal["modifier"] = field(default="modifier", init=False)


@dataclass(frozen=True, slots=True)
class StateChangeEffect:
    rule: EffectRule
    result: StateChangeResult
    result_kind: Literal["state-change"] = field(default="state-change", init=False)


@dataclass(frozen=True, slots=True)
class EventCreationEffect:
    rule: EffectRule
    result: EventCreationResult
    result_kind: Literal["event-creation"] = field(default="event-creation", init=False)


@dataclass(frozen=True, slots=True)
class UnresolvedEffect:
    rule: EffectRule
    unresolved: Unresolved
    result_kind: Literal["unresolved"] = field(default="unresolved", init=False)


Effect: TypeAlias = (
    ModifierEffect | StateChangeEffect | EventCreationEffect | UnresolvedEffect
)
