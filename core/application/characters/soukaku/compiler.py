"""Compile Soukaku's reviewed Nanoka 3.2 source into calculation contracts."""

from __future__ import annotations

from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
    DamageType,
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
    MoveId,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...element_scope import element_scope_filter
from ...ids import (
    DamageEventSemanticId,
    DiagnosticId,
    MoveEntryId,
    MultiplierVariantId,
    RuleItemId,
    ScenarioParameterId,
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
    source_for,
)
from ..nanoka_source import NanokaRawRecord
from ..templates import AttributeAnomalyDamageEventTemplate, DisorderDamageEventTemplate
from .config import SoukakuCompileConfig
from .reviewed import (
    FLAG_ATTACK_BUFF_ACTIVE,
    FLAG_ATTACK_HIT_ACTIVE,
    FLAG_CONSUMED_VORTEX,
    FLAG_STATE_ACTIVE,
    ICE_ANOMALY_MOVE_ID,
    ICE_ANOMALY_RECORD_ID,
    ICE_DAMAGE_BUFF_ACTIVE,
    ICE_DISORDER_MOVE_ID,
    PHYSICAL_ANOMALY_MOVE_ID,
    PHYSICAL_ANOMALY_RECORD_ID,
    SOUKAKU_ID,
    SOUKAKU_REVIEWED_MAPPING,
)


_ICE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:soukaku:ice-disorder-remaining-seconds"
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
    return source_for(SOUKAKU_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1131:{key}"),
        owner=SOUKAKU_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
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
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1131:{key}"),
            source=source,
            owner=SOUKAKU_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _note(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1131:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _event_filter(key: str) -> EventTemplateIdFilter:
    return EventTemplateIdFilter(
        EventTemplateId(f"template:character:1131:{key}:main")
    )


def _complete_entry(
    *,
    first: MoveCalculationEntry,
    second: MoveCalculationEntry,
    templates: list,
    entries: list,
    key: str,
    label: str,
    move_id: MoveId,
) -> None:
    first_multiplier = first.multiplier_variants[0].multiplier
    second_multiplier = second.multiplier_variants[0].multiplier
    if not (
        isinstance(first_multiplier, FixedMultiplier)
        and isinstance(first_multiplier.value, Resolved)
        and isinstance(second_multiplier, FixedMultiplier)
        and isinstance(second_multiplier.value, Resolved)
    ):
        raise ValueError(f"Soukaku complete entry source components are unresolved: {key}")
    first_template = next(
        item for item in templates if item.ref.template_id == first.main_damage_event.template_id
    )
    new_ref = replace(
        first.main_damage_event,
        template_id=EventTemplateId(f"template:character:1131:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1131:{key}:main"),
        label=label,
    )
    entries.append(
        MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1131:{key}"),
            character_id=SOUKAKU_ID,
            move_id=move_id,
            display_name=label,
            original_text=(
                f"{first.original_text}\n{second.original_text}\n"
                "完整单次招式总倍率为来源所列各段各一次相加，不推断额外次数。"
            ),
            skill_group=first.skill_group,
            damage_tags=first.damage_tags,
            multiplier_relation=MultiplierRelation.COMPLETE,
            multiplier_variants=(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1131:{key}"
                    ),
                    label="来源倍率相加",
                    parameter_name="完整招式总倍率",
                    multiplier=FixedMultiplier(
                        Resolved(first_multiplier.value.value + second_multiplier.value.value)
                    ),
                ),
            ),
            main_damage_event=new_ref,
        )
    )
    templates.append(replace(first_template, ref=new_ref, move_id=move_id))


