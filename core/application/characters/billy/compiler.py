"""Compile Billy's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

import re
from collections.abc import Mapping

from core.types import (
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
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
    FixedMultiplier,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import (
    DamageEventSemanticId,
    DiagnosticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
)
from ...moves import DamageEventTemplateRef, MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ParameterResolution, ScenarioCondition, ScenarioIntegerParameter
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import build_definition, compile_direct_moves, effective_skill_level, source_for
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import AttributeAnomalyDamageEventTemplate, DirectDamageEventTemplate, DisorderDamageEventTemplate
from .config import BillyCompileConfig
from .reviewed import (
    ASSIST_STRIKE_MOVE_ID,
    BILLY_ID,
    BILLY_PHYSICAL_ANOMALY_RECORD_ID,
    BILLY_REVIEWED_MAPPING,
    CINEMA4_EX_CRIT_RATE_BONUS,
    CROUCH_SHOOTING_DAMAGE_ACTIVE,
    DODGE_COUNTER_MOVE_ID,
    EX_SPECIAL_MOVE_ID,
    PHYSICAL_ANOMALY_MOVE_ID,
    PHYSICAL_DISORDER_MOVE_ID,
    PHYSICAL_DISORDER_REMAINING_SECONDS,
    ULTIMATE_AFTER_CHAIN_ACTIVE,
    ULTIMATE_MOVE_ID,
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


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(BILLY_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1081:{key}"),
        owner=BILLY_ID,
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


def _effect_rule(key: str, source: RuleSource, target: EffectTarget, *, condition=None, filters=()):
    return EffectRule(
        effect_id=EffectId(f"effect:character:1081:{key}"),
        source=source,
        owner=BILLY_ID,
        target=target,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        condition=condition,
        filters=tuple(filters),
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
        rule=_effect_rule(key, source, target, condition=condition, filters=filters),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _note(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1081:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_physical_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1081:physical-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1081:physical-anomaly"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=BILLY_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=BILLY_ID,
        history_record_source=BILLY_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1081:physical-anomaly"),
        character_id=BILLY_ID,
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text="按静态单人100%积蓄的物理异常记录结算强击，倍率7.13，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1081:physical-anomaly"),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1081:physical-disorder",
        semantic_id=DamageEventSemanticId("event:character:1081:physical-disorder"),
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=BILLY_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=BILLY_ID,
        history_record_source=BILLY_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1081:physical-disorder"),
        character_id=BILLY_ID,
        move_id=PHYSICAL_DISORDER_MOVE_ID,
        display_name="紊乱：物理异常（剩余时间补偿）",
        original_text="物理紊乱基础倍率450%，每秒剩余时间补偿75%，按floor(t)计算。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1081:physical-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="物理异常紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining_seconds = ScenarioIntegerParameter(
        parameter_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
        label="物理异常剩余持续时间（秒）",
        original_text="静态物理异常按10秒；本次紊乱剩余时间由用户输入，不从战斗时序推断。",
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


def compile_billy(
    config: BillyCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=BILLY_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=BILLY_REVIEWED_MAPPING,
        id_namespace="character:1081",
    )
    static_entries, static_templates, disorder_seconds = _static_physical_entries()
    scenario_parameters = [disorder_seconds]
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source("extra-ability", EffectSourceType.ADDITIONAL_ABILITY, core.extra_ability_name, core.extra_ability_description)
    crouch_bonus = _number(
        core.description,
        r"自身造成的伤害提升(?P<value>[\d.]+)%",
        "Billy Core crouch-shooting damage bonus",
    ) / 100.0
    ult_damage_bonus = _number(
        core.extra_ability_description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Billy Additional Ability Ultimate damage bonus per stack",
    ) / 100.0
    cinema2 = raw_record.mindscapes[1]
    c2_source = _source("cinema-2", EffectSourceType.CINEMA, cinema2.name, cinema2.description)
    counter_bonus = _number(
        cinema2.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Billy Cinema 2 Dodge Counter damage bonus",
    ) / 100.0

    conditions = [
        _condition(
            CROUCH_SHOOTING_DAMAGE_ACTIVE,
            "比利当前处于蹲姿射击伤害增益状态",
            core.description,
        ),
        _condition(
            ULTIMATE_AFTER_CHAIN_ACTIVE,
            "比利当前持有连携技后的终结技增伤",
            core.extra_ability_description,
        ),
    ]
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:crouch-shooting-damage",
            core_source,
            f"核心被动：蹲姿射击伤害+{crouch_bonus * 100:g}%",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(CROUCH_SHOOTING_DAMAGE_ACTIVE,),
            effects=(
                _modifier(
                    "core:crouch-shooting-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(crouch_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(DamageDealerFilter(BILLY_ID),),
                ),
            ),
        ),
        _rule(
            "extra-ability:ultimate-after-chain",
            extra_source,
            f"额外能力：连携技后终结技伤害+{ult_damage_bonus * 100:g}%/层",
            core.extra_ability_description,
            (
                RuleEligibility.ELIGIBLE
                if config.additional_ability_eligible
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(ULTIMATE_AFTER_CHAIN_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:ultimate-after-chain",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(ult_damage_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(DamageDealerFilter(BILLY_ID), MoveIdFilter(ULTIMATE_MOVE_ID)),
                ),
            ),
            stack_count=2,
            stack_min=0,
            stack_max=2,
        ),
        _rule(
            "cinema2:dodge-counter-damage",
            c2_source,
            f"2影：闪避反击伤害+{counter_bonus * 100:g}%",
            cinema2.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 2
                else RuleEligibility.INELIGIBLE
            ),
            effects=(
                _modifier(
                    "cinema2:dodge-counter-damage",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(counter_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(DamageDealerFilter(BILLY_ID), MoveIdFilter(DODGE_COUNTER_MOVE_ID)),
                ),
            ),
        ),
    ]

    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(f"cinema-{level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级提升",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    if config.cinema_level >= 4:
        cinema4 = raw_record.mindscapes[3]
        source = _source("cinema-4", EffectSourceType.CINEMA, cinema4.name, cinema4.description)
        original_text = cinema4.description
        c4_effect = _modifier(
            "cinema4:ex-crit-rate",
            source,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            ScenarioParameterDerivedValue(
                parameter_id=str(CINEMA4_EX_CRIT_RATE_BONUS),
                coefficient=Resolved(0.01),
                base=Resolved(0.0),
                cap_max=Resolved(0.32),
            ),
            target=EffectTarget.TEAM,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=(
                DamageDealerFilter(BILLY_ID),
                MoveIdFilter(EX_SPECIAL_MOVE_ID),
                DamageTypeFilter(DamageType.DIRECT),
            ),
        )
        rules.append(
            _rule(
                "cinema4:ex-crit-rate",
                source,
                "4影：本次强化特殊技暴击率增益",
                original_text,
                RuleEligibility.ELIGIBLE,
                effects=(c4_effect,),
            )
        )
        scenario_parameters.append(
            ScenarioIntegerParameter(
                parameter_id=CINEMA4_EX_CRIT_RATE_BONUS,
                label="本次强化特殊技暴击率增益（贴身最大场景）",
                original_text=(
                    f"{original_text}。当前计算由用户选择本次强化特殊技暴击率增益，默认取源上限32%；"
                    "不根据距离推导，允许调整为0–32%。"
                ),
                resolution=ParameterResolution.USER_SELECTED,
                value=32,
                minimum=0,
                maximum=32,
            ),
        )

    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        source = _source("cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description)
        damage_per_stack = _number(
            cinema6.description,
            r"造成的伤害提升(?P<value>[\d.]+)%",
            "Billy Cinema 6 damage bonus per stack",
        ) / 100.0
        rules.append(
            _rule(
                "cinema6:current-damage-stacks",
                source,
                f"6影：当前伤害增益层数（每层{damage_per_stack * 100:g}%）",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema6:current-damage-stacks",
                        source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(damage_per_stack),
                        target=EffectTarget.TEAM,
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(DamageDealerFilter(BILLY_ID),),
                    ),
                ),
                stack_count=5,
                stack_min=0,
                stack_max=5,
            )
        )

    c1 = raw_record.mindscapes[0]
    c1_source = _source("cinema-1", EffectSourceType.CINEMA, c1.name, c1.description)
    c1_energy_note = _note(
        "cinema1:energy-resource",
        "Cinema 1's Energy restoration is retained as source-only because the current calculation result does not expose the Energy resource.",
        c1.description,
    )
    rules.append(
        _rule(
            "cinema1:energy-source-only",
            c1_source,
            "1影：能量回复（资源结果未提供）",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            diagnostics=(c1_energy_note,),
        )
    )

    attack_diagnostics = (
        _note(
            "crouch-shooting-timing",
            "The current Crouch Shooting damage state is user-selected. Shot cadence, duration, and transition history are not replayed.",
            raw_record.core_levels[config.core_level - 1].description,
        ),
        _note(
            "daze-and-resource-results",
            "Source Daze, Energy, and Energy/resource effects remain nonblocking source notes because the current output contract has no Daze or Energy result.",
            "支援技、连携、终结技、Cinema 1的失衡/能量倍率与能量恢复文本",
        ),
    )
    direct_entries = list(direct_entries)
    direct_templates = list(direct_templates)
    return build_definition(
        character_id=BILLY_ID,
        role=CharacterRole.ATTACK,
        element=Element.PHYSICAL,
        source=core_source,
        entries=(*direct_entries, *static_entries),
        templates=(*direct_templates, *static_templates),
        rules=rules,
        conditions=conditions,
        parameters=tuple(scenario_parameters),
        diagnostics=(*direct_diagnostics, *attack_diagnostics),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: BillyCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "比利" or raw.code_name != "Billy":
        raise ValueError("unexpected character identity in Billy source")
    if raw.specialty != "强攻" or raw.element != "物理" or raw.rarity != 3:
        raise ValueError("Billy role, element, or rank changed from reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Billy source must include seven cores and six cinemas")
    if raw.potential_details:
        raise ValueError("Billy source unexpectedly contains Potential variants")
    if raw.source_version != "3.2" or not raw.source_url.endswith("/character/1081.json"):
        raise ValueError("Billy raw source provenance must identify Nanoka 3.2 character 1081")


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(BILLY_ID))


__all__ = ["compile_billy", "load_raw_record"]
