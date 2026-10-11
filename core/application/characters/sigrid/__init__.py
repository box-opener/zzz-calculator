"""Reviewed Sigrid (1591) calculation definition."""

from __future__ import annotations

from collections.abc import Mapping

from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .compiler import compile_sigrid
from .config import SIGRID_ID, SigridCompileConfig
from .reviewed import SIGRID_REVIEWED_MAPPING


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(SIGRID_ID))


__all__ = [
    "SIGRID_ID",
    "SIGRID_REVIEWED_MAPPING",
    "SigridCompileConfig",
    "compile_sigrid",
    "load_raw_record",
]
