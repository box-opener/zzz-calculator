"""Reviewed Nanoka 3.2 move identities for Jane Doe (character:1261)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


JANE_DOE_ID = CharacterId("character:1261")
JANE_FRENZY_ACTIVE = ScenarioConditionId("condition:jane-doe:frenzy-active")
JANE_GNAWING_ACTIVE = ScenarioConditionId("condition:jane-doe:gnawing-active")
JANE_SAHOFF_JUMP_AVAILABLE = ScenarioConditionId("condition:jane-doe:sahoff-jump-available")
JANE_C4_ANOMALY_BONUS_ACTIVE = ScenarioConditionId(
    "condition:jane-doe:cinema4-anomaly-bonus-active"
)
JANE_C6_ASSAULT_CRIT_TRIGGERED = ScenarioConditionId(
    "condition:jane-doe:cinema6-assault-crit-triggered"
)

JANE_BASIC_MOVE_ID = MoveId("move:jane-doe:basic-footwork")
JANE_SAHOFF_MOVE_ID = MoveId("move:jane-doe:basic-sahoff-jump")
JANE_DASH_MOVE_ID = MoveId("move:jane-doe:dash-blade-hop")
JANE_FRENZY_DASH_MOVE_ID = MoveId("move:jane-doe:dash-phantom-thrust")
JANE_COUNTER_MOVE_ID = MoveId("move:jane-doe:dodge-counter-shadow")
JANE_FRENZY_COUNTER_MOVE_ID = MoveId("move:jane-doe:dodge-counter-shadow-dance")
JANE_SPECIAL_MOVE_ID = MoveId("move:jane-doe:special-skybreaker")
JANE_EX_MOVE_ID = MoveId("move:jane-doe:ex-skybreaker-sweep")
JANE_FRENZY_EX_MOVE_ID = MoveId("move:jane-doe:ex-skybreaker-rush")
JANE_CHAIN_MOVE_ID = MoveId("move:jane-doe:chain-sins-in-bloom")
JANE_ULTIMATE_MOVE_ID = MoveId("move:jane-doe:ultimate-final-act")
JANE_QUICK_ASSIST_MOVE_ID = MoveId("move:jane-doe:quick-assist-barb")
JANE_FRENZY_QUICK_ASSIST_MOVE_ID = MoveId("move:jane-doe:quick-assist-hook-jump")
JANE_ASSIST_STRIKE_MOVE_ID = MoveId("move:jane-doe:assist-strike-gale-sweep")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_BASIC_DASH = frozenset({DamageTag.BASIC_ATTACK, DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_EX_DASH = frozenset({DamageTag.EX_SPECIAL_ATTACK, DamageTag.DASH_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    curve: str,
    conditions: tuple[ScenarioConditionId, ...] = (),
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=parameter,
                source_skill_id=curve,
                condition_ids=conditions,
            ),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
        condition_ids=conditions,
    )


_KNOWN_MOVES = (
    *tuple(
        _move(
            f"basic-footwork-{stage}",
            move_id=JANE_BASIC_MOVE_ID,
            label=(
                f"普通攻击：跳步刃舞（第{('一', '二', '三', '四', '五')[stage - 1]}段）"
                if stage < 6
                else "普通攻击：跳步刃舞（第六段·兼具冲刺攻击标签）"
            ),
            source="普通攻击：跳步刃舞",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC if stage < 6 else _BASIC_DASH,
            parameter=f"{('一', '二', '三', '四', '五', '六')[stage - 1]}段伤害倍率",
            curve=f"126100{stage}",
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
        for stage in range(1, 7)
    ),
    _move(
        "sahoff-jump-continuous",
        move_id=JANE_SAHOFF_MOVE_ID,
        label="普通攻击：萨霍夫跳（连续攻击）",
        source="普通攻击：萨霍夫跳",
        group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        parameter="连续攻击伤害倍率",
        curve="1261007",
        conditions=(JANE_FRENZY_ACTIVE, JANE_SAHOFF_JUMP_AVAILABLE),
    ),
    _move(
        "sahoff-jump-finisher",
        move_id=JANE_SAHOFF_MOVE_ID,
        label="普通攻击：萨霍夫跳（终结一击）",
        source="普通攻击：萨霍夫跳",
        group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        parameter="终结一击伤害倍率",
        curve="1261008",
        conditions=(JANE_FRENZY_ACTIVE, JANE_SAHOFF_JUMP_AVAILABLE),
    ),
    _move(
        "dash-blade-hop-first-dodge",
        move_id=JANE_DASH_MOVE_ID,
        label="冲刺攻击：刀刃跳（一段闪避衔接）",
        source="冲刺攻击：刀刃跳",
        group=SkillGroup.DODGE,
        tags=_DASH,
        parameter="一段伤害倍率",
        curve="1261011",
    ),
    _move(
        "dash-blade-hop-second-dodge",
        move_id=JANE_DASH_MOVE_ID,
        label="冲刺攻击：刀刃跳（二段闪避衔接）",
        source="冲刺攻击：刀刃跳",
        group=SkillGroup.DODGE,
        tags=_DASH,
        parameter="二段伤害倍率",
        curve="1261012",
    ),
    _move(
        "dash-phantom-thrust",
        move_id=JANE_FRENZY_DASH_MOVE_ID,
        label="冲刺攻击：虚像突刺（狂热）",
        source="冲刺攻击：虚像突刺",
        group=SkillGroup.DODGE,
        tags=_DASH,
        parameter="伤害倍率",
        curve="1261013",
        conditions=(JANE_FRENZY_ACTIVE,),
    ),
    _move(
        "dodge-counter-shadow-first-dodge",
        move_id=JANE_COUNTER_MOVE_ID,
        label="闪避反击：疾影（一段闪避衔接）",
        source="闪避反击：疾影",
        group=SkillGroup.DODGE,
        tags=_COUNTER,
        parameter="一段伤害倍率",
        curve="1261014",
    ),
    _move(
        "dodge-counter-shadow-second-dodge",
        move_id=JANE_COUNTER_MOVE_ID,
        label="闪避反击：疾影（二段闪避衔接）",
        source="闪避反击：疾影",
        group=SkillGroup.DODGE,
        tags=_COUNTER,
        parameter="二段伤害倍率",
        curve="1261015",
    ),
    _move(
        "dodge-counter-shadow-dance",
        move_id=JANE_FRENZY_COUNTER_MOVE_ID,
        label="闪避反击：疾影连舞（狂热）",
        source="闪避反击：疾影连舞",
        group=SkillGroup.DODGE,
        tags=_COUNTER,
        parameter="伤害倍率",
        curve="1261016",
        conditions=(JANE_FRENZY_ACTIVE,),
    ),
    _move(
        "special-skybreaker",
        move_id=JANE_SPECIAL_MOVE_ID,
        label="特殊技：掠空",
        source="特殊技：掠空",
        group=SkillGroup.SPECIAL_ATTACK,
        tags=_SPECIAL,
        parameter="伤害倍率",
        curve="1261009",
    ),
    _move(
        "ex-skybreaker-sweep",
        move_id=JANE_EX_MOVE_ID,
        label="强化特殊技：掠空-横扫",
        source="强化特殊技：掠空-横扫",
        group=SkillGroup.SPECIAL_ATTACK,
        tags=_EX,
        parameter="伤害倍率",
        curve="1261010",
    ),
    _move(
        "ex-skybreaker-rush",
        move_id=JANE_FRENZY_EX_MOVE_ID,
        label="强化特殊技：掠空-强袭（狂热；兼具冲刺攻击标签）",
        source="强化特殊技：掠空-强袭",
        group=SkillGroup.SPECIAL_ATTACK,
        tags=_EX_DASH,
        parameter="伤害倍率",
        curve="1261031",
        conditions=(JANE_FRENZY_ACTIVE,),
    ),
    _move(
        "chain-sins-in-bloom",
        move_id=JANE_CHAIN_MOVE_ID,
        label="连携技：罪孽生花",
        source="连携技：罪孽生花",
        group=SkillGroup.CHAIN_ATTACK,
        tags=_CHAIN,
        parameter="伤害倍率",
        curve="1261017",
    ),
    _move(
        "ultimate-final-act",
        move_id=JANE_ULTIMATE_MOVE_ID,
        label="终结技：终幕演出",
        source="终结技：终幕演出",
        group=SkillGroup.ULTIMATE,
        tags=_ULTIMATE,
        parameter="伤害倍率",
        curve="1261018",
    ),
    _move(
        "quick-assist-barb",
        move_id=JANE_QUICK_ASSIST_MOVE_ID,
        label="快速支援：乌刺",
        source="快速支援：乌刺",
        group=SkillGroup.ASSIST,
        tags=_ASSIST,
        parameter="伤害倍率",
        curve="1261019",
    ),
    _move(
        "quick-assist-hook-jump",
        move_id=JANE_FRENZY_QUICK_ASSIST_MOVE_ID,
        label="快速支援：勾手跳（狂热）",
        source="快速支援：勾手跳",
        group=SkillGroup.ASSIST,
        tags=_ASSIST,
        parameter="伤害倍率",
        curve="1261020",
        conditions=(JANE_FRENZY_ACTIVE,),
    ),
    _move(
        "assist-strike-gale-sweep",
        move_id=JANE_ASSIST_STRIKE_MOVE_ID,
        label="支援突击：疾风扫",
        source="支援突击：疾风扫",
        group=SkillGroup.ASSIST,
        tags=_ASSIST,
        parameter="伤害倍率",
        curve="1261024",
    ),
)

JANE_DOE_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=_KNOWN_MOVES,
    data_quality_notes=(
        "Jane's Basic Saohov Jump continuous segment has separate source curves for Potential 0 and Potential 1+; the compiler selects the matching source curve.",
        "Cinema 6's 1600% Anomaly Proficiency Physical extra attack remains a local partial until its event identity is clarified.",
    ),
)


__all__ = [name for name in globals() if name.isupper()] + ["JANE_DOE_REVIEWED_MAPPING"]
