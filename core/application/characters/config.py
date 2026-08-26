"""Small configuration contracts shared by character compilers."""

from dataclasses import dataclass

from core.types import SkillGroup


@dataclass(frozen=True, slots=True)
class CharacterSkillLevel:
    skill_group: SkillGroup
    level: int

    def __post_init__(self) -> None:
        if self.level < 1:
            raise ValueError("skill level must be positive")
