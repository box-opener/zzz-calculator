"""Compile Nicole's reviewed live Nanoka 3.2 record."""

from __future__ import annotations

from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
    DamageTagFilter,
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
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
    SnapshotRule,
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
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import NicoleCompileConfig
from .reviewed import (
    BASIC_RABBIT_COMBO_MOVE_ID,
    CHAIN_EXPENSIVE_ETHER_BOMB_MOVE_ID,
    CINEMA6_TARGET_CRIT_ACTIVE,
    CORE_DEFENSE_DOWN_ACTIVE,
    CHAIN_ENERGY_FIELD_HIT_OCCURRED,
    DASH_SURPRISE_BOX_MOVE_ID,
    DODGE_COUNTER_PINNING_SHOT_MOVE_ID,
    ENHANCED_AMMO_ACTIVE,
    ETHER_ANOMALY_MOVE_ID,
    ETHER_ANOMALY_RECORD_ID,
    ETHER_DISORDER_MOVE_ID,
    EX_CHARGED_HIT_OCCURRED,
    EX_ENERGY_FIELD_HIT_OCCURRED,
    EX_SPECIAL_CANDY_BULLET_MOVE_ID,
    NICOLE_ID,
    NICOLE_REVIEWED_MAPPING,
    QUICK_ASSIST_EMERGENCY_SHELLING_MOVE_ID,
    SPECIAL_CANDY_BULLET_MOVE_ID,
    SUPPORT_FOLLOWUP_TAKE_ADVANTAGE_MOVE_ID,
    ULTIMATE_ENERGY_FIELD_HIT_OCCURRED,
    ULTIMATE_CUSTOM_ETHER_GRENADE_MOVE_ID,
)


CINEMA6_CRIT_STACKS = "parameter:nicole:cinema6-target-crit-stacks"
ETHER_DISORDER_REMAINING_SECONDS = "parameter:nicole:ether-disorder-remaining-seconds"

_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_DASH = frozenset({DamageTag.DASH_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})


def _plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _one_number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one reviewed value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str, value: bool = False):
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    suffix: str,
    source: RuleSource,
    label: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    conditions=(),
    effects=(),
    diagnostics=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1031:{suffix}"),
        owner=NICOLE_ID,
        source=source,
        display_name=label,
        original_text=original_text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        effects=tuple(effects),
        diagnostics=tuple(diagnostics),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
    )


def _modifier(
    suffix: str,
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
            effect_id=EffectId(f"effect:character:1031:{suffix}"),
            source=source,
            owner=NICOLE_ID,
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


def _diagnostic(
    suffix: str,
    message: str,
    original_text: str,
    *,
    blocking: bool = False,
    kind: DiagnosticKind | None = None,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"{suffix}"),
        kind=kind or (DiagnosticKind.AMBIGUOUS_SEMANTICS if blocking else DiagnosticKind.UNSUPPORTED_CALCULATOR),
        message=message,
        blocking=blocking,
        original_text=original_text,
    )


def _ether_static_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1031:ether-corrosion",
        semantic_id=DamageEventSemanticId("event:character:1031:ether-corrosion"),
        label="属性异常：侵蚀（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ETHER,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=NICOLE_ID,
        element=Element.ETHER,
        anomaly_triggerer=NICOLE_ID,
        history_record_source=ETHER_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ETHER_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1031:ether-corrosion"),
        character_id=NICOLE_ID,
        move_id=ETHER_ANOMALY_MOVE_ID,
        display_name="属性异常：侵蚀（10秒满异常）",
        original_text="静态单人100%积蓄记录按规范结算侵蚀：单跳62.5%，10秒共20跳，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1031:ether-corrosion"),
                label="每跳侵蚀倍率（10秒20跳）",
                parameter_name="侵蚀单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.625)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1031:ether-corrosion-disorder",
        semantic_id=DamageEventSemanticId("event:character:1031:ether-corrosion-disorder"),
        label="紊乱：以太侵蚀",
        damage_type=DamageType.DISORDER,
        element=Element.ETHER,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=NICOLE_ID,
        element=Element.ETHER,
        disorder_triggerer=NICOLE_ID,
        history_record_source=ETHER_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ETHER_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1031:ether-corrosion-disorder"),
        character_id=NICOLE_ID,
        move_id=ETHER_DISORDER_MOVE_ID,
        display_name="紊乱：以太侵蚀",
        original_text="按规范以太紊乱倍率450% + floor(t)×125%；剩余持续时间由用户输入。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1031:ether-corrosion-disorder"),
                label="450% + floor(t) × 125%",
                parameter_name="以太紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=ETHER_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.25,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    disorder_seconds = ScenarioIntegerParameter(
        parameter_id=ETHER_DISORDER_REMAINING_SECONDS,
        label="以太异常剩余持续时间（秒）",
        original_text="按10秒静态异常记录设最大默认剩余时间；本次紊乱剩余时间由用户输入。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        disorder_seconds,
    )


