"""Packaged source data for the current calculation slices."""

from .loader import load_character_record, supported_character_ids
from .wengines.loader import load_wengine_record, supported_wengine_ids

__all__ = [
    "load_character_record",
    "supported_character_ids",
    "load_wengine_record",
    "supported_wengine_ids",
]
