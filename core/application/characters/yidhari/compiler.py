"""Compile Yidhari's reviewed live Nanoka 3.2 data into typed Penetration events."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    AnomalyRecordId,
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentPenetrationForceValueSource,
    DamageSubtype,
    DamageTag,
    DamageTagFilter,
    DamageDealerFilter,
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
    ElementFilter,
    EventTemplateId,
    EventTemplateIdFilter,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    MoveId,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
    SnapshotRule,
    StateId,
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
    ScenarioParameterId,
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
    build_definition,
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawMoveRecord, NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
    PenetrationDamageEventTemplate,
)
from .config import YidhariCompileConfig
from .reviewed import (
    CINEMA6_INSIGHT_ACTIVE,
    CORE_MAX_HP_DAMAGE_BONUS_ACTIVE,
    ETHER_CURTAIN_ACTIVE,
    HP_BELOW_50_ACTIVE,
    ICE_ANOMALY_MOVE_ID,
    ICE_DISORDER_MOVE_ID,
    YIDHARI_ID,
    YIDHARI_REVIEWED_MAPPING,
)


ICE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:yidhari:ice-disorder-remaining-seconds"
)
CORE_CURRENT_HP_DAMAGE_BONUS_PERCENT = ScenarioParameterId(
    "parameter:yidhari:core-current-hp-damage-bonus-percent"
)
ICE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:yidhari:ice-shatter")


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(YIDHARI_ID))


def _validate_raw_record(raw: NanokaRawRecord, config: YidhariCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "伊德海莉" or raw.code_name != "Yidhari":
        raise ValueError("unexpected identity in Yidhari raw record")
    if raw.specialty != "命破" or raw.element != "冰属性" or raw.rarity != 4:
        raise ValueError("Yidhari raw role, element, or rarity changed")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Yidhari source must include seven cores and six cinemas")


def _number(text: str, pattern: str, subject: str) -> float:
    plain = re.sub(r"<[^>]*>", "", text)
    match = re.search(pattern, plain)
    if match is None:
        raise ValueError(f"Yidhari source is missing {subject}")
    return float(match.group("value"))


def _condition(condition_id, label: str, text: str, value: bool | None = None):
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(YIDHARI_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    condition_not_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1051:{key}"),
        owner=YIDHARI_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        condition_not_ids=tuple(condition_not_ids),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.TEAM,
    condition=None,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1051:{key}"),
            source=source,
            owner=YIDHARI_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _diagnostic(
    key: str,
    message: str,
    original_text: str,
    *,
    blocking: bool = False,
    kind: DiagnosticKind = DiagnosticKind.UNSUPPORTED_CALCULATOR,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1051:{key}"),
        kind=kind,
        message=message,
        blocking=blocking,
        original_text=original_text,
    )


def _raw_parameter_multiplier(
    raw_move: NanokaRawMoveRecord,
    parameter_name: str,
    source_skill_id: str,
    skill_level: int,
    subject: str,
) -> tuple[FixedMultiplier | Unresolved, CalculationDiagnostic | None]:
    parameter = next(
        (item for item in raw_move.parameters if item.name == parameter_name),
        None,
    )
    value = (
        parameter.value_for_level(skill_level, source_skill_id)
        if parameter is not None and parameter.format == "%"
        else None
    )
    if value is None:
        message = (
            f"{subject}: missing {parameter_name} from {raw_move.name} "
            f"at skill level {skill_level}"
        )
        return (
            Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=message,
                original_text=parameter_name,
            ),
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(
                    f"data:character:1051:{subject}:{parameter_name}:{skill_level}"
                ),
                kind=DiagnosticKind.MISSING_DATA,
                message=message,
                blocking=True,
                original_text=parameter_name,
            ),
        )
    return FixedMultiplier(Resolved(float(value) / 100.0)), None


def _penetration_template(
    *,
    key: str,
    label: str,
    move_id: MoveId | None,
    skill_group: SkillGroup | None,
    damage_tags: frozenset[DamageTag],
) -> PenetrationDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1051:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1051:{key}:main"),
        label=label,
        damage_type=DamageType.PENETRATION,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=Element.ICE,
    )
    return PenetrationDamageEventTemplate(
        ref=ref,
        damage_dealer=YIDHARI_ID,
        element=Element.ICE,
        base_source=CurrentPenetrationForceValueSource(YIDHARI_ID),
        crit_rule=StandardCritRule(YIDHARI_ID),
        move_id=move_id,
    )


def _compile_main_moves(raw: NanokaRawRecord, config: YidhariCompileConfig):
    raw_moves = raw_move_index(raw)
    entries: list[MoveCalculationEntry] = []
    templates: list[PenetrationDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for spec in YIDHARI_REVIEWED_MAPPING.moves:
        raw_move = raw_moves.get(spec.source_name)
        if raw_move is None:
            raise ValueError(f"Yidhari raw source is missing {spec.source_name!r}")
        level = effective_skill_level(config, spec.skill_group)
        parameter_spec = spec.parameters[0]
        assert parameter_spec.source_skill_id is not None
        multiplier, diagnostic = _raw_parameter_multiplier(
            raw_move,
            parameter_spec.parameter_name,
            parameter_spec.source_skill_id,
            level,
            spec.entry_key,
        )
        entry_diagnostics = (diagnostic,) if diagnostic is not None else ()
        template = _penetration_template(
            key=spec.entry_key,
            label=spec.display_name,
            move_id=spec.move_id,
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(f"move-entry:character:1051:{spec.entry_key}"),
                character_id=YIDHARI_ID,
                move_id=spec.move_id,
                display_name=spec.display_name,
                original_text=raw_move.description,
                skill_group=spec.skill_group,
                damage_tags=spec.damage_tags,
                multiplier_relation=spec.multiplier_relation,
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId(
                            f"variant:character:1051:{spec.entry_key}:damage"
                        ),
                        label=parameter_spec.parameter_name,
                        parameter_name=parameter_spec.parameter_name,
                        multiplier=multiplier,
                    ),
                ),
                main_damage_event=template.ref,
                condition_ids=spec.condition_ids,
                stage_index=spec.stage_index,
                diagnostics=entry_diagnostics,
            )
        )
        templates.append(template)
        diagnostics.extend(entry_diagnostics)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def _frost_sinking_counter(raw: NanokaRawRecord, config: YidhariCompileConfig):
    raw_move = next(item for item in raw.moves if item.name == "霜凝千钧")
    level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    multiplier, diagnostic = _raw_parameter_multiplier(
        raw_move,
        "伤害倍率",
        "1051026",
        level,
        "frost-sinking-counter",
    )
    template = _penetration_template(
        key="frost-sinking-counter",
        label="霜凝千钧：反击",
        move_id=None,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1051:frost-sinking-counter"),
        character_id=YIDHARI_ID,
        move_id=None,
        display_name="霜凝千钧：反击",
        original_text=raw_move.description,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1051:frost-sinking-counter:damage"
                ),
                label="伤害倍率",
                parameter_name="伤害倍率",
                multiplier=multiplier,
            ),
        ),
        main_damage_event=template.ref,
        diagnostics=(diagnostic,) if diagnostic is not None else (),
    )
    return entry, template, ((diagnostic,) if diagnostic is not None else ())


def _static_ice_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1051:ice-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1051:ice-anomaly"),
        label="属性异常：碎冰（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=YIDHARI_ID,
        element=Element.ICE,
        anomaly_triggerer=YIDHARI_ID,
        history_record_source=ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ICE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1051:ice-anomaly"),
        character_id=YIDHARI_ID,
        move_id=ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：碎冰（10秒满异常）",
        original_text=(
            "按规范的冰属性异常固定倍率：10秒剩余时间造成异常效果强度500%；"
            "静态单人按100%积蓄，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1051:ice-anomaly"),
                label="碎冰500%（10秒）",
                parameter_name="碎冰倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1051:ice-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1051:ice-disorder"),
        label="紊乱：碎冰（默认最大剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=YIDHARI_ID,
        element=Element.ICE,
        disorder_triggerer=YIDHARI_ID,
        history_record_source=ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1051:ice-disorder"),
        character_id=YIDHARI_ID,
        move_id=ICE_DISORDER_MOVE_ID,
        display_name="紊乱：碎冰（默认最大剩余时间）",
        original_text="按规范默认紊乱基础450% + floor(t)×7.5%；t范围0–10秒，默认10秒，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1051:ice-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="碎冰紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ICE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=ICE_DISORDER_REMAINING_SECONDS,
        label="碎冰紊乱时目标剩余持续时间（秒）",
        original_text="剩余时间单独选择0–10秒，默认10秒；不从触发时序推断。",
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


def _curtain_tentacle_unresolved_effect(source: RuleSource) -> EventCreationEffect:
    original_text = (
        "伊德海莉处于[以太帷幕·涌泉]中时，普通攻击：霜寒拥覆第三段蓄力攻击、"
        "强化特殊技：极寒重碾结束后召唤寒冰触手造成额外伤害；原文称招式视为强化特殊技，"
        "但没有在此句明确额外伤害的元素、伤害类型、暴击归属或独立攻击身份。"
    )
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes=(
            "The source multiplier is retained as raw. The additional tentacle hit cannot be "
            "typed without choosing an unverified element, damage class, crit owner, or hit identity."
        ),
        original_text=original_text,
    )
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(
                "effect:character:1051:extra-ability:ice-tentacle-source-unresolved"
            ),
            source=source,
            owner=YIDHARI_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=(
                DamageTypeFilter(DamageType.PENETRATION),
                DamageDealerFilter(YIDHARI_ID),
                AnyFilter(
                    (
                        EventTemplateIdFilter(
                            EventTemplateId(
                                "template:character:1051:basic-frost-charge-three-finisher:main"
                            )
                        ),
                        EventTemplateIdFilter(
                            EventTemplateId(
                                "template:character:1051:ex-special-polar-crush:main"
                            )
                        ),
                    )
                ),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=unresolved,
            unique_per_source_event=True,
        ),
    )


def compile_yidhari(
    config: YidhariCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = _compile_main_moves(
        raw_record, config
    )
    frost_entry, frost_template, frost_diagnostics = _frost_sinking_counter(
        raw_record, config
    )
    static_entries, static_templates, disorder_remaining = _static_ice_entries()
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description
    )
    core_max_hp_force_source = PanelStatDerivedValue(
        source_character_id=YIDHARI_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_MAX_HP,
        coefficient=Resolved(0.10),
    )
    core_force_rule = _rule(
        "core:extra-penetration-force-from-current-max-hp",
        core_source,
        "核心被动：按当前最大生命值增加贯穿力",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(
            _modifier(
                "core:extra-penetration-force-from-current-max-hp",
                core_source,
                CalculationNode.PENETRATION_FORCE_BONUS,
                core_max_hp_force_source,
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(DamageTypeFilter(DamageType.PENETRATION),),
            ),
        ),
    )
    max_hp_bonus_percent = _number(
        core.description,
        r"攻击造成的伤害最多提升(?P<value>[\d.]+)%",
        "core maximum low-HP damage bonus",
    )
    current_hp_bonus = ScenarioIntegerParameter(
        parameter_id=CORE_CURRENT_HP_DAMAGE_BONUS_PERCENT,
        label=f"核心：当前低生命值增伤百分比（当前核心上限{max_hp_bonus_percent:g}%）",
        original_text=(
            "原文说明当前生命值百分比越低伤害越高，并给出低于50%时的最大值；"
            "没有给出中间生命值对应的增伤曲线，故显式选择当前增伤百分比。"
        ),
        resolution=ParameterResolution.USER_SELECTED,
        value=None,
        minimum=0,
        maximum=int(max_hp_bonus_percent),
    )
    core_max_damage_rule = _rule(
        "core:maximum-low-hp-damage-increase",
        core_source,
        "核心被动：低生命增伤达到当前核心上限",
        core.description,
        RuleEligibility.ELIGIBLE,
        condition_ids=(CORE_MAX_HP_DAMAGE_BONUS_ACTIVE,),
        effects=(
            _modifier(
                "core:maximum-low-hp-damage-increase",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(max_hp_bonus_percent / 100.0),
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(DamageTypeFilter(DamageType.PENETRATION),),
            ),
        ),
    )
    core_intermediate_damage_rule = _rule(
        "core:intermediate-low-hp-damage-increase",
        core_source,
        "核心被动：低生命增伤当前非上限值",
        core.description,
        RuleEligibility.ELIGIBLE,
        condition_not_ids=(CORE_MAX_HP_DAMAGE_BONUS_ACTIVE,),
        effects=(
            _modifier(
                "core:intermediate-low-hp-damage-increase",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                ScenarioParameterDerivedValue(
                    parameter_id=str(CORE_CURRENT_HP_DAMAGE_BONUS_PERCENT),
                    coefficient=Resolved(0.01),
                    base=Resolved(0.0),
                    cap_max=Resolved(max_hp_bonus_percent / 100.0),
                ),
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(DamageTypeFilter(DamageType.PENETRATION),),
            ),
        ),
    )
    core_resource_rule = _rule(
        "core:flash-entry-restore-source-only",
        core_source,
        "核心被动：入场闪能回复（仅保留来源）",
        core.description,
        RuleEligibility.ELIGIBLE,
        diagnostics=(
            _diagnostic(
                "core-flash-resource-unavailable",
                "The raw source's combat-entry Flash restore is preserved; the current calculation request has no Flash resource result.",
                core.description,
            ),
        ),
    )

    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    extra_rules = [
        _rule(
            "extra-ability:low-hp-crit-damage",
            extra_source,
            "额外能力：生命值低于50%时暴击伤害提升",
            core.extra_ability_description,
            extra_eligibility,
            condition_ids=(HP_BELOW_50_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:low-hp-crit-damage",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(0.30),
                    target=EffectTarget.SELF,
                ),
            ),
        ),
        _rule(
            "extra-ability:incoming-damage-reduction-source-only",
            extra_source,
            "额外能力：受到伤害降低（无来袭伤害结果）",
            core.extra_ability_description,
            extra_eligibility,
        ),
    ]
    tentacle_original_text = (
        "伊德海莉处于[以太帷幕·涌泉]中时，普通攻击：霜寒拥覆第三段蓄力攻击、"
        "强化特殊技：极寒重碾结束后召唤寒冰触手造成额外伤害；原文称招式视为强化特殊技，"
        "但没有在此句明确额外伤害的元素、伤害类型、暴击归属或独立攻击身份。"
    )
    tentacle_rule = _rule(
        "extra-ability:ice-tentacle-source-unresolved",
        extra_source,
        "额外能力：寒冰触手攻击身份待确认",
        tentacle_original_text,
        extra_eligibility,
        condition_ids=(ETHER_CURTAIN_ACTIVE,),
        effects=(_curtain_tentacle_unresolved_effect(extra_source),),
    )
    extra_rules.append(tentacle_rule)

    mindscapes = {item.level: item for item in raw_record.mindscapes}
    rules: list[CalculationRuleItem] = [
        core_force_rule,
        core_max_damage_rule,
        core_intermediate_damage_rule,
        core_resource_rule,
        *extra_rules,
    ]
    parameters = [disorder_remaining, current_hp_bonus]
    conditions = [
        _condition(
            ETHER_CURTAIN_ACTIVE,
            "伊德海莉当前处于以太帷幕·涌泉中",
            "本次静态计算所选的当前幕状态；不模拟开启、延长或到期。",
            False,
        ),
        _condition(
            CORE_MAX_HP_DAMAGE_BONUS_ACTIVE,
            "核心低生命增伤最大值当前生效（生命值低于50%或触发后的持续状态）",
            core.description,
            False,
        ),
        _condition(
            HP_BELOW_50_ACTIVE,
            "伊德海莉当前生命值低于50%",
            core.extra_ability_description,
            False,
        ),
        _condition(
            CINEMA6_INSIGHT_ACTIVE,
            "伊德海莉6影启谛增益当前有效",
            mindscapes[6].description,
            False,
        ),
    ]

    for level, mindscape in mindscapes.items():
        source = _source(
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        eligible = (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= level
            else RuleEligibility.INELIGIBLE
        )
        if level == 1:
            c1_energy_diag = _diagnostic(
                "cinema1-flash-consumption-unavailable",
                "Cinema 1's reduced EX Flash cost and post-EX Flash follow-up are preserved in source; the calculation request has no Flash resource result.",
                mindscape.description,
            )
            rules.append(
                _rule(
                    "cinema1:ice-resistance-ignore-and-flash-source",
                    source,
                    "1影：普攻/强化特殊技无视冰属性抗性",
                    mindscape.description,
                    eligible,
                    effects=(
                        _modifier(
                            "cinema1:ice-resistance-ignore",
                            source,
                            CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                            Resolved(0.20),
                            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                            filters=(
                                DamageTypeFilter(DamageType.PENETRATION),
                                ElementFilter(Element.ICE),
                                AnyFilter(
                                    (
                                        DamageTagFilter(DamageTag.BASIC_ATTACK),
                                        DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                                    )
                                ),
                            ),
                        ),
                    ),
                    diagnostics=(c1_energy_diag,),
                )
            )
        elif level == 2:
            rules.append(
                _rule(
                    "cinema2:crit-damage",
                    source,
                    "2影：暴击伤害提升40%",
                    mindscape.description,
                    eligible,
                    effects=(
                        _modifier(
                            "cinema2:crit-damage",
                            source,
                            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                            Resolved(0.40),
                            target=EffectTarget.SELF,
                        ),
                    ),
                    diagnostics=(
                        _diagnostic(
                            "cinema2-flash-regeneration-unavailable",
                            "Cinema 2's Flash regeneration is preserved in source; this request has no Flash resource result.",
                            mindscape.description,
                        ),
                    ),
                )
            )
        elif level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    source,
                    f"{level}影：技能等级提升",
                    mindscape.description,
                    eligible,
                )
            )
        elif level == 4:
            rules.append(
                _rule(
                    "cinema4:veil-max-hp-bonus",
                    source,
                    "4影：以太帷幕中最大生命值提升5%",
                    mindscape.description,
                    eligible,
                    condition_ids=(ETHER_CURTAIN_ACTIVE,),
                    effects=(
                        _modifier(
                            "cinema4:veil-max-hp-bonus",
                            source,
                            CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                            Resolved(0.05),
                            target=EffectTarget.SELF,
                        ),
                    ),
                    diagnostics=(
                        _diagnostic(
                            "cinema4-flash-value-unavailable",
                            "Cinema 4's additional Decibel gain is preserved in raw; the request has no Decibel result.",
                            mindscape.description,
                        ),
                    ),
                )
            )
        elif level == 6:
            rules.append(
                _rule(
                    "cinema6:insight-penetration-bonus",
                    source,
                    "6影启谛：贯穿伤害提升25%",
                    mindscape.description,
                    eligible,
                    condition_ids=(CINEMA6_INSIGHT_ACTIVE,),
                    effects=(
                        _modifier(
                            "cinema6:insight-penetration-bonus",
                            source,
                            CalculationNode.PENETRATION_DAMAGE_BONUS,
                            Resolved(0.25),
                            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                            filters=(DamageTypeFilter(DamageType.PENETRATION),),
                        ),
                    ),
                    diagnostics=(
                        _diagnostic(
                            "cinema6-survival-result-unavailable",
                            "The one-time lethal protection and healing are preserved in raw; the request has no incoming-damage or healing result.",
                            mindscape.description,
                        ),
                    ),
                )
            )

    extra_tentacle_diagnostic = _diagnostic(
        "daze-result-unavailable",
        "Raw Daze curves for attacks and Parry Assist remain preserved, but this calculation request has no Daze result.",
        "失衡倍率",
    )
    return build_definition(
        character_id=YIDHARI_ID,
        role=CharacterRole.RUPTURE,
        element=Element.ICE,
        source=core_source,
        entries=(
            *direct_entries,
            frost_entry,
            *static_entries,
        ),
        templates=(
            *direct_templates,
            frost_template,
            *static_templates,
        ),
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=(*direct_diagnostics, *frost_diagnostics, extra_tentacle_diagnostic),
    )


__all__ = [
    "CORE_CURRENT_HP_DAMAGE_BONUS_PERCENT",
    "ICE_DISORDER_REMAINING_SECONDS",
    "YIDHARI_ID",
    "compile_yidhari",
    "load_raw_record",
]
