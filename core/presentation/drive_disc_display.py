"""Shared display metadata for Drive Disc editor and Build Preview views."""

from __future__ import annotations

from core.types import DriveDiscStatKey


DRIVE_DISC_STAT_LABELS = {
    "hp-flat": "生命值",
    "attack-flat": "攻击力",
    "defense-flat": "防御力",
    "penetration-flat": "穿透值",
    "anomaly-proficiency-flat": "异常精通",
    "crit-rate": "暴击率",
    "crit-damage": "暴击伤害",
    "hp-percent": "生命值%",
    "attack-percent": "攻击力%",
    "defense-percent": "防御力%",
    "impact-percent": "冲击力%",
    "anomaly-mastery-percent": "异常掌控%",
    "energy-regen-percent": "能量自动回复%",
    "penetration-rate": "穿透率",
    "fire-damage-bonus": "火属性伤害",
    "ice-damage-bonus": "冰属性伤害",
    "wind-damage-bonus": "风属性伤害",
    "electric-damage-bonus": "电属性伤害",
    "physical-damage-bonus": "物理属性伤害",
    "ether-damage-bonus": "以太属性伤害",
}

_RATIO_STATS = frozenset(
    {
        DriveDiscStatKey.CRIT_RATE,
        DriveDiscStatKey.CRIT_DAMAGE,
        DriveDiscStatKey.HP_PERCENT,
        DriveDiscStatKey.ATTACK_PERCENT,
        DriveDiscStatKey.DEFENSE_PERCENT,
        DriveDiscStatKey.IMPACT_PERCENT,
        DriveDiscStatKey.ANOMALY_MASTERY_PERCENT,
        DriveDiscStatKey.ENERGY_REGEN_PERCENT,
        DriveDiscStatKey.PENETRATION_RATE,
        DriveDiscStatKey.FIRE_DAMAGE_BONUS,
        DriveDiscStatKey.ICE_DAMAGE_BONUS,
        DriveDiscStatKey.WIND_DAMAGE_BONUS,
        DriveDiscStatKey.ELECTRIC_DAMAGE_BONUS,
        DriveDiscStatKey.PHYSICAL_DAMAGE_BONUS,
        DriveDiscStatKey.ETHER_DAMAGE_BONUS,
    }
)


def drive_disc_stat_label(stat: DriveDiscStatKey) -> str:
    return DRIVE_DISC_STAT_LABELS[stat.value]


def display_drive_disc_value(stat: DriveDiscStatKey, value: float) -> str:
    return f"{value * 100:g}%" if stat in _RATIO_STATS else f"{value:g}"


__all__ = [
    "DRIVE_DISC_STAT_LABELS",
    "display_drive_disc_value",
    "drive_disc_stat_label",
]
