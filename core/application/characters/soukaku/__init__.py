"""Reviewed Soukaku compiler for the live Nanoka 3.2 record."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_soukaku
from .config import SoukakuCompileConfig
from .reviewed import SOUKAKU_ID, SOUKAKU_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(SOUKAKU_ID))


__all__ = [
    "SOUKAKU_ID",
    "SOUKAKU_REVIEWED_MAPPING",
    "SoukakuCompileConfig",
    "compile_soukaku",
    "load_raw_record",
]
