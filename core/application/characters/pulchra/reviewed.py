"""Reviewed Nanoka 3.2 identities and exact curve IDs for Pulchra."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import RuleItemId, ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping
from .config import PULCHRA_ID


PULCHRA_HUNTER_STEP_ACTIVE = ScenarioConditionId("condition:pulchra:hunter-step-active")
PULCHRA_PURSUIT_MARK_ACTIVE = ScenarioConditionId("condition:pulchra:pursuit-mark-active")
PULCHRA_EXTRA_ABILITY_RULE_ID = RuleItemId("rule:character:1351:extra-ability:pursuit")
PULCHRA_CINEMA6_NIGHTMARE_RULE_ID = RuleItemId("rule:character:1351:cinema6:nightmare-damage")
PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT = ScenarioParameterId("parameter:pulchra:nightmare-base-extra-attack-count")
PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT = ScenarioParameterId("parameter:pulchra:cinema6-extra-attack-count")

PULCHRA_BASIC_MOVE_ID = MoveId("move:pulchra:basic-jab")
PULCHRA_JUMP_MOVE_ID = MoveId("move:pulchra:basic-leaping-slash")
PULCHRA_DASH_MOVE_ID = MoveId("move:pulchra:dash-attack")
PULCHRA_COUNTER_MOVE_ID = MoveId("move:pulchra:dodge-counter")
PULCHRA_SPECIAL_MOVE_ID = MoveId("move:pulchra:special-claw-strike")
PULCHRA_NIGHTMARE_MOVE_ID = MoveId("move:pulchra:special-nightmare-shadow")
PULCHRA_EX_MOVE_ID = MoveId("move:pulchra:ex-step")
PULCHRA_CHAIN_MOVE_ID = MoveId("move:pulchra:chain-attack")
PULCHRA_ULTIMATE_MOVE_ID = MoveId("move:pulchra:ultimate")
PULCHRA_QUICK_ASSIST_MOVE_ID = MoveId("move:pulchra:quick-assist")
PULCHRA_ASSIST_STRIKE_MOVE_ID = MoveId("move:pulchra:assist-strike")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_NIGHTMARE = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK})


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    curve: str,
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
        parameters=(NanokaDamageParameterSpec(
            variant_key=f"{key}-damage",
            parameter_name=parameter,
            source_skill_id=curve,
        ),),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
    )


PULCHRA_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-jab-{stage}", move_id=PULCHRA_BASIC_MOVE_ID,
                label=f"普通攻击：捷击（{('一', '二', '三')[stage - 1]}段）",
                source_name="普通攻击：捷击", group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC, parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                curve=f"135100{stage}", relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            ) for stage in range(1, 4)
        ),
        _move("basic-leaping-slash", move_id=PULCHRA_JUMP_MOVE_ID,
              label="普通攻击：跃击", source_name="普通攻击：跃击",
              group=SkillGroup.BASIC_ATTACK, tags=_BASIC,
              parameter="伤害倍率", curve="1351004"),
        _move("dash-attack", move_id=PULCHRA_DASH_MOVE_ID,
              label="冲刺攻击：先下手为强", source_name="冲刺攻击：先下手为强",
              group=SkillGroup.DODGE, tags=_DASH,
              parameter="伤害倍率", curve="1351009"),
        _move("dodge-counter", move_id=PULCHRA_COUNTER_MOVE_ID,
              label="闪避反击：睚眦必报", source_name="闪避反击：睚眦必报",
              group=SkillGroup.DODGE, tags=_COUNTER,
              parameter="伤害倍率", curve="1351010"),
        _move("special-claw-strike", move_id=PULCHRA_SPECIAL_MOVE_ID,
              label="特殊技：噬爪", source_name="特殊技：噬爪",
              group=SkillGroup.SPECIAL_ATTACK, tags=_SPECIAL,
              parameter="伤害倍率", curve="1351005"),
        _move("nightmare-shadow-main", move_id=PULCHRA_NIGHTMARE_MOVE_ID,
              label="特殊技：噬爪·噩梦袭影（初次攻击）",
              source_name="特殊技：噬爪·噩梦袭影",
              group=SkillGroup.SPECIAL_ATTACK, tags=_NIGHTMARE,
              parameter="伤害倍率", curve="1351006"),
        # The EX proc is an explicit EX Special move. Nightmare's proc trigger
        # mentions EX heavy hits, but its own damage packet remains Special.
        _move("ex-step", move_id=PULCHRA_EX_MOVE_ID,
              label="强化特殊技：噬爪·瞬步", source_name="强化特殊技：噬爪·瞬步",
              group=SkillGroup.SPECIAL_ATTACK, tags=_EX,
              parameter="伤害倍率", curve="1351008"),
        _move("chain-attack", move_id=PULCHRA_CHAIN_MOVE_ID,
              label="连携技：嗨，想不到吧", source_name="连携技：嗨，想不到吧",
              group=SkillGroup.CHAIN_ATTACK, tags=_CHAIN,
              parameter="伤害倍率", curve="1351011"),
        _move("ultimate", move_id=PULCHRA_ULTIMATE_MOVE_ID,
              label="终结技：噢，游戏时间", source_name="终结技：噢，游戏时间",
              group=SkillGroup.ULTIMATE, tags=_ULTIMATE,
              parameter="伤害倍率", curve="1351012"),
        _move("quick-assist", move_id=PULCHRA_QUICK_ASSIST_MOVE_ID,
              label="快速支援：雇佣合同·保镖业务",
              source_name="快速支援：雇佣合同·保镖业务",
              group=SkillGroup.ASSIST, tags=_ASSIST,
              parameter="伤害倍率", curve="1351013"),
        _move("assist-strike", move_id=PULCHRA_ASSIST_STRIKE_MOVE_ID,
              label="支援突击：单独计价", source_name="支援突击：单独计价",
              group=SkillGroup.ASSIST, tags=_ASSIST,
              parameter="伤害倍率", curve="1351014"),
    )
)


__all__ = [
    "PULCHRA_EXTRA_ABILITY_RULE_ID", "PULCHRA_HUNTER_STEP_ACTIVE",
    "PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT", "PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT",
    "PULCHRA_CINEMA6_NIGHTMARE_RULE_ID", "PULCHRA_PURSUIT_MARK_ACTIVE",
    "PULCHRA_REVIEWED_MAPPING", "PULCHRA_ID", "PULCHRA_BASIC_MOVE_ID",
    "PULCHRA_JUMP_MOVE_ID", "PULCHRA_DASH_MOVE_ID", "PULCHRA_COUNTER_MOVE_ID",
    "PULCHRA_SPECIAL_MOVE_ID", "PULCHRA_NIGHTMARE_MOVE_ID", "PULCHRA_EX_MOVE_ID",
    "PULCHRA_CHAIN_MOVE_ID", "PULCHRA_ULTIMATE_MOVE_ID", "PULCHRA_QUICK_ASSIST_MOVE_ID",
    "PULCHRA_ASSIST_STRIKE_MOVE_ID",
]
