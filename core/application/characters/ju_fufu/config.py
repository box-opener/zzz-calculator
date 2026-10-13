"""Compile-time configuration for Ju Fufu (character:1391)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


JU_FUFU_ID = CharacterId("character:1391")


@dataclass(frozen=True, slots=True)
class JuFufuCompileConfig:
    character_id: CharacterId = JU_FUFU_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    tiger_roar_active: bool = False
    c1_target_debuff_active: bool = False

    def __post_init__(self) -> None:
        if self.character_id != JU_FUFU_ID:
            raise ValueError("JuFufuCompileConfig requires character:1391")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if not isinstance(self.additional_ability_eligible, bool):
            raise ValueError("additional_ability_eligible must be boolean")
        if not isinstance(self.tiger_roar_active, bool):
            raise ValueError("tiger_roar_active must be boolean")
        if not isinstance(self.c1_target_debuff_active, bool):
            raise ValueError("c1_target_debuff_active must be boolean")
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


__all__ = ["JU_FUFU_ID", "JuFufuCompileConfig"]
