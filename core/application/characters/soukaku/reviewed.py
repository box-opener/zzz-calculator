"""Reviewed live Nanoka 3.2 source mapping for Soukaku (character:1131)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


SOUKAKU_ID = CharacterId("character:1131")
FLAG_STATE_ACTIVE = ScenarioConditionId("condition:soukaku:frost-banner-active")
FLAG_ATTACK_BUFF_ACTIVE = ScenarioConditionId("condition:soukaku:flag-attack-buff-active")
FLAG_CONSUMED_VORTEX = ScenarioConditionId("condition:soukaku:flag-consumed-vortex")
ICE_DAMAGE_BUFF_ACTIVE = ScenarioConditionId("condition:soukaku:ice-damage-buff-active")
FLAG_ATTACK_HIT_ACTIVE = ScenarioConditionId("condition:soukaku:flag-attack-hit-active")

PHYSICAL_ANOMALY_RECORD_ID = "anomaly:character:1131:physical-assault"
ICE_ANOMALY_RECORD_ID = "anomaly:character:1131:ice-shatter"

BASIC_MOVE_ID = MoveId("move:soukaku:basic-rice-cake")
FLAG_BASIC_MOVE_ID = MoveId("move:soukaku:basic-frost-banner")
DASH_MOVE_ID = MoveId("move:soukaku:dash-half-share")
FLAG_DASH_MOVE_ID = MoveId("move:soukaku:dash-frost-banner")
DODGE_COUNTER_MOVE_ID = MoveId("move:soukaku:dodge-counter-no-snatching")
SPECIAL_MOVE_ID = MoveId("move:soukaku:special-cool-the-lunch")
EX_SPECIAL_MOVE_ID = MoveId("move:soukaku:ex-special-swat-insects")
FLAG_MOVE_ID = MoveId("move:soukaku:special-flag-gather-round")
CHAIN_MOVE_ID = MoveId("move:soukaku:chain-goose-chicken-slash")
ULTIMATE_MOVE_ID = MoveId("move:soukaku:ultimate-large-goose-chicken-slash")
QUICK_ASSIST_MOVE_ID = MoveId("move:soukaku:quick-assist-double-meal")
ASSIST_STRIKE_MOVE_ID = MoveId("move:soukaku:assist-strike-sweeping-blow")
PHYSICAL_ANOMALY_MOVE_ID = MoveId("move:soukaku:physical-assault")
ICE_ANOMALY_MOVE_ID = MoveId("move:soukaku:ice-shatter")
ICE_DISORDER_MOVE_ID = MoveId("move:soukaku:ice-disorder")

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
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
    element: Element = Element.ICE,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids: tuple[object, ...] = (),
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
                source_skill_id=source_skill_id,
                source_skill_components=source_skill_components,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=condition_ids,
    )


SOUKAKU_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-rice-cake-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：打年糕（{('一', '二', '三')[stage - 1]}段）",
                source="普通攻击：打年糕",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=f"113100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        *tuple(
            _move(
                f"basic-frost-banner-{stage}",
                move_id=FLAG_BASIC_MOVE_ID,
                label=f"普通攻击：打年糕·霜染刃旗（{('一', '二', '三')[stage - 1]}段）",
                source="普通攻击：打年糕（霜染刃旗）",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=f"113100{stage + 3}",
                element=Element.ICE,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
                condition_ids=(FLAG_STATE_ACTIVE,),
            )
            for stage in range(1, 4)
        ),
        _move(
            "dash-half-share",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：对半分",
            source="冲刺攻击：对半分",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1131015",
            element=Element.PHYSICAL,
        ),
        _move(
            "dash-frost-banner",
            move_id=FLAG_DASH_MOVE_ID,
            label="冲刺攻击：对半分·霜染刃旗",
            source="冲刺攻击：对半分（霜染刃旗）",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1131016",
            element=Element.ICE,
            condition_ids=(FLAG_STATE_ACTIVE,),
        ),
        _move(
            "dodge-counter-no-snatching",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：别抢零食",
            source="闪避反击：别抢零食",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            source_skill_id="1131017",
            element=Element.ICE,
        ),
        _move(
            "special-cool-lunch-field",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：吹凉便当（风场）",
            source="特殊技：吹凉便当",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="一段伤害倍率",
            source_skill_id="1131008",
        ),
        _move(
            "special-cool-lunch-finisher",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：吹凉便当（终结段）",
            source="特殊技：吹凉便当",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="终结段伤害倍率",
            source_skill_id="1131009",
        ),
        _move(
            "ex-swat-insects-continuous",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：扇走蚊虫（连续攻击，来源倍率÷2）",
            source="强化特殊技：扇走蚊虫",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="连续攻击伤害倍率",
            source_skill_components=(("1131011", 0.5),),
        ),
        _move(
            "ex-swat-insects-windfield",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：扇走蚊虫（风场）",
            source="强化特殊技：扇走蚊虫",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="风场伤害倍率",
            source_skill_id="1131010",
        ),
        _move(
            "flag-attack",
            move_id=FLAG_MOVE_ID,
            label="特殊技：集合啦！（展旗攻击）",
            source="特殊技：集合啦！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="展旗伤害倍率",
            source_skill_id="1131012",
        ),
        _move(
            "flag-attack-quick",
            move_id=FLAG_MOVE_ID,
            label="特殊技：集合啦！（快速展旗）",
            source="特殊技：集合啦！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="快速展旗伤害倍率",
            source_skill_id="1131013",
        ),
        _move(
            "flag-collect-attack",
            move_id=FLAG_MOVE_ID,
            label="特殊技：集合啦！（收旗攻击）",
            source="特殊技：集合啦！",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="收旗攻击伤害倍率",
            source_skill_id="1131014",
        ),
        _move(
            "chain-goose-chicken-slash",
            move_id=CHAIN_MOVE_ID,
            label="连携技：鹅鸡斩",
            source="连携技：鹅鸡斩",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            source_skill_id="1131018",
        ),
        _move(
            "ultimate-large-goose-chicken-slash",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：大份鹅鸡斩",
            source="终结技：大份鹅鸡斩",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            source_skill_id="1131019",
        ),
        _move(
            "quick-assist-double-meal",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：双人套餐",
            source="快速支援：双人套餐",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1131020",
        ),
        _move(
            "assist-strike-sweeping-blow",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：席卷打击",
            source="支援突击：席卷打击",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_components=(("1131024", 1.0), ("1131026", 1.0)),
        ),
    ),
    data_quality_notes=(
        "招架支援来源只提供失衡倍率；当前结果没有失衡值字段，因此不伪造伤害。",
        "强化特殊技的连续攻击来源倍率按原文除以2；单次连续段与风场分开列出，不推算点按次数、能量或整招总次数。",
        "Assist Strike 来源明确把1131024与1131026两条曲线相加为一个总伤害倍率。",
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_MOVE_ID",
    "CHAIN_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "FLAG_ATTACK_BUFF_ACTIVE",
    "FLAG_ATTACK_HIT_ACTIVE",
    "FLAG_BASIC_MOVE_ID",
    "FLAG_CONSUMED_VORTEX",
    "FLAG_DASH_MOVE_ID",
    "FLAG_MOVE_ID",
    "FLAG_STATE_ACTIVE",
    "ICE_ANOMALY_MOVE_ID",
    "ICE_ANOMALY_RECORD_ID",
    "ICE_DAMAGE_BUFF_ACTIVE",
    "ICE_DISORDER_MOVE_ID",
    "PHYSICAL_ANOMALY_MOVE_ID",
    "PHYSICAL_ANOMALY_RECORD_ID",
    "QUICK_ASSIST_MOVE_ID",
    "SOUKAKU_ID",
    "SOUKAKU_REVIEWED_MAPPING",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
