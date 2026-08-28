"""Domain input for an equipped W-Engine."""

from __future__ import annotations

from dataclasses import dataclass

from .common import CharacterId, WEngineId


@dataclass(frozen=True, slots=True)
class WEngineBuildInput:
    """One equipped W-Engine selection for a character build."""

    wengine_id: WEngineId
    equipped_character_id: CharacterId
    level: int = 60
    refinement: int = 1

    def __post_init__(self) -> None:
        if not str(self.wengine_id):
            raise ValueError("wengine_id must not be empty")
        if not str(self.equipped_character_id):
            raise ValueError("equipped_character_id must not be empty")
        if not 1 <= self.level <= 60:
            raise ValueError("W-Engine level must be between 1 and 60")
        if not 1 <= self.refinement <= 5:
            raise ValueError("W-Engine refinement must be between 1 and 5")


__all__ = ["WEngineBuildInput"]
