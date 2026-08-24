"""Enemy base data; mutable combat values belong to BattleState."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .common import EnemyId, Ratio, Resolvable
from .enums import Element


@dataclass(frozen=True, slots=True)
class Enemy:
    enemy_id: EnemyId
    name: str
    level: int
    initial_defense: Resolvable[float]
    resistance: Mapping[Element, Resolvable[Ratio]] = field(default_factory=dict)
    daze_capacity: Resolvable[float] | None = None
    daze_resistance: Resolvable[Ratio] | None = None
    anomaly_buildup_resistance: Mapping[Element, Resolvable[Ratio]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 80:
            raise ValueError("enemy level must be between 1 and 80")
