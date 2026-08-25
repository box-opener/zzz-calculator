from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    AttributeAnomalyDamageCalculator,
    CalculationResult,
    DamageCalculator,
    InvalidCalculationContextError,
)
from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    BattleStateId,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DirectDamageEvent,
    EffectId,
    EffectOperation,
    Element,
    EnemyId,
    EnemySnapshot,
    FixedMultiplier,
    IndependentAnomalyCrit,
    Modifier,
    NoAnomalyCrit,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolved,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)


def _value(value: float | Unresolved) -> Resolved[float] | Unresolved:
    return value if isinstance(value, Unresolved) else Resolved(value)


def _stats(
    *,
    penetration_rate: float = 0.0,
    penetration_flat: float = 0.0,
    ordinary_crit_rate: float = 1.0,
    ordinary_crit_damage: float = 10.0,
) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(99999.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(ordinary_crit_rate),
        crit_damage=Resolved(ordinary_crit_damage),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(penetration_rate),
        penetration_flat=Resolved(penetration_flat),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(99.0)},
    )


def _snapshot(
    character_id: CharacterId,
    *,
    level: int = 60,
    penetration_rate: float = 0.0,
    penetration_flat: float = 0.0,
    ordinary_crit_rate: float = 1.0,
    ordinary_crit_damage: float = 10.0,
) -> CharacterSnapshot:
    return CharacterSnapshot(
        character_id=character_id,
        level=level,
        settlement_stats=_stats(
            penetration_rate=penetration_rate,
            penetration_flat=penetration_flat,
            ordinary_crit_rate=ordinary_crit_rate,
            ordinary_crit_damage=ordinary_crit_damage,
        ),
    )


def _record(
    *,
    record_id: str = "anomaly:record",
    target_enemy: EnemyId | None = None,
    element: Element = Element.PHYSICAL,
    triggerer: CharacterId | None = None,
    effect_strength: float | Unresolved = 10000.0,
    anomaly_bonus_region: float | Unresolved = 1.2,
    crit_capability: NoAnomalyCrit | IndependentAnomalyCrit | Unresolved | None = None,
) -> AnomalyRecord:
    trigger = triggerer or CharacterId("character:triggerer")
    capability = crit_capability or NoAnomalyCrit()
    strength = _value(effect_strength)
    return AnomalyRecord(
        record_id=AnomalyRecordId(record_id),
        target_enemy=target_enemy or EnemyId("enemy:target"),
        element=element,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[element],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[element],
        weighted_anomaly_effect_strength=strength,
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=_value(anomaly_bonus_region),
        contributors=(trigger,),
        anomaly_triggerer=trigger,
        crit_capability=capability,
        triggered_at=1.0,
        duration=Resolved(10.0),
        contributions=(
            AnomalyContribution(
                contributor=trigger,
                actual_written_buildup=100.0,
                anomaly_effect_strength=strength,
                impact_strength=Resolved(100.0),
                occurred_at=1.0,
            ),
        ),
    )


def _crit_rule(
    record: AnomalyRecord,
) -> NoCritRule | RecordedAnomalyCritRule | Unresolved:
    if isinstance(record.crit_capability, NoAnomalyCrit):
        return NoCritRule()
    if isinstance(record.crit_capability, IndependentAnomalyCrit):
        return RecordedAnomalyCritRule(
            record_id=record.record_id,
            capability=record.crit_capability,
        )
    return record.crit_capability


def _event(
    record: AnomalyRecord,
    *,
    damage_dealer: CharacterId | None = None,
    anomaly_triggerer: CharacterId | None = None,
    target_enemy: EnemyId | None = None,
    element: Element | None = None,
    multiplier: FixedMultiplier | CalculationNodeMultiplier | Unresolved | None = None,
    crit_rule: NoCritRule | RecordedAnomalyCritRule | Unresolved | None = None,
) -> AttributeAnomalyDamageEvent:
    dealer = damage_dealer or record.anomaly_triggerer
    return AttributeAnomalyDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:attribute-anomaly"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=target_enemy or record.target_enemy,
            element=element or record.element,
            created_at=record.triggered_at,
        ),
        anomaly_triggerer=anomaly_triggerer or record.anomaly_triggerer,
        base_settlement_data_source=AnomalyRecordValueSource(record.record_id),
        history_record_source=record.record_id,
        multiplier=multiplier or FixedMultiplier(Resolved(7.13)),
        crit_rule=crit_rule or _crit_rule(record),
    )


