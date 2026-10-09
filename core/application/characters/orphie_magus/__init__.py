"""Orphie & Magus (1301) reviewed calculator integration."""

from .compiler import compile_orphie_magus, load_raw_record
from .config import OrphieMagusCompileConfig
from .reviewed import ORPHIE_MAGUS_ID, ORPHIE_MAGUS_REVIEWED_MAPPING

__all__ = [
    "ORPHIE_MAGUS_ID",
    "ORPHIE_MAGUS_REVIEWED_MAPPING",
    "OrphieMagusCompileConfig",
    "compile_orphie_magus",
    "load_raw_record",
]
