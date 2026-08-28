"""Load the small, reviewed Stage-018-2 W-Engine raw fixture set."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any


_WENGINE_FILES = {
    "wengine:14131": "14131.json",
    "wengine:14143": "14143.json",
}


def load_wengine_record(wengine_id: str) -> dict[str, Any]:
    try:
        filename = _WENGINE_FILES[wengine_id]
    except KeyError as exc:
        raise ValueError(f"unsupported Stage-018-2 W-Engine: {wengine_id}") from exc
    resource = resources.files("core.data.wengines").joinpath(filename)
    with resource.open("rb") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"W-Engine raw record must be an object: {filename}")
    return payload


def supported_wengine_ids() -> tuple[str, ...]:
    return tuple(_WENGINE_FILES)


__all__ = ["load_wengine_record", "supported_wengine_ids"]
