from __future__ import annotations

from dataclasses import replace

import pytest

from core.calculation import (
    DamageCalculator,
    DischargeDamageCalculator,
    InvalidCalculationContextError,
)
from core.types import (
    AnomalyRecordValueSource,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    DamageSubtype,
    DischargeDamageEvent,
    EffectOperation,
    EnemyId,
    FixedMultiplier,
    IndependentAnomalyCrit,
    IndependentAnomalyCritRule,
    NoCritRule,
    RecordedAnomalyCritRule,
    Resolved,
    Unresolved,
    UnresolvedReason,
)
from tests.unit.calculation._historical_anomaly_helpers import (
    breakdown,
    context,
    metadata,
    modifier,
    record,
)


def _event(
    history,
    *,
    triggerer: CharacterId | None = None,
    multiplier=None,
    crit_rule=None,
) -> DischargeDamageEvent:
    actor = triggerer or CharacterId("character:discharge-triggerer")
    return DischargeDamageEvent(
        metadata(actor, history, "discharge"),
        actor,
        AnomalyRecordValueSource(history.record_id),
        history.record_id,
        multiplier or FixedMultiplier(Resolved(14.26)),
        crit_rule or NoCritRule(),
    )


def test_discharge_golden_and_triggerer_identity() -> None:
    history = record()
    event = _event(history)
    ctx = context(
        event,
        records=(history,),
        modifiers=(modifier(CalculationNode.DISCHARGE_DAMAGE_BONUS, 0.1),),
    )

    result = DischargeDamageCalculator().calculate(ctx)
    values = breakdown(result)

    assert event.discharge_triggerer != history.anomaly_triggerer
    assert result.value == pytest.approx(75292.8)
    assert values[CalculationNode.DISCHARGE_ORIGINAL_ANOMALY_MULTIPLIER] == 14.26
    assert values[CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER] == 1.0
    assert values[CalculationNode.DISCHARGE_TOTAL_MULTIPLIER] == 14.26
    assert values[CalculationNode.ANOMALY_DAMAGE_BONUS_REGION] == 1.2
    assert values[CalculationNode.DISCHARGE_CRIT_REGION] == 1.0
    assert values[CalculationNode.DISCHARGE_DAMAGE_BONUS_REGION] == 1.1


def test_discharge_own_independent_crit_and_record_inherited_crit() -> None:
    own_capability = IndependentAnomalyCrit(Resolved(1.0), Resolved(0.5))
    history = record()
    actor = CharacterId("character:discharge-triggerer")
    own_event = _event(
        history,
        triggerer=actor,
        crit_rule=IndependentAnomalyCritRule(actor, own_capability),
    )
    own_result = DischargeDamageCalculator().calculate(
        context(
            own_event,
            records=(history,),
            modifiers=(modifier(CalculationNode.DISCHARGE_DAMAGE_BONUS, 0.1),),
        )
    )

    inherited_capability = IndependentAnomalyCrit(
        Resolved(1.0),
        Resolved(0.5),
        inherited_by=(DamageSubtype.DISCHARGE,),
    )
    inherited_history = record(crit_capability=inherited_capability)
    inherited_event = _event(
        inherited_history,
        crit_rule=RecordedAnomalyCritRule(
            inherited_history.record_id,
            inherited_capability,
        ),
    )
    inherited_result = DischargeDamageCalculator().calculate(
        context(
            inherited_event,
            records=(inherited_history,),
            modifiers=(modifier(CalculationNode.DISCHARGE_DAMAGE_BONUS, 0.1),),
        )
    )

    assert own_result.value == pytest.approx(112939.2)
    assert inherited_result.value == own_result.value


def test_discharge_rejects_invalid_crit_inheritance_and_missing_owner() -> None:
    non_inheritable = IndependentAnomalyCrit(Resolved(1.0), Resolved(0.5))
    history = record(crit_capability=non_inheritable)
    inherited_event = _event(
        history,
        crit_rule=RecordedAnomalyCritRule(history.record_id, non_inheritable),
    )
    with pytest.raises(InvalidCalculationContextError, match="not inheritable"):
        DischargeDamageCalculator().calculate(context(inherited_event, records=(history,)))

    missing_owner = CharacterId("character:missing-crit-owner")
    own_event = _event(
        record(),
        crit_rule=IndependentAnomalyCritRule(missing_owner, non_inheritable),
    )
    with pytest.raises(InvalidCalculationContextError, match="crit owner"):
        DischargeDamageCalculator().calculate(
            context(own_event, records=(record(),))
        )


def test_discharge_ignores_current_anomaly_and_normal_bonus_nodes() -> None:
    history = record()
    event = _event(history)
    base = context(event, records=(history,))
    modified = replace(
        base,
        modifiers=(
            modifier(CalculationNode.ANOMALY_DAMAGE_BONUS, 99.0),
            modifier(CalculationNode.DAMAGE_NORMAL_BONUS, 99.0),
            modifier(CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION, 99.0),
        ),
    )
    calculator = DischargeDamageCalculator()

    result = calculator.calculate(modified)

    assert result == calculator.calculate(base)
    assert CalculationNode.DAMAGE_NORMAL_BONUS_REGION not in breakdown(result)


def test_discharge_unresolved_and_non_add_paths_are_not_guessed() -> None:
    history = record()
    node_event = _event(
        history,
        multiplier=CalculationNodeMultiplier(CalculationNode.DISCHARGE_TOTAL_MULTIPLIER),
    )
    node_result = DischargeDamageCalculator().calculate(
        context(node_event, records=(history,))
    )
    assert node_result.value is None

    multiply_event = _event(history)
    multiply_result = DischargeDamageCalculator().calculate(
        context(
            multiply_event,
            records=(history,),
            modifiers=(
                modifier(
                    CalculationNode.DISCHARGE_DAMAGE_BONUS,
                    1.2,
                    operation=EffectOperation.MULTIPLY,
                ),
            ),
        )
    )
    assert multiply_result.value is None


def test_discharge_history_structure_and_unresolved_record_values() -> None:
    history = record()
    event = _event(history)
    base = context(event, records=(history,))
    calculator = DischargeDamageCalculator()

    with pytest.raises(InvalidCalculationContextError, match="missing anomaly record"):
        calculator.calculate(replace(base, history_records=()))
    with pytest.raises(InvalidCalculationContextError, match="duplicate anomaly record"):
        calculator.calculate(replace(base, history_records=(history, history)))

    wrong_target = replace(history, target_enemy=EnemyId("enemy:other"))
    with pytest.raises(InvalidCalculationContextError, match="target"):
        calculator.calculate(replace(base, history_records=(wrong_target,)))

    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="historical effect strength is unknown",
    )
    unresolved_history = record(effect_strength=unresolved)
    unresolved_event = _event(unresolved_history)
    unresolved_result = calculator.calculate(
        context(unresolved_event, records=(unresolved_history,))
    )
    assert unresolved_result.value is None


def test_discharge_protocol_history_selection_and_context_immutability() -> None:
    selected = record(record_id="anomaly:selected")
    other = record(record_id="anomaly:other", effect_strength=999999.0)
    event = _event(selected)
    base = context(event, records=(selected,))
    extra = replace(base, history_records=(other, selected))
    calculator = DischargeDamageCalculator()

    assert isinstance(calculator, DamageCalculator)
    assert calculator.calculate(base) == calculator.calculate(extra)
    assert base == context(event, records=(selected,))
