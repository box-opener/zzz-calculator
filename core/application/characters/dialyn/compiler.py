"""Compile Dialyn's raw record into reviewed physical damage and Effects."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageDealerIdentityFilter,
    DamageSubtype,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    DynamicIdentity,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventCreationEffect,
    EventCreationResult,
    EventSelector,
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
from ..nanoka_compiler import (
    compile_direct_moves,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, NanokaRawMoveRecord, load_nanoka_raw_record
from ..templates import DirectDamageEventTemplate
from ..templates import AttributeAnomalyDamageEventTemplate, DisorderDamageEventTemplate
from .config import DialynCompileConfig
from .reviewed import (
    AFTER_SOUND_ACTIVE,
    AFTER_SOUND_HIT_COUNT,
    DIALYN_EX_CINEMA6_TAGS,
    DIALYN_EX_MOVE_IDS,
    DIALYN_ID,
    DIALYN_REVIEWED_MAPPING,
    DIALYN_PHYSICAL_ANOMALY_RECORD_ID,
    GOOD_REVIEW_ACTIVE,
    MALICIOUS_COMPLAINT_ACTIVE,
    PHYSICAL_DISORDER_REMAINING_SECONDS,
)


_EX_SPECIAL = DIALYN_EX_CINEMA6_TAGS
_AFTER_SOUND_EFFECT_ID = EffectId("effect:character:1481:cinema6:after-sound-hit")
_PREVIOUS_TEAMMATE_DAMAGE_EFFECT_ID = EffectId(
    "effect:character:1481:extra-ability:previous-teammate-hit"
)


def _static_physical_anomaly_entries():
    record_id = DIALYN_PHYSICAL_ANOMALY_RECORD_ID
    physical_move_id = MoveId("move:dialyn:physical-assault")
    physical_ref = DamageEventTemplateRef(
        template_id="template:character:1481:physical-assault",
        semantic_id=DamageEventSemanticId("event:character:1481:physical-assault"),
        label="属性异常：强击",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    physical_template = AttributeAnomalyDamageEventTemplate(
        ref=physical_ref,
        damage_dealer=DIALYN_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=DIALYN_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=physical_move_id,
    )
    physical_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1481:physical-assault"),
        character_id=DIALYN_ID,
        move_id=physical_move_id,
        display_name="属性异常：强击",
        original_text="按静态物理异常单人100%积蓄记录结算强击，伤害倍率7.13。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1481:physical-assault"),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=physical_ref,
    )

    disorder_move_id = MoveId("move:dialyn:physical-disorder")
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1481:physical-disorder",
        semantic_id=DamageEventSemanticId("event:character:1481:physical-disorder"),
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=DIALYN_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=DIALYN_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=disorder_move_id,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1481:physical-disorder"),
        character_id=DIALYN_ID,
        move_id=disorder_move_id,
        display_name="紊乱：物理异常",
        original_text="物理异常的紊乱基础倍率4.5，剩余持续时间每秒补偿0.075。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1481:physical-disorder"),
                label="紊乱基础倍率+剩余时间补偿",
                parameter_name="物理异常紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    duration_parameter = ScenarioIntegerParameter(
        parameter_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
        label="物理异常剩余持续时间（秒）",
        original_text="按静态物理异常记录为10秒；本次紊乱剩余时间由用户输入，未推断触发时机。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (physical_entry, disorder_entry),
        (physical_template, disorder_template),
        duration_parameter,
    )


def _condition(
    condition_id,
    label: str,
    original_text: str,
    value: bool | None = None,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    rule_key: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1481:{rule_key}"),
        owner=DIALYN_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    effect_key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1481:{effect_key}"),
            source=source,
            owner=DIALYN_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _number(text: str, pattern: str, *, subject: str) -> float:
    matches = tuple(re.finditer(pattern, text, re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one reviewed value; found {len(matches)}")
    return float(matches[0].group("value"))


def _ratio(text: str, pattern: str, *, subject: str) -> float:
    return _number(text, pattern, subject=subject) / 100.0


def _move(raw_moves: dict[str, NanokaRawMoveRecord], name: str) -> NanokaRawMoveRecord:
    try:
        return raw_moves[name]
    except KeyError as exc:
        raise ValueError(f"Dialyn raw record is missing move {name!r}") from exc


def _diagnostic(
    key: str,
    kind: DiagnosticKind,
    message: str,
    original_text: str,
    *,
    blocking: bool = False,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"{key}"),
        kind=kind,
        message=message,
        blocking=blocking,
        original_text=original_text,
    )


def _direct_template(
    *,
    key: str,
    label: str,
    move_id: MoveId | None,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    source_rule_item_id: RuleItemId | None = None,
) -> DirectDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1481:{key}",
        semantic_id=DamageEventSemanticId(f"event:character:1481:{key}"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=Element.PHYSICAL,
        source_rule_item_id=source_rule_item_id,
    )
    return DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=DIALYN_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(DIALYN_ID),
        crit_rule=StandardCritRule(DIALYN_ID),
        move_id=move_id,
    )


def _previous_teammate_extra_damage(
    raw: NanokaRawRecord,
    source: RuleSource,
) -> EventCreationEffect:
    extra = raw.extra_ability_description
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            "The Additional Ability states two formulas for the 'previous teammate' "
            "but the calculation request carries only primary and supporting team "
            "membership, not an ordered active-party history or typed previous-"
            "teammate reference. It also does not fully identify the generated hit's "
            "damage dealer, element, or crit owner. No teammate panel or damage value "
            "is selected."
        ),
        original_text=extra,
        candidates=(
            "Previous Attack teammate: 320% of that teammate's attack",
            "Previous Rupture teammate: 400% of that teammate's penetration force",
        ),
    )
    ex_move_filters = tuple(MoveIdFilter(move_id) for move_id in DIALYN_EX_MOVE_IDS)
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=_PREVIOUS_TEAMMATE_DAMAGE_EFFECT_ID,
            source=source,
            owner=DIALYN_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageDealerFilter(DIALYN_ID),
                DamageTypeFilter(DamageType.DIRECT),
                AnyFilter(ex_move_filters),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=unresolved,
        ),
    )


def compile_dialyn(
    config: DialynCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != DIALYN_ID:
        raise ValueError("Dialyn compiler requires character:1481 raw data")
    if raw_record.element != "物理":
        raise ValueError("Dialyn raw data must identify 物理 as its base element")

    direct_entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=DIALYN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=DIALYN_REVIEWED_MAPPING,
        id_namespace="character:1481",
    )
    entries, anomaly_templates, disorder_remaining_parameter = _static_physical_anomaly_entries()
    entries = (*direct_entries, *entries)
    templates: list[object] = [*direct_templates, *anomaly_templates]
    rules: list[CalculationRuleItem] = []
    conditions = [
        _condition(
            GOOD_REVIEW_ACTIVE,
            "全队当前处于好评如潮状态",
            "额外能力在发动强化特殊技或终结技后使全队获得好评如潮；当前状态和剩余时长由本次请求选择。",
        ),
        _condition(
            MALICIOUS_COMPLAINT_ACTIVE,
            "目标当前处于恶意投诉状态",
            "强化特殊技：布！命中后施加恶意投诉；失衡恢复前至多触发一次。",
        ),
        _condition(
            AFTER_SOUND_ACTIVE,
            "队伍中当前有一名角色持有余音",
            "影画6在队友通过核心机制以终结技入场后赋予余音；当前唯一持有者状态按本次请求选择。",
        ),
    ]

    raw_moves = raw_move_index(raw_record)
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        DIALYN_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_impact_per_one_percent = _number(
        core.description,
        r"初始暴击率超过50%时，每超过1%，冲击力提升<color=[^>]+>(?P<value>[\d.]+)</color>点",
        subject="Dialyn Core initial-crit impact coefficient",
    )
    core_malicious_stun_vulnerability = _ratio(
        core.description,
        r"\[恶意投诉\]</color>效果下敌人进入失衡状态后的失衡持续时间提升\d+秒，失衡易伤倍率提升<color=[^>]+>(?P<value>[\d.]+)%</color>",
        subject="Dialyn Core malicious-complaint stun vulnerability",
    )
    resource_diagnostic = _diagnostic(
        "unsupported:character:1481:core:reviews-sequence-and-forced-chain",
        DiagnosticKind.UNSUPPORTED_CALCULATOR,
        "Review accumulation, the 8-second Rock/Scissors EX transition, complaint consumption, chain-window creation, and forced-Ultimate sequence are not replayed by the static damage calculator.",
        core.description,
    )
    rules.append(
        _rule(
            "core:initial-crit-impact",
            core_source,
            "核心被动：初始暴击率转冲击力",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(resource_diagnostic,),
            effects=(
                _modifier(
                    "core:initial-crit-impact",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
                    PanelStatDerivedValue(
                        source_character_id=DIALYN_ID,
                        source_node=CalculationNode.CHARACTER_INITIAL_CRIT_RATE,
                        coefficient=Resolved(core_impact_per_one_percent * 100.0),
                        cap_max=Resolved(100.0),
                        threshold=Resolved(0.50),
                    ),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "core:paper-malicious-complaint-stun-vulnerability",
            core_source,
            "核心被动：恶意投诉失衡易伤",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(MALICIOUS_COMPLAINT_ACTIVE,),
            effects=(
                _modifier(
                    "core:paper-malicious-complaint-stun-vulnerability",
                    core_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(core_malicious_stun_vulnerability),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    )

    extra_source = source_for(
        DIALYN_ID,
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
    extra_good_review_damage = _ratio(
        raw_record.extra_ability_description,
        r"状态下的角色造成的伤害提升(?P<value>[\d.]+)%",
        subject="Dialyn Additional Ability Good Review team damage bonus",
    )
    extra_ex_crit_damage = _ratio(
        raw_record.extra_ability_description,
        r"琉音造成的<color=#FFFFFF>\[强化特殊技\]</color>伤害的暴击伤害提升(?P<value>[\d.]+)%",
        subject="Dialyn Additional Ability EX Special crit damage",
    )
    extra_diagnostic = _diagnostic(
        "unsupported:character:1481:extra-ability:good-review-timing",
        DiagnosticKind.UNSUPPORTED_CALCULATOR,
        "Good Review duration refresh and the 35-second refresh threshold are represented only as a current-state input.",
        raw_record.extra_ability_description,
    )
    rules.append(
        _rule(
            "extra-ability:good-review-team-damage",
            extra_source,
            "额外能力：好评如潮全队增伤",
            raw_record.extra_ability_description,
            extra_eligibility,
            condition_ids=(GOOD_REVIEW_ACTIVE,),
            diagnostics=(extra_diagnostic,),
            effects=(
                _modifier(
                    "extra-ability:good-review-team-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(extra_good_review_damage),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "extra-ability:ex-special-crit-damage",
            extra_source,
            "额外能力：强化特殊技暴击伤害",
            raw_record.extra_ability_description,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:ex-special-crit-damage",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(extra_ex_crit_damage),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(DIALYN_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                    ),
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "extra-ability:previous-teammate-extra-hit",
            extra_source,
            "额外能力：上一位队友强化特殊技追加伤害（身份未决）",
            raw_record.extra_ability_description,
            extra_eligibility,
            effects=(_previous_teammate_extra_damage(raw_record, extra_source),),
        )
    )

    c1 = _mindscape(raw_record, 1)
    c1_source = source_for(
        DIALYN_ID,
        "cinema1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    c1_resistance_ignore = _ratio(
        c1.description,
        r"\[好评如潮\]</color>状态下的角色无视敌人(?P<value>[\d.]+)%全属性伤害抗性",
        subject="Dialyn Cinema 1 Good Review all-element resistance ignore",
    )
    c1_review_diagnostic = _diagnostic(
        "unsupported:character:1481:cinema1:review-accumulation",
        DiagnosticKind.UNSUPPORTED_CALCULATOR,
        "Cinema 1's 16% Good Review accumulation improvement and 15-second Good Review reapplication are not simulated.",
        c1.description,
    )
    rules.append(
        _rule(
            "cinema1:review-accumulation",
            c1_source,
            "1影：好评积累与状态续期",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            diagnostics=(c1_review_diagnostic,),
        )
    )
    c1_good_review_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 1 and config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema1:good-review-resistance-ignore",
            c1_source,
            "1影：好评如潮全属性抗性无视",
            c1.description,
            c1_good_review_eligibility,
            condition_ids=(GOOD_REVIEW_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:good-review-resistance-ignore",
                    c1_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c1_resistance_ignore),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    c2 = _mindscape(raw_record, 2)
    c2_source = source_for(
        DIALYN_ID,
        "cinema2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    c2_stun_vulnerability = _ratio(
        c2.description,
        r"\[恶意投诉\]</color>效果下敌人进入失衡状态后的失衡易伤倍率额外提升(?P<value>[\d.]+)%",
        subject="Dialyn Cinema 2 malicious-complaint stun vulnerability",
    )
    c2_damage_bonus = _ratio(
        c2.description,
        r"所有单位对<color=#FFFFFF>\[恶意投诉\]</color>效果下的敌人造成的伤害提升(?P<value>[\d.]+)%",
        subject="Dialyn Cinema 2 damage bonus against malicious complaint",
    )
    c2_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 2
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema2:complaint-stun-vulnerability",
            c2_source,
            "2影：恶意投诉目标失衡易伤",
            c2.description,
            c2_eligibility,
            condition_ids=(MALICIOUS_COMPLAINT_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:complaint-stun-vulnerability",
                    c2_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(c2_stun_vulnerability),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "cinema2:complaint-damage-bonus",
            c2_source,
            "2影：恶意投诉目标受到的全队伤害提升",
            c2.description,
            c2_eligibility,
            condition_ids=(MALICIOUS_COMPLAINT_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:complaint-damage-bonus",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c2_damage_bonus),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    for level in (3, 5):
        mindscape = _mindscape(raw_record, level)
        source = source_for(
            DIALYN_ID,
            f"cinema{level}",
            EffectSourceType.CINEMA,
            f"{level}影：{mindscape.name}",
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：{mindscape.name}",
                mindscape.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    c4 = _mindscape(raw_record, 4)
    c4_source = source_for(
        DIALYN_ID,
        "cinema4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    c4_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 4
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema4:decibel-resource",
            c4_source,
            f"4影：{c4.name}（喧响值）",
            c4.description,
            c4_eligibility,
            diagnostics=(
                _diagnostic(
                    "unsupported:character:1481:cinema4:decibel-resource",
                    DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    "Cinema 4's 100-decibel resource gain and 180-second refresh limit are not represented by the static damage calculator.",
                    c4.description,
                ),
            ),
        )
    )
    c4_attack_bonus = _number(
        c4.description,
        r"\[好评如潮\]</color>效果下，琉音攻击力提升(?P<value>[\d.]+)点",
        subject="Dialyn Cinema 4 Good Review attack bonus",
    )
    c4_panel_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 4 and config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema4:good-review-attack",
            c4_source,
            "4影：好评如潮琉音攻击力提升",
            c4.description,
            c4_panel_eligibility,
            condition_ids=(GOOD_REVIEW_ACTIVE,),
            effects=(
                _modifier(
                    "cinema4:good-review-attack",
                    c4_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    Resolved(c4_attack_bonus),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )

    c6 = _mindscape(raw_record, 6)
    c6_source = source_for(
        DIALYN_ID,
        "cinema6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    c6_eligible = (
        config.cinema_level >= 6 and config.after_sound_eligible
    )
    c6_rule_eligibility = (
        RuleEligibility.ELIGIBLE if c6_eligible else RuleEligibility.INELIGIBLE
    )
    c6_multiplier = _ratio(
        c6.description,
        r"额外一次<color=[^>]+>物理属性伤害</color>，等同于琉音(?P<value>[\d.]+)%攻击力",
        subject="Dialyn Cinema 6 AfterSound physical damage",
    )
    c6_template = _direct_template(
        key="cinema6-after-sound-hit",
        label="6影：余音命中后的额外物理伤害",
        move_id=None,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=_EX_SPECIAL,
        source_rule_item_id=RuleItemId("rule:character:1481:cinema6:after-sound-hit"),
    )
    c6_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=_AFTER_SOUND_EFFECT_ID,
            source=c6_source,
            owner=DIALYN_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
            filters=(
                DamageDealerIdentityFilter(DynamicIdentity.SUPPORT_ENTRY_CHARACTER),
                NotFilter(DamageDealerFilter(DIALYN_ID)),
                AnyFilter(
                    (
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTypeFilter(DamageType.PENETRATION),
                    )
                ),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=c6_template.ref.template_id,
        ),
    )
    c6_static_diagnostic = _diagnostic(
        "unsupported:character:1481:cinema6:after-sound-cooldown",
        DiagnosticKind.UNSUPPORTED_CALCULATOR,
        "Cinema 6's one-second trigger interval is not replayed; the requested repeat count is an explicit count of eligible hits and is capped at the source-stated 12.",
        c6.description,
    )
    rules.append(
        _rule(
            "cinema6:after-sound-hit",
            c6_source,
            "6影：余音持有者命中后的额外攻击",
            c6.description,
            c6_rule_eligibility,
            condition_ids=(AFTER_SOUND_ACTIVE,),
            diagnostics=(c6_static_diagnostic,),
            effects=(c6_effect,),
        )
    )
    templates.append(c6_template)

    # The multiplier and event classification are source-stated, while the
    # cadence is not. The selected count is bounded by the text's 12 hits;
    # the one-second cooldown is documented but not simulated.
    after_sound_parameters = (
        (
            ScenarioIntegerParameter(
                parameter_id=AFTER_SOUND_HIT_COUNT,
                label="余音额外攻击次数",
                original_text=c6.description,
                resolution=ParameterResolution.USER_SELECTED,
                value=None,
                minimum=0,
                maximum=12,
            ),
        )
        if c6_eligible
        else ()
    )
    parameters = (disorder_remaining_parameter, *after_sound_parameters)
    c6_derived = DerivedDamageEventTemplateRef(
        template=c6_template.ref,
        multiplier=FixedMultiplier(Resolved(c6_multiplier)),
        repeat_count_parameter_id=(AFTER_SOUND_HIT_COUNT if c6_eligible else None),
        skip_when_repeat_count_zero=True,
    )

    return CharacterCalculationDefinition(
        character_id=DIALYN_ID,
        role=CharacterRole.STUN,
        base_element=Element.PHYSICAL,
        source=source_for(
            DIALYN_ID,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=tuple(conditions),
        scenario_parameters=parameters,
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=(c6_derived,),
        diagnostics=tuple(diagnostics),
    )


def _mindscape(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"Dialyn raw record is missing mindscape {level}") from exc


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(DIALYN_ID))


__all__ = ["compile_dialyn", "load_raw_record"]
