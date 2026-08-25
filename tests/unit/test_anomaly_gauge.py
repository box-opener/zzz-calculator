from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.calculation import apply_anomaly_buildup, build_anomaly_record
from core.types import (
    AnomalyBuildupApplicationContext,
    AnomalyBuildupEvent,
    AnomalyContribution,
    AnomalyGauge,
    AnomalyRecordId,
    AnomalyTriggerSnapshot,
    AttributeAnomalyDamageKind,
    AttributeAnomalyStateKind,
    BattleEventId,
    BattleEventMetadata,
    BattleStateId,
    CharacterId,
    Element,
    EnemyId,
    NoAnomalyCrit,
    Resolved,
    Unresolved,
    UnresolvedReason,
)


def _value(value: float | Unresolved) -> Resolved[float] | Unresolved:
    return value if isinstance(value, Unresolved) else Resolved(value)


def _event(
    buildup: float | Unresolved,
    *,
    contributor: CharacterId | None = None,
    element: Element = Element.FIRE,
    target_enemy: EnemyId | None = None,
    occurred_at: float = 1.0,
) -> AnomalyBuildupEvent:
    return AnomalyBuildupEvent(
        metadata=BattleEventMetadata(
            event_id=BattleEventId(f"event:buildup:{occurred_at}"),
            battle_state_id=BattleStateId("battle:1"),
            occurred_at=occurred_at,
        ),
        contributor=contributor or CharacterId("character:a"),
        target_enemy=target_enemy or EnemyId("enemy:target"),
        element=element,
        calculated_buildup=_value(buildup),
    )


def _application(
    buildup: float | Unresolved,
    *,
    contributor: CharacterId | None = None,
    element: Element = Element.FIRE,
    target_enemy: EnemyId | None = None,
    anomaly_effect_strength: float | Unresolved = 1000.0,
    impact_strength: float | Unresolved = 100.0,
    occurred_at: float = 1.0,
) -> AnomalyBuildupApplicationContext:
    return AnomalyBuildupApplicationContext(
        event=_event(
            buildup,
            contributor=contributor,
            element=element,
            target_enemy=target_enemy,
            occurred_at=occurred_at,
        ),
        anomaly_effect_strength=_value(anomaly_effect_strength),
        impact_strength=_value(impact_strength),
    )


def _trigger_snapshot(
    *,
    record_id: str = "anomaly:record",
) -> AnomalyTriggerSnapshot:
    return AnomalyTriggerSnapshot(
        record_id=AnomalyRecordId(record_id),
        anomaly_damage_bonus_region=Resolved(1.2),
        crit_capability=NoAnomalyCrit(),
        duration=Resolved(10.0),
    )


def _gauge(
    *,
    capacity: float = 100.0,
    element: Element = Element.FIRE,
    target_enemy: EnemyId | None = None,
) -> AnomalyGauge:
    return AnomalyGauge(
        target_enemy=target_enemy or EnemyId("enemy:target"),
        element=element,
        capacity=capacity,
    )


def test_partial_buildup_writes_contribution_without_triggering_record() -> None:
    gauge = _gauge()
    application = apply_anomaly_buildup(
        gauge,
        _application(40.0),
        _trigger_snapshot(),
    )

    assert application.gauge_before is gauge
    assert application.gauge_after.current_buildup == 40.0
    assert application.contribution is not None
    assert application.contribution.actual_written_buildup == 40.0
    assert application.gauge_after.contributions == (application.contribution,)
    assert application.triggered_record is None
    assert application.discarded_buildup == 0.0


def test_exact_fill_creates_record_and_resets_gauge() -> None:
    first = apply_anomaly_buildup(
        _gauge(),
        _application(40.0),
        _trigger_snapshot(),
    )
    second = apply_anomaly_buildup(
        first.gauge_after,
        _application(60.0, occurred_at=2.0),
        _trigger_snapshot(),
    )

    assert second.contribution is not None
    assert second.contribution.actual_written_buildup == 60.0
    assert second.triggered_record is not None
    assert second.gauge_after.current_buildup == 0.0
    assert second.gauge_after.contributions == ()
    assert second.discarded_buildup == 0.0


def test_overflow_is_clipped_and_not_carried_to_next_gauge() -> None:
    first = apply_anomaly_buildup(
        _gauge(),
        _application(90.0, anomaly_effect_strength=1000.0),
        _trigger_snapshot(),
    )
    second = apply_anomaly_buildup(
        first.gauge_after,
        _application(
            50.0,
            anomaly_effect_strength=2000.0,
            occurred_at=2.0,
        ),
        _trigger_snapshot(),
    )

    assert second.contribution is not None
    assert second.contribution.actual_written_buildup == 10.0
    assert second.discarded_buildup == 40.0
    assert second.gauge_after.current_buildup == 0.0
    assert second.gauge_after.contributions == ()
    assert second.triggered_record is not None
    assert second.triggered_record.weighted_anomaly_effect_strength == Resolved(1100.0)


