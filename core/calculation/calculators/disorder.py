"""Disorder damage from one explicitly settled anomaly record."""

from __future__ import annotations

from core.types import (
    BASE_ELEMENT_BY_ELEMENT,
    AnomalyRecord,
    AnomalyRecordId,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    DisorderDamageEvent,
    EffectId,
    EffectOperation,
    FixedMultiplier,
    Modifier,
    NoCritRule,
    Resolvable,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
from ..regions import (
    BroadVulnerabilityRegionInput,
    DefenseRegionInput,
    DisorderDamageBonusRegionInput,
    ResistanceRegionInput,
    calculate_broad_vulnerability_region,
    calculate_defense_region,
    calculate_disorder_damage_bonus_region,
    calculate_resistance_region,
)
from ..result import CalculationResult
from .errors import InvalidCalculationContextError


_SUPPORTED_MODIFIER_PATHS = frozenset(
    {
        CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
        CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
        CalculationNode.DISORDER_EXTRA_MULTIPLIER,
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
            f"DisorderDamageCalculator does not support {modifier.operation.value} "
            f"for {modifier.modifier_path.value} from {modifier.effect_id}"
        ),
    )


def _reject_duplicate_disorder_attribution(
    modifiers: tuple[Modifier, ...],
) -> None:
    trigger_effects: set[EffectId] = set()
    contributor_effects: set[EffectId] = set()
    for modifier in modifiers:
        if modifier.modifier_path is CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS:
            trigger_effects.add(modifier.effect_id)
        elif (
            modifier.modifier_path
            is CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS
        ):
            contributor_effects.add(modifier.effect_id)
    duplicate_effects = trigger_effects & contributor_effects
    if duplicate_effects:
        duplicate_list = ", ".join(sorted(str(effect) for effect in duplicate_effects))
        raise InvalidCalculationContextError(
            "same disorder modifier effect cannot be attributed to both identities: "
            f"{duplicate_list}"
        )


def _modifier_totals(
    context: CalculationContext,
    unresolved: list[Unresolved],
) -> dict[CalculationNode, float]:
    _reject_duplicate_disorder_attribution(context.modifiers)
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


class DisorderDamageCalculator:
    """Calculate disorder damage only; disorder daze is a separate result."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, DisorderDamageEvent):
            raise InvalidCalculationContextError(
                "DisorderDamageCalculator only accepts DisorderDamageEvent"
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

        snapshots = _snapshot_index(context.character_snapshots)
        damage_dealer = _required_snapshot(
            snapshots,
            event.metadata.damage_dealer,
        )
        unresolved: list[Unresolved] = []
        if isinstance(event.crit_rule, Unresolved):
            unresolved.append(event.crit_rule)
        elif not isinstance(event.crit_rule, NoCritRule):
            raise InvalidCalculationContextError(
                "disorder damage must use NoCritRule"
            )

        anomaly_effect_strength = _resolved_number(
            record.weighted_anomaly_effect_strength,
            unresolved,
        )
        if isinstance(event.multiplier, FixedMultiplier):
            disorder_multiplier = _resolved_number(event.multiplier.value, unresolved)
        elif isinstance(event.multiplier, CalculationNodeMultiplier):
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        "DisorderDamageCalculator only supports FixedMultiplier; "
                        f"received node {event.multiplier.node.value}"
                    ),
                )
            )
            disorder_multiplier = None
        else:
            unresolved.append(event.multiplier)
            disorder_multiplier = None

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
            disorder_multiplier,
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
                anomaly_effect_strength_trace=record.anomaly_effect_strength_trace,
                anomaly_record_id=str(record.record_id),
            )

        assert anomaly_effect_strength is not None
        assert disorder_multiplier is not None
        assert penetration_rate is not None
        assert penetration_flat is not None
        assert initial_defense is not None
        assert damage_reduction is not None
        assert base_resistance is not None

        total_multiplier = disorder_multiplier + modifiers[
            CalculationNode.DISORDER_EXTRA_MULTIPLIER
        ]
        base_damage = anomaly_effect_strength * total_multiplier
        disorder_bonus = calculate_disorder_damage_bonus_region(
            DisorderDamageBonusRegionInput(
                trigger_damage_bonus=modifiers[
                    CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS
                ],
                settled_contributor_damage_bonus=modifiers[
                    CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS
                ],
            )
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
            * disorder_bonus.value
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
            _node(CalculationNode.DISORDER_TOTAL_MULTIPLIER, total_multiplier),
            _node(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
        )
        return CalculationResult(
            value=final_damage,
            breakdown=(
                *base_breakdown,
                *disorder_bonus.breakdown,
                *defense.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
            unresolved=(
                *disorder_bonus.unresolved,
                *defense.unresolved,
                *resistance.unresolved,
                *vulnerability.unresolved,
            ),
            anomaly_effect_strength_trace=record.anomaly_effect_strength_trace,
            anomaly_record_id=str(record.record_id),
        )
