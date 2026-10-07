"""Yanagi's reviewed live Nanoka 3.2 character compiler."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_yanagi
from .config import YanagiCompileConfig
from .reviewed import YANAGI_ID, YANAGI_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(YANAGI_ID))


__all__ = [
    "YANAGI_ID",
    "YANAGI_REVIEWED_MAPPING",
    "YanagiCompileConfig",
    "compile_yanagi",
    "load_raw_record",
]
