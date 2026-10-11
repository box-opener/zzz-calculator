"""Compile Aria's reviewed Nanoka 3.2 source into damage contracts."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    ANOMALY_ELEMENTS,
    AnomalyRecordId,
    BASE_ELEMENT_BY_ELEMENT,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CreatedByEffectFilter,
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
    SnapshotRule,
    StateId,
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
    source_for,
)
from ..nanoka_source import NanokaRawRecord
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DischargeDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import ARIA_ID, AriaCompileConfig
from .reviewed import (
    ARIA_DELUSION_ACTIVE,
    ARIA_ETHER_ANOMALY_RECORD_ID,
    ARIA_REVIEWED_MAPPING,
    ARIA_THIRD_CHARGE_ANOMALY_HIT,
)


_DISCHARGE_RATE_ELEMENTS = (
    Element.ETHER,
    Element.ELECTRIC,
    Element.FIRE,
    Element.PHYSICAL,
    Element.ICE,
    Element.WIND,
)
_DISCHARGE_RATE_LABELS = ("以太", "电", "火", "物理", "冰", "风")
_ENEMY_STUNNED = StateId("state:enemy:stunned")
_ETHER_DISORDER_REMAINING_HALF_SECONDS = ScenarioParameterId(
    "parameter:aria:ether-disorder-remaining-half-seconds"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _single_number(text: str, pattern: str, label: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{label} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _core_rates(text: str) -> tuple[float, ...]:
    clean = _plain(text)
    match = re.search(
        r"每10点初始异常掌控\s*(?P<ether>[\d.]+)%/"
        r"(?P<electric>[\d.]+)%/(?P<fire>[\d.]+)%/"
        r"(?P<physical>[\d.]+)%/(?P<ice>[\d.]+)%/(?P<wind>[\d.]+)%",
        clean,
    )
    if match is None:
        raise ValueError("Aria Core must contain the six typed anomaly Discharge ratios")
    return tuple(float(match.group(key)) for key in _DISCHARGE_RATE_LABELS_KEYS)


_DISCHARGE_RATE_LABELS_KEYS = ("ether", "electric", "fire", "physical", "ice", "wind")


def _condition(condition_id: ScenarioConditionId, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
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
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1501:{key}"),
        owner=ARIA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        effects=tuple(effects),
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
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1501:{key}"),
            source=source,
            owner=ARIA_ID,
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


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("Aria raw record must contain all seven core levels") from exc


def _raw_talent(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"Aria raw record is missing cinema {level}") from exc


def _validate_raw_record(raw: NanokaRawRecord, config: AriaCompileConfig) -> None:
    if raw.character_id != ARIA_ID or raw.code_name != "Aria":
        raise ValueError("Aria compiler requires character:1501 code_name='Aria'")
    if raw.name != "爱芮" or raw.specialty != "异常" or raw.element != "以太":
        raise ValueError("Aria raw identity must remain Anomaly/Ether")
    if raw.faction != "妄想天使" or raw.icon != "IconRole57" or raw.rarity != 4:
        raise ValueError("Aria raw identity fields do not match the reviewed Nanoka source")
    if raw.source_version != "3.2" or not raw.source_url.endswith("/1501.json"):
        raise ValueError("Aria raw source provenance must be the Nanoka 3.2 record")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Aria raw record must contain seven Core and six Cinema levels")
    _raw_core(raw, config.core_level)
    _raw_talent(raw, 6)


def _static_anomaly_entries(raw: NanokaRawRecord, *, extra_eligible: bool):
    # This is the compiled maximum when the team can enable the Extra Ability.
    # At execution time the full-gauge tick count follows the actual record
    # duration, so turning the rule off automatically returns to 10 seconds.
    corrosion_duration = 13 if extra_eligible else 10
    corrosion_ticks = corrosion_duration * 2
    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1501:ether-corruption"),
        semantic_id=DamageEventSemanticId("event:character:1501:ether-corruption"),
        label="属性异常：侵蚀（单跳62.5%，完整当前记录时长）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ETHER,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=ARIA_ID,
        element=Element.ETHER,
        anomaly_triggerer=ARIA_ID,
        history_record_source=AnomalyRecordId(ARIA_ETHER_ANOMALY_RECORD_ID),
        crit_rule=NoCritRule(),
        move_id=None,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1501:ether-corruption"),
        character_id=ARIA_ID,
        move_id=None,
        display_name="属性异常：侵蚀（单跳62.5%，完整当前记录时长）",
        original_text=(
            "按规范静态单人100%以太异常记录结算：每0.5秒62.5%侵蚀，"
            f"完整当前记录最多{corrosion_duration}秒、{corrosion_ticks}跳；"
            "跳数随启用的额外能力记录时长确定，不模拟积蓄或时间轴。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1501:ether-corrosion-tick"),
                label=f"侵蚀单跳倍率 × {corrosion_ticks}",
                parameter_name="侵蚀单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.625)),
                repeat_count=corrosion_ticks,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1501:ether-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1501:ether-disorder"),
        label="紊乱：侵蚀（按所选剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ETHER,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ARIA_ID,
        element=Element.ETHER,
        disorder_triggerer=ARIA_ID,
        history_record_source=AnomalyRecordId(ARIA_ETHER_ANOMALY_RECORD_ID),
        crit_rule=NoCritRule(),
        move_id=None,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1501:ether-disorder"),
        character_id=ARIA_ID,
        move_id=None,
        display_name="紊乱：侵蚀（按所选剩余时间）",
        original_text=(
            "以太紊乱倍率为450% + floor(t/0.5) × 62.5%；"
            f"t为当前以太异常剩余时间，范围0–{corrosion_duration}秒，不推断战斗时序。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1501:ether-disorder"),
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
        original_text=(
            f"以太异常最多{corrosion_duration}秒；按当前静态剩余时间输入，"
            "不模拟时间轴。"
        ),
        resolution=ParameterResolution.USER_SELECTED,
        value=corrosion_ticks,
        minimum=0,
        maximum=corrosion_ticks,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        remaining,
    )


def _core_discharge_refs(raw: NanokaRawRecord, level: int):
    core = _raw_core(raw, level)
    rates = _core_rates(core.description)
    creation_id = EffectId("effect:character:1501:core:discharge")
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1501:core:discharge"),
        semantic_id=DamageEventSemanticId("event:character:1501:core:discharge"),
        label="核心被动：异放（所选原属性异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        element=Element.ETHER,
        source_rule_item_id=RuleItemId("rule:character:1501:core:anomaly-discharge"),
    )
    template = DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=ARIA_ID,
        element=Element.ETHER,
        discharge_triggerer=ARIA_ID,
        history_record_source=None,
        # C0 has no Aria-owned Discharge crit capability. Execution binds
        # the selected source record's explicitly inheritable capability.
        crit_rule=NoCritRule(),
        move_id=None,
        multiplier_from_source_event=False,
        source_multiplier_by_element=tuple(
            (element, 1.0) for element in _DISCHARGE_RATE_ELEMENTS
        ),
    )
    derived_refs = (
        DerivedDamageEventTemplateRef(
            template=ref,
            multiplier=FixedMultiplier(Resolved(1.0)),
        ),
    )
    third_charge_templates = (
        EventTemplateId(
            "template:character:1501:basic-absolute-pitch-charge-3:main"
        ),
        EventTemplateId(
            "template:character:1501:basic-absolute-pitch-charge-3-cooperative:main"
        ),
    )
    creation_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=creation_id,
            source=source_for(
                ARIA_ID,
                "core:discharge",
                EffectSourceType.CORE_PASSIVE,
                core.name,
                core.description,
            ),
            owner=ARIA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(AnyFilter(tuple(EventTemplateIdFilter(item) for item in third_charge_templates)),),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=ref.template_id,
            unique_per_source_event=True,
        ),
    )
    ratio_effects = []
    for element, rate, label in zip(
        _DISCHARGE_RATE_ELEMENTS, rates, _DISCHARGE_RATE_LABELS
    ):
        suffix = element.value
        rate_factor = rate / 1000.0
        family_element_filter = AnyFilter(
            tuple(
                ElementFilter(candidate)
                for candidate in sorted(ANOMALY_ELEMENTS, key=lambda item: item.value)
                if BASE_ELEMENT_BY_ELEMENT[candidate] is element
            )
        )
        ratio_effects.append(
            _modifier(
                f"core:discharge:{suffix}:initial-mastery-ratio",
                source_for(
                    ARIA_ID,
                    f"core:discharge:{suffix}",
                    EffectSourceType.CORE_PASSIVE,
                    core.name,
                    core.description,
                ),
                CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
                PanelStatDerivedValue(
                    source_character_id=ARIA_ID,
                    source_node=CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
                    coefficient=Resolved(rate_factor),
                ),
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(ARIA_ID),
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                    family_element_filter,
                    CreatedByEffectFilter(creation_id),
                ),
            )
        )
        ratio_effects.append(
            _modifier(
                f"core:discharge:{suffix}:stunned-target-ratio",
                source_for(
                    ARIA_ID,
                    f"core:discharge:{suffix}",
                    EffectSourceType.CORE_PASSIVE,
                    core.name,
                    core.description,
                ),
                CalculationNode.DISCHARGE_PROFICIENCY_MULTIPLIER,
                PanelStatDerivedValue(
                    source_character_id=ARIA_ID,
                    source_node=CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
                    coefficient=Resolved(rate_factor / 2.0),
                ),
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(ARIA_ID),
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                    family_element_filter,
                    CreatedByEffectFilter(creation_id),
                    EnemyStateFilter(_ENEMY_STUNNED),
                ),
            )
        )
    return (
        (ref,),
        (template,),
        derived_refs,
        (creation_effect,),
        tuple(ratio_effects),
        (creation_id,),
        rates,
    )


def compile_aria(
    config: AriaCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = ARIA_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=ARIA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="character:1501",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    conditions = [
        _condition(
            ARIA_DELUSION_ACTIVE,
            "爱芮当前处于妄想时刻",
            next(
                item.description
                for item in raw_record.moves
                if item.name == "终结技：元气百分百"
            ),
        ),
        _condition(
            ARIA_THIRD_CHARGE_ANOMALY_HIT,
            "本次第三段绝对音准重击命中异常目标",
            _raw_core(raw_record, config.core_level).description,
        ),
    ]
    anomaly_entries, anomaly_templates, disorder_remaining = _static_anomaly_entries(
        raw_record,
        extra_eligible=config.additional_ability_eligible,
    )
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)

    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        ARIA_ID,
        f"core-{config.core_level}",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_mastery = _single_number(
        core.description,
        r"异常精通提升\s*(?P<value>[\d.]+)\s*点",
        "Aria Core Anomaly Proficiency bonus",
    )
    rules: list[CalculationRuleItem] = [
        _rule(
        "core:anomaly-proficiency",
            core_source,
            f"核心被动：异常精通+{core_mastery:g}",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:anomaly-proficiency",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    Resolved(core_mastery),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    ]

    (
        _discharge_refs,
        discharge_templates,
        discharge_derived,
        discharge_creation_effects,
        discharge_ratio_effects,
        discharge_creation_ids,
        discharge_rates,
    ) = _core_discharge_refs(raw_record, config.core_level)
    templates.extend(discharge_templates)
    core_rule_source = source_for(
        ARIA_ID,
        "core:anomaly-discharge",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    rules.append(
        _rule(
            "core:anomaly-discharge",
            core_rule_source,
            "核心被动：异放（按原异常元素、记录与倍率）",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(*discharge_creation_effects, *discharge_ratio_effects),
            conditions=(ARIA_THIRD_CHARGE_ANOMALY_HIT,),
        )
    )

    extra_source = source_for(
        ARIA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    rules.append(
        _rule(
            "extra-ability:ether-corrosion-duration",
            extra_source,
            "额外能力：以太侵蚀持续时间+3秒",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "extra-ability:ether-corrosion-duration",
                    extra_source,
                    CalculationNode.ANOMALY_DURATION_BONUS,
                    Resolved(3.0),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        AnyFilter(
                            (
                                ElementFilter(Element.ETHER),
                                ElementFilter(Element.XUANMO),
                            )
                        ),
                    ),
                ),
            )
            if config.additional_ability_eligible
            else (),
        )
    )

    # Cinema 1 grants an independent crit zone only while its scenario rule is
    # enabled. Keep that override separate from the record-backed fallback:
    # C0 and a disabled C1 must still honor a source record that explicitly
    # allows its crit zone to be inherited by Discharge.
    c1 = _raw_talent(raw_record, 1)
    c1_base_rate = _single_number(
        c1.description,
        r"基础暴击率为\s*(?P<value>[\d.]+)%",
        "Aria Cinema 1 Discharge crit rate",
    ) / 100.0
    c1_crit_damage = _single_number(
        c1.description,
        r"暴击伤害为\s*(?P<value>[\d.]+)%",
        "Aria Cinema 1 Discharge crit damage",
    ) / 100.0
    c1_extra_rate = _single_number(
        c1.description,
        r"每超过1点初始异常掌控会使该效果的暴击率额外提升\s*(?P<value>[\d.]+)%",
        "Aria Cinema 1 extra Discharge crit rate",
    ) / 100.0
    c1_source = source_for(
        ARIA_ID,
        "cinema1",
        EffectSourceType.CINEMA,
        c1.name,
        c1.description,
    )
    c1_filters = (
        DamageDealerFilter(ARIA_ID),
        DamageTypeFilter(DamageType.ANOMALY),
        DamageSubtypeFilter(DamageSubtype.DISCHARGE),
        AnyFilter(
            tuple(
                CreatedByEffectFilter(effect_id)
                for effect_id in discharge_creation_ids
            )
        ),
    )
    c1_effects = (
        _modifier(
            "cinema1:initial-am-discharge-crit-rate",
            c1_source,
            CalculationNode.DISCHARGE_CRIT_RATE_OVERRIDE,
            PanelStatDerivedValue(
                source_character_id=ARIA_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY,
                coefficient=Resolved(c1_extra_rate),
                base=Resolved(c1_base_rate),
                threshold=Resolved(100.0),
            ),
            target=EffectTarget.TEAM,
            filters=c1_filters,
            operation=EffectOperation.OVERRIDE,
        ),
        _modifier(
            "cinema1:discharge-crit-damage",
            c1_source,
            CalculationNode.DISCHARGE_CRIT_DAMAGE_OVERRIDE,
            Resolved(c1_crit_damage),
            target=EffectTarget.TEAM,
            filters=c1_filters,
            operation=EffectOperation.OVERRIDE,
        ),
    )
    rules.append(
        _rule(
            "cinema1:discharge-independent-crit",
            c1_source,
            f"1影：自身异放独立暴击（基础{c1_base_rate:.0%} / 暴伤{c1_crit_damage:.0%}）",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=c1_effects,
        )
    )

    c2 = _raw_talent(raw_record, 2)
    c2_ignores = tuple(
        float(value)
        for value in re.findall(r"无视目标\s*([\d.]+)%防御力", _plain(c2.description))
    )
    if len(c2_ignores) != 2:
        raise ValueError("Aria Cinema 2 must contain its two defense-ignore ratios")
    c2_source = source_for(
        ARIA_ID,
        "cinema2",
        EffectSourceType.CINEMA,
        c2.name,
        c2.description,
    )
    attack_or_discharge = (
        DamageDealerFilter(ARIA_ID),
        AnyFilter(
            (
                DamageTypeFilter(DamageType.DIRECT),
                DamageSubtypeFilter(DamageSubtype.DISCHARGE),
            )
        ),
    )
    c2_eligible = config.cinema_level >= 2
    rules.append(
        _rule(
            "cinema2:defense-ignore",
            c2_source,
            f"2影：自身攻击与异放无视防御{c2_ignores[0]:g}%",
            c2.description,
            RuleEligibility.ELIGIBLE if c2_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:defense-ignore",
                    c2_source,
                    CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    Resolved(c2_ignores[0] / 100.0),
                    target=EffectTarget.TEAM,
                    filters=attack_or_discharge,
                ),
            )
            if c2_eligible
            else (),
        )
    )
    rules.append(
        _rule(
            "cinema2:delusion-defense-ignore",
            c2_source,
            f"2影：妄想时刻期间自身攻击与异放额外无视防御{c2_ignores[1]:g}%",
            c2.description,
            RuleEligibility.ELIGIBLE if c2_eligible else RuleEligibility.INELIGIBLE,
            conditions=(ARIA_DELUSION_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:delusion-defense-ignore",
                    c2_source,
                    CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    Resolved(c2_ignores[1] / 100.0),
                    target=EffectTarget.TEAM,
                    filters=attack_or_discharge,
                ),
            )
            if c2_eligible
            else (),
        )
    )

    # Cinema 3/5 are reflected by effective_skill_level; the records remain
    # visible without duplicating a second multiplier effect.
    for level in (3, 5):
        mindscape = _raw_talent(raw_record, level)
        source = source_for(
            ARIA_ID,
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

    c6 = _raw_talent(raw_record, 6)
    c6_bonus = _single_number(
        c6.description,
        r"造成的以太伤害提升\s*(?P<value>[\d.]+)%",
        "Aria Cinema 6 Ether damage bonus",
    ) / 100.0
    c6_source = source_for(
        ARIA_ID,
        "cinema6",
        EffectSourceType.CINEMA,
        c6.name,
        c6.description,
    )
    enhanced_charge_template_id = EventTemplateId(
        "template:character:1501:basic-absolute-pitch-enhanced:main"
    )
    ultimate_template_id = EventTemplateId(
        "template:character:1501:ultimate-energy-full:main"
    )
    c6_eligible = config.cinema_level >= 6
    rules.append(
        _rule(
            "cinema6:delusion-enhanced-basic-and-ultimate-damage",
            c6_source,
            f"6影：妄想时刻强化蓄力普通攻击与终结技以太伤害+{c6_bonus:.0%}",
            c6.description,
            RuleEligibility.ELIGIBLE if c6_eligible else RuleEligibility.INELIGIBLE,
            conditions=(ARIA_DELUSION_ACTIVE,),
            effects=(
                _modifier(
                    "cinema6:delusion-enhanced-basic-and-ultimate-damage",
                    c6_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c6_bonus),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(ARIA_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        ElementFilter(Element.ETHER),
                        AnyFilter(
                            (
                                EventTemplateIdFilter(enhanced_charge_template_id),
                                EventTemplateIdFilter(ultimate_template_id),
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
        character_id=ARIA_ID,
        role=CharacterRole.ANOMALY,
        element=Element.ETHER,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(disorder_remaining,),
        independent_derived_damage_events=discharge_derived,
        diagnostics=diagnostics,
    )


__all__ = ["compile_aria"]
