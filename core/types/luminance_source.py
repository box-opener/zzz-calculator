"""Typed snapshots for Remielle's virtual-void Luminance sources.

These are deliberately separate from ``AnomalyRecord``: the game source is a
stored special virtual void, not an ordinary Luminance attribute-anomaly
record.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .anomaly_record import AnomalyEffectStrengthTrace
from .common import (
    CharacterId,
    LuminanceSpecialSourceId,
    Ratio,
    Resolvable,
)
from .enums import Element


class LuminanceSourceKind(StrEnum):
    ORDINARY_ANOMALY = "ordinary-anomaly"
    SPECIAL_ENTRY = "special-entry"
    SPECIAL_REFILL = "special-refill"
    SPECIAL_BASIC4 = "special-basic4"


@dataclass(frozen=True, slots=True)
class LuminanceSourceChoice:
    """One explicitly selected current virtual-void source slot."""

    slot_id: str
    source_character_id: CharacterId
    kind: LuminanceSourceKind
    element: Element

    def __post_init__(self) -> None:
        if not self.slot_id.strip():
            raise ValueError("Luminance source slot ID must not be empty")
        if not str(self.source_character_id):
            raise ValueError("Luminance source character ID must not be empty")
        if not isinstance(self.kind, LuminanceSourceKind):
            raise ValueError("unknown Luminance source kind")
        if not isinstance(self.element, Element):
            raise ValueError("Luminance source element must be typed")


@dataclass(frozen=True, slots=True)
class LuminanceSpecialSourceSnapshot:
    """Strength and penetration captured when a special virtual void is made."""

    source_id: LuminanceSpecialSourceId
    slot_id: str
    source_character_id: CharacterId
    element: Element
    weighted_anomaly_effect_strength: Resolvable[float]
    penetration_rate: Resolvable[Ratio]
    penetration_flat: Resolvable[float]
    source_multiplier: Resolvable[Multiplier]
    source_kind: LuminanceSourceKind
    level: int
    anomaly_effect_strength_trace: AnomalyEffectStrengthTrace | None = None

    def __post_init__(self) -> None:
        if not str(self.source_id) or not self.slot_id.strip():
            raise ValueError("special virtual-void source identity is required")
        if not str(self.source_character_id):
            raise ValueError("special virtual-void source owner is required")
        if self.source_kind not in {
            LuminanceSourceKind.SPECIAL_ENTRY,
            LuminanceSourceKind.SPECIAL_REFILL,
            LuminanceSourceKind.SPECIAL_BASIC4,
        }:
            raise ValueError("special virtual-void snapshot requires a special source kind")
        if not 1 <= self.level <= 60:
            raise ValueError("special virtual-void source level must be between 1 and 60")


__all__ = [
    "LuminanceSourceChoice",
    "LuminanceSourceKind",
    "LuminanceSpecialSourceSnapshot",
]
