"""Compile-time configuration for Remielle (character:1581)."""

from dataclasses import dataclass

from core.types import CharacterId, Element, SkillGroup

from ..config import CharacterSkillLevel


@dataclass(frozen=True, slots=True)
class RemielleCompileConfig:
    character_id: CharacterId = CharacterId("character:1581")
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    anomaly_team_count: int = 1
    damage_element: Element = Element.LUMINANCE
    damage_element_known: bool = True

    def __post_init__(self) -> None:
        if self.character_id != CharacterId("character:1581"):
            raise ValueError("RemielleCompileConfig requires character:1581")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if not 1 <= self.anomaly_team_count <= 3:
            raise ValueError("anomaly_team_count must be between 1 and 3")
        if not isinstance(self.damage_element, Element):
            raise ValueError("damage_element must be a known Element")
        if not isinstance(self.damage_element_known, bool):
            raise ValueError("damage_element_known must be boolean")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, skill_group: SkillGroup) -> int | None:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill level must be between 1 and 16")
                return item.level
        return 12


__all__ = ["RemielleCompileConfig"]
