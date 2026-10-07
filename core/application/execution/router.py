"""Route instantiated domain events to the available pure calculators."""

from __future__ import annotations

from dataclasses import dataclass

from core.calculation import CalculationResult
from core.calculation.calculators import (
    AttributeAnomalyDamageCalculator,
    CurrentAttributeAnomalyDamageCalculator,
    DirectDamageCalculator,
    DischargeDamageCalculator,
    DisorderDamageCalculator,
    PolarDisorderDamageCalculator,
    LuminanceDamageCalculator,
    PenetrationDamageCalculator,
    SettledAnomalyDamageCalculator,
    TurbulenceDamageCalculator,
)
from core.types import (
    AttributeAnomalyDamageEvent,
    CurrentAttributeAnomalyDamageEvent,
    CalculationContext,
    DamageEvent,
    DamageType,
    DirectDamageEvent,
    DischargeDamageEvent,
    DisorderDamageEvent,
    PolarDisorderDamageEvent,
    LuminanceDamageEvent,
    SpecialLuminanceDamageEvent,
    PenetrationDamageEvent,
    SettledAnomalyDamageEvent,
    TurbulenceDamageEvent,
    UnresolvedReason,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..output import EventCalculationStatus
from core.calculation.calculators.errors import InvalidCalculationContextError


@dataclass(frozen=True, slots=True)
class CalculatorExecutionResult:
    status: EventCalculationStatus
    result: CalculationResult | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()


class CalculationRouter:
    """Small application router; calculator implementations stay pure."""

    def calculate(
        self,
        event: DamageEvent,
        context: CalculationContext,
    ) -> CalculatorExecutionResult:
        calculator = _calculator_for(event)
        if calculator is None:
            return CalculatorExecutionResult(
                status=EventCalculationStatus.UNSUPPORTED_CALCULATOR,
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(
                            f"application:unsupported-damage-type:{event.damage_type.value}"
                        ),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message=(
                            "no application calculator is registered for "
                            f"{event.damage_type.value}"
                        ),
                        blocking=True,
                    ),
                ),
            )
        try:
            result = calculator.calculate(context)
        except InvalidCalculationContextError as exc:
            # Calculators keep strict identity contracts for direct callers;
            # the application boundary turns a malformed static/request
            # record into a readable blocked result instead of leaking a
            # traceback through the HTTP presentation API.
            return CalculatorExecutionResult(
                status=EventCalculationStatus.BLOCKED,
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(
                            "application:calculator-context-mismatch:"
                            f"{getattr(event, 'history_record_source', event.metadata.event_id)}"
                        ),
                        kind=DiagnosticKind.DATA_QUALITY,
                        message=str(exc),
                        blocking=True,
                    ),
                ),
            )
        if result.value is None:
            semantic_ambiguities = {
                UnresolvedReason.AMBIGUOUS_TEXT,
                UnresolvedReason.AMBIGUOUS_IDENTITY,
                UnresolvedReason.AMBIGUOUS_ORDERING,
            }
            if result.unresolved and all(
                item.reason is UnresolvedReason.MISSING_DATA
                for item in result.unresolved
            ):
                status = EventCalculationStatus.DATA_INSUFFICIENT
            elif any(
                item.reason in semantic_ambiguities
                for item in result.unresolved
            ):
                status = EventCalculationStatus.BLOCKED
            else:
                status = EventCalculationStatus.UNSUPPORTED_CALCULATOR
            diagnostics = tuple(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:calculator-unresolved:{index}"
                    ),
                    kind=(
                        DiagnosticKind.MISSING_DATA
                        if item.reason is UnresolvedReason.MISSING_DATA
                        else DiagnosticKind.AMBIGUOUS_SEMANTICS
                        if item.reason in semantic_ambiguities
                        else DiagnosticKind.UNSUPPORTED_CALCULATOR
                    ),
                    message=item.notes,
                    blocking=True,
                    original_text=item.original_text,
                )
                for index, item in enumerate(result.unresolved)
            )
            return CalculatorExecutionResult(
                status=status,
                result=None,
                diagnostics=diagnostics,
            )
        diagnostics = ()
        if isinstance(event, PolarDisorderDamageEvent) and result.unresolved:
            diagnostics = tuple(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:polar-disorder-partial:{index}"
                    ),
                    kind=(
                        DiagnosticKind.MISSING_DATA
                        if item.reason is UnresolvedReason.MISSING_DATA
                        else DiagnosticKind.UNSUPPORTED_CALCULATOR
                    ),
                    message=item.notes,
                    blocking=True,
                    original_text=item.original_text,
                )
                for index, item in enumerate(result.unresolved)
            )
        return CalculatorExecutionResult(
            status=EventCalculationStatus.CALCULATED,
            result=result,
            diagnostics=diagnostics,
        )


def _calculator_for(event: DamageEvent):
    """Map typed events to calculators without using character IDs."""

    if isinstance(event, DirectDamageEvent):
        return DirectDamageCalculator()
    if isinstance(event, SettledAnomalyDamageEvent):
        return SettledAnomalyDamageCalculator()
    if isinstance(event, CurrentAttributeAnomalyDamageEvent):
        return CurrentAttributeAnomalyDamageCalculator()
    if isinstance(event, AttributeAnomalyDamageEvent):
        return AttributeAnomalyDamageCalculator()
    if isinstance(event, DischargeDamageEvent):
        return DischargeDamageCalculator()
    if isinstance(event, DisorderDamageEvent):
        return DisorderDamageCalculator()
    if isinstance(event, PolarDisorderDamageEvent):
        return PolarDisorderDamageCalculator()
    if isinstance(event, TurbulenceDamageEvent):
        return TurbulenceDamageCalculator()
    if isinstance(event, (LuminanceDamageEvent, SpecialLuminanceDamageEvent)):
        return LuminanceDamageCalculator()
    if isinstance(event, PenetrationDamageEvent):
        return PenetrationDamageCalculator()
    return None
