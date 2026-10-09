"""Compile Orphie & Magus's reviewed Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    AnyFilter,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    BattleEventKind,
    CalculationNode,
    CharacterId,
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
    ElementFilter,
    EventCreationEffect,
    EventCreationResult,
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
    SkillGroup,
    SnapshotRule,
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
    UnresolvedDamageEventTemplate,
)
from .config import ORPHIE_MAGUS_ID, OrphieMagusCompileConfig
from .reviewed import (
    ORPHIE_ASSIST_STRIKE_MOVE_ID,
    ORPHIE_BASIC_MOVE_ID,
    ORPHIE_CHAIN_MOVE_ID,
    ORPHIE_DASH_MOVE_ID,
    ORPHIE_EX_CHARGE_MOVE_ID,
    ORPHIE_EX_FINISHER_MOVE_ID,
    ORPHIE_FOCUS_ACTIVE,
    ORPHIE_ID,
    ORPHIE_MAGUS_REVIEWED_MAPPING,
    ORPHIE_QUICK_ASSIST_MOVE_ID,
    ORPHIE_SPECIAL_AUTOFIRE_MOVE_ID,
    ORPHIE_SPECIAL_MOVE_ID,
    ORPHIE_ULTIMATE_ATTACK_BUFF_ACTIVE,
    ORPHIE_ULTIMATE_MOVE_ID,
)


_FIRE_ANOMALY_RECORD_ID = AnomalyRecordId("anomaly:character:1301:fire-burn")
_FIRE_ANOMALY_MOVE_ID = MoveId("move:orphie-magus:fire-burn")
_FIRE_DISORDER_MOVE_ID = MoveId("move:orphie-magus:fire-disorder")
_FIRE_ANOMALY_TEMPLATE_ID = EventTemplateId("template:character:1301:fire-burn")
_FIRE_DISORDER_TEMPLATE_ID = EventTemplateId("template:character:1301:fire-disorder")
_C6_EXTRA_FIRE_TEMPLATE_ID = EventTemplateId("template:character:1301:cinema6-extra-fire")
_C6_EXTRA_FIRE_ENTRY_ID = MoveEntryId("move-entry:character:1301:cinema6-extra-fire")
_FIRE_DISORDER_HALF_SECONDS = ScenarioParameterId(
    "parameter:orphie-magus:fire-disorder-half-seconds"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _source(
    key: str,
    kind: EffectSourceType,
    label: str,
    text: str | None,
) -> RuleSource:
    return source_for(ORPHIE_ID, key, kind, label, text)


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    text: str,
    value: bool = False,
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
    conditions=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1301:{key}"),
        owner=ORPHIE_ID,
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
    recipient: CharacterId | None = None,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1301:{key}"),
            source=source,
            owner=ORPHIE_ID,
            target=target,
            recipient_character_id=recipient,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _unresolved_effect(
    key: str,
    source: RuleSource,
    *,
    parent_template_ids: tuple[EventTemplateId, ...],
    original_text: str,
    notes: str,
) -> EventCreationEffect:
    parent_filter = (
        EventTemplateIdFilter(parent_template_ids[0])
        if len(parent_template_ids) == 1
        else AnyFilter(tuple(EventTemplateIdFilter(item) for item in parent_template_ids))
    )
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1301:{key}"),
            source=source,
            owner=ORPHIE_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(ORPHIE_ID),
                parent_filter,
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=Unresolved(
                reason=UnresolvedReason.AMBIGUOUS_TEXT,
                notes=notes,
                original_text=original_text,
            ),
        ),
    )


def _unresolved_source_entries(
    raw: NanokaRawRecord,
    config: OrphieMagusCompileConfig,
) -> tuple[tuple[MoveCalculationEntry, ...], tuple[UnresolvedDamageEventTemplate, ...], tuple[CalculationDiagnostic, ...]]:
    """Keep mixed-element source ratios visible without inventing Direct events."""

    raw_moves = raw_move_index(raw)
    specs = (
        (
            "basic-stage-1",
            "普通攻击：高压火枪",
            "一段伤害倍率",
            "1301001",
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            "普通攻击：高压火枪（一段，元素待确认）",
        ),
        (
            "basic-stage-2",
            "普通攻击：高压火枪",
            "二段伤害倍率",
            "1301002",
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            "普通攻击：高压火枪（二段，元素待确认）",
        ),
        (
            "basic-stage-3",
            "普通攻击：高压火枪",
            "三段伤害倍率",
            "1301003",
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            "普通攻击：高压火枪（三段，元素待确认）",
        ),
        (
            "basic-stage-4",
            "普通攻击：高压火枪",
            "四段伤害倍率",
            "1301004",
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            "普通攻击：高压火枪（四段，元素待确认）",
        ),
        (
            "basic-stage-5",
            "普通攻击：高压火枪",
            "五段伤害倍率",
            "1301005",
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
            "普通攻击：高压火枪（五段，元素待确认）",
        ),
        (
            "dodge-counter",
            "闪避反击：反攻战机",
            "伤害倍率",
            "1301013",
            SkillGroup.DODGE,
            frozenset({DamageTag.DODGE_COUNTER}),
            "闪避反击：反攻战机（元素待确认）",
        ),
        (
            "quick-assist",
            "快速支援：焦痕劈斩",
            "伤害倍率",
            "1301017",
            SkillGroup.ASSIST,
            frozenset({DamageTag.ASSIST}),
            "快速支援：焦痕劈斩（元素待确认）",
        ),
    )
    entries: list[MoveCalculationEntry] = []
    templates: list[UnresolvedDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for key, source_name, parameter_name, curve_id, group, tags, label in specs:
        source_move = raw_moves[source_name]
        ratio = raw_multiplier(
            raw_moves,
            source_name,
            parameter_name,
            effective_skill_level(config, group),
            f"{ORPHIE_ID}:{key}",
            [],
            source_skill_id=curve_id,
        )
        if isinstance(ratio, Unresolved):
            raise ValueError(f"Orphie source ratio is missing for {key}")
        unresolved = Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_TEXT,
            notes=(
                f"已知来源倍率为{ratio:.4f}；原文只给出物理与火属性伤害的组合描述，"
                "该招式的具体元素尚未按阶段说明，因此不发射猜测的Direct事件。"
            ),
            original_text=source_move.description,
        )
        ref = DamageEventTemplateRef(
            template_id=EventTemplateId(
                f"template:character:1301:{key}:unresolved"
            ),
            semantic_id=DamageEventSemanticId(
                f"event:character:1301:{key}:unresolved"
            ),
            label=label,
            damage_type=DamageType.DIRECT,
            skill_group=group,
            damage_tags=tags,
        )
        template = UnresolvedDamageEventTemplate(
            ref=ref,
            damage_dealer=ORPHIE_ID,
            move_id=None,
            unresolved=unresolved,
        )
        diagnostic = CalculationDiagnostic(
            diagnostic_id=DiagnosticId(
                f"unsupported:character:1301:{key}:element"
            ),
            kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
            message=unresolved.notes,
            blocking=True,
            original_text=source_move.description,
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(f"move-entry:character:1301:{key}"),
                character_id=ORPHIE_ID,
                move_id=None,
                display_name=label,
                original_text=source_move.description,
                skill_group=group,
                damage_tags=tags,
                multiplier_relation=MultiplierRelation.UNRESOLVED_RELATION,
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId(
                            f"variant:character:1301:{key}:known-ratio"
                        ),
                        label=f"已知来源倍率{ratio:.4f}（元素待确认）",
                        parameter_name=parameter_name,
                        multiplier=FixedMultiplier(Resolved(ratio)),
                    ),
                ),
                main_damage_event=ref,
                diagnostics=(diagnostic,),
            )
        )
        templates.append(template)
        diagnostics.append(diagnostic)
    return tuple(entries), tuple(templates), tuple(diagnostics)


def _static_fire_entries(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id=_FIRE_ANOMALY_TEMPLATE_ID,
        semantic_id=DamageEventSemanticId("event:character:1301:fire-burn"),
        label="属性异常：灼烧（单跳50%，10秒20跳）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.FIRE,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=ORPHIE_ID,
        element=Element.FIRE,
        anomaly_triggerer=ORPHIE_ID,
        history_record_source=_FIRE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_FIRE_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1301:fire-anomaly"),
        character_id=ORPHIE_ID,
        move_id=_FIRE_ANOMALY_MOVE_ID,
        display_name="属性异常：灼烧（单跳50%，10秒20跳）",
        original_text="静态单人100%火属性异常记录；每0.5秒结算异常效果强度的50%，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.UNIT_REPEAT,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1301:fire-anomaly-tick"),
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
        semantic_id=DamageEventSemanticId("event:character:1301:fire-disorder"),
        label="紊乱：灼烧（当前剩余0.5秒单位）",
        damage_type=DamageType.DISORDER,
        element=Element.FIRE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=ORPHIE_ID,
        element=Element.FIRE,
        disorder_triggerer=ORPHIE_ID,
        history_record_source=_FIRE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=_FIRE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1301:fire-disorder"),
        character_id=ORPHIE_ID,
        move_id=_FIRE_DISORDER_MOVE_ID,
        display_name="紊乱：灼烧（当前剩余时间）",
        original_text="灼烧紊乱倍率为450% + 当前剩余0.5秒单位 × 50%；不模拟时间轴。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1301:fire-disorder"),
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


def compile_orphie_magus(
    config: OrphieMagusCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, templates, direct_diagnostics = compile_direct_moves(
        character_id=ORPHIE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=ORPHIE_MAGUS_REVIEWED_MAPPING,
    )
    entries = list(entries)
    templates = list(templates)
    light_eater_index = next(
        index for index, item in enumerate(entries)
        if str(item.entry_id) == "move-entry:character:1301:special-light-eater"
    )
    light_eater = entries[light_eater_index]
    light_eater_source = raw_move_index(raw_record)["特殊技：蚀光一闪"]
    entries[light_eater_index] = replace(
        light_eater,
        diagnostics=(
            *light_eater.diagnostics,
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(
                    "unsupported:character:1301:special-light-eater:four-hit-total"
                ),
                kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
                message=(
                    "来源明确有四次激光追加攻击，但只提供一条伤害倍率；"
                    "当前保留一个来源曲线，不把它猜成四次重复或整段合计。"
                ),
                blocking=True,
                original_text=light_eater_source.description,
            ),
        ),
    )
    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        interval_diagnostic = CalculationDiagnostic(
            diagnostic_id=DiagnosticId(
                "unsupported:character:1301:cinema6:laser-extra-interval-count"
            ),
            kind=DiagnosticKind.MISSING_DATA,
            message=(
                "影画6额外火伤的250%单次倍率可查；"
                "持续激光期间每0.5秒触发的总次数不模拟，因此父招式结果为局部部分。"
            ),
            blocking=True,
            original_text=cinema6.description,
        )
        for entry_key in (
            "ex-special-heat-charge",
            "ultimate",
            "ultimate-extension",
        ):
            entry_index = next(
                index for index, item in enumerate(entries)
                if str(item.entry_id) == f"move-entry:character:1301:{entry_key}"
            )
            entries[entry_index] = replace(
                entries[entry_index],
                diagnostics=(*entries[entry_index].diagnostics, interval_diagnostic),
            )
    unresolved_entries, unresolved_templates, unresolved_diagnostics = (
        _unresolved_source_entries(raw_record, config)
    )
    entries.extend(unresolved_entries)
    templates.extend(unresolved_templates)
    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []
    core = raw_record.core_levels[config.core_level - 1]
    core_text = core.description
    core_source = _source("core", EffectSourceType.CORE_PASSIVE, core.name, core_text)

    focus_active = ORPHIE_FOCUS_ACTIVE
    conditions.append(
        _condition(focus_active, "当前全队准星聚焦生效", core_text)
    )
    ultimate_attack_buff_active = ScenarioConditionId(
        "condition:orphie-magus:ultimate-attack-buff-active"
    )
    if config.cinema_level >= 2:
        conditions.append(
            _condition(
                ultimate_attack_buff_active,
                "终结技后的攻击力提升当前生效",
                raw_record.mindscapes[1].description,
            )
        )

    own_crit_rate = _number(
        core_text,
        r"暴击率提升(?P<value>[\d.]+)%",
        "Orphie Core Crit Rate",
    ) / 100.0
    own_after_attack_bonus = _number(
        core_text,
        r"\[追加攻击\]造成的伤害提升(?P<value>[\d.]+)%",
        "Orphie Core Follow-up Damage Bonus",
    ) / 100.0
    focus_attack_base = _number(
        core_text,
        r"代理人拥有\[准星聚焦\]效果时，攻击力提升(?P<value>[\d.]+)点",
        "Orphie Focus Attack Bonus",
    )
    focus_attack_cap = _number(
        core_text,
        r"初始提升与额外提升总共不超过(?P<value>[\d.]+)点",
        "Orphie Focus Attack Cap",
    )
    focus_attack_per_tenth = _number(
        core_text,
        r"每拥有0\.1点初始能量自动回复，攻击力额外提升(?P<value>[\d.]+)点",
        "Orphie Focus Attack Energy Coefficient",
    )
    focus_er_threshold = _number(
        core_text,
        r"初始能量自动回复大于等于(?P<value>[\d.]+)点",
        "Orphie Focus Initial Energy Threshold",
    )
    focus_attack_effects = []
    for recipient in config.focus_recipient_ids:
        suffix = str(recipient).replace(":", "-")
        focus_attack_effect = _modifier(
            f"core:focus-attack:{suffix}",
            core_source,
            CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            PanelStatDerivedValue(
                source_character_id=ORPHIE_MAGUS_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
                coefficient=Resolved(focus_attack_per_tenth),
                base=Resolved(focus_attack_base),
                cap_max=Resolved(focus_attack_cap),
                threshold=Resolved(focus_er_threshold),
                step_size=Resolved(0.1),
                minimum=Resolved(focus_er_threshold),
            ),
            target=EffectTarget.RECIPIENT,
            recipient=recipient,
        )
        focus_attack_effects.append(focus_attack_effect)
    rules.append(
        _rule(
            "core:focus-attack",
            core_source,
            f"当前准星聚焦：队伍面板攻击力+{focus_attack_base:g}及初始ER增幅",
            core_text,
            RuleEligibility.ELIGIBLE,
            effects=tuple(focus_attack_effects),
            conditions=(focus_active,),
        )
    )
    rules.append(
        _rule(
            "core:focus-attack-source-note",
            core_source,
            f"核心被动：准星聚焦初始攻击力+{focus_attack_base:g}，上限{focus_attack_cap:g}",
            core_text,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId("unsupported:character:1301:core:focus-duration"),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message="准星聚焦的触发、刷新、延长与持续时间不模拟；面板增幅按当前状态选择。",
                    blocking=False,
                    original_text=core_text,
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "core:own-crit-and-follow-up",
            core_source,
            f"核心被动：自身暴击率+{own_crit_rate:.1%}、追加攻击伤害+{own_after_attack_bonus:.1%}",
            core_text,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:own-crit-rate",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(own_crit_rate),
                    target=EffectTarget.SELF,
                ),
                _modifier(
                    "core:own-follow-up-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(own_after_attack_bonus),
                    target=EffectTarget.SELF,
                    filters=(DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),),
                ),
            ),
        )
    )

    if config.cinema_level >= 1:
        cinema1 = raw_record.mindscapes[0]
        c1_fire_ignore = _number(
            cinema1.description,
            r"无视(?P<value>[\d.]+)%火属性伤害抗性",
            "Orphie Cinema 1 Fire Resistance Ignore",
        ) / 100.0
        c1_focus_bonus = _number(
            cinema1.description,
            r"拥有\[准星聚焦\]的代理人攻击造成的伤害提升(?P<value>[\d.]+)%",
            "Orphie Cinema 1 Focus Damage Bonus",
        ) / 100.0
        cinema1_source = _source(
            "cinema1:focus-and-fire-ignore",
            EffectSourceType.CINEMA,
            cinema1.name,
            cinema1.description,
        )
        c1_fire_entry_keys = (
            "special-light-eater",
            "ex-special-red-whirlpool",
            "ex-special-heat-charge",
            "ex-special-blaze-burst",
        )
        c1_fire_templates = tuple(
            next(
                item.main_damage_event.template_id
                for item in entries
                if str(item.entry_id) == f"move-entry:character:1301:{key}"
            )
            for key in c1_fire_entry_keys
        )
        rules.append(
            _rule(
                "cinema1:focus-holder-damage",
                cinema1_source,
                f"1影：准星聚焦代理人伤害+{c1_focus_bonus:.0%}",
                cinema1.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema1:focus-holder-damage",
                        cinema1_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(c1_focus_bonus),
                        target=EffectTarget.TEAM,
                    ),
                ),
                conditions=(focus_active,),
            )
        )
        rules.append(
            _rule(
                "cinema1:fire-resistance-ignore",
                cinema1_source,
                f"1影：指定火招式无视火抗{c1_fire_ignore:.0%}",
                cinema1.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema1:fire-resistance-ignore",
                        cinema1_source,
                        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                        Resolved(c1_fire_ignore),
                        target=EffectTarget.SELF,
                        filters=(
                            DamageTypeFilter(DamageType.DIRECT),
                            ElementFilter(Element.FIRE),
                            AnyFilter(tuple(EventTemplateIdFilter(item) for item in c1_fire_templates)),
                        ),
                    ),
                    *(
                        (
                            _unresolved_effect(
                                "cinema1:cinema6-extra-fire-resistance-scope",
                                cinema1_source,
                                parent_template_ids=(_C6_EXTRA_FIRE_TEMPLATE_ID,),
                                original_text=cinema1.description,
                                notes=(
                                    "1影火抗无视明确适用于指定强化特殊技；"
                                    "影画6额外包继承强化特殊技身份，但其触发父招式可能为终结技，"
                                    "此包是否享受该抗性无视尚未确认。"
                                ),
                            ),
                        )
                        if config.cinema_level >= 6
                        else ()
                    ),
                ),
            )
        )

    if config.cinema_level >= 2:
        cinema2 = raw_record.mindscapes[1]
        ult_atk_bonus = _number(
            cinema2.description,
            r"自身的攻击力提升(?P<value>[\d.]+)%",
            "Orphie Cinema 2 Ultimate Attack Bonus",
        ) / 100.0
        cinema2_source = _source(
            "cinema2:ultimate-attack",
            EffectSourceType.CINEMA,
            cinema2.name,
            cinema2.description,
        )
        rules.append(
            _rule(
                "cinema2:ultimate-attack",
                cinema2_source,
                f"2影：终结技后的自身攻击力+{ult_atk_bonus:.0%}",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "cinema2:ultimate-attack",
                        cinema2_source,
                        CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                        Resolved(ult_atk_bonus),
                        target=EffectTarget.SELF,
                    ),
                ),
                conditions=(ultimate_attack_buff_active,),
                diagnostics=(
                    CalculationDiagnostic(
                        diagnostic_id=DiagnosticId("unsupported:character:1301:cinema2:uptime"),
                        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                        message="此状态由终结技触发并持续45秒；不模拟剩余时间，按当前状态选择。",
                        blocking=False,
                        original_text=cinema2.description,
                    ),
                ),
            )
        )

    if config.additional_ability_eligible:
        extra = raw_record.extra_ability_description
        extra_source = _source(
            "extra-ability:focus-follow-up-defense-ignore",
            EffectSourceType.ADDITIONAL_ABILITY,
            raw_record.extra_ability_name,
            extra,
        )
        follow_up_ignore = _number(
            extra,
            r"\[追加攻击\]伤害无视(?P<value>[\d.]+)%防御力",
            "Orphie Additional Ability Follow-up Defense Ignore",
        ) / 100.0
        rules.append(
            _rule(
                "extra-ability:focus-follow-up-defense-ignore",
                extra_source,
                f"额外能力：准星聚焦持有者的追加攻击无视{follow_up_ignore:.0%}防御",
                extra,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "extra-ability:focus-follow-up-defense-ignore",
                        extra_source,
                        CalculationNode.DAMAGE_DEFENSE_IGNORE,
                        Resolved(follow_up_ignore),
                        target=EffectTarget.TEAM,
                        filters=(DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),),
                    ),
                ),
                conditions=(focus_active,),
            )
        )
    else:
        extra = raw_record.extra_ability_description
        rules.append(
            _rule(
                "extra-ability:focus-follow-up-defense-ignore",
                _source(
                    "extra-ability:focus-follow-up-defense-ignore",
                    EffectSourceType.ADDITIONAL_ABILITY,
                    raw_record.extra_ability_name,
                    extra,
                ),
                "额外能力：准星聚焦持有者的追加攻击无视防御",
                extra,
                RuleEligibility.INELIGIBLE,
            )
        )

    if config.cinema_level >= 4:
        cinema4 = raw_record.mindscapes[3]
        c4_bonus = _number(
            cinema4.description,
            r"造成的伤害提高(?P<value>[\d.]+)%",
            "Orphie Cinema 4 Enhanced Special/Ultimate Damage Bonus",
        ) / 100.0
        cinema4_source = _source(
            "cinema4:charge-and-ultimate-damage",
            EffectSourceType.CINEMA,
            cinema4.name,
            cinema4.description,
        )
        charge_ref = next(
            item.main_damage_event for item in entries
            if str(item.entry_id) == "move-entry:character:1301:ex-special-heat-charge"
        )
        ultimate_ref = next(
            item.main_damage_event for item in entries
            if str(item.entry_id) == "move-entry:character:1301:ultimate"
        )
        ultimate_extension_ref = next(
            item.main_damage_event for item in entries
            if str(item.entry_id) == "move-entry:character:1301:ultimate-extension"
        )
        ultimate_extension_ref = next(
            item.main_damage_event for item in entries
            if str(item.entry_id) == "move-entry:character:1301:ultimate-extension"
        )
        c4_effects = [
            _modifier(
                "cinema4:charge-and-ultimate-damage",
                cinema4_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(c4_bonus),
                target=EffectTarget.SELF,
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(ORPHIE_ID),
                    AnyFilter(
                        (
                            EventTemplateIdFilter(charge_ref.template_id),
                            EventTemplateIdFilter(ultimate_ref.template_id),
                            EventTemplateIdFilter(ultimate_extension_ref.template_id),
                            EventTemplateIdFilter(ultimate_extension_ref.template_id),
                        )
                    ),
                ),
            )
        ]
        if config.cinema_level >= 6:
            c4_effects.append(
                _unresolved_effect(
                    "cinema4:cinema6-extra-fire-scope",
                    cinema4_source,
                    parent_template_ids=(_C6_EXTRA_FIRE_TEMPLATE_ID,),
                    original_text=cinema4.description,
                    notes=(
                        "4影的40%增伤明确作用于蓄热充能和终结技；"
                        "影画6额外火伤虽视为强化特殊技，是否继承该增幅尚未确认。"
                    ),
                )
            )
        rules.append(
            _rule(
                "cinema4:charge-and-ultimate-damage",
                cinema4_source,
                f"4影：蓄热充能与终结技伤害+{c4_bonus:.0%}",
                cinema4.description,
                RuleEligibility.ELIGIBLE,
                effects=tuple(c4_effects),
            )
        )

    if config.cinema_level >= 6:
        cinema6 = raw_record.mindscapes[5]
        c6_multiplier = _number(
            cinema6.description,
            r"造成等同于奥菲丝&「鬼火」(?P<value>[\d.]+)%攻击力的",
            "Orphie Cinema 6 extra fire damage ratio",
        ) / 100.0
        ref = DamageEventTemplateRef(
            template_id=_C6_EXTRA_FIRE_TEMPLATE_ID,
            semantic_id=DamageEventSemanticId("event:character:1301:cinema6-extra-fire"),
            label="影画6：激光命中后的单次追加火伤",
            damage_type=DamageType.DIRECT,
            skill_group=SkillGroup.SPECIAL_ATTACK,
            damage_tags=frozenset(
                {DamageTag.EX_SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}
            ),
            element=Element.FIRE,
        )
        template = DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=ORPHIE_ID,
            element=Element.FIRE,
            base_source=CurrentAttackValueSource(ORPHIE_ID),
            crit_rule=StandardCritRule(ORPHIE_ID),
            move_id=None,
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=_C6_EXTRA_FIRE_ENTRY_ID,
                character_id=ORPHIE_ID,
                move_id=None,
                display_name="影画6：单次额外火伤（250%攻击力）",
                original_text=(
                    "激光命中可触发一次额外火伤；每0.5秒最多触发一次。"
                    "此条显示单次触发倍率，不推算持续喷射期间触发次数。"
                ),
                skill_group=SkillGroup.SPECIAL_ATTACK,
                damage_tags=ref.damage_tags,
                multiplier_relation=MultiplierRelation.COMPLETE,
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId("variant:character:1301:cinema6-extra-fire"),
                        label=f"{c6_multiplier:.2f}×当前攻击力",
                        parameter_name="影画6额外火伤倍率",
                        multiplier=FixedMultiplier(Resolved(c6_multiplier)),
                    ),
                ),
                main_damage_event=ref,
            )
        )
        templates.append(template)
    anomaly_entries, anomaly_templates, disorder_parameter = _static_fire_entries(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)
    return build_definition(
        character_id=ORPHIE_ID,
        role=CharacterRole.ATTACK,
        element=Element.FIRE,
        source=_source(
            "character",
            EffectSourceType.SKILL,
            raw_record.name,
            raw_record.code_name,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=tuple(conditions),
        parameters=(disorder_parameter,),
        diagnostics=(
            *direct_diagnostics,
            *unresolved_diagnostics,
        ),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(deepcopy(dict(data)), expected_character_id=str(ORPHIE_ID))


def _validate_raw(raw: NanokaRawRecord, config: OrphieMagusCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Orphie source and compile config IDs must match")
    if raw.name != "奥菲丝&「鬼火」" or raw.code_name != "Orphie & Magus":
        raise ValueError("unexpected Orphie identity")
    if raw.specialty != "强攻" or raw.element != "火属性" or raw.rarity != 4:
        raise ValueError("unexpected Orphie role, element, or rank")
    if raw.faction != "新艾利都防卫军" or raw.icon != "IconRole49":
        raise ValueError("unexpected Orphie faction or icon")
    if raw.source_version != "3.2" or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1301.json":
        raise ValueError("Orphie provenance must identify live Nanoka 3.2 character 1301")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Orphie source must include seven cores and six mindscapes")
    if raw.potential_details:
        raise ValueError("Orphie source has no Potential levels")


__all__ = ["compile_orphie_magus", "load_raw_record"]
