"""Reviewed Anton compiler for the live Nanoka 3.2 record."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_anton
from .config import AntonCompileConfig
from .reviewed import ANTON_ID, ANTON_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(ANTON_ID))


__all__ = [
    "ANTON_ID",
    "ANTON_REVIEWED_MAPPING",
    "AntonCompileConfig",
    "compile_anton",
    "load_raw_record",
]
