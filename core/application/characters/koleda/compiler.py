"""Compile Koleda's reviewed live Nanoka 3.2 record."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageTagFilter,
    DamageTag,
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
    EnemyStateFilter,
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
    ScenarioParameterDerivedValue,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    StateId,
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
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import KoledaCompileConfig
from .reviewed import (
    BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,
    BEN_ENHANCED_FOLLOWUP_ACTIVE,
    BEN_ID,
    CINEMA4_CURRENT_FURNACE_LAYERS,
    CHAIN_ATTACK_MOVE_ID,
    DASH_MOVE_ID,
    DODGE_COUNTER_MOVE_ID,
    ENHANCED_BASIC_MOVE_ID,
    EXTRA_ABILITY_TARGET_MARK_ACTIVE,
    EX_SPECIAL_MOVE_ID,
    FIRE_ANOMALY_MOVE_ID,
    FIRE_DISORDER_MOVE_ID,
    FIRE_DISORDER_REMAINING_SECONDS,
    KOLEDA_ID,
    POTENTIAL1_ENHANCED_BASIC_LAYERS,
    POTENTIAL1_TEAM_DAMAGE_ACTIVE,
    QUICK_ASSIST_MOVE_ID,
    SPECIAL_MOVE_ID,
    ULTIMATE_MOVE_ID,
    reviewed_mapping,
)


_FIRE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1101:fire-burn")
_ENEMY_STUNNED = StateId("state:enemy:stunned")
_ENHANCED_BASIC_STAGE2_TEMPLATE = EventTemplateId(
    "template:character:1101:enhanced-basic-stage2:main"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(KOLEDA_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
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
        rule_id=RuleItemId(f"rule:character:1101:{key}"),
        owner=KOLEDA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
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
    condition=None,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1101:{key}"),
            source=source,
            owner=KOLEDA_ID,
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


def _diagnostic(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1101:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _potential_view(
    data: Mapping[str, object], potential_level: int
) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("potential_level must be between 0 and 6")
    details = data.get("potential_detail")
    if not isinstance(details, Mapping):
        raise ValueError("Koleda source has no potential_detail map")
    selected_id: int | None = None
    if potential_level:
        detail = next(
            (
                item
                for item in details.values()
                if isinstance(item, Mapping) and item.get("level") == potential_level
            ),
            None,
        )
        if detail is None or isinstance(detail.get("id"), bool) or not isinstance(detail.get("id"), int):
            raise ValueError(f"Koleda source has no Potential level {potential_level}")
        selected_id = int(detail["id"])

    def is_base(value: object) -> bool:
        return value is None or (
            isinstance(value, (list, tuple)) and (not value or 0 in value)
        )

    def select(value: object) -> bool:
        if is_base(value):
            return True
        return (
            selected_id is not None
            and isinstance(value, (list, tuple))
            and selected_id in value
        )

    def select_passive(value: object) -> bool:
        if value is None:
            return True
        if potential_level == 0:
            return is_base(value)
        return (
            isinstance(value, (list, tuple))
            and selected_id is not None
            and selected_id in value
        )

    view = deepcopy(dict(data))
    skill = view.get("skill")
    if isinstance(skill, dict):
        for section in skill.values():
            if isinstance(section, dict) and isinstance(section.get("description"), list):
                section["description"] = [
                    item
                    for item in section["description"]
                    if isinstance(item, dict) and select(item.get("potential"))
                ]
    passive = view.get("passive")
    if isinstance(passive, dict) and isinstance(passive.get("level"), dict):
        passive["level"] = {
            key: item
            for key, item in passive["level"].items()
            if isinstance(item, dict) and select_passive(item.get("potential"))
        }
    return view


def load_raw_record(
    data: Mapping[str, object], *, potential_level: int = 0
) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_view(data, potential_level),
        expected_character_id=str(KOLEDA_ID),
    )


def _static_fire_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1101:fire-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1101:fire-anomaly"),
        label="属性异常：灼烧（10秒，20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=KOLEDA_ID,
        element=Element.FIRE,
        anomaly_triggerer=KOLEDA_ID,
        history_record_source=_FIRE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1101:fire-anomaly"),
        character_id=KOLEDA_ID,
        move_id=FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（10秒，20跳）",
        original_text=(
            "按规范的火属性异常固定倍率：每0.5秒造成异常效果强度的50%，10秒共20跳；"
            "静态单人按100%积蓄并使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1101:fire-anomaly-tick"),
                label="灼烧每跳50%（10秒20跳）",
                parameter_name="灼烧每跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1101:fire-disorder",
        semantic_id=DamageEventSemanticId("event:character:1101:fire-disorder"),
        label="紊乱：灼烧",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=KOLEDA_ID,
        element=Element.FIRE,
        disorder_triggerer=KOLEDA_ID,
        history_record_source=_FIRE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1101:fire-disorder"),
        character_id=KOLEDA_ID,
        move_id=FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧（默认最大剩余时间）",
        original_text=(
            "按规范默认450%紊乱基础倍率 + floor(t/0.5)×50%灼烧剩余时间补偿；"
            "以整数秒输入0–10秒，默认10秒，不推断触发时间，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1101:fire-disorder"),
                label="450% + floor(t/0.5) × 50%",
                parameter_name="灼烧紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=FIRE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.0,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=FIRE_DISORDER_REMAINING_SECONDS,
        label="灼烧紊乱时目标剩余持续时间（秒）",
        original_text=(
            "规范补偿为floor(t/0.5)×50%；按整数秒独立选择0–10秒，默认10秒，"
            "不从触发时序推断。"
        ),
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        remaining,
    )


def _complete_two_component_entry(
    *,
    entries: list[MoveCalculationEntry],
    templates: list[DirectDamageEventTemplate],
    first_key: str,
    second_key: str,
    entry_key: str,
    label: str,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    first = next(item for item in entries if item.entry_id == MoveEntryId(f"move-entry:character:1101:{first_key}"))
    second = next(item for item in entries if item.entry_id == MoveEntryId(f"move-entry:character:1101:{second_key}"))
    first_multiplier = first.multiplier_variants[0].multiplier
    second_multiplier = second.multiplier_variants[0].multiplier
    if (
        not isinstance(first_multiplier, FixedMultiplier)
        or not isinstance(first_multiplier.value, Resolved)
        or not isinstance(second_multiplier, FixedMultiplier)
        or not isinstance(second_multiplier.value, Resolved)
    ):
        raise ValueError(f"Koleda complete entry source components are unresolved: {entry_key}")
    total_multiplier = first_multiplier.value.value + second_multiplier.value.value
    base_template = next(
        item for item in templates if item.ref.template_id == first.main_damage_event.template_id
    )
    new_template_ref = replace(
        first.main_damage_event,
        template_id=EventTemplateId(f"template:character:1101:{entry_key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1101:{entry_key}:main"),
        label=label,
    )
    complete_entry = replace(
        first,
        entry_id=MoveEntryId(f"move-entry:character:1101:{entry_key}"),
        display_name=label,
        original_text=(
            f"{first.original_text}\n{second.original_text}\n"
            "完整单次施放总倍率按源打击与引爆两项各一次相加，不推断额外次数。"
        ),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1101:{entry_key}"),
                label="打击倍率 + 引爆倍率",
                parameter_name="完整单次施放总倍率",
                multiplier=FixedMultiplier(Resolved(total_multiplier)),
            ),
        ),
        main_damage_event=new_template_ref,
        stage_index=None,
        condition_ids=(),
        diagnostics=(),
    )
    complete_template = replace(base_template, ref=new_template_ref)
    return complete_entry, complete_template


def _source_potential_level(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.potential_details if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"Koleda raw source is missing Potential level {level}") from exc


def compile_koleda(
    config: KoledaCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    mapping = reviewed_mapping(
        ben_in_team=config.ben_in_team,
        potential_level=config.potential_level,
    )
    entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=KOLEDA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1101",
    )
    entries = list(entries)
    direct_templates = list(direct_templates)
    for first_key, second_key, entry_key, label in (
        (
            "special-impact",
            "special-explosion",
            "special-complete",
            "特殊技：爆破！铁锤时间（完整单次施放）",
        ),
        (
            "ex-special-impact",
            "ex-special-explosion",
            "ex-special-complete",
            "强化特殊技：沸腾熔炉（完整单次施放）",
        ),
    ):
        complete_entry, complete_template = _complete_two_component_entry(
            entries=entries,
            templates=direct_templates,
            first_key=first_key,
            second_key=second_key,
            entry_key=entry_key,
            label=label,
        )
        entries.append(complete_entry)
        direct_templates.append(complete_template)
    static_entries, static_templates, disorder_remaining = _static_fire_entries()
    parameters: list[ScenarioIntegerParameter] = [disorder_remaining]

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    c1 = raw_record.mindscapes[0]
    c1_source = _source("cinema-1", EffectSourceType.CINEMA, c1.name, c1.description)
    c2 = raw_record.mindscapes[1]
    c2_source = _source("cinema-2", EffectSourceType.CINEMA, c2.name, c2.description)
    c3 = raw_record.mindscapes[2]
    c3_source = _source("cinema-3", EffectSourceType.CINEMA, c3.name, c3.description)
    c4 = raw_record.mindscapes[3]
    c4_source = _source("cinema-4", EffectSourceType.CINEMA, c4.name, c4.description)
    c5 = raw_record.mindscapes[4]
    c5_source = _source("cinema-5", EffectSourceType.CINEMA, c5.name, c5.description)
    c6 = raw_record.mindscapes[5]
    c6_source = _source("cinema-6", EffectSourceType.CINEMA, c6.name, c6.description)

    conditions: list[ScenarioCondition] = []
    if config.ben_in_team:
        conditions.append(
            _condition(
                BEN_ENHANCED_FOLLOWUP_ACTIVE,
                "本次特殊技/强化特殊技衔接在强化普攻后快速发动（珂蕾妲与本协同）",
                raw_record.moves[[item.name for item in raw_record.moves].index("强化特殊技：沸腾熔炉")].description,
            )
        )
        if config.potential_level >= 1:
            conditions.append(
                _condition(
                    BEN_ENHANCED_BASIC_FIRST_STAGE_NO_SWITCH,
                    "本次潜能强化普攻第一段期间未切换代理人（珂蕾妲与本协同）",
                    next(
                        item.description
                        for item in raw_record.moves
                        if item.name == "普通攻击：砸扁，粉碎"
                    ),
                )
            )
    if config.potential_level >= 1:
        basic = next(item for item in raw_record.moves if item.name == "普通攻击：砸扁，粉碎")
        conditions.append(
            _condition(
                POTENTIAL1_TEAM_DAMAGE_ACTIVE,
                "潜能：消耗熔炉升温后的全队伤害增益当前有效",
                basic.description,
            )
        )
        parameters.append(
            ScenarioIntegerParameter(
                parameter_id=POTENTIAL1_ENHANCED_BASIC_LAYERS,
                label="本次强化普攻消耗的熔炉升温层数",
                original_text=(
                    "当前强化普攻动作消耗0–2层熔炉升温；每层使第二段伤害提升10%。"
                    "层数不按触发历史或单位数量生成。"
                ),
                resolution=ParameterResolution.USER_SELECTED,
                value=0,
                minimum=0,
                maximum=2,
            )
        )
    if config.additional_ability_eligible:
        conditions.append(
            _condition(
                EXTRA_ABILITY_TARGET_MARK_ACTIVE,
                "珂蕾妲额外能力当前已对目标施加减益",
                core.extra_ability_description,
            )
        )

    rules: list[CalculationRuleItem] = []

    core_daze_note = _diagnostic(
        "core-daze-result",
        "The Core's source-described Daze increase is retained; this result contract does not emit Daze values.",
        core.description,
    )
    rules.append(
    _rule(
            "core:daze-source-only",
            core_source,
            "核心被动：强化特殊技/强化普攻失衡值提升（失衡结果未提供）",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(core_daze_note,),
        )
    )
    daze_source_text = "\n".join(
        f"{move.name}：{parameter.name}"
        for move in raw_record.moves
        for parameter in move.parameters
        if parameter.stun_ratio is not None or parameter.stun_ratio_growth is not None
    )
    daze_result_note = _diagnostic(
        "daze-parameter-results",
        "Raw Koleda skill parameters contain separate Daze ratios. They remain source-only because this calculator result does not emit Daze values.",
        daze_source_text or "Koleda skill Daze ratios",
    )

    extra_bonus = _number(
        core.extra_ability_description,
        r"连携技[^。]*?伤害提升(?P<value>[\d.]+)%",
        "Koleda Additional Ability Chain damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:chain-vulnerability",
            extra_source,
            f"额外能力：标记且失衡目标的连携技伤害易伤{extra_bonus * 100:g}%/层",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            condition_ids=(
                (EXTRA_ABILITY_TARGET_MARK_ACTIVE,)
                if config.additional_ability_eligible
                else ()
            ),
            effects=(
                _modifier(
                    "extra-ability:chain-vulnerability",
                    extra_source,
                    CalculationNode.ENEMY_NORMAL_VULNERABILITY,
                    Resolved(extra_bonus),
                    target=EffectTarget.ENEMY,
                    filters=(
                        DamageTagFilter(DamageTag.CHAIN_ATTACK),
                        DamageTypeFilter(DamageType.DIRECT),
                        EnemyStateFilter(_ENEMY_STUNNED),
                    ),
                ),
            ),
            stack_count=2,
            stack_min=0,
            stack_max=2,
        )
    )

    c1_note = _diagnostic(
        "cinema1-daze-result",
        "Cinema 1's source-described Daze increase depends on the attack-chain context, but the current result contract does not emit Daze values.",
        c1.description,
    )
    rules.append(
        _rule(
            "cinema1:daze-source-only",
            c1_source,
            "1影：特殊技失衡值提升（失衡结果未提供）",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            diagnostics=(c1_note,),
        )
    )
    c2_note = _diagnostic(
        "cinema2-energy-result",
        "Cinema 2's source-described Energy recovery is retained; the current result contract does not emit Energy values or replay its cooldown.",
        c2.description,
    )
    rules.append(
        _rule(
            "cinema2:energy-source-only",
            c2_source,
            "2影：能量回复（资源结果未提供）",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            diagnostics=(c2_note,),
        )
    )
    for level, cinema, source in ((3, c3, c3_source), (5, c5, c5_source)):
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级提升",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    if config.potential_level >= 1:
        potential_detail = _source_potential_level(raw_record, 1)
        potential_description = next(
            item.description
            for item in raw_record.moves
            if item.name == "普通攻击：砸扁，粉碎"
        )
        potential_source = _source(
            "potential-1-team-state",
            EffectSourceType.SPECIAL_MECHANISM,
            potential_detail.level_show_name,
            potential_description,
        )
        team_bonus = _number(
            potential_description,
            r"全队代理人造成的伤害提升(?P<value>[\d.]+)%",
            "Koleda Potential 1 team damage bonus",
        ) / 100.0
        rules.append(
            _rule(
                "potential1:team-damage-state",
                potential_source,
                f"潜能1：消耗熔炉升温后的全队伤害提升{team_bonus * 100:g}%",
                potential_description,
                RuleEligibility.ELIGIBLE,
                condition_ids=(POTENTIAL1_TEAM_DAMAGE_ACTIVE,),
                effects=(
                    _modifier(
                        "potential1:team-damage-state",
                        potential_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(team_bonus),
                        target=EffectTarget.TEAM,
                    ),
                ),
            )
        )
        layers_per_stack = _number(
            potential_description,
            r"每消耗一层.*?第二段强化\[普通攻击\]造成的伤害提升(?P<value>[\d.]+)%",
            "Koleda Potential 1 Enhanced Basic stage 2 per consumed stack",
        ) / 100.0
        stage2_template_filters = (
            EventTemplateIdFilter(_ENHANCED_BASIC_STAGE2_TEMPLATE),
        )
        if config.ben_in_team:
            stage2_template_filters = (
                *stage2_template_filters,
                EventTemplateIdFilter(
                    EventTemplateId(
                        "template:character:1101:enhanced-basic-stage2-ben-coordinated:main"
                    )
                ),
            )
        stage2_event_filter = (
            stage2_template_filters[0]
            if len(stage2_template_filters) == 1
            else AnyFilter(stage2_template_filters)
        )
        stage2_effect_template = _modifier(
            "potential1:enhanced-basic-stage2-per-consumed-layer",
            potential_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            ScenarioParameterDerivedValue(
                parameter_id=str(POTENTIAL1_ENHANCED_BASIC_LAYERS),
                coefficient=Resolved(layers_per_stack),
                base=Resolved(0.0),
                cap_max=Resolved(layers_per_stack * 2),
            ),
            target=EffectTarget.TEAM,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=(
                DamageDealerFilter(KOLEDA_ID),
                stage2_event_filter,
            ),
        )
        rules.append(
            _rule(
                "potential1:enhanced-basic-stage2-per-consumed-layer",
                potential_source,
                f"潜能1：本次消耗层数使强化普攻第二段每层伤害+{layers_per_stack * 100:g}%",
                potential_description,
                RuleEligibility.ELIGIBLE,
                effects=(stage2_effect_template,),
            )
        )

    if config.potential_level >= 2:
        potential_detail = _source_potential_level(raw_record, config.potential_level)
        potential_source = _source(
            f"potential-{config.potential_level}-team-crit-damage",
            EffectSourceType.SPECIAL_MECHANISM,
            potential_detail.name or potential_detail.level_show_name,
            potential_detail.description,
        )
        non_vanguard_crit_damage = _number(
            potential_detail.description,
            r"非\[锋御\]代理人暴击伤害提升(?P<value>[\d.]+)%",
            f"Koleda Potential {config.potential_level} non-Vanguard team Crit Damage",
        ) / 100.0
        vanguard_note = _diagnostic(
            f"potential{config.potential_level}-vanguard-rupture-output",
            "Koleda's source also names a [锋御] agent's 锐暴 damage branch. [锋御] role rules are not present in the current calculator, so that separate branch is preserved as source-only; the current registered non-[锋御] Crit Damage branch is applied.",
            potential_detail.description,
        )
        rules.append(
            _rule(
                f"potential{config.potential_level}:non-vanguard-team-crit-damage",
                potential_source,
                f"潜能{config.potential_level}：当前队伍非锋御角色暴击伤害+{non_vanguard_crit_damage * 100:g}%",
                potential_detail.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        f"potential{config.potential_level}:non-vanguard-team-crit-damage",
                        potential_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                        Resolved(non_vanguard_crit_damage),
                        target=EffectTarget.TEAM,
                    ),
                ),
                diagnostics=(vanguard_note,),
            )
        )

    if config.cinema_level >= 4:
        charge_bonus = _number(
            c4.description,
            r"每层充能使当前招式造成的伤害提升(?P<value>[\d.]+)%",
            "Koleda Cinema 4 damage bonus per Furnace charge",
        ) / 100.0
        parameters.append(
            ScenarioIntegerParameter(
                parameter_id=CINEMA4_CURRENT_FURNACE_LAYERS,
                label="当前熔炉升温充能层数（本次连携技/终结技）",
                original_text=(
                    f"{c4.description}。按本次计算选择当前充能0–2层，"
                    "不模拟获得或消耗时序。"
                ),
                resolution=ParameterResolution.USER_SELECTED,
                value=0,
                minimum=0,
                maximum=2,
            )
        )
        rules.append(
            _rule(
                "cinema4:chain-ultimate-current-furnace-damage",
                c4_source,
                f"4影：当前连携技/终结技每层充能伤害+{charge_bonus * 100:g}%",
                c4.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema4:chain-ultimate-current-furnace-damage",
                        c4_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        ScenarioParameterDerivedValue(
                            parameter_id=str(CINEMA4_CURRENT_FURNACE_LAYERS),
                            coefficient=Resolved(charge_bonus),
                            base=Resolved(0.0),
                            cap_max=Resolved(charge_bonus * 2),
                        ),
                        target=EffectTarget.TEAM,
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(
                            DamageDealerFilter(KOLEDA_ID),
                            DamageTypeFilter(DamageType.DIRECT),
                            AnyFilter(
                                (
                                    DamageTagFilter(DamageTag.CHAIN_ATTACK),
                                    DamageTagFilter(DamageTag.ULTIMATE),
                                )
                            ),
                        ),
                    ),
                ),
            )
        )
    else:
        rules.append(
            _rule(
                "cinema4:chain-ultimate-current-furnace-damage",
                c4_source,
                "4影：当前连携技/终结技每层充能伤害提升",
                c4.description,
                RuleEligibility.INELIGIBLE,
            )
        )

    c6_extra_multiplier = _number(
        c6.description,
        r"额外造成珂蕾妲(?P<value>[\d.]+)%攻击力的伤害",
        "Koleda Cinema 6 explosion extra damage ratio",
    ) / 100.0
    c6_rule_id = RuleItemId("rule:character:1101:cinema6:explosion-extra-damage")
    c6_child_specs = (
        (
            "ex-special",
            "6影：强化特殊技爆炸额外伤害",
            EX_SPECIAL_MOVE_ID,
            SkillGroup.SPECIAL_ATTACK,
            frozenset({DamageTag.EX_SPECIAL_ATTACK}),
            {
                "ex-special-explosion",
                "ex-special-ben-coordinated-explosion",
                "ex-special-complete",
            },
        ),
        (
            "chain",
            "6影：连携技爆炸额外伤害",
            CHAIN_ATTACK_MOVE_ID,
            SkillGroup.CHAIN_ATTACK,
            frozenset({DamageTag.CHAIN_ATTACK}),
            {"chain-attack"},
        ),
        (
            "ultimate",
            "6影：终结技爆炸额外伤害",
            ULTIMATE_MOVE_ID,
            SkillGroup.ULTIMATE,
            frozenset({DamageTag.ULTIMATE}),
            {"ultimate"},
        ),
    )
    c6_templates: list[DirectDamageEventTemplate] = []
    c6_derived: list[DerivedDamageEventTemplateRef] = []
    c6_effects: list[EventCreationEffect] = []
    if config.cinema_level >= 6:
        mapping_entry_keys = {
            spec.entry_key for spec in mapping.moves
        } | {"special-complete", "ex-special-complete"}
        for key, label, move_id, group, tags, candidate_parent_keys in c6_child_specs:
            parent_filters = tuple(
                EventTemplateIdFilter(
                    EventTemplateId(f"template:character:1101:{parent_key}:main")
                )
                for parent_key in sorted(candidate_parent_keys & mapping_entry_keys)
            )
            if not parent_filters:
                continue
            child_template_id = EventTemplateId(
                f"template:character:1101:cinema6:{key}-explosion-extra"
            )
            child_ref = DamageEventTemplateRef(
                template_id=child_template_id,
                semantic_id=DamageEventSemanticId(
                    f"event:character:1101:cinema6:{key}-explosion-extra"
                ),
                label=label,
                damage_type=DamageType.DIRECT,
                skill_group=group,
                damage_tags=tags,
                element=Element.FIRE,
                source_rule_item_id=c6_rule_id,
            )
            c6_templates.append(
                DirectDamageEventTemplate(
                    ref=child_ref,
                    damage_dealer=KOLEDA_ID,
                    element=Element.FIRE,
                    base_source=CurrentAttackValueSource(KOLEDA_ID),
                    crit_rule=StandardCritRule(KOLEDA_ID),
                    move_id=None,
                )
            )
            c6_derived.append(
                DerivedDamageEventTemplateRef(
                    template=child_ref,
                    multiplier=FixedMultiplier(Resolved(c6_extra_multiplier)),
                    repeat_count=1,
                )
            )
            c6_effects.append(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            f"effect:character:1101:cinema6:{key}-explosion-extra"
                        ),
                        source=c6_source,
                        owner=KOLEDA_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(
                            DamageDealerFilter(KOLEDA_ID),
                            DamageTypeFilter(DamageType.DIRECT),
                            AnyFilter(parent_filters),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=child_template_id,
                        unique_per_source_event=True,
                    ),
                )
            )
    rules.append(
        _rule(
            "cinema6:explosion-extra-damage",
            c6_source,
            f"6影：强化特殊技/连携技/终结技爆炸额外造成{c6_extra_multiplier * 100:g}%攻击力伤害",
            c6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            effects=tuple(c6_effects) if config.cinema_level >= 6 else (),
        )
    )

    core_damage_diagnostics = []
    potential_diagnostics = []
    if config.potential_level >= 1:
        p1 = _source_potential_level(raw_record, 1)
        if not p1.description.strip():
            potential_diagnostics.append(
                _diagnostic(
                    "potential1-ability-id-only",
                    "Potential I references ability-list ID 11101401 but its raw potential_detail description is empty; no extra unlisted effect is inferred.",
                    "potential_detail[110100]: name='', desc='', ability_list=[11101401]",
                )
            )
        potential_move = next(item for item in raw_record.moves if item.name == "普通攻击：砸扁，粉碎")
        if "追击效果增强" in potential_move.description:
            potential_diagnostics.append(
                _diagnostic(
                    "potential1-enhanced-basic-chase-value",
                    "Potential I says the Enhanced Basic stage-one chase effect is enhanced, but no separate numeric chase curve is present; the reviewed stage-one source ratio remains calculable without inventing another hit or multiplier.",
                    potential_move.description,
                )
            )
        if "失衡值提升20%" in potential_move.description:
            potential_diagnostics.append(
                _diagnostic(
                    "potential1-enhanced-basic-stage2-daze",
                    "Potential I also raises the second Enhanced Basic stage's Daze by 20% per consumed Furnace layer; the current calculator does not emit Daze results.",
                    potential_move.description,
                )
            )
    if not config.additional_ability_eligible:
        core_damage_diagnostics.append(
            _diagnostic(
                "extra-ability-team-qualification",
                "Koleda's Additional Ability requires another same-element or same-faction agent, a Rupture agent, or (from Potential I) a Vanguard agent in the actual team.",
                core.extra_ability_description,
            )
        )

    diagnostics = (
        *direct_diagnostics,
        *core_damage_diagnostics,
        *potential_diagnostics,
        daze_result_note,
    )
    return build_definition(
        character_id=KOLEDA_ID,
        role=CharacterRole.STUN,
        element=Element.FIRE,
        source=core_source,
        entries=(*entries, *static_entries),
        templates=(*direct_templates, *static_templates, *c6_templates),
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        independent_derived_damage_events=c6_derived,
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: KoledaCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "珂蕾妲" or raw.code_name != "Koleda":
        raise ValueError("unexpected identity in Koleda raw record")
    if raw.specialty != "击破" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("Koleda raw role, element, or rank changed from reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Koleda compile view must contain seven Core levels and six Cinemas")
    if config.potential_level > 0 and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError(f"Koleda raw source is missing Potential level {config.potential_level}")
    expected_core_source = "1101501" if config.potential_level == 0 else "1101508"
    if raw.core_levels[0].source_id != expected_core_source:
        raise ValueError("Koleda raw Potential view does not match the selected compile config")
    if raw.source_version != "3.2" or not raw.source_url.endswith("/character/1101.json"):
        raise ValueError("Koleda source provenance must identify live Nanoka 3.2 character 1101")


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(KOLEDA_ID, key, kind, label, text)


__all__ = ["compile_koleda", "load_raw_record"]
