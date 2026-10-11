"""Reviewed Nanoka 3.2 move identities for Yinhu (character:1421)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping
from .config import YINHU_ID


YINHU_QI_JUE_ACTIVE = ScenarioConditionId("condition:yinhu:enemy-qi-jue-active")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})

YINHU_BASIC_MOVE_ID = MoveId("move:yinhu:basic-extreme-strikes")
YINHU_DASH_MOVE_ID = MoveId("move:yinhu:dash-hot-oil-prosperity")
YINHU_COUNTER_MOVE_ID = MoveId("move:yinhu:dodge-counter-shifting-peaks")
YINHU_SPECIAL_MOVE_ID = MoveId("move:yinhu:special-explosive-acupoint-finger")
YINHU_BROKEN_MERIDIANS_MOVE_ID = MoveId("move:yinhu:special-broken-meridians")
YINHU_EX_MOVE_ID = MoveId("move:yinhu:ex-special-mountain-shaking-palm")
YINHU_CHAIN_MOVE_ID = MoveId("move:yinhu:chain-wok-qi-overhead")
YINHU_ULTIMATE_MOVE_ID = MoveId("move:yinhu:ultimate-grand-banquet")
YINHU_QUICK_ASSIST_MOVE_ID = MoveId("move:yinhu:quick-assist-good-fortune")
YINHU_ASSIST_FOLLOW_UP_MOVE_ID = MoveId("move:yinhu:assist-follow-up-turning-force")


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    curve: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=parameter,
                source_skill_id=curve,
            ),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


YINHU_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=YINHU_BASIC_MOVE_ID,
                label=f"普通攻击：极意连打（{('一', '二', '三', '四')[stage - 1]}段）",
                source_name="普通攻击：极意连打",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一段', '二段', '三段', '四段')[stage - 1]}伤害倍率",
                curve=f"142100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "dash-attack",
            move_id=YINHU_DASH_MOVE_ID,
            label="冲刺攻击：热油鼎盛",
            source_name="冲刺攻击：热油鼎盛",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1421010",
        ),
        _move(
            "dodge-counter",
            move_id=YINHU_COUNTER_MOVE_ID,
            label="闪避反击：移峰倒海",
            source_name="闪避反击：移峰倒海",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            curve="1421011",
        ),
        _move(
            "special-explosive-acupoint-finger",
            move_id=YINHU_SPECIAL_MOVE_ID,
            label="特殊技：爆音点穴指",
            source_name="特殊技：爆音点穴指",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            curve="1421005",
        ),
        *tuple(
            _move(
                f"special-broken-meridians-stage-{stage}",
                move_id=YINHU_BROKEN_MERIDIANS_MOVE_ID,
                label=f"特殊技：断脉破穴手（{('一', '二', '三')[stage - 1]}段）",
                source_name="特殊技：断脉破穴手",
                group=SkillGroup.SPECIAL_ATTACK,
                tags=_SPECIAL,
                parameter=f"{('一段', '二段', '三段')[stage - 1]}伤害倍率",
                curve=f"142100{stage + 6}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            "ex-special-mountain-shaking-palm",
            move_id=YINHU_EX_MOVE_ID,
            label="强化特殊技：贴山震脉靠",
            source_name="强化特殊技：贴山震脉靠",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            curve="1421006",
        ),
        _move(
            "chain-wok-qi-overhead",
            move_id=YINHU_CHAIN_MOVE_ID,
            label="连携技：锅气灌顶",
            source_name="连携技：锅气灌顶",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            curve="1421012",
        ),
        _move(
            "ultimate-grand-banquet",
            move_id=YINHU_ULTIMATE_MOVE_ID,
            label="终结技：满汉全席！",
            source_name="终结技：满汉全席！",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            curve="1421013",
        ),
        _move(
            "quick-assist-good-fortune",
            move_id=YINHU_QUICK_ASSIST_MOVE_ID,
            label="快速支援：抬头见喜",
            source_name="快速支援：抬头见喜",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1421014",
        ),
        _move(
            "assist-follow-up-turning-force",
            move_id=YINHU_ASSIST_FOLLOW_UP_MOVE_ID,
            label="支援突击：借势打势",
            source_name="支援突击：借势打势",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1421018",
        ),
    ),
    data_quality_notes=(
        "Defensive Assist lists Daze values but no damage multiplier; it is not assigned a synthetic damage event.",
        "The EX-triggered Quick Assist belongs to the previous teammate. The static single-character move model does not simulate that teammate's event or the switch timeline.",
    ),
)


def penetration_recipient_condition_id_for(character_id: CharacterId) -> ScenarioConditionId:
    token = str(character_id).replace(":", "-")
    return ScenarioConditionId(f"condition:yinhu:core:tongqiao-active:{token}")


__all__ = [
    "YINHU_ID",
    "YINHU_QI_JUE_ACTIVE",
    "YINHU_REVIEWED_MAPPING",
    "YINHU_BASIC_MOVE_ID",
    "YINHU_DASH_MOVE_ID",
    "YINHU_COUNTER_MOVE_ID",
    "YINHU_SPECIAL_MOVE_ID",
    "YINHU_BROKEN_MERIDIANS_MOVE_ID",
    "YINHU_EX_MOVE_ID",
    "YINHU_CHAIN_MOVE_ID",
    "YINHU_ULTIMATE_MOVE_ID",
    "YINHU_QUICK_ASSIST_MOVE_ID",
    "YINHU_ASSIST_FOLLOW_UP_MOVE_ID",
    "penetration_recipient_condition_id_for",
]
