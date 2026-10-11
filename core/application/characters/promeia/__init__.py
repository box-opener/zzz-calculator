"""Reviewed compiler for Promeia (character:1541)."""

from collections.abc import Mapping

from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .compiler import compile_promeia
from .config import PROMEIA_ID, PromeiaCompileConfig
from .reviewed import PROMEIA_REVIEWED_MAPPING


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(PROMEIA_ID))


__all__ = [
    "PROMEIA_ID",
    "PROMEIA_REVIEWED_MAPPING",
    "PromeiaCompileConfig",
    "compile_promeia",
    "load_raw_record",
]
