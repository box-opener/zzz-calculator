"""Compile Hugo's reviewed Nanoka 3.2 source into calculator contracts."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    DamageTagFilter,
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
    MoveId,
    NoCritRule,
    NotFilter,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    ScenarioParameterDerivedValue,
    ScenarioParameterRangeCondition,
    StandardCritRule,
    StateId,
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
    ScenarioConditionId,
    ScenarioParameterId,
)
from ...moves import DerivedDamageEventTemplateRef
from ...moves import DamageEventTemplateRef, MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ParameterResolution, ScenarioCondition, ScenarioIntegerParameter
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
from .config import HugoCompileConfig
from .reviewed import (
    HUGO_CHAIN_MOVE_ID,
    HUGO_C4_ICE_RESISTANCE_IGNORE_ACTIVE,
    HUGO_DARK_ECHO_ACTIVE,
    HUGO_ID,
    HUGO_EX_MOVE_ID,
    HUGO_REVIEWED_MAPPING,
    HUGO_TARGET_IS_NORMAL,
    HUGO_ICE_ANOMALY_RECORD_ID,
    HUGO_ICE_ANOMALY_MOVE_ID,
    HUGO_ICE_DISORDER_MOVE_ID,
)


_ENEMY_STUNNED = StateId("state:enemy:stunned")
_ICE_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1291:ice-shatter")
_ICE_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1291:ice-disorder")
_CHAIN_TEMPLATE_ID = EventTemplateId("template:character:1291:chain-attack:main")
_EX_FULL_TEMPLATE_ID = EventTemplateId("template:character:1291:ex-special-full:main")
_EX_FINISHER_TEMPLATE_ID = EventTemplateId("template:character:1291:ex-special-finisher:main")
_EX_FULL_FINISHER_TEMPLATE_ID = EventTemplateId("template:character:1291:ex-special-full:finisher")
_ULTIMATE_TEMPLATE_ID = EventTemplateId("template:character:1291:ultimate:main")
_ICE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:hugo:ice-disorder-remaining-seconds"
)
_CURRENT_STUN_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:hugo:current-stun-remaining-seconds"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, text: str, value: bool = False) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(HUGO_ID, key, kind, label, text)


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
    condition_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1291:{key}"),
        owner=HUGO_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
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
            effect_id=EffectId(f"effect:character:1291:{key}"),
            source=source,
            owner=HUGO_ID,
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


def _unresolved_scope_effect(
    key: str,
    source: RuleSource,
    *,
    parent_template_ids: tuple[EventTemplateId, ...],
    original_text: str,
    notes: str,
    filters=(),
) -> EventCreationEffect:
    parent_filter = (
        EventTemplateIdFilter(parent_template_ids[0])
        if len(parent_template_ids) == 1
        else AnyFilter(tuple(EventTemplateIdFilter(item) for item in parent_template_ids))
    )
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes=notes,
        original_text=original_text,
    )
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1291:{key}"),
            source=source,
            owner=HUGO_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(HUGO_ID),
                parent_filter,
                *filters,
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=unresolved,
            unique_per_source_event=True,
        ),
    )


def _full_ex_entry(
    raw: NanokaRawRecord,
    entries: list[MoveCalculationEntry],
    templates: list,
):
    spin_entry = next(
        item for item in entries
        if str(item.entry_id) == "move-entry:character:1291:ex-special-spin"
    )
    finisher_entry = next(
        item for item in entries
        if str(item.entry_id) == "move-entry:character:1291:ex-special-finisher"
    )
    spin_ratio = spin_entry.multiplier_variants[0].multiplier.value.value
    finisher_ratio = finisher_entry.multiplier_variants[0].multiplier.value.value
    source_move = raw_move_index(raw)["强化特殊技：魂狩·惩戒"]
    parent_ref = DamageEventTemplateRef(
        template_id=_EX_FULL_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1291:ex-special-full:spin"),
        label="强化特殊技完整招式（旋转段）",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=frozenset({DamageTag.EX_SPECIAL_ATTACK}),
        element=Element.ICE,
    )
    parent_template = DirectDamageEventTemplate(
        ref=parent_ref,
        damage_dealer=HUGO_ID,
        element=Element.ICE,
        base_source=CurrentAttackValueSource(HUGO_ID),
        crit_rule=StandardCritRule(HUGO_ID),
        move_id=HUGO_EX_MOVE_ID,
    )
    child_ref = DamageEventTemplateRef(
        template_id=_EX_FULL_FINISHER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1291:ex-special-full:finisher"),
        label="强化特殊技完整招式（终结一击）",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=frozenset({DamageTag.EX_SPECIAL_ATTACK}),
        element=Element.ICE,
    )
    child_template = DirectDamageEventTemplate(
        ref=child_ref,
        damage_dealer=HUGO_ID,
        element=Element.ICE,
        base_source=CurrentAttackValueSource(HUGO_ID),
        crit_rule=StandardCritRule(HUGO_ID),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1291:ex-special-full"),
        character_id=HUGO_ID,
        move_id=HUGO_EX_MOVE_ID,
        display_name="强化特殊技：魂狩·惩戒（完整：旋转+终结）",
        original_text=(
            f"完整招式采用来源两项倍率相加：{spin_ratio:.4f} + {finisher_ratio:.4f}；"
            "输出将旋转段与终结一击分开结算。"
        ),
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=frozenset({DamageTag.EX_SPECIAL_ATTACK}),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1291:ex-special-full"),
                label=f"旋转段{spin_ratio:.4f}；终结段另计{finisher_ratio:.4f}",
                parameter_name="旋转段伤害倍率",
                multiplier=FixedMultiplier(Resolved(spin_ratio)),
            ),
        ),
        main_damage_event=parent_ref,
        derived_damage_events=(
            DerivedDamageEventTemplateRef(
                template=child_ref,
                multiplier=FixedMultiplier(Resolved(finisher_ratio)),
                required=True,
            ),
        ),
    )
    return entry, (parent_template, child_template)


def _full_chain_entry(
    raw: NanokaRawRecord,
    entries: list[MoveCalculationEntry],
):
    base_entry = next(
        item for item in entries
        if str(item.entry_id) == "move-entry:character:1291:chain-attack"
    )
    ratio = base_entry.multiplier_variants[0].multiplier.value.value
    source_move = raw_move_index(raw)["连携技：命运戏法"]
    charged_shot_entry = next(
        item for item in entries
        if str(item.entry_id) == "move-entry:character:1291:basic-fourth-charged-shot"
    )
    charged_shot_ratio = charged_shot_entry.multiplier_variants[0].multiplier.value.value
    child_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1291:chain-full:charged-shot"),
        semantic_id=DamageEventSemanticId("event:character:1291:chain-full:charged-shot"),
        label="连携技后续蓄力射击（普通攻击）",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        element=Element.ICE,
    )
    child_template = DirectDamageEventTemplate(
        ref=child_ref,
        damage_dealer=HUGO_ID,
        element=Element.ICE,
        base_source=CurrentAttackValueSource(HUGO_ID),
        crit_rule=StandardCritRule(HUGO_ID),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1291:chain-full"),
        character_id=HUGO_ID,
        move_id=HUGO_CHAIN_MOVE_ID,
        display_name="连携技：命运戏法（斩击+蓄力射击）",
        original_text=(
            f"连携技斩击倍率{ratio:.4f}，并结算一次普通攻击蓄力射击"
            f"倍率{charged_shot_ratio:.4f}。{source_move.description}"
        ),
        skill_group=SkillGroup.CHAIN_ATTACK,
        damage_tags=frozenset({DamageTag.CHAIN_ATTACK}),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1291:chain-full"),
                label=f"斩击{ratio:.4f}；蓄力射击另计{charged_shot_ratio:.4f}",
                parameter_name="斩击伤害倍率",
                multiplier=FixedMultiplier(Resolved(ratio)),
            ),
        ),
            main_damage_event=base_entry.main_damage_event,
            derived_damage_events=(
                DerivedDamageEventTemplateRef(
                    template=child_ref,
                    multiplier=FixedMultiplier(Resolved(charged_shot_ratio)),
                    required=True,
                ),
            ),
        )
    return entry, child_template


def _static_ice_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=_ICE_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1291:ice-shatter"),
        label="属性异常：碎冰（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=HUGO_ID,
        element=Element.ICE,
        anomaly_triggerer=HUGO_ID,
        history_record_source=HUGO_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=HUGO_ICE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1291:ice-shatter"),
        character_id=HUGO_ID,
        move_id=HUGO_ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：碎冰（10秒满异常）",
        original_text="按规范使用静态单人100%冰属性异常记录；碎冰固定倍率500%，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1291:ice-shatter"),
                label="碎冰倍率500%",
                parameter_name="冰属性碎冰伤害倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id=_ICE_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1291:ice-disorder"),
        label="紊乱：碎冰（当前剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=HUGO_ID,
        element=Element.ICE,
        disorder_triggerer=HUGO_ID,
        history_record_source=HUGO_ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=HUGO_ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1291:ice-disorder"),
        character_id=HUGO_ID,
        move_id=HUGO_ICE_DISORDER_MOVE_ID,
        display_name="紊乱：碎冰（当前剩余时间）",
        original_text="冰属性紊乱倍率为450% + floor(t)×7.5%；t为当前剩余时间，不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1291:ice-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="冰属性紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_ICE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_ICE_DISORDER_REMAINING_SECONDS,
        label="冰属性紊乱当前剩余时间（秒）",
        original_text="使用当前剩余时间0–10秒，默认10秒；不模拟冰异常时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def compile_hugo(
    config: HugoCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=HUGO_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=HUGO_REVIEWED_MAPPING,
    )
    entries = list(entries)
    templates = list(templates)
    rules: list[CalculationRuleItem] = []
    ex_full_entry, ex_full_templates = _full_ex_entry(
        raw_record,
        entries,
        templates,
    )
    entries.append(ex_full_entry)
    templates.extend(ex_full_templates)
    chain_full_entry, chain_full_template = _full_chain_entry(
        raw_record,
        entries,
    )
    entries.append(chain_full_entry)
    templates.append(chain_full_template)
    conditions: list[ScenarioCondition] = [
        _condition(
            HUGO_DARK_ECHO_ACTIVE,
            "雨果的暗渊回响当前生效",
            raw_record.core_levels[config.core_level - 1].description,
        ),
    ]

    core = raw_record.core_levels[config.core_level - 1]
    decision_remaining = ScenarioIntegerParameter(
        parameter_id=_CURRENT_STUN_REMAINING_SECONDS,
        label="决算当前目标剩余失衡时间（秒）",
        original_text=(
            "按触发【决算】时的当前剩余失衡时间选择0–15秒；"
            "不模拟失衡时间、决算后失衡值或时间轴。"
        ),
        resolution=ParameterResolution.USER_SELECTED,
        value=None,
        minimum=0,
        maximum=15,
    )
    core_text = _plain(core.description)
    attack_match = re.search(
        r"队伍中存在其他1/2名\[击破\]角色时，雨果的攻击力提升(?P<one>[\d.]+)/(?P<two>[\d.]+)点",
        core_text,
    )
    if attack_match is None:
        raise ValueError("Hugo Core source is missing the Stun-teammate ATK values")
    attack_value = float(
        attack_match.group("one" if config.stun_teammate_count == 1 else "two")
    ) if config.stun_teammate_count else 0.0
    core_source = _source("core", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    core_effects = ()
    if attack_value:
        core_effects = (
            _modifier(
                "core:stun-team-current-attack",
                core_source,
                CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                Resolved(attack_value),
                target=EffectTarget.SELF,
            ),
        )
    dark_echo_crit_rate = _number(
        core.description,
        r"该状态下雨果的暴击率提升(?P<value>[\d.]+)%",
        "Hugo Dark Echo Crit Rate",
    ) / 100.0
    dark_echo_crit_damage = _number(
        core.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Hugo Dark Echo Crit Damage",
    ) / 100.0
    dark_echo_effects = (
        _modifier(
            "core:dark-echo-crit-rate",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            Resolved(dark_echo_crit_rate),
            target=EffectTarget.SELF,
        ),
        _modifier(
            "core:dark-echo-crit-damage",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            Resolved(dark_echo_crit_damage),
            target=EffectTarget.SELF,
        ),
    )
    decision_base_ratio = _number(
        core.description,
        r"终结一击伤害倍率提升(?P<value>[\d.]+)%",
        "Hugo Decision finisher base multiplier increase",
    ) / 100.0
    decision_rate_matches = tuple(
        re.finditer(
            r"每剩余1秒，招式伤害倍率提升(?P<value>[\d.]+)%",
            _plain(core.description),
        )
    )
    if len(decision_rate_matches) != 2:
        raise ValueError("Hugo Core source must define both Decision time coefficients")
    decision_short_rate = float(decision_rate_matches[0].group("value")) / 100.0
    decision_long_rate = float(decision_rate_matches[1].group("value")) / 100.0
    decision_cap = _number(
        core.description,
        r"总共最多可以提升(?P<value>[\d.]+)%的招式伤害倍率",
        "Hugo Decision total multiplier cap",
    ) / 100.0
    finisher_entry = next(
        item for item in entries
        if str(item.entry_id) == "move-entry:character:1291:ex-special-finisher"
    )
    ultimate_entry = next(
        item for item in entries
        if str(item.entry_id) == "move-entry:character:1291:ultimate"
    )
    ex_finisher_ratio = finisher_entry.multiplier_variants[0].multiplier.value.value
    ultimate_ratio = ultimate_entry.multiplier_variants[0].multiplier.value.value
    ex_terminal_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(HUGO_ID),
        AnyFilter(
            (
                EventTemplateIdFilter(_EX_FINISHER_TEMPLATE_ID),
                EventTemplateIdFilter(_EX_FULL_FINISHER_TEMPLATE_ID),
            )
        ),
        EnemyStateFilter(_ENEMY_STUNNED),
    )
    ex_terminal_long_stun_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(HUGO_ID),
        AnyFilter(
            (
                EventTemplateIdFilter(_EX_FINISHER_TEMPLATE_ID),
                EventTemplateIdFilter(_EX_FULL_FINISHER_TEMPLATE_ID),
            )
        ),
        EnemyStateFilter(_ENEMY_STUNNED),
    )
    ultimate_stun_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(HUGO_ID),
        EventTemplateIdFilter(_ULTIMATE_TEMPLATE_ID),
        EnemyStateFilter(_ENEMY_STUNNED),
    )
    ex_short_stun_effect = _modifier(
        "core:decision-ex-short-stun-multiplier",
        core_source,
        CalculationNode.DAMAGE_SKILL_MULTIPLIER,
        ScenarioParameterDerivedValue(
            parameter_id=str(_CURRENT_STUN_REMAINING_SECONDS),
            coefficient=Resolved(decision_short_rate / ex_finisher_ratio),
            base=Resolved(1.0 + decision_base_ratio / ex_finisher_ratio),
            cap_max=Resolved(
                1.0
                + min(
                    decision_base_ratio + decision_short_rate * 5,
                    decision_cap,
                )
                / ex_finisher_ratio
            ),
        ),
        target=EffectTarget.SELF,
        filters=ex_terminal_filters,
        operation=EffectOperation.MULTIPLY,
        condition=ScenarioParameterRangeCondition(
            str(_CURRENT_STUN_REMAINING_SECONDS), minimum=0, maximum=5
        ),
    )
    ex_long_stun_effect = _modifier(
        "core:decision-ex-long-stun-multiplier",
        core_source,
        CalculationNode.DAMAGE_SKILL_MULTIPLIER,
        ScenarioParameterDerivedValue(
            parameter_id=str(_CURRENT_STUN_REMAINING_SECONDS),
            coefficient=Resolved(decision_long_rate / ex_finisher_ratio),
            base=Resolved(
                1.0
                + (
                    decision_base_ratio
                    + decision_short_rate * 5
                    - decision_long_rate * 5
                )
                / ex_finisher_ratio
            ),
            cap_max=Resolved(1.0 + decision_cap / ex_finisher_ratio),
        ),
        target=EffectTarget.SELF,
        filters=ex_terminal_long_stun_filters,
        operation=EffectOperation.MULTIPLY,
        condition=ScenarioParameterRangeCondition(
            str(_CURRENT_STUN_REMAINING_SECONDS), minimum=6, maximum=15
        ),
    )
    ultimate_short_stun_effect = _modifier(
        "core:decision-ultimate-short-stun-multiplier",
        core_source,
        CalculationNode.DAMAGE_SKILL_MULTIPLIER,
        ScenarioParameterDerivedValue(
            parameter_id=str(_CURRENT_STUN_REMAINING_SECONDS),
            coefficient=Resolved(decision_short_rate / ultimate_ratio),
            base=Resolved(1.0 + decision_base_ratio / ultimate_ratio),
            cap_max=Resolved(
                1.0
                + min(
                    decision_base_ratio + decision_short_rate * 5,
                    decision_cap,
                )
                / ultimate_ratio
            ),
        ),
        target=EffectTarget.SELF,
        filters=ultimate_stun_filters,
        operation=EffectOperation.MULTIPLY,
        condition=ScenarioParameterRangeCondition(
            str(_CURRENT_STUN_REMAINING_SECONDS), minimum=0, maximum=5
        ),
    )
    ultimate_long_stun_effect = _modifier(
        "core:decision-ultimate-long-stun-multiplier",
        core_source,
        CalculationNode.DAMAGE_SKILL_MULTIPLIER,
        ScenarioParameterDerivedValue(
            parameter_id=str(_CURRENT_STUN_REMAINING_SECONDS),
            coefficient=Resolved(decision_long_rate / ultimate_ratio),
            base=Resolved(
                1.0
                + (
                    decision_base_ratio
                    + decision_short_rate * 5
                    - decision_long_rate * 5
                )
                / ultimate_ratio
            ),
            cap_max=Resolved(1.0 + decision_cap / ultimate_ratio),
        ),
        target=EffectTarget.SELF,
        filters=ultimate_stun_filters,
        operation=EffectOperation.MULTIPLY,
        condition=ScenarioParameterRangeCondition(
            str(_CURRENT_STUN_REMAINING_SECONDS), minimum=6, maximum=15
        ),
    )
    rules.append(
        _rule(
            "core:decision-ex-finisher-multiplier",
            core_source,
            "核心被动：失衡时EX与终结技【决算】倍率",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                ex_short_stun_effect,
                ex_long_stun_effect,
                ultimate_short_stun_effect,
                ultimate_long_stun_effect,
            ),
        )
    )
    additional = raw_record.core_levels[config.core_level - 1].extra_ability_description
    additional_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.core_levels[config.core_level - 1].extra_ability_name,
        additional,
    )
    chain_bonus = _number(
        additional,
        r"\[连携技：命运戏法\]造成的伤害提升(?P<value>[\d.]+)%",
        "Hugo Additional Ability Chain Damage Bonus",
    ) / 100.0
    normal_enemy_bonus = _number(
        additional,
        r"对普通敌人造成的伤害额外提升(?P<value>[\d.]+)%",
        "Hugo Additional Ability Normal Enemy Chain Bonus",
    ) / 100.0
    decision_bonus = _number(
        additional,
        r"触发\[决算\]时，招式造成的伤害提升(?P<value>[\d.]+)%",
        "Hugo Additional Ability Decision Damage Bonus",
    ) / 100.0
    additional_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    ex_terminal_ids = (_EX_FINISHER_TEMPLATE_ID, _EX_FULL_FINISHER_TEMPLATE_ID)
    ex_terminal_identity_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(HUGO_ID),
        AnyFilter(tuple(EventTemplateIdFilter(item) for item in ex_terminal_ids)),
    )
    rules.append(
        _rule(
            "extra-ability:chain-damage",
            additional_source,
            f"额外能力：连携技伤害+{chain_bonus:.0%}",
            additional,
            additional_eligibility,
            effects=(
                _modifier(
                    "extra-ability:chain-damage",
                    additional_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(chain_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(HUGO_ID),
                        EventTemplateIdFilter(_CHAIN_TEMPLATE_ID),
                    ),
                ),
            ),
        )
    )
    conditions.append(
        _condition(
            HUGO_TARGET_IS_NORMAL,
            "当前目标为普通敌人",
            additional,
        )
    )
    rules.append(
        _rule(
            "extra-ability:chain-normal-enemy-damage",
            additional_source,
            f"额外能力：对普通敌人连携技伤害+{normal_enemy_bonus:.0%}",
            additional,
            additional_eligibility,
            condition_ids=(HUGO_TARGET_IS_NORMAL,),
            effects=(
                _modifier(
                    "extra-ability:chain-normal-enemy-damage",
                    additional_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(normal_enemy_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(HUGO_ID),
                        EventTemplateIdFilter(_CHAIN_TEMPLATE_ID),
                    ),
                ),
            ),
        )
    )
    if config.additional_ability_eligible and decision_bonus:
        rules.append(
            _rule(
                "extra-ability:ex-decision-stunned-damage",
                additional_source,
                f"额外能力：决算时EX终结一击伤害+{decision_bonus:.0%}",
                additional,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "extra-ability:ex-decision-stunned-damage",
                        additional_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(decision_bonus),
                        target=EffectTarget.SELF,
                        filters=(
                            *ex_terminal_identity_filters,
                            EnemyStateFilter(_ENEMY_STUNNED),
                        ),
                    ),
                    _unresolved_scope_effect(
                        "extra-ability:decision-ult-scope",
                        additional_source,
                        parent_template_ids=(
                            _EX_FULL_TEMPLATE_ID,
                            _ULTIMATE_TEMPLATE_ID,
                        ),
                        original_text=additional,
                        notes=(
                            "额外能力的决算增伤数值已知，但完整强化特殊技旋转段与"
                            "终结技整招曲线之间的伤害分段范围尚未确认。"
                        ),
                        filters=(EnemyStateFilter(_ENEMY_STUNNED),),
                    ),
                ),
            )
        )
        if config.cinema_level >= 6:
            rules.append(
                _rule(
                    "extra-ability:ex-cinema6-nonstun-decision-damage",
                    additional_source,
                    f"额外能力：影画6非失衡EX终结一击决算伤害+{decision_bonus:.0%}",
                    additional,
                    RuleEligibility.ELIGIBLE,
                    effects=(
                        _modifier(
                            "extra-ability:ex-cinema6-nonstun-decision-damage",
                            additional_source,
                            CalculationNode.DAMAGE_NORMAL_BONUS,
                            Resolved(decision_bonus),
                            target=EffectTarget.SELF,
                            filters=(
                                *ex_terminal_identity_filters,
                                NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),
                            ),
                        ),
                        _unresolved_scope_effect(
                            "extra-ability:decision-ult-scope-nonstunned",
                            additional_source,
                            parent_template_ids=(_EX_FULL_TEMPLATE_ID,),
                            original_text=additional,
                            notes=(
                                "影画6非失衡决算的额外能力增伤分段范围尚未确认；"
                                "保留已知终结一击，不补算旋转段。"
                            ),
                            filters=(NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),),
                        ),
                    ),
                )
            )

    for level, message in (
        (1, "触发决算时的额外暴击属性已保留在可识别终结段；完整EX及终结技的分段范围待确认。"),
        (2, "终结技决算期间15%防御无视的分段范围待确认；不推测终结技各段倍率。"),
        (6, "影画6决算额外伤害的分段范围待确认；非失衡EX终结段固定倍率单独保留。"),
    ):
        mindscape = raw_record.mindscapes[level - 1]
        rules.append(
            _rule(
                f"cinema{level}:decision-source-note",
                _source(f"cinema{level}", EffectSourceType.CINEMA, mindscape.name, mindscape.description),
                f"{level}影：决算终结一击局部来源说明",
                mindscape.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(f"unsupported:character:1291:cinema{level}:decision-terminal"),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message=message,
                        blocking=False,
                        original_text=mindscape.description,
                    ),
                ),
            )
        )

    if config.cinema_level >= 2:
        cinema2 = raw_record.mindscapes[1]
        cinema2_source = _source(
            "cinema2:decision-defense-ignore",
            EffectSourceType.CINEMA,
            cinema2.name,
            cinema2.description,
        )
        cinema2_ex_filters = (
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(HUGO_ID),
            AnyFilter(tuple(EventTemplateIdFilter(item) for item in ex_terminal_ids)),
        )
        if config.cinema_level < 6:
            cinema2_ex_filters = (
                *cinema2_ex_filters,
                EnemyStateFilter(_ENEMY_STUNNED),
            )
        rules.append(
            _rule(
                "cinema2:decision-defense-ignore",
                cinema2_source,
                "2影：决算时无视15%防御；完整动作及终结技分段待确认",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema2:decision-ex-terminal-defense-ignore",
                        cinema2_source,
                        CalculationNode.DAMAGE_DEFENSE_IGNORE,
                        Resolved(0.15),
                        target=EffectTarget.SELF,
                        filters=cinema2_ex_filters,
                    ),
                    _unresolved_scope_effect(
                        "cinema2:decision-full-ex-scope",
                        cinema2_source,
                        parent_template_ids=(_EX_FULL_TEMPLATE_ID,),
                        original_text=cinema2.description,
                        notes=(
                            "2影15%防御无视的已知终结段效果已计入；旋转段"
                            "是否也受益尚未确认。"
                        ),
                        filters=(
                            (EnemyStateFilter(_ENEMY_STUNNED),)
                            if config.cinema_level < 6
                            else ()
                        ),
                    ),
                    _unresolved_scope_effect(
                        "cinema2:ultimate-decision-defense-ignore-scope",
                        cinema2_source,
                        parent_template_ids=(_ULTIMATE_TEMPLATE_ID,),
                        original_text=cinema2.description,
                        notes=(
                            "终结技决算15%防御无视数值已知，但整招倍率曲线中"
                            "决算终结段占比尚未确认。"
                        ),
                        filters=(EnemyStateFilter(_ENEMY_STUNNED),),
                    ),
                ),
            )
        )
    # Cinema 4 is an explicitly selectable current target state; the source
    # says the Ice resistance ignore is granted after a charged shot hit.
    if config.cinema_level >= 4:
        cinema4 = raw_record.mindscapes[3]
        conditions.append(
            _condition(
                HUGO_C4_ICE_RESISTANCE_IGNORE_ACTIVE,
                "雨果蓄力射击命中后的冰抗无视当前生效",
                cinema4.description,
            )
        )
        resistance_ignore = _number(
            cinema4.description,
            r"无视(?P<value>[\d.]+)%冰属性伤害抗性",
            "Hugo Cinema 4 Ice Resistance Ignore",
        ) / 100.0
        rules.append(
            _rule(
                "cinema4:ice-resistance-ignore",
                _source("cinema4", EffectSourceType.CINEMA, cinema4.name, cinema4.description),
                f"4影：当前冰抗无视{resistance_ignore:.0%}",
                cinema4.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema4:ice-resistance-ignore",
                        _source("cinema4", EffectSourceType.CINEMA, cinema4.name, cinema4.description),
                        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                        Resolved(resistance_ignore),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageDealerFilter(HUGO_ID),
                            ElementFilter(Element.ICE),
                        ),
                    ),
                ),
                condition_ids=(HUGO_C4_ICE_RESISTANCE_IGNORE_ACTIVE,),
            )
        )

    if config.cinema_level >= 1:
        cinema1 = raw_record.mindscapes[0]
        c1_crit_rate = _number(
            cinema1.description,
            r"暴击率额外提升(?P<value>[\d.]+)%",
            "Hugo Cinema 1 Decision Crit Rate",
        ) / 100.0
        c1_crit_damage = _number(
            cinema1.description,
            r"暴击伤害额外提升(?P<value>[\d.]+)%",
            "Hugo Cinema 1 Decision Crit Damage",
        ) / 100.0
        cinema1_source = _source(
            "cinema1:decision-crit",
            EffectSourceType.CINEMA,
            cinema1.name,
            cinema1.description,
        )
        stunned_crit_effects = (
            _modifier(
                "cinema1:ex-decision-stunned-crit-rate",
                cinema1_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                Resolved(c1_crit_rate),
                target=EffectTarget.SELF,
                filters=(
                    *ex_terminal_identity_filters,
                    EnemyStateFilter(_ENEMY_STUNNED),
                ),
            ),
            _modifier(
                "cinema1:ex-decision-stunned-crit-damage",
                cinema1_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                Resolved(c1_crit_damage),
                target=EffectTarget.SELF,
                filters=(
                    *ex_terminal_identity_filters,
                    EnemyStateFilter(_ENEMY_STUNNED),
                ),
            ),
            _unresolved_scope_effect(
                "cinema1:decision-stunned-scope",
                cinema1_source,
                parent_template_ids=(
                    _EX_FULL_TEMPLATE_ID,
                    _ULTIMATE_TEMPLATE_ID,
                ),
                original_text=cinema1.description,
                notes=(
                    "1影决算暴击提升的数值已知，但完整强化特殊技旋转段与"
                    "终结技整招曲线的暴击分段范围尚未确认。"
                ),
                filters=(EnemyStateFilter(_ENEMY_STUNNED),),
            ),
        )
        rules.append(
            _rule(
                "cinema1:ex-decision-stunned-crit",
                cinema1_source,
                "1影：暗渊回响期间EX决算终结一击暴击提升",
                cinema1.description,
                RuleEligibility.ELIGIBLE,
                effects=stunned_crit_effects,
                condition_ids=(HUGO_DARK_ECHO_ACTIVE,),
            )
        )
        if config.cinema_level >= 6:
            nonstun_crit_effects = (
                _modifier(
                    "cinema1:ex-cinema6-nonstun-crit-rate",
                    cinema1_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(c1_crit_rate),
                    target=EffectTarget.SELF,
                    filters=(
                        *ex_terminal_identity_filters,
                        NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),
                    ),
                ),
                _modifier(
                    "cinema1:ex-cinema6-nonstun-crit-damage",
                    cinema1_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c1_crit_damage),
                    target=EffectTarget.SELF,
                    filters=(
                        *ex_terminal_identity_filters,
                        NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),
                    ),
                ),
                _unresolved_scope_effect(
                    "cinema1:decision-nonstunned-scope",
                    cinema1_source,
                    parent_template_ids=(_EX_FULL_TEMPLATE_ID,),
                    original_text=cinema1.description,
                    notes=(
                        "影画6非失衡决算触发时，1影暴击提升是否覆盖完整EX旋转段"
                        "尚未确认；保留已知终结一击。"
                    ),
                    filters=(NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),),
                ),
            )
            rules.append(
                _rule(
                    "cinema1:ex-cinema6-nonstun-crit",
                    cinema1_source,
                    "1影：暗渊回响期间影画6非失衡EX决算终结一击暴击提升",
                    cinema1.description,
                    RuleEligibility.ELIGIBLE,
                    effects=nonstun_crit_effects,
                    condition_ids=(HUGO_DARK_ECHO_ACTIVE,),
                )
            )

    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        c6_decision_bonus = _number(
            cinema6.description,
            r"任意招式触发\[决算\]效果时，此次伤害额外提升(?P<value>[\d.]+)%",
            "Hugo Cinema 6 Decision Damage Bonus",
        ) / 100.0
        c6_terminal_bonus = _number(
            cinema6.description,
            r"终结一击伤害倍率固定提升(?P<value>[\d.]+)%",
            "Hugo Cinema 6 Nonstunned EX Finisher Multiplier Increase",
        ) / 100.0
        cinema6_source = _source(
            "cinema6:decision",
            EffectSourceType.CINEMA,
            cinema6.name,
            cinema6.description,
        )
        c6_effects = [
            _modifier(
                "cinema6:ex-decision-damage-bonus",
                cinema6_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(c6_decision_bonus),
                target=EffectTarget.SELF,
                filters=ex_terminal_identity_filters,
            ),
            _modifier(
                "cinema6:ex-nonstunned-decision-multiplier",
                cinema6_source,
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                Resolved(1.0 + c6_terminal_bonus / ex_finisher_ratio),
                target=EffectTarget.SELF,
                filters=(
                    *ex_terminal_identity_filters,
                    NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),
                ),
                operation=EffectOperation.MULTIPLY,
            ),
            _unresolved_scope_effect(
                "cinema6:decision-full-ex-scope",
                cinema6_source,
                parent_template_ids=(_EX_FULL_TEMPLATE_ID,),
                original_text=cinema6.description,
                notes=(
                    "影画6决算额外伤害提升数值已知，但完整EX的旋转段是否"
                    "一并受益尚未确认；保留已知终结一击。"
                ),
            ),
            _unresolved_scope_effect(
                "cinema6:decision-ultimate-scope",
                cinema6_source,
                parent_template_ids=(_ULTIMATE_TEMPLATE_ID,),
                original_text=cinema6.description,
                notes=(
                    "影画6决算额外伤害提升数值已知，但终结技整招曲线的"
                    "伤害分段范围尚未确认。"
                ),
                filters=(EnemyStateFilter(_ENEMY_STUNNED),),
            ),
        ]
        if config.additional_ability_eligible:
            c6_effects.append(
                _modifier(
                    "extra-ability:ex-cinema6-nonstun-decision-damage",
                    additional_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(decision_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        *ex_terminal_identity_filters,
                        NotFilter(EnemyStateFilter(_ENEMY_STUNNED)),
                    ),
                )
            )
        rules.append(
            _rule(
                "cinema6:ex-nonstunned-decision",
                cinema6_source,
                "6影：非失衡敌人上的EX终结一击触发决算",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                effects=tuple(c6_effects),
            )
        )

    # Static ice anomaly/disorder remain valid for every Hugo build.
    anomaly_entries, anomaly_templates, disorder_parameter = _static_ice_entries()
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)

    # The source lists Daze, Energy recovery and immediate Daze-state changes;
    # they are retained as source notes because the damage result has no such
    # fields and does not replay time or combat history.
    core_daze = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1291:core:daze-energy-and-stun-reset"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message="失衡值、决算后的失衡时间变化、能量回复和时长均不在当前伤害结果中模拟。",
        blocking=False,
        original_text=core.description,
    )
    rules.append(
        _rule(
            "core:stun-teammate-attack",
            core_source,
            f"核心被动：其他击破角色当前攻击力+{attack_value:.0f}",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=core_effects,
        )
    )
    rules.append(
        _rule(
            "core:dark-echo-crit",
            core_source,
            f"核心被动：暗渊回响期间暴击率+{dark_echo_crit_rate:.0%}、暴击伤害+{dark_echo_crit_damage:.0%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=dark_echo_effects,
            condition_ids=(HUGO_DARK_ECHO_ACTIVE,),
        )
    )
    rules.append(
        _rule(
            "core:daze-energy-and-stun-reset-source-only",
            core_source,
            "核心被动：失衡与能量部分",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(core_daze,),
        )
    )

    return build_definition(
        character_id=HUGO_ID,
        role=CharacterRole.ATTACK,
        element=Element.ICE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=tuple(conditions),
        parameters=(disorder_parameter, decision_remaining),
        diagnostics=direct_diagnostics,
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(HUGO_ID))


def _validate_raw(raw: NanokaRawRecord, config: HugoCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Hugo raw record and compile config IDs must match")
    if raw.name != "雨果" or raw.code_name != "Hugo":
        raise ValueError("unexpected Hugo identity")
    if raw.specialty != "强攻" or raw.element != "冰属性" or raw.rarity != 4:
        raise ValueError("unexpected Hugo role, element, or rank")
    if raw.faction != "反舌鸟" or raw.icon != "IconRole42":
        raise ValueError("unexpected Hugo faction or icon")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1291.json":
        raise ValueError("Hugo provenance must identify live Nanoka 3.2 character 1291")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Hugo source must include seven cores and six mindscapes")
    if raw.potential_details:
        raise ValueError("Hugo source has no Potential levels")
    if config.character_id != raw.character_id:
        raise ValueError("Hugo config and raw IDs must match")


__all__ = ["compile_hugo", "load_raw_record"]
