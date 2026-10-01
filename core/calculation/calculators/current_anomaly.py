"""Attribute-anomaly calculation from a current character panel."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    CalculationContext,
    CalculationNode,
    CurrentAttributeAnomalyDamageEvent,
    EffectOperation,
    FixedMultiplier,
    NoCritRule,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
from ..anomaly import anomaly_effect_strength_with_trace
from ..regions import (
    AnomalyCritRegionInput,
    BroadVulnerabilityRegionInput,
    DefenseRegionInput,
    ResistanceRegionInput,
    calculate_anomaly_crit_region,
    calculate_broad_vulnerability_region,
    calculate_defense_region,
    calculate_resistance_region,
)
from ..result import CalculationResult
from .errors import InvalidCalculationContextError


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(node, Resolved(value), SnapshotRule.SETTLEMENT)


def _number(value, unresolved: list[Unresolved]) -> float | None:
    if isinstance(value, Resolved):
        return float(value.value)
    unresolved.append(value)
    return None


def _modifier_totals(context: CalculationContext, unresolved: list[Unresolved]):
    supported = {
        CalculationNode.DAMAGE_NORMAL_BONUS,
        CalculationNode.ANOMALY_DAMAGE_BONUS,
        CalculationNode.ENEMY_DEFENSE_INCREASE,
        CalculationNode.ENEMY_DEFENSE_REDUCTION,
        CalculationNode.DAMAGE_DEFENSE_IGNORE,
        CalculationNode.DAMAGE_PENETRATION_RATE,
        CalculationNode.DAMAGE_PENETRATION_FLAT,
        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
        CalculationNode.ENEMY_STUN_VULNERABILITY,
        CalculationNode.ENEMY_NORMAL_VULNERABILITY,
        CalculationNode.ENEMY_MOVE_VULNERABILITY,
        CalculationNode.ENEMY_DAMAGE_REDUCTION,
    }
    totals = {node: 0.0 for node in supported}
    for modifier in context.modifiers:
        if modifier.modifier_path not in supported:
            continue
        if modifier.operation is not EffectOperation.ADD:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        "CurrentAttributeAnomalyDamageCalculator only supports "
                        f"ADD for {modifier.modifier_path.value}"
                    ),
                )
            )
            continue
        value = _number(modifier.value, unresolved)
        if value is not None:
            totals[modifier.modifier_path] += value
    return totals


class CurrentAttributeAnomalyDamageCalculator:
    """Calculate one physical anomaly from current attack/mastery values."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, CurrentAttributeAnomalyDamageEvent):
            raise InvalidCalculationContextError(
                "CurrentAttributeAnomalyDamageCalculator only accepts "
                "CurrentAttributeAnomalyDamageEvent"
            )
        if context.battle_state_id != event.metadata.battle_state_id:
            raise InvalidCalculationContextError(
                "CalculationContext battle_state_id does not match DamageEvent"
            )
        if context.target_snapshot.enemy_id != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "target snapshot does not match DamageEvent target"
            )
        snapshots = {
            item.character_id: item for item in context.character_snapshots
        }
        dealer = snapshots.get(event.metadata.damage_dealer)
        if dealer is None:
            raise InvalidCalculationContextError(
                f"missing damage dealer character snapshot: {event.metadata.damage_dealer}"
            )
        if event.anomaly_triggerer != event.metadata.damage_dealer:
            raise InvalidCalculationContextError(
                "current anomaly event triggerer must match its damage dealer"
            )
        if (
            event.base_settlement_data_source.character_id
            != event.metadata.damage_dealer
        ):
            raise InvalidCalculationContextError(
                "current anomaly value source must match its damage dealer"
            )
        unresolved: list[Unresolved] = []
        attack = _number(dealer.settlement_stats.attack, unresolved)
        proficiency = _number(
            dealer.settlement_stats.anomaly_proficiency,
            unresolved,
        )
        penetration_rate = _number(dealer.settlement_stats.penetration_rate, unresolved)
        penetration_flat = _number(dealer.settlement_stats.penetration_flat, unresolved)
        initial_defense = _number(context.target_snapshot.initial_defense, unresolved)
        damage_reduction = _number(context.target_snapshot.damage_reduction, unresolved)
        base_element = BASE_ELEMENT_BY_ELEMENT[event.metadata.element]
        resistance = _number(
            context.target_snapshot.damage_resistance.get(base_element, Resolved(0.0)),
            unresolved,
        )
        element_bonus = _number(
            dealer.settlement_stats.element_damage_bonus.get(base_element, Resolved(0.0)),
            unresolved,
        )
        modifiers = _modifier_totals(context, unresolved)
        mutation, mutation_factors = _mutation_coefficient(context, unresolved)
        if isinstance(event.multiplier, FixedMultiplier):
            anomaly_multiplier = _number(event.multiplier.value, unresolved)
        else:
            anomaly_multiplier = None
            unresolved.append(
                event.multiplier
                if isinstance(event.multiplier, Unresolved)
                else Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes="current anomaly event requires FixedMultiplier",
                )
            )
        if not isinstance(event.crit_rule, NoCritRule):
            unresolved.append(
                event.crit_rule
                if isinstance(event.crit_rule, Unresolved)
                else Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes="current Alice polar strong attack uses NoCritRule",
                )
            )
        required = (
            attack,
            proficiency,
            penetration_rate,
            penetration_flat,
            initial_defense,
            damage_reduction,
            resistance,
            element_bonus,
            anomaly_multiplier,
        )
        if unresolved or any(value is None for value in required):
            return CalculationResult(value=None, breakdown=(), unresolved=tuple(unresolved))
        assert attack is not None and proficiency is not None
        assert penetration_rate is not None and penetration_flat is not None
        assert initial_defense is not None and damage_reduction is not None
        assert resistance is not None and element_bonus is not None
        assert anomaly_multiplier is not None
        level_coefficient = 1.0 + (dealer.level - 1) / 59.0
        effect_strength, effect_trace = anomaly_effect_strength_with_trace(
            character_id=event.anomaly_triggerer,
            level=dealer.level,
            attack=attack,
            anomaly_proficiency=proficiency,
            element_damage_bonus=element_bonus,
            normal_damage_bonus=modifiers[CalculationNode.DAMAGE_NORMAL_BONUS],
            mutation=mutation,
            element=event.metadata.element,
            normal_factors=tuple(
                # The application presentation layer resolves these effect IDs
                # to human-readable labels; the calculation remains independent
                # of that layer while retaining every actual modifier value.
                _strength_factor(modifier)
                for modifier in context.modifiers
                if modifier.modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
            ),
            mutation_factors=mutation_factors,
        )
        anomaly_bonus = 1.0 + modifiers[CalculationNode.ANOMALY_DAMAGE_BONUS]
        anomaly_crit = calculate_anomaly_crit_region(
            AnomalyCritRegionInput(crit_rate=0.0, crit_damage=0.0)
        )
        defense = calculate_defense_region(
            DefenseRegionInput(
                attacker_level=dealer.level,
                initial_defense=initial_defense,
                defense_increase=modifiers[CalculationNode.ENEMY_DEFENSE_INCREASE],
                defense_reduction=modifiers[CalculationNode.ENEMY_DEFENSE_REDUCTION],
                defense_ignore=modifiers[CalculationNode.DAMAGE_DEFENSE_IGNORE],
                penetration_rate=penetration_rate
                + modifiers[CalculationNode.DAMAGE_PENETRATION_RATE],
                penetration_flat=penetration_flat
                + modifiers[CalculationNode.DAMAGE_PENETRATION_FLAT],
            )
        )
        resistance_region = calculate_resistance_region(
            ResistanceRegionInput(
                base_resistance=resistance,
                resistance_ignore=modifiers[CalculationNode.DAMAGE_RESISTANCE_IGNORE],
                resistance_reduction=modifiers[CalculationNode.ENEMY_RESISTANCE_REDUCTION],
            )
        )
        vulnerability = calculate_broad_vulnerability_region(
            BroadVulnerabilityRegionInput(
                is_stunned=context.target_snapshot.is_stunned,
                stun_vulnerability=modifiers[CalculationNode.ENEMY_STUN_VULNERABILITY],
                normal_vulnerability=modifiers[CalculationNode.ENEMY_NORMAL_VULNERABILITY],
                move_vulnerability=modifiers[CalculationNode.ENEMY_MOVE_VULNERABILITY],
                damage_reduction=damage_reduction
                + modifiers[CalculationNode.ENEMY_DAMAGE_REDUCTION],
                settlement_policy=context.vulnerability_policy,
            )
        )
        base_damage = effect_strength * anomaly_multiplier
        value = (
            base_damage
            * anomaly_crit.value
            * anomaly_bonus
            * defense.value
            * resistance_region.value
            * vulnerability.value
        )
        return CalculationResult(
            value=value,
            breakdown=(
                _node(CalculationNode.ANOMALY_ATTACK_LEVEL_COEFFICIENT, level_coefficient),
                _node(CalculationNode.ANOMALY_EFFECT_STRENGTH, effect_strength),
                _node(CalculationNode.ATTRIBUTE_ANOMALY_MULTIPLIER, anomaly_multiplier),
                _node(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
                *anomaly_crit.breakdown,
                _node(CalculationNode.ANOMALY_DAMAGE_BONUS_REGION, anomaly_bonus),
                *defense.breakdown,
                *resistance_region.breakdown,
                *vulnerability.breakdown,
            ),
            anomaly_effect_strength_trace=effect_trace,
        )


def _strength_factor(modifier):
    from core.types import AnomalyStrengthFactor, Resolved

    return AnomalyStrengthFactor(
        factor="normal-bonus",
        value=modifier.value.value if isinstance(modifier.value, Resolved) else None,
        source_id=str(modifier.effect_id),
        source_label=str(modifier.effect_id),
        owner_character_id=None,
        unresolved=(modifier.value.notes if not isinstance(modifier.value, Resolved) else None),
    )


def _mutation_coefficient(context, unresolved):
    from core.types import AnomalyStrengthFactor, Resolved

    coefficient = 1.0
    factors = []
    for modifier in context.modifiers:
        if modifier.modifier_path is not CalculationNode.ANOMALY_MUTATION_COEFFICIENT:
            continue
        if modifier.operation is not EffectOperation.MULTIPLY:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        "CurrentAttributeAnomalyDamageCalculator supports "
                        "MULTIPLY only for anomaly mutation coefficient"
                    ),
                )
            )
            continue
        if not isinstance(modifier.value, Resolved):
            unresolved.append(modifier.value)
            value = None
        else:
            value = modifier.value.value
            coefficient *= value
        factors.append(
            AnomalyStrengthFactor(
                factor="mutation",
                value=value,
                source_id=str(modifier.effect_id),
                source_label=str(modifier.effect_id),
                owner_character_id=None,
                unresolved=(modifier.value.notes if value is None else None),
            )
        )
    return coefficient, tuple(factors)


__all__ = ["CurrentAttributeAnomalyDamageCalculator"]
