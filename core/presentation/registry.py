"""Presentation-owned registry for supported reviewed character compilers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any, Callable

from core.application.characters.astra import (
    AstraCompileConfig,
    compile_astra,
    load_raw_record as load_astra_raw_record,
)
from core.application.characters.definition import CharacterCalculationDefinition
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record as load_ye_raw_record,
)
from core.application.characters.ye_shunguang.compiler import MINGXIN_CONDITION_ID
from core.application.characters.config import CharacterSkillLevel
from core.types import CharacterId, CharacterRole, Element, SkillGroup
from core.application.scenario import CalculationScenario, ConditionResolution, ScenarioCondition
from core.application.equipment import compile_wengine, load_wengine_raw_record
from core.types import WEngineBuildInput, WEngineId

from core.data.loader import load_character_record

from .catalog import CharacterCatalogItem
from .character_editor import CompileConfigFieldView


@dataclass(frozen=True, slots=True)
class CharacterPresentationRegistration:
    character_id: CharacterId
    catalog: CharacterCatalogItem
    role: CharacterRole
    base_element: Element
    compile_definition: Callable[
        [Mapping[str, Any], Sequence[CharacterId], bool], CharacterCalculationDefinition
    ]
    config_fields: Callable[
        [Mapping[str, Any], Sequence[CharacterId]], tuple[CompileConfigFieldView, ...]
    ]


def _integer_field(
    field_id: str,
    label: str,
    value: int,
    minimum: int,
    maximum: int,
    help_text: str,
) -> CompileConfigFieldView:
    return CompileConfigFieldView(
        field_id=field_id,
        label=label,
        field_type="integer",
        value=value,
        minimum=minimum,
        maximum=maximum,
        help_text=help_text,
    )


def _boolean_field(
    field_id: str,
    label: str,
    value: bool,
    help_text: str,
    *,
    editable: bool = True,
) -> CompileConfigFieldView:
    return CompileConfigFieldView(
        field_id=field_id,
        label=label,
        field_type="boolean",
        value=value,
        editable=editable,
        help_text=help_text,
    )


def _ye_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "叶瞬光核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "叶瞬光影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        _boolean_field(
            "mingxin_active",
            "当前处于明心境",
            bool(values.get("mingxin_active", False)),
            "STATIC 场景语义，改变后重新编译",
        ),
        _boolean_field(
            "entry_move_uses_linren",
            "入场招式结算为凛刃",
            bool(values.get("entry_move_uses_linren", False)),
            "STATIC 属性结算语义，独立于明心境",
        ),
        *_skill_level_fields(values),
    )


def _astra_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "耀嘉音核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "耀嘉音影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


_SKILL_GROUP_LABELS = {
    SkillGroup.BASIC_ATTACK: "普通攻击",
    SkillGroup.DODGE: "闪避",
    SkillGroup.SPECIAL_ATTACK: "特殊技",
    SkillGroup.CHAIN_ATTACK: "连携技",
    SkillGroup.ASSIST: "支援技",
    SkillGroup.ULTIMATE: "终结技",
}


def _skill_level_fields(values: Mapping[str, Any]) -> tuple[CompileConfigFieldView, ...]:
    selected = values.get("skill_levels", {})
    if selected is None:
        selected = {}
    if not isinstance(selected, Mapping):
        raise ValueError("skill_levels must be an object keyed by SkillGroup")
    return tuple(
        CompileConfigFieldView(
            field_id=f"skill_level:{group.value}",
            label=f"{_SKILL_GROUP_LABELS[group]}等级",
            field_type="select",
            value=int(selected.get(group.value, 12)),
            minimum=1,
            maximum=16,
            options=("12", "14", "16"),
            help_text="当前生产源数据提供的技能倍率等级",
        )
        for group in (
            SkillGroup.BASIC_ATTACK,
            SkillGroup.DODGE,
            SkillGroup.SPECIAL_ATTACK,
            SkillGroup.CHAIN_ATTACK,
            SkillGroup.ASSIST,
            SkillGroup.ULTIMATE,
        )
    )


def _skill_levels(values: Mapping[str, Any]) -> tuple[CharacterSkillLevel, ...]:
    selected = values.get("skill_levels", {})
    if selected is None:
        return ()
    if not isinstance(selected, Mapping):
        raise ValueError("skill_levels must be an object keyed by SkillGroup")
    levels = []
    for key, value in selected.items():
        try:
            group = SkillGroup(str(key))
        except ValueError as exc:
            raise ValueError(f"unknown skill group in skill_levels: {key}") from exc
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"skill level must be an integer: {key}")
        levels.append(CharacterSkillLevel(group, value))
    return tuple(levels)


def _allowed(values: Mapping[str, Any], allowed: frozenset[str]) -> None:
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"unknown compile config fields: {sorted(unknown)}")


def _required(values: Mapping[str, Any], required: frozenset[str]) -> None:
    missing = required - set(values)
    if missing:
        raise ValueError(f"missing compile config fields: {sorted(missing)}")


def _integer(values: Mapping[str, Any], field_id: str) -> int:
    value = values[field_id]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"compile config field {field_id} must be an integer")
    return value


def _boolean(values: Mapping[str, Any], field_id: str) -> bool:
    value = values[field_id]
    if not isinstance(value, bool):
        raise ValueError(f"compile config field {field_id} must be a boolean")
    return value


def _integer_with_default(
    values: Mapping[str, Any], field_id: str, default: int, strict: bool
) -> int:
    return _integer(values, field_id) if strict else _integer({field_id: values.get(field_id, default)}, field_id)


def _boolean_with_default(
    values: Mapping[str, Any], field_id: str, default: bool, strict: bool
) -> bool:
    return _boolean(values, field_id) if strict else _boolean({field_id: values.get(field_id, default)}, field_id)


def _compile_ye(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(
        values,
        frozenset({"core_level", "cinema_level", "mingxin_active", "entry_move_uses_linren", "skill_levels"}),
    )
    if strict:
        _required(
            values,
            frozenset({"core_level", "cinema_level", "mingxin_active", "entry_move_uses_linren"}),
        )
    return compile_ye_shunguang(
        YeShunguangCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            mingxin_active=_boolean_with_default(values, "mingxin_active", False, strict),
            entry_move_uses_linren=_boolean_with_default(values, "entry_move_uses_linren", False, strict),
        ),
        load_ye_raw_record(load_character_record("character:1431")),
    )


def _astra_eligibility(team_ids: Sequence[CharacterId]) -> bool:
    return any(
        _REGISTRATIONS[character_id].role
        in {CharacterRole.ATTACK, CharacterRole.ANOMALY, CharacterRole.RUPTURE}
        for character_id in team_ids
        if character_id != CharacterId("character:1311")
    )


def _compile_astra(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(
        values,
        frozenset({"core_level", "cinema_level", "skill_levels"}),
    )
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_astra(
        AstraCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_astra_eligibility(team_ids),
        ),
        load_astra_raw_record(load_character_record("character:1311")),
    )


_REGISTRATIONS: dict[CharacterId, CharacterPresentationRegistration] = {
    CharacterId("character:1311"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1311"),
        catalog=CharacterCatalogItem(
            character_id="character:1311",
            display_name="耀嘉音",
            rarity="S",
            element="ether",
            specialty="support",
            image_path="/characters/IconRole36.webp",
            image_object_position="50% 20%",
        ),
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        compile_definition=_compile_astra,
        config_fields=_astra_fields,
    ),
    CharacterId("character:1431"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1431"),
        catalog=CharacterCatalogItem(
            character_id="character:1431",
            display_name="叶瞬光",
            rarity="S",
            element="physical",
            specialty="attack",
            image_path="/characters/IconRole55.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.ATTACK,
        base_element=Element.PHYSICAL,
        compile_definition=_compile_ye,
        config_fields=_ye_fields,
    ),
}


def supported_character_registrations() -> tuple[CharacterPresentationRegistration, ...]:
    return tuple(_REGISTRATIONS.values())


def registration_for(character_id: str | CharacterId) -> CharacterPresentationRegistration:
    try:
        return _REGISTRATIONS[CharacterId(str(character_id))]
    except KeyError as exc:
        raise ValueError(f"unsupported character_id: {character_id}") from exc


def compile_registered_definition(
    character_id: str | CharacterId,
    values: Mapping[str, Any],
    team_character_ids: Sequence[str | CharacterId],
    *,
    strict: bool = True,
) -> CharacterCalculationDefinition:
    registration = registration_for(character_id)
    team_ids = tuple(CharacterId(str(item)) for item in team_character_ids)
    if any(item not in _REGISTRATIONS for item in team_ids):
        raise ValueError("team contains an unsupported character")
    return registration.compile_definition(values, team_ids, strict)


def config_fields_for(
    character_id: str | CharacterId,
    values: Mapping[str, Any],
    team_character_ids: Sequence[str | CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    registration = registration_for(character_id)
    return registration.config_fields(
        values,
        tuple(CharacterId(str(item)) for item in team_character_ids),
    )


def build_registered_editor_view(
    character_id: str | CharacterId,
    config_values: Mapping[str, Any],
    team_character_ids: Sequence[str | CharacterId],
    condition_values: Mapping[str, bool | None] | None = None,
):
    """Compile and build an editor view without putting role semantics in HTTP."""

    team_ids = tuple(CharacterId(str(item)) for item in team_character_ids)
    definition = compile_registered_definition(
        character_id,
        config_values,
        team_ids,
        strict=False,
    )
    if condition_values is not None and not isinstance(condition_values, Mapping):
        raise ValueError("condition_values must be an object")
    selected = condition_values or {}
    scenario_conditions = tuple(
        condition
        if condition.resolution.value == "static"
        else replace(
            condition,
            value=selected.get(str(condition.condition_id), condition.value),
        )
        for condition in definition.scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id="preview",
        current_operator=CharacterId(str(character_id)),
        conditions=scenario_conditions,
        parameters=definition.scenario_parameters,
    )
    from .assembler import build_character_editor_view

    return build_character_editor_view(
        definition,
        scenario=scenario,
        team_character_ids=team_ids,
        compile_config_fields=config_fields_for(
            character_id,
            config_values,
            team_ids,
        ),
    )


def build_registered_wengine_editor_view(
    wengine_id: str,
    equipped_character_id: str | CharacterId,
    team_character_ids: Sequence[str | CharacterId] = (),
    *,
    level: int = 60,
    refinement: int = 1,
    condition_values: Mapping[str, bool | None] | None = None,
):
    """Build an editor view for a concrete W-Engine/owner instance."""

    owner = CharacterId(str(equipped_character_id))
    registration = registration_for(owner)
    team_ids = tuple(CharacterId(str(item)) for item in team_character_ids) or (owner,)
    if owner not in team_ids:
        raise ValueError("equipped W-Engine owner must be in team_character_ids")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("team_character_ids must be unique")
    if condition_values is None:
        raw_values: Mapping[str, bool | None] = {}
    elif not isinstance(condition_values, Mapping):
        raise ValueError("condition_values must be an object")
    else:
        raw_values = condition_values
    resolution = compile_wengine(
        WEngineBuildInput(
            WEngineId(str(wengine_id)),
            owner,
            level=level,
            refinement=refinement,
        ),
        equipped_character_role=registration.role,
    )
    known_conditions = {item.condition_id for item in resolution.scenario_conditions}
    selected_values = {
        str(condition_id): value
        for condition_id, value in raw_values.items()
        if str(condition_id) in {str(item) for item in known_conditions}
    }
    if any(value is not None and not isinstance(value, bool) for value in selected_values.values()):
        raise ValueError("W-Engine scenario conditions must be boolean or null")
    conditions = tuple(
        condition
        if condition.resolution.value == "static"
        else replace(
            condition,
            value=selected_values.get(str(condition.condition_id), condition.value),
        )
        for condition in resolution.scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id="wengine-preview",
        current_operator=owner,
        conditions=conditions,
    )
    external_conditions = []
    if any(
        MINGXIN_CONDITION_ID in rule.condition_ids
        for rule in resolution.rule_items
    ):
        mingxin_value = raw_values.get(str(MINGXIN_CONDITION_ID))
        if mingxin_value is not None and not isinstance(mingxin_value, bool):
            raise ValueError("Mingxin scenario condition must be boolean or null")
        external_conditions.append(
            ScenarioCondition(
                condition_id=MINGXIN_CONDITION_ID,
                label="当前处于明心境",
                original_text="叶瞬光进入明心境时开启以太帷幕",
                resolution=ConditionResolution.USER_SELECTED,
                value=mingxin_value,
            )
        )
    from .assembler import build_wengine_editor_view

    return build_wengine_editor_view(
        resolution,
        scenario=scenario,
        team_character_ids=team_ids,
        condition_context=tuple(external_conditions),
    )


__all__ = [
    "CharacterPresentationRegistration",
    "compile_registered_definition",
    "config_fields_for",
    "build_registered_editor_view",
    "build_registered_wengine_editor_view",
    "registration_for",
    "supported_character_registrations",
]
