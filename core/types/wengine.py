"""Domain input for an equipped W-Engine."""

from __future__ import annotations

from dataclasses import dataclass

from .common import CharacterId, WEngineId
from .enums import (
    BASE_ELEMENT_BY_ELEMENT,
    CharacterRole,
    DamageTag,
    Element,
    SkillGroup,
)


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


@dataclass(frozen=True, slots=True)
class EquipmentOwnerCapabilities:
    """Reviewed static capabilities used for equipment eligibility.

    These are not a battle timeline.  They describe what an owner can ever
    produce in the currently compiled character definition, so a scenario
    checkbox cannot activate an impossible equipment effect.
    """

    character_id: CharacterId
    role: CharacterRole
    possible_elements: frozenset[Element] = frozenset()
    skill_groups: frozenset[SkillGroup] = frozenset()
    damage_tags: frozenset[DamageTag] = frozenset()
    mechanisms: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not str(self.character_id):
            raise ValueError("equipment owner character_id must not be empty")
        if any(not item.strip() for item in self.mechanisms):
            raise ValueError("equipment owner mechanism IDs must not be empty")

    def can_produce_element(self, element: Element) -> bool:
        base = BASE_ELEMENT_BY_ELEMENT.get(element, element)
        return any(
            BASE_ELEMENT_BY_ELEMENT.get(item, item) is base
            for item in self.possible_elements
        )

    def can_use_skill_group(self, skill_group: SkillGroup) -> bool:
        return skill_group in self.skill_groups

    def can_produce_tag(self, tag: DamageTag) -> bool:
        return tag in self.damage_tags

    def has_mechanism(self, mechanism: str) -> bool:
        return mechanism in self.mechanisms


__all__ = ["EquipmentOwnerCapabilities", "WEngineBuildInput"]
