"""Compile Pulchra's reviewed Nanoka 3.2 moves and explicit state effects."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from core.types import (
    AllCondition,
    AnyCondition,
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageTag,
    DamageTagFilter,
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
    NotCondition,
    NotFilter,
    Resolved,
    RuleSource,
    RuleStackCondition,
    ScenarioParameterRangeCondition,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import DamageEventSemanticId, DiagnosticId, MoveEntryId, RuleItemId
from ...moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
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
    raw_multiplier,
    raw_move_index,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import DirectDamageEventTemplate
from .config import PULCHRA_ID, PulchraCompileConfig
from .reviewed import (
    PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT,
    PULCHRA_CINEMA6_NIGHTMARE_RULE_ID,
    PULCHRA_EXTRA_ABILITY_RULE_ID,
    PULCHRA_HUNTER_STEP_ACTIVE,
    PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT,
    PULCHRA_PURSUIT_MARK_ACTIVE,
    PULCHRA_REVIEWED_MAPPING,
)


_NIGHTMARE_MAIN_TEMPLATE = EventTemplateId(
    "template:pulchra:1351:nightmare-shadow-main:main"
)
_NIGHTMARE_FINISHER_SOURCE = "特殊技：噬爪·噩梦袭影"
_NIGHTMARE_FINISHER_PARAMETER = "终结一击伤害倍率"
_NIGHTMARE_MAX_EXTRA = 7
_NIGHTMARE_REPEAT_RULE_ID = RuleItemId("rule:character:1351:nightmare-repeat-packets")


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1351:{key}"),
        owner=PULCHRA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
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
            effect_id=EffectId(f"effect:character:1351:{key}"),
            source=source,
            owner=PULCHRA_ID,
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


def _source(raw: NanokaRawRecord, key: str, kind: EffectSourceType, label: str, text: str | None):
    return source_for(
        PULCHRA_ID,
        key,
        kind,
        label,
        text if text is not None else f"Nanoka {raw.source_version}: {raw.source_url}",
    )


def _nightmare_child(
    ordinal: int,
    *,
    finisher: bool,
    source_rule_id: RuleItemId,
) -> DirectDamageEventTemplate:
    kind = "finisher" if finisher else "ordinary"
    template_id = EventTemplateId(
        f"template:pulchra:1351:nightmare-extra-{ordinal}:{kind}"
    )
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId(
            f"event:pulchra:1351:nightmare-extra-{ordinal}:{kind}"
        ),
        label=f"噩梦袭影：第{ordinal}次追加攻击（{'终结一击' if finisher else '重复攻击'}）",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}),
        element=Element.PHYSICAL,
        source_rule_item_id=source_rule_id,
    )
    return DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=PULCHRA_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(PULCHRA_ID),
        crit_rule=StandardCritRule(PULCHRA_ID),
        move_id=None,
    )


def _raw_ratio(raw: NanokaRawRecord, parameter_name: str, level: int) -> float | Unresolved:
    diagnostic_sink: list[CalculationDiagnostic] = []
    value = raw_multiplier(
        raw_move_index(raw),
        _NIGHTMARE_FINISHER_SOURCE,
        parameter_name,
        level,
        f"{PULCHRA_ID}:nightmare:{parameter_name}",
        diagnostic_sink,
        "1351007" if parameter_name == _NIGHTMARE_FINISHER_PARAMETER else "1351006",
    )
    return value


def _exact_parameter(parameter_id: str, value: int):
    return ScenarioParameterRangeCondition(parameter_id, minimum=value, maximum=value)


def _nightmare_slot_rules(
    raw: NanokaRawRecord,
    *,
    ordinary_multiplier,
    finisher_multiplier,
) -> tuple[CalculationRuleItem, tuple[DirectDamageEventTemplate, ...], tuple[DerivedDamageEventTemplateRef, ...]]:
    """Select one packet per added hit; only the selected final hit is the finisher.

    For an additional-hit count N, slots 1..N-1 use the 1351006 source curve
    and slot N uses the 1351007 finisher curve. This yields 1 initial + 4
    ordinary repeats + 1 finisher at N=5, and 1 + 6 + 1 at C6/N=7.
    """
    source_text = raw_move_index(raw)[_NIGHTMARE_FINISHER_SOURCE].description
    effects: list[EventCreationEffect] = []
    templates: list[DirectDamageEventTemplate] = []
    derived: list[DerivedDamageEventTemplateRef] = []
    cap = 7
    for ordinal in range(1, cap + 1):
        for finisher in (False, True):
            kind = "finisher" if finisher else "ordinary"
            template = _nightmare_child(
                ordinal,
                finisher=finisher,
                source_rule_id=_NIGHTMARE_REPEAT_RULE_ID,
            )
            base_count = str(PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT)
            c6_count = str(PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT)
            c6_enabled = RuleStackCondition(
                str(PULCHRA_CINEMA6_NIGHTMARE_RULE_ID),
                1,
                requires_rule_enabled=True,
            )
            if finisher:
                base_condition = AllCondition((
                    _exact_parameter(base_count, ordinal),
                    AnyCondition((
                        NotCondition(c6_enabled),
                        _exact_parameter(c6_count, 0),
                    )),
                ))
                c6_conditions = tuple(
                    AllCondition((
                        _exact_parameter(base_count, base_value),
                        _exact_parameter(c6_count, c6_value),
                        c6_enabled,
                    ))
                    for base_value in range(6)
                    for c6_value in range(3)
                    if base_value + c6_value == ordinal
                )
                conditions = (base_condition, *c6_conditions)
            else:
                base_condition = ScenarioParameterRangeCondition(
                    base_count,
                    minimum=ordinal + 1,
                )
                c6_conditions = tuple(
                    AllCondition((
                        _exact_parameter(base_count, base_value),
                        _exact_parameter(c6_count, c6_value),
                        c6_enabled,
                    ))
                    for base_value in range(6)
                    for c6_value in range(3)
                    if base_value + c6_value >= ordinal + 1
                )
                conditions = (base_condition, *c6_conditions)
            condition = conditions[0] if len(conditions) == 1 else AnyCondition(tuple(conditions))
            effects.append(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            f"effect:character:1351:nightmare-extra-{ordinal}:{kind}"
                        ),
                        source=_source(
                            raw,
                            f"nightmare-extra-{ordinal}:{kind}",
                            EffectSourceType.SKILL,
                            f"特殊技：噬爪·噩梦袭影（追加攻击{ordinal}）",
                            source_text,
                        ),
                        owner=PULCHRA_ID,
                        target=EffectTarget.SELF,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        condition=condition,
                        filters=(
                            EventTemplateIdFilter(_NIGHTMARE_MAIN_TEMPLATE),
                            DamageDealerFilter(PULCHRA_ID),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=template.ref.template_id,
                        unique_per_source_event=True,
                    ),
                )
            )
            templates.append(template)
            packet_multiplier = finisher_multiplier if finisher else ordinary_multiplier
            derived.append(
                DerivedDamageEventTemplateRef(
                    template=template.ref,
                    multiplier=packet_multiplier,
                )
            )
    missing_finisher_diagnostic = (
        (
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId("data:character:1351:nightmare-finisher:missing-curve"),
                kind=DiagnosticKind.MISSING_DATA,
                message="The finisher event is retained with an unresolved multiplier because its exact Nanoka source curve is unavailable at this skill level.",
                blocking=False,
                original_text=_NIGHTMARE_FINISHER_PARAMETER,
            ),
        )
        if isinstance(finisher_multiplier, Unresolved)
        else ()
    )
    packet_rule = _rule(
        "nightmare-repeat-packets",
        _source(raw, "nightmare-repeat-packets", EffectSourceType.SKILL, "噩梦袭影：重复攻击与终结一击", source_text),
        "噩梦袭影：按当前追加次数生成重复攻击与终结一击",
        source_text,
        RuleEligibility.ELIGIBLE,
        effects=tuple(effects),
        diagnostics=missing_finisher_diagnostic,
    )
    return packet_rule, tuple(templates), tuple(derived)


def compile_pulchra(
    config: PulchraCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, move_diagnostics = compile_direct_moves(
        character_id=PULCHRA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=PULCHRA_REVIEWED_MAPPING,
        id_namespace="pulchra:1351",
    )
    entry_by_key = {str(entry.entry_id).rsplit(":", 1)[-1]: entry for entry in entries}
    nightmare_entry = entry_by_key["nightmare-shadow-main"]
    nightmare_main_id = nightmare_entry.main_damage_event.template_id
    if nightmare_main_id != _NIGHTMARE_MAIN_TEMPLATE:
        raise ValueError("reviewed Nightmare main template identity changed")

    raw_moves = raw_move_index(raw_record)
    nightmare_level = effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    ordinary_multiplier = nightmare_entry.multiplier_variants[0].multiplier
    finisher_ratio = _raw_ratio(raw_record, _NIGHTMARE_FINISHER_PARAMETER, nightmare_level)
    finisher_multiplier = (
        finisher_ratio
        if isinstance(finisher_ratio, Unresolved)
        else FixedMultiplier(Resolved(float(finisher_ratio)))
    )
    nightmare_packet_rule, nightmare_templates, nightmare_derived = _nightmare_slot_rules(
        raw_record,
        ordinary_multiplier=ordinary_multiplier,
        finisher_multiplier=finisher_multiplier,
    )

    rules: list[CalculationRuleItem] = [nightmare_packet_rule]
    conditions: list[ScenarioCondition] = []
    parameters = (
        ScenarioIntegerParameter(
            parameter_id=PULCHRA_NIGHTMARE_BASE_EXTRA_ATTACK_COUNT,
            label="噩梦袭影追加攻击次数（基础上限5）",
            original_text=raw_moves["特殊技：噬爪·噩梦袭影"].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=5,
            minimum=0,
            maximum=5,
        ),
        ScenarioIntegerParameter(
            parameter_id=PULCHRA_CINEMA6_EXTRA_ATTACK_COUNT,
            label="6影：额外追加攻击次数（仅启用6影时计入）",
            original_text=raw_record.mindscapes[5].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=2 if config.cinema_level >= 6 else 0,
            minimum=0,
            maximum=2 if config.cinema_level >= 6 else 0,
        ),
    )

    pursuit_source = _source(
        raw_record,
        "extra-ability:pursuit",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    conditions.append(
        ScenarioCondition(
            condition_id=PULCHRA_PURSUIT_MARK_ACTIVE,
            label="当前目标已处于困迹状态",
            original_text=raw_record.extra_ability_description,
            resolution=ConditionResolution.USER_SELECTED,
            value=config.pursuit_mark_active,
        )
    )
    extra_effect = _modifier(
        "extra-ability:pursuit-follow-up-damage",
        pursuit_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.30),
        target=EffectTarget.TEAM,
        filters=(DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),),
        condition=RuleStackCondition(
            str(PULCHRA_EXTRA_ABILITY_RULE_ID), 1, requires_rule_enabled=True
        ),
    )
    eligible = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "extra-ability:pursuit",
            pursuit_source,
            "额外能力：困迹目标的追加攻击伤害+30%",
            raw_record.extra_ability_description,
            eligible,
            effects=(extra_effect,) if config.additional_ability_eligible else (),
            condition_ids=(PULCHRA_PURSUIT_MARK_ACTIVE,),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )

    talent1, talent2, talent3, _talent4, talent5, talent6 = raw_record.mindscapes
    talent1_source = _source(raw_record, "cinema1", EffectSourceType.CINEMA, talent1.name, talent1.description)
    talent2_source = _source(raw_record, "cinema2", EffectSourceType.CINEMA, talent2.name, talent2.description)
    talent1_unlocked = config.cinema_level >= 1
    talent2_unlocked = config.cinema_level >= 2
    c1_effect = _modifier(
        "cinema1:pursuit-crit-rate",
        talent1_source,
        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        Resolved(0.10),
        target=EffectTarget.SELF,
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(PULCHRA_ID),
        ),
    )
    rules.append(
        _rule(
            "cinema1:pursuit-crit-rate",
            talent1_source,
            "1影：攻击困迹目标时自身暴击率+10%",
            talent1.description,
            RuleEligibility.ELIGIBLE if talent1_unlocked else RuleEligibility.INELIGIBLE,
            effects=(c1_effect,) if talent1_unlocked else (),
            condition_ids=(PULCHRA_PURSUIT_MARK_ACTIVE,) if talent1_unlocked else (),
        )
    )
    # The live-target mark condition is independent of whether Pulchra's
    # Extra Ability is team-eligible or enabled in this scenario.
    c2_effects = ()
    if talent2_unlocked:
        conditions.append(
            ScenarioCondition(
                condition_id=PULCHRA_HUNTER_STEP_ACTIVE,
                label="波可娜当前处于猎步状态",
                original_text=talent2.description,
                resolution=ConditionResolution.USER_SELECTED,
                value=config.hunter_step_active,
            )
        )
        c2_effects = (_modifier(
            "cinema2:hunter-step-attack",
            talent2_source,
            CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
            Resolved(0.10),
            target=EffectTarget.SELF,
        ),)
    rules.append(
        _rule(
            "cinema2:hunter-step-attack",
            talent2_source,
            "2影：猎步状态攻击力+10%",
            talent2.description,
            RuleEligibility.ELIGIBLE if talent2_unlocked else RuleEligibility.INELIGIBLE,
            effects=c2_effects,
            condition_ids=(PULCHRA_HUNTER_STEP_ACTIVE,) if talent2_unlocked else (),
        )
    )

    for level, talent in ((3, talent3), (5, talent5)):
        source = _source(raw_record, f"cinema{level}", EffectSourceType.CINEMA, talent.name, talent.description)
        unlocked = config.cinema_level >= level
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级+2",
                talent.description,
                RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE,
            )
        )

    c6_source = _source(raw_record, "cinema6", EffectSourceType.CINEMA, talent6.name, talent6.description)
    c6_unlocked = config.cinema_level >= 6
    c6_bonus_ids = (
        nightmare_entry.main_damage_event.template_id,
        *(template.ref.template_id for template in nightmare_templates),
    )
    c6_bonus = _modifier(
        "cinema6:nightmare-shadow-damage",
        c6_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.15),
        target=EffectTarget.TEAM,
        filters=(
            DamageTypeFilter(DamageType.DIRECT),
            DamageDealerFilter(PULCHRA_ID),
            AnyFilter(tuple(EventTemplateIdFilter(item) for item in c6_bonus_ids)),
        ),
    )
    rules.append(
        _rule(
            "cinema6:nightmare-damage",
            c6_source,
            "6影：噩梦袭影伤害+15%并启用追加次数上限+2",
            talent6.description,
            RuleEligibility.ELIGIBLE if c6_unlocked else RuleEligibility.INELIGIBLE,
            effects=(c6_bonus,) if c6_unlocked else (),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )
    c6_pursuit_bonus = _modifier(
        "cinema6:pursuit-other-damage",
        c6_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.30),
        target=EffectTarget.TEAM,
        filters=(
            NotFilter(DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK)),
        ),
        condition=RuleStackCondition(
            str(PULCHRA_EXTRA_ABILITY_RULE_ID), 1, requires_rule_enabled=True
        ),
    )
    rules.append(
        _rule(
            "cinema6:pursuit-non-follow-up",
            c6_source,
            "6影：困迹对非追加攻击也生效",
            talent6.description,
            RuleEligibility.ELIGIBLE
            if c6_unlocked and config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            effects=(c6_pursuit_bonus,)
            if c6_unlocked and config.additional_ability_eligible
            else (),
            condition_ids=(PULCHRA_PURSUIT_MARK_ACTIVE,)
            if c6_unlocked and config.additional_ability_eligible
            else (),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )

    all_templates = (*templates, *nightmare_templates)
    return build_definition(
        character_id=PULCHRA_ID,
        role=CharacterRole.STUN,
        element=Element.PHYSICAL,
        source=_source(raw_record, "character", EffectSourceType.SKILL, raw_record.name, None),
        entries=entries,
        templates=all_templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        independent_derived_damage_events=nightmare_derived,
        diagnostics=tuple(move_diagnostics),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(PULCHRA_ID))


def _validate_raw(raw: NanokaRawRecord, config: PulchraCompileConfig) -> None:
    if raw.character_id != PULCHRA_ID or raw.name != "波可娜" or raw.code_name != "Pulchra":
        raise ValueError("unexpected Pulchra raw identity")
    if raw.specialty != "击破" or raw.element != "物理" or raw.rarity != 3:
        raise ValueError("unexpected Pulchra role, element, or rank")
    if raw.faction != "卡吕冬之子" or raw.icon != "IconRole38":
        raise ValueError("Pulchra source identity or faction changed")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1351.json":
        raise ValueError("Pulchra provenance must identify live Nanoka 3.2 character 1351")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Pulchra source must contain seven Core levels and six Cinemas")
    if raw.potential_details:
        raise ValueError("Pulchra source has no Potential levels")
    if config.character_id != raw.character_id:
        raise ValueError("Pulchra config and raw IDs must match")


__all__ = ["compile_pulchra", "load_raw_record"]