def _static_anomaly_entries():
    physical_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1131:physical-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1131:physical-anomaly"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    physical_template = AttributeAnomalyDamageEventTemplate(
        ref=physical_ref,
        damage_dealer=SOUKAKU_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=SOUKAKU_ID,
        history_record_source=PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
    )
    physical_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1131:physical-anomaly"),
        character_id=SOUKAKU_ID,
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text="按规范静态单人100%积蓄物理异常，强击固定倍率713%，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1131:physical-anomaly"
                ),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=physical_ref,
    )

    ice_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1131:ice-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1131:ice-anomaly"),
        label="属性异常：碎冰（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    ice_template = AttributeAnomalyDamageEventTemplate(
        ref=ice_ref,
        damage_dealer=SOUKAKU_ID,
        element=Element.ICE,
        anomaly_triggerer=SOUKAKU_ID,
        history_record_source=ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ICE_ANOMALY_MOVE_ID,
    )
    ice_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1131:ice-anomaly"),
        character_id=SOUKAKU_ID,
        move_id=ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：碎冰（10秒满异常）",
        original_text="按规范静态单人100%积蓄冰异常；10秒碎冰倍率500%，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1131:ice-anomaly"),
                label="碎冰500%（10秒）",
                parameter_name="碎冰倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=ice_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1131:ice-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1131:ice-disorder"),
        label="紊乱：碎冰（默认最大剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=SOUKAKU_ID,
        element=Element.ICE,
        disorder_triggerer=SOUKAKU_ID,
        history_record_source=ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1131:ice-disorder"),
        character_id=SOUKAKU_ID,
        move_id=ICE_DISORDER_MOVE_ID,
        display_name="紊乱：碎冰（默认最大剩余时间）",
        original_text="按规范冰紊乱基础倍率450% + floor(t)×7.5%；t范围0–10秒，默认10秒，不模拟时序；使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1131:ice-disorder"),
                label="450% + floor(t) × 7.5%",
                parameter_name="冰紊乱倍率",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_ICE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=0.075,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining_seconds = ScenarioIntegerParameter(
        parameter_id=_ICE_DISORDER_REMAINING_SECONDS,
        label="冰异常剩余持续时间（秒）",
        original_text="按本次选定的剩余时间计算；范围0–10秒，默认10秒，不从战斗时序推断。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (physical_entry, ice_entry, disorder_entry),
        (physical_template, ice_template, disorder_template),
        remaining_seconds,
    )


