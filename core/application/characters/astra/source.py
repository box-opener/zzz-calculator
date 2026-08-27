"""Deterministic raw-record loading for the Astra reviewed compiler.

Only source fields are read here.  Skill taxonomy, event identities, trigger
relationships and calculator effects are deliberately kept in ``reviewed``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from core.types import CharacterId


@dataclass(frozen=True, slots=True)
class AstraRawSkillParameter:
    name: str
    format: str
    values: tuple[tuple[int, float], ...]

    def value_for_level(self, level: int) -> float | None:
        return dict(self.values).get(level)


@dataclass(frozen=True, slots=True)
class AstraRawMoveRecord:
    skill_section: str
    name: str
    description: str
    parameters: tuple[AstraRawSkillParameter, ...] = ()


@dataclass(frozen=True, slots=True)
class AstraRawCoreLevel:
    level: int
    name: str
    description: str
    attack_bonus_percent: float
    attack_bonus_cap: float


@dataclass(frozen=True, slots=True)
class AstraRawMindscape:
    level: int
    name: str
    description: str
    calculation_values: tuple[tuple[str, float], ...] = ()

    def calculation_value(self, key: str) -> float | None:
        return dict(self.calculation_values).get(key)


@dataclass(frozen=True, slots=True)
class AstraRawRecord:
    character_id: CharacterId
    name: str
    code_name: str
    specialty: str
    element: str
    moves: tuple[AstraRawMoveRecord, ...]
    core_levels: tuple[AstraRawCoreLevel, ...]
    extra_ability_name: str
    extra_ability_description: str
    mindscapes: tuple[AstraRawMindscape, ...]


def load_raw_record(data: Mapping[str, object]) -> AstraRawRecord:
    raw_id = _string(data, "id", "character")
    character_id = CharacterId(
        raw_id if raw_id.startswith("character:") else f"character:{raw_id}"
    )
    skills = _mapping(data, "skills")
    moves: list[AstraRawMoveRecord] = []
    for section in ("basic", "dodge", "special", "chain", "assist"):
        for raw_move in _sequence(skills.get(section), section):
            move = _mapping_value(raw_move, section)
            parameters = tuple(
                _raw_parameter(_mapping_value(item, section), section)
                for item in _sequence(move.get("parameters", ()), "parameters")
            )
            moves.append(
                AstraRawMoveRecord(
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
    return AstraRawRecord(
        character_id=character_id,
        name=_string(data, "name", "character"),
        code_name=_string(data, "code_name", "character"),
        specialty=_string(data, "specialty", "character"),
        element=_string(data, "element", "character"),
        moves=tuple(moves),
        core_levels=core_levels,
        extra_ability_name=_string(extra, "name", "extra_ability"),
        extra_ability_description=_string(extra, "desc", "extra_ability"),
        mindscapes=tuple(
            AstraRawMindscape(
                level=level,
                name=_string(raw, "name", "mindscapes"),
                description=_string(raw, "desc", "mindscapes"),
                calculation_values=_calculation_values(raw, "mindscapes"),
            )
            for level, raw in zip((1, 2, 4, 6), raw_mindscapes)
        ),
    )


def _raw_parameter(
    data: Mapping[str, object],
    section: str,
) -> AstraRawSkillParameter:
    values = _mapping(data, "values")
    parsed_values: list[tuple[int, float]] = []
    for key, value in values.items():
        if not isinstance(key, str) or not key.startswith("lv"):
            raise ValueError(f"raw {section} parameter level must use lvN keys")
        if not isinstance(value, (int, float)):
            raise ValueError(f"raw {section} parameter values must be numeric")
        parsed_values.append((int(key[2:]), float(value)))
    return AstraRawSkillParameter(
        name=_string(data, "param_name", section),
        format=_string(data, "format", section),
        values=tuple(sorted(parsed_values)),
    )


def _raw_core_level(
    data: Mapping[str, object],
    level: int,
) -> AstraRawCoreLevel:
    core = _mapping(data, "core_passive")
    values = _mapping(data, "calculation_values")
    attack_bonus_percent = values.get("attack_bonus_percent")
    attack_bonus_cap = values.get("attack_bonus_cap")
    if not isinstance(attack_bonus_percent, (int, float)) or not isinstance(
        attack_bonus_cap, (int, float)
    ):
        raise ValueError("raw Astra core calculation values must be numeric")
    return AstraRawCoreLevel(
        level=level,
        name=_string(core, "name", "core_passive"),
        description=_string(core, "desc", "core_passive"),
        attack_bonus_percent=float(attack_bonus_percent),
        attack_bonus_cap=float(attack_bonus_cap),
    )


def _calculation_values(
    data: Mapping[str, object],
    section: str,
) -> tuple[tuple[str, float], ...]:
    raw_values = data.get("calculation_values", {})
    if not isinstance(raw_values, Mapping):
        raise ValueError(f"raw {section} calculation_values must be an object")
    values: list[tuple[str, float]] = []
    for key, value in raw_values.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"raw {section} calculation value keys must be strings")
        if not isinstance(value, (int, float)):
            raise ValueError(f"raw {section} calculation values must be numeric")
        values.append((key, float(value)))
    return tuple(sorted(values))


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
