"""Route instantiated domain events to the available pure calculators."""

from __future__ import annotations

from dataclasses import dataclass

from core.calculation import CalculationResult
from core.calculation.calculators import DirectDamageCalculator
from core.types import CalculationContext, DamageEvent, DamageType, UnresolvedReason

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from ..output import EventCalculationStatus


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
        if event.damage_type is not DamageType.DIRECT:
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
        result = DirectDamageCalculator().calculate(context)
        if result.value is None:
            status = (
                EventCalculationStatus.DATA_INSUFFICIENT
                if result.unresolved
                and all(
                    item.reason is UnresolvedReason.MISSING_DATA
                    for item in result.unresolved
                )
                else EventCalculationStatus.UNSUPPORTED_CALCULATOR
            )
            diagnostics = tuple(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"application:calculator-unresolved:{index}"
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
                status=status,
                result=None,
                diagnostics=diagnostics,
            )
        return CalculatorExecutionResult(
            status=EventCalculationStatus.CALCULATED,
            result=result,
        )
