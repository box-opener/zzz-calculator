"""Compile Corin's reviewed live Nanoka 3.2 record."""

from __future__ import annotations

from dataclasses import replace
import re

from core.types import (
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
    ElementFilter,
    EnemyStateFilter,
    CurrentAttackValueSource,
    FixedMultiplier,
    MoveId,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
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
    raw_multiplier,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import CorinCompileConfig
from .reviewed import (
    C1_TARGET_DAMAGE_ACTIVE,
    CHAINSAW_CONTINUOUS_ACTIVE,
    CINEMA6_CURRENT_CHARGES,
    CORIN_ID,
    CORIN_PHYSICAL_ANOMALY_RECORD_ID,
    CORIN_REVIEWED_MAPPING,
    ENEMY_STUNNED_STATE_ID,
    EX_SPECIAL_MOVE_ID,
    SPECIAL_SWEEP_MOVE_ID,
    PHYSICAL_DISORDER_REMAINING_SECONDS,
)


_PHYSICAL_ANOMALY_MOVE_ID = MoveId("move:corin:physical-assault")
_PHYSICAL_DISORDER_MOVE_ID = MoveId("move:corin:physical-disorder")


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


def _source(
    source_key: str,
    source_type: EffectSourceType,
    label: str,
    text: str,
) -> RuleSource:
    return source_for(CORIN_ID, source_key, source_type, label, text)


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
        rule_id=RuleItemId(f"rule:character:1061:{key}"),
        owner=CORIN_ID,
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
            effect_id=EffectId(f"effect:character:1061:{key}"),
            source=source,
            owner=CORIN_ID,
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


def _note(key: str, text: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1061:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=text,
        blocking=False,
        original_text=original_text,
    )


def _static_entries() -> tuple[
    tuple[MoveCalculationEntry, ...],
    tuple[object, ...],
    ScenarioIntegerParameter,
]:
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1061:physical-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1061:physical-anomaly"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=CORIN_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=CORIN_ID,
        history_record_source=CORIN_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_PHYSICAL_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1061:physical-anomaly"),
        character_id=CORIN_ID,
        move_id=_PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text=(
            "按静态单人100%积蓄的物理异常记录结算强击，倍率7.13，使用NoCrit。"
        ),
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1061:physical-anomaly"
                ),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1061:physical-disorder",
        semantic_id=DamageEventSemanticId("event:character:1061:physical-disorder"),
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=CORIN_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=CORIN_ID,
        history_record_source=CORIN_PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_PHYSICAL_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1061:physical-disorder"),
        character_id=CORIN_ID,
        move_id=_PHYSICAL_DISORDER_MOVE_ID,
        display_name="紊乱：物理异常（剩余时间补偿）",
        original_text="物理紊乱基础倍率450%，每秒剩余时间补偿75%，按floor(t)计算。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1061:physical-disorder"
                ),
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


def _with_cinema6_charge_bonus(
    entries: tuple[MoveCalculationEntry, ...],
    config: CorinCompileConfig,
    raw: NanokaRawRecord,
) -> tuple[MoveCalculationEntry, ...]:
    if config.cinema_level < 6:
        return entries
    mindscape = raw.mindscapes[5]
    per_charge = _number(
        mindscape.description,
        r"每层充能使本次攻击额外造成可琳(?P<value>[\d.]+)%攻击力",
        "Corin Cinema 6 damage per charge",
    ) / 100.0
    bonus_entry_keys = {
        "dodge-counter",
        "special-saw-explosion",
        "special-full-maximum-continuous-saw",
        "ex-special-saw-explosion",
        "ex-special-full-maximum-continuous-saw",
        "quick-assist-emergency-measures",
        "assist-strike-quick-cleaning",
    }
    updated: list[MoveCalculationEntry] = []
    for entry in entries:
        key = str(entry.entry_id).rsplit(":", 1)[-1]
        if key not in bonus_entry_keys:
            updated.append(entry)
            continue
        variant = entry.multiplier_variants[0]
        if not isinstance(variant.multiplier, FixedMultiplier) or not isinstance(
            variant.multiplier.value, Resolved
        ):
            raise ValueError("Corin C6 requires resolved reviewed damage curves")
        base_value = variant.multiplier.value.value
        updated_variant = replace(
            variant,
            label=f"{variant.label} + 3%攻击力 × 当前充能层数",
            parameter_value_id=CINEMA6_CURRENT_CHARGES,
            parameter_base_value=base_value,
            parameter_coefficient=per_charge,
        )
        updated.append(
            replace(entry, multiplier_variants=(updated_variant,))
        )
    return tuple(updated)


