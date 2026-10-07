"""Compile Anton's reviewed Nanoka 3.2 source into calculation contracts."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
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
from ..nanoka_compiler import build_definition, compile_direct_moves, source_for
from ..nanoka_source import NanokaRawRecord
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import AntonCompileConfig
from .reviewed import (
    ANTON_ELECTRIC_ANOMALY_MOVE_ID,
    ANTON_ELECTRIC_ANOMALY_RECORD_ID,
    ANTON_ELECTRIC_DISORDER_MOVE_ID,
    ANTON_ID,
    ANTON_REVIEWED_MAPPING,
    BURST_STATE_ACTIVE,
    CINEMA4_TEAM_CRIT_ACTIVE,
    ELECTRIC_DISORDER_REMAINING_SECONDS,
    ENEMY_SHOCKED_ACTIVE,
    EXTRA_SHOCK_READY,
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(ANTON_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1111:{key}"),
        owner=ANTON_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=tuple(diagnostics),
    )


def _modifier(key: str, source: RuleSource, node: CalculationNode, value, *, filters=(), condition=None) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1111:{key}"),
            source=source,
            owner=ANTON_ID,
            target=EffectTarget.TEAM,
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


def _static_electric_entries():
    shock_ref = DamageEventTemplateRef(
        template_id="template:character:1111:electric-shock",
        semantic_id=DamageEventSemanticId("event:character:1111:electric-shock"),
        label="属性异常：感电（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ELECTRIC,
    )
    shock_template = AttributeAnomalyDamageEventTemplate(
        ref=shock_ref,
        damage_dealer=ANTON_ID,
        element=Element.ELECTRIC,
        anomaly_triggerer=ANTON_ID,
        history_record_source=ANTON_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ANTON_ELECTRIC_ANOMALY_MOVE_ID,
    )
    shock_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1111:electric-shock"),
        character_id=ANTON_ID,
        move_id=ANTON_ELECTRIC_ANOMALY_MOVE_ID,
        display_name="属性异常：感电（10秒满异常）",
        original_text=(
            "静态单人100%积蓄记录按规范结算感电：每秒125%异常效果强度，"
            "持续10秒，共10跳；使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1111:electric-shock-tick"),
                label="感电单跳125%（10秒10跳）",
                parameter_name="感电单跳倍率",
                multiplier=FixedMultiplier(Resolved(1.25)),
                repeat_count=10,
            ),
        ),
        main_damage_event=shock_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1111:electric-disorder",
        semantic_id=DamageEventSemanticId("event:character:1111:electric-disorder"),
        label="紊乱：感电（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ELECTRIC,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ANTON_ID,
        element=Element.ELECTRIC,
        disorder_triggerer=ANTON_ID,
        history_record_source=ANTON_ELECTRIC_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ANTON_ELECTRIC_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1111:electric-disorder"),
        character_id=ANTON_ID,
        move_id=ANTON_ELECTRIC_DISORDER_MOVE_ID,
        display_name="紊乱：感电（剩余时间补偿）",
        original_text=(
            "感电紊乱倍率按规范为450% + floor(t)×125%；"
            "剩余时间是当前输入，不推算战斗时间。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1111:electric-disorder"),
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
    remaining_seconds = ScenarioIntegerParameter(
        parameter_id=ELECTRIC_DISORDER_REMAINING_SECONDS,
        label="感电紊乱时目标剩余持续时间（秒）",
        original_text="使用当前输入的剩余持续时间，范围0–10秒；不模拟时间流逝。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (shock_entry, disorder_entry),
        (shock_template, disorder_template),
        remaining_seconds,
    )


def _event_filter(key: str) -> EventTemplateIdFilter:
    return EventTemplateIdFilter(EventTemplateId(f"template:character:1111:{key}:main"))


def compile_anton(
    config: AntonCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=ANTON_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=ANTON_REVIEWED_MAPPING,
        id_namespace="character:1111",
    )
    static_entries, static_templates, disorder_seconds = _static_electric_entries()
    entries = [*direct_entries, *static_entries]
    templates = [*direct_templates, *static_templates]
    conditions = [
        _condition(BURST_STATE_ACTIVE, "安东当前处于爆发状态", "爆发状态下使用独立招式倍率。"),
    ]
    rules: list[CalculationRuleItem] = []
    parameters = [disorder_seconds]
    diagnostics = list(direct_diagnostics)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    pile_bonus = _number(
        core.description,
        r"打桩攻击.*?伤害提升(?P<value>[\d.]+)%",
        "Anton Core Pile Driver damage bonus",
    ) / 100.0
    drill_bonus = _number(
        core.description,
        r"电钻攻击.*?伤害提升(?P<value>[\d.]+)%",
        "Anton Core Drill damage bonus",
    ) / 100.0
    pile_keys = (
        "basic-normal-4",
        "basic-burst-3",
        "special-pile-driver",
        "ex-special-pile-driver",
        "burst-special-pile-driver",
        "chain-pile-driver",
        "ultimate-pile-driver",
    )
    drill_keys = (
        "basic-burst-2",
        "burst-dodge-counter",
        "burst-quick-assist-drill",
    )
    mixed_assist_text = next(
        move.description
        for move in raw_record.moves
        if move.name == "支援突击：极限突进"
    )
    mixed_assist_unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes=(
            "The Support Strike has one total multiplier for a Drill hit followed by a Pile Driver finisher. "
            "The raw source provides no per-component ratios, so the two Core bonuses cannot be allocated "
            "to this selected aggregate event."
        ),
        original_text=mixed_assist_text,
    )
    rules.append(
        _rule(
            "core:pile-driver-and-drill-damage",
            core_source,
            f"核心被动：打桩攻击+{pile_bonus * 100:g}%／电钻攻击+{drill_bonus * 100:g}%",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:pile-driver-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(pile_bonus),
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(ANTON_ID),
                        AnyFilter(tuple(_event_filter(key) for key in pile_keys)),
                    ),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                ),
                _modifier(
                    "core:drill-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(drill_bonus),
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(ANTON_ID),
                        AnyFilter(tuple(_event_filter(key) for key in drill_keys)),
                    ),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                ),
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1111:core:mixed-assist-strike-mode-allocation"
                        ),
                        source=core_source,
                        owner=ANTON_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            DamageDealerFilter(ANTON_ID),
                            _event_filter("assist-strike-drill-pile"),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        unresolved_template=mixed_assist_unresolved,
                    ),
                ),
            ),
        )
    )

    extra = core.extra_ability_description
    extra_source = _source("extra-ability", EffectSourceType.ADDITIONAL_ABILITY, core.extra_ability_name, extra)
    extra_diagnostic = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            "The source fixes this extra Shock to 45% of one standard Electric Shock tick "
            "(0.5625 of its selected Electric anomaly record). Its source-record attribution and "
            "following settlement ownership are unresolved; only this triggered child event is blocked."
        ),
        original_text=extra,
    )
    conditions.extend(
        (
            _condition(EXTRA_SHOCK_READY, "额外感电当前已就绪（此前4次暴击）", extra),
            _condition(ENEMY_SHOCKED_ACTIVE, "当前目标处于感电状态", extra),
        )
    )
    rules.append(
        _rule(
            "extra-ability:shock-extra-hit",
            extra_source,
            "额外能力：下一次攻击额外结算一次感电（45%）",
            extra,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            conditions=(BURST_STATE_ACTIVE, EXTRA_SHOCK_READY, ENEMY_SHOCKED_ACTIVE),
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId("effect:character:1111:extra-ability:shock-extra-hit"),
                        source=extra_source,
                        owner=ANTON_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            DamageDealerFilter(ANTON_ID),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        unresolved_template=extra_diagnostic,
                        unique_per_source_event=True,
                    ),
                ),
            ),
        )
    )

    cinema4 = raw_record.mindscapes[3]
    c4_source = _source("cinema-4", EffectSourceType.CINEMA, cinema4.name, cinema4.description)
    if config.cinema_level >= 4:
        c4_value = _number(
            cinema4.description,
            r"暴击率提升(?P<value>[\d.]+)%",
            "Anton Cinema 4 team Crit Rate bonus",
        ) / 100.0
        conditions.append(
            _condition(
                CINEMA4_TEAM_CRIT_ACTIVE,
                "安东4影连携技或终结技后的全队暴击率增益当前有效",
                cinema4.description,
            )
        )
        rules.append(
            _rule(
                "cinema4:team-crit-rate",
                c4_source,
                f"4影：全队暴击率+{c4_value * 100:g}%（当前状态）",
                cinema4.description,
                RuleEligibility.ELIGIBLE,
                conditions=(CINEMA4_TEAM_CRIT_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema4:team-crit-rate",
                        c4_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                        Resolved(c4_value),
                    ),
                ),
            )
        )
    else:
        rules.append(
            _rule(
                "cinema4:team-crit-rate",
                c4_source,
                "4影：全队暴击率提升",
                cinema4.description,
                RuleEligibility.INELIGIBLE,
            )
        )

    cinema6 = raw_record.mindscapes[5]
    c6_source = _source("cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description)
    if config.cinema_level >= 6:
        c6_value = _number(
            cinema6.description,
            r"伤害提升(?P<value>[\d.]+)%",
            "Anton Cinema 6 burst damage per stack",
        ) / 100.0
        c6_keys = (
            "basic-burst-1",
            "basic-burst-2",
            "basic-burst-3",
            "burst-dodge-counter",
        )
        rules.append(
            _rule(
                "cinema6:burst-basic-and-counter-damage-stacks",
                c6_source,
                f"6影：爆发状态普攻／闪避反击伤害+{c6_value * 100:g}%/层",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema6:burst-basic-and-counter-damage-stacks",
                        c6_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(c6_value),
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            DamageDealerFilter(ANTON_ID),
                            AnyFilter(tuple(_event_filter(key) for key in c6_keys)),
                        ),
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    ),
                ),
                stack_count=6,
                stack_min=0,
                stack_max=6,
            )
        )
    else:
        rules.append(
            _rule(
                "cinema6:burst-basic-and-counter-damage-stacks",
                c6_source,
                "6影：爆发状态普攻／闪避反击伤害叠层",
                cinema6.description,
                RuleEligibility.INELIGIBLE,
                stack_count=6,
                stack_min=0,
                stack_max=6,
            )
        )

    return build_definition(
        character_id=ANTON_ID,
        role=CharacterRole.ATTACK,
        element=Element.ELECTRIC,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: AntonCompileConfig) -> None:
    if raw.character_id != ANTON_ID or raw.name != "安东" or raw.code_name != "Anton":
        raise ValueError("unexpected identity in Anton raw record")
    if raw.specialty != "强攻" or raw.element != "电属性" or raw.rarity != 3:
        raise ValueError("Anton raw role, element, or rank changed from reviewed source")
    if raw.faction != "白祇重工":
        raise ValueError("Anton raw faction changed from reviewed source")
    if (
        raw.source_version != "3.2"
        or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1111.json"
    ):
        raise ValueError("Anton source provenance must identify live Nanoka 3.2 character 1111")
    if raw.potential_details:
        raise ValueError("Anton 3.2 source does not have a potential configuration")
    if not 1 <= config.core_level <= 7 or not 0 <= config.cinema_level <= 6:
        raise ValueError("Anton compile levels are outside source bounds")


__all__ = ["compile_anton"]
