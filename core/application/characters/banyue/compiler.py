"""Compile BanYue's reviewed Nanoka source into static rupture contracts."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    AnyFilter,
    BattleEventKind,
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
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveIdFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    ScenarioParameterRangeCondition,
    ScenarioParameterDerivedValue,
    SnapshotRule,
    StandardCritRule,
    SkillGroup,
    Unresolved,
    UnresolvedEffect,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic
from ...ids import (
    DamageEventSemanticId,
    ScenarioParameterId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioConditionId,
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
    NanokaRawRecord,
    build_definition,
    effective_skill_level,
    raw_move_index,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import PenetrationDamageEventTemplate
from .config import BANYUE_ID, BanYueCompileConfig
from .reviewed import (
    BANYUE_BASIC_CUIYUE_MOVE_ID,
    BANYUE_BASIC_QINGSHAN_MOVE_ID,
    BANYUE_CORE_BUFF_ACTIVE,
    BANYUE_EX_SHANYAO_MOVE_ID,
    BANYUE_EX_SHANYAO_RAGE_MOVE_ID,
    BANYUE_EX_SHIZIHOU_MOVE_ID,
    BANYUE_EX_SHIZIHOU_RAGE_MOVE_ID,
    BANYUE_REVIEWED_MAPPING,
    BANYUE_TREMOR_ACTIVE,
)


BANYUE_MINGWANG_STACK_COUNT = ScenarioParameterId(
    "parameter:character:1471:mingwang-current-stacks"
)
BANYUE_CUIYUE_FOLLOWUP_RULE = RuleItemId(
    "rule:character:1471:skill:cuiyue-qingshan-followup"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _validate_raw(raw: NanokaRawRecord, config: BanYueCompileConfig) -> None:
    if raw.character_id != BANYUE_ID:
        raise ValueError("raw character does not match BanYue")
    if (
        raw.name != "般岳"
        or raw.code_name != "BanYue"
        or raw.rarity != 4
        or raw.specialty != "命破"
        or raw.element != "火属性"
        or raw.faction != "坎卜斯黑枝"
        or raw.icon != "IconRole53"
    ):
        raise ValueError("raw character identity does not match reviewed BanYue source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1471.json"
    ):
        raise ValueError("raw BanYue source provenance does not match Nanoka live3.2")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("raw BanYue record must contain seven Core levels and six cinemas")
    required = {spec.source_name for spec in BANYUE_REVIEWED_MAPPING.moves}
    available = {item.name for item in raw.moves}
    missing = required - available
    if missing:
        raise ValueError(f"raw BanYue record is missing reviewed moves: {sorted(missing)}")
    if not 1 <= config.core_level <= len(raw.core_levels):
        raise ValueError("configured BanYue Core level is not available in raw source")


def _source(
    key: str,
    kind: EffectSourceType,
    label: str,
    text: str,
) -> RuleSource:
    return source_for(BANYUE_ID, key, kind, label, text)


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
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1471:{key}"),
        owner=BANYUE_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
    )


def _modifier(
    key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1471:{key}"),
            source=source,
            owner=BANYUE_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    source_text: str,
    *,
    value: bool = False,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=source_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _typed_template(
    *,
    key: str,
    label: str,
    move_id,
    skill_group,
    damage_tags,
    source_rule_item_id: RuleItemId | None = None,
) -> PenetrationDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1471:{key}"),
        semantic_id=DamageEventSemanticId(f"event:character:1471:{key}"),
        label=label,
        damage_type=DamageType.PENETRATION,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=Element.FIRE,
        source_rule_item_id=source_rule_item_id,
    )
    return PenetrationDamageEventTemplate(
        ref=ref,
        damage_dealer=BANYUE_ID,
        element=Element.FIRE,
        base_source=CurrentPenetrationForceValueSource(BANYUE_ID),
        crit_rule=StandardCritRule(BANYUE_ID),
        move_id=move_id,
    )


def _compile_moves(raw: NanokaRawRecord, config: BanYueCompileConfig):
    raw_moves = raw_move_index(raw)
    entries: list[MoveCalculationEntry] = []
    templates: list[PenetrationDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    derived_refs: list[DerivedDamageEventTemplateRef] = []

    for spec in BANYUE_REVIEWED_MAPPING.moves:
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
                f"{BANYUE_ID}:{spec.entry_key}",
                entry_diagnostics,
                source_skill_id=parameter_spec.source_skill_id,
                source_skill_components=parameter_spec.source_skill_components,
            )
            variants.append(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1471:{spec.entry_key}:damage"
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

        template = _typed_template(
            key=f"{spec.entry_key}:main",
            label=spec.display_name,
            move_id=spec.move_id,
            skill_group=spec.skill_group,
            damage_tags=spec.damage_tags,
        )
        derived_events: tuple[DerivedDamageEventTemplateRef, ...] = ()
        if spec.entry_key == "basic-cuiyue":
            # 摧岳 explicitly auto-releases 普通攻击：倾山. Keep the child event's
            # own Basic identity and source multiplier; do not copy parent metadata.
            followup = _typed_template(
                key="basic-cuiyue-auto-qingshan",
                label="摧岳后自动释放：普通攻击·倾山",
                move_id=BANYUE_BASIC_QINGSHAN_MOVE_ID,
                skill_group=SkillGroup.BASIC_ATTACK,
                damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
                source_rule_item_id=BANYUE_CUIYUE_FOLLOWUP_RULE,
            )
            followup_raw = raw_moves["普通攻击：倾山"]
            followup_diagnostics: list[CalculationDiagnostic] = []
            followup_multiplier = raw_multiplier(
                raw_moves,
                followup_raw.name,
                "伤害倍率",
                effective_skill_level(config, spec.skill_group),
                f"{BANYUE_ID}:basic-cuiyue-auto-qingshan",
                followup_diagnostics,
                source_skill_id="1471009",
            )
            derived = DerivedDamageEventTemplateRef(
                template=followup.ref,
                multiplier=(
                    followup_multiplier
                    if isinstance(followup_multiplier, Unresolved)
                    else FixedMultiplier(Resolved(followup_multiplier))
                ),
            )
            templates.append(followup)
            # This derived child has its own source-authored MoveId and Basic
            # identity. Keep it in the independent-derived registry, whose
            # contract permits an explicit child MoveId, rather than treating
            # it as an identity-less child of the selected 摧岳 entry.
            derived_refs.append(derived)
            diagnostics.extend(followup_diagnostics)

        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(f"move-entry:character:1471:{spec.entry_key}"),
                character_id=BANYUE_ID,
                move_id=spec.move_id,
                display_name=spec.display_name,
                original_text=raw_move.description or spec.source_name,
                skill_group=spec.skill_group,
                damage_tags=spec.damage_tags,
                multiplier_relation=spec.multiplier_relation,
                multiplier_variants=tuple(variants),
                main_damage_event=template.ref,
                derived_damage_events=derived_events,
                stage_index=spec.stage_index,
                condition_ids=tuple(spec.condition_ids),
                diagnostics=tuple(entry_diagnostics),
            )
        )
        templates.append(template)
        diagnostics.extend(entry_diagnostics)

    return entries, templates, diagnostics, derived_refs, raw_moves


def _event_creation_effect(
    *,
    key: str,
    source: RuleSource,
    parent_template_id: EventTemplateId,
    child_template_id: EventTemplateId,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1471:{key}"),
            source=source,
            owner=BANYUE_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.PENETRATION),
                DamageDealerFilter(BANYUE_ID),
                EventTemplateIdFilter(parent_template_id),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=child_template_id,
            unique_per_source_event=True,
        ),
    )


def _move_filter(*move_ids):
    return AnyFilter(tuple(MoveIdFilter(move_id) for move_id in move_ids))


_CUIYUE_QINGSHAN_FOLLOWUP_TEMPLATE_ID = EventTemplateId(
    "template:character:1471:basic-cuiyue-auto-qingshan"
)


def _move_or_cuiyue_qingshan_followup_filter(*move_ids):
    return AnyFilter(
        (
            *(MoveIdFilter(move_id) for move_id in move_ids),
            EventTemplateIdFilter(_CUIYUE_QINGSHAN_FOLLOWUP_TEMPLATE_ID),
        )
    )


def compile_banyue(
    config: BanYueCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, diagnostics, derived_refs, raw_moves = _compile_moves(
        raw_record, config
    )

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    cinema_sources = {
        item.level: _source(
            f"cinema{item.level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for item in raw_record.mindscapes
    }
    cinema = {item.level: item for item in raw_record.mindscapes}

    conditions = [
        _condition(
            BANYUE_CORE_BUFF_ACTIVE,
            "本次贯穿伤害在般岳发动强化特殊技或支援突击后30秒内",
            core.description,
        ),
        _condition(
            BANYUE_TREMOR_ACTIVE,
            "目标当前处于般岳的[战栗]状态",
            cinema[1].description,
        ),
    ]
    rules: list[CalculationRuleItem] = []

    max_hp_force_ratio = _number(
        core.description,
        r"每1点最大生命值将提高(?P<value>[\d.]+)点贯穿力",
        "BanYue Core max-HP penetration-force coefficient",
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
                        source_character_id=BANYUE_ID,
                        source_node=CalculationNode.CHARACTER_CURRENT_MAX_HP,
                        coefficient=Resolved(max_hp_force_ratio),
                    ),
                    target=EffectTarget.SELF,
                    filters=(DamageTypeFilter(DamageType.PENETRATION),),
                ),
            ),
        )
    )

    core_force_bonus = _number(
        core.description,
        r"\[强化特殊技\]或\[支援突击\]时，贯穿力提升(?P<value>[\d.]+)点",
        "BanYue Core post-EX/assist penetration-force bonus",
    )
    core_fire_bonus = _number(
        core.description,
        r"造成的火属性伤害提升(?P<value>[\d.]+)%",
        "BanYue Core post-EX/assist Fire-damage bonus",
    ) / 100.0
    core_crit_damage_bonus = _number(
        core.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "BanYue Core post-EX/assist critical-damage bonus",
    ) / 100.0
    core_active = (BANYUE_CORE_BUFF_ACTIVE,)
    core_eligibility = RuleEligibility.ELIGIBLE
    core_effects = (
        _modifier(
            "core:enhanced-special-assist-penetration-force",
            core_source,
            CalculationNode.PENETRATION_FORCE_BONUS,
            Resolved(core_force_bonus),
            target=EffectTarget.SELF,
            filters=(
                DamageDealerFilter(BANYUE_ID),
                DamageTypeFilter(DamageType.PENETRATION),
            ),
        ),
        _modifier(
            "core:enhanced-special-assist-fire-damage",
            core_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(core_fire_bonus),
            target=EffectTarget.SELF,
            filters=(
                DamageDealerFilter(BANYUE_ID),
                DamageTypeFilter(DamageType.PENETRATION),
                ElementFilter(Element.FIRE),
            ),
        ),
        _modifier(
            "core:enhanced-special-assist-crit-damage",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            Resolved(core_crit_damage_bonus),
            target=EffectTarget.SELF,
        ),
    )
    rules.append(
        _rule(
            "core:enhanced-special-assist-buffs",
            core_source,
            "核心被动：强化特殊技/支援突击触发的30秒增益",
            core.description,
            core_eligibility,
            condition_ids=core_active,
            effects=core_effects,
        )
    )

    mingwang_base_bonus = _number(
        core.extra_ability_description,
        r"每层\[明王\]会使自身造成的火属性伤害提升(?P<value>[\d.]+)%",
        "BanYue additional-ability Mingwang Fire-damage bonus per stack",
    ) / 100.0
    mingwang_max_stacks = int(
        _number(
            core.extra_ability_description,
            r"最多叠加(?P<value>\d+)层",
            "BanYue additional-ability Mingwang stack cap",
        )
    )
    c6_bonus = _number(
        cinema[6].description,
        r"\[明王\]提供的火属性伤害增益效果额外提升(?P<value>[\d.]+)%",
        "BanYue Cinema 6 Mingwang Fire-damage increase per stack",
    ) / 100.0
    mingwang_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    mingwang_stacks = ScenarioIntegerParameter(
        parameter_id=BANYUE_MINGWANG_STACK_COUNT,
        label=f"般岳当前[明王]层数（0–{mingwang_max_stacks}层）",
        original_text=core.extra_ability_description,
        resolution=ParameterResolution.USER_SELECTED,
        value=mingwang_max_stacks,
        minimum=0,
        maximum=mingwang_max_stacks,
    )
    mingwang_available = config.additional_ability_eligible or config.cinema_level >= 6
    rules.append(
        _rule(
            "extra-ability:mingwang-fire-damage",
            extra_source,
            "额外能力/6影：[明王]层数对应火伤增益",
            core.extra_ability_description,
            mingwang_eligibility,
            effects=(
                _modifier(
                    "extra-ability:mingwang-fire-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(BANYUE_MINGWANG_STACK_COUNT),
                        coefficient=Resolved(mingwang_base_bonus),
                        cap_max=Resolved(
                            mingwang_base_bonus * mingwang_max_stacks
                        ),
                    ),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(BANYUE_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.FIRE),
                    ),
                ),
            ),
        )
    )

    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    cinema6_mingwang_effects = [
        _modifier(
            "cinema6:mingwang-fire-damage-increase",
            cinema_sources[6],
            CalculationNode.DAMAGE_NORMAL_BONUS,
            ScenarioParameterDerivedValue(
                parameter_id=str(BANYUE_MINGWANG_STACK_COUNT),
                coefficient=Resolved(c6_bonus),
                cap_max=Resolved(c6_bonus * mingwang_max_stacks),
            ),
            target=EffectTarget.SELF,
            filters=(
                DamageDealerFilter(BANYUE_ID),
                DamageTypeFilter(DamageType.PENETRATION),
                ElementFilter(Element.FIRE),
            ),
        )
    ]
    if config.cinema_level >= 6 and not config.additional_ability_eligible:
        cinema6_mingwang_effects.append(
            UnresolvedEffect(
                rule=EffectRule(
                    effect_id=EffectId(
                        "effect:character:1471:cinema6:mingwang-base-bonus-eligibility"
                    ),
                    source=cinema_sources[6],
                    owner=BANYUE_ID,
                    target=EffectTarget.SELF,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    condition=ScenarioParameterRangeCondition(
                        str(BANYUE_MINGWANG_STACK_COUNT), minimum=1
                    ),
                    filters=(
                        DamageDealerFilter(BANYUE_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.FIRE),
                    ),
                ),
                unresolved=Unresolved(
                    reason=UnresolvedReason.AMBIGUOUS_TEXT,
                    notes=(
                        "Cinema 6 explicitly permits any-time EX to grant Mingwang and adds 8% Fire damage per stack. "
                        "The 5% base bonus is described under Extra Ability, whose support/stun-team condition may still apply; "
                        "the source does not state whether Cinema 6 bypasses that condition. Keep this base component unresolved "
                        "for C6-only eligibility while retaining the explicit 8% C6 bonus."
                    ),
                    original_text=core.extra_ability_description + "\n" + cinema[6].description,
                ),
            )
        )
    rules.append(
        _rule(
            "cinema6:mingwang-fire-damage-increase",
            cinema_sources[6],
            "6影：[明王]每层火伤增益额外提升",
            cinema[6].description,
            c6_eligibility,
            effects=tuple(cinema6_mingwang_effects),
        )
    )

    c1 = cinema[1]
    c1_source = cinema_sources[1]
    c1_resistance_reduction = _number(
        c1.description,
        r"火属性伤害抗性降低(?P<value>[\d.]+)%",
        "BanYue Cinema 1 Fire resistance reduction",
    ) / 100.0
    c1_damage_bonus = _number(
        c1.description,
        r"造成的贯穿伤害提高(?P<value>[\d.]+)%",
        "BanYue Cinema 1 Tremor-target damage bonus",
    ) / 100.0
    c1_moves = _move_or_cuiyue_qingshan_followup_filter(
        BANYUE_EX_SHIZIHOU_MOVE_ID,
        BANYUE_EX_SHIZIHOU_RAGE_MOVE_ID,
        BANYUE_EX_SHANYAO_MOVE_ID,
        BANYUE_EX_SHANYAO_RAGE_MOVE_ID,
        BANYUE_BASIC_QINGSHAN_MOVE_ID,
        BANYUE_BASIC_CUIYUE_MOVE_ID,
    )
    c1_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 1
        else RuleEligibility.INELIGIBLE
    )
    rules.extend(
        (
            _rule(
                "cinema1:tremor-fire-resistance-reduction",
                c1_source,
                "1影：[战栗]期间火属性抗性降低",
                c1.description,
                c1_eligibility,
                condition_ids=(BANYUE_TREMOR_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema1:tremor-fire-resistance-reduction",
                        c1_source,
                        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                        Resolved(c1_resistance_reduction),
                        target=EffectTarget.ENEMY,
                        filters=(ElementFilter(Element.FIRE),),
                    ),
                ),
            ),
            _rule(
                "cinema1:tremor-listed-move-penetration-damage",
                c1_source,
                "1影：[战栗]目标上的指定贯穿伤害提升",
                c1.description,
                c1_eligibility,
                condition_ids=(BANYUE_TREMOR_ACTIVE,),
                effects=(
                    _modifier(
                        "cinema1:tremor-listed-move-penetration-damage",
                        c1_source,
                        CalculationNode.PENETRATION_DAMAGE_BONUS,
                        Resolved(c1_damage_bonus),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageDealerFilter(BANYUE_ID),
                            DamageTypeFilter(DamageType.PENETRATION),
                            ElementFilter(Element.FIRE),
                            c1_moves,
                        ),
                    ),
                ),
            ),
        )
    )

    c2 = cinema[2]
    c2_source = cinema_sources[2]
    c2_fire_bonus = _number(
        c2.description,
        r"火属性伤害增益效果额外提升(?P<value>[\d.]+)%",
        "BanYue Cinema 2 Core Fire-damage-buff increase",
    ) / 100.0
    c2_crit_bonus = _number(
        c2.description,
        r"暴击伤害增益效果额外提升(?P<value>[\d.]+)%",
        "BanYue Cinema 2 Core critical-damage-buff increase",
    ) / 100.0
    c2_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 2
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema2:core-buff-increase",
            c2_source,
            "2影：核心火伤与暴击伤害增益额外提升",
            c2.description,
            c2_eligibility,
            condition_ids=core_active,
            effects=(
                _modifier(
                    "cinema2:core-fire-damage-buff-increase",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c2_fire_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(BANYUE_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.FIRE),
                    ),
                ),
                _modifier(
                    "cinema2:core-critical-damage-buff-increase",
                    c2_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c2_crit_bonus),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )

    c4 = cinema[4]
    c4_source = cinema_sources[4]
    c4_damage_bonus = _number(
        c4.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "BanYue Cinema 4 listed-move damage increase",
    ) / 100.0
    c4_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 4
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema4:listed-move-damage",
            c4_source,
            "4影：狮子吼·怒/山摇·怒/倾山/摧岳增伤",
            c4.description,
            c4_eligibility,
            effects=(
                _modifier(
                    "cinema4:listed-move-damage",
                    c4_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c4_damage_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(BANYUE_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.FIRE),
                        _move_or_cuiyue_qingshan_followup_filter(
                            BANYUE_EX_SHIZIHOU_RAGE_MOVE_ID,
                            BANYUE_EX_SHANYAO_RAGE_MOVE_ID,
                            BANYUE_BASIC_QINGSHAN_MOVE_ID,
                            BANYUE_BASIC_CUIYUE_MOVE_ID,
                        ),
                    ),
                ),
            ),
        )
    )

    # 摧岳's authored follow-up is a new Basic event with its own source move,
    # multiplier, skill group, and tag. The effect links it only to 摧岳's event.
    cuiyue_entry = next(
        item for item in entries if item.move_id == BANYUE_BASIC_CUIYUE_MOVE_ID
    )
    qingshan_child = next(
        item
        for item in templates
        if item.ref.template_id
        == EventTemplateId("template:character:1471:basic-cuiyue-auto-qingshan")
    )
    followup_source = _source(
        "skill:cuiyue-qingshan-followup",
        EffectSourceType.SKILL,
        "普通攻击：摧岳自动释放普通攻击：倾山",
        cuiyue_entry.original_text,
    )
    rules.append(
        _rule(
            "skill:cuiyue-qingshan-followup",
            followup_source,
            "摧岳后自动释放独立的普通攻击：倾山事件",
            cuiyue_entry.original_text,
            RuleEligibility.ELIGIBLE,
            effects=(
                _event_creation_effect(
                    key="skill:cuiyue-qingshan-followup",
                    source=followup_source,
                    parent_template_id=cuiyue_entry.main_damage_event.template_id,
                    child_template_id=qingshan_child.ref.template_id,
                ),
            ),
        )
    )

    c6 = cinema[6]
    c6_source = cinema_sources[6]
    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    c6_force_ratio = _number(
        c6.description,
        r"等同于自身(?P<value>[\d.]+)%贯穿力的火属性伤害",
        "BanYue Cinema 6 摧岳 Fire penetration-force damage multiplier",
    ) / 100.0
    c6_template = _typed_template(
        key="cinema6-cuiyue-fire-burst",
        label="6影：普通攻击·摧岳追加周身火属性伤害",
        move_id=None,
        skill_group=None,
        damage_tags=frozenset(),
        source_rule_item_id=RuleItemId("rule:character:1471:cinema6:cuiyue-fire-burst"),
    )
    c6_derived = DerivedDamageEventTemplateRef(
        template=c6_template.ref,
        multiplier=FixedMultiplier(Resolved(c6_force_ratio)),
    )
    templates.append(c6_template)
    derived_refs.append(c6_derived)
    rules.append(
        _rule(
            "cinema6:cuiyue-fire-burst",
            c6_source,
            "6影：摧岳追加600%贯穿力周身火属性伤害",
            c6.description,
            c6_eligibility,
            effects=(
                _event_creation_effect(
                    key="cinema6:cuiyue-fire-burst",
                    source=c6_source,
                    parent_template_id=cuiyue_entry.main_damage_event.template_id,
                    child_template_id=c6_template.ref.template_id,
                ),
            ),
        )
    )

    return build_definition(
        character_id=BANYUE_ID,
        role=CharacterRole.RUPTURE,
        element=Element.FIRE,
        source=source_for(
            BANYUE_ID,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(mingwang_stacks,) if mingwang_available else (),
        independent_derived_damage_events=derived_refs,
        diagnostics=diagnostics,
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(BANYUE_ID))


__all__ = [
    "BANYUE_MINGWANG_STACK_COUNT",
    "compile_banyue",
    "load_raw_record",
]
