"""Application-facing calculation output and display modes."""

from dataclasses import dataclass
from enum import StrEnum
import math

from core.calculation import CalculationResult
from core.types import DamageSubtype, DamageType

from .diagnostics import CalculationDiagnostic
from .ids import DamageEventSemanticId, MoveEntryId


class CritDisplayMode(StrEnum):
    NON_CRIT = "non-crit"
    EXPECTED = "expected"
    FULL_CRIT = "full-crit"


class EventCalculationStatus(StrEnum):
    CALCULATED = "calculated"
    DATA_INSUFFICIENT = "data-insufficient"
    UNSUPPORTED_CALCULATOR = "unsupported-calculator"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class DamageEventCalculationOutput:
    """One event's unit calculation plus application-level repeat metadata."""

    semantic_id: DamageEventSemanticId
    label: str
    damage_type: DamageType
    damage_subtype: DamageSubtype | None
    status: EventCalculationStatus
    result: CalculationResult | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()
    repeat_count: int = 1

    def __post_init__(self) -> None:
        if not str(self.semantic_id) or not self.label.strip():
            raise ValueError("damage event output identity and label are required")
        if self.repeat_count < 0:
            raise ValueError("repeat_count must be non-negative")
        if self.status is EventCalculationStatus.CALCULATED:
            if self.result is None or self.result.value is None:
                raise ValueError("calculated events require a numeric result")
        elif self.result is not None and self.result.value is not None:
            raise ValueError(
                "non-calculated events cannot carry a formal numeric result"
            )

    @property
    def known_value(self) -> float | None:
        """Return the application-level value including an equivalent repeat count."""

        if self.result is None or self.result.value is None:
            return None
        return self.result.value * self.repeat_count


@dataclass(frozen=True, slots=True)
class MoveCalculationOutput:
    move_entry_id: MoveEntryId
    crit_display_mode: CritDisplayMode
    events: tuple[DamageEventCalculationOutput, ...]
    known_total: float | None
    complete: bool
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        event_ids = tuple(item.semantic_id for item in self.events)
        if len(set(event_ids)) != len(event_ids):
            raise ValueError("move output event semantic IDs must be unique")
        known_values = tuple(
            item.known_value for item in self.events if item.known_value is not None
        )
        if self.known_total is None and known_values:
            raise ValueError("known events require a known_total")
        if self.known_total is not None:
            if not known_values:
                raise ValueError("known_total requires at least one known event")
            if not math.isclose(
                self.known_total,
                sum(known_values),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise ValueError("known_total must equal the known event values")
        if self.complete:
            if self.known_total is None:
                raise ValueError("complete output requires a known_total")
            if any(
                item.status is not EventCalculationStatus.CALCULATED
                for item in self.events
            ):
                raise ValueError("complete output cannot contain incomplete events")
            if any(item.blocking for item in self.diagnostics):
                raise ValueError("complete output cannot contain blocking diagnostics")
        if self.known_total is None and self.complete:
            raise ValueError("complete output requires a formal total")
