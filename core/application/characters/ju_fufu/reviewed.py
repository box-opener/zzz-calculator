"""Reviewed live Nanoka 3.2 move identities for Ju Fufu (character:1391)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping
from .config import JU_FUFU_ID


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_CHAIN_FOLLOW_UP = frozenset({DamageTag.CHAIN_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


JU_FUFU_BASIC_MOVE_ID = MoveId("move:ju-fufu:basic-seven-forms")
JU_FUFU_TIGER_MIGHT_MOVE_ID = MoveId("move:ju-fufu:basic-tiger-might")
JU_FUFU_DASH_MOVE_ID = MoveId("move:ju-fufu:dash-seven-forms")
JU_FUFU_SPIN_MOVE_ID = MoveId("move:ju-fufu:dash-tiger-cauldron")
JU_FUFU_COUNTER_MOVE_ID = MoveId("move:ju-fufu:dodge-counter-fire-return")
JU_FUFU_SPECIAL_MOVE_ID = MoveId("move:ju-fufu:special-descending-tiger")
JU_FUFU_EX_MOVE_ID = MoveId("move:ju-fufu:ex-descending-tiger")
JU_FUFU_CHAIN_MOVE_ID = MoveId("move:ju-fufu:chain-tiger-cauldron-collapse")
JU_FUFU_FOLLOW_UP_CHAIN_MOVE_ID = MoveId("move:ju-fufu:chain-tiger-cauldron-shake")
JU_FUFU_ULTIMATE_MOVE_ID = MoveId("move:ju-fufu:ultimate-tiger-bloom")
JU_FUFU_QUICK_ASSIST_MOVE_ID = MoveId("move:ju-fufu:quick-assist-tiger-paw")
JU_FUFU_ASSIST_STRIKE_MOVE_ID = MoveId("move:ju-fufu:assist-strike-flame-jaw")


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    source_skill_id: str,
    element: Element,
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
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
    )


_BASIC_SOURCE = "普通攻击：恶虎七式·燎身爪"
_TIGER_MIGHT_SOURCE = "普通攻击：「虎威」"
_SPIN_SOURCE = "冲刺攻击：恶虎七式·山君鼎戏"


JU_FUFU_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=JU_FUFU_BASIC_MOVE_ID,
                label=f"普通攻击：恶虎七式·燎身爪（{('一', '二', '三')[stage - 1]}段）",
                source_name=_BASIC_SOURCE,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=f"139100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            "basic-stage-4",
            move_id=JU_FUFU_BASIC_MOVE_ID,
            label="普通攻击：恶虎七式·燎身爪（第四段）",
            source_name=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="四段伤害倍率",
            source_skill_id="1391004",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=4,
        ),
        _move(
            "basic-tiger-might",
            move_id=JU_FUFU_TIGER_MIGHT_MOVE_ID,
            label="普通攻击：「虎威」",
            source_name=_TIGER_MIGHT_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="伤害倍率",
            source_skill_id="1391005",
            element=Element.FIRE,
        ),
        _move(
            "dash-tiger-sprint",
            move_id=JU_FUFU_DASH_MOVE_ID,
            label="冲刺攻击：恶虎七式·虎奔",
            source_name="冲刺攻击：恶虎七式·虎奔",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1391008",
            element=Element.PHYSICAL,
        ),
        _move(
            "dash-tiger-cauldron-physical",
            move_id=JU_FUFU_SPIN_MOVE_ID,
            label="冲刺攻击：恶虎七式·山君鼎戏（物理）",
            source_name=_SPIN_SOURCE,
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1391009",
            element=Element.PHYSICAL,
        ),
        _move(
            "dash-tiger-cauldron-fire",
            move_id=JU_FUFU_SPIN_MOVE_ID,
            label="冲刺攻击：恶虎七式·山君鼎戏（威势）",
            source_name="冲刺攻击：恶虎七式·山君鼎戏·威势",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1391010",
            element=Element.FIRE,
        ),
        _move(
            "dash-tiger-cauldron-tiger-might",
            move_id=JU_FUFU_SPIN_MOVE_ID,
            label="冲刺攻击：恶虎七式·山君鼎戏（「虎威」）",
            source_name="冲刺攻击：恶虎七式·山君鼎戏·「虎威」",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1391022",
            element=Element.FIRE,
        ),
        _move(
            "dodge-counter-fire-return",
            move_id=JU_FUFU_COUNTER_MOVE_ID,
            label="闪避反击：恶虎七式·离火回峰",
            source_name="闪避反击：恶虎七式·离火回峰",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            source_skill_id="1391011",
            element=Element.FIRE,
        ),
        _move(
            "special-descending-tiger",
            move_id=JU_FUFU_SPECIAL_MOVE_ID,
            label="特殊技：恶虎七式·下山虎",
            source_name="特殊技：恶虎七式·下山虎",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1391006",
            element=Element.FIRE,
        ),
        _move(
            "ex-descending-tiger",
            move_id=JU_FUFU_EX_MOVE_ID,
            label="强化特殊技：恶虎七式改·下山猛虎",
            source_name="强化特殊技：恶虎七式改·下山猛虎",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1391007",
            element=Element.FIRE,
        ),
        _move(
            "chain-tiger-cauldron-collapse",
            move_id=JU_FUFU_CHAIN_MOVE_ID,
            label="连携技：虎釜崩",
            source_name="连携技：虎釜崩",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            source_skill_id="1391012",
            element=Element.FIRE,
        ),
        _move(
            "chain-tiger-cauldron-shake",
            move_id=JU_FUFU_FOLLOW_UP_CHAIN_MOVE_ID,
            label="连携技：虎釜震煞",
            source_name="连携技：虎釜震煞",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN_FOLLOW_UP,
            parameter="伤害倍率",
            source_skill_id="1391013",
            element=Element.FIRE,
        ),
        _move(
            "ultimate-tiger-bloom",
            move_id=JU_FUFU_ULTIMATE_MOVE_ID,
            label="终结技：恶虎七式·猛虎炸开花",
            source_name="终结技：恶虎七式·猛虎炸开花",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            source_skill_id="1391014",
            element=Element.FIRE,
        ),
        _move(
            "quick-assist-tiger-paw",
            move_id=JU_FUFU_QUICK_ASSIST_MOVE_ID,
            label="快速支援：怒决蹯",
            source_name="快速支援：怒决蹯",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1391015",
            element=Element.FIRE,
        ),
        _move(
            "assist-strike-flame-jaw",
            move_id=JU_FUFU_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：彪形焰颌",
            source_name="支援突击：彪形焰颌",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1391019",
            element=Element.FIRE,
        ),
    )
)


__all__ = [
    "JU_FUFU_REVIEWED_MAPPING",
    "JU_FUFU_ID",
    "JU_FUFU_BASIC_MOVE_ID",
    "JU_FUFU_TIGER_MIGHT_MOVE_ID",
    "JU_FUFU_DASH_MOVE_ID",
    "JU_FUFU_SPIN_MOVE_ID",
    "JU_FUFU_COUNTER_MOVE_ID",
    "JU_FUFU_SPECIAL_MOVE_ID",
    "JU_FUFU_EX_MOVE_ID",
    "JU_FUFU_CHAIN_MOVE_ID",
    "JU_FUFU_FOLLOW_UP_CHAIN_MOVE_ID",
    "JU_FUFU_ULTIMATE_MOVE_ID",
    "JU_FUFU_QUICK_ASSIST_MOVE_ID",
    "JU_FUFU_ASSIST_STRIKE_MOVE_ID",
]