def _unresolved_extra_damage_effect(
    *,
    effect_key: str,
    source: RuleSource,
    parent_template_id: EventTemplateId,
    source_move_name: str,
    parameter_name: str,
    source_skill_id: str,
    raw_moves,
    skill_level: int,
    scope_label: str,
) -> EventCreationEffect:
    raw_move = raw_moves[source_move_name]
    parameter = next(item for item in raw_move.parameters if item.name == parameter_name)
    source_rate = parameter.value_for_level(skill_level, source_skill_id)
    if source_rate is None:
        raise ValueError(
            f"Nicole raw branch curve is missing: {source_move_name}:{parameter_name}:{source_skill_id}"
        )
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes=(
            f"The raw {parameter_name} curve is {source_rate:g}% at effective skill level {skill_level}. "
            f"The source text identifies the {scope_label}, but does not establish whether that coefficient "
            "is one damage event or the complete multi-hit total, nor how many hit events occur. No total is chosen."
        ),
        original_text=raw_move.description,
        candidates=(
            "The raw curve is the complete total for the selected branch",
            "The raw curve applies separately to multiple field/charge damage events",
        ),
    )
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1031:{effect_key}"),
            source=source,
            owner=NICOLE_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=(
                DamageDealerFilter(NICOLE_ID),
                DamageTypeFilter(DamageType.DIRECT),
                EventTemplateIdFilter(parent_template_id),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=unresolved,
        ),
    )


