"""Compile Nekomata's reviewed live Nanoka record into calculation contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import re
from collections.abc import Mapping

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CreatedByEffectFilter,
    DamageDealerFilter,
    DamageTag,
    DamageTagFilter,
    DamageSubtype,
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
    EnemyStateFilter,
    CurrentAttackValueSource,
    EventTemplateId,
    EventTemplateIdFilter,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    NotFilter,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
    StandardCritRule,
    SnapshotRule,
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
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import NekomataCompileConfig
from .reviewed import (
    BACK_HIT_ACTIVE,
    CINEMA4_CRIT_RATE_STACKS,
    CINEMA6_CRIT_DAMAGE_STACKS,
    CORE_DAMAGE_BUFF_ACTIVE,
    ENEMY_STUNNED_STATE_ID,
    EX_SPECIAL_MOVE_ID,
    EXTRA_ABILITY_DAMAGE_STACKS,
    NEKOMATA_ID,
    NEKOMATA_POTENTIAL_ONE_MOVES,
    NEKOMATA_REVIEWED_MAPPING,
    POTENTIAL_DODGE_COUNTER_MOVE_ID,
    POTENTIAL_POUNCE_ACTIVE,
    PHYSICAL_ANOMALY_MOVE_ID,
    PHYSICAL_ANOMALY_RECORD_ID,
    PHYSICAL_DISORDER_MOVE_ID,
    PHYSICAL_DISORDER_REMAINING_SECONDS,
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _one_number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain exactly one value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _rule(
    suffix: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1021:{suffix}"),
        owner=NEKOMATA_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        diagnostics=tuple(diagnostics),
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
            effect_id=EffectId(f"effect:character:1021:{suffix}"),
            source=source,
            owner=NEKOMATA_ID,
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


def _diagnostic(suffix: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1021:{suffix}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_physical_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1021:physical-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1021:physical-anomaly"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=NEKOMATA_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=NEKOMATA_ID,
        history_record_source=PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1021:physical-anomaly"),
        character_id=NEKOMATA_ID,
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text="静态单人100%积蓄记录按权威规范结算物理强击，倍率7.13，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1021:physical-anomaly"),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1021:physical-disorder",
        semantic_id=DamageEventSemanticId("event:character:1021:physical-disorder"),
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=NEKOMATA_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=NEKOMATA_ID,
        history_record_source=PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1021:physical-disorder"),
        character_id=NEKOMATA_ID,
        move_id=PHYSICAL_DISORDER_MOVE_ID,
        display_name="紊乱：物理异常",
        original_text="物理异常的紊乱倍率按规范为450% + floor(t)×7.5%。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1021:physical-disorder"),
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
    remaining_seconds = ScenarioIntegerParameter(
        parameter_id=PHYSICAL_DISORDER_REMAINING_SECONDS,
        label="物理异常剩余持续时间（秒）",
        original_text="按静态物理异常记录为10秒；本次紊乱剩余时间由用户输入，不从触发时机推断。",
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


def _potential_stun_repeat(
    *,
    key: str,
    source: RuleSource,
    parent_template: DirectDamageEventTemplate,
    multiplier,
    original_text: str,
) -> tuple[CalculationRuleItem, DirectDamageEventTemplate, DerivedDamageEventTemplateRef]:
    rule_id = RuleItemId(f"rule:character:1021:potential:{key}")
    effect_id = EffectId(f"effect:character:1021:potential:{key}")
    template_ref = replace(
        parent_template.ref,
        template_id=EventTemplateId(f"template:character:1021:potential:{key}"),
        semantic_id=DamageEventSemanticId(f"event:character:1021:potential:{key}"),
        label=f"潜能：失衡目标重复攻击（{parent_template.ref.label}）",
        source_rule_item_id=rule_id,
    )
    template = replace(parent_template, ref=template_ref)
    effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=source,
            owner=NEKOMATA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=(
                DamageDealerFilter(NEKOMATA_ID),
                DamageTypeFilter(DamageType.DIRECT),
                EventTemplateIdFilter(parent_template.ref.template_id),
                EnemyStateFilter(ENEMY_STUNNED_STATE_ID),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_ref.template_id,
            unique_per_source_event=True,
        ),
    )
    rule = _rule(
        f"potential:{key}",
        source,
        f"潜能：失衡目标重复攻击（{parent_template.ref.label}）",
        original_text,
        RuleEligibility.ELIGIBLE,
        effects=(effect,),
    )
    return (
        rule,
        template,
        DerivedDamageEventTemplateRef(
            template=template_ref,
            multiplier=multiplier,
            repeat_count=2,
        ),
    )


def _potential_pounce_mark(
    source: RuleSource,
    *,
    stun_repeat_effect_ids: tuple[EffectId, ...],
) -> tuple[CalculationRuleItem, DirectDamageEventTemplate, DerivedDamageEventTemplateRef]:
    rule_id = RuleItemId("rule:character:1021:potential:super-furry-mark")
    effect_id = EffectId("effect:character:1021:potential:super-furry-mark")
    template_ref = DamageEventTemplateRef(
        template_id="template:character:1021:potential:super-furry-mark",
        semantic_id=DamageEventSemanticId("event:character:1021:potential:super-furry-mark"),
        label="潜能：超凶爪印",
        damage_type=DamageType.DIRECT,
        element=Element.PHYSICAL,
        source_rule_item_id=rule_id,
    )
    template = DirectDamageEventTemplate(
        ref=template_ref,
        damage_dealer=NEKOMATA_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(NEKOMATA_ID),
        crit_rule=StandardCritRule(NEKOMATA_ID),
        move_id=None,
    )
    source_filter = (
        DamageDealerFilter(NEKOMATA_ID),
        DamageTypeFilter(DamageType.DIRECT),
        NotFilter(CreatedByEffectFilter(effect_id)),
        *(NotFilter(CreatedByEffectFilter(item)) for item in stun_repeat_effect_ids),
    )
    effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=effect_id,
            source=source,
            owner=NEKOMATA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=source_filter,
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_ref.template_id,
            unique_per_source_event=True,
        ),
    )
    rule = _rule(
        "potential:super-furry-mark",
        source,
        "潜能：肉球突袭时的超凶爪印",
        source.raw_text or "肉球突袭状态下，猫又自身攻击命中会触发超凶爪印",
        RuleEligibility.ELIGIBLE,
        conditions=(POTENTIAL_POUNCE_ACTIVE,),
        effects=(effect,),
    )
    return (
        rule,
        template,
        DerivedDamageEventTemplateRef(
            template=template_ref,
            multiplier=FixedMultiplier(Resolved(0.30)),
        ),
    )


def compile_nekomata(
    config: NekomataCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    reviewed_mapping = NEKOMATA_REVIEWED_MAPPING
    if config.potential_level > 0:
        reviewed_mapping = replace(
            NEKOMATA_REVIEWED_MAPPING,
            moves=(*NEKOMATA_REVIEWED_MAPPING.moves, *NEKOMATA_POTENTIAL_ONE_MOVES),
        )
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=NEKOMATA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="character:1021",
    )
    potential_rules: list[CalculationRuleItem] = []
    potential_templates: list[DirectDamageEventTemplate] = []
    potential_derived: list[DerivedDamageEventTemplateRef] = []
    potential_numeric_rule: CalculationRuleItem | None = None
    potential_source: RuleSource | None = None
    if config.potential_level > 0:
        selected_detail = next(
            item
            for item in raw_record.potential_details
            if item.level == config.potential_level
        )
        potential_source = source_for(
            NEKOMATA_ID,
            f"potential-{config.potential_level}",
            EffectSourceType.SPECIAL_MECHANISM,
            selected_detail.name or selected_detail.level_show_name,
            selected_detail.description or raw_record.core_levels[0].description,
        )
        entries_by_id = {str(item.entry_id): item for item in direct_entries}
        templates_by_id = {item.ref.template_id: item for item in direct_templates}
        raw_moves = {move.name: move for move in raw_record.moves}
        stun_repeat_effect_ids: list[EffectId] = []
        for key, entry_id, source_name in (
            (
                "basic-cat-claw-final-stun-repeat",
                "move-entry:character:1021:basic-cat-claw-5",
                "普通攻击：猫猫爪刺",
            ),
            (
                "basic-red-blade-stun-repeat",
                "move-entry:character:1021:basic-red-blade",
                "普通攻击：赤色之刃",
            ),
        ):
            entry = entries_by_id[entry_id]
            parent_template = templates_by_id[entry.main_damage_event.template_id]
            repeat_source = source_for(
                NEKOMATA_ID,
                f"potential-{config.potential_level}-{key}",
                EffectSourceType.SPECIAL_MECHANISM,
                source_name,
                raw_moves[source_name].description,
            )
            rule, template, derived = _potential_stun_repeat(
                key=key,
                source=repeat_source,
                parent_template=parent_template,
                multiplier=entry.multiplier_variants[0].multiplier,
                original_text=raw_moves[source_name].description,
            )
            potential_rules.append(rule)
            potential_templates.append(template)
            potential_derived.append(derived)
            stun_repeat_effect_ids.append(
                EffectId(f"effect:character:1021:potential:{key}")
            )

        mark_rule, mark_template, mark_derived = _potential_pounce_mark(
            potential_source,
            stun_repeat_effect_ids=tuple(stun_repeat_effect_ids),
        )
        potential_rules.append(mark_rule)
        potential_templates.append(mark_template)
        potential_derived.append(mark_derived)

        if config.potential_level >= 2:
            crit_damage_bonus = _one_number(
                selected_detail.description,
                r"暴击伤害提升(?P<value>[\d.]+)%",
                f"Nekomata potential {config.potential_level} Pounce Crit Damage",
            ) / 100.0
            potential_numeric_rule = _rule(
                "potential:pounce-crit-damage",
                potential_source,
                f"潜能：肉球突袭暴击伤害+{crit_damage_bonus * 100:g}%",
                selected_detail.description,
                RuleEligibility.ELIGIBLE,
                conditions=(POTENTIAL_POUNCE_ACTIVE,),
                effects=(
                    _modifier(
                        "potential:pounce-crit-damage",
                        potential_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                        Resolved(crit_damage_bonus),
                        target=EffectTarget.SELF,
                    ),
                ),
            )

    static_entries, static_templates, disorder_seconds = _static_physical_entries()
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        NEKOMATA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_bonus = _one_number(
        core.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Nekomata Core damage bonus",
    ) / 100.0

    extra_source = source_for(
        NEKOMATA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    extra_bonus = _one_number(
        core.extra_ability_description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Nekomata Additional Ability EX damage bonus",
    ) / 100.0

    conditions = [
        _condition(
            CORE_DAMAGE_BUFF_ACTIVE,
            "核心被动：闪避反击/快速支援后的伤害增益当前有效",
            core.description,
        ),
        _condition(
            BACK_HIT_ACTIVE,
            "本次物理攻击确认为背后命中",
            raw_record.mindscapes[0].description,
        ),
    ]
    if config.potential_level > 0:
        conditions.append(
            _condition(
                POTENTIAL_POUNCE_ACTIVE,
                "潜能：肉球突袭状态当前有效",
                core.description,
            )
        )
    parameters = (
        ScenarioIntegerParameter(
            parameter_id=EXTRA_ABILITY_DAMAGE_STACKS,
            label="猫步秀：当前待由强化特殊技消耗的增伤层数",
            original_text=core.extra_ability_description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=2,
        ),
        ScenarioIntegerParameter(
            parameter_id=CINEMA4_CRIT_RATE_STACKS,
            label="4影：当前暴击率增益层数",
            original_text=raw_record.mindscapes[3].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=2,
        ),
        ScenarioIntegerParameter(
            parameter_id=CINEMA6_CRIT_DAMAGE_STACKS,
            label="6影：当前暴击伤害增益层数",
            original_text=raw_record.mindscapes[5].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=3,
        ),
        disorder_seconds,
    )

    core_diagnostic = _diagnostic(
        "core-damage-duration",
        "The current Core damage state is an explicit 6-second-active selection; dodge-counter/Quick Assist trigger history and expiration are not replayed.",
        core.description,
    )
    extra_diagnostic = _diagnostic(
        "extra-ability-stacks",
        "The explicit 0–2 value is the currently available EX damage stack count. Teammate Assault trigger history and next-EX consumption are not replayed.",
        core.extra_ability_description,
    )
    c2_energy_diagnostic = _diagnostic(
        "cinema2-energy-efficiency-result",
        "Cinema 2's single-enemy/front-field Energy Gain Efficiency is preserved as a source-only RuleItem. The request has no Energy resource result, so it is not converted to Energy Regeneration.",
        raw_record.mindscapes[1].description,
    )
    c4_stack_diagnostic = _diagnostic(
        "cinema4-stack-timing",
        "The selected 0–2 current Crit Rate layers preserve the stack value. Individual 15-second expirations and EX trigger timing are not replayed.",
        raw_record.mindscapes[3].description,
    )
    c6_stack_diagnostic = _diagnostic(
        "cinema6-stack-timing",
        "The selected 0–3 current Crit Damage layers preserve the stack value. Encounter exit and enemy-defeat timing are not replayed.",
        raw_record.mindscapes[5].description,
    )
    daze_diagnostic = _diagnostic(
        "daze-result-unavailable",
        "Raw Support Parry Daze curves are retained in the source but this calculation request does not return a Daze result; they are not represented as damage multipliers.",
        "招架支援：应激防御的轻/重/连续招架失衡倍率",
    )

    rules: list[CalculationRuleItem] = []
    rules.append(
        _rule(
            "core:current-damage-buff",
            core_source,
            f"{core.name}·当前伤害增益",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(CORE_DAMAGE_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:current-damage-buff",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(core_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(DamageDealerFilter(NEKOMATA_ID),),
                ),
            ),
            diagnostics=(core_diagnostic,),
        )
    )

    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_move_filters = [
        DamageDealerFilter(NEKOMATA_ID),
        DamageTypeFilter(DamageType.DIRECT),
    ]
    if config.potential_level == 0:
        extra_move_filters.append(MoveIdFilter(EX_SPECIAL_MOVE_ID))
    else:
        extra_move_filters.append(
            AnyFilter(
                (
                    DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                    DamageTagFilter(DamageTag.DODGE_COUNTER),
                )
            )
        )
    rules.append(
        _rule(
            "extra-ability:ex-current-stacks",
            extra_source,
            (
                "潜能：猫步秀·强化特殊技/闪避反击当前增伤层数"
                if config.potential_level > 0
                else "额外能力：猫步秀·当前强化特殊技增伤层数"
            ),
            core.extra_ability_description,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:ex-current-stacks",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(EXTRA_ABILITY_DAMAGE_STACKS),
                        coefficient=Resolved(extra_bonus),
                        base=Resolved(0.0),
                        cap_max=Resolved(extra_bonus * 2),
                    ),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=tuple(extra_move_filters),
                ),
            ),
            diagnostics=(extra_diagnostic,),
        )
    )
    rules.extend(potential_rules)
    if potential_numeric_rule is not None:
        rules.append(potential_numeric_rule)

    for level, mindscape in enumerate(raw_record.mindscapes, start=1):
        source = source_for(
            NEKOMATA_ID,
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
            physical_ignore = _one_number(
                mindscape.description,
                r"无视目标(?P<value>[\d.]+)%物理伤害抗性",
                "Nekomata Cinema 1 Physical resistance ignore",
            ) / 100.0
            owner_condition = DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER)
            filters = (
                DamageDealerFilter(NEKOMATA_ID),
                DamageTypeFilter(DamageType.DIRECT),
                ElementFilter(Element.PHYSICAL),
            )
            rules.extend(
                (
                    _rule(
                        "cinema1:back-hit-physical-resistance-ignore",
                        source,
                        "1影：背后攻击物理抗性无视",
                        mindscape.description,
                        eligibility,
                        conditions=(BACK_HIT_ACTIVE,),
                        effects=(
                            _modifier(
                                "cinema1:back-hit-physical-resistance-ignore",
                                source,
                                CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                                Resolved(physical_ignore),
                                target=EffectTarget.TEAM,
                                condition=owner_condition,
                                filters=filters + (NotFilter(EnemyStateFilter(ENEMY_STUNNED_STATE_ID)),),
                            ),
                        ),
                    ),
                    _rule(
                        "cinema1:stunned-target-physical-resistance-ignore",
                        source,
                        "1影：失衡目标视为背后攻击",
                        mindscape.description,
                        eligibility,
                        effects=(
                            _modifier(
                                "cinema1:stunned-target-physical-resistance-ignore",
                                source,
                                CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                                Resolved(physical_ignore),
                                target=EffectTarget.TEAM,
                                condition=owner_condition,
                                filters=filters + (EnemyStateFilter(ENEMY_STUNNED_STATE_ID),),
                            ),
                        ),
                    ),
                )
            )
        elif level == 2:
            rules.append(
                _rule(
                    "cinema2:energy-gain-efficiency-source-only",
                    source,
                    "2影：单敌前场能量获得效率",
                    mindscape.description,
                    eligibility,
                    diagnostics=(c2_energy_diagnostic,),
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
            crit_per_stack = _one_number(
                mindscape.description,
                r"暴击率提升(?P<value>[\d.]+)%",
                "Nekomata Cinema 4 Crit Rate per stack",
            ) / 100.0
            rules.append(
                _rule(
                    "cinema4:current-crit-rate-stacks",
                    source,
                    "4影：当前暴击率层数",
                    mindscape.description,
                    eligibility,
                    effects=(
                        _modifier(
                            "cinema4:current-crit-rate-stacks",
                            source,
                            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                            ScenarioParameterDerivedValue(
                                parameter_id=str(CINEMA4_CRIT_RATE_STACKS),
                                coefficient=Resolved(crit_per_stack),
                                base=Resolved(0.0),
                                cap_max=Resolved(crit_per_stack * 2),
                            ),
                            target=EffectTarget.SELF,
                        ),
                    ),
                    diagnostics=(c4_stack_diagnostic,),
                )
            )
        elif level == 6:
            crit_damage_per_stack = _one_number(
                mindscape.description,
                r"暴击伤害提升(?P<value>[\d.]+)%",
                "Nekomata Cinema 6 Crit Damage per stack",
            ) / 100.0
            rules.append(
                _rule(
                    "cinema6:current-crit-damage-stacks",
                    source,
                    "6影：当前暴击伤害层数",
                    mindscape.description,
                    eligibility,
                    effects=(
                        _modifier(
                            "cinema6:current-crit-damage-stacks",
                            source,
                            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                            ScenarioParameterDerivedValue(
                                parameter_id=str(CINEMA6_CRIT_DAMAGE_STACKS),
                                coefficient=Resolved(crit_damage_per_stack),
                                base=Resolved(0.0),
                                cap_max=Resolved(crit_damage_per_stack * 3),
                            ),
                            target=EffectTarget.SELF,
                        ),
                    ),
                    diagnostics=(c6_stack_diagnostic,),
                )
            )

    daze_diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1021:daze-result"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=(
            "Nanoka's three Support Parry Daze curves are retained in raw, but the current request has no Daze result and no Parry damage curve; they are not turned into fake Direct damage."
        ),
        blocking=False,
        original_text="招架支援：应激防御的轻/重/连续招架失衡倍率",
    )
    return build_definition(
        character_id=NEKOMATA_ID,
        role=CharacterRole.ATTACK,
        element=Element.PHYSICAL,
        source=core_source,
        entries=(*direct_entries, *static_entries),
        templates=(*direct_templates, *static_templates, *potential_templates),
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        independent_derived_damage_events=potential_derived,
        diagnostics=(*direct_diagnostics, daze_diagnostic),
    )


def _is_base_potential(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, (list, tuple)):
        return False
    return not value or 0 in value


def _potential_level_view(
    data: Mapping[str, object],
    potential_level: int,
) -> dict[str, object]:
    """Select the raw 0 or potential-1+ variant without changing the fixture."""

    if not 0 <= potential_level <= 6:
        raise ValueError("potential_level must be between 0 and 6")
    selected_potential_id: int | None = None
    if potential_level > 0:
        details = data.get("potential_detail")
        if not isinstance(details, Mapping):
            raise ValueError("Nekomata raw source is missing potential_detail")
        detail = next(
            (
                item
                for item in details.values()
                if isinstance(item, Mapping) and item.get("level") == potential_level
            ),
            None,
        )
        if detail is None or not isinstance(detail.get("id"), int):
            raise ValueError(
                f"Nekomata raw source is missing potential level {potential_level}"
            )
        selected_potential_id = int(detail["id"])

    def selected(value: object) -> bool:
        if potential_level == 0:
            return _is_base_potential(value)
        if _is_base_potential(value):
            return True
        return (
            selected_potential_id is not None
            and isinstance(value, (list, tuple))
            and selected_potential_id in value
        )

    def selected_passive(value: object) -> bool:
        if potential_level == 0:
            return _is_base_potential(value)
        if value is None:
            return True
        return (
            selected_potential_id is not None
            and isinstance(value, (list, tuple))
            and selected_potential_id in value
        )

    view = deepcopy(dict(data))
    skill_root = view.get("skill")
    if isinstance(skill_root, dict):
        for section_data in skill_root.values():
            if not isinstance(section_data, dict):
                continue
            descriptions = section_data.get("description")
            if isinstance(descriptions, list):
                section_data["description"] = [
                    item
                    for item in descriptions
                    if isinstance(item, dict) and selected(item.get("potential"))
                ]
    passive = view.get("passive")
    if isinstance(passive, dict) and isinstance(passive.get("level"), dict):
        passive["level"] = {
            key: item
            for key, item in passive["level"].items()
            if isinstance(item, dict) and selected_passive(item.get("potential"))
        }
    return view


def load_raw_record(
    data: Mapping[str, object], *, potential_level: int = 0
) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_level_view(data, potential_level),
        expected_character_id=str(NEKOMATA_ID),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: NekomataCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "猫又" or raw.code_name != "Nekomata":
        raise ValueError("unexpected character identity in raw Nekomata record")
    if raw.specialty != "强攻" or raw.element != "物理":
        raise ValueError("Nekomata raw role or element does not match reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Nekomata compile view must contain seven cores and six cinemas")
    expected_core_source = "1021501" if config.potential_level == 0 else "1021508"
    if raw.core_levels[0].source_id != expected_core_source:
        raise ValueError(
            "Nekomata raw potential view does not match the selected compile config"
        )
    if config.potential_level > 0 and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError("Nekomata raw source is missing selected potential detail")


__all__ = ["compile_nekomata", "load_raw_record"]
