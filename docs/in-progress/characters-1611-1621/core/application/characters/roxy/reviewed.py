"""Reviewed move identities and Nanoka live 3.2 curves for Roxy."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import ROXY_ID


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


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
        element=Element.WIND,
        stage_index=stage,
    )


_BASIC_SOURCE = "普通攻击：烦请留步"
_BASIC_STAGE_NAMES = ("一段", "二段", "三段", "四段")

ROXY_BASIC_MOVE_ID = MoveId("move:roxy:basic-please-stop")
ROXY_DASH_MOVE_ID = MoveId("move:roxy:dash-excuse-me")
ROXY_COUNTER_MOVE_ID = MoveId("move:roxy:counter-courtesy")
ROXY_SPECIAL_MOVE_ID = MoveId("move:roxy:special-after-you")
ROXY_HAMMER_MOVE_ID = MoveId("move:roxy:special-no-further")
ROXY_EX_SPIN_MOVE_ID = MoveId("move:roxy:ex-mind-the-cold")
ROXY_EX_CANNON_MOVE_ID = MoveId("move:roxy:ex-rest-in-peace")
ROXY_CHAIN_MOVE_ID = MoveId("move:roxy:chain-wind-hammer")
ROXY_ULTIMATE_MOVE_ID = MoveId("move:roxy:ultimate-night-dirge")
ROXY_BASIC_ASSIST_MOVE_ID = MoveId("move:roxy:assist-stay-late")
ROXY_QUICK_ASSIST_MOVE_ID = MoveId("move:roxy:quick-assist-at-your-service")
ROXY_ASSIST_STRIKE_MOVE_ID = MoveId("move:roxy:assist-strike-midnight-protocol")

ROXY_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-please-stop-stage-{stage}",
                move_id=ROXY_BASIC_MOVE_ID,
                label=f"普通攻击：烦请留步（{_BASIC_STAGE_NAMES[stage - 1]}）",
                source_name=_BASIC_SOURCE,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{_BASIC_STAGE_NAMES[stage - 1]}伤害倍率",
                source_skill_id=f"162100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "dash-excuse-me",
            move_id=ROXY_DASH_MOVE_ID,
            label="冲刺攻击：失礼",
            source_name="冲刺攻击：失礼",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1621009",
        ),
        _move(
            "counter-courtesy",
            move_id=ROXY_COUNTER_MOVE_ID,
            label="闪避反击：礼尚往来",
            source_name="闪避反击：礼尚往来",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1621010",
        ),
        _move(
            "special-after-you",
            move_id=ROXY_SPECIAL_MOVE_ID,
            label="特殊技：劳驾",
            source_name="特殊技：劳驾",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1621006",
        ),
        _move(
            "special-no-further",
            move_id=ROXY_HAMMER_MOVE_ID,
            label="特殊技：恕不远送",
            source_name="特殊技：恕不远送",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1621005",
        ),
        _move(
            "ex-mind-the-cold",
            move_id=ROXY_EX_SPIN_MOVE_ID,
            label="强化特殊技：小心风寒",
            source_name="强化特殊技：小心风寒",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1621007",
        ),
        _move(
            "ex-rest-in-peace",
            move_id=ROXY_EX_CANNON_MOVE_ID,
            label="强化特殊技：敬请安息",
            source_name="强化特殊技：敬请安息",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1621023",
        ),
        _move(
            "chain-wind-hammer",
            move_id=ROXY_CHAIN_MOVE_ID,
            label="连携技：葬风巨锤",
            source_name="连携技：葬风巨锤",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1621011",
        ),
        _move(
            "ultimate-night-dirge",
            move_id=ROXY_ULTIMATE_MOVE_ID,
            label="终结技：葬夜安魂曲",
            source_name="终结技：葬夜安魂曲",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1621012",
        ),
        _move(
            "assist-stay-late",
            move_id=ROXY_BASIC_ASSIST_MOVE_ID,
            label="支援技：还要加班？",
            source_name="支援技：还要加班？",
            group=SkillGroup.ASSIST,
            tags=frozenset({DamageTag.ASSIST, DamageTag.BASIC_ATTACK}),
            parameter_name="伤害倍率",
            source_skill_id="1621018",
        ),
        _move(
            "quick-assist-at-your-service",
            move_id=ROXY_QUICK_ASSIST_MOVE_ID,
            label="快速支援：听凭差遣",
            source_name="快速支援：听凭差遣",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1621013",
        ),
        _move(
            "assist-strike-midnight-protocol",
            move_id=ROXY_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：午夜守则",
            source_name="支援突击：午夜守则",
            group=SkillGroup.ASSIST,
            tags=frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK}),
            parameter_name="伤害倍率",
            source_skill_id="1621017",
        ),
    ),
    data_quality_notes=(
        "The source has four authored Basic Attack damage stages, Direct curves for the named combat moves, and three Parry Assist Daze curves. The Daze curves are not emitted as damage events.",
        "The source explicitly says 支援技：还要加班？ is treated as 普通攻击, so its event retains both Assist and Basic Attack tags.",
        "Wind Eyes, spin-per-second, and energy-consumption child damage are separately described source events; they are not folded into a named move's multiplier. Their current static selection/count support is handled separately from this ordinary-move mapping.",
        "No self Wind Anomaly or Disorder result is added to this non-Anomaly Stun definition.",
    ),
)


__all__ = [
    "ROXY_REVIEWED_MAPPING",
    "ROXY_BASIC_MOVE_ID",
    "ROXY_DASH_MOVE_ID",
    "ROXY_COUNTER_MOVE_ID",
    "ROXY_SPECIAL_MOVE_ID",
    "ROXY_HAMMER_MOVE_ID",
    "ROXY_EX_SPIN_MOVE_ID",
    "ROXY_EX_CANNON_MOVE_ID",
    "ROXY_CHAIN_MOVE_ID",
    "ROXY_ULTIMATE_MOVE_ID",
    "ROXY_BASIC_ASSIST_MOVE_ID",
    "ROXY_QUICK_ASSIST_MOVE_ID",
    "ROXY_ASSIST_STRIKE_MOVE_ID",
]
