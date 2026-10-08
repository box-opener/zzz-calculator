"""Reviewed compiler for Rina (character:1211), Nanoka 3.2."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re

from core.types import (
    AnomalyRecordId,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageSubtype,
    DamageTag,
    DamageType,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventTemplateId,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    PanelStatDerivedValue,
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
from .config import RinaCompileConfig
from .reviewed import (
    RINA_C2_DAMAGE_BONUS_ACTIVE,
    RINA_C4_DOLLS_AWAY,
    RINA_C6_ELECTRIC_DAMAGE_BONUS_ACTIVE,
    RINA_CORE_BUFF_ACTIVE,
    RINA_DOLLS_NEARBY_BONUS_ACTIVE,
    RINA_ELECTRIC_ANOMALY_RECORD_ID,
    RINA_FEAR_STACKS_FULL,
    RINA_ID,
    RINA_BASIC_MOVE_ID,
    RINA_MORNING_SWEEP_MOVE_ID,
    RINA_TARGET_SHOCKED,
    reviewed_mapping,
)


_SHOCK_TEMPLATE_ID = EventTemplateId("template:character:1211:electric-shock")
_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1211:electric-disorder")
_SHOCK_MOVE_ID = MoveId("move:rina:electric-shock")
_DISORDER_MOVE_ID = MoveId("move:rina:electric-disorder")
_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:rina:electric-disorder-remaining-seconds"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    found = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(found) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(found)}")
    return float(found[0].group("value"))


def _condition(condition_id, label: str, text: str, value: bool = False) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
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
    condition_not=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1211:{key}"),
        owner=RINA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        condition_not_ids=tuple(condition_not),
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
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1211:{key}"),
            source=source,
            owner=RINA_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(modifier_path=node, operation=operation, value=value),
    )


def load_raw_record(
    data: Mapping[str, object],
    *,
    potential_level: int = 0,
) -> NanokaRawRecord:
    if not 0 <= potential_level <= 6:
        raise ValueError("Rina potential_level must be between 0 and 6")
    raw = load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(RINA_ID))
    if potential_level and not any(item.level == potential_level for item in raw.potential_details):
        raise ValueError(f"Rina source is missing Potential {potential_level}")
    return raw


def _validate_raw(raw: NanokaRawRecord) -> None:
    if raw.character_id != RINA_ID:
        raise ValueError("Rina raw record and compile config IDs must match")
    if raw.name != "丽娜" or raw.code_name != "Rina":
        raise ValueError("unexpected Rina identity")
    if raw.specialty != "支援" or raw.element != "电属性" or raw.rarity != 4:
        raise ValueError("unexpected Rina role, element, or rank")
    if raw.faction != "维多利亚家政":
        raise ValueError("unexpected Rina faction")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1211.json":
        raise ValueError("Rina provenance must identify live Nanoka 3.2 character 1211")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Rina source must include seven core levels and six mindscapes")


def _unresolved_source_move(
    raw_moves,
    config: RinaCompileConfig,
    *,
    key: str,
    label: str,
    source_name: str,
    parameter_name: str,
    source_skill_id: str,
    original_text: str,
    unresolved_message: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    move_id: MoveId | None,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate, CalculationDiagnostic]:
    ratio = raw_multiplier(
        raw_moves,
        source_name,
        parameter_name,
        effective_skill_level(config, group),
        f"{RINA_ID}:{key}",
        [],
        source_skill_id=source_skill_id,
    )
    if isinstance(ratio, Unresolved):
        raise ValueError(f"Rina source ratio is missing for {key}")
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1211:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1211:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=tags,
        element=Element.PHYSICAL,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=RINA_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(RINA_ID),
        crit_rule=StandardCritRule(RINA_ID),
        move_id=move_id,
    )
    diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1211:{key}:element"),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message=unresolved_message,
        blocking=True,
        original_text=original_text,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1211:{key}"),
        character_id=RINA_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=group,
        damage_tags=tags,
        multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1211:{key}:known-ratio"),
                label=f"已知源倍率{ratio:.3%}（元素待确认）",
                parameter_name=parameter_name,
                multiplier=FixedMultiplier(Resolved(ratio)),
            ),
        ),
        main_damage_event=ref,
        diagnostics=(diagnostic,),
    )
    return entry, template, diagnostic


def _ambiguous_element_entries(raw: NanokaRawRecord, config: RinaCompileConfig):
    raw_moves = raw_move_index(raw)
    basic_source = raw_moves["普通攻击：痛打呆子"]
    stage_names = ("一段", "二段", "三段", "四段")
    entries = []
    templates = []
    diagnostics = []
    for stage, source_skill_id in enumerate(("1211001", "1211003", "1211004", "1211006"), start=1):
        entry, template, diagnostic = _unresolved_source_move(
            raw_moves,
            config,
            key=f"basic-stage-{stage}-element-unresolved",
            label=f"普通攻击：痛打呆子（{stage_names[stage - 1]}，元素待确认）",
            source_name="普通攻击：痛打呆子",
            parameter_name=f"{stage_names[stage - 1]}伤害倍率",
            source_skill_id=source_skill_id,
            original_text=basic_source.description,
            unresolved_message="普通攻击说明整套四段同时造成物理与电属性伤害，但没有把元素分配到各段；本段倍率保留，确认前不生成伤害事件。",
            group=SkillGroup.BASIC_ATTACK,
            tags=frozenset({DamageTag.BASIC_ATTACK}),
            move_id=RINA_BASIC_MOVE_ID,
        )
        entries.append(entry)
        templates.append(template)
        diagnostics.append(diagnostic)

    if config.potential_level >= 1:
        sweep_source = raw_moves["普通攻击：晨间清扫"]
        for stage, source_skill_id in enumerate(("1211023", "1211024", "1211025"), start=1):
            entry, template, diagnostic = _unresolved_source_move(
                raw_moves,
                config,
                key=f"potential1-morning-sweep-hit-{stage}-element-unresolved",
                label=f"潜能1：普通攻击·晨间清扫（第{stage}次来源倍率，元素待确认）",
                source_name="普通攻击：晨间清扫",
                parameter_name=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
                source_skill_id=source_skill_id,
                original_text=sweep_source.description,
                unresolved_message="晨间清扫每次攻击的倍率已保留，但原文列物理与电属性伤害、参数表未给出各元素倍率；此单次来源倍率在元素关系确认前不生成伤害事件。",
                group=SkillGroup.BASIC_ATTACK,
                tags=frozenset({DamageTag.BASIC_ATTACK}),
                move_id=RINA_MORNING_SWEEP_MOVE_ID,
            )
            entries.append(entry)
            templates.append(template)
            diagnostics.append(diagnostic)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def _static_electric_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=_SHOCK_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1211:electric-shock"),
        label="属性异常：感电（单跳125%，10秒10跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=RINA_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=RINA_ID,
        history_record_source=RINA_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_SHOCK_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1211:electric-shock"),
        character_id=RINA_ID,
        move_id=_SHOCK_MOVE_ID,
        display_name="属性异常：感电（单跳125%，10秒10跳）",
        original_text="静态单人100%电属性异常记录；感电每跳125%，持续10秒，共10跳；使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1211:electric-shock-tick"),
                label="感电单跳125% × 10",
                parameter_name="感电单跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id=_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1211:electric-disorder"),
        label="紊乱：感电（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=RINA_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=RINA_ID,
        history_record_source=RINA_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1211:electric-disorder"),
        character_id=RINA_ID,
        move_id=_DISORDER_MOVE_ID,
        display_name="紊乱：感电（当前剩余时间）",
        original_text="感电紊乱倍率按规范为450% + floor(t)×125%；剩余时间是当前输入，不推演感电时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1211:electric-disorder"),
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
    remaining = ScenarioIntegerParameter(
        parameter_id=_DISORDER_REMAINING_SECONDS,
        label="当前目标感电剩余时间（秒）",
        original_text="使用当前剩余时间，范围0–10秒；不模拟感电时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def compile_rina(config: RinaCompileConfig, raw_record: NanokaRawRecord) -> CharacterCalculationDefinition:
    _validate_raw(raw_record)
    if raw_record.character_id != config.character_id:
        raise ValueError("Rina raw record and compile config IDs must match")
    raw_moves = raw_move_index(raw_record)
    mapping = reviewed_mapping(potential_level=config.potential_level)
    direct_entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=RINA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1211",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    all_diagnostics = list(diagnostics)
    conditions = [
        _condition(RINA_CORE_BUFF_ACTIVE, "丽娜的杜苏拉或安娜塔莎当前被指派在外", raw_record.core_levels[config.core_level - 1].description),
    ]
    if config.additional_ability_eligible:
        conditions.append(_condition(RINA_TARGET_SHOCKED, "当前目标处于感电状态", raw_record.extra_ability_description))
    if config.cinema_level >= 1:
        conditions.append(
            _condition(
                RINA_DOLLS_NEARBY_BONUS_ACTIVE,
                "本次受益的其他角色均处于杜苏拉或安娜塔莎附近10米范围内",
                raw_record.mindscapes[0].description,
            )
        )
    if config.potential_level >= 1:
        conditions.append(
            _condition(
                RINA_FEAR_STACKS_FULL,
                "当前惊吓层数达到6层，可触发午夜清扫",
                raw_moves["普通攻击：午夜清扫"].description,
            )
        )
    if config.cinema_level >= 2:
        conditions.append(_condition(RINA_C2_DAMAGE_BONUS_ACTIVE, "丽娜的2影伤害增益当前生效", raw_record.mindscapes[1].description))
    if config.cinema_level >= 4:
        conditions.append(_condition(RINA_C4_DOLLS_AWAY, "杜苏拉与安娜塔莎当前均在外", raw_record.mindscapes[3].description))
    if config.cinema_level >= 6:
        conditions.append(_condition(RINA_C6_ELECTRIC_DAMAGE_BONUS_ACTIVE, "丽娜的6影电属性伤害增益当前生效", raw_record.mindscapes[5].description))

    unresolved_entries, unresolved_templates, _ = _ambiguous_element_entries(raw_record, config)
    entries.extend(unresolved_entries)
    templates.extend(unresolved_templates)
    static_entries, static_templates, disorder_remaining = _static_electric_entries(raw_record)
    entries.extend(static_entries)
    templates.extend(static_templates)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(RINA_ID, "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = source_for(RINA_ID, "extra-ability", EffectSourceType.ADDITIONAL_ABILITY, raw_record.extra_ability_name, raw_record.extra_ability_description)
    extra_electric_damage_bonus = _number(
        raw_record.extra_ability_description,
        r"电属性伤害提升(?P<value>[\d.]+)%",
        "Rina Additional Ability Electric damage bonus",
    ) / 100.0
    shock_duration_note = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1211:extra-ability:shock-duration"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message="The Additional Ability also extends Shock duration by 3 seconds. Duration and anomaly-timing output are not simulated; this note does not change damage settlement.",
        blocking=False,
        original_text=raw_record.extra_ability_description,
    )
    core_pen_percent = _number(core.description, r"丽娜(?P<value>[\d.]+)%穿透率", "Rina Core PEN coefficient") / 100.0
    core_pen_base = _number(core.description, r"穿透率\+(?P<value>[\d.]+)%", "Rina Core flat PEN") / 100.0
    core_pen_cap = _number(core.description, r"最高提升(?P<value>[\d.]+)%", "Rina Core PEN cap") / 100.0
    core_pen_value = PanelStatDerivedValue(
        source_character_id=RINA_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        coefficient=Resolved(core_pen_percent),
        base=Resolved(core_pen_base),
        cap_max=Resolved(core_pen_cap),
    )
    core_buff_multiplier = (
        _number(
            raw_record.mindscapes[0].description,
            r"提升至原本的(?P<value>[\d.]+)%",
            "Rina Cinema 1 nearby Core buff multiplier",
        ) / 100.0
        if config.cinema_level >= 1
        else 1.0
    )
    enhanced_pen_value = PanelStatDerivedValue(
        source_character_id=RINA_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        coefficient=Resolved(core_pen_percent * core_buff_multiplier),
        base=Resolved(core_pen_base * core_buff_multiplier),
        cap_max=Resolved(core_pen_cap * core_buff_multiplier),
    )
    core_pen_effect = _modifier(
        "core:other-agents-penetration-rate",
        core_source,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        core_pen_value,
        target=EffectTarget.TEAM_OTHER,
    )
    enhanced_pen_effect = _modifier(
        "core:other-agents-penetration-rate-enhanced",
        core_source,
        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
        enhanced_pen_value,
        target=EffectTarget.TEAM_OTHER,
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:other-agents-penetration-rate",
            core_source,
            "核心被动：丽娜当前穿透率的25%+固定穿透率（最多30%）赋予其他队员",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(RINA_CORE_BUFF_ACTIVE,),
            condition_not=(RINA_DOLLS_NEARBY_BONUS_ACTIVE,) if config.cinema_level >= 1 else (),
            effects=(core_pen_effect,),
        ),
    ]
    if config.cinema_level >= 1:
        rules.append(
            _rule(
                "core:other-agents-penetration-rate-enhanced",
                core_source,
                "1影/潜能1：核心穿透率增益提升至130%（10米范围）",
                raw_record.mindscapes[0].description,
                RuleEligibility.ELIGIBLE,
                conditions=(RINA_CORE_BUFF_ACTIVE, RINA_DOLLS_NEARBY_BONUS_ACTIVE),
                effects=(enhanced_pen_effect,),
            )
        )

    if config.additional_ability_eligible:
        rules.append(
            _rule(
                "extra-ability:team-electric-damage-while-shocked",
                extra_source,
                "额外能力：目标感电时全队电属性伤害+10%",
                raw_record.extra_ability_description,
                RuleEligibility.ELIGIBLE,
                conditions=(RINA_TARGET_SHOCKED,),
                effects=(
                    _modifier(
                        "extra-ability:team-electric-damage-while-shocked",
                        extra_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(extra_electric_damage_bonus),
                        target=EffectTarget.TEAM,
                        filters=(ElementFilter(Element.ELECTRIC),),
                    ),
                ),
                diagnostics=(shock_duration_note,),
            )
        )
    else:
        rules.append(_rule(
            "extra-ability:team-electric-damage-while-shocked",
            extra_source,
            "额外能力：当前队伍未满足同属性或同阵营条件",
            raw_record.extra_ability_description,
            RuleEligibility.INELIGIBLE,
            diagnostics=(shock_duration_note,),
        ))

    parameters = [disorder_remaining]
    if config.potential_level >= 2:
        detail = next(item for item in raw_record.potential_details if item.level == config.potential_level)
        pen_bonus = _number(detail.description, r"穿透率提升(?P<value>[\d.]+)%", "Rina Potential PEN bonus") / 100.0
        atk_per_one_percent = _number(detail.description, r"每1%，全队角色攻击力和防御力分别提升(?P<value>[\d.]+)点", "Rina Potential ATK per PEN")
        def_match = re.search(r"全队角色攻击力和防御力分别提升[\d.]+点和(?P<value>[\d.]+)点", _plain(detail.description))
        cap_atk = _number(detail.description, r"至多提升(?P<value>[\d.]+)点攻击力", "Rina Potential ATK cap")
        cap_def = _number(detail.description, r"点攻击力和(?P<value>[\d.]+)点防御力", "Rina Potential DEF cap")
        if def_match is None:
            raise ValueError("Rina Potential source is missing DEF coefficient")
        atk_value = PanelStatDerivedValue(
            source_character_id=RINA_ID,
            source_node=CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
            coefficient=Resolved(atk_per_one_percent * 100.0),
            cap_max=Resolved(cap_atk),
        )
        def_value = PanelStatDerivedValue(
            source_character_id=RINA_ID,
            source_node=CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
            coefficient=Resolved(float(def_match.group("value")) * 100.0),
            cap_max=Resolved(cap_def),
        )
        potential_source = source_for(
            RINA_ID,
            f"potential{config.potential_level}",
            EffectSourceType.SPECIAL_MECHANISM,
            detail.name or detail.level_show_name,
            detail.description,
        )
        rules.append(
            _rule(
                "potential2-6:self-penetration-rate",
                potential_source,
                f"潜能{config.potential_level}：穿透率+{pen_bonus:.1%}",
                detail.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "potential2-6:self-penetration-rate",
                        potential_source,
                        CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
                        Resolved(pen_bonus),
                        target=EffectTarget.SELF,
                    ),
                ),
            )
        )
        rules.extend((
            _rule(
                "potential2-6:team-atk-def-from-pen",
                potential_source,
                f"潜能{config.potential_level}：核心增益期间全队攻击力/防御力随丽娜穿透率提升",
                detail.description,
                RuleEligibility.ELIGIBLE,
                conditions=(RINA_CORE_BUFF_ACTIVE,),
                effects=(
                    _modifier("potential2-6:team-attack-from-pen", potential_source, CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS, atk_value, target=EffectTarget.TEAM),
                    _modifier("potential2-6:team-defense-from-pen", potential_source, CalculationNode.CHARACTER_COMBAT_DEFENSE_FLAT_BONUS, def_value, target=EffectTarget.TEAM),
                ),
            ),
        ))

    if config.cinema_level >= 2:
        c2 = raw_record.mindscapes[1]
        c2_source = source_for(RINA_ID, "cinema2", EffectSourceType.CINEMA, c2.name, c2.description)
        c2_damage_bonus = _number(c2.description, r"伤害提升(?P<value>[\d.]+)%", "Rina Cinema 2 damage bonus") / 100.0
        rules.append(_rule(
            "cinema2:self-damage-bonus",
            c2_source,
            "2影：丽娜当前伤害+15%",
            c2.description,
            RuleEligibility.ELIGIBLE,
            conditions=(RINA_C2_DAMAGE_BONUS_ACTIVE,),
            effects=(_modifier("cinema2:self-damage-bonus", c2_source, CalculationNode.DAMAGE_NORMAL_BONUS, Resolved(c2_damage_bonus), target=EffectTarget.SELF),),
        ))
    if config.cinema_level >= 4:
        c4 = raw_record.mindscapes[3]
        c4_source = source_for(RINA_ID, "cinema4", EffectSourceType.CINEMA, c4.name, c4.description)
        c4_energy_regen = _number(c4.description, r"能量自动回复速度提升(?P<value>[\d.]+)点/秒", "Rina Cinema 4 Energy Regeneration bonus")
        rules.append(_rule(
            "cinema4:energy-regen-while-dolls-away",
            c4_source,
            "4影：杜苏拉与安娜塔莎在外时能量自动回复+0.5",
            c4.description,
            RuleEligibility.ELIGIBLE,
            conditions=(RINA_C4_DOLLS_AWAY,),
            effects=(_modifier("cinema4:energy-regen-while-dolls-away", c4_source, CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS, Resolved(c4_energy_regen), target=EffectTarget.SELF),),
        ))
    if config.cinema_level >= 6:
        c6 = raw_record.mindscapes[5]
        c6_source = source_for(RINA_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
        c6_electric_damage_bonus = _number(c6.description, r"电属性伤害提升(?P<value>[\d.]+)%", "Rina Cinema 6 Electric damage bonus") / 100.0
        rules.append(_rule(
            "cinema6:team-electric-damage-bonus",
            c6_source,
            "6影：当前电属性伤害增益+15%",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(RINA_C6_ELECTRIC_DAMAGE_BONUS_ACTIVE,),
            effects=(_modifier("cinema6:team-electric-damage-bonus", c6_source, CalculationNode.DAMAGE_NORMAL_BONUS, Resolved(c6_electric_damage_bonus), target=EffectTarget.TEAM, filters=(ElementFilter(Element.ELECTRIC),)),),
        ))

    return build_definition(
        character_id=RINA_ID,
        role=CharacterRole.SUPPORT,
        element=Element.ELECTRIC,
        source=source_for(RINA_ID, "character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=all_diagnostics,
    )


__all__ = ["compile_rina", "load_raw_record"]
