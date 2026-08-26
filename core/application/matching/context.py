"""Immutable facts consumed by the static Effect matcher."""

from dataclasses import dataclass

from core.types import (
    AnomalyRecord,
    BattleEventKind,
    CalculationContext,
    CharacterId,
    CharacterRole,
    DamageEvent,
    EffectId,
    EnemyId,
    FieldPosition,
    MoveId,
    OperationState,
    StateId,
)

from ..scenario import CalculationScenario


@dataclass(frozen=True, slots=True)
class CharacterMatchProfile:
    character_id: CharacterId
    role: CharacterRole
    states: frozenset[StateId] = frozenset()
    field_position: FieldPosition | None = None
    operation_state: OperationState | None = None


@dataclass(frozen=True, slots=True)
class EnemyMatchProfile:
    enemy_id: EnemyId
    states: frozenset[StateId] = frozenset()


@dataclass(frozen=True, slots=True)
class ScenarioTriggerFactView:
    effect_id: EffectId
    event_kind: BattleEventKind
    move_id: MoveId | None
    actor: CharacterId | None


@dataclass(frozen=True, slots=True)
class EffectMatchContext:
    """Separates the settlement event from scenario trigger facts."""

    current_event: DamageEvent
    calculation_context: CalculationContext
    scenario: CalculationScenario
    current_operator: CharacterId
    team: tuple[CharacterMatchProfile, ...]
    target: EnemyMatchProfile

    def __post_init__(self) -> None:
        if self.calculation_context.event != self.current_event:
            raise ValueError("calculation context must contain current_event")
        if (
            self.calculation_context.target_snapshot.enemy_id
            != self.target.enemy_id
        ):
            raise ValueError("calculation context target must match target profile")
        if (
            self.calculation_context.battle_state_id
            != self.current_event.metadata.battle_state_id
        ):
            raise ValueError("calculation context battle state must match event")
        if self.current_event.metadata.target_enemy != self.target.enemy_id:
            raise ValueError("target profile must match current event target")
        character_ids = tuple(item.character_id for item in self.team)
        if len(set(character_ids)) != len(character_ids):
            raise ValueError("team character IDs must be unique")
        if self.current_operator not in set(character_ids):
            raise ValueError("current_operator must be a team member")

    @property
    def history_records(self) -> tuple[AnomalyRecord, ...]:
        return self.calculation_context.history_records

    @property
    def trigger_facts(self) -> tuple[ScenarioTriggerFactView, ...]:
        return tuple(
            ScenarioTriggerFactView(
                effect_id=item.effect_id,
                event_kind=item.event_kind,
                move_id=item.move_id,
                actor=item.actor,
            )
            for item in self.scenario.trigger_facts
        )

    def character(self, character_id: CharacterId) -> CharacterMatchProfile | None:
        return next(
            (item for item in self.team if item.character_id == character_id),
            None,
        )
