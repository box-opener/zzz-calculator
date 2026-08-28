"""Presentation-level request inputs; no arbitrary Modifier objects allowed."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import math


@dataclass(frozen=True, slots=True)
class CharacterBuildInput:
    character_id: str
    level: int
    out_of_combat_stats: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.character_id.strip():
            raise ValueError("character build character_id is required")
        if not 1 <= self.level <= 60:
            raise ValueError("character build level must be between 1 and 60")
        for key, value in self.out_of_combat_stats.items():
            if key == "element_damage_bonus":
                if not isinstance(value, Mapping):
                    raise ValueError("element_damage_bonus must be an object")
                values = value.values()
            else:
                values = (value,)
            if any(
                not isinstance(item, (int, float)) or not math.isfinite(float(item))
                for item in values
            ):
                raise ValueError("character build stats must be finite numbers")


@dataclass(frozen=True, slots=True)
class EnemyInput:
    enemy_id: str
    level: int
    initial_defense: float
    damage_resistance: Mapping[str, float] = field(default_factory=dict)
    damage_reduction: float = 0.0
    stun_vulnerability_bonus: float = 0.0
    is_stunned: bool = False

    def __post_init__(self) -> None:
        if not self.enemy_id.strip():
            raise ValueError("enemy_id is required")
        if not 1 <= self.level <= 80:
            raise ValueError("enemy level must be between 1 and 80")
        if self.initial_defense < 0:
            raise ValueError("initial_defense must be non-negative")
        numeric_values = (*self.damage_resistance.values(), self.damage_reduction, self.stun_vulnerability_bonus)
        if any(not math.isfinite(float(value)) for value in numeric_values):
            raise ValueError("enemy values must be finite numbers")


@dataclass(frozen=True, slots=True)
class SelectedTriggerInput:
    input_id: str
    actor_id: str | None


@dataclass(frozen=True, slots=True)
class MoveCalculationViewRequest:
    primary_character_id: str
    supporting_character_ids: tuple[str, ...]
    move_entry_id: str
    character_builds: tuple[CharacterBuildInput, ...]
    enemy: EnemyInput
    selected_condition_values: Mapping[str, bool | None] = field(default_factory=dict)
    selected_parameter_values: Mapping[str, int | None] = field(default_factory=dict)
    enabled_rule_item_ids: frozenset[str] = frozenset()
    selected_trigger_inputs: tuple[SelectedTriggerInput, ...] = ()
    rule_stack_counts: Mapping[str, int] = field(default_factory=dict)


__all__ = [
    "CharacterBuildInput",
    "EnemyInput",
    "MoveCalculationViewRequest",
    "SelectedTriggerInput",
]
