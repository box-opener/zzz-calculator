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

    def __post_init__(self) -> None:
        if not self.wengine_id.strip() or not self.display_name.strip():
            raise ValueError("catalog W-Engine identity is required")
        if not self.icon_key.strip():
            raise ValueError("catalog W-Engine icon_key is required")


@dataclass(frozen=True, slots=True)
class DriveDiscCatalogItem:
    set_id: str
    display_name: str
    icon_path: str
    two_piece_text: str
    four_piece_text: str
    two_piece_disposition: str
    four_piece_disposition: str
    ignored_two_piece_reason: str | None = None
    ignored_four_piece_reason: str | None = None


def supported_drive_disc_catalog() -> tuple[DriveDiscCatalogItem, ...]:
    from core.application.equipment import (
        DRIVE_DISC_REVIEWED_MAPPINGS,
        load_drive_disc_raw_record,
        stable_set_id,
    )
    from core.data.drive_discs.loader import DRIVE_DISC_SET_IDS

    items = []
    for raw_id in DRIVE_DISC_SET_IDS:
        raw = load_drive_disc_raw_record(stable_set_id(raw_id))
        reviewed = DRIVE_DISC_REVIEWED_MAPPINGS[raw_id]
        icon_name = raw.icon.rsplit("/", 1)[-1].removesuffix(".png")
        items.append(
            DriveDiscCatalogItem(
                set_id=str(raw.set_id),
                display_name=raw.name,
                icon_path=f"/drive-discs/{icon_name}.webp",
                two_piece_text=raw.two_piece_text,
                four_piece_text=raw.four_piece_text,
                two_piece_disposition=reviewed.two_piece_disposition.value,
                four_piece_disposition=reviewed.four_piece_disposition.value,
                ignored_two_piece_reason=reviewed.ignored_two_piece_reason,
                ignored_four_piece_reason=reviewed.ignored_four_piece_reason,
            )
        )
    return tuple(items)


def supported_character_catalog() -> tuple[CharacterCatalogItem, ...]:
    from .registry import supported_character_registrations

    return tuple(item.catalog for item in supported_character_registrations())


def supported_wengine_catalog() -> tuple[WEngineCatalogItem, ...]:
    from core.application.equipment import (
        load_wengine_raw_record,
        signature_wengine_id_for,
    )
    from core.data.wengines.loader import supported_wengine_ids
    from core.application.equipment.wengine import ASTRA_ID, YE_ID

    signature_characters = {
        signature_wengine_id_for(ASTRA_ID): ASTRA_ID,
        signature_wengine_id_for(YE_ID): YE_ID,
    }
    items = []
    for wengine_id in supported_wengine_ids():
        raw = load_wengine_raw_record(wengine_id)
        signature_character_id = signature_characters.get(wengine_id)
        items.append(
            WEngineCatalogItem(
                wengine_id=wengine_id,
                display_name=raw.name,
                rarity=raw.rarity,
                specialty=raw.specialty.value,
                icon_key=raw.icon,
                signature_character_id=(
                    str(signature_character_id)
                    if signature_character_id is not None
                    else None
                ),
            )
        )
    return tuple(items)


__all__ = [
    "CharacterCatalogItem",
    "DriveDiscCatalogItem",
    "WEngineCatalogItem",
    "supported_character_catalog",
    "supported_drive_disc_catalog",
    "supported_wengine_catalog",
]
