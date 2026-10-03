"""Compile Qingyi's live Nanoka record into typed, static damage rules."""

from __future__ import annotations

import re
from collections.abc import Mapping

from core.types import (
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageTag,
    DamageSubtype,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    FixedMultiplier,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NotFilter,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
    SkillGroup,
    ScenarioParameterDerivedValue,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import DamageEventSemanticId, DiagnosticId, MoveEntryId, MultiplierVariantId, RuleItemId
from ...moves import (
    DamageEventTemplateRef,
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
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawRecord
from ..templates import DirectDamageEventTemplate
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import QingyiCompileConfig
from .reviewed import (
    BASIC_DRUNKEN_CLOUD_MOVE_ID,
    BASIC_MOON_TURN_MOVE_ID,
    BASIC_YISHA_MOVE_ID,
    C1_TARGET_DEBUFF_ACTIVE,
    C6_ALL_RESISTANCE_ACTIVE,
    CHAIN_MOVE_ID,
    DASH_ATTACK_MOVE_ID,
    DODGE_COUNTER_MOVE_ID,
    ELECTRIC_ANOMALY_MOVE_ID,
    ELECTRIC_ANOMALY_RECORD_ID,
    ELECTRIC_DISORDER_MOVE_ID,
    ELECTRIC_DISORDER_REMAINING_SECONDS,
    EX_SPECIAL_MOVE_ID,
    FLASHOVER_ACTIVE,
    FLASHOVER_EXCESS_PERCENT,
    QINGYI_ID,
    QINGYI_REVIEWED_MAPPING,
    SUBJUGATION_STACKS,
    SUPPORT_FOLLOWUP_MOVE_ID,
)


_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    from ..nanoka_source import load_nanoka_raw_record

    return load_nanoka_raw_record(data, expected_character_id=str(QINGYI_ID))


def _plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain exactly one value; found {len(matches)}")
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
    suffix: str,
    source: RuleSource,
    label: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    conditions=(),
    effects=(),
    diagnostics=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1251:{suffix}"),
        owner=QINGYI_ID,
        source=source,
        display_name=label,
        original_text=original_text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    suffix: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1251:{suffix}"),
            source=source,
            owner=QINGYI_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=operation,
            value=value,
        ),
    )


def _diagnostic(
    suffix: str,
    message: str,
    original_text: str,
    *,
    blocking: bool = False,
    kind: DiagnosticKind | None = None,
    candidates: tuple[str, ...] = (),
) -> CalculationDiagnostic:
    if kind is None:
        kind = (
            DiagnosticKind.AMBIGUOUS_SEMANTICS
            if blocking
            else DiagnosticKind.UNSUPPORTED_CALCULATOR
        )
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"{suffix}"),
        kind=kind,
        message=message,
        blocking=blocking,
        original_text=original_text,
        candidates=candidates,
    )


def _source_parameter(
    raw_moves,
    move_name: str,
    parameter_name: str,
    source_skill_id: str,
    level: int,
) -> float:
    move = raw_moves.get(move_name)
    parameter = (
        next((item for item in move.parameters if item.name == parameter_name), None)
        if move is not None
        else None
    )
    value = parameter.value_for_level(level, source_skill_id) if parameter else None
    if value is None:
        raise ValueError(
            f"Qingyi raw curve missing {move_name}/{parameter_name}/{source_skill_id} at level {level}"
        )
    return value / 100.0


def _direct_template(
    *,
    key: str,
    label: str,
    move_id: MoveId,
    skill_group: SkillGroup,
    tags: frozenset[DamageTag],
    element: Element,
) -> DirectDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1251:{key}:main",
        semantic_id=DamageEventSemanticId(f"event:character:1251:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=tags,
        element=element,
    )
    return DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=QINGYI_ID,
        element=element,
        base_source=CurrentAttackValueSource(QINGYI_ID),
        crit_rule=StandardCritRule(QINGYI_ID),
        move_id=move_id,
    )


