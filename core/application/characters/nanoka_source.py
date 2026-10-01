"""Common, lossless loader for the fixed Nanoka character detail shape.

The loader deliberately does not assign calculator semantics.  It keeps the
complete source descriptions and the source parameter curve (``main`` and
``growth``) so each reviewed character compiler can make an explicit choice
about skill groups, damage tags, event identity, and multiplier relations.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from core.types import CharacterId


NANOKA_SOURCE_VERSION = "3.2.4+18409985"
NANOKA_SOURCE_BASE_URL = (
    "https://static.nanoka.cc/zzz/3.2.4+18409985/zh/character"
)


@dataclass(frozen=True, slots=True)
class NanokaRawSkillParameter:
    """One source parameter curve, retained without semantic interpretation."""

    name: str
    format: str
    main: float | None
    growth: float | None
    source_skill_id: str | None
    values: tuple[tuple[int, float], ...]
    source_curves: tuple[
        tuple[str, tuple[tuple[int, float], ...]], ...
    ] = ()
    stun_ratio: float | None = None
    stun_ratio_growth: float | None = None
    attribute_infliction: float | None = None

    def value_for_level(
        self,
        level: int,
        source_skill_id: str | None = None,
    ) -> float | None:
        if source_skill_id is not None:
            source_values = next(
                (
                    values
                    for source_id, values in self.source_curves
                    if source_id == source_skill_id
                ),
                None,
            )
            if source_values is None:
                return None
            return dict(source_values).get(level)
        return dict(self.values).get(level)


@dataclass(frozen=True, slots=True)
class NanokaRawMoveRecord:
    skill_section: str
    name: str
    description: str
    parameters: tuple[NanokaRawSkillParameter, ...] = ()


@dataclass(frozen=True, slots=True)
class NanokaRawCoreLevel:
    level: int
    names: tuple[str, ...]
    descriptions: tuple[str, ...]
    source_id: str

    @property
    def name(self) -> str:
        return self.names[0] if self.names else ""

    @property
    def description(self) -> str:
        return self.descriptions[0] if self.descriptions else ""

    @property
    def extra_ability_name(self) -> str:
        return self.names[1] if len(self.names) > 1 else ""

    @property
    def extra_ability_description(self) -> str:
        return self.descriptions[1] if len(self.descriptions) > 1 else ""


@dataclass(frozen=True, slots=True)
class NanokaRawMindscape:
    level: int
    name: str
    description: str
    source_id: str


@dataclass(frozen=True, slots=True)
class NanokaRawRecord:
    character_id: CharacterId
    name: str
    code_name: str
    specialty: str
    element: str
    faction: str
    icon: str
    rarity: int
    source_version: str
    source_url: str
    moves: tuple[NanokaRawMoveRecord, ...]
    core_levels: tuple[NanokaRawCoreLevel, ...]
    mindscapes: tuple[NanokaRawMindscape, ...]
    special_element: str | None = None

    @property
    def extra_ability_name(self) -> str:
        return self.core_levels[0].extra_ability_name

    @property
    def extra_ability_description(self) -> str:
        return self.core_levels[0].extra_ability_description


def load_nanoka_raw_record(
    data: Mapping[str, object],
    *,
    expected_character_id: str | None = None,
) -> NanokaRawRecord:
    """Load one Nanoka detail record while preserving all damage-relevant text."""

    raw_id = _required(data, "id")
    character_id = CharacterId(
        str(raw_id)
        if str(raw_id).startswith("character:")
        else f"character:{raw_id}"
    )
    if expected_character_id is not None and character_id != CharacterId(
        expected_character_id
    ):
        raise ValueError(
            "Nanoka raw character ID does not match expected ID: "
            f"{character_id} != {expected_character_id}"
        )

    skill_root = _mapping(data, "skill")
    moves: list[NanokaRawMoveRecord] = []
    for section in ("basic", "dodge", "special", "chain", "assist"):
        section_data = skill_root.get(section, {})
        if not isinstance(section_data, Mapping):
            raise ValueError(f"Nanoka skill section must be an object: {section}")
        descriptions = section_data.get("description", ())
        if not isinstance(descriptions, (list, tuple)):
            raise ValueError(f"Nanoka descriptions must be an array: {section}")

        # The detail payload stores a prose entry and a parameter entry under
        # the same name.  Merge them in source order rather than discarding
        # either half of the raw record.
        grouped: dict[str, dict[str, object]] = {}
        order: list[str] = []
        for raw_description in descriptions:
            if not isinstance(raw_description, Mapping):
                continue
            name = _string(raw_description, "name", f"{section}.description")
            if name not in grouped:
                grouped[name] = {"description": "", "parameters": []}
                order.append(name)
            description = raw_description.get("desc")
            if isinstance(description, str) and description.strip():
                grouped[name]["description"] = description
            raw_parameters = raw_description.get("param")
            if isinstance(raw_parameters, (list, tuple)):
                grouped[name]["parameters"].extend(
                    item for item in raw_parameters if isinstance(item, Mapping)
                )
        for name in order:
            grouped_move = grouped[name]
            raw_parameters = grouped_move["parameters"]
            assert isinstance(raw_parameters, list)
            parameters = tuple(
                _raw_parameter(item, f"{section}:{name}")
                for item in raw_parameters
            )
            moves.append(
                NanokaRawMoveRecord(
                    skill_section=section,
                    name=name,
                    description=str(grouped_move["description"]),
                    parameters=parameters,
                )
            )

    passive = _mapping(data, "passive")
    raw_levels = _mapping(passive, "level")
    core_levels: list[NanokaRawCoreLevel] = []
    for key, raw_level in sorted(
        raw_levels.items(),
        key=lambda item: int(
            item[1].get("level", 0) if isinstance(item[1], Mapping) else 0
        ),
    ):
        if not isinstance(raw_level, Mapping):
            raise ValueError(f"Nanoka passive level must be an object: {key}")
        level = raw_level.get("level")
        if isinstance(level, bool) or not isinstance(level, int):
            raise ValueError(f"Nanoka passive level must be an integer: {key}")
        names = _strings(raw_level.get("name", ()), f"passive.level.{key}.name")
        descriptions_for_level = _strings(
            raw_level.get("desc", ()),
            f"passive.level.{key}.desc",
        )
        core_levels.append(
            NanokaRawCoreLevel(
                level=level,
                names=names,
                descriptions=descriptions_for_level,
                source_id=str(key),
            )
        )

    raw_talents = _mapping(data, "talent")
    mindscapes: list[NanokaRawMindscape] = []
    for key, raw_talent in sorted(raw_talents.items(), key=lambda item: int(item[0])):
        if not isinstance(raw_talent, Mapping):
            raise ValueError(f"Nanoka talent must be an object: {key}")
        level = int(key)
        mindscapes.append(
            NanokaRawMindscape(
                level=level,
                name=_string(raw_talent, "name", f"talent.{key}"),
                description=_string(raw_talent, "desc", f"talent.{key}"),
                source_id=key,
            )
        )

    weapon_type = _mapping(data, "weapon_type")
    element_type = _mapping(data, "element_type")
    raw_special_element = data.get("special_element_type", {})
    special_element = (
        raw_special_element.get("name")
        if isinstance(raw_special_element, Mapping)
        else None
    )
    camp = _mapping(data, "camp")
    source_version = str(
        data.get("source_version", NANOKA_SOURCE_VERSION)
    )
    source_url = str(
        data.get(
            "source_url",
            f"{NANOKA_SOURCE_BASE_URL}/{raw_id}.json",
        )
    )
    return NanokaRawRecord(
        character_id=character_id,
        name=_string(data, "name", "character"),
        code_name=_string(data, "code_name", "character"),
        specialty=_first_map_value(weapon_type, "weapon_type"),
        element=_first_map_value(element_type, "element_type"),
        faction=_first_map_value(camp, "camp"),
        icon=_string(data, "icon", "character"),
        rarity=_integer(data, "rarity", "character"),
        source_version=source_version,
        source_url=source_url,
        moves=tuple(moves),
        core_levels=tuple(core_levels),
        mindscapes=tuple(mindscapes),
        special_element=(
            str(special_element).strip()
            if isinstance(special_element, str) and special_element.strip()
            else None
        ),
    )


def _raw_parameter(
    data: Mapping[str, object],
    section: str,
) -> NanokaRawSkillParameter:
    name = _string(data, "name", f"{section}.parameter")
    raw_param = data.get("param")
    if not isinstance(raw_param, Mapping) or not raw_param:
        # Some source parameters are formula-only metadata (energy cost,
        # duration, or efficiency).  Keep their names in the raw record, but
        # do not pretend they are damage multiplier curves.
        return NanokaRawSkillParameter(
            name=name,
            format="raw",
            main=None,
            growth=None,
            source_skill_id=None,
            values=(),
            source_curves=(),
        )
    source_curves: list[tuple[str, tuple[tuple[int, float], ...]]] = []
    raw_curves: list[tuple[str, Mapping[str, object], float, float]] = []
    for source_skill_id, raw_value in raw_param.items():
        if not isinstance(raw_value, Mapping):
            raise ValueError(f"Nanoka parameter value must be an object: {section}:{name}")
        main = _number(raw_value, "main", f"{section}:{name}")
        growth = _number(raw_value, "growth", f"{section}:{name}")
        raw_curves.append((str(source_skill_id), raw_value, main, growth))
        source_curves.append(
            (
                str(source_skill_id),
                tuple(
                    (level, (main + growth * (level - 1)) / 100.0)
                    for level in range(1, 17)
                ),
            )
        )
    source_skill_id, raw_value, main, growth = raw_curves[0]
    raw_format = raw_value.get("format", "%")
    if not isinstance(raw_format, str) or not raw_format.strip():
        raise ValueError(f"Nanoka parameter format is invalid: {section}:{name}")
    values = tuple(
        (level, (main + growth * (level - 1)) / 100.0)
        for level in range(1, 17)
    )
    return NanokaRawSkillParameter(
        name=name,
        format=raw_format,
        main=main,
        growth=growth,
        source_skill_id=str(source_skill_id),
        values=values,
        source_curves=tuple(source_curves),
        stun_ratio=_optional_number(raw_value.get("stun_ratio")),
        stun_ratio_growth=_optional_number(raw_value.get("stun_ratio_growth")),
        attribute_infliction=_optional_number(
            raw_value.get("attribute_infliction")
        ),
    )


def _mapping(data: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"Nanoka raw field {key!r} must be an object")
    return value


def _required(data: Mapping[str, object], key: str) -> object:
    if key not in data:
        raise ValueError(f"Nanoka raw field {key!r} is missing")
    return data[key]


def _string(data: Mapping[str, object], key: str, section: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Nanoka {section} field {key!r} must be a non-empty string")
    return value


def _strings(value: object, section: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"Nanoka {section} must be an array")
    result = tuple(item for item in value if isinstance(item, str) and item.strip())
    if not result:
        raise ValueError(f"Nanoka {section} must contain text")
    return result


def _number(data: Mapping[str, object], key: str, section: str) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Nanoka {section} field {key!r} must be numeric")
    return float(value)


def _integer(data: Mapping[str, object], key: str, section: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Nanoka {section} field {key!r} must be an integer")
    return value


def _optional_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _first_map_value(data: Mapping[str, object], section: str) -> str:
    if not data:
        raise ValueError(f"Nanoka {section} must contain one value")
    value = next(iter(data.values()))
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Nanoka {section} value must be a non-empty string")
    return value


__all__ = [
    "NANOKA_SOURCE_BASE_URL",
    "NANOKA_SOURCE_VERSION",
    "NanokaRawCoreLevel",
    "NanokaRawMindscape",
    "NanokaRawMoveRecord",
    "NanokaRawRecord",
    "NanokaRawSkillParameter",
    "load_nanoka_raw_record",
]