def _target(
    *,
    enemy_id: EnemyId | None = None,
    initial_defense: float = 794.0,
    element: Element = Element.PHYSICAL,
    resistance: float = 0.2,
    damage_reduction: float = 0.0,
) -> EnemySnapshot:
    return EnemySnapshot(
        enemy_id=enemy_id or EnemyId("enemy:target"),
        level=70,
        initial_defense=Resolved(initial_defense),
        damage_resistance={element: Resolved(resistance)},
        anomaly_buildup_resistance={},
        daze_resistance=Resolved(0.0),
        damage_reduction=Resolved(damage_reduction),
    )


def _modifier(
    node: CalculationNode,
    value: float | Unresolved,
    *,
    operation: EffectOperation = EffectOperation.ADD,
) -> Modifier:
    return Modifier(
        effect_id=EffectId(f"effect:{node.value}"),
        modifier_path=node,
        operation=operation,
        value=value if isinstance(value, Unresolved) else Resolved(value),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )


def _context(
    event: AttributeAnomalyDamageEvent | DirectDamageEvent,
    *,
    snapshots: tuple[CharacterSnapshot, ...],
    records: tuple[AnomalyRecord, ...],
    target: EnemySnapshot | None = None,
    modifiers: tuple[Modifier, ...] = (),
) -> CalculationContext:
    return CalculationContext(
        event=event,
        battle_state_id=BattleStateId("battle:1"),
        character_snapshots=snapshots,
        target_snapshot=target or _target(),
        modifiers=modifiers,
        history_records=records,
    )


def _breakdown(result: CalculationResult) -> dict[CalculationNode, float]:
    values: dict[CalculationNode, float] = {}
    for node_value in result.breakdown:
        assert isinstance(node_value.value, Resolved)
        values[node_value.node] = node_value.value.value
    return values


def test_attribute_anomaly_damage_golden_result() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )

    result = AttributeAnomalyDamageCalculator().calculate(context)
    breakdown = _breakdown(result)

    assert result.value == pytest.approx(34224.0)
    assert result.unresolved == ()
    assert breakdown[CalculationNode.ANOMALY_EFFECT_STRENGTH] == 10000.0
    assert breakdown[CalculationNode.ATTRIBUTE_ANOMALY_MULTIPLIER] == 7.13
    assert breakdown[CalculationNode.DAMAGE_BASE_VALUE] == 71300.0
    assert breakdown[CalculationNode.ANOMALY_CRIT_REGION] == 1.0
    assert breakdown[CalculationNode.ANOMALY_DAMAGE_BONUS_REGION] == 1.2
    assert breakdown[CalculationNode.DAMAGE_DEFENSE_REGION] == 0.5
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8


def test_independent_anomaly_crit_does_not_read_ordinary_crit_stats() -> None:
    capability = IndependentAnomalyCrit(
        crit_rate=Resolved(1.0),
        crit_damage=Resolved(0.5),
    )
    record = _record(crit_capability=capability)
    event = _event(record)
    low_ordinary_crit = _context(
        event,
        snapshots=(
            _snapshot(
                event.metadata.damage_dealer,
                ordinary_crit_rate=0.0,
                ordinary_crit_damage=0.0,
            ),
        ),
        records=(record,),
    )
    high_ordinary_crit = replace(
        low_ordinary_crit,
        character_snapshots=(
            _snapshot(
                event.metadata.damage_dealer,
                ordinary_crit_rate=1.0,
                ordinary_crit_damage=99.0,
            ),
        ),
    )
    calculator = AttributeAnomalyDamageCalculator()

    low_result = calculator.calculate(low_ordinary_crit)
    high_result = calculator.calculate(high_ordinary_crit)

    assert low_result.value == pytest.approx(51336.0)
    assert high_result.value == low_result.value
    assert _breakdown(low_result)[CalculationNode.ANOMALY_CRIT_REGION] == 1.5


