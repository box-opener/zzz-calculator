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


@dataclass(frozen=True, slots=True)
class WEngineCatalogItem:
    wengine_id: str
    display_name: str
    rarity: str
    specialty: str
    icon_key: str
    signature_character_id: str | None = None
    rule_item_ids: tuple[str, ...] = ()
    scenario_condition_ids: tuple[str, ...] = ()
    stack_rule_item_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.wengine_id.strip() or not self.display_name.strip():
            raise ValueError("catalog W-Engine identity is required")
        if not self.icon_key.strip():
            raise ValueError("catalog W-Engine icon_key is required")


def supported_character_catalog() -> tuple[CharacterCatalogItem, ...]:
    from .registry import supported_character_registrations

    return tuple(item.catalog for item in supported_character_registrations())


def supported_wengine_catalog() -> tuple[WEngineCatalogItem, ...]:
    from core.application.equipment import (
        compile_wengine,
        load_wengine_raw_record,
        signature_wengine_id_for,
    )
    from core.application.equipment.wengine import ASTRA_ID, YE_ID
    from core.types import WEngineBuildInput

    signature_characters = {
        signature_wengine_id_for(ASTRA_ID): ASTRA_ID,
        signature_wengine_id_for(YE_ID): YE_ID,
    }
    items = []
    for wengine_id in ("wengine:14131", "wengine:14143"):
        raw = load_wengine_raw_record(wengine_id)
        signature_character_id = signature_characters[wengine_id]
        resolution = compile_wengine(
            WEngineBuildInput(
                raw.wengine_id,
                signature_character_id,
            ),
            equipped_character_role=raw.specialty,
        )
        items.append(
            WEngineCatalogItem(
                wengine_id=wengine_id,
                display_name=raw.name,
                rarity=raw.rarity,
                specialty=raw.specialty.value,
                icon_key=raw.icon,
                signature_character_id=str(signature_character_id),
                rule_item_ids=tuple(str(item.rule_id) for item in resolution.rule_items),
                scenario_condition_ids=tuple(
                    str(item.condition_id)
                    for item in resolution.scenario_conditions
                ),
                stack_rule_item_ids=tuple(
                    str(item.rule_id)
                    for item in resolution.rule_items
                    if item.stack_count is not None
                ),
            )
        )
    return tuple(items)


__all__ = [
    "CharacterCatalogItem",
    "WEngineCatalogItem",
    "supported_character_catalog",
    "supported_wengine_catalog",
]
