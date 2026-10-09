"""Compile-time configuration for Orphie & Magus (character:1301)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel
from .reviewed import ORPHIE_MAGUS_ID


@dataclass(frozen=True, slots=True)
class OrphieMagusCompileConfig:
    character_id: CharacterId = ORPHIE_MAGUS_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    focus_recipient_ids: tuple[CharacterId, ...] = (ORPHIE_MAGUS_ID,)

    def __post_init__(self) -> None:
        if self.character_id != ORPHIE_MAGUS_ID:
            raise ValueError("OrphieMagusCompileConfig requires character:1301")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if not isinstance(self.additional_ability_eligible, bool):
            raise ValueError("additional_ability_eligible must be boolean")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")
        if len(set(self.focus_recipient_ids)) != len(self.focus_recipient_ids):
            raise ValueError("Focus recipient IDs must be unique")
        if self.character_id not in self.focus_recipient_ids:
            raise ValueError("Orphie must be available as a Focus recipient")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        return 12


__all__ = ["OrphieMagusCompileConfig"]
