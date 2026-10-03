"""Compile-time settings for Dialyn (character:1481)."""

from dataclasses import dataclass

from core.types import CharacterId, CharacterRole, SkillGroup

from ..config import CharacterSkillLevel
from .reviewed import DIALYN_ID


@dataclass(frozen=True, slots=True)
class DialynCompileConfig:
    character_id: CharacterId = DIALYN_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 1
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    after_sound_eligible: bool = False
    previous_teammate_id: CharacterId | None = None
    previous_teammate_role: CharacterRole | None = None
    previous_teammate_order_known: bool = False

    def __post_init__(self) -> None:
        if self.character_id != DIALYN_ID:
            raise ValueError("DialynCompileConfig requires character:1481")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if (self.previous_teammate_id is None) != (self.previous_teammate_role is None):
            raise ValueError("previous teammate identity and role must be supplied together")
        if self.previous_teammate_id is not None and not self.previous_teammate_order_known:
            raise ValueError("previous teammate requires a known fixed formation order")
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


__all__ = ["DialynCompileConfig"]
