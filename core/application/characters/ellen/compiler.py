"""Reviewed compiler for Ellen (character:1191), Nanoka 3.2."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    BattleEventKind,
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
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    ScenarioParameterRangeCondition,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic
from ...element_scope import element_scope_filter
from ...ids import (
    DamageEventSemanticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
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
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import EllenCompileConfig
from .reviewed import (
    ELLEN_C6_FEAST_STACKS,
    ELLEN_C6_PENETRATION_ACTIVE,
    ELLEN_CHILL_CHARGES_FOR_EX,
    ELLEN_EXTRA_ABILITY_ICE_STACKS,
    ELLEN_FROST_EDGE_TARGET_SIZE,
    ELLEN_ICE_ANOMALY_MOVE_ID,
    ELLEN_ICE_ANOMALY_RECORD_ID,
    ELLEN_ICE_BLADE_WAVE_READY,
    ELLEN_ICE_DISORDER_MOVE_ID,
    ELLEN_ICE_DISORDER_REMAINING_SECONDS,
    ELLEN_ICE_MODE_ACTIVE,
    ELLEN_ID,
    reviewed_mapping,
)


_ICE_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1191:ice-anomaly")
_ICE_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1191:ice-disorder")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str, value: bool = False) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(key: str, source_type: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(ELLEN_ID, key, source_type, label, text)


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
        rule_id=RuleItemId(f"rule:character:1191:{key}"),
        owner=ELLEN_ID,
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
            effect_id=EffectId(f"effect:character:1191:{key}"),
            source=source,
            owner=ELLEN_ID,
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


def _potential_view(data: Mapping[str, object], potential_level: int) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("Ellen potential level must be between 0 and 6")
    view = deepcopy(dict(data))
    potential_details = view.get("potential_detail")
    if not isinstance(potential_details, Mapping):
        raise ValueError("Ellen source is missing potential_detail")
    selected = next(
        (
            item
            for item in potential_details.values()
            if isinstance(item, Mapping) and item.get("level") == potential_level
        ),
        None,
    ) if potential_level else None
    selected_id = int(selected["id"]) if isinstance(selected, Mapping) else None

    def base_variant(value: object) -> bool:
        return value is None or (
            isinstance(value, (list, tuple)) and (not value or 0 in value)
        )

    def included(value: object) -> bool:
        if base_variant(value):
            return True
        return (
            selected_id is not None
            and isinstance(value, (list, tuple))
            and selected_id in value
        )

    skills = view.get("skill")
    if isinstance(skills, dict):
        for section in skills.values():
            if isinstance(section, dict) and isinstance(section.get("description"), list):
                section["description"] = [
                    item
                    for item in section["description"]
                    if isinstance(item, dict) and included(item.get("potential"))
                ]
    passive = view.get("passive")
    levels = passive.get("level") if isinstance(passive, dict) else None
    if not isinstance(levels, dict):
        raise ValueError("Ellen source is missing passive level data")
    first_id, last_id = (1191501, 1191507) if potential_level == 0 else (1191508, 1191514)
    passive["level"] = {
        key: item
        for key, item in levels.items()
        if isinstance(item, Mapping)
        and isinstance(item.get("id"), int)
        and first_id <= int(item["id"]) <= last_id
    }
    return view


def load_raw_record(data: Mapping[str, object], *, potential_level: int = 0) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_view(data, potential_level),
        expected_character_id=str(ELLEN_ID),
    )


def _direct_composite(
    raw: NanokaRawRecord,
    config: EllenCompileConfig,
    *,
    key: str,
    label: str,
    source_name: str,
    skill_group: SkillGroup,
    tags: frozenset[DamageTag],
    element: Element,
    parameter_components: tuple[tuple[str, str], ...],
    move_id: MoveId,
    condition_ids=(),
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    raw_moves = raw_move_index(raw)
    level = effective_skill_level(config, skill_group)
    parts: list[float] = []
    for parameter_name, curve_id in parameter_components:
        diagnostics: list[CalculationDiagnostic] = []
        part = raw_multiplier(
            raw_moves,
            source_name,
            parameter_name,
            level,
            f"character:1191:{key}",
            diagnostics,
            source_skill_id=curve_id,
        )
        if diagnostics or not isinstance(part, float):
            raise ValueError(f"Ellen source is missing composite component {key}:{parameter_name}")
        parts.append(part)
    multiplier = sum(parts)
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1191:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1191:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=tags,
        element=element,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=ELLEN_ID,
        element=element,
        base_source=CurrentAttackValueSource(ELLEN_ID),
        crit_rule=StandardCritRule(ELLEN_ID),
        move_id=move_id,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1191:{key}"),
        character_id=ELLEN_ID,
        move_id=move_id,
        display_name=label,
        original_text=raw_moves[source_name].description,
        skill_group=skill_group,
        damage_tags=tags,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1191:{key}:total"),
                label="完整招式总倍率",
                parameter_name="总倍率",
                multiplier=FixedMultiplier(Resolved(multiplier)),
            ),
        ),
        main_damage_event=ref,
        condition_ids=tuple(condition_ids),
    )
    return entry, template


def _anomaly_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=_ICE_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1191:ice-anomaly"),
        label="属性异常：碎冰（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=ELLEN_ID,
        element=Element.ICE,
        anomaly_triggerer=ELLEN_ID,
        history_record_source=ELLEN_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ELLEN_ICE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1191:ice-anomaly"),
        character_id=ELLEN_ID,
        move_id=ELLEN_ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：碎冰（10秒满异常）",
        original_text="按规范静态单人100%积蓄冰异常；使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1191:ice-anomaly"),
                label="碎冰500%（10秒）",
                parameter_name="碎冰倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=_ICE_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1191:ice-disorder"),
        label="紊乱：碎冰（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ELLEN_ID,
        element=Element.ICE,
        disorder_triggerer=ELLEN_ID,
        history_record_source=ELLEN_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ELLEN_ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1191:ice-disorder"),
        character_id=ELLEN_ID,
        move_id=ELLEN_ICE_DISORDER_MOVE_ID,
        display_name="紊乱：碎冰（当前剩余时间）",
        original_text="冰紊乱倍率为450% + floor(t)×7.5%；剩余时间是当前输入，不推演时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1191:ice-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="冰紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ScenarioParameterId(ELLEN_ICE_DISORDER_REMAINING_SECONDS),
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=ScenarioParameterId(ELLEN_ICE_DISORDER_REMAINING_SECONDS),
        label="冰异常剩余持续时间（秒）",
        original_text="使用本次选择的剩余时间，范围0–10秒；不模拟时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _frost_edge_followups(
    raw: NanokaRawRecord,
    config: EllenCompileConfig,
    entries,
    source: RuleSource,
):
    if config.potential_level < 1:
        return (), (), (), ()
    raw_moves = raw_move_index(raw)
    rule_id = RuleItemId("rule:character:1191:potential1:frost-edge-follow-up")
    templates: list[DirectDamageEventTemplate] = []
    refs_by_parent: dict[MoveEntryId, list[DerivedDamageEventTemplateRef]] = {}
    effects: list[EventCreationEffect] = []
    parent_keys = ("basic-ice-3", "ex-whirlwind", "dodge-counter", "assist-strike-cruising-shark")
    size_components = {
        1: (("1191027", 3.0),),
        2: (("1191027", 3.0), ("1191028", 3.0)),
        3: (("1191027", 3.0), ("1191028", 6.0)),
    }
    for parent_key in parent_keys:
        parent_entry = next(
            item for item in entries
            if str(item.entry_id) == f"move-entry:character:1191:{parent_key}"
        )
        parent_template_id = parent_entry.main_damage_event.template_id
        child_refs: list[DerivedDamageEventTemplateRef] = []
        effects.append(
            EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId(f"effect:character:1191:potential1:frost-edge-unknown-size:{parent_key}"),
                    source=source,
                    owner=ELLEN_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    condition=ScenarioParameterRangeCondition(ELLEN_FROST_EDGE_TARGET_SIZE, minimum=0, maximum=0),
                    filters=(DamageTypeFilter(DamageType.DIRECT), DamageDealerFilter(ELLEN_ID), EventTemplateIdFilter(parent_template_id)),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    unresolved_template=Unresolved(
                        reason=UnresolvedReason.MISSING_DATA,
                        notes="霜锋的倍率取决于目标体型；请选择小、中或大型目标。此项仅影响本次自动追击，父招式仍按已知倍率结算。",
                        original_text="对中/大体型的敌人会分别额外造成多段冰属性伤害",
                    ),
                    unique_per_source_event=True,
                ),
            )
        )
        for size, components in size_components.items():
            level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
            value = sum(
                float(raw_multiplier(
                    raw_moves,
                    "普通攻击：霜锋",
                    "对小体型敌人伤害倍率" if source_id == "1191027" else "对中体型敌人伤害倍率",
                    level,
                    f"character:1191:frost-edge:{parent_key}:{size}:{source_id}",
                    [],
                    source_skill_id=source_id,
                )) * coefficient
                for source_id, coefficient in components
            )
            template_id = EventTemplateId(f"template:character:1191:potential1:frost-edge:{parent_key}:size{size}")
            ref = DamageEventTemplateRef(
                template_id=template_id,
                semantic_id=DamageEventSemanticId(f"event:character:1191:potential1:frost-edge:{parent_key}:size{size}"),
                label=f"潜能1：霜锋（自动追击，体型{size}）",
                damage_type=DamageType.DIRECT,
                skill_group=SkillGroup.BASIC_ATTACK,
                damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
                element=Element.ICE,
                source_rule_item_id=rule_id,
            )
            templates.append(
                DirectDamageEventTemplate(
                    ref=ref,
                    damage_dealer=ELLEN_ID,
                    element=Element.ICE,
                    base_source=CurrentAttackValueSource(ELLEN_ID),
                    crit_rule=StandardCritRule(ELLEN_ID),
                    move_id=None,
                )
            )
            child_refs.append(DerivedDamageEventTemplateRef(template=ref, multiplier=FixedMultiplier(Resolved(value))))
            effects.append(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(f"effect:character:1191:potential1:frost-edge-{parent_key}:size{size}"),
                        source=source,
                        owner=ELLEN_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=ScenarioParameterRangeCondition(ELLEN_FROST_EDGE_TARGET_SIZE, minimum=size, maximum=size),
                        filters=(DamageTypeFilter(DamageType.DIRECT), DamageDealerFilter(ELLEN_ID), EventTemplateIdFilter(parent_template_id)),
                    ),
                    result=EventCreationResult(event_kind=BattleEventKind.DAMAGE, event_template_id=template_id, unique_per_source_event=True),
                )
            )
        refs_by_parent[parent_entry.entry_id] = child_refs
    updated_entries = tuple(
        replace(item, derived_damage_events=tuple(refs_by_parent.get(item.entry_id, ())))
        for item in entries
    )
    return tuple(templates), tuple(effects), updated_entries


def compile_ellen(config: EllenCompileConfig, raw_record: NanokaRawRecord) -> CharacterCalculationDefinition:
    if raw_record.character_id != ELLEN_ID or raw_record.name != "艾莲" or raw_record.code_name != "Ellen":
        raise ValueError("unexpected identity in Ellen raw record")
    if raw_record.specialty != "强攻" or raw_record.element != "冰属性" or raw_record.rarity != 4 or raw_record.faction != "维多利亚家政":
        raise ValueError("Ellen raw role, element, rarity, or faction changed from reviewed source")
    if raw_record.source_version != "3.2" or raw_record.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1191.json":
        raise ValueError("Ellen provenance must identify live Nanoka 3.2 character 1191")
    expected_core = "1191501" if config.potential_level == 0 else "1191508"
    if len(raw_record.core_levels) != 7 or raw_record.core_levels[0].source_id != expected_core:
        raise ValueError("Ellen source potential projection does not match compile config")

    mapping = reviewed_mapping(potential_level=config.potential_level)
    entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=ELLEN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1191",
    )
    entries = list(entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    raw_moves = raw_move_index(raw_record)

    quick_full, quick_template = _direct_composite(
        raw_record,
        config,
        key="dash-ice-quick-full",
        label="冲刺攻击：冰渊潜袭（快速完整招式）",
        source_name="冲刺攻击：冰渊潜袭",
        skill_group=SkillGroup.DODGE,
        tags=frozenset({DamageTag.DASH_ATTACK}),
        element=Element.ICE,
        parameter_components=(("回旋斩击伤害倍率", "1191007"), ("快速剪击伤害倍率", "1191008")),
        move_id=MoveId("move:ellen:dash-ice-fast-full"),
        condition_ids=(),
    )
    charged_full, charged_template = _direct_composite(
        raw_record,
        config,
        key="dash-ice-charged-full",
        label="冲刺攻击：冰渊潜袭（蓄力完整招式）",
        source_name="冲刺攻击：冰渊潜袭",
        skill_group=SkillGroup.DODGE,
        tags=frozenset({DamageTag.DASH_ATTACK}),
        element=Element.ICE,
        parameter_components=(("回旋斩击伤害倍率", "1191007"), ("蓄力剪击伤害倍率", "1191009")),
        move_id=MoveId("move:ellen:dash-ice-charged-full"),
        condition_ids=(),
    )
    entries.extend((quick_full, charged_full))
    templates.extend((quick_template, charged_template))

    anomaly_entries, anomaly_templates, disorder_seconds = _anomaly_entries()
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)

    conditions: list[ScenarioCondition] = [
        _condition(ELLEN_ICE_MODE_ACTIVE, "当前处于急冻效果", raw_moves["普通攻击：急冻修剪法"].description),
    ]
    if config.potential_level >= 1:
        conditions.append(_condition(ELLEN_ICE_BLADE_WAVE_READY, "当前可发动冰刃浪", raw_moves["普通攻击：冰刃浪"].description))
    parameters: list[ScenarioIntegerParameter] = [disorder_seconds]
    parameters.extend((
        ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId(ELLEN_CHILL_CHARGES_FOR_EX),
            label="当前急冻充能（2影增益最多计入3点）",
            original_text="用于计算2影本次强化特殊技的暴击伤害增益；源当前充能范围为0–6，增益最多计入3点。只按当前选择值，不回放资源历史。",
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=6,
        ),
    ))
    if config.additional_ability_eligible:
        parameters.append(ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId(ELLEN_EXTRA_ABILITY_ICE_STACKS),
            label="艾莲额外能力当前冰伤增益层数",
            original_text="按艾莲当前层数计算，范围0–10；不模拟10秒持续和触发历史。",
            resolution=ParameterResolution.USER_SELECTED,
            value=10,
            minimum=0,
            maximum=10,
        ))
    if config.cinema_level >= 6:
        conditions.append(_condition(ELLEN_C6_PENETRATION_ACTIVE, "艾莲当前穿透率提升生效", raw_record.mindscapes[5].description))
        parameters.append(ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId(ELLEN_C6_FEAST_STACKS),
            label="当前盛宴层数",
            original_text="按当前层数0–3计算；仅3层时本次蓄力冲刺攻击获得额外增伤。",
            resolution=ParameterResolution.USER_SELECTED,
            value=3,
            minimum=0,
            maximum=3,
        ))
    if config.potential_level >= 1:
        parameters.append(ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId(ELLEN_FROST_EDGE_TARGET_SIZE),
            label="霜锋自动追击目标体型（0未知、1小、2中、3大）",
            original_text="只选择当前自动霜锋追击使用的体型倍率，不从战斗历史推断。",
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=3,
        ))
    if config.cinema_level >= 1:
        parameters.append(ScenarioIntegerParameter(
            parameter_id=ScenarioParameterId("parameter:ellen:current-chill-charge-crit-rate-stacks"),
            label="当前急冻充能暴击率层数",
            original_text="按当前0–6层计算；不模拟每层15秒的持续时间。",
            resolution=ParameterResolution.USER_SELECTED,
            value=6,
            minimum=0,
            maximum=6,
        ))

    rules: list[CalculationRuleItem] = []
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source("extra-ability", EffectSourceType.ADDITIONAL_ABILITY, core.extra_ability_name, core.extra_ability_description)
    core_cd = _number(core.description, r"暴击伤害提升(?P<value>[\d.]+)%", "Ellen Core Crit Damage") / 100.0
    core_templates = [
        EventTemplateId(f"template:character:1191:basic-ice-{stage}:main") for stage in range(1, 4)
    ] + [
        EventTemplateId("template:character:1191:dash-ice-charged-shear:main"),
        EventTemplateId("template:character:1191:dash-ice-charged-full:main"),
    ]
    if config.potential_level >= 1:
        core_templates.extend(
            EventTemplateId(f"template:character:1191:potential1-ice-blade-wave-{stage}:main")
            for stage in (1, 2)
        )
        core_templates.extend(
            EventTemplateId(f"template:character:1191:potential1-frost-edge-{size}:main")
            for size in ("small", "medium", "large")
        )
        core_templates.extend(
            EventTemplateId(str(ref.template.template_id))
            for entry in entries
            for ref in entry.derived_damage_events
        )
        core_templates.extend((
            EventTemplateId("template:character:1191:chain-avalanche:main"),
            EventTemplateId("template:character:1191:ultimate-endless-winter:main"),
        ))
    core_filters = tuple(EventTemplateIdFilter(item) for item in dict.fromkeys(core_templates))
    core_filter = core_filters[0] if len(core_filters) == 1 else AnyFilter(core_filters)
    rules.append(_rule(
        "core:charged-moves-crit-damage",
        core_source,
        f"核心被动：符合条件的冰系招式暴击伤害+{core_cd:.1%}",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(_modifier(
            "core:charged-moves-crit-damage",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            Resolved(core_cd),
            target=EffectTarget.SELF,
            filters=(DamageDealerFilter(ELLEN_ID), core_filter),
        ),),
    ))

    extra_eligible = RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE
    if config.additional_ability_eligible:
        rules.append(_rule(
            "extra-ability:subsequent-ice-damage",
            extra_source,
            "额外能力：艾莲自身冰伤增益（每层3%，最多10层）",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE,
            effects=(_modifier(
                "extra-ability:subsequent-ice-damage",
                extra_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                ScenarioParameterDerivedValue(
                    parameter_id=ELLEN_EXTRA_ABILITY_ICE_STACKS,
                    coefficient=Resolved(0.03),
                    cap_max=Resolved(0.30),
                ),
                target=EffectTarget.SELF,
                filters=(DamageDealerFilter(ELLEN_ID), element_scope_filter(Element.ICE)),
            ),),
        ))
    else:
        rules.append(_rule("extra-ability:subsequent-ice-damage", extra_source, "额外能力：队伍条件未满足", core.extra_ability_description, extra_eligible))

    if config.cinema_level >= 1:
        c1 = raw_record.mindscapes[0]
        c1_source = _source("cinema1", EffectSourceType.CINEMA, c1.name, c1.description)
        rules.append(_rule(
            "cinema1:current-chill-charge-crit-rate",
            c1_source,
            "1影：当前急冻充能暴击率增益（每层2%）",
            c1.description,
            RuleEligibility.ELIGIBLE,
            effects=(_modifier(
                "cinema1:current-chill-charge-crit-rate",
                c1_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                ScenarioParameterDerivedValue(
                    parameter_id="parameter:ellen:current-chill-charge-crit-rate-stacks",
                    coefficient=Resolved(0.02),
                    cap_max=Resolved(0.12),
                ),
                target=EffectTarget.SELF,
            ),),
        ))
    if config.cinema_level >= 2:
        c2 = raw_record.mindscapes[1]
        c2_source = _source("cinema2", EffectSourceType.CINEMA, c2.name, c2.description)
        ex_ids = (EventTemplateId("template:character:1191:ex-sweep:main"), EventTemplateId("template:character:1191:ex-whirlwind:main"))
        rules.append(_rule(
            "cinema2:ex-current-charge-crit-damage",
            c2_source,
            "2影：本次强化特殊技暴击伤害（每点急冻充能20%，最多60%）",
            c2.description,
            RuleEligibility.ELIGIBLE,
            effects=(_modifier(
                "cinema2:ex-current-charge-crit-damage",
                c2_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                ScenarioParameterDerivedValue(
                    parameter_id=ELLEN_CHILL_CHARGES_FOR_EX,
                    coefficient=Resolved(0.20),
                    cap_max=Resolved(0.60),
                ),
                target=EffectTarget.SELF,
                filters=(DamageDealerFilter(ELLEN_ID), DamageTypeFilter(DamageType.DIRECT), AnyFilter(tuple(EventTemplateIdFilter(x) for x in ex_ids))),
            ),),
        ))
    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        rules.append(_rule(f"cinema{level}:skill-levels", source, f"{level}影：技能等级提升", cinema.description, RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE))
    for level in (4,):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(f"cinema{level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        rules.append(_rule(f"cinema{level}:resource-source-only", source, "4影：急冻充能与能量回复（资源/时序不模拟）", cinema.description, RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE))
    if config.cinema_level >= 6:
        c6 = raw_record.mindscapes[5]
        c6_source = _source("cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
        # The condition was added above only when C6 is unlocked.
        rules.append(_rule(
            "cinema6:current-penetration",
            c6_source,
            "6影：当前穿透率+20%",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(ELLEN_C6_PENETRATION_ACTIVE,),
            effects=(_modifier(
                "cinema6:current-penetration",
                c6_source,
                CalculationNode.CHARACTER_CURRENT_PENETRATION_RATE,
                Resolved(0.20),
                target=EffectTarget.SELF,
            ),),
        ))
        rules.append(_rule(
            "cinema6:charged-dash-feast-damage",
            c6_source,
            "6影：3层盛宴时，蓄力冲刺攻击伤害+250%",
            c6.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "cinema6:charged-dash-feast-damage",
                    c6_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(2.50),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(ELLEN_ID),
                        AnyFilter((
                            EventTemplateIdFilter(EventTemplateId("template:character:1191:dash-ice-charged-shear:main")),
                            EventTemplateIdFilter(EventTemplateId("template:character:1191:dash-ice-charged-full:main")),
                        )),
                    ),
                    condition=ScenarioParameterRangeCondition(ELLEN_C6_FEAST_STACKS, minimum=3),
                ),
            ),
        ))

    potential_followup_templates = ()
    potential_effects = ()
    updated_entries = tuple(entries)
    if config.potential_level >= 1:
        p1 = raw_record.potential_details[0]
        p1_source = _source("potential1:frost-edge", EffectSourceType.SPECIAL_MECHANISM, p1.name or p1.level_show_name, p1.description or raw_record.core_levels[0].description)
        potential_followup_templates, potential_effects, updated_entries = _frost_edge_followups(
            raw_record,
            config,
            tuple(entries),
            p1_source,
        )
        templates.extend(potential_followup_templates)
        rules.append(_rule(
            "potential1:frost-edge-follow-up",
            p1_source,
            "潜能1：霜锋自动追击（按体型选择）",
            raw_record.moves[[move.name for move in raw_record.moves].index("普通攻击：霜锋")].description,
            RuleEligibility.ELIGIBLE,
            effects=potential_effects,
        ))

    # Core P1 adds the automatic Frost Edge child template references to the
    # same Core crit-damage effect; all other P0 entries remain unchanged.
    if config.potential_level >= 1:
        core_rule_index = next(index for index, item in enumerate(rules) if item.rule_id == RuleItemId("rule:character:1191:core:charged-moves-crit-damage"))
        current_rule = rules[core_rule_index]
        current_effects = list(current_rule.effects)
        current_effect = current_effects[0]
        filters = tuple(current_effect.rule.filters)
        existing_templates = [item.template_id for item in filters if isinstance(item, EventTemplateIdFilter)]
        existing_any = next((item for item in filters if isinstance(item, AnyFilter)), None)
        existing_templates = list(existing_any.filters) if existing_any is not None else [EventTemplateIdFilter(item) for item in existing_templates]
        auto_child_filters = tuple(EventTemplateIdFilter(ref.template.template_id) for entry in updated_entries for ref in entry.derived_damage_events)
        new_effect = replace(current_effect, rule=replace(current_effect.rule, filters=(DamageDealerFilter(ELLEN_ID), AnyFilter(tuple(existing_templates) + auto_child_filters))))
        current_effects[0] = new_effect
        rules[core_rule_index] = replace(current_rule, effects=tuple(current_effects))

    if config.potential_level >= 2:
        detail = next(item for item in raw_record.potential_details if item.level == config.potential_level)
        cd_bonus = _number(detail.description, r"每层暴击伤害提升(?P<value>[\d.]+)%", "Ellen Potential Crit Damage per stack") / 100.0
        ice_ignore = _number(detail.description, r"无视(?P<value>[\d.]+)%的冰属性伤害抗性", "Ellen Potential Ice resistance ignore") / 100.0
        p_source = _source(f"potential{config.potential_level}", EffectSourceType.SPECIAL_MECHANISM, detail.name or detail.level_show_name, detail.description)
        rules.append(_rule(
            f"potential{config.potential_level}:extra-ability-stacks",
            p_source,
            f"潜能{config.potential_level}：额外能力层数暴击伤害+{cd_bonus:.1%}/层",
            detail.description,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    f"potential{config.potential_level}:extra-ability-crit-damage",
                    p_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    ScenarioParameterDerivedValue(parameter_id=ELLEN_EXTRA_ABILITY_ICE_STACKS, coefficient=Resolved(cd_bonus)),
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    f"potential{config.potential_level}:ten-stack-ice-resistance-ignore",
                    p_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(ice_ignore),
                    target=EffectTarget.ENEMY,
                    filters=(DamageDealerFilter(ELLEN_ID), element_scope_filter(Element.ICE)),
                    condition=ScenarioParameterRangeCondition(ELLEN_EXTRA_ABILITY_ICE_STACKS, minimum=10),
                ),
            ),
        ))

    return build_definition(
        character_id=ELLEN_ID,
        role=CharacterRole.ATTACK,
        element=Element.ICE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=updated_entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


__all__ = ["compile_ellen", "load_raw_record"]
