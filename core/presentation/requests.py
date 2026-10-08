"""Presentation-level request inputs; no arbitrary Modifier objects allowed."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
import math

from core.types import (
    AnomalySourceChoice,
    BuildMode,
    EquippedDriveDisc,
    LuminanceSourceChoice,
)


@dataclass(frozen=True, slots=True)
class CharacterBuildInput:
    character_id: str
    level: int
    out_of_combat_stats: Mapping[str, object]
    build_mode: BuildMode = BuildMode.MANUAL_PANEL
    base_stats: Mapping[str, object] | None = None
    wengine_id: str | None = None
    wengine_level: int = 60
    wengine_refinement: int = 1
    drive_discs: tuple[EquippedDriveDisc, ...] = ()

    def __post_init__(self) -> None:
        if not self.character_id.strip():
            raise ValueError("character build character_id is required")
        if not 1 <= self.level <= 60:
            raise ValueError("character build level must be between 1 and 60")
        if not 1 <= self.wengine_level <= 60:
            raise ValueError("W-Engine level must be between 1 and 60")
        if not 1 <= self.wengine_refinement <= 5:
            raise ValueError("W-Engine refinement must be between 1 and 5")
        if self.build_mode is BuildMode.MANUAL_PANEL and (
            self.wengine_id is not None or self.drive_discs
        ):
            raise ValueError("manual panel build cannot define equipment")
        for key, value in self.out_of_combat_stats.items():
            values: Iterable[object]
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
        if self.base_stats is not None:
            for key, value in self.base_stats.items():
                base_values: Iterable[object]
                if key == "element_damage_bonus":
                    if not isinstance(value, Mapping):
                        raise ValueError("base element_damage_bonus must be an object")
                    base_values = value.values()
                else:
                    base_values = (value,)
                if any(
                    not isinstance(item, (int, float)) or not math.isfinite(float(item))
                    for item in base_values
                ):
                    raise ValueError("base character stats must be finite numbers")


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
        numeric_values = (
            *self.damage_resistance.values(),
            self.damage_reduction,
            self.stun_vulnerability_bonus,
        )
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
    luminance_source_slots: tuple[LuminanceSourceChoice, ...] = ()
    polarity_anomaly_source_choice: AnomalySourceChoice | None = None
    burnice_anomaly_source_choice: AnomalySourceChoice | None = None


__all__ = [
    "CharacterBuildInput",
    "EnemyInput",
    "MoveCalculationViewRequest",
    "SelectedTriggerInput",
]
