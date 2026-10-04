"""Reviewed Yidhari (1051) raw skill identities and Ice attack mapping."""

from __future__ import annotations

from core.types import CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId
from ...moves import MultiplierRelation
from ..nanoka_compiler import NanokaDamageParameterSpec, NanokaMoveSpec, NanokaReviewedMapping


YIDHARI_ID = CharacterId("character:1051")
ETHER_CURTAIN_ACTIVE = ScenarioConditionId("condition:yidhari:ether-curtain-active")
CORE_MAX_HP_DAMAGE_BONUS_ACTIVE = ScenarioConditionId(
    "condition:yidhari:core-max-hp-damage-bonus-active"
)
HP_BELOW_50_ACTIVE = ScenarioConditionId("condition:yidhari:hp-below-50-active")
CINEMA6_INSIGHT_ACTIVE = ScenarioConditionId("condition:yidhari:cinema6-insight-active")

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})

BASIC_SMASH_MOVE_ID = MoveId("move:yidhari:basic-shattered-strike")
BASIC_CHARGE_MOVE_ID = MoveId("move:yidhari:basic-frost-covering-charge")
DASH_MOVE_ID = MoveId("move:yidhari:dash-frostbloom-impact")
DODGE_COUNTER_MOVE_ID = MoveId("move:yidhari:dodge-counter-ice-sway")
SPECIAL_MOVE_ID = MoveId("move:yidhari:special-broken-thought")
EX_SPECIAL_MOVE_ID = MoveId("move:yidhari:ex-special-frost-wrap")
SPECIAL_PURSUIT_MOVE_ID = MoveId("move:yidhari:special-cold-pursuit")
EX_POLAR_CRUSH_MOVE_ID = MoveId("move:yidhari:ex-special-polar-crush")
CHAIN_MOVE_ID = MoveId("move:yidhari:chain-cold-vow")
ULTIMATE_MOVE_ID = MoveId("move:yidhari:ultimate-final-act")
QUICK_ASSIST_MOVE_ID = MoveId("move:yidhari:quick-assist-frost-call")
ASSIST_FOLLOW_UP_MOVE_ID = MoveId("move:yidhari:assist-ice-shard-strike")
ICE_ANOMALY_MOVE_ID = MoveId("move:yidhari:ice-anomaly")
ICE_DISORDER_MOVE_ID = MoveId("move:yidhari:ice-disorder")


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
        element=Element.ICE,
        stage_index=stage,
        condition_ids=conditions,
    )


