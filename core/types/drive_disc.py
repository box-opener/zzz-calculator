"""Typed six-slot Drive Disc build inputs.

The UI may construct partial discs while the user is editing.  Completeness
is checked by the equipment compiler so partial input becomes a structured
diagnostic instead of a fabricated zero contribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum

from .common import CharacterId, DriveDiscSetId


class DriveDiscSlot(IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6


class DriveDiscStatKey(StrEnum):
    HP_FLAT = "hp-flat"
    ATTACK_FLAT = "attack-flat"
    DEFENSE_FLAT = "defense-flat"
    PENETRATION_FLAT = "penetration-flat"
    ANOMALY_PROFICIENCY_FLAT = "anomaly-proficiency-flat"
    CRIT_RATE = "crit-rate"
    CRIT_DAMAGE = "crit-damage"
    HP_PERCENT = "hp-percent"
    ATTACK_PERCENT = "attack-percent"
    DEFENSE_PERCENT = "defense-percent"
    IMPACT_PERCENT = "impact-percent"
    ANOMALY_MASTERY_PERCENT = "anomaly-mastery-percent"
    ENERGY_REGEN_PERCENT = "energy-regen-percent"
    PENETRATION_RATE = "penetration-rate"
    FIRE_DAMAGE_BONUS = "fire-damage-bonus"
    ICE_DAMAGE_BONUS = "ice-damage-bonus"
    WIND_DAMAGE_BONUS = "wind-damage-bonus"
    ELECTRIC_DAMAGE_BONUS = "electric-damage-bonus"
    PHYSICAL_DAMAGE_BONUS = "physical-damage-bonus"
    ETHER_DAMAGE_BONUS = "ether-damage-bonus"


@dataclass(frozen=True, slots=True)
class DriveDiscSubstatRoll:
    stat: DriveDiscStatKey
    roll_count: int

    def __post_init__(self) -> None:
        if self.stat not in DRIVE_DISC_SUBSTAT_VALUES:
            raise ValueError(f"unsupported Drive Disc substat: {self.stat.value}")
        if not 1 <= self.roll_count <= 6:
            raise ValueError("Drive Disc substat roll_count must be between 1 and 6")


@dataclass(frozen=True, slots=True)
class EquippedDriveDisc:
    slot: DriveDiscSlot
    set_id: DriveDiscSetId
    main_stat: DriveDiscStatKey | None
    substats: tuple[DriveDiscSubstatRoll, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.set_id):
            raise ValueError("Drive Disc set_id must not be empty")
        if (
            self.main_stat is not None
            and self.main_stat not in DRIVE_DISC_MAIN_STATS_BY_SLOT[self.slot]
        ):
            assert self.main_stat is not None
            raise ValueError(
                f"invalid main stat {self.main_stat.value} for slot {int(self.slot)}"
            )
        if len(self.substats) > 4:
            raise ValueError("a Drive Disc can have at most four substats")
        keys = tuple(item.stat for item in self.substats)
        if len(set(keys)) != len(keys):
            raise ValueError("Drive Disc substats must be unique")
        if self.main_stat is not None:
            if self.main_stat in keys:
                raise ValueError("Drive Disc main stat cannot also be a substat")

    @property
    def total_roll_count(self) -> int:
        return sum(item.roll_count for item in self.substats)

    @property
    def complete(self) -> bool:
        return (
            self.main_stat is not None
            and len(self.substats) == 4
            and self.total_roll_count in {8, 9}
        )


@dataclass(frozen=True, slots=True)
class DriveDiscBuildInput:
    equipped_character_id: CharacterId
    discs: tuple[EquippedDriveDisc, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.equipped_character_id):
            raise ValueError("Drive Disc owner is required")
        if len(self.discs) > 6:
            raise ValueError("a character can equip at most six Drive Discs")
        slots = tuple(item.slot for item in self.discs)
        if len(set(slots)) != len(slots):
            raise ValueError("Drive Disc slots must be unique")


DRIVE_DISC_MAIN_STATS_BY_SLOT: dict[DriveDiscSlot, frozenset[DriveDiscStatKey]] = {
    DriveDiscSlot.ONE: frozenset({DriveDiscStatKey.HP_FLAT}),
    DriveDiscSlot.TWO: frozenset({DriveDiscStatKey.ATTACK_FLAT}),
    DriveDiscSlot.THREE: frozenset({DriveDiscStatKey.DEFENSE_FLAT}),
    DriveDiscSlot.FOUR: frozenset(
        {
            DriveDiscStatKey.CRIT_RATE,
            DriveDiscStatKey.CRIT_DAMAGE,
            DriveDiscStatKey.ATTACK_PERCENT,
            DriveDiscStatKey.DEFENSE_PERCENT,
            DriveDiscStatKey.ANOMALY_PROFICIENCY_FLAT,
            DriveDiscStatKey.HP_PERCENT,
        }
    ),
    DriveDiscSlot.FIVE: frozenset(
        {
            DriveDiscStatKey.ATTACK_PERCENT,
            DriveDiscStatKey.DEFENSE_PERCENT,
            DriveDiscStatKey.HP_PERCENT,
            DriveDiscStatKey.FIRE_DAMAGE_BONUS,
            DriveDiscStatKey.ICE_DAMAGE_BONUS,
            DriveDiscStatKey.WIND_DAMAGE_BONUS,
            DriveDiscStatKey.ELECTRIC_DAMAGE_BONUS,
            DriveDiscStatKey.PHYSICAL_DAMAGE_BONUS,
            DriveDiscStatKey.ETHER_DAMAGE_BONUS,
            DriveDiscStatKey.PENETRATION_RATE,
        }
    ),
    DriveDiscSlot.SIX: frozenset(
        {
            DriveDiscStatKey.ENERGY_REGEN_PERCENT,
            DriveDiscStatKey.ATTACK_PERCENT,
            DriveDiscStatKey.DEFENSE_PERCENT,
            DriveDiscStatKey.HP_PERCENT,
            DriveDiscStatKey.ANOMALY_MASTERY_PERCENT,
            DriveDiscStatKey.IMPACT_PERCENT,
        }
    ),
}


DRIVE_DISC_MAIN_STAT_VALUES: dict[DriveDiscStatKey, float] = {
    DriveDiscStatKey.HP_FLAT: 2200.0,
    DriveDiscStatKey.ATTACK_FLAT: 316.0,
    DriveDiscStatKey.DEFENSE_FLAT: 184.0,
    DriveDiscStatKey.CRIT_RATE: 0.24,
    DriveDiscStatKey.CRIT_DAMAGE: 0.48,
    DriveDiscStatKey.ATTACK_PERCENT: 0.30,
    DriveDiscStatKey.DEFENSE_PERCENT: 0.48,
    DriveDiscStatKey.ANOMALY_PROFICIENCY_FLAT: 92.0,
    DriveDiscStatKey.HP_PERCENT: 0.30,
    DriveDiscStatKey.FIRE_DAMAGE_BONUS: 0.30,
    DriveDiscStatKey.ICE_DAMAGE_BONUS: 0.30,
    DriveDiscStatKey.WIND_DAMAGE_BONUS: 0.30,
    DriveDiscStatKey.ELECTRIC_DAMAGE_BONUS: 0.30,
    DriveDiscStatKey.PHYSICAL_DAMAGE_BONUS: 0.30,
    DriveDiscStatKey.ETHER_DAMAGE_BONUS: 0.30,
    DriveDiscStatKey.PENETRATION_RATE: 0.24,
    DriveDiscStatKey.ENERGY_REGEN_PERCENT: 0.60,
    DriveDiscStatKey.ANOMALY_MASTERY_PERCENT: 0.30,
    DriveDiscStatKey.IMPACT_PERCENT: 0.18,
}


DRIVE_DISC_SUBSTAT_VALUES: dict[DriveDiscStatKey, float] = {
    DriveDiscStatKey.ATTACK_FLAT: 19.0,
    DriveDiscStatKey.DEFENSE_FLAT: 15.0,
    DriveDiscStatKey.HP_FLAT: 112.0,
    DriveDiscStatKey.PENETRATION_FLAT: 9.0,
    DriveDiscStatKey.ANOMALY_PROFICIENCY_FLAT: 9.0,
    DriveDiscStatKey.CRIT_RATE: 0.024,
    DriveDiscStatKey.CRIT_DAMAGE: 0.048,
    DriveDiscStatKey.ATTACK_PERCENT: 0.03,
    DriveDiscStatKey.HP_PERCENT: 0.03,
    DriveDiscStatKey.DEFENSE_PERCENT: 0.048,
}


__all__ = [
    "DRIVE_DISC_MAIN_STATS_BY_SLOT",
    "DRIVE_DISC_MAIN_STAT_VALUES",
    "DRIVE_DISC_SUBSTAT_VALUES",
    "DriveDiscBuildInput",
    "DriveDiscSlot",
    "DriveDiscStatKey",
    "DriveDiscSubstatRoll",
    "EquippedDriveDisc",
]