def _basic_yisha_entries(
    config: QingyiCompileConfig,
    raw_record: NanokaRawRecord,
) -> tuple[tuple[MoveCalculationEntry, ...], tuple[DirectDamageEventTemplate, ...], tuple[CalculationDiagnostic, ...]]:
    raw_moves = raw_move_index(raw_record)
    source_name = "普通攻击：一煞"
    raw_move = raw_moves[source_name]
    level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    mapped = (
        ("basic-yisha-1", "普通攻击：一煞（一段）", "一段伤害倍率", "1251001", 1, Element.PHYSICAL),
        ("basic-yisha-2", "普通攻击：一煞（二段）", "二段伤害倍率", "1251003", 2, Element.PHYSICAL),
        ("basic-yisha-3", "普通攻击：一煞（三段）", "三段伤害倍率", "1251004", 3, Element.ELECTRIC),
        ("basic-yisha-4", "普通攻击：一煞（四段）", "四段伤害倍率", "1251005", 4, Element.ELECTRIC),
        ("basic-yisha-4-enhanced", "普通攻击：一煞（强化四段）", "四段伤害倍率（强化）", "1251006", 4, Element.ELECTRIC),
    )
    entries: list[MoveCalculationEntry] = []
    templates: list[DirectDamageEventTemplate] = []
    for key, label, parameter_name, source_id, stage, element in mapped:
        value = _source_parameter(raw_moves, source_name, parameter_name, source_id, level)
        raw_percentage = value * 100.0
        variant = MultiplierVariant(
            variant_id=MultiplierVariantId(f"variant:character:1251:{key}:raw"),
            label=parameter_name,
            parameter_name=parameter_name,
            multiplier=FixedMultiplier(Resolved(value)),
        )
        template = _direct_template(
            key=key,
            label=label,
            move_id=BASIC_YISHA_MOVE_ID,
            skill_group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            element=element,
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(f"move-entry:character:1251:{key}"),
                character_id=QINGYI_ID,
                move_id=BASIC_YISHA_MOVE_ID,
                display_name=label,
                original_text=(
                    f"{raw_move.description}\nRaw source: {source_id}, {parameter_name}, "
                    f"{raw_percentage:.1f}% at effective Basic level {level}."
                ),
                skill_group=SkillGroup.BASIC_ATTACK,
                damage_tags=_BASIC,
                multiplier_relation=MultiplierRelation.SEQUENTIAL_STAGE,
                multiplier_variants=(variant,),
                main_damage_event=template.ref,
                stage_index=stage,
            )
        )
        templates.append(template)
    return tuple(entries), tuple(templates), ()


def _moon_turn_entries(
    config: QingyiCompileConfig,
    raw_record: NanokaRawRecord,
) -> tuple[tuple[MoveCalculationEntry, ...], tuple[DirectDamageEventTemplate, ...], tuple[CalculationDiagnostic, ...]]:
    raw_moves = raw_move_index(raw_record)
    raw_move = raw_moves["普通攻击：醉花月云转"]
    level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    rush = _source_parameter(raw_moves, raw_move.name, "突进攻击伤害倍率", "1251008", level)
    finisher = _source_parameter(raw_moves, raw_move.name, "终结一击伤害倍率", "1251009", level)
    rush_pct, finisher_pct = rush * 100.0, finisher * 100.0
    rush_variant = MultiplierVariant(
        variant_id=MultiplierVariantId("variant:character:1251:moon-turn-rush:raw"),
        label="五段突进总伤害倍率",
        parameter_name="突进攻击伤害倍率",
        multiplier=FixedMultiplier(Resolved(rush)),
    )
    rush_template = _direct_template(
        key="moon-turn-rush",
        label="普通攻击：醉花月云转（突进攻击曲线）",
        move_id=BASIC_MOON_TURN_MOVE_ID,
        skill_group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        element=Element.ELECTRIC,
    )
    rush_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1251:moon-turn-rush"),
        character_id=QINGYI_ID,
        move_id=BASIC_MOON_TURN_MOVE_ID,
        display_name="普通攻击：醉花月云转（五段突进总倍率）",
        original_text=(
            f"{raw_move.description}\nUser confirmed source curve 1251008 = {rush_pct:.1f}% for all five rushes at effective Basic level {level}; it is applied once."
        ),
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(rush_variant,),
        main_damage_event=rush_template.ref,
        condition_ids=(FLASHOVER_ACTIVE,),
    )

    finisher_template = _direct_template(
        key="moon-turn-finisher",
        label="普通攻击：醉花月云转（终结一击）",
        move_id=BASIC_MOON_TURN_MOVE_ID,
        skill_group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        element=Element.ELECTRIC,
    )
    finisher_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1251:moon-turn-finisher"),
        character_id=QINGYI_ID,
        move_id=BASIC_MOON_TURN_MOVE_ID,
        display_name="普通攻击：醉花月云转（终结一击）",
        original_text=(
            f"{raw_move.description}\nIsolated final-hit curve source 1251009 = "
            f"{finisher_pct:.1f}% at effective Basic level {level}."
        ),
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1251:moon-turn-finisher:raw"),
                label="终结一击伤害倍率",
                parameter_name="终结一击伤害倍率",
                multiplier=FixedMultiplier(Resolved(finisher)),
            ),
        ),
        main_damage_event=finisher_template.ref,
        condition_ids=(FLASHOVER_ACTIVE,),
    )

    full_multiplier = rush + finisher
    full_template = _direct_template(
        key="moon-turn-full-sequence",
        label="普通攻击：醉花月云转（完整连续招式）",
        move_id=BASIC_MOON_TURN_MOVE_ID,
        skill_group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        element=Element.ELECTRIC,
    )
    full_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1251:moon-turn-full-sequence"),
        character_id=QINGYI_ID,
        move_id=BASIC_MOON_TURN_MOVE_ID,
        display_name="普通攻击：醉花月云转（完整连续招式）",
        original_text=(
            f"{raw_move.description}\nUser confirmed total sequence = source 1251008 ({rush_pct:.1f}%, all five rushes once) + source 1251009 ({finisher_pct:.1f}%, once)."
        ),
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1251:moon-turn-full-sequence:source-sum"),
                label="五段突进总倍率 + 终结一击",
                parameter_name="完整招式倍率",
                multiplier=FixedMultiplier(Resolved(full_multiplier)),
            ),
        ),
        main_damage_event=full_template.ref,
        condition_ids=(FLASHOVER_ACTIVE,),
    )
    return (
        (rush_entry, finisher_entry, full_entry),
        (rush_template, finisher_template, full_template),
        (),
    )


