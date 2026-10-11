"""Reviewed live Nanoka 3.2 move mapping for Norma (character:1571)."""

from __future__ import annotations

from dataclasses import dataclass

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import RuleItemId, ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


NORMA_ID = CharacterId("character:1571")

CORE_INITIAL_CRIT_DAMAGE_RULE_ID = RuleItemId(
    "rule:character:1571:core:initial-crit-damage"
)
EXTRA_TECH_GAP_RULE_ID = RuleItemId(
    "rule:character:1571:extra-ability:technical-gap-stacks"
)
CURRENT_TECH_GAP_STACKS = ScenarioParameterId(
    "parameter:character:1571:current-technology-gap-stacks"
)
TERM_1000012_ACTIVE = ScenarioConditionId(
    "condition:character:1571:term-1000012-active"
)
EN_NI_BARRAGE_ACTIVE = ScenarioConditionId(
    "condition:character:1571:en-ni-barrage-active"
)
CINEMA1_RESISTANCE_REDUCTION_ACTIVE = ScenarioConditionId(
    "condition:character:1571:cinema1-all-resistance-reduction-active"
)
CINEMA6_MISSILE_CURRENT_HIT = ScenarioConditionId(
    "condition:character:1571:cinema6-missile-current-hit"
)
EX_TARGET_STUNNED = ScenarioConditionId(
    "condition:character:1571:ex-special-target-stunned"
)
EX_TARGET_NOT_STUNNED = ScenarioConditionId(
    "condition:character:1571:ex-special-target-not-stunned"
)

BASIC_MOVE_ID = MoveId("move:norma:basic-engineering-insurance")
HAT_TRICK_MOVE_ID = MoveId("move:norma:basic-hat-trick")
DASH_MOVE_ID = MoveId("move:norma:dash-dead-line-dash")
DODGE_COUNTER_MOVE_ID = MoveId("move:norma:dodge-counter-compliance-test")
SPECIAL_MOVE_ID = MoveId("move:norma:special-high-temperature-fusing")
EX_SPECIAL_MOVE_ID = MoveId("move:norma:ex-special-en-ni-barrage")
CHAIN_MOVE_ID = MoveId("move:norma:chain-impact-drilling")
ULTIMATE_MOVE_ID = MoveId("move:norma:ultimate-firepower-doctrine")
QUICK_ASSIST_MOVE_ID = MoveId("move:norma:quick-assist-rumble-support")
ASSIST_STRIKE_MOVE_ID = MoveId("move:norma:assist-strike-technical-suppression")


@dataclass(frozen=True, slots=True)
class NormaSourceCurve:
    """A source ratio whose attack actor/event identity is not established."""

    entry_key: str
    display_name: str
    source_name: str
    parameter_name: str
    source_skill_id: str
    parameter_skill_group: SkillGroup
    element: Element
    source_text_hint: str
    move_id: MoveId | None = None
    authored_skill_group: SkillGroup | None = None
    authored_damage_tags: frozenset[DamageTag] = frozenset()


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tag: DamageTag,
    parameter: str,
    source_skill_id: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    conditions: tuple[object, ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=frozenset({tag}),
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=parameter,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=Element.FIRE,
        stage_index=stage,
        condition_ids=conditions,
    )


_BASIC_SOURCE = "普通攻击：工程保险"
_EX_SOURCE = "强化特殊技：嗯呢弹幕"
_EX_EXPERIMENT_SOURCE = "强化特殊技：火力实验"
_BASIC = DamageTag.BASIC_ATTACK
_DASH = DamageTag.DASH_ATTACK
_COUNTER = DamageTag.DODGE_COUNTER
_SPECIAL = DamageTag.SPECIAL_ATTACK
_EX = DamageTag.EX_SPECIAL_ATTACK
_CHAIN = DamageTag.CHAIN_ATTACK
_ULTIMATE = DamageTag.ULTIMATE
_ASSIST = DamageTag.ASSIST


