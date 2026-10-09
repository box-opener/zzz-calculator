"""Reviewed Nanoka 3.2 move identities for Piper (character:1281)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import RuleItemId, ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


PIPER_ID = CharacterId("character:1281")
PIPER_POWER_STACKS_RULE_ID = RuleItemId("rule:character:1281:core:current-power-stacks")
PIPER_C2_ANOMALY_RECORD_BONUS_ACTIVE = ScenarioConditionId(
    "condition:piper:cinema2:physical-anomaly-record-bonus-active"
)

PIPER_BASIC_MOVE_ID = MoveId("move:piper:basic-prepare-to-depart")
PIPER_DASH_MOVE_ID = MoveId("move:piper:dash-full-throttle")
PIPER_COUNTER_MOVE_ID = MoveId("move:piper:dodge-counter-power-drift")
PIPER_SPECIAL_SPIN_MOVE_ID = MoveId("move:piper:special-tire-spin")
PIPER_SPECIAL_SLAM_MOVE_ID = MoveId("move:piper:special-very-heavy")
PIPER_EX_SPIN_MOVE_ID = MoveId("move:piper:ex-engine-spin")
PIPER_EX_SLAM_MOVE_ID = MoveId("move:piper:ex-very-heavy")
PIPER_CHAIN_MOVE_ID = MoveId("move:piper:chain-seatbelt")
PIPER_ULTIMATE_MOVE_ID = MoveId("move:piper:ultimate-sit-tight")
PIPER_QUICK_ASSIST_MOVE_ID = MoveId("move:piper:quick-assist-brake-tap")
PIPER_ASSIST_STRIKE_MOVE_ID = MoveId("move:piper:assist-strike-cornering")
PIPER_PHYSICAL_ANOMALY_RECORD_ID = "anomaly:character:1281:physical-assault"
PIPER_PHYSICAL_ANOMALY_MOVE_ID = MoveId("move:piper:physical-assault")
PIPER_PHYSICAL_DISORDER_MOVE_ID = MoveId("move:piper:physical-disorder")

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
    curve: str | None = None,
    source_components: tuple[tuple[str, float], ...] = (),
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
                source_skill_components=source_components,
            ),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


PIPER_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-stage-{stage}",
                move_id=PIPER_BASIC_MOVE_ID,
                label=f"普通攻击：准备发车（{('一', '二', '三', '四')[stage - 1]}段）",
                source_name="普通攻击：准备发车",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一段', '二段', '三段', '四段')[stage - 1]}伤害倍率",
                curve=f"128100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "dash-attack",
            move_id=PIPER_DASH_MOVE_ID,
            label="冲刺攻击：一脚油门",
            source_name="冲刺攻击：一脚油门",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1281011",
        ),
        _move(
            "dodge-counter",
            move_id=PIPER_COUNTER_MOVE_ID,
            label="闪避反击：动力漂移",
            source_name="闪避反击：动力漂移",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            curve="1281012",
        ),
        _move(
            "special-tire-spin",
            move_id=PIPER_SPECIAL_SPIN_MOVE_ID,
            label="特殊技：轮胎转（来源倍率）",
            source_name="特殊技：轮胎转",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            curve="1281005",
        ),
        *tuple(
            _move(
                f"special-very-heavy-charge-{charge}",
                move_id=PIPER_SPECIAL_SLAM_MOVE_ID,
                label=f"特殊技：有亿点重（{('一', '二', '三')[charge - 1]}级蓄力下砸）",
                source_name="特殊技：有亿点重",
                group=SkillGroup.SPECIAL_ATTACK,
                tags=_SPECIAL,
                parameter=f"{('一级', '二级', '三级')[charge - 1]}蓄力伤害倍率",
                curve=f"128100{5 + charge}",
            )
            for charge in range(1, 4)
        ),
        _move(
            "ex-engine-spin-one-circle",
            move_id=PIPER_EX_SPIN_MOVE_ID,
            label="强化特殊技：引擎转（单圈）",
            source_name="强化特殊技：引擎转",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="每圈伤害倍率",
            source_components=(("1281010", 0.5),),
        ),
        _move(
            "ex-very-heavy",
            move_id=PIPER_EX_SLAM_MOVE_ID,
            label="强化特殊技：非常重（下砸）",
            source_name="强化特殊技：非常重",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            curve="1281009",
        ),
        _move(
            "chain-seatbelt",
            move_id=PIPER_CHAIN_MOVE_ID,
            label="连携技：系好安全带",
            source_name="连携技：系好安全带",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            curve="1281013",
        ),
        _move(
            "ultimate-sit-tight",
            move_id=PIPER_ULTIMATE_MOVE_ID,
            label="终结技：坐~稳~啦~（旋转+下砸总倍率）",
            source_name="终结技：坐~稳~啦~",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            curve="1281014",
        ),
        _move(
            "quick-assist-brake-tap",
            move_id=PIPER_QUICK_ASSIST_MOVE_ID,
            label="快速支援：点刹",
            source_name="快速支援：点刹",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1281015",
        ),
        _move(
            "assist-strike-cornering",
            move_id=PIPER_ASSIST_STRIKE_MOVE_ID,
            label="支援突击：弯道超车",
            source_name="支援突击：弯道超车",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1281019",
        ),
    )
)


__all__ = [
    "PIPER_ASSIST_STRIKE_MOVE_ID",
    "PIPER_BASIC_MOVE_ID",
    "PIPER_C2_ANOMALY_RECORD_BONUS_ACTIVE",
    "PIPER_CHAIN_MOVE_ID",
    "PIPER_COUNTER_MOVE_ID",
    "PIPER_DASH_MOVE_ID",
    "PIPER_EX_SLAM_MOVE_ID",
    "PIPER_EX_SPIN_MOVE_ID",
    "PIPER_ID",
    "PIPER_PHYSICAL_ANOMALY_MOVE_ID",
    "PIPER_PHYSICAL_ANOMALY_RECORD_ID",
    "PIPER_PHYSICAL_DISORDER_MOVE_ID",
    "PIPER_POWER_STACKS_RULE_ID",
    "PIPER_QUICK_ASSIST_MOVE_ID",
    "PIPER_REVIEWED_MAPPING",
    "PIPER_SPECIAL_SLAM_MOVE_ID",
    "PIPER_SPECIAL_SPIN_MOVE_ID",
    "PIPER_ULTIMATE_MOVE_ID",
]
