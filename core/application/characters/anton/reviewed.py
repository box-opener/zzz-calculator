"""Reviewed Nanoka 3.2 move identities for Anton (character:1111)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


ANTON_ID = CharacterId("character:1111")
ANTON_ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1111:electric-shock")
ANTON_ELECTRIC_ANOMALY_MOVE_ID = MoveId("move:anton:electric-shock")
ANTON_ELECTRIC_DISORDER_MOVE_ID = MoveId("move:anton:electric-disorder")

BURST_STATE_ACTIVE = ScenarioConditionId("condition:anton:burst-state-active")
CINEMA4_TEAM_CRIT_ACTIVE = ScenarioConditionId("condition:anton:cinema4-team-crit-active")
EXTRA_SHOCK_READY = ScenarioConditionId("condition:anton:extra-shock-ready")
ENEMY_SHOCKED_ACTIVE = ScenarioConditionId("condition:anton:enemy-shocked")
ELECTRIC_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:anton:electric-disorder-remaining-seconds"
)

BASIC_NORMAL_MOVE_ID = MoveId("move:anton:basic-normal")
BASIC_NORMAL_PILE_MOVE_ID = MoveId("move:anton:basic-normal-pile-driver")
BASIC_BURST_1_MOVE_ID = MoveId("move:anton:basic-burst-1")
BASIC_BURST_2_MOVE_ID = MoveId("move:anton:basic-burst-2-drill")
BASIC_BURST_3_MOVE_ID = MoveId("move:anton:basic-burst-3-pile-driver")
DASH_ATTACK_MOVE_ID = MoveId("move:anton:dash-attack")
DODGE_COUNTER_MOVE_ID = MoveId("move:anton:dodge-counter")
BURST_DODGE_COUNTER_MOVE_ID = MoveId("move:anton:burst-dodge-counter-drill")
SPECIAL_PILE_MOVE_ID = MoveId("move:anton:special-pile-driver")
EX_SPECIAL_PILE_MOVE_ID = MoveId("move:anton:ex-special-pile-driver")
BURST_SPECIAL_PILE_MOVE_ID = MoveId("move:anton:burst-special-pile-driver")
CHAIN_PILE_MOVE_ID = MoveId("move:anton:chain-pile-driver")
ULTIMATE_PILE_MOVE_ID = MoveId("move:anton:ultimate-pile-driver")
QUICK_ASSIST_MOVE_ID = MoveId("move:anton:quick-assist")
BURST_QUICK_ASSIST_DRILL_MOVE_ID = MoveId("move:anton:burst-quick-assist-drill")
ASSIST_STRIKE_MIXED_MOVE_ID = MoveId("move:anton:assist-strike-drill-pile")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move(
    *,
    key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    element: Element,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    conditions: tuple[ScenarioConditionId, ...] = (),
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
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=conditions,
    )


_BASIC_NAME = "普通攻击：热血上工操"
_DASH_NAME = "冲刺攻击：硬碰硬"
_DODGE_COUNTER_NAME = "闪避反击：回敬拳击"
_BURST_COUNTER_NAME = "闪避反击：过载钻击（爆发状态）"
_SPECIAL_NAME = "特殊技：兄弟，转起来！"
_EX_NAME = "强化特殊技：兄弟，突破天际！"
_BURST_SPECIAL_NAME = "特殊技：爆发钻击（爆发状态）"
_CHAIN_NAME = "连携技：转转转！"
_ULTIMATE_NAME = "终结技：转转转转转！"
_QUICK_ASSIST_NAME = "快速支援：并肩作战"
_BURST_QUICK_ASSIST_NAME = "快速支援：援护钻击（爆发状态）"
_ASSIST_STRIKE_NAME = "支援突击：极限突进"


ANTON_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                key=f"basic-normal-{stage}",
                move_id=(BASIC_NORMAL_PILE_MOVE_ID if stage == 4 else BASIC_NORMAL_MOVE_ID),
                label=f"普通攻击：热血上工操（第{stage}段）",
                source_name=_BASIC_NAME,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{('一', '二', '三', '四')[stage - 1]}段伤害倍率",
                source_skill_id=f"111100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        *tuple(
            _move(
                key=f"basic-burst-{stage}",
                move_id=(BASIC_BURST_1_MOVE_ID, BASIC_BURST_2_MOVE_ID, BASIC_BURST_3_MOVE_ID)[stage - 1],
                label=f"普通攻击：热血上工操（爆发状态·第{stage}段）",
                source_name=f"{_BASIC_NAME}（爆发状态）",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=f"111100{stage + 5}",
                element=Element.ELECTRIC,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
                conditions=(BURST_STATE_ACTIVE,),
            )
            for stage in range(1, 4)
        ),
        _move(
            key="dash-attack", move_id=DASH_ATTACK_MOVE_ID,
            label="冲刺攻击：硬碰硬", source_name=_DASH_NAME,
            group=SkillGroup.DODGE, tags=_DASH, parameter_name="伤害倍率",
            source_skill_id="1111012", element=Element.PHYSICAL,
        ),
        _move(
            key="dodge-counter", move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：回敬拳击", source_name=_DODGE_COUNTER_NAME,
            group=SkillGroup.DODGE, tags=_COUNTER, parameter_name="伤害倍率",
            source_skill_id="1111014", element=Element.PHYSICAL,
        ),
        _move(
            key="burst-dodge-counter", move_id=BURST_DODGE_COUNTER_MOVE_ID,
            label="闪避反击：过载钻击（爆发状态）", source_name=_BURST_COUNTER_NAME,
            group=SkillGroup.DODGE, tags=_COUNTER, parameter_name="伤害倍率",
            source_skill_id="1111015", element=Element.ELECTRIC,
            conditions=(BURST_STATE_ACTIVE,),
        ),
        _move(
            key="special-pile-driver", move_id=SPECIAL_PILE_MOVE_ID,
            label="特殊技：兄弟，转起来！", source_name=_SPECIAL_NAME,
            group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter_name="伤害倍率",
            source_skill_id="1111009", element=Element.ELECTRIC,
        ),
        _move(
            key="ex-special-pile-driver", move_id=EX_SPECIAL_PILE_MOVE_ID,
            label="强化特殊技：兄弟，突破天际！", source_name=_EX_NAME,
            group=SkillGroup.SPECIAL_ATTACK, tags=_EX_SPECIAL, parameter_name="伤害倍率",
            source_skill_id="1111011", element=Element.ELECTRIC,
        ),
        _move(
            key="burst-special-pile-driver", move_id=BURST_SPECIAL_PILE_MOVE_ID,
            label="特殊技：爆发钻击（爆发状态）", source_name=_BURST_SPECIAL_NAME,
            group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter_name="伤害倍率",
            source_skill_id="1111010", element=Element.ELECTRIC,
            conditions=(BURST_STATE_ACTIVE,),
        ),
        _move(
            key="chain-pile-driver", move_id=CHAIN_PILE_MOVE_ID,
            label="连携技：转转转！", source_name=_CHAIN_NAME,
            group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN, parameter_name="伤害倍率",
            source_skill_id="1111016", element=Element.ELECTRIC,
        ),
        _move(
            key="ultimate-pile-driver", move_id=ULTIMATE_PILE_MOVE_ID,
            label="终结技：转转转转转！", source_name=_ULTIMATE_NAME,
            group=SkillGroup.ULTIMATE, tags=_ULTIMATE, parameter_name="伤害倍率",
            source_skill_id="1111017", element=Element.ELECTRIC,
        ),
        _move(
            key="quick-assist", move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：并肩作战", source_name=_QUICK_ASSIST_NAME,
            group=SkillGroup.ASSIST, tags=_ASSIST, parameter_name="伤害倍率",
            source_skill_id="1111018", element=Element.PHYSICAL,
        ),
        _move(
            key="burst-quick-assist-drill", move_id=BURST_QUICK_ASSIST_DRILL_MOVE_ID,
            label="快速支援：援护钻击（爆发状态）", source_name=_BURST_QUICK_ASSIST_NAME,
            group=SkillGroup.ASSIST, tags=_ASSIST, parameter_name="伤害倍率",
            source_skill_id="1111019", element=Element.ELECTRIC,
            conditions=(BURST_STATE_ACTIVE,),
        ),
        _move(
            key="assist-strike-drill-pile", move_id=ASSIST_STRIKE_MIXED_MOVE_ID,
            label="支援突击：极限突进（电钻并以打桩收尾）", source_name=_ASSIST_STRIKE_NAME,
            group=SkillGroup.ASSIST, tags=_ASSIST, parameter_name="伤害倍率",
            source_skill_id="1111023", element=Element.ELECTRIC,
        ),
    ),
    data_quality_notes=(
        "The source's mixed Support Strike has one total multiplier for an Electric Drill hit followed by a Pile Driver finisher; no per-component ratios are provided, so the Core's two category bonuses are not guessed for this aggregate entry.",
        "Cinema 1 Energy recovery and Cinema 2 shield/incoming-damage behavior are retained in source text only; the result contract does not simulate resources, shields, or durations.",
        "The Additional Ability's extra Shock hit has a known 45% of one 125% Shock tick (0.5625× the selected Electric anomaly record). Source-record attribution and its settlement ownership are kept as a local unresolved child until confirmed; burst/readiness/shocked-target state are explicit static inputs, not replayed history or cooldown.",
    ),
)


__all__ = [
    "ANTON_ID",
    "ANTON_ELECTRIC_ANOMALY_RECORD_ID",
    "ANTON_ELECTRIC_ANOMALY_MOVE_ID",
    "ANTON_ELECTRIC_DISORDER_MOVE_ID",
    "ANTON_REVIEWED_MAPPING",
    "BURST_STATE_ACTIVE",
    "CINEMA4_TEAM_CRIT_ACTIVE",
    "EXTRA_SHOCK_READY",
    "ENEMY_SHOCKED_ACTIVE",
    "ELECTRIC_DISORDER_REMAINING_SECONDS",
    "BASIC_NORMAL_PILE_MOVE_ID",
    "BASIC_BURST_1_MOVE_ID",
    "BASIC_BURST_2_MOVE_ID",
    "BASIC_BURST_3_MOVE_ID",
    "BURST_DODGE_COUNTER_MOVE_ID",
    "ASSIST_STRIKE_MIXED_MOVE_ID",
]
