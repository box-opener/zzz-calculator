"""Attribute-anomaly damage from one explicit historical record."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    AnomalyRecord,
    AnomalyRecordId,
    AttributeAnomalyDamageEvent,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    EffectOperation,
    FixedMultiplier,
    IndependentAnomalyCrit,
    IndependentAnomalyCritRule,
    Modifier,
    NoAnomalyCrit,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolvable,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
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


_SUPPORTED_MODIFIER_PATHS = frozenset(
    {
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
) -> CharacterSnapshot:
    try:
        return snapshots[character_id]
    except KeyError as error:
        raise InvalidCalculationContextError(
            f"missing damage dealer character snapshot: {character_id}"
        ) from error


def _record_index(
    records: tuple[AnomalyRecord, ...],
) -> dict[AnomalyRecordId, AnomalyRecord]:
    index: dict[AnomalyRecordId, AnomalyRecord] = {}
    for record in records:
        if record.record_id in index:
            raise InvalidCalculationContextError(
                f"duplicate anomaly record: {record.record_id}"
            )
        index[record.record_id] = record
    return index


def _required_record(
    records: dict[AnomalyRecordId, AnomalyRecord],
    record_id: AnomalyRecordId,
) -> AnomalyRecord:
    try:
        return records[record_id]
    except KeyError as error:
        raise InvalidCalculationContextError(
            f"missing anomaly record: {record_id}"
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
            "AttributeAnomalyDamageCalculator does not support "
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


def _anomaly_crit_values(
    event: AttributeAnomalyDamageEvent,
    record: AnomalyRecord,
    unresolved: list[Unresolved],
) -> tuple[float | None, float | None]:
    rule = event.crit_rule
    capability = record.crit_capability
    if isinstance(rule, Unresolved):
        unresolved.append(rule)
        return None, None
    if isinstance(capability, Unresolved):
        unresolved.append(capability)
        return None, None
    if isinstance(rule, NoCritRule):
        if not isinstance(capability, NoAnomalyCrit):
            raise InvalidCalculationContextError(
                "NoCritRule contradicts anomaly record crit capability"
            )
        return 0.0, 0.0
    if isinstance(rule, IndependentAnomalyCritRule):
        raise InvalidCalculationContextError(
            "attribute anomaly damage cannot use independent discharge crit rule"
        )
    if rule.record_id != record.record_id:
        raise InvalidCalculationContextError(
            "crit rule record does not match anomaly history record"
        )
    if rule.capability != capability:
        raise InvalidCalculationContextError(
            "crit rule capability does not match anomaly history record"
        )
    if not isinstance(capability, IndependentAnomalyCrit):
        raise InvalidCalculationContextError(
            "recorded anomaly crit rule requires independent anomaly crit"
        )
    return (
        _resolved_number(capability.crit_rate, unresolved),
        _resolved_number(capability.crit_damage, unresolved),
    )


class AttributeAnomalyDamageCalculator:
    """Calculate only the attribute-anomaly subtype of anomaly damage."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, AttributeAnomalyDamageEvent):
            raise InvalidCalculationContextError(
                "AttributeAnomalyDamageCalculator only accepts "
                "AttributeAnomalyDamageEvent"
            )
        if context.battle_state_id != event.metadata.battle_state_id:
            raise InvalidCalculationContextError(
                "CalculationContext battle_state_id does not match DamageEvent"
            )
        if context.target_snapshot.enemy_id != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "target snapshot does not match DamageEvent target"
            )

        records = _record_index(context.history_records)
        record = _required_record(records, event.history_record_source)
        if record.target_enemy != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "anomaly record target does not match DamageEvent target"
            )
        if record.element != event.metadata.element:
            raise InvalidCalculationContextError(
                "anomaly record element does not match DamageEvent element"
            )
        if record.anomaly_triggerer != event.anomaly_triggerer:
            raise InvalidCalculationContextError(
                "anomaly record triggerer does not match DamageEvent triggerer"
            )

        snapshots = _snapshot_index(context.character_snapshots)
        damage_dealer = _required_snapshot(
            snapshots,
            event.metadata.damage_dealer,
        )
        unresolved: list[Unresolved] = []
        anomaly_effect_strength = _resolved_number(
            record.weighted_anomaly_effect_strength,
            unresolved,
        )
        anomaly_damage_bonus_region = _resolved_number(
            record.anomaly_damage_bonus_region,
            unresolved,
        )
        if isinstance(event.multiplier, FixedMultiplier):
            anomaly_multiplier = _resolved_number(event.multiplier.value, unresolved)
        elif isinstance(event.multiplier, CalculationNodeMultiplier):
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        "AttributeAnomalyDamageCalculator only supports "
                        f"FixedMultiplier; received node {event.multiplier.node.value}"
                    ),
                )
            )
            anomaly_multiplier = None
        else:
            unresolved.append(event.multiplier)
            anomaly_multiplier = None

        crit_rate, crit_damage = _anomaly_crit_values(event, record, unresolved)
        penetration_rate = _resolved_number(
            damage_dealer.settlement_stats.penetration_rate,
            unresolved,
        )
        penetration_flat = _resolved_number(
            damage_dealer.settlement_stats.penetration_flat,
            unresolved,
        )
        initial_defense = _resolved_number(
            context.target_snapshot.initial_defense,
            unresolved,
        )
        damage_reduction = _resolved_number(
            context.target_snapshot.damage_reduction,
            unresolved,
        )
        base_element = BASE_ELEMENT_BY_ELEMENT[event.metadata.element]
        base_resistance = _resolved_number(
            context.target_snapshot.damage_resistance.get(
                base_element,
                Resolved(0.0),
            ),
            unresolved,
        )
        modifiers = _modifier_totals(context, unresolved)

        required_values = (
            anomaly_effect_strength,
            anomaly_damage_bonus_region,
            anomaly_multiplier,
            crit_rate,
            crit_damage,
            penetration_rate,
            penetration_flat,
            initial_defense,
            damage_reduction,
            base_resistance,
        )
        if unresolved or any(value is None for value in required_values):
            return CalculationResult(
                value=None,
                breakdown=(),
                unresolved=tuple(unresolved),
            )

        assert anomaly_effect_strength is not None
        assert anomaly_damage_bonus_region is not None
        assert anomaly_multiplier is not None
        assert crit_rate is not None
        assert crit_damage is not None
        assert penetration_rate is not None
        assert penetration_flat is not None
        assert initial_defense is not None
        assert damage_reduction is not None
        assert base_resistance is not None

        base_damage = anomaly_effect_strength * anomaly_multiplier
        anomaly_crit = calculate_anomaly_crit_region(
            AnomalyCritRegionInput(
                crit_rate=crit_rate,
                crit_damage=crit_damage,
            )
        )
        anomaly_bonus = CalculationResult(
            value=anomaly_damage_bonus_region,
            breakdown=(
                _node(
                    CalculationNode.ANOMALY_DAMAGE_BONUS_REGION,
                    anomaly_damage_bonus_region,
                ),
            ),
        )
        defense = calculate_defense_region(
            DefenseRegionInput(
                attacker_level=damage_dealer.level,
                initial_defense=initial_defense,
                defense_increase=modifiers[
                    CalculationNode.ENEMY_DEFENSE_INCREASE
                ],
                defense_reduction=modifiers[
                    CalculationNode.ENEMY_DEFENSE_REDUCTION
                ],
                defense_ignore=modifiers[CalculationNode.DAMAGE_DEFENSE_IGNORE],
                penetration_rate=(
                    penetration_rate
                    + modifiers[CalculationNode.DAMAGE_PENETRATION_RATE]
                ),
                penetration_flat=(
                    penetration_flat
                    + modifiers[CalculationNode.DAMAGE_PENETRATION_FLAT]
                ),
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
                is_stunned=context.target_snapshot.is_stunned,
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
                settlement_policy=context.vulnerability_policy,
            )
        )
        final_damage = (
            base_damage
            * anomaly_crit.value
            * anomaly_bonus.value
            * defense.value
            * resistance.value
            * vulnerability.value
        )
        assert final_damage is not None
        base_breakdown = (
            _node(
                CalculationNode.ANOMALY_EFFECT_STRENGTH,
                anomaly_effect_strength,
            ),
            _node(
                CalculationNode.ATTRIBUTE_ANOMALY_MULTIPLIER,
                anomaly_multiplier,
            ),
            _node(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
        )
        return CalculationResult(
            value=final_damage,
            breakdown=(
                *base_breakdown,
                *anomaly_crit.breakdown,
                *anomaly_bonus.breakdown,
                *defense.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
            unresolved=(
                *anomaly_crit.unresolved,
                *anomaly_bonus.unresolved,
                *defense.unresolved,
                *resistance.unresolved,
                *vulnerability.unresolved,
            ),
        )
