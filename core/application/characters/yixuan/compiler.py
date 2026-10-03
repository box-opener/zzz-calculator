"""Compile Nanoka's raw Yixuan record into reviewed penetration events."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CharacterRole,
    CalculationNode,
    CreatedByEffectFilter,
    CurrentPenetrationForceValueSource,
    DamageDealerFilter,
    DamageTag,
    DamageTagFilter,
    DamageSubtype,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventCreationResult,
    EventSelector,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    MoveId,
    MoveIdFilter,
    NoCritRule,
    ModifierEffect,
    ModifierResult,
    NotFilter,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
    StateId,
    StatePresentCondition,
    Unresolved,
    UnresolvedReason,
    SkillGroup,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import (
    DamageEventSemanticId,
    DiagnosticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
)
from ...moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import effective_skill_level, raw_move_index, source_for
from ..nanoka_source import NanokaRawRecord, NanokaRawMoveRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
    PenetrationDamageEventTemplate,
)
from .config import YixuanCompileConfig
from .reviewed import (
    ASSIST_FOLLOW_UP_MOVE_ID,
    BASIC_SPECIAL_MOVE_ID,
    BASIC_XIAOYUN_MOVE_ID,
    C2_INK_BREAK_READY,
    C6_EXTRA_ULTIMATE_ACTIVE,
    CHAIN_MOVE_ID,
    DASH_ATTACK_MOVE_ID,
    DODGE_COUNTER_MOVE_ID,
    EX_CLOUD_MOVE_ID,
    EX_INK_BURST_MOVE_ID,
    EX_MARK_CHARGE_EXTRA,
    EX_MARK_EXTRA_MOVE_ID,
    EX_MARK_MOVE_ID,
    EX_QINGMING_BREAK_MOVE_ID,
    EX_TALISMAN_BREAK_MOVE_ID,
    EX_XIAOYUN_BREAK_MOVE_ID,
    FOCUSED_MIND_ACTIVE,
    INK_ARRAY_MOVE_ID,
    INK_SHADOW_MOVE_ID,
    MATRIX_MAX_DURATION,
    PERFECT_SUPPORT_SWITCH_OUT,
    QUICK_ASSIST_MOVE_ID,
    QINGMING_SHOCK_MOVE_ID,
    ULTIMATE_QINGMING_MOVE_ID,
    ULTIMATE_TALISMAN_MOVE_ID,
    XUANMO_ANOMALY_MOVE_ID,
    XUANMO_ANOMALY_RECORD_ID,
    XUANMO_DISORDER_MOVE_ID,
    YIXUAN_ID,
    YIXUAN_REVIEWED_MAPPING,
)


_ENEMY_STUNNED_STATE_ID = StateId("state:enemy:stunned")
_LIGHTNING_C1_EFFECT_ID = EffectId("effect:character:1371:cinema1:lightning")
_LIGHTNING_C1_SELECTION_TEMPLATE_ID = EventTemplateId(
    "template:character:1371:cinema1-lightning-selectable"
)


def _condition(
    condition_id,
    label: str,
    original_text: str,
    value: bool | None = None,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(
    raw: NanokaRawRecord,
    source_key: str,
    source_type: EffectSourceType,
    label: str,
    raw_text: str | None,
) -> RuleSource:
    return source_for(YIXUAN_ID, source_key, source_type, label, raw_text)


def _rule(
    rule_key: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1371:{rule_key}"),
        owner=YIXUAN_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
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
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1371:{effect_key}"),
            source=source,
            owner=YIXUAN_ID,
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


def _percentage(text: str, pattern: str, *, subject: str) -> float:
    matches = tuple(re.finditer(pattern, text, re.DOTALL))
    if len(matches) != 1:
        raise ValueError(
            f"{subject} must contain one reviewed percentage; found {len(matches)}"
        )
    return float(matches[0].group("value")) / 100.0


def _raw_mindscape(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Yixuan record is missing mindscape {level}") from exc


def _raw_move(raw_moves: dict[str, NanokaRawMoveRecord], name: str):
    try:
        return raw_moves[name]
    except KeyError as exc:
        raise ValueError(f"raw Yixuan record is missing move {name!r}") from exc


def _parameter_multiplier(
    raw_move: NanokaRawMoveRecord,
    parameter_name: str,
    source_skill_id: str,
    level: int,
    *,
    subject: str,
) -> tuple[FixedMultiplier | Unresolved, CalculationDiagnostic | None]:
    parameter = next(
        (item for item in raw_move.parameters if item.name == parameter_name),
        None,
    )
    value = (
        parameter.value_for_level(level, source_skill_id)
        if parameter is not None and parameter.format == "%"
        else None
    )
    if value is None:
        note = (
            f"{subject}: missing source curve {source_skill_id} for "
            f"{parameter_name!r} at skill level {level}"
        )
        return (
            Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=note,
                original_text=parameter_name,
            ),
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(f"data:character:1371:{subject}:{level}"),
                kind=DiagnosticKind.MISSING_DATA,
                message=note,
                blocking=True,
                original_text=parameter_name,
            ),
        )
    return FixedMultiplier(Resolved(value / 100.0)), None


def _typed_template(
    *,
    key: str,
    label: str,
    move_id: MoveId,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    source_rule_item_id: RuleItemId | None = None,
) -> PenetrationDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1371:{key}",
        semantic_id=DamageEventSemanticId(f"event:character:1371:{key}"),
        label=label,
        damage_type=DamageType.PENETRATION,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=Element.XUANMO,
        source_rule_item_id=source_rule_item_id,
    )
    return PenetrationDamageEventTemplate(
        ref=ref,
        damage_dealer=YIXUAN_ID,
        element=Element.XUANMO,
        base_source=CurrentPenetrationForceValueSource(YIXUAN_ID),
        crit_rule=StandardCritRule(YIXUAN_ID),
        move_id=move_id,
    )


def _compile_main_moves(raw: NanokaRawRecord, config: YixuanCompileConfig):
    raw_moves = raw_move_index(raw)
    entries: list[MoveCalculationEntry] = []
    templates: list[PenetrationDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for spec in YIXUAN_REVIEWED_MAPPING.moves:
        raw_move = _raw_move(raw_moves, spec.source_name)
        level = effective_skill_level(config, spec.skill_group)
        variants: list[MultiplierVariant] = []
        entry_diagnostics: list[CalculationDiagnostic] = []
        for parameter_spec in spec.parameters:
            assert parameter_spec.source_skill_id is not None
            multiplier, diagnostic = _parameter_multiplier(
                raw_move,
                parameter_spec.parameter_name,
                parameter_spec.source_skill_id,
                level,
                subject=spec.entry_key,
            )
            if diagnostic is not None:
                entry_diagnostics.append(diagnostic)
            variants.append(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1371:{spec.entry_key}:damage"
                    ),
                    label=parameter_spec.parameter_name,
                    parameter_name=parameter_spec.parameter_name,
                    multiplier=multiplier,
                )
            )
        template = _typed_template(
            key=f"{spec.entry_key}:main",
            label=spec.display_name,
            move_id=spec.move_id,
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
        )
        entry = MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1371:{spec.entry_key}"),
            character_id=YIXUAN_ID,
            move_id=spec.move_id,
            display_name=spec.display_name,
            original_text=raw_move.description or spec.source_name,
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
            multiplier_relation=spec.multiplier_relation,
            multiplier_variants=tuple(variants),
            main_damage_event=template.ref,
            stage_index=spec.stage_index,
            condition_ids=spec.condition_ids,
            diagnostics=tuple(entry_diagnostics),
        )
        entries.append(entry)
        templates.append(template)
        diagnostics.extend(entry_diagnostics)
    return entries, templates, diagnostics, raw_moves


def _make_derived(
    *,
    raw_record: NanokaRawRecord,
    key: str,
    label: str,
    move_id: MoveId,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    multiplier: FixedMultiplier | Unresolved,
    parent_move_id: MoveId,
    source_key: str,
    source_text: str,
    condition_id=None,
    eligibility: RuleEligibility = RuleEligibility.ELIGIBLE,
):
    rule_id = RuleItemId(f"rule:character:1371:{source_key}")
    source = _source(
        raw_record,
        source_key,
        EffectSourceType.SKILL,
        label,
        source_text,
    )
    template = _typed_template(
        key=key,
        label=label,
        move_id=move_id,
        skill_group=skill_group,
        damage_tags=damage_tags,
        source_rule_item_id=rule_id,
    )
    event_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1371:{source_key}"),
            source=source,
            owner=YIXUAN_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.PENETRATION),
                DamageDealerFilter(YIXUAN_ID),
                MoveIdFilter(parent_move_id),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template.ref.template_id,
        ),
    )
    rule = _rule(
        source_key,
        source,
        label,
        source_text,
        eligibility,
        effects=(event_effect,),
        condition_ids=(() if condition_id is None else (condition_id,)),
    )
    derived = DerivedDamageEventTemplateRef(
        template=template.ref,
        multiplier=multiplier,
    )
    return template, rule, derived


def _fixed_entry(
    *,
    key: str,
    move_id: MoveId,
    label: str,
    original_text: str,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    multiplier: FixedMultiplier,
    condition_id,
):
    template = _typed_template(
        key=f"{key}:main",
        label=label,
        move_id=move_id,
        skill_group=skill_group,
        damage_tags=damage_tags,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1371:{key}"),
        character_id=YIXUAN_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=skill_group,
        damage_tags=damage_tags,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1371:{key}:damage"),
                label="1200%贯穿力",
                parameter_name="贯穿力伤害倍率",
                multiplier=multiplier,
            ),
        ),
        main_damage_event=template.ref,
        condition_ids=(condition_id,),
    )
    return entry, template


def _xuanmo_anomaly_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1371:xuanmo-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1371:xuanmo-anomaly"),
        label="属性异常：玄墨侵蚀",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.XUANMO,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=YIXUAN_ID,
        element=Element.XUANMO,
        anomaly_triggerer=YIXUAN_ID,
        history_record_source=XUANMO_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=XUANMO_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1371:xuanmo-anomaly"),
        character_id=YIXUAN_ID,
        move_id=XUANMO_ANOMALY_MOVE_ID,
        display_name="属性异常：玄墨侵蚀",
        original_text=(
            f"{raw.special_element}拥有独立的属性异常积蓄槽；按规范的以太/玄墨侵蚀"
            "规则，取10秒满持续时间，按20次62.5%伤害跳字结算。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1371:xuanmo-anomaly:tick"
                ),
                label="每跳62.5%（满10秒共20跳）",
                parameter_name="玄墨侵蚀单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.625)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1371:xuanmo-disorder",
        semantic_id=DamageEventSemanticId("event:character:1371:xuanmo-disorder"),
        label="紊乱：玄墨侵蚀",
        damage_type=DamageType.DISORDER,
        damage_subtype=None,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.XUANMO,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=YIXUAN_ID,
        element=Element.XUANMO,
        disorder_triggerer=YIXUAN_ID,
        history_record_source=XUANMO_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=XUANMO_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1371:xuanmo-disorder"),
        character_id=YIXUAN_ID,
        move_id=XUANMO_DISORDER_MOVE_ID,
        display_name="紊乱：玄墨侵蚀",
        original_text=(
            "按10秒最大剩余时间结算：450%紊乱基础倍率 + "
            "20次侵蚀补偿（每次62.5%）= 1700%。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1371:xuanmo-disorder:maximum-duration"
                ),
                label="450% + 20 × 62.5% = 1700%",
                parameter_name="玄墨侵蚀满持续时间紊乱倍率",
                multiplier=FixedMultiplier(Resolved(17.0)),
            ),
        ),
        main_damage_event=disorder_ref,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
    )


def _lightning_event(
    *,
    key: str,
    effect_id: EffectId,
    source: RuleSource,
    rule_id: RuleItemId,
    trigger: EventSelector | None = None,
    filters=(),
    percent: float,
    unique_per_source_event: bool = False,
) -> tuple[EventCreationEffect, PenetrationDamageEventTemplate, DerivedDamageEventTemplateRef]:
    template_ref = DamageEventTemplateRef(
        template_id=f"template:character:1371:{key}",
        semantic_id=DamageEventSemanticId(f"event:character:1371:{key}"),
        label="落雷：玄墨贯穿伤害",
        damage_type=DamageType.PENETRATION,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.XUANMO,
        source_rule_item_id=rule_id,
    )
    template = PenetrationDamageEventTemplate(
        ref=template_ref,
        damage_dealer=YIXUAN_ID,
        element=Element.XUANMO,
        base_source=CurrentPenetrationForceValueSource(YIXUAN_ID),
        crit_rule=StandardCritRule(YIXUAN_ID),
        move_id=None,
    )
    creation = EventCreationEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=source,
            owner=YIXUAN_ID,
            target=EffectTarget.TEAM if trigger is None else EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            trigger=trigger,
            filters=tuple(filters),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_ref.template_id,
            unique_per_source_event=unique_per_source_event,
        ),
    )
    derived = DerivedDamageEventTemplateRef(
        template=template_ref,
        multiplier=FixedMultiplier(Resolved(percent)),
    )
    return creation, template, derived


def _lightning_selection_entry(
    *,
    key: str,
    display_name: str,
    original_text: str,
    rule_id: RuleItemId,
    percent: float,
    condition_ids=(),
) -> tuple[MoveCalculationEntry, PenetrationDamageEventTemplate]:
    """Expose one source-backed lightning event without inventing a move ID."""

    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(
            f"template:character:1371:{key}-selectable"
        ),
        semantic_id=DamageEventSemanticId(
            f"event:character:1371:{key}-selectable"
        ),
        label=display_name,
        damage_type=DamageType.PENETRATION,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.XUANMO,
        source_rule_item_id=rule_id,
    )
    template = PenetrationDamageEventTemplate(
        ref=ref,
        damage_dealer=YIXUAN_ID,
        element=Element.XUANMO,
        base_source=CurrentPenetrationForceValueSource(YIXUAN_ID),
        crit_rule=StandardCritRule(YIXUAN_ID),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1371:{key}-selectable"),
        character_id=YIXUAN_ID,
        move_id=None,
        display_name=display_name,
        original_text=original_text,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    f"variant:character:1371:{key}-selectable"
                ),
                label=f"{percent * 100:g}%贯穿力",
                parameter_name=f"{display_name}倍率",
                multiplier=FixedMultiplier(Resolved(percent)),
            ),
        ),
        main_damage_event=ref,
        condition_ids=tuple(condition_ids),
    )
    return entry, template


def compile_yixuan(
    config: YixuanCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != YIXUAN_ID:
        raise ValueError("Yixuan compiler requires character:1371 raw data")
    if raw_record.special_element != "玄墨":
        raise ValueError("Yixuan raw data must identify its special element as 玄墨")

    entries, templates, diagnostics, raw_moves = _compile_main_moves(raw_record, config)
    anomaly_entries, anomaly_templates = _xuanmo_anomaly_entries(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)
    rules: list[CalculationRuleItem] = []
    derived_refs: list[DerivedDamageEventTemplateRef] = []
    conditions = [
        _condition(
            EX_MARK_CHARGE_EXTRA,
            "墨痕化形蓄力至闪光或触发完美格挡",
            "若蓄力至闪光或触发完美格挡效果，则翅膀上挑攻击后可额外追加符箓攻击。",
        ),
        _condition(
            MATRIX_MAX_DURATION,
            "玄墨极阵达到最大时长",
            "普通攻击：青溟震击在发动普通攻击：玄墨极阵达到最大时长后自动释放。",
            True,
        ),
        _condition(
            FOCUSED_MIND_ACTIVE,
            "仪玄当前处于凝神状态",
            "发动终结技后，仪玄进入凝神状态；持续时间按当前静态状态输入。",
        ),
        _condition(
            PERFECT_SUPPORT_SWITCH_OUT,
            "仪玄被极限支援换下场",
            "仪玄被极限支援换下场时，仪玄会自动追加一道落雷。",
        ),
    ]

    # Explicitly named follow-up attacks retain their own source move IDs and
    # are emitted as child events with provenance.
    followup_specs = (
        (
            "basic-ink-shadow-fifth-hit",
            "普通攻击：霄云劲（五段）",
            BASIC_XIAOYUN_MOVE_ID,
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            INK_SHADOW_MOVE_ID,
            "普通攻击：霄云劲",
            "五段伤害倍率",
            "1371006",
            None,
            "普通攻击：墨影凝云招式结束时自动释放普通攻击：霄云劲第五段攻击。",
        ),
        (
            "basic-array-qingming-shock",
            "普通攻击：青溟震击",
            QINGMING_SHOCK_MOVE_ID,
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            INK_ARRAY_MOVE_ID,
            "普通攻击：青溟震击",
            "伤害倍率",
            "1371007",
            MATRIX_MAX_DURATION,
            "普通攻击：玄墨极阵结束时自动释放普通攻击：青溟震击。",
        ),
        (
            "ex-cloud-ink-ember-shadow",
            "强化特殊技：墨烬影消",
            EX_INK_BURST_MOVE_ID,
            SkillGroup.SPECIAL_ATTACK,
            frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}),
            EX_CLOUD_MOVE_ID,
            "强化特殊技：墨烬影消",
            "伤害倍率",
            "1371026",
            None,
            "强化特殊技：凝云术蓄力至最长时间或提前中断后，自动释放强化特殊技：墨烬影消。",
        ),
        (
            "ex-mark-charge-talisman",
            "强化特殊技：墨痕化形·追加符箓攻击",
            EX_MARK_EXTRA_MOVE_ID,
            SkillGroup.SPECIAL_ATTACK,
            frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}),
            EX_MARK_MOVE_ID,
            "强化特殊技：墨痕化形",
            "蓄力完成追加伤害倍率",
            "1371024",
            EX_MARK_CHARGE_EXTRA,
            "蓄力至闪光或触发完美格挡效果后，翅膀上挑攻击后可额外追加符箓攻击。",
        ),
    )
    for (
        key,
        label,
        move_id,
        group,
        tags,
        parent_move,
        source_move_name,
        parameter_name,
        skill_id,
        condition_id,
        source_text,
    ) in followup_specs:
        raw_move = _raw_move(raw_moves, source_move_name)
        multiplier, diagnostic = _parameter_multiplier(
            raw_move,
            parameter_name,
            skill_id,
            effective_skill_level(config, group),
            subject=key,
        )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
        source_key = f"followup:{key}"
        template, rule, derived = _make_derived(
            raw_record=raw_record,
            key=key,
            label=label,
            move_id=move_id,
            skill_group=group,
            damage_tags=tags,
            multiplier=multiplier,
            parent_move_id=parent_move,
            source_key=source_key,
            source_text=source_text,
            condition_id=condition_id,
        )
        templates.append(template)
        rules.append(rule)
        derived_refs.append(derived)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        raw_record,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_bonus = _percentage(
        core.description,
        r"施展\[普通攻击：玄墨极阵\]、\[普通攻击：青溟震击\]、\[强化特殊技\]、\[支援突击\]、\[连携技\]、\[终结技\]造成的伤害提升<color=[^>]+>(?P<value>\d+(?:\.\d+)?)%</color>",
        subject="Yixuan core passive listed-move damage bonus",
    )
    listed_move_filter = AnyFilter(
        (
            DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
            MoveIdFilter(INK_ARRAY_MOVE_ID),
            MoveIdFilter(QINGMING_SHOCK_MOVE_ID),
            MoveIdFilter(ASSIST_FOLLOW_UP_MOVE_ID),
            MoveIdFilter(CHAIN_MOVE_ID),
            MoveIdFilter(ULTIMATE_QINGMING_MOVE_ID),
            MoveIdFilter(ULTIMATE_TALISMAN_MOVE_ID),
            MoveIdFilter(EX_TALISMAN_BREAK_MOVE_ID),
        )
    )
    core_rule = _rule(
        "core:listed-move-damage",
        core_source,
        "核心被动：指定招式伤害提升",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(
            _modifier(
                "core:listed-move-damage",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(core_bonus),
                filters=(
                    DamageDealerFilter(YIXUAN_ID),
                    DamageTypeFilter(DamageType.PENETRATION),
                    ElementFilter(Element.XUANMO),
                    listed_move_filter,
                ),
            ),
        ),
    )
    rules.append(core_rule)

    extra_source = _source(
        raw_record,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_text = raw_record.extra_ability_description
    extra_stun_bonus = _percentage(
        extra_text,
        r"\[强化特殊技：凝云术\]与\[强化特殊技：墨烬影消\]命中处于失衡状态下的敌人时，伤害提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Yixuan additional-ability stunned EX-special damage bonus",
    )
    focused_crit_bonus = _percentage(
        extra_text,
        r"凝神\]状态下，仪玄的暴击伤害提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Yixuan additional-ability focused-mind crit-damage bonus",
    )
    stun_condition = StatePresentCondition(
        subject=EffectTarget.ENEMY,
        state_id=_ENEMY_STUNNED_STATE_ID,
    )
    rules.append(
        _rule(
            "extra-ability:stunned-ex-special-damage",
            extra_source,
            "额外能力：失衡目标强化特殊技增伤",
            extra_text,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:stunned-ex-special-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(extra_stun_bonus),
                    filters=(
                        DamageDealerFilter(YIXUAN_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.XUANMO),
                        AnyFilter(
                            (
                                MoveIdFilter(EX_CLOUD_MOVE_ID),
                                MoveIdFilter(EX_INK_BURST_MOVE_ID),
                            )
                        ),
                    ),
                    condition=stun_condition,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "extra-ability:focused-mind-crit-damage",
            extra_source,
            "额外能力：凝神暴击伤害提升",
            extra_text,
            extra_eligibility,
            condition_ids=(FOCUSED_MIND_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:focused-mind-crit-damage",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(focused_crit_bonus),
                ),
            ),
        )
    )
    lightning225 = _percentage(
        extra_text,
        r"自动追加一道落雷，造成等同于仪玄(?P<value>\d+(?:\.\d+)?)%贯穿力的伤害",
        subject="Yixuan additional-ability lightning force multiplier",
    )
    lightning225_effect_id = EffectId("effect:character:1371:extra-ability:lightning")
    lightning225_effect, lightning225_template, lightning225_derived = _lightning_event(
        key="extra-ability-lightning",
        effect_id=lightning225_effect_id,
        source=extra_source,
        rule_id=RuleItemId("rule:character:1371:extra-ability:lightning"),
        trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
        filters=(NotFilter(CreatedByEffectFilter(lightning225_effect_id)),),
        percent=lightning225,
    )
    rules.append(
        _rule(
            "extra-ability:lightning",
            extra_source,
            "额外能力：极限支援换下场落雷",
            extra_text,
            extra_eligibility,
            condition_ids=(PERFECT_SUPPORT_SWITCH_OUT,),
            effects=(lightning225_effect,),
        )
    )
    templates.append(lightning225_template)
    derived_refs.append(lightning225_derived)
    if config.additional_ability_eligible:
        lightning_entry, lightning_selection_template = _lightning_selection_entry(
            key="extra-ability-lightning",
            display_name="额外能力：极限支援换下场落雷",
            original_text=extra_text,
            rule_id=RuleItemId("rule:character:1371:extra-ability:lightning"),
            percent=lightning225,
            condition_ids=(PERFECT_SUPPORT_SWITCH_OUT,),
        )
        entries.append(lightning_entry)
        templates.append(lightning_selection_template)

    # C1's entry bonus applies once C1 is unlocked.  Its lightning trigger
    # accepts Yixuan's own penetration event and teammates' direct events; the
    # Each hit receives its own typed child identity; the child is excluded by
    # its effect provenance so it cannot trigger another copy of itself.
    c1 = _raw_mindscape(raw_record, 1)
    c1_source = _source(
        raw_record,
        "cinema1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    c1_crit_rate = _percentage(
        c1.description,
        r"进入战场时，暴击率提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Yixuan Cinema 1 entry crit rate",
    )
    c1_lightning = _percentage(
        c1.description,
        r"自动追加一道落雷，造成等同于仪玄(?P<value>\d+(?:\.\d+)?)%贯穿力的伤害",
        subject="Yixuan Cinema 1 lightning force multiplier",
    )
    c1_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 1
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema1:entry-crit-rate",
            c1_source,
            f"1影：{c1.name}·入场暴击率",
            c1.description,
            c1_eligibility,
            effects=(
                _modifier(
                    "cinema1:entry-crit-rate",
                    c1_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(c1_crit_rate),
                ),
            ),
        )
    )
    c1_event_effect, c1_lightning_template, c1_lightning_derived = _lightning_event(
        key="cinema1-lightning",
        effect_id=_LIGHTNING_C1_EFFECT_ID,
        source=c1_source,
        rule_id=RuleItemId("rule:character:1371:cinema1:lightning"),
        percent=c1_lightning,
        unique_per_source_event=True,
        filters=(
            AnyFilter(
                (
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageTypeFilter(DamageType.PENETRATION),
                )
            ),
            NotFilter(CreatedByEffectFilter(_LIGHTNING_C1_EFFECT_ID)),
            NotFilter(EventTemplateIdFilter(_LIGHTNING_C1_SELECTION_TEMPLATE_ID)),
        ),
    )
    rules.append(
        _rule(
            "cinema1:lightning",
            c1_source,
            f"1影：{c1.name}·命中追加落雷",
            c1.description,
            c1_eligibility,
            effects=(c1_event_effect,),
        )
    )
    templates.append(c1_lightning_template)
    derived_refs.append(c1_lightning_derived)
    if config.cinema_level >= 1:
        c1_lightning_entry, c1_lightning_selection_template = (
            _lightning_selection_entry(
                key="cinema1-lightning",
                display_name="1影：命中追加落雷",
                original_text=c1.description,
                rule_id=RuleItemId("rule:character:1371:cinema1:lightning"),
                percent=c1_lightning,
            )
        )
        entries.append(c1_lightning_entry)
        templates.append(c1_lightning_selection_template)

    # C2 resistance ignore is attached only to Yixuan's EX-special and
    # Ultimate penetration events.  The 1200% break technique is registered
    # only for an unlocked C2 configuration.
    c2 = _raw_mindscape(raw_record, 2)
    c2_source = _source(
        raw_record,
        "cinema2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    resistance_ignore = _percentage(
        c2.description,
        r"无视目标(?P<value>\d+(?:\.\d+)?)%<color=[^>]+>以太伤害抗性</color>",
        subject="Yixuan Cinema 2 Ether resistance ignore",
    )
    c2_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 2
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema2:resistance-ignore",
            c2_source,
            "2影：终结技与强化特殊技无视以太抗性",
            c2.description,
            c2_eligibility,
            effects=(
                _modifier(
                    "cinema2:resistance-ignore",
                    c2_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(resistance_ignore),
                    filters=(
                        DamageDealerFilter(YIXUAN_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.XUANMO),
                        AnyFilter(
                            (
                                DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                                DamageTagFilter(DamageTag.ULTIMATE),
                            )
                        ),
                    ),
                ),
            ),
        )
    )
    c2_branch_multiplier = _percentage(
        c2.description,
        r"最多造成等同于(?P<value>\d+(?:\.\d+)?)%贯穿力的伤害",
        subject="Yixuan Cinema 2 talisman break force multiplier",
    )
    if config.cinema_level >= 2:
        branch_entry, branch_template = _fixed_entry(
            key="cinema2-ex-talisman-break",
            move_id=EX_TALISMAN_BREAK_MOVE_ID,
            label="强化特殊技：符法千重-破",
            original_text=c2.description,
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=frozenset(
                {DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}
            ),
            multiplier=FixedMultiplier(Resolved(c2_branch_multiplier)),
            condition_id=C2_INK_BREAK_READY,
        )
        entries.append(branch_entry)
        templates.append(branch_template)
        conditions.append(
            _condition(
                C2_INK_BREAK_READY,
                "仪玄当前拥有可消耗的聚墨效果并选择符法千重-破",
                "2影：符法千重-破需要消耗一层聚墨；聚墨最多一层。",
            )
        )
    else:
        # Keep the raw numeric clause reviewable even while its move is locked.
        diagnostics.append(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId("review:character:1371:cinema2-branch-locked"),
                kind=DiagnosticKind.DATA_QUALITY,
                message="C2-only 符法千重-破 is omitted until cinema_level >= 2.",
                blocking=False,
                original_text=c2.description,
            )
        )

    # C3/C5 skill upgrades are applied by effective_skill_level above.
    for level in (3, 5):
        mindscape = _raw_mindscape(raw_record, level)
        source = _source(
            raw_record,
            f"cinema{level}",
            EffectSourceType.CINEMA,
            f"{level}影：{mindscape.name}",
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：{mindscape.name}",
                mindscape.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    # C4's two-stack damage bonus remains MoveId-specific.
    c4 = _raw_mindscape(raw_record, 4)
    c4_source = _source(
        raw_record,
        "cinema4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    c4_bonus = _percentage(
        c4.description,
        r"每有一层<color=[^>]+>\[静心\]</color>效果，下一次<color=[^>]+>\[强化特殊技：凝云术\]</color>和<color=[^>]+>\[强化特殊技：墨烬影消\]</color>造成的伤害提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Yixuan Cinema 4 Stillness damage bonus per stack",
    )
    rules.append(
        _rule(
            "cinema4:stillness-damage",
            c4_source,
            "4影：静心增幅凝云术与墨烬影消",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            stack_count=2,
            stack_min=0,
            stack_max=2,
            effects=(
                _modifier(
                    "cinema4:stillness-damage",
                    c4_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c4_bonus),
                    filters=(
                        DamageDealerFilter(YIXUAN_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.XUANMO),
                        AnyFilter(
                            (
                                MoveIdFilter(EX_CLOUD_MOVE_ID),
                                MoveIdFilter(EX_INK_BURST_MOVE_ID),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    # C6's damage bonus depends on an extra-ability state.  Both are gated by
    # source-derived eligibility so a user checkbox cannot enable it alone.
    c6 = _raw_mindscape(raw_record, 6)
    c6_source = _source(
        raw_record,
        "cinema6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    c6_penetration_bonus = _percentage(
        c6.description,
        r"凝神\]</color>状态下，仪玄的贯穿伤害提高(?P<value>\d+(?:\.\d+)?)%",
        subject="Yixuan Cinema 6 penetration damage bonus",
    )
    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6 and config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema6:focused-penetration-damage",
            c6_source,
            "6影：凝神期间贯穿伤害提升",
            c6.description,
            c6_eligibility,
            condition_ids=(FOCUSED_MIND_ACTIVE,),
            effects=(
                _modifier(
                    "cinema6:focused-penetration-damage",
                    c6_source,
                    CalculationNode.PENETRATION_DAMAGE_BONUS,
                    Resolved(c6_penetration_bonus),
                    filters=(
                        DamageDealerFilter(YIXUAN_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.XUANMO),
                    ),
                ),
            ),
        )
    )

    # C6 grants one selected, freely cast Talisman Ultimate after Qingming.
    c6_extra_multiplier, c6_extra_diagnostic = _parameter_multiplier(
        _raw_move(raw_moves, "终结技：符法千重"),
        "伤害倍率",
        "1371020",
        effective_skill_level(config, SkillGroup.ULTIMATE),
        subject="cinema6-extra-ultimate",
    )
    if c6_extra_diagnostic is not None:
        diagnostics.append(c6_extra_diagnostic)
    c6_extra_rule_id = RuleItemId("rule:character:1371:cinema6:extra-ultimate")
    c6_extra_source = c6_source
    c6_extra_template = _typed_template(
        key="cinema6-extra-ultimate",
        label="6影：调息追加终结技·符法千重",
        move_id=ULTIMATE_TALISMAN_MOVE_ID,
        skill_group=SkillGroup.ULTIMATE,
        damage_tags=frozenset({DamageTag.ULTIMATE}),
        source_rule_item_id=c6_extra_rule_id,
    )
    c6_extra_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1371:cinema6:extra-ultimate"),
            source=c6_extra_source,
            owner=YIXUAN_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.PENETRATION),
                DamageDealerFilter(YIXUAN_ID),
                MoveIdFilter(ULTIMATE_QINGMING_MOVE_ID),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=c6_extra_template.ref.template_id,
        ),
    )
    c6_extra_rule = _rule(
        "cinema6:extra-ultimate",
        c6_extra_source,
        "6影：调息追加符法千重",
        c6.description,
        c6_eligibility,
        condition_ids=(C6_EXTRA_ULTIMATE_ACTIVE,),
        effects=(c6_extra_effect,),
    )
    rules.append(c6_extra_rule)
    c6_extra_derived = DerivedDamageEventTemplateRef(
        template=c6_extra_template.ref,
        multiplier=c6_extra_multiplier,
    )
    templates.append(c6_extra_template)
    derived_refs.append(c6_extra_derived)
    conditions.append(
        _condition(
            C6_EXTRA_ULTIMATE_ACTIVE,
            "本次青溟云影后正在使用调息追加的符法千重",
            c6.description,
        )
    )

    # C1's lightning event is triggered by any supported hit in the team.
    # The source's 50% force multiplier is retained in the diagnostic.
    # 225% is similarly gated behind an actual support-entry trigger fact and
    # an explicit outgoing-Yixuan state selection.
    return CharacterCalculationDefinition(
        character_id=YIXUAN_ID,
        role=CharacterRole.RUPTURE,
        base_element=Element.ETHER,
        source=_source(
            raw_record,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=tuple(_unique_conditions(conditions)),
        scenario_parameters=(),
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=tuple(derived_refs),
        diagnostics=tuple(diagnostics),
    )


def _unique_conditions(conditions):
    result = []
    seen = set()
    for item in conditions:
        if item.condition_id in seen:
            continue
        seen.add(item.condition_id)
        result.append(item)
    return result


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(YIXUAN_ID))


__all__ = ["compile_yixuan", "load_raw_record"]
