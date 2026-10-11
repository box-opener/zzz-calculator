"""Compile-time settings for Sunna (character:1491)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, CharacterRole, Element, SkillGroup

from ..config import CharacterSkillLevel

SUNNA_ID = CharacterId("character:1491")


@dataclass(frozen=True, slots=True)
class SunnaCatGazeTriggerer:
    """A teammate whose actual role and native element came from team assembly."""

    character_id: CharacterId
    role: CharacterRole
    element: Element

    def __post_init__(self) -> None:
        if not str(self.character_id):
            raise ValueError("Cat's Gaze triggerer requires a character ID")
        object.__setattr__(self, "character_id", CharacterId(str(self.character_id)))
        if self.role not in {CharacterRole.ATTACK, CharacterRole.ANOMALY}:
            raise ValueError("Cat's Gaze only accepts Attack or Anomaly triggerers")


@dataclass(frozen=True, slots=True)
class SunnaCompileConfig:
    character_id: CharacterId = SUNNA_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    cat_gaze_triggerers: tuple[SunnaCatGazeTriggerer, ...] = ()
    cat_gaze_target_mark_active: bool = False
    bad_cat_active: bool = False
    angel_chorus_active: bool = False
    ether_veil_active: bool = False
    sunna_ether_veil_active: bool = False
    extra_stun_vulnerability_active: bool = False
    cooperative_photo_extra: int = 0
    cinema4_team_damage_active: bool = False
    cinema6_creating_active: bool = False
    cinema1_defense_reduction_stacks: int = 3

    def __post_init__(self) -> None:
        object.__setattr__(self, "character_id", CharacterId(str(self.character_id)))
        if self.character_id != SUNNA_ID:
            raise ValueError("SunnaCompileConfig requires character:1491")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if self.cinema6_creating_active and self.cinema_level < 6:
            raise ValueError("Cinema 6 creating state requires cinema_level 6")
        triggerers = tuple(self.cat_gaze_triggerers)
        object.__setattr__(self, "cat_gaze_triggerers", triggerers)
        triggerer_ids = tuple(item.character_id for item in triggerers)
        if len(set(triggerer_ids)) != len(triggerer_ids):
            raise ValueError("Cat's Gaze triggerer IDs must be unique")
        for triggerer in self.cat_gaze_triggerers:
            if triggerer.character_id == SUNNA_ID:
                if self.cinema_level < 6 or triggerer.role is not CharacterRole.ATTACK:
                    raise ValueError("Sunna is an Attack Cat's Gaze triggerer only at Cinema 6")
        if self.cinema4_team_damage_active and self.cinema_level < 4:
            raise ValueError("Cinema 4 current damage state requires cinema_level 4")
        if self.extra_stun_vulnerability_active and not self.additional_ability_eligible:
            raise ValueError("Sunna's extra-ability stun vulnerability requires eligibility")
        if (
            isinstance(self.cooperative_photo_extra, bool)
            or not isinstance(self.cooperative_photo_extra, int)
            or self.cooperative_photo_extra not in (0, 1)
        ):
            raise ValueError("cooperative_photo_extra must be 0 or 1")
        if self.cooperative_photo_extra and not self.angel_chorus_active:
            raise ValueError("the coordinated Photo Technique requires Angel Chorus")
        if not 0 <= self.cinema1_defense_reduction_stacks <= 3:
            raise ValueError("Cinema 1 defense-reduction stacks must be from 0 to 3")
        for value in (
            self.additional_ability_eligible,
            self.cat_gaze_target_mark_active,
            self.bad_cat_active,
            self.angel_chorus_active,
            self.ether_veil_active,
            self.sunna_ether_veil_active,
            self.extra_stun_vulnerability_active,
            self.cinema4_team_damage_active,
            self.cinema6_creating_active,
        ):
            if not isinstance(value, bool):
                raise ValueError("Sunna scenario options must be boolean")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        # Sunna is S-rank; the reviewed default is level 12 for every group.
        return 12


__all__ = ["SUNNA_ID", "SunnaCatGazeTriggerer", "SunnaCompileConfig"]
