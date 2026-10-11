"""Reviewed Starlight - Billy (1531) calculator integration."""

from __future__ import annotations

from collections.abc import Mapping

from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .compiler import compile_starlight_billy
from .config import STARLIGHT_BILLY_ID, StarlightBillyCompileConfig
from .reviewed import STARLIGHT_BILLY_REVIEWED_MAPPING


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(STARLIGHT_BILLY_ID))


__all__ = [
    "STARLIGHT_BILLY_ID",
    "STARLIGHT_BILLY_REVIEWED_MAPPING",
    "StarlightBillyCompileConfig",
    "compile_starlight_billy",
    "load_raw_record",
]
