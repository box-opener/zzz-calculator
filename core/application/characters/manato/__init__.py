"""Reviewed Manato (1441) calculator integration."""

from collections.abc import Mapping

from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .compiler import compile_manato
from .config import MANATO_ID, ManatoCompileConfig
from .reviewed import MANATO_REVIEWED_MAPPING


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(MANATO_ID))


__all__ = [
    "MANATO_ID",
    "MANATO_REVIEWED_MAPPING",
    "ManatoCompileConfig",
    "compile_manato",
    "load_raw_record",
]
