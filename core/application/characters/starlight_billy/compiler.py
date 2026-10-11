"""Compile Starlight - Billy's reviewed Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterRole,
    CurrentPenetrationForceValueSource,
    DamageDealerFilter,
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
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveIdFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
)

from ...diagnostics import CalculationDiagnostic
from ...ids import (
    DamageEventSemanticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioConditionId,
    ScenarioParameterId,
)
from ...moves import (
    DamageEventTemplateRef,
    MoveCalculationEntry,
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
    effective_skill_level,
    raw_move_index,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import PenetrationDamageEventTemplate
from .config import STARLIGHT_BILLY_ID, StarlightBillyCompileConfig
from .reviewed import STARLIGHT_BILLY_REVIEWED_MAPPING


STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE = ScenarioConditionId(
    "condition:starlight-billy:core-motor-suppression-crit-damage-active"
)
STARLIGHT_BILLY_C2_TURBO_ACTIVE = ScenarioConditionId(
    "condition:starlight-billy:cinema2-turbo-lone-wheel-active"
)
STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE = ScenarioConditionId(
    "condition:starlight-billy:cinema1-physical-resistance-ignore-active"
)
STARLIGHT_BILLY_EXTRA_ABILITY_STACKS = ScenarioParameterId(
    "parameter:character:1531:extra-ability-starshine-current-stacks"
)
STARLIGHT_BILLY_C4_SUPPRESSION_STACKS = ScenarioParameterId(
    "parameter:character:1531:cinema4-current-motor-suppression-stacks"
)
STARLIGHT_BILLY_C6_CONSUMED_STARSHINE = ScenarioParameterId(
    "parameter:character:1531:cinema6-consumed-starshine-stacks"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _validate_raw(raw: NanokaRawRecord, config: StarlightBillyCompileConfig) -> None:
    if raw.character_id != STARLIGHT_BILLY_ID:
        raise ValueError("raw character does not match Starlight - Billy")
    if (
        raw.name != "星徽·比利"
        or raw.code_name != "Starlight - Billy"
        or raw.rarity != 4
        or raw.specialty != "命破"
        or raw.element != "物理"
        or raw.faction != "狡兔屋"
        or raw.icon != "IconRole62"
    ):
        raise ValueError("raw character identity does not match reviewed Starlight - Billy source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1531.json"
    ):
        raise ValueError("raw Starlight - Billy provenance does not match Nanoka live3.2")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("raw Starlight - Billy record must contain seven Core levels and six cinemas")
    required = {spec.source_name for spec in STARLIGHT_BILLY_REVIEWED_MAPPING.moves}
    available = {item.name for item in raw.moves}
    missing = required - available
    if missing:
        raise ValueError(f"raw Starlight - Billy record is missing reviewed moves: {sorted(missing)}")
    if not 1 <= config.core_level <= len(raw.core_levels):
        raise ValueError("configured Core level is not available in raw source")


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(STARLIGHT_BILLY_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1531:{key}"),
        owner=STARLIGHT_BILLY_ID,
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
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1531:{key}"),
            source=source,
            owner=STARLIGHT_BILLY_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def _condition(condition_id: ScenarioConditionId, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _move_filter(*entry_keys: str) -> AnyFilter:
    return AnyFilter(
        tuple(
            EventTemplateIdFilter(
                EventTemplateId(f"template:character:1531:{entry_key}:main")
            )
            for entry_key in entry_keys
        )
    )


def _compile_moves(raw: NanokaRawRecord, config: StarlightBillyCompileConfig):
    raw_moves = raw_move_index(raw)
    entries: list[MoveCalculationEntry] = []
    templates: list[PenetrationDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    multipliers: dict[str, float] = {}

    for spec in STARLIGHT_BILLY_REVIEWED_MAPPING.moves:
        raw_move = raw_moves[spec.source_name]
        level = effective_skill_level(config, spec.skill_group)
        entry_diagnostics: list[CalculationDiagnostic] = []
        variants: list[MultiplierVariant] = []
        for parameter_spec in spec.parameters:
            multiplier = raw_multiplier(
                raw_moves,
                spec.source_name,
                parameter_spec.parameter_name,
                level,
                f"{STARLIGHT_BILLY_ID}:{spec.entry_key}",
                entry_diagnostics,
                source_skill_id=parameter_spec.source_skill_id,
            )
            if not isinstance(multiplier, Unresolved):
                multipliers[spec.entry_key] = multiplier
            variants.append(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1531:{spec.entry_key}:damage"
                    ),
                    label=parameter_spec.parameter_name,
                    parameter_name=parameter_spec.parameter_name,
                    multiplier=(
                        multiplier
                        if isinstance(multiplier, Unresolved)
                        else FixedMultiplier(Resolved(multiplier))
                    ),
                )
            )

        ref = DamageEventTemplateRef(
            template_id=EventTemplateId(
                f"template:character:1531:{spec.entry_key}:main"
            ),
            semantic_id=DamageEventSemanticId(
                f"event:character:1531:{spec.entry_key}:main"
            ),
            label=spec.display_name,
            damage_type=DamageType.PENETRATION,
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
            element=Element.PHYSICAL,
        )
        template = PenetrationDamageEventTemplate(
            ref=ref,
            damage_dealer=STARLIGHT_BILLY_ID,
            element=Element.PHYSICAL,
            base_source=CurrentPenetrationForceValueSource(STARLIGHT_BILLY_ID),
            crit_rule=StandardCritRule(STARLIGHT_BILLY_ID),
            move_id=spec.move_id,
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(
                    f"move-entry:character:1531:{spec.entry_key}"
                ),
                character_id=STARLIGHT_BILLY_ID,
                move_id=spec.move_id,
                display_name=spec.display_name,
                original_text=raw_move.description or spec.source_name,
                skill_group=spec.skill_group,
                damage_tags=spec.damage_tags,
                multiplier_relation=spec.multiplier_relation,
                multiplier_variants=tuple(variants),
                main_damage_event=ref,
                stage_index=spec.stage_index,
                condition_ids=tuple(spec.condition_ids),
                diagnostics=tuple(entry_diagnostics),
            )
        )
        templates.append(template)
        diagnostics.extend(entry_diagnostics)

    return entries, templates, diagnostics, raw_moves, multipliers


def compile_starlight_billy(
    config: StarlightBillyCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, diagnostics, _raw_moves, multipliers = _compile_moves(
        raw_record, config
    )
    core = raw_record.core_levels[config.core_level - 1]
    extra_text = core.extra_ability_description
    cinema_by_level = {item.level: item for item in raw_record.mindscapes}
    cinema_sources = {
        level: _source(
            f"cinema{level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for level, item in cinema_by_level.items()
    }
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        extra_text,
    )

    physical_penetration_scope = (
        DamageDealerFilter(STARLIGHT_BILLY_ID),
        DamageTypeFilter(DamageType.PENETRATION),
        ElementFilter(Element.PHYSICAL),
    )
    conditions = [
        _condition(
            STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE,
            "当前仍处于[特殊技：动力压制]触发的暴击伤害增益期间",
            core.description,
        ),
        _condition(
            STARLIGHT_BILLY_C2_TURBO_ACTIVE,
            "当前[涡轮增压]用于本次[强化特殊技：孤轮特技]",
            cinema_by_level[2].description,
        ),
        _condition(
            STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE,
            "当前仍处于[强化特殊技]命中后无视物理抗性期间",
            cinema_by_level[1].description,
        ),
    ]
    rules: list[CalculationRuleItem] = []

    force_per_max_hp = _number(
        core.description,
        r"每1点最大生命值将提高(?P<value>[\d.]+)点贯穿力",
        "Starlight - Billy Core max-HP Penetration Force coefficient",
    )
    rules.append(
        _rule(
            "core:max-hp-penetration-force",
            core_source,
            "核心被动：按当前最大生命值增加贯穿力",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:max-hp-penetration-force",
                    core_source,
                    CalculationNode.PENETRATION_FORCE_BONUS,
                    PanelStatDerivedValue(
                        source_character_id=STARLIGHT_BILLY_ID,
                        source_node=CalculationNode.CHARACTER_CURRENT_MAX_HP,
                        coefficient=Resolved(force_per_max_hp),
                    ),
                    target=EffectTarget.SELF,
                    filters=physical_penetration_scope,
                ),
            ),
        )
    )

    core_crit_damage = _number(
        core.description,
        r"自身暴击伤害提升(?P<value>[\d.]+)%",
        "Starlight - Billy Core Motor Suppression Crit Damage",
    ) / 100.0
    rules.append(
        _rule(
            "core:motor-suppression-crit-damage",
            core_source,
            "核心被动：动力压制触发的当前暴击伤害增益",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:motor-suppression-crit-damage",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(core_crit_damage),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )

    extra_per_stack = _number(
        extra_text,
        r"每层\[星辉\]会使.*?造成的伤害提升(?P<value>[\d.]+)%",
        "Starlight - Billy Extra Ability damage per Starshine stack",
    ) / 100.0
    extra_stack_cap = int(
        _number(
            extra_text,
            r"至多叠加(?P<value>\d+)层",
            "Starlight - Billy Extra Ability Starshine cap",
        )
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_parameter = ScenarioIntegerParameter(
        parameter_id=STARLIGHT_BILLY_EXTRA_ABILITY_STACKS,
        label=f"比利当前[星辉]层数（0–{extra_stack_cap}层）",
        original_text=extra_text,
        resolution=ParameterResolution.USER_SELECTED,
        value=extra_stack_cap,
        minimum=0,
        maximum=extra_stack_cap,
    )
    extra_move_filter = _move_filter(
        "ex-lone-wheel-stunt",
        "ex-grip-hub",
        "ex-swaying-step",
        "chain-knight-walk",
        "ultimate-knight-flying-kick",
        "basic-high-mileage-starlight",
    )
    rules.append(
        _rule(
            "extra-ability:starshine-damage",
            extra_source,
            "额外能力：[星辉]对指定招式的当前伤害增益",
            extra_text,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:starshine-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(STARLIGHT_BILLY_EXTRA_ABILITY_STACKS),
                        coefficient=Resolved(extra_per_stack),
                        cap_max=Resolved(extra_per_stack * extra_stack_cap),
                    ),
                    target=EffectTarget.SELF,
                    filters=(*physical_penetration_scope, extra_move_filter),
                ),
            ),
        )
    )

    c1 = cinema_by_level[1]
    c1_ignore = _number(
        c1.description,
        r"无视目标(?P<value>[\d.]+)%物理伤害抗性",
        "Starlight - Billy Cinema 1 Physical Resistance ignore",
    ) / 100.0
    rules.append(
        _rule(
            "cinema1:physical-resistance-ignore",
            cinema_sources[1],
            "1影：强化特殊技命中后的当前物理抗性无视",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            condition_ids=(STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE,),
            effects=(
                _modifier(
                    "cinema1:physical-resistance-ignore",
                    cinema_sources[1],
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c1_ignore),
                    target=EffectTarget.SELF,
                    filters=physical_penetration_scope,
                ),
            ),
        )
    )

    c2 = cinema_by_level[2]
    c2_normal_bonus = _number(
        c2.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Starlight - Billy Cinema 2 normal damage increase",
    ) / 100.0
    c2_moves = _move_filter(
        "basic-high-mileage-starlight",
        "ex-lone-wheel-stunt",
        "ultimate-knight-flying-kick",
    )
    c2_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 2
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema2:listed-move-damage",
            cinema_sources[2],
            "2影：最高马力、孤轮特技与终结技伤害提升",
            c2.description,
            c2_eligibility,
            effects=(
                _modifier(
                    "cinema2:listed-move-damage",
                    cinema_sources[2],
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c2_normal_bonus),
                    target=EffectTarget.SELF,
                    filters=(*physical_penetration_scope, c2_moves),
                ),
            ),
        )
    )
    c2_turbo_crit_bonus = _number(
        c2.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Starlight - Billy Cinema 2 Turbo Crit Damage",
    ) / 100.0
    rules.append(
        _rule(
            "cinema2:turbo-lone-wheel-crit-damage",
            cinema_sources[2],
            "2影：涡轮增压衔接的孤轮特技暴击伤害提升",
            c2.description,
            c2_eligibility,
            condition_ids=(STARLIGHT_BILLY_C2_TURBO_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:turbo-lone-wheel-crit-damage",
                    cinema_sources[2],
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c2_turbo_crit_bonus),
                    target=EffectTarget.SELF,
                    filters=(DamageDealerFilter(STARLIGHT_BILLY_ID), _move_filter("ex-lone-wheel-stunt")),
                ),
            ),
        )
    )

    c4 = cinema_by_level[4]
    c4_per_stack = _number(
        c4.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Starlight - Billy Cinema 4 Crit Damage per stack",
    ) / 100.0
    c4_stack_cap = int(
        _number(c4.description, r"至多叠加(?P<value>\d+)层", "Starlight - Billy Cinema 4 stack cap")
    )
    c4_parameter = ScenarioIntegerParameter(
        parameter_id=STARLIGHT_BILLY_C4_SUPPRESSION_STACKS,
        label=f"比利当前动力压制暴击伤害层数（0–{c4_stack_cap}层）",
        original_text=c4.description,
        resolution=ParameterResolution.USER_SELECTED,
        value=c4_stack_cap,
        minimum=0,
        maximum=c4_stack_cap,
    )
    rules.append(
        _rule(
            "cinema4:motor-suppression-crit-damage-stacks",
            cinema_sources[4],
            "4影：动力压制叠加的当前暴击伤害",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            condition_ids=(STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "cinema4:motor-suppression-crit-damage-stacks",
                    cinema_sources[4],
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(STARLIGHT_BILLY_C4_SUPPRESSION_STACKS),
                        coefficient=Resolved(c4_per_stack),
                        cap_max=Resolved(c4_per_stack * c4_stack_cap),
                    ),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )

    c6 = cinema_by_level[6]
    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    c6_penetration_bonus = _number(
        c6.description,
        r"造成的贯穿伤害提升(?P<value>[\d.]+)%",
        "Starlight - Billy Cinema 6 Penetration Damage Bonus",
    ) / 100.0
    c6_move_filter = _move_filter(
        "ultimate-knight-flying-kick",
        "basic-high-mileage-starlight",
    )
    rules.append(
        _rule(
            "cinema6:listed-penetration-damage-bonus",
            cinema_sources[6],
            "6影：终结技与最高马力的贯穿伤害提升",
            c6.description,
            c6_eligibility,
            effects=(
                _modifier(
                    "cinema6:listed-penetration-damage-bonus",
                    cinema_sources[6],
                    CalculationNode.PENETRATION_DAMAGE_BONUS,
                    Resolved(c6_penetration_bonus),
                    target=EffectTarget.SELF,
                    filters=(*physical_penetration_scope, c6_move_filter),
                ),
            ),
        )
    )

    c6_stack_cap = int(
        _number(c6.description, r"至多消耗(?P<value>\d+)层", "Starlight - Billy Cinema 6 consumed Starshine cap")
    )
    c6_parameter = ScenarioIntegerParameter(
        parameter_id=STARLIGHT_BILLY_C6_CONSUMED_STARSHINE,
        label=f"本次终结技/最高马力消耗的[煊赫星辉]层数（0–{c6_stack_cap}层）",
        original_text=c6.description,
        resolution=ParameterResolution.USER_SELECTED,
        value=c6_stack_cap,
        minimum=0,
        maximum=c6_stack_cap,
    )
    c6_whole_ratio_effects = []
    for entry_key in (
        "ultimate-knight-flying-kick",
        "basic-high-mileage-starlight",
    ):
        base_ratio = multipliers[entry_key]
        c6_whole_ratio_effects.append(
            _modifier(
                f"cinema6:whole-move-penetration-force:{entry_key}",
                cinema_sources[6],
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                ScenarioParameterDerivedValue(
                    parameter_id=str(STARLIGHT_BILLY_C6_CONSUMED_STARSHINE),
                    coefficient=Resolved(1.0 / base_ratio),
                    base=Resolved(1.0),
                    cap_max=Resolved(1.0 + c6_stack_cap / base_ratio),
                ),
                target=EffectTarget.SELF,
                filters=(*physical_penetration_scope, _move_filter(entry_key)),
                operation=EffectOperation.MULTIPLY,
            )
        )
    rules.append(
        _rule(
            "cinema6:consumed-starshine-whole-move-ratio",
            cinema_sources[6],
            "6影：消耗[煊赫星辉]为指定招式总倍率增加贯穿力倍率",
            c6.description,
            c6_eligibility,
            effects=tuple(c6_whole_ratio_effects),
        )
    )

    parameters = []
    if config.additional_ability_eligible:
        parameters.append(extra_parameter)
    if config.cinema_level >= 4:
        parameters.append(c4_parameter)
    if config.cinema_level >= 6:
        parameters.append(c6_parameter)

    return build_definition(
        character_id=STARLIGHT_BILLY_ID,
        role=CharacterRole.RUPTURE,
        element=Element.PHYSICAL,
        source=source_for(
            STARLIGHT_BILLY_ID,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(STARLIGHT_BILLY_ID))


__all__ = [
    "STARLIGHT_BILLY_C1_PHYSICAL_RESIST_IGNORE_ACTIVE",
    "STARLIGHT_BILLY_C2_TURBO_ACTIVE",
    "STARLIGHT_BILLY_C4_SUPPRESSION_STACKS",
    "STARLIGHT_BILLY_C6_CONSUMED_STARSHINE",
    "STARLIGHT_BILLY_CORE_SUPPRESSION_BUFF_ACTIVE",
    "STARLIGHT_BILLY_EXTRA_ABILITY_STACKS",
    "compile_starlight_billy",
    "load_raw_record",
]
