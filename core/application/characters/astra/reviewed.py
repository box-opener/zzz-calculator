"""Manually reviewed Astra semantics.

This module contains no source倍率 tables or copied game text.  It only maps
raw move names to the domain taxonomy and to explicit scenario relationships.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.types import DamageTag, MoveId, SkillGroup

from ...moves import MultiplierRelation


ARIA_ACTIVE_CONDITION_KEY = "aria_active"
CORE_ATTACK_BUFF_ACTIVE_CONDITION_KEY = "core_attack_buff_active"
RHAPSODY_STAGE3_MIN_CONDITION_KEY = "rhapsody_stage3_min"
RHAPSODY_STAGE3_FULL_CONDITION_KEY = "rhapsody_stage3_full"
ENERGY_AVAILABLE_CONDITION_KEY = "energy_available"
WIND_CHIME_COUNT_PARAMETER_KEY = "wind_chime_tremolo_count"


@dataclass(frozen=True, slots=True)
class AstraDamageParameter:
    variant_key: str
    parameter_name: str
    condition_key: str | None = None


@dataclass(frozen=True, slots=True)
class AstraMoveSpec:
    entry_key: str
    move_id: MoveId
    display_name: str
    source_name: str
    skill_group: SkillGroup
    damage_tags: frozenset[DamageTag]
    parameters: tuple[AstraDamageParameter, ...]
    multiplier_relation: MultiplierRelation
    stage_index: int | None = None
    requires_aria: bool = False
    repeat_parameter_key: str | None = None


@dataclass(frozen=True, slots=True)
class AstraReviewedMapping:
    moves: tuple[AstraMoveSpec, ...]


def _parameter(
    variant_key: str,
    parameter_name: str,
    *,
    condition_key: str | None = None,
) -> AstraDamageParameter:
    return AstraDamageParameter(
        variant_key=variant_key,
        parameter_name=parameter_name,
        condition_key=condition_key,
    )


def _move(
    entry_key: str,
    move_id: str,
    display_name: str,
    source_name: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    parameters: tuple[AstraDamageParameter, ...],
    relation: MultiplierRelation,
    *,
    stage_index: int | None = None,
    requires_aria: bool = False,
    repeat_parameter_key: str | None = None,
) -> AstraMoveSpec:
    return AstraMoveSpec(
        entry_key=entry_key,
        move_id=MoveId(move_id),
        display_name=display_name,
        source_name=source_name,
        skill_group=skill_group,
        damage_tags=damage_tags,
        parameters=parameters,
        multiplier_relation=relation,
        stage_index=stage_index,
        requires_aria=requires_aria,
        repeat_parameter_key=repeat_parameter_key,
    )


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_BASIC_TREMOLO = frozenset({DamageTag.BASIC_ATTACK, DamageTag.TREMOLO})
_SPECIAL_TREMOLO = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.TREMOLO})
_EX_SPECIAL_TREMOLO = frozenset(
    {
        DamageTag.SPECIAL_ATTACK,
        DamageTag.EX_SPECIAL_ATTACK,
        DamageTag.TREMOLO,
    }
)
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_STAGE_NAMES = ("一", "二", "三", "四", "五")


ASTRA_REVIEWED_MAPPING = AstraReviewedMapping(
    moves=(
        _move(
            "basic-rhapsody-1",
            "move:astra:rhapsody",
            "普通攻击：《随想曲》（一段）",
            "普通攻击：《随想曲》",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (_parameter("stage-1", "一段伤害倍率"),),
            MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=1,
        ),
        _move(
            "basic-rhapsody-2",
            "move:astra:rhapsody",
            "普通攻击：《随想曲》（二段）",
            "普通攻击：《随想曲》",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (_parameter("stage-2", "二段伤害倍率"),),
            MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=2,
        ),
        _move(
            "basic-rhapsody-3",
            "move:astra:rhapsody",
            "普通攻击：《随想曲》（三段）",
            "普通攻击：《随想曲》",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            (
                _parameter(
                    "minimum",
                    "三段最小伤害倍率",
                    condition_key=RHAPSODY_STAGE3_MIN_CONDITION_KEY,
                ),
                _parameter(
                    "full-charge",
                    "三段最大伤害倍率",
                    condition_key=RHAPSODY_STAGE3_FULL_CONDITION_KEY,
                ),
            ),
            MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
        ),
        *tuple(
            _move(
                f"basic-interlude-{stage}",
                "move:astra:interlude",
                f"普通攻击：间奏（{stage}段）",
                "普通攻击：间奏",
                SkillGroup.BASIC_ATTACK,
                _BASIC_TREMOLO,
                (
                    _parameter(
                        f"stage-{stage}",
                        f"{_STAGE_NAMES[stage - 1]}段伤害倍率",
                    ),
                ),
                MultiplierRelation.SEQUENTIAL_STAGE,
                stage_index=stage,
                requires_aria=True,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-chorus",
            "move:astra:chorus",
            "普通攻击：副歌",
            "普通攻击：副歌",
            SkillGroup.BASIC_ATTACK,
            _BASIC_TREMOLO,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
            requires_aria=True,
        ),
        _move(
            "basic-finale",
            "move:astra:finale",
            "普通攻击：终曲",
            "普通攻击：终曲",
            SkillGroup.BASIC_ATTACK,
            _BASIC_TREMOLO,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
            requires_aria=True,
        ),
        _move(
            "dodge-dash",
            "move:astra:dodge-dash",
            "冲刺攻击：《蚀月奏》",
            "冲刺攻击：《蚀月奏》",
            SkillGroup.DODGE,
            _DASH,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "dodge-counter",
            "move:astra:dodge-counter",
            "闪避反击：《折伞华尔兹》",
            "闪避反击：《折伞华尔兹》",
            SkillGroup.DODGE,
            _COUNTER,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "special-wind-chime",
            "move:astra:wind-chime",
            "特殊技：《风铃与旧约》",
            "特殊技：《风铃与旧约》",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL_TREMOLO,
            (_parameter("unit", "最小伤害倍率"),),
            MultiplierRelation.UNIT_REPEAT,
            repeat_parameter_key=WIND_CHIME_COUNT_PARAMETER_KEY,
        ),
        _move(
            "chain-concerto",
            "move:astra:concerto",
            "连携技：《微醺协奏》",
            "连携技：《微醺协奏》",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "ultimate-sonata",
            "move:astra:sonata",
            "终结技：《幻想式奏鸣》",
            "终结技：《幻想式奏鸣》",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "assist-quick-fireworks",
            "move:astra:quick-fireworks",
            "快速支援：《一川烟火》",
            "快速支援：《一川烟火》",
            SkillGroup.ASSIST,
            _ASSIST,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "assist-follow-up",
            "move:astra:follow-up",
            "支援突击：《三生初见》",
            "支援突击：《三生初见》",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            (_parameter("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
    )
)


__all__ = [
    "ARIA_ACTIVE_CONDITION_KEY",
    "CORE_ATTACK_BUFF_ACTIVE_CONDITION_KEY",
    "ENERGY_AVAILABLE_CONDITION_KEY",
    "RHAPSODY_STAGE3_FULL_CONDITION_KEY",
    "RHAPSODY_STAGE3_MIN_CONDITION_KEY",
    "ASTRA_REVIEWED_MAPPING",
    "AstraDamageParameter",
    "AstraMoveSpec",
    "AstraReviewedMapping",
    "WIND_CHIME_COUNT_PARAMETER_KEY",
]
