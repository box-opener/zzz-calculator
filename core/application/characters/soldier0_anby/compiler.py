"""Compile Soldier 0 - Anby's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
import re

from core.types import (
    BattleEventKind,
    CalculationNode,
    CharacterFilter,
    CharacterRole,
    CurrentAttackValueSource,
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
    EnemyStateFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    PanelStatDerivedValue,
    Resolved,
    RuleStackCondition,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import DamageEventSemanticId, DiagnosticId, RuleItemId
from ...moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_multiplier,
    raw_move_index,
    source_for,
)
from ..templates import DirectDamageEventTemplate
from ..nanoka_source import load_nanoka_raw_record
from .config import SOLDIER0_ANBY_ID, Soldier0AnbyCompileConfig
from .reviewed import (
    SOLDIER0_ANBY_CINEMA1_RULE_ID,
    SOLDIER0_ANBY_CINEMA2_RULE_ID,
    SOLDIER0_ANBY_CINEMA3_RULE_ID,
    SOLDIER0_ANBY_CINEMA4_RULE_ID,
    SOLDIER0_ANBY_CINEMA5_RULE_ID,
    SOLDIER0_ANBY_CINEMA6_RULE_ID,
    SOLDIER0_ANBY_CINEMA6_VORTEX_TEMPLATE_ID,
    SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED,
    SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER,
    SOLDIER0_ANBY_CANGGUANG_THUNDERCLAP_RULE_ID,
    SOLDIER0_ANBY_CORE_RULE_ID,
    SOLDIER0_ANBY_CRITICAL_CANGGUANG_TEMPLATE_ID,
    SOLDIER0_ANBY_EX_TEMPLATE_ID,
    SOLDIER0_ANBY_EXTRA_ABILITY_RULE_ID,
    SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID,
    SOLDIER0_ANBY_SILVER_STAR_ACTIVE,
    SOLDIER0_ANBY_SILVER_STAR_STATE,
    SOLDIER0_ANBY_THUNDERCLAP_CHILD_TEMPLATE_ID,
    SOLDIER0_ANBY_WHITE_THUNDER_ACTIVE,
    SOLDIER0_ANBY_WHITE_THUNDER_STATE,
    SOLDIER0_ANBY_WHITE_THUNDER_TEMPLATE_ID,
    SOLDIER0_ANBY_REVIEWED_MAPPING,
)


_SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1381.json"
_CANGGUANG_RULE_ID = RuleItemId("rule:character:1381:skill:cangguang-white-thunder")
_CANGGUANG_TEMPLATE_ID = "template:soldier0-anby:1381:special-cangguang-main:main"
_WHITE_THUNDER_MAIN_TEMPLATE_ID = EventTemplateId("template:soldier0-anby:1381:white-thunder:main")
_CANGGUANG_WHITE_THUNDER_PARAMETER = "[白雷]伤害倍率"
_THUNDERCLAP_PARAMETER = "[雷殛]伤害倍率"
_CRITICAL_CANGGUANG_PARAMETER = "伤害倍率"


def _source(raw: NanokaRawRecord, key: str, source_type: EffectSourceType, label: str, text: str | None):
    return source_for(
        SOLDIER0_ANBY_ID,
        key,
        source_type,
        label,
        text if text is not None else f"Nanoka {raw.source_version}: {raw.source_url}",
    )


def _rule(
    key: str,
    source,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
) -> CalculationRuleItem:
    rule_id = {
        "core:marked-target": SOLDIER0_ANBY_CORE_RULE_ID,
        "extra-ability:polarization": SOLDIER0_ANBY_EXTRA_ABILITY_RULE_ID,
        "cinema1:ex-white-thunder": SOLDIER0_ANBY_CINEMA1_RULE_ID,
        "cinema2:crit-rate": SOLDIER0_ANBY_CINEMA2_RULE_ID,
        "cinema3:skill-levels": SOLDIER0_ANBY_CINEMA3_RULE_ID,
        "cinema4:electric-resistance-ignore": SOLDIER0_ANBY_CINEMA4_RULE_ID,
        "cinema5:skill-levels": SOLDIER0_ANBY_CINEMA5_RULE_ID,
        "cinema6:electromagnetic-vortex": SOLDIER0_ANBY_CINEMA6_RULE_ID,
        "potential:critical-cangguang": SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID,
        "skill:cangguang-white-thunder": _CANGGUANG_RULE_ID,
        "skill:cangguang-thunderclap": SOLDIER0_ANBY_CANGGUANG_THUNDERCLAP_RULE_ID,
    }[key]
    return CalculationRuleItem(
        rule_id=rule_id,
        owner=SOLDIER0_ANBY_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    recipient_character_id=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1381:{key}"),
            source=source,
            owner=SOLDIER0_ANBY_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
            recipient_character_id=recipient_character_id,
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _ratio(text: str, pattern: str, label: str) -> float:
    match = re.search(pattern, text)
    if match is None:
        raise ValueError(f"Nanoka source does not provide a reviewed {label} value")
    return float(match.group("value")) / 100.0


def _fixed_multiplier(value: float | Unresolved):
    return value if isinstance(value, Unresolved) else FixedMultiplier(Resolved(float(value)))


def _raw_ratio(
    raw: NanokaRawRecord,
    source_name: str,
    parameter_name: str,
    source_skill_id: str,
    level: int,
    subject: str,
) -> tuple[float | Unresolved, tuple[CalculationDiagnostic, ...]]:
    diagnostics: list[CalculationDiagnostic] = []
    value = raw_multiplier(
        raw_move_index(raw),
        source_name,
        parameter_name,
        level,
        subject,
        diagnostics,
        source_skill_id=source_skill_id,
    )
    return value, tuple(diagnostics)


def _direct_child_template(
    template_id,
    semantic_id: str,
    label: str,
    *,
    skill_group: SkillGroup | None,
    tags: frozenset,
    source_rule_id: RuleItemId,
) -> DirectDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId(semantic_id),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=tags,
        element=Element.ELECTRIC,
        source_rule_item_id=source_rule_id,
    )
    return DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=SOLDIER0_ANBY_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(SOLDIER0_ANBY_ID),
        crit_rule=StandardCritRule(SOLDIER0_ANBY_ID),
        move_id=None,
    )


def _create_child_effect(
    effect_key: str,
    source,
    template_id,
    filters,
    condition=None,
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1381:{effect_key}"),
            source=source,
            owner=SOLDIER0_ANBY_ID,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
            condition=condition,
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_id,
            unique_per_source_event=True,
        ),
    )


def _potential_view(
    data: Mapping[str, object], potential_level: int
) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("potential_level must be between 0 and 6")
    details = data.get("potential_detail")
    if not isinstance(details, Mapping):
        raise ValueError("Soldier 0 - Anby source has no potential_detail")
    selected_detail = next(
        (
            item
            for item in details.values()
            if isinstance(item, Mapping)
            and item.get("level") == potential_level
            and isinstance(item.get("id"), int)
        ),
        None,
    )
    if selected_detail is None and potential_level != 0:
        raise ValueError(f"Soldier 0 - Anby source has no Potential level {potential_level}")
    selected_id = int(selected_detail["id"]) if selected_detail is not None else None

    def selected_skill_variant(value: object) -> bool:
        if not isinstance(value, (list, tuple)):
            return True
        if not value:
            return True
        if potential_level == 0:
            return 0 in value
        return selected_id is not None and selected_id in value and 0 not in value

    def selected_core_variant(value: object) -> bool:
        if not isinstance(value, (list, tuple)):
            return False
        if potential_level == 0:
            return value == [0] or value == (0,)
        return selected_id is not None and selected_id in value

    view = deepcopy(dict(data))
    skill = view.get("skill")
    if isinstance(skill, dict):
        for section in skill.values():
            if not isinstance(section, dict) or not isinstance(section.get("description"), list):
                continue
            selected_descriptions: list[dict[str, object]] = []
            for raw_description in section["description"]:
                if not isinstance(raw_description, dict) or not selected_skill_variant(
                    raw_description.get("potential")
                ):
                    continue
                parameters = raw_description.get("param")
                if isinstance(parameters, list):
                    raw_description["param"] = [
                        parameter
                        for parameter in parameters
                        if isinstance(parameter, dict)
                        and selected_skill_variant(parameter.get("potential"))
                    ]
                selected_descriptions.append(raw_description)
            section["description"] = selected_descriptions

    passive = view.get("passive")
    if isinstance(passive, dict) and isinstance(passive.get("level"), dict):
        passive["level"] = {
            key: item
            for key, item in passive["level"].items()
            if isinstance(item, dict) and selected_core_variant(item.get("potential"))
        }
    return view


def load_raw_record(
    data: Mapping[str, object], *, potential_level: int = 0
) -> NanokaRawRecord:
    view = _potential_view(data, potential_level)
    if view.get("source_version") != "3.2" or view.get("source_url") != _SOURCE_URL:
        raise ValueError("Soldier 0 - Anby provenance must identify live Nanoka 3.2 character 1381")
    return load_nanoka_raw_record(view, expected_character_id=str(SOLDIER0_ANBY_ID))


def _validate_raw(raw: NanokaRawRecord, config: Soldier0AnbyCompileConfig) -> None:
    if raw.character_id != SOLDIER0_ANBY_ID or raw.name != "零号·安比" or raw.code_name != "Soldier 0 - Anby":
        raise ValueError("unexpected Soldier 0 - Anby raw identity")
    if raw.specialty != "强攻" or raw.element != "电属性" or raw.rarity != 4:
        raise ValueError("unexpected Soldier 0 - Anby role, element, or rank")
    if raw.faction != "新艾利都防卫军" or raw.icon != "IconRole40":
        raise ValueError("Soldier 0 - Anby source identity or faction changed")
    if raw.source_version != "3.2" or raw.source_url != _SOURCE_URL:
        raise ValueError("Soldier 0 - Anby provenance must identify live Nanoka 3.2 character 1381")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Soldier 0 - Anby source must include seven Core levels and six Cinemas")
    if config.potential_level > 0 and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError("Soldier 0 - Anby raw source does not match selected Potential level")
    if config.character_id != raw.character_id:
        raise ValueError("Soldier 0 - Anby config and raw IDs must match")


def compile_soldier0_anby(
    config: Soldier0AnbyCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    reviewed_moves = []
    for spec in SOLDIER0_ANBY_REVIEWED_MAPPING.moves:
        # 雷殛 and 苍光·临界 are source-triggered children, not selectable moves.
        if spec.entry_key in {"special-thunderclap", "special-cangguang-critical"}:
            continue
        if spec.entry_key == "basic-stage-3":
            selected_curve = "1381003" if config.potential_level == 0 else "1381022"
            parameter = replace(spec.parameters[0], source_skill_id=selected_curve)
            spec = replace(spec, parameters=(parameter,))
        reviewed_moves.append(spec)
    reviewed_mapping = NanokaReviewedMapping(
        moves=tuple(reviewed_moves),
        data_quality_notes=SOLDIER0_ANBY_REVIEWED_MAPPING.data_quality_notes,
    )
    entries, templates, diagnostics = compile_direct_moves(
        character_id=SOLDIER0_ANBY_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="soldier0-anby:1381",
    )
    white_thunder_ref_updates = {}
    updated_entries = []
    for entry in entries:
        if str(entry.entry_id) != "move-entry:soldier0-anby:1381:white-thunder":
            updated_entries.append(entry)
            continue
        ref = replace(
            entry.main_damage_event,
            skill_group=None,
            damage_tags=frozenset({DamageTag.FOLLOW_UP_ATTACK}),
        )
        white_thunder_ref_updates[ref.template_id] = ref
        updated_entries.append(
            replace(
                entry,
                move_id=None,
                skill_group=None,
                damage_tags=frozenset({DamageTag.FOLLOW_UP_ATTACK}),
                main_damage_event=ref,
            )
        )
    entries = tuple(updated_entries)
    templates = tuple(
        replace(template, ref=white_thunder_ref_updates[template.ref.template_id], move_id=None)
        if template.ref.template_id in white_thunder_ref_updates
        else template
        for template in templates
    )
    raw_moves = raw_move_index(raw_record)

    selected_core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        raw_record,
        "core:marked-target",
        EffectSourceType.CORE_PASSIVE,
        selected_core.name,
        selected_core.description,
    )
    marked_damage_bonus = _ratio(
        selected_core.description,
        r"造成的伤害提升<color=[^>]+>(?P<value>[\d.]+)%",
        "Silver Star damage bonus",
    )
    follow_up_crit_factor = _ratio(
        selected_core.description,
        r"提升效果等同于零号·安比暴击伤害的<color=[^>]+>(?P<value>[\d.]+)%",
        "Silver Star Follow-up Crit Damage factor",
    )
    if config.potential_level >= 1:
        follow_up_crit_factor += _ratio(
            selected_core.description,
            r"额外提升零号·安比暴击伤害的(?P<value>[\d.]+)%",
            "Potential 1 Silver Star Follow-up Crit Damage factor",
        )
    core_effects = (
        _modifier(
            "core:marked-target-damage",
            core_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(marked_damage_bonus),
            target=EffectTarget.TEAM,
            filters=(
                DamageDealerFilter(SOLDIER0_ANBY_ID),
                EnemyStateFilter(SOLDIER0_ANBY_SILVER_STAR_STATE),
            ),
        ),
        _modifier(
            "core:marked-target-follow-up-crit-damage",
            core_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            PanelStatDerivedValue(
                source_character_id=SOLDIER0_ANBY_ID,
                source_node=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                coefficient=Resolved(follow_up_crit_factor),
            ),
            target=EffectTarget.TEAM,
            filters=(
                DamageTypeFilter(DamageType.DIRECT),
                DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),
                EnemyStateFilter(SOLDIER0_ANBY_SILVER_STAR_STATE),
            ),
        ),
    )
    rules: list[CalculationRuleItem] = [
        _rule(
            "core:marked-target",
            core_source,
            f"核心被动：银星目标伤害+{marked_damage_bonus:.1%}；追加攻击暴击伤害按零号·安比当前暴击伤害的{follow_up_crit_factor:.1%}提升",
            selected_core.description,
            RuleEligibility.ELIGIBLE,
            effects=core_effects,
        )
    ]

    extra_source = _source(
        raw_record,
        "extra-ability:polarization",
        EffectSourceType.ADDITIONAL_ABILITY,
        selected_core.extra_ability_name,
        selected_core.extra_ability_description,
    )
    extra_crit_rate = _ratio(
        selected_core.extra_ability_description,
        r"暴击率提升(?:<color=[^>]+>)?(?P<value>[\d.]+)%",
        "Additional Ability Crit Rate",
    )
    extra_follow_up_bonus = _ratio(
        selected_core.extra_ability_description,
        r"伤害提升(?:<color=[^>]+>)?(?P<value>[\d.]+)%",
        "Additional Ability Follow-up Damage",
    )
    if config.potential_level >= 2:
        selected_potential = next(
            item for item in raw_record.potential_details if item.level == config.potential_level
        )
        if selected_potential.description.strip():
            extra_follow_up_bonus = _ratio(
                selected_potential.description,
                r"提升至<color=[^>]+>(?P<value>[\d.]+)%",
                f"Potential {config.potential_level} Additional Ability Follow-up Damage",
            )
    extra_eligible = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_effects = []
    if config.additional_ability_eligible:
        extra_effects.append(
            _modifier(
                "extra-ability:crit-rate",
                extra_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                Resolved(extra_crit_rate),
                target=EffectTarget.RECIPIENT,
                recipient_character_id=SOLDIER0_ANBY_ID,
            )
        )
        extra_effects.append(
            _modifier(
                "extra-ability:marked-follow-up-damage",
                extra_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(extra_follow_up_bonus),
                target=EffectTarget.TEAM,
                filters=(
                    CharacterFilter(SOLDIER0_ANBY_ID),
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),
                    EnemyStateFilter(SOLDIER0_ANBY_SILVER_STAR_STATE),
                ),
            )
        )
    rules.append(
        _rule(
            "extra-ability:polarization",
            extra_source,
            f"额外能力：暴击率+{extra_crit_rate:.0%}；银星目标追加攻击伤害+{extra_follow_up_bonus:.0%}",
            selected_core.extra_ability_description,
            extra_eligible,
            effects=extra_effects,
        )
    )

    cinema_sources = {
        item.level: _source(
            raw_record,
            f"cinema{item.level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for item in raw_record.mindscapes
    }
    cinema_text = {item.level: item.description for item in raw_record.mindscapes}

    conditions = [
        ScenarioCondition(
            condition_id=SOLDIER0_ANBY_SILVER_STAR_ACTIVE,
            label="当前目标已拥有银星标记",
            original_text=selected_core.description,
            resolution=ConditionResolution.USER_SELECTED,
            value=config.silver_star_active,
        ),
        ScenarioCondition(
            condition_id=SOLDIER0_ANBY_WHITE_THUNDER_ACTIVE,
            label="当前目标已拥有白雷",
            original_text=raw_moves["特殊技：苍光"].description,
            resolution=ConditionResolution.USER_SELECTED,
            value=config.white_thunder_active,
        ),
        ScenarioCondition(
            condition_id=SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER,
            label="本次苍光触发第三次白雷",
            original_text=raw_moves["特殊技：苍光"].description,
            resolution=ConditionResolution.USER_SELECTED,
            value=False,
        ),
        ScenarioCondition(
            condition_id=SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED,
            label="本次招式触发了第六次白雷额外伤害",
            original_text=cinema_text[6],
            resolution=ConditionResolution.USER_SELECTED,
            value=config.cinema6_vortex_triggered,
        ),
    ]

    c1_source = cinema_sources[1]
    c1_unlocked = config.cinema_level >= 1
    white_thunder_c1, white_thunder_c1_diagnostics = _raw_ratio(
        raw_record,
        "特殊技：苍光",
        _CANGGUANG_WHITE_THUNDER_PARAMETER,
        "1381007",
        effective_skill_level(config, SkillGroup.SPECIAL_ATTACK),
        f"{SOLDIER0_ANBY_ID}:cinema1-white-thunder",
    )
    thunderclap_ratio, thunderclap_diagnostics = _raw_ratio(
        raw_record,
        "特殊技：雷殛",
        _THUNDERCLAP_PARAMETER,
        "1381008",
        effective_skill_level(config, SkillGroup.SPECIAL_ATTACK),
        f"{SOLDIER0_ANBY_ID}:cinema1-thunderclap",
    )
    white_thunder_c1_template = _direct_child_template(
        SOLDIER0_ANBY_WHITE_THUNDER_TEMPLATE_ID,
        "event:soldier0-anby:1381:cinema1:white-thunder",
        "1影：强化特殊技触发的白雷额外伤害（3次）",
        skill_group=None,
        tags=frozenset({DamageTag.FOLLOW_UP_ATTACK}),
        source_rule_id=SOLDIER0_ANBY_CINEMA1_RULE_ID,
    )
    thunderclap_child = _direct_child_template(
        SOLDIER0_ANBY_THUNDERCLAP_CHILD_TEMPLATE_ID,
        "event:soldier0-anby:1381:cinema1:thunderclap",
        "1影：白雷触发的雷殛",
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tags=frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}),
        source_rule_id=SOLDIER0_ANBY_CANGGUANG_THUNDERCLAP_RULE_ID,
    )
    c1_effects = ()
    if c1_unlocked:
        c1_effects = (
            _create_child_effect(
                "cinema1:white-thunder",
                c1_source,
                white_thunder_c1_template.ref.template_id,
                (EventTemplateIdFilter(SOLDIER0_ANBY_EX_TEMPLATE_ID),),
            ),
            _create_child_effect(
                "cinema1:thunderclap",
                c1_source,
                thunderclap_child.ref.template_id,
                (EventTemplateIdFilter(SOLDIER0_ANBY_EX_TEMPLATE_ID),),
            ),
        )
    rules.append(
        _rule(
            "cinema1:ex-white-thunder",
            c1_source,
            "1影：强化特殊技连续触发3次白雷额外伤害并触发雷殛",
            cinema_text[1],
            RuleEligibility.ELIGIBLE if c1_unlocked else RuleEligibility.INELIGIBLE,
            effects=c1_effects,
            diagnostics=(*white_thunder_c1_diagnostics, *thunderclap_diagnostics),
            stack_count=1 if c1_unlocked else None,
            stack_min=1 if c1_unlocked else None,
            stack_max=1 if c1_unlocked else None,
        )
    )

    cangguang_source_move = raw_moves["特殊技：苍光"]
    cangguang_source = _source(
        raw_record,
        "skill:cangguang-white-thunder",
        EffectSourceType.SKILL,
        cangguang_source_move.name,
        cangguang_source_move.description,
    )
    cangguang_white_thunder, cangguang_white_thunder_diagnostics = _raw_ratio(
        raw_record,
        "特殊技：苍光",
        _CANGGUANG_WHITE_THUNDER_PARAMETER,
        "1381007",
        effective_skill_level(config, SkillGroup.SPECIAL_ATTACK),
        f"{SOLDIER0_ANBY_ID}:cangguang-white-thunder",
    )
    cangguang_white_thunder_template = _direct_child_template(
        EventTemplateId("template:soldier0-anby:1381:special-cangguang:white-thunder"),
        "event:soldier0-anby:1381:special-cangguang:white-thunder",
        "特殊技：苍光（消耗白雷后追加伤害）",
        skill_group=None,
        tags=frozenset({DamageTag.FOLLOW_UP_ATTACK}),
        source_rule_id=_CANGGUANG_RULE_ID,
    )
    rules.append(
        _rule(
            "skill:cangguang-white-thunder",
            cangguang_source,
            "特殊技：苍光命中白雷目标后触发一次白雷追加伤害",
            cangguang_source_move.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _create_child_effect(
                    "skill:cangguang-white-thunder",
                    cangguang_source,
                    cangguang_white_thunder_template.ref.template_id,
                    (
                        EventTemplateIdFilter(EventTemplateId(_CANGGUANG_TEMPLATE_ID)),
                        EnemyStateFilter(SOLDIER0_ANBY_WHITE_THUNDER_STATE),
                    ),
                ),
            ),
            diagnostics=cangguang_white_thunder_diagnostics,
            stack_count=1,
            stack_min=1,
            stack_max=1,
        )
    )
    rules.append(
        _rule(
            "skill:cangguang-thunderclap",
            cangguang_source,
            "特殊技：苍光触发第三次白雷时追加雷殛",
            cangguang_source_move.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _create_child_effect(
                    "skill:cangguang-thunderclap",
                    cangguang_source,
                    SOLDIER0_ANBY_THUNDERCLAP_CHILD_TEMPLATE_ID,
                    (
                        EventTemplateIdFilter(EventTemplateId(_CANGGUANG_TEMPLATE_ID)),
                        EnemyStateFilter(SOLDIER0_ANBY_WHITE_THUNDER_STATE),
                    ),
                    condition=RuleStackCondition(str(_CANGGUANG_RULE_ID), 1),
                ),
            ),
            condition_ids=(SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER,),
            diagnostics=thunderclap_diagnostics,
        )
    )

    c2_source = cinema_sources[2]
    c2_crit_rate = _ratio(
        cinema_text[2],
        r"暴击率提升(?P<value>[\d.]+)%",
        "Cinema 2 Crit Rate",
    )
    c2_unlocked = config.cinema_level >= 2
    rules.append(
        _rule(
            "cinema2:crit-rate",
            c2_source,
            f"2影：暴击率+{c2_crit_rate:.0%}",
            cinema_text[2],
            RuleEligibility.ELIGIBLE if c2_unlocked else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:crit-rate",
                    c2_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(c2_crit_rate),
                    target=EffectTarget.SELF,
                ),
            )
            if c2_unlocked
            else (),
        )
    )
    for level in (3, 5):
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                cinema_sources[level],
                f"{level}影：技能等级+2（含终结技）",
                cinema_text[level],
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    c4_source = cinema_sources[4]
    c4_bonus = _ratio(
        cinema_text[4],
        r"无视目标(?P<value>[\d.]+)%<color=[^>]+>电属性伤害抗性",
        "Cinema 4 Electric Resistance Ignore",
    )
    c4_unlocked = config.cinema_level >= 4
    rules.append(
        _rule(
            "cinema4:electric-resistance-ignore",
            c4_source,
            f"4影：银星目标电属性伤害抗性无视+{c4_bonus:.0%}",
            cinema_text[4],
            RuleEligibility.ELIGIBLE if c4_unlocked else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:electric-resistance-ignore",
                    c4_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c4_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageDealerFilter(SOLDIER0_ANBY_ID),
                        ElementFilter(Element.ELECTRIC),
                        EnemyStateFilter(SOLDIER0_ANBY_SILVER_STAR_STATE),
                    ),
                ),
            )
            if c4_unlocked
            else (),
        )
    )

    c6_source = cinema_sources[6]
    c6_unlocked = config.cinema_level >= 6
    c6_multiplier = _ratio(
        cinema_text[6],
        r"造成零号·安比(?P<value>[\d.]+)%攻击力的",
        "Cinema 6 Electromagnetic Vortex ATK multiplier",
    )
    vortex_template = _direct_child_template(
        SOLDIER0_ANBY_CINEMA6_VORTEX_TEMPLATE_ID,
        "event:soldier0-anby:1381:cinema6:electromagnetic-vortex",
        "6影：电磁涡流",
        skill_group=None,
        tags=frozenset({DamageTag.FOLLOW_UP_ATTACK}),
        source_rule_id=SOLDIER0_ANBY_CINEMA6_RULE_ID,
    )
    c6_vortex_effects = (
        _create_child_effect(
            "cinema6:ex-vortex",
            c6_source,
            vortex_template.ref.template_id,
            (
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(SOLDIER0_ANBY_ID),
                EventTemplateIdFilter(SOLDIER0_ANBY_EX_TEMPLATE_ID),
            ),
            condition=RuleStackCondition(str(SOLDIER0_ANBY_CINEMA1_RULE_ID), 1),
        ),
        _create_child_effect(
            "cinema6:cangguang-vortex",
            c6_source,
            vortex_template.ref.template_id,
            (
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(SOLDIER0_ANBY_ID),
                EventTemplateIdFilter(EventTemplateId(_CANGGUANG_TEMPLATE_ID)),
                EnemyStateFilter(SOLDIER0_ANBY_WHITE_THUNDER_STATE),
            ),
            condition=RuleStackCondition(str(_CANGGUANG_RULE_ID), 1),
        ),
        _create_child_effect(
            "cinema6:standalone-white-thunder-vortex",
            c6_source,
            vortex_template.ref.template_id,
            (
                DamageTypeFilter(DamageType.DIRECT),
                DamageDealerFilter(SOLDIER0_ANBY_ID),
                EventTemplateIdFilter(_WHITE_THUNDER_MAIN_TEMPLATE_ID),
            ),
        ),
    ) if c6_unlocked else ()
    rules.append(
        _rule(
            "cinema6:electromagnetic-vortex",
            c6_source,
            "6影：本次招式触发第六次白雷额外伤害时触发电磁涡流",
            cinema_text[6],
            RuleEligibility.ELIGIBLE if c6_unlocked else RuleEligibility.INELIGIBLE,
            effects=c6_vortex_effects,
            condition_ids=(SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED,)
            if c6_unlocked
            else (),
        )
    )

    templates += (cangguang_white_thunder_template, thunderclap_child)
    if c1_unlocked:
        templates += (white_thunder_c1_template,)
    if c6_unlocked:
        templates += (vortex_template,)
    independent_derived = [
        DerivedDamageEventTemplateRef(
            template=cangguang_white_thunder_template.ref,
            multiplier=_fixed_multiplier(cangguang_white_thunder),
        ),
    ]
    if c1_unlocked:
        independent_derived.extend(
            (
                DerivedDamageEventTemplateRef(
                    template=white_thunder_c1_template.ref,
                    multiplier=_fixed_multiplier(white_thunder_c1),
                    repeat_count=3,
                ),
                DerivedDamageEventTemplateRef(
                    template=thunderclap_child.ref,
                    multiplier=_fixed_multiplier(thunderclap_ratio),
                ),
            )
        )
    else:
        # Cangguang's own current third White Thunder still creates Thunderclap.
        independent_derived.append(
            DerivedDamageEventTemplateRef(
                template=thunderclap_child.ref,
                multiplier=_fixed_multiplier(thunderclap_ratio),
            )
        )
    if c6_unlocked:
        independent_derived.append(
            DerivedDamageEventTemplateRef(
                template=vortex_template.ref,
                multiplier=FixedMultiplier(Resolved(c6_multiplier)),
            )
        )
    diagnostics = (*diagnostics, *white_thunder_c1_diagnostics, *thunderclap_diagnostics, *cangguang_white_thunder_diagnostics)

    if config.potential_level >= 1:
        critical_source_move = raw_moves.get("特殊技：苍光·临界")
        if critical_source_move is None:
            critical_multiplier: float | Unresolved = Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes="Potential 1 Critical Cangguang has no exact selected Nanoka source parameter.",
                original_text="特殊技：苍光·临界",
            )
            critical_diagnostics = (
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId("data:character:1381:potential-critical-cangguang:source"),
                    kind=DiagnosticKind.MISSING_DATA,
                    message="Potential 1 Critical Cangguang is retained, but its selected source parameter is missing.",
                    blocking=True,
                    original_text="特殊技：苍光·临界",
                ),
            )
            critical_text = "Potential 1 Critical Cangguang source parameter unavailable."
        else:
            critical_text = critical_source_move.description
            critical_multiplier, critical_diagnostics = _raw_ratio(
                raw_record,
                "特殊技：苍光·临界",
                _CRITICAL_CANGGUANG_PARAMETER,
                "1381023",
                effective_skill_level(config, SkillGroup.SPECIAL_ATTACK),
                f"{SOLDIER0_ANBY_ID}:potential-critical-cangguang",
            )
        critical_template = _direct_child_template(
            SOLDIER0_ANBY_CRITICAL_CANGGUANG_TEMPLATE_ID,
            "event:soldier0-anby:1381:potential:critical-cangguang",
            "潜能1：苍光·临界",
            skill_group=SkillGroup.SPECIAL_ATTACK,
            tags=frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.FOLLOW_UP_ATTACK}),
            source_rule_id=SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID,
        )
        potential_source = _source(
            raw_record,
            "potential:critical-cangguang",
            EffectSourceType.SPECIAL_MECHANISM,
            "潜能1：苍光·临界",
            critical_text,
        )
        rules.append(
            _rule(
                "potential:critical-cangguang",
                potential_source,
                "潜能1：雷殛在强化特殊技中触发后追加苍光·临界",
                critical_text,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _create_child_effect(
                        "potential:critical-cangguang",
                        potential_source,
                        critical_template.ref.template_id,
                        (EventTemplateIdFilter(SOLDIER0_ANBY_THUNDERCLAP_CHILD_TEMPLATE_ID),),
                    ),
                ),
                diagnostics=critical_diagnostics,
            )
        )
        templates += (critical_template,)
        independent_derived.append(
            DerivedDamageEventTemplateRef(
                template=critical_template.ref,
                multiplier=_fixed_multiplier(critical_multiplier),
            )
        )
        diagnostics = (*diagnostics, *critical_diagnostics)

    source = _source(
        raw_record,
        "character",
        EffectSourceType.CORE_PASSIVE,
        raw_record.name,
        None,
    )
    return build_definition(
        character_id=SOLDIER0_ANBY_ID,
        role=CharacterRole.ATTACK,
        element=Element.ELECTRIC,
        source=source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(),
        independent_derived_damage_events=independent_derived,
        diagnostics=diagnostics,
    )


__all__ = ["compile_soldier0_anby", "load_raw_record"]
