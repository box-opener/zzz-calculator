"""Compile-time configuration for Yinhu (character:1421)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


YINHU_ID = CharacterId("character:1421")


@dataclass(frozen=True, slots=True)
class YinhuCompileConfig:
    character_id: CharacterId = YINHU_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 6
    additional_ability_eligible: bool = False
    penetration_recipient_ids: tuple[CharacterId, ...] = ()
    penetration_recipient_names: tuple[tuple[CharacterId, str], ...] = ()

    def __post_init__(self) -> None:
        if self.character_id != YINHU_ID:
            raise ValueError("YinhuCompileConfig requires character:1421")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")
        if len(set(self.penetration_recipient_ids)) != len(self.penetration_recipient_ids):
            raise ValueError("penetration recipient IDs must be unique")
        if self.character_id in self.penetration_recipient_ids:
            raise ValueError("Yinhu cannot be selected as a next-agent recipient")
        recipient_name_ids = tuple(item[0] for item in self.penetration_recipient_names)
        if len(set(recipient_name_ids)) != len(recipient_name_ids):
            raise ValueError("penetration recipient names must be unique per character")
        if any(recipient not in self.penetration_recipient_ids for recipient in recipient_name_ids):
            raise ValueError("penetration recipient names must refer to configured recipients")
        if any(not name.strip() for _, name in self.penetration_recipient_names):
            raise ValueError("penetration recipient names must not be empty")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        return 16


__all__ = ["YINHU_ID", "YinhuCompileConfig"]
