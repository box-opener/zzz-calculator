"""Reviewed Nanoka 3.2 move identities for Evelyn (character:1321)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping
from .config import EVELYN_ID

EVELYN_BASIC_MOVE_ID = MoveId("move:evelyn:basic-string-cut")
EVELYN_STRANGLE_I_MOVE_ID = MoveId("move:evelyn:basic-strangle-i")
EVELYN_STRANGLE_II_MOVE_ID = MoveId("move:evelyn:basic-strangle-ii")
EVELYN_DASH_MOVE_ID = MoveId("move:evelyn:dash-shuttle-ambush")
EVELYN_COUNTER_MOVE_ID = MoveId("move:evelyn:dodge-counter-strangling-counter")
EVELYN_SPECIAL_LOCK_MOVE_ID = MoveId("move:evelyn:special-silk-control")
EVELYN_SPECIAL_BIND_MOVE_ID = MoveId("move:evelyn:special-rupture-i")
EVELYN_EX_SPECIAL_MOVE_ID = MoveId("move:evelyn:ex-special-rupture-final")
EVELYN_CHAIN_MOVE_ID = MoveId("move:evelyn:chain-moonlight-silk-bond")
EVELYN_ULTIMATE_SOUND_MOVE_ID = MoveId("move:evelyn:ultimate-moonlight-silk-sound")
EVELYN_ULTIMATE_SHADOW_MOVE_ID = MoveId("move:evelyn:ultimate-moonlight-silk-shadow")
EVELYN_QUICK_ASSIST_MOVE_ID = MoveId("move:evelyn:quick-assist-blade-edge")
EVELYN_ASSIST_STRIKE_MOVE_ID = MoveId("move:evelyn:assist-strike-trajectory-interference")

EVELYN_CONSTRAINT_CR_ACTIVE = "condition:evelyn:constraint-crit-active"
EVELYN_TARGET_IMPRISONED = "condition:evelyn:target-imprisoned"
EVELYN_C4_SHIELD_ACTIVE = "condition:evelyn:cinema4-shield-active"
EVELYN_C6_SHADOW_EDGE_ACTIVE = "condition:evelyn:cinema6-shadow-edge-active"

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
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
    parameter: str,
    curve: str,
    element: Element,
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
        multiplier_relation=MultiplierRelation.COMPLETE,
        element=element,
    )


EVELYN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=EVELYN_BASIC_MOVE_ID,
                label=f"普通攻击：割弦（第{stage}段）",
                source_name="普通攻击：割弦",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
                curve=f"132100{stage}",
                element=Element.PHYSICAL if stage <= 3 else Element.FIRE,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-stage-3-after-cancel",
            move_id=EVELYN_BASIC_MOVE_ID,
            label="普通攻击：割弦（束裂式取消引爆后的第三段单独查询）",
            source_name="普通攻击：割弦",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="三段伤害倍率",
            curve="1321003",
            element=Element.FIRE,
        ),
        _move(
            "strangle-i",
            move_id=EVELYN_STRANGLE_I_MOVE_ID,
            label="普通攻击：绞勒式·I型",
            source_name="普通攻击：绞勒式·I型",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="伤害倍率",
            curve="1321006",
            element=Element.FIRE,
        ),
        _move(
            "strangle-ii",
            move_id=EVELYN_STRANGLE_II_MOVE_ID,
            label="普通攻击：绞勒式·II型",
            source_name="普通攻击：绞勒式·II型",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="伤害倍率",
            curve="1321007",
            element=Element.FIRE,
        ),
        _move(
            "dash-attack",
            move_id=EVELYN_DASH_MOVE_ID,
            label="冲刺攻击：穿梭潜袭",
            source_name="冲刺攻击：穿梭潜袭",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1321013",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter",
            move_id=EVELYN_COUNTER_MOVE_ID,
            label="闪避反击：绞缢反制",
            source_name="闪避反击：绞缢反制",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            curve="1321014",
            element=Element.FIRE,
        ),
        _move(
            "special-lock",
            move_id=EVELYN_SPECIAL_LOCK_MOVE_ID,
            label="特殊技：锁系控位",
            source_name="特殊技：锁系控位",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="一段伤害倍率",
            curve="1321008",
            element=Element.FIRE,
        ),
        _move(
            "chain-attack",
            move_id=EVELYN_CHAIN_MOVE_ID,
            label="连携技：月辉丝·绊",
            source_name="连携技：月辉丝·绊",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            curve="1321015",
            element=Element.FIRE,
        ),
        _move(
            "ultimate-sound",
            move_id=EVELYN_ULTIMATE_SOUND_MOVE_ID,
            label="终结技：月辉丝·弦音",
            source_name="终结技：月辉丝·弦音",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            curve="1321016",
            element=Element.FIRE,
        ),
        _move(
            "ultimate-shadow",
            move_id=EVELYN_ULTIMATE_SHADOW_MOVE_ID,
            label="终结技：月辉丝·弦影",
            source_name="终结技：月辉丝·弦影",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            curve="1321016",
            element=Element.FIRE,
        ),
        _move(
            "quick-assist",
            move_id=EVELYN_QUICK_ASSIST_MOVE_ID,
            label="快速支援：烈锋",
            source_name="快速支援：烈锋",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1321017",
            element=Element.FIRE,
        ),
        _move(
            "assist-strike",
            move_id=EVELYN_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：轨迹干涉",
            source_name="支援突击：轨迹干涉",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1321021",
            element=Element.FIRE,
        ),
    )
)


__all__ = [
    "EVELYN_ID",
    "EVELYN_BASIC_MOVE_ID",
    "EVELYN_STRANGLE_I_MOVE_ID",
    "EVELYN_STRANGLE_II_MOVE_ID",
    "EVELYN_DASH_MOVE_ID",
    "EVELYN_COUNTER_MOVE_ID",
    "EVELYN_SPECIAL_LOCK_MOVE_ID",
    "EVELYN_SPECIAL_BIND_MOVE_ID",
    "EVELYN_EX_SPECIAL_MOVE_ID",
    "EVELYN_CHAIN_MOVE_ID",
    "EVELYN_ULTIMATE_SOUND_MOVE_ID",
    "EVELYN_ULTIMATE_SHADOW_MOVE_ID",
    "EVELYN_QUICK_ASSIST_MOVE_ID",
    "EVELYN_ASSIST_STRIKE_MOVE_ID",
    "EVELYN_CONSTRAINT_CR_ACTIVE",
    "EVELYN_TARGET_IMPRISONED",
    "EVELYN_C4_SHIELD_ACTIVE",
    "EVELYN_C6_SHADOW_EDGE_ACTIVE",
    "EVELYN_REVIEWED_MAPPING",
]
