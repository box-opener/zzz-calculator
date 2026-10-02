"""Compile Nekomata's reviewed live Nanoka record into calculation contracts."""

from __future__ import annotations

from copy import deepcopy
import re
from collections.abc import Mapping

from core.types import (
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    DamageDealerFilter,
    DamageSubtype,
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
    EventTemplateId,
    EventTemplateIdFilter,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    NotFilter,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SkillGroup,
    SnapshotRule,
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
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import NekomataCompileConfig
from .reviewed import (
    BACK_HIT_ACTIVE,
    CINEMA4_CRIT_RATE_STACKS,
    CINEMA6_CRIT_DAMAGE_STACKS,
    CORE_DAMAGE_BUFF_ACTIVE,
    ENEMY_STUNNED_STATE_ID,
    EX_SPECIAL_MOVE_ID,
    EXTRA_ABILITY_DAMAGE_STACKS,
    NEKOMATA_ID,
    NEKOMATA_REVIEWED_MAPPING,
    PHYSICAL_ANOMALY_MOVE_ID,
    PHYSICAL_ANOMALY_RECORD_ID,
    PHYSICAL_DISORDER_MOVE_ID,
    PHYSICAL_DISORDER_REMAINING_SECONDS,
    RANDOM_REPEAT_OCCURRED,
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _one_number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain exactly one value; found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _rule(
    suffix: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    conditions=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1021:{suffix}"),
        owner=NEKOMATA_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    suffix: str,
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
            effect_id=EffectId(f"effect:character:1021:{suffix}"),
            source=source,
            owner=NEKOMATA_ID,
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


def _diagnostic(suffix: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1021:{suffix}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _static_physical_entries():
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1021:physical-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1021:physical-anomaly"),
        label="属性异常：强击（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.PHYSICAL,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=NEKOMATA_ID,
        element=Element.PHYSICAL,
        anomaly_triggerer=NEKOMATA_ID,
        history_record_source=PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
    )
    anomaly_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1021:physical-anomaly"),
        character_id=NEKOMATA_ID,
        move_id=PHYSICAL_ANOMALY_MOVE_ID,
        display_name="属性异常：强击（10秒满异常）",
        original_text="静态单人100%积蓄记录按权威规范结算物理强击，倍率7.13，使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1021:physical-anomaly"),
                label="物理强击倍率",
                parameter_name="物理强击倍率",
                multiplier=FixedMultiplier(Resolved(7.13)),
            ),
        ),
        main_damage_event=anomaly_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1021:physical-disorder",
        semantic_id=DamageEventSemanticId("event:character:1021:physical-disorder"),
        label="紊乱：物理异常",
        damage_type=DamageType.DISORDER,
        element=Element.PHYSICAL,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=NEKOMATA_ID,
        element=Element.PHYSICAL,
        disorder_triggerer=NEKOMATA_ID,
        history_record_source=PHYSICAL_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=PHYSICAL_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1021:physical-disorder"),
        character_id=NEKOMATA_ID,
        move_id=PHYSICAL_DISORDER_MOVE_ID,
        display_name="紊乱：物理异常",
        original_text="物理异常的紊乱倍率按规范为450% + floor(t)×7.5%。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1021:physical-disorder"),
                label="紊乱基础倍率+剩余时间补偿",
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
        original_text="按静态物理异常记录为10秒；本次紊乱剩余时间由用户输入，不从触发时机推断。",
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


def _random_repeat_effect(
    *,
    key: str,
    source: RuleSource,
    template_id: EventTemplateId,
    original_text: str,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1021:{key}"),
            source=source,
            owner=NEKOMATA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=(
                DamageDealerFilter(NEKOMATA_ID),
                DamageTypeFilter(DamageType.DIRECT),
                EventTemplateIdFilter(template_id),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=Unresolved(
                reason=UnresolvedReason.AMBIGUOUS_TEXT,
                notes=(
                    "The selected current source state says this move produced the "
                    "33.33% random repeat (three repeated attacks). Nanoka provides "
                    "the main move multiplier but no separate multiplier curve or "
                    "event identity for those repeats, so their damage remains unknown; "
                    "the known main hit is preserved."
                ),
                original_text=original_text,
                candidates=(
                    "The repeat uses a separate unprovided multiplier curve",
                    "The repeat inherits the listed main-hit curve",
                ),
            ),
        ),
    )


