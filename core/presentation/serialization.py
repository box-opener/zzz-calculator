"""Explicit JSON serialization for presentation DTOs."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from enum import Enum
import math
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Convert a presentation DTO to JSON-compatible primitives only."""

    if is_dataclass(value):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("presentation output cannot contain non-finite numbers")
        return value
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported presentation value: {type(value).__name__}")


__all__ = ["to_jsonable"]
