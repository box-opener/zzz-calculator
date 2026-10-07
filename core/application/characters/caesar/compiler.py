"""Compile Caesar's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

import re
from collections.abc import Mapping

from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
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
    EnemyStateFilter,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    GuaranteedCritEffect,
    MoveId,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
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
from ...moves import DamageEventTemplateRef, MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ParameterResolution, ScenarioCondition, ScenarioIntegerParameter
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import build_definition, compile_direct_moves, effective_skill_level, source_for
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import AttributeAnomalyDamageEventTemplate, DirectDamageEventTemplate, DisorderDamageEventTemplate
from .config import CaesarCompileConfig
from .reviewed import (
    ASSIST_STRIKE_MOVE_ID,
    BASIC_SHIELD_THROW_MOVE_ID,
    BASIC_SLASH_MOVE_ID,
    CAESAR_CINEMA1_RESISTANCE_DEBUFF_ACTIVE,
    CAESAR_CINEMA6_SELF_CRIT_BUFF_ACTIVE,
    CAESAR_EXTRA_ABILITY_DEBUFF_ACTIVE,
    CAESAR_ID,
    CAESAR_IMPACT_BUFF_ACTIVE,
    CAESAR_PHYSICAL_ANOMALY_RECORD_ID,
    CAESAR_REVIEWED_MAPPING,
    CAESAR_SHIELD_ACTIVE,
    CAESAR_SHIELD_ATTACK_BUFF_ACTIVE,
    CHAIN_ATTACK_MOVE_ID,
    DASH_ATTACK_MOVE_ID,
    DODGE_COUNTER_MOVE_ID,
    EX_COUNTERATTACK_MOVE_ID,
    EX_DEFENSIVE_COUNTER_MOVE_ID,
    EX_SHIELD_BASH_MOVE_ID,
    PHYSICAL_ANOMALY_MOVE_ID,
    PHYSICAL_DISORDER_MOVE_ID,
    PHYSICAL_DISORDER_REMAINING_SECONDS,
    QUICK_ASSIST_MOVE_ID,
    SPECIAL_SHIELD_CRASH_MOVE_ID,
    SPECIAL_THRUST_MOVE_ID,
    ULTIMATE_MOVE_ID,
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


def _source(key: str, kind: EffectSourceType, name: str, text: str) -> RuleSource:
    return source_for(CAESAR_ID, key, kind, name, text)


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
        rule_id=RuleItemId(f"rule:character:1071:{key}"),
        owner=CAESAR_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
    )


def _effect_rule(key: str, source: RuleSource, target: EffectTarget, *, condition=None, filters=()):
    return EffectRule(
        effect_id=EffectId(f"effect:character:1071:{key}"),
        source=source,
        owner=CAESAR_ID,
        target=target,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        condition=condition,
        filters=tuple(filters),
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    condition=None,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(key, source, target, condition=condition, filters=filters),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _note(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1071:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_physical_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1071:physical-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1071:physical-anomaly"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=CAESAR_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=CAESAR_ID,
        history_record_source=CAESAR_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1071:physical-anomaly"),
        character_id=CAESAR_ID,
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text="按静态单人100%积蓄的物理异常记录结算强击，倍率7.13，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1071:physical-anomaly"),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1071:physical-disorder",
        semantic_id=DamageEventSemanticId("event:character:1071:physical-disorder"),
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=CAESAR_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=CAESAR_ID,
        history_record_source=CAESAR_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1071:physical-disorder"),
        character_id=CAESAR_ID,
        move_id=PHYSICAL_DISORDER_MOVE_ID,
        display_name="紊乱：物理异常（剩余时间补偿）",
        original_text="物理紊乱基础倍率450%，每秒剩余时间补偿75%，按floor(t)计算。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1071:physical-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="物理异常紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining_seconds = ScenarioIntegerParameter(
        parameter_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
        label="物理异常剩余持续时间（秒）",
        original_text="静态物理异常按10秒；本次紊乱剩余时间由用户输入，不从战斗时序推断。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        remaining_seconds,
    )


def _cinema6_attack_entries(
    entries: tuple[MoveCalculationEntry, ...],
    templates: tuple[DirectDamageEventTemplate, ...],
    source: RuleSource,
) -> tuple[CalculationRuleItem, ...]:
    qualifying_keys = {
        "ex-super-strong-shield-bash",
        "ex-defensive-counter-shield-bash",
        "assist-strike-support-edge",
    }
    template_ids = tuple(
        EventTemplateId(str(entry.main_damage_event.template_id))
        for entry in entries
        if str(entry.entry_id).rsplit(":", 1)[-1] in qualifying_keys
    )
    if len(template_ids) != len(qualifying_keys):
        raise ValueError("Caesar C6 direct sources must resolve to three entries")
    source_text = source.raw_text or ""
    damage_bonus = _number(
        source_text,
        r"招式造成的伤害提升(?P<value>[\d.]+)%",
        "Caesar Cinema 6 damage bonus",
    ) / 100.0
    main_target_extra = _number(
        source_text,
        r"主要目标造成的伤害额外提升(?P<value>[\d.]+)%",
        "Caesar Cinema 6 main-target damage bonus",
    ) / 100.0
    event_filters = (
        DamageDealerFilter(CAESAR_ID),
        DamageTypeFilter(DamageType.DIRECT),
        AnyFilter(tuple(EventTemplateIdFilter(item) for item in template_ids)),
    )
    effects = (
        _modifier(
            "cinema6:direct-damage-bonus",
            source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            # The result contract settles one selected target, which is the
            # source's main target; retain both explicit additive terms.
            Resolved(damage_bonus + main_target_extra),
            target=EffectTarget.TEAM,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=event_filters,
        ),
        GuaranteedCritEffect(
            rule=_effect_rule(
                "cinema6:direct-guaranteed-crit",
                source,
                EffectTarget.TEAM,
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=event_filters,
            )
        ),
    )
    return (
        _rule(
            "cinema6:shield-bash-and-support-strike",
            source,
            "6影：超强力盾击/支援之锋伤害+50%，主要目标额外+50%，必定暴击",
            source.raw_text or "",
            RuleEligibility.ELIGIBLE,
            effects=effects,
        ),
    )


def compile_caesar(
    config: CaesarCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=CAESAR_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=CAESAR_REVIEWED_MAPPING,
        id_namespace="character:1071",
    )
    static_entries, static_templates, disorder_seconds = _static_physical_entries()

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    shield_attack = _number(
        core.description,
        r"攻击力提升(?P<value>[\d.]+)点",
        "Caesar Core shield-holder ATK",
    )
    c2_multiplier = 1.0
    if config.cinema_level >= 2:
        c2_multiplier = _number(
            raw_record.mindscapes[1].description,
            r"提升至原本的(?P<value>[\d.]+)%",
            "Caesar Cinema 2 shield attack-buff multiplier",
        ) / 100.0

    cinema1 = raw_record.mindscapes[0]
    c1_source = _source("cinema-1", EffectSourceType.CINEMA, cinema1.name, cinema1.description)
    c1_resistance_reduction = _number(
        cinema1.description,
        r"伤害抗性降低(?P<value>[\d.]+)%",
        "Caesar Cinema 1 resistance reduction",
    ) / 100.0
    cinema2 = raw_record.mindscapes[1]
    c2_source = _source("cinema-2", EffectSourceType.CINEMA, cinema2.name, cinema2.description)
    extra_bonus = _number(
        core.extra_ability_description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Caesar Additional Ability enemy vulnerability",
    ) / 100.0

    conditions = [
        _condition(
            CAESAR_SHIELD_ACTIVE,
            "荣光之盾当前存在",
            core.description,
        ),
        _condition(
            CAESAR_SHIELD_ATTACK_BUFF_ACTIVE,
            "当前操作角色持有荣光之盾攻击力增益（含盾消失后的5秒残余）",
            core.description,
        ),
        _condition(
            CAESAR_CINEMA1_RESISTANCE_DEBUFF_ACTIVE,
            "凯撒1影：当前目标处于荣光之盾范围内的全属性抗性降低状态",
            cinema1.description,
        ),
        _condition(
            CAESAR_EXTRA_ABILITY_DEBUFF_ACTIVE,
            "额外能力：当前目标受凯撒伤害易伤效果影响",
            core.extra_ability_description,
        ),
        _condition(
            CAESAR_IMPACT_BUFF_ACTIVE,
            "凯撒攻防转换：冲击力提升当前有效",
            raw_record.moves[[item.name for item in raw_record.moves].index("攻防转换")].description,
        ),
    ]
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:shield-holder-attack",
            core_source,
            f"核心被动：当前持盾操作角色攻击力+{shield_attack:g}",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(CAESAR_SHIELD_ATTACK_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:shield-holder-attack",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    Resolved(shield_attack),
                    target=EffectTarget.CURRENT_OPERATOR,
                ),
            ),
            diagnostics=(
                _note(
                    "core:shield-result-not-calculated",
                    "The shared Glory Shield value, absorbed damage, interruption resistance, and duration are not output. Its current holder's explicit ATK effect is applied to the current operator panel.",
                    core.description,
                ),
            ),
        ),
        _rule(
            "extra-ability:enemy-normal-vulnerability",
            extra_source,
            "额外能力：当前目标受到的全队伤害提升",
            core.extra_ability_description,
            (
                RuleEligibility.ELIGIBLE
                if config.additional_ability_eligible
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(CAESAR_EXTRA_ABILITY_DEBUFF_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:enemy-normal-vulnerability",
                    extra_source,
                    CalculationNode.ENEMY_NORMAL_VULNERABILITY,
                    Resolved(extra_bonus),
                    target=EffectTarget.ENEMY,
                ),
            ),
        ),
        _rule(
            "cinema1:enemy-resistance-reduction",
            c1_source,
            f"1影：当前目标全属性抗性降低{c1_resistance_reduction * 100:g}%",
            cinema1.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 1
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(CAESAR_CINEMA1_RESISTANCE_DEBUFF_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:enemy-resistance-reduction",
                    c1_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(c1_resistance_reduction),
                    target=EffectTarget.ENEMY,
                ),
            ),
        ),
    ]

    if config.cinema_level >= 2:
        c2_attack_source = _source(
            "cinema-2:shield-attack",
            EffectSourceType.CINEMA,
            cinema2.name,
            cinema2.description,
        )
        rules.append(
            _rule(
                "cinema2:shield-holder-attack-increase",
                c2_attack_source,
                f"2影：盾存在时持有者攻击力额外+{shield_attack * (c2_multiplier - 1.0):g}",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                condition_ids=(CAESAR_SHIELD_ACTIVE, CAESAR_SHIELD_ATTACK_BUFF_ACTIVE),
                effects=(
                    _modifier(
                        "cinema2:shield-holder-attack-increase",
                        c2_attack_source,
                        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                        Resolved(shield_attack * (c2_multiplier - 1.0)),
                        target=EffectTarget.CURRENT_OPERATOR,
                    ),
                ),
            )
        )

    c2_energy_note = _note(
        "cinema2:energy-efficiency-resource",
        "Cinema 2 increases Energy Gain Efficiency while Glory Shield exists; the current calculation result has no Energy resource field, so no regeneration or Energy value is fabricated.",
        cinema2.description,
    )
    if config.cinema_level >= 2:
        rules.append(
            _rule(
                "cinema2:energy-source-only",
                c2_source,
                "2影：能量获得效率（资源结果未提供）",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                condition_ids=(CAESAR_SHIELD_ACTIVE,),
                diagnostics=(c2_energy_note,),
            )
        )

    for level in (3, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(f"cinema-{level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级提升",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    cinema4 = raw_record.mindscapes[3]
    c4_source = _source("cinema-4", EffectSourceType.CINEMA, cinema4.name, cinema4.description)
    c4_note = _note(
        "cinema4:resource-results",
        "Cinema 4's Support Point restoration and Energy substitution use resources that the current result contract does not expose; no resource values or timing are fabricated.",
        cinema4.description,
    )
    rules.append(
        _rule(
            "cinema4:resource-source-only",
            c4_source,
            "4影：支援点数/能量替代（资源结果未提供）",
            cinema4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            diagnostics=(c4_note,),
        )
    )

    impact_move = next(item for item in raw_record.moves if item.name == "攻防转换")
    impact_formula = re.search(
        r"\{CAL:(?P<base>[\d.]+)\+AvatarSkillLevel\(1\)\*(?P<growth>[\d.]+),1,2\}%",
        _plain(impact_move.description),
    )
    if impact_formula is None:
        raise ValueError("Caesar's Impact-conversion source is missing its CAL formula")
    impact_percentage = (
        float(impact_formula.group("base"))
        + float(impact_formula.group("growth"))
        * effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    ) / 100.0
    impact_source = _source("special:impact-conversion", EffectSourceType.SPECIAL_MECHANISM, impact_move.name, impact_move.description)
    rules.append(
        _rule(
            "special:impact-conversion",
            impact_source,
            f"攻防转换：当前冲击力提升{impact_percentage * 100:g}%",
            impact_move.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(CAESAR_IMPACT_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "special:impact-conversion",
                    impact_source,
                    CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
                    Resolved(impact_percentage),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )

    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        c6_source = _source("cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description)
        conditions.append(
            _condition(
                CAESAR_CINEMA6_SELF_CRIT_BUFF_ACTIVE,
                "6影：凯撒当前暴击率/暴击伤害增益有效",
                cinema6.description,
            )
        )
        c6_move_source = _cinema6_attack_entries(direct_entries, direct_templates, c6_source)
        rules.extend(c6_move_source)
        crit_rate = _number(cinema6.description, r"暴击率提升(?P<value>[\d.]+)%", "Caesar Cinema 6 Crit Rate") / 100.0
        crit_damage = _number(cinema6.description, r"暴击伤害提升(?P<value>[\d.]+)%", "Caesar Cinema 6 Crit Damage") / 100.0
        c6_panel_rule = _rule(
            "cinema6:self-crit-panel-buff",
            c6_source,
            "6影：凯撒当前暴击率/暴击伤害增益",
            cinema6.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(CAESAR_CINEMA6_SELF_CRIT_BUFF_ACTIVE,),
            effects=(
                _modifier("cinema6:self-crit-rate", c6_source, CalculationNode.CHARACTER_CURRENT_CRIT_RATE, Resolved(crit_rate), target=EffectTarget.SELF),
                _modifier("cinema6:self-crit-damage", c6_source, CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE, Resolved(crit_damage), target=EffectTarget.SELF),
            ),
            diagnostics=(
                _note(
                    "cinema6:self-crit-timing",
                    "The selected Crit Rate/Crit Damage state is current; the 15-second duration and trigger timing are not replayed.",
                    cinema6.description,
                ),
            ),
        )
        rules.append(c6_panel_rule)

    daze_note = _note(
        "parry-daze-unavailable",
        "Raw Parry Support and Perfect-Guard Daze curves are preserved as source data. The current result has no Daze output, so they are not converted into Direct damage.",
        "招架支援：守御之盾的轻/重/连续招架失衡倍率；特殊技/强化特殊技中的精准格挡失衡倍率",
    )
    shield_note = _note(
        "shield-and-incoming-results",
        "The current calculator does not return shield capacity, damage absorption, interruption resistance, or incoming damage. Current holder attack and enemy debuff effects remain separately available.",
        core.description,
    )

    static_entries, static_templates, disorder_seconds = _static_physical_entries()
    return build_definition(
        character_id=CAESAR_ID,
        role=CharacterRole.DEFENSE,
        element=Element.PHYSICAL,
        source=core_source,
        entries=(*direct_entries, *static_entries),
        templates=(*direct_templates, *static_templates),
        rules=rules,
        conditions=conditions,
        parameters=(disorder_seconds,),
        diagnostics=(*direct_diagnostics, daze_note, shield_note),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(CAESAR_ID))


def _validate_raw_record(raw: NanokaRawRecord, config: CaesarCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "凯撒" or raw.code_name != "Caesar":
        raise ValueError("unexpected character identity in Caesar source")
    if raw.specialty != "防护" or raw.element != "物理" or raw.rarity != 4:
        raise ValueError("Caesar role, element, or rank changed from reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Caesar source must contain seven core levels and six cinemas")
    if raw.source_version != "3.2" or not raw.source_url.endswith("/character/1071.json"):
        raise ValueError("Caesar raw source provenance must identify Nanoka 3.2 character 1071")


def _condition(condition_id, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(CAESAR_ID, key, kind, label, text)


__all__ = ["compile_caesar", "load_raw_record"]
