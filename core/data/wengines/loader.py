"""Load the reviewed W-Engine raw fixture sets."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any


_WENGINE_FILES = {
    "wengine:12001": "12001.json",
    "wengine:12002": "12002.json",
    "wengine:12003": "12003.json",
    "wengine:12004": "12004.json",
    "wengine:12005": "12005.json",
    "wengine:12006": "12006.json",
    "wengine:12007": "12007.json",
    "wengine:12008": "12008.json",
    "wengine:12009": "12009.json",
    "wengine:12010": "12010.json",
    "wengine:12011": "12011.json",
    "wengine:12012": "12012.json",
    "wengine:12013": "12013.json",
    "wengine:12014": "12014.json",
    "wengine:12015": "12015.json",
    "wengine:12016": "12016.json",
    "wengine:13001": "13001.json",
    "wengine:13002": "13002.json",
    "wengine:13003": "13003.json",
    "wengine:13004": "13004.json",
    "wengine:13005": "13005.json",
    "wengine:13103": "13103.json",
    "wengine:14102": "14102.json",
    "wengine:14104": "14104.json",
    "wengine:14119": "14119.json",
    "wengine:14120": "14120.json",
    "wengine:14121": "14121.json",
    "wengine:14124": "14124.json",
    "wengine:14131": "14131.json",
    "wengine:14143": "14143.json",
    "wengine:14145": "14145.json",
    "wengine:14149": "14149.json",
    "wengine:14136": "14136.json",
    "wengine:14140": "14140.json",
    "wengine:14141": "14141.json",
}


def load_wengine_record(wengine_id: str) -> dict[str, Any]:
    try:
        filename = _WENGINE_FILES[wengine_id]
    except KeyError as exc:
        raise ValueError(f"unsupported reviewed W-Engine: {wengine_id}") from exc
    resource = resources.files("core.data.wengines").joinpath(filename)
    with resource.open("rb") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"W-Engine raw record must be an object: {filename}")
    return payload


def supported_wengine_ids() -> tuple[str, ...]:
    return tuple(_WENGINE_FILES)


__all__ = ["load_wengine_record", "supported_wengine_ids"]
