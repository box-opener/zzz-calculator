"""Reviewed Nanoka 3.2 source identities for Corin (character:1061)."""

from __future__ import annotations

from core.types import (
    AnomalyRecordId,
    CharacterId,
    DamageTag,
    Element,
    MoveId,
    SkillGroup,
    StateId,
)

from ...ids import ScenarioConditionId, ScenarioParameterId

from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from ...moves import MultiplierRelation


CORIN_ID = CharacterId("character:1061")
CORIN_PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId(
    "anomaly:character:1061:physical-assault"
)

CHAINSAW_CONTINUOUS_ACTIVE = ScenarioConditionId(
    "condition:corin:chainsaw-continuous-active"
)
C1_TARGET_DAMAGE_ACTIVE = ScenarioConditionId(
    "condition:corin:cinema1-target-damage-active"
)
ENEMY_STUNNED_STATE_ID = StateId("state:enemy:stunned")
CINEMA6_CURRENT_CHARGES = ScenarioParameterId(
    "parameter:corin:cinema6-current-chainsaw-charges"
)
PHYSICAL_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:corin:physical-disorder-remaining-seconds"
)

BASIC_SWEEP_MOVE_ID = MoveId("move:corin:basic-cleaning-start")
DASH_ATTACK_MOVE_ID = MoveId("move:corin:dash-cut")
DODGE_COUNTER_MOVE_ID = MoveId("move:corin:dodge-counter")
SPECIAL_SWEEP_MOVE_ID = MoveId("move:corin:special-powerful-cleaning")
EX_SPECIAL_MOVE_ID = MoveId("move:corin:ex-special-mind-your-skirt")
CHAIN_ATTACK_MOVE_ID = MoveId("move:corin:chain-apologies")
ULTIMATE_MOVE_ID = MoveId("move:corin:ultimate-very-sorry")
QUICK_ASSIST_MOVE_ID = MoveId("move:corin:quick-assist-emergency-measures")
ASSIST_STRIKE_MOVE_ID = MoveId("move:corin:assist-strike-quick-cleaning")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _stage(stage: int, source_skill_id: str) -> NanokaMoveSpec:
    stage_name = ("一", "二", "三", "四", "五")[stage - 1]
    return NanokaMoveSpec(
        entry_key=f"basic-cleaning-{stage}",
        move_id=BASIC_SWEEP_MOVE_ID,
        display_name=f"普通攻击：扫除开始（{stage_name}段）",
        source_name="普通攻击：扫除开始",
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"basic-cleaning-{stage}-damage",
                parameter_name=f"{stage_name}段伤害倍率",
                source_skill_id=source_skill_id,
            ),
        ),
        multiplier_relation=MultiplierRelation.SEQUENTIAL_STAGE,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


def _move(
    *,
    key: str,
    move_id: MoveId,
    display_name: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str | None = None,
    source_skill_components: tuple[tuple[str, float], ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=display_name,
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=(
            NanokaDamageParameterSpec(
                variant_key=f"{key}-damage",
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
                source_skill_components=source_skill_components,
            ),
        ),
        multiplier_relation=MultiplierRelation.COMPLETE,
        element=Element.PHYSICAL,
    )


CORIN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _stage(1, "1061001"),
        _stage(2, "1061002"),
        _stage(3, "1061003"),
        _stage(4, "1061004"),
        _stage(5, "1061006"),
        _move(
            key="dash-cut",
            move_id=DASH_ATTACK_MOVE_ID,
            display_name="冲刺攻击：[断]",
            source_name="冲刺攻击：[断]",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="最大伤害倍率",
            source_skill_id="1061014",
        ),
        _move(
            key="dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            display_name="闪避反击：[舍]",
            source_name="闪避反击：[舍]",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_components=(("1061015", 1.0), ("1061016", 1.0)),
        ),
        _move(
            key="special-sweeping-slash",
            move_id=SPECIAL_SWEEP_MOVE_ID,
            display_name="特殊技：强力清扫（回旋斩击）",
            source_name="特殊技：强力清扫",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="回旋斩击伤害倍率",
            source_skill_id="1061008",
        ),
        _move(
            key="special-saw-explosion",
            move_id=SPECIAL_SWEEP_MOVE_ID,
            display_name="特殊技：强力清扫（电锯引爆）",
            source_name="特殊技：强力清扫",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="爆炸伤害倍率",
            source_skill_id="1061010",
        ),
        _move(
            key="special-continuous-saw-maximum",
            move_id=SPECIAL_SWEEP_MOVE_ID,
            display_name="特殊技：强力清扫（持续斩击最大伤害）",
            source_name="特殊技：强力清扫",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="持续斩击最大伤害倍率",
            source_skill_id="1061009",
        ),
        _move(
            key="ex-special-spinning-slash",
            move_id=EX_SPECIAL_MOVE_ID,
            display_name="强化特殊技：小心裙角（回旋斩击）",
            source_name="强化特殊技：小心裙角",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="回旋斩击伤害倍率",
            source_skill_id="1061011",
        ),
        _move(
            key="ex-special-saw-explosion",
            move_id=EX_SPECIAL_MOVE_ID,
            display_name="强化特殊技：小心裙角（电锯引爆）",
            source_name="强化特殊技：小心裙角",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="爆炸伤害倍率",
            source_skill_id="1061013",
        ),
        _move(
            key="ex-special-continuous-saw-maximum",
            move_id=EX_SPECIAL_MOVE_ID,
            display_name="强化特殊技：小心裙角（持续斩击最大伤害）",
            source_name="强化特殊技：小心裙角",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="持续斩击最大伤害倍率",
            source_skill_id="1061012",
        ),
        _move(
            key="chain-apologies",
            move_id=CHAIN_ATTACK_MOVE_ID,
            display_name="连携技：抱歉…",
            source_name="连携技：抱歉…",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1061017",
        ),
        _move(
            key="ultimate-very-sorry",
            move_id=ULTIMATE_MOVE_ID,
            display_name="终结技：非、非常抱歉！",
            source_name="终结技：非、非常抱歉！",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1061018",
        ),
        _move(
            key="quick-assist-emergency-measures",
            move_id=QUICK_ASSIST_MOVE_ID,
            display_name="快速支援：应急措施",
            source_name="快速支援：应急措施",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_components=(("1061019", 1.0), ("1061020", 1.0)),
        ),
        _move(
            key="assist-strike-quick-cleaning",
            move_id=ASSIST_STRIKE_MOVE_ID,
            display_name="支援突击：快速清扫",
            source_name="支援突击：快速清扫",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1061024",
        ),
    ),
    data_quality_notes=(
        "Dodge Counter and Quick Assist explicitly sum their two source multipliers. Continuous-saw maximum values are selectable as complete maximum segments once; no unlisted hit count or timeline is replayed.",
        "The source preserves Daze, Energy, and anomaly-buildup data. The calculation result does not emit those resources or Daze, and it does not replay resource or timing history.",
    ),
)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_SWEEP_MOVE_ID",
    "CHAINSAW_CONTINUOUS_ACTIVE",
    "CHAIN_ATTACK_MOVE_ID",
    "C1_TARGET_DAMAGE_ACTIVE",
    "CINEMA6_CURRENT_CHARGES",
    "CORIN_ID",
    "CORIN_PHYSICAL_ANOMALY_RECORD_ID",
    "CORIN_REVIEWED_MAPPING",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ENEMY_STUNNED_STATE_ID",
    "EX_SPECIAL_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "PHYSICAL_DISORDER_REMAINING_SECONDS",
    "SPECIAL_SWEEP_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
