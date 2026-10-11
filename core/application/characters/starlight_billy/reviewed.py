"""Reviewed move identities for Starlight - Billy's Nanoka live 3.2 source."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import STARLIGHT_BILLY_ID


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

_BASIC_MOVE = MoveId("move:starlight-billy:basic-knights-duel")
_HIGH_MILEAGE_MOVE = MoveId("move:starlight-billy:basic-high-mileage-starlight")
_DASH_MOVE = MoveId("move:starlight-billy:dash-star-emblem-punishment")
_COUNTER_MOVE = MoveId("move:starlight-billy:dodge-counter-king-of-duel")
_TAILSPIN_MOVE = MoveId("move:starlight-billy:dodge-counter-tail-flame-spin")
_MOTOR_SUPPRESSION_MOVE = MoveId("move:starlight-billy:special-motor-suppression")
_DISENGAGE_MOVE = MoveId("move:starlight-billy:special-disengage")
_LONE_WHEEL_MOVE = MoveId("move:starlight-billy:ex-lone-wheel-stunt")
_GRIP_HUB_MOVE = MoveId("move:starlight-billy:ex-grip-hub")
_SWAYING_STEP_MOVE = MoveId("move:starlight-billy:ex-swaying-step")
_CHAIN_MOVE = MoveId("move:starlight-billy:chain-knight-walk")
_ULTIMATE_MOVE = MoveId("move:starlight-billy:ultimate-knight-flying-kick")
_QUICK_ASSIST_MOVE = MoveId("move:starlight-billy:quick-assist-star-emblem-bond")
_SUPPORT_STRIKE_MOVE = MoveId("move:starlight-billy:assist-villain-exit")


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
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
                variant_key="damage",
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


_BASIC_SOURCE = "普通攻击：骑士斗技"
_BASIC_STAGES = tuple(
    _move(
        f"basic-knights-duel-stage-{stage}",
        move_id=_BASIC_MOVE,
        label=f"普通攻击：骑士斗技（{'一二三四'[stage - 1]}段）",
        source_name=_BASIC_SOURCE,
        group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        parameter_name=f"{'一二三四'[stage - 1]}段伤害倍率",
        source_skill_id=f"153100{stage}",
        relation=MultiplierRelation.SEQUENTIAL_STAGE,
        stage=stage,
    )
    for stage in range(1, 5)
)


STARLIGHT_BILLY_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *_BASIC_STAGES,
        _move(
            "basic-high-mileage-starlight",
            move_id=_HIGH_MILEAGE_MOVE,
            label="普通攻击：最高马力星光",
            source_name="普通攻击：最高马力星光",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="伤害倍率",
            source_skill_id="1531010",
        ),
        _move(
            "dash-star-emblem-punishment",
            move_id=_DASH_MOVE,
            label="冲刺攻击：星-徽-惩-戒",
            source_name="冲刺攻击：星-徽-惩-戒",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1531012",
        ),
        _move(
            "dodge-counter-king-of-duel",
            move_id=_COUNTER_MOVE,
            label="闪避反击：决斗之王",
            source_name="闪避反击：决斗之王",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1531013",
        ),
        _move(
            "dodge-counter-tail-flame-spin",
            move_id=_TAILSPIN_MOVE,
            label="闪避反击：尾焰全旋",
            source_name="闪避反击：尾焰全旋",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1531014",
        ),
        _move(
            "special-motor-suppression",
            move_id=_MOTOR_SUPPRESSION_MOVE,
            label="特殊技：动力压制",
            source_name="特殊技：动力压制",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1531006",
        ),
        _move(
            "special-disengage",
            move_id=_DISENGAGE_MOVE,
            label="特殊技：脱缰",
            source_name="特殊技：脱缰",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1531007",
        ),
        _move(
            "ex-lone-wheel-stunt",
            move_id=_LONE_WHEEL_MOVE,
            label="强化特殊技：孤轮特技",
            source_name="强化特殊技：孤轮特技",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1531008",
        ),
        _move(
            "ex-grip-hub",
            move_id=_GRIP_HUB_MOVE,
            label="强化特殊技：抓地轮毂",
            source_name="强化特殊技：抓地轮毂",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1531009",
        ),
        _move(
            "ex-swaying-step",
            move_id=_SWAYING_STEP_MOVE,
            label="强化特殊技：摇曳步伐",
            source_name="强化特殊技：摇曳步伐",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1531011",
        ),
        _move(
            "chain-knight-walk",
            move_id=_CHAIN_MOVE,
            label="连携技：骑士漫步",
            source_name="连携技：骑士漫步",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1531015",
        ),
        _move(
            "ultimate-knight-flying-kick",
            move_id=_ULTIMATE_MOVE,
            label="终结技：骑士飞踢",
            source_name="终结技：骑士飞踢",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1531016",
        ),
        _move(
            "quick-assist-star-emblem-bond",
            move_id=_QUICK_ASSIST_MOVE,
            label="快速支援：星徽-羁绊之力",
            source_name="快速支援：星徽-羁绊之力",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1531017",
        ),
        _move(
            "assist-villain-exit",
            move_id=_SUPPORT_STRIKE_MOVE,
            label="支援突击：反派退场",
            source_name="支援突击：反派退场",
            group=SkillGroup.ASSIST,
            tags=_FOLLOW_UP,
            parameter_name="伤害倍率",
            source_skill_id="1531021",
        ),
    ),
    data_quality_notes=(
        "All 17 reviewed damage entries map to source Physical curves. The source's three parry-assist curves are Daze-only and are intentionally not damage entries.",
        "The four Basic stages are separate sequential entries; High Mileage is a separately named Basic entry.",
    ),
)


__all__ = ["STARLIGHT_BILLY_REVIEWED_MAPPING"]