def _composite_ex_special(
    config: QingyiCompileConfig,
    raw_record: NanokaRawRecord,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    raw_moves = raw_move_index(raw_record)
    raw_move = raw_moves["强化特殊技：月上海棠"]
    parameter = next(item for item in raw_move.parameters if item.name == "伤害倍率")
    level = effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    source_ids = ("1251011", "1251021", "1251022")
    terms = []
    for source_id in source_ids:
        value = parameter.value_for_level(level, source_id)
        if value is None:
            raise ValueError(f"Qingyi EX source curve missing {source_id} at level {level}")
        terms.append((source_id, value / 100.0))
    total = sum(value for _, value in terms)
    expressions = " + ".join(f"{source_id}={value * 100:.1f}%" for source_id, value in terms)
    template = _direct_template(
        key="ex-special-moon-over-sea-begonia",
        label="强化特殊技：月上海棠",
        move_id=EX_SPECIAL_MOVE_ID,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tags=_EX_SPECIAL,
        element=Element.ELECTRIC,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1251:ex-special-moon-over-sea-begonia"),
        character_id=QINGYI_ID,
        move_id=EX_SPECIAL_MOVE_ID,
        display_name="强化特殊技：月上海棠（源文本相加倍率）",
        original_text=(
            f"{raw_move.description}\nRaw parameter explicitly adds at effective Special level {level}: {expressions}."
        ),
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=_EX_SPECIAL,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1251:ex-special-moon-over-sea-begonia:source-sum"),
                label="原始参数明确相加的三条曲线",
                parameter_name="伤害倍率",
                multiplier=FixedMultiplier(Resolved(total)),
            ),
        ),
        main_damage_event=template.ref,
    )
    return entry, template


