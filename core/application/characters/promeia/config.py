"""Compile-time configuration for Promeia (character:1541)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


PROMEIA_ID = CharacterId("character:1541")


@dataclass(frozen=True, slots=True)
class PromeiaCompileConfig:
    character_id: CharacterId = PROMEIA_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False

    def __post_init__(self) -> None:
        if self.character_id != PROMEIA_ID:
            raise ValueError("PromeiaCompileConfig requires character:1541")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if not isinstance(self.additional_ability_eligible, bool):
            raise ValueError("additional_ability_eligible must be boolean")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")
        if any(not 1 <= item.level <= 16 for item in self.skill_levels):
            raise ValueError("skill levels must be between 1 and 16")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                return item.level
        return 12


__all__ = ["PROMEIA_ID", "PromeiaCompileConfig"]
