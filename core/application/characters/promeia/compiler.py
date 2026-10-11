"""Compile Promeia's reviewed Nanoka 3.2 source into static damage contracts."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CreatedByEffectFilter,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
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
    SnapshotRule,
    StandardCritRule,
    SkillGroup,
    Unresolved,
    UnresolvedEffect,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic
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
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import NanokaRawMoveRecord, NanokaRawRecord
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DischargeDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import PROMEIA_ID, PromeiaCompileConfig
from .reviewed import (
    PROMEIA_ICE_ANOMALY_MOVE_ID,
    PROMEIA_ICE_DISORDER_MOVE_ID,
    PROMEIA_REVIEWED_MAPPING,
)


_ELEMENTS = (
    Element.ETHER,
    Element.ELECTRIC,
    Element.FIRE,
    Element.PHYSICAL,
    Element.ICE,
    Element.WIND,
)
_CORE_EX_FINISHER_TEMPLATE = EventTemplateId(
    "template:character:1541:ex-judgment:main"
)
_CHAIN_TEMPLATE = EventTemplateId(
    "template:character:1541:chain-hanging-reckoning:main"
)
_ULTIMATE_TEMPLATE = EventTemplateId(
    "template:character:1541:ultimate-bone-punishment:main"
)
_CORE_DISCHARGE_RULE_ID = RuleItemId("rule:character:1541:core:discharge")
_CHAIN_DISCHARGE_RULE_ID = RuleItemId("rule:character:1541:chain:discharge")
_ULTIMATE_DISCHARGE_RULE_ID = RuleItemId("rule:character:1541:ultimate:discharge")
_C6_DISCHARGE_RULE_ID = RuleItemId("rule:character:1541:cinema6:extra-discharge")
_CORE_DISCHARGE_CREATION_ID = EffectId(
    "effect:character:1541:core:discharge-creation"
)
_CHAIN_DISCHARGE_CREATION_ID = EffectId(
    "effect:character:1541:chain:discharge-creation"
)
_ULTIMATE_DISCHARGE_CREATION_ID = EffectId(
    "effect:character:1541:ultimate:discharge-creation"
)
_C6_DISCHARGE_CREATION_ID = EffectId(
    "effect:character:1541:cinema6:extra-discharge-creation"
)
_TARGET_HAS_ANOMALY = ScenarioConditionId(
    "condition:character:1541:target-has-anomaly"
)
_FROST_CONSUMED = ScenarioConditionId(
    "condition:character:1541:current-action-consumes-frost-punishment"
)
_VERDICT_ACTIVE = ScenarioConditionId(
    "condition:character:1541:verdict-active"
)
_ICE_BURN_ACTIVE = ScenarioConditionId(
    "condition:character:1541:ice-buildup-bonus-active"
)
_ICE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:character:1541:ice-disorder-remaining-seconds"
)
_ICE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1541:ice-frost-chill")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _single_number(text: str, pattern: str, label: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{label} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _core_ratio(text: str) -> float:
    return _single_number(
        text,
        r"固定结算\s*(?P<value>[\d.]+)%倍率的对应属性的属性异常伤害",
        "Promeia Core fixed type-2 Discharge multiplier",
    ) / 100.0


def _discharge_ratio(text: str, label: str) -> float:
    return _single_number(
        text,
        r"结算一次\s*(?P<value>[\d.]+)%倍率的对应属性的属性异常伤害",
        label,
    ) / 100.0


def _raw_move(raw: NanokaRawRecord, name: str) -> NanokaRawMoveRecord:
    try:
        return next(item for item in raw.moves if item.name == name)
    except StopIteration as exc:
        raise ValueError(f"Promeia raw record is missing move {name}") from exc


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("Promeia raw record must contain all seven Core levels") from exc


def _raw_cinema(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"Promeia raw record is missing Cinema {level}") from exc


def _validate_raw(raw: NanokaRawRecord, config: PromeiaCompileConfig) -> None:
    if raw.character_id != PROMEIA_ID:
        raise ValueError("Promeia compiler requires character:1541")
    if (
        raw.name != "普罗米娅"
        or raw.code_name != "Promeia"
        or raw.rarity != 4
        or raw.specialty != "异常"
        or raw.element != "冰属性"
        or raw.faction != "坎卜斯黑枝"
        or raw.icon != "IconRole61"
    ):
        raise ValueError("Promeia raw identity does not match reviewed Nanoka source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1541.json"
    ):
        raise ValueError("Promeia source provenance must be the Nanoka live 3.2 record")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Promeia raw record must contain seven Core and six Cinema levels")
    _raw_core(raw, config.core_level)
    _raw_cinema(raw, 6)


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    original_text: str,
    *,
    value: bool = False,
) -> ScenarioCondition:
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
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1541:{key}"),
        owner=PROMEIA_ID,
        source=source,
        display_name=label,
        original_text=original_text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        effects=tuple(effects),
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
            effect_id=EffectId(f"effect:character:1541:{key}"),
            source=source,
            owner=PROMEIA_ID,
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


def _event_creation(
    *,
    effect_id: EffectId,
    source: RuleSource,
    source_template_id: EventTemplateId,
    result_template_id: EventTemplateId,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=source,
            owner=PROMEIA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(EventTemplateIdFilter(source_template_id),),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=result_template_id,
            unique_per_source_event=True,
        ),
    )


def _make_discharge(
    *,
    key: str,
    label: str,
    ratio: float,
    source_rule_id: RuleItemId,
) -> tuple[DischargeDamageEventTemplate, DerivedDamageEventTemplateRef]:
    template_id = EventTemplateId(f"template:character:1541:{key}")
    semantic_id = DamageEventSemanticId(f"event:character:1541:{key}")
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label=label,
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        element=Element.ICE,
        source_rule_item_id=source_rule_id,
    )
    template = DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=PROMEIA_ID,
        element=Element.ICE,
        discharge_triggerer=PROMEIA_ID,
        history_record_source=None,
        crit_rule=NoCritRule(),
        move_id=None,
        multiplier_from_source_event=False,
        source_multiplier_by_element=tuple((element, 1.0) for element in _ELEMENTS),
        source_multiplier_uses_tick_profile=False,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(ratio)),
    )
    return template, derived


def _neutral_direct_query(
    *,
    raw_record: NanokaRawRecord,
    config: PromeiaCompileConfig,
    source_name: str,
    parameter_name: str,
    source_skill_id: str,
    key: str,
    display_name: str,
    skill_group: SkillGroup,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate, tuple[CalculationDiagnostic, ...]]:
    raw_moves = {item.name: item for item in raw_record.moves}
    diagnostics: list[CalculationDiagnostic] = []
    level = effective_skill_level(config, skill_group)
    multiplier = raw_multiplier(
        raw_moves,
        source_name,
        parameter_name,
        level,
        f"{PROMEIA_ID}:{key}",
        diagnostics,
        source_skill_id,
    )
    variant_multiplier = (
        multiplier
        if isinstance(multiplier, Unresolved)
        else FixedMultiplier(Resolved(multiplier))
    )
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1541:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1541:{key}:main"),
        label=display_name,
        damage_type=DamageType.DIRECT,
        element=Element.ICE,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=PROMEIA_ID,
        element=Element.ICE,
        base_source=CurrentAttackValueSource(PROMEIA_ID),
        crit_rule=StandardCritRule(PROMEIA_ID),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1541:{key}"),
        character_id=PROMEIA_ID,
        move_id=None,
        display_name=display_name,
        original_text=_raw_move(raw_record, source_name).description,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1541:{key}"),
                label=parameter_name,
                parameter_name=parameter_name,
                multiplier=variant_multiplier,
            ),
        ),
        main_damage_event=ref,
        diagnostics=tuple(diagnostics),
    )
    return entry, template, tuple(diagnostics)


def _static_ice_entries(
    config: PromeiaCompileConfig,
) -> tuple[tuple[MoveCalculationEntry, ...], tuple[object, ...], ScenarioIntegerParameter]:
    """Expose the standard Ice anomaly and Disorder records for source choice."""

    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1541:ice-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1541:ice-anomaly"),
        label="属性异常：霜寒（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=PROMEIA_ID,
        element=Element.ICE,
        anomaly_triggerer=PROMEIA_ID,
        history_record_source=_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PROMEIA_ICE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1541:ice-anomaly"),
        character_id=PROMEIA_ID,
        move_id=PROMEIA_ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：霜寒（10秒满异常）",
        original_text="标准冰属性异常：10秒剩余时间结算异常效果强度500%，不模拟异常积蓄时间。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1541:ice-anomaly"),
                label="霜寒500%（10秒）",
                parameter_name="霜寒倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1541:ice-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1541:ice-disorder"),
        label="紊乱：霜寒（按剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=PROMEIA_ID,
        element=Element.ICE,
        disorder_triggerer=PROMEIA_ID,
        history_record_source=_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PROMEIA_ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1541:ice-disorder"),
        character_id=PROMEIA_ID,
        move_id=PROMEIA_ICE_DISORDER_MOVE_ID,
        display_name="紊乱：霜寒（默认最大剩余时间）",
        original_text="标准冰属性紊乱：基础450% + floor(t)×7.5%；t为剩余秒数，默认按当前霜寒持续时间。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1541:ice-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="霜寒紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_ICE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    duration = 13 if config.additional_ability_eligible else 10
    remaining = ScenarioIntegerParameter(
        parameter_id=_ICE_DISORDER_REMAINING_SECONDS,
        label="霜寒紊乱时目标剩余持续时间（秒）",
        original_text=f"按当前霜寒记录选择0–{duration}秒；未手动设置时默认{duration}秒。",
        resolution=ParameterResolution.USER_SELECTED,
        value=duration,
        minimum=0,
        maximum=duration,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def compile_promeia(
    config: PromeiaCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = PROMEIA_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=PROMEIA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="character:1541",
    )
    entries = list(direct_entries)
    templates: list[object] = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    static_ice_entries, static_ice_templates, ice_disorder_remaining = (
        _static_ice_entries(config)
    )
    entries.extend(static_ice_entries)
    templates.extend(static_ice_templates)

    # These curves are known, but the source does not assign them the parent
    # move's tags or a total number of repeats. Keep each as a one-query neutral
    # event instead of inventing inherited identity or duration.
    cape_entry, cape_template, cape_diagnostics = _neutral_direct_query(
        raw_record=raw_record,
        config=config,
        source_name="普通攻击：偏锋",
        parameter_name="披风切割每秒伤害倍率",
        source_skill_id="1541008",
        key="cape-cut-per-second",
        display_name="镣锁赦罪：披风切割（每秒）",
        skill_group=SkillGroup.BASIC_ATTACK,
    )
    dart_entry, dart_template, dart_diagnostics = _neutral_direct_query(
        raw_record=raw_record,
        config=config,
        source_name="特殊技：处刑式·重霜",
        parameter_name="飞镖切割总伤害倍率",
        source_skill_id="1541012",
        key="heavy-frost-dart-cut",
        display_name="特殊技：处刑式·重霜（飞镖切割独立查询）",
        skill_group=SkillGroup.SPECIAL_ATTACK,
    )
    entries.extend((cape_entry, dart_entry))
    templates.extend((cape_template, dart_template))
    diagnostics.extend(cape_diagnostics)
    diagnostics.extend(dart_diagnostics)

    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        PROMEIA_ID,
        f"core-{config.core_level}",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    initial_mastery_coefficient = _single_number(
        core.description,
        r"每超过1点初始异常掌控会提升自身(?P<value>[\d.]+)点异常精通",
        "Promeia Core initial-mastery proficiency coefficient",
    )
    team_discharge_per_mastery = _single_number(
        core.description,
        r"提升自身[\d.]+点异常精通，提升(?P<value>[\d.]+)%全队造成的.*?伤害",
        "Promeia Core team Discharge bonus coefficient",
    ) / 100.0
    ap_value = PanelStatDerivedValue(
        source_character_id=PROMEIA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
        coefficient=Resolved(initial_mastery_coefficient),
        threshold=Resolved(150.0),
    )
    team_discharge_value = PanelStatDerivedValue(
        source_character_id=PROMEIA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
        coefficient=Resolved(team_discharge_per_mastery),
        threshold=Resolved(150.0),
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:panel-bonuses",
            core_source,
            "核心被动：初始掌控超过150点时提升自身异常精通与全队异放伤害",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:initial-mastery-to-proficiency",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    ap_value,
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    "core:initial-mastery-team-discharge-bonus",
                    core_source,
                    CalculationNode.DISCHARGE_DAMAGE_BONUS,
                    team_discharge_value,
                    target=EffectTarget.TEAM,
                    filters=(DamageSubtypeFilter(DamageSubtype.DISCHARGE),),
                ),
            ),
        )
    ]
    conditions = [
        _condition(
            _TARGET_HAS_ANOMALY,
            "本次招式命中当前处于任意属性异常状态的目标",
            "Chain / Ultimate source text requires the terminal hit to hit one of the six active attribute-anomaly states.",
        ),
        _condition(
            _FROST_CONSUMED,
            "本次绝裁发动时消耗1点霜刑",
            _raw_core(raw_record, config.core_level).description,
        ),
        _condition(
            _VERDICT_ACTIVE,
            "目标当前处于有罪推定状态",
            raw_record.extra_ability_description,
        ),
        _condition(
            _ICE_BURN_ACTIVE,
            "普罗米娅当前冰异常积蓄效率提升有效",
            raw_record.extra_ability_description,
        ),
    ]

    # Exact current-hit templates prevent an arbitrary existing anomaly record
    # from creating Core, Chain, or Ultimate Discharge on its own.
    core_ratio = _core_ratio(core.description)
    core_template, core_derived = _make_discharge(
        key="core-frost-consuming-discharge",
        label="核心被动：绝裁末击异放（消耗霜刑）",
        ratio=core_ratio,
        source_rule_id=_CORE_DISCHARGE_RULE_ID,
    )
    templates.append(core_template)
    core_discharge_source = source_for(
        PROMEIA_ID,
        "core:discharge",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_creation = _event_creation(
        effect_id=_CORE_DISCHARGE_CREATION_ID,
        source=core_discharge_source,
        source_template_id=_CORE_EX_FINISHER_TEMPLATE,
        result_template_id=core_template.ref.template_id,
    )
    rules.append(
        _rule(
            "core:discharge",
            core_discharge_source,
            f"核心被动：绝裁末击异放{core_ratio:.0%}（消耗1点霜刑）",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(_TARGET_HAS_ANOMALY, _FROST_CONSUMED),
            effects=(core_creation,),
        )
    )

    chain_raw = _raw_move(raw_record, "连携技：倒悬清算")
    chain_ratio = _discharge_ratio(
        chain_raw.description,
        "Promeia Chain fixed type-2 Discharge multiplier",
    )
    chain_template, chain_derived = _make_discharge(
        key="chain-anomaly-discharge",
        label="连携技：倒悬清算末击异放",
        ratio=chain_ratio,
        source_rule_id=_CHAIN_DISCHARGE_RULE_ID,
    )
    templates.append(chain_template)
    chain_source = source_for(
        PROMEIA_ID,
        "chain:discharge",
        EffectSourceType.SKILL,
        chain_raw.name,
        chain_raw.description,
    )
    rules.append(
        _rule(
            "chain:discharge",
            chain_source,
            f"连携技末击异放{chain_ratio:.0%}",
            chain_raw.description,
            RuleEligibility.ELIGIBLE,
            conditions=(_TARGET_HAS_ANOMALY,),
            effects=(
                _event_creation(
                    effect_id=_CHAIN_DISCHARGE_CREATION_ID,
                    source=chain_source,
                    source_template_id=_CHAIN_TEMPLATE,
                    result_template_id=chain_template.ref.template_id,
                ),
            ),
        )
    )

    ultimate_raw = _raw_move(raw_record, "终结技：彻骨磔罚")
    ultimate_ratio = _discharge_ratio(
        ultimate_raw.description,
        "Promeia Ultimate fixed type-2 Discharge multiplier",
    )
    ultimate_template, ultimate_derived = _make_discharge(
        key="ultimate-anomaly-discharge",
        label="终结技：彻骨磔罚末击异放",
        ratio=ultimate_ratio,
        source_rule_id=_ULTIMATE_DISCHARGE_RULE_ID,
    )
    templates.append(ultimate_template)
    ultimate_source = source_for(
        PROMEIA_ID,
        "ultimate:discharge",
        EffectSourceType.SKILL,
        ultimate_raw.name,
        ultimate_raw.description,
    )
    rules.append(
        _rule(
            "ultimate:discharge",
            ultimate_source,
            f"终结技末击异放{ultimate_ratio:.0%}",
            ultimate_raw.description,
            RuleEligibility.ELIGIBLE,
            conditions=(_TARGET_HAS_ANOMALY,),
            effects=(
                _event_creation(
                    effect_id=_ULTIMATE_DISCHARGE_CREATION_ID,
                    source=ultimate_source,
                    source_template_id=_ULTIMATE_TEMPLATE,
                    result_template_id=ultimate_template.ref.template_id,
                ),
            ),
        )
    )

    independent_derived = [core_derived, chain_derived, ultimate_derived]

    # The Extra Ability is team-eligible for another Anomaly or Support. The
    # composition flag is resolved by the registry/adapter; timers are static
    # duration bonuses rather than a simulation of the proc timeline.
    extra_source = source_for(
        PROMEIA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligible = config.additional_ability_eligible
    rules.append(
        _rule(
            "extra-ability:frost-chill-duration",
            extra_source,
            "额外能力：队伍霜寒持续时间+3秒",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE if extra_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "extra-ability:frost-chill-duration",
                    extra_source,
                    CalculationNode.ANOMALY_DURATION_BONUS,
                    Resolved(3.0),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        AnyFilter(
                            (
                                ElementFilter(Element.ICE),
                                ElementFilter(Element.LIESHUANG),
                            )
                        ),
                    ),
                ),
            )
            if extra_eligible
            else (),
        )
    )
    rules.append(
        _rule(
            "extra-ability:verdict-discharge-defense-ignore",
            extra_source,
            "额外能力：有罪推定目标上的全队异放无视防御40%",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE if extra_eligible else RuleEligibility.INELIGIBLE,
            conditions=(_VERDICT_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:verdict-discharge-defense-ignore",
                    extra_source,
                    CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    Resolved(0.40),
                    target=EffectTarget.TEAM,
                    filters=(DamageSubtypeFilter(DamageSubtype.DISCHARGE),),
                ),
            )
            if extra_eligible
            else (),
        )
    )
    rules.append(
        _rule(
            "extra-ability:ice-buildup-efficiency",
            extra_source,
            "额外能力：当前冰异常积蓄效率+30%",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE if extra_eligible else RuleEligibility.INELIGIBLE,
            conditions=(_ICE_BURN_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:ice-buildup-efficiency",
                    extra_source,
                    CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    Resolved(0.30),
                    target=EffectTarget.SELF,
                    filters=(ElementFilter(Element.ICE),),
                ),
            )
            if extra_eligible
            else (),
        )
    )

    # Cinema 1 affects team Discharges against the current Verdict state. Its
    # source also grants Frost, but that resource timing is outside this static
    # calculation and is intentionally not simulated.
    c1 = _raw_cinema(raw_record, 1)
    c1_source = source_for(
        PROMEIA_ID, "cinema1", EffectSourceType.CINEMA, c1.name, c1.description
    )
    c1_ignore = _single_number(
        c1.description,
        r"额外无视(?P<value>[\d.]+)%防御力",
        "Promeia Cinema 1 additional team Discharge defense ignore",
    ) / 100.0
    c1_eligible = config.cinema_level >= 1
    rules.append(
        _rule(
            "cinema1:verdict-discharge-defense-ignore",
            c1_source,
            f"1影：有罪推定目标上的全队异放额外无视防御{c1_ignore:.0%}",
            c1.description,
            RuleEligibility.ELIGIBLE if c1_eligible else RuleEligibility.INELIGIBLE,
            conditions=(_VERDICT_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:verdict-discharge-defense-ignore",
                    c1_source,
                    CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    Resolved(c1_ignore),
                    target=EffectTarget.TEAM,
                    filters=(DamageSubtypeFilter(DamageSubtype.DISCHARGE),),
                ),
            )
            if c1_eligible
            else (),
        )
    )

    c2 = _raw_cinema(raw_record, 2)
    c2_source = source_for(
        PROMEIA_ID, "cinema2", EffectSourceType.CINEMA, c2.name, c2.description
    )
    c2_ap = _single_number(
        c2.description,
        r"异常精通提升(?P<value>[\d.]+)点",
        "Promeia Cinema 2 Anomaly Proficiency increase",
    )
    c2_eligible = config.cinema_level >= 2
    c2_ambiguous_effect = UnresolvedEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1541:cinema2:frost-discharge-ratio"),
            source=c2_source,
            owner=PROMEIA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.ANOMALY),
                DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                AnyFilter(
                    (
                        CreatedByEffectFilter(_CORE_DISCHARGE_CREATION_ID),
                        CreatedByEffectFilter(_C6_DISCHARGE_CREATION_ID),
                    )
                ),
            ),
        ),
        unresolved=Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_TEXT,
            notes=(
                "Cinema 2 says the multiplier of Frost-consuming Discharge is increased by 120%, "
                "but does not say whether this is a +120-percentage-point addition or a relative "
                "increase by 120% (×2.20 total). The source also does not establish whether the modifier "
                "applies to Cinema 6's separate special 200% Discharge. Only the explicitly "
                "Frost-consuming Core and C6 events are affected; Chain and Ultimate do not consume Frost."
            ),
            original_text=c2.description,
            candidates=("add 120 percentage points", "increase the original multiplier by 120% (×2.20 total)"),
        ),
    )
    rules.append(
        _rule(
            "cinema2:anomaly-proficiency-and-frost-discharge",
            c2_source,
            f"2影：异常精通+{c2_ap:g}；霜刑异放倍率文本待判定",
            c2.description,
            RuleEligibility.ELIGIBLE if c2_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:anomaly-proficiency",
                    c2_source,
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    Resolved(c2_ap),
                    target=EffectTarget.SELF,
                ),
                c2_ambiguous_effect,
            )
            if c2_eligible
            else (),
        )
    )

    for level in (3, 5):
        mindscape = _raw_cinema(raw_record, level)
        source = source_for(
            PROMEIA_ID,
            f"cinema{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级+2（含终结技）",
                mindscape.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    c6 = _raw_cinema(raw_record, 6)
    c6_source = source_for(
        PROMEIA_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description
    )
    c6_ratio = _single_number(
        c6.description,
        r"固定结算(?P<value>[\d.]+)%倍率的对应属性的属性异常伤害",
        "Promeia Cinema 6 fixed type-2 Discharge multiplier",
    ) / 100.0
    c6_template, c6_derived = _make_discharge(
        key="cinema6-frost-special-discharge",
        label="6影：消耗霜刑时追加特殊异放",
        ratio=c6_ratio,
        source_rule_id=_C6_DISCHARGE_RULE_ID,
    )
    templates.append(c6_template)
    c6_eligible = config.cinema_level >= 6
    rules.append(
        _rule(
            "cinema6:extra-discharge",
            c6_source,
            f"6影：消耗霜刑时追加{c6_ratio:.0%}固定倍率异放",
            c6.description,
            RuleEligibility.ELIGIBLE if c6_eligible else RuleEligibility.INELIGIBLE,
            conditions=(_TARGET_HAS_ANOMALY, _FROST_CONSUMED),
            effects=(
                _event_creation(
                    effect_id=_C6_DISCHARGE_CREATION_ID,
                    source=c6_source,
                    source_template_id=_CORE_EX_FINISHER_TEMPLATE,
                    result_template_id=c6_template.ref.template_id,
                ),
            ),
        )
    )
    c6_resist_ignore = _single_number(
        c6.description,
        r"无视敌人(?P<value>[\d.]+)%全属性伤害抗性",
        "Promeia Cinema 6 anomaly and Disorder resistance ignore",
    ) / 100.0
    rules.append(
        _rule(
            "cinema6:anomaly-disorder-resistance-ignore",
            c6_source,
            f"6影：自身属性异常与紊乱伤害无视全属性抗性{c6_resist_ignore:.0%}",
            c6.description,
            RuleEligibility.ELIGIBLE if c6_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema6:anomaly-disorder-resistance-ignore",
                    c6_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c6_resist_ignore),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(PROMEIA_ID),
                        AnyFilter(
                            (
                            # Attribute-anomaly damage has a distinct subtype;
                            # Discharge is also DamageType.ANOMALY, so filtering
                            # only by type would incorrectly include every
                            # generated Discharge event.
                            DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                                DamageTypeFilter(DamageType.DISORDER),
                            )
                        ),
                    ),
                ),
            )
            if c6_eligible
            else (),
        )
    )

    return build_definition(
        character_id=PROMEIA_ID,
        role=CharacterRole.ANOMALY,
        element=Element.ICE,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(ice_disorder_remaining,),
        independent_derived_damage_events=(
            *independent_derived,
            c6_derived,
        ),
        diagnostics=diagnostics,
    )


__all__ = ["compile_promeia"]
