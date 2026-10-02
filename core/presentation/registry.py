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
from core.application.characters.alice import (
    AliceCompileConfig,
    compile_alice,
    load_raw_record as load_alice_raw_record,
)
from core.application.characters.anby import (
    ANBY_ID,
    AnbyCompileConfig,
    compile_anby,
    load_raw_record as load_anby_raw_record,
)
from core.application.characters.yuzuha import (
    YuzuhaCompileConfig,
    compile_yuzuha,
    load_raw_record as load_yuzuha_raw_record,
)
from core.application.characters.trigger import (
    TriggerCompileConfig,
    compile_trigger,
    load_raw_record as load_trigger_raw_record,
)
from core.application.characters.miyabi import (
    MiyabiCompileConfig,
    MIYABI_ID,
    compile_miyabi,
    load_raw_record as load_miyabi_raw_record,
)
from core.application.characters.yixuan import (
    YIXUAN_ID,
    YixuanCompileConfig,
    compile_yixuan,
    load_raw_record as load_yixuan_raw_record,
)
from core.application.characters.lucia import (
    LUCIA_ID,
    LuciaCompileConfig,
    compile_lucia,
    load_raw_record as load_lucia_raw_record,
)
from core.application.characters.dialyn import (
    DIALYN_ID,
    DialynCompileConfig,
    compile_dialyn,
    load_raw_record as load_dialyn_raw_record,
)
from core.application.characters.vivian import (
    VIVIAN_ID,
    VivianCompileConfig,
    compile_vivian,
    load_raw_record as load_vivian_raw_record,
)
from core.application.characters.zhao import (
    ZHAO_ID,
    ZhaoCompileConfig,
    compile_zhao,
    load_raw_record as load_zhao_raw_record,
)
from core.application.characters.qingyi import (
    QINGYI_ID,
    QingyiCompileConfig,
    compile_qingyi,
    load_raw_record as load_qingyi_raw_record,
)
from core.application.characters.nekomata import (
    NEKOMATA_ID,
    NekomataCompileConfig,
    compile_nekomata,
    load_raw_record as load_nekomata_raw_record,
)
from core.application.characters.definition import CharacterCalculationDefinition
from core.application.characters.ye_shunguang import (
    YeShunguangCompileConfig,
    compile_ye_shunguang,
    load_raw_record as load_ye_raw_record,
)
from core.application.characters.config import CharacterSkillLevel
from core.types import (
    CharacterId,
    CharacterRole,
    DamageTag,
    Element,
    EquipmentDamageScope,
    EquipmentOwnerCapabilities,
    SkillGroup,
)
from core.application.scenario import CalculationScenario
from core.application.equipment import (
    compile_drive_discs,
    compile_wengine,
    load_drive_disc_raw_record,
    load_wengine_raw_record,
    stable_set_id,
)
from core.application.build.assembler import assemble_build
from core.types import (
    BuildMode,
    DriveDiscBuildInput,
    DriveDiscSlot,
    DriveDiscStatKey,
    DriveDiscSubstatRoll,
    EquippedDriveDisc,
    CharacterBuildDefinition,
    CharacterSnapshot,
    Resolved,
    DRIVE_DISC_MAIN_STAT_VALUES,
    DRIVE_DISC_SUBSTAT_VALUES,
    WEngineBuildInput,
    WEngineId,
)

from core.data.loader import load_character_record

from .catalog import CharacterCatalogItem
from .character_editor import CompileConfigFieldView
from .base_stats import character_base_stat_contributions, character_base_stats
from .build_preview import (
    BuildPreviewView,
    DriveDiscPreviewView,
    DriveDiscStatPreviewView,
)
from .calculation import BuildContributionView, panel_snapshot_view
from .calculation import build_contribution_view
from .diagnostics import diagnostic_view
from .assembler import SCHEMA_VERSION
from .drive_disc_display import display_drive_disc_value, drive_disc_stat_label


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
    equipment_capabilities: EquipmentOwnerCapabilities


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


def _alice_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "爱丽丝核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "爱丽丝影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _miyabi_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "雅核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "雅影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _yixuan_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "仪玄核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "仪玄影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _lucia_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "卢西娅核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "卢西娅影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _dialyn_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "琉音核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "琉音影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _vivian_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "薇薇安核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "薇薇安影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _zhao_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "照核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "照影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _qingyi_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "青衣核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "青衣影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _yuzuha_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "柚叶核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "柚叶影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _trigger_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "扳机核心等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "扳机影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁的影画等级",
        ),
        *_skill_level_fields(values),
    )


