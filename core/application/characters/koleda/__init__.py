"""Reviewed Koleda compiler for the live Nanoka 3.2 record."""

from .compiler import compile_koleda
from .config import KoledaCompileConfig
from .reviewed import KOLEDA_ID, KOLEDA_REVIEWED_MAPPING


def load_raw_record(data, *, potential_level: int = 0):
    from .compiler import load_raw_record as _load

    return _load(data, potential_level=potential_level)


__all__ = [
    "KOLEDA_ID",
    "KOLEDA_REVIEWED_MAPPING",
    "KoledaCompileConfig",
    "compile_koleda",
    "load_raw_record",
]
"""Koleda's reviewed live Nanoka 3.2 compiler."""

from .compiler import compile_koleda, load_raw_record
from .config import KoledaCompileConfig
from .reviewed import KOLEDA_ID, KOLEDA_REVIEWED_MAPPING


__all__ = [
    "KOLEDA_ID",
    "KOLEDA_REVIEWED_MAPPING",
    "KoledaCompileConfig",
    "compile_koleda",
    "load_raw_record",
]
