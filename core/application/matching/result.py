"""Three-valued matching results for application-layer Effects."""

from dataclasses import dataclass
from enum import StrEnum

from core.types import Effect, EffectId

from ..diagnostics import CalculationDiagnostic
from ..ids import RuleItemId


class EffectMatchStatus(StrEnum):
    MATCHED = "matched"
    NOT_MATCHED = "not-matched"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class EffectMatchResult:
    effect_id: EffectId
    status: EffectMatchStatus
    effect: Effect | None = None
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if self.status is EffectMatchStatus.MATCHED and self.effect is None:
            raise ValueError("matched effects require the matched Effect object")
        if self.status is not EffectMatchStatus.MATCHED and self.effect is not None:
            raise ValueError("unmatched effects cannot be returned as matched")


@dataclass(frozen=True, slots=True)
class RuleItemMatchResult:
    rule_id: RuleItemId
    status: EffectMatchStatus
    effects: tuple[EffectMatchResult, ...] = ()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    @property
    def matched_effects(self) -> tuple[Effect, ...]:
        return tuple(
            item.effect
            for item in self.effects
            if item.status is EffectMatchStatus.MATCHED and item.effect is not None
        )
