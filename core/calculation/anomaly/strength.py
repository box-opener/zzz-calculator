"""Shared pure formulas for static anomaly record values."""

from __future__ import annotations

from collections.abc import Sequence

from core.types import (
    AnomalyEffectStrengthTrace,
    AnomalyStrengthFactor,
    CharacterId,
    Element,
)


def _strength_components(
    level: int,
    attack: float,
    anomaly_proficiency: float,
    element_damage_bonus: float,
    normal_damage_bonus: float,
    mutation: float = 1.0,
) -> tuple[float, float, float, float, float, float]:
    level_coefficient = 1.0 + (level - 1) / 59.0
    anomaly_proficiency_factor = anomaly_proficiency / 100.0
    normal_region = 1.0 + element_damage_bonus + normal_damage_bonus
    final = (
        level_coefficient
        * anomaly_proficiency_factor
        * normal_region
        * attack
        * mutation
    )
    return (
        level_coefficient,
        anomaly_proficiency_factor,
        normal_region,
        mutation,
        final,
        anomaly_proficiency,
    )


def anomaly_effect_strength(
    level: int,
    attack: float,
    anomaly_proficiency: float,
    element_damage_bonus: float,
    normal_damage_bonus: float = 0.0,
    mutation: float = 1.0,
) -> float:
    """Return current anomaly effect strength from settlement values."""

    return _strength_components(
        level,
        attack,
        anomaly_proficiency,
        element_damage_bonus,
        normal_damage_bonus,
        mutation,
    )[4]


def anomaly_effect_strength_with_trace(
    *,
    character_id: CharacterId,
    level: int,
    attack: float,
    anomaly_proficiency: float,
    element_damage_bonus: float,
    normal_damage_bonus: float = 0.0,
    mutation: float = 1.0,
    element: Element | None = None,
    normal_factors: Sequence[AnomalyStrengthFactor] = (),
    mutation_factors: Sequence[AnomalyStrengthFactor] = (),
    unresolved: str | None = None,
) -> tuple[float, AnomalyEffectStrengthTrace]:
    """Evaluate the shared formula and retain its concrete source values.

    Callers use this only at the same point where the anomaly strength is
    generated.  Historical settlement then carries the returned trace along
    with the weighted numeric value.
    """

    (
        level_coefficient,
        anomaly_proficiency_factor,
        _normal_region,
        mutation_value,
        final_strength,
        _proficiency,
    ) = _strength_components(
        level,
        attack,
        anomaly_proficiency,
        element_damage_bonus,
        normal_damage_bonus,
        mutation,
    )
    factors = (
        AnomalyStrengthFactor(
            factor="level-coefficient",
            value=level_coefficient,
            source_label="角色等级系数",
            owner_character_id=character_id,
        ),
        AnomalyStrengthFactor(
            factor="anomaly-proficiency",
            value=anomaly_proficiency,
            source_label="有效异常精通",
            owner_character_id=character_id,
        ),
        AnomalyStrengthFactor(
            factor="element-bonus",
            value=element_damage_bonus,
            source_label="对应属性增伤",
            owner_character_id=character_id,
        ),
        *normal_factors,
        *mutation_factors,
        AnomalyStrengthFactor(
            factor="mutation",
            value=mutation_value,
            source_label="异化系数（当前实现）",
            owner_character_id=character_id,
        ),
    )
    trace = AnomalyEffectStrengthTrace(
        character_id=character_id,
        level=level,
        level_coefficient=level_coefficient,
        anomaly_proficiency=anomaly_proficiency,
        anomaly_proficiency_factor=anomaly_proficiency_factor,
        attack=attack,
        element_bonus=element_damage_bonus,
        normal_bonus=normal_damage_bonus,
        mutation=mutation_value,
        final_strength=final_strength,
        element=element,
        factors=tuple(factors),
        unresolved=unresolved,
    )
    return final_strength, trace


def anomaly_impact_strength(level: int, impact: float) -> float:
    """Return the spec-v1 weighted impact-strength coefficient."""

    return (1.0 + 0.45 * (level - 1) / 59.0) * impact


__all__ = [
    "anomaly_effect_strength",
    "anomaly_effect_strength_with_trace",
    "anomaly_impact_strength",
]
