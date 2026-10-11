"""Compile Sigrid's reviewed Nanoka live 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    AllCondition,
    AnyFilter,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NotCondition,
    EnemyStateFilter,
    Resolved,
    RuleStackCondition,
    ScenarioParameterRangeCondition,
    StateId,
    SnapshotRule,
    Unresolved,
)

from ...diagnostics import CalculationDiagnostic
from ...ids import (
    MoveEntryId,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
)
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    raw_move_index,
    source_for,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from .config import SIGRID_ID, SigridCompileConfig
from .reviewed import SIGRID_REVIEWED_MAPPING


SIGRID_SKY_RIDER_STATE_ACTIVE = ScenarioConditionId(
    "condition:character:1591:sky-rider-state-active"
)
SIGRID_CORE_CRIT_BUFF_ACTIVE = ScenarioConditionId(
    "condition:character:1591:core-crit-buff-active"
)
_ENEMY_STUNNED = StateId("state:enemy:stunned")
SIGRID_ENEMY_WINDED = ScenarioConditionId(
    "condition:character:1591:enemy-winded"
)
SIGRID_CHAIN_LANCE_BUFF_ACTIVE = ScenarioConditionId(
    "condition:character:1591:chain-lance-damage-buff-active"
)
SIGRID_CINEMA4_DAMAGE_BUFF_ACTIVE = ScenarioConditionId(
    "condition:character:1591:cinema4-sky-rider-damage-buff-active"
)
SIGRID_CINEMA1_OVERFLOW_ACTIVE = ScenarioParameterId(
    "parameter:character:1591:cinema1-overflow-charge-attack-current"
)

_CINEMA1_OVERFLOW_RULE_ID = RuleItemId(
    "rule:character:1591:cinema1:overflow-last-hit"
)
_CINEMA6_WHOLE_RATIO_RULE_ID = RuleItemId(
    "rule:character:1591:cinema6:combined-last-hit-ratio"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _raw_core(raw: NanokaRawRecord, level: int):
    if not 1 <= level <= len(raw.core_levels):
        raise ValueError("configured Core level is not available in raw source")
    return raw.core_levels[level - 1]


def _raw_cinema(raw: NanokaRawRecord, level: int):
    item = next((item for item in raw.mindscapes if item.level == level), None)
    if item is None:
        raise ValueError(f"raw source is missing Cinema {level}")
    return item


def _number(text: str, pattern: str, label: str) -> float:
    found = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(found) != 1:
        raise ValueError(f"{label} must contain one source number; found {len(found)}")
    return float(found[0].group("value"))


def _validate_raw(raw: NanokaRawRecord, config: SigridCompileConfig) -> None:
    if raw.character_id != SIGRID_ID:
        raise ValueError("raw character does not match Sigrid")
    if (
        raw.name != "希格莉德"
        or raw.code_name != "Sigrid"
        or raw.rarity != 4
        or raw.specialty != "强攻"
        or raw.element != "冰属性"
        or raw.faction != "罗斯凯利法"
        or raw.icon != "IconRole66"
    ):
        raise ValueError("raw character identity does not match reviewed Sigrid source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1591.json"
    ):
        raise ValueError("raw Sigrid provenance does not match Nanoka live3.2")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("raw Sigrid record must contain seven Core levels and six cinemas")
    source_names = {spec.source_name for spec in SIGRID_REVIEWED_MAPPING.moves}
    available = {move.name for move in raw.moves}
    missing = source_names - available
    if missing:
        raise ValueError(f"raw Sigrid record is missing reviewed moves: {sorted(missing)}")
    _raw_core(raw, config.core_level)


def _source(key: str, kind: EffectSourceType, label: str, text: str):
    return source_for(SIGRID_ID, key, kind, label, text)


def _move_filter(*keys: str):
    return AnyFilter(
        tuple(
            EventTemplateIdFilter(
                EventTemplateId(f"template:{SIGRID_ID}:{key}:main")
            )
            for key in keys
        )
    )


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    original_text: str,
    value: bool,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    key: str,
    source,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    condition_not_ids=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1591:{key}"),
        owner=SIGRID_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        condition_not_ids=tuple(condition_not_ids),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
    )


def _modifier(
    key: str,
    source,
    path: CalculationNode,
    value,
    *,
    filters=(),
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1591:{key}"),
            source=source,
            owner=SIGRID_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
            condition=condition,
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def _direct_self_scope():
    return (
        DamageDealerFilter(SIGRID_ID),
        DamageTypeFilter(DamageType.DIRECT),
    )


def _value_scope():
    return (DamageDealerFilter(SIGRID_ID),)


def _core_crit_rate(raw: NanokaRawRecord, level: int) -> float:
    description = _raw_core(raw, level).description
    value = _number(
        description,
        r"暴击率提升(?P<value>\d+(?:\.\d+)?)%",
        "Sigrid Core Crit Rate",
    )
    return value / 100.0


def compile_sigrid(
    config: SigridCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    """Compile Sigrid's authored Direct damage and static current-state effects."""

    _validate_raw(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=SIGRID_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=SIGRID_REVIEWED_MAPPING,
    )
    move_multipliers = {
        str(entry.entry_id).rsplit(":", 1)[-1]: entry.multiplier_variants[0].multiplier.value.value
        for entry in entries
        if entry.multiplier_variants
        and isinstance(entry.multiplier_variants[0].multiplier, FixedMultiplier)
        and isinstance(entry.multiplier_variants[0].multiplier.value, Resolved)
    }
    core = _raw_core(raw_record, config.core_level)
    cinemas = {level: _raw_cinema(raw_record, level) for level in range(1, 7)}
    core_source = _source(
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    cinema_sources = {
        level: _source(
            f"cinema{level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for level, item in cinemas.items()
    }

    conditions = (
        _condition(
            SIGRID_SKY_RIDER_STATE_ACTIVE,
            "当前处于[巡空枪势]状态",
            core.description,
            config.sky_rider_state_active,
        ),
        _condition(
            SIGRID_CORE_CRIT_BUFF_ACTIVE,
            "当前仍处于激活或刷新[巡空枪势]后8秒内的暴击率提升期间",
            core.description,
            config.core_crit_buff_active,
        ),
        _condition(
            SIGRID_ENEMY_WINDED,
            "目标当前处于[浸染]状态",
            core.extra_ability_description,
            config.enemy_winded,
        ),
        _condition(
            SIGRID_CHAIN_LANCE_BUFF_ACTIVE,
            "当前仍处于[连携技：冰凌卷地]后[敛枪式]伤害提升期间",
            raw_move_index(raw_record)["连携技：冰凌卷地"].description,
            config.chain_damage_buff_active,
        ),
        _condition(
            SIGRID_CINEMA4_DAMAGE_BUFF_ACTIVE,
            "当前仍处于获得[巡空枪势]后8秒内的自身伤害提升期间",
            cinemas[4].description,
            config.cinema4_damage_buff_active,
        ),
    )
    rules: list[CalculationRuleItem] = []
    direct_scope = _direct_self_scope()
    all_self_scope = _value_scope()

    core_crit = _core_crit_rate(raw_record, config.core_level)
    rules.append(
        _rule(
            "core:sky-rider-crit-rate",
            core_source,
            "核心被动：[巡空枪势]触发后的当前暴击率提升",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(SIGRID_CORE_CRIT_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:sky-rider-crit-rate",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(core_crit),
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "core:stunned-enemy-stun-vulnerability",
            core_source,
            "核心被动：[巡空枪势]期间攻击失衡目标的失衡易伤",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(SIGRID_SKY_RIDER_STATE_ACTIVE,),
            effects=(
                _modifier(
                    "core:stunned-enemy-stun-vulnerability",
                    core_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(0.20),
                    filters=(*all_self_scope, EnemyStateFilter(_ENEMY_STUNNED)),
                ),
            ),
        )
    )

    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    flat_attack = min(120.0 + 12.0 * config.character_level, 840.0)
    rules.append(
        _rule(
            "extra-ability:level-scaled-flat-attack",
            extra_source,
            "额外能力：按角色等级提升的攻击力",
            core.extra_ability_description,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:level-scaled-flat-attack",
                    extra_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    Resolved(flat_attack),
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "extra-ability:wended-target-damage",
            extra_source,
            "额外能力：攻击[浸染]目标时的当前伤害提升",
            core.extra_ability_description,
            extra_eligibility,
            condition_ids=(SIGRID_ENEMY_WINDED,),
            effects=(
                _modifier(
                    "extra-ability:wended-target-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.15),
                    filters=direct_scope,
                ),
            ),
        )
    )

    c1_text = cinemas[1].description
    rules.append(
        _rule(
            "cinema1:attack-percent",
            cinema_sources[1],
            "1影：自身攻击力提升",
            c1_text,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:attack-percent",
                    cinema_sources[1],
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    Resolved(_number(c1_text, r"自身攻击力提升(?P<value>\d+(?:\.\d+)?)%", "Sigrid Cinema 1 ATK") / 100.0),
                ),
            ),
        )
    )
    overflow_value = ScenarioIntegerParameter(
        parameter_id=SIGRID_CINEMA1_OVERFLOW_ACTIVE,
        label="当前[敛枪式]发动机会溢出，下一次敛枪式最后一击额外造成100%攻击力伤害",
        original_text=c1_text,
        resolution=ParameterResolution.USER_SELECTED,
        value=int(config.cinema1_overflow_attack_active),
        minimum=0,
        maximum=1,
    )
    c1_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 1
        else RuleEligibility.INELIGIBLE
    )
    c1_overflow_value_condition = ScenarioParameterRangeCondition(
        str(SIGRID_CINEMA1_OVERFLOW_ACTIVE), minimum=1, maximum=1
    )
    c6_enabled_condition = RuleStackCondition(
        str(_CINEMA6_WHOLE_RATIO_RULE_ID), 1, requires_rule_enabled=True
    )
    charged_stage_keys = tuple(f"basic-lance-form-stage-{stage}" for stage in range(1, 4))
    c1_overflow_effects = []
    for entry_key in charged_stage_keys:
        base_ratio = move_multipliers[entry_key]
        c1_overflow_effects.append(
            _modifier(
                f"cinema1:overflow-last-hit:{entry_key}",
                cinema_sources[1],
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                Resolved((base_ratio + 1.0) / base_ratio),
                filters=(DamageTypeFilter(DamageType.DIRECT), _move_filter(entry_key)),
                condition=(
                    AllCondition(
                        (
                            c1_overflow_value_condition,
                            NotCondition(c6_enabled_condition),
                        )
                    )
                    if config.cinema_level >= 6
                    else c1_overflow_value_condition
                ),
                operation=EffectOperation.MULTIPLY,
            )
        )
    rules.append(
        _rule(
            "cinema1:overflow-last-hit",
            cinema_sources[1],
            "1影：发动机会溢出时下一次敛枪式最后一击",
            c1_text,
            c1_eligibility,
            effects=tuple(c1_overflow_effects),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )

    c2_text = cinemas[2].description
    c2_penetration_rate = _number(
        c2_text,
        r"穿透率提升(?P<value>\d+(?:\.\d+)?)%",
        "Sigrid Cinema 2 Penetration Rate",
    ) / 100.0
    source_attack_keys = (
        "basic-fierce-spear-stage-4",
        "dodge-counter-returning-spear",
        "ex-ranqiong",
        "ex-suiyu",
        "chain-ice-curtain",
        "ultimate-frost-sky",
        "assist-strike-ice-feast",
    )
    rules.append(
        _rule(
            "cinema2:listed-attacks-penetration-rate",
            cinema_sources[2],
            "2影：[出枪式]与[敛枪式]穿透率提升",
            c2_text,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:listed-attacks-penetration-rate",
                    cinema_sources[2],
                    CalculationNode.DAMAGE_PENETRATION_RATE,
                    Resolved(c2_penetration_rate),
                    filters=(
                        *direct_scope,
                        ElementFilter(Element.ICE),
                        _move_filter(*source_attack_keys, *charged_stage_keys),
                    ),
                ),
            ),
        )
    )

    c4_text = cinemas[4].description
    c4_bonus = _number(
        c4_text,
        r"自身造成的伤害提升(?P<value>\d+(?:\.\d+)?)%",
        "Sigrid Cinema 4 Damage Bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema4:sky-rider-damage-bonus",
            cinema_sources[4],
            "4影：当前[巡空枪势]后的自身伤害提升",
            c4_text,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            condition_ids=(SIGRID_CINEMA4_DAMAGE_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "cinema4:sky-rider-damage-bonus",
                    cinema_sources[4],
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c4_bonus),
                    filters=direct_scope,
                ),
            ),
        )
    )

    c6_text = cinemas[6].description
    c6_match = re.search(
        r"最后一击命中敌人时，额外造成(?P<first>\d+(?:\.\d+)?)%/(?P<second>\d+(?:\.\d+)?)%/(?P<third>\d+(?:\.\d+)?)%攻击力",
        _plain(c6_text),
    )
    if c6_match is None:
        raise ValueError("Sigrid Cinema 6 must list all three final-hit ATK ratios")
    c6_deltas = tuple(
        float(c6_match.group(key)) / 100.0
        for key in ("first", "second", "third")
    )
    stage_deltas = dict(zip(charged_stage_keys, c6_deltas))
    c1_overflow_rule_condition = RuleStackCondition(
        str(_CINEMA1_OVERFLOW_RULE_ID), 1, requires_rule_enabled=True
    )
    c1_and_overflow_active = AllCondition(
        (
            c1_overflow_value_condition,
            c1_overflow_rule_condition,
        )
    )
    c6_effects = []
    for entry_key in charged_stage_keys:
        base_ratio = move_multipliers[entry_key]
        c6_bonus = stage_deltas[entry_key]
        c6_effects.extend(
            (
                _modifier(
                    f"cinema6:last-hit-only:{entry_key}",
                    cinema_sources[6],
                    CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                    Resolved((base_ratio + c6_bonus) / base_ratio),
                    filters=(DamageTypeFilter(DamageType.DIRECT), _move_filter(entry_key)),
                    condition=NotCondition(c1_and_overflow_active),
                    operation=EffectOperation.MULTIPLY,
                ),
                _modifier(
                    f"cinema6:combined-overflow-last-hit:{entry_key}",
                    cinema_sources[6],
                    CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                    Resolved((base_ratio + c6_bonus + 1.0) / base_ratio),
                    filters=(DamageTypeFilter(DamageType.DIRECT), _move_filter(entry_key)),
                    condition=c1_and_overflow_active,
                    operation=EffectOperation.MULTIPLY,
                ),
            )
        )
    rules.append(
        _rule(
            "cinema6:combined-last-hit-ratio",
            cinema_sources[6],
            "6影：敛枪式最后一击追加冰伤（与1影溢出合并为同一倍率）",
            c6_text,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            effects=tuple(c6_effects),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )

    chain_buff_text = raw_move_index(raw_record)["连携技：冰凌卷地"].description
    chain_source = _source(
        "chain-lance-current-buff",
        EffectSourceType.SKILL,
        "连携技：冰凌卷地",
        chain_buff_text,
    )
    chain_buff_bonus = _number(
        chain_buff_text,
        r"使后续\[普通攻击：敛枪式\]造成的伤害提升(?P<value>\d+(?:\.\d+)?)%",
        "Sigrid Chain Lance Damage Bonus",
    ) / 100.0
    rules.append(
        _rule(
            "chain:current-lance-damage-bonus",
            chain_source,
            "当前[连携技：冰凌卷地]后的敛枪式伤害提升",
            chain_buff_text,
            RuleEligibility.ELIGIBLE,
            condition_ids=(SIGRID_CHAIN_LANCE_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "chain:current-lance-damage-bonus",
                    chain_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(chain_buff_bonus),
                    filters=(
                        *direct_scope,
                        _move_filter(*charged_stage_keys),
                    ),
                ),
            ),
        )
    )

    parameters = (overflow_value,) if config.cinema_level >= 1 else ()
    return build_definition(
        character_id=SIGRID_ID,
        role=CharacterRole.ATTACK,
        element=Element.ICE,
        source=source_for(
            SIGRID_ID,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


__all__ = [
    "SIGRID_SKY_RIDER_STATE_ACTIVE",
    "SIGRID_CORE_CRIT_BUFF_ACTIVE",
    "SIGRID_ENEMY_WINDED",
    "SIGRID_CHAIN_LANCE_BUFF_ACTIVE",
    "SIGRID_CINEMA4_DAMAGE_BUFF_ACTIVE",
    "SIGRID_CINEMA1_OVERFLOW_ACTIVE",
    "compile_sigrid",
]
