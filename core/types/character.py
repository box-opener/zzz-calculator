"""Character identity and panel layers; no panel calculation is performed here."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .common import CharacterId, Ratio, Resolvable
from .enums import CharacterRole, Element


@dataclass(frozen=True, slots=True)
class CharacterStats:
    hp: Resolvable[float]
    attack: Resolvable[float]
    defense: Resolvable[float]
    impact: Resolvable[float]
    crit_rate: Resolvable[Ratio]
    crit_damage: Resolvable[Ratio]
    anomaly_mastery: Resolvable[float]
    anomaly_proficiency: Resolvable[float]
    penetration_rate: Resolvable[Ratio]
    penetration_flat: Resolvable[float]
    energy_regen: Resolvable[float]
    element_damage_bonus: Mapping[Element, Resolvable[Ratio]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CharacterPanelLayers:
    """Values from distinct spec layers must never be silently substituted."""

    base: CharacterStats
    initial: CharacterStats


@dataclass(frozen=True, slots=True)
class Character:
    character_id: CharacterId
    name: str
    role: CharacterRole
    element: Element
    level: int
    panels: CharacterPanelLayers
    weapon_id: str | None = None
    drive_disc_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 60:
            raise ValueError("character level must be between 1 and 60")
        if len(self.drive_disc_ids) > 6:
            raise ValueError("a character can equip at most six drive discs")
