"""Compile Velina's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace

from core.types import (
    CalculationNode,
    AnyFilter,
    CharacterId,
    CharacterRole,
    CreatedByEffectFilter,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTagFilter,
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
    BattleEventKind,
    EventTemplateId,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveIdFilter,
    NoCritRule,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    ScenarioParameterRangeCondition,
    SnapshotRule,
    SkillGroup,
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
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DischargeDamageEventTemplate,
    TurbulenceDamageEventTemplate,
)
from .config import VelinaCompileConfig
from .reviewed import (
    ASSIST_FOLLOW_UP_MOVE_ID,
    BROAD_CYCLONE_DISSIPATING,
    BROAD_CYCLONE_MOVE_ID,
    CINEMA4_ATTACK_ACTIVE,
    ENEMY_WIND_WEATHERED,
    EX_SPECIAL_STORM_EYE_MOVE_ID,
    MICRO_CYCLONE_DISSIPATING,
    MICRO_CYCLONE_MOVE_ID,
    ULTIMATE_MOVE_ID,
    VELINA_ID,
    VELINA_REVIEWED_MAPPING,
    VELINA_WIND_RECORD_ID,
    WIND_EROSION_STACKS,
    WIND_WEATHERING_REMAINING_SECONDS,
)


_COLOURED_ELEMENTS: dict[int, Element] = {
    1: Element.PHYSICAL,
    2: Element.FIRE,
    3: Element.ELECTRIC,
    4: Element.ICE,
    5: Element.ETHER,
}


def _condition(condition_id, label: str, text: str, value: bool = False):
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    conditions=(),
    effects=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1561:{key}"),
        owner=VELINA_ID,
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
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1561:{key}"),
            source=source,
            owner=VELINA_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(VELINA_ID))


def _validate_raw(raw: NanokaRawRecord, config: VelinaCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Velina raw record and compile config IDs must match")
    if raw.name != "维琳娜" or raw.code_name != "Velina":
        raise ValueError("unexpected identity in Velina raw record")
    if raw.specialty != "异常" or raw.element != "风属性" or raw.rarity != 4:
        raise ValueError("Velina raw role, element, or rank changed")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Velina source must include seven cores and six mindscapes")
    if raw.potential_details:
        raise ValueError("Velina live source unexpectedly contains Potential variants")


def _mapping_for_config(config: VelinaCompileConfig) -> NanokaReviewedMapping:
    if config.current_coloured_element is None:
        return VELINA_REVIEWED_MAPPING
    moves: list[NanokaMoveSpec] = []
    for spec in VELINA_REVIEWED_MAPPING.moves:
        if spec.entry_key != "broad-cyclone-wind":
            moves.append(spec)
            continue
        element_name = config.current_coloured_element.value.replace(":", "-")
        moves.append(
            replace(
                spec,
                entry_key=f"broad-cyclone-coloured-{element_name}",
                display_name=(
                    f"广域气旋（染色为{config.current_coloured_element.value} × 10）"
                ),
                element=config.current_coloured_element,
                parameters=(
                    NanokaDamageParameterSpec(
                        variant_key=f"broad-cyclone-coloured-{element_name}-damage",
                        parameter_name="[广域气旋]染色属性单次攻击伤害倍率",
                        source_skill_components=(("1561020", 0.2),),
                        repeat_count=10,
                    ),
                ),
            )
        )
    return replace(VELINA_REVIEWED_MAPPING, moves=tuple(moves))


def _synthetic_entry(
    key: str,
    label: str,
    text: str,
    template: DamageEventTemplateRef,
    multiplier: float,
    *,
    repeat_count: int | None = None,
) -> MoveCalculationEntry:
    relation = (
        MultiplierRelation.UNIT_REPEAT
        if repeat_count is not None
        else MultiplierRelation.COMPLETE
    )
    return MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1561:{key}"),
        character_id=VELINA_ID,
        move_id=None,
        display_name=label,
        original_text=text,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=relation,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1561:{key}"),
                label=f"倍率 {multiplier * 100:g}% × {repeat_count}",
                parameter_name=label,
                multiplier=FixedMultiplier(Resolved(multiplier)),
                repeat_count=repeat_count,
            ),
        ),
        main_damage_event=template,
    )


def _source_event_refs(raw: NanokaRawRecord):
    source = raw.moves
    by_name = {item.name: item for item in source}
    if "强化特殊技：风切变·风暴眼" not in by_name:
        raise ValueError("Velina raw source is missing the Broad Cyclone host skill")
    wind_ref = DamageEventTemplateRef(
        template_id="template:character:1561:wind-weathering",
        semantic_id=DamageEventSemanticId("event:character:1561:wind-weathering"),
        label="风属性异常：风化",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.WIND,
    )
    wind_template = AttributeAnomalyDamageEventTemplate(
        ref=wind_ref,
        damage_dealer=VELINA_ID,
        element=Element.WIND,
        anomaly_triggerer=VELINA_ID,
        history_record_source=VELINA_WIND_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=None,
    )
    return wind_ref, wind_template


def _wind_entries(raw: NanokaRawRecord):
    wind_ref, wind_template = _source_event_refs(raw)
    weathering_entry = _synthetic_entry(
        "wind-weathering",
        "风属性异常：风化（完整结算）",
        "风属性异常造成一次1750%风化伤害并施加30秒风化状态；不拆成周期跳数。",
        wind_ref,
        17.5,
    )
    return (weathering_entry,), (wind_template,)


def _discharge_source(
    key: str,
    label: str,
    multiplier: float,
    source_rule_item_id: RuleItemId,
):
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1561:{key}"),
        semantic_id=DamageEventSemanticId(f"event:character:1561:{key}"),
        label=label,
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        element=Element.WIND,
        source_rule_item_id=source_rule_item_id,
    )
    template = DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=VELINA_ID,
        element=Element.WIND,
        discharge_triggerer=VELINA_ID,
        history_record_source=VELINA_WIND_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=None,
        multiplier_from_source_event=False,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(multiplier)),
    )
    return ref, template, derived


def _event_creation(
    *,
    key: str,
    source: RuleSource,
    template: DamageEventTemplateRef,
    filters,
    condition=None,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1561:{key}"),
            source=source,
            owner=VELINA_ID,
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


def _wind_static_parameters() -> tuple[ScenarioIntegerParameter, ...]:
    return (
        ScenarioIntegerParameter(
            parameter_id=WIND_EROSION_STACKS,
            label="当前风蚀层数",
            original_text="风蚀最多2层；不模拟获得、消耗或冷却时间。",
            resolution=ParameterResolution.USER_SELECTED,
            value=2,
            minimum=0,
            maximum=2,
        ),
        ScenarioIntegerParameter(
            parameter_id=WIND_WEATHERING_REMAINING_SECONDS,
            label="当前风化剩余时间（秒）",
            original_text="6影重新施加风化时每秒剩余时间提升2.5%，最多40%；默认按最大静态时间30秒，不模拟持续时间。",
            resolution=ParameterResolution.USER_SELECTED,
            value=30,
            minimum=0,
            maximum=30,
        ),
    )


def compile_velina(
    config: VelinaCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    mapping = _mapping_for_config(config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=VELINA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1561",
    )
    wind_entries, wind_templates = _wind_entries(raw_record)
    turbulence_rule_id = RuleItemId(
        "rule:character:1561:core:wind-triggered-turbulence-candidate"
    )
    direct_entries_by_id = {str(item.entry_id): item for item in direct_entries}
    direct_templates_by_id = {
        str(item.ref.template_id): item for item in direct_templates
    }

    def turbulence_cyclone_child(
        entry_id: str,
        suffix: str,
        label: str,
        *,
        source_rule_id: RuleItemId = turbulence_rule_id,
    ):
        entry = direct_entries_by_id[entry_id]
        base_template = direct_templates_by_id[str(entry.main_damage_event.template_id)]
        source_variant = entry.multiplier_variants[0]
        ref = replace(
            base_template.ref,
            template_id=EventTemplateId(
                f"template:character:1561:cyclone-child:{suffix}"
            ),
            semantic_id=DamageEventSemanticId(
                f"event:character:1561:cyclone-child:{suffix}"
            ),
            label=label,
            source_rule_item_id=source_rule_id,
        )
        # The raw sub-skill curve is a real source, but a Cyclone summoned by
        # Turbulence is a generated event rather than a separately chosen move.
        template = replace(base_template, ref=ref, move_id=None)
        repeat_count = source_variant.repeat_count or 1
        derived = DerivedDamageEventTemplateRef(
            template=ref,
            multiplier=source_variant.multiplier,
            repeat_count=repeat_count,
        )
        return template, derived

    micro_child_template, micro_child_derived = turbulence_cyclone_child(
        "move-entry:character:1561:micro-cyclone",
        "micro",
        "微域气旋（乱流触发）",
    )
    broad_entry = next(
        item
        for item in direct_entries
        if str(item.entry_id).startswith("move-entry:character:1561:broad-cyclone-")
    )
    broad_child_template, broad_child_derived = turbulence_cyclone_child(
        str(broad_entry.entry_id),
        "broad",
        "广域气旋（乱流触发）",
    )
    storm_eye_rule_id = RuleItemId(
        "rule:character:1561:special:storm-eye-broad-cyclone"
    )
    storm_eye_broad_template, storm_eye_broad_derived = turbulence_cyclone_child(
        str(broad_entry.entry_id),
        "storm-eye-broad",
        "广域气旋（风暴眼召唤）",
        source_rule_id=storm_eye_rule_id,
    )
    core = raw_record.core_levels[config.core_level - 1]
    extra_text = core.extra_ability_description
    core_source = source_for(
        VELINA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra_source = source_for(
        VELINA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        extra_text,
    )
    core_expression = PanelStatDerivedValue(
        source_character_id=VELINA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
        coefficient=Resolved(0.0021),
        base=Resolved(0.0),
        cap_max=Resolved(0.35),
        threshold=Resolved(1.2),
        step_size=Resolved(0.01),
    )
    mastery_expression = PanelStatDerivedValue(
        source_character_id=VELINA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
        coefficient=Resolved(0.5),
        base=Resolved(0.0),
        cap_max=Resolved(84.0),
        threshold=Resolved(1.2),
        step_size=Resolved(0.01),
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:initial-energy-regeneration-passive",
            core_source,
            "核心被动：初始能量自动回复增益",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:initial-energy-regeneration-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    core_expression,
                    target=EffectTarget.TEAM,
                    filters=(DamageDealerFilter(VELINA_ID),),
                ),
                _modifier(
                    "core:initial-energy-regeneration-mastery",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
                    mastery_expression,
                    target=EffectTarget.SELF,
                ),
            ),
        ),
        _rule(
            "cinema4:attack-buff",
            source_for(VELINA_ID, "cinema4", EffectSourceType.CINEMA, raw_record.mindscapes[3].name, raw_record.mindscapes[3].description),
            "4影：当前强化特殊技攻击增益",
            raw_record.mindscapes[3].description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            conditions=(CINEMA4_ATTACK_ACTIVE,),
            effects=(
                _modifier(
                    "cinema4:attack-buff",
                    source_for(VELINA_ID, "cinema4", EffectSourceType.CINEMA, raw_record.mindscapes[3].name, raw_record.mindscapes[3].description),
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    Resolved(0.15),
                    target=EffectTarget.SELF,
                ),
            ),
        ),
        _rule(
            "wind-weathered:direct-and-penetration-damage",
            source_for(
                VELINA_ID,
                "wind-weathered-state",
                EffectSourceType.SPECIAL_MECHANISM,
                "风化状态",
                raw_record.core_levels[0].description,
            ),
            "风化状态：风属性直接伤害与贯穿伤害提升",
            raw_record.core_levels[0].description,
            RuleEligibility.ELIGIBLE,
            conditions=(ENEMY_WIND_WEATHERED,),
            effects=(
                _modifier(
                    "wind-weathered:direct-damage",
                    source_for(
                        VELINA_ID,
                        "wind-weathered-state",
                        EffectSourceType.SPECIAL_MECHANISM,
                        "风化状态",
                        raw_record.core_levels[0].description,
                    ),
                    CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION,
                    Resolved(0.10),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        ElementFilter(Element.WIND),
                    ),
                ),
                _modifier(
                    "wind-weathered:penetration-damage",
                    source_for(
                        VELINA_ID,
                        "wind-weathered-state",
                        EffectSourceType.SPECIAL_MECHANISM,
                        "风化状态",
                        raw_record.core_levels[0].description,
                    ),
                    CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION,
                    Resolved(0.10),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.WIND),
                    ),
                ),
            ),
        ),
    ]
    if config.additional_ability_eligible:
        rules.append(
            _rule(
                "extra-ability:wind-weathering-and-turbulence-damage",
                extra_source,
                "额外能力：风化与乱流伤害提升",
                extra_text,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "extra-ability:weathering-damage",
                        extra_source,
                        CalculationNode.ANOMALY_DAMAGE_BONUS,
                        Resolved(0.10),
                        target=EffectTarget.TEAM,
                        filters=(
                            DamageDealerFilter(VELINA_ID),
                            DamageTypeFilter(DamageType.ANOMALY),
                            DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                            ElementFilter(Element.WIND),
                        ),
                    ),
                    _modifier(
                        "extra-ability:turbulence-damage",
                        extra_source,
                        CalculationNode.TURBULENCE_DAMAGE_BONUS,
                        Resolved(0.10),
                        target=EffectTarget.TEAM,
                        filters=(
                            DamageDealerFilter(VELINA_ID),
                            DamageTypeFilter(DamageType.ANOMALY),
                            DamageSubtypeFilter(DamageSubtype.TURBULENCE),
                        ),
                    ),
                ),
            )
        )
    else:
        rules.append(
            _rule(
                "extra-ability:wind-weathering-and-turbulence-damage",
                extra_source,
                "额外能力：风化与乱流伤害提升",
                extra_text,
                RuleEligibility.INELIGIBLE,
            )
        )
    if config.additional_ability_eligible and config.cinema_level >= 2:
        cinema2_source = source_for(
            VELINA_ID,
            "cinema2",
            EffectSourceType.CINEMA,
            raw_record.mindscapes[1].name,
            raw_record.mindscapes[1].description,
        )
        rules.append(
            _rule(
                "cinema2:extra-ability-damage-increase",
                cinema2_source,
                "2影：额外能力风化与乱流伤害提升",
                raw_record.mindscapes[1].description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema2:weathering-damage",
                        cinema2_source,
                        CalculationNode.ANOMALY_DAMAGE_BONUS,
                        Resolved(0.15),
                        target=EffectTarget.TEAM,
                        filters=(
                            DamageDealerFilter(VELINA_ID),
                            DamageTypeFilter(DamageType.ANOMALY),
                            DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                            ElementFilter(Element.WIND),
                        ),
                    ),
                    _modifier(
                        "cinema2:turbulence-damage",
                        cinema2_source,
                        CalculationNode.TURBULENCE_DAMAGE_BONUS,
                        Resolved(0.15),
                        target=EffectTarget.TEAM,
                        filters=(
                            DamageDealerFilter(VELINA_ID),
                            DamageTypeFilter(DamageType.ANOMALY),
                            DamageSubtypeFilter(DamageSubtype.TURBULENCE),
                        ),
                    ),
                ),
            )
        )
    else:
        cinema2_source = source_for(
            VELINA_ID,
            "cinema2",
            EffectSourceType.CINEMA,
            raw_record.mindscapes[1].name,
            raw_record.mindscapes[1].description,
        )
        rules.append(
            _rule(
                "cinema2:extra-ability-damage-increase",
                cinema2_source,
                "2影：额外能力风化与乱流伤害提升",
                raw_record.mindscapes[1].description,
                RuleEligibility.INELIGIBLE,
            )
        )
    c1_source = source_for(
        VELINA_ID,
        "cinema1",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[0].name,
        raw_record.mindscapes[0].description,
    )
    rules.append(
        _rule(
            "cinema1:resistance-ignore",
            c1_source,
            "1影：乱流与风属性风化抗性无视",
            raw_record.mindscapes[0].description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:turbulence-resistance-ignore",
                    c1_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(0.20),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(VELINA_ID),
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.TURBULENCE),
                    ),
                ),
                _modifier(
                    "cinema1:wind-weathering-resistance-ignore",
                    c1_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(0.20),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        ElementFilter(Element.WIND),
                    ),
                ),
            ),
        )
    )
    c6_source = source_for(
        VELINA_ID,
        "cinema6",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[5].name,
        raw_record.mindscapes[5].description,
    )
    rules.append(
        _rule(
            "cinema6:weathering-remaining-time-damage",
            c6_source,
            "6影：当前风化剩余时间伤害增幅",
            raw_record.mindscapes[5].description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            conditions=(ENEMY_WIND_WEATHERED,),
            effects=(
                _modifier(
                    "cinema6:weathering-remaining-time-damage",
                    c6_source,
                    CalculationNode.ANOMALY_DAMAGE_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(WIND_WEATHERING_REMAINING_SECONDS),
                        coefficient=Resolved(0.025),
                        base=Resolved(0.0),
                        cap_max=Resolved(0.40),
                    ),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(VELINA_ID),
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        ElementFilter(Element.WIND),
                    ),
                ),
            ),
        )
    )
    conditions = (
        _condition(
            CINEMA4_ATTACK_ACTIVE,
            "当前维琳娜的4影攻击增益生效",
            raw_record.mindscapes[3].description,
        ),
        _condition(
            ENEMY_WIND_WEATHERED,
            "目标当前处于风化状态",
            raw_record.core_levels[0].description,
        ),
        _condition(
            MICRO_CYCLONE_DISSIPATING,
            "微域气旋当前消散",
            raw_record.core_levels[0].description,
        ),
        _condition(
            BROAD_CYCLONE_DISSIPATING,
            "广域气旋当前消散",
            raw_record.core_levels[0].description,
        ),
    )
    for level in (3, 5):
        mindscape = raw_record.mindscapes[level - 1]
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source_for(VELINA_ID, f"cinema{level}", EffectSourceType.CINEMA, mindscape.name, mindscape.description),
                f"{level}影：技能等级",
                mindscape.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    params = _wind_static_parameters()
    micro_dissipation_rule_id = RuleItemId(
        "rule:character:1561:core:micro-cyclone-dissipation"
    )
    broad_dissipation_rule_id = RuleItemId(
        "rule:character:1561:core:broad-cyclone-dissipation"
    )
    ultimate_discharge_rule_id = RuleItemId(
        "rule:character:1561:extra-ability:ultimate-wind-discharge"
    )
    micro_discharge_ref, micro_discharge_template, micro_discharge_derived = (
        _discharge_source(
            "micro-cyclone-dissipation",
            "微域气旋消散：异放",
            0.85 + (config.core_level - 1) * 0.10,
            micro_dissipation_rule_id,
        )
    )
    broad_discharge_ref, broad_discharge_template, broad_discharge_derived = (
        _discharge_source(
            "broad-cyclone-dissipation",
            "广域气旋消散：异放",
            1.35 + (config.core_level - 1) * 0.20,
            broad_dissipation_rule_id,
        )
    )
    ultimate_discharge_ref, ultimate_discharge_template, ultimate_discharge_derived = (
        _discharge_source(
            "ultimate-wind-discharge",
            "终结技重击：异放（额外能力）",
            6.8,
            ultimate_discharge_rule_id,
        )
    )
    discharge_templates = (
        micro_discharge_template,
        broad_discharge_template,
        ultimate_discharge_template,
    )
    discharge_derived = (
        micro_discharge_derived,
        broad_discharge_derived,
        ultimate_discharge_derived,
    )
    turbulence_ref = DamageEventTemplateRef(
        template_id="template:character:1561:turbulence-from-record",
        semantic_id=DamageEventSemanticId(
            "event:character:1561:turbulence-from-record"
        ),
        label="乱流（继承当前非风异常记录）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.TURBULENCE,
        element=Element.WIND,
        source_rule_item_id=RuleItemId(
            "rule:character:1561:core:wind-triggered-turbulence-candidate"
        ),
    )
    turbulence_template = TurbulenceDamageEventTemplate(
        ref=turbulence_ref,
        damage_dealer=VELINA_ID,
        element=Element.WIND,
        wind_anomaly_triggerer=VELINA_ID,
        history_record_source=None,
        crit_rule=NoCritRule(),
        core_turbulence_bonus=0.90 + (config.core_level - 1) * 0.10,
        wind_erosion_stack_parameter_id=WIND_EROSION_STACKS,
        enhanced_at_stack_count=2,
    )
    turbulence_derived_ref = DerivedDamageEventTemplateRef(
        template=turbulence_ref,
        multiplier=FixedMultiplier(Resolved(1.0)),
    )
    micro_dissipation_creation = _event_creation(
        key="core:micro-cyclone-dissipation",
        source=core_source,
        template=micro_discharge_ref,
        filters=(
            DamageDealerFilter(VELINA_ID),
            DamageTypeFilter(DamageType.DIRECT),
            AnyFilter(
                (
                    MoveIdFilter(MICRO_CYCLONE_MOVE_ID),
                    CreatedByEffectFilter(
                        EffectId(
                            "effect:character:1561:core:turbulence-summons-micro-cyclone"
                        )
                    ),
                )
            ),
        ),
    )
    broad_dissipation_creation = _event_creation(
        key="core:broad-cyclone-dissipation",
        source=core_source,
        template=broad_discharge_ref,
        filters=(
            DamageDealerFilter(VELINA_ID),
            DamageTypeFilter(DamageType.DIRECT),
            AnyFilter(
                (
                    MoveIdFilter(BROAD_CYCLONE_MOVE_ID),
                    CreatedByEffectFilter(
                        EffectId(
                            "effect:character:1561:core:turbulence-summons-broad-cyclone"
                        )
                    ),
                    CreatedByEffectFilter(
                        EffectId(
                            "effect:character:1561:special:storm-eye-broad-cyclone"
                        )
                    ),
                )
            ),
        ),
    )
    rules.extend(
        (
            _rule(
                "core:micro-cyclone-dissipation",
                core_source,
                "核心被动：微域气旋消散异放",
                raw_record.core_levels[0].description,
                RuleEligibility.ELIGIBLE,
                conditions=(ENEMY_WIND_WEATHERED, MICRO_CYCLONE_DISSIPATING),
                effects=(micro_dissipation_creation,),
            ),
            _rule(
                "core:broad-cyclone-dissipation",
                core_source,
                "核心被动：广域气旋消散异放",
                raw_record.core_levels[0].description,
                RuleEligibility.ELIGIBLE,
                conditions=(ENEMY_WIND_WEATHERED, BROAD_CYCLONE_DISSIPATING),
                effects=(broad_dissipation_creation,),
            ),
        )
    )
    storm_eye_source = source_for(
        VELINA_ID,
        "special-storm-eye",
        EffectSourceType.SPECIAL_MECHANISM,
        "强化特殊技：风切变·风暴眼",
        next(
            item.description
            for item in raw_record.moves
            if item.name == "强化特殊技：风切变·风暴眼"
        ),
    )
    storm_eye_creation = _event_creation(
        key="special:storm-eye-broad-cyclone",
        source=storm_eye_source,
        template=storm_eye_broad_template.ref,
        filters=(
            DamageDealerFilter(VELINA_ID),
            DamageTypeFilter(DamageType.DIRECT),
            MoveIdFilter(EX_SPECIAL_STORM_EYE_MOVE_ID),
        ),
    )
    rules.append(
        _rule(
            "special:storm-eye-broad-cyclone",
            storm_eye_source,
            "强化特殊技：风暴眼召唤广域气旋",
            storm_eye_source.raw_text or "",
            RuleEligibility.ELIGIBLE,
            effects=(storm_eye_creation,),
        )
    )
    turbulence_creation = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1561:core:wind-triggered-turbulence"),
            source=core_source,
            owner=VELINA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DISORDER),
                NotFilter(ElementFilter(Element.WIND)),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=turbulence_ref.template_id,
            unique_per_source_event=True,
        ),
    )
    micro_cyclone_creation = _event_creation(
        key="core:turbulence-summons-micro-cyclone",
        source=core_source,
        template=micro_child_template.ref,
        filters=(
            DamageDealerFilter(VELINA_ID),
            DamageTypeFilter(DamageType.ANOMALY),
            DamageSubtypeFilter(DamageSubtype.TURBULENCE),
        ),
        condition=ScenarioParameterRangeCondition(
            parameter_id=str(WIND_EROSION_STACKS),
            minimum=0,
            maximum=1,
        ),
    )
    broad_cyclone_creation = _event_creation(
        key="core:turbulence-summons-broad-cyclone",
        source=core_source,
        template=broad_child_template.ref,
        filters=(
            DamageDealerFilter(VELINA_ID),
            DamageTypeFilter(DamageType.ANOMALY),
            DamageSubtypeFilter(DamageSubtype.TURBULENCE),
        ),
        condition=ScenarioParameterRangeCondition(
            parameter_id=str(WIND_EROSION_STACKS),
            minimum=2,
        ),
    )
    rules.append(
        _rule(
            "core:wind-triggered-turbulence-candidate",
            core_source,
            "核心被动：非风异常触发风化目标的乱流",
            raw_record.core_levels[0].description,
            RuleEligibility.ELIGIBLE,
            conditions=(ENEMY_WIND_WEATHERED,),
            effects=(
                turbulence_creation,
                micro_cyclone_creation,
                broad_cyclone_creation,
            ),
        )
    )
    ultimate_discharge_creation = _event_creation(
        key="extra-ability:ultimate-wind-discharge",
        source=extra_source,
        template=ultimate_discharge_ref,
        filters=(
            DamageDealerFilter(VELINA_ID),
            DamageTypeFilter(DamageType.DIRECT),
            MoveIdFilter(ULTIMATE_MOVE_ID),
        ),
    )
    rules.append(
        _rule(
            "extra-ability:ultimate-wind-discharge",
            extra_source,
            "额外能力：终结技重击命中风化目标异放",
            extra_text,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            conditions=(ENEMY_WIND_WEATHERED,),
            effects=(ultimate_discharge_creation,),
        )
    )
    diagnostics = (
        *direct_diagnostics,
        CalculationDiagnostic(
            diagnostic_id=DiagnosticId("unsupported:character:1561:daze-and-buildup-output"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message=(
                "The source retains Daze, buildup, resource and timing effects. "
                "This result contract does not output those quantities or replay "
                "cooldowns and durations; they do not block damage calculation."
            ),
            blocking=False,
            original_text=core.description,
        ),
    )
    return build_definition(
        character_id=VELINA_ID,
        role=CharacterRole.ANOMALY,
        element=Element.WIND,
        source=core_source,
        entries=(*direct_entries, *wind_entries),
        templates=(
            *direct_templates,
            *wind_templates,
            *discharge_templates,
            micro_child_template,
            broad_child_template,
            storm_eye_broad_template,
            turbulence_template,
        ),
        rules=tuple(rules),
        conditions=conditions,
        parameters=params,
        independent_derived_damage_events=(
            *discharge_derived,
            micro_child_derived,
            broad_child_derived,
            storm_eye_broad_derived,
            turbulence_derived_ref,
        ),
        diagnostics=diagnostics,
    )


__all__ = ["compile_velina", "load_raw_record"]
