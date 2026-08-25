"""Penetration damage calculated from live attack and maximum HP."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    EffectOperation,
    FixedMultiplier,
    Modifier,
    PenetrationDamageEvent,
    Resolvable,
    Resolved,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
from ..regions import (
    BroadVulnerabilityRegionInput,
    CritRegionInput,
    NormalDamageBonusRegionInput,
    PenetrationDamageBonusRegionInput,
    PenetrationForceInput,
    ResistanceRegionInput,
    SpecialIndependentRegionInput,
    calculate_broad_vulnerability_region,
    calculate_crit_region,
    calculate_normal_damage_bonus_region,
    calculate_penetration_damage_bonus_region,
    calculate_penetration_force,
    calculate_resistance_region,
    calculate_special_independent_region,
)
from ..result import CalculationResult
from .errors import InvalidCalculationContextError


_SUPPORTED_MODIFIER_PATHS = frozenset(
    {
        CalculationNode.DAMAGE_NORMAL_BONUS,
        CalculationNode.PENETRATION_DAMAGE_BONUS,
        CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION,
        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
        CalculationNode.ENEMY_STUN_VULNERABILITY,
        CalculationNode.ENEMY_NORMAL_VULNERABILITY,
        CalculationNode.ENEMY_MOVE_VULNERABILITY,
        CalculationNode.ENEMY_DAMAGE_REDUCTION,
    }
)


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def _snapshot_index(
    snapshots: tuple[CharacterSnapshot, ...],
) -> dict[CharacterId, CharacterSnapshot]:
    index: dict[CharacterId, CharacterSnapshot] = {}
    for snapshot in snapshots:
        if snapshot.character_id in index:
            raise InvalidCalculationContextError(
                f"duplicate character snapshot: {snapshot.character_id}"
            )
        index[snapshot.character_id] = snapshot
    return index


def _required_snapshot(
    snapshots: dict[CharacterId, CharacterSnapshot],
    character_id: CharacterId,
    role: str,
) -> CharacterSnapshot:
    try:
        return snapshots[character_id]
    except KeyError as error:
        raise InvalidCalculationContextError(
            f"missing {role} character snapshot: {character_id}"
        ) from error


def _resolved_number(
    value: Resolvable[float],
    unresolved: list[Unresolved],
) -> float | None:
    if isinstance(value, Resolved):
        return value.value
    unresolved.append(value)
    return None


def _unsupported_modifier(modifier: Modifier) -> Unresolved:
    return Unresolved(
        reason=UnresolvedReason.MISSING_SPEC_RULE,
        notes=(
            "PenetrationDamageCalculator does not support "
            f"{modifier.operation.value} for {modifier.modifier_path.value} "
            f"from {modifier.effect_id}"
        ),
    )


def _modifier_totals(
    context: CalculationContext,
    unresolved: list[Unresolved],
) -> dict[CalculationNode, float]:
    totals = {node: 0.0 for node in _SUPPORTED_MODIFIER_PATHS}
    for modifier in context.modifiers:
        if modifier.modifier_path not in _SUPPORTED_MODIFIER_PATHS:
            continue
        if modifier.operation is not EffectOperation.ADD:
            unresolved.append(_unsupported_modifier(modifier))
            continue
        value = _resolved_number(modifier.value, unresolved)
        if value is not None:
            totals[modifier.modifier_path] += value
    return totals


class PenetrationDamageCalculator:
    """Calculate one penetration event without reading a defense region."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, PenetrationDamageEvent):
            raise InvalidCalculationContextError(
                "PenetrationDamageCalculator only accepts PenetrationDamageEvent"
            )
        if context.battle_state_id != event.metadata.battle_state_id:
            raise InvalidCalculationContextError(
                "CalculationContext battle_state_id does not match DamageEvent"
            )
        if context.target_snapshot.enemy_id != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "target snapshot does not match DamageEvent target"
            )

        snapshots = _snapshot_index(context.character_snapshots)
        base_source = _required_snapshot(
            snapshots,
            event.base_settlement_data_source.character_id,
            "base settlement source",
        )
        damage_dealer = _required_snapshot(
            snapshots,
            event.metadata.damage_dealer,
            "damage dealer",
        )

        unresolved: list[Unresolved] = []
        if isinstance(event.crit_rule, StandardCritRule):
            crit_source = _required_snapshot(
                snapshots,
                event.crit_rule.stat_owner,
                "crit stat owner",
            )
        elif isinstance(event.crit_rule, Unresolved):
            unresolved.append(event.crit_rule)
            crit_source = None
        else:
            raise InvalidCalculationContextError(
                "penetration damage only supports StandardCritRule"
            )

        current_attack = _resolved_number(
            base_source.settlement_stats.attack,
            unresolved,
        )
        current_max_hp = _resolved_number(
            base_source.settlement_stats.hp,
            unresolved,
        )
        if isinstance(event.multiplier, FixedMultiplier):
            skill_multiplier = _resolved_number(event.multiplier.value, unresolved)
        elif isinstance(event.multiplier, CalculationNodeMultiplier):
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        "PenetrationDamageCalculator only supports FixedMultiplier; "
                        f"received node {event.multiplier.node.value}"
                    ),
                )
            )
            skill_multiplier = None
        else:
            unresolved.append(event.multiplier)
            skill_multiplier = None

        crit_rate = (
            _resolved_number(crit_source.settlement_stats.crit_rate, unresolved)
            if crit_source is not None
            else None
        )
        crit_damage = (
            _resolved_number(crit_source.settlement_stats.crit_damage, unresolved)
            if crit_source is not None
            else None
        )
        damage_reduction = _resolved_number(
            context.target_snapshot.damage_reduction,
            unresolved,
        )
        base_element = BASE_ELEMENT_BY_ELEMENT[event.metadata.element]
        element_damage_bonus = _resolved_number(
            damage_dealer.settlement_stats.element_damage_bonus.get(
                base_element,
                Resolved(0.0),
            ),
            unresolved,
        )
        base_resistance = _resolved_number(
            context.target_snapshot.damage_resistance.get(
                base_element,
                Resolved(0.0),
            ),
            unresolved,
        )
        modifiers = _modifier_totals(context, unresolved)

        required_values = (
            current_attack,
            current_max_hp,
            skill_multiplier,
            crit_rate,
            crit_damage,
            damage_reduction,
            element_damage_bonus,
            base_resistance,
        )
        if unresolved or any(value is None for value in required_values):
            return CalculationResult(
                value=None,
                breakdown=(),
                unresolved=tuple(unresolved),
            )

        assert current_attack is not None
        assert current_max_hp is not None
        assert skill_multiplier is not None
        assert crit_rate is not None
        assert crit_damage is not None
        assert damage_reduction is not None
        assert element_damage_bonus is not None
        assert base_resistance is not None

        force = calculate_penetration_force(
            PenetrationForceInput(
                current_attack=current_attack,
                current_max_hp=current_max_hp,
            )
        )
        assert force.value is not None
        base_damage = force.value * skill_multiplier
        crit = calculate_crit_region(
            CritRegionInput(crit_rate=crit_rate, crit_damage=crit_damage)
        )
        normal_bonus = calculate_normal_damage_bonus_region(
            NormalDamageBonusRegionInput(
                element_damage_bonus=element_damage_bonus,
                matched_damage_bonus=modifiers[CalculationNode.DAMAGE_NORMAL_BONUS],
            )
        )
        penetration_bonus = calculate_penetration_damage_bonus_region(
            PenetrationDamageBonusRegionInput(
                modifiers[CalculationNode.PENETRATION_DAMAGE_BONUS]
            )
        )
        special_independent = calculate_special_independent_region(
            SpecialIndependentRegionInput(
                independent_bonus=modifiers[
                    CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION
                ]
            )
        )
        resistance = calculate_resistance_region(
            ResistanceRegionInput(
                base_resistance=base_resistance,
                resistance_ignore=modifiers[
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE
                ],
                resistance_reduction=modifiers[
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION
                ],
            )
        )
        vulnerability = calculate_broad_vulnerability_region(
            BroadVulnerabilityRegionInput(
                stun_vulnerability=modifiers[
                    CalculationNode.ENEMY_STUN_VULNERABILITY
                ],
                normal_vulnerability=modifiers[
                    CalculationNode.ENEMY_NORMAL_VULNERABILITY
                ],
                move_vulnerability=modifiers[
                    CalculationNode.ENEMY_MOVE_VULNERABILITY
                ],
                damage_reduction=(
                    damage_reduction
                    + modifiers[CalculationNode.ENEMY_DAMAGE_REDUCTION]
                ),
            )
        )
        assert crit.value is not None
        assert normal_bonus.value is not None
        assert penetration_bonus.value is not None
        assert special_independent.value is not None
        assert resistance.value is not None
        assert vulnerability.value is not None
        final_damage = (
            base_damage
            * normal_bonus.value
            * crit.value
            * penetration_bonus.value
            * special_independent.value
            * resistance.value
            * vulnerability.value
        )
        return CalculationResult(
            value=final_damage,
            breakdown=(
                *force.breakdown,
                _node(CalculationNode.DAMAGE_SKILL_MULTIPLIER, skill_multiplier),
                _node(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
                *normal_bonus.breakdown,
                *crit.breakdown,
                *penetration_bonus.breakdown,
                *special_independent.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
        )
