from __future__ import annotations

from core.calculation import CalculationResult
from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AnomalyCritCapability,
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    BattleStateId,
    CalculationContext,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    DamageEvent,
    DamageEventId,
    DamageEventMetadata,
    EffectId,
    EffectOperation,
    Element,
    EnemyId,
    EnemySnapshot,
    Modifier,
    NoAnomalyCrit,
    Resolved,
    SnapshotRule,
    Unresolved,
)


def value(value: float | Unresolved) -> Resolved[float] | Unresolved:
    return value if isinstance(value, Unresolved) else Resolved(value)


def stats(
    *,
    penetration_rate: float = 0.0,
    penetration_flat: float = 0.0,
) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(99999.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(1.0),
        crit_damage=Resolved(99.0),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(penetration_rate),
        penetration_flat=Resolved(penetration_flat),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(99.0)},
    )


def snapshot(
    character_id: CharacterId,
    *,
    level: int = 60,
    penetration_rate: float = 0.0,
    penetration_flat: float = 0.0,
) -> CharacterSnapshot:
    return CharacterSnapshot(
        character_id,
        level,
        stats(
            penetration_rate=penetration_rate,
            penetration_flat=penetration_flat,
        ),
    )


def record(
    *,
    record_id: str = "anomaly:history",
    element: Element = Element.PHYSICAL,
    effect_strength: float | Unresolved = 10000.0,
    anomaly_bonus_region: float | Unresolved = 1.2,
    crit_capability: AnomalyCritCapability | None = None,
    penetration_rate: float | Unresolved = 0.0,
    penetration_flat: float | Unresolved = 0.0,
    target_enemy: EnemyId | None = None,
    triggerer: CharacterId | None = None,
) -> AnomalyRecord:
    source = triggerer or CharacterId("character:old-triggerer")
    strength = value(effect_strength)
    return AnomalyRecord(
        record_id=AnomalyRecordId(record_id),
        target_enemy=target_enemy or EnemyId("enemy:target"),
        element=element,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[element],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[element],
        weighted_anomaly_effect_strength=strength,
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=value(anomaly_bonus_region),
        contributors=(source,),
        anomaly_triggerer=source,
        crit_capability=(
            crit_capability if crit_capability is not None else NoAnomalyCrit()
        ),
        triggered_at=1.0,
        duration=Resolved(10.0),
        contributions=(
            AnomalyContribution(
                source,
                100.0,
                strength,
                Resolved(100.0),
                1.0,
            ),
        ),
        penetration_rate=value(penetration_rate),
        penetration_flat=value(penetration_flat),
    )


def metadata(
    dealer: CharacterId,
    record: AnomalyRecord,
    label: str,
) -> DamageEventMetadata:
    return DamageEventMetadata(
        event_id=DamageEventId(f"damage:{label}"),
        battle_state_id=BattleStateId("battle:1"),
        damage_dealer=dealer,
        target_enemy=record.target_enemy,
        element=record.element,
        created_at=2.0,
    )


def target(
    *,
    element: Element = Element.PHYSICAL,
    resistance: float = 0.2,
    initial_defense: float = 794.0,
    damage_reduction: float = 0.0,
) -> EnemySnapshot:
    return EnemySnapshot(
        EnemyId("enemy:target"),
        70,
        Resolved(initial_defense),
        {element: Resolved(resistance)},
        {},
        Resolved(0.0),
        Resolved(damage_reduction),
        True,
    )


def modifier(
    node: CalculationNode,
    amount: float | Unresolved,
    *,
    operation: EffectOperation = EffectOperation.ADD,
) -> Modifier:
    return Modifier(
        EffectId(f"effect:{node.value}"),
        node,
        operation,
        value(amount),
        SnapshotRule.SETTLEMENT,
    )


def context(
    event: DamageEvent,
    *,
    records: tuple[AnomalyRecord, ...],
    snapshots: tuple[CharacterSnapshot, ...] | None = None,
    target_snapshot: EnemySnapshot | None = None,
    modifiers: tuple[Modifier, ...] = (),
) -> CalculationContext:
    return CalculationContext(
        event,
        BattleStateId("battle:1"),
        snapshots or (snapshot(event.metadata.damage_dealer),),
        target_snapshot or target(),
        modifiers,
        records,
    )


def breakdown(result: CalculationResult) -> dict[CalculationNode, float]:
    values: dict[CalculationNode, float] = {}
    for item in result.breakdown:
        assert isinstance(item.value, Resolved)
        values[item.node] = item.value.value
    return values
