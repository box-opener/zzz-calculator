"""A battle snapshot consumed by future matchers and pure calculators."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .anomaly_record import AnomalyRecord
from .character import Character, CharacterStats
from .common import (
    AnomalyRecordId,
    BattleStateId,
    BattleTime,
    CharacterId,
    EnemyId,
    ResourceId,
    Resolvable,
)
from .enemy import Enemy
from .enums import Element, FieldPosition, OperationState, ResourceKind
from .state import State


@dataclass(frozen=True, slots=True)
class CharacterCombatState:
    current_stats: CharacterStats
    current_hp: Resolvable[float]
    field_position: FieldPosition
    operation_state: OperationState
    resources: Mapping[ResourceKind | ResourceId, Resolvable[float]] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class EnemyCombatState:
    current_daze: Resolvable[float]
    anomaly_buildup: Mapping[Element, Resolvable[float]] = field(default_factory=dict)
    current_anomaly_record: AnomalyRecordId | None = None


@dataclass(frozen=True, slots=True)
class BattleState:
    state_id: BattleStateId
    time: BattleTime
    characters: Mapping[CharacterId, Character]
    character_combat: Mapping[CharacterId, CharacterCombatState]
    enemies: Mapping[EnemyId, Enemy]
    enemy_combat: Mapping[EnemyId, EnemyCombatState]
    states: tuple[State, ...] = ()
    anomaly_records: tuple[AnomalyRecord, ...] = ()

    def __post_init__(self) -> None:
        if not set(self.character_combat).issubset(self.characters):
            raise ValueError("character combat state references an unknown character")
        if not set(self.enemy_combat).issubset(self.enemies):
            raise ValueError("enemy combat state references an unknown enemy")
        operated = [
            state
            for state in self.character_combat.values()
            if state.operation_state is OperationState.OPERATED
        ]
        if len(operated) > 1:
            raise ValueError("at most one character can be in operation state")
        for character_state in self.character_combat.values():
            if (
                character_state.field_position is FieldPosition.BACK
                and character_state.operation_state is OperationState.OPERATED
            ):
                raise ValueError("a back-field character cannot be the operated character")
        records = {record.record_id: record for record in self.anomaly_records}
        for enemy_id, enemy_state in self.enemy_combat.items():
            record_id = enemy_state.current_anomaly_record
            if record_id is None:
                continue
            record = records.get(record_id)
            if record is None:
                raise ValueError("current anomaly state references an unknown record")
            if record.target_enemy != enemy_id:
                raise ValueError("current anomaly record belongs to a different enemy")
