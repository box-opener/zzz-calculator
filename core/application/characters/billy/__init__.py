"""Billy's reviewed live Nanoka 3.2 character compiler."""

from ..nanoka_source import load_nanoka_raw_record
from .compiler import compile_billy
from .config import BillyCompileConfig
from .reviewed import BILLY_ID, BILLY_REVIEWED_MAPPING


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(BILLY_ID))


__all__ = [
    "BILLY_ID",
    "BILLY_REVIEWED_MAPPING",
    "BillyCompileConfig",
    "compile_billy",
    "load_raw_record",
]
