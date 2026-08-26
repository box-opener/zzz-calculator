"""Diagnostics that distinguish blocked calculation from non-blocking notes."""

from dataclasses import dataclass
from enum import StrEnum

from .ids import DiagnosticId


class DiagnosticKind(StrEnum):
    MISSING_DATA = "missing-data"
    AMBIGUOUS_SEMANTICS = "ambiguous-semantics"
    DATA_QUALITY = "data-quality"
    UNSUPPORTED_CALCULATOR = "unsupported-calculator"


@dataclass(frozen=True, slots=True)
class CalculationDiagnostic:
    diagnostic_id: DiagnosticId
    kind: DiagnosticKind
    message: str
    blocking: bool
    original_text: str | None = None
    candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.diagnostic_id):
            raise ValueError("diagnostic_id must not be empty")
        if not self.message.strip():
            raise ValueError("diagnostic message must not be empty")
