"""Compile the lossless Nanoka Vivian record into typed damage and rules."""

from __future__ import annotations

import re
from collections.abc import Mapping

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    CreatedByEffectFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    GuaranteedCritEffect,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
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
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..definition import CharacterCalculationDefinition
from ...element_scope import element_scope_filter
from ..nanoka_compiler import (
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DischargeDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import VivianCompileConfig
from .reviewed import (
    BASIC_BLOSSOMS_MOVE_ID,
    BASIC_FALL_MOVE_ID,
    C6_FEATHER_COUNT,
    DIRECT_BLOSSOM_MUTATION_SOURCE_EFFECT_ID,
    HAS_PROTECTIVE_FEATHER,
    MIND4_ATTACK_BUFF_ACTIVE,
    MUTATION_TRIGGERED,
    PROPHECY_ACTIVE,
    PROPHECY_TICK_COUNT,
    TARGET_HAS_ANOMALY,
    VIVIAN_ID,
    VIVIAN_REVIEWED_MAPPING,
)


ETHER_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:vivian:ether")
ETHER_ANOMALY_MOVE_ID = MoveId("move:vivian:ether-corrosion")
_BASIC = frozenset({DamageTag.BASIC_ATTACK})

_ELEMENT_RATE_INDEX = {
    Element.ETHER: 0,
    Element.XUANMO: 0,
    Element.ELECTRIC: 1,
    Element.FIRE: 2,
    Element.PHYSICAL: 3,
    Element.LINREN: 3,
    Element.ICE: 4,
    Element.LIESHUANG: 4,
    Element.WIND: 5,
}
_MUTATION_ELEMENTS = tuple(_ELEMENT_RATE_INDEX)


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        data,
        expected_character_id=str(VIVIAN_ID),
    )


def _condition(condition_id, label: str, text: str, value: bool = False):
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(key: str, source: RuleSource, label: str, text: str, eligibility, *, conditions=(), effects=(), diagnostics=()):
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1331:{key}"),
        owner=VIVIAN_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        effects=tuple(effects),
        diagnostics=tuple(diagnostics),
    )


def _modifier(key: str, source: RuleSource, node: CalculationNode, value, *, target=EffectTarget.SELF, filters=(), operation=EffectOperation.ADD):
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1331:{key}"),
            source=source,
            owner=VIVIAN_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=operation,
            value=value,
        ),
    )


def _diagnostic(key: str, text: str, *, blocking: bool, candidates=()):
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"{key}"),
        kind=(DiagnosticKind.AMBIGUOUS_SEMANTICS if blocking else DiagnosticKind.UNSUPPORTED_CALCULATOR),
        message=text,
        blocking=blocking,
        candidates=tuple(candidates),
    )


def _source_rate_values(text: str) -> tuple[float, ...]:
    plain = re.sub(r"<[^>]+>", "", text)
    match = re.search(
        r"每10点异常精通\s*([\d.]+)%/([\d.]+)%/([\d.]+)%/([\d.]+)%/([\d.]+)%/([\d.]+)%",
        plain,
    )
    if match is None:
        raise ValueError("Vivian Core must contain all six anomaly-mutation rates")
    return tuple(float(match.group(index)) for index in range(1, 7))


def _mutation_ref(element: Element, *, cinema6: bool) -> tuple[DischargeDamageEventTemplate, DerivedDamageEventTemplateRef, EffectId]:
    suffix = element.value.replace(":", "-")
    key = "cinema6-max-feather-mutation" if cinema6 else "core-anomaly-mutation"
    effect_id = EffectId(f"effect:character:1331:{key}:{suffix}")
    semantic = f"event:character:1331:{key}:{suffix}"
    rule_key = "cinema6:max-feather-mutation" if cinema6 else "core:anomaly-mutation"
    rule_id = RuleItemId(f"rule:character:1331:{rule_key}:{element.value}")
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1331:{key}:{suffix}",
        semantic_id=DamageEventSemanticId(semantic),
        label=("6影：护羽强化异放" if cinema6 else "核心被动：异放"),
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        element=element,
        source_rule_item_id=rule_id,
    )
    template = DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=VIVIAN_ID,
        element=element,
        discharge_triggerer=VIVIAN_ID,
        history_record_source=None,
        crit_rule=NoCritRule(),
        move_id=None,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=(
                "Anomaly Mutation inherits the complete original anomaly "
                "multiplier from its typed Attribute Anomaly source event."
            ),
        ),
        repeat_count_parameter_id=C6_FEATHER_COUNT if cinema6 else None,
        skip_when_repeat_count_zero=cinema6,
    )
    return template, derived, effect_id