NORMA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：工程保险（{('一', '二', '三', '四')[stage - 1]}段）",
                source=_BASIC_SOURCE,
                group=SkillGroup.BASIC_ATTACK,
                tag=_BASIC,
                parameter=f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                source_skill_id=f"157100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "basic-hat-trick",
            move_id=HAT_TRICK_MOVE_ID,
            label="普通攻击：帽子把戏",
            source="普通攻击：帽子把戏",
            group=SkillGroup.BASIC_ATTACK,
            tag=_BASIC,
            parameter="伤害倍率",
            source_skill_id="1571005",
        ),
        _move(
            "dash-attack",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：死线冲刺",
            source="冲刺攻击：死线冲刺",
            group=SkillGroup.DODGE,
            tag=_DASH,
            parameter="伤害倍率",
            source_skill_id="1571016",
        ),
        _move(
            "dodge-counter-compliance-test",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：合规测试",
            source="闪避反击：合规测试",
            group=SkillGroup.DODGE,
            tag=_COUNTER,
            parameter="伤害倍率",
            source_skill_id="1571017",
        ),
        _move(
            "special-high-temperature-fusing",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：高温熔断",
            source="特殊技：高温熔断",
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1571006",
        ),
        _move(
            "ex-turret-shot",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：嗯呢弹幕（驾驶炮塔射击）",
            source=_EX_SOURCE,
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_EX,
            parameter="射击伤害倍率",
            source_skill_id="1571007",
        ),
        _move(
            "ex-armor-shell",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：嗯呢弹幕（破甲弹头）",
            source=_EX_SOURCE,
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_EX,
            parameter="破甲弹头伤害倍率",
            source_skill_id="1571008",
            conditions=(EX_TARGET_NOT_STUNNED,),
        ),
        _move(
            "ex-high-explosive-shell",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：嗯呢弹幕（高爆弹头）",
            source=_EX_SOURCE,
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_EX,
            parameter="高爆弹头伤害倍率",
            source_skill_id="1571009",
            conditions=(EX_TARGET_STUNNED,),
        ),
        _move(
            "ex-extended-fire-per-second",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：嗯呢弹幕（延长射击每秒）",
            source=_EX_SOURCE,
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_EX,
            parameter="延长射击每秒伤害倍率",
            source_skill_id="1571010",
        ),
        _move(
            "ex-extended-armor-per-second",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：嗯呢弹幕（延长射击破甲弹头每秒）",
            source=_EX_SOURCE,
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_EX,
            parameter="延长射击破甲弹头每秒伤害倍率",
            source_skill_id="1571011",
            conditions=(EX_TARGET_NOT_STUNNED,),
        ),
        _move(
            "ex-extended-high-explosive-per-second",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：嗯呢弹幕（延长射击高爆弹头每秒）",
            source=_EX_SOURCE,
            group=SkillGroup.SPECIAL_ATTACK,
            tag=_EX,
            parameter="延长射击高爆弹头每秒伤害倍率",
            source_skill_id="1571012",
            conditions=(EX_TARGET_STUNNED,),
        ),
        _move(
            "chain-impact-drilling",
            move_id=CHAIN_MOVE_ID,
            label="连携技：冲击钻探",
            source="连携技：冲击钻探",
            group=SkillGroup.CHAIN_ATTACK,
            tag=_CHAIN,
            parameter="伤害倍率",
            source_skill_id="1571018",
        ),
        _move(
            "ultimate-firepower-doctrine",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：优势火力学说",
            source="终结技：优势火力学说",
            group=SkillGroup.ULTIMATE,
            tag=_ULTIMATE,
            parameter="伤害倍率",
            source_skill_id="1571019",
        ),
        _move(
            "quick-assist-rumble-support",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：隆隆援护",
            source="快速支援：隆隆援护",
            group=SkillGroup.ASSIST,
            tag=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1571020",
        ),
        _move(
            "assist-strike-technical-suppression",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：技术压制",
            source="支援突击：技术压制",
            group=SkillGroup.ASSIST,
            tag=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1571024",
        ),
    )
)


NORMA_UNRESOLVED_ACTOR_CURVES = (
    NormaSourceCurve(
        entry_key="special-target-practice-turret",
        display_name="特殊技：打靶练习（自动炮塔攻击）",
        source_name="特殊技：打靶练习",
        parameter_name="伤害倍率",
        source_skill_id="1571013",
        parameter_skill_group=SkillGroup.SPECIAL_ATTACK,
        element=Element.FIRE,
        source_text_hint="This automatic attack is attributed to Term 1000010; the source does not establish its actor or inherited ATK/Crit snapshot.",
    ),
    NormaSourceCurve(
        entry_key="ex-firepower-armor-shell",
        display_name="强化特殊技：火力实验（自动炮塔破甲弹头）",
        source_name=_EX_EXPERIMENT_SOURCE,
        parameter_name="额外破甲弹头伤害倍率",
        source_skill_id="1571014",
        parameter_skill_group=SkillGroup.SPECIAL_ATTACK,
        element=Element.FIRE,
        source_text_hint="The source attributes this automatic shell to Term 1000010/its turret but does not establish the actor or inherited ATK/Crit snapshot.",
    ),
    NormaSourceCurve(
        entry_key="ex-firepower-high-explosive-shell",
        display_name="强化特殊技：火力实验（自动炮塔高爆弹头）",
        source_name=_EX_EXPERIMENT_SOURCE,
        parameter_name="额外高爆弹头伤害倍率",
        source_skill_id="1571015",
        parameter_skill_group=SkillGroup.SPECIAL_ATTACK,
        element=Element.FIRE,
        source_text_hint="The source attributes this automatic shell to Term 1000010/its turret but does not establish the actor or inherited ATK/Crit snapshot.",
    ),
)


__all__ = [
    "BASIC_MOVE_ID",
    "CINEMA1_RESISTANCE_REDUCTION_ACTIVE",
    "CINEMA6_MISSILE_CURRENT_HIT",
    "CORE_INITIAL_CRIT_DAMAGE_RULE_ID",
    "CURRENT_TECH_GAP_STACKS",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EN_NI_BARRAGE_ACTIVE",
    "EX_SPECIAL_MOVE_ID",
    "EX_TARGET_NOT_STUNNED",
    "EX_TARGET_STUNNED",
    "EXTRA_TECH_GAP_RULE_ID",
    "HAT_TRICK_MOVE_ID",
    "NORMA_ID",
    "NORMA_REVIEWED_MAPPING",
    "NORMA_UNRESOLVED_ACTOR_CURVES",
    "NormaSourceCurve",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "TERM_1000012_ACTIVE",
    "ULTIMATE_MOVE_ID",
    "ASSIST_STRIKE_MOVE_ID",
    "CHAIN_MOVE_ID",
]