def compile_nicole(
    config: NicoleCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != NICOLE_ID:
        raise ValueError("Nicole compiler requires character:1031 raw data")
    if raw_record.code_name != "Nicole" or raw_record.name != "妮可":
        raise ValueError("Nicole raw record identity is invalid")
    if raw_record.specialty != "支援" or raw_record.element != "以太":
        raise ValueError("Nicole raw role or element does not match reviewed source")
    if raw_record.special_element is not None:
        raise ValueError("Nicole raw source must not declare a special element")
    if len(raw_record.core_levels) != 7 or len(raw_record.mindscapes) != 6:
        raise ValueError("Nicole raw source must contain seven cores and six cinemas")

    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=NICOLE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=NICOLE_REVIEWED_MAPPING,
        id_namespace="character:1031",
    )
    enhanced_ammo_description = next(
        move.description
        for move in raw_record.moves
        if move.name == "普通攻击：为所欲为"
    )
    direct_entries = tuple(
        replace(entry, original_text=enhanced_ammo_description)
        if str(entry.entry_id)
        == "move-entry:character:1031:dash-surprise-box-front-enhanced"
        else entry
        for entry in direct_entries
    )
    anomaly_entries, anomaly_templates, disorder_seconds = _ether_static_entries()
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        NICOLE_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    defense_reduction = _one_number(
        core.description,
        r"目标的防御力降低(?P<value>[\d.]+)%",
        "Nicole Core defense reduction",
    ) / 100.0
    extra_source = source_for(
        NICOLE_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    extra_ether_bonus = _one_number(
        core.extra_ability_description,
        r"以太伤害额外提升(?P<value>[\d.]+)%",
        "Nicole Additional Ability target Ether damage bonus",
    ) / 100.0
    raw_moves = raw_move_index(raw_record)
    ex_raw_move = raw_moves["强化特殊技：夹心糖衣炮弹"]
    chain_raw_move = raw_moves["连携技：高价以太爆弹"]
    ultimate_raw_move = raw_moves["终结技：特制以太榴弹"]

    conditions = (
        _condition(
            ENHANCED_AMMO_ACTIVE,
            "本次普攻/前闪使用的弹药已强化",
            core.description,
        ),
        _condition(
            CORE_DEFENSE_DOWN_ACTIVE,
            "妮可的核心被动减防当前对目标有效",
            core.description,
        ),
        _condition(
            EX_CHARGED_HIT_OCCURRED,
            "本次强化特殊技的额外蓄力伤害分支已触发",
            ex_raw_move.description,
        ),
        _condition(
            EX_ENERGY_FIELD_HIT_OCCURRED,
            "本次强化特殊技的能量场对目标造成伤害",
            ex_raw_move.description,
        ),
        _condition(
            CHAIN_ENERGY_FIELD_HIT_OCCURRED,
            "本次连携技的能量场对目标造成伤害",
            chain_raw_move.description,
        ),
        _condition(
            ULTIMATE_ENERGY_FIELD_HIT_OCCURRED,
            "本次终结技的能量场对目标造成伤害",
            ultimate_raw_move.description,
        ),
        _condition(
            CINEMA6_TARGET_CRIT_ACTIVE,
            "6影：目标能量场暴击率增益当前有效",
            raw_record.mindscapes[5].description,
        ),
    )
    cinema6_stacks = ScenarioIntegerParameter(
        parameter_id=CINEMA6_CRIT_STACKS,
        label="6影：当前目标暴击率增益层数",
        original_text=raw_record.mindscapes[5].description,
        resolution=ParameterResolution.USER_SELECTED,
        value=0,
        minimum=0,
        maximum=10,
    )

    core_state_diagnostic = _diagnostic(
        "unsupported:character:1031:core:trigger-and-duration",
        "The explicit Core Defense Down flag is the current 3.5-second target debuff. Energy-field/enhanced-bullet hit order and its expiration are not replayed.",
        core.description,
    )
    extra_diagnostic = _diagnostic(
        "unsupported:character:1031:extra-ability:duration",
        "The Additional Ability reuses the current Core target-debuff state. Its shared 3.5-second refresh timing is not replayed.",
        core.extra_ability_description,
    )
    c2_resource_diagnostic = _diagnostic(
        "unsupported:character:1031:cinema2:energy-result",
        "Cinema 2's 5-point Energy restore and 15-second internal cooldown remain source-only; the calculation request has no Energy resource result and does not convert this to Energy Regeneration.",
        raw_record.mindscapes[1].description,
    )
    c4_field_diagnostic = _diagnostic(
        "unsupported:character:1031:cinema4:field-size-result",
        "Cinema 4's 3-meter Energy Field diameter increase is preserved in the raw source but the request has no area/range result.",
        raw_record.mindscapes[3].description,
    )
    c6_duration_diagnostic = _diagnostic(
        "unsupported:character:1031:cinema6:stack-duration",
        "The explicit 0–10 layers are the current target-specific Crit Rate state. Per-hit layer timing and individual 12-second expirations are not replayed.",
        raw_record.mindscapes[5].description,
    )
    resource_diagnostic = _diagnostic(
        "unsupported:character:1031:ultimate:energy-results",
        "Ultimate's 10-point party Energy restore and 20-point next-in combatant restore are preserved as source text; the current request has no Energy result or ordered switch-in identity.",
        ultimate_raw_move.description,
    )
    daze_diagnostic = _diagnostic(
        "unsupported:character:1031:daze-result",
        "Nicole's Support Parry Daze curves remain in raw; this calculation request has no Daze result and no Parry damage curve.",
        "招架支援：狡兔出手！的轻/重/连续招架失衡倍率",
    )

    rules: list[CalculationRuleItem] = []
    rules.append(
        _rule(
            "core:target-defense-down",
            core_source,
            "核心被动：目标当前防御降低",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(CORE_DEFENSE_DOWN_ACTIVE,),
            effects=(
                _modifier(
                    "core:target-defense-down",
                    core_source,
                    CalculationNode.ENEMY_DEFENSE_REDUCTION,
                    Resolved(defense_reduction),
                    target=EffectTarget.ENEMY,
                ),
            ),
            diagnostics=(core_state_diagnostic,),
        )
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "extra-ability:target-ether-damage",
            extra_source,
            "额外能力：核心减益生效时目标受到的以太伤害提升",
            core.extra_ability_description,
            extra_eligibility,
            conditions=(CORE_DEFENSE_DOWN_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:target-ether-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(extra_ether_bonus),
                    target=EffectTarget.TEAM,
                    filters=(ElementFilter(Element.ETHER),),
                ),
            ),
            diagnostics=(extra_diagnostic,),
        )
    )

    for level, mindscape in enumerate(raw_record.mindscapes, start=1):
        source = source_for(
            NICOLE_ID,
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        eligibility = (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= level
            else RuleEligibility.INELIGIBLE
        )
        if level == 1:
            percent = _one_number(
                mindscape.description,
                r"累积的属性异常积蓄值提升(?P<value>[\d.]+)%",
                "Nicole Cinema 1 EX Buildup Efficiency",
            ) / 100.0
            rules.append(
                _rule(
                    "cinema1:ex-special-damage-and-buildup",
                    source,
                    "1影：强化特殊技伤害和异常积蓄提升",
                    mindscape.description,
                    eligibility,
                    effects=(
                        _modifier(
                            "cinema1:ex-special-damage",
                            source,
                            CalculationNode.DAMAGE_NORMAL_BONUS,
                            Resolved(percent),
                            target=EffectTarget.TEAM,
                            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                            filters=(DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),),
                        ),
                        _modifier(
                            "cinema1:ex-special-buildup-efficiency",
                            source,
                            CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                            Resolved(percent),
                            target=EffectTarget.TEAM,
                            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                            filters=(DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),),
                        ),
                    ),
                )
            )
        elif level == 2:
            rules.append(
                _rule(
                    "cinema2:core-debuff-energy-source-only",
                    source,
                    "2影：核心减益命中后的能量回复",
                    mindscape.description,
                    eligibility,
                    conditions=(CORE_DEFENSE_DOWN_ACTIVE,),
                    diagnostics=(c2_resource_diagnostic,),
                )
            )
        elif level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    source,
                    f"{level}影：{mindscape.name}·技能等级",
                    mindscape.description,
                    eligibility,
                )
            )
        elif level == 4:
            rules.append(
                _rule(
                    "cinema4:field-size-source-only",
                    source,
                    "4影：能量场范围提升",
                    mindscape.description,
                    eligibility,
                    diagnostics=(c4_field_diagnostic,),
                )
            )
        elif level == 6:
            crit_per_stack = _one_number(
                mindscape.description,
                r"暴击率提升(?P<value>[\d.]+)%",
                "Nicole Cinema 6 target Crit Rate per stack",
            ) / 100.0
            rules.append(
                _rule(
                    "cinema6:target-crit-rate-stacks",
                    source,
                    "6影：当前目标暴击率增益层数",
                    mindscape.description,
                    eligibility,
                    conditions=(CINEMA6_TARGET_CRIT_ACTIVE,),
                    effects=(
                        _modifier(
                            "cinema6:target-crit-rate-stacks",
                            source,
                            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                            ScenarioParameterDerivedValue(
                                parameter_id=CINEMA6_CRIT_STACKS,
                                coefficient=Resolved(crit_per_stack),
                                base=Resolved(0.0),
                                cap_max=Resolved(crit_per_stack * 10),
                            ),
                            target=EffectTarget.ENEMY,
                            filters=(
                                AnyFilter(
                                    (
                                        DamageTypeFilter(DamageType.DIRECT),
                                        DamageTypeFilter(DamageType.PENETRATION),
                                    )
                                ),
                            ),
                        ),
                    ),
                    diagnostics=(c6_duration_diagnostic,),
                )
            )

    ultimate_energy_source = source_for(
        NICOLE_ID,
        "ultimate-energy-restore",
        EffectSourceType.SKILL,
        "终结技：特制以太榴弹",
        ultimate_raw_move.description,
    )
    rules.append(
        _rule(
            "ultimate:energy-restore-source-only",
            ultimate_energy_source,
            "终结技：队伍能量回复",
            ultimate_energy_source.raw_text or "妮可终结技能量回复",
            RuleEligibility.ELIGIBLE,
            diagnostics=(resource_diagnostic,),
        )
    )

    ex_charge_source = source_for(
        NICOLE_ID,
        "ex-special-charge-damage",
        EffectSourceType.SKILL,
        "强化特殊技：蓄力额外伤害",
        ex_raw_move.description,
    )
    ex_cannon_template = EventTemplateId(
        "template:character:1031:ex-special-candy-bullet-shelling:main"
    )
    rules.append(
        _rule(
            "ex-special:charged-damage-unresolved",
            ex_charge_source,
            "强化特殊技：蓄力额外伤害（总伤害未定）",
            ex_raw_move.description,
            RuleEligibility.ELIGIBLE,
            conditions=(EX_CHARGED_HIT_OCCURRED,),
            effects=(
                _unresolved_extra_damage_effect(
                    effect_key="ex-special:charged-damage-unresolved",
                    source=ex_charge_source,
                    parent_template_id=ex_cannon_template,
                    source_move_name=ex_raw_move.name,
                    parameter_name="蓄力伤害倍率",
                    source_skill_id="1031103",
                    raw_moves=raw_moves,
                    skill_level=effective_skill_level(config, SkillGroup.SPECIAL_ATTACK),
                    scope_label="EX Special charged-damage branch",
                ),
            ),
        )
    )

    energy_field_branches = (
        (
            "ex-special:energy-field-damage-unresolved",
            EX_ENERGY_FIELD_HIT_OCCURRED,
            ex_raw_move,
            "1031106",
            "强化特殊技：夹心糖衣炮弹（炮击）",
            "template:character:1031:ex-special-candy-bullet-shelling:main",
            SkillGroup.SPECIAL_ATTACK,
            "EX Special Energy Field",
        ),
        (
            "chain:energy-field-damage-unresolved",
            CHAIN_ENERGY_FIELD_HIT_OCCURRED,
            chain_raw_move,
            "1031303",
            "连携技：高价以太爆弹（炮击）",
            "template:character:1031:chain-expensive-ether-bomb-shelling:main",
            SkillGroup.CHAIN_ATTACK,
            "Chain Attack Energy Field",
        ),
        (
            "ultimate:energy-field-damage-unresolved",
            ULTIMATE_ENERGY_FIELD_HIT_OCCURRED,
            ultimate_raw_move,
            "1031305",
            "终结技：特制以太榴弹（炮击）",
            "template:character:1031:ultimate-custom-ether-grenade-shelling:main",
            SkillGroup.ULTIMATE,
            "Ultimate Energy Field",
        ),
    )
    for suffix, condition_id, source_move, source_skill_id, label, parent_template_id, group, scope in energy_field_branches:
        field_source = source_for(
            NICOLE_ID,
            suffix.replace(":", "-"),
            EffectSourceType.SKILL,
            label,
            source_move.description,
        )
        rules.append(
            _rule(
                suffix,
                field_source,
                f"{label}（伤害次数/倍率单位未定）",
                source_move.description,
                RuleEligibility.ELIGIBLE,
                conditions=(condition_id,),
                effects=(
                    _unresolved_extra_damage_effect(
                        effect_key=suffix,
                        source=field_source,
                        parent_template_id=EventTemplateId(parent_template_id),
                        source_move_name=source_move.name,
                        parameter_name="能量场伤害倍率",
                        source_skill_id=source_skill_id,
                        raw_moves=raw_moves,
                        skill_level=effective_skill_level(config, group),
                        scope_label=scope,
                    ),
                ),
            )
        )

    daze_diagnostic = _diagnostic(
        "unsupported:character:1031:daze-result",
        "Nicole's Support Parry Daze curves remain in raw; this calculation request has no Daze result and no Parry damage curve.",
        "招架支援：狡兔出手！的轻/重/连续招架失衡倍率",
    )
    return build_definition(
        character_id=NICOLE_ID,
        role=CharacterRole.SUPPORT,
        element=Element.ETHER,
        source=core_source,
        entries=(*direct_entries, *anomaly_entries),
        templates=(*direct_templates, *anomaly_templates),
        rules=rules,
        conditions=conditions,
        parameters=(cinema6_stacks, disorder_seconds),
        diagnostics=(*direct_diagnostics, daze_diagnostic),
    )


__all__ = ["compile_nicole", "load_raw_record"]


def load_raw_record(data) -> NanokaRawRecord:
    raw = load_nanoka_raw_record(data, expected_character_id=str(NICOLE_ID))
    if raw.special_element is not None:
        raise ValueError("Nicole raw source must not declare a special element")
    return raw
