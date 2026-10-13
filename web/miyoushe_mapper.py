"""Strict field mapper for CN ZZZ official character-builder details."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
import math
from typing import Any

from core.application.equipment import load_wengine_raw_record, reviewed_mapping_for
from core.presentation import (
    supported_character_catalog,
    supported_drive_disc_catalog,
    supported_wengine_catalog,
)
from core.presentation.base_stats import character_base_stats
from core.types import CharacterStat, DriveDiscStatKey


_DRIVE_PROPERTY_TO_STAT: dict[int, DriveDiscStatKey] = {
    11101: DriveDiscStatKey.HP_FLAT,
    11102: DriveDiscStatKey.HP_PERCENT,
    12101: DriveDiscStatKey.ATTACK_FLAT,
    12102: DriveDiscStatKey.ATTACK_PERCENT,
    13101: DriveDiscStatKey.DEFENSE_FLAT,
    13102: DriveDiscStatKey.DEFENSE_PERCENT,
    12202: DriveDiscStatKey.IMPACT_PERCENT,
    20101: DriveDiscStatKey.CRIT_RATE,
    21101: DriveDiscStatKey.CRIT_DAMAGE,
    23101: DriveDiscStatKey.PENETRATION_RATE,
    23201: DriveDiscStatKey.PENETRATION_FLAT,
    30501: DriveDiscStatKey.ENERGY_REGEN_PERCENT,
    31201: DriveDiscStatKey.ANOMALY_PROFICIENCY_FLAT,
    31402: DriveDiscStatKey.ANOMALY_MASTERY_PERCENT,
    31501: DriveDiscStatKey.PHYSICAL_DAMAGE_BONUS,
    31601: DriveDiscStatKey.FIRE_DAMAGE_BONUS,
    31701: DriveDiscStatKey.ICE_DAMAGE_BONUS,
    31801: DriveDiscStatKey.ELECTRIC_DAMAGE_BONUS,
    31901: DriveDiscStatKey.ETHER_DAMAGE_BONUS,
    32301: DriveDiscStatKey.WIND_DAMAGE_BONUS,
}

_PERCENT_PROPERTY_IDS = frozenset(
    {
        11102,
        12102,
        13102,
        12202,
        20101,
        21101,
        23101,
        30501,
        31402,
        31501,
        31601,
        31701,
        31801,
        31901,
        32301,
    }
)

_ENGINE_PROPERTY_TO_STAT: dict[int, CharacterStat] = {
    11101: CharacterStat.HP,
    11102: CharacterStat.HP,
    12101: CharacterStat.ATTACK,
    12102: CharacterStat.ATTACK,
    13101: CharacterStat.DEFENSE,
    13102: CharacterStat.DEFENSE,
    12201: CharacterStat.IMPACT,
    12202: CharacterStat.IMPACT,
    20101: CharacterStat.CRIT_RATE,
    21101: CharacterStat.CRIT_DAMAGE,
    23101: CharacterStat.PENETRATION_RATE,
    23201: CharacterStat.PENETRATION_FLAT,
    30501: CharacterStat.ENERGY_REGEN,
    31201: CharacterStat.ANOMALY_PROFICIENCY,
    31401: CharacterStat.ANOMALY_MASTERY,
    31402: CharacterStat.ANOMALY_MASTERY,
}

_BASE_PROPERTY_ID_BY_STAT = {
    CharacterStat.HP: 11101,
    CharacterStat.ATTACK: 12101,
    CharacterStat.DEFENSE: 13101,
}


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    raise ValueError(f"{label} must be an integer")


def _number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        number = float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{label} must be finite and non-negative")
    return number


def _property_id(raw: Mapping[str, Any], label: str) -> int:
    return _integer(raw.get("property_id"), f"{label}.property_id")


def _property_value(raw: Mapping[str, Any], property_id: int, label: str) -> float:
    value = _number(raw.get("base"), f"{label}.base")
    # The official builder's static property renderer appends `%` to these
    # property families. Its API stores that number in percentage points;
    # this calculator stores ratios such as 0.24 for 24%.
    return value / 100.0 if property_id in _PERCENT_PROPERTY_IDS else value


def _property_list(value: object, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    if any(not isinstance(item, Mapping) for item in value):
        raise ValueError(f"{label} contains an invalid property")
    return value  # type: ignore[return-value]


def _catalog_numeric_id(value: str, prefix: str) -> int:
    if not value.startswith(prefix):
        raise ValueError(f"unsupported registry ID: {value}")
    return _integer(value[len(prefix):], "registry ID")


def _registered_character_id(source_id: int) -> str | None:
    expected = f"character:{source_id}"
    return next(
        (item.character_id for item in supported_character_catalog() if item.character_id == expected),
        None,
    )


def _registered_wengine_id(source_id: int) -> str | None:
    expected = f"wengine:{source_id}"
    return next(
        (item.wengine_id for item in supported_wengine_catalog() if item.wengine_id == expected),
        None,
    )


def _registered_drive_disc_set(source_id: int) -> str | None:
    expected = f"drive-disc:{source_id}"
    return next(
        (item.set_id for item in supported_drive_disc_catalog() if item.set_id == expected),
        None,
    )


def _compile_progress(avatar: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, object]]]:
    progress: dict[str, Any] = {}
    diagnostics: list[dict[str, object]] = []
    rank_value = avatar.get("rank")
    rank: int | None = None
    if rank_value is not None:
        try:
            rank = _integer(rank_value, "avatar.rank")
        except ValueError:
            diagnostics.append({"code": "cinema-unreadable", "blocking": False, "message": "影画等级字段格式无法识别，保留当前设置。"})
        else:
            if not 0 <= rank <= 6:
                diagnostics.append({"code": "cinema-out-of-range", "blocking": False, "message": "影画等级超出 0–6，保留当前设置。"})
                rank = None
    if rank is not None:
        progress["cinema_level"] = rank

    skills = avatar.get("skills")
    if not isinstance(skills, list):
        diagnostics.append({"code": "skills-missing", "blocking": False, "message": "米游社未提供技能等级，保留当前设置。"})
        return progress, diagnostics
    if skills:
        diagnostics.append({
            "code": "skills-semantics-unverified",
            "blocking": False,
            "message": "米游社返回了技能项，但尚未核实技能槽位及影画加成口径，保留当前核心技和技能等级。",
        })
    else:
        diagnostics.append({
            "code": "skills-empty",
            "blocking": False,
            "message": "米游社没有返回可用的技能等级，保留当前核心技和技能等级。",
        })
    return progress, diagnostics


def _map_disc_set(equip_suit: object) -> str | None:
    if not isinstance(equip_suit, Mapping):
        return None
    raw_id = equip_suit.get("suit_id")
    if raw_id is not None:
        try:
            return _registered_drive_disc_set(_integer(raw_id, "equip_suit.suit_id"))
        except ValueError:
            return None
    # Some official detail response versions expose a localized display name
    # before the numeric suit ID. Use exact, unique registry names only.
    name = equip_suit.get("name") or equip_suit.get("name_mi18n")
    if not isinstance(name, str) or not name:
        return None
    matches = [item.set_id for item in supported_drive_disc_catalog() if item.display_name == name]
    return matches[0] if len(matches) == 1 else None


def _map_drive_discs(raw_equip: object) -> tuple[list[dict[str, Any]], list[dict[str, object]]]:
    if not isinstance(raw_equip, list):
        return [], [{"code": "drive-discs-missing", "blocking": False, "message": "米游社未返回驱动盘列表，保留当前配置。"}]
    result: list[dict[str, Any]] = []
    diagnostics: list[dict[str, object]] = []
    seen_slots: set[int] = set()
    for item_index, raw_disc in enumerate(raw_equip):
        if not isinstance(raw_disc, Mapping):
            diagnostics.append({"code": "drive-disc-invalid", "blocking": True, "message": f"第 {item_index + 1} 个驱动盘格式无法识别，不能应用这份角色构筑。"})
            continue
        try:
            slot = _integer(raw_disc.get("equipment_type"), "equip.equipment_type")
            level = _integer(raw_disc.get("level"), "equip.level")
        except ValueError:
            diagnostics.append({"code": "drive-disc-slot-invalid", "blocking": True, "message": "驱动盘槽位或等级无法识别，不能应用这份角色构筑。"})
            continue
        if not 1 <= slot <= 6 or slot in seen_slots or not 0 <= level <= 15:
            diagnostics.append({"code": "drive-disc-slot-invalid", "blocking": True, "message": f"驱动盘槽位 {slot} 或等级 {level} 无效，不能应用这份角色构筑。"})
            continue
        set_id = _map_disc_set(raw_disc.get("equip_suit"))
        if set_id is None:
            diagnostics.append({"code": "drive-disc-set-unknown", "blocking": True, "message": f"{slot} 号位套装没有本地精确映射，不能应用这份角色构筑。"})
            continue
        main_properties = _property_list(raw_disc.get("main_properties"), f"equip[{item_index}].main_properties")
        if len(main_properties) != 1:
            diagnostics.append({"code": "drive-disc-main-missing", "blocking": True, "message": f"{slot} 号位主词条数量无法识别，不能应用这份角色构筑。"})
            continue
        main_property = main_properties[0]
        try:
            main_property_id = _property_id(main_property, f"equip[{item_index}].main_properties[0]")
            main_stat = _DRIVE_PROPERTY_TO_STAT[main_property_id]
            main_value = _property_value(main_property, main_property_id, f"equip[{item_index}].main_properties[0]")
        except (ValueError, KeyError):
            diagnostics.append({"code": "drive-disc-main-unsupported", "blocking": True, "message": f"{slot} 号位主词条 ID 无本地映射，不能应用这份角色构筑。"})
            continue
        raw_substats = raw_disc.get("properties")
        if not isinstance(raw_substats, list):
            diagnostics.append({"code": "drive-disc-substats-missing", "blocking": True, "message": f"{slot} 号位副词条列表无法识别，不能应用这份角色构筑。"})
            raw_substats = []
        if len(raw_substats) > 4:
            diagnostics.append({"code": "drive-disc-too-many-substats", "blocking": True, "message": f"{slot} 号位副词条超过四条，不能应用这份角色构筑。"})
            continue
        substats = []
        for sub_index, raw_sub in enumerate(raw_substats):
            if not isinstance(raw_sub, Mapping):
                diagnostics.append({"code": "drive-disc-substat-invalid", "blocking": True, "message": f"{slot} 号位第 {sub_index + 1} 条副词条格式无法识别，不能应用这份角色构筑。"})
                continue
            try:
                property_id = _property_id(raw_sub, f"equip[{item_index}].properties[{sub_index}]")
                stat = _DRIVE_PROPERTY_TO_STAT[property_id]
                value = _property_value(raw_sub, property_id, f"equip[{item_index}].properties[{sub_index}]")
            except (ValueError, KeyError):
                diagnostics.append({"code": "drive-disc-substat-unsupported", "blocking": True, "message": f"{slot} 号位副词条 ID 无本地映射，不能应用这份角色构筑。"})
                continue
            if stat == main_stat or any(existing["stat"] == stat.value for existing in substats):
                diagnostics.append({"code": "drive-disc-substat-duplicate", "blocking": True, "message": f"{slot} 号位出现重复主/副词条，不能应用这份角色构筑。"})
                continue
            substats.append({"stat": stat.value, "value": value})
        result.append({
            "slot": slot,
            "set_id": set_id,
            "main_stat": main_stat.value,
            "main_stat_value": main_value,
            "level": level,
            "substats": substats,
        })
        seen_slots.add(slot)
    return result, diagnostics


def _map_wengine(raw_weapon: object) -> tuple[dict[str, Any] | None, list[dict[str, object]]]:
    if raw_weapon is None:
        return None, []
    if not isinstance(raw_weapon, Mapping):
        return None, [{"code": "wengine-invalid", "blocking": False, "message": "音擎数据格式无法识别，保留当前配置。"}]
    diagnostics: list[dict[str, object]] = []
    try:
        source_id = _integer(raw_weapon.get("id"), "weapon.id")
    except ValueError:
        return None, [{"code": "wengine-id-invalid", "blocking": False, "message": "音擎 ID 无法识别，保留当前配置。"}]
    wengine_id = _registered_wengine_id(source_id)
    if wengine_id is None:
        return None, [{"code": "wengine-unknown", "blocking": False, "message": f"音擎 ID {source_id} 未注册到本地数据，保留当前配置。"}]
    try:
        level = _integer(raw_weapon.get("level"), "weapon.level")
        raw_record = load_wengine_raw_record(wengine_id)
        mapping = reviewed_mapping_for(raw_record.wengine_id)
    except (ValueError, KeyError):
        return None, [{"code": "wengine-data-invalid", "blocking": False, "message": "音擎等级或本地记录无法识别，保留当前配置。"}]
    if not 1 <= level <= 60:
        return None, [{"code": "wengine-level-invalid", "blocking": False, "message": "音擎等级超出 1–60，保留当前配置。"}]
    patch: dict[str, Any] = {"id": wengine_id, "level": level}
    refinement = raw_weapon.get("refinement")
    if refinement is not None:
        try:
            refinement_value = _integer(refinement, "weapon.refinement")
            if not 1 <= refinement_value <= 5:
                raise ValueError("out of range")
            patch["refinement"] = refinement_value
        except ValueError:
            diagnostics.append({"code": "wengine-refinement-invalid", "blocking": False, "message": "音擎精炼字段无法识别，保留当前设置。"})
            return None, diagnostics
    else:
        diagnostics.append({"code": "wengine-refinement-missing", "blocking": False, "message": "官方角色详情没有提供可确认的音擎精炼等级，保留当前音擎配置。"})
        return None, diagnostics

    main_properties = raw_weapon.get("main_properties")
    advanced_properties = raw_weapon.get("properties")
    if not isinstance(main_properties, list) or not isinstance(advanced_properties, list):
        diagnostics.append({"code": "wengine-stats-missing", "blocking": False, "message": "官方角色详情没有提供音擎实装属性，低于60级时计算结果会提示缺少数据。"})
        return patch, diagnostics
    expected_base_id = _BASE_PROPERTY_ID_BY_STAT.get(raw_record.base_stat)
    main_property = None
    for item in main_properties:
        if not isinstance(item, Mapping):
            continue
        try:
            if _property_id(item, "weapon.main_properties") == expected_base_id:
                main_property = item
                break
        except ValueError:
            continue
    advanced_property = next(
        (
            item for item in advanced_properties
            if isinstance(item, Mapping)
            and _ENGINE_PROPERTY_TO_STAT.get(
                int(item["property_id"]) if str(item.get("property_id", "")).isdecimal() else -1
            ) is mapping.advanced_stat
        ),
        None,
    )
    if main_property is None or advanced_property is None:
        diagnostics.append({"code": "wengine-source-stat-unmapped", "blocking": False, "message": "米游社音擎词条 ID 与本地注册属性未能一一对应，低于60级的精确面板不可用。"})
        return patch, diagnostics
    try:
        base_value = _number(main_property.get("base"), "weapon.main_properties.base")
        advanced_id = _property_id(advanced_property, "weapon.properties[0]")
        advanced_value = _property_value(advanced_property, advanced_id, "weapon.properties[0]")
    except ValueError:
        diagnostics.append({"code": "wengine-source-stat-invalid", "blocking": False, "message": "米游社音擎实装属性值格式无法识别，低于60级的精确面板不可用。"})
        return patch, diagnostics
    patch["source_base_value"] = base_value
    patch["source_advanced_stat_value"] = advanced_value
    return patch, diagnostics


def map_miyoushe_avatar_detail(
    detail: Mapping[str, Any],
    expected_character_id: str,
) -> dict[str, Any]:
    """Convert only source equipment/progression fields into a local patch.

    Final character panel values are intentionally ignored. Numeric equipment
    properties are kept as exact values; no roll count is reverse-derived.
    """

    expected_id = _catalog_numeric_id(expected_character_id, "character:")
    registered_id = _registered_character_id(expected_id)
    if registered_id is None:
        raise ValueError(f"unknown local character registry ID: {expected_character_id}")
    avatar = detail.get("avatar")
    if not isinstance(avatar, Mapping):
        raise ValueError("official avatar detail is missing the avatar object")
    if _integer(avatar.get("id"), "avatar.id") != expected_id:
        raise ValueError("official avatar ID does not match the selected local character")
    compile_config, diagnostics = _compile_progress(avatar)
    character_level: int | None = None
    try:
        source_level = _integer(avatar.get("level"), "avatar.level")
        if not 1 <= source_level <= 60:
            raise ValueError("avatar.level out of range")
        # Do not update a level when the local registry lacks the level curve
        # needed to calculate that character's base panel accurately.
        character_base_stats(registered_id, level=source_level)
        character_level = source_level
    except ValueError:
        diagnostics.append({
            "code": "character-level-unavailable",
            "blocking": False,
            "message": "角色等级缺少本地对应的白值成长记录，保留当前等级，避免错误换算角色基础面板。",
        })
    wengine_patch, wengine_diagnostics = _map_wengine(detail.get("weapon"))
    equip_present = "equip" in detail
    equip_value = detail.get("equip")
    drive_discs, drive_diagnostics = _map_drive_discs(
        [] if equip_present and equip_value is None else equip_value
    )
    diagnostics.extend(wengine_diagnostics)
    diagnostics.extend(drive_diagnostics)
    return {
        "character_id": registered_id,
        "display_name": str(avatar.get("name_mi18n") or avatar.get("full_name_mi18n") or expected_character_id),
        "character_level": character_level,
        "compile_config": compile_config,
        "wengine": wengine_patch,
        "wengine_present": "weapon" in detail,
        "wengine_explicit_null": "weapon" in detail and detail.get("weapon") is None,
        "drive_discs": drive_discs,
        "drive_discs_present": isinstance(equip_value, list),
        "drive_discs_explicit_null": equip_present and equip_value is None,
        "diagnostics": diagnostics,
        "can_apply": not any(item.get("blocking") is True for item in diagnostics),
    }


__all__ = ["map_miyoushe_avatar_detail"]