def _anby_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "安比核心被动等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级",
        ),
        _integer_field(
            "cinema_level",
            "安比影画",
            int(values.get("cinema_level", 6)),
            0,
            6,
            "A级角色默认按6影配置；已解锁影画等级",
        ),
        *_skill_level_fields(values, default_level=16),
    )


def _nekomata_fields(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
) -> tuple[CompileConfigFieldView, ...]:
    return (
        _integer_field(
            "core_level",
            "猫又核心被动等级",
            int(values.get("core_level", 1)),
            1,
            7,
            "角色核心被动等级；仅编译Nanoka明确标为潜能0的基础核心曲线",
        ),
        _integer_field(
            "cinema_level",
            "猫又影画",
            int(values.get("cinema_level", 0)),
            0,
            6,
            "已解锁影画等级；潜能觉醒单独记录且当前配置无潜能选择器",
        ),
        *_skill_level_fields(values),
    )


def _nekomata_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    nekomata_camps = {
        str(value)
        for value in load_character_record(str(NEKOMATA_ID)).get("camp", {}).values()
    }
    for character_id in team_ids:
        if character_id == NEKOMATA_ID:
            continue
        registration = _REGISTRATIONS.get(character_id)
        if registration is not None and registration.base_element is Element.PHYSICAL:
            return True
        camps = load_character_record(str(character_id)).get("camp", {})
        if isinstance(camps, Mapping) and nekomata_camps.intersection(
            str(value) for value in camps.values()
        ):
            return True
    return False


def _compile_nekomata(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_nekomata(
        NekomataCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_nekomata_additional_ability_eligibility(
                team_ids
            ),
        ),
        load_nekomata_raw_record(load_character_record(str(NEKOMATA_ID))),
    )


def _anby_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    anby_camps = {
        str(value)
        for value in load_character_record(str(ANBY_ID)).get("camp", {}).values()
    }
    for character_id in team_ids:
        if character_id == ANBY_ID:
            continue
        registration = _REGISTRATIONS[character_id]
        if registration.base_element is Element.ELECTRIC:
            return True
        camps = load_character_record(str(character_id)).get("camp", {})
        if isinstance(camps, Mapping) and anby_camps.intersection(
            str(value) for value in camps.values()
        ):
            return True
    return False


def _compile_anby(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_anby(
        AnbyCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 6, strict),
            additional_ability_eligible=_anby_additional_ability_eligibility(
                team_ids
            ),
        ),
        load_anby_raw_record(load_character_record(str(ANBY_ID))),
    )


_SKILL_GROUP_LABELS = {
    SkillGroup.BASIC_ATTACK: "普通攻击",
    SkillGroup.DODGE: "闪避",
    SkillGroup.SPECIAL_ATTACK: "特殊技",
    SkillGroup.CHAIN_ATTACK: "连携技",
    SkillGroup.ASSIST: "支援技",
    SkillGroup.ULTIMATE: "终结技",
}


def _skill_level_fields(
    values: Mapping[str, Any],
    *,
    default_level: int = 12,
) -> tuple[CompileConfigFieldView, ...]:
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
            value=int(selected.get(group.value, default_level)),
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
    return (
        _integer(values, field_id)
        if strict
        else _integer({field_id: values.get(field_id, default)}, field_id)
    )


def _boolean_with_default(
    values: Mapping[str, Any], field_id: str, default: bool, strict: bool
) -> bool:
    return (
        _boolean(values, field_id)
        if strict
        else _boolean({field_id: values.get(field_id, default)}, field_id)
    )


