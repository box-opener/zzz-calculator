from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    CalculationResult,
    DamageCalculator,
    InvalidCalculationContextError,
    PenetrationDamageCalculator,
)
from core.types import (
    BattleStateId,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    CurrentAttackValueSource,
    CurrentPenetrationForceValueSource,
    DamageEvent,
    DamageEventId,
    DamageEventMetadata,
    DirectDamageEvent,
    EffectId,
    EffectOperation,
    Element,
    EnemyId,
    EnemySnapshot,
    FixedMultiplier,
    Modifier,
    NoCritRule,
    PenetrationDamageEvent,
    Resolvable,
    Resolved,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)


def _value(value: float | Unresolved) -> Resolvable[float]:
    return value if isinstance(value, Unresolved) else Resolved(value)


def _stats(
    *,
    hp: float | Unresolved = 10000.0,
    attack: float | Unresolved = 2000.0,
    crit_rate: float | Unresolved = 0.0,
    crit_damage: float | Unresolved = 0.5,
    penetration_rate: float | Unresolved = 0.0,
    penetration_flat: float | Unresolved = 0.0,
    element_damage_bonus: dict[Element, float | Unresolved] | None = None,
) -> CharacterStats:
    bonuses = element_damage_bonus or {}
    return CharacterStats(
        hp=_value(hp),
        attack=_value(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=_value(crit_rate),
        crit_damage=_value(crit_damage),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=_value(penetration_rate),
        penetration_flat=_value(penetration_flat),
        energy_regen=Resolved(1.2),
        element_damage_bonus={
            element: _value(value) for element, value in bonuses.items()
        },
    )


def _snapshot(
    character_id: CharacterId,
    *,
    level: int = 60,
    hp: float | Unresolved = 10000.0,
    attack: float | Unresolved = 2000.0,
    crit_rate: float | Unresolved = 0.0,
    crit_damage: float | Unresolved = 0.5,
    penetration_rate: float | Unresolved = 0.0,
    penetration_flat: float | Unresolved = 0.0,
    element_damage_bonus: dict[Element, float | Unresolved] | None = None,
) -> CharacterSnapshot:
    return CharacterSnapshot(
        character_id=character_id,
        level=level,
        settlement_stats=_stats(
            hp=hp,
            attack=attack,
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            penetration_rate=penetration_rate,
            penetration_flat=penetration_flat,
            element_damage_bonus=element_damage_bonus,
        ),
    )


def _event(
    dealer: CharacterId,
    *,
    base_source: CharacterId | None = None,
    crit_owner: CharacterId | None = None,
    element: Element = Element.FIRE,
    multiplier: FixedMultiplier | CalculationNodeMultiplier | Unresolved | None = None,
) -> PenetrationDamageEvent:
    return PenetrationDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:penetration"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:target"),
            element=element,
            created_at=1.0,
        ),
        base_settlement_data_source=CurrentPenetrationForceValueSource(
            base_source or dealer
        ),
        multiplier=multiplier or FixedMultiplier(Resolved(2.0)),
        crit_rule=StandardCritRule(crit_owner or dealer),
    )


def _target(
    *,
    initial_defense: float | Unresolved = 794.0,
    element: Element = Element.FIRE,
    resistance: float | Unresolved = 0.0,
    damage_reduction: float | Unresolved = 0.0,
    is_stunned: bool = True,
) -> EnemySnapshot:
    return EnemySnapshot(
        enemy_id=EnemyId("enemy:target"),
        level=70,
        initial_defense=_value(initial_defense),
        damage_resistance={element: _value(resistance)},
        anomaly_buildup_resistance={},
        daze_resistance=Resolved(0.0),
        damage_reduction=_value(damage_reduction),
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
        value=_value(value),
        snapshot_rule=SnapshotRule.SETTLEMENT,
    )


def _context(
    event: DamageEvent,
    *,
    snapshots: tuple[CharacterSnapshot, ...],
    target: EnemySnapshot | None = None,
    modifiers: tuple[Modifier, ...] = (),
) -> CalculationContext:
    return CalculationContext(
        event=event,
        battle_state_id=BattleStateId("battle:1"),
        character_snapshots=snapshots,
        target_snapshot=target or _target(),
        modifiers=modifiers,
    )


def _breakdown(result: CalculationResult) -> dict[CalculationNode, float]:
    values: dict[CalculationNode, float] = {}
    for item in result.breakdown:
        assert isinstance(item.value, Resolved)
        values[item.node] = item.value.value
    return values


