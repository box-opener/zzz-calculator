"""Deterministic raw-record loading for the Ye Shunguang compiler.

This module deliberately retains source fields only.  Reviewed semantic
decisions such as SkillGroup, DamageTag, multiplier relations and variant
conditions live in :mod:`reviewed` and are never inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.types import CharacterId


@dataclass(frozen=True, slots=True)
class YeRawMoveRecord:
    skill_section: str
    name: str
    description: str
    parameter_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class YeShunguangRawRecord:
    character_id: CharacterId
    name: str
    code_name: str
    specialty: str
    element: str
    moves: tuple[YeRawMoveRecord, ...]
    core_passive_name: str
    extra_ability_name: str
    cinema_names: tuple[str, ...]


def load_raw_record(data: Mapping[str, object]) -> YeShunguangRawRecord:
    """Read only stable fields from a supplied character-record mapping."""

    raw_id = _string(data, "id", "character")
    character_id = CharacterId(
        raw_id if raw_id.startswith("character:") else f"character:{raw_id}"
    )
    skills = _mapping(data, "skills")
    moves: list[YeRawMoveRecord] = []
    for section in ("basic", "dodge", "special", "chain", "assist"):
        raw_moves = _sequence(skills.get(section), section)
        for raw_move in raw_moves:
            move = _mapping_value(raw_move, section)
            parameters = _sequence(move.get("parameters", ()), "parameters")
            moves.append(
                YeRawMoveRecord(
                    skill_section=section,
                    name=_string(move, "sub_skill_name", section),
                    description=_string(move, "sub_skill_desc", section),
                    parameter_names=tuple(
                        _string(_mapping_value(item, section), "param_name", section)
                        for item in parameters
                    ),
                )
            )

    passive = _mapping(data, "passive")
    level_one = _mapping(passive, "level_1")
    core = _mapping(level_one, "core_passive")
    extra = _mapping(level_one, "extra_ability")
    mindscapes = _mapping(data, "mindscapes")
    cinema_names = tuple(
        _string(_mapping(mindscapes, f"cinema_{level}"), "name", "mindscapes")
        for level in (1, 2, 4, 6)
    )
    return YeShunguangRawRecord(
        character_id=character_id,
        name=_string(data, "name", "character"),
        code_name=_string(data, "code_name", "character"),
        specialty=_string(data, "specialty", "character"),
        element=_string(data, "element", "character"),
        moves=tuple(moves),
        core_passive_name=_string(core, "name", "core_passive"),
        extra_ability_name=_string(extra, "name", "extra_ability"),
        cinema_names=cinema_names,
    )


def _mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"raw character field {key!r} must be an object")
    return value


def _mapping_value(data: object, section: str) -> Mapping[str, object]:
    if not isinstance(data, Mapping):
        raise ValueError(f"raw {section} skill entry must be an object")
    return data


def _sequence(data: object, field: str) -> tuple[object, ...]:
    if not isinstance(data, (list, tuple)):
        raise ValueError(f"raw character field {field!r} must be an array")
    return tuple(data)


def _string(data: Mapping[str, object], key: str, section: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"raw {section} field {key!r} must be a non-empty string")
    return value