def _static_electric_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1251:electric-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1251:electric-anomaly"),
        label="属性异常：感电（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=QINGYI_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=QINGYI_ID,
        history_record_source=ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ELECTRIC_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1251:electric-anomaly"),
        character_id=QINGYI_ID,
        move_id=ELECTRIC_ANOMALY_MOVE_ID,
        display_name="属性异常：感电（10秒满异常）",
        original_text=(
            "按权威规范电属性异常持续10秒，感电每秒造成125%异常效果强度；"
            "静态100%积蓄按10次跳字结算并使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1251:electric-anomaly-tick"),
                label="每跳125%（10秒10跳）",
                parameter_name="感电单跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1251:electric-disorder",
        semantic_id=DamageEventSemanticId("event:character:1251:electric-disorder"),
        label="紊乱：感电（剩余时间补偿）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=QINGYI_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=QINGYI_ID,
        history_record_source=ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ELECTRIC_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1251:electric-disorder"),
        character_id=QINGYI_ID,
        move_id=ELECTRIC_DISORDER_MOVE_ID,
        display_name="紊乱：感电（默认最大剩余时间）",
        original_text=(
            "电属性感电的紊乱基础倍率为规范默认450% + floor(t)×125%；"
            "剩余时间为可输入整数0–10秒，默认10秒，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1251:electric-disorder"),
                label="450% + floor(t) × 125%",
                parameter_name="感电紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ELECTRIC_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.25,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
    )


