"""Serializable diagnostic views."""

from __future__ import annotations

from dataclasses import dataclass

from ..application.diagnostics import CalculationDiagnostic


_DETAILS_ONLY_NONBLOCKING_IDS = frozenset(
    {
        "unsupported:character:1331:core:prophecy-timing",
        "unsupported:character:1331:core:feather-resource-sequence",
        "wengine:wengine:14133:result-scope",
    }
)


@dataclass(frozen=True, slots=True)
class DiagnosticView:
    diagnostic_id: str
    kind: str
    message: str
    blocking: bool
    original_text: str | None = None
    candidates: tuple[str, ...] = ()
    details_only: bool = False

    def __post_init__(self) -> None:
        if (
            not self.blocking
            and self.diagnostic_id in _DETAILS_ONLY_NONBLOCKING_IDS
        ):
            object.__setattr__(self, "details_only", True)


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
