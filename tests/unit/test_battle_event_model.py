from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.types import (
    AnomalyBuildupEvent,
    AnomalyBuildupOutcome,
    BattleEventId,
    BattleEventKind,
    BattleEventMetadata,
    BattleEventResult,
    BattleOutcomeId,
    BattleStateId,
    CharacterId,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DamageEventOutcome,
    DirectDamageEvent,
    DazeEvent,
    DazeOutcome,
    Element,
    EnemyId,
    EventCreationOutcome,
    EventCreationResult,
    EventTemplateId,
    FixedMultiplier,
    HitId,
    MoveId,
    OutcomeDependency,
    Resolved,
    ResourceChangeOutcome,
    ResourceKind,
    SkillGroup,
    SkillHitEvent,
    StandardCritRule,
    StateChangeAction,
    StateChangeOutcome,
    StateChangeResult,
    StateId,
    Unresolved,
    UnresolvedReason,
)


def _metadata(event_id: str) -> BattleEventMetadata:
    return BattleEventMetadata(
        event_id=BattleEventId(event_id),
        battle_state_id=BattleStateId("battle:1"),
        occurred_at=1.0,
    )


def _skill_hit() -> SkillHitEvent:
    return SkillHitEvent(
        metadata=_metadata("event:skill-hit"),
        actor=CharacterId("character:actor"),
        target_enemy=EnemyId("enemy:target"),
        element=Element.FIRE,
        skill_group=SkillGroup.BASIC_ATTACK,
        move_id=MoveId("move:basic-1"),
        hit_id=HitId("hit:1"),
    )


