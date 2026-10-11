"""Reviewed Nanoka 3.2 move identities for Manato (character:1441)."""

from __future__ import annotations

from core.types import DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)
from .config import MANATO_ID


MANATO_EMBER_EDGE_ACTIVE = ScenarioConditionId("condition:manato:ember-edge-active")
MANATO_HP_SPENDING_ATTACK_ACTIVE = ScenarioConditionId(
    "condition:manato:hp-spending-attack-active"
)
MANATO_SPECIAL_STANDARD_ACTIVE = ScenarioConditionId(
    "condition:manato:special-standard-variant"
)
MANATO_SPECIAL_ENHANCED_ACTIVE = ScenarioConditionId(
    "condition:manato:special-enhanced-variant"
)
MANATO_SUPPORT_FOLLOWUP_STANDARD_ACTIVE = ScenarioConditionId(
    "condition:manato:support-followup-standard-variant"
)
MANATO_SUPPORT_FOLLOWUP_MAX_ACTIVE = ScenarioConditionId(
    "condition:manato:support-followup-max-variant"
)

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

MANATO_BASIC_MOVE_ID = MoveId("move:manato:basic-blazing-wind-slash")
MANATO_EMPOWERED_BASIC_MOVE_ID = MoveId("move:manato:basic-blazing-wind-hidden-cut")
MANATO_DASH_MOVE_ID = MoveId("move:manato:dash-resolve-blade")
MANATO_COUNTER_MOVE_ID = MoveId("move:manato:dodge-counter-formation-blade")
MANATO_SPECIAL_MOVE_ID = MoveId("move:manato:special-return-to-ashes")
MANATO_EX_SPECIAL_MOVE_ID = MoveId("move:manato:ex-special-falling-ashes")
MANATO_CHAIN_MOVE_ID = MoveId("move:manato:chain-explosive-flame")
MANATO_ULTIMATE_MOVE_ID = MoveId("move:manato:ultimate-unthinking-soul")
MANATO_QUICK_ASSIST_MOVE_ID = MoveId("move:manato:quick-assist-return-to-formation")
MANATO_PARRY_ASSIST_MOVE_ID = MoveId("move:manato:parry-assist-mountain-stance")
MANATO_SUPPORT_FOLLOWUP_MOVE_ID = MoveId("move:manato:assist-follow-up-breaking-fang")


def _components(*skill_ids: str) -> tuple[tuple[str, float], ...]:
    return tuple((skill_id, 1.0) for skill_id in skill_ids)


def _move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    parameter: str,
    element: Element,
    curve: str | None = None,
    components: tuple[tuple[str, float], ...] = (),
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
                parameter_name=parameter,
                source_skill_id=curve,
                source_skill_components=components,
                condition_ids=conditions,
            ),
        ),
        multiplier_relation=relation,
        element=element,
        stage_index=stage,
        condition_ids=conditions,
    )


def _variant_move(
    key: str,
    *,
    move_id: MoveId,
    label: str,
    source_name: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    element: Element,
    variants: tuple[
        tuple[
            str,
            str,
            str | None,
            tuple[tuple[str, float], ...],
            ScenarioConditionId,
        ],
        ...,
    ],
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=key,
        move_id=move_id,
        display_name=label,
        source_name=source_name,
        skill_group=group,
        damage_tags=tags,
        parameters=tuple(
            NanokaDamageParameterSpec(
                variant_key=variant_key,
                parameter_name=parameter_name,
                source_skill_id=source_skill_id,
                source_skill_components=components,
                condition_ids=(condition_id,),
            )
            for (
                variant_key,
                parameter_name,
                source_skill_id,
                components,
                condition_id,
            ) in variants
        ),
        multiplier_relation=MultiplierRelation.MUTUALLY_EXCLUSIVE_VARIANT,
        element=element,
    )


