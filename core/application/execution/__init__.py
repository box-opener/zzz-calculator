"""Application execution pipeline from compiled definitions to calculator output."""

from .contracts import (
    DamageEventExecutionTrace,
    EventStatModifier,
    HistoryRecordMode,
    InstantiatedDamageEvent,
    MoveCalculationExecution,
    MoveCalculationRequest,
    PanelModifierExecutionTrace,
)
from .event_factory import instantiate_direct_damage_event
from .modifiers import (
    MatchedEffectApplication,
    ModifierApplicationResult,
    apply_global_panel_effects,
    apply_matched_modifiers,
)
from .multiplier import (
    MultiplierResolutionStatus,
    MoveMultiplierResolution,
    resolve_move_multiplier,
)
from .router import CalculationRouter, CalculatorExecutionResult
from .static_records import StaticAnomalyRecordAssembly, static_attribute_anomaly_record
from .service import DirectMoveApplicationService, calculate_move

__all__ = [
    "DamageEventExecutionTrace",
    "EventStatModifier",
    "HistoryRecordMode",
    "PanelModifierExecutionTrace",
    "CalculationRouter",
    "CalculatorExecutionResult",
    "DirectMoveApplicationService",
    "MultiplierResolutionStatus",
    "MoveMultiplierResolution",
    "InstantiatedDamageEvent",
    "ModifierApplicationResult",
    "MatchedEffectApplication",
    "MoveCalculationExecution",
    "MoveCalculationRequest",
    "apply_matched_modifiers",
    "apply_global_panel_effects",
    "calculate_move",
    "instantiate_direct_damage_event",
    "StaticAnomalyRecordAssembly",
    "static_attribute_anomaly_record",
    "resolve_move_multiplier",
]
