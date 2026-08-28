from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    CalculationResult,
    DamageCalculator,
    DirectDamageCalculator,
    InvalidCalculationContextError,
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
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    CurrentAttackValueSource,
    CurrentPenetrationForceValueSource,
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
    IndependentAnomalyCrit,
    IndependentAnomalyCritRule,
    Modifier,
    NoAnomalyCrit,
    PenetrationDamageEvent,
    Resolved,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)


def _stats(
    *,
    attack: float,
    crit_rate: float = 0.0,
    crit_damage: float = 0.5,
    penetration_rate: float = 0.0,
    penetration_flat: float = 0.0,
    element_damage_bonus: dict[Element, float] | None = None,
) -> CharacterStats:
    bonuses = element_damage_bonus or {}
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(crit_rate),
        crit_damage=Resolved(crit_damage),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(penetration_rate),
        penetration_flat=Resolved(penetration_flat),
        energy_regen=Resolved(1.2),
        element_damage_bonus={
            element: Resolved(value) for element, value in bonuses.items()
        },
    )


def _snapshot(
    character_id: CharacterId,
    *,
    level: int = 60,
    attack: float = 3000.0,
    crit_rate: float = 0.5,
    crit_damage: float = 1.0,
    penetration_rate: float = 0.0,
    penetration_flat: float = 0.0,
    element_damage_bonus: dict[Element, float] | None = None,
) -> CharacterSnapshot:
    return CharacterSnapshot(
        character_id=character_id,
        level=level,
        settlement_stats=_stats(
            attack=attack,
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            penetration_rate=penetration_rate,
            penetration_flat=penetration_flat,
            element_damage_bonus=element_damage_bonus,
        ),
    )


def _direct_event(
    dealer: CharacterId,
    *,
    base_source: CharacterId | None = None,
    crit_owner: CharacterId | None = None,
    element: Element = Element.FIRE,
    multiplier: FixedMultiplier | CalculationNodeMultiplier | Unresolved | None = None,
    damage_tags: frozenset[DamageTag] = frozenset({DamageTag.BASIC_ATTACK}),
) -> DirectDamageEvent:
    return DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:direct"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:target"),
            element=element,
            created_at=1.0,
            damage_tags=damage_tags,
        ),
        base_settlement_data_source=CurrentAttackValueSource(base_source or dealer),
        multiplier=multiplier or FixedMultiplier(Resolved(2.0)),
        crit_rule=StandardCritRule(crit_owner or dealer),
    )


def _target(
    *,
    initial_defense: float = 794.0,
    damage_resistance: dict[Element, float] | None = None,
    damage_reduction: float = 0.0,
    is_stunned: bool = True,
) -> EnemySnapshot:
    resistances = damage_resistance or {}
    return EnemySnapshot(
        enemy_id=EnemyId("enemy:target"),
        level=70,
        initial_defense=Resolved(initial_defense),
        damage_resistance={
            element: Resolved(value) for element, value in resistances.items()
        },
        anomaly_buildup_resistance={},
        daze_resistance=Resolved(0.0),
        damage_reduction=Resolved(damage_reduction),
        is_stunned=is_stunned,
    )


def _modifier(
    node: CalculationNode,
    value: float | Unresolved,
    *,
    operation: EffectOperation = EffectOperation.ADD,
    effect_id: str | None = None,
) -> Modifier:
    return Modifier(
        effect_id=EffectId(effect_id or f"effect:{node.value}"),
        modifier_path=node,
        operation=operation,
        value=value if isinstance(value, Unresolved) else Resolved(value),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )


def _context(
    event: DirectDamageEvent | PenetrationDamageEvent,
    *,
    snapshots: tuple[CharacterSnapshot, ...],
    target: EnemySnapshot | None = None,
    modifiers: tuple[Modifier, ...] = (),
    history_records: tuple[AnomalyRecord, ...] = (),
) -> CalculationContext:
    return CalculationContext(
        event=event,
        battle_state_id=BattleStateId("battle:1"),
        character_snapshots=snapshots,
        target_snapshot=target or _target(),
        modifiers=modifiers,
        history_records=history_records,
    )


