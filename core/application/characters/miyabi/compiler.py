"""Compile the Nanoka Miyabi record into reviewed application contracts."""

from __future__ import annotations

import re

from core.types import (
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterRole,
    CreatedByEffectFilter,
    CurrentAttackValueSource,
    DamageTag,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageType,
    DamageTypeFilter,
    DamageMultiplier,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventTemplateId,
    EventTemplateIdFilter,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    MoveId,
    MoveIdFilter,
    NoCritRule,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
    ModifierEffect,
    ModifierResult,
    SkillGroup,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...element_scope import element_scope_filter
from ...ids import (
    DamageEventSemanticId,
    DiagnosticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
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
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import MiyabiCompileConfig
from .reviewed import (
    DASH_MOVE_ID,
    DODGE_COUNTER_MOVE_ID,
    FROSTBURN_BREAK_READY,
    FROSTMOON_CHARGE_1,
    FROSTMOON_CHARGE_2,
    FROSTMOON_CHARGE_3,
    FROSTMOON_MOVE_ID,
    FROSTSCORCH_ACTIVE,
    FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE,
    ICEFIRE_ACTIVE,
    KAZAHANA_MOVE_ID,
    MIYABI_ID,
    MIYABI_REVIEWED_MAPPING,
    MIYABI_UNRESOLVED_MULTIPLIERS,
    NEXT_FROSTMOON_AFTER_DISORDER,
    QUICK_ASSIST_MOVE_ID,
    SPECIAL_MOVE_ID,
    ULTIMATE_ICE_BONUS_ACTIVE,
    ULTIMATE_MOVE_ID,
    UnresolvedMultiplierSpec,
)


MIYABI_DISORDER_REMAINING_DURATION_PARAMETER_ID = ScenarioParameterId(
    "parameter:miyabi:lieshuang-anomaly-remaining-seconds"
)
MIYABI_FROST_ANOMALY_RECORD_ID = AnomalyRecordId(
    "anomaly:miyabi:lieshuang-current"
)
FROSTBURN_BREAK_EFFECT_ID = EffectId(
    "effect:character:1091:core:frostburn-break"
)


def _condition(
    condition_id,
    label: str,
    original_text: str,
    *,
    default: bool = False,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=default,
    )


def _rule(
    rule_id: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(rule_id),
        owner=MIYABI_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    effect_key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1091:{effect_key}"),
            source=source,
            owner=MIYABI_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.core_levels if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Miyabi record is missing core level {level}") from exc


def _raw_mindscape(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Miyabi record is missing mindscape {level}") from exc


def _number_from_core_text(
    text: str,
    pattern: str,
    *,
    subject: str,
    original_text: str,
) -> float:
    matches = tuple(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError(
            f"{subject} must contain one reviewed numeric value; found {len(matches)}"
        )
    return float(matches[0].group("value")) / 100.0


def _unresolved_move_entry(
    spec: UnresolvedMultiplierSpec,
    *,
    raw_record: NanokaRawRecord,
    config: MiyabiCompileConfig,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    moves = raw_move_index(raw_record)
    raw_move = moves.get(spec.source_name)
    parameter = (
        next(
            (item for item in raw_move.parameters if item.name == spec.parameter_name),
            None,
        )
        if raw_move is not None
        else None
    )
    level = effective_skill_level(config, spec.skill_group)
    variants: list[MultiplierVariant] = []
    candidates: list[str] = []
    resolved_values: list[float] = []
    for source_skill_id in spec.source_skill_ids:
        value = (
            parameter.value_for_level(level, source_skill_id)
            if parameter is not None and parameter.format == "%"
            else None
        )
        if value is None:
            multiplier: DamageMultiplier = Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=(
                    f"{spec.display_name}: source curve {source_skill_id} is missing "
                    f"for skill level {level}"
                ),
                original_text=spec.parameter_name,
            )
            candidates.append(f"source {source_skill_id}: missing at skill level {level}")
        else:
            multiplier = FixedMultiplier(Resolved(value / 100.0))
            resolved_values.append(value)
            candidates.append(f"source {source_skill_id}: {value:.2f}%")
        if not spec.source_curves_are_additive:
            variants.append(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1091:{spec.entry_key}:{source_skill_id}"
                    ),
                    label=f"Nanoka 参数 {source_skill_id}",
                    parameter_name=spec.parameter_name,
                    multiplier=multiplier,
                )
            )
    original_text = raw_move.description if raw_move is not None else spec.source_name
    diagnostic = None
    if spec.source_curves_are_additive and len(resolved_values) == len(spec.source_skill_ids):
        total = sum(resolved_values)
        variants = [
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    f"variant:character:1091:{spec.entry_key}:source-sum"
                ),
                label="原始参数表达式相加的源曲线",
                parameter_name=spec.parameter_name,
                multiplier=FixedMultiplier(Resolved(total / 100.0)),
            )
        ]
        candidates.append(f"source sum: {total:.2f}%")
        relation = MultiplierRelation.COMPLETE
    elif spec.source_curves_are_additive:
        diagnostic = CalculationDiagnostic(
            diagnostic_id=DiagnosticId(
                f"data:character:1091:{spec.entry_key}:source-sum"
            ),
            kind=DiagnosticKind.MISSING_DATA,
            message=f"{spec.display_name}: one or more source curves are missing; explicit sum cannot be resolved.",
            blocking=True,
            original_text=original_text,
            candidates=tuple(candidates),
        )
        variants = [
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    f"variant:character:1091:{spec.entry_key}:source-sum"
                ),
                label="原始参数表达式相加的源曲线",
                parameter_name=spec.parameter_name,
                multiplier=Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes=diagnostic.message,
                    original_text=original_text,
                    candidates=tuple(candidates),
                ),
            )
        ]
        relation = MultiplierRelation.COMPLETE
    else:
        diagnostic = CalculationDiagnostic(
            diagnostic_id=DiagnosticId(
                f"review:character:1091:{spec.entry_key}:multiplier-relationship"
            ),
            kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
            message=f"{spec.explanation} 当前只保留源曲线候选，不合并或任选其中一条。",
            blocking=True,
            original_text=original_text,
            candidates=tuple(candidates),
        )
        relation = MultiplierRelation.UNRESOLVED_RELATION
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1091:{spec.entry_key}:main",
        semantic_id=f"event:character:1091:{spec.entry_key}:main",
        label=spec.display_name,
        damage_type=DamageType.DIRECT,
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        element=spec.element,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=MIYABI_ID,
        element=spec.element,
        base_source=CurrentAttackValueSource(MIYABI_ID),
        crit_rule=StandardCritRule(MIYABI_ID),
        move_id=spec.move_id,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1091:{spec.entry_key}"),
        character_id=MIYABI_ID,
        move_id=spec.move_id,
        display_name=spec.display_name,
        original_text=original_text,
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        multiplier_relation=relation,
        multiplier_variants=tuple(variants),
        main_damage_event=ref,
        diagnostics=(() if diagnostic is None else (diagnostic,)),
    )
    return entry, template


