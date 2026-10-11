"""Compile-time configuration for Aria (character:1501)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


ARIA_ID = CharacterId("character:1501")


@dataclass(frozen=True, slots=True)
class AriaCompileConfig:
    character_id: CharacterId = ARIA_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False

    def __post_init__(self) -> None:
        if self.character_id != ARIA_ID:
            raise ValueError("AriaCompileConfig requires character:1501")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if not isinstance(self.additional_ability_eligible, bool):
            raise ValueError("additional_ability_eligible must be boolean")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill level must be between 1 and 16")
                return item.level
        return 12


__all__ = ["ARIA_ID", "AriaCompileConfig"]
