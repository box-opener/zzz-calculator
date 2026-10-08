"""Compile Lighter's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
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
    EnemyStateFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    NotCondition,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    StateId,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...element_scope import element_scope_filter
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
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import LighterCompileConfig
from .reviewed import (
    BLIGHT_ACTIVE,
    CORE_RESISTANCE_DEBUFF_ACTIVE,
    FIRE_ANOMALY_MOVE_ID,
    FIRE_ANOMALY_RECORD_ID,
    FIRE_DISORDER_MOVE_ID,
    LIGHTER_ID,
    LIGHTER_REVIEWED_MAPPING,
    MORALE_BRAWL_ACTIVE,
    MORALE_FINISHER_ACTIVE,
    MORALE_IMPACT_BUFF_ACTIVE,
    YANG_ACTIVE,
)


_ENEMY_STUNNED = StateId("state:enemy:stunned")
_FIRE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:lighter:fire-disorder-remaining-seconds"
)

_C6_FIRE_IMPACT_NORMAL_RULE_ID = RuleItemId(
    "rule:character:1161:cinema6:fire-impact-on-current-move"
)
_C6_FIRE_IMPACT_EXTRA_RULE_ID = RuleItemId(
    "rule:character:1161:cinema6:morale-finisher-extra-fire-impact"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id: ScenarioConditionId, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(LIGHTER_ID, key, kind, label, text)


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
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1161:{key}"),
        owner=LIGHTER_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        diagnostics=tuple(diagnostics),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
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
            effect_id=EffectId(f"effect:character:1161:{key}"),
            source=source,
            owner=LIGHTER_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=operation,
            value=value,
        ),
    )


def _note(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1161:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_fire_entries():
    record_id = AnomalyRecordId(FIRE_ANOMALY_RECORD_ID)
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1161:fire-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1161:fire-anomaly"),
        label="属性异常：灼烧（10秒，20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=LIGHTER_ID,
        element=Element.FIRE,
        anomaly_triggerer=LIGHTER_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1161:fire-anomaly"),
        character_id=LIGHTER_ID,
        move_id=FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（10秒，20跳）",
        original_text="按规范静态火属性异常；每0.5秒结算异常效果强度的50%，共20跳并使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1161:fire-anomaly-tick"),
                label="灼烧每跳50%（10秒20跳）",
                parameter_name="灼烧每跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1161:fire-disorder",
        semantic_id=DamageEventSemanticId("event:character:1161:fire-disorder"),
        label="紊乱：灼烧",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=LIGHTER_ID,
        element=Element.FIRE,
        disorder_triggerer=LIGHTER_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1161:fire-disorder"),
        character_id=LIGHTER_ID,
        move_id=FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧",
        original_text="按规范灼烧紊乱倍率；使用用户选择的当前剩余时间，不模拟战斗时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1161:fire-disorder"),
                label="450% + floor(t/0.5秒) × 50%",
                parameter_name="当前目标灼烧剩余时间",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_FIRE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.0,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_FIRE_DISORDER_REMAINING_SECONDS,
        label="当前目标灼烧剩余时间（秒）",
        original_text="由用户选择当前剩余时间；不回放灼烧时间轴。",
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


def _impact_scaled_fire_impact_effect(
    *,
    key: str,
    source: RuleSource,
    child_template_ids: Sequence[EventTemplateId],
    base_multiplier: float,
    per_impact_point: float,
    extra_cap: float,
) -> ModifierEffect:
    """Apply the current-Impact part of C6 as an event-multiplier factor.

    The authored multiplier is 250% plus up to another 500%. Applying a
    factor of ``1 + per_impact_point / base_multiplier * (Impact - 170)`` to
    that base is algebraically identical to adding the source-defined amount
    per Impact point, capped at its extra-multiplier limit.
    """

    impact_factor = PanelStatDerivedValue(
        source_character_id=LIGHTER_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_IMPACT,
        coefficient=Resolved(per_impact_point / base_multiplier),
        base=Resolved(1.0),
        cap_max=Resolved(1.0 + extra_cap / base_multiplier),
        threshold=Resolved(170.0),
    )
    template_filter = (
        EventTemplateIdFilter(child_template_ids[0])
        if len(child_template_ids) == 1
        else AnyFilter(tuple(EventTemplateIdFilter(item) for item in child_template_ids))
    )
    return _modifier(
        key,
        source,
        CalculationNode.DAMAGE_SKILL_MULTIPLIER,
        impact_factor,
        target=EffectTarget.TEAM,
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(LIGHTER_ID),
            template_filter,
        ),
        operation=EffectOperation.MULTIPLY,
    )


def _c6_fire_impact_child(
    parent: DirectDamageEventTemplate,
    *,
    suffix: str,
    source_rule_id: RuleItemId,
    base_multiplier: float,
) -> tuple[DirectDamageEventTemplate, DerivedDamageEventTemplateRef]:
    parent_ref = parent.ref
    ref = replace(
        parent_ref,
        template_id=EventTemplateId(
            f"template:character:1161:cinema6:fire-impact:{suffix}"
        ),
        semantic_id=DamageEventSemanticId(
            f"event:character:1161:cinema6:fire-impact:{suffix}"
        ),
        label=f"6影火焰冲击（{parent_ref.label}）",
        element=Element.FIRE,
        source_rule_item_id=source_rule_id,
    )
    template = replace(
        parent,
        ref=ref,
        element=Element.FIRE,
        move_id=None,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(base_multiplier)),
        repeat_count=1,
    )
    return template, derived


def compile_lighter(
    config: LighterCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=LIGHTER_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=LIGHTER_REVIEWED_MAPPING,
        id_namespace="character:1161",
    )
    entries = list(entries)
    direct_templates = tuple(direct_templates)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    fire_entries, fire_templates, disorder_remaining = _static_fire_entries()
    entries.extend(fire_entries)
    templates.extend(fire_templates)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    cinema_sources = {
        cinema.level: _source(
            f"cinema-{cinema.level}",
            EffectSourceType.CINEMA,
            cinema.name,
            cinema.description,
        )
        for cinema in raw_record.mindscapes
    }
    conditions = [
        _condition(MORALE_BRAWL_ACTIVE, "当前处于士气喷发状态", core.description),
        _condition(MORALE_IMPACT_BUFF_ACTIVE, "士气消耗带来的冲击力提升当前生效", core.description),
        _condition(CORE_RESISTANCE_DEBUFF_ACTIVE, "当前目标处于莱特核心被动的火／冰抗性降低状态", core.description),
        _condition(BLIGHT_ACTIVE, "当前目标处于溃败状态", core.description),
        _condition(YANG_ACTIVE, "昂扬状态当前生效", core.extra_ability_description),
    ]
    rules: list[CalculationRuleItem] = []

    morale_impact_per_ten = _number(
        core.description,
        r"每消耗10点\[士气\]，莱特的冲击力提升(?P<value>[\d.]+)%",
        "Lighter Core Impact increase per 10 Morale",
    ) / 100.0
    morale_impact_cap = _number(
        core.description,
        r"最多提升(?P<value>[\d.]+)%",
        "Lighter Core maximum Impact increase",
    ) / 100.0
    morale_impact_stack_max = round(morale_impact_cap / morale_impact_per_ten)
    rules.append(
        _rule(
            "core:morale-impact-stacks",
            core_source,
            f"核心被动：当前士气消耗冲击力提升（每10点+{morale_impact_per_ten:.1%}，上限{morale_impact_cap:.0%}）",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(MORALE_IMPACT_BUFF_ACTIVE,),
            stack_count=morale_impact_stack_max,
            stack_min=0,
            stack_max=morale_impact_stack_max,
            effects=(
                _modifier(
                    "core:morale-impact-stacks",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
                    Resolved(morale_impact_per_ten),
                    target=EffectTarget.SELF,
                ),
            ),
            diagnostics=(
                _note(
                    "core:morale-resource-timing",
                    "Morale regeneration, Energy spending, the six-second refresh, and per-hit consumption are source-only; the selected 0–10 Impact-bonus layers represent the current buff without replaying a timeline.",
                    core.description,
                ),
            ),
        )
    )

    resistance_reduction = _number(
        core.description,
        r"冰属性伤害抗性和火属性伤害抗性降低(?P<value>[\d.]+)%",
        "Lighter Core Ice/Fire resistance reduction",
    ) / 100.0
    core_res_filters = AnyFilter(
        (
            element_scope_filter(Element.ICE),
            element_scope_filter(Element.FIRE),
        )
    )
    rules.append(
        _rule(
            "core:fire-ice-resistance-reduction",
            core_source,
            f"核心被动：当前目标火／冰抗性降低{resistance_reduction:.0%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(CORE_RESISTANCE_DEBUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:fire-ice-resistance-reduction",
                    core_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(resistance_reduction),
                    target=EffectTarget.ENEMY,
                    filters=(core_res_filters,),
                ),
            ),
            diagnostics=(
                _note(
                    "core:target-debuff-duration",
                    "The Core describes the 30-second resistance reduction and a three-second Stun extension. The current target resistance-down state is explicit; the calculator does not replay its application duration or output Daze/Stun duration.",
                    core.description,
                ),
            ),
        )
    )

    # Lighter's Additional Ability is not gated by the current operator. Its
    # native eligibility is resolved from active team members by the registry.
    yang_stack_max = round(
        _number(
            core.extra_ability_description,
            r"最多叠加(?P<value>\d+)层",
            "Lighter Additional Ability Yang stack cap",
        )
    )
    yang_base_per_stack = _number(
        core.extra_ability_description,
        r"每拥有一层\[昂扬\].*?伤害提升(?P<value>[\d.]+)%",
        "Lighter Additional Ability damage per Yang stack",
    ) / 100.0
    yang_impact_per_ten = _number(
        core.extra_ability_description,
        r"每超过10点冲击力.*?额外提升(?P<value>[\d.]+)%",
        "Lighter Additional Ability Impact bonus per 10 Impact",
    ) / 100.0
    yang_total_cap = _number(
        core.extra_ability_description,
        r"最多使代理人造成的.*?伤害提升(?P<value>[\d.]+)%",
        "Lighter Additional Ability total damage cap",
    ) / 100.0
    cinema2_yang_scale = 1.0
    cinema2 = raw_record.mindscapes[1]
    cinema2_source = cinema_sources[2]
    if config.cinema_level >= 2:
        cinema2_yang_scale = _number(
            cinema2.description,
            r"增益效果提升至原本的(?P<value>[\d.]+)%",
            "Lighter Cinema 2 Yang effect increase",
        ) / 100.0
    yang_rule_effects = [
        _modifier(
            "extra-ability:yang-stacks",
            extra_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            PanelStatDerivedValue(
                source_character_id=LIGHTER_ID,
                source_node=CalculationNode.CHARACTER_CURRENT_IMPACT,
                coefficient=Resolved(yang_impact_per_ten),
                base=Resolved(yang_base_per_stack),
                cap_max=Resolved(yang_total_cap / yang_stack_max),
                threshold=Resolved(170.0),
                step_size=Resolved(10.0),
            ),
            target=EffectTarget.TEAM,
            filters=(
                AnyFilter(
                    (
                        element_scope_filter(Element.ICE),
                        element_scope_filter(Element.FIRE),
                    )
                ),
            ),
        )
    ]
    if config.cinema_level >= 2:
        # Cinema 2 increases the entire per-stack Yang value by 20%, including
        # the current-Impact-derived part. Keep its source visible as a
        # separate additive trace while sharing the same stack control.
        yang_rule_effects.append(
            _modifier(
                "cinema2:yang-stacks-increase",
                cinema2_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                PanelStatDerivedValue(
                    source_character_id=LIGHTER_ID,
                    source_node=CalculationNode.CHARACTER_CURRENT_IMPACT,
                    coefficient=Resolved(
                        yang_impact_per_ten * (cinema2_yang_scale - 1.0)
                    ),
                    base=Resolved(yang_base_per_stack * (cinema2_yang_scale - 1.0)),
                    cap_max=Resolved(
                        yang_total_cap
                        / yang_stack_max
                        * (cinema2_yang_scale - 1.0)
                    ),
                    threshold=Resolved(170.0),
                    step_size=Resolved(10.0),
                ),
                target=EffectTarget.TEAM,
                filters=(
                    AnyFilter(
                        (
                            element_scope_filter(Element.ICE),
                            element_scope_filter(Element.FIRE),
                        )
                    ),
                ),
            )
        )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "extra-ability:yang-stacks",
            extra_source,
            f"额外能力：当前昂扬层数（每层火／冰伤害+{yang_base_per_stack:.2%}，受当前冲击力影响）",
            core.extra_ability_description,
            extra_eligibility,
            conditions=(YANG_ACTIVE,),
            stack_count=yang_stack_max,
            stack_min=0,
            stack_max=yang_stack_max,
            effects=tuple(yang_rule_effects),
            diagnostics=(
                _note(
                    "extra-ability:yang-duration",
                    "Yang's 30-second duration and refresh behavior are not replayed; the selected stack count and active state describe the current static buff.",
                    core.extra_ability_description,
                ),
            ),
        )
    )

    cinema1 = raw_record.mindscapes[0]
    cinema1_source = cinema_sources[1]
    if config.cinema_level >= 1:
        c1_resistance_bonus = _number(
            cinema1.description,
            r"额外降低(?P<value>[\d.]+)%",
            "Lighter Cinema 1 additional Fire/Ice resistance reduction",
        ) / 100.0
        rules.append(
            _rule(
                "cinema1:core-resistance-reduction",
                cinema1_source,
                f"1影：当前溃败目标火／冰抗性额外降低{c1_resistance_bonus:.0%}",
                cinema1.description,
                RuleEligibility.ELIGIBLE,
                conditions=(CORE_RESISTANCE_DEBUFF_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema1:core-resistance-reduction",
                        cinema1_source,
                        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                        Resolved(c1_resistance_bonus),
                        target=EffectTarget.ENEMY,
                        filters=(core_res_filters,),
                    ),
                ),
                diagnostics=(
                    _note(
                        "cinema1:blight-duration",
                        "Cinema 1 extends Blight duration by five seconds; the target's current resistance-down state is selected explicitly and the calculator does not simulate its duration.",
                        cinema1.description,
                    ),
                ),
            )
        )
        strong_finisher_template = EventTemplateId(
            "template:character:1161:basic-5-morale-strong-finisher:main"
        )
        c1_finisher_bonus = _number(
            cinema1.description,
            r"强力终结一击造成的伤害提升(?P<value>[\d.]+)%",
            "Lighter Cinema 1 Morale finisher damage increase",
        ) / 100.0
        rules.append(
            _rule(
                "cinema1:morale-finisher-damage",
                cinema1_source,
                f"1影：士气耗尽强力终结伤害+{c1_finisher_bonus:.0%}",
                cinema1.description,
                RuleEligibility.ELIGIBLE,
                conditions=(MORALE_FINISHER_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema1:morale-finisher-damage",
                        cinema1_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(c1_finisher_bonus),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageDealerFilter(LIGHTER_ID),
                            DamageTypeFilter(DamageType.DIRECT),
                            EventTemplateIdFilter(strong_finisher_template),
                        ),
                    ),
                ),
            )
        )

    if config.cinema_level >= 2:
        c2_stun_vulnerability = _number(
            cinema2.description,
            r"失衡易伤倍率提升(?P<value>[\d.]+)%",
            "Lighter Cinema 2 Blight Stun vulnerability increase",
        ) / 100.0
        rules.append(
            _rule(
                "cinema2:blight-stun-vulnerability",
                cinema2_source,
                f"2影：溃败目标当前失衡易伤倍率+{c2_stun_vulnerability:.0%}",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                conditions=(BLIGHT_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema2:blight-stun-vulnerability",
                        cinema2_source,
                        CalculationNode.ENEMY_STUN_VULNERABILITY,
                        Resolved(c2_stun_vulnerability),
                        target=EffectTarget.ENEMY,
                        filters=(EnemyStateFilter(_ENEMY_STUNNED),),
                    ),
                ),
            )
        )

    if config.cinema_level >= 4:
        cinema4 = raw_record.mindscapes[3]
        cinema4_source = cinema_sources[4]
        backline_regen_bonus = _number(
            cinema4.description,
            r"能量自动回复效率提升(?P<value>[\d.]+)%",
            "Lighter Cinema 4 front-line Energy regeneration bonus",
        ) / 100.0
        rules.append(
            _rule(
                "cinema4:frontline-energy-regeneration",
                cinema4_source,
                f"4影：莱特处于后场时，当前前场角色能量自动回复效率+{backline_regen_bonus:.0%}",
                cinema4.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema4:frontline-energy-regeneration",
                        cinema4_source,
                        CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS,
                        Resolved(backline_regen_bonus),
                        target=EffectTarget.CURRENT_OPERATOR,
                        condition=NotCondition(
                            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)
                        ),
                    ),
                ),
            )
        )
        rules.append(
            _rule(
                "cinema4:rear-energy-source-only",
                cinema4_source,
                "4影：入场时回复后场角色能量",
                cinema4.description,
                RuleEligibility.ELIGIBLE,
                diagnostics=(
                    _note(
                        "cinema4:rear-energy-source-only",
                        "The four-Energy entry effect has an 18-second limit; Energy and elapsed-time simulation are outside the calculator output.",
                        cinema4.description,
                    ),
                ),
            )
        )

    cinema6 = raw_record.mindscapes[5]
    cinema6_source = cinema_sources[6]
    c6_base_multiplier = _number(
        cinema6.description,
        r"造成(?P<value>[\d.]+)%攻击力",
        "Lighter Cinema 6 Fire Impact base multiplier",
    ) / 100.0
    c6_per_impact_point = _number(
        cinema6.description,
        r"每超过1点冲击力.*?倍率额外提升(?P<value>[\d.]+)%",
        "Lighter Cinema 6 Fire Impact per-Impact multiplier increase",
    ) / 100.0
    c6_extra_cap = _number(
        cinema6.description,
        r"最多提升(?P<value>[\d.]+)%",
        "Lighter Cinema 6 Fire Impact additional multiplier cap",
    ) / 100.0
    if config.cinema_level >= 6:
        c6_templates: list[DirectDamageEventTemplate] = []
        c6_refs_by_parent: dict[EventTemplateId, DerivedDamageEventTemplateRef] = {}
        normal_effects = []
        for parent in direct_templates:
            if not isinstance(parent, DirectDamageEventTemplate):
                continue
            # The source lists Basic/Counter/Special/EX/Quick Assist/Assist/
            # Chain/Ultimate. Dash Attack is not in that authored list.
            if DamageTag.DASH_ATTACK in parent.ref.damage_tags:
                continue
            suffix = (
                str(parent.ref.template_id)
                .split("character:1161:", 1)[-1]
                .replace(":", "-")
            )
            child_template, child_ref = _c6_fire_impact_child(
                parent,
                suffix=f"{suffix}-heavy-hit",
                source_rule_id=_C6_FIRE_IMPACT_NORMAL_RULE_ID,
                base_multiplier=c6_base_multiplier,
            )
            c6_templates.append(child_template)
            c6_refs_by_parent[parent.ref.template_id] = child_ref
            parent_index = next(
                index
                for index, entry in enumerate(entries)
                if entry.main_damage_event.template_id == parent.ref.template_id
            )
            entries[parent_index] = replace(
                entries[parent_index],
                derived_damage_events=(
                    *entries[parent_index].derived_damage_events,
                    child_ref,
                ),
            )
            normal_effects.append(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            f"effect:character:1161:cinema6:fire-impact:create:{suffix}"
                        ),
                        source=cinema6_source,
                        owner=LIGHTER_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            DamageDealerFilter(LIGHTER_ID),
                            EventTemplateIdFilter(parent.ref.template_id),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=child_ref.template.template_id,
                        unique_per_source_event=True,
                    ),
                )
            )
        normal_child_ids = tuple(
            item.template.template_id for item in c6_refs_by_parent.values()
        )
        normal_effects.append(
            _impact_scaled_fire_impact_effect(
                key="cinema6:fire-impact:heavy-hit-impact-scaling",
                source=cinema6_source,
                child_template_ids=normal_child_ids,
                base_multiplier=c6_base_multiplier,
                per_impact_point=c6_per_impact_point,
                extra_cap=c6_extra_cap,
            )
        )
        rules.append(
            _rule(
                "cinema6:fire-impact-on-current-move",
                cinema6_source,
                "6影：本次所选招式末击触发火焰冲击",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                effects=tuple(normal_effects),
            )
        )

        strong_finisher_template_id = EventTemplateId(
            "template:character:1161:basic-5-morale-strong-finisher:main"
        )
        strong_finisher = next(
            item for item in direct_templates if item.ref.template_id == strong_finisher_template_id
        )
        extra_template, extra_ref = _c6_fire_impact_child(
            strong_finisher,
            suffix="morale-exhausted-strong-finisher-extra",
            source_rule_id=_C6_FIRE_IMPACT_EXTRA_RULE_ID,
            base_multiplier=c6_base_multiplier,
        )
        c6_templates.append(extra_template)
        strong_finisher_index = next(
            index
            for index, entry in enumerate(entries)
            if entry.main_damage_event.template_id == strong_finisher_template_id
        )
        entries[strong_finisher_index] = replace(
            entries[strong_finisher_index],
            derived_damage_events=(
                *entries[strong_finisher_index].derived_damage_events,
                extra_ref,
            ),
        )
        extra_effects = (
            EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId(
                        "effect:character:1161:cinema6:fire-impact:morale-finisher-extra"
                    ),
                    source=cinema6_source,
                    owner=LIGHTER_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(LIGHTER_ID),
                        EventTemplateIdFilter(strong_finisher_template_id),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    event_template_id=extra_ref.template.template_id,
                    unique_per_source_event=True,
                ),
            ),
            _impact_scaled_fire_impact_effect(
                key="cinema6:fire-impact:finisher-extra-impact-scaling",
                source=cinema6_source,
                child_template_ids=(extra_ref.template.template_id,),
                base_multiplier=c6_base_multiplier,
                per_impact_point=c6_per_impact_point,
                extra_cap=c6_extra_cap,
            ),
        )
        rules.append(
            _rule(
                "cinema6:morale-finisher-extra-fire-impact",
                cinema6_source,
                "6影：士气耗尽强力终结额外触发一次火焰冲击",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                conditions=(MORALE_FINISHER_ACTIVE,),
                effects=extra_effects,
            )
        )
        templates.extend(c6_templates)

    if config.cinema_level >= 6:
        rules.append(
            _rule(
                "cinema6:morale-resource-source-only",
                cinema6_source,
                "6影：士气回复效率提升",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                diagnostics=(
                    _note(
                        "cinema6:morale-resource-source-only",
                        "Cinema 6 doubles Morale regeneration. Morale and elapsed-time behavior are not simulated; the strong finisher's additional Fire Impact is a separate source-defined effect.",
                        cinema6.description,
                    ),
                ),
            )
        )

    conditions.extend(
        (
            _condition(MORALE_FINISHER_ACTIVE, "士气耗尽后本次衔接强力终结一击", core.description),
        )
    )
    assist_parry = next(item for item in raw_record.moves if item.name == "招架支援：瞬破")
    assist_source = _source("assist-parry:daze-only", EffectSourceType.SKILL, assist_parry.name, assist_parry.description)
    rules.append(
        _rule(
            "assist-parry:daze-only",
            assist_source,
            "招架支援：瞬破（来源列出失衡值）",
            assist_parry.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                _note(
                    "assist-parry:daze-only",
                    "The Defense Assist source has Daze values but no damage ratio; the calculator has no Daze output and does not fabricate a damage event.",
                    assist_parry.description,
                ),
            ),
        )
    )

    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = cinema_sources[level]
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级提升",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )
    return build_definition(
        character_id=LIGHTER_ID,
        role=CharacterRole.STUN,
        element=Element.FIRE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=tuple(conditions),
        parameters=(disorder_remaining,),
        diagnostics=tuple(diagnostics),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(LIGHTER_ID))


def _validate_raw_record(raw: NanokaRawRecord, config: LighterCompileConfig) -> None:
    if raw.character_id != LIGHTER_ID or raw.name != "莱特" or raw.code_name != "Lighter":
        raise ValueError("unexpected identity in Lighter raw record")
    if raw.specialty != "击破" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("Lighter raw role, element, or rank changed from reviewed source")
    if raw.faction != "卡吕冬之子":
        raise ValueError("Lighter raw faction changed from reviewed source")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1161.json":
        raise ValueError("Lighter provenance must identify live Nanoka 3.2 character 1161")
    if raw.potential_details:
        raise ValueError("Lighter 3.2 source does not have potential variants")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Lighter source must contain seven Core levels and six Cinemas")
    if config.character_id != LIGHTER_ID:
        raise ValueError("Lighter compile config has an unexpected character ID")


__all__ = ["compile_lighter", "load_raw_record"]
