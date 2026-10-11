"""Compile Cissia's reviewed Nanoka 3.2 record into static damage rules."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import replace

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
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
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    RuleStackCondition,
    ScenarioParameterRangeCondition,
    SnapshotRule,
    StandardCritRule,
)

from ...ids import DamageEventSemanticId, RuleItemId
from ...moves import (
    DamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..templates import DirectDamageEventTemplate
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
from .config import CISSIA_ID, CissiaCompileConfig
from .reviewed import (
    CISSIA_CINEMA4_AWARENESS_STACKS,
    CISSIA_CINEMA6_MARK_PROC_ACTIVE,
    CISSIA_EX_EXTRA_HIT_COUNT,
    CISSIA_REVIEWED_MAPPING,
    CISSIA_SNAKE_SHADOW_AVAILABLE,
    CISSIA_TOXIN_ACTIVE,
)


_BONE_BASE_TEMPLATE = EventTemplateId("template:character:1521:bone-erosion:basic")
_BONE_CINEMA4_TEMPLATE = EventTemplateId("template:character:1521:bone-erosion:cinema4")
_BONE_CINEMA6_TEMPLATE = EventTemplateId("template:character:1521:bone-erosion:cinema6")
def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(CISSIA_ID))


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain exactly one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1521:{key}"),
        owner=CISSIA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
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
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1521:{key}"),
            source=source,
            owner=CISSIA_ID,
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


def _condition(condition_id, label: str, text: str, value: bool) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _event_filter(entry: MoveCalculationEntry) -> EventTemplateIdFilter:
    return EventTemplateIdFilter(EventTemplateId(str(entry.main_damage_event.template_id)))


def _bone_ref(template_id: EventTemplateId, suffix: str, label: str, source_rule=None):
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId(f"event:character:1521:{suffix}"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.ELECTRIC,
        source_rule_item_id=source_rule,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=CISSIA_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(CISSIA_ID),
        crit_rule=StandardCritRule(CISSIA_ID),
        move_id=None,
    )
    return ref, template


def _validate_raw_record(raw: NanokaRawRecord, config: CissiaCompileConfig) -> None:
    if raw.character_id != CISSIA_ID:
        raise ValueError(f"Cissia compiler requires {CISSIA_ID}; got {raw.character_id}")
    if raw.code_name != "Cissia" or raw.name != "希希芙" or raw.rarity != 4:
        raise ValueError("Cissia raw identity no longer matches the reviewed live source")
    if (raw.specialty, raw.element, raw.faction, raw.icon) != (
        "强攻",
        "电属性",
        "新艾利都治安局",
        "IconRole60",
    ):
        raise ValueError("Cissia raw role, element, camp, or icon changed")
    if len(raw.core_levels) != 7 or tuple(item.level for item in raw.core_levels) != tuple(range(1, 8)):
        raise ValueError("Cissia raw record must contain Core levels 1 through 7")
    if tuple(item.level for item in raw.mindscapes) != tuple(range(1, 7)):
        raise ValueError("Cissia raw record must contain Cinema levels 1 through 6")


def compile_cissia(
    config: CissiaCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, move_diagnostics = compile_direct_moves(
        character_id=CISSIA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=CISSIA_REVIEWED_MAPPING,
        id_namespace="character:1521",
    )
    entry_by_key = {
        str(item.entry_id).rsplit(":", 1)[-1]: item for item in entries
    }
    basic_level = effective_skill_level(config, next(
        item.skill_group for item in CISSIA_REVIEWED_MAPPING.moves if item.entry_key == "basic-snake-kiss"
    ))
    raw_moves = raw_move_index(raw_record)
    bone_base = raw_multiplier(
        raw_moves,
        "蚀骨",
        "伤害倍率",
        basic_level,
        "character:1521:bone-erosion",
        [],
        "1521019",
    )
    if not isinstance(bone_base, float):
        raise ValueError("Cissia Bone Erosion's reviewed 1521019 curve is incomplete")

    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        CISSIA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra = source_for(
        CISSIA_ID,
        "additional-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    core_bone_bonus = _number(
        core.description,
        r"\[蚀骨\]额外附加自身(?P<value>[\d.]+)%攻击力",
        "Cissia Core Bone Erosion Attack ratio",
    ) / 100.0
    def_ignore = _number(
        core.description,
        r"电属性伤害无视敌人(?P<value>[\d.]+)%防御力",
        "Cissia Core Electric defense ignore",
    ) / 100.0
    er_step = _number(
        core.description,
        r"每超过(?P<value>[\d.]+)，额外无视敌人",
        "Cissia Core initial Energy Regen step",
    )
    er_ignore_per_step = _number(
        core.description,
        r"每超过[\d.]+，额外无视敌人(?P<value>[\d.]+)%防御力",
        "Cissia Core defense ignore per Initial Energy Regen step",
    ) / 100.0
    total_def_ignore_cap = _number(
        core.description,
        r"至多无视敌人(?P<value>[\d.]+)%防御力",
        "Cissia Core maximum Electric defense ignore",
    ) / 100.0

    bone_multiplier = FixedMultiplier(Resolved(bone_base))
    base_bone_ref, base_bone_template = _bone_ref(
        _BONE_BASE_TEMPLATE,
        "basic-snake-kiss-bone-erosion",
        "蚀骨（蛇吻触发）",
    )
    templates = (*templates, base_bone_template)
    active_bone_template_ids = [_BONE_BASE_TEMPLATE]
    c4_bone_ref = None
    if config.cinema_level >= 4:
        c4_bone_ref, c4_bone_template = _bone_ref(
            _BONE_CINEMA4_TEMPLATE,
            "cinema4-bone-erosion",
            "4影：特殊蚀骨",
            RuleItemId("rule:character:1521:cinema4:special-bone-erosion"),
        )
        templates = (*templates, c4_bone_template)
        active_bone_template_ids.append(_BONE_CINEMA4_TEMPLATE)
    c6_bone_ref = None
    if config.cinema_level >= 6:
        c6_bone_ref, c6_bone_template = _bone_ref(
            _BONE_CINEMA6_TEMPLATE,
            "cinema6-bone-erosion",
            "6影：全队攻击触发的特殊蚀骨",
            RuleItemId("rule:character:1521:cinema6:team-bone-erosion"),
        )
        templates = (*templates, c6_bone_template)
        active_bone_template_ids.append(_BONE_CINEMA6_TEMPLATE)

    # The ordinary Snake Kiss explicitly triggers one Bone Erosion packet.
    snake_index = next(
        index for index, entry in enumerate(entries) if str(entry.entry_id).endswith(":basic-snake-kiss")
    )
    entries = list(entries)
    entries[snake_index] = replace(
        entries[snake_index],
        derived_damage_events=(
            DerivedDamageEventTemplateRef(
                template=base_bone_ref,
                multiplier=bone_multiplier,
                required=True,
            ),
        ),
    )
    entry_by_key["basic-snake-kiss"] = entries[snake_index]

    # EX Special 1521009 is a separate per-hit curve and is repeated 0–3 times.
    ex_extra_ratio = raw_multiplier(
        raw_moves,
        "强化特殊技：毒牙",
        "伤害倍率",
        effective_skill_level(config, entry_by_key["ex-special"].skill_group),
        "character:1521:ex-special-extra-hit",
        [],
        "1521009",
    )
    if not isinstance(ex_extra_ratio, float):
        raise ValueError("Cissia EX extra-hit source curve 1521009 is incomplete")
    ex_ref, ex_template = _bone_ref(
        EventTemplateId("template:character:1521:ex-special-extra-hit"),
        "ex-special-extra-hit",
        "强化特殊技：毒牙（额外打击）",
        RuleItemId("rule:character:1521:skill:ex-special-extra-hit"),
    )
    ex_ref = replace(ex_ref, element=Element.ELECTRIC)
    ex_template = replace(ex_template, ref=ex_ref)
    ex_index = next(
        index for index, entry in enumerate(entries) if str(entry.entry_id).endswith(":ex-special")
    )
    entries[ex_index] = replace(
        entries[ex_index],
        derived_damage_events=(
            DerivedDamageEventTemplateRef(
                template=ex_ref,
                multiplier=FixedMultiplier(Resolved(ex_extra_ratio)),
                repeat_count_parameter_id=CISSIA_EX_EXTRA_HIT_COUNT,
                skip_when_repeat_count_zero=True,
            ),
        ),
    )
    entry_by_key["ex-special"] = entries[ex_index]
    templates = (*templates, ex_template)

    conditions = [
        _condition(
            CISSIA_TOXIN_ACTIVE,
            "毒素或耗尽后30秒当前生效",
            "按当前毒素状态或耗尽后的30秒状态输入；不回放资源与时间轴。",
            config.toxin_active_or_recent,
        ),
        _condition(
            CISSIA_SNAKE_SHADOW_AVAILABLE,
            "当前拥有蛇影",
            "蛇吻需要当前拥有蛇影；按本次静态场景选择，不模拟毒素转化。",
            config.snake_shadow_available,
        ),
    ]
    parameters = [
        ScenarioIntegerParameter(
            parameter_id=CISSIA_EX_EXTRA_HIT_COUNT,
            label="本次强化特殊技额外打击次数",
            original_text="每额外消耗20点能量发动一次额外打击，至多额外消耗60点能量；当前输入0–3次，不模拟能量时间轴。",
            resolution=ParameterResolution.USER_SELECTED,
            value=config.ex_special_extra_hit_count,
            minimum=0,
            maximum=3,
        )
    ]
    rules: list[CalculationRuleItem] = []
    ex_source_move = raw_moves["强化特殊技：毒牙"]
    ex_extra_source = source_for(
        CISSIA_ID,
        "skill:ex-special-extra-hit",
        EffectSourceType.SKILL,
        ex_source_move.name,
        ex_source_move.description,
    )
    ex_extra_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1521:skill:ex-special-extra-hit"),
            source=ex_extra_source,
            owner=CISSIA_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=ScenarioParameterRangeCondition(
                parameter_id=str(CISSIA_EX_EXTRA_HIT_COUNT),
                minimum=1,
            ),
            filters=(_event_filter(entry_by_key["ex-special"]),),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=ex_ref.template_id,
            unique_per_source_event=True,
        ),
    )
    rules.append(
        _rule(
            "skill:ex-special-extra-hit",
            ex_extra_source,
            "强化特殊技：毒牙额外打击",
            ex_source_move.description,
            RuleEligibility.ELIGIBLE,
            effects=(ex_extra_effect,),
        )
    )

    core_ignore_value = PanelStatDerivedValue(
        source_character_id=CISSIA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
        coefficient=Resolved(er_ignore_per_step),
        base=Resolved(def_ignore),
        cap_max=Resolved(total_def_ignore_cap),
        threshold=Resolved(1.4),
        step_size=Resolved(er_step),
    )
    core_defense_effect = _modifier(
        "core:electric-defense-ignore",
        core_source,
        CalculationNode.DAMAGE_DEFENSE_IGNORE,
        core_ignore_value,
        target=EffectTarget.TEAM,
        filters=(ElementFilter(Element.ELECTRIC),),
    )
    # DamageEvent execution treats DAMAGE_SKILL_MULTIPLIER modifiers as
    # multiplicative factors.  Encode the source's additive ATK ratio as a
    # relative factor against the same effective 1521019 base curve so Core
    # can be disabled cleanly without inventing a generic ADD operation.
    core_bone_factor = (bone_base + core_bone_bonus) / bone_base
    core_bone_effect = _modifier(
        "core:bone-erosion-extra-ratio",
        core_source,
        CalculationNode.DAMAGE_SKILL_MULTIPLIER,
        Resolved(core_bone_factor),
        target=EffectTarget.TEAM,
        filters=(AnyFilter(tuple(EventTemplateIdFilter(item) for item in active_bone_template_ids)),),
        operation=EffectOperation.MULTIPLY,
    )
    # Poison state gates the DEF-ignore effect. The separately stated Core
    # Bone Erosion ratio applies to each reviewed Bone Erosion packet.
    rules.append(
        _rule(
            "core:toxin-electric-defense-ignore",
            core_source,
            "核心被动：毒素期间电伤无视防御",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(core_defense_effect,),
            condition_ids=(CISSIA_TOXIN_ACTIVE,),
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )
    rules.append(
        _rule(
            "core:bone-erosion-extra-ratio",
            core_source,
            "核心被动：蚀骨额外攻击倍率",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(core_bone_effect,),
        )
    )

    if config.additional_ability_eligible:
        crit_damage_bonus = _number(
            core.extra_ability_description,
            r"暴击伤害提升(?P<value>[\d.]+)%",
            "Cissia Additional Ability team Crit Damage",
        ) / 100.0
        self_extra = _number(
            core.extra_ability_description,
            r"自身额外提升(?P<value>[\d.]+)%",
            "Cissia Additional Ability self Crit Damage",
        ) / 100.0
        extra_effects = (
            _modifier(
                "extra:team-crit-damage",
                extra,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                Resolved(crit_damage_bonus),
                target=EffectTarget.TEAM,
            ),
            _modifier(
                "extra:self-crit-damage",
                extra,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                Resolved(self_extra),
                target=EffectTarget.SELF,
            ),
        )
    else:
        extra_effects = ()
    rules.append(
        _rule(
            "extra:toxin-team-crit-damage",
            extra,
            "额外能力：毒素期间全队暴伤提升",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            effects=extra_effects,
            condition_ids=(CISSIA_TOXIN_ACTIVE,),
        )
    )

    cinema_rules: list[CalculationRuleItem] = []
    for mindscape in raw_record.mindscapes:
        source = source_for(
            CISSIA_ID,
            f"cinema-{mindscape.level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        unlocked = config.cinema_level >= mindscape.level
        if mindscape.level in (3, 5):
            cinema_rules.append(
                _rule(
                    f"cinema{mindscape.level}:skill-levels",
                    source,
                    f"{mindscape.level}影：技能等级提升（含终结技）",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE,
                )
            )
            continue
        if mindscape.level == 1:
            core_scale = _number(
                mindscape.description,
                r"无视敌人防御力效果提升至原本的(?P<value>[\d.]+)%",
                "Cissia Cinema 1 Core defense-ignore multiplier",
            ) / 100.0
            c1_core_delta = PanelStatDerivedValue(
                source_character_id=CISSIA_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
                coefficient=Resolved(er_ignore_per_step * (core_scale - 1.0)),
                base=Resolved(def_ignore * (core_scale - 1.0)),
                cap_max=Resolved(total_def_ignore_cap * (core_scale - 1.0)),
                threshold=Resolved(1.4),
                step_size=Resolved(er_step),
            )
            team_res_ignore = _number(
                mindscape.description,
                r"全队角色造成的伤害无视目标(?P<value>[\d.]+)%电属性伤害抗性",
                "Cissia Cinema 1 team Electric resistance ignore",
            ) / 100.0
            bone_res_ignore = _number(
                mindscape.description,
                r"\[蚀骨\]造成的伤害无视目标(?P<value>[\d.]+)%电属性伤害抗性",
                "Cissia Cinema 1 Bone Erosion Electric resistance ignore",
            ) / 100.0
            c1_core_effect = _modifier(
                "cinema1:core-defense-ignore-increase",
                source,
                CalculationNode.DAMAGE_DEFENSE_IGNORE,
                c1_core_delta,
                target=EffectTarget.TEAM,
                filters=(ElementFilter(Element.ELECTRIC),),
                condition=RuleStackCondition(
                    str(RuleItemId("rule:character:1521:core:toxin-electric-defense-ignore")),
                    required_value=1,
                    requires_rule_enabled=True,
                ),
            )
            c1_res_effects = (
                _modifier(
                    "cinema1:team-electric-resistance-ignore",
                    source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(team_res_ignore),
                    target=EffectTarget.TEAM,
                    filters=(ElementFilter(Element.ELECTRIC),),
                ),
                _modifier(
                    "cinema1:bone-electric-resistance-ignore",
                    source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(bone_res_ignore),
                    target=EffectTarget.TEAM,
                    filters=(AnyFilter(tuple(EventTemplateIdFilter(item) for item in active_bone_template_ids)),),
                ),
            )
            cinema_rules.append(
                _rule(
                    "cinema1:core-defense-ignore-increase",
                    source,
                    "1影：核心无视防御提升至140%",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE,
                    effects=(c1_core_effect,) if unlocked else (),
                    condition_ids=(CISSIA_TOXIN_ACTIVE,) if unlocked else (),
                )
            )
            cinema_rules.append(
                _rule(
                    "cinema1:electric-resistance-ignore",
                    source,
                    "1影：全队电伤与蚀骨无视电抗",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE,
                    effects=c1_res_effects if unlocked else (),
                )
            )
            continue
        if mindscape.level == 2:
            kiss_bonus = _number(
                mindscape.description,
                r"\[普通攻击：蛇吻\]造成的伤害提升(?P<value>[\d.]+)%",
                "Cissia Cinema 2 Snake Kiss damage bonus",
            ) / 100.0
            c2_effects = (
                _modifier(
                    "cinema2:snake-kiss-damage-bonus",
                    source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(kiss_bonus),
                    target=EffectTarget.TEAM,
                    filters=(_event_filter(entry_by_key["basic-snake-kiss"]),),
                ),
            )
            cinema_rules.append(
                _rule(
                    "cinema2:snake-kiss-damage-bonus",
                    source,
                    "2影：蛇吻伤害提升35%",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE,
                    effects=c2_effects if unlocked else (),
                )
            )
            continue
        if mindscape.level == 4:
            if not unlocked:
                cinema_rules.append(
                    _rule(
                        "cinema4:special-bone-erosion",
                        source,
                        "4影：蛇吻消耗觉悟触发特殊蚀骨",
                        mindscape.description,
                        RuleEligibility.INELIGIBLE,
                    )
                )
                continue
            parameters.append(
                ScenarioIntegerParameter(
                    parameter_id=CISSIA_CINEMA4_AWARENESS_STACKS,
                    label="当前觉悟层数",
                    original_text="强化特殊技、连携技或终结技获得觉悟，最多3层；本次蛇吻消耗当前选择层数。",
                    resolution=ParameterResolution.USER_SELECTED,
                    value=config.cinema4_awareness_stacks,
                    minimum=0,
                    maximum=3,
                )
            )
            effect = EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId("effect:character:1521:cinema4:special-bone-erosion"),
                    source=source,
                    owner=CISSIA_ID,
                    target=EffectTarget.SELF,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    condition=ScenarioParameterRangeCondition(
                        parameter_id=str(CISSIA_CINEMA4_AWARENESS_STACKS),
                        minimum=1,
                    ),
                    filters=(_event_filter(entry_by_key["basic-snake-kiss"]),),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    event_template_id=_BONE_CINEMA4_TEMPLATE,
                    unique_per_source_event=True,
                ),
            )
            entries[snake_index] = replace(
                entries[snake_index],
                derived_damage_events=(
                    *entries[snake_index].derived_damage_events,
                    DerivedDamageEventTemplateRef(
                        template=c4_bone_ref,
                        multiplier=bone_multiplier,
                        repeat_count_parameter_id=CISSIA_CINEMA4_AWARENESS_STACKS,
                    ),
                ),
            )
            entry_by_key["basic-snake-kiss"] = entries[snake_index]
            cinema_rules.append(
                _rule(
                    "cinema4:special-bone-erosion",
                    source,
                    "4影：蛇吻消耗觉悟触发特殊蚀骨",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE,
                    effects=(effect,),
                )
            )
            continue
        if mindscape.level == 6:
            if not unlocked:
                cinema_rules.append(
                    _rule(
                        "cinema6:team-bone-erosion",
                        source,
                        "6影：全队攻击当前触发特殊蚀骨",
                        mindscape.description,
                        RuleEligibility.INELIGIBLE,
                    )
                )
                continue
            conditions.append(
                _condition(
                    CISSIA_CINEMA6_MARK_PROC_ACTIVE,
                    "蚀骨印记当前可触发蚀骨",
                    "按当前蚀骨印记与3秒触发间隔选择；不重放全队命中时间轴。",
                    config.cinema6_mark_proc_active,
                )
            )
            c6_effect = EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId("effect:character:1521:cinema6:team-bone-erosion"),
                    source=source,
                    owner=CISSIA_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        AnyFilter(
                            (
                                DamageTypeFilter(DamageType.DIRECT),
                                DamageTypeFilter(DamageType.PENETRATION),
                            )
                        ),
                        # Only a reviewed primary move is a fresh team hit for
                        # the static C6 proc; generated neutral children have
                        # no MoveId and must not consume a second proc here.
                        NotFilter(MoveIdFilter(None)),
                        NotFilter(AnyFilter(tuple(EventTemplateIdFilter(item) for item in active_bone_template_ids))),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    event_template_id=_BONE_CINEMA6_TEMPLATE,
                    unique_per_source_event=True,
                ),
            )
            cinema_rules.append(
                _rule(
                    "cinema6:team-bone-erosion",
                    source,
                    "6影：全队攻击当前触发特殊蚀骨",
                    mindscape.description,
                    RuleEligibility.ELIGIBLE,
                    effects=(c6_effect,),
                    condition_ids=(CISSIA_CINEMA6_MARK_PROC_ACTIVE,),
                )
            )
            continue

    rules.extend(cinema_rules)
    diagnostics = list(move_diagnostics)
    return build_definition(
        character_id=CISSIA_ID,
        role=CharacterRole.ATTACK,
        element=Element.ELECTRIC,
        source=source_for(
            CISSIA_ID,
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
        independent_derived_damage_events=(
            DerivedDamageEventTemplateRef(
                template=c6_bone_ref,
                multiplier=bone_multiplier,
            ),
        ) if config.cinema_level >= 6 else (),
        diagnostics=diagnostics,
    )


__all__ = ["compile_cissia", "load_raw_record"]
