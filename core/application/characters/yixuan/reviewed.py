"""Reviewed move taxonomy for Yixuan (character:1371).

The taxonomy records source skill IDs and application-facing move identities;
damage values remain sourced from the packaged Nanoka record by the compiler.
"""

from __future__ import annotations

from core.types import (
    AnomalyRecordId,
    CharacterId,
    DamageTag,
    Element,
    MoveId,
    SkillGroup,
)

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


YIXUAN_ID = CharacterId("character:1371")

EX_MARK_CHARGE_EXTRA = ScenarioConditionId(
    "condition:yixuan:ex-mark-charge-extra-active"
)
MATRIX_MAX_DURATION = ScenarioConditionId("condition:yixuan:matrix-max-duration")
C2_INK_BREAK_READY = ScenarioConditionId("condition:yixuan:c2-ink-break-ready")
C6_EXTRA_ULTIMATE_ACTIVE = ScenarioConditionId(
    "condition:yixuan:c6-extra-ultimate-active"
)
FOCUSED_MIND_ACTIVE = ScenarioConditionId("condition:yixuan:focused-mind-active")
PERFECT_SUPPORT_SWITCH_OUT = ScenarioConditionId(
    "condition:yixuan:perfect-support-switch-out-active"
)


BASIC_XIAOYUN_MOVE_ID = MoveId("move:yixuan:basic-xiaoyun-jin")
INK_SHADOW_MOVE_ID = MoveId("move:yixuan:basic-ink-shadow-gathering")
INK_ARRAY_MOVE_ID = MoveId("move:yixuan:basic-xuanmo-array")
QINGMING_SHOCK_MOVE_ID = MoveId("move:yixuan:basic-qingming-shock")
DASH_ATTACK_MOVE_ID = MoveId("move:yixuan:dash-lingyun-po")
DODGE_COUNTER_MOVE_ID = MoveId("move:yixuan:dodge-counter-chu-xie")
BASIC_SPECIAL_MOVE_ID = MoveId("move:yixuan:special-jin-ying-jue")
EX_MARK_MOVE_ID = MoveId("move:yixuan:ex-mark-transformation")
EX_MARK_EXTRA_MOVE_ID = MoveId("move:yixuan:ex-mark-charge-talisman")
EX_XIAOYUN_BREAK_MOVE_ID = MoveId("move:yixuan:ex-xiaoyun-strike-break")
EX_QINGMING_BREAK_MOVE_ID = MoveId("move:yixuan:ex-qingming-shock-break")
EX_CLOUD_MOVE_ID = MoveId("move:yixuan:ex-condense-cloud-technique")
EX_INK_BURST_MOVE_ID = MoveId("move:yixuan:ex-ink-ember-shadow")
CHAIN_MOVE_ID = MoveId("move:yixuan:chain-ink-strike")
ULTIMATE_QINGMING_MOVE_ID = MoveId("move:yixuan:ultimate-qingming-cloud-shadow")
ULTIMATE_TALISMAN_MOVE_ID = MoveId("move:yixuan:ultimate-talisman-mastery")
EX_TALISMAN_BREAK_MOVE_ID = MoveId("move:yixuan:ex-talisman-mastery-break")
QUICK_ASSIST_MOVE_ID = MoveId("move:yixuan:quick-assist-flowing-cloud-shadow")
ASSIST_FOLLOW_UP_MOVE_ID = MoveId("move:yixuan:assist-xiaoyun-strike")
XUANMO_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:yixuan:xuanmo-current")
XUANMO_ANOMALY_MOVE_ID = MoveId("move:yixuan:xuanmo-corruption-anomaly")
XUANMO_DISORDER_MOVE_ID = MoveId("move:yixuan:xuanmo-corruption-disorder")


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_DODGE_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _p(key: str, name: str, source_skill_id: str) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=name,
        source_skill_id=source_skill_id,
    )


