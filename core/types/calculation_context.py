"""Immutable inputs assembled before a pure calculator is invoked."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .anomaly_record import AnomalyRecord
from .calculation_node import CalculationNode
from .character import CharacterStats
from .common import (
    BattleStateId,
    CharacterId,
    EffectId,
    EnemyId,
    Ratio,
    Resolvable,
)
from .damage_event import DamageEvent
from .enums import EffectOperation, Element, SnapshotRule
from .vulnerability import StandardVulnerabilityPolicy, VulnerabilitySettlementPolicy


@dataclass(frozen=True, slots=True)
class CharacterSnapshot:
    character_id: CharacterId
    level: int
    settlement_stats: CharacterStats


@dataclass(frozen=True, slots=True)
class InitialCharacterSnapshot:
    """The immutable initial panel used by build-derived value sources."""

    character_id: CharacterId
    level: int
    initial_stats: CharacterStats


@dataclass(frozen=True, slots=True)
class EnemySnapshot:
    enemy_id: EnemyId
    level: int
    initial_defense: Resolvable[float]
    damage_resistance: Mapping[Element, Resolvable[Ratio]]
    anomaly_buildup_resistance: Mapping[Element, Resolvable[Ratio]]
    daze_resistance: Resolvable[Ratio]
    damage_reduction: Resolvable[Ratio]
    is_stunned: bool = False


@dataclass(frozen=True, slots=True)
class Modifier:
    effect_id: EffectId
    modifier_path: CalculationNode
    operation: EffectOperation
    value: Resolvable[float]
    snapshot_rule: SnapshotRule


@dataclass(frozen=True, slots=True)
class CalculationContext:
    """The complete, pre-resolved environment accepted by a calculator."""

    event: DamageEvent
    battle_state_id: BattleStateId
    character_snapshots: tuple[CharacterSnapshot, ...]
    target_snapshot: EnemySnapshot
    modifiers: tuple[Modifier, ...] = ()
    history_records: tuple[AnomalyRecord, ...] = ()
    vulnerability_policy: VulnerabilitySettlementPolicy = field(
        default_factory=StandardVulnerabilityPolicy
    )