YIDHARI_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-shattered-strike-{stage}",
                BASIC_SMASH_MOVE_ID,
                f"普通攻击：碎惘沉击（{stage}段）",
                "普通攻击：碎惘沉击",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{'一二三'[stage - 1]}段伤害倍率",
                f"105100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 4)
        ),
        _move(
            "basic-shattered-strike-first-derived",
            BASIC_SMASH_MOVE_ID,
            "普通攻击：碎惘沉击（派生一段）",
            "普通攻击：碎惘沉击",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "一段伤害倍率（派生）",
            "1051004",
        ),
        _move(
            "basic-frost-charge-one",
            BASIC_CHARGE_MOVE_ID,
            "普通攻击：霜寒拥覆（一级蓄力）",
            "普通攻击：霜寒拥覆",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "一级蓄力伤害倍率",
            "1051005",
        ),
        _move(
            "basic-frost-charge-two",
            BASIC_CHARGE_MOVE_ID,
            "普通攻击：霜寒拥覆（二级蓄力）",
            "普通攻击：霜寒拥覆",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "二级蓄力伤害倍率",
            "1051006",
        ),
        _move(
            "basic-frost-charge-three-spin",
            BASIC_CHARGE_MOVE_ID,
            "普通攻击：霜寒拥覆（三级蓄力旋转）",
            "普通攻击：霜寒拥覆",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "三级蓄力旋转伤害倍率",
            "1051008",
        ),
        _move(
            "basic-frost-charge-three-finisher",
            BASIC_CHARGE_MOVE_ID,
            "普通攻击：霜寒拥覆（三级蓄力下砸）",
            "普通攻击：霜寒拥覆",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "三级蓄力下砸伤害倍率",
            "1051007",
        ),
        _move(
            "dash-frostbloom-impact",
            DASH_MOVE_ID,
            "冲刺攻击：霜华突撼",
            "冲刺攻击：霜华突撼",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1051013",
        ),
        _move(
            "dodge-counter-ice-sway",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：冰曳回震",
            "闪避反击：冰曳回震",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1051014",
        ),
        _move(
            "special-broken-thought",
            SPECIAL_MOVE_ID,
            "特殊技：断想",
            "特殊技：断想",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1051009",
        ),
        _move(
            "ex-special-frost-wrap",
            EX_SPECIAL_MOVE_ID,
            "强化特殊技：缠霜",
            "强化特殊技：缠霜",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1051010",
        ),
        _move(
            "special-cold-pursuit",
            SPECIAL_PURSUIT_MOVE_ID,
            "特殊技：溯寒追碾",
            "特殊技：溯寒追碾",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1051011",
        ),
        _move(
            "ex-special-polar-crush",
            EX_POLAR_CRUSH_MOVE_ID,
            "强化特殊技：极寒重碾",
            "强化特殊技：极寒重碾",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "强化特殊技：极寒重碾伤害倍率",
            "1051012",
        ),
        _move(
            "chain-cold-vow",
            CHAIN_MOVE_ID,
            "连携技：踱寒践约（常规倍率）",
            "连携技：踱寒践约",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1051015",
        ),
        _move(
            "chain-cold-vow-in-ether-curtain",
            CHAIN_MOVE_ID,
            "连携技：踱寒践约（以太帷幕·涌泉中）",
            "连携技：踱寒践约",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "[以太帷幕·涌泉]中伤害倍率",
            "1051025",
            conditions=(ETHER_CURTAIN_ACTIVE,),
        ),
        _move(
            "ultimate-final-act",
            ULTIMATE_MOVE_ID,
            "终结技：终幕·惘事渡却",
            "终结技：终幕·惘事渡却",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1051016",
            conditions=(ETHER_CURTAIN_ACTIVE,),
        ),
        _move(
            "quick-assist-frost-call",
            QUICK_ASSIST_MOVE_ID,
            "快速支援：撼霜驰援",
            "快速支援：撼霜驰援",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1051017",
        ),
        _move(
            "assist-ice-shard-strike",
            ASSIST_FOLLOW_UP_MOVE_ID,
            "支援突击：冰袭痛击",
            "支援突击：冰袭痛击",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            "伤害倍率",
            "1051021",
        ),
    ),
    data_quality_notes=(
        "Every reviewed Direct curve names Ice damage and the raw Core describes "
        "her Ice skill damage as Penetration. Separate Daze curves remain raw; "
        "the current request has no Daze result.",
        "The Frost-Sinking Counter curve has no matching skill_list entry, so its "
        "event is reviewed without inventing a MoveId; it retains its Basic group "
        "and Basic tag from the raw skill.basic section.",
        "The raw Core low-HP damage effect specifies its maximum and threshold but "
        "not the intermediate HP-to-bonus function. Its current bonus input remains "
        "explicit rather than inferred or interpolated.",
    ),
)


__all__ = [
    "ASSIST_FOLLOW_UP_MOVE_ID",
    "BASIC_CHARGE_MOVE_ID",
    "BASIC_SMASH_MOVE_ID",
    "CINEMA6_INSIGHT_ACTIVE",
    "CORE_MAX_HP_DAMAGE_BONUS_ACTIVE",
    "DASH_MOVE_ID",
    "DODGE_COUNTER_MOVE_ID",
    "ETHER_CURTAIN_ACTIVE",
    "EX_POLAR_CRUSH_MOVE_ID",
    "EX_SPECIAL_MOVE_ID",
    "FROST_COUNTER_MOVE_ID",
    "HP_BELOW_50_ACTIVE",
    "ICE_ANOMALY_MOVE_ID",
    "ICE_DISORDER_MOVE_ID",
    "QUICK_ASSIST_MOVE_ID",
    "SPECIAL_MOVE_ID",
    "SPECIAL_PURSUIT_MOVE_ID",
    "ULTIMATE_MOVE_ID",
    "YIDHARI_ID",
    "YIDHARI_REVIEWED_MAPPING",
]
