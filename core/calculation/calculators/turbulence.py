"""Turbulence damage inherited from one non-wind anomaly record."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    AnomalyCritCapability,
    AnomalyRecordId,
    CalculationContext,
    CalculationNode,
    DamageSubtype,
    Element,
    IndependentAnomalyCrit,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolved,
    TurbulenceDamageEvent,
    Unresolved,
)

from ..regions import (
    BroadVulnerabilityRegionInput,
    DefenseRegionInput,
    ResistanceRegionInput,
    TurbulenceCritRegionInput,
    TurbulenceDamageBonusRegionInput,
    calculate_broad_vulnerability_region,
    calculate_defense_region,
    calculate_resistance_region,
    calculate_turbulence_crit_region,
    calculate_turbulence_damage_bonus_region,
)
from ..result import CalculationResult
from ._historical_anomaly import (
    COMMON_MODIFIER_PATHS,
    fixed_multiplier,
    modifier_totals,
    node_value,
    require_historical_context,
    resolved_number,
)
from .errors import InvalidCalculationContextError


_SUPPORTED_MODIFIER_PATHS = COMMON_MODIFIER_PATHS | frozenset(
    {CalculationNode.TURBULENCE_DAMAGE_BONUS}
)


def _crit_values(
    event: TurbulenceDamageEvent,
    record_capability: AnomalyCritCapability,
    record_id: AnomalyRecordId,
    unresolved: list[Unresolved],
) -> tuple[float | None, float | None]:
    rule = event.crit_rule
    if isinstance(rule, Unresolved):
        unresolved.append(rule)
        return None, None
    if isinstance(record_capability, Unresolved):
        unresolved.append(record_capability)
        return None, None
    inheritable = isinstance(record_capability, IndependentAnomalyCrit) and (
        DamageSubtype.TURBULENCE in record_capability.inherited_by
    )
    if isinstance(rule, NoCritRule):
        if inheritable:
            raise InvalidCalculationContextError(
                "NoCritRule contradicts turbulence-inheritable record capability"
            )
        return 0.0, 0.0
    if not isinstance(rule, RecordedAnomalyCritRule):
        raise InvalidCalculationContextError(
            "turbulence only supports recorded anomaly crit inheritance"
        )
    if rule.record_id != record_id:
        raise InvalidCalculationContextError(
            "turbulence crit rule record does not match anomaly history record"
        )
    if rule.capability != record_capability:
        raise InvalidCalculationContextError(
            "turbulence crit capability does not match anomaly history record"
        )
    if not inheritable:
        raise InvalidCalculationContextError(
            "record capability is not inheritable by turbulence damage"
        )
    assert isinstance(record_capability, IndependentAnomalyCrit)
    return (
        resolved_number(record_capability.crit_rate, unresolved),
        resolved_number(record_capability.crit_damage, unresolved),
    )


class TurbulenceDamageCalculator:
    def calculate(self, context: CalculationContext) -> CalculationResult:
        event, record, damage_dealer = require_historical_context(
            context,
            TurbulenceDamageEvent,
            "TurbulenceDamageCalculator",
        )
        if record.element is Element.WIND:
            raise InvalidCalculationContextError(
                "turbulence history record must be non-wind"
            )

        unresolved: list[Unresolved] = []
        effect_strength = resolved_number(
            record.weighted_anomaly_effect_strength,
            unresolved,
        )
        historical_anomaly_bonus = resolved_number(
            record.anomaly_damage_bonus_region,
            unresolved,
        )
        multiplier = fixed_multiplier(
            event.multiplier,
            "TurbulenceDamageCalculator",
            unresolved,
        )
        crit_rate, crit_damage = _crit_values(
            event,
            record.crit_capability,
            record.record_id,
            unresolved,
        )
        penetration_rate = resolved_number(
            damage_dealer.settlement_stats.penetration_rate,
            unresolved,
        )
        penetration_flat = resolved_number(
            damage_dealer.settlement_stats.penetration_flat,
            unresolved,
        )
        initial_defense = resolved_number(
            context.target_snapshot.initial_defense,
            unresolved,
        )
        damage_reduction = resolved_number(
            context.target_snapshot.damage_reduction,
            unresolved,
        )
        base_element = BASE_ELEMENT_BY_ELEMENT[event.metadata.element]
        resistance_value = resolved_number(
            context.target_snapshot.damage_resistance.get(
                base_element,
                Resolved(0.0),
            ),
            unresolved,
        )
        modifiers = modifier_totals(
            context,
            _SUPPORTED_MODIFIER_PATHS,
            "TurbulenceDamageCalculator",
            unresolved,
        )
        required = (
            effect_strength,
            historical_anomaly_bonus,
            multiplier,
            crit_rate,
            crit_damage,
            penetration_rate,
            penetration_flat,
            initial_defense,
            damage_reduction,
            resistance_value,
        )
        if unresolved or any(value is None for value in required):
            return CalculationResult(None, (), tuple(unresolved))

        assert effect_strength is not None
        assert historical_anomaly_bonus is not None
        assert multiplier is not None
        assert crit_rate is not None
        assert crit_damage is not None
        assert penetration_rate is not None
        assert penetration_flat is not None
        assert initial_defense is not None
        assert damage_reduction is not None
        assert resistance_value is not None

        base_damage = effect_strength * multiplier
        crit = calculate_turbulence_crit_region(
            TurbulenceCritRegionInput(crit_rate, crit_damage)
        )
        turbulence_bonus = calculate_turbulence_damage_bonus_region(
            TurbulenceDamageBonusRegionInput(
                modifiers[CalculationNode.TURBULENCE_DAMAGE_BONUS]
            )
        )
        defense = calculate_defense_region(
            DefenseRegionInput(
                damage_dealer.level,
                initial_defense,
                modifiers[CalculationNode.ENEMY_DEFENSE_INCREASE],
                modifiers[CalculationNode.ENEMY_DEFENSE_REDUCTION],
                modifiers[CalculationNode.DAMAGE_DEFENSE_IGNORE],
                penetration_rate
                + modifiers[CalculationNode.DAMAGE_PENETRATION_RATE],
                penetration_flat
                + modifiers[CalculationNode.DAMAGE_PENETRATION_FLAT],
            )
        )
        resistance = calculate_resistance_region(
            ResistanceRegionInput(
                resistance_value,
                modifiers[CalculationNode.DAMAGE_RESISTANCE_IGNORE],
                modifiers[CalculationNode.ENEMY_RESISTANCE_REDUCTION],
            )
        )
        vulnerability = calculate_broad_vulnerability_region(
            BroadVulnerabilityRegionInput(
                is_stunned=context.target_snapshot.is_stunned,
                stun_vulnerability=modifiers[CalculationNode.ENEMY_STUN_VULNERABILITY],
                normal_vulnerability=modifiers[CalculationNode.ENEMY_NORMAL_VULNERABILITY],
                move_vulnerability=modifiers[CalculationNode.ENEMY_MOVE_VULNERABILITY],
                damage_reduction=damage_reduction + modifiers[CalculationNode.ENEMY_DAMAGE_REDUCTION],
                settlement_policy=context.vulnerability_policy,
            )
        )
        assert crit.value is not None
        assert turbulence_bonus.value is not None
        assert defense.value is not None
        assert resistance.value is not None
        assert vulnerability.value is not None
        final = (
            base_damage
            * historical_anomaly_bonus
            * crit.value
            * turbulence_bonus.value
            * defense.value
            * resistance.value
            * vulnerability.value
        )
        assert final is not None
        return CalculationResult(
            value=final,
            breakdown=(
                node_value(CalculationNode.ANOMALY_EFFECT_STRENGTH, effect_strength),
                node_value(CalculationNode.TURBULENCE_TOTAL_MULTIPLIER, multiplier),
                node_value(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
                node_value(
                    CalculationNode.ANOMALY_DAMAGE_BONUS_REGION,
                    historical_anomaly_bonus,
                ),
                *crit.breakdown,
                *turbulence_bonus.breakdown,
                *defense.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
        )