def test_theoretical_50_writes_20_and_discards_30_when_gauge_is_at_80() -> None:
    first = apply_anomaly_buildup(
        _gauge(),
        _application(80.0),
        _trigger_snapshot(),
    )
    second = apply_anomaly_buildup(
        first.gauge_after,
        _application(50.0, occurred_at=2.0),
        _trigger_snapshot(),
    )

    assert second.contribution is not None
    assert second.contribution.actual_written_buildup == 20.0
    assert second.discarded_buildup == 30.0


def test_record_weights_effect_and_impact_by_actual_written_buildup() -> None:
    character_a = CharacterId("character:a")
    character_b = CharacterId("character:b")
    first = apply_anomaly_buildup(
        _gauge(),
        _application(
            30.0,
            contributor=character_a,
            anomaly_effect_strength=1000.0,
            impact_strength=100.0,
        ),
        _trigger_snapshot(),
    )
    second = apply_anomaly_buildup(
        first.gauge_after,
        _application(
            70.0,
            contributor=character_b,
            anomaly_effect_strength=2000.0,
            impact_strength=200.0,
            occurred_at=2.0,
        ),
        _trigger_snapshot(),
    )
    record = second.triggered_record

    assert record is not None
    assert record.weighted_anomaly_effect_strength == Resolved(1700.0)
    assert record.weighted_impact_strength == Resolved(170.0)
    assert record.contributors == (character_a, character_b)
    assert record.anomaly_triggerer == character_b
    assert tuple(item.actual_written_buildup for item in record.contributions) == (
        30.0,
        70.0,
    )


def test_same_character_can_contribute_at_multiple_snapshot_strengths() -> None:
    contributor = CharacterId("character:changing-state")
    first = apply_anomaly_buildup(
        _gauge(),
        _application(
            50.0,
            contributor=contributor,
            anomaly_effect_strength=1000.0,
            impact_strength=100.0,
        ),
        _trigger_snapshot(),
    )
    second = apply_anomaly_buildup(
        first.gauge_after,
        _application(
            50.0,
            contributor=contributor,
            anomaly_effect_strength=2000.0,
            impact_strength=300.0,
            occurred_at=2.0,
        ),
        _trigger_snapshot(),
    )
    record = second.triggered_record

    assert record is not None
    assert record.contributors == (contributor,)
    assert len(record.contributions) == 2
    assert record.weighted_anomaly_effect_strength == Resolved(1500.0)
    assert record.weighted_impact_strength == Resolved(200.0)


def test_record_uses_trigger_snapshot_and_final_event_identity() -> None:
    triggerer = CharacterId("character:triggerer")
    trigger_snapshot = _trigger_snapshot(record_id="anomaly:snapshot-record")
    application = apply_anomaly_buildup(
        _gauge(element=Element.ICE),
        _application(
            100.0,
            contributor=triggerer,
            element=Element.ICE,
            occurred_at=9.0,
        ),
        trigger_snapshot,
    )
    record = application.triggered_record

    assert record is not None
    assert record.record_id == AnomalyRecordId("anomaly:snapshot-record")
    assert record.element is Element.ICE
    assert record.damage_kind is AttributeAnomalyDamageKind.SHATTER
    assert record.state_kind is AttributeAnomalyStateKind.FROSTBITE
    assert record.anomaly_triggerer == triggerer
    assert record.triggered_at == 9.0
    assert record.anomaly_damage_bonus_region == Resolved(1.2)
    assert record.duration == Resolved(10.0)
    assert record.crit_capability is trigger_snapshot.crit_capability


def test_zero_buildup_does_not_create_contribution() -> None:
    gauge = _gauge()
    application = apply_anomaly_buildup(
        gauge,
        _application(0.0),
        _trigger_snapshot(),
    )

    assert application.gauge_after is gauge
    assert application.contribution is None
    assert application.triggered_record is None


def test_unresolved_buildup_does_not_mutate_gauge() -> None:
    gauge = _gauge()
    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="buildup value is unknown",
    )
    application = apply_anomaly_buildup(
        gauge,
        _application(unresolved),
        _trigger_snapshot(),
    )

    assert application.gauge_after is gauge
    assert application.contribution is None
    assert application.triggered_record is None
    assert application.unresolved == (unresolved,)


