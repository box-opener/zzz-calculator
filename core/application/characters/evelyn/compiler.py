"""Compile Evelyn's reviewed Nanoka 3.2 character source."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
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
    MoveId,
    NoCritRule,
    PanelStatThresholdCondition,
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
    ScenarioConditionId,
    ScenarioParameterId,
)
from ...moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
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
from .config import EVELYN_ID, EvelynCompileConfig
from .reviewed import (
    EVELYN_C6_SHADOW_EDGE_ACTIVE,
    EVELYN_C4_SHIELD_ACTIVE,
    EVELYN_CONSTRAINT_CR_ACTIVE,
    EVELYN_TARGET_IMPRISONED,
    EVELYN_REVIEWED_MAPPING,
    EVELYN_SPECIAL_BIND_MOVE_ID,
    EVELYN_EX_SPECIAL_MOVE_ID,
    EVELYN_ULTIMATE_SHADOW_MOVE_ID,
    EVELYN_ULTIMATE_SOUND_MOVE_ID,
)


_FIRE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1321:fire-burn")
_FIRE_ANOMALY_MOVE_ID = MoveId("move:evelyn:fire-burn")
_FIRE_DISORDER_MOVE_ID = MoveId("move:evelyn:fire-disorder")
_FIRE_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1321:fire-burn")
_FIRE_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1321:fire-disorder")
_C6_STANDALONE_TEMPLATE_ID = EventTemplateId("template:character:1321:cinema6-shadow-edge-single")
_FIRE_DISORDER_HALF_SECONDS = ScenarioParameterId("parameter:evelyn:fire-disorder-half-seconds")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _source(key: str, kind: EffectSourceType, label: str, text: str | None) -> RuleSource:
    return source_for(EVELYN_ID, key, kind, label, text)


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    text: str,
    value: bool,
) -> ScenarioCondition:
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
        rule_id=RuleItemId(f"rule:character:1321:{key}"),
        owner=EVELYN_ID,
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
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1321:{key}"),
            source=source,
            owner=EVELYN_ID,
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


def _combined_fire_entry(
    raw_moves,
    config: EvelynCompileConfig,
    *,
    entry_key: str,
    move_id: MoveId,
    label: str,
    source_name: str,
    components: tuple[tuple[str, str], ...],
    skill_group: SkillGroup,
    tag: DamageTag,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    level = effective_skill_level(config, skill_group)
    source_move = raw_moves[source_name]
    ratios: list[float] = []
    for parameter_name, source_skill_id in components:
        ratio = raw_multiplier(
            raw_moves,
            source_name,
            parameter_name,
            level,
            f"{EVELYN_ID}:{entry_key}",
            [],
            source_skill_id=source_skill_id,
        )
        if isinstance(ratio, Unresolved):
            raise ValueError(f"Evelyn source ratio is missing for {entry_key}: {parameter_name}")
        ratios.append(ratio)
    total = sum(ratios)
    template_id = EventTemplateId(f"template:character:1321:{entry_key}")
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId(f"event:character:1321:{entry_key}"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=frozenset({tag}),
        element=Element.FIRE,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=EVELYN_ID,
        element=Element.FIRE,
        base_source=CurrentAttackValueSource(EVELYN_ID),
        crit_rule=StandardCritRule(EVELYN_ID),
        move_id=move_id,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1321:{entry_key}"),
        character_id=EVELYN_ID,
        move_id=move_id,
        display_name=label,
        original_text=source_move.description,
        skill_group=skill_group,
        damage_tags=ref.damage_tags,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(f"variant:character:1321:{entry_key}"),
                label=" + ".join(f"{ratio:.4f}" for ratio in ratios),
                parameter_name="单次完整招式伤害倍率",
                multiplier=FixedMultiplier(Resolved(total)),
            ),
        ),
        main_damage_event=ref,
    )
    return entry, template


def _static_fire_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id=_FIRE_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1321:fire-burn"),
        label="属性异常：灼烧（单跳50%，10秒20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=EVELYN_ID,
        element=Element.FIRE,
        anomaly_triggerer=EVELYN_ID,
        history_record_source=_FIRE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1321:fire-anomaly"),
        character_id=EVELYN_ID,
        move_id=_FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（单跳50%，10秒20跳）",
        original_text="静态火属性异常记录；每0.5秒结算异常效果强度的50%，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1321:fire-anomaly-tick"),
                label="每跳50% × 20",
                parameter_name="灼烧单跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id=_FIRE_DISORDER_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1321:fire-disorder"),
        label="紊乱：灼烧（当前剩余0.5秒单位）",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=EVELYN_ID,
        element=Element.FIRE,
        disorder_triggerer=EVELYN_ID,
        history_record_source=_FIRE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1321:fire-disorder"),
        character_id=EVELYN_ID,
        move_id=_FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧（当前剩余时间）",
        original_text="灼烧紊乱倍率为450% + 当前剩余0.5秒单位 × 50%；不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1321:fire-disorder"),
                label="450% + 每0.5秒 × 50%",
                parameter_name="灼烧紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_FIRE_DISORDER_HALF_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.5,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_FIRE_DISORDER_HALF_SECONDS,
        label="当前目标灼烧剩余0.5秒单位",
        original_text="按当前剩余时间选择0–20个0.5秒单位；不模拟灼烧时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=20,
        minimum=0,
        maximum=20,
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template), remaining


def compile_evelyn(
    config: EvelynCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=EVELYN_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=EVELYN_REVIEWED_MAPPING,
    )
    entries = list(entries)
    templates = list(templates)
    raw_moves = raw_move_index(raw_record)

    special_source = raw_moves["特殊技：束裂式·I型"]
    ex_source = raw_moves["强化特殊技：束裂式·终型"]
    special_entry, special_template = _combined_fire_entry(
        raw_moves,
        config,
        entry_key="special-rupture-i-full",
        move_id=EVELYN_SPECIAL_BIND_MOVE_ID,
        label="特殊技：束裂式·I型（缠绕+引爆）",
        source_name=special_source.name,
        components=(("缠绕伤害倍率", "1321009"), ("引爆伤害倍率", "1321010")),
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tag=DamageTag.SPECIAL_ATTACK,
    )
    ex_entry, ex_template = _combined_fire_entry(
        raw_moves,
        config,
        entry_key="ex-special-rupture-final-full",
        move_id=EVELYN_EX_SPECIAL_MOVE_ID,
        label="强化特殊技：束裂式·终型（缠绕+引爆）",
        source_name=ex_source.name,
        components=(("缠绕伤害倍率", "1321011"), ("引爆伤害倍率", "1321012")),
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tag=DamageTag.EX_SPECIAL_ATTACK,
    )
    entries.extend((special_entry, ex_entry))
    templates.extend((special_template, ex_template))

    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []

    core = raw_record.core_levels[config.core_level - 1]
    core_text = core.description
    core_source = _source("core", EffectSourceType.CORE_PASSIVE, core.name, core_text)
    constraint_condition = ScenarioConditionId(EVELYN_CONSTRAINT_CR_ACTIVE)
    conditions.append(
        _condition(
            constraint_condition,
            "当前仍持有牵缠禁制期间的暴击率提升",
            core_text,
            config.constraint_crit_active,
        )
    )
    core_crit_rate = _number(
        core_text,
        r"暴击率提升(?P<value>[\d.]+)%",
        "Evelyn Core Crit Rate",
    ) / 100.0
    rules.append(
        _rule(
            "core:constraint-crit-rate",
            core_source,
            f"核心被动：牵缠禁制期间暴击率+{core_crit_rate:.1%}",
            core_text,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:constraint-crit-rate",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(core_crit_rate),
                ),
            ),
            condition_ids=(constraint_condition,),
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId("unsupported:character:1321:core:constraint-duration"),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message="牵缠禁制离场后的10秒延续不模拟；按当前状态选择暴击率增益。",
                    blocking=False,
                    original_text=core_text,
                ),
            ),
        )
    )

    if config.cinema_level >= 1:
        cinema1 = raw_record.mindscapes[0]
        cinema1_source = _source("cinema1:imprisoned-defense-ignore", EffectSourceType.CINEMA, cinema1.name, cinema1.description)
        imprisoned_condition = ScenarioConditionId(EVELYN_TARGET_IMPRISONED)
        conditions.append(
            _condition(
                imprisoned_condition,
                "当前目标处于禁锢状态",
                cinema1.description,
                config.target_imprisoned,
            )
        )
        def_ignore = _number(cinema1.description, r"无视目标(?P<value>[\d.]+)%防御力", "Evelyn Cinema 1 Defense Ignore") / 100.0
        rules.append(
            _rule(
                "cinema1:imprisoned-defense-ignore",
                cinema1_source,
                f"1影：攻击禁锢目标无视{def_ignore:.0%}防御",
                cinema1.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema1:imprisoned-defense-ignore",
                        cinema1_source,
                        CalculationNode.DAMAGE_DEFENSE_IGNORE,
                        Resolved(def_ignore),
                        filters=(DamageDealerFilter(EVELYN_ID),),
                    ),
                ),
                condition_ids=(imprisoned_condition,),
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId("unsupported:character:1321:cinema1:imprisoned-duration"),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message="禁锢状态的触发与扩散不模拟；当前目标禁锢状态由用户选择。",
                        blocking=False,
                        original_text=cinema1.description,
                    ),
                ),
            )
        )

    if config.cinema_level >= 2:
        cinema2 = raw_record.mindscapes[1]
        c2_source = _source("cinema2:attack", EffectSourceType.CINEMA, cinema2.name, cinema2.description)
        attack_bonus = _number(cinema2.description, r"攻击力提升(?P<value>[\d.]+)%", "Evelyn Cinema 2 Attack Bonus") / 100.0
        rules.append(
            _rule(
                "cinema2:attack",
                c2_source,
                f"2影：攻击力+{attack_bonus:.0%}",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema2:attack",
                        c2_source,
                        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                        Resolved(attack_bonus),
                    ),
                ),
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId("unsupported:character:1321:cinema2:resource-return"),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message="燎火返还和25秒触发间隔不模拟；攻击力提升按当前影画生效。",
                        blocking=False,
                        original_text=cinema2.description,
                    ),
                ),
            )
        )

    if config.additional_ability_eligible:
        extra = raw_record.extra_ability_description
        extra_source = _source("extra-ability:chain-ultimate", EffectSourceType.ADDITIONAL_ABILITY, raw_record.extra_ability_name, extra)
        damage_bonus = _number(extra, r"造成的伤害提升(?P<value>[\d.]+)%", "Evelyn Additional Chain/Ultimate Bonus") / 100.0
        extra_effects = [
            _modifier(
                "extra-ability:chain-ultimate-damage",
                extra_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(damage_bonus),
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(EVELYN_ID),
                    AnyFilter((DamageTagFilter(DamageTag.CHAIN_ATTACK), DamageTagFilter(DamageTag.ULTIMATE))),
                ),
            )
        ]
        crit_threshold = _number(extra, r"暴击率大于等于(?P<value>[\d.]+)%", "Evelyn Additional Ability Crit Threshold") / 100.0
        multiplier_factor = _number(extra, r"伤害倍率提升至原本的(?P<value>[\d.]+)%", "Evelyn Additional Ability Chain/Ultimate Multiplier") / 100.0
        exact_ultimate_and_chain = AnyFilter(
            tuple(
                EventTemplateIdFilter(entry.main_damage_event.template_id)
                for entry in entries
                if str(entry.entry_id)
                in {
                    "move-entry:character:1321:chain-attack",
                    "move-entry:character:1321:ultimate-sound",
                    "move-entry:character:1321:ultimate-shadow",
                }
            )
        )
        extra_effects.append(
            _modifier(
                "extra-ability:high-crit-skill-multiplier",
                extra_source,
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                Resolved(multiplier_factor),
                filters=(DamageTypeFilter(DamageType.DIRECT), DamageDealerFilter(EVELYN_ID), exact_ultimate_and_chain),
                condition=PanelStatThresholdCondition(
                    EVELYN_ID,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    crit_threshold,
                ),
                operation=EffectOperation.MULTIPLY,
            )
        )
        rules.append(
            _rule(
                "extra-ability:chain-ultimate",
                extra_source,
                f"额外能力：连携技/终结技伤害+{damage_bonus:.0%}；暴击率≥{crit_threshold:.0%}时指定三招倍率×{multiplier_factor:.2f}",
                extra,
                RuleEligibility.ELIGIBLE,
                effects=tuple(extra_effects),
            )
        )
    else:
        extra = raw_record.extra_ability_description
        rules.append(
            _rule(
                "extra-ability:chain-ultimate",
                _source("extra-ability:chain-ultimate", EffectSourceType.ADDITIONAL_ABILITY, raw_record.extra_ability_name, extra),
                "额外能力：队伍需有击破或支援角色",
                extra,
                RuleEligibility.INELIGIBLE,
            )
        )

    if config.cinema_level >= 4:
        cinema4 = raw_record.mindscapes[3]
        c4_source = _source("cinema4:shield-crit-damage", EffectSourceType.CINEMA, cinema4.name, cinema4.description)
        c4_crit_damage = _number(cinema4.description, r"暴击伤害提升(?P<value>[\d.]+)%", "Evelyn Cinema 4 Crit Damage") / 100.0
        c4_condition = ScenarioConditionId(EVELYN_C4_SHIELD_ACTIVE)
        conditions.append(_condition(c4_condition, "当前持有4影护盾", cinema4.description, config.cinema4_shield_active))
        rules.append(
            _rule(
                "cinema4:shield-crit-damage",
                c4_source,
                f"4影：护盾持有期间暴击伤害+{c4_crit_damage:.0%}",
                cinema4.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema4:shield-crit-damage",
                        c4_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                        Resolved(c4_crit_damage),
                    ),
                ),
                condition_ids=(c4_condition,),
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId("unsupported:character:1321:cinema4:shield-trigger"),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message="连携技/终结技的护盾触发不模拟；仅选择当前护盾持有状态。",
                        blocking=False,
                        original_text=cinema4.description,
                    ),
                ),
            )
        )

    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        c6_source = _source("cinema6:shadow-edge", EffectSourceType.CINEMA, cinema6.name, cinema6.description)
        c6_condition = ScenarioConditionId(EVELYN_C6_SHADOW_EDGE_ACTIVE)
        conditions.append(_condition(c6_condition, "当前弦影绝锋状态生效", cinema6.description, config.cinema6_shadow_edge_active))
        extra_ratio = _number(cinema6.description, r"等同于伊芙琳(?P<value>[\d.]+)%攻击力", "Evelyn Cinema 6 Chain Extra Ratio") / 100.0
        c6_rule_id = RuleItemId("rule:character:1321:cinema6:shadow-edge")
        direct_template_ids = {
            item.ref.template_id
            for item in templates
            if isinstance(item, DirectDamageEventTemplate)
        }
        c6_effects = []
        for parent_index, entry in enumerate(entries):
            parent_template_id = entry.main_damage_event.template_id
            if (
                parent_template_id not in direct_template_ids
                or entry.move_id is None
                or entry.skill_group not in {
                    SkillGroup.BASIC_ATTACK,
                    SkillGroup.DODGE,
                    SkillGroup.SPECIAL_ATTACK,
                }
                or not (
                    DamageTag.BASIC_ATTACK in entry.damage_tags
                    or DamageTag.DASH_ATTACK in entry.damage_tags
                    or DamageTag.SPECIAL_ATTACK in entry.damage_tags
                    or DamageTag.EX_SPECIAL_ATTACK in entry.damage_tags
                )
            ):
                continue
            suffix = str(entry.entry_id).rsplit(":", 1)[-1]
            child_template_id = EventTemplateId(
                f"template:character:1321:cinema6-shadow-edge-child:{suffix}"
            )
            child_ref = DamageEventTemplateRef(
                template_id=child_template_id,
                semantic_id=DamageEventSemanticId(
                    f"event:character:1321:cinema6-shadow-edge-child:{suffix}"
                ),
                label="影画6：弦影追击（连携技伤害）",
                damage_type=DamageType.DIRECT,
                skill_group=SkillGroup.CHAIN_ATTACK,
                damage_tags=frozenset({DamageTag.CHAIN_ATTACK}),
                element=Element.FIRE,
                source_rule_item_id=c6_rule_id,
            )
            templates.append(
                DirectDamageEventTemplate(
                    ref=child_ref,
                    damage_dealer=EVELYN_ID,
                    element=Element.FIRE,
                    base_source=CurrentAttackValueSource(EVELYN_ID),
                    crit_rule=StandardCritRule(EVELYN_ID),
                    move_id=None,
                )
            )
            entries[parent_index] = replace(
                entry,
                derived_damage_events=(
                    *entry.derived_damage_events,
                    DerivedDamageEventTemplateRef(
                        template=child_ref,
                        multiplier=FixedMultiplier(Resolved(extra_ratio)),
                    ),
                ),
            )
            c6_effects.append(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            f"effect:character:1321:cinema6:shadow-edge-child:{suffix}"
                        ),
                        source=c6_source,
                        owner=EVELYN_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            DamageDealerFilter(EVELYN_ID),
                            EventTemplateIdFilter(parent_template_id),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=child_template_id,
                        unique_per_source_event=True,
                    ),
                )
            )
        c6_diagnostic = CalculationDiagnostic(
            diagnostic_id=DiagnosticId("unsupported:character:1321:cinema6:time-and-hit-cap"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message="弦影绝锋持续20秒且最多16次；当前状态下仅按所选单次招式生成一次追击，不模拟时长或历史触发数。",
            blocking=False,
            original_text=cinema6.description,
        )
        rules.append(
            _rule(
                "cinema6:shadow-edge",
                c6_source,
                f"6影：当前弦影绝锋状态下命中追加{extra_ratio:.0%}攻击力火属性连携伤害",
                cinema6.description,
                RuleEligibility.ELIGIBLE,
                effects=tuple(c6_effects),
                condition_ids=(c6_condition,),
                diagnostics=(c6_diagnostic,),
            )
        )
        standalone_ref = DamageEventTemplateRef(
            template_id=_C6_STANDALONE_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId("event:character:1321:cinema6-shadow-edge-single"),
            label="影画6：单次弦影追击（连携技伤害）",
            damage_type=DamageType.DIRECT,
            skill_group=SkillGroup.CHAIN_ATTACK,
            damage_tags=frozenset({DamageTag.CHAIN_ATTACK}),
            element=Element.FIRE,
        )
        templates.append(
            DirectDamageEventTemplate(
                ref=standalone_ref,
                damage_dealer=EVELYN_ID,
                element=Element.FIRE,
                base_source=CurrentAttackValueSource(EVELYN_ID),
                crit_rule=StandardCritRule(EVELYN_ID),
                move_id=None,
            )
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId("move-entry:character:1321:cinema6-shadow-edge-single"),
                character_id=EVELYN_ID,
                move_id=None,
                display_name=f"影画6：单次弦影追击（{extra_ratio:.0%}攻击力）",
                original_text=cinema6.description,
                skill_group=SkillGroup.CHAIN_ATTACK,
                damage_tags=standalone_ref.damage_tags,
                multiplier_relation=MultiplierRelation.COMPLETE,
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId("variant:character:1321:cinema6-shadow-edge-single"),
                        label=f"{extra_ratio:.2f}×当前攻击力",
                        parameter_name="影画6弦影追击倍率",
                        multiplier=FixedMultiplier(Resolved(extra_ratio)),
                    ),
                ),
                main_damage_event=standalone_ref,
            )
        )

    anomaly_entries, anomaly_templates, disorder_parameter = _static_fire_entries()
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)
    return build_definition(
        character_id=EVELYN_ID,
        role=CharacterRole.ATTACK,
        element=Element.FIRE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=tuple(entries),
        templates=tuple(templates),
        rules=tuple(rules),
        conditions=tuple(conditions),
        parameters=(disorder_parameter,),
        diagnostics=direct_diagnostics,
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(EVELYN_ID))


def _validate_raw(raw: NanokaRawRecord, config: EvelynCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Evelyn source and compile config IDs must match")
    if raw.name != "伊芙琳" or raw.code_name != "Evelyn":
        raise ValueError("unexpected Evelyn identity")
    if raw.specialty != "强攻" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("unexpected Evelyn role, element, or rank")
    if raw.faction != "天琴座" or raw.icon != "IconRole37":
        raise ValueError("unexpected Evelyn faction or icon")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1321.json":
        raise ValueError("Evelyn provenance must identify live Nanoka 3.2 character 1321")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Evelyn source must include seven cores and six mindscapes")
    if raw.potential_details:
        raise ValueError("Evelyn source has no Potential levels")


__all__ = ["compile_evelyn", "load_raw_record"]
