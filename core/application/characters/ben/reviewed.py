"""Reviewed Nanoka 3.2 move identities for Ben (character:1121)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..koleda.reviewed import BEN_ID
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


BEN_GUARD_COUNTER_SUCCESSFUL = ScenarioConditionId(
    "condition:ben:special-guard-counter-current"
)
BEN_EX_FOLLOWUP_ACTIVE = ScenarioConditionId("condition:ben:ex-followup-current")
BEN_SHIELD_ACTIVE = ScenarioConditionId("condition:ben:core-shield-current")
BEN_C4_COUNTER_BONUS_ACTIVE = ScenarioConditionId(
    "condition:ben:cinema4-counter-bonus-current"
)
BEN_CORE_ATTACK_PANEL_UNRESOLVED = "unsupported:character:1121:core:initial-defense-to-attack-layer"
BEN_FIRE_ANOMALY_RECORD_ID = "anomaly:character:1121:fire-burn"
BEN_FIRE_ANOMALY_MOVE_ID = MoveId("move:ben:fire-burn")
BEN_FIRE_DISORDER_MOVE_ID = MoveId("move:ben:fire-disorder")

BASIC_MOVE_ID = MoveId("move:ben:basic-audit")
DASH_MOVE_ID = MoveId("move:ben:dash-invoice-loophole")
DODGE_COUNTER_MOVE_ID = MoveId("move:ben:dodge-settlement")
SPECIAL_ACTIVE_MOVE_ID = MoveId("move:ben:special-debt-accounting")
SPECIAL_COUNTER_MOVE_ID = MoveId("move:ben:special-guard-counter")
EX_SPECIAL_MAIN_MOVE_ID = MoveId("move:ben:ex-special-main")
EX_SPECIAL_FOLLOWUP_MOVE_ID = MoveId("move:ben:ex-special-followup")
EX_SPECIAL_COUNTER_MOVE_ID = MoveId("move:ben:ex-special-guard-counter")
EX_SPECIAL_COUNTER_FOLLOWUP_MOVE_ID = MoveId("move:ben:ex-special-guard-followup")
CHAIN_ATTACK_MOVE_ID = MoveId("move:ben:chain-stamp-settlement")
ULTIMATE_MOVE_ID = MoveId("move:ben:ultimate-debt-clearance")
QUICK_ASSIST_MOVE_ID = MoveId("move:ben:quick-assist-joint-debt-collection")
ASSIST_STRIKE_MOVE_ID = MoveId("move:ben:assist-strike-breach-penalty")

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


_BASIC_NAME = "普通攻击：对账"
_DASH_NAME = "冲刺攻击：前来报销"
_DODGE_COUNTER_NAME = "闪避反击：清算"
_SPECIAL_NAME = "特殊技：拳债统计"
_EX_NAME = "强化特殊技：到期还拳"
_CHAIN_NAME = "连携技：盖章，结算"
_ULTIMATE_NAME = "终结技：拳债，全面清偿"
_QUICK_ASSIST_NAME = "快速支援：联合追债"
_ASSIST_STRIKE_NAME = "支援突击：违约惩罚"


BEN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                key=f"basic-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：对账（第{stage}段）",
                source_name=_BASIC_NAME,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter_name=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=f"112100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            key="dash-attack",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：前来报销",
            source_name=_DASH_NAME,
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter_name="伤害倍率",
            source_skill_id="1121012",
            element=Element.PHYSICAL,
        ),
        _move(
            key="dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：清算",
            source_name=_DODGE_COUNTER_NAME,
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter_name="伤害倍率",
            source_skill_id="1121013",
            element=Element.FIRE,
        ),
        _move(
            key="special-active",
            move_id=SPECIAL_ACTIVE_MOVE_ID,
            label="特殊技：拳债统计（主动攻击）",
            source_name=_SPECIAL_NAME,
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="主动攻击伤害倍率",
            source_skill_id="1121005",
            element=Element.PHYSICAL,
        ),
        _move(
            key="special-counter",
            move_id=SPECIAL_COUNTER_MOVE_ID,
            label="特殊技：拳债统计（格挡反击）",
            source_name=_SPECIAL_NAME,
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter_name="格挡反击伤害倍率",
            source_skill_id="1121006",
            element=Element.PHYSICAL,
            conditions=(BEN_GUARD_COUNTER_SUCCESSFUL,),
        ),
        _move(
            key="ex-special-main",
            move_id=EX_SPECIAL_MAIN_MOVE_ID,
            label="强化特殊技：到期还拳（主动攻击）",
            source_name=_EX_NAME,
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="主动攻击伤害倍率",
            source_skill_id="1121008",
            element=Element.FIRE,
        ),
        _move(
            key="ex-special-followup",
            move_id=EX_SPECIAL_FOLLOWUP_MOVE_ID,
            label="强化特殊技：到期还拳（追加强力打击）",
            source_name=_EX_NAME,
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="追加攻击伤害倍率",
            source_skill_id="1121009",
            element=Element.FIRE,
            conditions=(BEN_EX_FOLLOWUP_ACTIVE,),
        ),
        _move(
            key="ex-special-counter",
            move_id=EX_SPECIAL_COUNTER_MOVE_ID,
            label="强化特殊技：到期还拳（格挡反击）",
            source_name=_EX_NAME,
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="格挡反击伤害倍率",
            source_skill_id="1121010",
            element=Element.FIRE,
            conditions=(BEN_GUARD_COUNTER_SUCCESSFUL,),
        ),
        _move(
            key="ex-special-counter-followup",
            move_id=EX_SPECIAL_COUNTER_FOLLOWUP_MOVE_ID,
            label="强化特殊技：到期还拳（格挡追击）",
            source_name=_EX_NAME,
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter_name="格挡追击伤害倍率",
            source_skill_id="1121011",
            element=Element.FIRE,
            conditions=(BEN_GUARD_COUNTER_SUCCESSFUL,),
        ),
        _move(
            key="chain-attack",
            move_id=CHAIN_ATTACK_MOVE_ID,
            label="连携技：盖章，结算",
            source_name=_CHAIN_NAME,
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter_name="伤害倍率",
            source_skill_id="1121014",
            element=Element.FIRE,
        ),
        _move(
            key="ultimate",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：拳债，全面清偿",
            source_name=_ULTIMATE_NAME,
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter_name="伤害倍率",
            source_skill_id="1121015",
            element=Element.FIRE,
        ),
        _move(
            key="quick-assist",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：联合追债",
            source_name=_QUICK_ASSIST_NAME,
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1121016",
            element=Element.FIRE,
        ),
        _move(
            key="assist-strike",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：违约惩罚",
            source_name=_ASSIST_STRIKE_NAME,
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter_name="伤害倍率",
            source_skill_id="1121020",
            element=Element.FIRE,
        ),
    ),
    data_quality_notes=(
        "Shield capacity, incoming damage reduction, Energy, Support Points, and Daze are source effects without corresponding outputs in the current calculation result.",
        "The Cinema 2 defense-scaling extra counter damage is retained as a local unresolved child until its parent element/crit attribution is confirmed; parent Special/EX counter damage remains available.",
        "The Core's Initial Attack from Initial Defense formula is numerically known, but its out-of-combat versus combat-layer placement awaits the user's current clarification; this does not block direct entries or shield/Cinema states.",
    ),
)


__all__ = [
    "BEN_ID",
    "BEN_REVIEWED_MAPPING",
    "BEN_GUARD_COUNTER_SUCCESSFUL",
    "BEN_EX_FOLLOWUP_ACTIVE",
    "BEN_SHIELD_ACTIVE",
    "BEN_C4_COUNTER_BONUS_ACTIVE",
    "BEN_CORE_ATTACK_PANEL_UNRESOLVED",
    "BEN_FIRE_ANOMALY_RECORD_ID",
    "BEN_FIRE_ANOMALY_MOVE_ID",
    "BEN_FIRE_DISORDER_MOVE_ID",
    "BASIC_MOVE_ID",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "SPECIAL_ACTIVE_MOVE_ID",
    "SPECIAL_COUNTER_MOVE_ID",
    "EX_SPECIAL_MAIN_MOVE_ID",
    "EX_SPECIAL_FOLLOWUP_MOVE_ID",
    "EX_SPECIAL_COUNTER_MOVE_ID",
    "EX_SPECIAL_COUNTER_FOLLOWUP_MOVE_ID",
    "CHAIN_ATTACK_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "ASSIST_STRIKE_MOVE_ID",
]
