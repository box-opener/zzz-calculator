"""Reviewed Ben compiler for the live Nanoka 3.2 record."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_ben
from .config import BenCompileConfig
from .reviewed import BEN_ID, BEN_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(BEN_ID))


__all__ = [
    "BEN_ID",
    "BEN_REVIEWED_MAPPING",
    "BenCompileConfig",
    "compile_ben",
    "load_raw_record",
]
