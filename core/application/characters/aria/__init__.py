"""Reviewed compiler for Aria (character:1501)."""

from collections.abc import Mapping

from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .compiler import compile_aria
from .config import ARIA_ID, AriaCompileConfig
from .reviewed import ARIA_REVIEWED_MAPPING


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(ARIA_ID))


__all__ = [
    "ARIA_ID",
    "ARIA_REVIEWED_MAPPING",
    "AriaCompileConfig",
    "compile_aria",
    "load_raw_record",
]
