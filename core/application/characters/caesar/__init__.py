"""Caesar's reviewed live Nanoka 3.2 character compiler."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_caesar
from .config import CaesarCompileConfig
from .reviewed import CAESAR_ID, CAESAR_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(CAESAR_ID))


__all__ = [
    "CAESAR_ID",
    "CAESAR_REVIEWED_MAPPING",
    "CaesarCompileConfig",
    "compile_caesar",
    "load_raw_record",
]