def test_penetration_damage_golden_keeps_three_identities_separate() -> None:
    dealer = CharacterId("character:dealer")
    base_source = CharacterId("character:force-source")
    crit_owner = CharacterId("character:crit-owner")
    event = _event(
        dealer,
        base_source=base_source,
        crit_owner=crit_owner,
    )
    modifier = _modifier(
        CalculationNode.PENETRATION_DAMAGE_BONUS,
        0.2,
        effect_id="character:external-effect",
    )
    context = _context(
        event,
        snapshots=(
            _snapshot(
                base_source,
                hp=10000.0,
                attack=2000.0,
                crit_rate=0.0,
                element_damage_bonus={Element.FIRE: 99.0},
            ),
            _snapshot(
                dealer,
                hp=1.0,
                attack=1.0,
                crit_rate=0.0,
                element_damage_bonus={Element.FIRE: 0.3},
            ),
            _snapshot(
                crit_owner,
                hp=1.0,
                attack=1.0,
                crit_rate=0.5,
                crit_damage=1.0,
            ),
        ),
        target=_target(resistance=0.2, damage_reduction=0.2),
        modifiers=(
            _modifier(CalculationNode.DAMAGE_NORMAL_BONUS, 0.3),
            modifier,
            _modifier(CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION, 0.1),
            _modifier(CalculationNode.ENEMY_STUN_VULNERABILITY, 0.5),
        ),
    )

    result = PenetrationDamageCalculator().calculate(context)
    values = _breakdown(result)

    assert event.metadata.damage_dealer == dealer
    assert event.base_settlement_data_source.character_id == base_source
    assert isinstance(event.crit_rule, StandardCritRule)
    assert event.crit_rule.stat_owner == crit_owner
    assert modifier.effect_id == EffectId("character:external-effect")
    assert result.value == pytest.approx(9732.096)
    assert values[CalculationNode.CHARACTER_CURRENT_ATTACK] == 2000.0
    assert values[CalculationNode.CHARACTER_CURRENT_MAX_HP] == 10000.0
    assert values[CalculationNode.PENETRATION_FORCE] == 1600.0
    assert values[CalculationNode.DAMAGE_BASE_VALUE] == 3200.0
    assert values[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == 1.6
    assert values[CalculationNode.DAMAGE_STANDARD_CRIT_REGION] == 1.5
    assert values[CalculationNode.PENETRATION_DAMAGE_BONUS_REGION] == 1.2
    assert values[CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION] == 1.1
    assert values[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8
    assert values[
        CalculationNode.DAMAGE_BROAD_VULNERABILITY_REGION
    ] == pytest.approx(1.2)


def test_penetration_force_is_recomputed_from_each_settlement_snapshot() -> None:
    dealer = CharacterId("character:live-force")
    event = _event(dealer, multiplier=FixedMultiplier(Resolved(1.0)))
    first = _context(
        event,
        snapshots=(_snapshot(dealer, hp=10000.0, attack=1000.0),),
        target=_target(initial_defense=0.0),
    )
    second = replace(
        first,
        character_snapshots=(
            _snapshot(dealer, hp=20000.0, attack=2000.0),
        ),
    )
    calculator = PenetrationDamageCalculator()

    first_result = calculator.calculate(first)
    second_result = calculator.calculate(second)

    assert _breakdown(first_result)[CalculationNode.PENETRATION_FORCE] == 1300.0
    assert _breakdown(second_result)[CalculationNode.PENETRATION_FORCE] == 2600.0
    assert first_result.value is not None
    assert second_result.value is not None
    assert second_result.value == first_result.value * 2.0


def test_penetration_force_flat_bonus_is_added_to_the_live_force_formula() -> None:
    dealer = CharacterId("character:force-bonus")
    event = _event(dealer, multiplier=FixedMultiplier(Resolved(1.0)))
    result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(_snapshot(dealer, hp=12000.0, attack=1000.0),),
            target=_target(initial_defense=0.0),
            modifiers=(
                _modifier(CalculationNode.PENETRATION_FORCE_BONUS, 900.0),
            ),
        )
    )

    assert _breakdown(result)[CalculationNode.PENETRATION_FORCE_BONUS] == 900.0
    assert _breakdown(result)[CalculationNode.PENETRATION_FORCE] == 2400.0


def test_guaranteed_penetration_crit_ignores_an_unresolved_panel_crit_rate() -> None:
    dealer = CharacterId("character:guaranteed-penetration-crit")
    event = replace(
        _event(dealer, multiplier=FixedMultiplier(Resolved(1.0))),
        crit_rule=StandardCritRule(dealer, guaranteed=True),
    )
    unresolved_rate = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="ordinary crit rate is unavailable, but this event is guaranteed to crit",
    )
    result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(
                _snapshot(
                    dealer,
                    hp=10000.0,
                    attack=1000.0,
                    crit_rate=unresolved_rate,
                    crit_damage=0.5,
                ),
            ),
            target=_target(initial_defense=0.0),
        )
    )

    assert result.value == pytest.approx(1300.0 * 1.5)
    assert _breakdown(result)[CalculationNode.DAMAGE_STANDARD_CRIT_REGION] == pytest.approx(1.5)
    assert _breakdown(result)[CalculationNode.CHARACTER_CURRENT_CRIT_RATE] == 1.0
    assert result.unresolved == ()


