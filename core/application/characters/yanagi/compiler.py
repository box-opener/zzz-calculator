"""Compile Yanagi's reviewed live Nanoka 3.2 character source."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CreatedByEffectFilter,
    DamageDealerFilter,
    DamageTag,
    DamageSubtype,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    DynamicIdentity,
    DynamicIdentityCondition,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    ScenarioParameterRangeCondition,
    SnapshotRule,
    SkillGroup,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import (
    DamageEventSemanticId,
    DiagnosticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
)
from ...moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
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
    effective_skill_level,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
    PolarDisorderDamageEventTemplate,
)
from .config import YanagiCompileConfig
from .reviewed import (
    ASSIST_STRIKE_FLYING_THISTLE_MOVE_ID,
    BASIC_LOWER_MOVE_ID,
    BASIC_UPPER_MOVE_ID,
    CHAIN_STAR_AND_MOON_MOVE_ID,
    DASH_ATTACK_MOVE_ID,
    DODGE_COUNTER_MOVE_ID,
    EX_SPECIAL_MOONLIT_FLOW_MOVE_ID,
    POLARITY_TARGET_HAS_ACTIVE_ANOMALY,
    QUICK_ASSIST_FLOWER_SLASH_MOVE_ID,
    SPECIAL_FLOWING_TURN_MOVE_ID,
    ULTIMATE_THUNDER_SHADOW_MOVE_ID,
    YANAGI_ELECTRIC_ANOMALY_RECORD_ID,
    YANAGI_ID,
    YANAGI_REVIEWED_MAPPING,
)


INSIGHT_STACKS = ScenarioParameterId("parameter:yanagi:insight-stacks")
EX_SPECIAL_EXTRA_THRUSTS = ScenarioParameterId(
    "parameter:yanagi:ex-special-extra-thrusts"
)
UPPER_STANCE_ELECTRIC_BONUS_ACTIVE = ScenarioConditionId(
    "condition:yanagi:upper-stance-electric-bonus-active"
)
LOWER_STANCE_PENETRATION_BONUS_ACTIVE = ScenarioConditionId(
    "condition:yanagi:lower-stance-penetration-bonus-active"
)
EX_SPECIAL_ELECTRIC_DAMAGE_ACTIVE = ScenarioConditionId(
    "condition:yanagi:ex-special-electric-damage-active"
)
CORE_DISORDER_MULTIPLIER_ACTIVE = ScenarioConditionId(
    "condition:yanagi:core-disorder-multiplier-active"
)
ENEMY_INSIGHT_ACTIVE = ScenarioConditionId("condition:yanagi:enemy-insight-active")
FOREST_ILLUMINATION_ACTIVE = ScenarioConditionId(
    "condition:yanagi:forest-illumination-active"
)
_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:yanagi:electric-disorder-remaining-seconds"
)


def _raw_number(text: str, expression: str, label: str) -> float:
    matches = tuple(re.finditer(expression, text, re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{label} must contain one reviewed numeric value")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str, value: bool = False):
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility = RuleEligibility.ELIGIBLE,
    *,
    condition_ids=(),
    effects=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1221:{key}"),
        owner=YANAGI_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        effects=tuple(effects),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1221:{key}"),
            source=source,
            owner=YANAGI_ID,
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


def _event_creation(
    key: str,
    source: RuleSource,
    template: DamageEventTemplateRef,
    filters,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1221:{key}"),
            source=source,
            owner=YANAGI_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template.template_id,
            unique_per_source_event=True,
        ),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(YANAGI_ID))


def _validate_raw(raw: NanokaRawRecord, config: YanagiCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Yanagi raw record and compile config IDs must match")
    if raw.name != "柳" or raw.code_name != "Yanagi":
        raise ValueError("unexpected identity in Yanagi raw record")
    if raw.specialty != "异常" or raw.element != "电属性" or raw.rarity != 4:
        raise ValueError("Yanagi source specialty, element, or rank changed")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Yanagi source must include seven cores and six cinemas")
    if raw.potential_details:
        raise ValueError("Yanagi live source unexpectedly contains Potential variants")


def _static_electric_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1221:electric-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1221:electric-anomaly"),
        label="属性异常：感电（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=YANAGI_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=YANAGI_ID,
        history_record_source=YANAGI_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=MoveId("move:yanagi:electric-anomaly"),
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1221:electric-anomaly"),
        character_id=YANAGI_ID,
        move_id=MoveId("move:yanagi:electric-anomaly"),
        display_name="属性异常：感电（10秒满异常）",
        original_text=(
            "按规范100%单人积蓄感电：10秒剩余持续时间，每跳125%异常效果强度，"
            "共10跳，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1221:electric-anomaly-tick"
                ),
                label="感电每跳125%（10秒10跳）",
                parameter_name="感电每跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1221:electric-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1221:electric-disorder"),
        label="紊乱：感电（当前选定剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=YANAGI_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=YANAGI_ID,
        history_record_source=YANAGI_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=MoveId("move:yanagi:electric-disorder"),
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1221:electric-disorder"),
        character_id=YANAGI_ID,
        move_id=MoveId("move:yanagi:electric-disorder"),
        display_name="紊乱：感电",
        original_text=(
            "按规范紊乱倍率450% + floor(t)×125%；剩余时间单独选择0–10秒，"
            "默认10秒，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1221:electric-disorder"),
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
        original_text="按规范范围0–10秒；静态默认最大10秒，不模拟触发时序。",
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


def compile_yanagi(
    config: YanagiCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=YANAGI_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=YANAGI_REVIEWED_MAPPING,
        id_namespace="character:1221",
    )
    entries = list(direct_entries)

    raw_moves = {item.name: item for item in raw_record.moves}
    ex_raw = raw_moves["强化特殊技：月华流转"]
    ex_downfall_parameter = next(
        item for item in ex_raw.parameters if item.name == "下落攻击伤害倍率"
    )
    if ex_downfall_parameter.main is None or ex_downfall_parameter.growth is None:
        raise ValueError("Yanagi raw EX Downfall curve is missing")
    ex_level = effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    ex_downfall_multiplier = (
        ex_downfall_parameter.main
        + ex_downfall_parameter.growth * (ex_level - 1)
    ) / 10000.0
    ex_entry = next(
        item
        for item in entries
        if str(item.entry_id)
        == "move-entry:character:1221:ex-special-moonlit-flow-thrust"
    )
    ex_main_template = next(
        item
        for item in direct_templates
        if item.ref.template_id == ex_entry.main_damage_event.template_id
    )
    ex_downfall_ref = replace(
        ex_main_template.ref,
        template_id=EventTemplateId(
            "template:character:1221:ex-special-moonlit-flow-downfall"
        ),
        semantic_id=DamageEventSemanticId(
            "event:character:1221:ex-special-moonlit-flow-downfall"
        ),
        label="强化特殊技：月华流转（下落攻击）",
        source_rule_item_id=RuleItemId(
            "rule:character:1221:ex-special:downfall-component"
        ),
    )
    ex_downfall_template = replace(ex_main_template, ref=ex_downfall_ref)
    ex_downfall_derived = DerivedDamageEventTemplateRef(
        template=ex_downfall_ref,
        multiplier=FixedMultiplier(Resolved(ex_downfall_multiplier)),
    )
    ex_extra_thrust_template = None
    ex_extra_thrust_derived = None
    ex_extra_thrust_ref = None
    if config.cinema_level >= 2:
        ex_thrust_variant = ex_entry.multiplier_variants[0]
        ex_extra_thrust_ref = replace(
            ex_main_template.ref,
            template_id=EventTemplateId(
                "template:character:1221:ex-special-extra-thrust"
            ),
            semantic_id=DamageEventSemanticId(
                "event:character:1221:ex-special-extra-thrust"
            ),
            label="强化特殊技：月华流转（额外突刺）",
            source_rule_item_id=RuleItemId(
                "rule:character:1221:ex-special:extra-thrusts"
            ),
        )
        ex_extra_thrust_template = replace(ex_main_template, ref=ex_extra_thrust_ref)
        ex_extra_thrust_derived = DerivedDamageEventTemplateRef(
            template=ex_extra_thrust_ref,
            multiplier=ex_thrust_variant.multiplier,
            repeat_count=1,
            repeat_count_parameter_id=EX_SPECIAL_EXTRA_THRUSTS,
            skip_when_repeat_count_zero=True,
        )

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        YANAGI_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra_source = source_for(
        YANAGI_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    cinema_sources = {
        item.level: source_for(
            YANAGI_ID,
            f"cinema{item.level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for item in raw_record.mindscapes
    }
    upper_text = raw_moves["架势：上弦"].description
    lower_text = raw_moves["架势：下弦"].description
    disorder_bonus = _raw_number(
        core.description,
        r"紊乱.*?伤害倍率提升<color=[^>]+>(?P<value>[\d.]+)%",
        "Yanagi Core Disorder multiplier increase",
    ) / 100.0
    electric_bonus = _raw_number(
        core.description,
        r"对目标造成的<color=[^>]+>电属性伤害</color>提升<color=[^>]+>(?P<value>[\d.]+)%",
        "Yanagi EX target Electric damage bonus",
    ) / 100.0

    upper_condition = _condition(
        UPPER_STANCE_ELECTRIC_BONUS_ACTIVE,
        "当前保有上弦架势增益",
        upper_text,
    )
    lower_condition = _condition(
        LOWER_STANCE_PENETRATION_BONUS_ACTIVE,
        "当前保有下弦架势增益",
        lower_text,
    )
    ex_electric_condition = _condition(
        EX_SPECIAL_ELECTRIC_DAMAGE_ACTIVE,
        "当前保有强化特殊技命中后的电属性增伤",
        core.description,
    )
    disorder_condition = _condition(
        CORE_DISORDER_MULTIPLIER_ACTIVE,
        "当前保有强化特殊技后的紊乱倍率提升",
        core.description,
    )
    insight_condition = _condition(
        ENEMY_INSIGHT_ACTIVE,
        "目标当前处于识破状态",
        next(
            item.description
            for item in raw_record.mindscapes
            if item.level == 4
        ),
    )
    forest_illumination = _condition(
        FOREST_ILLUMINATION_ACTIVE,
        "森罗万象状态当前生效",
        next(item.description for item in raw_record.mindscapes if item.level == 6),
    )
    insight_stacks = ScenarioIntegerParameter(
        parameter_id=INSIGHT_STACKS,
        label="当前洞悉层数",
        original_text=raw_record.mindscapes[0].description,
        resolution=ParameterResolution.USER_SELECTED,
        value=3 if config.cinema_level >= 1 else 0,
        minimum=0,
        maximum=3,
    )
    ex_extra_thrusts = (
        ScenarioIntegerParameter(
            parameter_id=EX_SPECIAL_EXTRA_THRUSTS,
            label="强化特殊技额外突刺次数",
            original_text=(
                "2影解锁的强化特殊技快速突刺可长按再次发动，每次额外消耗10点能量；"
                "显式选择本次招式的额外突刺次数，不模拟能量变化或操作时间。"
            ),
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=None,
        )
        if config.cinema_level >= 2
        else None
    )
    disorder_remaining = ScenarioIntegerParameter(
        parameter_id=_DISORDER_REMAINING_SECONDS,
        label="当前感电紊乱剩余时间（秒）",
        original_text="规范范围0–10秒；按静态最大剩余时间默认10秒，不模拟时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    polarity_target_condition = _condition(
        POLARITY_TARGET_HAS_ACTIVE_ANOMALY,
        "目标当前处于属性异常状态",
        (
            raw_moves["强化特殊技：月华流转"].description
            + "\n"
            + raw_moves["终结技：雷影天华"].description
        ),
    )

    rules: list[CalculationRuleItem] = []
    rules.extend(
        (
            _rule(
                "basic:upper-stance-electric-bonus",
                source_for(YANAGI_ID, "basic-upper-stance", EffectSourceType.SKILL, "架势：上弦", upper_text),
                "上弦：电属性伤害提升10%",
                upper_text,
                effects=(
                    _modifier(
                        "basic:upper-stance-electric-bonus",
                        source_for(YANAGI_ID, "basic-upper-stance", EffectSourceType.SKILL, "架势：上弦", upper_text),
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(0.10),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageDealerFilter(YANAGI_ID),
                            ElementFilter(Element.ELECTRIC),
                        ),
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    ),
                ),
                condition_ids=(UPPER_STANCE_ELECTRIC_BONUS_ACTIVE,),
            ),
            _rule(
                "basic:lower-stance-penetration-bonus",
                source_for(YANAGI_ID, "basic-lower-stance", EffectSourceType.SKILL, "架势：下弦", lower_text),
                "下弦：穿透率提升10%",
                lower_text,
                effects=(
                    _modifier(
                        "basic:lower-stance-penetration-bonus",
                        source_for(YANAGI_ID, "basic-lower-stance", EffectSourceType.SKILL, "架势：下弦", lower_text),
                        CalculationNode.DAMAGE_PENETRATION_RATE,
                        Resolved(0.10),
                        target=EffectTarget.SELF,
                        filters=(DamageDealerFilter(YANAGI_ID),),
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    ),
                ),
                condition_ids=(LOWER_STANCE_PENETRATION_BONUS_ACTIVE,),
            ),
        )
    )
    c1_source = cinema_sources[1]
    rules.append(
        _rule(
            "cinema1:insight-proficiency",
            c1_source,
            "1影：洞悉提升异常精通80点",
            raw_record.mindscapes[0].description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:insight-proficiency",
                    c1_source,
                    CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                    Resolved(80.0),
                    target=EffectTarget.SELF,
                    condition=ScenarioParameterRangeCondition(
                        parameter_id=str(INSIGHT_STACKS),
                        minimum=1,
                    ),
                ),
            ),
        )
    )
    c4_source = cinema_sources[4]
    rules.append(
        _rule(
            "cinema4:insight-penetration-rate",
            c4_source,
            "4影：识破期间攻击穿透率提升16%",
            raw_record.mindscapes[3].description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:insight-penetration-rate",
                    c4_source,
                    CalculationNode.DAMAGE_PENETRATION_RATE,
                    Resolved(0.16),
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(ENEMY_INSIGHT_ACTIVE,),
        )
    )
    c6_source = cinema_sources[6]
    c6_extra_text = raw_record.mindscapes[5].description
    c6_ex_damage_bonus = _raw_number(
        c6_extra_text,
        r"\[强化特殊技\]</color>造成的伤害提升(?P<value>[\d.]+)%",
        "Yanagi Cinema 6 EX Special damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema6:ex-special-damage-bonus",
            c6_source,
            f"6影：森罗万象期间强化特殊技伤害+{c6_ex_damage_bonus * 100:g}%",
            c6_extra_text,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema6:ex-special-damage-bonus",
                    c6_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c6_ex_damage_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(YANAGI_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                    ),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                ),
            ),
            condition_ids=(FOREST_ILLUMINATION_ACTIVE,),
        )
    )
    core_electric_source = source_for(
        YANAGI_ID,
        "core-electric-damage",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    rules.append(
        _rule(
            "core:ex-special-electric-damage",
            core_electric_source,
            f"核心：强化特殊技命中后电伤+{electric_bonus * 100:g}%",
            core.description,
            effects=(
                _modifier(
                    "core:ex-special-electric-damage",
                    core_electric_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(electric_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(YANAGI_ID),
                        ElementFilter(Element.ELECTRIC),
                    ),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                ),
            ),
            condition_ids=(EX_SPECIAL_ELECTRIC_DAMAGE_ACTIVE,),
        )
    )
    core_disorder_source = source_for(
        YANAGI_ID,
        "core-disorder-multiplier",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    rules.append(
        _rule(
            "core:disorder-multiplier",
            core_disorder_source,
            f"核心：紊乱额外倍率+{disorder_bonus * 100:g}%",
            core.description,
            effects=(
                _modifier(
                    "core:disorder-multiplier",
                    core_disorder_source,
                    CalculationNode.DISORDER_EXTRA_MULTIPLIER,
                    Resolved(disorder_bonus),
                    target=EffectTarget.TEAM,
                    filters=(DamageTypeFilter(DamageType.DISORDER),),
                ),
            ),
            condition_ids=(CORE_DISORDER_MULTIPLIER_ACTIVE,),
        )
    )
    extra_diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1221:extra-ability-buildup"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=(
            "The source grants +45% Electric anomaly buildup to qualifying Basic hits "
            "after a stance switch; the current result contract does not output buildup "
            "or replay stance-switch timing."
        ),
        blocking=False,
        original_text=core.extra_ability_description,
    )
    rules.append(
        _rule(
            "extra-ability:basic-electric-buildup",
            extra_source,
            "额外能力：架势切换后普攻三段提升电异常积蓄",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            diagnostics=(extra_diagnostic,),
        )
    )
    for level in (3, 5):
        mindscape = raw_record.mindscapes[level - 1]
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                cinema_sources[level],
                f"{level}影：技能等级",
                mindscape.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    ex_downfall_source = source_for(
        YANAGI_ID,
        "ex-special-downfall-component",
        EffectSourceType.SPECIAL_MECHANISM,
        "强化特殊技：月华流转（下落攻击）",
        raw_moves["强化特殊技：月华流转"].description,
    )
    ex_downfall_creation = _event_creation(
        "ex-special:downfall-component",
        ex_downfall_source,
        ex_downfall_ref,
        filters=(
            DamageDealerFilter(YANAGI_ID),
            DamageTypeFilter(DamageType.DIRECT),
            EventTemplateIdFilter(ex_main_template.ref.template_id),
        ),
    )
    rules.append(
        _rule(
            "ex-special:downfall-component",
            ex_downfall_source,
            "强化特殊技：月华流转的下落攻击",
            raw_moves["强化特殊技：月华流转"].description,
            RuleEligibility.ELIGIBLE,
            effects=(ex_downfall_creation,),
        )
    )
    ex_downfall_entry = next(
        item
        for item in direct_entries
        if str(item.entry_id)
        == "move-entry:character:1221:ex-special-moonlit-flow-downfall"
    )
    ex_downfall_direct_template = next(
        item
        for item in direct_templates
        if item.ref.template_id == ex_downfall_entry.main_damage_event.template_id
    )
    ex_polarity_source = source_for(
        YANAGI_ID,
        "ex-special-polarity-disorder",
        EffectSourceType.SPECIAL_MECHANISM,
        "强化特殊技：月华流转（极性紊乱）",
        raw_moves["强化特殊技：月华流转"].description,
    )
    ex_polarity_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1221:ex-special:polarity-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1221:ex-special:polarity-disorder"),
        label="强化特殊技：极性紊乱",
        damage_type=DamageType.DISORDER,
        element=None,
        source_rule_item_id=RuleItemId("rule:character:1221:ex-special:polarity-disorder"),
    )
    ex_polarity_template = PolarDisorderDamageEventTemplate(
        ref=ex_polarity_ref,
        damage_dealer=YANAGI_ID,
        disorder_triggerer=YANAGI_ID,
        element=None,
        base_polarity_multiplier=0.15,
        anomaly_proficiency_coefficient=5.0 + 2.25 * ex_level,
    )
    ex_polarity_creation = _event_creation(
        "ex-special:polarity-disorder",
        ex_polarity_source,
        ex_polarity_ref,
        filters=(
            DamageDealerFilter(YANAGI_ID),
            DamageTypeFilter(DamageType.DIRECT),
            AnyFilter(
                (
                    EventTemplateIdFilter(ex_downfall_ref.template_id),
                    EventTemplateIdFilter(ex_downfall_direct_template.ref.template_id),
                )
            ),
        ),
    )
    rules.append(
        _rule(
            "ex-special:polarity-disorder",
            ex_polarity_source,
            "强化特殊技：极性紊乱与异常精通附加伤害",
            raw_moves["强化特殊技：月华流转"].description,
            condition_ids=(POLARITY_TARGET_HAS_ACTIVE_ANOMALY,),
            effects=(ex_polarity_creation,),
        )
    )
    ultimate_entry = next(
        item
        for item in direct_entries
        if str(item.entry_id) == "move-entry:character:1221:ultimate-thunder-shadow"
    )
    ultimate_template = next(
        item
        for item in direct_templates
        if item.ref.template_id == ultimate_entry.main_damage_event.template_id
    )
    ultimate_level = effective_skill_level(config, SkillGroup.ULTIMATE)
    ultimate_polarity_source = source_for(
        YANAGI_ID,
        "ultimate-polarity-disorder",
        EffectSourceType.SPECIAL_MECHANISM,
        "终结技：雷影天华（极性紊乱）",
        raw_moves["终结技：雷影天华"].description,
    )
    ultimate_polarity_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1221:ultimate:polarity-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1221:ultimate:polarity-disorder"),
        label="终结技：极性紊乱",
        damage_type=DamageType.DISORDER,
        element=None,
        source_rule_item_id=RuleItemId("rule:character:1221:ultimate:polarity-disorder"),
    )
    ultimate_polarity_template = PolarDisorderDamageEventTemplate(
        ref=ultimate_polarity_ref,
        damage_dealer=YANAGI_ID,
        disorder_triggerer=YANAGI_ID,
        element=None,
        base_polarity_multiplier=0.15,
        anomaly_proficiency_coefficient=5.0 + 2.25 * ultimate_level,
    )
    ultimate_polarity_creation = _event_creation(
        "ultimate:polarity-disorder",
        ultimate_polarity_source,
        ultimate_polarity_ref,
        filters=(
            DamageDealerFilter(YANAGI_ID),
            DamageTypeFilter(DamageType.DIRECT),
            EventTemplateIdFilter(ultimate_template.ref.template_id),
        ),
    )
    rules.append(
        _rule(
            "ultimate:polarity-disorder",
            ultimate_polarity_source,
            "终结技：极性紊乱与异常精通附加伤害",
            raw_moves["终结技：雷影天华"].description,
            condition_ids=(POLARITY_TARGET_HAS_ACTIVE_ANOMALY,),
            effects=(ultimate_polarity_creation,),
        )
    )
    c2_polarity_source = cinema_sources[2]
    c2_polarity_text = raw_record.mindscapes[1].description
    c2_ex_polarity_effects = (
        _modifier(
            "cinema2:ex-polarity-base-multiplier",
            c2_polarity_source,
            CalculationNode.POLAR_DISORDER_MULTIPLIER,
            Resolved(0.05),
            target=EffectTarget.TEAM,
            filters=(CreatedByEffectFilter(ex_polarity_creation.rule.effect_id),),
        ),
        _modifier(
            "cinema2:ex-polarity-extra-thrusts",
            c2_polarity_source,
            CalculationNode.POLAR_DISORDER_MULTIPLIER,
            ScenarioParameterDerivedValue(
                parameter_id=str(EX_SPECIAL_EXTRA_THRUSTS),
                coefficient=Resolved(0.15),
                cap_max=Resolved(0.60 if config.cinema_level >= 6 else 0.30),
            ),
            target=EffectTarget.TEAM,
            filters=(CreatedByEffectFilter(ex_polarity_creation.rule.effect_id),),
        ),
    )
    rules.append(
        _rule(
            "cinema2:ex-polarity-multiplier",
            c2_polarity_source,
            "2影/6影：极性紊乱倍率与额外突刺加成",
            c2_polarity_text + "\n" + raw_record.mindscapes[5].description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=c2_ex_polarity_effects,
        )
    )
    ex_extra_thrust_source = source_for(
        YANAGI_ID,
        "ex-special-extra-thrusts",
        EffectSourceType.SPECIAL_MECHANISM,
        "强化特殊技：月华流转（额外突刺）",
        raw_moves["强化特殊技：月华流转"].description,
    )
    ex_extra_thrust_creation = (
        _event_creation(
            "ex-special:extra-thrusts",
            ex_extra_thrust_source,
            ex_extra_thrust_ref,
            filters=(
                DamageDealerFilter(YANAGI_ID),
                DamageTypeFilter(DamageType.DIRECT),
                EventTemplateIdFilter(ex_main_template.ref.template_id),
            ),
        )
        if ex_extra_thrust_ref is not None
        else None
    )
    rules.append(
        _rule(
            "ex-special:extra-thrusts",
            ex_extra_thrust_source,
            "强化特殊技：额外突刺命中",
            raw_moves["强化特殊技：月华流转"].description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=(
                (ex_extra_thrust_creation,)
                if ex_extra_thrust_creation is not None
                else ()
            ),
        )
    )

    static_entries, static_templates, disorder_remaining = _static_electric_entries()
    diagnostics = (
        *direct_diagnostics,
        CalculationDiagnostic(
            diagnostic_id=DiagnosticId("unsupported:character:1221:daze-and-timing-output"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message=(
                "The raw source includes Daze, anomaly buildup, energy, stance and "
                "duration effects. The result contract does not output Daze/buildup "
                "or replay energy and time-dependent actions."
            ),
            blocking=False,
            original_text=core.description,
        ),
    )
    return build_definition(
        character_id=YANAGI_ID,
        role=CharacterRole.ANOMALY,
        element=Element.ELECTRIC,
        source=core_source,
        entries=(*entries, *static_entries),
        templates=(
            *direct_templates,
            *static_templates,
            ex_downfall_template,
            *((ex_extra_thrust_template,) if ex_extra_thrust_template is not None else ()),
            ex_polarity_template,
            ultimate_polarity_template,
        ),
        rules=tuple(rules),
        conditions=(
            upper_condition,
            lower_condition,
            ex_electric_condition,
            disorder_condition,
            insight_condition,
            forest_illumination,
            polarity_target_condition,
        ),
        parameters=(
            insight_stacks,
            *((ex_extra_thrusts,) if ex_extra_thrusts is not None else ()),
            disorder_remaining,
        ),
        independent_derived_damage_events=(
            ex_downfall_derived,
            *((ex_extra_thrust_derived,) if ex_extra_thrust_derived is not None else ()),
            DerivedDamageEventTemplateRef(
                template=ex_polarity_ref,
                multiplier=FixedMultiplier(Resolved(1.0)),
            ),
            DerivedDamageEventTemplateRef(
                template=ultimate_polarity_ref,
                multiplier=FixedMultiplier(Resolved(1.0)),
            ),
        ),
        diagnostics=diagnostics,
    )


__all__ = ["compile_yanagi", "load_raw_record"]
