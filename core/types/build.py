"""Build and equipment contracts shared by application assembly layers.

These types describe where an out-of-combat stat contribution belongs.  They
do not aggregate values or execute combat Effects; that work belongs to the
application Build Assembly layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math

from .character import CharacterStats
from .common import CharacterId, Resolvable, Resolved, Unresolved
from .enums import CharacterStat, Element


class BuildMode(StrEnum):
    """How a character's out-of-combat panel is supplied."""

    MANUAL_PANEL = "manual-panel"
    EQUIPMENT_BUILD = "equipment-build"


class BuildContributionLayer(StrEnum):
    """The static panel layers and manual-input provenance marker."""

    WHITE_VALUE = "white-value"
    OUT_OF_COMBAT_PERCENT = "out-of-combat-percent"
    OUT_OF_COMBAT_FLAT = "out-of-combat-flat"
    DIRECT_RATIO = "direct-ratio"
    MANUAL_PANEL = "manual-panel"


class BuildSourceType(StrEnum):
    CHARACTER = "character"
    WENGINE = "w-engine"
    DRIVE_DISC = "drive-disc"
    DRIVE_DISC_SET = "drive-disc-set"
    MANUAL_PANEL = "manual-panel"
    MANUAL_ADJUSTMENT = "manual-adjustment"


@dataclass(frozen=True, slots=True)
class BuildSource:
    """Stable provenance for one static panel contribution."""

    source_id: str
    source_type: BuildSourceType
    label: str

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("build source_id must not be empty")
        if not self.label.strip():
            raise ValueError("build source label must not be empty")


_WHITE_VALUE_STATS = frozenset(
    {
        # Stage18-1 explicitly models the W-Engine attack contribution as
        # white attack.  Other character white values are supplied by
        # CharacterBuildDefinition.base_stats, not by equipment contributions.
        CharacterStat.ATTACK,
    }
)

_OUT_OF_COMBAT_PERCENT_STATS = _WHITE_VALUE_STATS

_OUT_OF_COMBAT_FLAT_STATS = frozenset(
    {
        CharacterStat.HP,
        CharacterStat.ATTACK,
        CharacterStat.DEFENSE,
        CharacterStat.IMPACT,
        CharacterStat.ANOMALY_MASTERY,
        CharacterStat.ANOMALY_PROFICIENCY,
        CharacterStat.PENETRATION_FLAT,
        CharacterStat.ENERGY_REGEN,
    }
)

_DIRECT_RATIO_STATS = frozenset(
    {
        CharacterStat.CRIT_RATE,
        CharacterStat.CRIT_DAMAGE,
        CharacterStat.PENETRATION_RATE,
        CharacterStat.ELEMENT_DAMAGE_BONUS,
    }
)


@dataclass(frozen=True, slots=True)
class BuildStatContribution:
    """One typed static contribution to a character's out-of-combat panel."""

    contribution_id: str
    source: BuildSource
    stat: CharacterStat
    layer: BuildContributionLayer
    value: Resolvable[float]
    element: Element | None = None

    def __post_init__(self) -> None:
        if not self.contribution_id.strip():
            raise ValueError("build contribution_id must not be empty")
        if isinstance(self.value, Resolved):
            numeric_value = float(self.value.value)
            if not math.isfinite(numeric_value):
                raise ValueError("build contribution value must be finite")

        allowed_stats = {
            BuildContributionLayer.WHITE_VALUE: _WHITE_VALUE_STATS,
            BuildContributionLayer.OUT_OF_COMBAT_PERCENT: _OUT_OF_COMBAT_PERCENT_STATS,
            BuildContributionLayer.OUT_OF_COMBAT_FLAT: _OUT_OF_COMBAT_FLAT_STATS,
            BuildContributionLayer.DIRECT_RATIO: _DIRECT_RATIO_STATS,
        }.get(self.layer)
        if allowed_stats is None:
            raise ValueError("manual panel is not a build stat contribution layer")
        if self.stat not in allowed_stats:
            raise ValueError(
                f"{self.layer.value} does not support stat {self.stat.value}"
            )
        if self.stat is CharacterStat.ELEMENT_DAMAGE_BONUS:
            if self.element is None:
                raise ValueError("element damage contribution requires an element")
        elif self.element is not None:
            raise ValueError("element is only valid for element damage contributions")


@dataclass(frozen=True, slots=True)
class CharacterBuildDefinition:
    """Immutable input to Build Assembly.

    Equipment mode starts from a character-only panel and applies typed
    static contributions.  Manual mode bypasses aggregation and preserves the
    caller-provided panel as-is.
    """

    character_id: CharacterId
    level: int
    mode: BuildMode
    base_stats: CharacterStats | None = None
    contributions: tuple[BuildStatContribution, ...] = ()
    manual_panel_stats: CharacterStats | None = None

    def __post_init__(self) -> None:
        if not str(self.character_id):
            raise ValueError("character build character_id must not be empty")
        if not 1 <= self.level <= 60:
            raise ValueError("character build level must be between 1 and 60")
        ids = tuple(item.contribution_id for item in self.contributions)
        if len(set(ids)) != len(ids):
            raise ValueError("build contribution IDs must be unique")
        if self.mode is BuildMode.EQUIPMENT_BUILD:
            if self.base_stats is None:
                raise ValueError("equipment build requires base_stats")
            if self.manual_panel_stats is not None:
                raise ValueError("equipment build cannot define manual panel stats")
        elif self.mode is BuildMode.MANUAL_PANEL:
            if self.manual_panel_stats is None:
                raise ValueError("manual panel build requires manual_panel_stats")
            if self.base_stats is not None or self.contributions:
                raise ValueError(
                    "manual panel build cannot define equipment contributions"
                )


@dataclass(frozen=True, slots=True)
class BuildContributionTrace:
    """White-box trace for one contribution after validation."""

    contribution_id: str
    source: BuildSource
    stat: CharacterStat
    layer: BuildContributionLayer
    input_value: Resolvable[float]
    applied_value: Resolvable[float]
    element: Element | None = None


__all__ = [
    "BuildContributionLayer",
    "BuildContributionTrace",
    "BuildMode",
    "BuildSource",
    "BuildSourceType",
    "BuildStatContribution",
    "CharacterBuildDefinition",
]
