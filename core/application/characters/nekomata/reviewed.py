"""Reviewed Nekomata (1021) identities and potential-0 Nanoka mappings."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup, StateId

from ...ids import RuleItemId, ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


NEKOMATA_ID = CharacterId("character:1021")

CORE_DAMAGE_BUFF_ACTIVE = ScenarioConditionId("condition:nekomata:core-damage-buff-active")
BACK_HIT_ACTIVE = ScenarioConditionId("condition:nekomata:back-hit-active")
POTENTIAL_POUNCE_ACTIVE = ScenarioConditionId(
    "condition:nekomata:potential-pounce-active"
)
ENEMY_STUNNED_STATE_ID = StateId("state:enemy:stunned")
NEKOMATA_C1_STUN_BACK_HIT_RULE_ID = RuleItemId(
    "rule:character:1021:cinema1:stunned-target-physical-resistance-ignore"
)

EXTRA_ABILITY_DAMAGE_STACKS = ScenarioParameterId(
    "parameter:nekomata:extra-ability-ex-damage-stacks"
)
CINEMA4_CRIT_RATE_STACKS = ScenarioParameterId(
    "parameter:nekomata:cinema4-crit-rate-stacks"
)
CINEMA6_CRIT_DAMAGE_STACKS = ScenarioParameterId(
    "parameter:nekomata:cinema6-crit-damage-stacks"
)
PHYSICAL_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:nekomata:physical-disorder-remaining-seconds"
)

BASIC_CAT_CLAW_MOVE_ID = MoveId("move:nekomata:basic-cat-claw")
BASIC_RED_BLADE_MOVE_ID = MoveId("move:nekomata:basic-red-blade")
DASH_ATTACK_MOVE_ID = MoveId("move:nekomata:dash-you-looking-at-what")
DODGE_COUNTER_MOVE_ID = MoveId("move:nekomata:dodge-counter-phantom-double-stab")
SPECIAL_ATTACK_MOVE_ID = MoveId("move:nekomata:special-ambush")
EX_SPECIAL_MOVE_ID = MoveId("move:nekomata:ex-special-super-ferocious-ambush")
CHAIN_ATTACK_MOVE_ID = MoveId("move:nekomata:chain-blade-claw-swipe")
ULTIMATE_MOVE_ID = MoveId("move:nekomata:ultimate-blade-claw-onslaught")
QUICK_ASSIST_MOVE_ID = MoveId("move:nekomata:quick-assist-borrowed-cat-claw")
SUPPORT_FOLLOWUP_MOVE_ID = MoveId("move:nekomata:support-followup-swift-shadow")
POTENTIAL_DODGE_COUNTER_MOVE_ID = MoveId(
    "move:nekomata:potential-dodge-counter-fluffy-claw"
)
PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:nekomata:physical-assault")
PHYSICAL_ANOMALY_MOVE_ID = MoveId("move:nekomata:physical-assault")
PHYSICAL_DISORDER_MOVE_ID = MoveId("move:nekomata:physical-disorder")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


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
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    *,
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
        parameters=(_p(f"{key}-damage", parameter_name, source_skill_id),),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


NEKOMATA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-cat-claw-{stage}",
                BASIC_CAT_CLAW_MOVE_ID,
                f"普通攻击：猫猫爪刺（{stage}段）",
                "普通攻击：猫猫爪刺",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
                f"102100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-red-blade",
            BASIC_RED_BLADE_MOVE_ID,
            "普通攻击：赤色之刃",
            "普通攻击：赤色之刃",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "伤害倍率",
            "1021006",
        ),
        _move(
            "dash-attack",
            DASH_ATTACK_MOVE_ID,
            "冲刺攻击：你在看哪边？",
            "冲刺攻击：你在看哪边？",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1021009",
        ),
        _move(
            "dodge-counter",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：虚影双刺",
            "闪避反击：虚影双刺",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1021010",
        ),
        _move(
            "special-ambush",
            SPECIAL_ATTACK_MOVE_ID,
            "特殊技：奇袭",
            "特殊技：奇袭",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1021007",
        ),
        _move(
            "ex-special-super-ferocious-ambush",
            EX_SPECIAL_MOVE_ID,
            "强化特殊技：超~凶奇袭！",
            "强化特殊技：超~凶奇袭！",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1021008",
        ),
        _move(
            "chain-blade-claw-swipe",
            CHAIN_ATTACK_MOVE_ID,
            "连携技：刃爪挥击",
            "连携技：刃爪挥击",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1021011",
        ),
        _move(
            "ultimate-blade-claw-onslaught",
            ULTIMATE_MOVE_ID,
            "终结技：刃爪强袭",
            "终结技：刃爪强袭",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1021012",
        ),
        _move(
            "quick-assist-borrowed-cat-claw",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：借用猫爪",
            "快速支援：借用猫爪",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1021013",
        ),
        _move(
            "support-followup-swift-shadow",
            SUPPORT_FOLLOWUP_MOVE_ID,
            "支援突击：迅影",
            "支援突击：迅影",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            "伤害倍率",
            "1021017",
        ),
    ),
    data_quality_notes=(
        "The base mapping selects potential 0; the compiler selects potential-1+ source records only when the explicit potential slider is above zero. Potential 1 adds the named Fluffy Claw Dodge Counter and the known stunned-target repeat rule.",
        "The base source's 33.33% random repeat on Cat Claw 5 and Red Blade is not modeled. The deterministic potential-1+ repeats are separate and use the confirmed main multiplier for the two extra attacks when the target is stunned.",
        "Tail Lost Technique has no damage curve, so it remains a source-described non-damaging unlock and is not represented as a Direct entry.",
        "Nekomata's two Support Parry Daze curves are preserved in raw but are not direct damage entries; this calculation request has no Daze result.",
    ),
)

NEKOMATA_POTENTIAL_ONE_MOVES = (
    _move(
        "potential-dodge-counter-fluffy-claw",
        POTENTIAL_DODGE_COUNTER_MOVE_ID,
        "潜能解锁：闪避反击：绒爪穿刺",
        "闪避反击：绒爪穿刺",
        SkillGroup.DODGE,
        _COUNTER,
        "伤害倍率",
        "1021019",
    ),
)


__all__ = [
    "BACK_HIT_ACTIVE",
    "BASIC_CAT_CLAW_MOVE_ID",
    "BASIC_RED_BLADE_MOVE_ID",
    "CHAIN_ATTACK_MOVE_ID",
    "CINEMA4_CRIT_RATE_STACKS",
    "CINEMA6_CRIT_DAMAGE_STACKS",
    "CORE_DAMAGE_BUFF_ACTIVE",
    "DASH_ATTACK_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ENEMY_STUNNED_STATE_ID",
    "EX_SPECIAL_MOVE_ID",
    "EXTRA_ABILITY_DAMAGE_STACKS",
    "NEKOMATA_ID",
    "NEKOMATA_C1_STUN_BACK_HIT_RULE_ID",
    "NEKOMATA_POTENTIAL_ONE_MOVES",
    "NEKOMATA_REVIEWED_MAPPING",
    "PHYSICAL_ANOMALY_MOVE_ID",
    "PHYSICAL_ANOMALY_RECORD_ID",
    "PHYSICAL_DISORDER_MOVE_ID",
    "PHYSICAL_DISORDER_REMAINING_SECONDS",
    "POTENTIAL_DODGE_COUNTER_MOVE_ID",
    "POTENTIAL_POUNCE_ACTIVE",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_ATTACK_MOVE_ID",
    "SUPPORT_FOLLOWUP_MOVE_ID",
    "ULTIMATE_MOVE_ID",
]
