"""Reviewed Nanoka 3.2 move identities for Seth (character:1271)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


SETH_ID = CharacterId("character:1271")
SETH_BASIC_MOVE_ID = MoveId("move:seth:basic-thunder-strike")
SETH_BASIC_SHOCK_MOVE_ID = MoveId("move:seth:basic-thunder-strike-shock")
SETH_BASIC_SHOCK_FULL_MOVE_ID = MoveId("move:seth:basic-thunder-strike-shock-full")
SETH_DASH_MOVE_ID = MoveId("move:seth:dash-electric-assault")
SETH_COUNTER_MOVE_ID = MoveId("move:seth:dodge-counter-retreat-into-advance")
SETH_SPECIAL_MOVE_ID = MoveId("move:seth:special-electric-shield-charge")
SETH_EX_MOVE_ID = MoveId("move:seth:ex-electric-shield-charge")
SETH_CHAIN_MOVE_ID = MoveId("move:seth:chain-final-judgment")
SETH_ULTIMATE_MOVE_ID = MoveId("move:seth:ultimate-justice-wins")
SETH_QUICK_ASSIST_MOVE_ID = MoveId("move:seth:quick-assist-force-support")
SETH_ASSIST_STRIKE_MOVE_ID = MoveId("move:seth:assist-strike-public-security-verdict")

SETH_ELECTRIC_ANOMALY_RECORD_ID = "anomaly:character:1271:electric-shock"
SETH_ELECTRIC_ANOMALY_MOVE_ID = MoveId("move:seth:electric-shock")
SETH_ELECTRIC_DISORDER_MOVE_ID = MoveId("move:seth:electric-disorder")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
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


SETH_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            "basic-shock-continuous",
            move_id=SETH_BASIC_SHOCK_MOVE_ID,
            label="普通攻击：雷霆击-感电（持续攻击）",
            source_name="普通攻击：雷霆击-感电",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="连续攻击伤害倍率",
            curve="1271005",
            element=Element.ELECTRIC,
        ),
        _move(
            "basic-shock-finisher",
            move_id=SETH_BASIC_SHOCK_MOVE_ID,
            label="普通攻击：雷霆击-感电（终结一击）",
            source_name="普通攻击：雷霆击-感电",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="终结一击伤害倍率",
            curve="1271006",
            element=Element.ELECTRIC,
        ),
        _move(
            "dash-attack",
            move_id=SETH_DASH_MOVE_ID,
            label="冲刺攻击：电光突袭",
            source_name="冲刺攻击：电光突袭",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1271011",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter",
            move_id=SETH_COUNTER_MOVE_ID,
            label="闪避反击：以退为进",
            source_name="闪避反击：以退为进",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            curve="1271012",
            element=Element.ELECTRIC,
        ),
        _move(
            "special-electric-shield-charge",
            move_id=SETH_SPECIAL_MOVE_ID,
            label="特殊技：电光盾冲",
            source_name="特殊技：电光盾冲",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            curve="1271007",
            element=Element.ELECTRIC,
        ),
        _move(
            "ex-electric-shield-charge",
            move_id=SETH_EX_MOVE_ID,
            label="强化特殊技：电光盾冲-高伏特（未蓄力）",
            source_name="强化特殊技：电光盾冲-高伏特",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            curve="1271008",
            element=Element.ELECTRIC,
        ),
        _move(
            "ex-electric-shield-charge-charged",
            move_id=SETH_EX_MOVE_ID,
            label="强化特殊技：电光盾冲-高伏特（蓄力完成）",
            source_name="强化特殊技：电光盾冲-高伏特",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率（蓄力）",
            curve="1271009",
            element=Element.ELECTRIC,
        ),
        _move(
            "chain-final-judgment",
            move_id=SETH_CHAIN_MOVE_ID,
            label="连携技：最终制裁",
            source_name="连携技：最终制裁",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            curve="1271013",
            element=Element.ELECTRIC,
        ),
        _move(
            "ultimate-justice-wins",
            move_id=SETH_ULTIMATE_MOVE_ID,
            label="终结技：正义必胜",
            source_name="终结技：正义必胜",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            curve="1271014",
            element=Element.ELECTRIC,
        ),
        _move(
            "quick-assist-force-support",
            move_id=SETH_QUICK_ASSIST_MOVE_ID,
            label="快速支援：武力支援",
            source_name="快速支援：武力支援",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1271015",
            element=Element.ELECTRIC,
        ),
        _move(
            "assist-strike-public-security-verdict",
            move_id=SETH_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：治安裁决",
            source_name="支援突击：治安裁决",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1271019",
            element=Element.ELECTRIC,
        ),
    ),
    data_quality_notes=(
        "普通攻击：雷霆击的四段说明合述物理与电属性伤害，段与元素的对应关系尚未确认。",
    ),
)


__all__ = [
    "SETH_ASSIST_STRIKE_MOVE_ID",
    "SETH_BASIC_MOVE_ID",
    "SETH_BASIC_SHOCK_MOVE_ID",
    "SETH_BASIC_SHOCK_FULL_MOVE_ID",
    "SETH_CHAIN_MOVE_ID",
    "SETH_COUNTER_MOVE_ID",
    "SETH_DASH_MOVE_ID",
    "SETH_ELECTRIC_ANOMALY_MOVE_ID",
    "SETH_ELECTRIC_ANOMALY_RECORD_ID",
    "SETH_ELECTRIC_DISORDER_MOVE_ID",
    "SETH_EX_MOVE_ID",
    "SETH_ID",
    "SETH_QUICK_ASSIST_MOVE_ID",
    "SETH_REVIEWED_MAPPING",
    "SETH_SPECIAL_MOVE_ID",
    "SETH_ULTIMATE_MOVE_ID",
]
