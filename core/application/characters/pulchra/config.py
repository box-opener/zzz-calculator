"""Compile-time configuration for Pulchra (character:1351)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel


PULCHRA_ID = CharacterId("character:1351")


@dataclass(frozen=True, slots=True)
class PulchraCompileConfig:
    character_id: CharacterId = PULCHRA_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 6
    additional_ability_eligible: bool = False
    hunter_step_active: bool = False
    pursuit_mark_active: bool = False

    def __post_init__(self) -> None:
        if self.character_id != PULCHRA_ID:
            raise ValueError("PulchraCompileConfig requires character:1351")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        for name, value in (
            ("additional_ability_eligible", self.additional_ability_eligible),
            ("hunter_step_active", self.hunter_step_active),
            ("pursuit_mark_active", self.pursuit_mark_active),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be boolean")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        return 16


__all__ = ["PULCHRA_ID", "PulchraCompileConfig"]
