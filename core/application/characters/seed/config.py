"""Compile-time configuration for Seed (character:1461)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, SkillGroup

from ..config import CharacterSkillLevel

SEED_ID = CharacterId("character:1461")


@dataclass(frozen=True, slots=True)
class SeedCompileConfig:
    character_id: CharacterId = SEED_ID
    skill_levels: tuple[CharacterSkillLevel, ...] = ()
    core_level: int = 7
    cinema_level: int = 0
    additional_ability_eligible: bool = False
    # Filled by team assembly only after the highest Initial ATK other-Attack
    # teammate is uniquely resolved; it is not an arbitrary UI selection.
    partner_character_id: CharacterId | None = None
    partner_selection_unresolved: bool = False
    partner_candidate_ids: tuple[CharacterId, ...] = ()
    partner_ex_buff_active: bool = False
    seed_ex_buff_active: bool = False
    seed_surround_hunt_active: bool = False
    partner_surround_hunt_active: bool = False
    cinema2_energy_intervals_spent: int = 0
    cinema6_laser_proc_active: bool = False

    def __post_init__(self) -> None:
        if self.character_id != SEED_ID:
            raise ValueError("SeedCompileConfig requires character:1461")
        if not 1 <= self.core_level <= 7:
            raise ValueError("core_level must be between 1 and 7")
        if not 0 <= self.cinema_level <= 6:
            raise ValueError("cinema_level must be between 0 and 6")
        if self.partner_character_id is not None:
            partner_id = CharacterId(str(self.partner_character_id))
            if partner_id == SEED_ID:
                raise ValueError("Seed's Core partner must be another character")
            object.__setattr__(self, "partner_character_id", partner_id)
        candidates = tuple(CharacterId(str(item)) for item in self.partner_candidate_ids)
        if any(item == SEED_ID for item in candidates):
            raise ValueError("Seed's Core partner candidates must be other characters")
        if len(set(candidates)) != len(candidates):
            raise ValueError("Seed's Core partner candidates must be unique")
        object.__setattr__(self, "partner_candidate_ids", candidates)
        if self.partner_selection_unresolved and self.partner_character_id is not None:
            raise ValueError(
                "an unresolved partner selection cannot also name a partner"
            )
        if self.partner_selection_unresolved and len(candidates) < 2:
            raise ValueError(
                "an unresolved Seed partner selection requires multiple candidates"
            )
        if not self.partner_selection_unresolved and candidates:
            raise ValueError(
                "Seed partner candidates are only provided for unresolved selection"
            )
        if self.additional_ability_eligible and self.partner_character_id == SEED_ID:
            raise ValueError("Seed's Additional Ability requires another Attack agent")
        has_attack_partner = (
            self.partner_character_id is not None or self.partner_selection_unresolved
        )
        if not has_attack_partner and any(
            (
                self.partner_ex_buff_active,
                self.seed_ex_buff_active,
                self.seed_surround_hunt_active,
                self.partner_surround_hunt_active,
            )
        ):
            raise ValueError("Seed Core current states require another Attack teammate")
        if self.partner_character_id is None and any(
            (self.seed_ex_buff_active, self.partner_surround_hunt_active)
        ) and not self.partner_selection_unresolved:
            raise ValueError(
                "partner-owned Core states require a resolved partner character"
            )
        for value in (
            self.additional_ability_eligible,
            self.partner_selection_unresolved,
            self.partner_ex_buff_active,
            self.seed_ex_buff_active,
            self.seed_surround_hunt_active,
            self.partner_surround_hunt_active,
            self.cinema6_laser_proc_active,
        ):
            if not isinstance(value, bool):
                raise ValueError("Seed scenario options must be boolean")
        if (
            isinstance(self.cinema2_energy_intervals_spent, bool)
            or not isinstance(self.cinema2_energy_intervals_spent, int)
            or not 0 <= self.cinema2_energy_intervals_spent <= 24
        ):
            raise ValueError(
                "cinema2_energy_intervals_spent must be an integer from 0 to 24"
            )
        if self.cinema_level < 2 and self.cinema2_energy_intervals_spent:
            raise ValueError("Cinema 2 energy intervals require cinema_level >= 2")
        if self.cinema_level < 6 and self.cinema6_laser_proc_active:
            raise ValueError("Cinema 6 laser proc requires cinema_level 6")
        groups = tuple(item.skill_group for item in self.skill_levels)
        if len(set(groups)) != len(groups):
            raise ValueError("skill levels must be unique per skill group")

    def skill_level_for(self, skill_group: SkillGroup) -> int:
        for item in self.skill_levels:
            if item.skill_group is skill_group:
                if not 1 <= item.level <= 16:
                    raise ValueError("skill levels must be between 1 and 16")
                return item.level
        # Seed is S-rank. The repository's agreed panel contract defaults
        # every skill group to level 12, with C3/C5 boosts applied separately.
        return 12


__all__ = ["SEED_ID", "SeedCompileConfig"]