def _compile_ye(
    values: Mapping[str, Any],
    _team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(
        values,
        frozenset(
            {
                "core_level",
                "cinema_level",
                "mingxin_active",
                "entry_move_uses_linren",
                "skill_levels",
            }
        ),
    )
    if strict:
        _required(
            values,
            frozenset(
                {
                    "core_level",
                    "cinema_level",
                    "mingxin_active",
                    "entry_move_uses_linren",
                }
            ),
        )
    return compile_ye_shunguang(
        YeShunguangCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            mingxin_active=_boolean_with_default(
                values, "mingxin_active", False, strict
            ),
            entry_move_uses_linren=_boolean_with_default(
                values, "entry_move_uses_linren", False, strict
            ),
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


def _alice_eligibility(team_ids: Sequence[CharacterId]) -> bool:
    return any(
        _REGISTRATIONS[character_id].role
        in {CharacterRole.ANOMALY, CharacterRole.SUPPORT}
        for character_id in team_ids
        if character_id != CharacterId("character:1401")
    )


def _yuzuha_eligibility(team_ids: Sequence[CharacterId]) -> bool:
    # Yuzuha's raw faction is Camp11.  The only other Camp11 member in the
    # current production roster is Alice; anomaly teammates also satisfy the
    # alternate qualification in the source text.
    return any(
        character_id == CharacterId("character:1401")
        or (
            character_id != CharacterId("character:1411")
            and _REGISTRATIONS[character_id].role is CharacterRole.ANOMALY
        )
        for character_id in team_ids
    )


def _trigger_eligibility(team_ids: Sequence[CharacterId]) -> bool:
    return any(
        character_id != CharacterId("character:1361")
        and (
            _REGISTRATIONS[character_id].role is CharacterRole.ATTACK
            or _REGISTRATIONS[character_id].base_element is Element.ELECTRIC
        )
        for character_id in team_ids
    )


def _compile_alice(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_alice(
        AliceCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_alice_eligibility(team_ids),
        ),
        load_alice_raw_record(load_character_record("character:1401")),
    )


def _compile_yuzuha(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_yuzuha(
        YuzuhaCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_yuzuha_eligibility(team_ids),
        ),
        load_yuzuha_raw_record(load_character_record("character:1411")),
    )


def _compile_trigger(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_trigger(
        TriggerCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_trigger_eligibility(team_ids),
        ),
        load_trigger_raw_record(load_character_record("character:1361")),
    )


def _miyabi_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    faction = "对空洞特别行动部第六课"
    for character_id in team_ids:
        if character_id == MIYABI_ID:
            continue
        registration = _REGISTRATIONS[character_id]
        if registration.role in {CharacterRole.SUPPORT, CharacterRole.ANOMALY}:
            return True
        camp = load_character_record(str(character_id)).get("camp", {})
        if isinstance(camp, Mapping) and faction in {
            str(value) for value in camp.values()
        }:
            return True
    return False


def _compile_miyabi(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_miyabi(
        MiyabiCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_miyabi_additional_ability_eligibility(
                team_ids
            ),
        ),
        load_miyabi_raw_record(load_character_record(str(MIYABI_ID))),
    )


def _yixuan_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    return any(
        character_id != YIXUAN_ID
        and _REGISTRATIONS[character_id].role
        in {CharacterRole.STUN, CharacterRole.SUPPORT, CharacterRole.DEFENSE}
        for character_id in team_ids
    )


def _compile_yixuan(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_yixuan(
        YixuanCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=(
                _yixuan_additional_ability_eligibility(team_ids)
            ),
        ),
        load_yixuan_raw_record(load_character_record(str(YIXUAN_ID))),
    )


def _lucia_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    return any(
        character_id != LUCIA_ID
        and _REGISTRATIONS[character_id].role
        in {CharacterRole.RUPTURE, CharacterRole.STUN}
        for character_id in team_ids
    )


def _compile_lucia(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_lucia(
        LuciaCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=(
                _lucia_additional_ability_eligibility(team_ids)
            ),
        ),
        load_lucia_raw_record(load_character_record(str(LUCIA_ID))),
    )


def _dialyn_eligibility(team_ids: Sequence[CharacterId]) -> bool:
    return any(
        character_id != DIALYN_ID
        and _REGISTRATIONS[character_id].role
        in {CharacterRole.ATTACK, CharacterRole.RUPTURE}
        for character_id in team_ids
    )


def _compile_dialyn(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_dialyn(
        DialynCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=_dialyn_eligibility(team_ids),
            after_sound_eligible=any(item != DIALYN_ID for item in team_ids),
        ),
        load_dialyn_raw_record(load_character_record(str(DIALYN_ID))),
    )


def _vivian_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    return any(
        character_id != VIVIAN_ID
        and character_id in _REGISTRATIONS
        and (
            _REGISTRATIONS[character_id].role is CharacterRole.ANOMALY
            or _REGISTRATIONS[character_id].base_element is Element.ETHER
        )
        for character_id in team_ids
    )


def _compile_vivian(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_vivian(
        VivianCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=(
                _vivian_additional_ability_eligibility(team_ids)
            ),
        ),
        load_vivian_raw_record(load_character_record(str(VIVIAN_ID))),
    )


def _zhao_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    return any(
        character_id != ZHAO_ID
        and character_id in _REGISTRATIONS
        and _REGISTRATIONS[character_id].role
        in {CharacterRole.ATTACK, CharacterRole.ANOMALY, CharacterRole.SUPPORT}
        for character_id in team_ids
    )


def _compile_zhao(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_zhao(
        ZhaoCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=(
                _zhao_additional_ability_eligibility(team_ids)
            ),
        ),
        load_zhao_raw_record(load_character_record(str(ZHAO_ID))),
    )


def _nanoka_camp_ids(character_id: CharacterId) -> frozenset[str]:
    raw = load_character_record(str(character_id))
    camps = raw.get("camp", {})
    if not isinstance(camps, Mapping):
        return frozenset()
    return frozenset(str(key) for key in camps)


def _qingyi_additional_ability_eligibility(
    team_ids: Sequence[CharacterId],
) -> bool:
    qingyi_camps = _nanoka_camp_ids(QINGYI_ID)
    for character_id in team_ids:
        if character_id == QINGYI_ID or character_id not in _REGISTRATIONS:
            continue
        if _REGISTRATIONS[character_id].role is CharacterRole.ATTACK:
            return True
        if qingyi_camps.intersection(_nanoka_camp_ids(character_id)):
            return True
    return False


def _compile_qingyi(
    values: Mapping[str, Any],
    team_ids: Sequence[CharacterId],
    strict: bool = True,
) -> CharacterCalculationDefinition:
    _allowed(values, frozenset({"core_level", "cinema_level", "skill_levels"}))
    if strict:
        _required(values, frozenset({"core_level", "cinema_level"}))
    return compile_qingyi(
        QingyiCompileConfig(
            skill_levels=_skill_levels(values),
            core_level=_integer_with_default(values, "core_level", 1, strict),
            cinema_level=_integer_with_default(values, "cinema_level", 0, strict),
            additional_ability_eligible=(
                _qingyi_additional_ability_eligibility(team_ids)
            ),
        ),
        load_qingyi_raw_record(load_character_record(str(QINGYI_ID))),
    )


_REGISTRATIONS: dict[CharacterId, CharacterPresentationRegistration] = {
    NEKOMATA_ID: CharacterPresentationRegistration(
        character_id=NEKOMATA_ID,
        catalog=CharacterCatalogItem(
            character_id="character:1021",
            display_name="猫又",
            rarity="S",
            element="physical",
            specialty="attack",
            image_path="/characters/portrait-placeholder.svg",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.ATTACK,
        base_element=Element.PHYSICAL,
        compile_definition=_compile_nekomata,
        config_fields=_nekomata_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=NEKOMATA_ID,
            role=CharacterRole.ATTACK,
            possible_elements=frozenset({Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            damage_scopes=frozenset(
                {
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.BASIC_ATTACK, frozenset({DamageTag.BASIC_ATTACK})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.DODGE, frozenset({DamageTag.DASH_ATTACK})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.DODGE, frozenset({DamageTag.DODGE_COUNTER})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.SPECIAL_ATTACK, frozenset({DamageTag.SPECIAL_ATTACK})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.SPECIAL_ATTACK, frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.CHAIN_ATTACK, frozenset({DamageTag.CHAIN_ATTACK})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.ULTIMATE, frozenset({DamageTag.ULTIMATE})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.ASSIST, frozenset({DamageTag.ASSIST})),
                    EquipmentDamageScope(Element.PHYSICAL, SkillGroup.ASSIST, frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})),
                }
            ),
        ),
    ),
    CharacterId("character:1011"): CharacterPresentationRegistration(
        character_id=ANBY_ID,
        catalog=CharacterCatalogItem(
            character_id="character:1011",
            display_name="安比",
            rarity="A",
            element="electric",
            specialty="stun",
            image_path="/characters/portrait-placeholder.svg",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.STUN,
        base_element=Element.ELECTRIC,
        compile_definition=_compile_anby,
        config_fields=_anby_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=ANBY_ID,
            role=CharacterRole.STUN,
            possible_elements=frozenset({Element.PHYSICAL, Element.ELECTRIC}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"anby-counter-energy", "anby-cinema6-charges"}),
            damage_scopes=frozenset(
                {
                    EquipmentDamageScope(
                        Element.PHYSICAL,
                        SkillGroup.BASIC_ATTACK,
                        frozenset({DamageTag.BASIC_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.BASIC_ATTACK,
                        frozenset({DamageTag.BASIC_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.PHYSICAL,
                        SkillGroup.DODGE,
                        frozenset({DamageTag.DASH_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.DODGE,
                        frozenset({DamageTag.DODGE_COUNTER}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.SPECIAL_ATTACK,
                        frozenset({DamageTag.SPECIAL_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.SPECIAL_ATTACK,
                        frozenset(
                            {DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}
                        ),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.CHAIN_ATTACK,
                        frozenset({DamageTag.CHAIN_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.ULTIMATE,
                        frozenset({DamageTag.ULTIMATE}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.ASSIST,
                        frozenset({DamageTag.ASSIST}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.ASSIST,
                        frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK}),
                    ),
                }
            ),
        ),
    ),
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
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1311"),
            role=CharacterRole.SUPPORT,
            possible_elements=frozenset({Element.ETHER}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
        ),
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
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1431"),
            role=CharacterRole.ATTACK,
            possible_elements=frozenset({Element.PHYSICAL, Element.LINREN}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"ether-veil"}),
        ),
    ),
    CharacterId("character:1401"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1401"),
        catalog=CharacterCatalogItem(
            character_id="character:1401",
            display_name="爱丽丝",
            rarity="S",
            element="physical",
            specialty="anomaly",
            image_path="/characters/IconRole46.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.ANOMALY,
        base_element=Element.PHYSICAL,
        compile_definition=_compile_alice,
        config_fields=_alice_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1401"),
            role=CharacterRole.ANOMALY,
            possible_elements=frozenset({Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"alice-polar-assault", "alice-physical-anomaly"}),
        ),
    ),
    CharacterId("character:1411"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1411"),
        catalog=CharacterCatalogItem(
            character_id="character:1411",
            display_name="浮波柚叶",
            rarity="S",
            element="physical",
            specialty="support",
            image_path="/characters/IconRole47.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.SUPPORT,
        base_element=Element.PHYSICAL,
        compile_definition=_compile_yuzuha,
        config_fields=_yuzuha_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1411"),
            role=CharacterRole.SUPPORT,
            possible_elements=frozenset({Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"yuzuha-tanuki-wish"}),
        ),
    ),
    CharacterId("character:1361"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1361"),
        catalog=CharacterCatalogItem(
            character_id="character:1361",
            display_name="「扳机」",
            rarity="S",
            element="electric",
            specialty="stun",
            image_path="/characters/IconRole39.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.STUN,
        base_element=Element.ELECTRIC,
        compile_definition=_compile_trigger,
        config_fields=_trigger_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1361"),
            role=CharacterRole.STUN,
            possible_elements=frozenset({Element.ELECTRIC, Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"trigger-follow-up", "trigger-sniper-stance"}),
        ),
    ),
    CharacterId("character:1091"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1091"),
        catalog=CharacterCatalogItem(
            character_id="character:1091",
            display_name="雅",
            rarity="S",
            element="ice",
            specialty="anomaly",
            image_path="/characters/IconRole13.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.ANOMALY,
        base_element=Element.ICE,
        compile_definition=_compile_miyabi,
        config_fields=_miyabi_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1091"),
            role=CharacterRole.ANOMALY,
            possible_elements=frozenset(
                {Element.ICE, Element.LIESHUANG, Element.PHYSICAL}
            ),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"miyabi-icefire", "miyabi-frostburn-break"}),
        ),
    ),
    CharacterId("character:1371"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1371"),
        catalog=CharacterCatalogItem(
            character_id="character:1371",
            display_name="仪玄",
            rarity="S",
            element="ether",
            specialty="rupture",
            image_path="/characters/IconRole44.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.RUPTURE,
        base_element=Element.ETHER,
        compile_definition=_compile_yixuan,
        config_fields=_yixuan_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1371"),
            role=CharacterRole.RUPTURE,
            possible_elements=frozenset({Element.ETHER, Element.XUANMO}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"yixuan-penetration"}),
        ),
    ),
    CharacterId("character:1451"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1451"),
        catalog=CharacterCatalogItem(
            character_id="character:1451",
            display_name="卢西娅",
            rarity="S",
            element="ether",
            specialty="support",
            image_path="/characters/IconRole50.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        compile_definition=_compile_lucia,
        config_fields=_lucia_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1451"),
            role=CharacterRole.SUPPORT,
            possible_elements=frozenset({Element.ETHER}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"lucia-dream-song", "lucia-ether-curtain"}),
        ),
    ),
    CharacterId("character:1481"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1481"),
        catalog=CharacterCatalogItem(
            character_id="character:1481",
            display_name="琉音",
            rarity="S",
            element="physical",
            specialty="stun",
            image_path="/characters/IconRole54.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.STUN,
        base_element=Element.PHYSICAL,
        compile_definition=_compile_dialyn,
        config_fields=_dialyn_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1481"),
            role=CharacterRole.STUN,
            possible_elements=frozenset({Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"dialyn-good-review", "dialyn-after-sound"}),
        ),
    ),
    CharacterId("character:1331"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1331"),
        catalog=CharacterCatalogItem(
            character_id="character:1331",
            display_name="薇薇安",
            rarity="S",
            element="ether",
            specialty="anomaly",
            image_path="/characters/IconRole41.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.ANOMALY,
        base_element=Element.ETHER,
        compile_definition=_compile_vivian,
        config_fields=_vivian_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1331"),
            role=CharacterRole.ANOMALY,
            possible_elements=frozenset({Element.ETHER, Element.XUANMO}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"vivian-prophecy", "vivian-discharge"}),
        ),
    ),
    CharacterId("character:1341"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1341"),
        catalog=CharacterCatalogItem(
            character_id="character:1341",
            display_name="照",
            rarity="S",
            element="ice",
            specialty="defense",
            image_path="/characters/IconRole56.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.DEFENSE,
        base_element=Element.ICE,
        compile_definition=_compile_zhao,
        config_fields=_zhao_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1341"),
            role=CharacterRole.DEFENSE,
            possible_elements=frozenset({Element.ICE, Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"zhao-ether-curtain", "zhao-frostbite", "zhao-charged-max-hp"}),
        ),
    ),
    CharacterId("character:1251"): CharacterPresentationRegistration(
        character_id=CharacterId("character:1251"),
        catalog=CharacterCatalogItem(
            character_id="character:1251",
            display_name="青衣",
            rarity="S",
            element="electric",
            specialty="stun",
            image_path="/characters/IconRole29.webp",
            image_object_position="50% 18%",
        ),
        role=CharacterRole.STUN,
        base_element=Element.ELECTRIC,
        compile_definition=_compile_qingyi,
        config_fields=_qingyi_fields,
        equipment_capabilities=EquipmentOwnerCapabilities(
            character_id=CharacterId("character:1251"),
            role=CharacterRole.STUN,
            possible_elements=frozenset({Element.ELECTRIC, Element.PHYSICAL}),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
            mechanisms=frozenset({"qingyi-flashover", "qingyi-subjugation"}),
            damage_scopes=frozenset(
                {
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.BASIC_ATTACK,
                        frozenset({DamageTag.BASIC_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.PHYSICAL,
                        SkillGroup.BASIC_ATTACK,
                        frozenset({DamageTag.BASIC_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.PHYSICAL,
                        SkillGroup.DODGE,
                        frozenset({DamageTag.DASH_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.DODGE,
                        frozenset({DamageTag.DODGE_COUNTER}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.SPECIAL_ATTACK,
                        frozenset({DamageTag.SPECIAL_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.SPECIAL_ATTACK,
                        frozenset(
                            {DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}
                        ),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.CHAIN_ATTACK,
                        frozenset({DamageTag.CHAIN_ATTACK}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.ULTIMATE,
                        frozenset({DamageTag.ULTIMATE}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.ASSIST,
                        frozenset({DamageTag.ASSIST}),
                    ),
                    EquipmentDamageScope(
                        Element.ELECTRIC,
                        SkillGroup.ASSIST,
                        frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK}),
                    ),
                }
            ),
        ),
    ),
}


def _drive_stat_preview(
    stat: DriveDiscStatKey,
    value_per_roll: float,
    roll_count: int,
) -> DriveDiscStatPreviewView:
    total = value_per_roll * roll_count
    return DriveDiscStatPreviewView(
        stat_key=stat.value,
        label=drive_disc_stat_label(stat),
        value_per_roll=value_per_roll,
        display_value_per_roll=display_drive_disc_value(stat, value_per_roll),
        roll_count=roll_count,
        total_value=total,
        display_total_value=display_drive_disc_value(stat, total),
    )


def _base_provenance(
    character_id: CharacterId,
    display_name: str,
    base_stats,
) -> tuple[BuildContributionView, ...]:
    source_id = f"{character_id}:base-stats"
    values = {
        "hp": base_stats.hp,
        "attack": base_stats.attack,
        "defense": base_stats.defense,
        "impact": base_stats.impact,
        "crit_rate": base_stats.crit_rate,
        "crit_damage": base_stats.crit_damage,
        "anomaly_mastery": base_stats.anomaly_mastery,
        "anomaly_proficiency": base_stats.anomaly_proficiency,
        "penetration_rate": base_stats.penetration_rate,
        "penetration_flat": base_stats.penetration_flat,
        "energy_regen": base_stats.energy_regen,
    }
    result = []
    for stat, value in values.items():
        numeric = float(value.value) if isinstance(value, Resolved) else None
        unresolved = value.notes if hasattr(value, "notes") else None
        result.append(
            BuildContributionView(
                character_id=str(character_id),
                contribution_id=f"{source_id}:{stat}",
                source_id=source_id,
                source_type="character",
                source_label=f"{display_name}·角色基础",
                stat=stat,
                layer="base-value",
                value=numeric,
                element=None,
                unresolved=unresolved,
            )
        )
    for element, value in base_stats.element_damage_bonus.items():
        numeric = float(value.value) if isinstance(value, Resolved) else None
        unresolved = value.notes if hasattr(value, "notes") else None
        result.append(
            BuildContributionView(
                character_id=str(character_id),
                contribution_id=f"{source_id}:element-damage:{element.value}",
                source_id=source_id,
                source_type="character",
                source_label=f"{display_name}·角色基础",
                stat="element_damage_bonus",
                layer="base-value",
                value=numeric,
                element=element.value,
                unresolved=unresolved,
            )
        )
    return tuple(result)


def _drive_disc_preview_views(
    resolution,
) -> tuple[DriveDiscPreviewView, ...]:
    result = []
    for disc in sorted(resolution.build_input.discs, key=lambda item: int(item.slot)):
        raw = load_drive_disc_raw_record(disc.set_id)
        main = (
            _drive_stat_preview(
                disc.main_stat,
                DRIVE_DISC_MAIN_STAT_VALUES[disc.main_stat],
                1,
            )
            if disc.main_stat is not None
            else None
        )
        substats = tuple(
            _drive_stat_preview(
                item.stat,
                DRIVE_DISC_SUBSTAT_VALUES[item.stat],
                item.roll_count,
            )
            for item in disc.substats
        )
        result.append(
            DriveDiscPreviewView(
                slot=int(disc.slot),
                set_id=str(disc.set_id),
                set_name=raw.name,
                main_stat=main,
                substats=substats,
                total_rolls=disc.total_roll_count,
                complete=disc.complete,
            )
        )
    return tuple(result)


def supported_character_registrations() -> (
    tuple[CharacterPresentationRegistration, ...]
):
    return tuple(_REGISTRATIONS.values())


def registration_for(
    character_id: str | CharacterId,
) -> CharacterPresentationRegistration:
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
        (
            condition
            if condition.resolution.value == "static"
            else replace(
                condition,
                value=selected.get(str(condition.condition_id), condition.value),
            )
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
    condition_context: Mapping[str, bool | None] | None = None,
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
    if condition_context is not None and condition_values is not None:
        if dict(condition_context) != dict(condition_values):
            raise ValueError("condition_context and condition_values disagree")
    supplied_context = (
        condition_context if condition_context is not None else condition_values
    )
    if supplied_context is None:
        raw_values: Mapping[str, bool | None] = {}
    elif not isinstance(supplied_context, Mapping):
        raise ValueError("condition_values must be an object")
    else:
        raw_values = supplied_context
    resolution = compile_wengine(
        WEngineBuildInput(
            WEngineId(str(wengine_id)),
            owner,
            level=level,
            refinement=refinement,
        ),
        owner_capabilities=registration.equipment_capabilities,
    )
    known_conditions = {item.condition_id for item in resolution.scenario_conditions}
    selected_values = {
        str(condition_id): value
        for condition_id, value in raw_values.items()
        if str(condition_id) in {str(item) for item in known_conditions}
    }
    if any(
        value is not None and not isinstance(value, bool)
        for value in raw_values.values()
    ):
        raise ValueError("W-Engine scenario conditions must be boolean or null")
    conditions = tuple(
        (
            condition
            if condition.resolution.value == "static"
            else replace(
                condition,
                value=selected_values.get(str(condition.condition_id), condition.value),
            )
        )
        for condition in resolution.scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id="wengine-preview",
        current_operator=owner,
        conditions=conditions,
    )
    from .assembler import build_wengine_editor_view

    return build_wengine_editor_view(
        resolution,
        scenario=scenario,
        team_character_ids=team_ids,
        condition_context=raw_values,
    )


def build_registered_drive_disc_editor_view(
    equipped_character_id: str | CharacterId,
    discs: Sequence[Mapping[str, object]],
    *,
    team_character_ids: Sequence[str | CharacterId] = (),
    condition_context: Mapping[str, bool | None] | None = None,
):
    """Build an owner-qualified editor view for one six-slot configuration."""

    owner = CharacterId(str(equipped_character_id))
    registration = registration_for(owner)
    team_ids = tuple(CharacterId(str(item)) for item in team_character_ids) or (owner,)
    if owner not in team_ids or len(set(team_ids)) != len(team_ids):
        raise ValueError("Drive Disc owner must belong to a unique active team")
    parsed = _parse_drive_disc_inputs(discs)
    resolution = compile_drive_discs(
        DriveDiscBuildInput(owner, parsed),
        owner_capabilities=registration.equipment_capabilities,
    )
    raw_context = dict(condition_context or {})
    if any(
        value is not None and not isinstance(value, bool)
        for value in raw_context.values()
    ):
        raise ValueError("Drive Disc scenario conditions must be boolean or null")
    conditions = tuple(
        (
            replace(
                item,
                value=raw_context.get(str(item.condition_id), item.value),
            )
            if item.resolution.value == "user-selected"
            else item
        )
        for item in resolution.scenario_conditions
    )
    scenario = CalculationScenario(
        scenario_id="drive-disc-preview",
        current_operator=owner,
        conditions=conditions,
    )
    from .assembler import build_drive_disc_editor_view

    return build_drive_disc_editor_view(
        resolution,
        scenario=scenario,
        team_character_ids=team_ids,
        condition_context=raw_context,
    )


def build_registered_build_preview(
    character_id: str | CharacterId,
    *,
    level: int = 60,
    wengine_id: str | None = None,
    wengine_level: int = 60,
    wengine_refinement: int = 1,
    discs: Sequence[Mapping[str, object]] = (),
):
    """Assemble one live equipment panel through the production pipeline.

    This is deliberately the only presentation entry point that knows how a
    character, W-Engine, and partial Drive Disc input become a panel.  It
    never executes combat rules: conditional rule items are returned by the
    existing equipment editor endpoints and remain separate from this static
    panel preview.
    """

    owner = CharacterId(str(character_id))
    registration = registration_for(owner)
    base_stats = character_base_stats(owner, level=level)
    contributions: list[BuildStatContribution] = []
    contributions.extend(character_base_stat_contributions(owner))
    diagnostics = []
    if wengine_id:
        wengine = compile_wengine(
            WEngineBuildInput(
                WEngineId(str(wengine_id)),
                owner,
                level=int(wengine_level),
                refinement=int(wengine_refinement),
            ),
            owner_capabilities=registration.equipment_capabilities,
        )
        contributions.extend(wengine.contributions)
        diagnostics.extend(wengine.diagnostics)

    parsed_discs = _parse_drive_disc_inputs(discs)
    drive_resolution = compile_drive_discs(
        DriveDiscBuildInput(owner, parsed_discs),
        owner_capabilities=registration.equipment_capabilities,
    )
    contributions.extend(drive_resolution.contributions)
    diagnostics.extend(drive_resolution.diagnostics)

    assembled = assemble_build(
        CharacterBuildDefinition(
            character_id=owner,
            level=level,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=base_stats,
            contributions=tuple(contributions),
        ),
    )
    diagnostics.extend(assembled.diagnostics)
    diagnostic_views = tuple(
        diagnostic_view(item) for item in dict.fromkeys(diagnostics)
    )
    display_name = registration.catalog.display_name
    base_snapshot = panel_snapshot_view(CharacterSnapshot(owner, level, base_stats))
    current_snapshot = panel_snapshot_view(assembled.character_snapshot)
    provenance = (
        *_base_provenance(owner, display_name, base_stats),
        *(build_contribution_view(item) for item in assembled.provenance),
    )
    complete = (
        assembled.complete
        and drive_resolution.complete
        and not any(item.blocking for item in diagnostics)
    )
    return BuildPreviewView(
        schema_version=SCHEMA_VERSION,
        character_id=str(owner),
        display_name=display_name,
        level=level,
        build_mode=BuildMode.EQUIPMENT_BUILD.value,
        base_stats=base_snapshot.stats,
        out_of_combat_stats=current_snapshot.stats,
        provenance=provenance,
        drive_discs=_drive_disc_preview_views(drive_resolution),
        set_counts=tuple(
            {"set_id": str(set_id), "count": count}
            for set_id, count in drive_resolution.set_counts
        ),
        diagnostics=diagnostic_views,
        complete=complete,
    )


def _parse_drive_disc_inputs(
    raw_value: Sequence[Mapping[str, object]],
) -> tuple[EquippedDriveDisc, ...]:
    parsed = []
    for raw in raw_value:
        raw_substats = raw.get("substats", ())
        if not isinstance(raw_substats, Sequence) or isinstance(
            raw_substats,
            (str, bytes),
        ):
            raise ValueError("Drive Disc substats must be an array")
        substats = []
        for item in raw_substats:
            if not isinstance(item, Mapping):
                raise ValueError("Drive Disc substat must be an object")
            substats.append(
                DriveDiscSubstatRoll(
                    DriveDiscStatKey(str(item.get("stat", ""))),
                    int(str(item.get("roll_count", 0))),
                )
            )
        raw_main_stat = raw.get("main_stat")
        main_stat = (
            None
            if raw_main_stat is None or str(raw_main_stat) == ""
            else DriveDiscStatKey(str(raw_main_stat))
        )
        parsed.append(
            EquippedDriveDisc(
                slot=DriveDiscSlot(int(str(raw.get("slot", 0)))),
                set_id=stable_set_id(
                    str(raw.get("set_id", "")).removeprefix("drive-disc:")
                ),
                main_stat=main_stat,
                substats=tuple(substats),
            )
        )
    return tuple(parsed)


__all__ = [
    "CharacterPresentationRegistration",
    "compile_registered_definition",
    "config_fields_for",
    "build_registered_editor_view",
    "build_registered_drive_disc_editor_view",
    "build_registered_build_preview",
    "build_registered_wengine_editor_view",
    "registration_for",
    "supported_character_registrations",
]
