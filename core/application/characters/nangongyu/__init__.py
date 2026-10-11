"""Nangong Yu's reviewed Nanoka 3.2 character compiler."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_nangongyu
from .config import NANGONGYU_ID, NangongYuCompileConfig
from .reviewed import NANGONGYU_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(NANGONGYU_ID))


__all__ = [
    "NANGONGYU_ID",
    "NANGONGYU_REVIEWED_MAPPING",
    "NangongYuCompileConfig",
    "compile_nangongyu",
    "load_raw_record",
]
