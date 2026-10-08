"""Reviewed compiler for Zhu Yuan (character:1241), Nanoka 3.2."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnomalyRecordId,
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
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
    ElementFilter,
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
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    StateId,
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
    ScenarioParameterId,
)
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
)
from .config import ZhuYuanCompileConfig
from .reviewed import (
    ZHU_ADDITIONAL_CRIT_ACTIVE,
    ZHU_C6_ETHER_AFTERGLOW_ACTIVE,
    ZHU_CURRENT_SPECIAL_SHOT_COUNT,
    ZHU_ENHANCED_SHELL_CONSUMED,
    ZHU_SUPPRESSION_MODE_ACTIVE,
    ZHU_YUAN_REVIEWED_MAPPING,
    ZHU_ASSAULT_BASIC_MOVE_ID,
    ZHU_ASSIST_STRIKE_MOVE_ID,
    ZHU_YUAN_ID,
)


_ETHER_ANOMALY_RECORD_ID = "anomaly:character:1241:ether-corrosion"
_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1241:ether-corrosion")
_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1241:ether-corrosion-disorder")
_ANOMALY_MOVE_ID = MoveId("move:zhu-yuan:ether-corrosion")
_DISORDER_MOVE_ID = MoveId("move:zhu-yuan:ether-corrosion-disorder")
_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:zhu-yuan:ether-disorder-remaining-seconds"
)


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


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1241:{key}"),
        owner=ZHU_YUAN_ID,
        source=source,
        display_name=label,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
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
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1241:{key}"),
            source=source,
            owner=ZHU_YUAN_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(modifier_path=node, operation=operation, value=value),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(ZHU_YUAN_ID))


def _validate_raw(raw: NanokaRawRecord) -> None:
    if raw.character_id != ZHU_YUAN_ID:
        raise ValueError("Zhu Yuan raw record and compile config IDs must match")
    if raw.name != "朱鸢" or raw.code_name != "Zhu Yuan":
        raise ValueError("unexpected Zhu Yuan identity")
    if raw.specialty != "强攻" or raw.element != "以太" or raw.rarity != 4:
        raise ValueError("unexpected Zhu Yuan role, element, or rarity")
    if raw.faction != "新艾利都治安局":
        raise ValueError("unexpected Zhu Yuan faction")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1241.json":
        raise ValueError("Zhu Yuan provenance must identify live Nanoka 3.2 character 1241")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Zhu Yuan source must include seven core levels and six mindscapes")


def _unresolved_source_entry(
    raw_moves,
    config: ZhuYuanCompileConfig,
    *,
    key: str,
    label: str,
    source_name: str,
    parameter_name: str,
    source_skill_id: str,
    original_text: str,
    message: str,
    skill_group: SkillGroup | None,
    damage_tags: frozenset[DamageTag],
    move_id: MoveId | None,
    placeholder_element: Element = Element.ETHER,
    ratio: float | None = None,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate, CalculationDiagnostic]:
    if ratio is None:
        value = raw_multiplier(
            raw_moves,
            source_name,
            parameter_name,
            effective_skill_level(config, skill_group or SkillGroup.BASIC_ATTACK),
            f"{ZHU_YUAN_ID}:{key}",
            [],
            source_skill_id=source_skill_id,
        )
        if isinstance(value, Unresolved):
            raise ValueError(f"Zhu Yuan source ratio is missing for {key}")
        ratio = value
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1241:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1241:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=placeholder_element,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=ZHU_YUAN_ID,
        element=placeholder_element,
        base_source=CurrentAttackValueSource(ZHU_YUAN_ID),
        crit_rule=StandardCritRule(ZHU_YUAN_ID),
        move_id=move_id,
    )
    diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1241:{key}:source-semantics"),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message=message,
        blocking=True,
        original_text=original_text,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1241:{key}"),
        character_id=ZHU_YUAN_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=skill_group,
        damage_tags=damage_tags,
        multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1241:{key}:known-source-ratio"),
                label=f"已知源倍率{ratio:.3%}（事件语义待确认）",
                parameter_name=parameter_name,
                multiplier=FixedMultiplier(Resolved(ratio)),
            ),
        ),
        main_damage_event=ref,
        diagnostics=(diagnostic,),
    )
    return entry, template, diagnostic


def _unresolved_assault_basic_entries(raw: NanokaRawRecord, config: ZhuYuanCompileConfig):
    raw_moves = raw_move_index(raw)
    source = raw_moves["普通攻击：不许动！"]
    stages = ("一", "二", "三", "四", "五")
    entries = []
    templates = []
    diagnostics = []
    for stage, source_skill_id in enumerate(("1241001", "1241002", "1241003", "1241004", "1241005"), start=1):
        entry, template, diagnostic = _unresolved_source_entry(
            raw_moves,
            config,
            key=f"assault-basic-stage-{stage}-element-unresolved",
            label=f"普通攻击：不许动！（突击模式第{stages[stage - 1]}段，元素待确认）",
            source_name="普通攻击：不许动！",
            parameter_name=f"{stages[stage - 1]}段伤害倍率",
            source_skill_id=source_skill_id,
            original_text=source.description,
            message="突击模式普通攻击的五段曲线保留，但原文只说明整套会造成物理和以太伤害，没有把元素映射到每一段；确认前不生成事件。",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
            move_id=ZHU_ASSAULT_BASIC_MOVE_ID,
            placeholder_element=Element.ETHER,
        )
        entries.append(entry)
        templates.append(template)
        diagnostics.append(diagnostic)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def _unresolved_assist_strike(raw: NanokaRawRecord, config: ZhuYuanCompileConfig):
    raw_moves = raw_move_index(raw)
    source = raw_moves["支援突击：自卫还击"]
    return _unresolved_source_entry(
        raw_moves,
        config,
        key="assist-strike-mixed-element-unresolved",
        label="支援突击：自卫还击（物理/以太曲线元素拆分待确认）",
        source_name="支援突击：自卫还击",
        parameter_name="伤害倍率",
        source_skill_id="1241025",
        original_text=source.description,
        message="支援突击说明交替造成物理与以太伤害，但只有一个总伤害倍率曲线，元素分量未拆分；确认前不生成事件。",
        skill_group=SkillGroup.ASSIST,
        damage_tags=frozenset({DamageTag.ASSIST}),
        move_id=ZHU_ASSIST_STRIKE_MOVE_ID,
        placeholder_element=Element.ETHER,
    )


def _unresolved_c6_ether_bullets(raw: NanokaRawRecord):
    c6 = raw.mindscapes[5]
    bullet_ratio = _number(c6.description, r"每枚额外发射的以太鹿弹将造成朱鸢(?P<value>[\d.]+)%攻击力的伤害", "Zhu Yuan Cinema 6 bullet ATK ratio") / 100.0
    bullet_count = _number(c6.description, r"额外发射总计(?P<value>[\d.]+)枚以太鹿弹", "Zhu Yuan Cinema 6 extra bullet count")
    total_ratio = bullet_ratio * bullet_count
    return _unresolved_source_entry(
        {},
        ZhuYuanCompileConfig(),
        key="cinema6-extra-ether-bullets-identity-unresolved",
        label=f"6影：以太鹿弹额外子弹（{bullet_count:g}×{bullet_ratio:.2%}攻击力，共{total_ratio:.2%}；伤害身份待确认）",
        source_name="终结技：歼灭模式MAX",
        parameter_name="额外以太鹿弹倍率",
        source_skill_id="",
        original_text=c6.description,
        message="6影明确额外发射4枚以太鹿弹，每枚造成220%攻击力，总倍率880%；元素已知，伤害身份/标签待确认。本行保留倍率但不生成Direct事件或触发武器效果。",
        skill_group=None,
        damage_tags=frozenset(),
        move_id=None,
        placeholder_element=Element.ETHER,
        ratio=total_ratio,
    )


def _static_ether_entries(raw: NanokaRawRecord):
    anomaly_record_id = "anomaly:character:1241:ether-corrosion"
    anomaly_move_id = MoveId("move:zhu-yuan:ether-corrosion")
    disorder_move_id = MoveId("move:zhu-yuan:ether-corrosion-disorder")
    anomaly_ref = DamageEventTemplateRef(
        template_id=_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1241:ether-corrosion"),
        label="属性异常：侵蚀（单跳62.5%，10秒20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ETHER,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=ZHU_YUAN_ID,
        element=Element.ETHER,
        anomaly_triggerer=ZHU_YUAN_ID,
        history_record_source=AnomalyRecordId(anomaly_record_id),
        crit_rule=NoCritRule(),
        move_id=anomaly_move_id,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1241:ether-corrosion"),
        character_id=ZHU_YUAN_ID,
        move_id=anomaly_move_id,
        display_name="属性异常：侵蚀（单跳62.5%，10秒20跳）",
        original_text="静态单人100%积蓄记录按规范结算侵蚀：单跳62.5%，10秒共20跳，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1241:ether-corrosion-tick"),
                label="侵蚀单跳62.5% × 20",
                parameter_name="侵蚀单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.625)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id=_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1241:ether-corrosion-disorder"),
        label="紊乱：以太侵蚀（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ETHER,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ZHU_YUAN_ID,
        element=Element.ETHER,
        disorder_triggerer=ZHU_YUAN_ID,
        history_record_source=AnomalyRecordId(anomaly_record_id),
        crit_rule=NoCritRule(),
        move_id=disorder_move_id,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1241:ether-corrosion-disorder"),
        character_id=ZHU_YUAN_ID,
        move_id=disorder_move_id,
        display_name="紊乱：以太侵蚀（当前剩余时间）",
        original_text="以太紊乱倍率按规范为450% + floor(t)×125%；剩余时间是当前输入，不推演时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1241:ether-corrosion-disorder"),
                label="450% + floor(t) × 125%",
                parameter_name="以太紊乱倍率",
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
        label="以太异常剩余持续时间（秒）",
        original_text="当前以太异常剩余持续时间，范围0–10秒；不模拟时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def compile_zhu_yuan(config: ZhuYuanCompileConfig, raw_record: NanokaRawRecord) -> CharacterCalculationDefinition:
    _validate_raw(raw_record)
    if raw_record.character_id != config.character_id:
        raise ValueError("Zhu Yuan raw record and compile config IDs must match")
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=ZHU_YUAN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=ZHU_YUAN_REVIEWED_MAPPING,
        id_namespace="character:1241",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    basic_entries, basic_templates, _ = _unresolved_assault_basic_entries(raw_record, config)
    entries.extend(basic_entries)
    templates.extend(basic_templates)
    assist_entry, assist_template, _ = _unresolved_assist_strike(raw_record, config)
    entries.append(assist_entry)
    templates.append(assist_template)
    if config.cinema_level >= 6:
        c6_standalone, c6_template, _ = _unresolved_c6_ether_bullets(raw_record)
        entries.append(c6_standalone)
        templates.append(c6_template)
    # Element-unresolved move notes are attached to the affected selector rows.
    raw_moves = raw_move_index(raw_record)
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(ZHU_YUAN_ID, "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = source_for(ZHU_YUAN_ID, "extra-ability", EffectSourceType.ADDITIONAL_ABILITY, raw_record.extra_ability_name, raw_record.extra_ability_description)
    core_bonuses = (
        _number(core.description, r"招式造成的伤害提升(?P<value>[\d.]+)%", "Zhu Yuan Core shell damage bonus") / 100.0,
        _number(core.description, r"该增益效果额外提升(?P<value>[\d.]+)%", "Zhu Yuan Core stunned-target bonus") / 100.0,
    )

    conditions = [
        _condition(ZHU_SUPPRESSION_MODE_ACTIVE, "当前处于压制模式", raw_moves["普通攻击：请勿抵抗"].description),
        _condition(ZHU_ENHANCED_SHELL_CONSUMED, "本次压制模式攻击消耗了强化霰弹", core.description),
    ]
    rules: list[CalculationRuleItem] = []
    pressure_template_ids = tuple(
        item.ref.template_id
        for item in templates
        if "pressure-" in str(item.ref.template_id)
    )
    pressure_direct_filter = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(ZHU_YUAN_ID),
        AnyFilter(tuple(EventTemplateIdFilter(item) for item in pressure_template_ids)),
    )
    rules.append(_rule(
        "core:pressure-spent-shell-damage-bonus",
        core_source,
        f"核心被动：压制模式消耗强化霰弹的当前招式伤害+{core_bonuses[0]:.1%}",
        core.description,
        RuleEligibility.ELIGIBLE,
        conditions=(ZHU_SUPPRESSION_MODE_ACTIVE, ZHU_ENHANCED_SHELL_CONSUMED),
        effects=(
            _modifier(
                "core:pressure-spent-shell-damage-bonus",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(core_bonuses[0]),
                target=EffectTarget.TEAM,
                filters=pressure_direct_filter,
            ),
        ),
    ))
    rules.append(_rule(
        "core:pressure-stunned-target-extra-damage-bonus",
        core_source,
        f"核心被动：目标失衡时当前压制强化弹招式额外伤害+{core_bonuses[1]:.1%}",
        core.description,
        RuleEligibility.ELIGIBLE,
        conditions=(ZHU_SUPPRESSION_MODE_ACTIVE, ZHU_ENHANCED_SHELL_CONSUMED),
        effects=(
            _modifier(
                "core:pressure-stunned-target-extra-damage-bonus",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(core_bonuses[1]),
                target=EffectTarget.TEAM,
                filters=(*pressure_direct_filter, EnemyStateFilter(StateId("state:enemy:stunned"))),
            ),
        ),
    ))

    if config.additional_ability_eligible:
        extra_description = raw_record.extra_ability_description
        additional_crit_bonus = _number(
            extra_description,
            r"自身暴击率提升(?P<value>[\d.]+)%",
            "Zhu Yuan Additional Ability Crit Rate bonus",
        ) / 100.0
        conditions.append(_condition(ZHU_ADDITIONAL_CRIT_ACTIVE, "朱鸢的额外能力暴击率增益当前生效", extra_description))
        rules.append(_rule(
            "extra-ability:self-crit-rate",
            extra_source,
            f"额外能力：当前朱鸢暴击率+{additional_crit_bonus:.1%}",
            extra_description,
            RuleEligibility.ELIGIBLE,
            conditions=(ZHU_ADDITIONAL_CRIT_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:self-crit-rate",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(additional_crit_bonus),
                    target=EffectTarget.SELF,
                ),
            ),
        ))
    else:
        rules.append(_rule(
            "extra-ability:self-crit-rate",
            extra_source,
            "额外能力：当前队伍未满足支援或同阵营条件",
            raw_record.extra_ability_description,
            RuleEligibility.INELIGIBLE,
        ))

    cinema2_source = source_for(ZHU_YUAN_ID, "cinema2", EffectSourceType.CINEMA, raw_record.mindscapes[1].name, raw_record.mindscapes[1].description)
    cinema4_source = source_for(ZHU_YUAN_ID, "cinema4", EffectSourceType.CINEMA, raw_record.mindscapes[3].name, raw_record.mindscapes[3].description)
    cinema6_source = source_for(ZHU_YUAN_ID, "cinema6", EffectSourceType.CINEMA, raw_record.mindscapes[5].name, raw_record.mindscapes[5].description)
    pressure_ether_template_ids = tuple(
        item.ref.template_id
        for item in templates
        if "pressure-" in str(item.ref.template_id) and "ether" in str(item.ref.template_id)
    )
    pressure_ether_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(ZHU_YUAN_ID),
        ElementFilter(Element.ETHER),
        AnyFilter(tuple(EventTemplateIdFilter(item) for item in pressure_ether_template_ids)),
    )
    if config.cinema_level >= 2:
        cinema2_bonus = _number(raw_record.mindscapes[1].description, r"以太伤害提升(?P<value>[\d.]+)%", "Zhu Yuan Cinema 2 Ether damage bonus") / 100.0
        rules.append(_rule(
            "cinema2:ethereal-remnant-ether-damage",
            cinema2_source,
            f"2影：当前以太余烬层数×{cinema2_bonus:.1%}（限压制模式基础/冲刺以太分项）",
            raw_record.mindscapes[1].description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:ethereal-remnant-ether-damage",
                    cinema2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(cinema2_bonus),
                    target=EffectTarget.SELF,
                    filters=pressure_ether_filters,
                ),
            ),
            stack_count=5,
            stack_min=0,
            stack_max=5,
        ))
    if config.cinema_level >= 4:
        cinema4_res_ignore = _number(raw_record.mindscapes[3].description, r"无视目标(?P<value>[\d.]+)%以太伤害抗性", "Zhu Yuan Cinema 4 Ether resistance ignore") / 100.0
        rules.append(_rule(
            "cinema4:pressure-spent-shell-ether-resistance-ignore",
            cinema4_source,
            f"4影：消耗强化霰弹的压制模式以太分项无视{cinema4_res_ignore:.1%}以太抗性",
            raw_record.mindscapes[3].description,
            RuleEligibility.ELIGIBLE,
            conditions=(ZHU_SUPPRESSION_MODE_ACTIVE, ZHU_ENHANCED_SHELL_CONSUMED),
            effects=(
                _modifier(
                    "cinema4:pressure-spent-shell-ether-resistance-ignore",
                    cinema4_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(cinema4_res_ignore),
                    target=EffectTarget.TEAM,
                    filters=pressure_ether_filters,
                ),
            ),
        ))
    parameters = [
        ScenarioIntegerParameter(
            parameter_id=ZHU_CURRENT_SPECIAL_SHOT_COUNT,
            label="本次特殊技鹿弹射击次数",
            original_text=raw_moves["特殊技：鹿弹射击"].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=1,
            minimum=1,
            maximum=3,
        ),
    ]
    special_index = next(
        index for index, item in enumerate(entries)
        if str(item.entry_id) == "move-entry:character:1241:special-ether-single-shot"
    )
    special_entry = entries[special_index]
    special_variant = special_entry.multiplier_variants[0]
    entries[special_index] = replace(
        special_entry,
        display_name="特殊技：鹿弹射击（当前射击次数）",
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(replace(special_variant, repeat_count_parameter_id=ZHU_CURRENT_SPECIAL_SHOT_COUNT),),
    )

    if config.cinema_level >= 6:
        c6 = raw_record.mindscapes[5]
        c6_source = source_for(ZHU_YUAN_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
        conditions.append(_condition(ZHU_C6_ETHER_AFTERGLOW_ACTIVE, "以太余温当前生效，下一次强化特殊技将额外发射鹿弹", c6.description))
        c6_unresolved = Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_TEXT,
            notes="C6 specifies four additional Ether Deer bullets at 220% of Zhu Yuan's ATK each (880% total). Their Direct/Crit/SkillGroup/DamageTag inheritance is pending confirmation; no typed child event is fabricated.",
            original_text=c6.description,
        )
        ex_template_id = EventTemplateId("template:character:1241:ex-ether:main")
        rules.append(_rule(
            "cinema6:extra-ether-bullets",
            c6_source,
            "6影：以太余温额外四枚以太鹿弹（伤害身份待确认）",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(ZHU_C6_ETHER_AFTERGLOW_ACTIVE,),
            effects=(EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId("effect:character:1241:cinema6:extra-ether-bullets"),
                    source=c6_source,
                    owner=ZHU_YUAN_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(ZHU_YUAN_ID),
                        EventTemplateIdFilter(ex_template_id),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    unresolved_template=c6_unresolved,
                    unique_per_source_event=True,
                ),
            ),),
        ))

    static_entries, static_templates, disorder_seconds = _static_ether_entries(raw_record)
    entries.extend(static_entries)
    templates.extend(static_templates)
    return build_definition(
        character_id=ZHU_YUAN_ID,
        role=CharacterRole.ATTACK,
        element=Element.ETHER,
        source=source_for(ZHU_YUAN_ID, "character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(*parameters, disorder_seconds),
        diagnostics=diagnostics,
    )


__all__ = ["compile_zhu_yuan", "load_raw_record"]
