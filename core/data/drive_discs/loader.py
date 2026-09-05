"""Load the complete frozen Nanoka Drive Disc set snapshot."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any


SOURCE_PROVIDER = "nanoka"
SOURCE_VERSION = "3.2.4+18409985"
SOURCE_URL_TEMPLATE = (
    "https://static.nanoka.cc/zzz/3.2.4+18409985/zh/equipment/{set_id}.json"
)

DRIVE_DISC_SET_IDS = (
    "31000", "31100", "31200", "31300", "31400", "31500", "31600",
    "31800", "31900", "32200", "32300", "32400", "32500", "32600",
    "32700", "32800", "32900", "33000", "33100", "33200", "33300",
    "33400", "33500", "33600", "33700", "33800", "33900", "34000",
    "34100", "34200",
)


def load_drive_disc_record(set_id: str) -> dict[str, Any]:
    if set_id not in DRIVE_DISC_SET_IDS:
        raise ValueError(f"unsupported reviewed Drive Disc set: {set_id}")
    resource = resources.files("core.data.drive_discs").joinpath(f"{set_id}.json")
    with resource.open("rb") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict) or str(payload.get("id")) != set_id:
        raise ValueError(f"invalid Drive Disc raw record: {set_id}")
    return payload


def source_url_for(set_id: str) -> str:
    if set_id not in DRIVE_DISC_SET_IDS:
        raise ValueError(f"unsupported reviewed Drive Disc set: {set_id}")
    return SOURCE_URL_TEMPLATE.format(set_id=set_id)


__all__ = [
    "DRIVE_DISC_SET_IDS",
    "SOURCE_PROVIDER",
    "SOURCE_VERSION",
    "load_drive_disc_record",
    "source_url_for",
]
