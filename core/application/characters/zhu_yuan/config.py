"""Compile-time configuration for Zhu Yuan (character:1241)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


@dataclass(frozen=True, slots=True)
class ZhuYuanCompileConfig:
    character_id: CharacterId = CharacterId("character:1241")
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False

    def __post_init__(self) -> None:
        if self.character_id != CharacterId("character:1241"):
            raise ValueError("ZhuYuanCompileConfig requires character:1241")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        return 12


__all__ = ["ZhuYuanCompileConfig"]
