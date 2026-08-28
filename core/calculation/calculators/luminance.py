"""One luminance damage event calculated from one non-luminance record."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    CalculationContext,
    CalculationNode,
    LuminanceDamageEvent,
    NoCritRule,
    Resolved,
    Unresolved,
)

from ..regions import (
    BroadVulnerabilityRegionInput,
    DefenseRegionInput,
    LuminanceAnomalyDamageBonusRegionInput,
    ResistanceRegionInput,
    calculate_broad_vulnerability_region,
    calculate_defense_region,
    calculate_luminance_anomaly_damage_bonus_region,
    calculate_resistance_region,
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
    {CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS}
)


class LuminanceDamageCalculator:
    def calculate(self, context: CalculationContext) -> CalculationResult:
        event, record, damage_dealer = require_historical_context(
            context,
            LuminanceDamageEvent,
            "LuminanceDamageCalculator",
        )
        unresolved: list[Unresolved] = []
        if isinstance(event.crit_rule, Unresolved):
            unresolved.append(event.crit_rule)
        elif not isinstance(event.crit_rule, NoCritRule):
            raise InvalidCalculationContextError(
                "luminance damage must use NoCritRule"
            )

        effect_strength = resolved_number(
            record.weighted_anomaly_effect_strength,
            unresolved,
        )
        multiplier = fixed_multiplier(
            event.multiplier,
            "LuminanceDamageCalculator",
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
            "LuminanceDamageCalculator",
            unresolved,
        )
        required = (
            effect_strength,
            multiplier,
            penetration_rate,
            penetration_flat,
            initial_defense,
            damage_reduction,
            resistance_value,
        )
        if unresolved or any(value is None for value in required):
            return CalculationResult(None, (), tuple(unresolved))

        assert effect_strength is not None
        assert multiplier is not None
        assert penetration_rate is not None
        assert penetration_flat is not None
        assert initial_defense is not None
        assert damage_reduction is not None
        assert resistance_value is not None

        base_damage = effect_strength * multiplier
        luminance_bonus = calculate_luminance_anomaly_damage_bonus_region(
            LuminanceAnomalyDamageBonusRegionInput(
                modifiers[CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS]
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
        assert luminance_bonus.value is not None
        assert defense.value is not None
        assert resistance.value is not None
        assert vulnerability.value is not None
        final = (
            base_damage
            * luminance_bonus.value
            * defense.value
            * resistance.value
            * vulnerability.value
        )
        assert final is not None
        return CalculationResult(
            value=final,
            breakdown=(
                node_value(CalculationNode.ANOMALY_EFFECT_STRENGTH, effect_strength),
                node_value(CalculationNode.LUMINANCE_MULTIPLIER, multiplier),
                node_value(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
                *luminance_bonus.breakdown,
                *defense.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
        )
