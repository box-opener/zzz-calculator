from __future__ import annotations

import pytest

from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import compile_registered_definition
from core.types import SkillGroup


def _ultimate_multipliers(character_id: str, cinema: int, selected_level: int) -> dict[str, float]:
    definition = compile_registered_definition(
        character_id,
        {
            "core_level": 7,
            "cinema_level": cinema,
            "skill_levels": {"ultimate": selected_level},
        },
        (character_id,),
        strict=False,
    )
    entries = {
        str(entry.entry_id): entry.multiplier_variants[0].multiplier.value.value
        for entry in definition.move_entries
        if entry.skill_group is SkillGroup.ULTIMATE
        and hasattr(entry.multiplier_variants[0].multiplier, "value")
        and hasattr(entry.multiplier_variants[0].multiplier.value, "value")
    }
    assert entries, f"{character_id} must expose at least one typed Ultimate entry"
    return entries


def test_cinema3_and5_raise_ultimate_levels_for_all_registered_characters() -> None:
    character_ids = tuple(item.character_id for item in supported_character_catalog())
    assert character_ids

    for character_id in character_ids:
        cinema3 = _ultimate_multipliers(character_id, cinema=3, selected_level=12)
        selected14 = _ultimate_multipliers(character_id, cinema=0, selected_level=14)
        cinema5 = _ultimate_multipliers(character_id, cinema=5, selected_level=12)
        selected16 = _ultimate_multipliers(character_id, cinema=0, selected_level=16)

        assert cinema3 == pytest.approx(selected14), character_id
        assert cinema5 == pytest.approx(selected16), character_id

        # Explicit level 16 remains capped when the cinema bonuses are present.
        cinema5_at16 = _ultimate_multipliers(character_id, cinema=5, selected_level=16)
        assert cinema5_at16 == pytest.approx(selected16), character_id
