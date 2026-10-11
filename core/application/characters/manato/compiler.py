"""Compile Manato's reviewed Nanoka source into static damage contracts."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    CurrentPenetrationForceValueSource,
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
    DerivedDamageEventTemplateRef,
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
    NanokaDamageParameterSpec,
    NanokaMoveSpec,
    NanokaRawRecord,
    build_definition,
    effective_skill_level,
    raw_multiplier,
    raw_move_index,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import DirectDamageEventTemplate, PenetrationDamageEventTemplate
from .config import MANATO_ID, ManatoCompileConfig
from .reviewed import (
    MANATO_EMBER_EDGE_ACTIVE,
    MANATO_EMPOWERED_BASIC_MOVE_ID,
    MANATO_HP_SPENDING_ATTACK_ACTIVE,
    MANATO_REVIEWED_MAPPING,
    MANATO_SPECIAL_ENHANCED_ACTIVE,
    MANATO_SPECIAL_STANDARD_ACTIVE,
    MANATO_SUPPORT_FOLLOWUP_MAX_ACTIVE,
    MANATO_SUPPORT_FOLLOWUP_MOVE_ID,
    MANATO_SUPPORT_FOLLOWUP_STANDARD_ACTIVE,
)


MANATO_C1_ACCUMULATED_HP_LOSS_BASIS_POINTS = ScenarioParameterId(
    "parameter:character:1441:cinema1:accumulated-hp-loss-basis-points"
)
MANATO_C6_FIRE_DAMAGE_STACKS = ScenarioParameterId(
    "parameter:character:1441:cinema6:fire-damage-stacks"
)
MANATO_SUPPORT_FOLLOWUP_CONTINUOUS_RULE = RuleItemId(
    "rule:character:1441:skill:support-follow-up-continuous-slashes"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _first_number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group(1))


def _validate_raw(raw: NanokaRawRecord, config: ManatoCompileConfig) -> None:
    if raw.character_id != MANATO_ID:
        raise ValueError("raw character does not match Manato")
    if (
        raw.name != "真斗"
        or raw.code_name != "Manato"
        or raw.rarity != 3
        or raw.specialty != "命破"
        or raw.element != "火属性"
        or raw.faction != "怪啖屋"
        or raw.icon != "IconRole51"
    ):
        raise ValueError("raw character identity does not match reviewed Manato source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("raw Manato record must contain seven Core levels and six cinemas")
    required = {spec.source_name for spec in MANATO_REVIEWED_MAPPING.moves}
    available = {item.name for item in raw.moves}
    missing = required - available
    if missing:
        raise ValueError(f"raw Manato record is missing reviewed moves: {sorted(missing)}")
    if not 1 <= config.core_level <= len(raw.core_levels):
        raise ValueError("configured Manato Core level is not available in raw source")


def _source(
    key: str,
    kind: EffectSourceType,
    label: str,
    text: str,
) -> RuleSource:
    return source_for(MANATO_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1441:{key}"),
        owner=MANATO_ID,
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
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1441:{key}"),
            source=source,
            owner=MANATO_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _user_condition(
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


def _template_for(spec: NanokaMoveSpec) -> DirectDamageEventTemplate | PenetrationDamageEventTemplate:
    damage_type = (
        DamageType.DIRECT if spec.element is Element.PHYSICAL else DamageType.PENETRATION
    )
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(
            f"template:character:1441:{spec.entry_key}:main"
        ),
        semantic_id=DamageEventSemanticId(
            f"event:character:1441:{spec.entry_key}:main"
        ),
        label=spec.display_name,
        damage_type=damage_type,
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        element=spec.element,
    )
    if damage_type is DamageType.DIRECT:
        return DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=MANATO_ID,
            element=spec.element,
            base_source=CurrentAttackValueSource(MANATO_ID),
            crit_rule=StandardCritRule(MANATO_ID),
            move_id=spec.move_id,
        )
    return PenetrationDamageEventTemplate(
        ref=ref,
        damage_dealer=MANATO_ID,
        element=spec.element,
        base_source=CurrentPenetrationForceValueSource(MANATO_ID),
        crit_rule=StandardCritRule(MANATO_ID),
        move_id=spec.move_id,
    )


def _compile_moves(raw: NanokaRawRecord, config: ManatoCompileConfig):
    raw_moves = raw_move_index(raw)
    entries: list[MoveCalculationEntry] = []
    templates: list[DirectDamageEventTemplate | PenetrationDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []

    for spec in MANATO_REVIEWED_MAPPING.moves:
        raw_move = raw_moves.get(spec.source_name)
        if raw_move is None:
            raise ValueError(f"Manato raw source is missing {spec.source_name!r}")
        level = effective_skill_level(config, spec.skill_group)
        variants: list[MultiplierVariant] = []
        entry_diagnostics: list[CalculationDiagnostic] = []
        for parameter_spec in spec.parameters:
            multiplier = raw_multiplier(
                raw_moves,
                spec.source_name,
                parameter_spec.parameter_name,
                level,
                f"{MANATO_ID}:{spec.entry_key}",
                entry_diagnostics,
                source_skill_id=parameter_spec.source_skill_id,
                source_skill_components=parameter_spec.source_skill_components,
            )
            variants.append(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1441:{spec.entry_key}:{parameter_spec.variant_key}"
                    ),
                    label=(
                        "连打模式起手斩击倍率"
                        if parameter_spec.variant_key == "continuous-max-total"
                        else parameter_spec.parameter_name
                    ),
                    parameter_name=parameter_spec.parameter_name,
                    multiplier=(
                        multiplier
                        if isinstance(multiplier, Unresolved)
                        else FixedMultiplier(Resolved(multiplier))
                    ),
                    condition_ids=tuple(parameter_spec.condition_ids),
                    repeat_count=parameter_spec.repeat_count,
                )
            )

        derived_events: tuple[DerivedDamageEventTemplateRef, ...] = ()
        if spec.entry_key == "support-follow-up-breaking-fang":
            continuous_multiplier = raw_multiplier(
                raw_moves,
                spec.source_name,
                "连打最大伤害倍率",
                level,
                f"{MANATO_ID}:support-follow-up-continuous-slashes",
                entry_diagnostics,
                source_skill_id="1441025",
            )
            continuous_ref = DamageEventTemplateRef(
                template_id=EventTemplateId(
                    "template:character:1441:support-follow-up-continuous-slashes"
                ),
                semantic_id=DamageEventSemanticId(
                    "event:character:1441:support-follow-up-continuous-slashes"
                ),
                label="支援突击：连斩最大追加伤害",
                damage_type=DamageType.PENETRATION,
                skill_group=spec.skill_group,
                damage_tags=spec.damage_tags,
                element=Element.FIRE,
                source_rule_item_id=MANATO_SUPPORT_FOLLOWUP_CONTINUOUS_RULE,
            )
            continuous_template = PenetrationDamageEventTemplate(
                ref=continuous_ref,
                damage_dealer=MANATO_ID,
                element=Element.FIRE,
                base_source=CurrentPenetrationForceValueSource(MANATO_ID),
                crit_rule=StandardCritRule(MANATO_ID),
                move_id=None,
            )
            templates.append(continuous_template)
            derived_events = (
                DerivedDamageEventTemplateRef(
                    template=continuous_ref,
                    multiplier=(
                        continuous_multiplier
                        if isinstance(continuous_multiplier, Unresolved)
                        else FixedMultiplier(Resolved(continuous_multiplier))
                    ),
                ),
            )

        template = _template_for(spec)
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(
                    f"move-entry:character:1441:{spec.entry_key}"
                ),
                character_id=MANATO_ID,
                move_id=spec.move_id,
                display_name=spec.display_name,
                original_text=raw_move.description or spec.source_name,
                skill_group=spec.skill_group,
                damage_tags=spec.damage_tags,
                multiplier_relation=spec.multiplier_relation,
                multiplier_variants=tuple(variants),
                main_damage_event=template.ref,
                condition_ids=tuple(spec.condition_ids),
                stage_index=spec.stage_index,
                derived_damage_events=derived_events,
                diagnostics=tuple(entry_diagnostics),
            )
        )
        templates.append(template)
        diagnostics.extend(entry_diagnostics)

    return tuple(entries), tuple(templates), tuple(diagnostics)


def compile_manato(
    config: ManatoCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, diagnostics = _compile_moves(raw_record, config)
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    c1, c2, c3, c4, c5, c6 = raw_record.mindscapes
    sources = {
        item.level: _source(
            f"cinema{item.level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for item in raw_record.mindscapes
    }

    conditions = (
        _user_condition(
            MANATO_EMBER_EDGE_ACTIVE,
            "真斗当前处于熔锋状态",
            core.description,
        ),
        _user_condition(
            MANATO_HP_SPENDING_ATTACK_ACTIVE,
            "本次炽风·胧切或支援突击在当前生命值高于30%时实际消耗了生命值",
            core.description,
        ),
        _user_condition(
            MANATO_SPECIAL_STANDARD_ACTIVE,
            "本次特殊技：归烬为普通斩击",
            next(
                item.description
                for item in raw_record.moves
                if item.name == "特殊技：归烬"
            ),
            value=True,
        ),
        _user_condition(
            MANATO_SPECIAL_ENHANCED_ACTIVE,
            "本次特殊技：归烬为蓄力或格挡成功强化斩击",
            next(
                item.description
                for item in raw_record.moves
                if item.name == "特殊技：归烬"
            ),
        ),
        _user_condition(
            MANATO_SUPPORT_FOLLOWUP_STANDARD_ACTIVE,
            "本次支援突击采用单次伤害倍率",
            next(item.description for item in raw_record.moves if item.name == "支援突击：孤影·断獠"),
            value=True,
        ),
        _user_condition(
            MANATO_SUPPORT_FOLLOWUP_MAX_ACTIVE,
            "本次支援突击采用连打最大总倍率",
            next(item.description for item in raw_record.moves if item.name == "支援突击：孤影·断獠"),
        ),
    )

    rules: list[CalculationRuleItem] = []
    core_force_coefficient = _number(
        core.description,
        r"每1点最大生命值将提高(?P<value>[\d.]+)点贯穿力",
        "Manato Core penetration-force coefficient",
    )
    core_force = PanelStatDerivedValue(
        source_character_id=MANATO_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_MAX_HP,
        coefficient=Resolved(core_force_coefficient),
    )
    rules.append(
        _rule(
            "core:extra-penetration-force-from-current-max-hp",
            core_source,
            "核心被动：按当前最大生命值增加贯穿力",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:extra-penetration-force-from-current-max-hp",
                    core_source,
                    CalculationNode.PENETRATION_FORCE_BONUS,
                    core_force,
                    target=EffectTarget.SELF,
                    filters=(DamageTypeFilter(DamageType.PENETRATION),),
                ),
            ),
        )
    )

    core_ember_crit_rate = _number(
        core.description,
        r"\[熔锋\]状态下.*?暴击率提升(?P<value>[\d.]+)%",
        "Manato Core Ember Edge Crit Rate bonus",
    ) / 100.0
    core_ember_fire_bonus = _number(
        core.description,
        r"火属性伤害提升(?P<value>[\d.]+)%",
        "Manato Core Ember Edge Fire damage bonus",
    ) / 100.0
    ember_eligibility = RuleEligibility.ELIGIBLE
    rules.extend(
        (
            _rule(
                "core:ember-edge-crit-rate",
                core_source,
                "核心被动：熔锋状态暴击率提升",
                core.description,
                ember_eligibility,
                condition_ids=(MANATO_EMBER_EDGE_ACTIVE,),
                effects=(
                    _modifier(
                        "core:ember-edge-crit-rate",
                        core_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                        Resolved(core_ember_crit_rate),
                        target=EffectTarget.SELF,
                    ),
                ),
            ),
            _rule(
                "core:ember-edge-fire-damage",
                core_source,
                f"核心被动：熔锋状态火伤提升{core_ember_fire_bonus:.1%}",
                core.description,
                ember_eligibility,
                condition_ids=(MANATO_EMBER_EDGE_ACTIVE,),
                effects=(
                    _modifier(
                        "core:ember-edge-fire-damage",
                        core_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(core_ember_fire_bonus),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageTypeFilter(DamageType.PENETRATION),
                            ElementFilter(Element.FIRE),
                        ),
                    ),
                ),
            ),
        )
    )

    hp_cost_crit_damage = _number(
        core.description,
        r"消耗生命值时，使此次攻击的暴击伤害提升(?P<value>[\d.]+)%",
        "Manato Core HP-spending attack Crit Damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "core:hp-spending-attack-crit-damage",
            core_source,
            f"核心被动：本次消耗生命值的炽风·胧切/支援突击暴伤提升{hp_cost_crit_damage:.1%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(MANATO_HP_SPENDING_ATTACK_ACTIVE,),
            effects=(
                _modifier(
                    "core:hp-spending-attack-crit-damage",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(hp_cost_crit_damage),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.FIRE),
                        AnyFilter(
                            (
                                MoveIdFilter(MANATO_EMPOWERED_BASIC_MOVE_ID),
                                EventTemplateIdFilter(
                                    EventTemplateId(
                                        "template:character:1441:support-follow-up-continuous-slashes"
                                    )
                                ),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    support_entry = next(
        item
        for item in entries
        if item.entry_id
        == MoveEntryId("move-entry:character:1441:support-follow-up-breaking-fang")
    )
    support_followup_source = _source(
        "skill:support-follow-up-continuous-slashes",
        EffectSourceType.SKILL,
        "支援突击：连斩",
        next(
            item.description
            for item in raw_record.moves
            if item.name == "支援突击：孤影·断獠"
        ),
    )
    rules.append(
        _rule(
            "skill:support-follow-up-continuous-slashes",
            support_followup_source,
            "连打最大倍率：创建独立连续斩击事件",
            support_followup_source.raw_text or "",
            RuleEligibility.ELIGIBLE,
            condition_ids=(MANATO_SUPPORT_FOLLOWUP_MAX_ACTIVE,),
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1441:skill:support-follow-up-continuous-slashes"
                        ),
                        source=support_followup_source,
                        owner=MANATO_ID,
                        target=EffectTarget.SELF,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            DamageTypeFilter(DamageType.PENETRATION),
                            DamageDealerFilter(MANATO_ID),
                            EventTemplateIdFilter(
                                support_entry.main_damage_event.template_id
                            ),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=EventTemplateId(
                            "template:character:1441:support-follow-up-continuous-slashes"
                        ),
                        unique_per_source_event=True,
                    ),
                ),
            ),
        )
    )

    c1_per_hp_step = _first_number(
        c1.description,
        r"每有相当于最大生命值([\d.]+)%的已损失生命值",
        "Manato Cinema 1 accumulated HP-loss step",
    )
    c1_per_step_bonus = _number(
        c1.description,
        r"已损失生命值使.*?火属性伤害提升(?P<value>[\d.]+)%",
        "Manato Cinema 1 damage bonus per HP-loss step",
    ) / 100.0
    c1_max_bonus = _number(
        c1.description,
        r"最多提升(?P<value>[\d.]+)%",
        "Manato Cinema 1 damage-bonus cap",
    ) / 100.0
    c1_max_hp_loss_percent = int(round(c1_max_bonus / c1_per_step_bonus * c1_per_hp_step))
    c1_max_hp_loss_basis_points = c1_max_hp_loss_percent * 100
    c1_parameter = ScenarioIntegerParameter(
        parameter_id=MANATO_C1_ACCUMULATED_HP_LOSS_BASIS_POINTS,
        label="影画1：历史累计已损失最大生命值（0.01%单位）",
        original_text=(
            "选择历史累计已损失最大生命值的百分点（每单位0.01%最大生命值）；"
            "不是当前生命值比例，也不由当前生命值推算；"
            f"范围0–{c1_max_hp_loss_basis_points}对应原文增伤上限。"
        ),
        resolution=ParameterResolution.USER_SELECTED,
        value=None,
        minimum=0,
        maximum=c1_max_hp_loss_basis_points,
    )
    c1_effect = _modifier(
        "cinema1:accumulated-hp-loss-fire-damage",
        sources[1],
        CalculationNode.DAMAGE_NORMAL_BONUS,
        ScenarioParameterDerivedValue(
            parameter_id=str(MANATO_C1_ACCUMULATED_HP_LOSS_BASIS_POINTS),
            coefficient=Resolved(c1_per_step_bonus / (c1_per_hp_step * 100)),
            cap_max=Resolved(c1_max_bonus),
        ),
        target=EffectTarget.SELF,
        filters=(
            DamageTypeFilter(DamageType.PENETRATION),
            ElementFilter(Element.FIRE),
            AnyFilter(
                (
                    DamageTagFilter(DamageTag.BASIC_ATTACK),
                    DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),
                )
            ),
        ),
    )
    rules.append(
        _rule(
            "cinema1:accumulated-hp-loss-fire-damage",
            sources[1],
            f"1影：按历史累计已损失生命值提升普攻/支援突击火伤，最多{c1_max_bonus:.0%}",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            effects=(c1_effect,),
        )
    )

    c2_resistance_ignore = _number(
        c2.description,
        r"无视目标(?P<value>[\d.]+)%火属性伤害抗性",
        "Manato Cinema 2 Fire resistance ignore",
    ) / 100.0
    rules.append(
        _rule(
            "cinema2:ember-edge-fire-resistance-ignore",
            sources[2],
            f"2影：熔锋状态无视目标{c2_resistance_ignore:.0%}火属性抗性",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            condition_ids=(MANATO_EMBER_EDGE_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:ember-edge-fire-resistance-ignore",
                    sources[2],
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c2_resistance_ignore),
                    target=EffectTarget.ENEMY,
                    filters=(
                        DamageDealerFilter(MANATO_ID),
                        DamageTypeFilter(DamageType.PENETRATION),
                        ElementFilter(Element.FIRE),
                    ),
                ),
            ),
        )
    )

    for level, cinema in ((3, c3), (5, c5)):
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                sources[level],
                f"{level}影：技能等级+2（含终结技，依共享等级规则）",
                cinema.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    c4_max_hp_bonus = _number(
        c4.description,
        r"最大生命值提升(?P<value>[\d.]+)%",
        "Manato Cinema 4 max HP bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema4:max-hp-bonus",
            sources[4],
            f"4影：最大生命值提升{c4_max_hp_bonus:.0%}",
            c4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:max-hp-bonus",
                    sources[4],
                    CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                    Resolved(c4_max_hp_bonus),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )

    c6_stack_bonus = _number(
        c6.description,
        r"火属性伤害提升(?P<value>[\d.]+)%",
        "Manato Cinema 6 Fire damage bonus per stack",
    ) / 100.0
    c6_stack_limit = int(
        _number(
            c6.description,
            r"最多叠加(?P<value>[\d.]+)层",
            "Manato Cinema 6 Fire damage stack cap",
        )
    )
    c6_stacks = ScenarioIntegerParameter(
        parameter_id=MANATO_C6_FIRE_DAMAGE_STACKS,
        label="影画6：当前有效火伤叠层",
        original_text=c6.description,
        resolution=ParameterResolution.USER_SELECTED,
        value=None,
        minimum=0,
        maximum=c6_stack_limit,
    )
    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    rules.extend(
        (
            _rule(
                "cinema6:current-fire-damage-stacks",
                sources[6],
                f"6影：当前火伤叠层每层提升{c6_stack_bonus:.0%}（最多{c6_stack_limit}层）",
                c6.description,
                c6_eligibility,
                effects=(
                    _modifier(
                        "cinema6:current-fire-damage-stacks",
                        sources[6],
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        ScenarioParameterDerivedValue(
                            parameter_id=str(MANATO_C6_FIRE_DAMAGE_STACKS),
                            coefficient=Resolved(c6_stack_bonus),
                            cap_max=Resolved(c6_stack_bonus * c6_stack_limit),
                        ),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageTypeFilter(DamageType.PENETRATION),
                            ElementFilter(Element.FIRE),
                        ),
                    ),
                ),
            ),
        )
    )

    parameters = (c1_parameter, c6_stacks)
    return build_definition(
        character_id=MANATO_ID,
        role=CharacterRole.RUPTURE,
        element=Element.FIRE,
        source=source_for(
            MANATO_ID,
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
    return load_nanoka_raw_record(data, expected_character_id=str(MANATO_ID))


__all__ = [
    "MANATO_C1_ACCUMULATED_HP_LOSS_BASIS_POINTS",
    "MANATO_C6_FIRE_DAMAGE_STACKS",
    "compile_manato",
    "load_raw_record",
]
