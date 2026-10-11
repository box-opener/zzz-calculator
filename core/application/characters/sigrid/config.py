"""Compile-time configuration for Sigrid (character:1591)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


SIGRID_ID = CharacterId("character:1591")


@dataclass(frozen=True, slots=True)
class SigridCompileConfig:
    character_id: CharacterId = SIGRID_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    character_level: int = 60
    additional_ability_eligible: bool = False
    sky_rider_state_active: bool = False
    core_crit_buff_active: bool = False
    enemy_winded: bool = False
    chain_damage_buff_active: bool = False
    cinema4_damage_buff_active: bool = False
    cinema1_overflow_attack_active: bool = False

    def __post_init__(self) -> None:
        if self.character_id != SIGRID_ID:
            raise ValueError("SigridCompileConfig requires character:1591")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if not 1 <= self.character_level <= 60:
            raise ValueError("character_level must be between 1 and 60")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")
        for value in (
            self.additional_ability_eligible,
            self.sky_rider_state_active,
            self.core_crit_buff_active,
            self.enemy_winded,
            self.chain_damage_buff_active,
            self.cinema4_damage_buff_active,
            self.cinema1_overflow_attack_active,
        ):
            if not isinstance(value, bool):
                raise ValueError("Sigrid scenario options must be boolean")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill level must be between 1 and 16")
                return item.level
        return 12


__all__ = ["SIGRID_ID", "SigridCompileConfig"]
