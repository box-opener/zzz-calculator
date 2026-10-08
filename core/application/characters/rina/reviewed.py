"""Reviewed Nanoka 3.2 move identities for Rina (character:1211)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


RINA_ID = CharacterId("character:1211")
RINA_ELECTRIC_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1211:electric-shock")
RINA_CORE_BUFF_ACTIVE = ScenarioConditionId("condition:rina:core-pen-buff-active")
RINA_DOLLS_NEARBY_BONUS_ACTIVE = ScenarioConditionId("condition:rina:dolls-nearby-bonus-active")
RINA_FEAR_STACKS_FULL = ScenarioConditionId("condition:rina:fear-stacks-full")
RINA_C2_DAMAGE_BONUS_ACTIVE = ScenarioConditionId("condition:rina:cinema2-damage-bonus-active")
RINA_C4_DOLLS_AWAY = ScenarioConditionId("condition:rina:cinema4-dolls-away")
RINA_C6_ELECTRIC_DAMAGE_BONUS_ACTIVE = ScenarioConditionId("condition:rina:cinema6-electric-damage-bonus-active")
RINA_TARGET_SHOCKED = ScenarioConditionId("condition:rina:target-shocked")

RINA_BASIC_MOVE_ID = MoveId("move:rina:basic-beat-the-fools")
RINA_HOLD_BASIC_MOVE_ID = MoveId("move:rina:basic-send-the-fool-away")
RINA_MORNING_SWEEP_MOVE_ID = MoveId("move:rina:basic-morning-sweep")
RINA_MIDNIGHT_SWEEP_MOVE_ID = MoveId("move:rina:basic-midnight-sweep")
RINA_DASH_MOVE_ID = MoveId("move:rina:dash-sudden-fright")
RINA_COUNTER_MOVE_ID = MoveId("move:rina:dodge-counter-bangboo-return")
RINA_SPECIAL_MOVE_ID = MoveId("move:rina:special-flatten-the-fool")
RINA_EX_MOVE_ID = MoveId("move:rina:ex-fool-disappearing-magic")
RINA_CHAIN_MOVE_ID = MoveId("move:rina:chain-servants-code")
RINA_ULTIMATE_MOVE_ID = MoveId("move:rina:ultimate-queens-attendants")
RINA_QUICK_ASSIST_MOVE_ID = MoveId("move:rina:quick-assist-allemande")
RINA_ASSIST_STRIKE_MOVE_ID = MoveId("move:rina:assist-strike-gavotte")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULT = frozenset({DamageTag.ULTIMATE})
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
    curve: str,
    element: Element,
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
                source_skill_id=curve,
            ),
        ),
        multiplier_relation=MultiplierRelation.COMPLETE,
        element=element,
        condition_ids=condition_ids,
    )


RINA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        _move("basic-hold-electric", move_id=RINA_HOLD_BASIC_MOVE_ID, label="普通攻击：赶走傻瓜", source="普通攻击：赶走傻瓜", group=SkillGroup.BASIC_ATTACK, tags=_BASIC, parameter="伤害倍率", curve="1211007", element=Element.ELECTRIC),
        _move("dash-physical", move_id=RINA_DASH_MOVE_ID, label="冲刺攻击：突然惊吓", source="冲刺攻击：突然惊吓", group=SkillGroup.DODGE, tags=_DASH, parameter="伤害倍率", curve="1211011", element=Element.PHYSICAL),
        _move("dodge-counter-electric", move_id=RINA_COUNTER_MOVE_ID, label="闪避反击：邦布回魂", source="闪避反击：邦布回魂", group=SkillGroup.DODGE, tags=_COUNTER, parameter="伤害倍率", curve="1211013", element=Element.ELECTRIC),
        _move("special-electric", move_id=RINA_SPECIAL_MOVE_ID, label="特殊技：砸扁笨蛋", source="特殊技：砸扁笨蛋", group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL, parameter="伤害倍率", curve="1211008", element=Element.ELECTRIC),
        _move("ex-electric", move_id=RINA_EX_MOVE_ID, label="强化特殊技：笨蛋消失魔法", source="强化特殊技：笨蛋消失魔法", group=SkillGroup.SPECIAL_ATTACK, tags=_EX, parameter="伤害倍率", curve="1211009", element=Element.ELECTRIC),
        _move("chain-electric", move_id=RINA_CHAIN_MOVE_ID, label="连携技：侍者守则", source="连携技：侍者守则", group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN, parameter="伤害倍率", curve="1211015", element=Element.ELECTRIC),
        _move("ultimate-electric", move_id=RINA_ULTIMATE_MOVE_ID, label="终结技：女王的侍从们", source="终结技：女王的侍从们", group=SkillGroup.ULTIMATE, tags=_ULT, parameter="伤害倍率", curve="1211017", element=Element.ELECTRIC),
        _move("quick-assist-electric", move_id=RINA_QUICK_ASSIST_MOVE_ID, label="快速支援：二拍的阿勒芒德", source="快速支援：二拍的阿勒芒德", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1211019", element=Element.ELECTRIC),
        _move("assist-strike-electric", move_id=RINA_ASSIST_STRIKE_MOVE_ID, label="支援突击：四拍的加沃特", source="支援突击：四拍的加沃特", group=SkillGroup.ASSIST, tags=_ASSIST, parameter="伤害倍率", curve="1211021", element=Element.ELECTRIC),
        _move("potential1-midnight-sweep", move_id=RINA_MIDNIGHT_SWEEP_MOVE_ID, label="潜能1：普通攻击·午夜清扫（当前6层惊吓）", source="普通攻击：午夜清扫", group=SkillGroup.BASIC_ATTACK, tags=_BASIC, parameter="伤害倍率", curve="1211027", element=Element.ELECTRIC, condition_ids=(RINA_FEAR_STACKS_FULL,)),
    ),
    data_quality_notes=(
        "The four Basic-stage ratios are preserved separately but their Physical/Electric mapping remains unresolved; the source only says the sequence deals both elements.",
        "Morning Sweep is exposed as per-source-hit coefficients, but each coefficient's Physical/Electric split is unresolved; no synthetic packet is emitted.",
        "Time-based doll returns, attack intervals, energy, and buildup are represented only by current-state controls where applicable.",
    ),
)


def reviewed_mapping(*, potential_level: int = 0) -> NanokaReviewedMapping:
    if not 0 <= potential_level <= 6:
        raise ValueError("Rina potential level must be between 0 and 6")
    return NanokaReviewedMapping(
        moves=tuple(
            item
            for item in RINA_REVIEWED_MAPPING.moves
            if not item.entry_key.startswith("potential1-") or potential_level >= 1
        ),
        data_quality_notes=RINA_REVIEWED_MAPPING.data_quality_notes,
    )


__all__ = [name for name in globals() if name.isupper()] + ["RINA_REVIEWED_MAPPING", "reviewed_mapping"]
