"""Compile Zhao's Nanoka record into reviewed direct and static-anomaly rules."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import replace

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    CurrentMaxHPValueSource,
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
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import ZhaoCompileConfig
from .reviewed import (
    ANY_ETHER_CURTAIN_ACTIVE,
    BASIC_FINAL_JUDGMENT_MOVE_ID,
    BASIC_JUDGMENT_MOVE_ID,
    CHAIN_TEMPORARY_COOPERATION_MOVE_ID,
    CHARGE_SECONDS,
    FROSTBITE_FULL,
    ICE_DISORDER_REMAINING_SECONDS,
    IN_COMBAT,
    SPRING_CURTAIN_ACTIVE,
    SPRING_CURTAIN_ATTACK_BUFF_ACTIVE,
    SUPPORT_FOLLOWUP_AFTERGLOW_MOVE_ID,
    ULTIMATE_RABBIT_SLASH_MOVE_ID,
    ZHAO_C1_RESISTANCE_IGNORE_ACTIVE,
    ZHAO_C2_ATTACK_BUFF_ACTIVE,
    ZHAO_ID,
    ZHAO_REVIEWED_MAPPING,
)


ZHAO_ICE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:zhao:ice-current")
ZHAO_ICE_ANOMALY_MOVE_ID = MoveId("move:zhao:ice-shatter")
ZHAO_ICE_DISORDER_MOVE_ID = MoveId("move:zhao:ice-disorder")
_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOWUP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(ZHAO_ID))


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
        rule_id=RuleItemId(f"rule:character:1341:{key}"),
        owner=ZHAO_ID,
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
            effect_id=EffectId(f"effect:character:1341:{key}"),
            source=source,
            owner=ZHAO_ID,
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


def _diag(key: str, message: str, text: str, *, blocking: bool = False, candidates=()):
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(key),
        kind=(
            DiagnosticKind.AMBIGUOUS_SEMANTICS
            if blocking
            else DiagnosticKind.UNSUPPORTED_CALCULATOR
        ),
        message=message,
        blocking=blocking,
        original_text=text,
        candidates=tuple(candidates),
    )


def _static_ice_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1341:ice-shatter",
        semantic_id=DamageEventSemanticId("event:character:1341:ice-shatter"),
        label="属性异常：碎冰（霜寒）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=ZHAO_ID,
        element=Element.ICE,
        anomaly_triggerer=ZHAO_ID,
        history_record_source=ZHAO_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ZHAO_ICE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1341:ice-shatter"),
        character_id=ZHAO_ID,
        move_id=ZHAO_ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：碎冰（霜寒）",
        original_text=(
            "按10秒静态满异常记录，冰属性碎冰固定倍率500%；"
            "异常精通、属性增伤和普通增伤在记录生成时取值。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1341:ice-shatter"),
                label="碎冰倍率500%",
                parameter_name="冰属性碎冰伤害倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1341:ice-disorder",
        semantic_id=DamageEventSemanticId("event:character:1341:ice-disorder"),
        label="紊乱：冰属性碎冰",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ZHAO_ID,
        element=Element.ICE,
        disorder_triggerer=ZHAO_ID,
        history_record_source=ZHAO_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ZHAO_ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1341:ice-disorder"),
        character_id=ZHAO_ID,
        move_id=ZHAO_ICE_DISORDER_MOVE_ID,
        display_name="紊乱：冰属性碎冰",
        original_text="按规范默认紊乱基础450%，加floor(t)×7.5%；t=10时为525%。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1341:ice-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="冰霜寒紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ICE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
    )


def _charge_hp_component(
    *,
    source: RuleSource,
    parent_move_id: MoveId,
    key: str,
    label: str,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    ratio: float,
) -> tuple[DirectDamageEventTemplate, DerivedDamageEventTemplateRef, EventCreationEffect, EffectId]:
    effect_id = EffectId(f"effect:character:1341:core:charged-hp-extra:{key}")
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1341:charged-hp-extra:{key}",
        semantic_id=DamageEventSemanticId(f"event:character:1341:charged-hp-extra:{key}"),
        label=f"核心被动：{label}蓄力生命值追加段",
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=tags,
        element=Element.ICE,
        source_rule_item_id=RuleItemId("rule:character:1341:core:charged-hp-extra"),
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=ZHAO_ID,
        element=Element.ICE,
        base_source=CurrentMaxHPValueSource(ZHAO_ID),
        crit_rule=StandardCritRule(ZHAO_ID),
        move_id=parent_move_id,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(ratio)),
        repeat_count_parameter_id=CHARGE_SECONDS,
        skip_when_repeat_count_zero=True,
    )
    creation = EventCreationEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=source,
            owner=ZHAO_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageDealerFilter(ZHAO_ID),
                DamageTypeFilter(DamageType.DIRECT),
                MoveIdFilter(parent_move_id),
                NotFilter(CreatedByEffectFilter(effect_id)),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=ref.template_id,
        ),
    )
    return template, derived, creation, effect_id


def _plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _one(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain exactly one value; found {len(matches)}")
    return float(matches[0].group("value"))


def _composite_multipliers(config: ZhaoCompileConfig, raw: NanokaRawRecord):
    raw_moves = raw_move_index(raw)
    basic_level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    ultimate_level = effective_skill_level(config, SkillGroup.ULTIMATE)
    basic_entry, basic_template = _composite_entry(
        raw_moves=raw_moves,
        config=config,
        source_name="普通攻击：凛冽裁决",
        parameter_name="五段伤害倍率",
        source_skill_ids=("1341005", "1341006"),
        entry_key="basic-cold-judgment-5",
        label="普通攻击：凛冽裁决（五段）",
        move_id=BASIC_JUDGMENT_MOVE_ID,
        group=SkillGroup.BASIC_ATTACK,
        tags=_BASIC,
        element=Element.ICE,
        relation=MultiplierRelation.SEQUENTIAL_STAGE,
        stage=5,
    )
    ultimate_entry, ultimate_template = _composite_entry(
        raw_moves=raw_moves,
        config=config,
        source_name="终结技：兔兔连斩",
        parameter_name="伤害倍率",
        source_skill_ids=("1341014", "1341023"),
        entry_key="ultimate-rabbit-slash",
        label="终结技：兔兔连斩",
        move_id=ULTIMATE_RABBIT_SLASH_MOVE_ID,
        group=SkillGroup.ULTIMATE,
        tags=_ULTIMATE,
        element=Element.ICE,
        relation=MultiplierRelation.COMPLETE,
        stage=None,
    )
    # Keep the skill levels visible in this source review: the raw sums are
    # evaluated independently at their effective, category-specific levels.
    assert basic_level == effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    assert ultimate_level == effective_skill_level(config, SkillGroup.ULTIMATE)
    return (basic_entry, ultimate_entry), (basic_template, ultimate_template)


def _composite_entry(
    *,
    raw_moves: Mapping[str, NanokaRawMoveRecord],
    config: ZhaoCompileConfig,
    source_name: str,
    parameter_name: str,
    source_skill_ids: tuple[str, ...],
    entry_key: str,
    label: str,
    move_id: MoveId,
    group: SkillGroup,
    tags: frozenset[DamageTag],
    element: Element,
    relation: MultiplierRelation,
    stage: int | None,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    raw_move = raw_moves[source_name]
    parameter = next(item for item in raw_move.parameters if item.name == parameter_name)
    level = effective_skill_level(config, group)
    terms = []
    for source_skill_id in source_skill_ids:
        value = parameter.value_for_level(level, source_skill_id)
        if value is None:
            raise ValueError(
                f"Zhao source sum is missing {source_skill_id} at effective skill level {level}"
            )
        terms.append((source_skill_id, value / 100.0))
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1341:{entry_key}:main",
        semantic_id=DamageEventSemanticId(f"event:character:1341:{entry_key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=group,
        damage_tags=tags,
        element=element,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=ZHAO_ID,
        element=element,
        base_source=CurrentAttackValueSource(ZHAO_ID),
        crit_rule=StandardCritRule(ZHAO_ID),
        move_id=move_id,
    )
    source_curve_text = " + ".join(
        f"{source_id}={value * 100:g}%" for source_id, value in terms
    )
    original = (
        f"{raw_move.description}\n{parameter.name}\n"
        f"Source curves at effective level {level}: {source_curve_text}."
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1341:{entry_key}"),
        character_id=ZHAO_ID,
        move_id=move_id,
        display_name=label,
        original_text=original,
        skill_group=group,
        damage_tags=tags,
        multiplier_relation=relation,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1341:{entry_key}:source-sum"),
                label="原文明确相加的源曲线",
                parameter_name=parameter_name,
                multiplier=FixedMultiplier(Resolved(sum(value for _, value in terms))),
            ),
        ),
        main_damage_event=ref,
        stage_index=stage,
    )
    return entry, template


def compile_zhao(
    config: ZhaoCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != ZHAO_ID:
        raise ValueError("Zhao compiler requires character:1341 raw data")
    if raw_record.element not in {"冰", "冰属性"}:
        raise ValueError("Zhao raw record must identify Ice as the base element")

    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=ZHAO_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=ZHAO_REVIEWED_MAPPING,
        id_namespace="character:1341",
    )
    entries: list[MoveCalculationEntry] = list(direct_entries)
    diagnostics = list(direct_diagnostics)

    composite_entries, composite_templates = _composite_multipliers(config, raw_record)
    entries.extend(composite_entries)
    templates: list[object] = list(direct_templates) + list(composite_templates)
    static_entries, static_templates = _static_ice_entries(raw_record)
    entries.extend(static_entries)
    templates.extend(static_templates)

    conditions = [
        _condition(SPRING_CURTAIN_ACTIVE, "涌泉幕当前生效", "照开启的涌泉幕持续40秒；当前状态由本次输入选择。"),
        _condition(ANY_ETHER_CURTAIN_ACTIVE, "照当前处于任意以太帷幕中", "额外能力要求照本人处于任意以太帷幕；当前状态由本次输入选择，不回放帷幕生成顺序或持续时间。"),
        _condition(SPRING_CURTAIN_ATTACK_BUFF_ACTIVE, "涌泉幕开启后的50秒攻击力提升当前生效", "该50秒状态独立于40秒涌泉幕状态。"),
        _condition(ZHAO_C1_RESISTANCE_IGNORE_ACTIVE, "照切出后50秒全属性抗性无视当前生效", "只表示当前团队增益状态。"),
        _condition(ZHAO_C2_ATTACK_BUFF_ACTIVE, "照回血触发的C2攻击力增益当前生效", "Self+20%、其他队员+15%，不由本次技能推断回血历史。"),
        _condition(FROSTBITE_FULL, "霜寒值当前已满", "入场获得100点；后续命中获得与消耗不模拟。", value=True),
        _condition(IN_COMBAT, "当前处于接战状态", "登场技要求霜寒值满且处于接战状态。"),
    ]
    parameters = [
        ScenarioIntegerParameter(
            parameter_id=CHARGE_SECONDS,
            label="本次适用招式终结一击的累计蓄力时长（秒）",
            original_text="最终裁决、连携技与支援突击终结一击最多5秒；用户选择本次实际蓄力时长，不从时间轴推算。0秒不产生生命值追加段。",
            resolution=ParameterResolution.USER_SELECTED,
            value=None,
            minimum=0,
            maximum=5,
        ),
        ScenarioIntegerParameter(
            parameter_id=ICE_DISORDER_REMAINING_SECONDS,
            label="本次冰属性异常剩余时长（秒）",
            original_text="按规范默认紊乱基础450%+floor(t)×7.5%，t范围0–10秒，默认10秒。",
            resolution=ParameterResolution.USER_SELECTED,
            value=10,
            minimum=0,
            maximum=10,
        ),
    ]

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        ZHAO_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_crit_percent_per_1000 = _one(
        core.description,
        r"每1000点初始最大生命值提高(?P<value>[\d.]+)%暴击率",
        "Zhao Core initial-HP crit-rate coefficient",
    )
    core_crit_per_hp = core_crit_percent_per_1000 / 100.0 / 1000.0
    core_attack_flat = _one(
        core.description,
        r"使全队角色的攻击力提升(?P<value>[\d.]+)点",
        "Zhao Core Spring Curtain attack bonus",
    )
    rules: list[CalculationRuleItem] = []
    rules.append(
        _rule(
            "core:initial-hp-crit-rate",
            core_source,
            "核心被动：初始最大生命值转暴击率",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:initial-hp-crit-rate",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    PanelStatDerivedValue(
                        source_character_id=ZHAO_ID,
                        source_node=CalculationNode.CHARACTER_INITIAL_HP,
                        coefficient=Resolved(core_crit_per_hp),
                    ),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "core:spring-curtain-team-hp",
            core_source,
            "核心被动：涌泉幕全队最大生命值提升",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(SPRING_CURTAIN_ACTIVE,),
            effects=(
                _modifier(
                    "core:spring-curtain-team-hp",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                    Resolved(0.05),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "core:spring-curtain-team-attack",
            core_source,
            "核心被动：开启涌泉幕时的全队攻击力提升",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(SPRING_CURTAIN_ATTACK_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:spring-curtain-team-attack",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    Resolved(core_attack_flat),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    resource_diagnostic = _diag(
        "unsupported:character:1341:core:frostbite-entry-sequence",
        "Frostbite gain/cap, 3-second hit throttling, 180-second opening limit, entry/quick-assist sequence, and state durations are not replayed; current Frostbite, Curtain, combat, and timed buff states are explicit inputs.",
        core.description,
        blocking=False,
    )
    rules.append(
        _rule(
            "core:frostbite-resource-and-entry-sequence",
            core_source,
            "核心被动：霜寒值和登场状态",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(resource_diagnostic,),
        )
    )

    extra_source = source_for(
        ZHAO_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_base_bonus = _one(
        raw_record.extra_ability_description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Zhao Additional Ability base team damage bonus",
    ) / 100.0
    hp_threshold = _one(
        raw_record.extra_ability_description,
        r"初始最大生命值高于(?P<value>[\d.]+)点",
        "Zhao Additional Ability initial-HP threshold",
    )
    hp_step = _one(
        raw_record.extra_ability_description,
        r"每超过(?P<value>[\d.]+)点初始最大生命值",
        "Zhao Additional Ability initial-HP step",
    )
    extra_per_step = _one(
        raw_record.extra_ability_description,
        r"每超过[\d.]+点初始最大生命值，可使增伤效果额外提升(?P<value>[\d.]+)%",
        "Zhao Additional Ability damage per initial-HP step",
    ) / 100.0
    extra_max_total = _one(
        raw_record.extra_ability_description,
        r"总共提升至(?P<value>[\d.]+)%",
        "Zhao Additional Ability total damage cap",
    ) / 100.0
    extra_max = extra_max_total - extra_base_bonus
    extra_effects = (
        _modifier(
            "extra-ability:curtain-team-damage-base",
            extra_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(extra_base_bonus),
            target=EffectTarget.TEAM,
        ),
        _modifier(
            "extra-ability:curtain-team-damage-from-initial-hp",
            extra_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            PanelStatDerivedValue(
                source_character_id=ZHAO_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_HP,
                coefficient=Resolved(extra_per_step / hp_step),
                cap_max=Resolved(extra_max),
                threshold=Resolved(hp_threshold),
            ),
            target=EffectTarget.TEAM,
        ),
    )
    rules.append(
        _rule(
            "extra-ability:curtain-team-damage",
            extra_source,
            "额外能力：以太帷幕下全队伤害提升",
            raw_record.extra_ability_description,
            extra_eligibility,
            conditions=(ANY_ETHER_CURTAIN_ACTIVE,),
            effects=extra_effects,
        )
    )

    c1 = raw_record.mindscapes[0]
    c1_source = source_for(ZHAO_ID, "cinema1", EffectSourceType.CINEMA, c1.name, c1.description)
    c1_res_ignore = _one(
        c1.description,
        r"无视目标(?P<value>[\d.]+)%全属性伤害抗性",
        "Zhao Cinema 1 team resistance ignore",
    ) / 100.0
    rules.append(
        _rule(
            "cinema1:team-resistance-ignore",
            c1_source,
            "1影：照切出后的全队全属性抗性无视",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            conditions=(ZHAO_C1_RESISTANCE_IGNORE_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:team-resistance-ignore",
                    c1_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c1_res_ignore),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    c2 = raw_record.mindscapes[1]
    c2_source = source_for(ZHAO_ID, "cinema2", EffectSourceType.CINEMA, c2.name, c2.description)
    c2_values = tuple(float(value) / 100.0 for value in re.findall(r"提升([\d.]+)%攻击力", _plain(c2.description)))
    if len(c2_values) != 2:
        raise ValueError("Zhao Cinema 2 must specify self and other-team attack bonuses")
    rules.append(
        _rule(
            "cinema2:healing-attack-buffs",
            c2_source,
            "2影：回血触发的照与其他队员攻击力提升",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            conditions=(ZHAO_C2_ATTACK_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:zhao-attack-bonus-after-heal",
                    c2_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    Resolved(c2_values[0]),
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    "cinema2:other-team-attack-bonus-after-heal",
                    c2_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    Resolved(c2_values[1]),
                    target=EffectTarget.TEAM_OTHER,
                ),
            ),
            diagnostics=(
                _diag(
                    "unsupported:character:1341:cinema2:heal-trigger",
                    "The 50-second C2 buff is selected as a current state. The calculator does not replay healing ticks or determine whether an HP-recovery event caused it.",
                    c2.description,
                    blocking=False,
                ),
            ),
        )
    )

    c4 = raw_record.mindscapes[3]
    c4_source = source_for(ZHAO_ID, "cinema4", EffectSourceType.CINEMA, c4.name, c4.description)
    c4_crit_damage = _one(
        c4.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Zhao Cinema 4 crit-damage bonus",
    ) / 100.0
    c4_crit_effect = _modifier(
        "cinema4:final-judgment-chain-ultimate-crit-damage",
        c4_source,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        Resolved(c4_crit_damage),
        target=EffectTarget.TEAM,
        filters=(
            DamageDealerFilter(ZHAO_ID),
            DamageTypeFilter(DamageType.DIRECT),
            AnyFilter(
                (
                    MoveIdFilter(BASIC_FINAL_JUDGMENT_MOVE_ID),
                    MoveIdFilter(CHAIN_TEMPORARY_COOPERATION_MOVE_ID),
                    MoveIdFilter(ULTIMATE_RABBIT_SLASH_MOVE_ID),
                )
            ),
        ),
    )
    decibel_diag = _diag(
        "unsupported:character:1341:cinema4:decibel-resource",
        "Cinema 4's 250-decibel gain on Ether Curtain opening is a resource event; it is not replayed by the damage calculator.",
        c4.description,
        blocking=False,
    )
    rules.append(
        _rule(
            "cinema4:crit-damage-and-decibel",
            c4_source,
            "4影：终结技、连携技及最终裁决暴击伤害提升",
            c4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            effects=(c4_crit_effect,),
            diagnostics=(decibel_diag,),
        )
    )

    # Charge HP additions are per full second of user-selected charge duration.
    raw_moves = raw_move_index(raw_record)
    charge_text_match = re.search(
        r"\{CAL:([\d.]+)\+AvatarSkillLevel\(0\)\*([\d.]+),100,2\}%",
        _plain(raw_moves["普通攻击：最终裁决"].description),
    )
    if charge_text_match is None:
        raise ValueError("Zhao Final Judgment must include its max-HP charge formula")
    basic_effective_level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    charge_ratio = float(charge_text_match.group(1)) + float(charge_text_match.group(2)) * basic_effective_level
    charge_components = (
        _charge_hp_component(
            source=core_source,
            parent_move_id=BASIC_FINAL_JUDGMENT_MOVE_ID,
            key="basic-final-judgment",
            label="普通攻击：最终裁决",
            group=SkillGroup.BASIC_ATTACK,
            tags=_BASIC,
            ratio=charge_ratio,
        ),
        _charge_hp_component(
            source=core_source,
            parent_move_id=CHAIN_TEMPORARY_COOPERATION_MOVE_ID,
            key="chain-temporary-cooperation",
            label="连携技：临时合作",
            group=SkillGroup.CHAIN_ATTACK,
            tags=_CHAIN,
            ratio=charge_ratio,
        ),
        _charge_hp_component(
            source=core_source,
            parent_move_id=SUPPORT_FOLLOWUP_AFTERGLOW_MOVE_ID,
            key="support-afterglow",
            label="支援突击：凛光返照",
            group=SkillGroup.ASSIST,
            tags=_FOLLOWUP,
            ratio=charge_ratio,
        ),
    )
    charge_templates = tuple(item[0] for item in charge_components)
    charge_refs = tuple(item[1] for item in charge_components)
    charge_creations = tuple(item[2] for item in charge_components)
    charge_creation_ids = tuple(item[3] for item in charge_components)
    templates.extend(charge_templates)
    rules.append(
        _rule(
            "core:charged-hp-extra",
            core_source,
            "核心被动：三种终结一击的蓄力生命值追加伤害",
            raw_moves["普通攻击：最终裁决"].description,
            RuleEligibility.ELIGIBLE,
            effects=charge_creations,
            diagnostics=(
                _diag(
                    "unsupported:character:1341:core:frostbite-charge-sequence",
                    "The selected integer charge duration is applied directly; Frostbite accumulation, switching during charge, and charge consumption timing are not replayed.",
                    core.description,
                    blocking=False,
                ),
            ),
        )
    )

    c6 = raw_record.mindscapes[5]
    c6_source = source_for(ZHAO_ID, "cinema6", EffectSourceType.CINEMA, c6.name, c6.description)
    c6_crit_multiplier = _one(
        c6.description,
        r"提高暴击率的效果提升至原本的(?P<value>[\d.]+)%",
        "Zhao Cinema 6 core crit multiplier",
    ) / 100.0
    c6_charge_multiplier = _one(
        c6.description,
        r"额外伤害提升至原本的(?P<value>[\d.]+)%",
        "Zhao Cinema 6 charge-damage multiplier",
    ) / 100.0
    c6_effects = [
        _modifier(
            "cinema6:core-initial-hp-crit-increase",
            c6_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            PanelStatDerivedValue(
                source_character_id=ZHAO_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_HP,
                coefficient=Resolved(core_crit_per_hp * (c6_crit_multiplier - 1.0)),
            ),
            target=EffectTarget.SELF,
        )
    ]
    for creation_id in charge_creation_ids:
        c6_effects.append(
            _modifier(
                f"cinema6:charge-hp-extra-multiplier:{str(creation_id).split(':')[-1]}",
                c6_source,
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                Resolved(c6_charge_multiplier),
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(ZHAO_ID),
                    DamageTypeFilter(DamageType.DIRECT),
                    CreatedByEffectFilter(creation_id),
                ),
                operation=EffectOperation.MULTIPLY,
            )
        )
    rules.append(
        _rule(
            "cinema6:core-and-charge-multipliers",
            c6_source,
            "6影：核心暴击率与蓄力生命伤害提升",
            c6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            effects=tuple(c6_effects),
            diagnostics=(
                _diag(
                    "unsupported:character:1341:cinema6:charge-preservation",
                    "Cinema 6 preserves accumulated charge during the attack; no charge sequence or cancellation timeline is replayed.",
                    c6.description,
                    blocking=False,
                ),
            ),
        )
    )

    c3 = raw_record.mindscapes[2]
    c5 = raw_record.mindscapes[4]
    for cinema in (c3, c5):
        source = source_for(ZHAO_ID, f"cinema{cinema.level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        rules.append(
            _rule(
                f"cinema{cinema.level}:skill-levels",
                source,
                f"{cinema.level}影：技能等级提升",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= cinema.level else RuleEligibility.INELIGIBLE,
                diagnostics=(
                    _diag(
                        f"unsupported:character:1341:cinema{cinema.level}:skill-levels",
                        "The +2 skill levels are applied to raw source curves before event construction; no independent damage modifier is emitted.",
                        cinema.description,
                        blocking=False,
                    ),
                ),
            )
        )

    heal_diag = _diag(
        "unsupported:character:1341:special:team-heal",
        "Special and EX Special healing ticks and the 5% current-HP cost are not represented as damage events. C2 healing-derived Attack bonuses are an explicit current-state condition.",
        raw_moves["特殊技：碎冰溢寒"].description,
        blocking=False,
    )
    rules.append(
        _rule(
            "skill:special-heal",
            source_for(ZHAO_ID, "special-heal", EffectSourceType.SKILL, "特殊技：碎冰溢寒/强化特殊技：流霜冻土", raw_moves["特殊技：碎冰溢寒"].description),
            "特殊技：碎冰溢寒团队治疗与生命消耗",
            raw_moves["特殊技：碎冰溢寒"].description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(heal_diag,),
        )
    )

    entry_state_diag = _diag(
        "unsupported:character:1341:entry:quick-assist-window",
        "The Entry Skill's Quick Assist window and automatic follow-up timing are not replayed; its raw Entry Skill damage is calculated, and the state transitions remain explicit.",
        raw_moves["登场技：霜迸"].description,
        blocking=False,
    )
    rules.append(
        _rule(
            "entry:frostbite-resource-window",
            core_source,
            "登场技：霜寒值与快速支援窗口",
            raw_moves["登场技：霜迸"].description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(entry_state_diag,),
        )
    )

    independent_refs = (*charge_refs,)
    definition_source = source_for(
        ZHAO_ID,
        "nanoka-3.2",
        EffectSourceType.SKILL,
        raw_record.name,
        f"source_version={raw_record.source_version}; source_url={raw_record.source_url}",
    )
    return CharacterCalculationDefinition(
        character_id=ZHAO_ID,
        role=CharacterRole.DEFENSE,
        base_element=Element.ICE,
        source=definition_source,
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=tuple(conditions),
        scenario_parameters=tuple(parameters),
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=tuple(independent_refs),
        diagnostics=tuple(diagnostics),
    )


__all__ = ["ZHAO_ICE_ANOMALY_MOVE_ID", "ZHAO_ICE_ANOMALY_RECORD_ID", "compile_zhao", "load_raw_record"]
