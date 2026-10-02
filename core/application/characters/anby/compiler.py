"""Compile the reviewed Nanoka Anby source into calculation contracts."""

from __future__ import annotations

import re

from core.types import (
    AllCondition,
    AnyCondition,
    AnyFilter,
    CalculationNode,
    CharacterRole,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageSubtype,
    DynamicIdentity,
    DynamicIdentityCondition,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EnemyStateFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveIdFilter,
    NoCritRule,
    NotFilter,
    RuleStackCondition,
    Resolved,
    RuleSource,
    SnapshotRule,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import (
    DamageEventSemanticId,
    DiagnosticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioParameterId,
)
from ...moves import (
    DamageEventTemplateRef as MoveDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import AnbyCompileConfig
from .reviewed import (
    AFTER_BASIC_THIRD_ACTIVE,
    ANBY_ELECTRIC_ANOMALY_MOVE_ID,
    ANBY_ELECTRIC_ANOMALY_RECORD_ID,
    ANBY_ELECTRIC_DISORDER_MOVE_ID,
    ANBY_ID,
    ANBY_REVIEWED_MAPPING,
    ANBY_ENEMY_STUNNED_STATE_ID,
    BASIC_FALLING_THUNDER_MOVE_ID,
    CINEMA1_ENERGY_EFFICIENCY_ACTIVE,
    EX_SPECIAL_COBALT_LIGHTNING_MOVE_ID,
    SPECIAL_ELECTRIC_SLASH_MOVE_ID,
)


_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:anby:electric-disorder-remaining-seconds"
)


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    effects=(),
    *,
    condition_ids=(),
    condition_not_ids=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1011:{key}"),
        owner=ANBY_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        condition_not_ids=tuple(condition_not_ids),
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    filters=(),
    condition=None,
    target: EffectTarget = EffectTarget.SELF,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1011:{key}"),
            source=source,
            owner=ANBY_ID,
            target=target,
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


def _diagnostic(
    key: str,
    message: str,
    original_text: str,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1011:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_electric_entries():
    anomaly_ref = MoveDamageEventTemplateRef(
        template_id="template:character:1011:electric-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1011:electric-anomaly"),
        label="属性异常：感电（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=ANBY_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=ANBY_ID,
        history_record_source=ANBY_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ANBY_ELECTRIC_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1011:electric-anomaly"),
        character_id=ANBY_ID,
        move_id=ANBY_ELECTRIC_ANOMALY_MOVE_ID,
        display_name="属性异常：感电（10秒满异常）",
        original_text=(
            "静态单人100%积蓄记录按权威规范结算感电：每秒125%异常效果强度，"
            "10秒共10跳，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1011:electric-anomaly-tick"
                ),
                label="感电单跳125%（10秒10跳）",
                parameter_name="感电单跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = MoveDamageEventTemplateRef(
        template_id="template:character:1011:electric-disorder",
        semantic_id=DamageEventSemanticId("event:character:1011:electric-disorder"),
        label="紊乱：感电（剩余时间补偿）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ANBY_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=ANBY_ID,
        history_record_source=ANBY_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ANBY_ELECTRIC_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1011:electric-disorder"),
        character_id=ANBY_ID,
        move_id=ANBY_ELECTRIC_DISORDER_MOVE_ID,
        display_name="紊乱：感电（默认最大剩余时间）",
        original_text=(
            "感电紊乱倍率按规范为450% + floor(t)×125%；剩余时间由用户输入，"
            "默认10秒，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1011:electric-disorder"),
                label="450% + floor(t) × 125%",
                parameter_name="感电紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.25,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining_seconds = ScenarioIntegerParameter(
        parameter_id=_DISORDER_REMAINING_SECONDS,
        label="感电紊乱时目标剩余持续时间（秒）",
        original_text="静态满异常按电异常10秒持续时间；本次紊乱剩余时间单独输入，不从触发时机推断。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        remaining_seconds,
    )


def compile_anby(
    config: AnbyCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=ANBY_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=ANBY_REVIEWED_MAPPING,
        id_namespace="character:1011",
    )
    static_entries, static_templates, remaining_seconds = _static_electric_entries()
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        ANBY_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_match = re.search(
        r"失衡值提升<color=[^>]+>(?P<value>[\d.]+)%</color>",
        core.description,
    )
    if core_match is None:
        raise ValueError("Anby core source is missing the Daze coefficient")
    core_daze_bonus = float(core_match.group("value")) / 100.0

    conditions = (
        _condition(
            AFTER_BASIC_THIRD_ACTIVE,
            "安比当前处于普攻三段后的衔接状态",
            "核心被动：安比在普通攻击第三段后发动落雷、特殊技或强化特殊技",
        ),
        _condition(
            CINEMA1_ENERGY_EFFICIENCY_ACTIVE,
            "当前处于1影能量获得效率增益",
            "1影：普通攻击第四段命中后，安比能量获得效率提升12%，持续30秒",
        ),
    )

    daze_result_diagnostic = _diagnostic(
        "daze-result-unavailable",
        "Anby's Nanoka raw record contains distinct Daze-ratio curves and the reviewed core/Cinema Daze modifiers. The current calculation request has no Daze result field, so these values remain traced as Daze modifiers and do not change damage totals.",
        core.description,
    )
    resource_diagnostic = _diagnostic(
        "energy-results-unavailable",
        "The additional-ability one-shot Energy restore is preserved as a source rule. The request has no Energy resource result.",
        raw_record.extra_ability_description,
    )

    rules: list[CalculationRuleItem] = []

    rules.append(
        _rule(
            "core:daze-after-basic-third",
            core_source,
            f"核心被动：{core.name}·衔接招式失衡值提升",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(AFTER_BASIC_THIRD_ACTIVE,),
            effects=(
                _modifier(
                    "core:daze-after-basic-third",
                    core_source,
                    CalculationNode.DAZE_OUTGOING_BONUS,
                    Resolved(core_daze_bonus),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    target=EffectTarget.TEAM,
                    filters=(
                        AnyFilter(
                            (
                                MoveIdFilter(BASIC_FALLING_THUNDER_MOVE_ID),
                                MoveIdFilter(SPECIAL_ELECTRIC_SLASH_MOVE_ID),
                                MoveIdFilter(EX_SPECIAL_COBALT_LIGHTNING_MOVE_ID),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    if config.additional_ability_eligible:
        rules.append(
            _rule(
                "extra-ability:counter-energy-restore-source-only",
                source_for(
                    ANBY_ID,
                    "extra-ability",
                    EffectSourceType.CORE_PASSIVE,
                    core.extra_ability_name,
                    core.extra_ability_description,
                ),
                f"额外能力：{core.extra_ability_name}·闪避反击能量回复",
                core.extra_ability_description,
                RuleEligibility.ELIGIBLE,
                diagnostics=(resource_diagnostic,),
            )
        )
    else:
        rules.append(
            _rule(
                "extra-ability:counter-energy-restore-source-only",
                source_for(
                    ANBY_ID,
                    "extra-ability",
                    EffectSourceType.CORE_PASSIVE,
                    core.extra_ability_name,
                    core.extra_ability_description,
                ),
                f"额外能力：{core.extra_ability_name}·闪避反击能量回复",
                core.extra_ability_description,
                RuleEligibility.INELIGIBLE,
                diagnostics=(resource_diagnostic,),
            )
        )

    cinema_sources = []
    for level in range(1, 7):
        mindscape = next(item for item in raw_record.mindscapes if item.level == level)
        cinema_source = source_for(
            ANBY_ID,
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            f"{level}影：{mindscape.name}",
            mindscape.description,
        )
        cinema_sources.append((mindscape, cinema_source))
        eligible = (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= level
            else RuleEligibility.INELIGIBLE
        )
        if level == 1:
            c1_energy_diagnostic = _diagnostic(
                "cinema1-energy-gain-efficiency-result-unavailable",
                "Energy Gain Efficiency is preserved as a current-state source effect. The request has no Energy resource result, so it is not approximated as Energy Regeneration.",
                mindscape.description,
            )
            rules.append(
                _rule(
                    "cinema1:energy-gain-efficiency-source-only",
                    cinema_source,
                    f"1影：{mindscape.name}·能量获得效率",
                    mindscape.description,
                    eligible,
                    condition_ids=(CINEMA1_ENERGY_EFFICIENCY_ACTIVE,),
                    diagnostics=(c1_energy_diagnostic,),
                )
            )
        elif level == 2:
            rules.extend(
                (
                    _rule(
                        "cinema2:falling-thunder-damage-vs-stunned",
                        cinema_source,
                        f"2影：{mindscape.name}·落雷对失衡目标伤害提升",
                        mindscape.description,
                        eligible,
                        effects=(
                            _modifier(
                                "cinema2:falling-thunder-damage-vs-stunned",
                                cinema_source,
                                CalculationNode.DAMAGE_NORMAL_BONUS,
                                Resolved(0.30),
                                filters=(
                                    MoveIdFilter(BASIC_FALLING_THUNDER_MOVE_ID),
                                    EnemyStateFilter(ANBY_ENEMY_STUNNED_STATE_ID),
                                ),
                                condition=DynamicIdentityCondition(
                                    DynamicIdentity.DAMAGE_DEALER
                                ),
                                target=EffectTarget.TEAM,
                            ),
                        ),
                    ),
                    _rule(
                        "cinema2:ex-special-daze-vs-not-stunned",
                        cinema_source,
                        f"2影：{mindscape.name}·强化特殊技对未失衡目标失衡值提升",
                        mindscape.description,
                        eligible,
                        effects=(
                            _modifier(
                                "cinema2:ex-special-daze-vs-not-stunned",
                                cinema_source,
                                CalculationNode.DAZE_OUTGOING_BONUS,
                                Resolved(0.10),
                                filters=(
                                    MoveIdFilter(EX_SPECIAL_COBALT_LIGHTNING_MOVE_ID),
                                    NotFilter(
                                        EnemyStateFilter(ANBY_ENEMY_STUNNED_STATE_ID)
                                    ),
                                ),
                                target=EffectTarget.TEAM,
                                condition=DynamicIdentityCondition(
                                    DynamicIdentity.DAMAGE_DEALER
                                ),
                            ),
                        ),
                    ),
                )
            )
        elif level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    cinema_source,
                    f"{level}影：{mindscape.name}·技能等级",
                    mindscape.description,
                    eligible,
                )
            )
        elif level == 4:
            c4_energy_diagnostic = _diagnostic(
                "cinema4-energy-restore-result-unavailable",
                "The Chain/Ultimate Energy restoration and its Efficiency-based increase are preserved in the source text. The request has no Energy resource result, so no recovery amount is fabricated.",
                mindscape.description,
            )
            rules.append(
                _rule(
                    "cinema4:backline-electric-energy-source-only",
                    cinema_source,
                    f"4影：{mindscape.name}·后场电属性角色能量回复",
                    mindscape.description,
                    eligible,
                    diagnostics=(c4_energy_diagnostic,),
                )
            )
        elif level == 6:
            stack_rule = _rule(
                "cinema6:charge-stacks",
                cinema_source,
                f"6影：{mindscape.name}·当前充能层数",
                mindscape.description,
                eligible,
                stack_count=0,
                stack_min=0,
                stack_max=8,
                diagnostics=(
                    _diagnostic(
                        "cinema6-charge-timing",
                        "The 0–8 current charges are an explicit pre-hit state. The EX Special trigger and per-hit consumption are not replayed.",
                        mindscape.description,
                    ),
                ),
            )
            stack_id = str(stack_rule.rule_id)
            positive_stack = AnyCondition(
                tuple(
                    RuleStackCondition(stack_id, count)
                    for count in range(1, 9)
                )
            )
            damage_rule = _rule(
                "cinema6:basic-dash-damage-bonus",
                cinema_source,
                f"6影：{mindscape.name}·普通攻击/冲刺攻击增伤",
                mindscape.description,
                eligible,
                effects=(
                    _modifier(
                        "cinema6:basic-dash-damage-bonus",
                        cinema_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(0.45),
                        filters=(
                            AnyFilter(
                                (
                                    DamageTagFilter(DamageTag.BASIC_ATTACK),
                                    DamageTagFilter(DamageTag.DASH_ATTACK),
                                )
                            ),
                        ),
                        condition=AllCondition(
                            (
                                DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                                positive_stack,
                            )
                        ),
                        target=EffectTarget.TEAM,
                    ),
                ),
            )
            rules.extend((stack_rule, damage_rule))

    return build_definition(
        character_id=ANBY_ID,
        role=CharacterRole.STUN,
        element=Element.ELECTRIC,
        source=core_source,
        entries=(*direct_entries, *static_entries),
        templates=(*direct_templates, *static_templates),
        rules=rules,
        conditions=conditions,
        parameters=(remaining_seconds,),
        diagnostics=(*direct_diagnostics, daze_result_diagnostic),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: AnbyCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "安比" or raw.code_name != "Anby":
        raise ValueError("unexpected character identity in raw Anby record")
    if raw.specialty != "击破" or raw.element != "电属性":
        raise ValueError("Anby raw role or element does not match reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Anby raw source must contain all seven cores and six cinemas")


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(ANBY_ID))


__all__ = [
    "ANBY_ELECTRIC_ANOMALY_MOVE_ID",
    "ANBY_ELECTRIC_ANOMALY_RECORD_ID",
    "compile_anby",
    "load_raw_record",
]