def _special_entry(
    *,
    entry_key: str,
    move_id: MoveId,
    label: str,
    ref: DamageEventTemplateRef,
    variant: MultiplierVariant,
    original_text: str,
) -> MoveCalculationEntry:
    return MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1091:{entry_key}"),
        character_id=MIYABI_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(variant,),
        main_damage_event=ref,
    )


def _anomaly_and_disorder_pairs():
    anomaly_move_id = MoveId("move:miyabi:lieshuang-anomaly")
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1091:lieshuang-anomaly",
        semantic_id="event:character:1091:lieshuang-anomaly",
        label="属性异常：烈霜碎冰",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.LIESHUANG,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=MIYABI_ID,
        element=Element.LIESHUANG,
        anomaly_triggerer=MIYABI_ID,
        history_record_source=MIYABI_FROST_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=anomaly_move_id,
    )
    anomaly_entry = _special_entry(
        entry_key="lieshuang-anomaly",
        move_id=anomaly_move_id,
        label="属性异常：烈霜碎冰",
        ref=anomaly_ref,
        variant=MultiplierVariant(
            variant_id=MultiplierVariantId("variant:character:1091:lieshuang-anomaly"),
            label="烈霜碎冰倍率",
            parameter_name="烈霜属性异常伤害倍率",
            multiplier=FixedMultiplier(Resolved(5.0)),
        ),
        original_text=(
            "烈霜异常触发冻结，并在冻结结束时造成碎冰；计算器按烈霜属性异常"
            "伤害倍率及20秒烈霜霜寒记录结算。"
        ),
    )

    disorder_move_id = MoveId("move:miyabi:lieshuang-disorder")
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1091:lieshuang-disorder",
        semantic_id="event:character:1091:lieshuang-disorder",
        label="紊乱：烈霜异常",
        damage_type=DamageType.DISORDER,
        damage_subtype=None,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.LIESHUANG,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=MIYABI_ID,
        element=Element.LIESHUANG,
        disorder_triggerer=MIYABI_ID,
        history_record_source=MIYABI_FROST_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=disorder_move_id,
    )
    disorder_entry = _special_entry(
        entry_key="lieshuang-disorder",
        move_id=disorder_move_id,
        label="紊乱：烈霜异常",
        ref=disorder_ref,
        variant=MultiplierVariant(
            variant_id=MultiplierVariantId("variant:character:1091:lieshuang-disorder"),
            label="450%基础倍率+烈霜剩余时间补偿",
            parameter_name="烈霜紊乱倍率",
            multiplier=FixedMultiplier(Resolved(4.5)),
            parameter_value_id=MIYABI_DISORDER_REMAINING_DURATION_PARAMETER_ID,
            parameter_base_value=4.5,
            parameter_coefficient=0.75,
        ),
        original_text=(
            "被结算的烈霜霜寒记录具有20秒最大持续时间；"
            "按《绝区零伤害计算规范》的烈霜碎冰剩余时间补偿倍率结算。"
        ),
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
    )


