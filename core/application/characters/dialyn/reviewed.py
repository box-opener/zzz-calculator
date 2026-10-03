"""Reviewed move identities and source-curve mappings for Dialyn (1481)."""

from __future__ import annotations

from core.types import AnomalyRecordId, CharacterId, DamageTag, Element, MoveId, SkillGroup

from ...ids import ScenarioConditionId, ScenarioParameterId
from ...moves import MultiplierRelation
from ..nanoka_compiler import (
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
)


DIALYN_ID = CharacterId("character:1481")

GOOD_REVIEW_ACTIVE = ScenarioConditionId("condition:dialyn:good-review-active")
MALICIOUS_COMPLAINT_ACTIVE = ScenarioConditionId(
    "condition:dialyn:malicious-complaint-active"
)
AFTER_SOUND_ACTIVE = ScenarioConditionId("condition:dialyn:after-sound-active")

AFTER_SOUND_HIT_COUNT = ScenarioParameterId("parameter:dialyn:after-sound-hit-count")
PHYSICAL_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:dialyn:physical-disorder-remaining-seconds"
)
DIALYN_PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:dialyn:physical")

BASIC_SERVICE_MOVE_ID = MoveId("move:dialyn:basic-very-happy-to-help")
GUESSING_GAME_MOVE_ID = MoveId("move:dialyn:basic-rock-paper-scissors")
DASH_CALL_MOVE_ID = MoveId("move:dialyn:dash-sudden-call")
DODGE_COUNTER_MOVE_ID = MoveId("move:dialyn:dodge-counter-cannot-answer")
EX_SENDOFF_MOVE_ID = MoveId("move:dialyn:ex-sendoff")
SPECIAL_WELCOME_MOVE_ID = MoveId("move:dialyn:special-welcome-gesture")
EX_STONE_MOVE_ID = MoveId("move:dialyn:ex-stone")
EX_SCISSORS_MOVE_ID = MoveId("move:dialyn:ex-scissors")
EX_PAPER_MOVE_ID = MoveId("move:dialyn:ex-paper")
CHAIN_WELCOME_MAT_MOVE_ID = MoveId("move:dialyn:chain-welcome-mat")
ULTIMATE_TERMINATE_CALL_MOVE_ID = MoveId("move:dialyn:ultimate-terminate-call")
QUICK_ASSIST_TRANSFER_MOVE_ID = MoveId("move:dialyn:quick-assist-transfer")
SUPPORT_FOLLOWUP_CHAIN_CALL_MOVE_ID = MoveId("move:dialyn:support-follow-up-chain-call")
DIALYN_EX_MOVE_IDS = (EX_STONE_MOVE_ID, EX_SCISSORS_MOVE_ID, EX_PAPER_MOVE_ID)
DIALYN_EX_CINEMA6_TAGS = frozenset({DamageTag.EX_SPECIAL_ATTACK})

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = DIALYN_EX_CINEMA6_TAGS
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _p(
    key: str,
    parameter_name: str,
    source_skill_id: str,
    *conditions: ScenarioConditionId,
) -> NanokaDamageParameterSpec:
    return NanokaDamageParameterSpec(
        variant_key=key,
        parameter_name=parameter_name,
        condition_ids=conditions,
        source_skill_id=source_skill_id,
    )


def _move(
    entry_key: str,
    move_id: MoveId,
    display_name: str,
    source_name: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    parameter_name: str,
    source_skill_id: str,
    *,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    stage: int | None = None,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
) -> NanokaMoveSpec:
    return NanokaMoveSpec(
        entry_key=entry_key,
        move_id=move_id,
        display_name=display_name,
        source_name=source_name,
        skill_group=skill_group,
        damage_tags=damage_tags,
        parameters=(
            _p(f"{entry_key}-damage", parameter_name, source_skill_id, *condition_ids),
        ),
        multiplier_relation=relation,
        element=Element.PHYSICAL,
        stage_index=stage,
        condition_ids=condition_ids,
    )


_STAGE_LABELS = ("一", "二", "三", "四")

