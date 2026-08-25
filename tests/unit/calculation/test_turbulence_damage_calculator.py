from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    DamageCalculator,
    InvalidCalculationContextError,
    TurbulenceDamageCalculator,
)
from core.types import (
    AnomalyRecordValueSource,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    DamageSubtype,
    EffectOperation,
    Element,
    FixedMultiplier,
    IndependentAnomalyCrit,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolved,
    TurbulenceDamageEvent,
)
from tests.unit.calculation._historical_anomaly_helpers import (
    breakdown,
    context,
    metadata,
    modifier,
    record,
    target,
)


def _event(history, *, multiplier=None, crit_rule=None) -> TurbulenceDamageEvent:
    wind_triggerer = CharacterId("character:wind-triggerer")
    return TurbulenceDamageEvent(
        metadata(wind_triggerer, history, "turbulence"),
        wind_triggerer,
        AnomalyRecordValueSource(history.record_id),
        history.record_id,
        multiplier or FixedMultiplier(Resolved(8.75)),
        crit_rule or NoCritRule(),
    )


def test_turbulence_golden_and_wind_trigger_identity() -> None:
    history = record()
    event = _event(history)
    result = TurbulenceDamageCalculator().calculate(
        context(
            event,
            records=(history,),
            modifiers=(modifier(CalculationNode.TURBULENCE_DAMAGE_BONUS, 0.1),),
        )
    )
    values = breakdown(result)

    assert event.wind_anomaly_triggerer != history.anomaly_triggerer
    assert result.value == pytest.approx(46200.0)
    assert values[CalculationNode.TURBULENCE_TOTAL_MULTIPLIER] == 8.75
    assert values[CalculationNode.ANOMALY_DAMAGE_BONUS_REGION] == 1.2
    assert values[CalculationNode.TURBULENCE_CRIT_REGION] == 1.0
    assert values[CalculationNode.TURBULENCE_DAMAGE_BONUS_REGION] == 1.1


def test_turbulence_inherits_only_explicitly_inheritable_crit() -> None:
    capability = IndependentAnomalyCrit(
        Resolved(1.0),
        Resolved(0.5),
        inherited_by=(DamageSubtype.TURBULENCE,),
    )
    history = record(crit_capability=capability)
    event = _event(
        history,
        crit_rule=RecordedAnomalyCritRule(history.record_id, capability),
    )

    result = TurbulenceDamageCalculator().calculate(
        context(
            event,
            records=(history,),
            modifiers=(modifier(CalculationNode.TURBULENCE_DAMAGE_BONUS, 0.1),),
        )
    )

    assert result.value == pytest.approx(69300.0)
    assert breakdown(result)[CalculationNode.TURBULENCE_CRIT_REGION] == 1.5


def test_turbulence_rejects_non_inheritable_or_contradictory_crit() -> None:
    capability = IndependentAnomalyCrit(Resolved(1.0), Resolved(0.5))
    history = record(crit_capability=capability)
    recorded_event = _event(
        history,
        crit_rule=RecordedAnomalyCritRule(history.record_id, capability),
    )
    with pytest.raises(InvalidCalculationContextError, match="not inheritable"):
        TurbulenceDamageCalculator().calculate(
            context(recorded_event, records=(history,))
        )

    inheritable = replace(
        capability,
        inherited_by=(DamageSubtype.TURBULENCE,),
    )
    inheritable_history = record(crit_capability=inheritable)
    no_crit_event = _event(inheritable_history)
    with pytest.raises(InvalidCalculationContextError, match="contradicts"):
        TurbulenceDamageCalculator().calculate(
            context(no_crit_event, records=(inheritable_history,))
        )


def test_turbulence_rejects_wind_history_record() -> None:
    history = record(element=Element.WIND)
    event = _event(history)

    with pytest.raises(InvalidCalculationContextError, match="non-wind"):
        TurbulenceDamageCalculator().calculate(context(event, records=(history,)))


def test_turbulence_ignores_current_anomaly_and_unrelated_bonus_nodes() -> None:
    history = record()
    event = _event(history)
    base = context(event, records=(history,))
    modified = replace(
        base,
        modifiers=(
            modifier(CalculationNode.ANOMALY_DAMAGE_BONUS, 99.0),
            modifier(CalculationNode.DISCHARGE_DAMAGE_BONUS, 99.0),
            modifier(CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS, 99.0),
        ),
    )
    calculator = TurbulenceDamageCalculator()

    assert calculator.calculate(base) == calculator.calculate(modified)


def test_turbulence_variant_resistance_and_unresolved_paths() -> None:
    history = record(element=Element.LINREN)
    event = _event(history, multiplier=FixedMultiplier(Resolved(1.0)))
    ctx = context(
        event,
        records=(history,),
        target_snapshot=target(
            element=Element.PHYSICAL,
            resistance=0.2,
            initial_defense=0.0,
        ),
    )
    result = TurbulenceDamageCalculator().calculate(ctx)

    assert breakdown(result)[CalculationNode.DAMAGE_RESISTANCE_REGION] == 0.8

    node_event = _event(
        history,
        multiplier=CalculationNodeMultiplier(CalculationNode.TURBULENCE_TOTAL_MULTIPLIER),
    )
    assert TurbulenceDamageCalculator().calculate(
        context(node_event, records=(history,))
    ).value is None

    non_add = context(
        event,
        records=(history,),
        modifiers=(
            modifier(
                CalculationNode.TURBULENCE_DAMAGE_BONUS,
                1.2,
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )
    assert TurbulenceDamageCalculator().calculate(non_add).value is None


def test_turbulence_protocol_and_context_immutability() -> None:
    history = record()
    event = _event(history)
    ctx = context(event, records=(history,))
    calculator = TurbulenceDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    calculator.calculate(ctx)
    assert ctx == context(event, records=(history,))
