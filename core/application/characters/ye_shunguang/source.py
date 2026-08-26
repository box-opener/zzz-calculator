"""Deterministic raw-record loading for the Ye Shunguang compiler.

This module deliberately retains source fields only.  Reviewed semantic
decisions such as SkillGroup, DamageTag, multiplier relations and variant
conditions live in :mod:`reviewed` and are never inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from core.types import CharacterId


@dataclass(frozen=True, slots=True)
class YeRawMoveRecord:
    skill_section: str
    name: str
    description: str
    parameters: tuple["YeRawSkillParameter", ...] = ()


@dataclass(frozen=True, slots=True)
class YeRawSkillParameter:
    name: str
    format: str
    values: tuple[tuple[int, float], ...]

    def value_for_level(self, level: int) -> float | None:
        return dict(self.values).get(level)


@dataclass(frozen=True, slots=True)
class YeRawCoreLevel:
    level: int
    name: str
    description: str
    crit_rate_bonus: float
    damage_bonus: float


@dataclass(frozen=True, slots=True)
class YeRawMindscape:
    level: int
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class YeShunguangRawRecord:
    character_id: CharacterId
    name: str
    code_name: str
    specialty: str
    element: str
    moves: tuple[YeRawMoveRecord, ...]
    core_levels: tuple[YeRawCoreLevel, ...]
    extra_ability_name: str
    extra_ability_description: str
    mindscapes: tuple[YeRawMindscape, ...]


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
            parameters = tuple(
                _raw_parameter(_mapping_value(item, section), section)
                for item in _sequence(move.get("parameters", ()), "parameters")
            )
            moves.append(
                YeRawMoveRecord(
                    skill_section=section,
                    name=_string(move, "sub_skill_name", section),
                    description=_string(move, "sub_skill_desc", section),
                    parameters=parameters,
                )
            )

    passive = _mapping(data, "passive")
    core_levels = tuple(
        _raw_core_level(_mapping(passive, f"level_{level}"), level)
        for level in range(1, 8)
    )
    level_one = _mapping(passive, "level_1")
    extra = _mapping(level_one, "extra_ability")
    mindscapes = _mapping(data, "mindscapes")
    raw_mindscapes = tuple(
        _mapping(mindscapes, f"cinema_{level}") for level in (1, 2, 4, 6)
    )
    return YeShunguangRawRecord(
        character_id=character_id,
        name=_string(data, "name", "character"),
        code_name=_string(data, "code_name", "character"),
        specialty=_string(data, "specialty", "character"),
        element=_string(data, "element", "character"),
        moves=tuple(moves),
        extra_ability_name=_string(extra, "name", "extra_ability"),
        extra_ability_description=_string(extra, "desc", "extra_ability"),
        core_levels=core_levels,
        mindscapes=tuple(
            YeRawMindscape(
                level=level,
                name=_string(raw, "name", "mindscapes"),
                description=_string(raw, "desc", "mindscapes"),
            )
            for level, raw in zip((1, 2, 4, 6), raw_mindscapes)
        ),
    )


def _raw_parameter(
    data: Mapping[str, object],
    section: str,
) -> YeRawSkillParameter:
    values = _mapping(data, "values")
    parsed_values: list[tuple[int, float]] = []
    for key, value in values.items():
        if not isinstance(key, str) or not key.startswith("lv"):
            raise ValueError(f"raw {section} parameter level must use lvN keys")
        if not isinstance(value, (int, float)):
            raise ValueError(f"raw {section} parameter values must be numeric")
        parsed_values.append((int(key[2:]), float(value)))
    return YeRawSkillParameter(
        name=_string(data, "param_name", section),
        format=_string(data, "format", section),
        values=tuple(sorted(parsed_values)),
    )


def _raw_core_level(data: Mapping[str, object], level: int) -> YeRawCoreLevel:
    core = _mapping(data, "core_passive")
    values = _mapping(data, "calculation_values")
    crit_rate = values.get("crit_rate_bonus")
    damage = values.get("damage_bonus")
    if not isinstance(crit_rate, (int, float)) or not isinstance(damage, (int, float)):
        raise ValueError("raw core level calculation values must be numeric")
    return YeRawCoreLevel(
        level=level,
        name=_string(core, "name", "core_passive"),
        description=_string(core, "desc", "core_passive"),
        crit_rate_bonus=float(crit_rate),
        damage_bonus=float(damage),
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