def test_penetration_damage_does_not_read_any_defense_or_penetration_stat() -> None:
    unknown = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="defense-only input is intentionally unknown",
    )
    dealer = CharacterId("character:no-defense-region")
    event = _event(dealer, multiplier=FixedMultiplier(Resolved(1.0)))
    base = _context(
        event,
        snapshots=(
            _snapshot(
                dealer,
                hp=10000.0,
                attack=1000.0,
                penetration_rate=unknown,
                penetration_flat=unknown,
            ),
        ),
        target=_target(initial_defense=unknown),
    )
    with_defense_modifiers = replace(
        base,
        modifiers=(
            _modifier(CalculationNode.ENEMY_DEFENSE_INCREASE, 99.0),
            _modifier(CalculationNode.ENEMY_DEFENSE_REDUCTION, 99.0),
            _modifier(CalculationNode.DAMAGE_DEFENSE_IGNORE, 99.0),
            _modifier(CalculationNode.DAMAGE_PENETRATION_RATE, 99.0),
            _modifier(
                CalculationNode.DAMAGE_PENETRATION_FLAT,
                99.0,
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )
    calculator = PenetrationDamageCalculator()

    result = calculator.calculate(with_defense_modifiers)
    values = _breakdown(result)

    assert result == calculator.calculate(base)
    assert result.value == 1300.0
    defense_nodes = {
        CalculationNode.DEFENSE_LEVEL_COEFFICIENT,
        CalculationNode.ENEMY_INITIAL_DEFENSE,
        CalculationNode.ENEMY_DEFENSE_INCREASE,
        CalculationNode.ENEMY_DEFENSE_REDUCTION,
        CalculationNode.DAMAGE_DEFENSE_IGNORE,
        CalculationNode.DAMAGE_PENETRATION_RATE,
        CalculationNode.DAMAGE_PENETRATION_FLAT,
        CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE,
        CalculationNode.DAMAGE_DEFENSE_REGION,
    }
    assert defense_nodes.isdisjoint(values)


def test_penetration_bonus_is_separate_from_normal_damage_bonus() -> None:
    dealer = CharacterId("character:separate-bonuses")
    event = _event(dealer, multiplier=FixedMultiplier(Resolved(1.0)))
    result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(
                _snapshot(
                    dealer,
                    hp=10000.0,
                    attack=0.0,
                    element_damage_bonus={Element.FIRE: 0.3},
                ),
            ),
            target=_target(initial_defense=999999.0),
            modifiers=(
                _modifier(CalculationNode.DAMAGE_NORMAL_BONUS, 0.2),
                _modifier(CalculationNode.PENETRATION_DAMAGE_BONUS, 0.4),
            ),
        )
    )
    values = _breakdown(result)

    assert values[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == 1.5
    assert values[CalculationNode.PENETRATION_DAMAGE_BONUS_REGION] == 1.4
    assert result.value == pytest.approx(2100.0)


def test_penetration_variant_reads_original_element_bonus_and_resistance() -> None:
    dealer = CharacterId("character:variant")
    event = _event(
        dealer,
        element=Element.LIESHUANG,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
    result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(
                _snapshot(
                    dealer,
                    hp=10000.0,
                    attack=0.0,
                    element_damage_bonus={Element.ICE: 0.3},
                ),
            ),
            target=_target(
                element=Element.ICE,
                resistance=0.2,
                initial_defense=999999.0,
            ),
        )
    )
    values = _breakdown(result)

    assert values[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == 1.3
    assert values[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8
    assert result.value == pytest.approx(1040.0)


def test_penetration_routes_resistance_vulnerability_and_reduction() -> None:
    dealer = CharacterId("character:modifier-routing")
    event = _event(dealer, multiplier=FixedMultiplier(Resolved(1.0)))
    result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(_snapshot(dealer, hp=10000.0, attack=0.0),),
            target=_target(resistance=0.2, damage_reduction=0.1),
            modifiers=(
                _modifier(CalculationNode.DAMAGE_RESISTANCE_IGNORE, 0.1),
                _modifier(CalculationNode.ENEMY_RESISTANCE_REDUCTION, 0.05),
                _modifier(CalculationNode.ENEMY_NORMAL_VULNERABILITY, 0.2),
                _modifier(CalculationNode.ENEMY_MOVE_VULNERABILITY, 0.1),
                _modifier(CalculationNode.ENEMY_DAMAGE_REDUCTION, 0.1),
            ),
        )
    )
    values = _breakdown(result)

    assert values[CalculationNode.DAMAGE_RESISTANCE_REGION] == pytest.approx(0.95)
    assert values[CalculationNode.DAMAGE_REDUCTION_REGION] == pytest.approx(0.8)
    assert values[CalculationNode.DAMAGE_BROAD_VULNERABILITY_REGION] == pytest.approx(
        1.04
    )
    assert result.value == pytest.approx(1000.0 * 0.95 * 1.04)


