"""Reviewed compiler for Harumasa (character:1201), Nanoka 3.2."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EnemyStateFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    NotCondition,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    ScenarioParameterRangeCondition,
    SkillGroup,
    SnapshotRule,
    StatePresentCondition,
    StandardCritRule,
    StateId,
    Unresolved,
    UnresolvedReason,
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
    NanokaRawRecord,
    NanokaReviewedMapping,
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
)
from .config import HarumasaCompileConfig
from .reviewed import (
    HARUMASA_C6_ELECTRIC_RESISTANCE_IGNORE_ACTIVE,
    HARUMASA_C6_ELECTROMAGNETIC_EXPLOSION_READY,
    HARUMASA_CURRENT_ELECTRIC_BLADE_STACKS,
    HARUMASA_CURRENT_FENGMANG_STACKS,
    HARUMASA_ELECTRIC_ANOMALY_RECORD_ID,
    HARUMASA_ELECTRIC_DISORDER_REMAINING_SECONDS,
    HARUMASA_EXTRA_ABILITY_ANOMALY_ACTIVE,
    HARUMASA_ID,
    HARUMASA_POTENTIAL_ATK_BUFF_ACTIVE,
    HARUMASA_REVIEWED_MAPPING,
    HARUMASA_TEN_CROSS_ACTIVE,
    HARUMASA_ULTIMATE_MOVE_ID,
    HARUMASA_ULTIMATE_SCATTER_MOVE_ID,
    reviewed_mapping,
)


_ELECTRIC_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1201:electric-shock")
_ELECTRIC_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1201:electric-disorder")
_ENEMY_STUNNED = StateId("state:enemy:stunned")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str, value: bool = False) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(key: str, source_type: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(HARUMASA_ID, key, source_type, label, text)


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
        rule_id=RuleItemId(f"rule:character:1201:{key}"),
        owner=HARUMASA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1201:{key}"),
            source=source,
            owner=HARUMASA_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _potential_view(data: Mapping[str, object], potential_level: int) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("Harumasa potential level must be between 0 and 6")
    view = deepcopy(dict(data))
    details = view.get("potential_detail")
    if not isinstance(details, Mapping):
        raise ValueError("Harumasa source is missing potential_detail")
    selected = next(
        (
            item
            for item in details.values()
            if isinstance(item, Mapping) and item.get("level") == potential_level
        ),
        None,
    ) if potential_level else None
    selected_id = int(selected["id"]) if isinstance(selected, Mapping) else None

    def base_variant(value: object) -> bool:
        return value is None or (
            isinstance(value, (list, tuple)) and (not value or 0 in value)
        )

    def included(value: object) -> bool:
        if base_variant(value):
            return True
        return (
            selected_id is not None
            and isinstance(value, (list, tuple))
            and selected_id in value
        )

    skills = view.get("skill")
    if isinstance(skills, dict):
        for section in skills.values():
            if isinstance(section, dict) and isinstance(section.get("description"), list):
                section["description"] = [
                    item
                    for item in section["description"]
                    if isinstance(item, dict) and included(item.get("potential"))
                ]
    passive = view.get("passive")
    levels = passive.get("level") if isinstance(passive, dict) else None
    if not isinstance(levels, dict):
        raise ValueError("Harumasa source is missing passive level data")
    first_id, last_id = (1201501, 1201507) if potential_level == 0 else (1201508, 1201514)
    passive["level"] = {
        key: item
        for key, item in levels.items()
        if isinstance(item, Mapping)
        and isinstance(item.get("id"), int)
        and first_id <= int(item["id"]) <= last_id
    }
    return view


def load_raw_record(data: Mapping[str, object], *, potential_level: int = 0) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_view(data, potential_level),
        expected_character_id=str(HARUMASA_ID),
    )


def _electric_anomaly_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=_ELECTRIC_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1201:electric-anomaly"),
        label="属性异常：感电（10秒）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=HARUMASA_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=HARUMASA_ID,
        history_record_source=HARUMASA_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=MoveId("move:harumasa:electric-shock"),
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1201:electric-anomaly"),
        character_id=HARUMASA_ID,
        move_id=MoveId("move:harumasa:electric-shock"),
        display_name="属性异常：感电（10秒）",
        original_text="按规范静态单人100%积蓄电异常；使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(MultiplierVariant(
            variant_id=MultiplierVariantId("variant:character:1201:electric-anomaly"),
            label="感电125% × 10跳",
            parameter_name="感电总倍率",
            multiplier=FixedMultiplier(Resolved(1.25)),
            repeat_count=10,
        ),),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id=_ELECTRIC_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1201:electric-disorder"),
        label="紊乱：感电（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=HARUMASA_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=HARUMASA_ID,
        history_record_source=HARUMASA_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=MoveId("move:harumasa:electric-disorder"),
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1201:electric-disorder"),
        character_id=HARUMASA_ID,
        move_id=MoveId("move:harumasa:electric-disorder"),
        display_name="紊乱：感电（当前剩余时间）",
        original_text="感电紊乱倍率为450% + floor(t)×125%；使用当前剩余时间输入，不推演时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(MultiplierVariant(
            variant_id=MultiplierVariantId("variant:character:1201:electric-disorder"),
            label="450% + floor(t) × 125%",
            parameter_name="电紊乱倍率",
            multiplier=FixedMultiplier(Resolved(4.5)),
            parameter_value_id=ScenarioParameterId(HARUMASA_ELECTRIC_DISORDER_REMAINING_SECONDS),
            parameter_base_value=4.5,
            parameter_coefficient=1.25,
        ),),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=ScenarioParameterId(HARUMASA_ELECTRIC_DISORDER_REMAINING_SECONDS),
        label="电异常剩余持续时间（秒）",
        original_text="使用本次选择的剩余时间，范围0–10秒；不模拟时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _ultimate_scatter(raw: NanokaRawRecord, config: HarumasaCompileConfig, entries):
    if config.potential_level < 1:
        return (), (), tuple(entries)
    raw_moves = raw_move_index(raw)
    diagnostics: list[CalculationDiagnostic] = []
    ratio = raw_multiplier(
        raw_moves,
        "残心·散华",
        "伤害倍率",
        effective_skill_level(config, SkillGroup.ULTIMATE),
        "character:1201:potential1-ultimate-scatter",
        diagnostics,
        source_skill_id="1201024",
    )
    if diagnostics or not isinstance(ratio, float):
        raise ValueError("Harumasa Potential 1 Ultimate follow-up curve is missing")
    source = source_for(
        HARUMASA_ID,
        "potential1:ultimate-scatter",
        EffectSourceType.SPECIAL_MECHANISM,
        "潜能1：终结技后的残心·散华",
        raw_moves["残心·散华"].description,
    )
    rule_id = RuleItemId("rule:character:1201:potential1-ultimate-scatter")
    template_id = EventTemplateId("template:character:1201:potential1:ultimate-scatter")
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId("event:character:1201:potential1:ultimate-scatter"),
        label="潜能1：残心·散华",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.ULTIMATE,
        damage_tags=frozenset({DamageTag.ULTIMATE}),
        element=Element.ELECTRIC,
        source_rule_item_id=rule_id,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=HARUMASA_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(HARUMASA_ID),
        crit_rule=StandardCritRule(HARUMASA_ID),
        move_id=None,
    )
    effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1201:potential1-ultimate-scatter"),
            source=source,
            owner=HARUMASA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(HARUMASA_ID),
                EventTemplateIdFilter(EventTemplateId("template:character:1201:ultimate-electric:main")),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_id,
            unique_per_source_event=True,
        ),
    )
    updated = tuple(
        replace(
            entry,
            derived_damage_events=(
                *entry.derived_damage_events,
                DerivedDamageEventTemplateRef(template=ref, multiplier=FixedMultiplier(Resolved(ratio))),
            ),
        )
        if str(entry.entry_id) == "move-entry:character:1201:ultimate-electric"
        else entry
        for entry in entries
    )
    return (template,), (effect,), updated, (rule_id, source)


def _c6_electromagnetic_explosion(source: RuleSource):
    """Create the confirmed independent one-packet Direct event and its Arrow child."""
    standalone_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1201:cinema6-electromagnetic-explosion:standalone"),
        semantic_id=DamageEventSemanticId("event:character:1201:cinema6-electromagnetic-explosion:standalone"),
        label="6影：电磁爆炸（1500%攻击力，单次）",
        damage_type=DamageType.DIRECT,
        element=Element.ELECTRIC,
    )
    standalone_template = DirectDamageEventTemplate(
        ref=standalone_ref,
        damage_dealer=HARUMASA_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(HARUMASA_ID),
        crit_rule=StandardCritRule(HARUMASA_ID),
        move_id=None,
    )
    standalone_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1201:cinema6-electromagnetic-explosion"),
        character_id=HARUMASA_ID,
        move_id=None,
        display_name="6影：电磁爆炸（1500%攻击力，单次）",
        original_text=source.raw_text or "[甲乙矢]连续命中同一敌人12次后额外触发。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(MultiplierVariant(
            variant_id=MultiplierVariantId("variant:character:1201:cinema6-electromagnetic-explosion:standalone"),
            label="1500%攻击力",
            parameter_name="电磁爆炸倍率",
            multiplier=FixedMultiplier(Resolved(15.0)),
        ),),
        main_damage_event=standalone_ref,
    )
    child_rule_id = RuleItemId("rule:character:1201:cinema6:electric-explosion-child")
    child_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1201:cinema6-electromagnetic-explosion:arrow-child"),
        semantic_id=DamageEventSemanticId("event:character:1201:cinema6-electromagnetic-explosion:arrow-child"),
        label="6影：甲乙矢触发的电磁爆炸（单次）",
        damage_type=DamageType.DIRECT,
        element=Element.ELECTRIC,
        source_rule_item_id=child_rule_id,
    )
    child_template = DirectDamageEventTemplate(
        ref=child_ref,
        damage_dealer=HARUMASA_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(HARUMASA_ID),
        crit_rule=StandardCritRule(HARUMASA_ID),
        move_id=None,
    )
    child_ref_with_multiplier = DerivedDamageEventTemplateRef(
        template=child_ref,
        multiplier=FixedMultiplier(Resolved(15.0)),
    )
    child_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1201:cinema6:electric-explosion-child"),
            source=source,
            owner=HARUMASA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(HARUMASA_ID),
                EventTemplateIdFilter(EventTemplateId("template:character:1201:basic-arrow:main")),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=child_ref.template_id,
            unique_per_source_event=True,
        ),
    )
    return standalone_entry, standalone_template, child_template, child_ref_with_multiplier, child_effect, child_rule_id


def compile_harumasa(config: HarumasaCompileConfig, raw_record: NanokaRawRecord) -> CharacterCalculationDefinition:
    if raw_record.character_id != HARUMASA_ID or raw_record.name != "悠真" or raw_record.code_name != "Harumasa":
        raise ValueError("unexpected identity in Harumasa raw record")
    if raw_record.specialty != "强攻" or raw_record.element != "电属性" or raw_record.rarity != 4 or raw_record.faction != "对空洞特别行动部第六课":
        raise ValueError("Harumasa raw role, element, rarity, or faction changed from reviewed source")
    if raw_record.source_version != "3.2" or raw_record.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1201.json":
        raise ValueError("Harumasa provenance must identify live Nanoka 3.2 character 1201")
    expected_core = "1201501" if config.potential_level == 0 else "1201508"
    if len(raw_record.core_levels) != 7 or raw_record.core_levels[0].source_id != expected_core:
        raise ValueError("Harumasa source potential projection does not match compile config")

    direct_entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=HARUMASA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping(potential_level=config.potential_level),
        id_namespace="character:1201",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    diagnostics = list(diagnostics)
    raw_moves = raw_move_index(raw_record)
    if config.potential_level >= 1:
        julei_index = next(
            index for index, entry in enumerate(entries)
            if str(entry.entry_id) == "move-entry:character:1201:potential1-julei"
        )
        julei_entry = entries[julei_index]
        entries[julei_index] = replace(
            julei_entry,
            diagnostics=(CalculationDiagnostic(
                diagnostic_id=DiagnosticId("unsupported:character:1201:potential1:julei-tag-scope"),
                kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
                message="逐雷来源位于闪避技能段，但未明确 DamageTag；基础倍率可计算，标签限定装备效果不作推测。",
                blocking=False,
                original_text=raw_moves["冲刺攻击：飞弦·斩"].description,
            ),),
        )
    anomaly_entries, anomaly_templates, disorder_parameter = _electric_anomaly_entries()
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(HARUMASA_ID, "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = source_for(HARUMASA_ID, "extra-ability", EffectSourceType.ADDITIONAL_ABILITY, core.extra_ability_name, core.extra_ability_description)
    conditions: list[ScenarioCondition] = [
        _condition(HARUMASA_TEN_CROSS_ACTIVE, "目标当前拥有十文字标记（冲刺攻击·飞弦·斩可用）", "场上存在拥有十文字标记的敌人时进入醒觉状态。"),
        _condition(HARUMASA_EXTRA_ABILITY_ANOMALY_ACTIVE, "目标当前处于属性异常状态", core.extra_ability_description),
    ]
    parameters: list[ScenarioIntegerParameter] = [disorder_parameter]
    parameters.append(ScenarioIntegerParameter(
        parameter_id=ScenarioParameterId(HARUMASA_CURRENT_FENGMANG_STACKS),
        label="当前锋芒层数",
        original_text="按当前0–6层计算悠真核心被动暴击伤害，不模拟暴击触发与5秒持续时间。",
        resolution=ParameterResolution.USER_SELECTED,
        value=6,
        minimum=0,
        maximum=6,
    ))
    if config.cinema_level >= 2:
        parameters.append(ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId(HARUMASA_CURRENT_ELECTRIC_BLADE_STACKS),
            label="当前电掣层数",
            original_text="按当前0–7层静态表示；不模拟连携/终结技获得层数或冲刺攻击消耗。",
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=7,
        ))
    if config.potential_level >= 2:
        conditions.append(_condition(HARUMASA_POTENTIAL_ATK_BUFF_ACTIVE, "潜能攻击力增益当前生效", raw_record.potential_details[config.potential_level - 1].description))
    if config.cinema_level >= 6:
        conditions.extend((
            _condition(HARUMASA_C6_ELECTRIC_RESISTANCE_IGNORE_ACTIVE, "悠真当前无视目标15%电属性抗性", raw_record.mindscapes[5].description),
            _condition(HARUMASA_C6_ELECTROMAGNETIC_EXPLOSION_READY, "本次甲乙矢已满足12次命中后的电磁爆炸触发", raw_record.mindscapes[5].description),
        ))

    rules: list[CalculationRuleItem] = []
    dash_slash_templates = tuple(
        EventTemplateId(f"template:character:1201:dash-slash-{stage}:main")
        for stage in range(1, 4)
    )
    julei_template = EventTemplateId("template:character:1201:potential1-julei:main")
    ultimate_template = EventTemplateId("template:character:1201:ultimate-electric:main")
    core_crit_rate = _number(core.description, r"暴击率提升(?P<value>[\d.]+)%", "Harumasa Core Crit Rate") / 100.0
    core_crit_damage = _number(core.description, r"每层[^；\n]*暴击伤害提升(?P<value>[\d.]+)%", "Harumasa Core Crit Damage per Fengmang") / 100.0
    core_crit_rate_templates = list(dash_slash_templates)
    core_crit_damage_templates = list(dash_slash_templates)
    if config.potential_level >= 1:
        core_crit_rate_templates.extend((julei_template, ultimate_template))
        core_crit_damage_templates.extend((julei_template, ultimate_template))
    core_rule_effects = (
        _modifier(
            "core:dash-slash-crit-rate",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            Resolved(core_crit_rate),
            target=EffectTarget.SELF,
            filters=(DamageDealerFilter(HARUMASA_ID), AnyFilter(tuple(EventTemplateIdFilter(item) for item in core_crit_rate_templates))),
        ),
        _modifier(
            "core:fengmang-crit-damage",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            ScenarioParameterDerivedValue(
                parameter_id=HARUMASA_CURRENT_FENGMANG_STACKS,
                coefficient=Resolved(core_crit_damage),
                cap_max=Resolved(core_crit_damage * 6),
            ),
            target=EffectTarget.SELF,
            filters=(DamageDealerFilter(HARUMASA_ID), AnyFilter(tuple(EventTemplateIdFilter(item) for item in core_crit_damage_templates))),
        ),
    )
    rules.append(_rule("core:dash-crit-buffs", core_source, "核心被动：飞弦·斩暴击率与锋芒暴击伤害", core.description, RuleEligibility.ELIGIBLE, effects=core_rule_effects))

    if config.potential_level >= 1:
        p1_source = source_for(
            HARUMASA_ID,
            "potential1:julei-follow-up",
            EffectSourceType.SPECIAL_MECHANISM,
            "潜能1：逐雷",
            raw_moves["冲刺攻击：飞弦·斩"].description,
        )
        julei_ratio = raw_moves["逐雷"].parameters
        source_ratio = next(
            (parameter.value_for_level(effective_skill_level(config, SkillGroup.DODGE), "1201025") for parameter in julei_ratio if parameter.name == "额外伤害倍率"),
            None,
        )
        if source_ratio is None:
            raise ValueError("Harumasa Potential 1 Julei source curve is missing")
        julei_unresolved = Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_TEXT,
            notes=f"逐雷来源倍率为{source_ratio / 100:.3%}（L{effective_skill_level(config, SkillGroup.DODGE)}）；原文说明失衡目标会触发额外电伤，但未说明该触发按每个飞弦·斩段还是每次完整招式结算。",
            original_text=raw_moves["冲刺攻击：飞弦·斩"].description,
        )
        julei_effects = tuple(
            EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId(f"effect:character:1201:potential1:julei-follow-up:dash-slash-{stage}"),
                    source=p1_source,
                    owner=HARUMASA_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(HARUMASA_ID),
                        EventTemplateIdFilter(EventTemplateId(f"template:character:1201:dash-slash-{stage}:main")),
                        EnemyStateFilter(_ENEMY_STUNNED),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    unresolved_template=julei_unresolved,
                    unique_per_source_event=True,
                ),
            )
            for stage in (1, 2, 3)
        )
        rules.append(_rule(
            "potential1:julei-follow-up",
            p1_source,
            "潜能1：失衡目标触发逐雷（触发次数待确认）",
            raw_moves["冲刺攻击：飞弦·斩"].description,
            RuleEligibility.ELIGIBLE,
            effects=julei_effects,
        ))

    extra_eligibility = RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE
    damage_bonus = _number(core.extra_ability_description, r"自身造成的伤害提升(?P<value>[\d.]+)%", "Harumasa Additional Ability damage bonus") / 100.0
    target_stun_bonus = _modifier(
        "extra-ability:stunned-target-damage-bonus",
        extra_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(damage_bonus),
        target=EffectTarget.SELF,
        filters=(DamageDealerFilter(HARUMASA_ID), EnemyStateFilter(_ENEMY_STUNNED)),
    )
    rules.append(_rule(
        "extra-ability:stunned-target-damage-bonus",
        extra_source,
        f"额外能力：失衡目标伤害+{damage_bonus:.0%}",
        core.extra_ability_description,
        extra_eligibility,
        effects=(target_stun_bonus,),
    ))
    rules.append(_rule(
        "extra-ability:anomalous-target-damage-bonus",
        extra_source,
        f"额外能力：属性异常目标伤害+{damage_bonus:.0%}",
        core.extra_ability_description,
        extra_eligibility,
        conditions=(HARUMASA_EXTRA_ABILITY_ANOMALY_ACTIVE,),
        effects=(_modifier(
            "extra-ability:anomalous-target-damage-bonus",
            extra_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(damage_bonus),
            target=EffectTarget.SELF,
            filters=(DamageDealerFilter(HARUMASA_ID),),
            condition=NotCondition(StatePresentCondition(EffectTarget.ENEMY, _ENEMY_STUNNED)),
        ),),
    ))
    rules.append(_rule(
        "extra-ability:electric-prison-source-only",
        extra_source,
        "额外能力：电囚层数（当前计算无电囚结果）",
        core.extra_ability_description,
        extra_eligibility,
        diagnostics=(CalculationDiagnostic(
            diagnostic_id=DiagnosticId("unsupported:character:1201:extra-ability:electric-prison-state"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message="额外能力可以为目标施加电囚层数，但当前结果不模拟电囚资源和刷新历史。",
            blocking=False,
            original_text=core.extra_ability_description,
        ),),
    ))

    if config.cinema_level >= 1:
        c1 = raw_record.mindscapes[0]
        c1_source = source_for(HARUMASA_ID, "cinema1", EffectSourceType.CINEMA, c1.name, c1.description)
        rules.append(_rule("cinema1:electric-prison-resource-source-only", c1_source, "1影：电囚资源上限与电壶箭数量", c1.description, RuleEligibility.ELIGIBLE))
    if config.cinema_level >= 2:
        c2 = raw_record.mindscapes[1]
        c2_source = source_for(HARUMASA_ID, "cinema2", EffectSourceType.CINEMA, c2.name, c2.description)
        rules.append(_rule(
            "cinema2:electric-blade-dash-slash-damage",
            c2_source,
            "2影：当前拥有电掣时飞弦·斩伤害+50%",
            c2.description,
            RuleEligibility.ELIGIBLE,
            effects=(_modifier(
                "cinema2:electric-blade-dash-slash-damage",
                c2_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(0.50),
                target=EffectTarget.SELF,
                filters=(DamageDealerFilter(HARUMASA_ID), AnyFilter(tuple(EventTemplateIdFilter(item) for item in dash_slash_templates))),
                condition=ScenarioParameterRangeCondition(HARUMASA_CURRENT_ELECTRIC_BLADE_STACKS, minimum=1),
            ),),
        ))
    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        c_source = source_for(HARUMASA_ID, f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        rules.append(_rule(f"cinema{level}:skill-levels", c_source, f"{level}影：技能等级提升", cinema.description, RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE))
    if config.cinema_level >= 4:
        c4 = raw_record.mindscapes[3]
        c4_source = source_for(HARUMASA_ID, "cinema4", EffectSourceType.CINEMA, c4.name, c4.description)
        rules.append(_rule("cinema4:resource-source-only", c4_source, "4影：电囚持续时间与喧响值回复（资源/时间不模拟）", c4.description, RuleEligibility.ELIGIBLE))
    if config.cinema_level >= 6:
        c6 = raw_record.mindscapes[5]
        c6_source = source_for(HARUMASA_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
        standalone, standalone_template, explosion_template, explosion_ref, explosion_effect, child_rule_id = _c6_electromagnetic_explosion(c6_source)
        entries.append(standalone)
        templates.extend((standalone_template, explosion_template))
        arrow_entry_index = next(
            index for index, entry in enumerate(entries)
            if str(entry.entry_id) == "move-entry:character:1201:basic-arrow"
        )
        arrow_entry = entries[arrow_entry_index]
        entries[arrow_entry_index] = replace(
            arrow_entry,
            derived_damage_events=(*arrow_entry.derived_damage_events, explosion_ref),
        )
        c6_res_ignore = _number(c6.description, r"无视其(?P<value>[\d.]+)%电属性伤害抗性", "Harumasa Cinema 6 Electric resistance ignore") / 100.0
        rules.append(_rule(
            "cinema6:electric-resistance-ignore-current",
            c6_source,
            f"6影：当前无视目标{c6_res_ignore:.0%}电属性抗性",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(HARUMASA_C6_ELECTRIC_RESISTANCE_IGNORE_ACTIVE,),
            effects=(_modifier(
                "cinema6:electric-resistance-ignore-current",
                c6_source,
                CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                Resolved(c6_res_ignore),
                target=EffectTarget.ENEMY,
                filters=(DamageDealerFilter(HARUMASA_ID), element_scope_filter(Element.ELECTRIC)),
            ),),
        ))
        rules.append(_rule(
            "cinema6:electric-explosion-child",
            c6_source,
            "6影：甲乙矢满足当前12次命中状态时派生电磁爆炸",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(HARUMASA_C6_ELECTROMAGNETIC_EXPLOSION_READY,),
            effects=(explosion_effect,),
        ))

    if config.potential_level >= 2:
        detail = next(item for item in raw_record.potential_details if item.level == config.potential_level)
        p_source = source_for(HARUMASA_ID, f"potential{config.potential_level}", EffectSourceType.SPECIAL_MECHANISM, detail.name or detail.level_show_name, detail.description)
        atk_bonus = _number(detail.description, r"攻击力提升(?P<value>[\d.]+)%", f"Harumasa Potential {config.potential_level} attack bonus") / 100.0
        res_ignore = _number(detail.description, r"无视目标(?P<value>[\d.]+)%的电属性伤害抗性", f"Harumasa Potential {config.potential_level} Electric resistance ignore") / 100.0
        rules.append(_rule(
            f"potential{config.potential_level}:current-attack-and-dash-res-ignore",
            p_source,
            f"潜能{config.potential_level}：当前攻击力+{atk_bonus:.0%}与飞弦·斩/逐雷抗性无视{res_ignore:.1%}",
            detail.description,
            RuleEligibility.ELIGIBLE,
            conditions=(HARUMASA_POTENTIAL_ATK_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    f"potential{config.potential_level}:current-attack-bonus",
                    p_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    Resolved(atk_bonus),
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    f"potential{config.potential_level}:dash-julei-resistance-ignore",
                    p_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(res_ignore),
                    target=EffectTarget.ENEMY,
                    filters=(DamageDealerFilter(HARUMASA_ID), element_scope_filter(Element.ELECTRIC), AnyFilter(tuple(EventTemplateIdFilter(item) for item in (*dash_slash_templates, julei_template)))),
                ),
            ),
        ))

    potential_templates: tuple[DirectDamageEventTemplate, ...] = ()
    potential_effects: tuple[EventCreationEffect, ...] = ()
    updated_entries = tuple(entries)
    if config.potential_level >= 1:
        p1 = raw_record.potential_details[0]
        p1_source = source_for(HARUMASA_ID, "potential1-ultimate-scatter", EffectSourceType.SPECIAL_MECHANISM, p1.name or p1.level_show_name, raw_moves["残心·散华"].description)
        potential_templates, potential_effects, updated_entries, (_rule_id, _source) = _ultimate_scatter(raw_record, config, tuple(entries))
        templates.extend(potential_templates)
        rules.append(_rule(
            "potential1-ultimate-scatter",
            p1_source,
            "潜能1：终结技后自动派生残心·散华",
            raw_moves["残心·散华"].description,
            RuleEligibility.ELIGIBLE,
            effects=potential_effects,
        ))
        if config.potential_level >= 1:
            core_rule_index = next(index for index, item in enumerate(rules) if item.rule_id == RuleItemId("rule:character:1201:core:dash-crit-buffs"))
            core_rule = rules[core_rule_index]
            core_effects = list(core_rule.effects)
            # The P1 Core explicitly extends its CR/CD bonuses to the ultimate follow-up.
            for index, effect in enumerate(core_effects):
                if not isinstance(effect, ModifierEffect):
                    continue
                existing = next((item for item in effect.rule.filters if isinstance(item, AnyFilter)), None)
                if existing is None:
                    continue
                extras = (*existing.filters, EventTemplateIdFilter(potential_templates[0].ref.template_id))
                core_effects[index] = replace(effect, rule=replace(effect.rule, filters=tuple(item for item in effect.rule.filters if not isinstance(item, AnyFilter)) + (AnyFilter(extras),)))
            rules[core_rule_index] = replace(core_rule, effects=tuple(core_effects))

    return build_definition(
        character_id=HARUMASA_ID,
        role=CharacterRole.ATTACK,
        element=Element.ELECTRIC,
        source=source_for(HARUMASA_ID, "character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=updated_entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


__all__ = ["compile_harumasa", "load_raw_record"]
