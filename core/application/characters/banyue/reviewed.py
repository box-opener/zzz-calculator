"""Reviewed Nanoka 3.2 move identities for BanYue (character:1471)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import BANYUE_ID


BANYUE_CORE_BUFF_ACTIVE = ScenarioConditionId(
    "condition:banyue:core-enhanced-special-or-assist-buff-active"
)
BANYUE_TREMOR_ACTIVE = ScenarioConditionId("condition:banyue:tremor-active")

BANYUE_BASIC_ZHENGRONG_MOVE_ID = MoveId("move:banyue:basic-zhengrong")
BANYUE_BASIC_CUIWEI_MOVE_ID = MoveId("move:banyue:basic-cuiwei")
BANYUE_BASIC_FENSHEN_MOVE_ID = MoveId("move:banyue:basic-fenshen")
BANYUE_BASIC_QINGSHAN_MOVE_ID = MoveId("move:banyue:basic-qingshan")
BANYUE_BASIC_CUIYUE_MOVE_ID = MoveId("move:banyue:basic-cuiyue")
BANYUE_DASH_FEISHA_MOVE_ID = MoveId("move:banyue:dash-feisha")
BANYUE_DODGE_COUNTER_YANGLI_MOVE_ID = MoveId("move:banyue:dodge-counter-yangli")
BANYUE_EX_DIDONG_MOVE_ID = MoveId("move:banyue:ex-didong")
BANYUE_EX_SHANYAO_MOVE_ID = MoveId("move:banyue:ex-shanyao")
BANYUE_EX_LUNDAO_MOVE_ID = MoveId("move:banyue:ex-lundao")
BANYUE_EX_SHIZIHOU_MOVE_ID = MoveId("move:banyue:ex-shizihou")
BANYUE_EX_SHANYAO_RAGE_MOVE_ID = MoveId("move:banyue:ex-shanyao-rage")
BANYUE_EX_SHIZIHOU_RAGE_MOVE_ID = MoveId("move:banyue:ex-shizihou-rage")
BANYUE_CHAIN_NUYAN_MOVE_ID = MoveId("move:banyue:chain-nuyan")
BANYUE_ULTIMATE_HANTIANDONGDI_MOVE_ID = MoveId(
    "move:banyue:ultimate-hantiandongdi"
)
BANYUE_QUICK_ASSIST_PANYAN_MOVE_ID = MoveId("move:banyue:quick-assist-panyan")
BANYUE_ASSIST_ANGXIAO_MOVE_ID = MoveId("move:banyue:assist-angxiao")
BANYUE_ASSIST_CHONGXIAO_MOVE_ID = MoveId("move:banyue:assist-chongxiao")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_DODGE_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_EX = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    entry_key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage_index: int | None = None,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=entry_key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key="damage",
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=Element.FIRE,
        stage_index=stage_index,
    )


def _stages(
    *,
    key: str,
    move_id: MoveId,
    move_label: str,
    source_name: str,
    skill_id_base: int,
) -> tuple[NanokaMoveSpec, ...]:
    return tuple(
        _move(
            f"basic-{key}-stage-{stage}",
            move_id=move_id,
            label=f"普通攻击：{move_label}（{stage}段）",
            source_name=source_name,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name=f"{'一二三四'[stage - 1]}段伤害倍率",
            source_skill_id=str(skill_id_base + stage - 1),
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage_index=stage,
        )
        for stage in range(1, 5)
    )


BANYUE_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *_stages(
            key="zhengrong",
            move_id=BANYUE_BASIC_ZHENGRONG_MOVE_ID,
            move_label="峥嵘",
            source_name="普通攻击：峥嵘",
            skill_id_base=1471001,
        ),
        *_stages(
            key="cuiwei",
            move_id=BANYUE_BASIC_CUIWEI_MOVE_ID,
            move_label="崔巍",
            source_name="普通攻击：崔巍",
            skill_id_base=1471005,
        ),
        _move(
            "basic-fenshen",
            move_id=BANYUE_BASIC_FENSHEN_MOVE_ID,
            label="普通攻击：焚身",
            source_name="普通攻击：焚身",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            source_skill_id="1471027",
        ),
        _move(
            "basic-qingshan",
            move_id=BANYUE_BASIC_QINGSHAN_MOVE_ID,
            label="普通攻击：倾山",
            source_name="普通攻击：倾山",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            source_skill_id="1471009",
        ),
        _move(
            "basic-cuiyue",
            move_id=BANYUE_BASIC_CUIYUE_MOVE_ID,
            label="普通攻击：摧岳",
            source_name="普通攻击：摧岳",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            source_skill_id="1471010",
        ),
        _move(
            "dash-feisha",
            move_id=BANYUE_DASH_FEISHA_MOVE_ID,
            label="冲刺攻击：飞砂",
            source_name="冲刺攻击：飞砂",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1471018",
        ),
        _move(
            "dodge-counter-yangli",
            move_id=BANYUE_DODGE_COUNTER_YANGLI_MOVE_ID,
            label="闪避反击：扬砾",
            source_name="闪避反击：扬砾",
            group=SkillGroup.DODGE,
            tags=_DODGE_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1471019",
        ),
        _move(
            "ex-didong",
            move_id=BANYUE_EX_DIDONG_MOVE_ID,
            label="强化特殊技：地动",
            source_name="强化特殊技：地动",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter_name="伤害倍率",
            source_skill_id="1471013",
        ),
        _move(
            "ex-shanyao",
            move_id=BANYUE_EX_SHANYAO_MOVE_ID,
            label="强化特殊技：山摇",
            source_name="强化特殊技：山摇",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter_name="伤害倍率",
            source_skill_id="1471012",
        ),
        _move(
            "ex-lundao",
            move_id=BANYUE_EX_LUNDAO_MOVE_ID,
            label="强化特殊技：论道",
            source_name="强化特殊技：论道",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter_name="伤害倍率",
            source_skill_id="1471015",
        ),
        _move(
            "ex-shizihou",
            move_id=BANYUE_EX_SHIZIHOU_MOVE_ID,
            label="强化特殊技：狮子吼",
            source_name="强化特殊技：狮子吼",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter_name="伤害倍率",
            source_skill_id="1471014",
        ),
        _move(
            "ex-shanyao-rage",
            move_id=BANYUE_EX_SHANYAO_RAGE_MOVE_ID,
            label="强化特殊技：山摇·怒",
            source_name="强化特殊技：山摇·怒",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter_name="伤害倍率",
            source_skill_id="1471017",
        ),
        _move(
            "ex-shizihou-rage",
            move_id=BANYUE_EX_SHIZIHOU_RAGE_MOVE_ID,
            label="强化特殊技：狮子吼·怒",
            source_name="强化特殊技：狮子吼·怒",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
            parameter_name="伤害倍率",
            source_skill_id="1471016",
        ),
        _move(
            "chain-nuyan",
            move_id=BANYUE_CHAIN_NUYAN_MOVE_ID,
            label="连携技：怒焰",
            source_name="连携技：怒焰",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1471020",
        ),
        _move(
            "ultimate-hantiandongdi",
            move_id=BANYUE_ULTIMATE_HANTIANDONGDI_MOVE_ID,
            label="终结技：撼天动地",
            source_name="终结技：撼天动地",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1471021",
        ),
        _move(
            "quick-assist-panyan",
            move_id=BANYUE_QUICK_ASSIST_PANYAN_MOVE_ID,
            label="快速支援：磐岩",
            source_name="快速支援：磐岩",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1471022",
        ),
        _move(
            "assist-angxiao",
            move_id=BANYUE_ASSIST_ANGXIAO_MOVE_ID,
            label="支援突击：昂霄",
            source_name="支援突击：昂霄",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1471026",
        ),
        _move(
            "assist-chongxiao",
            move_id=BANYUE_ASSIST_CHONGXIAO_MOVE_ID,
            label="支援突击：冲霄",
            source_name="支援突击：冲霄",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1471029",
        ),
    )
)


__all__ = [
    "BANYUE_ASSIST_ANGXIAO_MOVE_ID",
    "BANYUE_ASSIST_CHONGXIAO_MOVE_ID",
    "BANYUE_BASIC_CUIWEI_MOVE_ID",
    "BANYUE_BASIC_CUIYUE_MOVE_ID",
    "BANYUE_BASIC_FENSHEN_MOVE_ID",
    "BANYUE_BASIC_QINGSHAN_MOVE_ID",
    "BANYUE_BASIC_ZHENGRONG_MOVE_ID",
    "BANYUE_CHAIN_NUYAN_MOVE_ID",
    "BANYUE_CORE_BUFF_ACTIVE",
    "BANYUE_DASH_FEISHA_MOVE_ID",
    "BANYUE_DODGE_COUNTER_YANGLI_MOVE_ID",
    "BANYUE_EX_DIDONG_MOVE_ID",
    "BANYUE_EX_LUNDAO_MOVE_ID",
    "BANYUE_EX_SHANYAO_MOVE_ID",
    "BANYUE_EX_SHANYAO_RAGE_MOVE_ID",
    "BANYUE_EX_SHIZIHOU_MOVE_ID",
    "BANYUE_EX_SHIZIHOU_RAGE_MOVE_ID",
    "BANYUE_QUICK_ASSIST_PANYAN_MOVE_ID",
    "BANYUE_REVIEWED_MAPPING",
    "BANYUE_ULTIMATE_HANTIANDONGDI_MOVE_ID",
    "BANYUE_TREMOR_ACTIVE",
]
