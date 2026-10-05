"""Compile-time inputs for Velina (character:1561)."""

from dataclasses import dataclass

from core.types import CharacterId, Element, SkillGroup

from ..config import CharacterSkillLevel


@dataclass(frozen=True, slots=True)
class VelinaCompileConfig:
    character_id: CharacterId = CharacterId("character:1561")
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    current_coloured_element: Element | None = None

    def __post_init__(self) -> None:
        if self.character_id != CharacterId("character:1561"):
            raise ValueError("VelinaCompileConfig requires character:1561")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if self.current_coloured_element not in {
            None,
            Element.PHYSICAL,
            Element.FIRE,
            Element.ELECTRIC,
            Element.ICE,
            Element.ETHER,
        }:
            raise ValueError("current_coloured_element must be a supported non-wind attribute")
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


__all__ = ["VelinaCompileConfig"]
