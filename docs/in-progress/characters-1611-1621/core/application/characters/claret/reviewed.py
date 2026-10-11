"""Source-reviewed Nanoka mappings for Claret (character:1611).

This module preserves the moves' actual source curves and identities.  The
current calculator has no typed Sharp Damage event, so these mappings are not
compiled as Direct or Sharp Explosion damage.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from core.types import CalculationNode, DamageTag, Element, MoveId, SkillGroup

from ...moves import MultiplierRelation


class ClaretDamageSemantics(StrEnum):
    SHARPENED = "sharpened"
    DESTROY = "destroy"


@dataclass(frozen=True, slots=True)
class ClaretSourceCurveSpec:
    key: str
    source_name: str
    parameter_name: str
    source_skill_id: str
    source_skill_group: SkillGroup
    source_move_id: MoveId
    event_move_id: MoveId | None
    event_skill_group: SkillGroup | None
    damage_tags: frozenset[DamageTag]
    triggering_move_ids: tuple[MoveId, ...] = ()
    element: Element = Element.ELECTRIC
    damage_basis_node: CalculationNode = CalculationNode.CHARACTER_CURRENT_DEFENSE
    semantics: ClaretDamageSemantics = ClaretDamageSemantics.SHARPENED
    multiplier_relation: MultiplierRelation = MultiplierRelation.COMPLETE
    stage_index: int | None = None


@dataclass(frozen=True, slots=True)
class ClaretInitialCritConversionSpec:
    source_node: CalculationNode
    target_node: CalculationNode
    coefficient: float
    source_text: str


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX = frozenset({DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})


def _move_id(key: str) -> MoveId:
    return MoveId(f"move:claret:{key}")


_ACTION_MOVE_KEYS = {
    "普通攻击：血锻四式": "basic-forge-four",
    "普通攻击：血华誓·锻星": "basic-scarlet-forge",
    "普通攻击：血华誓·伏钺": "basic-scarlet-ambush",
    "冲刺攻击：淬火": "dash-temper",
    "闪避反击：回锋": "counter-returning-edge",
    "闪避反击：血华誓·回锋": "counter-scarlet-returning-edge",
    "特殊技：初辉启鸣": "special-first-light",
    "强化特殊技：血华誓·铸锋秘术": "ex-scarlet-forging",
    "特殊技：血华誓·斩金断铁": "special-sever-gold",
    "特殊技：血华誓·葬血强袭": "special-blood-burial",
    "连携技：血华誓·血契共鸣": "chain-blood-contract",
    "终结技：血华誓·千锤百炼": "ultimate-hundred-forges",
    "快速支援：厄月再临": "quick-assist-waning-moon",
    "快速支援：血华誓·厄月再临": "quick-assist-scarlet-waning-moon",
    "支援突击：血华誓·无垢熔锋": "assist-strike-pure-forge",
    "反制支援：寸铁不让": "counter-assist-unyielding-core",
    "支援突击：血华誓·琢形": "assist-strike-carve-form",
}


def _curve(
    key: str,
    source_name: str,
    parameter_name: str,
    source_skill_id: int,
    source_skill_group: SkillGroup,
    *,
    tags: frozenset[DamageTag],
    semantics: ClaretDamageSemantics = ClaretDamageSemantics.SHARPENED,
    event_move_id: MoveId | None = None,
    event_skill_group: SkillGroup | None = None,
    triggering_move_ids: tuple[MoveId, ...] = (),
    stage_index: int | None = None,
) -> ClaretSourceCurveSpec:
    source_move_id = _move_id(_ACTION_MOVE_KEYS[source_name])
    if semantics is ClaretDamageSemantics.DESTROY:
        # Destroy is an explicitly separate event created by a marked-target
        # hit; do not inherit the triggering Special's move/tag/group identity.
        event_move_id = None
        event_skill_group = None
        tags = frozenset()
        triggering_move_ids = (
            _move_id(_ACTION_MOVE_KEYS["特殊技：血华誓·斩金断铁"]),
            _move_id(_ACTION_MOVE_KEYS["特殊技：血华誓·葬血强袭"]),
        )
    else:
        event_move_id = event_move_id or source_move_id
        event_skill_group = event_skill_group or source_skill_group
    return ClaretSourceCurveSpec(
        key=key,
        source_name=source_name,
        parameter_name=parameter_name,
        source_skill_id=str(source_skill_id),
        source_skill_group=source_skill_group,
        source_move_id=source_move_id,
        event_move_id=event_move_id,
        event_skill_group=event_skill_group,
        damage_tags=tags,
        triggering_move_ids=triggering_move_ids,
        semantics=semantics,
        stage_index=stage_index,
    )


_curves: list[ClaretSourceCurveSpec] = []
for stage, parameter_name, skill_id in (
    (1, "一段伤害倍率", 1611001),
    (2, "二段伤害倍率", 1611002),
    (3, "三段伤害倍率", 1611003),
    (4, "四段伤害倍率", 1611004),
):
    _curves.append(
        _curve(
            f"basic-forge-{stage}",
            "普通攻击：血锻四式",
            parameter_name,
            skill_id,
            SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            stage_index=stage,
        )
    )

for key, parameter_name, skill_id, stage in (
    ("basic-scarlet-forge-1", "一段伤害倍率", 1611005, 1),
    ("basic-scarlet-forge-2", "二段伤害倍率", 1611006, 2),
    ("basic-scarlet-forge-3-slashes", "三段连续斩击伤害倍率", 1611007, 3),
    ("basic-scarlet-forge-3-finisher", "三段下砸伤害倍率", 1611029, 3),
):
    _curves.append(
        _curve(
            key,
            "普通攻击：血华誓·锻星",
            parameter_name,
            skill_id,
            SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            stage_index=stage,
        )
    )

_curves.extend(
    (
        _curve(
            "basic-scarlet-ambush",
            "普通攻击：血华誓·伏钺",
            "伤害倍率",
            1611008,
            SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
        ),
        _curve(
            "dash-temper",
            "冲刺攻击：淬火",
            "伤害倍率",
            1611016,
            SkillGroup.DODGE,
            tags=_DASH,
        ),
        _curve(
            "counter-returning-edge",
            "闪避反击：回锋",
            "伤害倍率",
            1611018,
            SkillGroup.DODGE,
            tags=_COUNTER,
        ),
        _curve(
            "counter-scarlet-returning-edge",
            "闪避反击：血华誓·回锋",
            "伤害倍率",
            1611019,
            SkillGroup.DODGE,
            tags=_COUNTER,
        ),
        _curve(
            "special-first-light",
            "特殊技：初辉启鸣",
            "伤害倍率",
            1611009,
            SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
        ),
        _curve(
            "ex-scarlet-forging",
            "强化特殊技：血华誓·铸锋秘术",
            "伤害倍率",
            1611010,
            SkillGroup.SPECIAL_ATTACK,
            tags=_EX,
        ),
        _curve(
            "special-sever-gold-uppercut",
            "特殊技：血华誓·斩金断铁",
            "上挑伤害倍率",
            1611011,
            SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
        ),
        _curve(
            "special-sever-gold-crosscut",
            "特殊技：血华誓·斩金断铁",
            "横斩伤害倍率",
            1611012,
            SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
        ),
        _curve(
            "special-sever-gold-destroy",
            "特殊技：血华誓·斩金断铁",
            "毁伤伤害倍率",
            1611013,
            SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
            semantics=ClaretDamageSemantics.DESTROY,
        ),
        _curve(
            "special-blood-burial",
            "特殊技：血华誓·葬血强袭",
            "伤害倍率",
            1611014,
            SkillGroup.SPECIAL_ATTACK,
            tags=_SPECIAL,
        ),
        _curve(
            "chain-blood-contract",
            "连携技：血华誓·血契共鸣",
            "伤害倍率",
            1611020,
            SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
        ),
        _curve(
            "ultimate-hundred-forges",
            "终结技：血华誓·千锤百炼",
            "伤害倍率",
            1611021,
            SkillGroup.ULTIMATE,
            tags=_ULTIMATE,
        ),
        _curve(
            "quick-assist-waning-moon",
            "快速支援：厄月再临",
            "伤害倍率",
            1611022,
            SkillGroup.ASSIST,
            tags=_ASSIST,
        ),
        _curve(
            "quick-assist-scarlet-waning-moon",
            "快速支援：血华誓·厄月再临",
            "伤害倍率",
            1611023,
            SkillGroup.ASSIST,
            tags=_ASSIST,
        ),
        _curve(
            "assist-strike-pure-forge",
            "支援突击：血华誓·无垢熔锋",
            "伤害倍率",
            1611027,
            SkillGroup.ASSIST,
            tags=_ASSIST,
        ),
        _curve(
            "counter-assist-unyielding-core",
            "反制支援：寸铁不让",
            "伤害倍率",
            1611028,
            SkillGroup.ASSIST,
            tags=_ASSIST,
        ),
        _curve(
            "assist-strike-carve-form",
            "支援突击：血华誓·琢形",
            "伤害倍率",
            1611030,
            SkillGroup.ASSIST,
            tags=_ASSIST,
        ),
    )
)


CLARET_SOURCE_CURVES = tuple(_curves)
CLARET_SOURCE_CURVE_BY_SKILL_ID = {
    item.source_skill_id: item for item in CLARET_SOURCE_CURVES
}

CLARET_INITIAL_CRIT_CONVERSION = ClaretInitialCritConversionSpec(
    source_node=CalculationNode.CHARACTER_INITIAL_CRIT_DAMAGE,
    target_node=CalculationNode.CHARACTER_INITIAL_CRIT_RATE,
    coefficient=0.35,
    source_text=(
        "克拉蕾每拥有1%的初始暴击伤害，初始暴击率提升0.35%"
    ),
)

CLARET_CURRENT_SCARLET_CRIT_NODE = CalculationNode.CHARACTER_CURRENT_CRIT_RATE

__all__ = [
    "CLARET_CURRENT_SCARLET_CRIT_NODE",
    "CLARET_INITIAL_CRIT_CONVERSION",
    "CLARET_SOURCE_CURVES",
    "CLARET_SOURCE_CURVE_BY_SKILL_ID",
    "ClaretDamageSemantics",
    "ClaretInitialCritConversionSpec",
    "ClaretSourceCurveSpec",
]
