"""Serializable diagnostic views."""

from __future__ import annotations

from dataclasses import dataclass

from ..application.diagnostics import CalculationDiagnostic


@dataclass(frozen=True, slots=True)
class DiagnosticView:
    diagnostic_id: str
    kind: str
    message: str
    blocking: bool
    original_text: str | None = None
    candidates: tuple[str, ...] = ()


def diagnostic_view(diagnostic: CalculationDiagnostic) -> DiagnosticView:
    return DiagnosticView(
        diagnostic_id=str(diagnostic.diagnostic_id),
        kind=diagnostic.kind.value,
        message=diagnostic.message,
        blocking=diagnostic.blocking,
        original_text=diagnostic.original_text,
        candidates=diagnostic.candidates,
    )


__all__ = ["DiagnosticView", "diagnostic_view"]
