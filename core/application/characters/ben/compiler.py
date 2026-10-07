"""Compile Ben's reviewed Nanoka 3.2 source into calculation contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
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
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)

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
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import AttributeAnomalyDamageEventTemplate, DisorderDamageEventTemplate
from .config import BenCompileConfig
from .reviewed import (
    BEN_C4_COUNTER_BONUS_ACTIVE,
    BEN_EX_FOLLOWUP_ACTIVE,
    BEN_FIRE_ANOMALY_MOVE_ID,
    BEN_FIRE_DISORDER_MOVE_ID,
    BEN_GUARD_COUNTER_SUCCESSFUL,
    BEN_ID,
    BEN_REVIEWED_MAPPING,
    BEN_SHIELD_ACTIVE,
    BEN_FIRE_ANOMALY_RECORD_ID,
)


_FIRE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:ben:fire-disorder-remaining-seconds"
)
def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(BEN_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1121:{key}"),
        owner=BEN_ID,
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
    target: EffectTarget = EffectTarget.TEAM,
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1121:{key}"),
            source=source,
            owner=BEN_ID,
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


def _static_fire_entries():
    record_id = AnomalyRecordId(BEN_FIRE_ANOMALY_RECORD_ID)
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1121:fire-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1121:fire-anomaly"),
        label="属性异常：灼烧（10秒，20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=BEN_ID,
        element=Element.FIRE,
        anomaly_triggerer=BEN_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=BEN_FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1121:fire-anomaly"),
        character_id=BEN_ID,
        move_id=BEN_FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（10秒，20跳）",
        original_text=(
            "按规范火属性异常固定倍率：每0.5秒造成异常效果强度的50%，10秒共20跳；"
            "静态单人按100%积蓄并使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1121:fire-anomaly-tick"),
                label="灼烧每跳50%（10秒20跳）",
                parameter_name="灼烧每跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1121:fire-disorder",
        semantic_id=DamageEventSemanticId("event:character:1121:fire-disorder"),
        label="紊乱：灼烧",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=BEN_ID,
        element=Element.FIRE,
        disorder_triggerer=BEN_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=BEN_FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1121:fire-disorder"),
        character_id=BEN_ID,
        move_id=BEN_FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧（剩余时间补偿）",
        original_text=(
            "按规范默认450%紊乱基础倍率 + floor(t/0.5)×50%灼烧剩余时间补偿；"
            "以整数秒输入0–10秒，默认10秒，不推断触发时间。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1121:fire-disorder"),
                label="450% + floor(t/0.5) × 50%",
                parameter_name="灼烧紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_FIRE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.0,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_FIRE_DISORDER_REMAINING_SECONDS,
        label="灼烧紊乱时目标剩余持续时间（秒）",
        original_text=(
            "规范补偿为floor(t/0.5)×50%；按整数秒独立选择0–10秒，默认10秒，"
            "不从触发时序推断。"
        ),
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def _event_filter(key: str) -> EventTemplateIdFilter:
    return EventTemplateIdFilter(EventTemplateId(f"template:character:1121:{key}:main"))


def _complete_entry(
    *,
    first: MoveCalculationEntry,
    second: MoveCalculationEntry,
    templates: list,
    entries: list,
    key: str,
    label: str,
    move_id,
    condition_ids=(),
) -> None:
    first_multiplier = first.multiplier_variants[0].multiplier
    second_multiplier = second.multiplier_variants[0].multiplier
    if not isinstance(first_multiplier, FixedMultiplier) or not isinstance(second_multiplier, FixedMultiplier):
        raise ValueError(f"Ben complete entry components are unresolved: {key}")
    if not isinstance(first_multiplier.value, Resolved) or not isinstance(second_multiplier.value, Resolved):
        raise ValueError(f"Ben complete entry components are unresolved: {key}")
    first_template = next(
        item for item in templates if item.ref.template_id == first.main_damage_event.template_id
    )
    new_ref = replace(
        first.main_damage_event,
        template_id=EventTemplateId(f"template:character:1121:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1121:{key}:main"),
        label=label,
    )
    entries.append(
        MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1121:{key}"),
            character_id=BEN_ID,
            move_id=move_id,
            display_name=label,
            original_text=(
                f"{first.original_text}\n{second.original_text}\n"
                "完整单次动作总倍率由来源曲线各一次相加，不推断额外次数。"
            ),
            skill_group=first.skill_group,
            damage_tags=first.damage_tags,
            multiplier_relation=MultiplierRelation.COMPLETE,
            multiplier_variants=(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(f"variant:character:1121:{key}"),
                    label="来源倍率相加",
                    parameter_name="完整动作总倍率",
                    multiplier=FixedMultiplier(
                        Resolved(first_multiplier.value.value + second_multiplier.value.value)
                    ),
                ),
            ),
            main_damage_event=new_ref,
            condition_ids=tuple(condition_ids),
        )
    )
    templates.append(replace(first_template, ref=new_ref, move_id=move_id))


def compile_ben(
    config: BenCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=BEN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=BEN_REVIEWED_MAPPING,
        id_namespace="character:1121",
    )
    entries = list(entries)
    templates = list(templates)
    diagnostics = list(direct_diagnostics)
    parameters = []

    entry_index = {str(item.entry_id).rsplit(":", 1)[-1]: item for item in entries}
    _complete_entry(
        first=entry_index["ex-special-main"],
        second=entry_index["ex-special-followup"],
        templates=templates,
        entries=entries,
        key="ex-special-complete-followup",
        label="强化特殊技：到期还拳（含追加强力打击）",
        move_id=MoveId("move:ben:ex-special-complete-followup"),
        condition_ids=(BEN_EX_FOLLOWUP_ACTIVE,),
    )
    _complete_entry(
        first=entry_index["ex-special-counter"],
        second=entry_index["ex-special-counter-followup"],
        templates=templates,
        entries=entries,
        key="ex-special-complete-successful-counter",
        label="强化特殊技：到期还拳（格挡反击与追击）",
        move_id=MoveId("move:ben:ex-special-complete-successful-counter"),
        condition_ids=(BEN_GUARD_COUNTER_SUCCESSFUL,),
    )
    static_entries, static_templates, disorder_remaining = _static_fire_entries()
    entries.extend(static_entries)
    templates.extend(static_templates)
    parameters.append(disorder_remaining)

    conditions = [
        _condition(
            BEN_GUARD_COUNTER_SUCCESSFUL,
            "本次特殊技/强化特殊技成功格挡并触发反击",
            "用户选择当前成功触发格挡反击的分支，不模拟敌人攻击时序。",
        ),
        _condition(
            BEN_EX_FOLLOWUP_ACTIVE,
            "本次强化特殊技已追加强力打击",
            next(move.description for move in raw_record.moves if move.name == "强化特殊技：到期还拳"),
        ),
        _condition(
            BEN_SHIELD_ACTIVE,
            "Ben核心被动提供的全队护盾当前有效",
            raw_record.core_levels[0].description,
        ),
    ]
    rules: list[CalculationRuleItem] = []
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    core_attack_ratio = _number(
        core.description,
        r"提升效果等同于自身初始防御力的(?P<value>[\d.]+)%",
        "Ben Core initial ATK per initial DEF",
    ) / 100.0
    core_attack_unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes=(
            f"Ben Core supplies a known {core_attack_ratio:.0%} Initial DEF-to-Initial ATK conversion, "
            "but its out-of-combat versus combat-layer placement is awaiting the user's clarification. "
            "Keep the selected Ben event's base value, mark the Ben-ATK-dependent result incomplete, "
            "and do not create a synthetic damage hit."
        ),
        original_text=core.description,
    )
    ben_direct_template_filters = AnyFilter(
        tuple(
            EventTemplateIdFilter(
                EventTemplateId(f"template:character:1121:{spec.entry_key}:main")
            )
            for spec in BEN_REVIEWED_MAPPING.moves
        )
        + tuple(
            EventTemplateIdFilter(
                EventTemplateId(f"template:character:1121:{key}:main")
            )
            for key in (
                "special-complete-successful-counter",
                "ex-special-complete-followup",
                "ex-special-complete-successful-counter",
            )
        )
    )
    core_attack_effects = (
        EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId("effect:character:1121:core:initial-defense-to-attack-direct"),
                source=core_source,
                owner=BEN_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(BEN_ID),
                    ben_direct_template_filters,
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                unresolved_template=core_attack_unresolved,
            ),
        ),
        EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId("effect:character:1121:core:initial-defense-to-attack-fire-anomaly"),
                source=core_source,
                owner=BEN_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    DamageDealerFilter(BEN_ID),
                    EventTemplateIdFilter(EventTemplateId("template:character:1121:fire-anomaly")),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                unresolved_template=core_attack_unresolved,
            ),
        ),
        EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId("effect:character:1121:core:initial-defense-to-attack-fire-disorder"),
                source=core_source,
                owner=BEN_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(
                    DamageTypeFilter(DamageType.DISORDER),
                    DamageDealerFilter(BEN_ID),
                    EventTemplateIdFilter(EventTemplateId("template:character:1121:fire-disorder")),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                unresolved_template=core_attack_unresolved,
            ),
        ),
    )
    rules.append(
        _rule(
            "core:initial-defense-to-attack",
            core_source,
            f"核心被动：初始防御力×{core_attack_ratio:.0%}转攻击力",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=core_attack_effects,
        )
    )

    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    extra_cr = _number(
        core.extra_ability_description,
        r"暴击率提升(?P<value>[\d.]+)%",
        "Ben Additional Ability Crit Rate",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:team-crit-rate-while-core-shielded",
            extra_source,
            f"额外能力：持有Ben核心护盾时全队暴击率+{extra_cr * 100:g}%",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            conditions=(BEN_SHIELD_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:team-crit-rate-while-core-shielded",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(extra_cr),
                ),
            ),
        )
    )

    cinema2 = raw_record.mindscapes[1]
    cinema2_source = _source("cinema-2", EffectSourceType.CINEMA, cinema2.name, cinema2.description)
    c2_ratio = _number(
        cinema2.description,
        r"额外造成本(?P<value>[\d.]+)%防御力的伤害",
        "Ben Cinema 2 DEF-scaled counter damage",
    ) / 100.0
    c2_unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            f"The known extra hit is {c2_ratio:.0%} of Ben's current DEF. "
            "Its child element/Crit/tag inheritance and whether the EX follow-up shares one C2 proc "
            "are not specified by a separate typed source event."
        ),
        original_text=cinema2.description,
    )
    c2_counter_keys = (
        "special-counter",
        "ex-special-counter",
        "ex-special-complete-successful-counter",
    )
    rules.append(
        _rule(
            "cinema2:counter-defense-extra-damage",
            cinema2_source,
            f"2影：成功格挡反击额外造成防御力×{c2_ratio:.0%}伤害",
            cinema2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId("effect:character:1121:cinema2:counter-defense-extra-damage"),
                        source=cinema2_source,
                        owner=BEN_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            DamageDealerFilter(BEN_ID),
                            AnyFilter(tuple(_event_filter(key) for key in c2_counter_keys)),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        unresolved_template=c2_unresolved,
                    ),
                ),
            ),
        )
    )

    c4 = raw_record.mindscapes[3]
    c4_source = _source("cinema-4", EffectSourceType.CINEMA, c4.name, c4.description)
    c4_bonus = _number(
        c4.description,
        r"反击造成的伤害提升(?P<value>[\d.]+)%",
        "Ben Cinema 4 follow-up counter damage bonus",
    ) / 100.0
    if config.cinema_level >= 4:
        conditions.append(
            _condition(
                BEN_C4_COUNTER_BONUS_ACTIVE,
                "Ben4影成功格挡后的反击伤害增益当前有效",
                c4.description,
            )
        )
        eligibility = RuleEligibility.ELIGIBLE
    else:
        eligibility = RuleEligibility.INELIGIBLE
    c4_counter_keys = (
        "special-counter",
        "ex-special-counter",
        "ex-special-counter-followup",
        "ex-special-complete-successful-counter",
    )
    rules.append(
        _rule(
            "cinema4:counter-damage",
            c4_source,
            f"4影：成功格挡后的反击伤害+{c4_bonus * 100:g}%",
            c4.description,
            eligibility,
            conditions=(BEN_C4_COUNTER_BONUS_ACTIVE,) if config.cinema_level >= 4 else (),
            effects=(
                _modifier(
                    "cinema4:counter-damage",
                    c4_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c4_bonus),
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(BEN_ID),
                        AnyFilter(tuple(_event_filter(key) for key in c4_counter_keys)),
                    ),
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                ),
            ) if config.cinema_level >= 4 else (),
        )
    )

    for level in (1, 3, 5, 6):
        mindscape = raw_record.mindscapes[level - 1]
        source = _source(
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        if level in {3, 5}:
            # Skill-level growth is already applied by effective_skill_level.
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    source,
                    f"{level}影：技能等级提升",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                )
            )
        else:
            rules.append(
                _rule(
                    f"cinema{level}:source-only",
                    source,
                    f"{level}影：当前计算不输出护盾／失衡值",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                )
            )

    return build_definition(
        character_id=BEN_ID,
        role=CharacterRole.DEFENSE,
        element=Element.FIRE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: BenCompileConfig) -> None:
    if raw.character_id != BEN_ID or raw.name != "本" or raw.code_name != "Ben":
        raise ValueError("unexpected identity in Ben raw record")
    if raw.specialty != "防护" or raw.element != "火属性" or raw.rarity != 3:
        raise ValueError("Ben raw role, element, or rank changed from reviewed source")
    if raw.faction != "白祇重工":
        raise ValueError("Ben raw faction changed from reviewed source")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1121.json":
        raise ValueError("Ben source provenance must identify live Nanoka 3.2 character 1121")
    if raw.potential_details:
        raise ValueError("Ben 3.2 source does not have a potential configuration")
    if not 1 <= config.core_level <= 7 or not 0 <= config.cinema_level <= 6:
        raise ValueError("Ben compile levels are outside source bounds")


__all__ = ["compile_ben"]