def test_current_anomaly_bonus_and_normal_bonus_modifiers_are_not_reapplied() -> None:
    record = _record(anomaly_bonus_region=1.2)
    event = _event(record)
    base_context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )
    context_with_irrelevant_current_bonuses = replace(
        base_context,
        modifiers=(
            _modifier(CalculationNode.ANOMALY_DAMAGE_BONUS, 99.0),
            _modifier(CalculationNode.DAMAGE_NORMAL_BONUS, 99.0),
            _modifier(CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION, 99.0),
        ),
    )
    calculator = AttributeAnomalyDamageCalculator()

    base_result = calculator.calculate(base_context)
    modified_result = calculator.calculate(context_with_irrelevant_current_bonuses)
    breakdown = _breakdown(modified_result)

    assert modified_result == base_result
    assert CalculationNode.DAMAGE_NORMAL_BONUS_REGION not in breakdown
    assert CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION not in breakdown
    assert CalculationNode.CHARACTER_CURRENT_ATTACK not in breakdown
    assert CalculationNode.CHARACTER_CURRENT_CRIT_RATE not in breakdown
    assert CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE not in breakdown
    assert CalculationNode.DAMAGE_STANDARD_CRIT_REGION not in breakdown


def test_variant_element_reads_original_element_resistance() -> None:
    record = _record(
        element=Element.LINREN,
        effect_strength=1000.0,
        anomaly_bonus_region=1.0,
    )
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
        target=_target(
            initial_defense=0.0,
            element=Element.PHYSICAL,
            resistance=0.2,
        ),
    )

    result = AttributeAnomalyDamageCalculator().calculate(context)

    assert _breakdown(result)[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8
    assert result.value == pytest.approx(5704.0)


def test_calculator_routes_defense_resistance_and_reduction_modifiers() -> None:
    record = _record(effect_strength=1000.0, anomaly_bonus_region=1.0)
    event = _event(record, multiplier=FixedMultiplier(Resolved(1.0)))
    context = _context(
        event,
        snapshots=(
            _snapshot(
                event.metadata.damage_dealer,
                penetration_rate=0.1,
                penetration_flat=20.0,
            ),
        ),
        records=(record,),
        target=_target(initial_defense=1000.0, damage_reduction=0.1),
        modifiers=(
            _modifier(CalculationNode.ENEMY_DEFENSE_INCREASE, 0.1),
            _modifier(CalculationNode.ENEMY_DEFENSE_REDUCTION, 0.2),
            _modifier(CalculationNode.DAMAGE_DEFENSE_IGNORE, 0.1),
            _modifier(CalculationNode.DAMAGE_PENETRATION_RATE, 0.05),
            _modifier(CalculationNode.DAMAGE_PENETRATION_FLAT, 30.0),
            _modifier(CalculationNode.DAMAGE_RESISTANCE_IGNORE, 0.1),
            _modifier(CalculationNode.ENEMY_RESISTANCE_REDUCTION, 0.05),
            _modifier(CalculationNode.ENEMY_DAMAGE_REDUCTION, 0.1),
        ),
    )

    result = AttributeAnomalyDamageCalculator().calculate(context)
    breakdown = _breakdown(result)
    defense_region = 794.0 / (630.0 + 794.0)

    assert breakdown[CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE] == pytest.approx(
        630.0
    )
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == pytest.approx(0.95)
    assert breakdown[CalculationNode.DAMAGE_REDUCTION_REGION] == pytest.approx(0.8)
    assert result.value == pytest.approx(1000.0 * defense_region * 0.95 * 0.8)


def test_missing_and_duplicate_history_records_are_context_errors() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(),
    )

    with pytest.raises(InvalidCalculationContextError, match="missing anomaly record"):
        AttributeAnomalyDamageCalculator().calculate(context)

    duplicate_context = replace(context, history_records=(record, record))
    with pytest.raises(InvalidCalculationContextError, match="duplicate anomaly record"):
        AttributeAnomalyDamageCalculator().calculate(duplicate_context)


@pytest.mark.parametrize("mismatch", ("target", "element", "triggerer"))
def test_event_and_record_identities_must_match(mismatch: str) -> None:
    record = _record()
    if mismatch == "target":
        event = _event(record, target_enemy=EnemyId("enemy:other"))
        target = _target(enemy_id=EnemyId("enemy:other"))
    elif mismatch == "element":
        event = _event(record, element=Element.ICE)
        target = _target(element=Element.ICE)
    else:
        event = _event(
            record,
            anomaly_triggerer=CharacterId("character:other-triggerer"),
        )
        target = _target()
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
        target=target,
    )

    with pytest.raises(InvalidCalculationContextError, match=mismatch):
        AttributeAnomalyDamageCalculator().calculate(context)


