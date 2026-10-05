from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    DamageCalculator,
    InvalidCalculationContextError,
    LuminanceDamageCalculator,
)
from core.types import (
    AnomalyRecordValueSource,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    EffectOperation,
    Element,
    FixedMultiplier,
    IndependentAnomalyCrit,
    LuminanceDamageEvent,
    NoCritRule,
    Resolved,
    StandardCritRule,
)
from tests.unit.calculation._historical_anomaly_helpers import (
    breakdown,
    context,
    metadata,
    modifier,
    record,
    snapshot,
    target,
)


def _event(history, *, multiplier=None, crit_rule=None) -> LuminanceDamageEvent:
    triggerer = CharacterId("character:luminance-triggerer")
    return LuminanceDamageEvent(
        metadata(triggerer, history, "luminance"),
        triggerer,
        AnomalyRecordValueSource(history.record_id),
        history.record_id,
        multiplier or FixedMultiplier(Resolved(5.0)),
        crit_rule or NoCritRule(),
    )


def test_luminance_golden_uses_current_bonus_not_historical_anomaly_bonus() -> None:
    history = record(anomaly_bonus_region=9.9)
    event = _event(history)
    result = LuminanceDamageCalculator().calculate(
        context(
            event,
            records=(history,),
            modifiers=(
                modifier(CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS, 0.2),
            ),
        )
    )
    values = breakdown(result)

    assert event.luminance_triggerer != history.anomaly_triggerer
    assert result.value == pytest.approx(24000.0)
    assert values[CalculationNode.LUMINANCE_MULTIPLIER] == 5.0
    assert values[CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS_REGION] == 1.2
    assert CalculationNode.ANOMALY_DAMAGE_BONUS_REGION not in values


def test_luminance_separate_events_read_separate_history_records() -> None:
    first_record = record(record_id="anomaly:first", effect_strength=10000.0)
    second_record = record(record_id="anomaly:second", effect_strength=20000.0)
    first_event = _event(first_record)
    second_event = _event(second_record)
    calculator = LuminanceDamageCalculator()

    first_result = calculator.calculate(
        context(first_event, records=(first_record, second_record))
    )
    second_result = calculator.calculate(
        context(second_event, records=(first_record, second_record))
    )

    assert first_result.value == pytest.approx(20000.0)
    assert second_result.value == pytest.approx(40000.0)


def test_luminance_ignores_record_crit_and_other_subtype_bonuses() -> None:
    history = record(
        crit_capability=IndependentAnomalyCrit(Resolved(1.0), Resolved(99.0)),
        anomaly_bonus_region=99.0,
    )
    event = _event(history)
    base = context(event, records=(history,))
    modified = replace(
        base,
        modifiers=(
            modifier(CalculationNode.DISCHARGE_DAMAGE_BONUS, 99.0),
            modifier(CalculationNode.TURBULENCE_DAMAGE_BONUS, 99.0),
            modifier(CalculationNode.ANOMALY_DAMAGE_BONUS, 99.0),
        ),
    )
    calculator = LuminanceDamageCalculator()

    assert calculator.calculate(base) == calculator.calculate(modified)


def test_luminance_rejects_ordinary_crit_rule() -> None:
    history = record()
    event = _event(
        history,
        crit_rule=StandardCritRule(CharacterId("character:ordinary-crit")),
    )

    with pytest.raises(InvalidCalculationContextError, match="NoCritRule"):
        LuminanceDamageCalculator().calculate(context(event, records=(history,)))


def test_luminance_unresolved_and_non_add_paths_are_not_guessed() -> None:
    history = record()
    node_event = _event(
        history,
        multiplier=CalculationNodeMultiplier(CalculationNode.LUMINANCE_MULTIPLIER),
    )
    assert LuminanceDamageCalculator().calculate(
        context(node_event, records=(history,))
    ).value is None

    event = _event(history)
    non_add = context(
        event,
        records=(history,),
        modifiers=(
            modifier(
                CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
                1.2,
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )
    assert LuminanceDamageCalculator().calculate(non_add).value is None


def test_luminance_variant_and_common_modifier_routing() -> None:
    history = record(
        element=Element.LINREN,
        effect_strength=1000.0,
        anomaly_bonus_region=99.0,
        penetration_rate=0.1,
        penetration_flat=20.0,
    )
    event = _event(history, multiplier=FixedMultiplier(Resolved(1.0)))
    ctx = context(
        event,
        records=(history,),
        snapshots=(
            snapshot(
                event.metadata.damage_dealer,
                penetration_rate=0.9,
                penetration_flat=900.0,
            ),
        ),
        target_snapshot=target(
            element=Element.PHYSICAL,
            resistance=0.2,
            initial_defense=1000.0,
            damage_reduction=0.1,
        ),
        modifiers=(
            modifier(CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS, 0.2),
            modifier(CalculationNode.ENEMY_DEFENSE_INCREASE, 0.1),
            modifier(CalculationNode.ENEMY_DEFENSE_REDUCTION, 0.2),
            modifier(CalculationNode.DAMAGE_DEFENSE_IGNORE, 0.1),
            modifier(CalculationNode.DAMAGE_PENETRATION_RATE, 0.05),
            modifier(CalculationNode.DAMAGE_PENETRATION_FLAT, 30.0),
            modifier(CalculationNode.DAMAGE_RESISTANCE_IGNORE, 0.1),
            modifier(CalculationNode.ENEMY_RESISTANCE_REDUCTION, 0.05),
            modifier(CalculationNode.ENEMY_DAMAGE_REDUCTION, 0.1),
        ),
    )

    result = LuminanceDamageCalculator().calculate(ctx)
    values = breakdown(result)
    defense_region = 794.0 / (630.0 + 794.0)

    assert values[CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE] == pytest.approx(
        630.0
    )
    assert values[CalculationNode.DAMAGE_RESISTANCE_REGION] == pytest.approx(0.95)
    assert values[CalculationNode.DAMAGE_REDUCTION_REGION] == pytest.approx(0.8)
    assert result.value == pytest.approx(
        1000.0 * 1.2 * defense_region * 0.95 * 0.8
    )


def test_luminance_requires_historical_penetration_snapshot() -> None:
    history = record(penetration_rate=0.0, penetration_flat=0.0)
    history = replace(history, penetration_rate=None, penetration_flat=None)
    event = _event(history)
    result = LuminanceDamageCalculator().calculate(context(event, records=(history,)))

    assert result.value is None
    assert any("captured penetration rate" in item.notes for item in result.unresolved)
    assert any("captured penetration flat" in item.notes for item in result.unresolved)


def test_luminance_protocol_and_context_immutability() -> None:
    history = record()
    event = _event(history)
    ctx = context(event, records=(history,))
    calculator = LuminanceDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    calculator.calculate(ctx)
    assert ctx == context(event, records=(history,))
