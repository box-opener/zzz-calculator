from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    CalculationResult,
    DamageCalculator,
    DisorderDamageCalculator,
    InvalidCalculationContextError,
)
from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    AnomalyRecordValueSource,
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
    DisorderDamageEvent,
    EffectId,
    EffectOperation,
    Element,
    EnemyId,
    EnemySnapshot,
    FixedMultiplier,
    IndependentAnomalyCrit,
    Modifier,
    NoCritRule,
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
) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(99999.0),
        defense=Resolved(500.0),
        impact=Resolved(99999.0),
        crit_rate=Resolved(1.0),
        crit_damage=Resolved(99.0),
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
) -> CharacterSnapshot:
    return CharacterSnapshot(
        character_id=character_id,
        level=level,
        settlement_stats=_stats(
            penetration_rate=penetration_rate,
            penetration_flat=penetration_flat,
        ),
    )


def _record(
    *,
    record_id: str = "anomaly:settled",
    target_enemy: EnemyId | None = None,
    element: Element = Element.PHYSICAL,
    anomaly_triggerer: CharacterId | None = None,
    contributors: tuple[CharacterId, ...] | None = None,
    effect_strength: float | Unresolved = 10000.0,
) -> AnomalyRecord:
    triggerer = anomaly_triggerer or CharacterId("character:old-triggerer")
    participant_ids = contributors or (
        triggerer,
        CharacterId("character:other-contributor"),
    )
    strength = _value(effect_strength)
    contribution_value = 100.0 / len(participant_ids)
    contributions_detail = tuple(
        AnomalyContribution(
            contributor=participant,
            actual_written_buildup=contribution_value,
            anomaly_effect_strength=strength,
            impact_strength=Resolved(999999.0),
            occurred_at=float(index + 1),
        )
        for index, participant in enumerate(participant_ids)
    )
    return AnomalyRecord(
        record_id=AnomalyRecordId(record_id),
        target_enemy=target_enemy or EnemyId("enemy:target"),
        element=element,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[element],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[element],
        weighted_anomaly_effect_strength=strength,
        weighted_impact_strength=Resolved(999999.0),
        anomaly_damage_bonus_region=Resolved(9.9),
        contributors=participant_ids,
        anomaly_triggerer=triggerer,
        crit_capability=IndependentAnomalyCrit(
            crit_rate=Resolved(1.0),
            crit_damage=Resolved(99.0),
        ),
        triggered_at=1.0,
        duration=Resolved(10.0),
        contributions=contributions_detail,
    )


def _event(
    record: AnomalyRecord,
    *,
    disorder_triggerer: CharacterId | None = None,
    damage_dealer: CharacterId | None = None,
    target_enemy: EnemyId | None = None,
    element: Element | None = None,
    multiplier: FixedMultiplier | CalculationNodeMultiplier | Unresolved | None = None,
    crit_rule: NoCritRule | Unresolved | StandardCritRule | None = None,
) -> DisorderDamageEvent:
    triggerer = disorder_triggerer or CharacterId("character:disorder-triggerer")
    dealer = damage_dealer or triggerer
    return DisorderDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:disorder"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=target_enemy or record.target_enemy,
            element=element or record.element,
            created_at=2.0,
        ),
        disorder_triggerer=triggerer,
        base_settlement_data_source=AnomalyRecordValueSource(record.record_id),
        history_record_source=record.record_id,
        multiplier=multiplier or FixedMultiplier(Resolved(5.25)),
        crit_rule=crit_rule or NoCritRule(),
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
    effect_id: str | None = None,
    operation: EffectOperation = EffectOperation.ADD,
) -> Modifier:
    return Modifier(
        effect_id=EffectId(effect_id or f"effect:{node.value}"),
        modifier_path=node,
        operation=operation,
        value=value if isinstance(value, Unresolved) else Resolved(value),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )


def _context(
    event: DisorderDamageEvent | DirectDamageEvent,
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


def test_disorder_damage_golden_result_keeps_dynamic_identities_separate() -> None:
    old_triggerer = CharacterId("character:old-triggerer")
    other_contributor = CharacterId("character:other-contributor")
    disorder_triggerer = CharacterId("character:disorder-triggerer")
    record = _record(
        anomaly_triggerer=old_triggerer,
        contributors=(old_triggerer, other_contributor),
    )
    event = _event(record, disorder_triggerer=disorder_triggerer)
    context = _context(
        event,
        snapshots=(_snapshot(disorder_triggerer),),
        records=(record,),
        modifiers=(
            _modifier(
                CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                0.2,
                effect_id="effect:trigger-bonus",
            ),
            _modifier(
                CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
                0.15,
                effect_id="effect:settled-bonus",
            ),
        ),
    )

    result = DisorderDamageCalculator().calculate(context)
    breakdown = _breakdown(result)

    assert disorder_triggerer not in record.contributors
    assert event.disorder_triggerer != record.anomaly_triggerer
    assert result.value == pytest.approx(28350.0)
    assert breakdown[CalculationNode.ANOMALY_EFFECT_STRENGTH] == 10000.0
    assert breakdown[CalculationNode.DISORDER_TOTAL_MULTIPLIER] == 5.25
    assert breakdown[CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS] == 0.2
    assert (
        breakdown[CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS]
        == 0.15
    )
    assert breakdown[CalculationNode.DISORDER_DAMAGE_BONUS_REGION] == pytest.approx(
        1.35
    )


def test_disorder_ignores_anomaly_bonus_crit_impact_and_ordinary_regions() -> None:
    record = _record()
    event = _event(record)
    base_context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )
    irrelevant_modifiers = replace(
        base_context,
        modifiers=(
            _modifier(CalculationNode.ANOMALY_DAMAGE_BONUS, 99.0),
            _modifier(CalculationNode.DAMAGE_NORMAL_BONUS, 99.0),
            _modifier(CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION, 99.0),
        ),
    )
    calculator = DisorderDamageCalculator()

    result = calculator.calculate(irrelevant_modifiers)
    breakdown = _breakdown(result)

    assert result == calculator.calculate(base_context)
    forbidden = {
        CalculationNode.ANOMALY_DAMAGE_BONUS_REGION,
        CalculationNode.ANOMALY_CRIT_REGION,
        CalculationNode.DAMAGE_STANDARD_CRIT_REGION,
        CalculationNode.DAMAGE_NORMAL_BONUS_REGION,
        CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION,
        CalculationNode.DISORDER_IMPACT_STRENGTH,
        CalculationNode.DISORDER_WEIGHTED_IMPACT_STRENGTH,
        CalculationNode.DISORDER_DAZE_MULTIPLIER,
        CalculationNode.DISORDER_DAZE_VALUE,
    }
    assert forbidden.isdisjoint(breakdown)


def test_two_different_effects_can_apply_to_two_disorder_identities() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
        modifiers=(
            _modifier(
                CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                0.2,
                effect_id="character:same:trigger-effect",
            ),
            _modifier(
                CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
                0.15,
                effect_id="character:same:settled-effect",
            ),
        ),
    )

    result = DisorderDamageCalculator().calculate(context)

    assert _breakdown(result)[CalculationNode.DISORDER_DAMAGE_BONUS_REGION] == pytest.approx(
        1.35
    )


def test_same_effect_cannot_be_counted_for_both_disorder_identities() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
        modifiers=(
            _modifier(
                CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                0.2,
                effect_id="effect:shared",
            ),
            _modifier(
                CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
                0.2,
                effect_id="effect:shared",
            ),
        ),
    )

    with pytest.raises(InvalidCalculationContextError, match="both identities"):
        DisorderDamageCalculator().calculate(context)