def test_crit_record_id_and_capability_must_match_selected_record() -> None:
    capability = IndependentAnomalyCrit(
        crit_rate=Resolved(1.0),
        crit_damage=Resolved(0.5),
    )
    record = _record(crit_capability=capability)
    wrong_id_rule = RecordedAnomalyCritRule(
        record_id=AnomalyRecordId("anomaly:other"),
        capability=capability,
    )
    event = _event(record, crit_rule=wrong_id_rule)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )

    with pytest.raises(InvalidCalculationContextError, match="crit rule record"):
        AttributeAnomalyDamageCalculator().calculate(context)

    mismatched_capability = IndependentAnomalyCrit(
        crit_rate=Resolved(0.5),
        crit_damage=Resolved(0.5),
    )
    mismatched_event = _event(
        record,
        crit_rule=RecordedAnomalyCritRule(
            record_id=record.record_id,
            capability=mismatched_capability,
        ),
    )
    mismatched_context = replace(context, event=mismatched_event)
    with pytest.raises(InvalidCalculationContextError, match="capability"):
        AttributeAnomalyDamageCalculator().calculate(mismatched_context)


def test_non_attribute_anomaly_event_is_rejected() -> None:
    dealer = CharacterId("character:direct")
    event = DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:direct"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:target"),
            element=Element.PHYSICAL,
            created_at=1.0,
        ),
        base_settlement_data_source=CurrentAttackValueSource(dealer),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(dealer),
    )
    context = _context(
        event,
        snapshots=(_snapshot(dealer),),
        records=(),
    )

    with pytest.raises(InvalidCalculationContextError, match="AttributeAnomalyDamageEvent"):
        AttributeAnomalyDamageCalculator().calculate(context)


def test_node_multiplier_returns_unresolved_without_partial_damage() -> None:
    record = _record()
    event = _event(
        record,
        multiplier=CalculationNodeMultiplier(
            CalculationNode.ATTRIBUTE_ANOMALY_MULTIPLIER
        ),
    )
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )

    result = AttributeAnomalyDamageCalculator().calculate(context)

    assert result.value is None
    assert result.breakdown == ()
    assert len(result.unresolved) == 1


def test_non_add_modifier_is_not_guessed() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
        modifiers=(
            _modifier(
                CalculationNode.ENEMY_DEFENSE_REDUCTION,
                1.2,
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )

    result = AttributeAnomalyDamageCalculator().calculate(context)

    assert result.value is None
    assert result.unresolved[0].reason is UnresolvedReason.MISSING_SPEC_RULE


@pytest.mark.parametrize("unresolved_field", ("strength", "bonus", "crit"))
def test_unresolved_record_inputs_prevent_formal_damage(
    unresolved_field: str,
) -> None:
    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes=f"{unresolved_field} is unresolved",
    )
    record = _record(
        effect_strength=(unresolved if unresolved_field == "strength" else 10000.0),
        anomaly_bonus_region=(unresolved if unresolved_field == "bonus" else 1.2),
        crit_capability=(unresolved if unresolved_field == "crit" else None),
    )
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )

    result = AttributeAnomalyDamageCalculator().calculate(context)

    assert result.value is None
    assert result.breakdown == ()
    assert result.unresolved


def test_other_history_records_do_not_change_selected_record_damage() -> None:
    selected = _record(record_id="anomaly:selected")
    other = _record(record_id="anomaly:other", effect_strength=999999.0)
    event = _event(selected)
    base_context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(selected,),
    )
    extra_history_context = replace(
        base_context,
        history_records=(other, selected),
    )
    calculator = AttributeAnomalyDamageCalculator()

    assert calculator.calculate(base_context) == calculator.calculate(
        extra_history_context
    )


def test_calculator_satisfies_protocol_and_does_not_mutate_context() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )
    original = context
    calculator = AttributeAnomalyDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    calculator.calculate(context)
    assert context == original
