"""Compile Yinhu's reviewed Nanoka 3.2 source into static damage contracts."""

from __future__ import annotations

import re

from core.types import (
    CharacterRole,
    CalculationNode,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ModifierEffect,
    ModifierResult,
    NotCondition,
    PanelStatDerivedValue,
    Resolved,
    RuleStackCondition,
    RuleSource,
    SnapshotRule,
)

from ...ids import RuleItemId
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from .config import YINHU_ID, YinhuCompileConfig
from .reviewed import (
    YINHU_QI_JUE_ACTIVE,
    YINHU_REVIEWED_MAPPING,
    penetration_recipient_condition_id_for,
)


_CINEMA6_CORE_LEVEL_RULE_ID = RuleItemId(
    "rule:character:1421:cinema6:core-enhanced-selection"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _validate_raw(raw: NanokaRawRecord, config: YinhuCompileConfig) -> None:
    if raw.character_id != YINHU_ID:
        raise ValueError("raw character does not match Yinhu")
    if raw.code_name != "Yinhu" or raw.rarity != 3:
        raise ValueError("raw character identity does not match the reviewed Yinhu source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("raw Yinhu record must contain seven Core levels and six cinemas")
    required = {
        "普通攻击：极意连打",
        "冲刺攻击：热油鼎盛",
        "闪避反击：移峰倒海",
        "特殊技：爆音点穴指",
        "特殊技：断脉破穴手",
        "强化特殊技：贴山震脉靠",
        "连携技：锅气灌顶",
        "终结技：满汉全席！",
        "快速支援：抬头见喜",
        "支援突击：借势打势",
    }
    available = {item.name for item in raw.moves}
    missing = required - available
    if missing:
        raise ValueError(f"raw Yinhu record is missing reviewed moves: {sorted(missing)}")
    if not 1 <= config.core_level <= len(raw.core_levels):
        raise ValueError("configured Yinhu Core level is not available in raw source")


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(YINHU_ID, key, kind, label, text)


def _condition(condition_id, label: str, source_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=source_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1421:{key}"),
        owner=YINHU_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    recipient=None,
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1421:{key}"),
            source=source,
            owner=YINHU_ID,
            target=target,
            recipient_character_id=recipient,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _core_force(raw: NanokaRawRecord, config: YinhuCompileConfig):
    core = raw.core_levels[config.core_level - 1]
    coefficient = _number(
        core.description,
        r"初始攻击力(?P<value>[\d.]+)%的贯穿力提升",
        "Yinhu Core Penetration Force coefficient",
    ) / 100.0
    cap = _number(
        core.description,
        r"贯穿力最多不超过(?P<value>[\d.]+)点",
        "Yinhu Core Penetration Force cap",
    )
    return core, coefficient, cap


def _core_effect(
    recipient,
    coefficient: float,
    cap: float,
    source: RuleSource,
    *,
    condition=None,
    key: str | None = None,
):
    recipient_token = str(recipient).replace(":", "-")
    value = PanelStatDerivedValue(
        source_character_id=YINHU_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
        coefficient=Resolved(coefficient),
        cap_max=Resolved(cap),
    )
    return _modifier(
        key or f"core:tongqiao-penetration-force:{recipient_token}",
        source,
        CalculationNode.PENETRATION_FORCE_BONUS,
        value,
        target=EffectTarget.RECIPIENT,
        recipient=recipient,
        filters=(DamageTypeFilter(DamageType.PENETRATION),),
        condition=condition,
    )


def compile_yinhu(
    config: YinhuCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=YINHU_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=YINHU_REVIEWED_MAPPING,
        id_namespace="character:1421",
    )

    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []
    core, core_coefficient, core_cap = _core_force(raw_record, config)
    core_source = _source(
        "core-passive:tongqiao-penetration-force",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    recipient_labels = dict(config.penetration_recipient_names)
    cinema6 = raw_record.mindscapes[5]
    cinema6_source = _source(
        "cinema6:core-penetration-force",
        EffectSourceType.CINEMA,
        cinema6.name,
        cinema6.description,
    )
    cinema6_coefficient = core_coefficient + _number(
        cinema6.description,
        r"初始攻击力(?P<value>[\d.]+)%的提升",
        "Yinhu Cinema 6 Penetration Force increase",
    ) / 100.0
    cinema6_cap = _number(
        cinema6.description,
        r"最多提升至(?P<value>[\d.]+)点",
        "Yinhu Cinema 6 Penetration Force cap",
    )
    cinema6_unlocked = config.cinema_level >= 6
    rules.append(
        _rule(
            "cinema6:core-enhanced-selection",
            cinema6_source,
            "6影核心被动：通窍加强效果当前生效",
            cinema6.description,
            RuleEligibility.ELIGIBLE if cinema6_unlocked else RuleEligibility.INELIGIBLE,
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )

    for recipient in config.penetration_recipient_ids:
        recipient_condition = penetration_recipient_condition_id_for(recipient)
        recipient_label = recipient_labels.get(recipient, str(recipient))
        conditions.append(
            _condition(
                recipient_condition,
                f"{recipient_label}当前持有通窍（潘引壶初始攻击力的贯穿力加成）",
                core.description,
            )
        )
        recipient_token = str(recipient).replace(":", "-")
        base_state = (
            NotCondition(
                RuleStackCondition(
                    str(_CINEMA6_CORE_LEVEL_RULE_ID),
                    1,
                    requires_rule_enabled=True,
                )
            )
            if cinema6_unlocked
            else None
        )
        core_effects = [
            _core_effect(
                recipient,
                core_coefficient,
                core_cap,
                core_source,
                condition=base_state,
            )
        ]
        if cinema6_unlocked:
            core_effects.append(
                _core_effect(
                    recipient,
                    cinema6_coefficient,
                    cinema6_cap,
                    cinema6_source,
                    condition=RuleStackCondition(
                        str(_CINEMA6_CORE_LEVEL_RULE_ID),
                        1,
                        requires_rule_enabled=True,
                    ),
                    key=f"cinema6:tongqiao-penetration-force:{recipient_token}",
                )
            )
        rules.append(
            _rule(
                f"core:tongqiao-penetration-force:{recipient_token}",
                core_source,
                f"通窍：{recipient_label}贯穿力+{core_coefficient * 100:g}%，至多{core_cap:g}；6影时使用强化值",
                core.description,
                RuleEligibility.ELIGIBLE,
                effects=tuple(core_effects),
                condition_ids=(recipient_condition,),
            )
        )

    extra_description = core.extra_ability_description
    extra_source = _source(
        "extra-ability:qi-jue-normal-damage",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        extra_description,
    )
    extra_eligible = config.additional_ability_eligible
    extra_bonus = _number(
        extra_description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Yinhu Additional Ability target damage bonus",
    ) / 100.0
    if extra_eligible:
        conditions.append(
            _condition(
                YINHU_QI_JUE_ACTIVE,
                "当前目标处于气绝（全队普通增伤）",
                extra_description,
            )
        )
    rules.append(
        _rule(
            "extra-ability:qi-jue-normal-damage",
            extra_source,
            f"额外能力：气绝目标受到全队普通增伤{extra_bonus * 100:g}%",
            extra_description,
            RuleEligibility.ELIGIBLE if extra_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "extra-ability:qi-jue-normal-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(extra_bonus),
                    target=EffectTarget.ENEMY,
                ),
            ),
            condition_ids=(YINHU_QI_JUE_ACTIVE,) if extra_eligible else (),
        )
    )

    cinema1 = raw_record.mindscapes[0]
    c1_source = _source(
        "cinema1:qi-jue-normal-damage",
        EffectSourceType.CINEMA,
        cinema1.name,
        cinema1.description,
    )
    c1_bonus = _number(
        cinema1.description,
        r"伤害额外提升(?P<value>[\d.]+)%",
        "Yinhu Cinema 1 Qi-Jue target damage bonus",
    ) / 100.0
    c1_eligible = config.cinema_level >= 1 and extra_eligible
    rules.append(
        _rule(
            "cinema1:qi-jue-normal-damage",
            c1_source,
            f"1影：气绝目标受到全队普通增伤{c1_bonus * 100:g}%",
            cinema1.description,
            RuleEligibility.ELIGIBLE if c1_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:qi-jue-normal-damage",
                    c1_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c1_bonus),
                    target=EffectTarget.ENEMY,
                ),
            ),
            condition_ids=(YINHU_QI_JUE_ACTIVE,) if extra_eligible else (),
        )
    )

    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(
            f"cinema{level}:source-only",
            EffectSourceType.CINEMA,
            cinema.name,
            cinema.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级+2",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    return build_definition(
        character_id=YINHU_ID,
        role=CharacterRole.DEFENSE,
        element=Element.PHYSICAL,
        source=source_for(
            YINHU_ID,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        diagnostics=diagnostics,
    )


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(YINHU_ID))


__all__ = ["compile_yinhu", "load_raw_record"]
