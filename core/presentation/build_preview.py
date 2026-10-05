"""Stable presentation contract for live equipment-build previews."""

from __future__ import annotations

from dataclasses import dataclass

from core.calculation import PenetrationForceInput, calculate_penetration_force
from core.types import CharacterSnapshot, Resolved

from .calculation import BuildContributionView
from .diagnostics import DiagnosticView


@dataclass(frozen=True, slots=True)
class DriveDiscStatPreviewView:
    """One configured main/sub stat with display-ready roll metadata."""

    stat_key: str
    label: str
    value_per_roll: float
    display_value_per_roll: str
    roll_count: int
    total_value: float
    display_total_value: str


@dataclass(frozen=True, slots=True)
class DriveDiscPreviewView:
    slot: int
    set_id: str
    set_name: str
    main_stat: DriveDiscStatPreviewView | None
    substats: tuple[DriveDiscStatPreviewView, ...]
    total_rolls: int
    complete: bool


@dataclass(frozen=True, slots=True)
class BuildPreviewView:
    """Authoritative live panel and provenance returned by Build Assembly."""

    schema_version: str
    character_id: str
    display_name: str
    level: int
    build_mode: str
    base_stats: dict[str, object]
    out_of_combat_stats: dict[str, object]
    provenance: tuple[BuildContributionView, ...]
    drive_discs: tuple[DriveDiscPreviewView, ...]
    set_counts: tuple[dict[str, object], ...]
    diagnostics: tuple[DiagnosticView, ...]
    complete: bool


def out_of_combat_penetration_force(snapshot: CharacterSnapshot) -> float | None:
    """Return Force from resolved out-of-combat ATK/HP, preserving missing data."""

    stats = snapshot.settlement_stats
    if not isinstance(stats.attack, Resolved) or not isinstance(stats.hp, Resolved):
        return None
    result = calculate_penetration_force(
        PenetrationForceInput(
            current_attack=stats.attack.value,
            current_max_hp=stats.hp.value,
        )
    )
    return (
        float(result.value)
        if isinstance(result.value, (int, float)) and not isinstance(result.value, bool)
        else None
    )


__all__ = [
    "BuildPreviewView",
    "DriveDiscPreviewView",
    "DriveDiscStatPreviewView",
    "out_of_combat_penetration_force",
]
