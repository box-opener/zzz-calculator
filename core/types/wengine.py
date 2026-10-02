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
class EquipmentDamageScope:
    """One reviewed element/skill/tag combination an owner can produce."""

    element: Element
    skill_group: SkillGroup
    damage_tags: frozenset[DamageTag]


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
    damage_scopes: frozenset[EquipmentDamageScope] | None = None

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

    def can_produce_damage_scope(
        self,
        *,
        element: Element | None,
        skill_groups: tuple[SkillGroup, ...],
        tags: tuple[DamageTag, ...],
    ) -> bool:
        if self.damage_scopes is None:
            return (
                (element is None or self.can_produce_element(element))
                and (
                    not skill_groups
                    or any(self.can_use_skill_group(group) for group in skill_groups)
                )
                and all(self.can_produce_tag(tag) for tag in tags)
            )
        return any(
            (
                element is None
                or BASE_ELEMENT_BY_ELEMENT.get(scope.element, scope.element)
                is BASE_ELEMENT_BY_ELEMENT.get(element, element)
            )
            and (not skill_groups or scope.skill_group in skill_groups)
            and all(tag in scope.damage_tags for tag in tags)
            for scope in self.damage_scopes
        )

    def has_mechanism(self, mechanism: str) -> bool:
        return mechanism in self.mechanisms


__all__ = [
    "EquipmentDamageScope",
    "EquipmentOwnerCapabilities",
    "WEngineBuildInput",
]