def _damage_outcome(outcome_id: str = "outcome:damage") -> DamageEventOutcome:
    dealer = CharacterId("character:actor")
    event = DirectDamageEvent(
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
    return DamageEventOutcome(
        outcome_id=BattleOutcomeId(outcome_id),
        event=event,
    )


def _buildup_outcome(
    outcome_id: str = "outcome:buildup",
) -> AnomalyBuildupOutcome:
    event = AnomalyBuildupEvent(
        metadata=_metadata("event:buildup"),
        contributor=CharacterId("character:actor"),
        target_enemy=EnemyId("enemy:target"),
        element=Element.FIRE,
        calculated_buildup=Resolved(50.0),
        anomaly_effect_strength=Resolved(1000.0),
        impact_strength=Resolved(100.0),
    )
    return AnomalyBuildupOutcome(
        outcome_id=BattleOutcomeId(outcome_id),
        event=event,
    )


def _daze_outcome(outcome_id: str = "outcome:daze") -> DazeOutcome:
    event = DazeEvent(
        metadata=_metadata("event:daze"),
        daze_source=CharacterId("character:actor"),
        target_enemy=EnemyId("enemy:target"),
        calculated_daze=Resolved(25.0),
    )
    return DazeOutcome(
        outcome_id=BattleOutcomeId(outcome_id),
        event=event,
    )


def test_skill_hit_event_is_frozen() -> None:
    event = _skill_hit()

    with pytest.raises(FrozenInstanceError):
        event.actor = CharacterId("character:other")  # type: ignore[misc]


def test_one_hit_can_produce_multiple_independent_outcomes() -> None:
    resource = ResourceChangeOutcome(
        outcome_id=BattleOutcomeId("outcome:resource"),
        target_character=CharacterId("character:actor"),
        resource=ResourceKind.ENERGY,
        delta=Resolved(5.0),
    )
    result = BattleEventResult(
        source_event_id=_skill_hit().metadata.event_id,
        outcomes=(
            _damage_outcome(),
            _buildup_outcome(),
            _daze_outcome(),
            resource,
        ),
    )

    assert len(result.outcomes) == 4
    assert result.dependencies == ()
    assert isinstance(result.outcomes[0], DamageEventOutcome)
    assert isinstance(result.outcomes[1], AnomalyBuildupOutcome)
    assert isinstance(result.outcomes[2], DazeOutcome)
    assert isinstance(result.outcomes[3], ResourceChangeOutcome)


def test_damage_outcome_contains_damage_event_not_calculation_result() -> None:
    outcome = _damage_outcome()

    assert isinstance(outcome.event, DirectDamageEvent)
    assert not hasattr(outcome, "calculation_result")
    assert not hasattr(outcome, "value")


def test_buildup_outcome_precedes_actual_contribution_generation() -> None:
    outcome = _buildup_outcome()

    assert isinstance(outcome.event, AnomalyBuildupEvent)
    assert outcome.event.calculated_buildup == Resolved(50.0)
    assert outcome.event.anomaly_effect_strength == Resolved(1000.0)
    assert outcome.event.impact_strength == Resolved(100.0)
    assert not hasattr(outcome.event, "actual_written_buildup")
    assert not hasattr(outcome, "contribution")


def test_luminance_cannot_create_ordinary_anomaly_buildup_event() -> None:
    with pytest.raises(ValueError, match="luminance"):
        AnomalyBuildupEvent(
            metadata=_metadata("event:luminance-buildup"),
            contributor=CharacterId("character:luminance"),
            target_enemy=EnemyId("enemy:target"),
            element=Element.LUMINANCE,
            calculated_buildup=Resolved(1.0),
            anomaly_effect_strength=Resolved(1000.0),
            impact_strength=Resolved(100.0),
        )


def test_outcome_ids_must_be_unique() -> None:
    with pytest.raises(ValueError, match="IDs must be unique"):
        BattleEventResult(
            source_event_id=BattleEventId("event:source"),
            outcomes=(
                _damage_outcome("outcome:duplicate"),
                _buildup_outcome("outcome:duplicate"),
            ),
        )


def test_dependency_must_reference_known_outcomes() -> None:
    with pytest.raises(ValueError, match="unknown outcome"):
        BattleEventResult(
            source_event_id=BattleEventId("event:source"),
            outcomes=(_damage_outcome(),),
            dependencies=(
                OutcomeDependency(
                    before=BattleOutcomeId("outcome:damage"),
                    after=BattleOutcomeId("outcome:missing"),
                ),
            ),
        )


def test_dependency_cannot_reference_itself() -> None:
    with pytest.raises(ValueError, match="cannot reference itself"):
        BattleEventResult(
            source_event_id=BattleEventId("event:source"),
            outcomes=(_damage_outcome(),),
            dependencies=(
                OutcomeDependency(
                    before=BattleOutcomeId("outcome:damage"),
                    after=BattleOutcomeId("outcome:damage"),
                ),
            ),
        )


def test_dependency_graph_cannot_contain_a_cycle() -> None:
    damage = _damage_outcome()
    buildup = _buildup_outcome()
    daze = _daze_outcome()

    with pytest.raises(ValueError, match="cycle"):
        BattleEventResult(
            source_event_id=BattleEventId("event:source"),
            outcomes=(damage, buildup, daze),
            dependencies=(
                OutcomeDependency(damage.outcome_id, buildup.outcome_id),
                OutcomeDependency(buildup.outcome_id, daze.outcome_id),
                OutcomeDependency(daze.outcome_id, damage.outcome_id),
            ),
        )


def test_tuple_storage_order_does_not_create_execution_dependencies() -> None:
    damage = _damage_outcome()
    daze = _daze_outcome()
    forward = BattleEventResult(
        source_event_id=BattleEventId("event:source"),
        outcomes=(damage, daze),
    )
    reversed_storage = BattleEventResult(
        source_event_id=BattleEventId("event:source"),
        outcomes=(daze, damage),
    )

    assert forward.dependencies == reversed_storage.dependencies == ()
    assert {outcome.outcome_id for outcome in forward.outcomes} == {
        outcome.outcome_id for outcome in reversed_storage.outcomes
    }


def test_explicit_dependency_can_order_state_change_before_damage() -> None:
    state_change = StateChangeOutcome(
        outcome_id=BattleOutcomeId("outcome:state-change"),
        change=StateChangeResult(
            action=StateChangeAction.REMOVE,
            state_id=StateId("state:old-anomaly"),
        ),
    )
    damage = _damage_outcome()
    dependency = OutcomeDependency(
        before=state_change.outcome_id,
        after=damage.outcome_id,
    )
    result = BattleEventResult(
        source_event_id=BattleEventId("event:source"),
        outcomes=(damage, state_change),
        dependencies=(dependency,),
    )

    assert result.dependencies == (dependency,)


def test_unresolved_ordering_is_preserved_structurally() -> None:
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_ORDERING,
        notes="the specification does not determine outcome order",
    )
    result = BattleEventResult(
        source_event_id=BattleEventId("event:source"),
        outcomes=(_damage_outcome(), _daze_outcome()),
        unresolved_ordering=unresolved,
    )

    assert result.unresolved_ordering is unresolved


def test_state_and_event_creation_outcomes_reuse_existing_structures() -> None:
    state_change = StateChangeOutcome(
        outcome_id=BattleOutcomeId("outcome:state"),
        change=StateChangeResult(
            action=StateChangeAction.REFRESH,
            state_id=StateId("state:buff"),
        ),
    )
    event_creation = EventCreationOutcome(
        outcome_id=BattleOutcomeId("outcome:event"),
        creation=EventCreationResult(
            event_kind=BattleEventKind.RESOURCE_CHANGE,
            event_template_id=EventTemplateId("template:resource-change"),
        ),
    )
    result = BattleEventResult(
        source_event_id=BattleEventId("event:source"),
        outcomes=(state_change, event_creation),
    )

    assert result.outcomes == (state_change, event_creation)


def test_battle_event_model_has_no_calculation_or_history_shortcut() -> None:
    source = (
        Path(__file__).parents[2] / "core" / "types" / "battle_event.py"
    ).read_text(encoding="utf-8")

    assert "core.calculation" not in source
    assert "CalculationResult" not in source
    assert "AnomalyContribution" not in source
    assert "Dispatcher" not in source
    assert "Resolver" not in source
