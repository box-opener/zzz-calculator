"""Compile Burnice's reviewed Nanoka 3.2 record."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
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
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SnapshotRule,
    StandardCritRule,
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
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DischargeDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from ...moves import DerivedDamageEventTemplateRef
from .config import BurniceCompileConfig
from .reviewed import (
    BLENDER_MOVE_ID,
    BURN_ACTIVE,
    BURNICE_FIRE_ANOMALY_MOVE_ID,
    BURNICE_FIRE_ANOMALY_RECORD_ID,
    BURNICE_FIRE_DISORDER_MOVE_ID,
    BURNICE_ID,
    BURN_THROUGH_STACKS,
    SCORCHED_ACTIVE,
    DOUBLE_EX_STATE_ACTIVE,
    EX_SPECIAL_DOUBLE_MOVE_ID,
    EX_SPECIAL_MOVE_ID,
    FIRE_DISORDER_REMAINING_SECONDS,
    reviewed_mapping,
)


_SPECIAL_EMBER_ID = MoveEntryId("move-entry:character:1171:cinema6-special-ember")
_C6_BURN_TICK_ID = MoveEntryId("move-entry:character:1171:cinema6-extra-burn-tick")
_FIRE_ANOMALY_RECORD = AnomalyRecordId(str(BURNICE_FIRE_ANOMALY_RECORD_ID))
_BURN_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1171:fire-anomaly")
_BURN_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1171:fire-disorder")
_POTENTIAL1_EMBER_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:potential1:blender-finisher-ember"
)
_POTENTIAL1_BLENDER_FULL_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:potential1:blender-full-ember"
)
_SPECIAL_EMBER_TEMPLATE_ID = EventTemplateId("template:character:1171:cinema6-special-ember")
_CINEMA6_SPECIAL_EMBER_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:cinema6:special-ember-child"
)
_CINEMA6_SPECIAL_EMBER_IMPACT_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:cinema6:special-ember-impact-child"
)
_C6_BURN_TICK_TEMPLATE_ID = EventTemplateId("template:character:1171:cinema6-extra-burn-tick")
_CINEMA6_BURN_TICK_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:cinema6:extra-burn-tick-child"
)
_POTENTIAL1_THROW_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:special-throw:main"
)
_POTENTIAL1_THROW_DISCHARGE_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:potential1:special-throw-discharge"
)
_EX_DOUBLE_IMPACT_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:ex-double-impact:main"
)
_BLENDER_FULL_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:blender-full:main"
)
_EX_DOUBLE_FULL_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:ex-double-full:main"
)
_POTENTIAL1_BLENDER_FULL_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:potential1:blender-full-ember"
)
_CINEMA6_SPECIAL_EMBER_FULL_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:cinema6:special-ember-full-child"
)
_CINEMA6_BURN_TICK_FULL_CHILD_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:cinema6:extra-burn-tick-full-child"
)
_EX_DOUBLE_SPRAY_TEMPLATE_ID = EventTemplateId(
    "template:character:1171:ex-double-spray:main"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    found = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(found) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(found)}")
    return float(found[0].group("value"))


def _potential_view(data: Mapping[str, object], potential_level: int) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("potential_level must be between 0 and 6")
    details = data.get("potential_detail")
    if not isinstance(details, Mapping):
        raise ValueError("Burnice source has no potential_detail map")
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
        if not isinstance(detail, Mapping) or not isinstance(detail.get("id"), int):
            raise ValueError(f"Burnice source has no Potential level {potential_level}")
        selected_id = int(detail["id"])

    def is_base(value: object) -> bool:
        return value is None or (
            isinstance(value, (list, tuple)) and (not value or 0 in value)
        )

    def include(value: object) -> bool:
        if is_base(value):
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
            if not isinstance(section, dict) or not isinstance(section.get("description"), list):
                continue
            section["description"] = [
                item
                for item in section["description"]
                if not isinstance(item, dict) or include(item.get("potential"))
            ]
    return view


def load_raw_record(
    data: Mapping[str, object], *, potential_level: int = 0
) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_view(data, potential_level),
        expected_character_id=str(BURNICE_ID),
    )


def _validate_raw(raw: NanokaRawRecord, config: BurniceCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Burnice raw record and compile config IDs must match")
    if raw.name != "柏妮思" or raw.code_name != "Burnice":
        raise ValueError("unexpected Burnice identity")
    if raw.specialty != "异常" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("unexpected Burnice role, element, or rank")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Burnice source must include seven cores and six mindscapes")
    if config.potential_level and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError(f"Burnice source is missing Potential {config.potential_level}")


def _condition(condition_id, label: str, text: str, value: bool = False) -> ScenarioCondition:
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
    effects=(),
    conditions=(),
    parameters=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1171:{key}"),
        owner=BURNICE_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
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
    operation: EffectOperation = EffectOperation.ADD,
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1171:{key}"),
            source=source,
            owner=BURNICE_ID,
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


def _event_creation_effect(
    *,
    key: str,
    source: RuleSource,
    child_template_id: EventTemplateId,
    parent_template_id: EventTemplateId,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1171:{key}"),
            source=source,
            owner=BURNICE_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(BURNICE_ID),
                EventTemplateIdFilter(parent_template_id),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=child_template_id,
            unique_per_source_event=True,
        ),
    )


def _fixed_direct_entry(
    *,
    entry_id: MoveEntryId,
    template_id: EventTemplateId,
    semantic_id: DamageEventSemanticId,
    move_id,
    label: str,
    original_text: str,
    multiplier: float,
    group,
    tags,
    condition_ids=(),
    element: Element = Element.FIRE,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=frozenset(tags),
        element=element,
    )
    entry = MoveCalculationEntry(
        entry_id=entry_id,
        character_id=BURNICE_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=group,
        damage_tags=frozenset(tags),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:{entry_id}:base"),
                label=f"{multiplier * 100:g}%",
                parameter_name=label,
                multiplier=FixedMultiplier(Resolved(multiplier)),
            ),
        ),
        main_damage_event=ref,
        condition_ids=tuple(condition_ids),
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=BURNICE_ID,
        element=element,
        base_source=CurrentAttackValueSource(BURNICE_ID),
        crit_rule=StandardCritRule(BURNICE_ID),
        move_id=move_id,
    )
    return entry, template


def _combined_direct_entry(
    *,
    key: str,
    label: str,
    original_text: str,
    move_id: MoveId,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    element: Element,
    component_keys: tuple[str, ...],
    direct_entries: tuple[MoveCalculationEntry, ...],
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    entries_by_key = {
        str(entry.entry_id).rsplit(":", 1)[-1]: entry
        for entry in direct_entries
    }
    ratios = []
    for component_key in component_keys:
        component = entries_by_key[component_key]
        multiplier = component.multiplier_variants[0].multiplier
        if not isinstance(multiplier, FixedMultiplier) or not isinstance(
            multiplier.value, Resolved
        ):
            raise ValueError(
                f"Burnice source component is unresolved for complete move {key}: {component_key}"
            )
        ratios.append(multiplier.value.value)
    total_ratio = sum(ratios)
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1171:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1171:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=frozenset(tags),
        element=element,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1171:{key}"),
        character_id=BURNICE_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=group,
        damage_tags=frozenset(tags),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1171:{key}:total"),
                label=f"合计倍率 {total_ratio * 100:g}%（各源倍率各计一次）",
                parameter_name="完整招式倍率",
                multiplier=FixedMultiplier(Resolved(total_ratio)),
            ),
        ),
        main_damage_event=ref,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=BURNICE_ID,
        element=element,
        base_source=CurrentAttackValueSource(BURNICE_ID),
        crit_rule=StandardCritRule(BURNICE_ID),
        move_id=move_id,
    )
    return entry, template


def _ember_source_text(raw: NanokaRawRecord) -> str:
    return raw.core_levels[-1].description


def _static_fire_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=_BURN_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1171:fire-anomaly"),
        label="属性异常：灼烧（单跳50%，10秒20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=BURNICE_ID,
        element=Element.FIRE,
        anomaly_triggerer=BURNICE_ID,
        history_record_source=_FIRE_ANOMALY_RECORD,
        crit_rule=NoCritRule(),
        move_id=BURNICE_FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1171:fire-anomaly"),
        character_id=BURNICE_ID,
        move_id=BURNICE_FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（单跳50%，10秒20跳）",
        original_text="静态单人100%火属性异常记录；每0.5秒结算异常效果强度的50%，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1171:fire-anomaly-tick"),
                label="每跳50% × 20",
                parameter_name="灼烧单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=_BURN_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1171:fire-disorder"),
        label="紊乱：灼烧（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=BURNICE_ID,
        element=Element.FIRE,
        disorder_triggerer=BURNICE_ID,
        history_record_source=_FIRE_ANOMALY_RECORD,
        crit_rule=NoCritRule(),
        move_id=BURNICE_FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1171:fire-disorder"),
        character_id=BURNICE_ID,
        move_id=BURNICE_FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧（当前剩余时间）",
        original_text="灼烧紊乱为450% + 当前剩余时间（秒）×100%；不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1171:fire-disorder"),
                label="450% + 当前剩余时间 × 100%",
                parameter_name="灼烧紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=FIRE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.0,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=FIRE_DISORDER_REMAINING_SECONDS,
        label="当前目标灼烧剩余时间（秒）",
        original_text="使用用户选择的当前剩余时间；不模拟灼烧时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _static_ember_entry(
    *,
    suffix: str,
    label: str,
    original_text: str,
    multiplier: float,
    condition_ids=(),
):
    return _fixed_direct_entry(
        entry_id=MoveEntryId(f"move-entry:character:1171:{suffix}"),
        template_id=EventTemplateId(f"template:character:1171:{suffix}"),
        semantic_id=DamageEventSemanticId(f"event:character:1171:{suffix}"),
        move_id=None,
        label=label,
        original_text=original_text,
        multiplier=multiplier,
        group=SkillGroup.ASSIST,
        tags=(DamageTag.ASSIST,),
        condition_ids=condition_ids,
    )


def _static_burn_tick_entry(raw: NanokaRawRecord, multiplier: float):
    ref = DamageEventTemplateRef(
        template_id=_C6_BURN_TICK_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1171:cinema6-extra-burn-tick"),
        label="6影：额外结算一次灼烧（单跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    template = AttributeAnomalyDamageEventTemplate(
        ref=ref,
        damage_dealer=BURNICE_ID,
        element=Element.FIRE,
        anomaly_triggerer=BURNICE_ID,
        history_record_source=_FIRE_ANOMALY_RECORD,
        crit_rule=NoCritRule(),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=_C6_BURN_TICK_ID,
        character_id=BURNICE_ID,
        move_id=None,
        display_name="6影：额外结算一次灼烧（单跳）",
        original_text=raw.mindscapes[5].description,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1171:cinema6-extra-burn-tick"),
                label="原灼烧单跳倍率 × 18 = 900%",
                parameter_name="灼烧额外单跳倍率",
                multiplier=FixedMultiplier(Resolved(multiplier)),
            ),
        ),
        main_damage_event=ref,
        condition_ids=(BURN_ACTIVE, DOUBLE_EX_STATE_ACTIVE),
    )
    return entry, template


def _special_throw_source_multipliers(raw: NanokaRawRecord):
    source_move = next(
        (item for item in raw.moves if item.name == "强化特殊技：灼热抛接法"),
        None,
    )
    if source_move is None:
        raise ValueError("Burnice source is missing the Potential 1 Special Throw description")
    values = tuple(
        float(value)
        for value in re.findall(r"([\d.]+)%", _plain(source_move.description))
    )
    if len(values) != 6:
        raise ValueError(
            "Burnice Special Throw must define six Discharge source multipliers; "
            f"found {len(values)}"
        )
    ether, electric, fire, physical, ice, wind = (value / 100.0 for value in values)
    return (
        (Element.ETHER, ether),
        (Element.XUANMO, ether),
        (Element.ELECTRIC, electric),
        (Element.FIRE, fire),
        (Element.PHYSICAL, physical),
        (Element.LINREN, physical),
        (Element.ICE, ice),
        (Element.LIESHUANG, ice),
        (Element.WIND, wind),
    )


def compile_burnice(
    config: BurniceCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=BURNICE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping(potential_level=config.potential_level),
        id_namespace="character:1171",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    raw_descriptions = {item.name: item.description for item in raw_record.moves}
    complete_specs = (
        (
            "blender-full",
            "普通攻击：炽焰搅拌式（持续喷射+终结一击）",
            "普通攻击：炽焰搅拌式",
            BLENDER_MOVE_ID,
            SkillGroup.BASIC_ATTACK,
            Element.FIRE,
            ("blender-spray", "blender-finisher"),
        ),
        (
            "ex-single-full",
            "强化特殊技：灼热摇荡法（持续喷射+火焰冲击）",
            "强化特殊技：灼热摇荡法",
            EX_SPECIAL_MOVE_ID,
            SkillGroup.SPECIAL_ATTACK,
            Element.FIRE,
            ("ex-single-spray", "ex-single-impact"),
        ),
        (
            "ex-double-full",
            "强化特殊技：灼热摇荡法·双份（持续喷射+火焰冲击）",
            "强化特殊技：灼热摇荡法·双份",
            EX_SPECIAL_DOUBLE_MOVE_ID,
            SkillGroup.SPECIAL_ATTACK,
            Element.FIRE,
            ("ex-double-spray", "ex-double-impact"),
        ),
    )
    complete_entries: dict[str, MoveCalculationEntry] = {}
    for key, label, source_name, move_id, group, element, component_keys in complete_specs:
        component_tags = frozenset(
            tag
            for entry in direct_entries
            if str(entry.entry_id).rsplit(":", 1)[-1] in component_keys
            for tag in entry.damage_tags
        )
        complete_entry, complete_template = _combined_direct_entry(
            key=key,
            label=label,
            original_text=raw_descriptions[source_name],
            move_id=move_id,
            group=group,
            tags=component_tags,
            element=element,
            component_keys=component_keys,
            direct_entries=tuple(direct_entries),
        )
        entries.append(complete_entry)
        templates.append(complete_template)
        complete_entries[key] = complete_entry
    conditions = [
        _condition(BURN_ACTIVE, "目标当前处于火属性灼烧状态", "使用当前异常状态，不模拟持续时间。"),
        _condition(
            SCORCHED_ACTIVE,
            "目标当前处于核心被动施加的灼伤状态",
            raw_record.core_levels[config.core_level - 1].description,
        ),
        _condition(
            DOUBLE_EX_STATE_ACTIVE,
            "当前处于强化特殊技·双份命中后的状态",
            raw_record.mindscapes[5].description,
        ),
    ]
    rules: list[CalculationRuleItem] = []
    diagnostics = list(direct_diagnostics)
    parameters: list[ScenarioIntegerParameter] = []

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        BURNICE_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    ember_ratio = _number(
        core.description,
        r"等同于柏妮思(?P<value>[\d.]+)%攻击力的火属性伤害",
        "Burnice Core Ember damage ratio",
    ) / 100.0
    c1_text = raw_record.mindscapes[0].description
    c1_ember_bonus = (
        _number(
            raw_record.mindscapes[0].description,
            r"\[余烬\]效果的伤害倍率提升.*?攻击力的(?P<value>[\d.]+)%",
            "Burnice Cinema 1 Ember multiplier increase",
        ) / 100.0
        if config.cinema_level >= 1
        else 0.0
    )

    # Core Ember is a one-hit Support Attack query. The selected entry represents
    # one current proc; the source's 1.5-second throttle and fuel history are not replayed.
    ember_entry, ember_template = _static_ember_entry(
        suffix="core-ember",
        label="核心被动：余烬（单次支援攻击）",
        original_text=core.description + (f"\n{c1_text}" if config.cinema_level >= 1 else ""),
        multiplier=ember_ratio + c1_ember_bonus,
        condition_ids=(SCORCHED_ACTIVE,),
    )
    entries.append(ember_entry)
    templates.append(ember_template)

    ap_source = PanelStatDerivedValue(
        source_character_id=BURNICE_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        coefficient=Resolved(0.001),
        cap_max=Resolved(0.30),
    )
    ember_template_filter = DamageTypeFilter(DamageType.DIRECT)
    rules.append(
        _rule(
            "core:ember-current-proficiency-damage",
            core_source,
            "核心被动：余烬伤害按当前异常精通提升（最高30%）",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:ember-current-proficiency-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ap_source,
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(BURNICE_ID),
                        AnyFilter(
                            (
                                EventTemplateIdFilter(ember_template.ref.template_id),
                                EventTemplateIdFilter(_POTENTIAL1_EMBER_TEMPLATE_ID),
                                EventTemplateIdFilter(_POTENTIAL1_BLENDER_FULL_CHILD_TEMPLATE_ID),
                                EventTemplateIdFilter(_SPECIAL_EMBER_TEMPLATE_ID),
                                EventTemplateIdFilter(_CINEMA6_SPECIAL_EMBER_CHILD_TEMPLATE_ID),
                                EventTemplateIdFilter(_CINEMA6_SPECIAL_EMBER_IMPACT_CHILD_TEMPLATE_ID),
                                EventTemplateIdFilter(_CINEMA6_SPECIAL_EMBER_FULL_CHILD_TEMPLATE_ID),
                            )
                        ),
                        ember_template_filter,
                    ),
                ),
            ),
        )
    )

    if config.cinema_level >= 6:
        c6_source = source_for(
            BURNICE_ID,
            "cinema6",
            EffectSourceType.CINEMA,
            raw_record.mindscapes[5].name,
            raw_record.mindscapes[5].description,
        )
        special_ratio = 0.60 + c1_ember_bonus
        special_entry, special_template = _static_ember_entry(
            suffix="cinema6-special-ember",
            label="6影：特殊余烬（单次支援攻击）",
            original_text=raw_record.mindscapes[5].description,
            multiplier=special_ratio,
            condition_ids=(DOUBLE_EX_STATE_ACTIVE,),
        )
        special_entry = replace(
            special_entry,
            entry_id=_SPECIAL_EMBER_ID,
            main_damage_event=replace(
                special_entry.main_damage_event,
                template_id=_SPECIAL_EMBER_TEMPLATE_ID,
                semantic_id=DamageEventSemanticId("event:character:1171:cinema6-special-ember"),
            ),
        )
        special_template = replace(
            special_template,
            ref=special_entry.main_damage_event,
        )
        entries.append(special_entry)
        templates.append(special_template)
        c6_tick_entry, c6_tick_template = _static_burn_tick_entry(
            raw_record,
            multiplier=18 * 0.5,
        )
        entries.append(c6_tick_entry)
        templates.append(c6_tick_template)

        special_child_rule_id = RuleItemId(
            "rule:character:1171:cinema6:special-ember"
        )
        special_child_ref = replace(
            special_template.ref,
            template_id=_CINEMA6_SPECIAL_EMBER_CHILD_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:cinema6:special-ember-child"
            ),
            source_rule_item_id=special_child_rule_id,
        )
        special_child_template = replace(special_template, ref=special_child_ref)
        templates.append(special_child_template)
        special_impact_child_ref = replace(
            special_template.ref,
            template_id=_CINEMA6_SPECIAL_EMBER_IMPACT_CHILD_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:cinema6:special-ember-impact-child"
            ),
            source_rule_item_id=special_child_rule_id,
        )
        special_impact_child_template = replace(
            special_template,
            ref=special_impact_child_ref,
        )
        templates.append(special_impact_child_template)
        special_full_child_ref = replace(
            special_template.ref,
            template_id=_CINEMA6_SPECIAL_EMBER_FULL_CHILD_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:cinema6:special-ember-full-child"
            ),
            source_rule_item_id=special_child_rule_id,
        )
        templates.append(replace(special_template, ref=special_full_child_ref))

        burn_child_rule_id = RuleItemId(
            "rule:character:1171:cinema6:double-ex-extra-burn-tick"
        )
        burn_child_ref = replace(
            c6_tick_template.ref,
            template_id=_CINEMA6_BURN_TICK_CHILD_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:cinema6:extra-burn-tick-child"
            ),
            source_rule_item_id=burn_child_rule_id,
        )
        burn_child_template = replace(c6_tick_template, ref=burn_child_ref)
        templates.append(burn_child_template)
        burn_full_child_ref = replace(
            c6_tick_template.ref,
            template_id=_CINEMA6_BURN_TICK_FULL_CHILD_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:cinema6:extra-burn-tick-full-child"
            ),
            source_rule_item_id=burn_child_rule_id,
        )
        templates.append(replace(c6_tick_template, ref=burn_full_child_ref))

        special_ember_ref = DerivedDamageEventTemplateRef(
            template=special_child_ref,
            multiplier=FixedMultiplier(Resolved(special_ratio)),
        )
        special_impact_ember_ref = DerivedDamageEventTemplateRef(
            template=special_impact_child_ref,
            multiplier=FixedMultiplier(Resolved(special_ratio)),
        )
        extra_burn_ref = DerivedDamageEventTemplateRef(
            template=burn_child_ref,
            multiplier=FixedMultiplier(Resolved(9.0)),
        )
        special_full_ref = DerivedDamageEventTemplateRef(
            template=special_full_child_ref,
            multiplier=FixedMultiplier(Resolved(special_ratio)),
        )
        burn_full_ref = DerivedDamageEventTemplateRef(
            template=burn_full_child_ref,
            multiplier=FixedMultiplier(Resolved(9.0)),
        )
        double_impact_index = next(
            index
            for index, item in enumerate(entries)
            if item.entry_id == MoveEntryId("move-entry:character:1171:ex-double-impact")
        )
        entries[double_impact_index] = replace(
            entries[double_impact_index],
            derived_damage_events=(
                *entries[double_impact_index].derived_damage_events,
                extra_burn_ref,
            ),
        )
        double_spray_index = next(
            index
            for index, item in enumerate(entries)
            if item.entry_id == MoveEntryId("move-entry:character:1171:ex-double-spray")
        )
        entries[double_spray_index] = replace(
            entries[double_spray_index],
            derived_damage_events=(
                *entries[double_spray_index].derived_damage_events,
                special_ember_ref,
            ),
        )
        entries[double_impact_index] = replace(
            entries[double_impact_index],
            derived_damage_events=(
                *entries[double_impact_index].derived_damage_events,
                special_impact_ember_ref,
            ),
        )
        full_entry = complete_entries["ex-double-full"]
        full_entry_index = next(
            index for index, item in enumerate(entries)
            if item.entry_id == full_entry.entry_id
        )
        entries[full_entry_index] = replace(
            full_entry,
            derived_damage_events=(
                *full_entry.derived_damage_events,
                special_full_ref,
                burn_full_ref,
            ),
        )
        c6_spray_special_effect = _event_creation_effect(
            key="cinema6:double-ex-spray-special-ember",
            source=c6_source,
            child_template_id=special_child_ref.template_id,
            parent_template_id=_EX_DOUBLE_SPRAY_TEMPLATE_ID,
        )
        c6_impact_special_effect = _event_creation_effect(
            key="cinema6:double-ex-impact-special-ember",
            source=c6_source,
            child_template_id=special_impact_child_ref.template_id,
            parent_template_id=_EX_DOUBLE_IMPACT_TEMPLATE_ID,
        )
        c6_full_special_effect = _event_creation_effect(
            key="cinema6:double-ex-full-special-ember",
            source=c6_source,
            child_template_id=special_full_child_ref.template_id,
            parent_template_id=_EX_DOUBLE_FULL_TEMPLATE_ID,
        )
        c6_burn_rule = _event_creation_effect(
            key="cinema6:double-ex-extra-burn-tick",
            source=c6_source,
            child_template_id=burn_child_ref.template_id,
            parent_template_id=_EX_DOUBLE_IMPACT_TEMPLATE_ID,
        )
        c6_full_burn_rule = _event_creation_effect(
            key="cinema6:double-ex-full-extra-burn-tick",
            source=c6_source,
            child_template_id=burn_full_child_ref.template_id,
            parent_template_id=_EX_DOUBLE_FULL_TEMPLATE_ID,
        )
        rules.append(
            _rule(
                "cinema6:special-ember",
                c6_source,
                "6影：双份强化特殊技额外触发一次特殊余烬",
                raw_record.mindscapes[5].description,
                RuleEligibility.ELIGIBLE,
                conditions=(DOUBLE_EX_STATE_ACTIVE,),
                effects=(
                    c6_spray_special_effect,
                    c6_impact_special_effect,
                    c6_full_special_effect,
                ),
            )
        )
        rules.append(
            _rule(
                "cinema6:double-ex-extra-burn-tick",
                c6_source,
                "6影：火焰冲击命中灼烧目标时额外结算一个灼烧单跳",
                raw_record.mindscapes[5].description,
                RuleEligibility.ELIGIBLE,
                conditions=(DOUBLE_EX_STATE_ACTIVE, BURN_ACTIVE),
                effects=(c6_burn_rule, c6_full_burn_rule),
            )
        )
        rules.append(
            _rule(
                "cinema6:fire-resistance-ignore-state",
                c6_source,
                "6影：双份强化特殊技期间火属性抗性无视",
                raw_record.mindscapes[5].description,
                RuleEligibility.ELIGIBLE,
                conditions=(DOUBLE_EX_STATE_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema6:fire-resistance-ignore",
                        c6_source,
                        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                        Resolved(0.25),
                        target=EffectTarget.TEAM,
                        filters=(
                            DamageDealerFilter(BURNICE_ID),
                            ElementFilter(Element.FIRE),
                            AnyFilter(
                                (
                                    EventTemplateIdFilter(_EX_DOUBLE_SPRAY_TEMPLATE_ID),
                                    EventTemplateIdFilter(_EX_DOUBLE_IMPACT_TEMPLATE_ID),
                                    EventTemplateIdFilter(_EX_DOUBLE_FULL_TEMPLATE_ID),
                                    EventTemplateIdFilter(_SPECIAL_EMBER_TEMPLATE_ID),
                                    EventTemplateIdFilter(_CINEMA6_SPECIAL_EMBER_CHILD_TEMPLATE_ID),
                                    EventTemplateIdFilter(_CINEMA6_SPECIAL_EMBER_IMPACT_CHILD_TEMPLATE_ID),
                                    EventTemplateIdFilter(_CINEMA6_SPECIAL_EMBER_FULL_CHILD_TEMPLATE_ID),
                                    EventTemplateIdFilter(_BURN_ANOMALY_TEMPLATE_ID),
                                    EventTemplateIdFilter(_C6_BURN_TICK_TEMPLATE_ID),
                                    EventTemplateIdFilter(_CINEMA6_BURN_TICK_CHILD_TEMPLATE_ID),
                                    EventTemplateIdFilter(_CINEMA6_BURN_TICK_FULL_CHILD_TEMPLATE_ID),
                                )
                            ),
                        ),
                    ),
                ),
            )
        )
    else:
        rules.append(
            _rule(
                "cinema6:fire-resistance-ignore-state",
                source_for(BURNICE_ID, "cinema6", EffectSourceType.CINEMA, raw_record.mindscapes[5].name, raw_record.mindscapes[5].description),
                "6影：双份强化特殊技期间火属性抗性无视",
                raw_record.mindscapes[5].description,
                RuleEligibility.INELIGIBLE,
            )
        )

    # A normal static Burn record uses the current Burnice panel and the standard
    # Fire anomaly profile; it is not a timeline or a direct-damage proxy.
    fire_entries, fire_templates, disorder_remaining = _static_fire_entries(raw_record)
    entries.extend(fire_entries)
    templates.extend(fire_templates)
    parameters.append(disorder_remaining)

    # Potential 1–6 effects are continuous excess-initial-ER panel values. The
    # source's cooldown/fuel progression is intentionally not simulated.
    if config.potential_level >= 2:
        potential_detail = next(
            item for item in raw_record.potential_details if item.level == config.potential_level
        )
        potential_description = potential_detail.description
        am_per_step = _number(
            potential_description,
            r"异常掌控额外提升(?P<value>[\d.]+)点",
            "Burnice Potential Anomaly Mastery per initial ER interval",
        )
        damage_per_step = _number(
            potential_description,
            r"造成的伤害提升(?P<value>[\d.]+)%",
            "Burnice Potential damage per initial ER interval",
        ) / 100.0
        potential_source = source_for(
            BURNICE_ID,
            f"potential-{config.potential_level}",
            EffectSourceType.SPECIAL_MECHANISM,
            potential_detail.level_show_name,
            potential_description,
        )
        initial_er_excess = PanelStatDerivedValue(
            source_character_id=BURNICE_ID,
            source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
            threshold=Resolved(1.8),
            step_size=Resolved(0.1),
            coefficient=Resolved(am_per_step),
            cap_max=Resolved(25.0),
        )
        initial_er_damage = PanelStatDerivedValue(
            source_character_id=BURNICE_ID,
            source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
            threshold=Resolved(1.8),
            step_size=Resolved(0.1),
            coefficient=Resolved(damage_per_step),
            cap_max=Resolved(0.20),
        )
        rules.append(
            _rule(
                f"potential{config.potential_level}:initial-er-bonuses",
                potential_source,
                f"潜能{config.potential_level}：初始能量回复增益（连续比例）",
                potential_description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        f"potential{config.potential_level}:anomaly-mastery",
                        potential_source,
                        CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
                        initial_er_excess,
                        target=EffectTarget.SELF,
                    ),
                    _modifier(
                        f"potential{config.potential_level}:damage-bonus",
                        potential_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        initial_er_damage,
                        target=EffectTarget.TEAM,
                        filters=(DamageDealerFilter(BURNICE_ID),),
                    ),
                ),
            )
        )

    # C4 raises the event-only Crit Rate of Enhanced Special and Support Attack
    # hits; it never changes Burnice's formal panel Crit Rate.
    c4_source = source_for(
        BURNICE_ID,
        "cinema4",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[3].name,
        raw_record.mindscapes[3].description,
    )
    c4_eligible = config.cinema_level >= 4
    rules.append(
        _rule(
            "cinema4:event-crit-rate",
            c4_source,
            "4影：强化特殊技与支援攻击命中时暴击率+30%",
            raw_record.mindscapes[3].description,
            RuleEligibility.ELIGIBLE if c4_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:event-crit-rate",
                    c4_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(0.30),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(BURNICE_ID),
                        AnyFilter(
                            (
                                DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                                DamageTagFilter(DamageTag.ASSIST),
                            )
                        ),
                        DamageTypeFilter(DamageType.DIRECT),
                    ),
                ),
            ) if c4_eligible else (),
        )
    )

    c2_source = source_for(
        BURNICE_ID,
        "cinema2",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[1].name,
        raw_record.mindscapes[1].description,
    )
    if config.cinema_level >= 2:
        parameters.append(
            ScenarioIntegerParameter(
                parameter_id=BURN_THROUGH_STACKS,
                label="当前目标热意洞穿层数",
                original_text=raw_record.mindscapes[1].description,
                resolution=ParameterResolution.USER_SELECTED,
                value=5,
                minimum=0,
                maximum=5,
            )
        )
        rules.append(
            _rule(
                "cinema2:target-burn-through-stacks",
                c2_source,
                "2影：热意洞穿层数提高本次攻击穿透率",
                raw_record.mindscapes[1].description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema2:target-burn-through-stacks",
                        c2_source,
                        CalculationNode.DAMAGE_PENETRATION_RATE,
                        ScenarioParameterDerivedValue(
                            parameter_id=str(BURN_THROUGH_STACKS),
                            coefficient=Resolved(0.04),
                            cap_max=Resolved(0.20),
                        ),
                        target=EffectTarget.TEAM,
                    ),
                ),
            )
        )
    else:
        rules.append(
            _rule(
                "cinema2:target-burn-through-stacks",
                c2_source,
                "2影：热意洞穿层数提高本次攻击穿透率",
                raw_record.mindscapes[1].description,
                RuleEligibility.INELIGIBLE,
            )
        )

    # Core and Cinema level fields select values, while these notes retain
    # source-only counters and durations outside the calculation result.
    extra_source = source_for(
        BURNICE_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    rules.append(
        _rule(
            "extra-ability:anomaly-buildup-and-burn-duration",
            extra_source,
            "额外能力：异常积蓄提升（状态持续时间不模拟）",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId("unsupported:character:1171:extra-ability:buildup-and-duration"),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message="异常积蓄与灼烧持续时间不属于当前伤害数值结果；角色资格按队伍成员计算。",
                    blocking=False,
                    original_text=core.extra_ability_description,
                ),
            ),
        )
    )

    burn_source = source_for(
        BURNICE_ID,
        "core-fuel-state",
        EffectSourceType.SPECIAL_MECHANISM,
        "燃油特调与燃点状态",
        core.description,
    )
    rules.append(
        _rule(
            "core:fuel-state-source-only",
            burn_source,
            "核心被动：燃油特调状态（燃点资源与冷却不模拟）",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId("unsupported:character:1171:core:fuel-resource-and-cooldown"),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message="燃点累计、消耗、灼伤触发历史及1.5秒触发间隔不模拟；可以单独查询已知的单次余烬事件。",
                    blocking=False,
                    original_text=core.description,
                ),
            ),
        )
    )

    # Cinema 3/5 skill growth is already folded into effective_skill_level.
    for level in (3, 5):
        mindscape = raw_record.mindscapes[level - 1]
        source = source_for(
            BURNICE_ID,
            f"cinema{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级+2",
                mindscape.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    if config.potential_level >= 1:
        potential_detail = next(
            item for item in raw_record.potential_details if item.level == config.potential_level
        )
        potential_source = source_for(
            BURNICE_ID,
            "potential1:blender-ember-trigger",
            EffectSourceType.SPECIAL_MECHANISM,
            potential_detail.level_show_name,
            potential_detail.description,
        )
        throw_source = next(
            item for item in raw_record.moves if item.name == "强化特殊技：灼热抛接法"
        )
        throw_rule_id = RuleItemId(
            "rule:character:1171:potential1:special-throw-discharge"
        )
        discharge_ref = DamageEventTemplateRef(
            template_id=_POTENTIAL1_THROW_DISCHARGE_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:potential1:special-throw-discharge"
            ),
            label="强化特殊技：灼热抛接法（所选异常记录的异放）",
            damage_type=DamageType.ANOMALY,
            damage_subtype=DamageSubtype.DISCHARGE,
            element=Element.FIRE,
            source_rule_item_id=throw_rule_id,
        )
        discharge_template = DischargeDamageEventTemplate(
            ref=discharge_ref,
            damage_dealer=BURNICE_ID,
            element=Element.FIRE,
            discharge_triggerer=BURNICE_ID,
            history_record_source=None,
            crit_rule=NoCritRule(),
            move_id=None,
            multiplier_from_source_event=False,
            source_multiplier_by_element=_special_throw_source_multipliers(raw_record),
        )
        templates.append(discharge_template)
        throw_entry_index = next(
            index
            for index, item in enumerate(entries)
            if item.entry_id == MoveEntryId("move-entry:character:1171:special-throw")
        )
        throw_entry = entries[throw_entry_index]
        entries[throw_entry_index] = replace(
            throw_entry,
            derived_damage_events=(
                *throw_entry.derived_damage_events,
                DerivedDamageEventTemplateRef(
                    template=discharge_ref,
                    multiplier=FixedMultiplier(Resolved(1.0)),
                ),
            ),
        )
        rules.append(
            _rule(
                "potential1:special-throw-discharge",
                potential_source,
                "潜能1：灼热抛接命中异常目标时按所选异常来源结算一次异放",
                throw_source.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _event_creation_effect(
                        key="potential1:special-throw-discharge",
                        source=potential_source,
                        child_template_id=discharge_ref.template_id,
                        parent_template_id=_POTENTIAL1_THROW_TEMPLATE_ID,
                    ),
                ),
            )
        )
        blender_entry = next(
            item for item in entries if item.entry_id == MoveEntryId("move-entry:character:1171:blender-finisher")
        )
        blender_entry_index = next(
            index
            for index, item in enumerate(entries)
            if item.entry_id == blender_entry.entry_id
        )
        potential1_rule_id = RuleItemId(
            "rule:character:1171:potential1:blender-extra-ember"
        )
        potential1_ember_ref = replace(
            ember_template.ref,
            template_id=_POTENTIAL1_EMBER_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:potential1:blender-finisher-ember"
            ),
            source_rule_item_id=potential1_rule_id,
        )
        potential1_ember_template = replace(
            ember_template,
            ref=potential1_ember_ref,
        )
        templates.append(potential1_ember_template)
        potential1_ember_full_ref = replace(
            ember_template.ref,
            template_id=_POTENTIAL1_BLENDER_FULL_CHILD_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId(
                "event:character:1171:potential1:blender-full-ember"
            ),
            source_rule_item_id=potential1_rule_id,
        )
        templates.append(replace(ember_template, ref=potential1_ember_full_ref))
        blender_ember_ref = DerivedDamageEventTemplateRef(
            template=potential1_ember_ref,
            multiplier=FixedMultiplier(Resolved(ember_ratio + c1_ember_bonus)),
        )
        entries[blender_entry_index] = replace(
            blender_entry,
            derived_damage_events=(
                *blender_entry.derived_damage_events,
                blender_ember_ref,
            ),
        )
        blender_full = complete_entries["blender-full"]
        blender_full_index = next(
            index for index, item in enumerate(entries)
            if item.entry_id == blender_full.entry_id
        )
        entries[blender_full_index] = replace(
            blender_full,
            derived_damage_events=(
                *blender_full.derived_damage_events,
                DerivedDamageEventTemplateRef(
                    template=potential1_ember_full_ref,
                    multiplier=FixedMultiplier(Resolved(ember_ratio + c1_ember_bonus)),
                ),
            ),
        )
        # The selected finisher is one authored point for the extra Support Ember.
        ember_effect = EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId("effect:character:1171:potential1:blender-finisher-ember"),
                source=potential_source,
                owner=BURNICE_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(BURNICE_ID),
                    EventTemplateIdFilter(
                        EventTemplateId("template:character:1171:blender-finisher:main")
                    ),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=potential1_ember_ref.template_id,
                unique_per_source_event=True,
            ),
        )
        blender_full_ember_effect = _event_creation_effect(
            key="potential1:blender-full-extra-ember",
            source=potential_source,
            child_template_id=potential1_ember_full_ref.template_id,
            parent_template_id=_BLENDER_FULL_TEMPLATE_ID,
        )
        rules.append(
            _rule(
                "potential1:blender-extra-ember",
                potential_source,
                "潜能1：炽焰搅拌式终结一击额外触发一次余烬",
                potential_detail.description,
                RuleEligibility.ELIGIBLE,
                effects=(ember_effect, blender_full_ember_effect),
            )
        )

    diagnostics.append(
        CalculationDiagnostic(
            diagnostic_id=DiagnosticId("unsupported:character:1171:resource-and-daze-results"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message="燃点、流火、能量消耗、抗打断、失衡值及招式持续时间不输出为伤害数值。",
            blocking=False,
            original_text=raw_record.core_levels[-1].description,
        )
    )

    return build_definition(
        character_id=BURNICE_ID,
        role=CharacterRole.ANOMALY,
        element=Element.FIRE,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


__all__ = ["compile_burnice", "load_raw_record"]
