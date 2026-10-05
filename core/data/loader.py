"""Load reviewed character source records from package data.

The character-specific ``source`` modules remain responsible for validating
and normalizing their own raw shape.  This module only owns the production
resource boundary so application code never has to reach into ``tests``.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any


_CHARACTER_FILES = {
    "character:1011": "anby.json",
    "character:1021": "nekomata.json",
    "character:1031": "nicole.json",
    "character:1041": "soldier11.json",
    "character:1051": "yidhari.json",
    "character:1581": "remielle.json",
    "character:1561": "velina.json",
    "character:1311": "astra.json",
    "character:1431": "ye_shunguang.json",
    "character:1401": "alice.json",
    "character:1411": "yuzuha.json",
    "character:1361": "trigger.json",
    "character:1091": "miyabi.json",
    "character:1371": "yixuan.json",
    "character:1451": "lucia.json",
    "character:1481": "dialyn.json",
    "character:1331": "vivian.json",
    "character:1341": "zhao.json",
    "character:1251": "qingyi.json",
}


def load_character_record(character_id: str) -> dict[str, Any]:
    """Return a fresh raw record for a supported production character."""

    try:
        filename = _CHARACTER_FILES[character_id]
    except KeyError as exc:
        raise ValueError(f"unsupported production character: {character_id}") from exc

    resource = resources.files("core.data.characters").joinpath(filename)
    with resource.open("rb") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"production character record must be an object: {filename}")
    return payload


def supported_character_ids() -> tuple[str, ...]:
    """Return stable IDs available to the current production build."""

    return tuple(_CHARACTER_FILES)


__all__ = ["load_character_record", "supported_character_ids"]
