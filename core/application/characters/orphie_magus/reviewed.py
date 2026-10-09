"""Reviewed Nanoka 3.2 move identities for Orphie & Magus (1301)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping

ORPHIE_MAGUS_ID = CharacterId("character:1301")
ORPHIE_ID = ORPHIE_MAGUS_ID

ORPHIE_BASIC_MOVE_ID = MoveId("move:orphie-magus:basic-high-pressure-gun")
ORPHIE_DASH_MOVE_ID = MoveId("move:orphie-magus:dash-assault-command")
ORPHIE_COUNTER_MOVE_ID = MoveId("move:orphie-magus:dodge-counter-counterattack")
ORPHIE_SPECIAL_MOVE_ID = MoveId("move:orphie-magus:special-hot-loaded")
ORPHIE_SPECIAL_AUTOFIRE_MOVE_ID = MoveId("move:orphie-magus:special-light-eater")
ORPHIE_EX_SPECIAL_MOVE_ID = MoveId("move:orphie-magus:ex-careful")
ORPHIE_EX_WHIRLWIND_MOVE_ID = MoveId("move:orphie-magus:ex-red-whirlpool")
ORPHIE_EX_CHARGE_MOVE_ID = MoveId("move:orphie-magus:ex-heat-charge")
ORPHIE_EX_FINISHER_MOVE_ID = MoveId("move:orphie-magus:ex-blaze-burst")
ORPHIE_CHAIN_MOVE_ID = MoveId("move:orphie-magus:chain-overheated-barrel")
ORPHIE_ULTIMATE_MOVE_ID = MoveId("move:orphie-magus:ultimate-dance-with-fire")
ORPHIE_QUICK_ASSIST_MOVE_ID = MoveId("move:orphie-magus:quick-assist-scorch-slash")
ORPHIE_ASSIST_STRIKE_MOVE_ID = MoveId("move:orphie-magus:assist-strike-boiling-pierce")

ORPHIE_FOCUS_ACTIVE = ScenarioConditionId("condition:orphie-magus:team-focus-active")
ORPHIE_ULTIMATE_ATTACK_BUFF_ACTIVE = ScenarioConditionId(
    "condition:orphie-magus:ultimate-attack-buff-active"
)

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_SPECIAL_FOLLOW_UP = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_EX_FOLLOW_UP = frozenset({DamageTag.EX_SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_CHAIN_FOLLOW_UP = frozenset({DamageTag.CHAIN_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_ULTIMATE_FOLLOW_UP = frozenset({DamageTag.ULTIMATE, DamageTag.FOLLOW_UP_ATTACK})
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
        element=element,
        stage_index=stage,
    )


ORPHIE_MAGUS_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            "basic-flame-blade",
            move_id=ORPHIE_BASIC_MOVE_ID,
            label="普通攻击：高压火枪（火刀）",
            source_name="普通攻击：高压火枪",
            group=SkillGroup.BASIC_ATTACK,
            tags=frozenset({DamageTag.BASIC_ATTACK, DamageTag.FOLLOW_UP_ATTACK}),
            parameter="火刀伤害倍率",
            curve="1301006",
            element=Element.FIRE,
        ),
        _move(
            "dash-attack",
            move_id=ORPHIE_DASH_MOVE_ID,
            label="冲刺攻击：突袭命令",
            source_name="冲刺攻击：突袭命令",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1301012",
            element=Element.PHYSICAL,
        ),
        _move(
            "special-hot-loaded",
            move_id=ORPHIE_SPECIAL_MOVE_ID,
            label="特殊技：热血满膛",
            source_name="特殊技：热血满膛",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            curve="1301007",
            element=Element.FIRE,
        ),
        _move(
            "special-light-eater",
            move_id=ORPHIE_SPECIAL_AUTOFIRE_MOVE_ID,
            label="特殊技：蚀光一闪（来源单项倍率）",
            source_name="特殊技：蚀光一闪",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL_FOLLOW_UP,
            parameter="伤害倍率",
            curve="1301008",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-careful",
            move_id=ORPHIE_EX_SPECIAL_MOVE_ID,
            label="强化特殊技：小心脚下",
            source_name="强化特殊技：小心脚下",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_FOLLOW_UP,
            parameter="伤害倍率",
            curve="1301009",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-red-whirlpool",
            move_id=ORPHIE_EX_WHIRLWIND_MOVE_ID,
            label="强化特殊技：灼红旋涡",
            source_name="强化特殊技：灼红旋涡",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_FOLLOW_UP,
            parameter="伤害倍率",
            curve="1301010",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-heat-charge",
            move_id=ORPHIE_EX_CHARGE_MOVE_ID,
            label="强化特殊技：蓄热充能（最大激光倍率）",
            source_name="强化特殊技：蓄热充能",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_FOLLOW_UP,
            parameter="激光最大伤害倍率",
            curve="1301011",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-blaze-burst",
            move_id=ORPHIE_EX_FINISHER_MOVE_ID,
            label="强化特殊技：燥焰迸射",
            source_name="强化特殊技：燥焰迸射",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_FOLLOW_UP,
            parameter="伤害倍率",
            curve="1301022",
            element=Element.FIRE,
        ),
        _move(
            "chain-attack",
            move_id=ORPHIE_CHAIN_MOVE_ID,
            label="连携技：枪管过热",
            source_name="连携技：枪管过热",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN_FOLLOW_UP,
            parameter="伤害倍率",
            curve="1301014",
            element=Element.FIRE,
        ),
        _move(
            "ultimate",
            move_id=ORPHIE_ULTIMATE_MOVE_ID,
            label="终结技：与火共舞（基础喷射）",
            source_name="终结技：与火共舞",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE_FOLLOW_UP,
            parameter="伤害倍率",
            curve="1301015",
            element=Element.FIRE,
        ),
        _move(
            "ultimate-extension",
            move_id=ORPHIE_ULTIMATE_MOVE_ID,
            label="终结技：与火共舞（快速支援回应后的延长部分）",
            source_name="终结技：与火共舞",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE_FOLLOW_UP,
            parameter="延长时间总伤害倍率",
            curve="1301016",
            element=Element.FIRE,
        ),
        _move(
            "assist-strike",
            move_id=ORPHIE_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：沸热穿刺",
            source_name="支援突击：沸热穿刺",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1301021",
            element=Element.FIRE,
        ),
    )
)

__all__ = [
    "ORPHIE_ASSIST_STRIKE_MOVE_ID",
    "ORPHIE_BASIC_MOVE_ID",
    "ORPHIE_CHAIN_MOVE_ID",
    "ORPHIE_COUNTER_MOVE_ID",
    "ORPHIE_DASH_MOVE_ID",
    "ORPHIE_EX_CHARGE_MOVE_ID",
    "ORPHIE_EX_FINISHER_MOVE_ID",
    "ORPHIE_EX_SPECIAL_MOVE_ID",
    "ORPHIE_EX_WHIRLWIND_MOVE_ID",
    "ORPHIE_FOCUS_ACTIVE",
    "ORPHIE_ID",
    "ORPHIE_MAGUS_REVIEWED_MAPPING",
    "ORPHIE_QUICK_ASSIST_MOVE_ID",
    "ORPHIE_SPECIAL_AUTOFIRE_MOVE_ID",
    "ORPHIE_SPECIAL_MOVE_ID",
    "ORPHIE_ULTIMATE_ATTACK_BUFF_ACTIVE",
    "ORPHIE_ULTIMATE_MOVE_ID",
    "ORPHIE_ID",
]
