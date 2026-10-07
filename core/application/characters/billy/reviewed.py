"""Reviewed live Nanoka 3.2 move identities for Billy (character:1081)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


BILLY_ID = CharacterId("character:1081")
BILLY_PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId(
    "anomaly:character:1081:physical-assault"
)

CROUCH_SHOOTING_DAMAGE_ACTIVE = ScenarioConditionId(
    "condition:billy:crouch-shooting-damage-active"
)
ULTIMATE_AFTER_CHAIN_ACTIVE = ScenarioConditionId(
    "condition:billy:ultimate-after-chain-buff-active"
)
CINEMA4_EX_CRIT_RATE_BONUS = ScenarioParameterId(
    "parameter:billy:cinema4-ex-current-crit-rate-bonus-percent"
)
PHYSICAL_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:billy:physical-disorder-remaining-seconds"
)

BASIC_FIRE_MOVE_ID = MoveId("move:billy:basic-fire-all")
DASH_SCATTER_MOVE_ID = MoveId("move:billy:dash-star-emblem-verdict-scatter")
DASH_FOCUSED_MOVE_ID = MoveId("move:billy:dash-star-emblem-verdict-focused")
DODGE_COUNTER_MOVE_ID = MoveId("move:billy:dodge-counter-fair-duel")
SPECIAL_MOVE_ID = MoveId("move:billy:special-stay-still")
EX_SPECIAL_MOVE_ID = MoveId("move:billy:ex-special-cleanup-time")
CHAIN_ATTACK_MOVE_ID = MoveId("move:billy:chain-star-emblem-glory-phantom")
ULTIMATE_MOVE_ID = MoveId("move:billy:ultimate-star-emblem-shines-here")
QUICK_ASSIST_MOVE_ID = MoveId("move:billy:quick-assist-star-emblem-comrade-power")
ASSIST_STRIKE_MOVE_ID = MoveId("move:billy:assist-strike-vital-shot")
PHYSICAL_ANOMALY_MOVE_ID = MoveId("move:billy:physical-assault")
PHYSICAL_DISORDER_MOVE_ID = MoveId("move:billy:physical-disorder")

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
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


_SPECIAL_STAGES = ("一", "二", "三")

BILLY_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move(
            key="basic-standing-fire",
            move_id=BASIC_FIRE_MOVE_ID,
            label="普通攻击：火力全开（站姿开火）",
            source_name="普通攻击：火力全开",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="站姿开火伤害倍率",
            source_skill_id="1081002",
        ),
        _move(
            key="basic-standing-bullet",
            move_id=BASIC_FIRE_MOVE_ID,
            label="普通攻击：火力全开（站姿单发子弹）",
            source_name="普通攻击：火力全开",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="站姿子弹伤害倍率",
            source_skill_id="1081003",
        ),
        _move(
            key="basic-crouch-fire",
            move_id=BASIC_FIRE_MOVE_ID,
            label="普通攻击：火力全开（蹲姿开火）",
            source_name="普通攻击：火力全开",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="蹲姿开火伤害倍率",
            source_skill_id="1081004",
        ),
        _move(
            key="basic-crouch-bullet",
            move_id=BASIC_FIRE_MOVE_ID,
            label="普通攻击：火力全开（蹲姿单发子弹）",
            source_name="普通攻击：火力全开",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="蹲姿子弹伤害倍率",
            source_skill_id="1081007",
        ),
        _move(
            key="basic-roll-shot",
            move_id=BASIC_FIRE_MOVE_ID,
            label="普通攻击：火力全开（翻滚射击）",
            source_name="普通攻击：火力全开",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="翻滚射击伤害倍率",
            source_skill_id="1081004",
        ),
        _move(
            key="basic-finisher-shot",
            move_id=BASIC_FIRE_MOVE_ID,
            label="普通攻击：火力全开（终结射击）",
            source_name="普通攻击：火力全开",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter_name="终结射击伤害倍率",
            source_skill_id="1081008",
        ),
        _move(
            key="dash-scatter",
            move_id=DASH_SCATTER_MOVE_ID,
            label="冲刺攻击：星-徽-制-裁（散射）",
            source_name="冲刺攻击：星-徽-制-裁",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="周身射击伤害倍率",
            source_skill_id="1081016",
        ),
        _move(
            key="dash-focused",
            move_id=DASH_FOCUSED_MOVE_ID,
            label="冲刺攻击：星-徽-制-裁（直线）",
            source_name="冲刺攻击：星-徽-制-裁",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="直线射击伤害倍率",
            source_skill_id="1081014",
        ),
        _move(
            key="dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：公平决斗",
            source_name="闪避反击：公平决斗",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1081017",
        ),
        *tuple(
            _move(
                key=f"special-stay-still-{stage}",
                move_id=SPECIAL_MOVE_ID,
                label=f"特殊技：乖乖站好（{_SPECIAL_STAGES[stage - 1]}段）",
                source_name="特殊技：乖乖站好",
                group=SkillGroup.SPECIAL_ATTACK,
                tags=_SPECIAL,
                parameter_name=f"{_SPECIAL_STAGES[stage - 1]}段伤害倍率",
                source_skill_id=f"108101{stage - 1}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            key="ex-cleanup-time",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：清场时间",
            source_name="强化特殊技：清场时间",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="伤害倍率",
            source_skill_id="1081013",
        ),
        _move(
            key="chain-star-emblem-glory",
            move_id=CHAIN_ATTACK_MOVE_ID,
            label="连携技：星徽荣耀幻影",
            source_name="连携技：星徽荣耀幻影",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1081018",
        ),
        _move(
            key="ultimate-star-emblem",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：星徽在此闪耀",
            source_name="终结技：星徽在此闪耀",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1081019",
        ),
        _move(
            key="quick-assist-comrade-power",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：星徽-同伴之力",
            source_name="快速支援：星徽-同伴之力",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1081020",
        ),
        _move(
            key="assist-strike-vital-shot",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：要害射击",
            source_name="支援突击：要害射击",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1081021",
        ),
    ),
    data_quality_notes=(
        "Standing/crouching bullet entries are one source-defined bullet each; no unspecified bullet count, shot cadence, or crouch duration is multiplied.",
        "The two Dash attacks are distinct source action variants (spread and focused line); their source ratios are not summed or multiplied by target count/range.",
        "Crouch-shooting damage bonus is a current state that ends on movement/interrupt/return to idle. Charge cadence, 10-hit history, support resources, Daze, and incoming damage are not replayed.",
        "Cinema 4 exposes a current EX-event Crit Rate input from 0% to the source maximum of 32%, defaulting to the close-range maximum; distance is not inferred.",
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_FIRE_MOVE_ID",
    "BILLY_ID",
    "BILLY_PHYSICAL_ANOMALY_RECORD_ID",
    "BILLY_REVIEWED_MAPPING",
    "CHAIN_ATTACK_MOVE_ID",
    "CINEMA4_EX_CRIT_RATE_BONUS",
    "CROUCH_SHOOTING_DAMAGE_ACTIVE",
    "DASH_FOCUSED_MOVE_ID",
    "DASH_SCATTER_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "PHYSICAL_ANOMALY_MOVE_ID",
    "PHYSICAL_DISORDER_MOVE_ID",
    "PHYSICAL_DISORDER_REMAINING_SECONDS",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_AFTER_CHAIN_ACTIVE",
    "ULTIMATE_MOVE_ID",
]
