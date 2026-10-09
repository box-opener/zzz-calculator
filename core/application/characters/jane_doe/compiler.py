"""Reviewed compiler for Jane Doe (character:1261), Nanoka 3.2."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAnomalyProficiencyValueSource,
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
    ElementFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SkillGroup,
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
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import JaneDoeCompileConfig
from .reviewed import (
    JANE_C4_ANOMALY_BONUS_ACTIVE,
    JANE_C6_ASSAULT_CRIT_TRIGGERED,
    JANE_DOE_ID,
    JANE_DOE_REVIEWED_MAPPING,
    JANE_FRENZY_ACTIVE,
    JANE_GNAWING_ACTIVE,
    JANE_SAHOFF_JUMP_AVAILABLE,
    JANE_SAHOFF_MOVE_ID,
)


_PHYSICAL_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1261:physical-assault")
_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1261:physical-assault")
_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1261:physical-disorder")
_ANOMALY_MOVE_ID = MoveId("move:jane-doe:physical-assault")
_DISORDER_MOVE_ID = MoveId("move:jane-doe:physical-disorder")
_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:jane-doe:physical-disorder-remaining-seconds"
)


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


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1261:{key}"),
        owner=JANE_DOE_ID,
        source=source,
        display_name=label,
        original_text=original_text,
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
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1261:{key}"),
            source=source,
            owner=JANE_DOE_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(JANE_DOE_ID))


def _validate_raw(raw: NanokaRawRecord) -> None:
    if raw.character_id != JANE_DOE_ID:
        raise ValueError("Jane Doe raw record and compile config IDs must match")
    if raw.name != "简" or raw.code_name != "Jane":
        raise ValueError("unexpected Jane Doe identity")
    if raw.specialty != "异常" or raw.element != "物理" or raw.rarity != 4:
        raise ValueError("unexpected Jane Doe role, element, or rarity")
    if raw.faction != "新艾利都治安局":
        raise ValueError("unexpected Jane Doe faction")
    if raw.icon != "IconRole24":
        raise ValueError("unexpected Jane Doe portrait identity")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1261.json":
        raise ValueError("Jane Doe provenance must identify live Nanoka 3.2 character 1261")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6 or len(raw.potential_details) != 6:
        raise ValueError("Jane Doe source must include seven Core levels and six Potential levels")


def _curve_ratio(
    raw_moves,
    source_name: str,
    parameter_name: str,
    source_skill_id: str,
    level: int,
) -> float:
    move = raw_moves.get(source_name)
    if move is None:
        raise ValueError(f"Jane Doe source move is missing: {source_name}")
    for parameter in move.parameters:
        if parameter.name != parameter_name or parameter.format != "%":
            continue
        value = parameter.value_for_level(level, source_skill_id)
        if value is not None:
            return value / 100.0
    raise ValueError(
        f"Jane Doe curve {source_skill_id} is missing for {source_name}:{parameter_name}"
    )


def _fixed_direct_entry(
    *,
    key: str,
    label: str,
    source_text: str,
    move_id: MoveId,
    skill_group: SkillGroup,
    tags: frozenset[DamageTag],
    ratio: float,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    conditions=(),
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1261:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1261:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=tags,
        element=Element.PHYSICAL,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=JANE_DOE_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(JANE_DOE_ID),
        crit_rule=StandardCritRule(JANE_DOE_ID),
        move_id=move_id,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1261:{key}"),
        character_id=JANE_DOE_ID,
        move_id=move_id,
        display_name=label,
        original_text=source_text,
        skill_group=skill_group,
        damage_tags=tags,
        multiplier_relation=relation,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1261:{key}:source-ratio"),
                label=f"{ratio:.3%}攻击力",
                parameter_name="伤害倍率",
                multiplier=FixedMultiplier(Resolved(ratio)),
            ),
        ),
        main_damage_event=ref,
        condition_ids=tuple(conditions),
    )
    return entry, template


def _static_physical_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1261:physical-assault"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=JANE_DOE_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=JANE_DOE_ID,
        history_record_source=_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1261:physical-assault"),
        character_id=JANE_DOE_ID,
        move_id=_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text="静态单人100%积蓄物理记录；强击倍率713%，使用异常暴击规则（仅啮咬状态可用）。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1261:physical-assault"),
                label="物理强击倍率713%",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1261:physical-disorder"),
        label="紊乱：物理强击",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=JANE_DOE_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=JANE_DOE_ID,
        history_record_source=_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1261:physical-disorder"),
        character_id=JANE_DOE_ID,
        move_id=_DISORDER_MOVE_ID,
        display_name="紊乱：物理强击（当前剩余时间）",
        original_text="物理强击紊乱倍率为450% + floor(t)×7.5%；当前剩余时间是用户输入，不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1261:physical-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="物理紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_DISORDER_REMAINING_SECONDS,
        label="物理异常剩余持续时间（秒）",
        original_text="当前物理异常剩余持续时间，范围0–10秒；不模拟时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _unresolved_c6_extra_attack(raw: NanokaRawRecord):
    c6 = raw.mindscapes[5]
    ratio = _number(
        c6.description,
        r"造成等同于简(?P<value>[\d.]+)%异常精通的物理伤害",
        "Jane Doe Cinema 6 anomaly-proficiency extra-attack coefficient",
    ) / 100.0
    key = "cinema6-extra-assault-identity-unresolved"
    label = f"6影：强击暴击额外物理伤害（{ratio:.0%}×当前异常精通；事件身份待确认）"
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1261:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1261:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        element=Element.PHYSICAL,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=JANE_DOE_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAnomalyProficiencyValueSource(JANE_DOE_ID),
        crit_rule=StandardCritRule(JANE_DOE_ID),
        move_id=None,
    )
    diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1261:{key}:identity"),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message="Cinema 6's 1600% current-Anomaly-Proficiency Physical extra hit has unresolved event type, Crit rule, skill group, and damage tags; no typed damage event is emitted.",
        blocking=True,
        original_text=c6.description,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1261:{key}"),
        character_id=JANE_DOE_ID,
        move_id=None,
        display_name=label,
        original_text=c6.description,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1261:{key}:coefficient"),
                label="1600% × 当前异常精通",
                parameter_name="额外攻击异常精通系数",
                multiplier=FixedMultiplier(Resolved(ratio)),
            ),
        ),
        main_damage_event=ref,
        diagnostics=(diagnostic,),
    )
    unresolved_child = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes="The source defines a one-time 1600% current-Anomaly-Proficiency Physical extra attack after a team Assault crit. Its damage type, Crit rule, group, and tags are unresolved; no synthetic event is emitted.",
        original_text=c6.description,
    )
    return entry, template, unresolved_child


def compile_jane_doe(
    config: JaneDoeCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record)
    if raw_record.character_id != config.character_id:
        raise ValueError("Jane Doe raw record and compile config IDs must match")

    direct_entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=JANE_DOE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=JANE_DOE_REVIEWED_MAPPING,
        id_namespace="character:1261",
    )
    entries = list(direct_entries)
    templates = list(direct_templates)
    raw_moves = raw_move_index(raw_record)
    basic_level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    saohov_curve_id = "1261030" if config.potential_level >= 1 else "1261007"
    saohov_continuous = _curve_ratio(
        raw_moves,
        "普通攻击：萨霍夫跳",
        "连续攻击伤害倍率",
        saohov_curve_id,
        basic_level,
    )
    saohov_finisher = _curve_ratio(
        raw_moves,
        "普通攻击：萨霍夫跳",
        "终结一击伤害倍率",
        "1261008",
        basic_level,
    )
    continuous_key = "sahoff-jump-continuous"
    continuous_index = next(
        index for index, item in enumerate(entries)
        if str(item.entry_id) == f"move-entry:character:1261:{continuous_key}"
    )
    continuous_entry = entries[continuous_index]
    continuous_label = (
        "普通攻击：萨霍夫跳（连续攻击·潜能1加强版）"
        if config.potential_level >= 1
        else "普通攻击：萨霍夫跳（连续攻击）"
    )
    entries[continuous_index] = replace(
        continuous_entry,
        display_name=continuous_label,
        multiplier_variants=(
            replace(
                continuous_entry.multiplier_variants[0],
                label="连续攻击伤害倍率",
                multiplier=FixedMultiplier(Resolved(saohov_continuous)),
            ),
        ),
    )
    full_sahoff_entry, full_sahoff_template = _fixed_direct_entry(
        key="sahoff-jump-full",
        label="普通攻击：萨霍夫跳（连续攻击与终结一击）",
        source_text=raw_moves["普通攻击：萨霍夫跳"].description,
        move_id=JANE_SAHOFF_MOVE_ID,
        skill_group=SkillGroup.BASIC_ATTACK,
        tags=frozenset({DamageTag.BASIC_ATTACK}),
        ratio=saohov_continuous + saohov_finisher,
        relation=MultiplierRelation.COMPLETE,
        conditions=(JANE_FRENZY_ACTIVE, JANE_SAHOFF_JUMP_AVAILABLE),
    )
    entries.append(full_sahoff_entry)
    templates.append(full_sahoff_template)

    conditions = [
        _condition(
            JANE_FRENZY_ACTIVE,
            "当前处于狂热状态",
            raw_moves["狂热"].description,
        ),
        _condition(
            JANE_GNAWING_ACTIVE,
            "目标当前处于啮咬状态",
            raw_record.core_levels[0].description,
        ),
        _condition(
            JANE_SAHOFF_JUMP_AVAILABLE,
            "当前萨霍夫跳使用次数可用",
            raw_moves["普通攻击：萨霍夫跳"].description,
        ),
    ]
    rules: list[CalculationRuleItem] = []
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        JANE_DOE_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra_source = source_for(
        JANE_DOE_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    frenzy_text = raw_moves["狂热"].description
    ap_to_attack_coefficient = _number(
        frenzy_text,
        r"每超过1点异常精通会使自身的攻击力提升(?P<value>[\d.]+)点",
        "Jane Doe Frenzy attack per Anomaly Proficiency",
    )
    ap_attack_cap = _number(
        frenzy_text,
        r"最多使自身的攻击力提升(?P<value>[\d.]+)点",
        "Jane Doe Frenzy attack cap",
    )
    ap_attack_effect = _modifier(
        "core:frenzy-ap-to-attack",
        core_source,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        PanelStatDerivedValue(
            source_character_id=JANE_DOE_ID,
            source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
            coefficient=Resolved(ap_to_attack_coefficient),
            cap_max=Resolved(ap_attack_cap),
            threshold=Resolved(120.0),
        ),
        target=EffectTarget.SELF,
    )
    rules.append(_rule(
        "core:frenzy-ap-to-attack",
        core_source,
        f"狂热：当前异常精通每超过120点使简攻击力+{ap_to_attack_coefficient:g}，最多+{ap_attack_cap:g}",
        frenzy_text,
        RuleEligibility.ELIGIBLE,
        effects=(ap_attack_effect,),
        conditions=(JANE_FRENZY_ACTIVE,),
    ))

    bite_anomaly_filter = (
        DamageTypeFilter(DamageType.ANOMALY),
        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
        ElementFilter(Element.PHYSICAL),
    )
    core_base_crit_rate = _number(
        core.description,
        r"基础暴击率为(?P<value>[\d.]+)%",
        "Jane Doe Core Strong anomaly crit rate",
    ) / 100.0
    core_crit_rate_per_ap = _number(
        core.description,
        r"每点异常精通会使该效果的暴击率额外提升(?P<value>[\d.]+)%",
        "Jane Doe Core Strong anomaly crit rate per proficiency",
    ) / 100.0
    core_strong_crit_damage = _number(
        core.description,
        r"暴击伤害为(?P<value>[\d.]+)%",
        "Jane Doe Core Strong anomaly crit damage",
    ) / 100.0
    core_crit_rate = PanelStatDerivedValue(
        source_character_id=JANE_DOE_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        coefficient=Resolved(core_crit_rate_per_ap),
        base=Resolved(core_base_crit_rate),
        cap_max=Resolved(1.0),
    )
    rules.append(_rule(
        "core:gnawing-strong-anomaly-crit",
        core_source,
        f"核心被动：啮咬目标上的全队物理强击异常暴击率{core_base_crit_rate:.0%}+当前异常精通×{core_crit_rate_per_ap:.2%}，上限100%；暴伤{core_strong_crit_damage:.0%}",
        core.description,
        RuleEligibility.ELIGIBLE,
        conditions=(JANE_GNAWING_ACTIVE,),
        effects=(
            _modifier(
                "core:gnawing-strong-anomaly-crit-rate",
                core_source,
                CalculationNode.ANOMALY_CRIT_RATE,
                core_crit_rate,
                target=EffectTarget.TEAM,
                filters=bite_anomaly_filter,
            ),
            _modifier(
                "core:gnawing-strong-anomaly-crit-damage",
                core_source,
                CalculationNode.ANOMALY_CRIT_DAMAGE,
                Resolved(core_strong_crit_damage),
                target=EffectTarget.TEAM,
                filters=bite_anomaly_filter,
            ),
        ),
    ))

    if config.additional_ability_eligible:
        rules.append(_rule(
            "extra-ability:physical-buildup-scope",
            extra_source,
            "额外能力：物理异常积蓄效率提升（只保留来源；不改变静态满积蓄伤害）",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE,
        ))
    else:
        rules.append(_rule(
            "extra-ability:physical-buildup-scope",
            extra_source,
            "额外能力：队伍未满足另一异常角色或同阵营条件",
            raw_record.extra_ability_description,
            RuleEligibility.INELIGIBLE,
        ))

    cinema1_source = source_for(
        JANE_DOE_ID,
        "cinema1",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[0].name,
        raw_record.mindscapes[0].description,
    )
    if config.cinema_level >= 1:
        c1_ap_damage = _number(
            raw_record.mindscapes[0].description,
            r"每点异常精通将会使自身造成的伤害提升(?P<value>[\d.]+)%",
            "Jane Doe Cinema 1 damage per Anomaly Proficiency",
        ) / 100.0
        c1_damage_cap = _number(
            raw_record.mindscapes[0].description,
            r"最多提升(?P<value>[\d.]+)%",
            "Jane Doe Cinema 1 AP damage cap",
        ) / 100.0
        rules.append(_rule(
            "cinema1:frenzy-ap-damage-bonus",
            cinema1_source,
            f"1影：狂热时当前异常精通×{c1_ap_damage:.1%}伤害增益，上限{c1_damage_cap:.0%}",
            raw_record.mindscapes[0].description,
            RuleEligibility.ELIGIBLE,
            conditions=(JANE_FRENZY_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:frenzy-ap-damage-bonus",
                    cinema1_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    PanelStatDerivedValue(
                        source_character_id=JANE_DOE_ID,
                        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                        coefficient=Resolved(c1_ap_damage),
                        cap_max=Resolved(c1_damage_cap),
                    ),
                    target=EffectTarget.SELF,
                ),
            ),
        ))

    cinema2_source = source_for(
        JANE_DOE_ID,
        "cinema2",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[1].name,
        raw_record.mindscapes[1].description,
    )
    cinema2_defense_ignore = _number(
        raw_record.mindscapes[1].description,
        r"无视其(?P<value>[\d.]+)%防御力",
        "Jane Doe Cinema 2 Defense ignore",
    ) / 100.0
    cinema2_crit_damage = _number(
        raw_record.mindscapes[1].description,
        r"暴击伤害额外提升(?P<value>[\d.]+)%",
        "Jane Doe Cinema 2 Strong Crit Damage",
    ) / 100.0
    if config.cinema_level >= 2:
        rules.append(_rule(
            "cinema2:gnawing-target-defense-ignore",
            cinema2_source,
            f"2影：啮咬目标当前强击与简直击无视{cinema2_defense_ignore:.0%}防御",
            raw_record.mindscapes[1].description,
            RuleEligibility.ELIGIBLE,
            conditions=(JANE_GNAWING_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:jane-direct-defense-ignore",
                    cinema2_source,
                    CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    Resolved(cinema2_defense_ignore),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(JANE_DOE_ID),
                    ),
                ),
                _modifier(
                    "cinema2:team-physical-assault-defense-ignore",
                    cinema2_source,
                    CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    Resolved(cinema2_defense_ignore),
                    target=EffectTarget.TEAM,
                    filters=bite_anomaly_filter,
                ),
                _modifier(
                    "cinema2:team-physical-assault-crit-damage",
                    cinema2_source,
                    CalculationNode.ANOMALY_CRIT_DAMAGE,
                    Resolved(cinema2_crit_damage),
                    target=EffectTarget.TEAM,
                    filters=bite_anomaly_filter,
                ),
            ),
        ))

    if config.potential_level >= 2:
        detail = raw_record.potential_details[config.potential_level - 1]
        p_source = source_for(
            JANE_DOE_ID,
            f"potential{config.potential_level}",
            EffectSourceType.SPECIAL_MECHANISM,
            detail.level_show_name,
            detail.description,
        )
        p_crit_damage = _number(
            detail.description,
            r"暴击伤害额外提升(?P<value>[\d.]+)%",
            f"Jane Doe Potential {config.potential_level} Strong Crit Damage",
        ) / 100.0
        rules.append(_rule(
            f"potential{config.potential_level}:strong-crit-damage",
            p_source,
            f"潜能{config.potential_level}：简触发强击时暴击伤害+{p_crit_damage:.0%}",
            detail.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    f"potential{config.potential_level}:strong-crit-damage",
                    p_source,
                    CalculationNode.ANOMALY_CRIT_DAMAGE,
                    Resolved(p_crit_damage),
                    target=EffectTarget.TEAM,
                    filters=(
                        *bite_anomaly_filter,
                        DamageDealerFilter(JANE_DOE_ID),
                    ),
                ),
            ),
        ))

    cinema4_source = source_for(
        JANE_DOE_ID,
        "cinema4",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[3].name,
        raw_record.mindscapes[3].description,
    )
    if config.cinema_level >= 4:
        conditions.append(_condition(
            JANE_C4_ANOMALY_BONUS_ACTIVE,
            "简的4影属性异常伤害增益当前生效",
            raw_record.mindscapes[3].description,
        ))
        c4_anomaly_bonus = _number(
            raw_record.mindscapes[3].description,
            r"属性异常伤害提升(?P<value>[\d.]+)%",
            "Jane Doe Cinema 4 anomaly damage bonus",
        ) / 100.0
        rules.append(_rule(
            "cinema4:team-anomaly-damage-bonus",
            cinema4_source,
            f"4影：全队属性异常伤害+{c4_anomaly_bonus:.0%}（当前状态，记录捕获）",
            raw_record.mindscapes[3].description,
            RuleEligibility.ELIGIBLE,
            conditions=(JANE_C4_ANOMALY_BONUS_ACTIVE,),
            effects=(
                _modifier(
                    "cinema4:team-anomaly-damage-bonus",
                    cinema4_source,
                    CalculationNode.ANOMALY_DAMAGE_BONUS,
                    Resolved(c4_anomaly_bonus),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    ),
                ),
            ),
        ))

    cinema6_source = source_for(
        JANE_DOE_ID,
        "cinema6",
        EffectSourceType.CINEMA,
        raw_record.mindscapes[5].name,
        raw_record.mindscapes[5].description,
    )
    if config.cinema_level >= 6:
        c6 = raw_record.mindscapes[5]
        frenzy_crit_rate = _number(
            c6.description,
            r"暴击率提升(?P<value>[\d.]+)%",
            "Jane Doe Cinema 6 Frenzy Crit Rate",
        ) / 100.0
        frenzy_crit_damage = _number(
            c6.description,
            r"暴击伤害提升(?P<value>[\d.]+)%",
            "Jane Doe Cinema 6 Frenzy Crit Damage",
        ) / 100.0
        rules.append(_rule(
            "cinema6:frenzy-panel-crit",
            cinema6_source,
            f"6影：狂热时简当前暴击率+{frenzy_crit_rate:.0%}、暴击伤害+{frenzy_crit_damage:.0%}",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(JANE_FRENZY_ACTIVE,),
            effects=(
                _modifier(
                    "cinema6:frenzy-current-crit-rate",
                    cinema6_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(frenzy_crit_rate),
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    "cinema6:frenzy-current-crit-damage",
                    cinema6_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(frenzy_crit_damage),
                    target=EffectTarget.SELF,
                ),
            ),
        ))
        c6_entry, c6_template, c6_unresolved = _unresolved_c6_extra_attack(raw_record)
        entries.append(c6_entry)
        templates.append(c6_template)
        conditions.append(_condition(
            JANE_C6_ASSAULT_CRIT_TRIGGERED,
            "本次队伍强击暴击已触发简的6影额外攻击",
            c6.description,
        ))
        rules.append(_rule(
            "cinema6:strong-crit-extra-attack-identity-unresolved",
            cinema6_source,
            "6影：队伍强击暴击触发的1600%异常精通额外攻击（身份待确认）",
            c6.description,
            RuleEligibility.ELIGIBLE,
            conditions=(JANE_C6_ASSAULT_CRIT_TRIGGERED,),
            effects=(EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId("effect:character:1261:cinema6:strong-crit-extra-attack"),
                    source=cinema6_source,
                    owner=JANE_DOE_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        ElementFilter(Element.PHYSICAL),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    unresolved_template=c6_unresolved,
                    unique_per_source_event=True,
                ),
            ),),
        ))

    anomaly_entries, anomaly_templates, disorder_seconds = _static_physical_entries(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)
    return build_definition(
        character_id=JANE_DOE_ID,
        role=CharacterRole.ANOMALY,
        element=Element.PHYSICAL,
        source=source_for(
            JANE_DOE_ID,
            "character",
            EffectSourceType.SKILL,
            raw_record.name,
            raw_record.code_name,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(disorder_seconds,),
        diagnostics=diagnostics,
    )


__all__ = ["compile_jane_doe", "load_raw_record"]