def compile_qingyi(
    config: QingyiCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != QINGYI_ID:
        raise ValueError("Qingyi compiler requires character:1251 raw data")
    if raw_record.element not in {"电", "电属性"}:
        raise ValueError("Qingyi raw record must identify Electric as the base element")

    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=QINGYI_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=QINGYI_REVIEWED_MAPPING,
        id_namespace="character:1251",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    basic_yisha_entries, basic_yisha_templates, basic_yisha_diagnostics = _basic_yisha_entries(
        config,
        raw_record,
    )
    entries.extend(basic_yisha_entries)
    templates.extend(basic_yisha_templates)
    diagnostics.extend(basic_yisha_diagnostics)
    moon_entries, moon_templates, moon_diagnostics = _moon_turn_entries(
        config,
        raw_record,
    )
    entries.extend(moon_entries)
    templates.extend(moon_templates)
    diagnostics.extend(moon_diagnostics)
    ex_entry, ex_template = _composite_ex_special(config, raw_record)
    entries.append(ex_entry)
    templates.append(ex_template)
    static_entries, static_templates = _static_electric_entries()
    entries.extend(static_entries)
    templates.extend(static_templates)

    conditions = [
        _condition(
            FLASHOVER_ACTIVE,
            "青衣当前处于闪络状态",
            "醉花月云转要求闪络；其生成与闪络电压时间轴不模拟。",
        ),
        _condition(
            C1_TARGET_DEBUFF_ACTIVE,
            "青衣1影对本次敌人的15秒状态当前生效",
            "仅表示已有的目标防御降低与青衣对该目标的暴击率提升，不从本次月云转反推触发。",
        ),
        _condition(
            C6_ALL_RESISTANCE_ACTIVE,
            "青衣6影造成的目标全属性抗性降低当前生效",
            "这是目标当前的全属性抗性降低状态；后续任意角色和属性伤害均可受益，不由本次招式自动开启。",
        ),
    ]
    parameters = [
        ScenarioIntegerParameter(
            parameter_id=ELECTRIC_DISORDER_REMAINING_SECONDS,
            label="本次电属性异常剩余时间（秒）",
            original_text="电属性异常感电持续10秒；规范默认紊乱基值450%，再加floor(t)×125%，范围0–10秒，默认10秒。",
            resolution=ParameterResolution.USER_SELECTED,
            value=10,
            minimum=0,
            maximum=10,
        ),
        ScenarioIntegerParameter(
            parameter_id=SUBJUGATION_STACKS,
            label="目标当前羁服层数",
            original_text="羁服上限20层；这里输入本次静态分析开始时已经存在的层数，不模拟施加、普通/精英翻倍或失衡恢复清零。",
            resolution=ParameterResolution.USER_SELECTED,
            value=20,
            minimum=0,
            maximum=20,
        ),
        ScenarioIntegerParameter(
            parameter_id=FLASHOVER_EXCESS_PERCENT,
            label="闪络电压超过75%的百分点",
            original_text="月云转消耗的闪络电压中超过75%的部分每1个百分点提升伤害1%；可输入0–25，不模拟充能过程。",
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=25,
        ),
    ]

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        QINGYI_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_per_layer = _number(
        core.description,
        r"每层\[羁服\]能够使目标的失衡易伤倍率提升(?P<value>[\d.]+)%",
        "Qingyi Core stun-vulnerability per Subjugation layer",
    ) / 100.0
    core_effect = _modifier(
        "core:subjugation-stun-vulnerability",
        core_source,
        CalculationNode.ENEMY_STUN_VULNERABILITY,
        ScenarioParameterDerivedValue(
            parameter_id=str(SUBJUGATION_STACKS),
            coefficient=Resolved(core_per_layer),
            base=Resolved(0.0),
            cap_max=Resolved(core_per_layer * 20.0),
        ),
        target=EffectTarget.ENEMY,
    )
    resource_diagnostic = _diagnostic(
        "unsupported:character:1251:core:stack-application-and-reset",
        "The calculator uses an explicit current 0–20 Subjugation-layer input; it does not replay finisher application, dash-hit additions, Perfect Dodge stacks, normal/elite doubling, or clearing when the enemy recovers from stun.",
        core.description,
        blocking=False,
    )
    daze_diagnostic = _diagnostic(
        "unsupported:character:1251:core:daze-output",
        "The damage request pipeline does not emit Daze results, so the Additional Ability's +20% Basic Daze and Cinema 2's conditional +15% Daze are not part of damage totals. Raw Daze curves remain preserved in the source record.",
        core.description,
        blocking=False,
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:subjugation-stun-vulnerability",
            core_source,
            "核心被动：羁服层数提高目标失衡易伤",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(core_effect,),
            diagnostics=(resource_diagnostic,),
        )
    ]

    # A chain hit has a separate +3% direct damage bonus per current layer;
    # it is not the Core stun-vulnerability effect.
    chain_raw = next(item for item in raw_record.moves if item.name == "连携技：太平令")
    chain_source = source_for(
        QINGYI_ID,
        "chain-subjugation-damage",
        EffectSourceType.SKILL,
        chain_raw.name,
        chain_raw.description,
    )
    chain_per_stack = _number(
        chain_raw.description,
        r"每拥有一层\[核心被动：千秋岁\]中的\[羁服\]，招式对其造成的伤害提升(?P<value>[\d.]+)%",
        "Qingyi Chain damage per Subjugation layer",
    ) / 100.0
    rules.append(
        _rule(
            "chain:damage-per-subjugation-layer",
            chain_source,
            "连携技：每层羁服提高连携伤害",
            chain_raw.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "chain:damage-per-subjugation-layer",
                    chain_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(SUBJUGATION_STACKS),
                        coefficient=Resolved(chain_per_stack),
                        base=Resolved(0.0),
                        cap_max=Resolved(chain_per_stack * 20.0),
                    ),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(QINGYI_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        MoveIdFilter(CHAIN_MOVE_ID),
                    ),
                ),
            ),
        )
    )

    # Extra Ability: eligibility is compiled from the active team; the current
    # Impact panel is read after equipment and other formal panel modifiers.
    extra_source = source_for(
        QINGYI_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    impact_threshold = _number(
        raw_record.extra_ability_description,
        r"冲击力高于(?P<value>[\d.]+)点",
        "Qingyi Additional Ability Impact threshold",
    )
    attack_per_impact = _number(
        raw_record.extra_ability_description,
        r"每超过1点冲击力会使自身的攻击力提升(?P<value>[\d.]+)点",
        "Qingyi Additional Ability Attack per Impact",
    )
    attack_cap = _number(
        raw_record.extra_ability_description,
        r"最多使自身的攻击力提升(?P<value>[\d.]+)点",
        "Qingyi Additional Ability Attack cap",
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "extra-ability:impact-to-attack",
            extra_source,
            "额外能力：当前冲击力转攻击力",
            raw_record.extra_ability_description,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:impact-to-attack",
                    extra_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    PanelStatDerivedValue(
                        source_character_id=QINGYI_ID,
                        source_node=CalculationNode.CHARACTER_CURRENT_IMPACT,
                        coefficient=Resolved(attack_per_impact),
                        threshold=Resolved(impact_threshold),
                        cap_max=Resolved(attack_cap),
                    ),
                    target=EffectTarget.SELF,
                ),
            ),
            diagnostics=(daze_diagnostic,),
        )
    )

    # Flashover excess is an event multiplier on both raw damage components of
    # Moon Turn. Daze's separate 0.5% coefficient is documented as unsupported.
    moon_raw = next(item for item in raw_record.moves if item.name == "普通攻击：醉花月云转")
    moon_source = source_for(
        QINGYI_ID,
        "moon-turn-flashover-excess",
        EffectSourceType.SKILL,
        moon_raw.name,
        moon_raw.description,
    )
    rules.append(
        _rule(
            "basic:moon-turn-flashover-damage",
            moon_source,
            "普通攻击：醉花月云转消耗过量闪络电压提高伤害",
            moon_raw.description,
            RuleEligibility.ELIGIBLE,
            conditions=(FLASHOVER_ACTIVE,),
            effects=(
                _modifier(
                    "basic:moon-turn-flashover-damage",
                    moon_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(FLASHOVER_EXCESS_PERCENT),
                        coefficient=Resolved(0.01),
                        base=Resolved(0.0),
                        cap_max=Resolved(0.25),
                    ),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(QINGYI_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        MoveIdFilter(BASIC_MOON_TURN_MOVE_ID),
                    ),
                    operation=EffectOperation.ADD,
                ),
            ),
            diagnostics=(
                _diagnostic(
                    "unsupported:character:1251:moon-turn:flashover-daze",
                    "The raw text also increases Daze by 0.5% per excess Flashover-voltage percentage point; Daze values are outside this damage-only request.",
                    moon_raw.description,
                    blocking=False,
                ),
            ),
        )
    )

    # C1 has two independent numeric effects in one selected current-target
    # status: defense reduction benefits any ally; crit rate is Qingyi-owned.
    c1 = raw_record.mindscapes[0]
    c1_source = source_for(QINGYI_ID, "cinema1", EffectSourceType.CINEMA, c1.name, c1.description)
    c1_defense_reduction = _number(
        c1.description,
        r"本次招式命中的敌人防御力降低(?P<value>[\d.]+)%",
        "Qingyi Cinema 1 defense reduction",
    ) / 100.0
    c1_crit_rate = _number(
        c1.description,
        r"自身对该目标的暴击率提升(?P<value>[\d.]+)%",
        "Qingyi Cinema 1 target-specific crit rate",
    ) / 100.0
    c1_rules = (
        _rule(
            "cinema1:target-defense-and-qingyi-crit",
            c1_source,
            "1影：当前目标防御降低与青衣对其暴击率提高",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            conditions=(C1_TARGET_DEBUFF_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:target-defense-reduction",
                    c1_source,
                    CalculationNode.ENEMY_DEFENSE_REDUCTION,
                    Resolved(c1_defense_reduction),
                    target=EffectTarget.ENEMY,
                ),
                _modifier(
                    "cinema1:qingyi-target-crit-rate",
                    c1_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(c1_crit_rate),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(QINGYI_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                    ),
                ),
            ),
            diagnostics=(
                _diagnostic(
                    "unsupported:character:1251:cinema1:flashover-timeline",
                    "C1 restores Flashover voltage on battle entry and increases later accumulation by 30%; the calculator treats the defense/crit effects as a current 15-second target status and does not replay voltage or duration.",
                    c1.description,
                    blocking=False,
                ),
            ),
        ),
    )
    rules.extend(c1_rules)

    c2 = raw_record.mindscapes[1]
    c2_source = source_for(QINGYI_ID, "cinema2", EffectSourceType.CINEMA, c2.name, c2.description)
    c2_multiplier = _number(
        c2.description,
        r"效果提升至原本的(?P<value>[\d.]+)%",
        "Qingyi Cinema 2 Core coefficient multiplier",
    ) / 100.0
    rules.append(
        _rule(
            "cinema2:subjugation-vulnerability-enhancement",
            c2_source,
            "2影：羁服每层失衡易伤提升至原本的135%",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:subjugation-stun-vulnerability-extra",
                    c2_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(SUBJUGATION_STACKS),
                        coefficient=Resolved(core_per_layer * (c2_multiplier - 1.0)),
                        base=Resolved(0.0),
                        cap_max=Resolved(core_per_layer * (c2_multiplier - 1.0) * 20.0),
                    ),
                    target=EffectTarget.ENEMY,
                ),
            ),
            diagnostics=(daze_diagnostic,),
        )
    )

    chain_diagnostic = _diagnostic(
        "unsupported:character:1251:cinema2:max-stack-daze",
        "Cinema 2's additional +15% Daze against a target already at the 20-layer cap is not emitted because the damage request has no Daze calculation output.",
        c2.description,
        blocking=False,
    )
    rules.append(
        _rule(
            "cinema2:max-subjugation-daze",
            c2_source,
            "2影：羁服满层命中提升青衣失衡值",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            diagnostics=(chain_diagnostic,),
        )
    )

    for cinema in (3, 5):
        mindscape = raw_record.mindscapes[cinema - 1]
        source = source_for(
            QINGYI_ID,
            f"cinema{cinema}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{cinema}:skill-levels",
                source,
                f"{cinema}影：技能等级提高",
                mindscape.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= cinema else RuleEligibility.INELIGIBLE,
                diagnostics=(
                    _diagnostic(
                        f"unsupported:character:1251:cinema{cinema}:level-already-applied",
                        "The source's +2 skill levels are applied to raw source curves before event construction; no separate damage multiplier is emitted.",
                        mindscape.description,
                        blocking=False,
                    ),
                ),
            )
        )

    c4 = raw_record.mindscapes[3]
    c4_source = source_for(QINGYI_ID, "cinema4", EffectSourceType.CINEMA, c4.name, c4.description)
    shield_diag = _diagnostic(
        "unsupported:character:1251:cinema4:shield-and-energy",
        "Cinema 4 grants a shield based on max HP when entering/leaving Flashover and can restore 5 energy on a refresh; shield/resource outcomes are not part of the damage request.",
        c4.description,
        blocking=False,
    )
    rules.append(
        _rule(
            "cinema4:shield-and-energy",
            c4_source,
            "4影：闪络护盾与能量恢复",
            c4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            diagnostics=(shield_diag,),
        )
    )

    c6 = raw_record.mindscapes[5]
    c6_source = source_for(QINGYI_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
    c6_crit_damage = _number(
        c6.description,
        r"暴击伤害额外提升(?P<value>[\d.]+)%",
        "Qingyi Cinema 6 Moon Turn crit damage",
    ) / 100.0
    c6_resistance_reduction = _number(
        c6.description,
        r"全属性伤害抗性降低(?P<value>[\d.]+)%",
        "Qingyi Cinema 6 all-element resistance reduction",
    ) / 100.0
    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema6:moon-turn-crit-damage",
            c6_source,
            "6影：醉花月云转暴击伤害提高",
            c6.description,
            c6_eligibility,
            effects=(
                _modifier(
                    "cinema6:moon-turn-crit-damage",
                    c6_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c6_crit_damage),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(QINGYI_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        MoveIdFilter(BASIC_MOON_TURN_MOVE_ID),
                    ),
                ),
            ),
            diagnostics=(
                _diagnostic(
                    "unsupported:character:1251:cinema6:interrupt-rank",
                    "Cinema 6 also improves Moon Turn's interruption level; interruption is not calculated in the damage-only request.",
                    c6.description,
                    blocking=False,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "cinema6:all-resistance-reduction-active",
            c6_source,
            "6影：目标全属性抗性降低当前生效",
            c6.description,
            c6_eligibility,
            conditions=(C6_ALL_RESISTANCE_ACTIVE,),
            effects=(
                _modifier(
                    "cinema6:all-resistance-reduction",
                    c6_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(c6_resistance_reduction),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    )

    entry_source = source_for(
        QINGYI_ID,
        "nanoka-3.2",
        EffectSourceType.SKILL,
        raw_record.name,
        f"source_version={raw_record.source_version}; source_url={raw_record.source_url}",
    )
    return CharacterCalculationDefinition(
        character_id=QINGYI_ID,
        role=CharacterRole.STUN,
        base_element=Element.ELECTRIC,
        source=entry_source,
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=tuple(conditions),
        scenario_parameters=tuple(parameters),
        damage_event_templates=tuple(templates),
        diagnostics=tuple(
            diagnostics
            + [
                _diagnostic(
                    "unsupported:character:1251:daze-values",
                    "Nanoka provides Daze multipliers for the mapped damage moves and three Daze-only Assist curves; the current calculate_payload presentation contract outputs damage only, so no Daze damage entry is fabricated.",
                    "Nanoka Qingyi raw parameters Prop:1002 and Assist skills 1251017–1251019.",
                    blocking=False,
                )
            ]
        ),
    )


__all__ = ["compile_qingyi", "load_raw_record"]