def compile_nekomata(
    config: NekomataCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    direct_entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=NEKOMATA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=NEKOMATA_REVIEWED_MAPPING,
        id_namespace="character:1021",
    )
    static_entries, static_templates, disorder_seconds = _static_physical_entries()
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        NEKOMATA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_bonus = _one_number(
        core.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Nekomata Core damage bonus",
    ) / 100.0

    extra_source = source_for(
        NEKOMATA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    extra_bonus = _one_number(
        core.extra_ability_description,
        r"招式造成的伤害提升(?P<value>[\d.]+)%",
        "Nekomata Additional Ability EX damage bonus",
    ) / 100.0

    conditions = (
        _condition(
            CORE_DAMAGE_BUFF_ACTIVE,
            "核心被动：闪避反击/快速支援后的伤害增益当前有效",
            core.description,
        ),
        _condition(
            BACK_HIT_ACTIVE,
            "本次物理攻击确认为背后命中",
            raw_record.mindscapes[0].description,
        ),
        _condition(
            RANDOM_REPEAT_OCCURRED,
            "本次猫猫爪刺五段/赤色之刃触发了33.33%重复攻击",
            "普通攻击原文明确有33.33%随机重复分支；此状态只表示本次结果已发生，不模拟概率。",
        ),
    )
    parameters = (
        ScenarioIntegerParameter(
            parameter_id=EXTRA_ABILITY_DAMAGE_STACKS,
            label="猫步秀：当前待由强化特殊技消耗的增伤层数",
            original_text=core.extra_ability_description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=2,
        ),
        ScenarioIntegerParameter(
            parameter_id=CINEMA4_CRIT_RATE_STACKS,
            label="4影：当前暴击率增益层数",
            original_text=raw_record.mindscapes[3].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=2,
        ),
        ScenarioIntegerParameter(
            parameter_id=CINEMA6_CRIT_DAMAGE_STACKS,
            label="6影：当前暴击伤害增益层数",
            original_text=raw_record.mindscapes[5].description,
            resolution=ParameterResolution.USER_SELECTED,
            value=0,
            minimum=0,
            maximum=3,
        ),
        disorder_seconds,
    )

    core_diagnostic = _diagnostic(
        "core-damage-duration",
        "The current Core damage state is an explicit 6-second-active selection; dodge-counter/Quick Assist trigger history and expiration are not replayed.",
        core.description,
    )
    extra_diagnostic = _diagnostic(
        "extra-ability-stacks",
        "The explicit 0–2 value is the currently available EX damage stack count. Teammate Assault trigger history and next-EX consumption are not replayed.",
        core.extra_ability_description,
    )
    c2_energy_diagnostic = _diagnostic(
        "cinema2-energy-efficiency-result",
        "Cinema 2's single-enemy/front-field Energy Gain Efficiency is preserved as a source-only RuleItem. The request has no Energy resource result, so it is not converted to Energy Regeneration.",
        raw_record.mindscapes[1].description,
    )
    c4_stack_diagnostic = _diagnostic(
        "cinema4-stack-timing",
        "The selected 0–2 current Crit Rate layers preserve the stack value. Individual 15-second expirations and EX trigger timing are not replayed.",
        raw_record.mindscapes[3].description,
    )
    c6_stack_diagnostic = _diagnostic(
        "cinema6-stack-timing",
        "The selected 0–3 current Crit Damage layers preserve the stack value. Encounter exit and enemy-defeat timing are not replayed.",
        raw_record.mindscapes[5].description,
    )
    daze_diagnostic = _diagnostic(
        "daze-result-unavailable",
        "Raw Support Parry Daze curves are retained in the source but this calculation request does not return a Daze result; they are not represented as damage multipliers.",
        "招架支援：应激防御的轻/重/连续招架失衡倍率",
    )

    rules: list[CalculationRuleItem] = []
    rules.append(
        _rule(
            "core:current-damage-buff",
            core_source,
            f"{core.name}·当前伤害增益",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(CORE_DAMAGE_BUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:current-damage-buff",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(core_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(DamageDealerFilter(NEKOMATA_ID),),
                ),
            ),
            diagnostics=(core_diagnostic,),
        )
    )

    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "extra-ability:ex-current-stacks",
            extra_source,
            "额外能力：猫步秀·当前强化特殊技增伤层数",
            core.extra_ability_description,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:ex-current-stacks",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    ScenarioParameterDerivedValue(
                        parameter_id=str(EXTRA_ABILITY_DAMAGE_STACKS),
                        coefficient=Resolved(extra_bonus),
                        base=Resolved(0.0),
                        cap_max=Resolved(extra_bonus * 2),
                    ),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=(
                        DamageDealerFilter(NEKOMATA_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        MoveIdFilter(EX_SPECIAL_MOVE_ID),
                    ),
                ),
            ),
            diagnostics=(extra_diagnostic,),
        )
    )

    for level, mindscape in enumerate(raw_record.mindscapes, start=1):
        source = source_for(
            NEKOMATA_ID,
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            mindscape.name,
            mindscape.description,
        )
        eligibility = (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= level
            else RuleEligibility.INELIGIBLE
        )
        if level == 1:
            physical_ignore = _one_number(
                mindscape.description,
                r"无视目标(?P<value>[\d.]+)%物理伤害抗性",
                "Nekomata Cinema 1 Physical resistance ignore",
            ) / 100.0
            owner_condition = DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER)
            filters = (
                DamageDealerFilter(NEKOMATA_ID),
                DamageTypeFilter(DamageType.DIRECT),
                ElementFilter(Element.PHYSICAL),
            )
            rules.extend(
                (
                    _rule(
                        "cinema1:back-hit-physical-resistance-ignore",
                        source,
                        "1影：背后攻击物理抗性无视",
                        mindscape.description,
                        eligibility,
                        conditions=(BACK_HIT_ACTIVE,),
                        effects=(
                            _modifier(
                                "cinema1:back-hit-physical-resistance-ignore",
                                source,
                                CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                                Resolved(physical_ignore),
                                target=EffectTarget.TEAM,
                                condition=owner_condition,
                                filters=filters + (NotFilter(EnemyStateFilter(ENEMY_STUNNED_STATE_ID)),),
                            ),
                        ),
                    ),
                    _rule(
                        "cinema1:stunned-target-physical-resistance-ignore",
                        source,
                        "1影：失衡目标视为背后攻击",
                        mindscape.description,
                        eligibility,
                        effects=(
                            _modifier(
                                "cinema1:stunned-target-physical-resistance-ignore",
                                source,
                                CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                                Resolved(physical_ignore),
                                target=EffectTarget.TEAM,
                                condition=owner_condition,
                                filters=filters + (EnemyStateFilter(ENEMY_STUNNED_STATE_ID),),
                            ),
                        ),
                    ),
                )
            )
        elif level == 2:
            rules.append(
                _rule(
                    "cinema2:energy-gain-efficiency-source-only",
                    source,
                    "2影：单敌前场能量获得效率",
                    mindscape.description,
                    eligibility,
                    diagnostics=(c2_energy_diagnostic,),
                )
            )
        elif level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    source,
                    f"{level}影：{mindscape.name}·技能等级",
                    mindscape.description,
                    eligibility,
                )
            )
        elif level == 4:
            crit_per_stack = _one_number(
                mindscape.description,
                r"暴击率提升(?P<value>[\d.]+)%",
                "Nekomata Cinema 4 Crit Rate per stack",
            ) / 100.0
            rules.append(
                _rule(
                    "cinema4:current-crit-rate-stacks",
                    source,
                    "4影：当前暴击率层数",
                    mindscape.description,
                    eligibility,
                    effects=(
                        _modifier(
                            "cinema4:current-crit-rate-stacks",
                            source,
                            CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                            ScenarioParameterDerivedValue(
                                parameter_id=str(CINEMA4_CRIT_RATE_STACKS),
                                coefficient=Resolved(crit_per_stack),
                                base=Resolved(0.0),
                                cap_max=Resolved(crit_per_stack * 2),
                            ),
                            target=EffectTarget.SELF,
                        ),
                    ),
                    diagnostics=(c4_stack_diagnostic,),
                )
            )
        elif level == 6:
            crit_damage_per_stack = _one_number(
                mindscape.description,
                r"暴击伤害提升(?P<value>[\d.]+)%",
                "Nekomata Cinema 6 Crit Damage per stack",
            ) / 100.0
            rules.append(
                _rule(
                    "cinema6:current-crit-damage-stacks",
                    source,
                    "6影：当前暴击伤害层数",
                    mindscape.description,
                    eligibility,
                    effects=(
                        _modifier(
                            "cinema6:current-crit-damage-stacks",
                            source,
                            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                            ScenarioParameterDerivedValue(
                                parameter_id=str(CINEMA6_CRIT_DAMAGE_STACKS),
                                coefficient=Resolved(crit_damage_per_stack),
                                base=Resolved(0.0),
                                cap_max=Resolved(crit_damage_per_stack * 3),
                            ),
                            target=EffectTarget.SELF,
                        ),
                    ),
                    diagnostics=(c6_stack_diagnostic,),
                )
            )

    raw_moves = {move.name: move for move in raw_record.moves}
    repeat_specs = (
        (
            "basic-cat-claw-final-repeat",
            EventTemplateId("template:character:1021:basic-cat-claw-5:main"),
            "普通攻击：猫猫爪刺",
        ),
        (
            "basic-red-blade-repeat",
            EventTemplateId("template:character:1021:basic-red-blade:main"),
            "普通攻击：赤色之刃",
        ),
    )
    for key, template_id, source_name in repeat_specs:
        raw_move = raw_moves[source_name]
        repeat_rule_source = source_for(
            NEKOMATA_ID,
            key,
            EffectSourceType.SKILL,
            raw_move.name,
            raw_move.description,
        )
        unresolved_effect = _random_repeat_effect(
            key=key,
            source=repeat_rule_source,
            template_id=template_id,
            original_text=raw_move.description,
        )
        rules.append(
            _rule(
                f"random-repeat:{key}",
                repeat_rule_source,
                f"随机重复分支：{raw_move.name}",
                raw_move.description,
                RuleEligibility.ELIGIBLE,
                conditions=(RANDOM_REPEAT_OCCURRED,),
                effects=(unresolved_effect,),
            )
        )

    potential_diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1021:potential-variants"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=(
            "Potential IDs 102100–102105 are distinct Nanoka source variants. The current compile config has no Potential selection, so only potential 0 is compiled; the full raw variants remain preserved."
        ),
        blocking=False,
        original_text="Nanoka potential_detail names these as 猫的报恩 I–VI / 潜能觉醒.",
    )
    daze_diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("unsupported:character:1021:daze-result"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=(
            "Nanoka's three Support Parry Daze curves are retained in raw, but the current request has no Daze result and no Parry damage curve; they are not turned into fake Direct damage."
        ),
        blocking=False,
        original_text="招架支援：应激防御的轻/重/连续招架失衡倍率",
    )
    return build_definition(
        character_id=NEKOMATA_ID,
        role=CharacterRole.ATTACK,
        element=Element.PHYSICAL,
        source=core_source,
        entries=(*direct_entries, *static_entries),
        templates=(*direct_templates, *static_templates),
        rules=rules,
        conditions=conditions,
        parameters=parameters,
        diagnostics=(*direct_diagnostics, potential_diagnostic, daze_diagnostic),
    )


