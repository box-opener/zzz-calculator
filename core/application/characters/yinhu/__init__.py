"""Yinhu (1421) reviewed calculator integration."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_yinhu
from .config import YinhuCompileConfig
from .reviewed import YINHU_ID, YINHU_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(YINHU_ID))


__all__ = [
    "YINHU_ID",
    "YINHU_REVIEWED_MAPPING",
    "YinhuCompileConfig",
    "compile_yinhu",
    "load_raw_record",
]
