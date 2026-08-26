"""Static calculation scenarios and user-selectable conditions."""

from dataclasses import dataclass
from enum import StrEnum

from core.types import BattleEventKind, CharacterId, EffectId, MoveId

from .ids import (
    MultiplierVariantId,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
)


class ConditionResolution(StrEnum):
    STATIC = "static"
    USER_SELECTED = "user-selected"


class ParameterResolution(StrEnum):
    STATIC = "static"
    USER_SELECTED = "user-selected"


@dataclass(frozen=True, slots=True)
class ScenarioTriggerFact:
    effect_id: EffectId
    event_kind: BattleEventKind
    move_id: MoveId | None = None
    actor: CharacterId | None = None

    def __post_init__(self) -> None:
        if not str(self.effect_id):
            raise ValueError("trigger fact effect_id must not be empty")


@dataclass(frozen=True, slots=True)
class ScenarioCondition:
    condition_id: ScenarioConditionId
    label: str
    original_text: str
    resolution: ConditionResolution
    value: bool | None

    def __post_init__(self) -> None:
        if not str(self.condition_id):
            raise ValueError("condition_id must not be empty")
        if not self.label.strip():
            raise ValueError("condition label must not be empty")
        if self.resolution is ConditionResolution.STATIC and self.value is None:
            raise ValueError("static conditions must have a resolved value")


@dataclass(frozen=True, slots=True)
class ScenarioIntegerParameter:
    parameter_id: ScenarioParameterId
    label: str
    original_text: str
    resolution: ParameterResolution
    value: int | None
    minimum: int
    maximum: int | None

    def __post_init__(self) -> None:
        if not str(self.parameter_id):
            raise ValueError("parameter_id must not be empty")
        if not self.label.strip():
            raise ValueError("parameter label must not be empty")
        if self.minimum < 0:
            raise ValueError("parameter minimum must be non-negative")
        if self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("parameter bounds must be ordered")
        if self.resolution is ParameterResolution.STATIC and self.value is None:
            raise ValueError("static parameters must have a resolved value")
        if self.value is not None and (
            self.value < self.minimum
            or (self.maximum is not None and self.value > self.maximum)
        ):
            raise ValueError("parameter value must be within its legal bounds")


@dataclass(frozen=True, slots=True)
class CalculationScenario:
    scenario_id: str
    current_operator: CharacterId
    conditions: tuple[ScenarioCondition, ...] = ()
    parameters: tuple[ScenarioIntegerParameter, ...] = ()
    trigger_facts: tuple[ScenarioTriggerFact, ...] = ()
    selected_multiplier_variant_ids: frozenset[MultiplierVariantId] = frozenset()
    enabled_rule_item_ids: frozenset[RuleItemId] = frozenset()

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        condition_ids = tuple(item.condition_id for item in self.conditions)
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("scenario condition IDs must be unique")
        parameter_ids = tuple(item.parameter_id for item in self.parameters)
        if len(set(parameter_ids)) != len(parameter_ids):
            raise ValueError("scenario parameter IDs must be unique")
        trigger_effect_ids = tuple(item.effect_id for item in self.trigger_facts)
        if len(set(trigger_effect_ids)) != len(trigger_effect_ids):
            raise ValueError("scenario trigger facts must be unique per effect")
