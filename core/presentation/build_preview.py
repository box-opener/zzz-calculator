"""Stable presentation contract for live equipment-build previews."""

from __future__ import annotations

from dataclasses import dataclass
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


__all__ = [
    "BuildPreviewView",
    "DriveDiscPreviewView",
    "DriveDiscStatPreviewView",
]