def test_unresolved_strength_is_preserved_in_completed_record() -> None:
    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_DATA,
        notes="effect strength snapshot is unknown",
    )
    first = apply_anomaly_buildup(
        _gauge(),
        _application(50.0),
        _trigger_snapshot(),
    )
    second = apply_anomaly_buildup(
        first.gauge_after,
        _application(
            50.0,
            anomaly_effect_strength=unresolved,
            impact_strength=200.0,
            occurred_at=2.0,
        ),
        _trigger_snapshot(),
    )
    record = second.triggered_record

    assert record is not None
    assert isinstance(record.weighted_anomaly_effect_strength, Unresolved)
    assert record.weighted_impact_strength == Resolved(150.0)


def test_event_target_and_element_must_match_gauge() -> None:
    with pytest.raises(ValueError, match="target"):
        apply_anomaly_buildup(
            _gauge(),
            _application(10.0, target_enemy=EnemyId("enemy:other")),
            _trigger_snapshot(),
        )
    with pytest.raises(ValueError, match="element"):
        apply_anomaly_buildup(
            _gauge(),
            _application(10.0, element=Element.ICE),
            _trigger_snapshot(),
        )


def test_luminance_cannot_have_ordinary_anomaly_gauge() -> None:
    with pytest.raises(ValueError, match="luminance"):
        _gauge(element=Element.LUMINANCE)


@pytest.mark.parametrize("capacity", (float("nan"), float("inf"), 0.0, -1.0))
def test_gauge_capacity_must_be_finite_and_positive(capacity: float) -> None:
    with pytest.raises(ValueError, match="capacity"):
        _gauge(capacity=capacity)


@pytest.mark.parametrize(
    "current_buildup",
    (float("nan"), float("inf"), -1.0, 100.0, 101.0),
)
def test_current_buildup_must_be_inside_unfilled_gauge(
    current_buildup: float,
) -> None:
    with pytest.raises(ValueError, match="within"):
        AnomalyGauge(
            target_enemy=EnemyId("enemy:target"),
            element=Element.FIRE,
            capacity=100.0,
            current_buildup=current_buildup,
        )


def test_current_buildup_must_equal_contribution_total() -> None:
    contribution = AnomalyContribution(
        contributor=CharacterId("character:a"),
        actual_written_buildup=10.0,
        anomaly_effect_strength=Resolved(1000.0),
        impact_strength=Resolved(100.0),
        occurred_at=1.0,
    )

    with pytest.raises(ValueError, match="must equal"):
        AnomalyGauge(
            target_enemy=EnemyId("enemy:target"),
            element=Element.FIRE,
            capacity=100.0,
            current_buildup=5.0,
            contributions=(contribution,),
        )


def test_record_builder_rejects_incomplete_contribution_history() -> None:
    application_context = _application(10.0)
    event = application_context.event
    contribution = AnomalyContribution(
        contributor=event.contributor,
        actual_written_buildup=10.0,
        anomaly_effect_strength=application_context.anomaly_effect_strength,
        impact_strength=application_context.impact_strength,
        occurred_at=event.metadata.occurred_at,
    )

    with pytest.raises(ValueError, match="completed gauge"):
        build_anomaly_record(
            _gauge(),
            event,
            _trigger_snapshot(),
            (contribution,),
        )


@pytest.mark.parametrize("buildup", (float("nan"), float("inf"), -1.0))
def test_resolved_event_buildup_must_be_finite_and_non_negative(
    buildup: float,
) -> None:
    with pytest.raises(ValueError, match="finite and non-negative"):
        _event(buildup)


def test_gauge_and_application_are_frozen() -> None:
    gauge = _gauge()
    application_context = _application(10.0)
    application = apply_anomaly_buildup(
        gauge,
        application_context,
        _trigger_snapshot(),
    )

    with pytest.raises(FrozenInstanceError):
        gauge.current_buildup = 10.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        application.discarded_buildup = 1.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        application_context.impact_strength = Resolved(1.0)  # type: ignore[misc]


def test_anomaly_gauge_modules_do_not_cross_future_boundaries() -> None:
    root = Path(__file__).parents[2]
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            root / "core" / "types" / "anomaly_gauge.py",
            root / "core" / "calculation" / "anomaly" / "gauge.py",
            root / "core" / "calculation" / "anomaly" / "record.py",
        )
    )

    assert "DamageCalculator" not in sources
    assert "EffectMatcher" not in sources
    assert "BattleState" not in sources
    assert "Disorder" not in sources
    assert "Discharge" not in sources
    assert "Turbulence" not in sources
    assert "LuminanceDamage" not in sources
