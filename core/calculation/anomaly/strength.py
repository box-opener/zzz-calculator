"""Shared pure formulas for static anomaly record values."""

from __future__ import annotations


def anomaly_effect_strength(
    level: int,
    attack: float,
    anomaly_proficiency: float,
    element_damage_bonus: float,
    normal_damage_bonus: float = 0.0,
) -> float:
    """Return current anomaly effect strength from settlement values."""

    level_coefficient = 1.0 + (level - 1) / 59.0
    return (
        level_coefficient
        * (anomaly_proficiency / 100.0)
        * (1.0 + element_damage_bonus + normal_damage_bonus)
        * attack
    )


def anomaly_impact_strength(level: int, impact: float) -> float:
    """Return the spec-v1 weighted impact-strength coefficient."""

    return (1.0 + 0.45 * (level - 1) / 59.0) * impact


__all__ = ["anomaly_effect_strength", "anomaly_impact_strength"]