def compile_miyabi(
    config: MiyabiCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = MIYABI_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=MIYABI_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="character:1091",
    )
    unresolved_entries = tuple(
        _unresolved_move_entry(item, raw_record=raw_record, config=config)
        for item in MIYABI_UNRESOLVED_MULTIPLIERS
    )
    entries = (*entries, *(item[0] for item in unresolved_entries))
    templates = (*templates, *(item[1] for item in unresolved_entries))

    anomaly_disorder_entries, anomaly_disorder_templates = _anomaly_and_disorder_pairs()
    entries = (*entries, *anomaly_disorder_entries)
    templates = (*templates, *anomaly_disorder_templates)

    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        MIYABI_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_break_multiplier = _number_from_core_text(
        core.description,
        r"对目标造成星见雅<color=#2BAD00>(?P<value>\d+(?:\.\d+)?)%</color>攻击力的<color=#98EFF0>烈霜伤害</color>",
        subject="Miyabi Frostburn Break attack multiplier",
        original_text=core.description,
    )
    frostscorch_buildup_bonus = _number_from_core_text(
        core.description,
        r"所有单位对目标累积的属性异常积蓄值提升<color=#2BAD00>(?P<value>\d+(?:\.\d+)?)%</color>",
        subject="Miyabi Frostscorch buildup increase",
        original_text=core.description,
    )

    core_rule_id = RuleItemId("rule:character:1091:core:frostburn-break")
    frostburn_ref = DamageEventTemplateRef(
        template_id="template:character:1091:core:frostburn-break",
        semantic_id="event:character:1091:core:frostburn-break",
        label="核心被动：霜灼·破",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.LIESHUANG,
        source_rule_item_id=core_rule_id,
    )
    frostburn_template = DirectDamageEventTemplate(
        ref=frostburn_ref,
        damage_dealer=MIYABI_ID,
        element=Element.LIESHUANG,
        base_source=CurrentAttackValueSource(MIYABI_ID),
        crit_rule=StandardCritRule(MIYABI_ID),
        move_id=None,
    )
    frostburn_derived = DerivedDamageEventTemplateRef(
        template=frostburn_ref,
        multiplier=FixedMultiplier(Resolved(core_break_multiplier)),
    )
    frostburn_creation = EventCreationEffect(
        rule=EffectRule(
            effect_id=FROSTBURN_BREAK_EFFECT_ID,
            source=core_source,
            owner=MIYABI_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.ANOMALY),
                DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                DamageDealerFilter(MIYABI_ID),
                ElementFilter(Element.LIESHUANG),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=frostburn_ref.template_id,
        ),
    )
    core_break_rule = _rule(
        str(core_rule_id),
        core_source,
        f"{core.name}：霜灼·破",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(frostburn_creation,),
        condition_ids=(ICEFIRE_ACTIVE, FROSTBURN_BREAK_READY),
    )
    frostscorch_buildup_effect = _modifier(
        "core:frostscorch-anomaly-buildup-increase",
        core_source,
        CalculationNode.ANOMALY_BUILDUP_INCREASE,
        Resolved(frostscorch_buildup_bonus),
        target=EffectTarget.ENEMY,
        filters=(DamageTypeFilter(DamageType.DIRECT),),
    )
    frostscorch_rule = _rule(
        "rule:character:1091:core:frostscorch-buildup",
        core_source,
        f"{core.name}：霜灼",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(frostscorch_buildup_effect,),
        condition_ids=(FROSTSCORCH_ACTIVE,),
    )
    icefire_buildup_efficiency = _modifier(
        "core:icefire-buildup-efficiency",
        core_source,
        CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
        PanelStatDerivedValue(
            source_character_id=MIYABI_ID,
            source_node=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            coefficient=Resolved(1.0),
            cap_max=Resolved(0.80),
        ),
        target=EffectTarget.SELF,
        filters=(
            DamageDealerFilter(MIYABI_ID),
            ElementFilter(Element.LIESHUANG),
        ),
    )
    icefire_buildup_rule = _rule(
        "rule:character:1091:core:icefire-buildup",
        core_source,
        f"{core.name}：冰焰烈霜异常积蓄效率",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(icefire_buildup_efficiency,),
        condition_ids=(ICEFIRE_ACTIVE,),
    )

    extra_source = source_for(
        MIYABI_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    additional_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    frostmoon_bonus = _modifier(
        "extra-ability:frostmoon-damage",
        extra_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.60),
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(MIYABI_ID),
            MoveIdFilter(FROSTMOON_MOVE_ID),
        ),
    )
    extra_ability_rule = _rule(
        "rule:character:1091:extra-ability:frostmoon-damage",
        extra_source,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
        additional_eligibility,
        effects=(frostmoon_bonus,),
    )
    post_disorder_resistance_ignore = _modifier(
        "extra-ability:post-disorder-frostmoon-resistance-ignore",
        extra_source,
        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
        Resolved(0.30),
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(MIYABI_ID),
            MoveIdFilter(FROSTMOON_MOVE_ID),
            element_scope_filter(Element.ICE),
        ),
    )
    post_disorder_rule = _rule(
        "rule:character:1091:extra-ability:post-disorder-frostmoon-resistance-ignore",
        extra_source,
        "额外能力：紊乱后的下一次霜月无视冰抗",
        raw_record.extra_ability_description,
        additional_eligibility,
        effects=(post_disorder_resistance_ignore,),
        condition_ids=(NEXT_FROSTMOON_AFTER_DISORDER,),
    )

    ultimate = next(item for item in raw_record.moves if item.name == "终结技：名残雪")
    ultimate_source = source_for(
        MIYABI_ID,
        "ultimate-ice-damage-state",
        EffectSourceType.SKILL,
        "终结技：名残雪状态效果",
        ultimate.description,
    )
    ultimate_ice_damage_bonus = _modifier(
        "ultimate:ice-damage-bonus-state",
        ultimate_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.30),
        filters=(
            DamageDealerFilter(MIYABI_ID),
            element_scope_filter(Element.ICE),
        ),
    )
    ultimate_state_rule = _rule(
        "rule:character:1091:ultimate:ice-damage-bonus-state",
        ultimate_source,
        "终结技：名残雪·冰属性伤害提升",
        ultimate.description,
        RuleEligibility.ELIGIBLE,
        effects=(ultimate_ice_damage_bonus,),
        condition_ids=(ULTIMATE_ICE_BONUS_ACTIVE,),
    )

    rules: list[CalculationRuleItem] = [
        core_break_rule,
        frostscorch_rule,
        icefire_buildup_rule,
        extra_ability_rule,
        post_disorder_rule,
        ultimate_state_rule,
    ]
    templates = (*templates, frostburn_template)
    independent_derived = [frostburn_derived]

    frostburn_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1091:frostburn-break"),
        character_id=MIYABI_ID,
        move_id=None,
        display_name="核心被动：霜灼·破",
        original_text=core.description,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1091:frostburn-break"
                ),
                label="霜灼·破倍率",
                parameter_name="当前攻击力倍率",
                multiplier=FixedMultiplier(Resolved(core_break_multiplier)),
            ),
        ),
        main_damage_event=frostburn_ref,
        condition_ids=(ICEFIRE_ACTIVE, FROSTBURN_BREAK_READY),
    )
    entries = (*entries, frostburn_entry)

    cinema_rules, cinema_templates, cinema_derived, c6_parameters = _cinema_rules(
        raw_record,
        config,
        frostburn_ref.template_id,
    )
    rules.extend(cinema_rules)
    templates = (*templates, *cinema_templates)
    independent_derived.extend(cinema_derived)

    conditions = (
        _condition(
            FROSTMOON_CHARGE_1,
            "霜月：一段蓄力",
            "每段蓄力消耗2点落霜，按当前蓄力段数结算",
        ),
        _condition(
            FROSTMOON_CHARGE_2,
            "霜月：二段蓄力",
            "每段蓄力消耗2点落霜，按当前蓄力段数结算",
        ),
        _condition(
            FROSTMOON_CHARGE_3,
            "霜月：三段蓄力",
            "每段蓄力消耗2点落霜，按当前蓄力段数结算",
        ),
        _condition(
            ICEFIRE_ACTIVE,
            "敌人当前处于冰焰状态",
            core.description,
            default=False,
        ),
        _condition(
            FROSTBURN_BREAK_READY,
            "霜灼·破的10秒触发间隔已满足",
            core.description,
            default=True,
        ),
        _condition(
            FROSTSCORCH_ACTIVE,
            "敌人当前处于霜灼状态",
            core.description,
            default=False,
        ),
        _condition(
            FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE,
            "影画1：全队异常积蓄效率提升当前生效",
            _raw_mindscape(raw_record, 1).description,
            default=False,
        ),
        _condition(
            NEXT_FROSTMOON_AFTER_DISORDER,
            "额外能力：队伍触发紊乱后，当前为雅的下一次霜月",
            raw_record.extra_ability_description,
            default=False,
        ),
        _condition(
            ULTIMATE_ICE_BONUS_ACTIVE,
            "终结技：名残雪的12秒冰属性伤害提升当前生效",
            ultimate.description,
            default=False,
        ),
    )
    scenario_parameters = (
        ScenarioIntegerParameter(
            parameter_id=MIYABI_DISORDER_REMAINING_DURATION_PARAMETER_ID,
            label="被结算烈霜霜寒剩余时间（秒）",
            original_text="默认按烈霜霜寒最大剩余时间20秒结算",
            resolution=ParameterResolution.USER_SELECTED,
            value=20,
            minimum=0,
            maximum=20,
        ),
    )
    # C6 emits one aggregate slash for the selected charge stage.  Its ratio
    # sums the source curves for stages 1..k; no extra repeat count is needed.
    scenario_parameters = (*scenario_parameters, *c6_parameters)

    return build_definition(
        character_id=MIYABI_ID,
        role=CharacterRole.ANOMALY,
        element=Element.ICE,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=scenario_parameters,
        independent_derived_damage_events=independent_derived,
        diagnostics=diagnostics,
    )


