"""Corin's reviewed live Nanoka 3.2 character compiler."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_corin
from .config import CorinCompileConfig
from .reviewed import CORIN_ID, CORIN_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(CORIN_ID))


__all__ = [
    "CORIN_ID",
    "CORIN_REVIEWED_MAPPING",
    "CorinCompileConfig",
    "compile_corin",
    "load_raw_record",
]
