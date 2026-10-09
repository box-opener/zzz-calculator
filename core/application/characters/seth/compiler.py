"""Compile Seth's reviewed Nanoka 3.2 source into calculation contracts."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CharacterId,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
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
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ParameterResolution, ScenarioCondition, ScenarioIntegerParameter
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
    UnresolvedDamageEventTemplate,
)
from .config import SethCompileConfig
from .reviewed import (
    SETH_BASIC_MOVE_ID,
    SETH_BASIC_SHOCK_FULL_MOVE_ID,
    SETH_ELECTRIC_ANOMALY_MOVE_ID,
    SETH_ELECTRIC_ANOMALY_RECORD_ID,
    SETH_ELECTRIC_DISORDER_MOVE_ID,
    SETH_ID,
    SETH_REVIEWED_MAPPING,
)


_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:seth:electric-disorder-remaining-seconds"
)
_BASIC_FINISHER_TEMPLATE_ID = EventTemplateId(
    "template:character:1271:basic-shock-finisher:main"
)
_BASIC_SHOCK_FULL_TEMPLATE_ID = EventTemplateId(
    "template:character:1271:basic-shock-full:main"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(SETH_ID, key, kind, label, text)


def _condition(condition_id: ScenarioConditionId, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
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
    conditions=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1271:{key}"),
        owner=SETH_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        diagnostics=tuple(diagnostics),
    )


def _shield_ap_effect(
    recipient: CharacterId,
    source: RuleSource,
    amount: float,
) -> ModifierEffect:
    recipient_key = str(recipient).replace(":", "-")
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1271:core:shield-ap:{recipient_key}"),
            source=source,
            owner=SETH_ID,
            target=EffectTarget.RECIPIENT,
            recipient_character_id=recipient,
            snapshot_rule=SnapshotRule.SETTLEMENT,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(amount),
        ),
    )


def _unresolved_basic_entries(
    raw: NanokaRawRecord,
    config: SethCompileConfig,
) -> tuple[tuple[MoveCalculationEntry, ...], tuple[UnresolvedDamageEventTemplate, ...], tuple[CalculationDiagnostic, ...]]:
    raw_moves = raw_move_index(raw)
    source_move = raw_moves["普通攻击：雷霆击"]
    entries: list[MoveCalculationEntry] = []
    templates: list[UnresolvedDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    stage_labels = ("一段", "二段", "三段", "四段")
    for stage, skill_id in enumerate(("1271001", "1271002", "1271003", "1271004"), start=1):
        stage_label = stage_labels[stage - 1]
        key = f"basic-stage-{stage}-element-unresolved"
        ratio = raw_multiplier(
            raw_moves,
            source_move.name,
            f"{stage_label}伤害倍率",
            effective_skill_level(config, SkillGroup.BASIC_ATTACK),
            f"{SETH_ID}:{key}",
            [],
            source_skill_id=skill_id,
        )
        if isinstance(ratio, Unresolved):
            raise ValueError(f"Seth source is missing the {stage_label} damage curve")
        label = f"普通攻击：雷霆击（{stage_label}，元素待确认）"
        unresolved = Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_TEXT,
            notes="原文只说明四段攻击合计造成物理与电属性伤害，未说明各段元素；保留本段源倍率，不生成伤害事件。",
            original_text=source_move.description,
        )
        ref = DamageEventTemplateRef(
            template_id=EventTemplateId(f"template:character:1271:{key}:main"),
            semantic_id=DamageEventSemanticId(f"event:character:1271:{key}:main"),
            label=label,
            damage_type=DamageType.DIRECT,
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
            element=None,
        )
        template = UnresolvedDamageEventTemplate(
            ref=ref,
            damage_dealer=SETH_ID,
            move_id=SETH_BASIC_MOVE_ID,
            unresolved=unresolved,
        )
        diagnostic = CalculationDiagnostic(
            diagnostic_id=DiagnosticId(f"unsupported:character:1271:{key}:element"),
            kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
            message=unresolved.notes,
            blocking=True,
            original_text=source_move.description,
        )
        entry = MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1271:{key}"),
            character_id=SETH_ID,
            move_id=SETH_BASIC_MOVE_ID,
            display_name=label,
            original_text=source_move.description,
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
            multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
            multiplier_variants=(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(f"variant:character:1271:{key}:known-ratio"),
                    label=f"已知源倍率{ratio:.3%}（元素待确认）",
                    parameter_name=f"{stage_label}伤害倍率",
                    multiplier=FixedMultiplier(Resolved(ratio)),
                ),
            ),
            main_damage_event=ref,
            diagnostics=(diagnostic,),
        )
        entries.append(entry)
        templates.append(template)
        diagnostics.append(diagnostic)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def _full_basic_shock_entry(raw: NanokaRawRecord, config: SethCompileConfig):
    source_move = raw_move_index(raw)["普通攻击：雷霆击-感电"]
    level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    raw_moves = raw_move_index(raw)
    continuous_ratio = raw_multiplier(
        raw_moves,
        source_move.name,
        "连续攻击伤害倍率",
        level,
        f"{SETH_ID}:basic-shock-full-continuous",
        [],
        source_skill_id="1271005",
    )
    finisher_ratio = raw_multiplier(
        raw_moves,
        source_move.name,
        "终结一击伤害倍率",
        level,
        f"{SETH_ID}:basic-shock-full-finisher",
        [],
        source_skill_id="1271006",
    )
    if isinstance(continuous_ratio, Unresolved) or isinstance(finisher_ratio, Unresolved):
        raise ValueError("Seth source is missing a Basic Shock sequence damage curve")

    total_ratio = continuous_ratio + finisher_ratio
    label = "普通攻击：雷霆击-感电（完整攻击：持续攻击+终结一击）"
    ref = DamageEventTemplateRef(
        template_id=_BASIC_SHOCK_FULL_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1271:basic-shock-full:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        element=Element.ELECTRIC,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=SETH_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(SETH_ID),
        crit_rule=StandardCritRule(SETH_ID),
        move_id=SETH_BASIC_SHOCK_FULL_MOVE_ID,
    )

    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1271:basic-shock-full"),
        character_id=SETH_ID,
        move_id=SETH_BASIC_SHOCK_FULL_MOVE_ID,
        display_name=label,
        original_text=source_move.description,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1271:basic-shock-full:total"),
                label=f"持续攻击{continuous_ratio:.3%} + 终结一击{finisher_ratio:.3%}",
                parameter_name="完整感电普通攻击总倍率",
                multiplier=FixedMultiplier(Resolved(total_ratio)),
            ),
        ),
        main_damage_event=ref,
    )
    return entry, template


def _static_electric_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1271:electric-shock"),
        semantic_id=DamageEventSemanticId("event:character:1271:electric-shock"),
        label="属性异常：感电（单跳125%，10秒10跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=SETH_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=SETH_ID,
        history_record_source=AnomalyRecordId(SETH_ELECTRIC_ANOMALY_RECORD_ID),
        crit_rule=NoCritRule(),
        move_id=SETH_ELECTRIC_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1271:electric-shock"),
        character_id=SETH_ID,
        move_id=SETH_ELECTRIC_ANOMALY_MOVE_ID,
        display_name="属性异常：感电（单跳125%，10秒10跳）",
        original_text="按静态100%电属性异常记录计算；感电每跳125%，持续10秒共10跳，异常伤害不暴击。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1271:electric-shock-tick"),
                label="感电单跳125% × 10",
                parameter_name="感电单跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1271:electric-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1271:electric-disorder"),
        label="紊乱：感电（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=SETH_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=SETH_ID,
        history_record_source=AnomalyRecordId(SETH_ELECTRIC_ANOMALY_RECORD_ID),
        crit_rule=NoCritRule(),
        move_id=SETH_ELECTRIC_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1271:electric-disorder"),
        character_id=SETH_ID,
        move_id=SETH_ELECTRIC_DISORDER_MOVE_ID,
        display_name="紊乱：感电（当前剩余时间）",
        original_text="感电紊乱倍率为450% + floor(t)×125%；输入当前剩余时间，不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1271:electric-disorder"),
                label="450% + floor(t) × 125%",
                parameter_name="电紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.25,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_DISORDER_REMAINING_SECONDS,
        label="电异常剩余持续时间（秒）",
        original_text="使用当前剩余时间，范围0–10秒；不模拟感电时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _unresolved_c6_extra(raw: NanokaRawRecord):
    cinema6 = raw.mindscapes[5]
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes="已知追加倍率为500%赛斯当前攻击力、必定暴击且额外提高60%暴击伤害；追加事件的元素及技能标签/分组尚未确认，因此不创建伤害事件。",
        original_text=cinema6.description,
    )
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1271:cinema6-basic-shock-extra-unresolved"),
        semantic_id=DamageEventSemanticId("event:character:1271:cinema6-basic-shock-extra-unresolved"),
        label="6影：雷霆击-感电终结一击追加伤害（500%攻击力，类型待确认）",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=None,
    )
    template = UnresolvedDamageEventTemplate(
        ref=ref,
        damage_dealer=SETH_ID,
        move_id=None,
        unresolved=unresolved,
    )
    diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1271:cinema6:extra-damage-identity"),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message=unresolved.notes,
        blocking=True,
        original_text=cinema6.description,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1271:cinema6-basic-shock-extra"),
        character_id=SETH_ID,
        move_id=None,
        display_name=ref.label,
        original_text=cinema6.description,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1271:cinema6-basic-shock-extra"),
                label="500%攻击力（必暴；额外暴击伤害+60%）",
                parameter_name="追加伤害倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=ref,
        diagnostics=(diagnostic,),
    )
    return entry, template, diagnostic


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(SETH_ID))


def compile_seth(
    config: SethCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=SETH_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=SETH_REVIEWED_MAPPING,
    )
    entries = list(direct_entries)
    templates: list[object] = list(direct_templates)
    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []
    diagnostics = list(direct_diagnostics)

    full_shock_entry, full_shock_template = _full_basic_shock_entry(
        raw_record,
        config,
    )
    entries.append(full_shock_entry)
    templates.append(full_shock_template)

    unresolved_basics, unresolved_basic_templates, unresolved_basic_diagnostics = (
        _unresolved_basic_entries(raw_record, config)
    )
    entries.extend(unresolved_basics)
    templates.extend(unresolved_basic_templates)
    diagnostics.extend(unresolved_basic_diagnostics)

    shield_core = raw_record.core_levels[config.core_level - 1]
    shield_ap = _number(
        shield_core.description,
        r"持有者的异常精通提升(?P<value>[\d.]+)点",
        "Seth shield holder anomaly proficiency",
    )
    shield_source = _source(
        "core-passive:shield-holder-anomaly-proficiency",
        EffectSourceType.CORE_PASSIVE,
        "核心被动：守望者",
        shield_core.description,
    )
    for recipient in config.shield_recipient_ids:
        suffix = str(recipient).replace(":", "-")
        recipient_label = dict(config.shield_recipient_names).get(recipient, str(recipient))
        condition_id = ScenarioConditionId(f"condition:seth:shield-active:{suffix}")
        conditions.append(
            _condition(
                condition_id,
                f"{recipient_label}当前持有匪石之盾",
                shield_core.description,
            )
        )
        rules.append(
            _rule(
                f"core:shield-holder-ap:{suffix}",
                shield_source,
                f"当前持有匪石之盾：异常精通+{shield_ap:g}",
                shield_core.description,
                RuleEligibility.ELIGIBLE,
                effects=(_shield_ap_effect(recipient, shield_source, shield_ap),),
                conditions=(condition_id,),
            )
        )

    # The Extra Ability changes anomaly buildup resistance, which this
    # calculator does not simulate as a duration/timeline. Preserve the source
    # statement as a non-blocking note rather than turning it into damage.
    extra_source = _source(
        "extra-ability:anomaly-buildup-resistance",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_note = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1271:extra-ability:buildup-resistance-duration"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message="The Extra Ability reduces the target's all-element anomaly buildup resistance after its trigger. Buildup and the 20-second duration are not simulated in damage results.",
        blocking=False,
        original_text=raw_record.extra_ability_description,
    )
    rules.append(
        _rule(
            "extra-ability:buildup-resistance-source-only",
            extra_source,
            "额外能力：全属性异常积蓄抗性降低（不模拟积蓄）",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            diagnostics=(extra_note,),
        )
    )

    for cinema_index in range(5):
        cinema = raw_record.mindscapes[cinema_index]
        level = cinema_index + 1
        if level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    _source(f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description),
                    f"{level}影：技能等级+2",
                    cinema.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                )
            )
            continue
        note_message = {
            1: "This Cinema increases shield capacity and preserves the Core anomaly-proficiency effect briefly after the shield expires; shield timing is not simulated.",
            2: "This Cinema grants Will on entry and increases Shock anomaly buildup; resource history and buildup are not simulated.",
            4: "This Cinema increases Parry Assist Daze; Daze is not represented in damage results.",
        }[level]
        note = CalculationDiagnostic(
            diagnostic_id=DiagnosticId(f"unsupported:character:1271:cinema{level}:source-only"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message=note_message,
            blocking=False,
            original_text=cinema.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:source-only",
                _source(f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description),
                f"{level}影：来源效果不在伤害结果中模拟",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                diagnostics=(note,),
            )
        )

    c6 = raw_record.mindscapes[5]
    c6_source = _source("cinema6:basic-shock-extra", EffectSourceType.CINEMA, c6.name, c6.description)
    c6_entry, c6_template, c6_diagnostic = _unresolved_c6_extra(raw_record)
    if config.cinema_level >= 6:
        entries.append(c6_entry)
        templates.append(c6_template)
        diagnostics.append(c6_diagnostic)
    c6_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1271:cinema6:basic-shock-extra"),
            source=c6_source,
            owner=SETH_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(SETH_ID),
                AnyFilter(
                    (
                        EventTemplateIdFilter(_BASIC_FINISHER_TEMPLATE_ID),
                        EventTemplateIdFilter(_BASIC_SHOCK_FULL_TEMPLATE_ID),
                    )
                ),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=c6_template.unresolved,
            unique_per_source_event=True,
        ),
    )
    rules.append(
        _rule(
            "cinema6:basic-shock-extra",
            c6_source,
            "6影：雷霆击-感电终结一击追加伤害（事件类型待确认）",
            c6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            effects=(c6_effect,) if config.cinema_level >= 6 else (),
        )
    )

    anomaly_entries, anomaly_templates, disorder_parameter = _static_electric_entries(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)

    parry_source = next(item for item in raw_record.moves if item.name == "招架支援：迅雷盾")
    parry_note = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1271:parry-assist:daze-only"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message="This Parry Assist source lists Daze values but no damage ratio; no damage event is created.",
        blocking=False,
        original_text=parry_source.description,
    )
    rules.append(
        _rule(
            "parry-assist:daze-source-only",
            _source("parry-assist:daze-source-only", EffectSourceType.SKILL, parry_source.name, parry_source.description),
            "招架支援：迅雷盾（仅失衡倍率）",
            parry_source.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(parry_note,),
        )
    )

    return build_definition(
        character_id=SETH_ID,
        role=CharacterRole.DEFENSE,
        element=Element.ELECTRIC,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(disorder_parameter,),
        diagnostics=diagnostics,
    )


def _validate_raw(raw: NanokaRawRecord, config: SethCompileConfig) -> None:
    if raw.character_id != SETH_ID or raw.name != "赛斯" or raw.code_name != "Seth":
        raise ValueError("unexpected Seth raw identity")
    if raw.specialty != "防护" or raw.element != "电属性" or raw.rarity != 3:
        raise ValueError("unexpected Seth role, element, or rank")
    if raw.faction != "新艾利都治安局" or raw.icon != "IconRole30":
        raise ValueError("unexpected Seth faction or icon")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1271.json":
        raise ValueError("Seth provenance must identify live Nanoka 3.2 character 1271")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Seth source must contain seven Core levels and six Cinemas")
    if raw.potential_details:
        raise ValueError("Seth source has no reviewed Potential levels")
    if config.character_id != raw.character_id:
        raise ValueError("Seth config and raw IDs must match")


__all__ = ["compile_seth", "load_raw_record"]