def _combined_continuous_saw_entries(
    config: CorinCompileConfig,
    raw: NanokaRawRecord,
) -> tuple[
    tuple[MoveCalculationEntry, ...],
    tuple[DirectDamageEventTemplate, ...],
    tuple[CalculationDiagnostic, ...],
]:
    """Build the source-explicit full maximum Special/EX totals once."""

    raw_moves = raw_move_index(raw)
    definitions = (
        (
            "special-full-maximum-continuous-saw",
            SPECIAL_SWEEP_MOVE_ID,
            "特殊技：强力清扫（持续斩击最大完整伤害）",
            "特殊技：强力清扫",
            SkillGroup.SPECIAL_ATTACK,
            frozenset({DamageTag.SPECIAL_ATTACK}),
            (
                ("特殊技：强力清扫", "回旋斩击伤害倍率", "1061008"),
                ("特殊技：强力清扫", "持续斩击最大伤害倍率", "1061009"),
                ("特殊技：强力清扫", "爆炸伤害倍率", "1061010"),
            ),
        ),
        (
            "ex-special-full-maximum-continuous-saw",
            EX_SPECIAL_MOVE_ID,
            "强化特殊技：小心裙角（持续斩击最大完整伤害）",
            "强化特殊技：小心裙角",
            SkillGroup.SPECIAL_ATTACK,
            frozenset({DamageTag.EX_SPECIAL_ATTACK}),
            (
                ("强化特殊技：小心裙角", "回旋斩击伤害倍率", "1061011"),
                ("强化特殊技：小心裙角", "持续斩击最大伤害倍率", "1061012"),
                ("强化特殊技：小心裙角", "爆炸伤害倍率", "1061013"),
            ),
        ),
    )
    entries: list[MoveCalculationEntry] = []
    templates: list[DirectDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for key, move_id, label, source_name, group, tags, components in definitions:
        level = effective_skill_level(config, group)
        multiplier_components = []
        entry_diagnostics: list[CalculationDiagnostic] = []
        for component_source_name, parameter_name, source_skill_id in components:
            multiplier_components.append(
                raw_multiplier(
                    raw_moves,
                    component_source_name,
                    parameter_name,
                    level,
                    f"{CORIN_ID}:{key}",
                    entry_diagnostics,
                    source_skill_id,
                )
            )
        unresolved = next(
            (item for item in multiplier_components if isinstance(item, Unresolved)),
            None,
        )
        if unresolved is not None:
            multiplier = unresolved
        else:
            multiplier = FixedMultiplier(
                Resolved(sum(float(item) for item in multiplier_components))
            )
        ref = DamageEventTemplateRef(
            template_id=f"template:character:1061:{key}:main",
            semantic_id=DamageEventSemanticId(f"event:character:1061:{key}:main"),
            label=label,
            damage_type=DamageType.DIRECT,
            skill_group=group,
            damage_tags=tags,
            element=Element.PHYSICAL,
        )
        template = DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=CORIN_ID,
            element=Element.PHYSICAL,
            base_source=CurrentAttackValueSource(CORIN_ID),
            crit_rule=StandardCritRule(CORIN_ID),
            move_id=move_id,
        )
        raw_move = raw_moves.get(source_name)
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(f"move-entry:character:1061:{key}"),
                character_id=CORIN_ID,
                move_id=move_id,
                display_name=label,
                original_text=(
                    raw_move.description
                    if raw_move is not None
                    else source_name
                ),
                skill_group=group,
                damage_tags=tags,
                multiplier_relation=MultiplierRelation.COMPLETE,
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId(
                            f"variant:character:1061:{key}:damage"
                        ),
                        label="起手 + 持续斩击最大值 + 爆炸",
                        parameter_name="完整最大伤害倍率",
                        multiplier=multiplier,
                    ),
                ),
                main_damage_event=ref,
                diagnostics=tuple(entry_diagnostics),
            )
        )
        templates.append(template)
        diagnostics.extend(entry_diagnostics)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def compile_corin(
    config: CorinCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=CORIN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=CORIN_REVIEWED_MAPPING,
        id_namespace="character:1061",
    )
    combined_entries, combined_templates, combined_diagnostics = (
        _combined_continuous_saw_entries(config, raw_record)
    )
    direct_entries = (*direct_entries, *combined_entries)
    direct_templates = (*direct_templates, *combined_templates)
    direct_diagnostics = (*direct_diagnostics, *combined_diagnostics)
    direct_entries = _with_cinema6_charge_bonus(
        direct_entries,
        config,
        raw_record,
    )
    static_entries, static_templates, disorder_seconds = _static_entries()

    core_level = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core_level.name,
        core_level.description,
    )
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core_level.extra_ability_name,
        core_level.extra_ability_description,
    )
    core_bonus = _number(
        core_level.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Corin Core chainsaw damage bonus",
    ) / 100.0
    extra_bonus = _number(
        core_level.extra_ability_description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Corin Additional Ability damage bonus",
    ) / 100.0

    cinema1 = raw_record.mindscapes[0]
    cinema1_source = _source(
        "cinema-1",
        EffectSourceType.CINEMA,
        cinema1.name,
        cinema1.description,
    )
    cinema1_bonus = _number(
        cinema1.description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Corin Cinema 1 damage bonus",
    ) / 100.0

    cinema2 = raw_record.mindscapes[1]
    cinema2_source = _source(
        "cinema-2",
        EffectSourceType.CINEMA,
        cinema2.name,
        cinema2.description,
    )
    cinema2_resistance_per_stack = _number(
        cinema2.description,
        r"下降(?P<value>[\d.]+)%",
        "Corin Cinema 2 physical resistance reduction per stack",
    ) / 100.0

    conditions = (
        _condition(
            CHAINSAW_CONTINUOUS_ACTIVE,
            "可琳当前使用电锯持续斩击",
            core_level.description,
        ),
        _condition(
            C1_TARGET_DAMAGE_ACTIVE,
            "可琳1影：当前目标受伤增益有效",
            cinema1.description,
        ),
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:chainsaw-continuous-damage",
            core_source,
            f"核心被动：电锯持续斩击伤害+{core_bonus * 100:g}%",
            core_level.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(CHAINSAW_CONTINUOUS_ACTIVE,),
            effects=(
                _modifier(
                    "core:chainsaw-continuous-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(core_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(
                        DamageDealerFilter(CORIN_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                    ),
                ),
            ),
        ),
        _rule(
            "extra-ability:stunned-target-damage",
            extra_source,
            f"额外能力：失衡目标伤害+{extra_bonus * 100:g}%",
            core_level.extra_ability_description,
            (
                RuleEligibility.ELIGIBLE
                if config.additional_ability_eligible
                else RuleEligibility.INELIGIBLE
            ),
            effects=(
                _modifier(
                    "extra-ability:stunned-target-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(extra_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(
                        DamageDealerFilter(CORIN_ID),
                        EnemyStateFilter(ENEMY_STUNNED_STATE_ID),
                    ),
                ),
            ),
        ),
        _rule(
            "cinema1:current-target-damage",
            cinema1_source,
            f"1影：对当前目标伤害+{cinema1_bonus * 100:g}%",
            cinema1.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 1
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(C1_TARGET_DAMAGE_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:current-target-damage",
                    cinema1_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(cinema1_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(DamageDealerFilter(CORIN_ID),),
                ),
            ),
        ),
        _rule(
            "cinema2:current-physical-resistance-stacks",
            cinema2_source,
            "2影：当前物理抗性降低层数",
            cinema2.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 2
                else RuleEligibility.INELIGIBLE
            ),
            effects=(
                _modifier(
                    "cinema2:current-physical-resistance-stacks",
                    cinema2_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(cinema2_resistance_per_stack),
                    target=EffectTarget.ENEMY,
                    filters=(ElementFilter(Element.PHYSICAL),),
                ),
            ),
            stack_count=20,
            stack_min=0,
            stack_max=20,
        ),
    ]

    for level in (3, 5):
        mindscape = raw_record.mindscapes[level - 1]
        source = _source(
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级提升",
                mindscape.description,
                (
                    RuleEligibility.ELIGIBLE
                    if config.cinema_level >= level
                    else RuleEligibility.INELIGIBLE
                ),
            )
        )

    cinema4 = raw_record.mindscapes[3]
    c4_source = _source(
        "cinema-4",
        EffectSourceType.CINEMA,
        cinema4.name,
        cinema4.description,
    )
    c4_energy_note = _note(
        "cinema4-energy-resource",
        "Cinema 4 restores an Energy resource after the listed support/Chain actions, but this calculation result does not expose Energy; no Energy value is fabricated.",
        cinema4.description,
    )
    rules.append(
        _rule(
            "cinema4:energy-source-only",
            c4_source,
            "4影：能量回复（资源结果未提供）",
            cinema4.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 4
                else RuleEligibility.INELIGIBLE
            ),
            diagnostics=(c4_energy_note,),
        )
    )

    if config.cinema_level >= 6:
        charge_parameter = ScenarioIntegerParameter(
            parameter_id=CINEMA6_CURRENT_CHARGES,
            label="6影：当前电锯充能层数",
            original_text=raw_record.mindscapes[5].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=40,
        )
        parameters = (disorder_seconds, charge_parameter)
    else:
        parameters = (disorder_seconds,)

    daze_note = _note(
        "parry-daze-unavailable",
        "The raw Support Parry entries contain only Daze coefficients. The current result has no Daze field, so they are retained as source text and are not turned into damage.",
        "招架支援：请、请让我来！的轻/重/连续招架失衡倍率",
    )
    c6_note = (
        _note(
            "cinema6-charge-timing",
            "The selected 0–40 value is Corin's current charge resource. The calculator does not replay chainsaw hit or charge-consumption timing.",
            raw_record.mindscapes[5].description,
        )
        if config.cinema_level >= 6
        else None
    )
    diagnostics = [*direct_diagnostics, daze_note]
    if c6_note is not None:
        diagnostics.append(c6_note)
    entries = (*direct_entries, *static_entries)
    templates = (*direct_templates, *static_templates)

    return build_definition(
        character_id=CORIN_ID,
        role=CharacterRole.ATTACK,
        element=Element.PHYSICAL,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: CorinCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "可琳" or raw.code_name != "Corin":
        raise ValueError("unexpected character identity in Corin source")
    if raw.specialty != "强攻" or raw.element != "物理" or raw.rarity != 3:
        raise ValueError("Corin role, element, or rank changed from reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Corin source must contain seven cores and six cinemas")
    if raw.source_version != "3.2" or not raw.source_url.endswith("/character/1061.json"):
        raise ValueError("Corin raw source provenance must identify Nanoka 3.2 character 1061")


__all__ = ["compile_corin"]
