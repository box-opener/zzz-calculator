from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.calculation import (
    CalculationNodeValue,
    CalculationResult,
    DamageCalculator,
)
from core.types import (
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    AttributeAnomalyDamageKind,
    AttributeAnomalyStateKind,
    BattleStateId,
    CalculationContext,
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DamageTag,
    DirectDamageEvent,
    EffectId,
    EffectOperation,
    Element,
    EnemyId,
    EnemySnapshot,
    FixedMultiplier,
    Modifier,
    NoAnomalyCrit,
    Resolved,
    SnapshotRule,
    StandardCritRule,
)


def _stats(*, attack: float) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.05),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.FIRE: Resolved(0.0)},
    )


def _history_record(contributor: CharacterId, enemy_id: EnemyId) -> AnomalyRecord:
    return AnomalyRecord(
        record_id=AnomalyRecordId("anomaly:history"),
        target_enemy=enemy_id,
        element=Element.PHYSICAL,
        damage_kind=AttributeAnomalyDamageKind.ASSAULT,
        state_kind=AttributeAnomalyStateKind.FLINCH,
        weighted_anomaly_effect_strength=Resolved(1000.0),
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=Resolved(1.0),
        contributors=(contributor,),
        anomaly_triggerer=contributor,
        crit_capability=NoAnomalyCrit(),
        triggered_at=1.0,
        duration=Resolved(10.0),
        contributions=(
            AnomalyContribution(
                contributor=contributor,
                actual_written_buildup=100.0,
                anomaly_effect_strength=Resolved(1000.0),
                impact_strength=Resolved(100.0),
                occurred_at=1.0,
            ),
        ),
    )


def _context() -> CalculationContext:
    dealer = CharacterId("character:dealer")
    teammate = CharacterId("character:teammate")
    enemy_id = EnemyId("enemy:target")
    event = DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:direct"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=enemy_id,
            element=Element.FIRE,
            created_at=2.0,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        ),
        base_settlement_data_source=CurrentAttackValueSource(dealer),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(dealer),
    )
    modifier = Modifier(
        effect_id=EffectId("effect:normal-damage"),
        modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
        operation=EffectOperation.ADD,
        value=Resolved(0.2),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )
    return CalculationContext(
        event=event,
        battle_state_id=BattleStateId("battle:1"),
        character_snapshots=(
            CharacterSnapshot(
                character_id=dealer,
                level=60,
                settlement_stats=_stats(attack=3000.0),
            ),
            CharacterSnapshot(
                character_id=teammate,
                level=60,
                settlement_stats=_stats(attack=2000.0),
            ),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=enemy_id,
            level=70,
            initial_defense=Resolved(1000.0),
            damage_resistance={Element.FIRE: Resolved(0.2)},
            anomaly_buildup_resistance={Element.FIRE: Resolved(0.1)},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        modifiers=(modifier,),
        history_records=(_history_record(dealer, enemy_id),),
    )


def test_calculation_context_and_snapshots_are_frozen() -> None:
    context = _context()

    with pytest.raises(FrozenInstanceError):
        context.event = context.event  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        context.character_snapshots[0].level = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        context.target_snapshot.level = 1  # type: ignore[misc]


def test_context_exposes_resolved_inputs_without_full_battle_state() -> None:
    context = _context()

    assert not hasattr(context, "battle_state")
    assert not hasattr(context, "current_damage")
    assert not hasattr(context, "final_multiplier")
    assert not hasattr(context, "result")
    assert not hasattr(context.character_snapshots[0], "current_stats")
    assert context.character_snapshots[0].settlement_stats.attack == Resolved(3000.0)
    assert len(context.character_snapshots) == 2
    assert context.character_snapshots[0].character_id != (
        context.character_snapshots[1].character_id
    )
    assert context.modifiers[0].modifier_path is CalculationNode.DAMAGE_NORMAL_BONUS
    assert isinstance(context.history_records[0], AnomalyRecord)


def test_enemy_snapshot_keeps_resistance_and_reduction_domains_separate() -> None:
    target = _context().target_snapshot

    assert not hasattr(target, "resistance")
    assert target.damage_resistance[Element.FIRE] == Resolved(0.2)
    assert target.anomaly_buildup_resistance[Element.FIRE] == Resolved(0.1)
    assert target.daze_resistance == Resolved(0.0)
    assert target.damage_reduction == Resolved(0.0)


def test_calculation_result_keeps_breakdown_and_empty_unresolved() -> None:
    node_value = CalculationNodeValue(
        node=CalculationNode.DAMAGE_DEFENSE_REGION,
        value=Resolved(0.5),
        read_rule=SnapshotRule.SETTLEMENT,
    )
    result = CalculationResult(value=100.0, breakdown=(node_value,))

    assert result.value == 100.0
    assert result.breakdown == (node_value,)
    assert result.unresolved == ()
    with pytest.raises(FrozenInstanceError):
        result.value = 200.0  # type: ignore[misc]


class _DummyCalculator:
    def calculate(self, context: CalculationContext) -> CalculationResult:
        return CalculationResult(value=0.0, breakdown=())


def test_damage_calculator_protocol_accepts_a_structural_implementation() -> None:
    calculator = _DummyCalculator()

    assert isinstance(calculator, DamageCalculator)
    assert calculator.calculate(_context()).unresolved == ()
