"""Compile Nangong Yu's reviewed Nanoka 3.2 source into damage contracts."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    BASE_ELEMENT_BY_ELEMENT,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterRole,
    DamageDealerFilter,
    DamageDealerIdentityFilter,
    DamageTag,
    DamageTagFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageType,
    DamageTypeFilter,
    DynamicIdentity,
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
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    ScenarioParameterRangeCondition,
    ScenarioParameterDerivedValue,
    SnapshotRule,
    StateId,
    Unresolved,
    UnresolvedEffect,
    UnresolvedReason,
    NotCondition,
    RuleStackCondition,
)

from ...ids import (
    DamageEventSemanticId,
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
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    source_for,
)
from ..nanoka_source import NanokaRawRecord
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DischargeDamageEventTemplate,
    DisorderDamageEventTemplate,
    PolarDisorderDamageEventTemplate,
)
from .config import NANGONGYU_ID, NangongYuCompileConfig
from .reviewed import (
    NANGONGYU_ETHER_ANOMALY_RECORD_ID,
    NANGONGYU_REVIEWED_MAPPING,
)


_DISCHARGE_ELEMENTS = (
    Element.ETHER,
    Element.ELECTRIC,
    Element.FIRE,
    Element.PHYSICAL,
    Element.ICE,
    Element.WIND,
)
_ELEMENT_KEYS = ("ether", "electric", "fire", "physical", "ice", "wind")
_ELEMENT_LABELS = ("以太", "电", "火", "物理", "冰", "风")
_ENEMY_STUNNED = StateId("state:enemy:stunned")
_VOICE_STACKS = ScenarioParameterId("parameter:character:1511:voice-stacks")
_DANCE_STACKS = ScenarioParameterId("parameter:character:1511:dance-all-night-stacks")
_ETHER_DISORDER_REMAINING_HALF_SECONDS = ScenarioParameterId(
    "parameter:character:1511:ether-disorder-remaining-half-seconds"
)
_VOICE_DISCHARGE_READY = ScenarioConditionId(
    "condition:character:1511:voice-discharge-ready"
)
_VOICE_CHANGED_MODE = ScenarioConditionId(
    "condition:character:1511:voice-changed-mode"
)
_TARGET_HAS_ACTIVE_ANOMALY = ScenarioConditionId(
    "condition:character:1511:target-has-active-anomaly"
)
_CORE_STATUS_ACTIVE = ScenarioConditionId(
    "condition:character:1511:core-status-active"
)
_STUMBLE_ACTIVE = ScenarioConditionId("condition:character:1511:stumble-active")
_C1_RESISTANCE_REDUCTION_ACTIVE = ScenarioConditionId(
    "condition:character:1511:cinema1-resistance-reduction-active"
)
_C2_CHAIN_POLARITY_AVAILABLE = ScenarioConditionId(
    "condition:character:1511:cinema2-chain-polarity-available"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _one_number(text: str, pattern: str, label: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{label} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _core_rates(text: str) -> tuple[float, ...]:
    match = re.search(
        r"相对于原属性异常伤害的比例为\s*"
        r"(?P<ether>[\d.]+)%/(?P<electric>[\d.]+)%/(?P<fire>[\d.]+)%/"
        r"(?P<physical>[\d.]+)%/(?P<ice>[\d.]+)%/(?P<wind>[\d.]+)%",
        _plain(text),
    )
    if match is None:
        raise ValueError("Nangong Yu Core must contain all six typed Discharge ratios")
    return tuple(float(match.group(key)) / 100.0 for key in _ELEMENT_KEYS)


def _element_family_filter(element: Element):
    members = tuple(
        candidate
        for candidate, base_element in BASE_ELEMENT_BY_ELEMENT.items()
        if base_element is element
    )
    if not members:
        raise ValueError(f"No source element family for {element}")
    if len(members) == 1:
        return ElementFilter(element)
    return AnyFilter(tuple(ElementFilter(candidate) for candidate in members))


def _core_proficiency(text: str) -> float:
    return _one_number(
        text,
        r"异常精通提升\s*(?P<value>[\d.]+)\s*点",
        "Nangong Yu Core Anomaly Proficiency",
    )


def _core_current_bonuses(text: str) -> tuple[float, float, float]:
    match = re.search(
        r"属性异常积蓄效率提升\s*(?P<buildup>[\d.]+)%.*?"
        r"失衡值提升\s*(?P<daze>[\d.]+)%.*?"
        r"全队造成的伤害提升\s*(?P<damage>[\d.]+)%",
        _plain(text),
        re.DOTALL,
    )
    if match is None:
        raise ValueError("Nangong Yu Core must contain its three hit bonuses")
    return tuple(float(match.group(key)) / 100.0 for key in ("buildup", "daze", "damage"))


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("Nangong Yu raw record must contain all seven Core levels") from exc


def _raw_cinema(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"Nangong Yu raw record is missing Cinema {level}") from exc


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    text: str,
    *,
    value: bool = False,
    resolution: ConditionResolution = ConditionResolution.USER_SELECTED,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=resolution,
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
    not_conditions=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1511:{key}"),
        owner=NANGONGYU_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        condition_not_ids=tuple(not_conditions),
        effects=tuple(effects),
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
            effect_id=EffectId(f"effect:character:1511:{key}"),
            source=source,
            owner=NANGONGYU_ID,
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


def _validate_raw(raw: NanokaRawRecord, config: NangongYuCompileConfig) -> None:
    if raw.character_id != NANGONGYU_ID or raw.code_name != "NangongYu":
        raise ValueError("Nangong Yu compiler requires character:1511 code_name='NangongYu'")
    if raw.name != "南宫羽" or raw.specialty != "击破" or raw.element != "以太":
        raise ValueError("Nangong Yu raw identity must remain Stun/Ether")
    if raw.faction != "妄想天使" or raw.icon != "IconRole59" or raw.rarity != 4:
        raise ValueError("Nangong Yu raw identity fields do not match Nanoka source")
    if raw.source_version != "3.2" or not raw.source_url.endswith("/1511.json"):
        raise ValueError("Nangong Yu raw provenance must be the Nanoka 3.2 record")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Nangong Yu source must contain seven Core and six Cinema levels")
    _raw_core(raw, config.core_level)
    _raw_cinema(raw, 6)


def _static_ether_entries(raw: NanokaRawRecord):
    anomaly_id = AnomalyRecordId(NANGONGYU_ETHER_ANOMALY_RECORD_ID)
    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1511:ether-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1511:ether-anomaly"),
        label="属性异常：侵蚀（单跳62.5%，最多20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ETHER,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=NANGONGYU_ID,
        element=Element.ETHER,
        anomaly_triggerer=NANGONGYU_ID,
        history_record_source=anomaly_id,
        crit_rule=NoCritRule(),
        move_id=None,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1511:ether-anomaly"),
        character_id=NANGONGYU_ID,
        move_id=None,
        display_name=anomaly_ref.label,
        original_text=(
            "南宫羽为击破角色；按100%以太异常记录展示侵蚀，规范单跳62.5%，最多20跳。"
            "不模拟异常积蓄或战斗时间轴。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1511:ether-anomaly-tick"),
                label="侵蚀单跳倍率 × 20",
                parameter_name="侵蚀单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.625)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1511:ether-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1511:ether-disorder"),
        label="紊乱：侵蚀（按当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ETHER,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=NANGONGYU_ID,
        element=Element.ETHER,
        disorder_triggerer=NANGONGYU_ID,
        history_record_source=anomaly_id,
        crit_rule=NoCritRule(),
        move_id=None,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1511:ether-disorder"),
        character_id=NANGONGYU_ID,
        move_id=None,
        display_name=disorder_ref.label,
        original_text=(
            "以太紊乱倍率为450% + floor(t/0.5) × 62.5%；t为当前异常剩余时间，"
            "范围0–10秒，不模拟时间轴。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1511:ether-disorder"),
                label="450% + 当前剩余半秒数 × 62.5%",
                parameter_name="以太紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_ETHER_DISORDER_REMAINING_HALF_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.625,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_ETHER_DISORDER_REMAINING_HALF_SECONDS,
        label="以太异常当前剩余半秒数",
        original_text="以太异常持续时间最多10秒；按当前静态剩余时间输入，不模拟时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=20,
        minimum=0,
        maximum=20,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _discharge_contract(raw: NanokaRawRecord, *, core_level: int):
    core = _raw_core(raw, core_level)
    normal_rates = _core_rates(core.description)
    changed_rates = _core_rates(_raw_cinema(raw, 6).description)
    core_rule_id = RuleItemId("rule:character:1511:core:voice-discharge")
    core_source = source_for(
        NANGONGYU_ID,
        "core:voice-discharge",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    changed_source = source_for(
        NANGONGYU_ID,
        "cinema6:changed-voice-discharge",
        EffectSourceType.CINEMA,
        _raw_cinema(raw, 6).name,
        _raw_cinema(raw, 6).description,
    )
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1511:core:voice-discharge"),
        semantic_id=DamageEventSemanticId("event:character:1511:core:voice-discharge"),
        label="颤音异放（按当前所选原异常记录）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        # The selected source record supplies the actual element at execution.
        # This placeholder is replaced by the generic dynamic Discharge chooser.
        element=Element.ETHER,
        source_rule_item_id=core_rule_id,
    )
    template = DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=NANGONGYU_ID,
        element=Element.ETHER,
        discharge_triggerer=NANGONGYU_ID,
        history_record_source=None,
        crit_rule=NoCritRule(),
        move_id=None,
        multiplier_from_source_event=False,
        source_multiplier_uses_tick_profile=True,
        source_multiplier_by_element=tuple(zip(_DISCHARGE_ELEMENTS, normal_rates)),
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1511:core:voice-discharge"),
        character_id=NANGONGYU_ID,
        move_id=None,
        display_name=ref.label,
        original_text=(
            f"{core.description} 仅在当前已选择颤音清除异放状态、目标仍处于属性异常时，"
            "由本条独立查询并显式选择原异常记录；不由普通异常事件自动触发，也不回放清除时序。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1511:core:voice-discharge"
                ),
                label="按所选原异常记录倍率",
                parameter_name="颤音异放倍率",
                multiplier=FixedMultiplier(Resolved(1.0)),
            ),
        ),
        main_damage_event=ref,
        condition_ids=(_VOICE_DISCHARGE_READY, _TARGET_HAS_ACTIVE_ANOMALY),
    )
    return core_source, changed_source, entry, template, normal_rates, changed_rates


def _polar_event(
    *,
    key: str,
    label: str,
    source: RuleSource,
    rule_key: str,
):
    rule_id = RuleItemId(f"rule:character:1511:{rule_key}")
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1511:{key}"),
        semantic_id=DamageEventSemanticId(f"event:character:1511:{key}"),
        label=label,
        damage_type=DamageType.DISORDER,
        element=None,
        source_rule_item_id=rule_id,
    )
    template = PolarDisorderDamageEventTemplate(
        ref=ref,
        damage_dealer=NANGONGYU_ID,
        disorder_triggerer=NANGONGYU_ID,
        element=None,
        base_polarity_multiplier=0.25,
        anomaly_proficiency_coefficient=0.0,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
    return ref, template, derived


def _event_creation(
    *,
    key: str,
    source: RuleSource,
    template: DamageEventTemplateRef,
    filters,
    condition=None,
):
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1511:{key}"),
            source=source,
            owner=NANGONGYU_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template.template_id,
            unique_per_source_event=True,
        ),
    )
def compile_nangongyu(
    config: NangongYuCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = NANGONGYU_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=NANGONGYU_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="character:1511",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        NANGONGYU_ID,
        f"core-{config.core_level}",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_proficiency = _core_proficiency(core.description)
    mastery_effects = [
        _modifier(
            "core:anomaly-mastery",
            core_source,
            CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
            Resolved(core_proficiency),
            target=EffectTarget.SELF,
        ),
        _modifier(
            "core:impact-from-initial-anomaly-mastery",
            core_source,
            CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
            PanelStatDerivedValue(
                source_character_id=NANGONGYU_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
                coefficient=Resolved(1.0),
                threshold=Resolved(110.0),
                step_size=Resolved(1.0),
            ),
            target=EffectTarget.SELF,
        ),
    ]
    core_mastery_rule = _rule(
        "core:mastery-and-impact",
        core_source,
        f"核心被动：异常精通+{core_proficiency:g}；初始异常掌控超过110时提升冲击力",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=mastery_effects,
    )

    anomaly_entries, static_templates, disorder_remaining = _static_ether_entries(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(static_templates)
    parameters = [
        disorder_remaining,
        ScenarioIntegerParameter(
            parameter_id=_VOICE_STACKS,
            label="本次颤音异放清除时的层数",
            original_text="同一目标最多4层；普通颤音与6影颤音：改互斥，共用本次清除时的层数输入，不模拟叠层或清除时序。",
            resolution=ParameterResolution.USER_SELECTED,
            value=4,
            minimum=1,
            maximum=4,
        ),
    ]
    conditions = [
        _condition(
            _VOICE_DISCHARGE_READY,
            "颤音已清除且触发异放的当前状态成立",
            core.description,
        ),
        _condition(
            _VOICE_CHANGED_MODE,
            "当前使用6影颤音：改",
            _raw_cinema(raw_record, 6).description,
            resolution=(
                ConditionResolution.USER_SELECTED
                if config.cinema_level >= 6
                else ConditionResolution.STATIC
            ),
        ),
        _condition(
            _TARGET_HAS_ACTIVE_ANOMALY,
            "目标当前处于属性异常状态",
            core.description,
        ),
        _condition(
            _CORE_STATUS_ACTIVE,
            "核心被动命中后全队增伤状态当前生效",
            core.description,
        ),
        _condition(
            _STUMBLE_ACTIVE,
            "踉跄状态当前生效",
            raw_record.extra_ability_description,
        ),
        _condition(
            _C1_RESISTANCE_REDUCTION_ACTIVE,
            "1影全属性抗性降低状态当前生效",
            _raw_cinema(raw_record, 1).description,
        ),
    ]
    (
        normal_source,
        changed_source,
        discharge_entry,
        discharge_template,
        normal_rates,
        changed_rates,
    ) = _discharge_contract(raw_record, core_level=config.core_level)
    entries.append(discharge_entry)
    templates.append(discharge_template)

    discharge_common_conditions = (
        _VOICE_DISCHARGE_READY,
        _TARGET_HAS_ACTIVE_ANOMALY,
    )
    discharge_filters = (
        DamageDealerFilter(NANGONGYU_ID),
        DamageTypeFilter(DamageType.ANOMALY),
        DamageSubtypeFilter(DamageSubtype.DISCHARGE),
        EventTemplateIdFilter(discharge_template.ref.template_id),
    )
    normal_rate_effects = tuple(
        _modifier(
            f"core:voice-discharge:stack-ratio:{element.value.replace(':', '-')}",
            normal_source,
            CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
            ScenarioParameterDerivedValue(
                parameter_id=str(_VOICE_STACKS),
                base=Resolved(1.0),
                coefficient=Resolved(0.25),
            ),
            target=EffectTarget.TEAM,
            filters=(*discharge_filters, _element_family_filter(element)),
        )
        for element in _DISCHARGE_ELEMENTS
    )
    rules = [
        core_mastery_rule,
        _rule(
            "core:voice-discharge",
            normal_source,
            "核心被动：颤音异放（显式选择原异常记录）",
            _raw_core(raw_record, config.core_level).description,
            RuleEligibility.ELIGIBLE,
            effects=normal_rate_effects,
            conditions=discharge_common_conditions,
            not_conditions=(_VOICE_CHANGED_MODE,),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        ),
    ]
    core_discharge_rule_id = RuleItemId(
        "rule:character:1511:core:voice-discharge"
    )
    rules.append(
        _rule(
            "core:voice-discharge-disabled-guard",
            normal_source,
            "核心颤音异放规则关闭时不能按无加成倍率结算",
            _raw_core(raw_record, config.core_level).description,
            RuleEligibility.ELIGIBLE,
            effects=(
                UnresolvedEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1511:core:voice-discharge-disabled-guard"
                        ),
                        source=normal_source,
                        owner=NANGONGYU_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=NotCondition(
                            RuleStackCondition(
                                str(core_discharge_rule_id),
                                required_value=1,
                                requires_rule_enabled=True,
                            )
                        ),
                        filters=discharge_filters,
                    ),
                    unresolved=Unresolved(
                        reason=UnresolvedReason.MISSING_SPEC_RULE,
                        notes=(
                            "The current request selects Nangong Yu's normal Voice Discharge, "
                            "but its Core rule is disabled. The source ratio cannot be reported as a complete result without the per-stack ratio effect."
                        ),
                        original_text=_raw_core(raw_record, config.core_level).description,
                    ),
                ),
            ),
            conditions=discharge_common_conditions,
            not_conditions=(_VOICE_CHANGED_MODE,),
        )
    )
    changed_rule_id = RuleItemId(
        "rule:character:1511:cinema6:changed-voice-discharge"
    )
    changed_rate_effects = []
    for element, normal_ratio, changed_ratio in zip(
        _DISCHARGE_ELEMENTS, normal_rates, changed_rates
    ):
        relative_ratio = changed_ratio / normal_ratio
        changed_rate_effects.append(
            _modifier(
                f"cinema6:changed-voice-discharge:stack-ratio:{element.value.replace(':', '-')}",
                changed_source,
                CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
                ScenarioParameterDerivedValue(
                    parameter_id=str(_VOICE_STACKS),
                    base=Resolved(relative_ratio),
                    coefficient=Resolved(relative_ratio * 0.25),
                ),
                target=EffectTarget.TEAM,
                filters=(*discharge_filters, _element_family_filter(element)),
            )
        )
    changed_rule_eligible = config.cinema_level >= 6
    rules.append(
        _rule(
            "cinema6:changed-voice-discharge",
            changed_source,
            "6影：颤音：改异放（替换普通颤音）",
            _raw_cinema(raw_record, 6).description,
            RuleEligibility.ELIGIBLE
            if changed_rule_eligible
            else RuleEligibility.INELIGIBLE,
            effects=tuple(changed_rate_effects),
            conditions=(*discharge_common_conditions, _VOICE_CHANGED_MODE),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )
    if changed_rule_eligible:
        rules.append(
            _rule(
                "cinema6:changed-voice-disabled-guard",
                changed_source,
                "6影颤音：改异放规则关闭时不能按普通颤音结算",
                _raw_cinema(raw_record, 6).description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    UnresolvedEffect(
                        rule=EffectRule(
                            effect_id=EffectId(
                                "effect:character:1511:cinema6:changed-voice-disabled-guard"
                            ),
                            source=changed_source,
                            owner=NANGONGYU_ID,
                            target=EffectTarget.TEAM,
                            snapshot_rule=SnapshotRule.SETTLEMENT,
                            condition=NotCondition(
                                RuleStackCondition(
                                    str(changed_rule_id),
                                    required_value=1,
                                    requires_rule_enabled=True,
                                )
                            ),
                            filters=discharge_filters,
                        ),
                        unresolved=Unresolved(
                            reason=UnresolvedReason.MISSING_SPEC_RULE,
                            notes=(
                                "The current request selects Nangong Yu's Cinema 6 changed-Voice Discharge, "
                                "but its rule is disabled. The changed source ratio cannot be replaced with the normal-Voice ratio."
                            ),
                            original_text=_raw_cinema(raw_record, 6).description,
                        ),
                    ),
                ),
                conditions=(*discharge_common_conditions, _VOICE_CHANGED_MODE),
            )
        )
    cinema2 = _raw_cinema(raw_record, 2)
    c2_source = source_for(
        NANGONGYU_ID,
        "cinema2:voice-ratio-and-polarity",
        EffectSourceType.CINEMA,
        cinema2.name,
        cinema2.description,
    )
    c2_ratio_effects = tuple(
        _modifier(
            f"cinema2:normal-voice-ratio:{element.value.replace(':', '-')}",
            c2_source,
            CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
            ScenarioParameterDerivedValue(
                parameter_id=str(_VOICE_STACKS),
                base=Resolved(0.0),
                coefficient=Resolved(0.10),
            ),
            target=EffectTarget.TEAM,
            filters=(*discharge_filters, _element_family_filter(element)),
        )
        for element in _DISCHARGE_ELEMENTS
    )
    rules.append(
        _rule(
            "cinema2:normal-voice-ratio",
            c2_source,
            "2影：每层普通颤音使异放比例额外提升10%",
            cinema2.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=tuple(c2_ratio_effects),
            conditions=discharge_common_conditions,
            not_conditions=(_VOICE_CHANGED_MODE,),
        )
    )

    core_mastery_rule_source = core_source
    core_bonus_text = core.description
    current_bonus_values = _core_current_bonuses(core_bonus_text)
    mastery_extra = _modifier(
        "core:team-current-damage-bonus",
        core_mastery_rule_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(current_bonus_values[2]),
        target=EffectTarget.TEAM,
    )
    rules.append(
        _rule(
            "core:team-current-damage-bonus",
            core_mastery_rule_source,
            f"核心被动命中状态：全队普通增伤+{current_bonus_values[2]:.0%}",
            core_bonus_text,
            RuleEligibility.ELIGIBLE,
            effects=(mastery_extra,),
            conditions=(_CORE_STATUS_ACTIVE,),
        )
    )

    cinema1 = _raw_cinema(raw_record, 1)
    c1_source = source_for(
        NANGONGYU_ID,
        "cinema1:resistance-reduction",
        EffectSourceType.CINEMA,
        cinema1.name,
        cinema1.description,
    )
    c1_resistance = _one_number(
        cinema1.description,
        r"全属性伤害抗性降低(?P<value>[\d.]+)%",
        "Nangong Yu Cinema 1 resistance reduction",
    ) / 100.0
    rules.append(
        _rule(
            "cinema1:resistance-reduction",
            c1_source,
            f"1影：全属性伤害抗性降低{c1_resistance:.0%}",
            cinema1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:resistance-reduction",
                    c1_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(c1_resistance),
                    target=EffectTarget.ENEMY,
                ),
            ),
            conditions=(_C1_RESISTANCE_REDUCTION_ACTIVE,),
        )
    )

    cinema4 = _raw_cinema(raw_record, 4)
    c4_proficiency = _one_number(
        cinema4.description,
        r"异常精通提升\s*(?P<value>[\d.]+)\s*点",
        "Nangong Yu Cinema 4 Anomaly Proficiency",
    )
    c4_source = source_for(
        NANGONGYU_ID,
        "cinema4:anomaly-mastery",
        EffectSourceType.CINEMA,
        cinema4.name,
        cinema4.description,
    )
    rules.append(
        _rule(
            "cinema4:anomaly-mastery",
            c4_source,
            f"4影：异常精通+{c4_proficiency:g}",
            cinema4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:anomaly-mastery",
                    c4_source,
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    Resolved(c4_proficiency),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )
    extra_source = source_for(
        NANGONGYU_ID,
        "extra-ability:stumble-vulnerability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligible = config.additional_ability_eligible
    extra_vulnerability_text = raw_record.extra_ability_description
    stumble_bonus = 0.30
    rules.append(
        _rule(
            "extra-ability:stumble-vulnerability",
            extra_source,
            "额外能力：踉跄使失衡易伤倍率提升30%",
            extra_vulnerability_text,
            RuleEligibility.ELIGIBLE if extra_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "extra-ability:stumble-vulnerability",
                    extra_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(stumble_bonus),
                    target=EffectTarget.ENEMY,
                ),
            ),
            conditions=(_STUMBLE_ACTIVE,),
        )
    )
    rules.extend(
        (
            _rule(
                "cinema2:stumble-vulnerability",
                c2_source,
                "2影：踉跄期间失衡易伤倍率额外提升30%",
                cinema2.description,
                RuleEligibility.ELIGIBLE
                if extra_eligible and config.cinema_level >= 2
                else RuleEligibility.INELIGIBLE,
                effects=(
                    _modifier(
                        "cinema2:stumble-vulnerability",
                        c2_source,
                        CalculationNode.ENEMY_STUN_VULNERABILITY,
                        Resolved(0.30),
                        target=EffectTarget.ENEMY,
                    ),
                ),
                conditions=(_STUMBLE_ACTIVE,),
            ),
            _rule(
                "cinema3:skill-levels",
                source_for(
                    NANGONGYU_ID,
                    "cinema3:skill-levels",
                    EffectSourceType.CINEMA,
                    _raw_cinema(raw_record, 3).name,
                    _raw_cinema(raw_record, 3).description,
                ),
                "3影：技能等级+2",
                _raw_cinema(raw_record, 3).description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 3
                else RuleEligibility.INELIGIBLE,
            ),
            _rule(
                "cinema5:skill-levels",
                source_for(
                    NANGONGYU_ID,
                    "cinema5:skill-levels",
                    EffectSourceType.CINEMA,
                    _raw_cinema(raw_record, 5).name,
                    _raw_cinema(raw_record, 5).description,
                ),
                "5影：技能等级+2",
                _raw_cinema(raw_record, 5).description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 5
                else RuleEligibility.INELIGIBLE,
            ),
        )
    )

    # This is the selected current proc fact for the active Chain Attack hit;
    # it does not replay hit timing or prior triggers during a Stun window.
    conditions.append(
        _condition(
            _C2_CHAIN_POLARITY_AVAILABLE,
            "本次连携重击命中且当前失衡尚可触发2影极性紊乱",
            cinema2.description,
            value=True,
        )
    )
    parameters.append(
        ScenarioIntegerParameter(
            parameter_id=_DANCE_STACKS,
            label="当前舞力全开层数",
            original_text="舞力全开最多2层；按当前剩余层数输入，不模拟获得、消耗或持续时间。",
            resolution=ParameterResolution.USER_SELECTED,
            value=2 if extra_eligible else 0,
            minimum=0,
            maximum=2,
        )
    )
    extra_dance_condition = ScenarioParameterRangeCondition(
        parameter_id=str(_DANCE_STACKS), minimum=1, maximum=2
    )

    own_extra_sources = tuple(
        entry.main_damage_event.template_id
        for entry in entries
        if str(entry.entry_id).endswith(
            (
                ":basic-charge-strike-1",
                ":basic-charge-strike-2",
                ":basic-charge-strike-3",
                ":basic-charge-strike-3-cooperative",
                ":ex-special",
                ":quick-assist",
            )
        )
    )
    polar_templates = []
    polar_derived = []
    if own_extra_sources:
        extra_polar_ref, extra_polar_template, extra_polar_derived = _polar_event(
            key="extra-ability:polar-disorder",
            label="额外能力：舞力全开触发极性紊乱",
            source=extra_source,
            rule_key="extra-ability:polar-disorder",
        )
        polar_templates.append(extra_polar_template)
        polar_derived.append(extra_polar_derived)
        extra_polar_creation = _event_creation(
            key="extra-ability:polar-disorder",
            source=extra_source,
            template=extra_polar_ref,
            filters=(
                DamageDealerFilter(NANGONGYU_ID),
                DamageTypeFilter(DamageType.DIRECT),
                AnyFilter(tuple(EventTemplateIdFilter(item) for item in own_extra_sources)),
                EnemyStateFilter(_ENEMY_STUNNED),
            ),
            condition=extra_dance_condition,
        )
        rules.append(
            _rule(
                "extra-ability:polar-disorder",
                extra_source,
                "额外能力：舞力全开期间重击触发极性紊乱",
                raw_record.extra_ability_description,
                RuleEligibility.ELIGIBLE if extra_eligible else RuleEligibility.INELIGIBLE,
                effects=(extra_polar_creation,),
                conditions=(_TARGET_HAS_ACTIVE_ANOMALY,),
            )
        )

    # Cinema 2's one-per-stun Chain trigger is scoped to the active operator's
    # direct Chain Attack event. It does not inherit the parent move's tags.
    c2_chain_ref, c2_chain_template, c2_chain_derived = _polar_event(
        key="cinema2:chain-polar-disorder",
        label="2影：操作中角色连携技极性紊乱",
        source=c2_source,
        rule_key="cinema2:chain-polar-disorder",
    )
    polar_templates.append(c2_chain_template)
    polar_derived.append(c2_chain_derived)
    c2_chain_creation = _event_creation(
        key="cinema2:chain-polar-disorder",
        source=c2_source,
        template=c2_chain_ref,
        filters=(
            DamageDealerIdentityFilter(DynamicIdentity.CURRENT_OPERATOR),
            DamageTypeFilter(DamageType.DIRECT),
            DamageTagFilter(DamageTag.CHAIN_ATTACK),
            EnemyStateFilter(_ENEMY_STUNNED),
        ),
    )
    rules.append(
        _rule(
            "cinema2:chain-polar-disorder",
            c2_source,
            "2影：操作中角色连携技重击触发极性紊乱（每次失衡一次）",
            cinema2.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=(c2_chain_creation,),
            conditions=(_TARGET_HAS_ACTIVE_ANOMALY, _C2_CHAIN_POLARITY_AVAILABLE),
        )
    )

    if config.aria_in_team and extra_eligible:
        aria_source_templates = tuple(
            EventTemplateId(value)
            for value in (
                "template:character:1501:basic-absolute-pitch-charge-3:main",
                "template:character:1501:basic-absolute-pitch-charge-3-cooperative:main",
                "template:character:1501:basic-absolute-pitch-enhanced:main",
            )
        )
        aria_full_participation = ScenarioConditionId(
            "condition:character:1511:aria-full-participation"
        )
        conditions.append(
            _condition(
                aria_full_participation,
                "南宫羽完整参与爱芮本次绝对音准攻击",
                raw_record.extra_ability_description,
            )
        )
        aria_polar_ref, aria_polar_template, aria_polar_derived = _polar_event(
            key="extra-ability:aria-polar-disorder",
            label="爱芮绝对音准：南宫羽协同极性紊乱",
            source=extra_source,
            rule_key="extra-ability:aria-polar-disorder",
        )
        polar_templates.append(aria_polar_template)
        polar_derived.append(aria_polar_derived)
        aria_creation = _event_creation(
            key="extra-ability:aria-polar-disorder",
            source=extra_source,
            template=aria_polar_ref,
            filters=(
                DamageDealerFilter(CharacterId("character:1501")),
                DamageTypeFilter(DamageType.DIRECT),
                AnyFilter(tuple(EventTemplateIdFilter(item) for item in aria_source_templates)),
                EnemyStateFilter(_ENEMY_STUNNED),
            ),
            condition=extra_dance_condition,
        )
        rules.append(
            _rule(
                "extra-ability:aria-polar-disorder",
                extra_source,
                "额外能力：爱芮绝对音准协同触发极性紊乱",
                raw_record.extra_ability_description,
                RuleEligibility.ELIGIBLE,
                effects=(aria_creation,),
                conditions=(_TARGET_HAS_ACTIVE_ANOMALY, aria_full_participation),
            )
        )
    return build_definition(
        character_id=NANGONGYU_ID,
        role=CharacterRole.STUN,
        element=Element.ETHER,
        source=core_source,
        entries=tuple(entries),
        templates=(*templates, *polar_templates),
        rules=tuple(rules),
        conditions=tuple(conditions),
        parameters=tuple(parameters),
        independent_derived_damage_events=(
            *polar_derived,
        ),
        diagnostics=tuple(diagnostics),
    )


__all__ = ["compile_nangongyu"]
