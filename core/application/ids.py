"""Stable identifiers owned by the application layer."""

from typing import NewType


RuleItemId = NewType("RuleItemId", str)
ScenarioConditionId = NewType("ScenarioConditionId", str)
MoveEntryId = NewType("MoveEntryId", str)
MultiplierVariantId = NewType("MultiplierVariantId", str)
DiagnosticId = NewType("DiagnosticId", str)
DamageEventSemanticId = NewType("DamageEventSemanticId", str)