def _history_record(character_id: CharacterId) -> AnomalyRecord:
    return AnomalyRecord(
        record_id=AnomalyRecordId("anomaly:unrelated-history"),
        target_enemy=EnemyId("enemy:target"),
        element=Element.PHYSICAL,
        damage_kind=AttributeAnomalyDamageKind.ASSAULT,
        state_kind=AttributeAnomalyStateKind.FLINCH,
        weighted_anomaly_effect_strength=Resolved(1000.0),
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=Resolved(1.0),
        contributors=(character_id,),
        anomaly_triggerer=character_id,
        crit_capability=NoAnomalyCrit(),
        triggered_at=0.0,
        duration=Resolved(10.0),
        contributions=(
            AnomalyContribution(
                contributor=character_id,
                actual_written_buildup=100.0,
                anomaly_effect_strength=Resolved(1000.0),
                impact_strength=Resolved(100.0),
                occurred_at=0.0,
            ),
        ),
    )


def _breakdown(result: CalculationResult) -> dict[CalculationNode, float]:
    values: dict[CalculationNode, float] = {}
    for node_value in result.breakdown:
        assert isinstance(node_value.value, Resolved)
        values[node_value.node] = node_value.value.value
    return values


def test_direct_damage_calculator_completes_first_end_to_end_damage() -> None:
    dealer = CharacterId("character:dealer")
    event = _direct_event(dealer)
    context = _context(
        event,
        snapshots=(
            _snapshot(
                dealer,
                element_damage_bonus={Element.FIRE: 0.3},
            ),
        ),
        target=_target(
            damage_resistance={Element.FIRE: 0.2},
            damage_reduction=0.2,
        ),
        modifiers=(
            _modifier(
                CalculationNode.DAMAGE_NORMAL_BONUS,
                0.1,
                effect_id="effect:normal-damage:a",
            ),
            _modifier(
                CalculationNode.DAMAGE_NORMAL_BONUS,
                0.2,
                effect_id="effect:normal-damage:b",
            ),
            _modifier(CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION, 0.1),
            _modifier(CalculationNode.ENEMY_STUN_VULNERABILITY, 0.5),
        ),
    )

    result = DirectDamageCalculator().calculate(context)
    breakdown = _breakdown(result)

    assert result.value == pytest.approx(7603.2)
    assert result.unresolved == ()
    assert breakdown[CalculationNode.DAMAGE_BASE_VALUE] == 6000.0
    assert breakdown[CalculationNode.DAMAGE_STANDARD_CRIT_REGION] == 1.5
    assert breakdown[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == pytest.approx(1.6)
    assert breakdown[CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION] == 1.1
    assert breakdown[CalculationNode.DAMAGE_DEFENSE_REGION] == 0.5
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8
    assert breakdown[CalculationNode.DAMAGE_BROAD_VULNERABILITY_REGION] == pytest.approx(
        1.2
    )
    assert all(not isinstance(item, CalculationResult) for item in result.breakdown)


def test_calculator_keeps_base_dealer_and_crit_identities_separate() -> None:
    base_source = CharacterId("character:base-source")
    damage_dealer = CharacterId("character:damage-dealer")
    crit_owner = CharacterId("character:crit-owner")
    event = _direct_event(
        damage_dealer,
        base_source=base_source,
        crit_owner=crit_owner,
    )
    context = _context(
        event,
        snapshots=(
            _snapshot(base_source, level=1, attack=1000.0, crit_rate=0.0),
            _snapshot(
                damage_dealer,
                level=60,
                attack=9999.0,
                crit_rate=0.0,
                element_damage_bonus={Element.FIRE: 0.2},
            ),
            _snapshot(crit_owner, level=1, attack=1.0, crit_rate=1.0),
        ),
    )

    result = DirectDamageCalculator().calculate(context)
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.CHARACTER_CURRENT_ATTACK] == 1000.0
    assert breakdown[CalculationNode.DAMAGE_STANDARD_CRIT_REGION] == 2.0
    assert breakdown[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == 1.2
    assert breakdown[CalculationNode.DEFENSE_LEVEL_COEFFICIENT] == 794.0
    assert result.value == pytest.approx(2400.0)


def test_calculator_routes_defense_resistance_and_reduction_modifiers() -> None:
    dealer = CharacterId("character:modifier-routing")
    event = _direct_event(
        dealer,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
    context = _context(
        event,
        snapshots=(
            _snapshot(
                dealer,
                attack=1000.0,
                crit_rate=0.0,
                penetration_rate=0.1,
                penetration_flat=20.0,
            ),
        ),
        target=_target(
            initial_defense=1000.0,
            damage_resistance={Element.FIRE: 0.2},
            damage_reduction=0.1,
        ),
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

    result = DirectDamageCalculator().calculate(context)
    breakdown = _breakdown(result)
    expected_defense_region = 794.0 / (630.0 + 794.0)

    assert breakdown[CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE] == pytest.approx(
        630.0
    )
    assert breakdown[CalculationNode.DAMAGE_DEFENSE_REGION] == pytest.approx(
        expected_defense_region
    )
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == pytest.approx(0.95)
    assert breakdown[CalculationNode.DAMAGE_REDUCTION_REGION] == pytest.approx(0.8)
    assert result.value == pytest.approx(
        1000.0 * expected_defense_region * 0.95 * 0.8
    )


def test_modifier_effect_identity_does_not_replace_damage_identities() -> None:
    damage_dealer = CharacterId("character:damage-dealer")
    base_source = CharacterId("character:base-source")
    event = _direct_event(
        damage_dealer,
        base_source=base_source,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
    modifier = _modifier(
        CalculationNode.DAMAGE_NORMAL_BONUS,
        0.2,
        effect_id="character:D_buff",
    )
    context = _context(
        event,
        snapshots=(
            _snapshot(base_source, attack=500.0, crit_rate=0.0),
            _snapshot(damage_dealer, attack=9000.0, crit_rate=0.0),
        ),
        target=_target(initial_defense=0.0),
        modifiers=(modifier,),
    )

    result = DirectDamageCalculator().calculate(context)
    breakdown = _breakdown(result)

    assert event.metadata.damage_dealer == damage_dealer
    assert event.base_settlement_data_source.character_id == base_source
    assert modifier.effect_id == EffectId("character:D_buff")
    assert breakdown[CalculationNode.CHARACTER_CURRENT_ATTACK] == 500.0
    assert breakdown[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == 1.2
    assert result.value == pytest.approx(600.0)


def test_variant_element_reads_original_element_bonus_and_resistance() -> None:
    dealer = CharacterId("character:variant")
    event = _direct_event(
        dealer,
        element=Element.LIESHUANG,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
    context = _context(
        event,
        snapshots=(
            _snapshot(
                dealer,
                attack=1000.0,
                crit_rate=0.0,
                element_damage_bonus={Element.ICE: 0.3},
            ),
        ),
        target=_target(
            initial_defense=0.0,
            damage_resistance={Element.ICE: 0.2},
        ),
    )

    result = DirectDamageCalculator().calculate(context)
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == 1.3
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8
    assert result.value == pytest.approx(1040.0)


def test_empty_damage_tags_do_not_remove_pre_matched_generic_modifier() -> None:
    dealer = CharacterId("character:generic-bonus")
    event = _direct_event(
        dealer,
        multiplier=FixedMultiplier(Resolved(1.0)),
        damage_tags=frozenset(),
    )
    context = _context(
        event,
        snapshots=(_snapshot(dealer, attack=100.0, crit_rate=0.0),),
        target=_target(initial_defense=0.0),
        modifiers=(_modifier(CalculationNode.DAMAGE_NORMAL_BONUS, 0.2),),
    )

    result = DirectDamageCalculator().calculate(context)

    assert result.value == pytest.approx(120.0)


def test_missing_required_snapshot_is_a_context_error() -> None:
    dealer = CharacterId("character:dealer")
    missing_source = CharacterId("character:missing")
    event = _direct_event(dealer, base_source=missing_source)
    context = _context(event, snapshots=(_snapshot(dealer),))

    with pytest.raises(InvalidCalculationContextError, match="base settlement source"):
        DirectDamageCalculator().calculate(context)


def test_duplicate_character_snapshot_is_a_context_error() -> None:
    dealer = CharacterId("character:dealer")
    event = _direct_event(dealer)
    snapshot = _snapshot(dealer)
    context = _context(event, snapshots=(snapshot, snapshot))

    with pytest.raises(InvalidCalculationContextError, match="duplicate"):
        DirectDamageCalculator().calculate(context)


def test_context_and_event_battle_state_ids_must_match() -> None:
    dealer = CharacterId("character:battle-state-mismatch")
    event = _direct_event(dealer)
    context = replace(
        _context(event, snapshots=(_snapshot(dealer),)),
        battle_state_id=BattleStateId("battle:other"),
    )

    with pytest.raises(InvalidCalculationContextError, match="battle_state_id"):
        DirectDamageCalculator().calculate(context)


def test_target_snapshot_must_match_event_target() -> None:
    dealer = CharacterId("character:target-mismatch")
    event = _direct_event(dealer)
    wrong_target = replace(_target(), enemy_id=EnemyId("enemy:other"))
    context = _context(
        event,
        snapshots=(_snapshot(dealer),),
        target=wrong_target,
    )

    with pytest.raises(InvalidCalculationContextError, match="target snapshot"):
        DirectDamageCalculator().calculate(context)


def test_non_direct_event_is_rejected() -> None:
    dealer = CharacterId("character:penetration")
    event = PenetrationDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:penetration"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:target"),
            element=Element.FIRE,
            created_at=1.0,
        ),
        base_settlement_data_source=CurrentPenetrationForceValueSource(dealer),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(dealer),
    )
    context = _context(event, snapshots=(_snapshot(dealer),))

    with pytest.raises(InvalidCalculationContextError, match="DirectDamageEvent"):
        DirectDamageCalculator().calculate(context)


def test_direct_damage_rejects_independent_discharge_crit_rule() -> None:
    dealer = CharacterId("character:direct-crit-boundary")
    event = _direct_event(dealer)
    invalid_event = replace(
        event,
        crit_rule=IndependentAnomalyCritRule(
            dealer,
            IndependentAnomalyCrit(Resolved(1.0), Resolved(0.5)),
        ),  # type: ignore[arg-type]
    )
    context = _context(invalid_event, snapshots=(_snapshot(dealer),))

    with pytest.raises(InvalidCalculationContextError, match="StandardCritRule"):
        DirectDamageCalculator().calculate(context)


def test_node_multiplier_returns_unresolved_without_partial_damage() -> None:
    dealer = CharacterId("character:node-multiplier")
    event = _direct_event(
        dealer,
        multiplier=CalculationNodeMultiplier(CalculationNode.DAMAGE_SKILL_MULTIPLIER),
    )
    context = _context(event, snapshots=(_snapshot(dealer),))

    result = DirectDamageCalculator().calculate(context)

    assert result.value is None
    assert result.breakdown == ()
    assert len(result.unresolved) == 1


def test_none_result_value_requires_an_unresolved_reason() -> None:
    with pytest.raises(ValueError, match="requires at least one unresolved"):
        CalculationResult(value=None, breakdown=())


def test_unresolved_modifier_prevents_formal_damage_value() -> None:
    dealer = CharacterId("character:unresolved-modifier")
    event = _direct_event(dealer)
    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="normal damage bonus is unknown",
    )
    context = _context(
        event,
        snapshots=(_snapshot(dealer),),
        modifiers=(
            _modifier(CalculationNode.DAMAGE_NORMAL_BONUS, unresolved),
        ),
    )

    result = DirectDamageCalculator().calculate(context)

    assert result.value is None
    assert result.unresolved == (unresolved,)


def test_non_add_modifier_is_not_guessed() -> None:
    dealer = CharacterId("character:multiply-modifier")
    event = _direct_event(dealer)
    context = _context(
        event,
        snapshots=(_snapshot(dealer),),
        modifiers=(
            _modifier(
                CalculationNode.DAMAGE_NORMAL_BONUS,
                1.2,
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )

    result = DirectDamageCalculator().calculate(context)

    assert result.value is None
    assert result.unresolved[0].reason is UnresolvedReason.MISSING_SPEC_RULE


def test_history_records_do_not_change_direct_damage() -> None:
    dealer = CharacterId("character:history")
    event = _direct_event(dealer)
    base_context = _context(event, snapshots=(_snapshot(dealer),))
    context_with_history = replace(
        base_context,
        history_records=(_history_record(dealer),),
    )
    calculator = DirectDamageCalculator()

    assert calculator.calculate(base_context) == calculator.calculate(
        context_with_history
    )


def test_calculator_satisfies_protocol_and_does_not_mutate_context() -> None:
    dealer = CharacterId("character:protocol")
    event = _direct_event(dealer)
    context = _context(event, snapshots=(_snapshot(dealer),))
    original = context
    calculator = DirectDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    calculator.calculate(context)
    assert context == original
