"""Reviewed BanYue (1471) calculator integration."""

from collections.abc import Mapping

from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .compiler import compile_banyue
from .config import BANYUE_ID, BanYueCompileConfig
from .reviewed import BANYUE_REVIEWED_MAPPING


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(BANYUE_ID))


__all__ = [
    "BANYUE_ID",
    "BANYUE_REVIEWED_MAPPING",
    "BanYueCompileConfig",
    "compile_banyue",
    "load_raw_record",
]