def compile_vivian(
    config: VivianCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != VIVIAN_ID:
        raise ValueError("Vivian compiler requires character:1331 raw data")
    if raw_record.element != "以太":
        raise ValueError("Vivian raw record must identify 以太 as her base element")

    direct_entries, direct_templates, compile_diagnostics = compile_direct_moves(
        character_id=VIVIAN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=VIVIAN_REVIEWED_MAPPING,
        id_namespace="character:1331",
    )
    entries: list[MoveCalculationEntry] = list(direct_entries)
    diagnostics = list(compile_diagnostics)

    # Static full-gauge Ether corrosion entry. The history record is assembled
    # from the actual dealer snapshot by the shared static-record adapter.
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1331:ether-corrosion",
        semantic_id=DamageEventSemanticId("event:character:1331:ether-corrosion"),
        label="属性异常：侵蚀",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ETHER,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=VIVIAN_ID,
        element=Element.ETHER,
        anomaly_triggerer=VIVIAN_ID,
        history_record_source=ETHER_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ETHER_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1331:ether-corrosion"),
        character_id=VIVIAN_ID,
        move_id=ETHER_ANOMALY_MOVE_ID,
        display_name="属性异常：侵蚀（10秒满异常）",
        original_text=(
            "按规范满10秒侵蚀记录结算：单跳62.5%，共20跳；异放子事件读取这个"
            "typed源事件的完整异常倍率，不用当前薇薇安面板替代原历史来源。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1331:ether-corrosion"),
                label="每跳侵蚀倍率（10秒20跳）",
                parameter_name="侵蚀单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.625)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_move_id = MoveId("move:vivian:ether-corrosion-disorder")
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1331:ether-corrosion-disorder",
        semantic_id=DamageEventSemanticId("event:character:1331:ether-corrosion-disorder"),
        label="紊乱：以太侵蚀",
        damage_type=DamageType.DISORDER,
        element=Element.ETHER,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=VIVIAN_ID,
        element=Element.ETHER,
        disorder_triggerer=VIVIAN_ID,
        history_record_source=ETHER_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=disorder_move_id,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1331:ether-corrosion-disorder"),
        character_id=VIVIAN_ID,
        move_id=disorder_move_id,
        display_name="紊乱：以太侵蚀",
        original_text="按10秒最大剩余时间结算：450%紊乱基础倍率 + 20次侵蚀补偿（每次62.5%）= 1700%。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1331:ether-corrosion-disorder"),
                label="450% + 20 × 62.5% = 1700%",
                parameter_name="侵蚀满持续时间紊乱倍率",
                multiplier=FixedMultiplier(Resolved(17.0)),
            ),
        ),
        main_damage_event=disorder_ref,
    )
    entries.append(anomaly_entry)
    entries.append(disorder_entry)

    templates: list[object] = [*direct_templates, anomaly_template, disorder_template]
    rules: list[CalculationRuleItem] = []
    conditions = [
        _condition(PROPHECY_ACTIVE, "目标当前处于薇薇安的预言", "预言持续至目标不再处于属性异常状态。"),
        _condition(MIND4_ATTACK_BUFF_ACTIVE, "4影攻击力提升当前有效", "两项指定普通攻击命中后获得，持续12秒；重复命中刷新。"),
        _condition(TARGET_HAS_ANOMALY, "目标当前处于任意属性异常状态", "只表示当前异常状态；不模拟积蓄触发顺序。"),
        _condition(HAS_PROTECTIVE_FEATHER, "薇薇安当前至少有1点护羽", "资源数量由本次静态输入选择。"),
        _condition(MUTATION_TRIGGERED, "落羽生花命中已有属性异常的目标", "表示本次核心异放触发条件已满足；历史异常数值仍来自对应typed记录。"),
    ]
    parameters = [
        ScenarioIntegerParameter(
            parameter_id=PROPHECY_TICK_COUNT,
            label="薇薇安的预言本次结算跳数",
            original_text="每0.55秒造成55%攻击力以太伤害；由用户给出本次跳数，不由时长推算。",
            resolution=ParameterResolution.USER_SELECTED,
            value=None,
            minimum=0,
            maximum=None,
        ),
        ScenarioIntegerParameter(
            parameter_id=C6_FEATHER_COUNT,
            label="影画6：本次异放消耗的护羽数",
            original_text="当前静态模型将消耗护羽数显式选为0–5；每点护羽对应一次基础异放倍率，默认取上限5。",
            resolution=ParameterResolution.USER_SELECTED,
            value=5,
            minimum=0,
            maximum=5,
        ),
    ]
    core_mutation_effects: dict[Element, EffectId] = {}
    c6_mutation_effects: dict[Element, EffectId] = {}

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        VIVIAN_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_eligibility = RuleEligibility.ELIGIBLE
    prophecy_ref = DamageEventTemplateRef(
        template_id="template:character:1331:prophecy-tick",
        semantic_id=DamageEventSemanticId("event:character:1331:prophecy-tick"),
        label="核心被动：薇薇安的预言（每跳）",
        damage_type=DamageType.DIRECT,
        element=Element.ETHER,
        source_rule_item_id=RuleItemId("rule:character:1331:core:prophecy-ticks"),
    )
    prophecy_template = DirectDamageEventTemplate(
        ref=prophecy_ref,
        damage_dealer=VIVIAN_ID,
        element=Element.ETHER,
        base_source=CurrentAttackValueSource(VIVIAN_ID),
        crit_rule=StandardCritRule(VIVIAN_ID),
        move_id=None,
    )
    prophecy_effect_id = EffectId("effect:character:1331:core:prophecy-ticks")
    prophecy_creation = EventCreationEffect(
        rule=EffectRule(
            effect_id=prophecy_effect_id,
            source=core_source,
            owner=VIVIAN_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageDealerFilter(VIVIAN_ID),
                DamageTypeFilter(DamageType.DIRECT),
                AnyFilter((MoveIdFilter(BASIC_FALL_MOVE_ID), MoveIdFilter(BASIC_BLOSSOMS_MOVE_ID))),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=prophecy_ref.template_id,
        ),
    )
    prophecy_derived = DerivedDamageEventTemplateRef(
        template=prophecy_ref,
        multiplier=FixedMultiplier(Resolved(0.55)),
        repeat_count_parameter_id=PROPHECY_TICK_COUNT,
        skip_when_repeat_count_zero=True,
    )
    independent_refs = [prophecy_derived]
    entries.append(
        MoveCalculationEntry(
            entry_id=MoveEntryId("move-entry:character:1331:core-prophecy-tick"),
            character_id=VIVIAN_ID,
            move_id=None,
            display_name="核心被动：薇薇安的预言（每跳）",
            original_text=core.description,
            skill_group=None,
            damage_tags=prophecy_ref.damage_tags,
            multiplier_relation=MultiplierRelation.UNIT_REPEAT,
            multiplier_variants=(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        "variant:character:1331:core-prophecy-tick"
                    ),
                    label="每跳55%攻击力",
                    parameter_name="薇薇安预言当前结算跳数",
                    multiplier=prophecy_derived.multiplier,
                    repeat_count_parameter_id=PROPHECY_TICK_COUNT,
                ),
            ),
            main_damage_event=prophecy_ref,
            condition_ids=(TARGET_HAS_ANOMALY,),
        )
    )
    templates.append(prophecy_template)
    prophecy_diagnostic = _diagnostic(
        "unsupported:character:1331:core:prophecy-timing",
        "The 0.55-second interval and end condition are retained, but static analysis requires an explicit tick count and does not infer ticks from elapsed duration.",
        blocking=False,
    )
    rules.append(
        _rule(
            "core:prophecy-ticks",
            core_source,
            "核心被动：薇薇安的预言周期伤害",
            core.description,
            core_eligibility,
            conditions=(TARGET_HAS_ANOMALY,),
            effects=(prophecy_creation,),
            diagnostics=(prophecy_diagnostic,),
        )
    )

    # Core Anomaly Mutation uses the selected historical anomaly's effect
    # strength and resistance pipeline; only the AP coefficient comes from
    # Vivian's current panel.
    rates = _source_rate_values(core.description)
    for element in _MUTATION_ELEMENTS:
        template, derived, creation_id = _mutation_ref(element, cinema6=False)
        independent_refs.append(derived)
        templates.append(template)
        core_mutation_effects[element] = creation_id
        creation = EventCreationEffect(
            rule=EffectRule(
                effect_id=creation_id,
                source=core_source,
                owner=VIVIAN_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=(
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    ElementFilter(element),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=template.ref.template_id,
            ),
        )
        ratio = rates[_ELEMENT_RATE_INDEX[element]] / 1000.0
        panel_effect = _modifier(
            f"core:anomaly-mutation:current-ap:{element.value.replace(':', '-')}",
            core_source,
            CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
            PanelStatDerivedValue(
                source_character_id=VIVIAN_ID,
                source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                coefficient=Resolved(ratio),
            ),
            target=EffectTarget.TEAM,
            filters=(
                DamageDealerFilter(VIVIAN_ID),
                DamageTypeFilter(DamageType.ANOMALY),
                DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                CreatedByEffectFilter(creation_id),
            ),
        )
        mutation_effects = (creation, panel_effect)
        if element is Element.ETHER:
            direct_source_missing = EventCreationEffect(
                rule=EffectRule(
                    effect_id=DIRECT_BLOSSOM_MUTATION_SOURCE_EFFECT_ID,
                    source=core_source,
                    owner=VIVIAN_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageDealerFilter(VIVIAN_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        MoveIdFilter(BASIC_BLOSSOMS_MOVE_ID),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    unresolved_template=Unresolved(
                        reason=UnresolvedReason.MISSING_DATA,
                        notes=(
                            "The direct Feathering Blossoms event carries no typed "
                            "history-record identity for the target's existing anomaly. "
                            "The original anomaly result cannot be reconstructed from "
                            "Vivian's current panel."
                        ),
                        original_text=core.description,
                    ),
                ),
            )
            mutation_effects = (*mutation_effects, direct_source_missing)
        rules.append(
            _rule(
                f"core:anomaly-mutation:{element.value}",
                core_source,
                f"核心被动：异放（{element.value}）",
                core.description,
                core_eligibility,
                conditions=(MUTATION_TRIGGERED,),
                effects=mutation_effects,
            )
        )
        # C6 has its own maximum-only effect. Intermediate counts have a
        # separate unresolved path below instead of an invented linear ratio.
        c6_template, c6_derived, c6_creation_id = _mutation_ref(element, cinema6=True)
        independent_refs.append(c6_derived)
        templates.append(c6_template)
        c6_mutation_effects[element] = c6_creation_id
        c6_creation = EventCreationEffect(
            rule=EffectRule(
                effect_id=c6_creation_id,
                source=source_for(
                    VIVIAN_ID,
                    "cinema6",
                    EffectSourceType.CINEMA,
                    "6影：薇薇安",
                    raw_record.mindscapes[5].description,
                ),
                owner=VIVIAN_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=(
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    ElementFilter(element),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=c6_template.ref.template_id,
            ),
        )
        c6_source = c6_creation.rule.source
        c6_ratio = rates[_ELEMENT_RATE_INDEX[element]] / 1000.0
        c6_panel_effect = _modifier(
            f"cinema6:max-feather-mutation:current-ap:{element.value.replace(':', '-')}",
            c6_source,
            CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
            PanelStatDerivedValue(
                source_character_id=VIVIAN_ID,
                source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                coefficient=Resolved(c6_ratio),
            ),
            target=EffectTarget.TEAM,
            filters=(
                DamageDealerFilter(VIVIAN_ID),
                DamageTypeFilter(DamageType.ANOMALY),
                DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                CreatedByEffectFilter(c6_creation_id),
            ),
        )
        rules.append(
            _rule(
                f"cinema6:max-feather-mutation:{element.value}",
                c6_source,
                f"6影：当前护羽数异放（{element.value}）",
                raw_record.mindscapes[5].description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
                effects=(c6_creation, c6_panel_effect),
            )
        )

    # Cinema 2 multiplies the proficiency contribution only when the RuleItem
    # is explicitly enabled; it also ignores 15% resistance only on mutation.
    c2 = raw_record.mindscapes[1]
    c2_source = source_for(VIVIAN_ID, "cinema2", EffectSourceType.CINEMA, c2.name, c2.description)
    mutation_filters = (
        DamageDealerFilter(VIVIAN_ID),
        DamageTypeFilter(DamageType.ANOMALY),
        DamageSubtypeFilter(DamageSubtype.DISCHARGE),
        AnyFilter(tuple(CreatedByEffectFilter(item) for item in (*core_mutation_effects.values(), *c6_mutation_effects.values()))),
    )
    c2_effects = [
        _modifier(
            "cinema2:anomaly-buildup-efficiency",
            c2_source,
            CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
            Resolved(0.25),
            target=EffectTarget.TEAM,
            filters=(DamageDealerFilter(VIVIAN_ID), DamageTypeFilter(DamageType.ANOMALY), DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY), ElementFilter(Element.ETHER)),
        ),
        _modifier(
            "cinema2:mutation-resistance-ignore",
            c2_source,
            CalculationNode.DAMAGE_RESISTANCE_IGNORE,
            Resolved(0.15),
            target=EffectTarget.TEAM,
            filters=mutation_filters,
        ),
    ]
    # C2 adds 30% of the AP-derived coefficient. This keeps its RuleItem
    # independently switchable without overloading the existing Anomaly
    # Mutation coefficient node.
    for element in _MUTATION_ELEMENTS:
        base_ratio = rates[_ELEMENT_RATE_INDEX[element]] / 1000.0
        suffix = element.value.replace(":", "-")
        for effect_key, creation_id, factor in (
            ("base", core_mutation_effects[element], 1.0),
            ("c6-feather", c6_mutation_effects[element], 1.0),
        ):
            c2_effects.append(
                _modifier(
                    f"cinema2:mutation-proficiency-yield:{effect_key}:{suffix}",
                    c2_source,
                    CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
                    PanelStatDerivedValue(
                        source_character_id=VIVIAN_ID,
                        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                        coefficient=Resolved(base_ratio * factor * 0.30),
                    ),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(VIVIAN_ID),
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                        CreatedByEffectFilter(creation_id),
                    ),
                )
            )
    rules.append(
        _rule(
            "cinema2:anomaly-proficiency-and-resistance",
            c2_source,
            "2影：以太积蓄效率与异放收益",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=tuple(c2_effects),
        )
    )

    # C1 target state grants team anomaly and disorder damage bonuses.
    c1 = raw_record.mindscapes[0]
    c1_source = source_for(VIVIAN_ID, "cinema1", EffectSourceType.CINEMA, c1.name, c1.description)
    c1_value = float(re.search(r"提升([\d.]+)%", re.sub(r"<[^>]+>", "", c1.description)).group(1)) / 100.0
    c1_eligibility = RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE
    rules.append(
        _rule(
            "cinema1:prophecy-anomaly-damage",
            c1_source,
            "1影：预言目标受到的属性异常伤害提升",
            c1.description,
            c1_eligibility,
            conditions=(PROPHECY_ACTIVE,),
            effects=(
                _modifier("cinema1:prophecy-anomaly-damage", c1_source, CalculationNode.ANOMALY_DAMAGE_BONUS, Resolved(c1_value), target=EffectTarget.TEAM, filters=(DamageTypeFilter(DamageType.ANOMALY),)),
            ),
        )
    )
    rules.append(
        _rule(
            "cinema1:prophecy-disorder-damage",
            c1_source,
            "1影：预言目标受到的紊乱伤害提升",
            c1.description,
            c1_eligibility,
            conditions=(PROPHECY_ACTIVE,),
            effects=(
                _modifier("cinema1:prophecy-disorder-damage", c1_source, CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS, Resolved(c1_value), target=EffectTarget.TEAM, filters=(DamageTypeFilter(DamageType.DISORDER),)),
            ),
        )
    )

    # Additional Ability eligibility is determined from actual team roles and
    # elements by the presentation registry, never by the selected operator.
    extra_source = source_for(
        VIVIAN_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligibility = RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE
    extra_ratio_match = re.search(r"伤害提升([\d.]+)%", re.sub(r"<[^>]+>", "", raw_record.extra_ability_description))
    if extra_ratio_match is None:
        raise ValueError("Vivian Additional Ability must contain the Corrosion bonus")
    extra_ratio = float(extra_ratio_match.group(1)) / 100.0
    corrosion_filters = (
        DamageTypeFilter(DamageType.ANOMALY),
        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
        ElementFilter(Element.ETHER),
    )
    extra_damage_effects = (
        _modifier("extra-ability:corrosion-damage", extra_source, CalculationNode.ANOMALY_DAMAGE_BONUS, Resolved(extra_ratio), target=EffectTarget.TEAM, filters=corrosion_filters),
        _modifier("extra-ability:corrosion-disorder-damage", extra_source, CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS, Resolved(extra_ratio), target=EffectTarget.TEAM, filters=(DamageTypeFilter(DamageType.DISORDER), ElementFilter(Element.ETHER))),
    )
    extra_hit_id = EffectId("effect:character:1331:extra-ability:feathering-blossoms")
    extra_rule_id = RuleItemId("rule:character:1331:extra-ability:feathering-blossoms")
    blossoms_entry = next(item for item in entries if item.move_id == BASIC_BLOSSOMS_MOVE_ID)
    extra_hit_ref = DamageEventTemplateRef(
        template_id="template:character:1331:extra-ability:feathering-blossoms",
        semantic_id=DamageEventSemanticId("event:character:1331:extra-ability:feathering-blossoms"),
        label="额外能力：普通攻击：落羽生花",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=_BASIC,
        element=Element.ETHER,
        source_rule_item_id=extra_rule_id,
    )
    templates.append(
        DirectDamageEventTemplate(
            ref=extra_hit_ref,
            damage_dealer=VIVIAN_ID,
            element=Element.ETHER,
            base_source=CurrentAttackValueSource(VIVIAN_ID),
            crit_rule=StandardCritRule(VIVIAN_ID),
            move_id=BASIC_BLOSSOMS_MOVE_ID,
        )
    )
    extra_hit_derived = DerivedDamageEventTemplateRef(
        template=extra_hit_ref,
        multiplier=blossoms_entry.multiplier_variants[0].multiplier,
    )
    independent_refs.append(extra_hit_derived)
    extra_hit_rule = EventCreationEffect(
        rule=EffectRule(
            effect_id=extra_hit_id,
            source=extra_source,
            owner=VIVIAN_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.ANOMALY),
                DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                NotFilter(DamageDealerFilter(VIVIAN_ID)),
            ),
        ),
        result=EventCreationResult(event_kind=BattleEventKind.DAMAGE, event_template_id=extra_hit_ref.template_id),
    )
    extra_hit_diagnostic = _diagnostic(
        "unsupported:character:1331:extra-ability:resource-throttle",
        "Anomaly applications are represented as typed source events. Feather consumption is an explicit current-state condition, while the 0.5-second throttle is not replayed as a timeline.",
        blocking=False,
    )
    rules.append(
        _rule(
            "extra-ability:corrosion-damage",
            extra_source,
            "额外能力：全队侵蚀与紊乱伤害提升",
            raw_record.extra_ability_description,
            extra_eligibility,
            effects=extra_damage_effects,
        )
    )
    rules.append(
        _rule(
            "extra-ability:feathering-blossoms",
            extra_source,
            "额外能力：护羽追击落羽生花",
            raw_record.extra_ability_description,
            extra_eligibility,
            conditions=(HAS_PROTECTIVE_FEATHER,),
            effects=(extra_hit_rule,),
            diagnostics=(extra_hit_diagnostic,),
        )
    )

    # Cinema 4 attack buff is a self panel modifier during Prophecy. Its
    # guaranteed crit is separately scoped to the two named Basic moves.
    c4 = raw_record.mindscapes[3]
    c4_source = source_for(VIVIAN_ID, "cinema4", EffectSourceType.CINEMA, c4.name, c4.description)
    c4_text = re.sub(r"<[^>]+>", "", c4.description)
    c4_attack = float(re.search(r"攻击力提升([\d.]+)%", c4_text).group(1)) / 100.0
    c4_eligibility = RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE
    rules.append(
        _rule(
            "cinema4:prophecy-attack",
            c4_source,
            "4影：预言期间薇薇安攻击力提升",
            c4.description,
            c4_eligibility,
            conditions=(MIND4_ATTACK_BUFF_ACTIVE,),
            effects=(
                _modifier("cinema4:prophecy-attack", c4_source, CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS, Resolved(c4_attack), target=EffectTarget.SELF),
            ),
        )
    )
    c4_guaranteed_id = EffectId("effect:character:1331:cinema4:basic-guaranteed-crit")
    c4_guaranteed = GuaranteedCritEffect(
        rule=EffectRule(
            effect_id=c4_guaranteed_id,
            source=c4_source,
            owner=VIVIAN_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageDealerFilter(VIVIAN_ID),
                DamageTypeFilter(DamageType.DIRECT),
                AnyFilter((MoveIdFilter(BASIC_FALL_MOVE_ID), MoveIdFilter(BASIC_BLOSSOMS_MOVE_ID))),
            ),
        )
    )
    rules.append(_rule("cinema4:basic-guaranteed-crit", c4_source, "4影：悬落与落羽生花必定暴击", c4.description, c4_eligibility, effects=(c4_guaranteed,)))

    # Cinema 6 Ether damage is scoped to Vivian's actual event dealer and the
    # Ether/Xuanmo shared element scope. Each calculator lane receives its
    # correctly typed damage bonus.
    c6 = raw_record.mindscapes[5]
    c6_source = source_for(VIVIAN_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
    c6_text = re.sub(r"<[^>]+>", "", c6.description)
    c6_ether_bonus = float(re.search(r"以太伤害提升([\d.]+)%", c6_text).group(1)) / 100.0
    c6_eligibility = RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE
    ether_scope = element_scope_filter(Element.ETHER)
    c6_effects = (
        _modifier(
            "cinema6:ether-normal-damage",
            c6_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(c6_ether_bonus),
            target=EffectTarget.TEAM,
            filters=(DamageDealerFilter(VIVIAN_ID), ether_scope, NotFilter(DamageSubtypeFilter(DamageSubtype.DISCHARGE))),
        ),
    )
    feather_resource_diagnostic = _diagnostic(
        "unsupported:character:1331:cinema6:feather-resource-sequence",
        "Cinema 6's feather gains/consumption sequence and evade trigger are not replayed; the current static request supplies an explicit 0–5 feather count, defaulting to five, and each selected feather applies one base Anomaly Mutation ratio.",
        blocking=False,
    )
    c6_lane_diagnostic = _diagnostic(
        "unsupported:character:1331:cinema6:ether-damage-lanes",
        "Cinema 6's 40% Ether damage uses the normal bonus at damage-record creation for Vivian-owned static anomaly/Disorder sources. It is not copied into an independent Discharge bonus region, and explicit historical records or another character's source record are not rewritten.",
        blocking=False,
    )
    rules.append(_rule("cinema6:ether-damage-and-feather-resource", c6_source, "6影：薇薇安以太伤害与飞羽资源", c6.description, c6_eligibility, effects=c6_effects, diagnostics=(feather_resource_diagnostic, c6_lane_diagnostic)))

    # The source's non-damage resource and buildup timelines stay explicit.
    resource_diagnostic = _diagnostic(
        "unsupported:character:1331:core:feather-resource-sequence",
        "Feather and Protective Feather gains/consumption, stance transitions, and 0.5-second event throttles are not simulated; users select only the current state needed for a calculation.",
        blocking=False,
    )
    rules.append(_rule("core:feather-resource", core_source, "核心被动：飞羽与护羽资源", core.description, core_eligibility, diagnostics=(resource_diagnostic,)))
    definition_source = source_for(
        VIVIAN_ID,
        "nanoka-3.2",
        EffectSourceType.SKILL,
        raw_record.name,
        f"source_version={raw_record.source_version}; source_url={raw_record.source_url}",
    )
    return CharacterCalculationDefinition(
        character_id=VIVIAN_ID,
        role=CharacterRole.ANOMALY,
        base_element=Element.ETHER,
        source=definition_source,
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=tuple(conditions),
        scenario_parameters=tuple(parameters),
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=tuple(independent_refs),
        diagnostics=tuple(diagnostics),
    )


__all__ = ["ETHER_ANOMALY_MOVE_ID", "ETHER_ANOMALY_RECORD_ID", "compile_vivian", "load_raw_record"]
