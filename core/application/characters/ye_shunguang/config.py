"""Ye Shunguang-specific compiler inputs."""

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


@dataclass(frozen=True, slots=True)
class YeShunguangCompileConfig:
    character_id: CharacterId = CharacterId("character:1431")
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 1
    cinema_level: int = 0
    mingxin_active: bool = False
    entry_move_uses_linren: bool = False

    def __post_init__(self) -> None:
        if self.character_id != CharacterId("character:1431"):
            raise ValueError("YeShunguangCompileConfig requires character:1431")
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
                return item.level
        return None