_BASIC_SOURCE = "普通攻击：炽风斩"
_BASIC_STAGES = (
    (1, "一段伤害倍率", ("1441001",)),
    (2, "二段伤害倍率", ("1441002", "1441003")),
    (3, "三段伤害倍率", ("1441004", "1441005")),
)
_EMBER_BASIC_STAGES = (
    (1, "一段伤害倍率（触发烬风）", "1441001", "1441006"),
    (2, "二段伤害倍率（触发烬风）", "1441002", "1441007"),
    (3, "三段伤害倍率（触发烬风）", "1441004", "1441008"),
)


_moves: list[NanokaMoveSpec] = []
for stage, parameter, skill_ids in _BASIC_STAGES:
    _moves.append(
        _move(
            f"basic-stage-{stage}",
            move_id=MANATO_BASIC_MOVE_ID,
            label=f"普通攻击：炽风斩（{('一', '二', '三')[stage - 1]}段）",
            source_name=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter=parameter,
            components=_components(*skill_ids),
            element=Element.PHYSICAL,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
    )

for stage, parameter, base_skill, fire_skill in _EMBER_BASIC_STAGES:
    _moves.append(
        _move(
            f"basic-ember-stage-{stage}",
            move_id=MANATO_BASIC_MOVE_ID,
            label=f"普通攻击：炽风斩·烬风（{('一', '二', '三')[stage - 1]}段）",
            source_name=_BASIC_SOURCE,
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter=parameter,
            components=_components(base_skill, fire_skill),
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
        )
    )

for stage, curve in enumerate(("1441009", "1441010", "1441011", "1441012"), 1):
    _moves.append(
        _move(
            f"basic-empowered-stage-{stage}",
            move_id=MANATO_EMPOWERED_BASIC_MOVE_ID,
            label=f"普通攻击：炽风·胧切（{('一', '二', '三', '四')[stage - 1]}段）",
            source_name="普通攻击：炽风·胧切",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            parameter=f"{('一段', '二段', '三段', '四段')[stage - 1]}伤害倍率",
            curve=curve,
            element=Element.FIRE,
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=stage,
            conditions=(MANATO_EMBER_EDGE_ACTIVE,),
        )
    )

_moves.extend(
    (
        _move(
            "dash-resolve-blade",
            move_id=MANATO_DASH_MOVE_ID,
            label="冲刺攻击：曜刃·残心",
            source_name="冲刺攻击：曜刃·残心",
            group=SkillGroup.DODGE,
            tags=_DASH,
            parameter="伤害倍率",
            curve="1441016",
            element=Element.PHYSICAL,
        ),
        _move(
            "dodge-counter-formation-blade",
            move_id=MANATO_COUNTER_MOVE_ID,
            label="闪避反击：曜刃·掠阵",
            source_name="闪避反击：曜刃·掠阵",
            group=SkillGroup.DODGE,
            tags=_COUNTER,
            parameter="伤害倍率",
            curve="1441017",
            element=Element.FIRE,
        ),
        _move(
            "ex-special-falling-ashes",
            move_id=MANATO_EX_SPECIAL_MOVE_ID,
            label="强化特殊技：归烬·天坠",
            source_name="强化特殊技：归烬·天坠",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_EX_SPECIAL,
            parameter="伤害倍率",
            curve="1441015",
            element=Element.FIRE,
            conditions=(MANATO_EMBER_EDGE_ACTIVE,),
        ),
        _move(
            "chain-explosive-flame",
            move_id=MANATO_CHAIN_MOVE_ID,
            label="连携技：极炽炎爆",
            source_name="连携技：极炽炎爆",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            parameter="伤害倍率",
            curve="1441018",
            element=Element.FIRE,
        ),
        _move(
            "ultimate-unthinking-soul",
            move_id=MANATO_ULTIMATE_MOVE_ID,
            label="终结技：无想荒魂",
            source_name="终结技：无想荒魂",
            group=SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
            parameter="伤害倍率",
            curve="1441019",
            element=Element.FIRE,
        ),
        _move(
            "quick-assist-return-to-formation",
            move_id=MANATO_QUICK_ASSIST_MOVE_ID,
            label="快速支援：孤影·归阵",
            source_name="快速支援：孤影·归阵",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1441020",
            element=Element.FIRE,
        ),
        _move(
            "parry-assist-mountain-stance",
            move_id=MANATO_PARRY_ASSIST_MOVE_ID,
            label="招架支援：孤影·岳峙",
            source_name="招架支援：孤影·岳峙",
            group=SkillGroup.ASSIST,
            tags=_ASSIST,
            parameter="伤害倍率",
            curve="1441026",
            element=Element.FIRE,
        ),
    )
)

_moves.extend(
    (
        _variant_move(
            "special-return-to-ashes",
            move_id=MANATO_SPECIAL_MOVE_ID,
            label="特殊技：归烬",
            source_name="特殊技：归烬",
            group=SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            element=Element.FIRE,
            variants=(
                (
                    "standard-slash",
                    "伤害倍率",
                    "1441013",
                    (),
                    MANATO_SPECIAL_STANDARD_ACTIVE,
                ),
                (
                    "charged-or-parry-success",
                    "伤害倍率（蓄力或格挡成功）",
                    "1441014",
                    (),
                    MANATO_SPECIAL_ENHANCED_ACTIVE,
                ),
            ),
        ),
        _variant_move(
            "support-follow-up-breaking-fang",
            move_id=MANATO_SUPPORT_FOLLOWUP_MOVE_ID,
            label="支援突击：孤影·断獠",
            source_name="支援突击：孤影·断獠",
            group=SkillGroup.ASSIST,
            tags=_FOLLOW_UP,
            element=Element.FIRE,
            variants=(
                (
                    "single-hit",
                    "伤害倍率",
                    "1441024",
                    (),
                    MANATO_SUPPORT_FOLLOWUP_STANDARD_ACTIVE,
                ),
                (
                    "continuous-max-total",
                    "连打最大伤害倍率",
                    "1441024",
                    (),
                    MANATO_SUPPORT_FOLLOWUP_MAX_ACTIVE,
                ),
            ),
        ),
    )
)

MANATO_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=tuple(_moves),
    data_quality_notes=(
        "烬风原文明确写作每段Basic发动时触发并使此次攻击造成更高火属性伤害；"
        "各烬风总倍率按raw明确列出的基础ID与火伤ID求和，视为互斥的整次Fire/Penetration攻击，不另造物理子事件。",
        "支援突击只有单次伤害倍率与连打最大总倍率两条raw曲线；最大模式将显式的1441024起手伤害与"
        "1441025连续斩击汇总倍率作为两个伤害事件；连续追加次数的中间曲线未给出，不把最大值除以7或推定次数。",
        "影画6只建模raw明确列出的当前有效火伤层数加成；不添加raw中不存在的激光事件或暴伤加成。",
        "额外能力原文只提供炽心/残焰资源与回复；资源和时间不属于静态伤害输出，因此不产生空效果规则。",
    ),
)


__all__ = [
    "MANATO_BASIC_MOVE_ID",
    "MANATO_EMBER_EDGE_ACTIVE",
    "MANATO_EMPOWERED_BASIC_MOVE_ID",
    "MANATO_HP_SPENDING_ATTACK_ACTIVE",
    "MANATO_ID",
    "MANATO_PARRY_ASSIST_MOVE_ID",
    "MANATO_QUICK_ASSIST_MOVE_ID",
    "MANATO_REVIEWED_MAPPING",
    "MANATO_SPECIAL_ENHANCED_ACTIVE",
    "MANATO_SPECIAL_MOVE_ID",
    "MANATO_SPECIAL_STANDARD_ACTIVE",
    "MANATO_SUPPORT_FOLLOWUP_MAX_ACTIVE",
    "MANATO_SUPPORT_FOLLOWUP_MOVE_ID",
    "MANATO_SUPPORT_FOLLOWUP_STANDARD_ACTIVE",
    "MANATO_ULTIMATE_MOVE_ID",
]