DIALYN_REVIEWED_MAPPING = NanokaReviewedMapping(
    moves=(
        *tuple(
            _move(
                f"basic-service-{stage}",
                BASIC_SERVICE_MOVE_ID,
                f"普通攻击：很高兴为您服务（{_STAGE_LABELS[stage - 1]}段）",
                "普通攻击：很高兴为您服务",
                SkillGroup.BASIC_ATTACK,
                _BASIC,
                f"{_STAGE_LABELS[stage - 1]}段伤害倍率",
                f"148100{stage}",
                relation=MultiplierRelation.SEQUENTIAL_STAGE,
                stage=stage,
            )
            for stage in range(1, 5)
        ),
        _move(
            "guessing-game-stage-1",
            GUESSING_GAME_MOVE_ID,
            "普通攻击：猜拳把戏（石头·一段）",
            "普通攻击：猜拳把戏",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "一段伤害倍率",
            "1481005",
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=1,
        ),
        _move(
            "guessing-game-stage-2",
            GUESSING_GAME_MOVE_ID,
            "普通攻击：猜拳把戏（石头·二段）",
            "普通攻击：猜拳把戏",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "二段伤害倍率",
            "1481006",
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=2,
        ),
        _move(
            "guessing-game-stage-3",
            GUESSING_GAME_MOVE_ID,
            "普通攻击：猜拳把戏（剪刀·三段）",
            "普通攻击：猜拳把戏",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "三段伤害倍率",
            "1481007",
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=3,
        ),
        _move(
            "guessing-game-stage-4",
            GUESSING_GAME_MOVE_ID,
            "普通攻击：猜拳把戏（剪刀·四段）",
            "普通攻击：猜拳把戏",
            SkillGroup.BASIC_ATTACK,
            _BASIC,
            "四段伤害倍率",
            "1481008",
            relation=MultiplierRelation.SEQUENTIAL_STAGE,
            stage=4,
        ),
        _move(
            "dash-sudden-call",
            DASH_CALL_MOVE_ID,
            "冲刺攻击：突然来电",
            "冲刺攻击：突然来电",
            SkillGroup.DODGE,
            _DASH,
            "伤害倍率",
            "1481014",
        ),
        _move(
            "dodge-counter-cannot-answer",
            DODGE_COUNTER_MOVE_ID,
            "闪避反击：无法接听",
            "闪避反击：无法接听",
            SkillGroup.DODGE,
            _COUNTER,
            "伤害倍率",
            "1481015",
        ),
        _move(
            "ex-sendoff",
            EX_SENDOFF_MOVE_ID,
            "强化特殊技：送客！",
            "强化特殊技：送客！",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1481009",
        ),
        _move(
            "special-welcome-gesture",
            SPECIAL_WELCOME_MOVE_ID,
            "特殊技：欢迎手势",
            "特殊技：欢迎手势",
            SkillGroup.SPECIAL_ATTACK,
            _SPECIAL,
            "伤害倍率",
            "1481010",
        ),
        _move(
            "ex-stone",
            EX_STONE_MOVE_ID,
            "强化特殊技：石头",
            "强化特殊技：石头",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1481011",
        ),
        _move(
            "ex-scissors",
            EX_SCISSORS_MOVE_ID,
            "强化特殊技：剪刀",
            "强化特殊技：剪刀",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1481012",
        ),
        _move(
            "ex-paper",
            EX_PAPER_MOVE_ID,
            "强化特殊技：布！",
            "强化特殊技：布！",
            SkillGroup.SPECIAL_ATTACK,
            _EX_SPECIAL,
            "伤害倍率",
            "1481013",
        ),
        _move(
            "chain-welcome-mat",
            CHAIN_WELCOME_MAT_MOVE_ID,
            "连携技：迎宾踏垫",
            "连携技：迎宾踏垫",
            SkillGroup.CHAIN_ATTACK,
            _CHAIN,
            "伤害倍率",
            "1481016",
        ),
        _move(
            "ultimate-terminate-call",
            ULTIMATE_TERMINATE_CALL_MOVE_ID,
            "终结技：拨打用户即刻停机",
            "终结技：拨打用户即刻停机",
            SkillGroup.ULTIMATE,
            _ULTIMATE,
            "伤害倍率",
            "1481017",
        ),
        _move(
            "quick-assist-transfer",
            QUICK_ASSIST_TRANSFER_MOVE_ID,
            "快速支援：呼叫转移",
            "快速支援：呼叫转移",
            SkillGroup.ASSIST,
            _ASSIST,
            "伤害倍率",
            "1481018",
        ),
        _move(
            "assist-chain-call",
            SUPPORT_FOLLOWUP_CHAIN_CALL_MOVE_ID,
            "支援突击：连环呼叫",
            "支援突击：连环呼叫",
            SkillGroup.ASSIST,
            _FOLLOW_UP,
            "伤害倍率",
            "1481022",
        ),
    )
)


__all__ = [
    "AFTER_SOUND_ACTIVE",
    "AFTER_SOUND_HIT_COUNT",
    "CHAIN_WELCOME_MAT_MOVE_ID",
    "DIALYN_EX_CINEMA6_TAGS",
    "DIALYN_EX_MOVE_IDS",
    "DIALYN_ID",
    "DIALYN_PHYSICAL_ANOMALY_RECORD_ID",
    "DIALYN_REVIEWED_MAPPING",
    "EX_PAPER_MOVE_ID",
    "EX_SCISSORS_MOVE_ID",
    "EX_STONE_MOVE_ID",
    "GOOD_REVIEW_ACTIVE",
    "MALICIOUS_COMPLAINT_ACTIVE",
    "PHYSICAL_DISORDER_REMAINING_SECONDS",
    "QUICK_ASSIST_TRANSFER_MOVE_ID",
    "ULTIMATE_TERMINATE_CALL_MOVE_ID",
]
