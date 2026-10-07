"""Reviewed live Nanoka 3.2 source mapping for Lycaon (character:1141)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...ids import RuleItemId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


LYCAON_ID = CharacterId("character:1141")

HUNT_OFF_FIELD_ACTIVE = ScenarioConditionId("condition:lycaon:hunt-off-field-active")
ICE_RESISTANCE_DEBUFF_ACTIVE = ScenarioConditionId(
    "condition:lycaon:core-ice-resistance-debuff-active"
)
OTHER_ELEMENT_VULNERABILITY_ACTIVE = ScenarioConditionId(
    "condition:lycaon:potential-other-element-vulnerability-active"
)

ICE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1141:ice-freeze")
C6_DAMAGE_STACKS_RULE_ID = RuleItemId(
    "rule:character:1141:cinema6:current-damage-bonus-stacks"
)

BASIC_MOVE_ID = MoveId("move:lycaon:basic-hunting-dance")
HUNT_SYNC_BASIC_SEQUENCE_MOVE_ID = MoveId("move:lycaon:hunt-off-field-basic-sequence")
CHARGED_BASIC_MOVE_ID = MoveId("move:lycaon:charged-basic-hunting-dance")
HUNT_COUNTER_BASIC3_MOVE_ID = MoveId("move:lycaon:hunt-counter-basic3-followup")
DASH_MOVE_ID = MoveId("move:lycaon:dash-maintain-cleanliness")
DODGE_COUNTER_MOVE_ID = MoveId("move:lycaon:dodge-counter-etiquette-lesson")
SPECIAL_MOVE_ID = MoveId("move:lycaon:special-hunting-hour")
EX_SPECIAL_MOVE_ID = MoveId("move:lycaon:ex-special-hunting-hour")
CHAIN_MOVE_ID = MoveId("move:lycaon:chain-as-you-command")
ULTIMATE_MOVE_ID = MoveId("move:lycaon:ultimate-unblemished-duty")
QUICK_ASSIST_MOVE_ID = MoveId("move:lycaon:quick-assist-wolf-pack")
ASSIST_STRIKE_MOVE_ID = MoveId("move:lycaon:assist-strike-revenge-counterattack")
ICE_DANCE_MOVE_ID = MoveId("move:lycaon:assist-strike-ice-dance")
ICE_ANOMALY_MOVE_ID = MoveId("move:lycaon:ice-freeze")
ICE_DISORDER_MOVE_ID = MoveId("move:lycaon:ice-disorder")

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


def reviewed_mapping(potential_level: int) -> NanokaReviewedMapping:
    if not 0 <= potential_level <= 6:
        raise ValueError("Lycaon potential level must be between 0 and 6")

    moves: list[NanokaMoveSpec] = [
        *tuple(
            _move(
                f"basic-physical-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：狩月舞步（{('一', '二', '三', '四', '五')[stage - 1]}段）",
                source="普通攻击：狩月舞步",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
                source_skill_id=f"114100{2 * stage - 1}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        *tuple(
            _move(
                f"basic-charge-ice-{stage}",
                move_id=CHARGED_BASIC_MOVE_ID,
                label=f"普通攻击：狩月舞步（{('一', '二', '三', '四')[stage - 1]}段蓄力）",
                source="普通攻击：狩月舞步",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三', '四')[stage - 1]}段蓄力伤害倍率",
                source_skill_id=f"114100{2 * stage}",
                element=Element.ICE,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "basic-charge-ice-stage5-tier1",
            move_id=MoveId("move:lycaon:charged-basic-stage5-tier1"),
            label="普通攻击：狩月舞步（五段一级蓄力）",
            source="普通攻击：狩月舞步",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段一级蓄力伤害倍率",
            source_skill_id="1141010",
            element=Element.ICE,
        ),
        _move(
            "basic-charge-ice-stage5-tier2",
            move_id=MoveId("move:lycaon:charged-basic-stage5-tier2"),
            label="普通攻击：狩月舞步（五段二级蓄力）",
            source="普通攻击：狩月舞步",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段二级蓄力伤害倍率",
            source_skill_id="1141011",
            element=Element.ICE,
        ),
        _move(
            "dash-maintain-cleanliness",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：保持清洁",
            source="冲刺攻击：保持清洁",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1141018",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter-etiquette-lesson",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：礼仪教导",
            source="闪避反击：礼仪教导",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            source_skill_id="1141019",
            element=Element.ICE,
        ),
        _move(
            "special-hunting-hour-normal",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：追猎时刻（点按）",
            source="特殊技：追猎时刻",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            source_skill_components=(("1141012", 1.0), ("1141013", 1.0)),
            element=Element.ICE,
        ),
        _move(
            "special-hunting-hour-charged",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：追猎时刻（蓄力）",
            source="特殊技：追猎时刻",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="蓄力伤害倍率",
            source_skill_components=(("1141012", 1.0), ("1141014", 1.0)),
            element=Element.ICE,
        ),
        _move(
            "ex-special-hunting-hour-normal",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：狂猎时刻（点按）",
            source="强化特殊技：狂猎时刻",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            source_skill_components=(("1141015", 1.0), ("1141016", 1.0)),
            element=Element.ICE,
        ),
        _move(
            "ex-special-hunting-hour-charged",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：狂猎时刻（蓄力）",
            source="强化特殊技：狂猎时刻",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="蓄力伤害倍率",
            source_skill_components=(("1141015", 1.0), ("1141017", 1.0)),
            element=Element.ICE,
        ),
        _move(
            "chain-as-you-command",
            move_id=CHAIN_MOVE_ID,
            label="连携技：遵命",
            source="连携技：遵命",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            source_skill_id="1141020",
            element=Element.ICE,
        ),
        _move(
            "ultimate-unblemished-duty",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：不辱使命",
            source="终结技：不辱使命",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            source_skill_id="1141021",
            element=Element.ICE,
        ),
        _move(
            "quick-assist-wolf-pack",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：狼群",
            source="快速支援：狼群",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1141022",
            element=Element.ICE,
        ),
        _move(
            "assist-strike-revenge-counterattack",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：复仇反扑",
            source="支援突击：复仇反扑",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1141026",
            element=Element.ICE,
        ),
    ]
    if potential_level >= 1:
        moves.append(
            _move(
                "hunt-off-field-basic-sequence",
                move_id=HUNT_SYNC_BASIC_SEQUENCE_MOVE_ID,
                label="围猎：同步普通攻击（一至三段）",
                source="普通攻击：狩月舞步",
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter="一段伤害倍率",
                source_skill_id="1141001",
                element=Element.PHYSICAL,
                condition_ids=(HUNT_OFF_FIELD_ACTIVE,),
            )
        )
        moves.append(
            _move(
                "hunt-counter-basic3-followup",
                move_id=HUNT_COUNTER_BASIC3_MOVE_ID,
                label="围猎：闪避反击后衔接普通攻击三段",
                source="闪避反击：礼仪教导",
                group=SkillGroup.DODGE,
                tags=_COUNTER,
                parameter="伤害倍率",
                source_skill_id="1141019",
                element=Element.ICE,
                condition_ids=(HUNT_OFF_FIELD_ACTIVE,),
            )
        )
        moves.append(
            _move(
                "assist-strike-ice-dance",
                move_id=ICE_DANCE_MOVE_ID,
                label="支援突击：复仇反扑·冰舞",
                source="支援突击：复仇反扑·冰舞",
                group=SkillGroup.ASSIST,
                tags=_ASSIST,
                parameter="伤害倍率",
                source_skill_id="1141027",
                element=Element.ICE,
            )
        )
    return NanokaReviewedMapping(moves=tuple(moves))


LYCAON_REVIEWED_MAPPING = reviewed_mapping(0)


__all__ = [
    "ASSIST_STRIKE_MOVE_ID",
    "BASIC_MOVE_ID",
    "C6_DAMAGE_STACKS_RULE_ID",
    "CHAIN_MOVE_ID",
    "CHARGED_BASIC_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "HUNT_OFF_FIELD_ACTIVE",
    "HUNT_COUNTER_BASIC3_MOVE_ID",
    "HUNT_SYNC_BASIC_SEQUENCE_MOVE_ID",
    "ICE_ANOMALY_MOVE_ID",
    "ICE_ANOMALY_RECORD_ID",
    "ICE_DANCE_MOVE_ID",
    "ICE_DISORDER_MOVE_ID",
    "ICE_RESISTANCE_DEBUFF_ACTIVE",
    "LYCAON_ID",
    "LYCAON_REVIEWED_MAPPING",
    "OTHER_ELEMENT_VULNERABILITY_ACTIVE",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "reviewed_mapping",
]