def _is_base_potential(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, (list, tuple)):
        return False
    return not value or 0 in value


def _potential_zero_view(data: Mapping[str, object]) -> dict[str, object]:
    """Create a local compile view; the packaged full raw source stays lossless."""

    view = deepcopy(dict(data))
    skill_root = view.get("skill")
    if isinstance(skill_root, dict):
        for section_data in skill_root.values():
            if not isinstance(section_data, dict):
                continue
            descriptions = section_data.get("description")
            if isinstance(descriptions, list):
                section_data["description"] = [
                    item
                    for item in descriptions
                    if isinstance(item, dict) and _is_base_potential(item.get("potential"))
                ]
    passive = view.get("passive")
    if isinstance(passive, dict) and isinstance(passive.get("level"), dict):
        passive["level"] = {
            key: item
            for key, item in passive["level"].items()
            if isinstance(item, dict) and _is_base_potential(item.get("potential"))
        }
    return view


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_zero_view(data),
        expected_character_id=str(NEKOMATA_ID),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: NekomataCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "猫又" or raw.code_name != "Nekomata":
        raise ValueError("unexpected character identity in raw Nekomata record")
    if raw.specialty != "强攻" or raw.element != "物理":
        raise ValueError("Nekomata raw role or element does not match reviewed source")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Nekomata compile view must contain seven cores and six cinemas")


__all__ = ["compile_nekomata", "load_raw_record"]
