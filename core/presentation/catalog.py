"""Small presentation-only character catalog.

Calculation semantics remain in the reviewed compilers.  The catalog only
contains identity and asset metadata needed to render a roster.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CharacterCatalogItem:
    character_id: str
    display_name: str
    rarity: str
    element: str
    specialty: str
    image_path: str
    image_object_position: str = "50% 50%"

    def __post_init__(self) -> None:
        if not self.character_id.strip() or not self.display_name.strip():
            raise ValueError("catalog character identity is required")
        if not self.image_path.strip():
            raise ValueError("catalog character image_path is required")


def supported_character_catalog() -> tuple[CharacterCatalogItem, ...]:
    from .registry import supported_character_registrations

    return tuple(item.catalog for item in supported_character_registrations())


__all__ = ["CharacterCatalogItem", "supported_character_catalog"]
