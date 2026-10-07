"""Reviewed Lycaon compiler for the live Nanoka 3.2 record."""

from .compiler import compile_lycaon, load_raw_record as _load_raw_record
from .config import LycaonCompileConfig
from .reviewed import LYCAON_ID, LYCAON_REVIEWED_MAPPING


def load_raw_record(data, *, potential_level: int = 0):
    return _load_raw_record(data, potential_level=potential_level)


__all__ = [
    "LYCAON_ID",
    "LYCAON_REVIEWED_MAPPING",
    "LycaonCompileConfig",
    "compile_lycaon",
    "load_raw_record",
]
