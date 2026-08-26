"""Static Effect matching contracts and evaluators."""

from .context import (
    CharacterMatchProfile,
    EffectMatchContext,
    EnemyMatchProfile,
    ScenarioTriggerFactView,
)
from .identity import DynamicIdentityResolver, IdentityResolution
from .matcher import EffectMatcher
from .result import EffectMatchResult, EffectMatchStatus, RuleItemMatchResult

__all__ = [
    "CharacterMatchProfile",
    "DynamicIdentityResolver",
    "EffectMatchContext",
    "EffectMatchResult",
    "EffectMatchStatus",
    "EffectMatcher",
    "EnemyMatchProfile",
    "IdentityResolution",
    "RuleItemMatchResult",
    "ScenarioTriggerFactView",
]