def _condition(condition_id, label: str, original_text: str, *, default=False):
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=default,
    )


def _cinema_rules(
    raw: NanokaRawRecord,
    config: MiyabiCompileConfig,
    frostburn_template_id: EventTemplateId,
):
    rules: list[CalculationRuleItem] = []
    templates: list[DirectDamageEventTemplate] = []
    derived: list[DerivedDamageEventTemplateRef] = []
    parameters: list[ScenarioIntegerParameter] = []

    c1 = _raw_mindscape(raw, 1)
    c1_source = source_for(
        MIYABI_ID, "cinema-1", EffectSourceType.CINEMA, f"1影：{c1.name}", c1.description
    )
    stage_values = (
        ("1", FROSTMOON_CHARGE_1, 0.12),
        ("2", FROSTMOON_CHARGE_2, 0.24),
        ("3", FROSTMOON_CHARGE_3, 0.36),
    )
    for stage, condition_id, ignored_defense in stage_values:
        effect = _modifier(
            f"cinema1:frostmoon-defense-ignore-{stage}",
            c1_source,
            CalculationNode.DAMAGE_DEFENSE_IGNORE,
            Resolved(ignored_defense),
            target=EffectTarget.ENEMY,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(MIYABI_ID),
                MoveIdFilter(FROSTMOON_MOVE_ID),
            ),
        )
        rules.append(
            _rule(
                f"rule:character:1091:cinema1:frostmoon-defense-ignore-{stage}",
                c1_source,
                f"1影：霜月{stage}段蓄力无视防御",
                c1.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
                effects=(effect,),
                condition_ids=(condition_id,),
            )
        )
    rules.append(
        _rule(
            "rule:character:1091:cinema1:team-buildup-efficiency",
            c1_source,
            f"1影：全队异常积蓄效率提升",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:team-anomaly-buildup-efficiency",
                    c1_source,
                    CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    Resolved(0.20),
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(FROSTSCORCH_TEAM_BUILDUP_BUFF_ACTIVE,),
        )
    )

    c2 = _raw_mindscape(raw, 2)
    c2_source = source_for(
        MIYABI_ID, "cinema-2", EffectSourceType.CINEMA, f"2影：{c2.name}", c2.description
    )
    rules.append(
        _rule(
            "rule:character:1091:cinema2",
            c2_source,
            f"2影：{c2.name}",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:entry-crit-rate",
                    c2_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(0.15),
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    "cinema2:kazahana-damage",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.30),
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(MIYABI_ID),
                        MoveIdFilter(KAZAHANA_MOVE_ID),
                    ),
                ),
                _modifier(
                    "cinema2:dodge-counter-damage",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.30),
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(MIYABI_ID),
                        MoveIdFilter(DODGE_COUNTER_MOVE_ID),
                    ),
                ),
            ),
        )
    )

    c3 = _raw_mindscape(raw, 3)
    c3_source = source_for(
        MIYABI_ID, "cinema-3", EffectSourceType.CINEMA, f"3影：{c3.name}", c3.description
    )
    rules.append(
        _rule(
            "rule:character:1091:cinema3",
            c3_source,
            f"3影：{c3.name}",
            c3.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 3 else RuleEligibility.INELIGIBLE,
        )
    )

    c4 = _raw_mindscape(raw, 4)
    c4_source = source_for(
        MIYABI_ID, "cinema-4", EffectSourceType.CINEMA, f"4影：{c4.name}", c4.description
    )
    c4_break_bonus = _modifier(
        "cinema4:frostburn-break-damage",
        c4_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.30),
        target=EffectTarget.TEAM,
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(MIYABI_ID),
            EventTemplateIdFilter(frostburn_template_id),
        ),
    )
    rules.append(
        _rule(
            "rule:character:1091:cinema4",
            c4_source,
            f"4影：{c4.name}",
            c4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            effects=(c4_break_bonus,),
        )
    )

    c5 = _raw_mindscape(raw, 5)
    c5_source = source_for(
        MIYABI_ID, "cinema-5", EffectSourceType.CINEMA, f"5影：{c5.name}", c5.description
    )
    rules.append(
        _rule(
            "rule:character:1091:cinema5",
            c5_source,
            f"5影：{c5.name}",
            c5.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 5 else RuleEligibility.INELIGIBLE,
        )
    )

    c6 = _raw_mindscape(raw, 6)
    c6_source = source_for(
        MIYABI_ID, "cinema-6", EffectSourceType.CINEMA, f"6影：{c6.name}", c6.description
    )
    common_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    c6_moon_bonus = _modifier(
        "cinema6:frostmoon-damage",
        c6_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.30),
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(MIYABI_ID),
            MoveIdFilter(FROSTMOON_MOVE_ID),
        ),
    )
    rules.append(
        _rule(
            "rule:character:1091:cinema6:frostmoon-damage",
            c6_source,
            "6影：霜月伤害提升",
            c6.description,
            common_eligibility,
            effects=(c6_moon_bonus,),
        )
    )
    charge_sources = (
        (1, ("1091027",), FROSTMOON_CHARGE_1),
        (2, ("1091027", "1091028"), FROSTMOON_CHARGE_2),
        (3, ("1091027", "1091028", "1091029"), FROSTMOON_CHARGE_3),
    )
    for charge, source_skill_ids, condition_id in charge_sources:
        # The selected k-charge Frostmoon main event already accounts for
        # source curve k. C6 adds only the earlier 1..k-1 slashes, so the
        # combined result contains each charge curve exactly once.
        if charge == 1:
            continue
        prior_source_skill_ids = source_skill_ids[:-1]
        level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
        raw_moon = next(move for move in raw.moves if move.name == "普通攻击：霜月")
        charge_parameter_names = tuple(
            f"{('一', '二', '三')[index]}段蓄力斩击伤害倍率"
            for index in range(charge - 1)
        )
        raw_parameters = {
            parameter.name: parameter for parameter in raw_moon.parameters
        }
        damage_components = tuple(
            raw_parameters[parameter_name].value_for_level(level, source_skill_id)
            for parameter_name, source_skill_id in zip(
                charge_parameter_names,
                prior_source_skill_ids,
            )
        )
        if any(value is None for value in damage_components):
            raise ValueError(f"Miyabi C6 is missing source multiplier(s) {prior_source_skill_ids}")
        damage_ratio = sum(float(value) for value in damage_components) / 100.0
        entry_key = f"cinema6-extra-slash-charge-{charge}"
        ref = DamageEventTemplateRef(
            template_id=f"template:character:1091:{entry_key}",
            semantic_id=f"event:character:1091:{entry_key}",
            label=f"6影：霜月{charge}段蓄力前序斩击",
            damage_type=DamageType.DIRECT,
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
            element=Element.LIESHUANG,
            source_rule_item_id=RuleItemId(
                f"rule:character:1091:cinema6-extra-slash-charge-{charge}"
            ),
        )
        template = DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=MIYABI_ID,
            element=Element.LIESHUANG,
            base_source=CurrentAttackValueSource(MIYABI_ID),
            crit_rule=StandardCritRule(MIYABI_ID),
            move_id=FROSTMOON_MOVE_ID,
        )
        derived_ref = DerivedDamageEventTemplateRef(
            template=ref,
            multiplier=FixedMultiplier(Resolved(damage_ratio)),
        )
        event_id = EffectId(
                f"effect:character:1091:cinema6:extra-slash-charge-{charge}"
        )
        creation = EventCreationEffect(
            rule=EffectRule(
                effect_id=event_id,
                source=c6_source,
                owner=MIYABI_ID,
                target=EffectTarget.SELF,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(MIYABI_ID),
                    MoveIdFilter(FROSTMOON_MOVE_ID),
                    NotFilter(CreatedByEffectFilter(event_id)),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=ref.template_id,
            ),
        )
        rules.append(
            _rule(
                f"rule:character:1091:{entry_key}",
                c6_source,
                f"6影：霜月{charge}段蓄力前序斩击",
                c6.description,
                common_eligibility,
                effects=(creation,),
                condition_ids=(condition_id,),
            )
        )
        templates.append(template)
        derived.append(derived_ref)

    return tuple(rules), tuple(templates), tuple(derived), tuple(parameters)


def _validate_raw_record(raw: NanokaRawRecord, config: MiyabiCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "雅":
        raise ValueError("unexpected character name in raw Miyabi record")
    if raw.code_name != "Miyabi":
        raise ValueError("unexpected Miyabi code name in raw record")
    if raw.specialty != "异常":
        raise ValueError("unexpected Miyabi specialty in raw record")
    if raw.element != "冰属性":
        raise ValueError("unexpected Miyabi base element in raw record")
    if len(raw.core_levels) != 7:
        raise ValueError("raw Miyabi record must contain all seven core levels")
    if len(raw.mindscapes) != 6:
        raise ValueError("raw Miyabi record must contain all six mindscapes")


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(MIYABI_ID))


__all__ = [
    "MIYABI_DISORDER_REMAINING_DURATION_PARAMETER_ID",
    "MIYABI_FROST_ANOMALY_RECORD_ID",
    "MIYABI_ID",
    "compile_miyabi",
    "load_raw_record",
]
