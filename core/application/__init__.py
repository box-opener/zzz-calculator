"""Application contracts between parsed rules, scenarios, and calculators."""

from .diagnostics import CalculationDiagnostic, DiagnosticKind
from .ids import (
    DiagnosticId,
    DamageEventSemanticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
)
from .moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from .output import (
    CritDisplayMode,
    DamageEventCalculationOutput,
    EventCalculationStatus,
    MoveCalculationOutput,
)
from .rules import CalculationRuleItem, RuleEligibility
from .scenario import (
    CalculationScenario,
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)

__all__ = [
    "CalculationDiagnostic",
    "CalculationRuleItem",
    "CalculationScenario",
    "ConditionResolution",
    "CritDisplayMode",
    "DamageEventCalculationOutput",
    "DamageEventTemplateRef",
    "DerivedDamageEventTemplateRef",
    "DiagnosticId",
    "DiagnosticKind",
    "EventCalculationStatus",
    "DamageEventSemanticId",
    "MoveCalculationEntry",
    "MoveCalculationOutput",
    "MoveEntryId",
    "MultiplierRelation",
    "MultiplierVariant",
    "MultiplierVariantId",
    "RuleEligibility",
    "RuleItemId",
    "ScenarioCondition",
    "ScenarioConditionId",
    "ScenarioIntegerParameter",
    "ScenarioParameterId",
    "ParameterResolution",
]
