"""Calculation-rule items exposed by the application layer."""

from dataclasses import dataclass
from enum import StrEnum

from core.types import CharacterId, Effect, RuleSource

from .diagnostics import CalculationDiagnostic
from .ids import RuleItemId
from .ids import ScenarioConditionId


class RuleEligibility(StrEnum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    SCENARIO_REQUIRED = "scenario-required"


@dataclass(frozen=True, slots=True)
class CalculationRuleItem:
    rule_id: RuleItemId
    owner: CharacterId | None
    source: RuleSource
    display_name: str
    original_text: str
    eligibility: RuleEligibility
    condition_ids: tuple[ScenarioConditionId, ...] = ()
    effects: tuple[Effect, ...] = ()
    stack_count: int | None = None
    stack_min: int | None = None
    stack_max: int | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()
    non_stacking_group_id: str | None = None

    def __post_init__(self) -> None:
        if not str(self.rule_id):
            raise ValueError("rule_id must not be empty")
        if not self.display_name.strip():
            raise ValueError("rule display_name must not be empty")
        if (
            self.non_stacking_group_id is not None
            and not self.non_stacking_group_id.strip()
        ):
            raise ValueError("non-stacking group ID must not be empty")
        condition_ids = tuple(self.condition_ids)
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("rule condition IDs must be unique")
        if self.eligibility is RuleEligibility.SCENARIO_REQUIRED and not condition_ids:
            raise ValueError(
                "scenario-required rules must reference at least one condition"
            )
        stack_fields = (self.stack_count, self.stack_min, self.stack_max)
        if self.stack_count is None:
            if self.stack_min is not None or self.stack_max is not None:
                raise ValueError("stack bounds require stack_count")
        else:
            if self.stack_min is None or self.stack_max is None:
                raise ValueError("stacked rules require both stack bounds")
            if self.stack_min < 0 or self.stack_max < self.stack_min:
                raise ValueError("stack bounds must be ordered and non-negative")
            if not self.stack_min <= self.stack_count <= self.stack_max:
                raise ValueError("stack_count must be within its legal bounds")

        if self.stack_count is None and any(item is not None for item in stack_fields):
            raise ValueError("non-stacked rules cannot define stack metadata")
