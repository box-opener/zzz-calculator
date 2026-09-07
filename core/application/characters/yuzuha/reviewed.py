"""Manually reviewed Yuzuha skill taxonomy and scenario identities."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


YUZUHA_ID = CharacterId("character:1411")
TANUKI_WISH_ACTIVE_CONDITION_ID = ScenarioConditionId(
    "condition:yuzuha:tanuki-wish-active"
)
TANUKI_ATTACK_CONDITION_ID = ScenarioConditionId(
    "condition:yuzuha:tanuki-helper-team-attack"
)
TANUKI_SELF_ATTACK_CONDITION_ID = ScenarioConditionId(
    "condition:yuzuha:tanuki-helper-self-attack"
)
EXTRA_ABILITY_ACTIVE_CONDITION_ID = ScenarioConditionId(
    "condition:yuzuha:extra-ability-active"
)
SWEET_SCARE_ACTIVE_CONDITION_ID = ScenarioConditionId(
    "condition:yuzuha:sweet-scare-active"
)


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_FOLLOW_UP = frozenset({DamageTag.BASIC_ATTACK, DamageTag.FOLLOW_UP_ATTACK})
_DODGE = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _p(key: str, name: str, *condition_ids: object) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(key, name, tuple(condition_ids))


def _move(
    key: str,
    move_id: str,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    params: tuple[NanokaDamageParameterSpec, ...],
    relation: MultiplierRelation,
    *,
    stage: int | None = None,
    conditions: tuple[object, ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=MoveId(move_id),
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=params,
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
        condition_ids=conditions,
    )


YUZUHA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-tanuki-claw-{stage}",
                "move:yuzuha:tanuki-claw",
                f"普通攻击：狸之爪（{stage}段）",
                "普通攻击：狸之爪",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                (_p(f"stage-{stage}", f"{('一','二','三','四','五')[stage - 1]}段伤害倍率"),),
                MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-hard-candy-shot",
            "move:yuzuha:hard-candy-shot",
            "普通攻击：硬糖射击",
            "普通攻击：硬糖射击",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (_p("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "basic-candy-fireworks",
            "move:yuzuha:candy-fireworks",
            "普通攻击：彩糖花火",
            "普通攻击：彩糖花火",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (_p("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "basic-candy-fireworks-polar",
            "move:yuzuha:candy-fireworks-polar",
            "普通攻击：彩糖花火·极",
            "普通攻击：彩糖花火·极",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (_p("complete", "伤害倍率"),),
            MultiplierRelation.COMPLETE,
        ),
        _move(
            "basic-tanuki-helper",
            "move:yuzuha:tanuki-helper",
            "普通攻击：狸之助",
            "普通攻击：狸之助",
            SkillGroup.BASIC_ATTACK,
            _FOLLOW_UP,
            (
                _p("team-attack", "狸猫阿釜协同柚叶攻击伤害倍率", TANUKI_ATTACK_CONDITION_ID),
                _p("self-attack", "狸猫阿釜自主攻击伤害倍率", TANUKI_SELF_ATTACK_CONDITION_ID),
            ),
            MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
        ),
        _move("dodge-dash", "move:yuzuha:dodge-dash", "冲刺攻击：你要倒霉了！", "冲刺攻击：你要倒霉了！", SkillGroup.DODGE, _DODGE, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("dodge-counter", "move:yuzuha:dodge-counter", "闪避反击：报复开始~", "闪避反击：报复开始~", SkillGroup.DODGE, _COUNTER, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-gummy-bombard", "move:yuzuha:gummy-bombard", "特殊技：软糖轰击", "特殊技：软糖轰击", SkillGroup.SPECIAL_ATTACK, _SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-ex-toothache", "move:yuzuha:toothache", "强化特殊技：小心蛀牙", "强化特殊技：小心蛀牙", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("special-ex-now", "move:yuzuha:toothache-now", "强化特殊技：小心蛀牙，就是现在！", "强化特殊技：小心蛀牙，就是现在！", SkillGroup.SPECIAL_ATTACK, _EX_SPECIAL, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("chain-prank-battle", "move:yuzuha:prank-battle", "连携技：恶作剧合战", "连携技：恶作剧合战", SkillGroup.CHAIN_ATTACK, _CHAIN, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("ultimate-no-surrender", "move:yuzuha:no-surrender", "终结技：不投降就捣乱", "终结技：不投降就捣乱", SkillGroup.ULTIMATE, _ULTIMATE, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-quick-dessert", "move:yuzuha:quick-dessert", "快速支援：甜点时间", "快速支援：甜点时间", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-cookie", "move:yuzuha:cookie", "支援突击：来块曲奇", "支援突击：来块曲奇", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
        _move("assist-stuffed-candy", "move:yuzuha:stuffed-candy", "支援突击：夹心硬糖射击", "支援突击：夹心硬糖射击", SkillGroup.ASSIST, _ASSIST, (_p("complete", "伤害倍率"),), MultiplierRelation.COMPLETE),
    )
)


__all__ = [
    "EXTRA_ABILITY_ACTIVE_CONDITION_ID",
    "SWEET_SCARE_ACTIVE_CONDITION_ID",
    "TANUKI_ATTACK_CONDITION_ID",
    "TANUKI_SELF_ATTACK_CONDITION_ID",
    "TANUKI_WISH_ACTIVE_CONDITION_ID",
    "YUZUHA_ID",
    "YUZUHA_REVIEWED_MAPPING",
]
