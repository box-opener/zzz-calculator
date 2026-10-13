"""Compile Norma's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterId,
    CharacterRole,
    CurrentAttackValueSource,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    PanelStatDerivedValue,
    Resolved,
    RuleStackCondition,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
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
from ..templates import DirectDamageEventTemplate
from .config import NormaCompileConfig
from .reviewed import (
    CINEMA1_RESISTANCE_REDUCTION_ACTIVE,
    CINEMA6_MISSILE_CURRENT_HIT,
    CORE_INITIAL_CRIT_DAMAGE_RULE_ID,
    CURRENT_TECH_GAP_STACKS,
    EN_NI_BARRAGE_ACTIVE,
    EXTRA_TECH_GAP_RULE_ID,
    NORMA_ID,
    NORMA_CONSTRUCT_PREFIX,
    NORMA_FRIENDLY_ACTOR_CURVES,
    NORMA_REVIEWED_MAPPING,
    EX_TARGET_NOT_STUNNED,
    EX_TARGET_STUNNED,
    TERM_1000012_ACTIVE,
)


_CINEMA6_CURRENT_MISSILE_TEMPLATE = EventTemplateId(
    "template:character:1571:cinema6-current-missile:main"
)
_EX_HIGH_EXPLOSIVE_TEMPLATE = EventTemplateId(
    "template:character:1571:ex-high-explosive-shell:main"
)
_EX_EXTENDED_HIGH_EXPLOSIVE_TEMPLATE = EventTemplateId(
    "template:character:1571:ex-extended-high-explosive-per-second:main"
)
_NORMA_CONSTRUCT_HIGH_EXPLOSIVE_TEMPLATE = EventTemplateId(
    "template:character:1571:friendly-construct:ex-firepower-high-explosive-shell:main"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(NORMA_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1571:{key}"),
        owner=NORMA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(conditions),
        effects=tuple(effects),
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
            effect_id=EffectId(f"effect:character:1571:{key}"),
            source=source,
            owner=NORMA_ID,
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


def _validate_raw_record(raw: NanokaRawRecord, config: NormaCompileConfig) -> None:
    if raw.character_id != NORMA_ID or raw.name != "诺姆" or raw.code_name != "Norma":
        raise ValueError("unexpected identity in Norma raw record")
    if raw.specialty != "击破" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("Norma source role, element, or rarity changed")
    if raw.faction != "罗斯凯利法" or raw.icon != "IconRole65":
        raise ValueError("Norma source faction or icon changed")
    if (
        raw.source_version != "3.2"
        or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1571.json"
    ):
        raise ValueError("Norma provenance must identify live Nanoka 3.2 character 1571")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Norma source must contain seven Core levels and six Cinemas")
    if config.character_id != NORMA_ID:
        raise ValueError("Norma compile config has an unexpected character ID")


def _core_effects(
    config: NormaCompileConfig,
    core_source: RuleSource,
    core_text: str,
) -> tuple[CalculationRuleItem, ...]:
    per_point_cd = _number(
        core_text,
        r"每超过1%，暴击伤害提升(?P<value>[\d.]+)%",
        "Norma Core Crit Damage per initial Crit Rate point",
    )
    cap_cd = _number(
        core_text,
        r"暴击伤害.*?最多额外提升(?P<value>[\d.]+)%",
        "Norma Core maximum Crit Damage",
    ) / 100.0
    crit_effect = _modifier(
        "core:initial-crit-damage",
        core_source,
        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
        PanelStatDerivedValue(
            source_character_id=NORMA_ID,
            source_node=CalculationNode.CHARACTER_INITIAL_CRIT_RATE,
            coefficient=Resolved(per_point_cd),
            base=Resolved(0.0),
            cap_max=Resolved(cap_cd),
            threshold=Resolved(0.50),
        ),
        target=EffectTarget.SELF,
    )
    crit_rule = _rule(
        "core:initial-crit-damage",
        core_source,
        f"核心被动：初始暴击率超过50%时，每1%提升暴击伤害{per_point_cd:g}%，至多{cap_cd:.0%}",
        core_text,
        RuleEligibility.ELIGIBLE,
        effects=(crit_effect,),
    )
    pf_rule = _rule(
        "core:penetration-force-atk",
        core_source,
        "核心被动：每点当前贯穿力转化为1.25攻击力，最多1200点攻击力",
        core_text,
        RuleEligibility.ELIGIBLE,
    )
    return crit_rule, pf_rule


def _extra_rules(
    config: NormaCompileConfig,
    extra_source: RuleSource,
    extra_text: str,
) -> tuple[list[CalculationRuleItem], list[ScenarioCondition], list[ScenarioIntegerParameter]]:
    rules: list[CalculationRuleItem] = []
    conditions = [
        _condition(
            TERM_1000012_ACTIVE,
            "嗯呢弹幕当前生效",
            extra_text,
        ),
    ]
    parameters = [
        ScenarioIntegerParameter(
            parameter_id=CURRENT_TECH_GAP_STACKS,
            label="目标当前技术鸿沟层数",
            original_text="每层提高目标失衡易伤倍率3%，最多10层；当前层数作为静态输入，不重放命中时间轴。",
            resolution=ParameterResolution.USER_SELECTED,
            value=10,
            minimum=0,
            maximum=10,
        ),
    ]
    eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    base_per_stack = _number(
        extra_text,
        r"每层.*?提升(?P<value>[\d.]+)%",
        "Norma Extra Technical Gap stun vulnerability per stack",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:technical-gap-stacks",
            extra_source,
            f"额外能力：技术鸿沟每层使目标失衡易伤+{base_per_stack:.0%}",
            extra_text,
            eligibility,
            stack_count=1,
            stack_min=1,
            stack_max=1,
            effects=(
                _modifier(
                    "extra-ability:technical-gap-stacks",
                    extra_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(CURRENT_TECH_GAP_STACKS),
                        coefficient=Resolved(base_per_stack),
                        cap_max=Resolved(base_per_stack * 10),
                    ),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    )
    term_atk = _number(
        extra_text,
        r"攻击力提升(?P<value>[\d.]+)点",
        "Norma Term 1000012 initial flat ATK bonus",
    )
    term_per_level = _number(
        extra_text,
        r"每级增加(?P<value>[\d.]+)点",
        "Norma Term 1000012 per-level flat ATK bonus",
    )
    term_cap = _number(
        extra_text,
        r"最多提升(?P<value>[\d.]+)点",
        "Norma Term 1000012 maximum flat ATK bonus",
    )
    rules.append(
        _rule(
            "extra-ability:term-1000012-attack",
            extra_source,
            f"额外能力：嗯呢弹幕期间攻击力+{term_atk:g}+{term_per_level:g}/等级（至多{term_cap:g}）",
            extra_text,
            eligibility,
            conditions=(TERM_1000012_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:term-1000012-attack",
                    extra_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    # The calculator's character-build contract uses level 60.
                    # Keep the source's exact level formula in the rule text,
                    # and apply its explicit level-60 cap rather than adding a
                    # second, potentially conflicting level selector.
                    Resolved(term_cap),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )
    team_damage = _number(
        extra_text,
        r"全队代理人造成的伤害提升(?P<value>[\d.]+)%",
        "Norma Extra team damage bonus during En-Ni Barrage",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:en-ni-barrage-team-damage",
            extra_source,
            f"额外能力：嗯呢弹幕期间全队造成伤害+{team_damage:.0%}",
            extra_text,
            eligibility,
            conditions=(EN_NI_BARRAGE_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:en-ni-barrage-team-damage",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(team_damage),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )
    return rules, conditions, parameters


def _cinema_rules(
    config: NormaCompileConfig,
    raw: NanokaRawRecord,
    extra_rule_id: RuleItemId,
) -> tuple[list[CalculationRuleItem], list[ScenarioCondition]]:
    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []
    for cinema in raw.mindscapes:
        source = _source(
            f"cinema-{cinema.level}", EffectSourceType.CINEMA, cinema.name, cinema.description
        )
        unlocked = config.cinema_level >= cinema.level
        eligibility = RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE
        if cinema.level == 1:
            conditions.append(
                _condition(
                    CINEMA1_RESISTANCE_REDUCTION_ACTIVE,
                    "目标当前受到诺姆破甲／高爆弹头造成的全属性抗性降低",
                    cinema.description,
                )
            )
            reduction = _number(
                cinema.description,
                r"全属性伤害抗性降低(?P<value>[\d.]+)%",
                "Norma Cinema 1 all resistance reduction",
            ) / 100.0
            effect = _modifier(
                "cinema1:all-resistance-reduction",
                source,
                CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                Resolved(reduction),
                target=EffectTarget.ENEMY,
            )
            rules.append(
                _rule(
                    "cinema1:all-resistance-reduction",
                    source,
                    f"1影：破甲／高爆弹头命中后全属性抗性降低{reduction:.0%}",
                    cinema.description,
                    eligibility,
                    effects=(effect,) if unlocked else (),
                    conditions=(CINEMA1_RESISTANCE_REDUCTION_ACTIVE,),
                )
            )
        elif cinema.level == 2:
            c2_eligible = unlocked and config.additional_ability_eligible
            c2_rule_eligibility = (
                RuleEligibility.ELIGIBLE
                if c2_eligible
                else RuleEligibility.INELIGIBLE
            )
            c2_per_stack = _number(
                cinema.description,
                r"每层.*?失衡易伤倍率提升至(?P<value>[\d.]+)%",
                "Norma Cinema 2 Technical Gap total stun vulnerability per stack",
            ) / 100.0
            base_per_stack = _number(
                raw.extra_ability_description,
                r"每层.*?提升(?P<value>[\d.]+)%",
                "Norma Extra Technical Gap base stun vulnerability per stack",
            ) / 100.0
            increment = c2_per_stack - base_per_stack
            if increment < 0:
                raise ValueError("Norma Cinema 2 per-stack value cannot be below the Extra base")
            effect = _modifier(
                "cinema2:technical-gap-stun-vulnerability",
                source,
                CalculationNode.ENEMY_STUN_VULNERABILITY,
                ScenarioParameterDerivedValue(
                    parameter_id=str(CURRENT_TECH_GAP_STACKS),
                    coefficient=Resolved(increment),
                    cap_max=Resolved(increment * 10),
                ),
                target=EffectTarget.ENEMY,
                condition=RuleStackCondition(
                    str(extra_rule_id), 1, requires_rule_enabled=True
                ),
            )
            rules.append(
                _rule(
                    "cinema2:technical-gap-stun-vulnerability",
                    source,
                    f"2影：额外能力技术鸿沟每层再增加{increment:.0%}（与基础值相加替代至{c2_per_stack:.0%}）",
                    cinema.description,
                    c2_rule_eligibility,
                    effects=(effect,) if c2_eligible else (),
                )
            )
        elif cinema.level == 3 or cinema.level == 5:
            rules.append(
                _rule(
                    f"cinema{cinema.level}:skill-levels",
                    source,
                    f"{cinema.level}影：技能等级提升（含终结技）",
                    cinema.description,
                    eligibility,
                )
            )
        elif cinema.level == 6:
            conditions.append(
                _condition(
                    CINEMA6_MISSILE_CURRENT_HIT,
                    "6影当前有一发导弹命中（只计算单发，不推算持续总数）",
                    cinema.description,
                )
            )
            high_explosive_bonus = _number(
                cinema.description,
                r"\[高爆弹头\]造成的伤害提升(?P<value>[\d.]+)%",
                "Norma Cinema 6 High Explosive damage bonus",
            ) / 100.0
            high_explosive = _modifier(
                "cinema6:high-explosive-damage",
                source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(high_explosive_bonus),
                target=EffectTarget.TEAM,
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    AnyFilter(
                        (
                            EventTemplateIdFilter(_EX_HIGH_EXPLOSIVE_TEMPLATE),
                            EventTemplateIdFilter(_EX_EXTENDED_HIGH_EXPLOSIVE_TEMPLATE),
                            EventTemplateIdFilter(
                                _NORMA_CONSTRUCT_HIGH_EXPLOSIVE_TEMPLATE
                            ),
                        )
                    ),
                ),
            )
            rules.append(
                _rule(
                    "cinema6:high-explosive-damage",
                    source,
                    f"6影：高爆弹头伤害+{high_explosive_bonus:.0%}",
                    cinema.description,
                    eligibility,
                    effects=(high_explosive,) if unlocked else (),
                )
            )
    return rules, conditions


def _friendly_construct_entries(
    config: NormaCompileConfig,
    raw: NanokaRawRecord,
) -> tuple[tuple[MoveCalculationEntry, ...], tuple[DirectDamageEventTemplate, ...], tuple[CalculationDiagnostic, ...]]:
    raw_moves = raw_move_index(raw)
    entries: list[MoveCalculationEntry] = []
    templates: list[DirectDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for candidate in NORMA_FRIENDLY_ACTOR_CURVES:
        source_level = effective_skill_level(config, candidate.parameter_skill_group)
        ratio = raw_multiplier(
            raw_moves,
            candidate.source_name,
            candidate.parameter_name,
            source_level,
            f"{NORMA_ID}:{candidate.entry_key}",
            diagnostics,
            candidate.source_skill_id,
        )
        raw_move = raw_moves.get(candidate.source_name)
        original_text = (
            raw_move.description if raw_move is not None else candidate.source_text_hint
        )
        actor_id = CharacterId(f"{NORMA_CONSTRUCT_PREFIX}{candidate.entry_key}")
        template_id = (
            _NORMA_CONSTRUCT_HIGH_EXPLOSIVE_TEMPLATE
            if candidate.entry_key == "ex-firepower-high-explosive-shell"
            else EventTemplateId(
                f"template:character:1571:friendly-construct:{candidate.entry_key}:main"
            )
        )
        ref = DamageEventTemplateRef(
            template_id=template_id,
            semantic_id=DamageEventSemanticId(
                f"event:character:1571:{candidate.entry_key}:main"
            ),
            label=candidate.display_name,
            damage_type=DamageType.DIRECT,
            element=candidate.element,
        )
        template = DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=actor_id,
            element=candidate.element,
            base_source=CurrentAttackValueSource(actor_id),
            crit_rule=StandardCritRule(actor_id),
            move_id=None,
            friendly_actor_owner_id=NORMA_ID,
        )
        conditions = (
            (EX_TARGET_NOT_STUNNED,)
            if candidate.entry_key == "ex-firepower-armor-shell"
            else (EX_TARGET_STUNNED,)
            if candidate.entry_key == "ex-firepower-high-explosive-shell"
            else ()
        )
        multiplier = (
            ratio
            if isinstance(ratio, Unresolved)
            else FixedMultiplier(Resolved(ratio))
        )
        entry = MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1571:{candidate.entry_key}"),
            character_id=NORMA_ID,
            move_id=None,
            display_name=candidate.display_name,
            original_text=original_text,
            skill_group=None,
            damage_tags=frozenset(),
            multiplier_relation=MultiplierRelation.COMPLETE,
            multiplier_variants=(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1571:{candidate.entry_key}:source-ratio"
                    ),
                    label="来源倍率",
                    parameter_name=candidate.parameter_name,
                    multiplier=multiplier,
                    condition_ids=conditions,
                ),
            ),
            main_damage_event=ref,
            condition_ids=conditions,
        )
        entries.append(entry)
        templates.append(template)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def _cinema6_current_missile(
    config: NormaCompileConfig,
    raw: NanokaRawRecord,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate] | None:
    if config.cinema_level < 6:
        return None
    cinema = raw.mindscapes[5]
    ratio = _number(
        cinema.description,
        r"诺姆(?P<value>[\d.]+)%攻击力的火属性伤害",
        "Norma Cinema 6 single missile damage multiplier",
    ) / 100.0
    ref = DamageEventTemplateRef(
        template_id=_CINEMA6_CURRENT_MISSILE_TEMPLATE,
        semantic_id=DamageEventSemanticId(
            "event:character:1571:cinema6-current-missile:main"
        ),
        label="6影：当前一发导弹（按终结技伤害）",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.ULTIMATE,
        damage_tags=frozenset({DamageTag.ULTIMATE}),
        element=Element.FIRE,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=NORMA_ID,
        element=Element.FIRE,
        base_source=CurrentAttackValueSource(NORMA_ID),
        crit_rule=StandardCritRule(NORMA_ID),
        move_id=None,
    )
    variant = MultiplierVariant(
        variant_id=MultiplierVariantId(
            "variant:character:1571:cinema6-current-missile:main"
        ),
        label=f"单发{ratio:.0%}攻击力",
        parameter_name="导弹单发倍率",
        multiplier=FixedMultiplier(Resolved(ratio)),
        condition_ids=(CINEMA6_MISSILE_CURRENT_HIT,),
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1571:cinema6-current-missile"),
        character_id=NORMA_ID,
        move_id=None,
        display_name="6影：当前一发导弹（按终结技伤害）",
        original_text=cinema.description,
        skill_group=SkillGroup.ULTIMATE,
        damage_tags=frozenset({DamageTag.ULTIMATE}),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(variant,),
        main_damage_event=ref,
        condition_ids=(CINEMA6_MISSILE_CURRENT_HIT,),
    )
    return entry, typed


def compile_norma(
    config: NormaCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=NORMA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=NORMA_REVIEWED_MAPPING,
        id_namespace="character:1571",
    )
    entries = list(entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description
    )
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    ex_source_move = next(
        item for item in raw_record.moves if item.name == "强化特殊技：嗯呢弹幕"
    )
    conditions = [
        _condition(
            EX_TARGET_STUNNED,
            "嗯呢弹幕主要攻击目标当前处于失衡状态（发射高爆弹头）",
            ex_source_move.description,
        ),
        _condition(
            EX_TARGET_NOT_STUNNED,
            "嗯呢弹幕主要攻击目标当前未处于失衡状态（发射破甲弹头）",
            ex_source_move.description,
        ),
    ]
    rules = list(_core_effects(config, core_source, core.description))
    extra_rules, extra_conditions, parameters = _extra_rules(
        config, extra_source, core.extra_ability_description
    )
    rules.extend(extra_rules)
    conditions.extend(extra_conditions)
    cinema_rules, cinema_conditions = _cinema_rules(
        config,
        raw_record,
        EXTRA_TECH_GAP_RULE_ID,
    )
    rules.extend(cinema_rules)
    conditions.extend(cinema_conditions)

    construct_entries, construct_templates, construct_diagnostics = (
        _friendly_construct_entries(config, raw_record)
    )
    entries.extend(construct_entries)
    templates.extend(construct_templates)
    diagnostics.extend(construct_diagnostics)

    c6_result = _cinema6_current_missile(config, raw_record)
    if c6_result is not None:
        c6_entry, c6_template = c6_result
        entries.append(c6_entry)
        templates.append(c6_template)

    return build_definition(
        character_id=NORMA_ID,
        role=CharacterRole.STUN,
        element=Element.FIRE,
        source=_source(
            "live-source",
            EffectSourceType.SKILL,
            raw_record.name,
            f"Nanoka {raw_record.source_version}: {raw_record.source_url}",
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(NORMA_ID))


__all__ = ["compile_norma", "load_raw_record"]
