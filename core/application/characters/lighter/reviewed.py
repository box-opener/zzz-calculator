"""Reviewed live Nanoka 3.2 move mapping for Lighter (character:1161)."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import RuleItemId, ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


LIGHTER_ID = CharacterId("character:1161")
FIRE_ANOMALY_RECORD_ID = "anomaly:character:1161:fire-burn"
FIRE_ANOMALY_MOVE_ID = MoveId("move:lighter:fire-burn")
FIRE_DISORDER_MOVE_ID = MoveId("move:lighter:fire-disorder")

MORALE_BRAWL_ACTIVE = ScenarioConditionId("condition:lighter:morale-brawl-active")
MORALE_IMPACT_BUFF_ACTIVE = ScenarioConditionId("condition:lighter:morale-impact-buff-active")
MORALE_FINISHER_ACTIVE = ScenarioConditionId("condition:lighter:morale-exhausted-finisher-active")
CORE_RESISTANCE_DEBUFF_ACTIVE = ScenarioConditionId(
    "condition:lighter:core-fire-ice-resistance-debuff-active"
)
BLIGHT_ACTIVE = ScenarioConditionId("condition:lighter:blight-active")
YANG_ACTIVE = ScenarioConditionId("condition:lighter:yang-active")

MORALE_IMPACT_STACKS = RuleItemId("rule:character:1161:core:morale-impact-stacks")
YANG_STACKS = RuleItemId("rule:character:1161:extra-ability:yang-stacks")

BASIC_MOVE_ID = MoveId("move:lighter:basic-l-style-roar-punch")
DASH_MOVE_ID = MoveId("move:lighter:dash-rib-rush")
DODGE_COUNTER_MOVE_ID = MoveId("move:lighter:dodge-counter-fierce-flash")
SPECIAL_MOVE_ID = MoveId("move:lighter:special-v-style-sunrise-uppercut")
SPECIAL_STEP_MOVE_ID = MoveId("move:lighter:special-v-style-sunrise-uppercut-step")
EX_SPECIAL_MOVE_ID = MoveId("move:lighter:ex-v-style-full-course")
EX_SPECIAL_STEP_MOVE_ID = MoveId("move:lighter:ex-v-style-full-course-step")
CHAIN_MOVE_ID = MoveId("move:lighter:chain-v-style-scorching-sun")
ULTIMATE_MOVE_ID = MoveId("move:lighter:ultimate-w-style-laurel-flame")
QUICK_ASSIST_MOVE_ID = MoveId("move:lighter:quick-assist-fierce-flash-guard")
ASSIST_STRIKE_MOVE_ID = MoveId("move:lighter:assist-strike-rib-rush-stab")

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
    source_skill_id: str,
    element: Element,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
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
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=condition_ids,
    )


_BASIC_SOURCE = "普通攻击：L式轰鸣拳"
_MORALE = (MORALE_BRAWL_ACTIVE,)
_MORALE_FINISHER = (MORALE_BRAWL_ACTIVE, MORALE_FINISHER_ACTIVE)

LIGHTER_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：L式轰鸣拳（{('一', '二', '三')[stage - 1]}段）",
                source=_BASIC_SOURCE,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=f"116100{stage}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        *tuple(
            _move(
                f"basic-continuous-combo-{stage}",
                move_id=BASIC_MOVE_ID,
                label=f"普通攻击：L式轰鸣拳（连续体术追击{stage}）",
                source=_BASIC_SOURCE,
                group=SkillGroup.BASIC_ATTACK,
                tags=_BASIC,
                parameter=f"追击{('一', '二', '三', '四', '五')[stage - 1]}段伤害倍率",
                source_skill_id=f"116100{stage + 3}",
                element=Element.PHYSICAL,
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 6)
        ),
        _move(
            "basic-4",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：L式轰鸣拳（四段）",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="四段伤害倍率",
            source_skill_id="1161009",
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=4,
        ),
        _move(
            "basic-5-jab-start",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：L式轰鸣拳（五段轻拳起攻）",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段起攻伤害倍率",
            source_skill_id="1161010",
            element=Element.FIRE,
        ),
        _move(
            "basic-5-jab-combo",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：L式轰鸣拳（五段刺拳连击）",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段连击伤害倍率",
            source_skill_id="1161011",
            element=Element.FIRE,
        ),
        _move(
            "basic-5-finisher",
            move_id=BASIC_MOVE_ID,
            label="普通攻击：L式轰鸣拳（五段终结一击）",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段终结伤害倍率",
            source_skill_id="1161012",
            element=Element.FIRE,
        ),
        _move(
            "basic-5-morale-jab-start",
            move_id=BASIC_MOVE_ID,
            label="士气喷发：普通攻击五段轻拳起攻",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段起攻伤害倍率（士气喷发状态）",
            source_skill_id="1161026",
            element=Element.FIRE,
            condition_ids=_MORALE,
        ),
        _move(
            "basic-5-morale-jab-combo",
            move_id=BASIC_MOVE_ID,
            label="士气喷发：普通攻击五段刺拳连击",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段连击伤害倍率（士气喷发状态）",
            source_skill_id="1161027",
            element=Element.FIRE,
            condition_ids=_MORALE,
        ),
        _move(
            "basic-5-morale-finisher",
            move_id=BASIC_MOVE_ID,
            label="士气喷发：普通攻击五段终结一击",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段终结伤害倍率（士气喷发状态）",
            source_skill_id="1161028",
            element=Element.FIRE,
            condition_ids=_MORALE,
        ),
        _move(
            "basic-5-morale-strong-finisher",
            move_id=BASIC_MOVE_ID,
            label="士气耗尽：普通攻击强力终结一击",
            source=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter="五段强力终结伤害倍率（士气喷发状态）",
            source_skill_id="1161025",
            element=Element.FIRE,
            condition_ids=_MORALE_FINISHER,
        ),
        _move(
            "dash-attack",
            move_id=DASH_MOVE_ID,
            label="冲刺攻击：骸突",
            source="冲刺攻击：骸突",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            source_skill_id="1161016",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter",
            move_id=DODGE_COUNTER_MOVE_ID,
            label="闪避反击：烈闪",
            source="闪避反击：烈闪",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            source_skill_id="1161017",
            element=Element.FIRE,
        ),
        _move(
            "special-uppercut",
            move_id=SPECIAL_MOVE_ID,
            label="特殊技：V式日轮升拳（上勾拳）",
            source="特殊技：V式日轮升拳",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1161013",
            element=Element.FIRE,
        ),
        _move(
            "special-step-combo",
            move_id=SPECIAL_STEP_MOVE_ID,
            label="垫步闪避期间：特殊技V式日轮升拳（组合拳）",
            source="特殊技：V式日轮升拳",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1161013",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-main",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：V式日轮升拳-全冲程（主击）",
            source="强化特殊技：V式日轮升拳-全冲程",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1161014",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-followup",
            move_id=EX_SPECIAL_MOVE_ID,
            label="强化特殊技：V式日轮升拳-全冲程（一次强力追击）",
            source="强化特殊技：V式日轮升拳-全冲程",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="追击伤害倍率",
            source_skill_id="1161015",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-step-combo",
            move_id=EX_SPECIAL_STEP_MOVE_ID,
            label="垫步闪避期间：强化特殊技（组合拳一次）",
            source="强化特殊技：V式日轮升拳-全冲程",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            source_skill_id="1161014",
            element=Element.FIRE,
        ),
        _move(
            "chain-attack",
            move_id=CHAIN_MOVE_ID,
            label="连携技：V式灼日炎",
            source="连携技：V式灼日炎",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            source_skill_id="1161018",
            element=Element.FIRE,
        ),
        _move(
            "ultimate",
            move_id=ULTIMATE_MOVE_ID,
            label="终结技：W式桂冠终火",
            source="终结技：W式桂冠终火",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            source_skill_id="1161019",
            element=Element.FIRE,
        ),
        _move(
            "quick-assist",
            move_id=QUICK_ASSIST_MOVE_ID,
            label="快速支援：烈闪-守",
            source="快速支援：烈闪-守",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1161020",
            element=Element.FIRE,
        ),
        _move(
            "assist-strike",
            move_id=ASSIST_STRIKE_MOVE_ID,
            label="支援突击：骸突-刺",
            source="支援突击：骸突-刺",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            source_skill_id="1161024",
            element=Element.FIRE,
        ),
    ),
)


__all__ = [
    "BLIGHT_ACTIVE",
    "CORE_RESISTANCE_DEBUFF_ACTIVE",
    "FIRE_ANOMALY_MOVE_ID",
    "FIRE_ANOMALY_RECORD_ID",
    "FIRE_DISORDER_MOVE_ID",
    "LIGHTER_ID",
    "LIGHTER_REVIEWED_MAPPING",
    "MORALE_BRAWL_ACTIVE",
    "MORALE_FINISHER_ACTIVE",
    "MORALE_IMPACT_BUFF_ACTIVE",
    "MORALE_IMPACT_STACKS",
    "YANG_ACTIVE",
    "YANG_STACKS",
]