def _move(
    key: str,
    move_id: MoveId,
    label: str,
    source: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    conditions: tuple[ScenarioConditionId, ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source,
        skill_group=group,
        damage_tags=tags,
        parameters=(_p("damage", parameter_name, source_skill_id),),
        multiplier_relation=relation,
        element=Element.XUANMO,
        stage_index=stage,
        condition_ids=conditions,
    )


YIXUAN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-xiaoyun-jin-{stage}",
                BASIC_XIAOYUN_MOVE_ID,
                f"普通攻击：霄云劲（{stage}段）",
                "普通攻击：霄云劲",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{'一二三四五'[stage - 1]}段伤害倍率",
                f"137100{stage}" if stage < 5 else "1371006",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-ink-shadow-gathering",
            INK_SHADOW_MOVE_ID,
            "普通攻击：墨影凝云",
            "普通攻击：墨影凝云",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "墨影凝云总伤害倍率",
            "1371005",
        ),
        _move(
            "basic-xuanmo-array",
            INK_ARRAY_MOVE_ID,
            "普通攻击：玄墨极阵",
            "普通攻击：玄墨极阵",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "玄墨极阵总伤害倍率",
            "1371021",
            conditions=(MATRIX_MAX_DURATION,),
        ),
        _move(
            "basic-qingming-shock",
            QINGMING_SHOCK_MOVE_ID,
            "普通攻击：青溟震击",
            "普通攻击：青溟震击",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1371007",
        ),
        _move(
            "dodge-dash-lingyun-po",
            DASH_ATTACK_MOVE_ID,
            "冲刺攻击：凌云破",
            "冲刺攻击：凌云破",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1371010",
        ),
        _move(
            "dodge-counter-chu-xie",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：除祟一击",
            "闪避反击：除祟一击",
            SkillGroup.DODGE,
            _DODGE_COUNTER,
            "伤害倍率",
            "1371012",
        ),
        _move(
            "special-jin-ying-jue",
            BASIC_SPECIAL_MOVE_ID,
            "特殊技：烬影诀",
            "特殊技：烬影诀",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1371008",
        ),
        _move(
            "ex-mark-transformation",
            EX_MARK_MOVE_ID,
            "强化特殊技：墨痕化形",
            "强化特殊技：墨痕化形",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1371009",
        ),
        _move(
            "ex-xiaoyun-strike-break",
            EX_XIAOYUN_BREAK_MOVE_ID,
            "强化特殊技：霄云迅击-破",
            "强化特殊技：墨痕化形",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "[强化特殊技：霄云迅击-破]总伤害倍率",
            "1371023",
        ),
        _move(
            "ex-qingming-shock-break",
            EX_QINGMING_BREAK_MOVE_ID,
            "强化特殊技：青溟震击-破",
            "强化特殊技：墨痕化形",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "[强化特殊技：青溟震击-破]总伤害倍率",
            "1371025",
        ),
        _move(
            "ex-condense-cloud-technique",
            EX_CLOUD_MOVE_ID,
            "强化特殊技：凝云术",
            "强化特殊技：凝云术",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "蓄力期间总伤害倍率",
            "1371022",
        ),
        _move(
            "ex-ink-ember-shadow",
            EX_INK_BURST_MOVE_ID,
            "强化特殊技：墨烬影消",
            "强化特殊技：墨烬影消",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1371026",
        ),
        _move(
            "chain-ink-strike",
            CHAIN_MOVE_ID,
            "连携技：玄墨迅击",
            "连携技：玄墨迅击",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1371013",
        ),
        _move(
            "ultimate-qingming-cloud-shadow",
            ULTIMATE_QINGMING_MOVE_ID,
            "终结技：青溟云影",
            "终结技：青溟云影",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1371014",
        ),
        _move(
            "ultimate-talisman-mastery",
            ULTIMATE_TALISMAN_MOVE_ID,
            "终结技：符法千重",
            "终结技：符法千重",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1371020",
        ),
        _move(
            "quick-assist-flowing-cloud-shadow",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：流云影身",
            "快速支援：流云影身",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1371015",
        ),
        _move(
            "assist-xiaoyun-strike",
            ASSIST_FOLLOW_UP_MOVE_ID,
            "支援突击：霄云迅击",
            "支援突击：霄云迅击",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1371019",
        ),
    )
)


__all__ = [
    "ASSIST_FOLLOW_UP_MOVE_ID",
    "BASIC_SPECIAL_MOVE_ID",
    "BASIC_XIAOYUN_MOVE_ID",
    "C2_INK_BREAK_READY",
    "C6_EXTRA_ULTIMATE_ACTIVE",
    "CHAIN_MOVE_ID",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_CLOUD_MOVE_ID",
    "EX_INK_BURST_MOVE_ID",
    "EX_MARK_CHARGE_EXTRA",
    "EX_MARK_EXTRA_MOVE_ID",
    "EX_MARK_MOVE_ID",
    "EX_QINGMING_BREAK_MOVE_ID",
    "EX_TALISMAN_BREAK_MOVE_ID",
    "EX_XIAOYUN_BREAK_MOVE_ID",
    "FOCUSED_MIND_ACTIVE",
    "INK_ARRAY_MOVE_ID",
    "INK_SHADOW_MOVE_ID",
    "MATRIX_MAX_DURATION",
    "PERFECT_SUPPORT_SWITCH_OUT",
    "QUICK_ASSIST_MOVE_ID",
    "QINGMING_SHOCK_MOVE_ID",
    "ULTIMATE_QINGMING_MOVE_ID",
    "ULTIMATE_TALISMAN_MOVE_ID",
    "XUANMO_ANOMALY_MOVE_ID",
    "XUANMO_ANOMALY_RECORD_ID",
    "XUANMO_DISORDER_MOVE_ID",
    "YIXUAN_ID",
    "YIXUAN_REVIEWED_MAPPING",
]
