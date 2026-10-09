"""Reviewed Nanoka 3.2 move identities for Hugo (character:1291)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping
from ...ids import ScenarioConditionId


HUGO_ID = CharacterId("character:1291")
HUGO_DARK_ECHO_ACTIVE = ScenarioConditionId("condition:hugo:dark-echo-active")
HUGO_TARGET_IS_NORMAL = ScenarioConditionId("condition:hugo:target-is-normal-enemy")
HUGO_C4_ICE_RESISTANCE_IGNORE_ACTIVE = ScenarioConditionId(
    "condition:hugo:cinema4:ice-resistance-ignore-active"
)
HUGO_ICE_ANOMALY_RECORD_ID = "anomaly:character:1291:ice-shatter"
HUGO_ICE_ANOMALY_MOVE_ID = MoveId("move:hugo:ice-shatter")
HUGO_ICE_DISORDER_MOVE_ID = MoveId("move:hugo:ice-disorder")

HUGO_BASIC_QUARTET_MOVE_ID = MoveId("move:hugo:basic-dark-lyric")
HUGO_BASIC_CONCERTO_MOVE_ID = MoveId("move:hugo:basic-dark-concerto")
HUGO_DASH_MOVE_ID = MoveId("move:hugo:dodge-shadow-break")
HUGO_COUNTER_MOVE_ID = MoveId("move:hugo:dodge-counter-shadow-slash")
HUGO_SPECIAL_MOVE_ID = MoveId("move:hugo:special-soul-hunt-condemnation")
HUGO_EX_MOVE_ID = MoveId("move:hugo:ex-soul-hunt-punishment")
HUGO_CHAIN_MOVE_ID = MoveId("move:hugo:chain-destiny-trick")
HUGO_ULTIMATE_MOVE_ID = MoveId("move:hugo:ultimate-blasphemer")
HUGO_QUICK_ASSIST_MOVE_ID = MoveId("move:hugo:quick-assist-requiem")
HUGO_ASSIST_STRIKE_MOVE_ID = MoveId("move:hugo:assist-strike-ace-reversal")

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
    element: Element,
    curve: str | None = None,
    source_components: tuple[tuple[str, float], ...] = (),
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    parameter_skill_group: SkillGroup | None = None,
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
                source_skill_components=source_components,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        parameter_skill_group=parameter_skill_group,
    )


HUGO_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=HUGO_BASIC_QUARTET_MOVE_ID,
                label=f"普通攻击：暗渊四重奏（第{stage}段）",
                source_name="普通攻击：暗渊四重奏",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                element=Element.PHYSICAL,
                curve=f"129100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            "basic-fourth-slash",
            move_id=HUGO_BASIC_QUARTET_MOVE_ID,
            label="普通攻击：暗渊四重奏（第四段斩击）",
            source_name="普通攻击：暗渊四重奏",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="斩击伤害倍率",
            element=Element.ICE,
            curve="1291004",
        ),
        _move(
            "basic-fourth-shot",
            move_id=HUGO_BASIC_QUARTET_MOVE_ID,
            label="普通攻击：暗渊四重奏（第四段射击）",
            source_name="普通攻击：暗渊四重奏",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="射击伤害倍率",
            element=Element.ICE,
            curve="1291005",
        ),
        _move(
            "basic-fourth-charged-shot",
            move_id=HUGO_BASIC_QUARTET_MOVE_ID,
            label="普通攻击：暗渊四重奏（第四段蓄力射击）",
            source_name="普通攻击：暗渊四重奏",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="蓄力射击伤害倍率",
            element=Element.ICE,
            curve="1291006",
        ),
        _move(
            "basic-concerto-slash",
            move_id=HUGO_BASIC_CONCERTO_MOVE_ID,
            label="普通攻击：暗渊协奏曲（斩击）",
            source_name="普通攻击：暗渊协奏曲",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="斩击伤害倍率",
            element=Element.ICE,
            curve="1291024",
        ),
        _move(
            "basic-concerto-shot",
            move_id=HUGO_BASIC_CONCERTO_MOVE_ID,
            label="普通攻击：暗渊协奏曲（射击）",
            source_name="普通攻击：暗渊协奏曲",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="射击伤害倍率",
            element=Element.ICE,
            curve="1291025",
        ),
        _move(
            "basic-concerto-charged-shot",
            move_id=HUGO_BASIC_CONCERTO_MOVE_ID,
            label="普通攻击：暗渊协奏曲（蓄力射击）",
            source_name="普通攻击：暗渊协奏曲",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="蓄力射击伤害倍率",
            element=Element.ICE,
            curve="1291026",
        ),
        _move(
            "dash-attack",
            move_id=HUGO_DASH_MOVE_ID,
            label="冲刺攻击：诡影·破",
            source_name="冲刺攻击：诡影·破",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            element=Element.PHYSICAL,
            curve="1291011",
        ),
        _move(
            "dodge-counter",
            move_id=HUGO_COUNTER_MOVE_ID,
            label="闪避反击：诡影·斩（连续攻击）",
            source_name="闪避反击：诡影·斩",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291012",
        ),
        _move(
            "dodge-counter-shot",
            move_id=HUGO_COUNTER_MOVE_ID,
            label="闪避反击：诡影·斩（普通攻击射击）",
            source_name="闪避反击：诡影·斩",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="派生射击伤害倍率",
            element=Element.ICE,
            curve="1291013",
            parameter_skill_group=SkillGroup.DODGE,
        ),
        _move(
            "dodge-counter-charged-shot",
            move_id=HUGO_COUNTER_MOVE_ID,
            label="闪避反击：诡影·斩（普通攻击蓄力射击）",
            source_name="闪避反击：诡影·斩",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="派生蓄力射击伤害倍率",
            element=Element.ICE,
            curve="1291014",
            parameter_skill_group=SkillGroup.DODGE,
        ),
        _move(
            "special",
            move_id=HUGO_SPECIAL_MOVE_ID,
            label="特殊技：魂狩·断罪",
            source_name="特殊技：魂狩·断罪",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291008",
        ),
        _move(
            "ex-special-spin",
            move_id=HUGO_EX_MOVE_ID,
            label="强化特殊技：魂狩·惩戒（旋转）",
            source_name="强化特殊技：魂狩·惩戒",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291009",
        ),
        _move(
            "ex-special-finisher",
            move_id=HUGO_EX_MOVE_ID,
            label="强化特殊技：魂狩·惩戒（终结一击）",
            source_name="强化特殊技：魂狩·惩戒",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291010",
        ),
        _move(
            "chain-attack",
            move_id=HUGO_CHAIN_MOVE_ID,
            label="连携技：命运戏法（来源倍率）",
            source_name="连携技：命运戏法",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="斩击伤害倍率",
            element=Element.ICE,
            curve="1291015",
        ),
        _move(
            "ultimate",
            move_id=HUGO_ULTIMATE_MOVE_ID,
            label="终结技：渎神者（来源总倍率）",
            source_name="终结技：渎神者",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291018",
        ),
        _move(
            "quick-assist",
            move_id=HUGO_QUICK_ASSIST_MOVE_ID,
            label="快速支援：葬歌（连续攻击）",
            source_name="快速支援：葬歌",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291019",
        ),
        _move(
            "quick-assist-shot",
            move_id=HUGO_QUICK_ASSIST_MOVE_ID,
            label="快速支援：葬歌（普通攻击射击）",
            source_name="快速支援：葬歌",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="派生射击伤害倍率",
            element=Element.ICE,
            curve="1291027",
            parameter_skill_group=SkillGroup.ASSIST,
        ),
        _move(
            "quick-assist-charged-shot",
            move_id=HUGO_QUICK_ASSIST_MOVE_ID,
            label="快速支援：葬歌（普通攻击蓄力射击）",
            source_name="快速支援：葬歌",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="派生蓄力射击伤害倍率",
            element=Element.ICE,
            curve="1291028",
            parameter_skill_group=SkillGroup.ASSIST,
        ),
        _move(
            "assist-strike",
            move_id=HUGO_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：王牌反转（来源倍率）",
            source_name="支援突击：王牌反转",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            element=Element.ICE,
            curve="1291023",
        ),
    )
)


__all__ = [
    "HUGO_ASSIST_STRIKE_MOVE_ID",
    "HUGO_BASIC_CONCERTO_MOVE_ID",
    "HUGO_BASIC_QUARTET_MOVE_ID",
    "HUGO_CHAIN_MOVE_ID",
    "HUGO_COUNTER_MOVE_ID",
    "HUGO_C4_ICE_RESISTANCE_IGNORE_ACTIVE",
    "HUGO_DASH_MOVE_ID",
    "HUGO_DARK_ECHO_ACTIVE",
    "HUGO_EX_MOVE_ID",
    "HUGO_ID",
    "HUGO_ICE_ANOMALY_MOVE_ID",
    "HUGO_ICE_ANOMALY_RECORD_ID",
    "HUGO_ICE_DISORDER_MOVE_ID",
    "HUGO_QUICK_ASSIST_MOVE_ID",
    "HUGO_REVIEWED_MAPPING",
    "HUGO_SPECIAL_MOVE_ID",
    "HUGO_TARGET_IS_NORMAL",
    "HUGO_ULTIMATE_MOVE_ID",
]
