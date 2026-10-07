"""Compile Lucy's reviewed live Nanoka 3.2 record."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import re

from core.types import (
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
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    SkillGroup,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
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
from .config import LucyCompileConfig
from .reviewed import (
    CHEER_ON_ACTIVE,
    FIRE_ANOMALY_MOVE_ID,
    FIRE_ANOMALY_RECORD_ID,
    FIRE_DISORDER_MOVE_ID,
    LUCY_ID,
    LUCY_REVIEWED_MAPPING,
    PIGS_ACTIVE,
)


_FIRE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:lucy:fire-disorder-remaining-seconds"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(
            f"{subject} must contain one source value; found {len(matches)}"
        )
    return float(matches[0].group("value"))


def _condition(
    condition_id: ScenarioConditionId, label: str, text: str
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(LUCY_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1151:{key}"),
        owner=LUCY_ID,
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
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1151:{key}"),
            source=source,
            owner=LUCY_ID,
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


def _note(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1151:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_fire_entries():
    record_id = AnomalyRecordId(FIRE_ANOMALY_RECORD_ID)
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1151:fire-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1151:fire-anomaly"),
        label="属性异常：灼烧（10秒，20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=LUCY_ID,
        element=Element.FIRE,
        anomaly_triggerer=LUCY_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1151:fire-anomaly"),
        character_id=LUCY_ID,
        move_id=FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（10秒，20跳）",
        original_text="按规范静态火属性异常；每0.5秒结算异常效果强度的50%，共20跳并使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    "variant:character:1151:fire-anomaly-tick"
                ),
                label="灼烧每跳50%（10秒20跳）",
                parameter_name="灼烧每跳倍率",
                multiplier=FixedMultiplier(Resolved(0.5)),
                repeat_count=20,
            ),
        ),
        main_damage_event=anomaly_ref,
    )
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1151:fire-disorder",
        semantic_id=DamageEventSemanticId("event:character:1151:fire-disorder"),
        label="紊乱：灼烧",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=LUCY_ID,
        element=Element.FIRE,
        disorder_triggerer=LUCY_ID,
        history_record_source=record_id,
        crit_rule=NoCritRule(),
        move_id=FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1151:fire-disorder"),
        character_id=LUCY_ID,
        move_id=FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧",
        original_text="按规范灼烧紊乱倍率；使用用户选择的当前剩余时间，不模拟战斗时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1151:fire-disorder"),
                label="灼烧紊乱",
                parameter_name="当前目标灼烧剩余时间",
                multiplier=FixedMultiplier(Resolved(4.5)),
                parameter_value_id=_FIRE_DISORDER_REMAINING_SECONDS,
                parameter_base_value=4.5,
                parameter_coefficient=1.0,
            ),
        ),
        main_damage_event=disorder_ref,
    )
    remaining = ScenarioIntegerParameter(
        parameter_id=_FIRE_DISORDER_REMAINING_SECONDS,
        label="当前目标灼烧剩余时间（秒）",
        original_text="由用户选择当前剩余时间；不回放灼烧时间轴。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (
        (anomaly_entry, disorder_entry),
        (anomaly_template, disorder_template),
        remaining,
    )


def _pig_source_entry(
    *,
    entry_key: str,
    display_name: str,
    source_name: str,
    original_text: str,
    element: Element,
    multiplier: float | Unresolved,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
    source_diagnostics: tuple[CalculationDiagnostic, ...] = (),
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    """Retain a known pig ratio without emitting an untyped follower hit.

    The actor/source snapshot is unresolved, so the relation blocks before an
    event can be instantiated. This keeps the selectable source and its raw
    ratio visible without allowing it to trigger character or engine effects.
    """

    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1151:{entry_key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1151:{entry_key}:main"),
        label=display_name,
        damage_type=DamageType.DIRECT,
        element=element,
    )
    template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=LUCY_ID,
        element=element,
        base_source=CurrentAttackValueSource(LUCY_ID),
        crit_rule=StandardCritRule(LUCY_ID),
        move_id=None,
    )
    unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            "The source ratio is retained, but the pig actor's ATK/Crit snapshot and event identity are not available. "
            "This entry is blocked before event creation and cannot trigger role or equipment effects."
        ),
        original_text=original_text,
    )
    diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId(
            f"source:character:1151:{entry_key}:follower-identity"
        ),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message=unresolved.notes,
        blocking=True,
        original_text=original_text,
    )
    variant_multiplier = multiplier
    if isinstance(multiplier, Unresolved):
        variant_multiplier = multiplier
    return (
        MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1151:{entry_key}"),
            character_id=LUCY_ID,
            move_id=None,
            display_name=display_name,
            original_text=original_text,
            skill_group=None,
            damage_tags=frozenset(),
            multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
            multiplier_variants=(
                MultiplierVariant(
                    variant_id=MultiplierVariantId(
                        f"variant:character:1151:{entry_key}:source-ratio"
                    ),
                    label="源倍率",
                    parameter_name=source_name,
                    multiplier=(
                        variant_multiplier
                        if isinstance(variant_multiplier, Unresolved)
                        else FixedMultiplier(Resolved(variant_multiplier))
                    ),
                ),
            ),
            main_damage_event=ref,
            condition_ids=condition_ids,
            diagnostics=(diagnostic, *source_diagnostics),
        ),
        template,
    )


def _reviewed_pig_curve(
    raw: NanokaRawRecord,
    config: LucyCompileConfig,
    *,
    source_name: str,
    parameter_name: str,
    source_skill_id: str,
    entry_key: str,
    display_name: str,
    element: Element,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate]:
    raw_moves = raw_move_index(raw)
    source_level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    source_diagnostics: list[CalculationDiagnostic] = []
    ratio = raw_multiplier(
        raw_moves,
        source_name,
        parameter_name,
        source_level,
        f"{LUCY_ID}:{entry_key}",
        source_diagnostics,
        source_skill_id,
    )
    if isinstance(ratio, Unresolved):
        display_text = f"{source_name}：{parameter_name}（曲线待定）"
    else:
        display_text = f"{display_name}（来源倍率{ratio:.3f}）"
    source = raw_moves[source_name]
    return _pig_source_entry(
        entry_key=entry_key,
        display_name=display_text,
        source_name=parameter_name,
        original_text=source.description or parameter_name,
        element=element,
        multiplier=ratio,
        condition_ids=condition_ids,
        source_diagnostics=tuple(source_diagnostics),
    )


def compile_lucy(
    config: LucyCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=LUCY_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=LUCY_REVIEWED_MAPPING,
        id_namespace="character:1151",
    )
    entries = list(entries)
    templates = list(templates)
    diagnostics = list(direct_diagnostics)
    basic_source_description = next(
        item.description
        for item in raw_record.moves
        if item.name == "普通攻击：淑女的球棍"
    )
    basic_derived_index = next(
        index
        for index, entry in enumerate(entries)
        if str(entry.entry_id) == "move-entry:character:1151:basic-3-derived"
    )
    basic_derived = entries[basic_derived_index]
    basic_derived_diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("review:character:1151:basic-3-derived-element"),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message=(
            "The raw Basic description states that the sequence deals Physical and Fire damage, "
            "but it does not assign the separately named third-stage-derived curve 1151003 to either element. "
            "The skill-list action IDs are a different namespace and do not identify this parameter curve. "
            "Its source ratio is retained, but this branch does not emit a damage event until the element is known."
        ),
        blocking=True,
        original_text=basic_source_description,
    )
    entries[basic_derived_index] = replace(
        basic_derived,
        display_name="普通攻击：淑女的球棍（三段派生，属性待确认）",
        multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
        original_text=basic_source_description,
        diagnostics=(basic_derived_diagnostic,),
    )
    pig_basic_source = "亲卫队小猪：抄家伙！"
    for key, label, parameter_name, source_skill_id, element in (
        ("pig-random-bat", "棒球棍", "棒球棍伤害倍率", "1151023", Element.PHYSICAL),
        ("pig-random-gloves", "拳套", "拳套伤害倍率", "1151024", Element.PHYSICAL),
        ("pig-random-slingshot", "弹弓", "弹弓伤害倍率", "1151025", Element.PHYSICAL),
    ):
        pig_entry, pig_template = _reviewed_pig_curve(
            raw_record,
            config,
            source_name=pig_basic_source,
            parameter_name=parameter_name,
            source_skill_id=source_skill_id,
            entry_key=key,
            display_name=f"亲卫队小猪：抄家伙！（{label}单次来源）",
            element=element,
            condition_ids=(PIGS_ACTIVE,),
        )
        entries.append(pig_entry)
        templates.append(pig_template)
    pig_swing_entry, pig_swing_template = _reviewed_pig_curve(
        raw_record,
        config,
        source_name="亲卫队小猪：回旋挥击！",
        parameter_name="回旋挥击伤害倍率",
        source_skill_id="1151026",
        entry_key="pig-revolving-swing",
        display_name="亲卫队小猪：回旋挥击！",
        element=Element.PHYSICAL,
        condition_ids=(PIGS_ACTIVE,),
    )
    entries.append(pig_swing_entry)
    templates.append(pig_swing_template)
    if config.cinema_level >= 6:
        cinema6_source_text = raw_record.mindscapes[5].description
        explosion_ratio = (
            _number(
                cinema6_source_text,
                r"亲卫队小猪(?P<value>[\d.]+)%攻击力",
                "Lucy Cinema 6 pig explosion multiplier",
            )
            / 100.0
        )
        explosion_entry, explosion_template = _pig_source_entry(
            entry_key="cinema6-pig-explosion",
            display_name="6影：亲卫队小猪落地爆炸（火伤，300%小猪攻击力）",
            source_name="落地爆炸伤害倍率",
            original_text=cinema6_source_text,
            element=Element.FIRE,
            multiplier=explosion_ratio,
            condition_ids=(CHEER_ON_ACTIVE,),
        )
        swing_entry, swing_template = _reviewed_pig_curve(
            raw_record,
            config,
            source_name="亲卫队小猪：回旋挥击！",
            parameter_name="回旋挥击伤害倍率",
            source_skill_id="1151026",
            entry_key="cinema6-pig-revolving-swing",
            display_name="6影：小猪爆炸后回旋挥击（一次）",
            element=Element.PHYSICAL,
            condition_ids=(CHEER_ON_ACTIVE,),
        )
        entries.extend((explosion_entry, swing_entry))
        templates.extend((explosion_template, swing_template))
    fire_entries, fire_templates, disorder_remaining = _static_fire_entries()
    entries.extend(fire_entries)
    templates.extend(fire_templates)

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
    special_level = effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    # Read both arithmetic terms directly; the raw expression uses the Special Attack skill level.
    cheer_description = next(
        item.description for item in raw_record.moves if item.name == "加油！"
    )
    plain_cheer_description = _plain(cheer_description)
    percent_match = re.search(
        r"{CAL:(?P<base>[\d.]+)\+AvatarSkillLevel\(1\)\*(?P<growth>[\d.]+),1,2}%",
        plain_cheer_description,
    )
    flat_match = re.search(
        r"\+{CAL:(?P<base>[\d.]+)\+AvatarSkillLevel\(1\)\*(?P<growth>[\d.]+),1,2}",
        plain_cheer_description,
    )
    cap_match = re.search(r"最高不超过(?P<value>[\d.]+)点", plain_cheer_description)
    if percent_match is None or flat_match is None or cap_match is None:
        raise ValueError("Lucy Cheer On source must expose both CAL terms and its cap")
    cheer_percent = (
        float(percent_match.group("base"))
        + special_level * float(percent_match.group("growth"))
    ) / 100.0
    cheer_flat = float(flat_match.group("base")) + special_level * float(
        flat_match.group("growth")
    )
    cheer_cap = float(cap_match.group("value"))

    pig_source_note = _note(
        "core:pig-actor-model",
        "The source states that pigs join when Lucy uses Special/EX, inherit Lucy's ATK/Impact/Anomaly Proficiency, and that their random attacks and deferred spin attacks can occur multiple times. Source ratios remain selectable, but the current actor model has no pig stat owner or attack-history counter, so no follower hit is added to Lucy's own Direct events; Lucy's own source moves and team Cheer On panel effect remain available.",
        core.description,
    )
    cheer_source = _source(
        "cheer-on", EffectSourceType.SPECIAL_MECHANISM, "加油！", cheer_description
    )
    cheer_value = PanelStatDerivedValue(
        source_character_id=LUCY_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
        coefficient=Resolved(cheer_percent),
        base=Resolved(cheer_flat),
        cap_max=Resolved(cheer_cap),
    )
    cheer_noncharacter_note = _note(
        "cheer-on:non-character-recipients",
        "The source also names Bangboo and pigs as recipients. This calculation request exposes character snapshots only, so the panel buff is applied to the active agent team; no Bangboo/pig panel row is fabricated.",
        cheer_description,
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:pig-followers",
            core_source,
            "核心被动：亲卫队小猪继承属性（当前输出不生成小猪自动攻击）",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(pig_source_note,),
        ),
        _rule(
            "extra-ability:pig-crit-inheritance",
            extra_source,
            "额外能力：满足队伍条件时小猪继承露西暴击属性",
            core.extra_ability_description,
            (
                RuleEligibility.ELIGIBLE
                if config.additional_ability_eligible
                else RuleEligibility.INELIGIBLE
            ),
            diagnostics=(
                _note(
                    "extra-ability:pig-actor-model",
                    "This condition is evaluated from the actual team's same-element, same-faction, or Rupture membership. It affects follower inheritance only; it does not change Lucy's own Direct moves.",
                    core.extra_ability_description,
                ),
            ),
        ),
        _rule(
            "cheer-on:team-attack",
            cheer_source,
            f"加油！：全队攻击力+初始攻击力×{cheer_percent:.1%}+{cheer_flat:g}（上限{cheer_cap:g}）",
            cheer_description,
            RuleEligibility.ELIGIBLE,
            conditions=(CHEER_ON_ACTIVE,),
            effects=(
                _modifier(
                    "cheer-on:team-attack",
                    cheer_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    cheer_value,
                    target=EffectTarget.TEAM,
                ),
            ),
            diagnostics=(cheer_noncharacter_note,),
        ),
    ]
    basic_description = basic_source_description
    pig_swing_unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            "The Basic 4 prose explicitly triggers Bodyguard Pig: Revolving Swing when pigs are on the field; the raw swing curve is 592%. "
            "The current calculator has no separate pig stat owner or supported count for the on-field pig group, so this child remains local-unresolved without instantiating a fake Direct hit."
        ),
        original_text=basic_description,
    )
    basic_four_swing_source = _source(
        "basic-four-pig-swing",
        EffectSourceType.SKILL,
        "普通攻击四段：亲卫队小猪回旋挥击",
        basic_description,
    )
    rules.append(
        _rule(
            "skill:basic-four-pig-swing",
            basic_four_swing_source,
            "普通攻击四段：当前小猪在场时的回旋挥击（倍率已知，仆从属性待明确）",
            basic_description,
            RuleEligibility.ELIGIBLE,
            conditions=(PIGS_ACTIVE,),
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1151:basic-four-pig-swing"
                        ),
                        source=basic_four_swing_source,
                        owner=LUCY_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            DamageDealerFilter(LUCY_ID),
                            EventTemplateIdFilter(
                                EventTemplateId("template:character:1151:basic-4:main")
                            ),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        unresolved_template=pig_swing_unresolved,
                        unique_per_source_event=True,
                    ),
                ),
            ),
        )
    )

    cinema4 = raw_record.mindscapes[3]
    c4_source = _source(
        "cinema-4", EffectSourceType.CINEMA, cinema4.name, cinema4.description
    )
    c4_crit_damage = (
        _number(
            cinema4.description,
            r"暴击伤害额外提升(?P<value>[\d.]+)%",
            "Lucy Cinema 4 team Crit Damage",
        )
        / 100.0
    )
    rules.append(
        _rule(
            "cinema4:cheer-on-team-crit-damage",
            c4_source,
            f"4影：加油状态下全队暴击伤害+{c4_crit_damage:.0%}",
            cinema4.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 4
                else RuleEligibility.INELIGIBLE
            ),
            conditions=(CHEER_ON_ACTIVE,),
            effects=(
                (
                    _modifier(
                        "cinema4:cheer-on-team-crit-damage",
                        c4_source,
                        CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                        Resolved(c4_crit_damage),
                        target=EffectTarget.TEAM,
                    ),
                )
                if config.cinema_level >= 4
                else ()
            ),
        )
    )

    cinema6 = raw_record.mindscapes[5]
    c6_source = _source(
        "cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description
    )
    c6_unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            "The source supplies the pig explosion as 300% of pig ATK and one pig Revolving Swing after the explosion (source ratio 592%). "
            "The pig's combat stat/crit owner is not represented as a separate actor, so only these child events are left unresolved; the triggering teammate EX event remains calculated."
        ),
        original_text=cinema6.description,
    )
    team_ex_filters = (
        DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
        # A teammate EX may be a Rupture/Penetration event; only the real EX
        # tag and non-Lucy dealer identity are source constraints.
        NotFilter(DamageDealerFilter(LUCY_ID)),
    )
    c6_effects = tuple(
        EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId(f"effect:character:1151:cinema6:{key}"),
                source=c6_source,
                owner=LUCY_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=team_ex_filters,
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                unresolved_template=c6_unresolved,
                unique_per_source_event=True,
            ),
        )
        for key in ("pig-explosion", "pig-revolving-swing")
    )
    c6_source_note = _note(
        "cinema6:duration-and-cap",
        "Cinema 6 extends the current Cheer On state and has a three-extension cap/refresh rule; duration and trigger history are not replayed. The known explosion and subsequent swing are kept as local unresolved child events until the follower actor's inherited stat source is representable.",
        cinema6.description,
    )
    rules.append(
        _rule(
            "cinema6:pig-followup",
            c6_source,
            "6影：队友强化特殊技命中后的小猪爆炸与回旋挥击",
            cinema6.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 6
                else RuleEligibility.INELIGIBLE
            ),
            conditions=(CHEER_ON_ACTIVE,),
            effects=c6_effects if config.cinema_level >= 6 else (),
            diagnostics=(c6_source_note,),
        )
    )

    for level in (1, 2, 3, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(
            f"cinema-{level}", EffectSourceType.CINEMA, cinema.name, cinema.description
        )
        if level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    source,
                    f"{level}影：技能等级提升",
                    cinema.description,
                    (
                        RuleEligibility.ELIGIBLE
                        if config.cinema_level >= level
                        else RuleEligibility.INELIGIBLE
                    ),
                )
            )
        else:
            note = _note(
                f"cinema{level}:resource-or-duration",
                "Energy gain, trigger limits, and buff duration are source-only; the calculator keeps current Cheer On as an explicit state and does not replay time or Energy.",
                cinema.description,
            )
            rules.append(
                _rule(
                    f"cinema{level}:source-only",
                    source,
                    f"{level}影：能量／持续时间效果不在当前结果中模拟",
                    cinema.description,
                    (
                        RuleEligibility.ELIGIBLE
                        if config.cinema_level >= level
                        else RuleEligibility.INELIGIBLE
                    ),
                    diagnostics=(note,),
                )
            )

    defense_assist = next(
        item for item in raw_record.moves if item.name == "招架支援：安全上垒！"
    )
    assist_source = _source(
        "assist-parry:daze-source-only",
        EffectSourceType.SKILL,
        defense_assist.name,
        defense_assist.description,
    )
    rules.append(
        _rule(
            "assist-parry:daze-source-only",
            assist_source,
            "招架支援：安全上垒！（来源列出失衡倍率）",
            defense_assist.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                _note(
                    "assist-parry:daze-only",
                    "This Defense Assist has Daze values but no damage ratio; the current result has no Daze output, so no damage entry is fabricated.",
                    defense_assist.description,
                ),
            ),
        )
    )

    conditions = (
        _condition(
            PIGS_ACTIVE,
            "亲卫队小猪当前在场",
            basic_description,
        ),
        _condition(
            CHEER_ON_ACTIVE,
            "加油！当前生效",
            "由用户选择当前状态；不模拟平直球10秒/高飞球15秒持续时间或刷新过程。",
        ),
    )
    # Random pig attacks, the pig ATK inheritance details and delayed spin
    # counts are documented on the affected Core/Cinema rules; they do not
    # block Lucy's explicitly parameterized direct actions.
    return build_definition(
        character_id=LUCY_ID,
        role=CharacterRole.SUPPORT,
        element=Element.FIRE,
        source=_source(
            "character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(disorder_remaining,),
        diagnostics=tuple(diagnostics),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(LUCY_ID))


def _validate_raw_record(raw: NanokaRawRecord, config: LucyCompileConfig) -> None:
    if raw.character_id != LUCY_ID or raw.name != "露西" or raw.code_name != "Lucy":
        raise ValueError("unexpected identity in Lucy raw record")
    if raw.specialty != "支援" or raw.element != "火属性" or raw.rarity != 3:
        raise ValueError("Lucy raw role, element, or rank changed from reviewed source")
    if raw.faction != "卡吕冬之子":
        raise ValueError("Lucy raw faction changed from reviewed source")
    if (
        raw.source_version != "3.2"
        or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1151.json"
    ):
        raise ValueError("Lucy provenance must identify live Nanoka 3.2 character 1151")
    if raw.potential_details:
        raise ValueError("Lucy 3.2 source does not have potential variants")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Lucy source must contain seven Core levels and six Cinemas")
    if config.character_id != LUCY_ID:
        raise ValueError("Lucy compile config has an unexpected character ID")


__all__ = ["compile_lucy", "load_raw_record"]
