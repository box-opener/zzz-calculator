"""Static calculation scenarios and user-selectable conditions."""

from dataclasses import dataclass
from enum import StrEnum

from core.types import CharacterId

from .ids import RuleItemId, ScenarioConditionId


class ConditionResolution(StrEnum):
    STATIC = "static"
    USER_SELECTED = "user-selected"


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
class CalculationScenario:
    scenario_id: str
    current_operator: CharacterId
    conditions: tuple[ScenarioCondition, ...] = ()
    enabled_rule_item_ids: frozenset[RuleItemId] = frozenset()

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        condition_ids = tuple(item.condition_id for item in self.conditions)
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("scenario condition IDs must be unique")
