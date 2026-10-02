"""Reviewed Anby (character:1011) compiler."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import ANBY_ELECTRIC_ANOMALY_MOVE_ID, ANBY_ELECTRIC_ANOMALY_RECORD_ID, compile_anby
from .config import AnbyCompileConfig
from .reviewed import ANBY_ID, ANBY_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(ANBY_ID))


__all__ = [
    "ANBY_ELECTRIC_ANOMALY_MOVE_ID",
    "ANBY_ELECTRIC_ANOMALY_RECORD_ID",
    "ANBY_ID",
    "ANBY_REVIEWED_MAPPING",
    "AnbyCompileConfig",
    "compile_anby",
    "load_raw_record",
]
