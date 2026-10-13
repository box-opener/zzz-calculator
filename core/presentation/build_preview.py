"""Stable presentation contract for live equipment-build previews."""

from __future__ import annotations

from dataclasses import dataclass

from core.calculation import PenetrationForceInput, calculate_penetration_force
from core.application.build import ResolvedBuild
from core.types import BuildContributionLayer, CharacterSnapshot, CharacterStat, Resolved

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
class BuildStatBreakdownView:
    white_value: float | None
    additional_value: float | None


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
    stat_breakdown: dict[str, BuildStatBreakdownView]
    provenance: tuple[BuildContributionView, ...]
    drive_discs: tuple[DriveDiscPreviewView, ...]
    set_counts: tuple[dict[str, object], ...]
    diagnostics: tuple[DiagnosticView, ...]
    complete: bool


def out_of_combat_stat_breakdown(build: ResolvedBuild) -> dict[str, BuildStatBreakdownView]:
    """Present white values and additions from the same authoritative Build.

    White-value contributions (including W-Engine base attack/defense) belong
    to the percentage baseline. All other additions are final minus white.
    Missing values stay missing, even when the rest of the build is known.
    """
    result = {}
    for stat in (
        CharacterStat.HP, CharacterStat.ATTACK, CharacterStat.DEFENSE,
        CharacterStat.ANOMALY_MASTERY, CharacterStat.ENERGY_REGEN,
    ):
        key = stat.value.replace("-", "_")
        base = getattr(build.base_stats, key, None)
        white = float(base.value) if isinstance(base, Resolved) else None
        for trace in build.provenance:
            if trace.stat is stat and trace.layer is BuildContributionLayer.WHITE_VALUE:
                if white is not None and isinstance(trace.applied_value, Resolved):
                    white += float(trace.applied_value.value)
                else:
                    white = None
        total = getattr(build.out_of_combat_stats, key)
        additional = float(total.value) - white if isinstance(total, Resolved) and white is not None else None
        result[key] = BuildStatBreakdownView(white, additional)
    return result


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
    "BuildStatBreakdownView",
    "DriveDiscPreviewView",
    "DriveDiscStatPreviewView",
    "out_of_combat_penetration_force",
    "out_of_combat_stat_breakdown",
]
