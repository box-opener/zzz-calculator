"""Declarative Effect structure only; matching and execution are later tickets."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
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


@dataclass(frozen=True, slots=True)
class RuleStackCondition:
    """A predicate over an already-resolved RuleItem stack selection."""

    rule_item_id: str
    required_value: int
    requires_rule_enabled: bool = True
    kind: Literal["rule-stack"] = field(default="rule-stack", init=False)

    def __post_init__(self) -> None:
        if not self.rule_item_id.strip():
            raise ValueError("rule stack condition requires a rule item ID")
        if self.required_value < 0:
            raise ValueError("rule stack condition value must be non-negative")
        if not isinstance(self.requires_rule_enabled, bool):
            raise ValueError("rule stack condition enabled flag must be boolean")


@dataclass(frozen=True, slots=True)
class ScenarioParameterRangeCondition:
    """Match a user-selected integer scenario parameter by inclusive bounds."""

    parameter_id: str
    minimum: int | None = None
    maximum: int | None = None
    kind: Literal["scenario-parameter-range"] = field(
        default="scenario-parameter-range",
        init=False,
    )

    def __post_init__(self) -> None:
        if not self.parameter_id.strip():
            raise ValueError("scenario parameter range requires a parameter ID")
        if self.minimum is None and self.maximum is None:
            raise ValueError("scenario parameter range requires at least one bound")
        if self.minimum is not None and self.minimum < 0:
            raise ValueError("scenario parameter range minimum must be non-negative")
        if self.maximum is not None and self.maximum < 0:
            raise ValueError("scenario parameter range maximum must be non-negative")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("scenario parameter range bounds must be ordered")


@dataclass(frozen=True, slots=True)
class PanelStatThresholdCondition:
    """Compare one explicit initial/current panel node with a threshold."""

    source_character_id: CharacterId
    source_node: CalculationNode
    minimum: float
    kind: Literal["panel-stat-threshold"] = field(
        default="panel-stat-threshold",
        init=False,
    )

    def __post_init__(self) -> None:
        if not str(self.source_character_id):
            raise ValueError("panel threshold source character is required")
        if self.source_node not in {
            CalculationNode.CHARACTER_INITIAL_DEFENSE,
            CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        }:
            raise ValueError("unsupported panel threshold node")
        if not math.isfinite(self.minimum):
            raise ValueError("panel threshold minimum must be finite")


Condition: TypeAlias = (
    AlwaysCondition
    | AllCondition
    | AnyCondition
    | NotCondition
    | StatePresentCondition
    | DynamicIdentityCondition
    | RuleStackCondition
    | ScenarioParameterRangeCondition
    | PanelStatThresholdCondition
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
class EventTemplateIdFilter:
    """Match one exact authored event template, including its move stage."""

    template_id: EventTemplateId


@dataclass(frozen=True, slots=True)
class CharacterFilter:
    character_id: CharacterId


@dataclass(frozen=True, slots=True)
class DamageDealerFilter:
    """Match the character that owns the current damage event."""

    character_id: CharacterId


@dataclass(frozen=True, slots=True)
class CharacterRoleFilter:
    role: CharacterRole


@dataclass(frozen=True, slots=True)
class DynamicIdentityFilter:
    identity: DynamicIdentity


@dataclass(frozen=True, slots=True)
class DamageDealerIdentityFilter:
    """Match the event dealer against an identity resolved from typed facts."""

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
    | EventTemplateIdFilter
    | CharacterFilter
    | DamageDealerFilter
    | CharacterRoleFilter
    | DynamicIdentityFilter
    | DamageDealerIdentityFilter
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
    """A deliberately small value source for build-time panel-derived Effects.

    Reviewed character effects can read a character's immutable initial
    attack, defense, HP, crit rate, or energy regeneration, the final settlement maximum HP, impact,
    anomaly mastery, proficiency, or crit rate. ``threshold`` (and its
    compatibility alias ``minimum``) expresses ``max(source - threshold, 0)``
    before applying the coefficient. ``step_size`` is the source interval for
    a continuous proportional coefficient on the excess; fractional intervals
    contribute proportionally.
    Keeping the source node and threshold explicit prevents a compiler from
    accidentally reading an initial panel value or inventing a cap.
    """

    source_character_id: CharacterId
    source_node: CalculationNode
    coefficient: Resolvable[float]
    base: Resolvable[float] = Resolved(0.0)
    cap_max: Resolvable[float] | None = None
    threshold: Resolvable[float] | None = None
    step_size: Resolvable[float] | None = None
    # ``minimum`` is retained as a named alias for callers that describe this
    # contract in threshold/minimum terms.  Compilers should set both fields
    # to the same value when exposing a thresholded current-panel effect.
    minimum: Resolvable[float] | None = None
    kind: Literal["panel-stat-derived"] = field(
        default="panel-stat-derived",
        init=False,
    )

    def __post_init__(self) -> None:
        if not str(self.source_character_id):
            raise ValueError("derived panel value source character is required")
        if self.source_node not in {
            CalculationNode.CHARACTER_INITIAL_ATTACK,
            CalculationNode.CHARACTER_INITIAL_DEFENSE,
            CalculationNode.CHARACTER_INITIAL_HP,
            CalculationNode.CHARACTER_INITIAL_CRIT_RATE,
            CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
            CalculationNode.CHARACTER_CURRENT_MAX_HP,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            CalculationNode.CHARACTER_CURRENT_IMPACT,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
            CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        }:
            raise ValueError(
                "panel derived values only support initial attack/defense/HP/crit rate/energy regen, "
                "current maximum HP/crit rate/impact, anomaly mastery, or "
                "anomaly proficiency"
            )
        if isinstance(self.coefficient, Resolved) and self.coefficient.value < 0:
            raise ValueError("derived panel value coefficient must be non-negative")
        if isinstance(self.base, Resolved) and self.base.value < 0:
            raise ValueError("derived panel value base must be non-negative")
        if isinstance(self.cap_max, Resolved) and self.cap_max.value < 0:
            raise ValueError("derived panel value cap must be non-negative")
        if isinstance(self.threshold, Resolved) and self.threshold.value < 0:
            raise ValueError("derived panel value threshold must be non-negative")
        if isinstance(self.step_size, Resolved) and self.step_size.value <= 0:
            raise ValueError("derived panel value step_size must be positive")
        if self.step_size is not None and (
            self.source_node
            not in {
                CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
                CalculationNode.CHARACTER_CURRENT_IMPACT,
            }
            or (self.threshold is None and self.minimum is None)
        ):
            raise ValueError(
                "interval-scaled panel values require an initial energy-regeneration or current-impact threshold"
            )
        if isinstance(self.minimum, Resolved) and self.minimum.value < 0:
            raise ValueError("derived panel value minimum must be non-negative")
        if (
            isinstance(self.threshold, Resolved)
            and isinstance(self.minimum, Resolved)
            and self.threshold.value != self.minimum.value
        ):
            raise ValueError("derived panel value threshold and minimum must agree")
        if self.source_node in {
            CalculationNode.CHARACTER_INITIAL_ATTACK,
        } and (
            self.threshold is not None or self.minimum is not None
        ):
            raise ValueError(
                "initial attack derived values cannot declare a panel threshold"
            )


@dataclass(frozen=True, slots=True)
class ScenarioParameterDerivedValue:
    """A linear value derived from one static scenario integer parameter."""

    parameter_id: str
    coefficient: Resolvable[float]
    base: Resolvable[float] = Resolved(0.0)
    cap_max: Resolvable[float] | None = None
    kind: Literal["scenario-parameter-derived"] = field(
        default="scenario-parameter-derived", init=False
    )

    def __post_init__(self) -> None:
        if not self.parameter_id.strip():
            raise ValueError("scenario parameter value source requires an ID")
        if isinstance(self.coefficient, Resolved) and self.coefficient.value < 0:
            raise ValueError("scenario parameter coefficient must be non-negative")
        if isinstance(self.cap_max, Resolved) and self.cap_max.value < 0:
            raise ValueError("scenario parameter value cap must be non-negative")


ModifierValue: TypeAlias = (
    Resolvable[float] | PanelStatDerivedValue | ScenarioParameterDerivedValue
)


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
    unique_per_source_event: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.unique_per_source_event, bool):
            raise ValueError("unique_per_source_event must be boolean")


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
class GuaranteedCritEffect:
    """Guarantee a standard-crit event after its owning rule is matched."""

    rule: EffectRule
    result_kind: Literal["guaranteed-crit"] = field(
        default="guaranteed-crit",
        init=False,
    )


@dataclass(frozen=True, slots=True)
class UnresolvedEffect:
    rule: EffectRule
    unresolved: Unresolved
    result_kind: Literal["unresolved"] = field(default="unresolved", init=False)


Effect: TypeAlias = (
    ModifierEffect
    | StateChangeEffect
    | EventCreationEffect
    | GuaranteedCritEffect
    | UnresolvedEffect
)
