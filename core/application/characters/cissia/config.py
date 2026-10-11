"""Compile-time configuration for Cissia (character:1521)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel

CISSIA_ID = CharacterId("character:1521")


@dataclass(frozen=True, slots=True)
class CissiaCompileConfig:
    character_id: CharacterId = CISSIA_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    # Filled by team assembly from the active roster: another Stun or Electric agent.
    additional_ability_eligible: bool = False
    # Current poison, or its source-defined 30-second post-depletion state.
    toxin_active_or_recent: bool = False
    snake_shadow_available: bool = True
    # Static damage defaults to the source's maximum explicit extra-hit count;
    # callers can choose fewer hits without simulating energy consumption.
    ex_special_extra_hit_count: int = 3
    cinema4_awareness_stacks: int | None = None
    cinema6_mark_proc_active: bool = False

    def __post_init__(self) -> None:
        if self.character_id != CISSIA_ID:
            raise ValueError("CissiaCompileConfig requires character:1521")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        for name, value in (
            ("additional_ability_eligible", self.additional_ability_eligible),
            ("toxin_active_or_recent", self.toxin_active_or_recent),
            ("snake_shadow_available", self.snake_shadow_available),
            ("cinema6_mark_proc_active", self.cinema6_mark_proc_active),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be boolean")
        if (
            isinstance(self.ex_special_extra_hit_count, bool)
            or not isinstance(self.ex_special_extra_hit_count, int)
            or not 0 <= self.ex_special_extra_hit_count <= 3
        ):
            raise ValueError("EX extra-hit count must be an integer from 0 to 3")
        if self.cinema_level < 4:
            if self.cinema4_awareness_stacks not in (None, 0):
                raise ValueError("Cinema 4 awareness stacks require cinema_level >= 4")
            object.__setattr__(self, "cinema4_awareness_stacks", 0)
        else:
            stacks = (
                3
                if self.cinema4_awareness_stacks is None
                else self.cinema4_awareness_stacks
            )
            if (
                isinstance(stacks, bool)
                or not isinstance(stacks, int)
                or not 0 <= stacks <= 3
            ):
                raise ValueError("Cinema 4 awareness stacks must be an integer from 0 to 3")
            object.__setattr__(self, "cinema4_awareness_stacks", stacks)
        if self.cinema_level < 6 and self.cinema6_mark_proc_active:
            raise ValueError("Cinema 6 mark proc requires cinema_level 6")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per group")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        return 12


__all__ = ["CISSIA_ID", "CissiaCompileConfig"]