def compile_soukaku(
    config: SoukakuCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=SOUKAKU_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=SOUKAKU_REVIEWED_MAPPING,
        id_namespace="character:1131",
    )
    entries = list(entries)
    templates = list(templates)
    diagnostics = list(direct_diagnostics)

    ex_total_note = _note(
        "ex-special:multi-click-total",
        "The EX source describes repeated clicks before an automatic finishing strike. This selected component's source value is resolved, but a full multi-click total is not inferred.",
        next(item.description for item in raw_record.moves if item.name == "强化特殊技：扇走蚊虫"),
    )
    direct_entry_indexes = {
        str(item.entry_id).rsplit(":", 1)[-1]: index
        for index, item in enumerate(entries)
    }
    for key in ("ex-swat-insects-continuous", "ex-swat-insects-windfield"):
        index = direct_entry_indexes[key]
        entries[index] = replace(entries[index], diagnostics=(ex_total_note,))

    entry_index = {
        str(item.entry_id).rsplit(":", 1)[-1]: item for item in entries
    }
    # The normal Special source explicitly proceeds from its windfield to a
    # finishing strike. Both source curves are single applications here.
    _complete_entry(
        first=entry_index["special-cool-lunch-field"],
        second=entry_index["special-cool-lunch-finisher"],
        templates=templates,
        entries=entries,
        key="special-cool-lunch-complete",
        label="特殊技：吹凉便当（风场与终结段，各一次）",
        move_id=MoveId("move:soukaku:special-cool-lunch-complete"),
    )
    _complete_entry(
        first=entry_index["flag-attack"],
        second=entry_index["flag-collect-attack"],
        templates=templates,
        entries=entries,
        key="flag-attack-and-collect",
        label="特殊技：集合啦！（展旗后收旗，各一次）",
        move_id=MoveId("move:soukaku:flag-attack-and-collect"),
    )
    _complete_entry(
        first=entry_index["flag-attack-quick"],
        second=entry_index["flag-collect-attack"],
        templates=templates,
        entries=entries,
        key="flag-quick-attack-and-collect",
        label="特殊技：集合啦！（快速展旗后收旗，各一次）",
        move_id=MoveId("move:soukaku:flag-quick-attack-and-collect"),
    )

    static_entries, static_templates, disorder_remaining = _static_anomaly_entries()
    entries.extend(static_entries)
    templates.extend(static_templates)

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    core_attack_percent = _number(
        core.description,
        r"等同于苍角(?P<value>[\d.]+)%初始攻击力",
        "Soukaku Core flag attack initial-ATK coefficient",
    ) / 100.0
    core_caps = tuple(
        float(match.group("value"))
        for match in re.finditer(
            r"最高不超过(?P<value>[\d.]+)点", _plain(core.description)
        )
    )
    if len(core_caps) != 2 or core_caps[1] != core_caps[0] * 2.0:
        raise ValueError("Soukaku Core must state the self and consumed-Vortex ATK caps")
    core_attack_cap = core_caps[0]
    core_attack_value = PanelStatDerivedValue(
        source_character_id=SOUKAKU_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
        coefficient=Resolved(core_attack_percent),
        cap_max=Resolved(core_attack_cap),
    )
    core_attack_effect = _modifier(
        "core:flag-attack-self-initial-atk",
        core_source,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        core_attack_value,
        target=EffectTarget.SELF,
    )
    core_transfer_note = _note(
        "core:flag-attack-transfer-recipient",
        "The self ATK increase is modeled from Soukaku's current flag-attack state. The text also transfers it to the corresponding entrant after Flag-triggered Quick Assist or Chain; the holder retention and simultaneous recipient scope are awaiting clarification, so no other character is assigned this buff.",
        core.description,
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:flag-attack-self-atk",
            core_source,
            f"核心被动：展旗当前自身攻击力+初始攻击力×{core_attack_percent:.1%}（上限{core_attack_cap:g}）",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(FLAG_ATTACK_BUFF_ACTIVE,),
            effects=(core_attack_effect,),
            diagnostics=(core_transfer_note,),
        ),
        _rule(
            "core:flag-attack-consumed-vortex-extra-atk",
            core_source,
            "核心被动：消耗涡流时展旗攻击力增益翻倍",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(FLAG_ATTACK_BUFF_ACTIVE, FLAG_CONSUMED_VORTEX),
            effects=(
                _modifier(
                    "core:flag-attack-consumed-vortex-extra-atk",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    core_attack_value,
                    target=EffectTarget.SELF,
                ),
            ),
        ),
    ]

    extra_ability_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    ice_damage_bonus = _number(
        core.extra_ability_description,
        r"冰属性伤害提升(?P<value>[\d.]+)%",
        "Soukaku Additional Ability Ice damage bonus",
    ) / 100.0
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "extra-ability:ice-damage",
            extra_ability_source,
            f"额外能力：当前展旗消耗涡流后全队冰属性伤害+{ice_damage_bonus:.0%}",
            core.extra_ability_description,
            extra_eligibility,
            conditions=(ICE_DAMAGE_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:ice-direct-and-anomaly-damage",
                    extra_ability_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(ice_damage_bonus),
                    target=EffectTarget.TEAM,
                    # Leave the type unrestricted: the source says Ice damage,
                    # and this is the ordinary elemental bonus region. Static
                    # anomaly records capture it once; Disorder does not read
                    # DAMAGE_NORMAL_BONUS as a second settlement region.
                    filters=(element_scope_filter(Element.ICE),),
                ),
            ),
        )
    )

    cinema4 = raw_record.mindscapes[3]
    cinema4_source = _source(
        "cinema-4", EffectSourceType.CINEMA, cinema4.name, cinema4.description
    )
    ice_resistance_reduction = _number(
        cinema4.description,
        r"冰属性伤害抗性降低(?P<value>[\d.]+)%",
        "Soukaku Cinema 4 Ice resistance reduction",
    ) / 100.0
    rules.append(
        _rule(
            "cinema4:enemy-ice-resistance-reduction",
            cinema4_source,
            f"4影：展旗命中后当前目标冰抗降低{ice_resistance_reduction:.0%}",
            cinema4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            conditions=(FLAG_ATTACK_HIT_ACTIVE,),
            effects=(
                _modifier(
                    "cinema4:enemy-ice-resistance-reduction",
                    cinema4_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(ice_resistance_reduction),
                    target=EffectTarget.ENEMY,
                    filters=(element_scope_filter(Element.ICE),),
                ),
            ) if config.cinema_level >= 4 else (),
        )
    )

    cinema6 = raw_record.mindscapes[5]
    cinema6_source = _source(
        "cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description
    )
    frost_banner_damage_bonus = _number(
        cinema6.description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Soukaku Cinema 6 Frost Banner damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema6:frost-banner-enhanced-basic-and-dash",
            cinema6_source,
            f"6影：霜染刃旗下强化普攻／冲刺伤害+{frost_banner_damage_bonus:.0%}",
            cinema6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            conditions=(FLAG_STATE_ACTIVE,),
            effects=(
                _modifier(
                    "cinema6:frost-banner-enhanced-basic-and-dash",
                    cinema6_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(frost_banner_damage_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(SOUKAKU_ID),
                        AnyFilter(
                            (
                                _event_filter("basic-frost-banner-1"),
                                _event_filter("basic-frost-banner-2"),
                                _event_filter("basic-frost-banner-3"),
                                _event_filter("dash-frost-banner"),
                            )
                        ),
                    ),
                ),
            ) if config.cinema_level >= 6 else (),
        )
    )

    for level in (1, 2, 3, 5):
        cinema = raw_record.mindscapes[level - 1]
        cinema_source = _source(
            f"cinema-{level}", EffectSourceType.CINEMA, cinema.name, cinema.description
        )
        if level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    cinema_source,
                    f"{level}影：技能等级提升",
                    cinema.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                )
            )
        else:
            source_note = ()
            if level == 1:
                source_note = (
                    _note(
                        "cinema1:duration",
                        "Cinema 1 extends Core and Additional Ability duration by 8 seconds; duration is not simulated.",
                        cinema.description,
                    ),
                )
            elif level == 2:
                source_note = (
                    _note(
                        "cinema2:random-resource",
                        "Cinema 2's 15% Vortex chance and Energy replacement are probability/resource behavior; no expected value, cooldown, or Energy result is produced.",
                        cinema.description,
                    ),
                )
            rules.append(
                _rule(
                    f"cinema{level}:source-only",
                    cinema_source,
                    f"{level}影：能量／涡流资源效果不在当前结果中模拟",
                    cinema.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                    diagnostics=source_note,
                )
            )

    defense_assist = next(
        item for item in raw_record.moves if item.name == "招架支援：防守战术"
    )
    rules.append(
        _rule(
            "assist-parry:daze-source-only",
            _source(
                "assist-parry:daze-source-only",
                EffectSourceType.SKILL,
                defense_assist.name,
                defense_assist.description,
            ),
            "招架支援：防守战术（来源列出失衡倍率）",
            defense_assist.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                _note(
                    "assist-parry:daze-only",
                    "This Support Defense action has source Daze ratios but no damage ratio; the result has no Daze output, so no damage entry is fabricated.",
                    defense_assist.description,
                ),
            ),
        )
    )

    conditions = (
        _condition(
            FLAG_STATE_ACTIVE,
            "当前处于霜染刃旗状态",
            "用户选择当前状态，不模拟持续时间或6/12次招式计数。",
        ),
        _condition(
            FLAG_ATTACK_BUFF_ACTIVE,
            "苍角当前持有展旗攻击力增益",
            core.description,
        ),
        _condition(
            FLAG_CONSUMED_VORTEX,
            "当前展旗攻击消耗了涡流",
            core.description,
        ),
        _condition(
            ICE_DAMAGE_BUFF_ACTIVE,
            "全队冰属性伤害增益当前有效",
            core.extra_ability_description,
        ),
        _condition(
            FLAG_ATTACK_HIT_ACTIVE,
            "展旗攻击当前已命中目标",
            cinema4.description,
        ),
    )
    diagnostics = tuple(direct_diagnostics)

    return build_definition(
        character_id=SOUKAKU_ID,
        role=CharacterRole.SUPPORT,
        element=Element.ICE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(disorder_remaining,),
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: SoukakuCompileConfig) -> None:
    if raw.character_id != SOUKAKU_ID or raw.name != "苍角" or raw.code_name != "Soukaku":
        raise ValueError("unexpected identity in Soukaku raw record")
    if raw.specialty != "支援" or raw.element != "冰属性" or raw.rarity != 3:
        raise ValueError("Soukaku raw role, element, or rank changed from reviewed source")
    if raw.faction != "对空洞特别行动部第六课":
        raise ValueError("Soukaku raw faction changed from reviewed source")
    if (
        raw.source_version != "3.2"
        or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1131.json"
    ):
        raise ValueError("Soukaku provenance must identify live Nanoka 3.2 character 1131")
    if raw.potential_details:
        raise ValueError("Soukaku 3.2 source does not have potential variants")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Soukaku raw source must contain seven Core levels and six Cinemas")
    if config.character_id != SOUKAKU_ID:
        raise ValueError("Soukaku compile config has an unexpected character ID")


__all__ = ["compile_soukaku"]
