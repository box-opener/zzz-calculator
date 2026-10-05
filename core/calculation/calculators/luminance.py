"""Luminance damage from an ordinary record or a special virtual-void snapshot."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    CalculationContext,
    CalculationNode,
    LuminanceDamageEvent,
    SpecialLuminanceDamageEvent,
    NoCritRule,
    Resolved,
    Unresolved,
    UnresolvedReason,
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
    {
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
        CalculationNode.LUMINANCE_FLARE_AP_CONTRIBUTION,
    }
)


class LuminanceDamageCalculator:
    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        source_trace = None
        is_special_source = isinstance(event, SpecialLuminanceDamageEvent)
        anomaly_record_id = None
        if isinstance(event, LuminanceDamageEvent):
            event, record, damage_dealer = require_historical_context(
                context,
                LuminanceDamageEvent,
                "LuminanceDamageCalculator",
            )
            effect_strength_source = record.weighted_anomaly_effect_strength
            source_penetration_rate = record.penetration_rate
            source_penetration_flat = record.penetration_flat
            source_multiplier = Resolved(1.0)
            source_label = f"anomaly record {record.record_id}"
            anomaly_record_id = str(record.record_id)
        elif isinstance(event, SpecialLuminanceDamageEvent):
            if context.battle_state_id != event.metadata.battle_state_id:
                raise InvalidCalculationContextError(
                    "CalculationContext battle_state_id does not match DamageEvent"
                )
            if context.target_snapshot.enemy_id != event.metadata.target_enemy:
                raise InvalidCalculationContextError(
                    "target snapshot does not match DamageEvent target"
                )
            damage_dealer = next(
                (
                    item for item in context.character_snapshots
                    if item.character_id == event.metadata.damage_dealer
                ),
                None,
            )
            if damage_dealer is None:
                raise InvalidCalculationContextError(
                    f"missing damage dealer character snapshot: {event.metadata.damage_dealer}"
                )
            source_snapshot = event.source_snapshot
            if source_snapshot.element is not event.metadata.element:
                raise InvalidCalculationContextError(
                    "special virtual-void source element does not match DamageEvent"
                )
            effect_strength_source = source_snapshot.weighted_anomaly_effect_strength
            source_penetration_rate = source_snapshot.penetration_rate
            source_penetration_flat = source_snapshot.penetration_flat
            source_multiplier = source_snapshot.source_multiplier
            source_trace = source_snapshot.anomaly_effect_strength_trace
            source_label = f"special virtual-void source {source_snapshot.source_id}"
        else:
            raise InvalidCalculationContextError(
                "LuminanceDamageCalculator only accepts typed Luminance events"
            )
        unresolved: list[Unresolved] = []
        if isinstance(event.crit_rule, Unresolved):
            unresolved.append(event.crit_rule)
        elif not isinstance(event.crit_rule, NoCritRule):
            raise InvalidCalculationContextError(
                "luminance damage must use NoCritRule"
            )

        effect_strength = resolved_number(effect_strength_source, unresolved)
        base_multiplier = fixed_multiplier(
            event.multiplier,
            "LuminanceDamageCalculator",
            unresolved,
        )
        if source_penetration_rate is None:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes=(
                        f"{source_label} is missing its captured "
                        "penetration rate for luminance settlement"
                    ),
                )
            )
            penetration_rate = None
        else:
            penetration_rate = resolved_number(source_penetration_rate, unresolved)
        if source_penetration_flat is None:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes=(
                        f"{source_label} is missing its captured "
                        "penetration flat value for luminance settlement"
                    ),
                )
            )
            penetration_flat = None
        else:
            penetration_flat = resolved_number(source_penetration_flat, unresolved)
        source_multiplier_value = resolved_number(source_multiplier, unresolved)
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
        ap_contribution = modifiers[CalculationNode.LUMINANCE_FLARE_AP_CONTRIBUTION]
        cinema_multiplier = _luminance_cinema_multiplier(context.modifiers, unresolved)
        multiplier = (
            (base_multiplier + ap_contribution) * cinema_multiplier
            if base_multiplier is not None and cinema_multiplier is not None
            else None
        )
        required = (
            effect_strength,
            multiplier,
            penetration_rate,
            penetration_flat,
            initial_defense,
            damage_reduction,
            resistance_value,
            source_multiplier_value,
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
        assert source_multiplier_value is not None

        base_damage = effect_strength * multiplier * source_multiplier_value
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
        flare_breakdown = (
            node_value(
                CalculationNode.LUMINANCE_FLARE_AP_CONTRIBUTION,
                ap_contribution,
            ),
            node_value(
                CalculationNode.LUMINANCE_FLARE_CINEMA_MULTIPLIER,
                cinema_multiplier,
            ),
        )
        return CalculationResult(
            value=final,
            breakdown=(
                node_value(CalculationNode.ANOMALY_EFFECT_STRENGTH, effect_strength),
                node_value(
                    (
                        CalculationNode.LUMINANCE_SPECIAL_SOURCE_PENETRATION_RATE
                        if is_special_source
                        else CalculationNode.ANOMALY_RECORD_PENETRATION_RATE
                    ),
                    penetration_rate,
                ),
                node_value(
                    (
                        CalculationNode.LUMINANCE_SPECIAL_SOURCE_PENETRATION_FLAT
                        if is_special_source
                        else CalculationNode.ANOMALY_RECORD_PENETRATION_FLAT
                    ),
                    penetration_flat,
                ),
                node_value(CalculationNode.LUMINANCE_MULTIPLIER, multiplier),
                *flare_breakdown,
                node_value(
                    CalculationNode.LUMINANCE_SPECIAL_SOURCE_MULTIPLIER,
                    source_multiplier_value,
                ),
                node_value(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
                *luminance_bonus.breakdown,
                *defense.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
            anomaly_effect_strength_trace=source_trace,
            anomaly_record_id=anomaly_record_id,
        )


def _luminance_cinema_multiplier(modifiers, unresolved: list[Unresolved]) -> float | None:
    product = 1.0
    for modifier in modifiers:
        if modifier.modifier_path is not CalculationNode.DAMAGE_SKILL_MULTIPLIER:
            continue
        if modifier.operation.value != "multiply":
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes="Luminance Flare cinema multiplier supports MULTIPLY only",
                )
            )
            continue
        value = resolved_number(modifier.value, unresolved)
        if value is not None:
            product *= value
    return product
