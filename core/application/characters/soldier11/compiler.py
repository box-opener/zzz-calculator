"""Compile Soldier 11's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnomalyRecordId,
    AnyFilter,
    CalculationNode,
    CharacterRole,
    DamageSubtype,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DynamicIdentity,
    DynamicIdentityCondition,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EnemyStateFilter,
    EventTemplateId,
    FixedMultiplier,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
    SnapshotRule,
    StateId,
    StandardCritRule,
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
from ...scenario import ParameterResolution, ScenarioIntegerParameter
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
    DisorderDamageEventTemplate,
)
from .config import Soldier11CompileConfig
from .reviewed import (
    BASIC_SUPPRESSION_MOVE_ID,
    DASH_SUPPRESSION_MOVE_ID,
    SOLDIER11_ID,
    SOLDIER11_POTENTIAL_MOVES,
    SOLDIER11_REVIEWED_MAPPING,
)


POTENTIAL_FIRE_SUPPRESSION_USES = ScenarioParameterId(
    "parameter:soldier11:potential-current-fire-suppression-uses"
)
CINEMA6_CURRENT_CHARGES = ScenarioParameterId(
    "parameter:soldier11:cinema6-current-charges"
)
ENEMY_STUNNED = StateId("state:enemy:stunned")
FIRE_ANOMALY_RECORD = AnomalyRecordId("anomaly:soldier11:burn")
FIRE_ANOMALY_MOVE_ID = MoveId("move:soldier11:burn")
FIRE_DISORDER_MOVE_ID = MoveId("move:soldier11:burn-disorder")


def _base_potential(value: object) -> bool:
    return value is None or (
        isinstance(value, (list, tuple)) and (not value or 0 in value)
    )


def _potential_view(data: Mapping[str, object], potential_level: int) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("potential_level must be between 0 and 6")
    details = data.get("potential_detail")
    if not isinstance(details, Mapping):
        raise ValueError("Soldier 11 source has no potential_detail")
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
        if detail is None or not isinstance(detail.get("id"), int):
            raise ValueError(f"Soldier 11 source has no Potential level {potential_level}")
        selected_id = int(detail["id"])

    def selected(value: object) -> bool:
        if _base_potential(value):
            return True
        return (
            selected_id is not None
            and isinstance(value, (list, tuple))
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
                    if isinstance(item, dict) and selected(item.get("potential"))
                ]
    passive = view.get("passive")
    if isinstance(passive, dict) and isinstance(passive.get("level"), dict):
        passive["level"] = {
            key: item
            for key, item in passive["level"].items()
            if isinstance(item, dict) and selected(item.get("potential"))
        }
    return view


def load_raw_record(
    data: Mapping[str, object], *, potential_level: int = 0
) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_view(data, potential_level),
        expected_character_id=str(SOLDIER11_ID),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: Soldier11CompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "「11号」" or raw.code_name != "Soldier 11":
        raise ValueError("unexpected identity in Soldier 11 raw record")
    if raw.specialty != "强攻" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("Soldier 11 raw role, element, or rarity changed")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Soldier 11 source must include seven cores and six cinemas")
    if config.potential_level and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError("Soldier 11 raw source is missing selected Potential detail")


def _number(text: str, pattern: str, subject: str) -> float:
    plain = re.sub(r"<[^>]*>", "", text)
    match = re.search(pattern, plain)
    if match is None:
        raise ValueError(f"Soldier 11 source is missing {subject}")
    return float(match.group("value"))


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(SOLDIER11_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1041:{key}"),
        owner=SOLDIER11_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
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
    condition=None,
    filters=(),
    target: EffectTarget = EffectTarget.TEAM,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1041:{key}"),
            source=source,
            owner=SOLDIER11_ID,
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


def _diagnostic(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1041:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_fire_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1041:fire-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1041:fire-anomaly"),
        label="属性异常：灼烧（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=SOLDIER11_ID,
        element=Element.FIRE,
        anomaly_triggerer=SOLDIER11_ID,
        history_record_source=FIRE_ANOMALY_RECORD,
        crit_rule=NoCritRule(),
        move_id=FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1041:fire-anomaly"),
        character_id=SOLDIER11_ID,
        move_id=FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（10秒满异常）",
        original_text=(
            "按规范的火属性异常固定值：每0.5秒造成异常效果强度的50%，10秒共20跳；"
            "静态单人按100%积蓄，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1041:fire-anomaly-tick"),
                label="灼烧单跳50%（10秒20跳）",
                parameter_name="灼烧单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1041:fire-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1041:fire-disorder"),
        label="紊乱：灼烧（默认最大剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=SOLDIER11_ID,
        element=Element.FIRE,
        disorder_triggerer=SOLDIER11_ID,
        history_record_source=FIRE_ANOMALY_RECORD,
        crit_rule=NoCritRule(),
        move_id=FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1041:fire-disorder"),
        character_id=SOLDIER11_ID,
        move_id=FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧（默认最大剩余时间）",
        original_text=(
            "按规范默认450%紊乱基础倍率 + floor(t/0.5)×50%灼烧剩余时间补偿；"
            "t范围0–10秒，默认10秒，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1041:fire-disorder"),
                label="450% + floor(t/0.5) × 50%",
                parameter_name="灼烧紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ScenarioParameterId(
                    "parameter:soldier11:fire-disorder-remaining-seconds"
                ),
                parameter_base_value=4.5,
                # For integer-second selections, floor(t / 0.5) * 0.5 equals t.
                parameter_coefficient=1.0,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    disorder_remaining = ScenarioIntegerParameter(
        parameter_id=ScenarioParameterId("parameter:soldier11:fire-disorder-remaining-seconds"),
        label="灼烧紊乱时目标剩余持续时间（秒）",
        original_text="规范补偿为floor(t/0.5)×50%；按整数秒独立选择0–10秒，默认10秒，不推断触发时间。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        disorder_remaining,
    )


def _with_potential_charge_variant(
    entries: tuple[MoveCalculationEntry, ...],
    raw: NanokaRawRecord,
    config: Soldier11CompileConfig,
) -> tuple[MoveCalculationEntry, ...]:
    if config.potential_level == 0:
        return entries
    entry_id = "move-entry:character:1041:basic-fire-suppression-fifth-enhanced"
    move = next(item for item in raw.moves if item.name == "普通攻击：火力镇压")
    main = next(item for item in move.parameters if item.name == "强化普攻第五段伤害倍率")
    extra = next(item for item in move.parameters if item.name == "强化普攻第五段额外伤害倍率")
    skill_level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    base_value = main.value_for_level(skill_level, "1041025")
    extra_value = extra.value_for_level(skill_level, "1041026")
    if base_value is None or extra_value is None:
        raise ValueError("Soldier 11 enhanced fifth-stage source curves are incomplete")
    base_multiplier = float(base_value) / 100.0
    per_charge = float(extra_value) / 100.0
    result: list[MoveCalculationEntry] = []
    for entry in entries:
        if str(entry.entry_id) != entry_id:
            result.append(entry)
            continue
        variant = entry.multiplier_variants[0]
        result.append(
            replace(
                entry,
                multiplier_variants=(
                    replace(
                        variant,
                        label="强化第五段倍率 + 每次消耗充能的额外倍率",
                        parameter_value_id=POTENTIAL_FIRE_SUPPRESSION_USES,
                        parameter_base_value=base_multiplier,
                        parameter_coefficient=per_charge,
                    ),
                ),
            )
        )
    return tuple(result)


def compile_soldier11(
    config: Soldier11CompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    mapping = SOLDIER11_REVIEWED_MAPPING
    if config.potential_level > 0:
        mapping = replace(
            mapping,
            moves=(*mapping.moves, *SOLDIER11_POTENTIAL_MOVES),
        )
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=SOLDIER11_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1041",
    )
    direct_entries = _with_potential_charge_variant(direct_entries, raw_record, config)
    static_entries, static_templates, disorder_remaining = _static_fire_entries()
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description
    )
    core_bonus = _number(
        core.description,
        r"招式造成的伤害提升(?P<value>[\d.]+)%",
        "core damage bonus",
    ) / 100.0
    core_rule = _rule(
        "core:fire-suppression-damage",
        core_source,
        "核心被动：火力镇压伤害提升",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(
            _modifier(
                "core:fire-suppression-damage",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(core_bonus),
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(
                    AnyFilter(
                        (
                            MoveIdFilter(BASIC_SUPPRESSION_MOVE_ID),
                            MoveIdFilter(DASH_SUPPRESSION_MOVE_ID),
                        )
                    ),
                ),
            ),
        ),
    )

    extra_text = raw_record.extra_ability_description
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        extra_text,
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    fire_bonus = _number(
        extra_text, r"火属性伤害提升(?P<value>[\d.]+)%", "extra Fire bonus"
    ) / 100.0
    stunned_bonus = _number(
        extra_text, r"增益效果额外提升(?P<value>[\d.]+)%", "stunned target extra bonus"
    ) / 100.0
    extra_rules = [
        _rule(
            "extra-ability:fire-damage",
            extra_source,
            "额外能力：火属性伤害提升",
            extra_text,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:fire-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(fire_bonus),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(ElementFilter(Element.FIRE),),
                ),
            ),
        ),
        _rule(
            "extra-ability:stunned-target-fire-damage",
            extra_source,
            "额外能力：攻击失衡目标时额外提升火伤",
            extra_text,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:stunned-target-fire-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(stunned_bonus),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(ElementFilter(Element.FIRE), EnemyStateFilter(ENEMY_STUNNED)),
                ),
            ),
        ),
    ]

    mindscapes = {item.level: item for item in raw_record.mindscapes}
    rules: list[CalculationRuleItem] = [core_rule, *extra_rules]
    c2 = mindscapes[2]
    c2_source = _source("cinema-2", EffectSourceType.CINEMA, c2.name, c2.description)
    c2_eligible = config.cinema_level >= 2
    c2_effects = ()
    if c2_eligible:
        c2_stack_filters = (
            AnyFilter(
                (
                    DamageTagFilter(DamageTag.BASIC_ATTACK),
                    DamageTagFilter(DamageTag.DASH_ATTACK),
                    DamageTagFilter(DamageTag.DODGE_COUNTER),
                )
            ),
        )
        c2_effects = (
            _modifier(
                "cinema2:damage-per-stack",
                c2_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(0.03),
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=c2_stack_filters,
            ),
        )
    rules.append(
        _rule(
            "cinema2:current-stacks",
            c2_source,
            "2影：火力镇压增伤当前层数",
            c2.description,
            RuleEligibility.ELIGIBLE if c2_eligible else RuleEligibility.INELIGIBLE,
            effects=c2_effects,
            stack_count=12 if c2_eligible else None,
            stack_min=0 if c2_eligible else None,
            stack_max=12 if c2_eligible else None,
            diagnostics=(
                _diagnostic(
                    "cinema2-stack-duration",
                    "The selected 0–12 stacks are the current state. Individual 15-second expirations are not simulated.",
                    c2.description,
                ),
            ),
        )
    )

    c1 = mindscapes[1]
    rules.append(
        _rule(
            "cinema1:energy-restore-source-only",
            _source("cinema-1", EffectSourceType.CINEMA, c1.name, c1.description),
            "1影：入场能量回复（仅保留来源）",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            diagnostics=(
                _diagnostic(
                    "cinema1-energy-result-unavailable",
                    "The one-time combat-entry Energy restore and its eligibility are retained in raw; the calculation request has no Energy resource result.",
                    c1.description,
                ),
            ),
        )
    )
    c4 = mindscapes[4]
    rules.append(
        _rule(
            "cinema4:survival-effects-source-only",
            _source("cinema-4", EffectSourceType.CINEMA, c4.name, c4.description),
            "4影：减伤与无敌（无伤害输出）",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
        )
    )
    for level in (3, 5):
        mindscape = mindscapes[level]
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                _source(
                    f"cinema-{level}",
                    EffectSourceType.CINEMA,
                    mindscape.name,
                    mindscape.description,
                ),
                f"{level}影：技能等级提升",
                mindscape.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    parameters = [disorder_remaining]
    if config.potential_level > 0:
        parameters.append(
            ScenarioIntegerParameter(
                parameter_id=POTENTIAL_FIRE_SUPPRESSION_USES,
                label="潜能：当前必定触发火力镇压的次数（0–8）",
                original_text=(
                    "潜能原文称强化第五段可消耗当前所有必定触发火力镇压的次数，"
                    "潜能技能文本给出上限8；按当前剩余次数显式输入。"
                ),
                resolution=ParameterResolution.USER_SELECTED,
                value=0,
                minimum=0,
                maximum=8,
            )
        )
    if config.cinema_level >= 6:
        parameters.append(
            ScenarioIntegerParameter(
                parameter_id=CINEMA6_CURRENT_CHARGES,
                label="6影当前充能（0–8）",
                original_text=(
                    "6影原文称发动强化特殊技、连携技或终结技时获得8层充能；"
                    "按当前剩余充能显式输入，不模拟获得和消耗时序。"
                ),
                resolution=ParameterResolution.USER_SELECTED,
                value=0,
                minimum=0,
                maximum=8,
            )
        )

    c6 = mindscapes[6]
    c6_source = _source("cinema-6", EffectSourceType.CINEMA, c6.name, c6.description)
    c6_eligible = config.cinema_level >= 6
    if c6_eligible:
        rules.append(
            _rule(
                "cinema6:fire-resistance-ignore",
                c6_source,
                "6影：当前火力镇压招式无视火属性抗性",
                c6.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema6:fire-resistance-ignore",
                        c6_source,
                        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                        ScenarioParameterDerivedValue(
                            parameter_id=str(CINEMA6_CURRENT_CHARGES),
                            coefficient=Resolved(0.25),
                            base=Resolved(0.0),
                            cap_max=Resolved(0.25),
                        ),
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(
                            ElementFilter(Element.FIRE),
                            AnyFilter(
                                (
                                    MoveIdFilter(BASIC_SUPPRESSION_MOVE_ID),
                                    MoveIdFilter(DASH_SUPPRESSION_MOVE_ID),
                                )
                            ),
                        ),
                    ),
                ),
                diagnostics=(
                    _diagnostic(
                        "cinema6-charge-timing",
                        "The user selects the current 0–8 charges. EX/Chain/Ultimate charge generation and per-hit consumption are not replayed.",
                        c6.description,
                    ),
                ),
            )
        )
    else:
        rules.append(
            _rule(
                "cinema6:fire-resistance-ignore",
                c6_source,
                "6影：当前火力镇压招式无视火属性抗性",
                c6.description,
                RuleEligibility.INELIGIBLE,
            )
        )

    potential_rules: list[CalculationRuleItem] = []
    if config.potential_level >= 2:
        detail = next(
            item for item in raw_record.potential_details if item.level == config.potential_level
        )
        potential_value = _number(
            detail.description,
            r"暴击伤害提升(?P<value>[\d.]+)%",
            f"Potential {config.potential_level} Crit Damage",
        ) / 100.0
        eligibility = (
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE
        )
        potential_source = _source(
            f"potential-{config.potential_level}",
            EffectSourceType.SPECIAL_MECHANISM,
            detail.name or detail.level_show_name,
            detail.description,
        )
        potential_rules.append(
            _rule(
                "potential:additional-ability-crit-damage",
                potential_source,
                f"潜能{config.potential_level}：额外能力暴击伤害提升",
                detail.description,
                eligibility,
                effects=(
                    _modifier(
                        "potential:additional-ability-crit-damage",
                        potential_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                        Resolved(potential_value),
                        target=EffectTarget.SELF,
                    ),
                ),
            )
        )

    static_diagnostics = (
        _diagnostic(
            "daze-result-unavailable",
            "The source retains Daze curves for damage moves and three Parry Daze curves; this calculation request has no Daze result, so they are not added to damage.",
            "失衡倍率",
        ),
    )
    return build_definition(
        character_id=SOLDIER11_ID,
        role=CharacterRole.ATTACK,
        element=Element.FIRE,
        source=core_source,
        entries=(
            *direct_entries,
            *static_entries,
        ),
        templates=(
            *direct_templates,
            *static_templates,
        ),
        rules=(*rules, *potential_rules),
        conditions=(),
        parameters=parameters,
        diagnostics=(*direct_diagnostics, *static_diagnostics),
    )


__all__ = [
    "CINEMA6_CURRENT_CHARGES",
    "POTENTIAL_FIRE_SUPPRESSION_USES",
    "SOLDIER11_ID",
    "compile_soldier11",
    "load_raw_record",
]