def test_penetration_unresolved_inputs_are_not_guessed() -> None:
    unknown = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="current attack is unknown",
    )
    dealer = CharacterId("character:unresolved")
    event = _event(dealer)
    unresolved_result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(_snapshot(dealer, attack=unknown),),
        )
    )
    assert unresolved_result.value is None
    assert unresolved_result.unresolved == (unknown,)

    node_event = _event(
        dealer,
        multiplier=CalculationNodeMultiplier(CalculationNode.DAMAGE_SKILL_MULTIPLIER),
    )
    node_result = PenetrationDamageCalculator().calculate(
        _context(node_event, snapshots=(_snapshot(dealer),))
    )
    assert node_result.value is None
    assert node_result.unresolved[0].reason is UnresolvedReason.MISSING_SPEC_RULE


def test_penetration_non_add_supported_modifier_is_not_guessed() -> None:
    dealer = CharacterId("character:unsupported-operation")
    event = _event(dealer)
    result = PenetrationDamageCalculator().calculate(
        _context(
            event,
            snapshots=(_snapshot(dealer),),
            modifiers=(
                _modifier(
                    CalculationNode.PENETRATION_DAMAGE_BONUS,
                    1.2,
                    operation=EffectOperation.MULTIPLY,
                ),
            ),
        )
    )

    assert result.value is None
    assert result.breakdown == ()
    assert result.unresolved[0].reason is UnresolvedReason.MISSING_SPEC_RULE


def test_penetration_context_identity_mismatches_are_rejected() -> None:
    dealer = CharacterId("character:context-errors")
    missing = CharacterId("character:missing")
    missing_event = _event(dealer, base_source=missing)
    missing_context = _context(
        missing_event,
        snapshots=(_snapshot(dealer),),
    )
    calculator = PenetrationDamageCalculator()

    with pytest.raises(InvalidCalculationContextError, match="base settlement source"):
        calculator.calculate(missing_context)

    event = _event(dealer)
    snapshot = _snapshot(dealer)
    with pytest.raises(InvalidCalculationContextError, match="duplicate"):
        calculator.calculate(_context(event, snapshots=(snapshot, snapshot)))

    battle_mismatch = replace(
        _context(event, snapshots=(snapshot,)),
        battle_state_id=BattleStateId("battle:other"),
    )
    with pytest.raises(InvalidCalculationContextError, match="battle_state_id"):
        calculator.calculate(battle_mismatch)

    target_mismatch = replace(
        _target(),
        enemy_id=EnemyId("enemy:other"),
    )
    with pytest.raises(InvalidCalculationContextError, match="target snapshot"):
        calculator.calculate(
            _context(event, snapshots=(snapshot,), target=target_mismatch)
        )


def test_penetration_rejects_other_event_and_non_standard_crit_rule() -> None:
    dealer = CharacterId("character:event-boundary")
    direct_event = DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:direct"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:target"),
            element=Element.FIRE,
            created_at=1.0,
        ),
        base_settlement_data_source=CurrentAttackValueSource(dealer),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(dealer),
    )
    calculator = PenetrationDamageCalculator()
    with pytest.raises(InvalidCalculationContextError, match="PenetrationDamageEvent"):
        calculator.calculate(_context(direct_event, snapshots=(_snapshot(dealer),)))

    invalid_crit_event = replace(
        _event(dealer),
        crit_rule=NoCritRule(),  # type: ignore[arg-type]
    )
    with pytest.raises(InvalidCalculationContextError, match="StandardCritRule"):
        calculator.calculate(
            _context(invalid_crit_event, snapshots=(_snapshot(dealer),))
        )


def test_penetration_calculator_satisfies_protocol_and_keeps_context_frozen() -> None:
    dealer = CharacterId("character:protocol")
    event = _event(dealer)
    context = _context(event, snapshots=(_snapshot(dealer),))
    calculator = PenetrationDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    calculator.calculate(context)
    assert context == _context(event, snapshots=(_snapshot(dealer),))
