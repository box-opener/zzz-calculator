"""Compile-time settings for Lucia (character:1451)."""

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel
from .reviewed import LUCIA_ID


@dataclass(frozen=True, slots=True)
class LuciaCompileConfig:
    character_id: CharacterId = LUCIA_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 1
    cinema_level: int = 0
    additional_ability_eligible: bool = False

    def __post_init__(self) -> None:
        if self.character_id != LUCIA_ID:
            raise ValueError("LuciaCompileConfig requires character:1451")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, skill_group: SkillGroup) -> int | None:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill level must be between 1 and 16")
                return item.level
        return None


__all__ = ["LuciaCompileConfig"]
