"""Compile Piper's reviewed Nanoka 3.2 source into calculation contracts."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
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
    ElementFilter,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    RuleStackCondition,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
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
from ...moves import DamageEventTemplateRef, MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ParameterResolution, ScenarioCondition, ScenarioIntegerParameter
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    raw_move_index,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import PiperCompileConfig
from .reviewed import (
    PIPER_C2_ANOMALY_RECORD_BONUS_ACTIVE,
    PIPER_ID,
    PIPER_PHYSICAL_ANOMALY_MOVE_ID,
    PIPER_PHYSICAL_ANOMALY_RECORD_ID,
    PIPER_PHYSICAL_DISORDER_MOVE_ID,
    PIPER_POWER_STACKS_RULE_ID,
    PIPER_REVIEWED_MAPPING,
)


_PHYSICAL_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:piper:physical-disorder-remaining-seconds"
)
_PHYSICAL_ANOMALY_TEMPLATE_ID = EventTemplateId(
    "template:character:1281:physical-assault"
)
_PHYSICAL_DISORDER_TEMPLATE_ID = EventTemplateId(
    "template:character:1281:physical-disorder"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(PIPER_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1281:{key}"),
        owner=PIPER_ID,
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
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1281:{key}"),
            source=source,
            owner=PIPER_ID,
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


def _static_physical_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=_PHYSICAL_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1281:physical-assault"),
        label="属性异常：强击（单次）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=PIPER_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=PIPER_ID,
        history_record_source=AnomalyRecordId(PIPER_PHYSICAL_ANOMALY_RECORD_ID),
        crit_rule=NoCritRule(),
        move_id=PIPER_PHYSICAL_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1281:physical-assault"),
        character_id=PIPER_ID,
        move_id=PIPER_PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（7.13倍，单次）",
        original_text="按静态单人100%物理异常记录结算，强击倍率713%，无异常暴击。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1281:physical-assault"),
                label="强击倍率713%",
                parameter_name="强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=_PHYSICAL_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1281:physical-disorder"),
        label="紊乱：物理强击（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=PIPER_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=PIPER_ID,
        history_record_source=AnomalyRecordId(PIPER_PHYSICAL_ANOMALY_RECORD_ID),
        crit_rule=NoCritRule(),
        move_id=PIPER_PHYSICAL_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1281:physical-disorder"),
        character_id=PIPER_ID,
        move_id=PIPER_PHYSICAL_DISORDER_MOVE_ID,
        display_name="紊乱：物理强击（当前剩余时间）",
        original_text="物理紊乱倍率为450% + floor(t)×7.5%；使用当前剩余时间，不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1281:physical-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="物理紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_PHYSICAL_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_PHYSICAL_DISORDER_REMAINING_SECONDS,
        label="物理异常剩余持续时间（秒）",
        original_text="按静态物理异常记录为10秒；本次紊乱剩余时间由用户输入，不从战斗时序推断。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _cinema2_slam_template_ids() -> tuple[EventTemplateId, ...]:
    return (
        EventTemplateId("template:character:1281:special-very-heavy-charge-1:main"),
        EventTemplateId("template:character:1281:special-very-heavy-charge-2:main"),
        EventTemplateId("template:character:1281:special-very-heavy-charge-3:main"),
        EventTemplateId("template:character:1281:ex-very-heavy:main"),
        EventTemplateId("template:character:1281:ultimate-sit-tight:main"),
    )


def compile_piper(
    config: PiperCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=PIPER_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=PIPER_REVIEWED_MAPPING,
    )
    entries = list(entries)
    templates = list(templates)
    diagnostics = list(direct_diagnostics)
    raw_moves = raw_move_index(raw_record)
    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []

    core = raw_record.core_levels[config.core_level - 1]
    power_stack_cap = 30 if config.cinema_level >= 1 else 20
    power_stack_source = _source(
        "core:current-power-stacks",
        EffectSourceType.CORE_PASSIVE,
        "核心被动：动力",
        core.description,
    )
    power_stack_rule = _rule(
        "core:current-power-stacks",
        power_stack_source,
        f"当前动力层数（0–{power_stack_cap}）",
        core.description,
        RuleEligibility.ELIGIBLE,
        stack_count=power_stack_cap,
        stack_min=0,
        stack_max=power_stack_cap,
        diagnostics=(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId("unsupported:character:1281:core:power-duration-and-generation"),
                kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                message="Power is a user-selected current 0–20/30 stack value. The calculator does not replay spin hits, the 12-second duration, or Cinema 1's 50% extra-stack chance.",
                blocking=False,
                original_text=core.description,
            ),
        ),
    )
    rules.append(power_stack_rule)

    additional = core.extra_ability_description
    team_bonus = _number(
        additional,
        r"全队角色造成的伤害提升(?P<value>[\d.]+)%",
        "Piper Additional Ability team damage bonus",
    ) / 100.0
    additional_source = _source(
        "extra-ability:twenty-power-team-damage",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        additional,
    )
    team_bonus_effects = tuple(
        _modifier(
            f"extra-ability:twenty-power-team-damage-at-{stacks}",
            additional_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(team_bonus),
            target=EffectTarget.TEAM,
            condition=RuleStackCondition(
                str(PIPER_POWER_STACKS_RULE_ID),
                stacks,
                requires_rule_enabled=False,
            ),
        )
        for stacks in range(20, power_stack_cap + 1)
    )
    rules.append(
        _rule(
            "extra-ability:twenty-power-team-damage",
            additional_source,
            f"额外能力：20层动力时全队伤害+{team_bonus:.0%}",
            additional,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            effects=team_bonus_effects,
        )
    )

    cinema2 = raw_record.mindscapes[1]
    cinema2_base_bonus = _number(
        cinema2.description,
        r"物理伤害提升(?P<value>[\d.]+)%",
        "Piper Cinema 2 base slam damage bonus",
    ) / 100.0
    cinema2_stack_bonus = _number(
        cinema2.description,
        r"每拥有1层.*?额外提升(?P<value>[\d.]+)%",
        "Piper Cinema 2 damage bonus per Power stack",
    ) / 100.0
    slam_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(PIPER_ID),
        AnyFilter(tuple(EventTemplateIdFilter(item) for item in _cinema2_slam_template_ids())),
    )
    cinema2_source = _source(
        "cinema2:power-stack-slam-damage",
        EffectSourceType.CINEMA,
        cinema2.name,
        cinema2.description,
    )
    c2_eligible = config.cinema_level >= 2
    c2_effects = tuple(
        _modifier(
            f"cinema2:slam-power-stack-{stack}",
            cinema2_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(cinema2_base_bonus + cinema2_stack_bonus * stack),
            target=EffectTarget.SELF,
            filters=slam_filters,
            condition=RuleStackCondition(
                str(PIPER_POWER_STACKS_RULE_ID),
                stack,
                requires_rule_enabled=False,
            ),
        )
        for stack in range(0, power_stack_cap + 1)
    )
    rules.append(
        _rule(
            "cinema2:power-stack-slam-damage",
            cinema2_source,
            "2影：下砸攻击伤害+基础值及每层动力增益",
            cinema2.description,
            RuleEligibility.ELIGIBLE if c2_eligible else RuleEligibility.INELIGIBLE,
            effects=c2_effects if c2_eligible else (),
        )
    )

    if c2_eligible:
        conditions.append(
            ScenarioCondition(
                condition_id=PIPER_C2_ANOMALY_RECORD_BONUS_ACTIVE,
                label="派派2影异常记录增伤（开100%／关0%）",
                original_text=cinema2.description,
                resolution=ConditionResolution.USER_SELECTED,
                value=True,
            )
        )
    c2_record_filters = (
        DamageTypeFilter(DamageType.ANOMALY),
        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
        ElementFilter(Element.PHYSICAL),
        DamageDealerFilter(PIPER_ID),
        EventTemplateIdFilter(_PHYSICAL_ANOMALY_TEMPLATE_ID),
    )
    c2_disorder_record_filters = (
        DamageTypeFilter(DamageType.DISORDER),
        ElementFilter(Element.PHYSICAL),
        DamageDealerFilter(PIPER_ID),
        EventTemplateIdFilter(_PHYSICAL_DISORDER_TEMPLATE_ID),
    )
    c2_record_effects = tuple(
        _modifier(
            f"cinema2:physical-record-normal-bonus-at-{stacks}",
            cinema2_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(cinema2_base_bonus + cinema2_stack_bonus * stacks),
            target=EffectTarget.TEAM,
            filters=c2_record_filters,
            condition=RuleStackCondition(
                str(PIPER_POWER_STACKS_RULE_ID),
                stacks,
                requires_rule_enabled=False,
            ),
        )
        for stacks in range(0, power_stack_cap + 1)
    ) + tuple(
        _modifier(
            f"cinema2:physical-disorder-record-normal-bonus-at-{stacks}",
            cinema2_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(cinema2_base_bonus + cinema2_stack_bonus * stacks),
            target=EffectTarget.TEAM,
            filters=c2_disorder_record_filters,
            condition=RuleStackCondition(
                str(PIPER_POWER_STACKS_RULE_ID),
                stacks,
                requires_rule_enabled=False,
            ),
        )
        for stacks in range(0, power_stack_cap + 1)
    )
    rules.append(
        _rule(
            "cinema2:physical-record-normal-bonus",
            cinema2_source,
            "2影：物理强击与紊乱源记录的当前普通增伤（0%/100%）",
            cinema2.description,
            RuleEligibility.ELIGIBLE if c2_eligible else RuleEligibility.INELIGIBLE,
            effects=c2_record_effects if c2_eligible else (),
            condition_ids=(PIPER_C2_ANOMALY_RECORD_BONUS_ACTIVE,) if c2_eligible else (),
        )
    )

    for level in (1, 4, 6):
        cinema = raw_record.mindscapes[level - 1]
        message = {
            1: "Cinema 1 raises the Power stack cap and grants an extra stack with a 50% chance. The current stack count is selectable; chance and history are not simulated.",
            4: "Cinema 4 restores Energy after an anomaly application. Energy and its 30-second trigger limit are not simulated.",
            6: "Cinema 6 extends the duration of EX Special and Power. Duration and time are not simulated.",
        }[level]
        rules.append(
            _rule(
                f"cinema{level}:source-only",
                _source(f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description),
                f"{level}影：来源效果不在伤害结果中模拟",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(f"unsupported:character:1281:cinema{level}:source-only"),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message=message,
                        blocking=False,
                        original_text=cinema.description,
                    ),
                ),
            )
        )
    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                _source(f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description),
                f"{level}影：技能等级+2",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    anomaly_entries, anomaly_templates, disorder_parameter = _static_physical_entries(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)

    parry = next(item for item in raw_record.moves if item.name == "招架支援：极限刹车")
    rules.append(
        _rule(
            "parry-assist:daze-source-only",
            _source("parry-assist:daze-source-only", EffectSourceType.SKILL, parry.name, parry.description),
            "招架支援：极限刹车（仅失衡倍率）",
            parry.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId("unsupported:character:1281:parry-assist:daze-only"),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message="This Parry Assist source lists Daze values but no damage ratio; no damage event is created.",
                    blocking=False,
                    original_text=parry.description,
                ),
            ),
        )
    )

    return build_definition(
        character_id=PIPER_ID,
        role=CharacterRole.ANOMALY,
        element=Element.PHYSICAL,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=tuple(conditions),
        parameters=(disorder_parameter,),
        diagnostics=tuple(direct_diagnostics),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(PIPER_ID))


def _validate_raw(raw: NanokaRawRecord, config: PiperCompileConfig) -> None:
    if raw.character_id != PIPER_ID or raw.name != "派派" or raw.code_name != "Piper":
        raise ValueError("unexpected Piper raw identity")
    if raw.specialty != "异常" or raw.element != "物理" or raw.rarity != 3:
        raise ValueError("unexpected Piper role, element, or rank")
    if raw.faction != "卡吕冬之子" or raw.icon != "IconRole28":
        raise ValueError("unexpected Piper faction or icon")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1281.json":
        raise ValueError("Piper provenance must identify live Nanoka 3.2 character 1281")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Piper source must contain seven Core levels and six Cinemas")
    if raw.potential_details:
        raise ValueError("Piper source has no Potential levels")
    if config.character_id != raw.character_id:
        raise ValueError("Piper config and raw IDs must match")


__all__ = ["compile_piper", "load_raw_record"]
