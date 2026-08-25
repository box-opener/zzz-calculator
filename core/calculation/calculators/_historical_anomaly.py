"""Private structural helpers for calculators that read AnomalyRecord."""

from __future__ import annotations

from typing import Any, TypeVar

from core.types import (
    AnomalyRecord,
    AnomalyRecordId,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    EffectOperation,
    FixedMultiplier,
    Resolvable,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
from .errors import InvalidCalculationContextError


EventT = TypeVar("EventT")


COMMON_MODIFIER_PATHS = frozenset(
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


def node_value(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def resolved_number(
    value: Resolvable[float],
    unresolved: list[Unresolved],
) -> float | None:
    if isinstance(value, Resolved):
        return value.value
    unresolved.append(value)
    return None


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


def require_historical_context(
    context: CalculationContext,
    event_type: type[EventT],
    calculator_name: str,
) -> tuple[EventT, AnomalyRecord, CharacterSnapshot]:
    event = context.event
    if not isinstance(event, event_type):
        raise InvalidCalculationContextError(
            f"{calculator_name} only accepts {event_type.__name__}"
        )
    event_data: Any = event
    if context.battle_state_id != event_data.metadata.battle_state_id:
        raise InvalidCalculationContextError(
            "CalculationContext battle_state_id does not match DamageEvent"
        )
    if context.target_snapshot.enemy_id != event_data.metadata.target_enemy:
        raise InvalidCalculationContextError(
            "target snapshot does not match DamageEvent target"
        )

    records = _record_index(context.history_records)
    try:
        record = records[event_data.history_record_source]
    except KeyError as error:
        raise InvalidCalculationContextError(
            f"missing anomaly record: {event_data.history_record_source}"
        ) from error
    if record.target_enemy != event_data.metadata.target_enemy:
        raise InvalidCalculationContextError(
            "anomaly record target does not match DamageEvent target"
        )
    if record.element != event_data.metadata.element:
        raise InvalidCalculationContextError(
            "anomaly record element does not match DamageEvent element"
        )

    snapshots = _snapshot_index(context.character_snapshots)
    try:
        damage_dealer = snapshots[event_data.metadata.damage_dealer]
    except KeyError as error:
        raise InvalidCalculationContextError(
            "missing damage dealer character snapshot: "
            f"{event_data.metadata.damage_dealer}"
        ) from error
    return event, record, damage_dealer


def fixed_multiplier(
    multiplier: Any,
    calculator_name: str,
    unresolved: list[Unresolved],
) -> float | None:
    if isinstance(multiplier, FixedMultiplier):
        return resolved_number(multiplier.value, unresolved)
    if isinstance(multiplier, CalculationNodeMultiplier):
        unresolved.append(
            Unresolved(
                reason=UnresolvedReason.MISSING_SPEC_RULE,
                notes=(
                    f"{calculator_name} only supports FixedMultiplier; "
                    f"received node {multiplier.node.value}"
                ),
            )
        )
        return None
    unresolved.append(multiplier)
    return None


def modifier_totals(
    context: CalculationContext,
    supported_paths: frozenset[CalculationNode],
    calculator_name: str,
    unresolved: list[Unresolved],
) -> dict[CalculationNode, float]:
    totals = {node: 0.0 for node in supported_paths}
    for modifier in context.modifiers:
        if modifier.modifier_path not in supported_paths:
            continue
        if modifier.operation is not EffectOperation.ADD:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        f"{calculator_name} does not support "
                        f"{modifier.operation.value} for "
                        f"{modifier.modifier_path.value} from {modifier.effect_id}"
                    ),
                )
            )
            continue
        value = resolved_number(modifier.value, unresolved)
        if value is not None:
            totals[modifier.modifier_path] += value
    return totals