def test_variant_element_reads_original_element_resistance() -> None:
    record = _record(element=Element.LINREN, effect_strength=1000.0)
    event = _event(
        record,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
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

    result = DisorderDamageCalculator().calculate(context)

    assert _breakdown(result)[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8
    assert result.value == pytest.approx(800.0)


def test_calculator_routes_defense_resistance_and_reduction_modifiers() -> None:
    record = _record(effect_strength=1000.0)
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

    result = DisorderDamageCalculator().calculate(context)
    breakdown = _breakdown(result)
    defense_region = 794.0 / (630.0 + 794.0)

    assert breakdown[CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE] == pytest.approx(
        630.0
    )
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == pytest.approx(0.95)
    assert breakdown[CalculationNode.DAMAGE_REDUCTION_REGION] == pytest.approx(0.8)
    assert result.value == pytest.approx(1000.0 * defense_region * 0.95 * 0.8)


def test_missing_duplicate_and_mismatched_records_are_context_errors() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(),
    )
    calculator = DisorderDamageCalculator()

    with pytest.raises(InvalidCalculationContextError, match="missing anomaly record"):
        calculator.calculate(context)
    with pytest.raises(InvalidCalculationContextError, match="duplicate anomaly record"):
        calculator.calculate(replace(context, history_records=(record, record)))

    wrong_target_record = replace(record, target_enemy=EnemyId("enemy:other"))
    with pytest.raises(InvalidCalculationContextError, match="target"):
        calculator.calculate(replace(context, history_records=(wrong_target_record,)))

    wrong_element_record = _record(element=Element.ICE)
    with pytest.raises(InvalidCalculationContextError, match="element"):
        calculator.calculate(replace(context, history_records=(wrong_element_record,)))


def test_non_disorder_event_is_rejected() -> None:
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

    with pytest.raises(InvalidCalculationContextError, match="DisorderDamageEvent"):
        DisorderDamageCalculator().calculate(context)


def test_non_no_crit_rule_is_rejected_or_unresolved() -> None:
    record = _record()
    ordinary_crit_event = _event(
        record,
        crit_rule=StandardCritRule(CharacterId("character:crit")),
    )
    context = _context(
        ordinary_crit_event,
        snapshots=(_snapshot(ordinary_crit_event.metadata.damage_dealer),),
        records=(record,),
    )

    with pytest.raises(InvalidCalculationContextError, match="NoCritRule"):
        DisorderDamageCalculator().calculate(context)

    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="disorder crit rule is unknown",
    )
    unresolved_event = _event(record, crit_rule=unresolved)
    unresolved_result = DisorderDamageCalculator().calculate(
        replace(context, event=unresolved_event)
    )
    assert unresolved_result.value is None
    assert unresolved_result.unresolved == (unresolved,)


def test_node_multiplier_and_unresolved_strength_prevent_formal_damage() -> None:
    record = _record()
    node_event = _event(
        record,
        multiplier=CalculationNodeMultiplier(CalculationNode.DISORDER_TOTAL_MULTIPLIER),
    )
    context = _context(
        node_event,
        snapshots=(_snapshot(node_event.metadata.damage_dealer),),
        records=(record,),
    )

    node_result = DisorderDamageCalculator().calculate(context)
    assert node_result.value is None
    assert node_result.breakdown == ()

    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="settled anomaly effect strength is unknown",
    )
    unresolved_record = _record(effect_strength=unresolved)
    unresolved_event = _event(unresolved_record)
    unresolved_context = _context(
        unresolved_event,
        snapshots=(_snapshot(unresolved_event.metadata.damage_dealer),),
        records=(unresolved_record,),
    )
    unresolved_result = DisorderDamageCalculator().calculate(unresolved_context)
    assert unresolved_result.value is None
    assert unresolved_result.unresolved


def test_non_add_modifier_is_not_guessed() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
        modifiers=(
            _modifier(
                CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                1.2,
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )

    result = DisorderDamageCalculator().calculate(context)

    assert result.value is None
    assert result.unresolved[0].reason is UnresolvedReason.MISSING_SPEC_RULE


def test_other_history_records_do_not_change_selected_record_damage() -> None:
    selected = _record(record_id="anomaly:selected")
    other = _record(record_id="anomaly:other", effect_strength=999999.0)
    event = _event(selected)
    base_context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(selected,),
    )
    extra_history = replace(base_context, history_records=(other, selected))
    calculator = DisorderDamageCalculator()

    assert calculator.calculate(base_context) == calculator.calculate(extra_history)


def test_calculator_satisfies_protocol_and_does_not_mutate_context() -> None:
    record = _record()
    event = _event(record)
    context = _context(
        event,
        snapshots=(_snapshot(event.metadata.damage_dealer),),
        records=(record,),
    )
    original = context
    calculator = DisorderDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    calculator.calculate(context)
    assert context == original
