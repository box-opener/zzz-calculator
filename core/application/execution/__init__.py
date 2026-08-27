"""Application execution pipeline from compiled definitions to calculator output."""

from .contracts import (
    DamageEventExecutionTrace,
    InstantiatedDamageEvent,
    MoveCalculationExecution,
    MoveCalculationRequest,
)
from .event_factory import instantiate_direct_damage_event
from .modifiers import ModifierApplicationResult, apply_matched_modifiers
from .multiplier import (
    MultiplierResolutionStatus,
    MoveMultiplierResolution,
    resolve_move_multiplier,
)
from .router import CalculationRouter, CalculatorExecutionResult
from .service import DirectMoveApplicationService, calculate_move

__all__ = [
    "DamageEventExecutionTrace",
    "CalculationRouter",
    "CalculatorExecutionResult",
    "DirectMoveApplicationService",
    "MultiplierResolutionStatus",
    "MoveMultiplierResolution",
    "InstantiatedDamageEvent",
    "ModifierApplicationResult",
    "MoveCalculationExecution",
    "MoveCalculationRequest",
    "apply_matched_modifiers",
    "calculate_move",
    "instantiate_direct_damage_event",
    "resolve_move_multiplier",
]
