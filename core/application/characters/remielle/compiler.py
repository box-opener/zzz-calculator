"""Compile Remielle's reviewed live Nanoka 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
import re

from core.types import (
    CalculationNode,
    CharacterId,
    CharacterRole,
    CharacterRoleFilter,
    DamageDealerFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventTemplateId,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    PanelStatDerivedValue,
    Resolved,
    SkillGroup,
    RuleSource,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import RuleItemId
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ...ids import DamageEventSemanticId, MoveEntryId, MultiplierVariantId
from ...moves import (
    DamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from ..templates import LuminanceFlareDamageEventTemplate
from .config import RemielleCompileConfig
from .reviewed import (
    ENEMY_PRISM_ACTIVE,
    PHASE_SHIFT_ACTIVE,
    REMIELLE_ID,
    REMIELLE_REVIEWED_MAPPING,
    REFLECTION_STATE_ACTIVE,
)


_TAG_RE = re.compile(r"<[^>]*>")


def _plain(text: str) -> str:
    return _TAG_RE.sub("", text).replace("[", "").replace("]", "")


def _condition(condition_id, label: str, original_text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    condition_ids=(),
    effects=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1581:{key}"),
        owner=REMIELLE_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        effects=tuple(effects),
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1581:{key}"),
            source=source,
            owner=REMIELLE_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=operation,
            value=value,
        ),
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(REMIELLE_ID))


def _validate_raw(raw: NanokaRawRecord, config: RemielleCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Remielle raw record and compile config IDs must match")
    if raw.name != "蕾米埃尔" or raw.code_name != "Remielle":
        raise ValueError("unexpected identity in Remielle raw record")
    if raw.specialty != "异常" or raw.element != "流明" or raw.rarity != 4:
        raise ValueError("Remielle raw role, element, or rarity changed")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Remielle source must include seven core levels and six cinemas")
    if raw.potential_details:
        raise ValueError("Remielle live source unexpectedly contains Potential variants")


def _flare_entries(raw: NanokaRawRecord, config: RemielleCompileConfig, element: Element):
    reviewed = (
        (
            "basic-vertical-rainbow",
            "耀变：垂虹",
            "普通攻击：垂虹",
            100.0,
            5.0,
            SkillGroup.BASIC_ATTACK,
            True,
            "{CAL:100+AvatarSkillLevel(0)*5,1,2}%",
        ),
        (
            "basic-surprise",
            "耀变：惊鸿",
            "普通攻击：惊鸿",
            200.0,
            10.0,
            SkillGroup.BASIC_ATTACK,
            True,
            "{CAL:200+AvatarSkillLevel(0)*10,1,2}%",
        ),
        (
            "ultimate",
            "耀变：缭乱终幕",
            "终结技：缭乱终幕",
            210.0,
            10.5,
            SkillGroup.ULTIMATE,
            False,
            "{CAL:210+AvatarSkillLevel(3)*10.5,1,2}%",
        ),
        (
            "support-flower-dance",
            "耀变：花羽轮舞",
            "支援技：花羽轮舞",
            200.0,
            10.0,
            SkillGroup.ASSIST,
            False,
            "{CAL:200+AvatarSkillLevel(6)*10,1,2}%",
        ),
    )
    raw_by_name = {move.name: move for move in raw.moves}
    entries = []
    templates = []
    for key, label, raw_name, base, growth, group, repeatable, expression in reviewed:
        raw_move = raw_by_name.get(raw_name)
        if raw_move is None or not any(
            parameter.name == "耀变倍率"
            for parameter in raw_move.parameters
        ):
            raise ValueError(f"Remielle raw source is missing Flare formula: {raw_name}")
        skill_level = effective_skill_level(config, group)
        # The source CAL expression uses AvatarSkillLevel directly (for
        # example, 100 + 12 * 5 = 160%), not a level-curve index offset.
        base_multiplier = (base + growth * skill_level) / 100.0
        multiplier = FixedMultiplier(Resolved(base_multiplier))
        entry_key = f"flare:{key}"
        template_id = EventTemplateId(f"template:character:1581:{entry_key}")
        semantic_id = DamageEventSemanticId(f"event:character:1581:{entry_key}")
        ref = DamageEventTemplateRef(
            template_id=template_id,
            semantic_id=semantic_id,
            label=label,
            damage_type=DamageType.ANOMALY,
            damage_subtype=DamageSubtype.LUMINANCE,
            element=element,
        )
        template = LuminanceFlareDamageEventTemplate(
            ref=ref,
            damage_dealer=REMIELLE_ID,
            element=element,
            luminance_triggerer=REMIELLE_ID,
            crit_rule=NoCritRule(),
            repeat_count_rule_item_id=(
                RuleItemId("rule:character:1581:cinema6:flare-repeat")
                if repeatable
                else None
            ),
        )
        variant = MultiplierVariant(
            variant_id=MultiplierVariantId(f"variant:character:1581:{entry_key}"),
            label=f"倍率（技能等级{skill_level}）",
            parameter_name="耀变倍率",
            multiplier=multiplier,
        )
        entry = MoveCalculationEntry(
            entry_id=MoveEntryId(f"move-entry:character:1581:{entry_key}"),
            character_id=REMIELLE_ID,
            move_id=None,
            display_name=label,
            original_text=(
                f"{raw_name}命中后触发耀变；倍率原文：{expression}。"
                "按当前来源槽分别结算，使用来源生成时的效果强度与穿透快照。"
            ),
            skill_group=None,
            damage_tags=frozenset(),
            multiplier_relation=MultiplierRelation.COMPLETE,
            multiplier_variants=(variant,),
            main_damage_event=ref,
        )
        entries.append(entry)
        templates.append(template)
    return tuple(entries), tuple(templates)


def _team_attack_bonus(raw: NanokaRawRecord, config: RemielleCompileConfig):
    core = raw.core_levels[config.core_level - 1]
    text = _plain(core.extra_ability_description)
    match = re.search(
        r"初始攻击力(?P<one>[\d.]+)%/(?P<two>[\d.]+)%/(?P<three>[\d.]+)%",
        text,
    )
    cap_match = re.search(r"上限不超过(?P<value>[\d.]+)点", text)
    if match is None or cap_match is None:
        raise ValueError("Remielle extra-ability source is missing its team ATK values")
    coefficient = float(match.group(config.anomaly_team_count)) / 100.0
    cap = float(cap_match.group("value"))
    return core, coefficient, cap


def compile_remielle(
    config: RemielleCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    reviewed_mapping = replace(
        REMIELLE_REVIEWED_MAPPING,
        moves=tuple(
            replace(spec, element=config.damage_element)
            for spec in REMIELLE_REVIEWED_MAPPING.moves
        ),
    )
    entries, templates, diagnostics = compile_direct_moves(
        character_id=REMIELLE_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="character:1581",
    )
    flare_entries, flare_templates = _flare_entries(
        raw_record,
        config,
        config.damage_element,
    )
    entries = (*entries, *flare_entries)
    templates = (*templates, *flare_templates)
    if not config.damage_element_known:
        unresolved_element = Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=(
                "Remielle's current Luminance flow element requires the fixed "
                "formation order; this legacy request omitted formation_character_ids."
            ),
            original_text=(
                "蕾米埃尔会将其属性自动流变为队伍中下一位代理人的属性。"
            ),
        )
        entries = tuple(
            replace(
                entry,
                multiplier_variants=tuple(
                    replace(variant, multiplier=unresolved_element)
                    for variant in entry.multiplier_variants
                ),
            )
            for entry in entries
        )
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        REMIELLE_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    extra_source = source_for(
        REMIELLE_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    mutation_rule_source = source_for(
        REMIELLE_ID,
        "core-anomaly-mutation-coefficient",
        EffectSourceType.CORE_PASSIVE,
        f"{core.name}（异化系数基础值：异常精通0.02%）",
        core.description,
    )

    plain_core = _plain(core.description)
    mutation_base_match = re.search(
        r"(?:\[)?异化系数(?:\])?为自身异常精通的(?P<value>[\d.]+)%",
        plain_core,
    )
    if mutation_base_match is None:
        raise ValueError("Remielle Core source is missing its AP-based mutation coefficient")
    mutation_ap_coefficient = float(mutation_base_match.group("value")) / 100.0
    mutation_three_anomaly_match = re.search(
        r"异常角色数量为3时，(?:\[)?异化系数(?:\])?额外提升(?P<value>[\d.]+)%",
        plain_core,
    )
    if mutation_three_anomaly_match is None:
        raise ValueError("Remielle Core source is missing its three-anomaly coefficient increase")
    mutation_current_ap = PanelStatDerivedValue(
        source_character_id=REMIELLE_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        coefficient=Resolved(mutation_ap_coefficient),
        base=Resolved(1.0),
    )
    cinema2_mutation_match = re.search(
        r"(?:\[)?异化系数(?:\])?提升(?P<value>[\d.]+)%",
        _plain(raw_record.mindscapes[1].description),
    )
    if cinema2_mutation_match is None:
        raise ValueError("Remielle Cinema 2 source is missing its mutation coefficient increase")
    mutation_source = _modifier(
        "core:anomaly-mutation-coefficient",
        mutation_rule_source,
        CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
        mutation_current_ap,
        target=EffectTarget.TEAM,
        filters=(
            DamageTypeFilter(DamageType.ANOMALY),
            DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
        ),
        operation=EffectOperation.MULTIPLY,
    )
    disorder_mutation_source = _modifier(
        "core:disorder-source-anomaly-mutation-coefficient",
        mutation_rule_source,
        CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
        mutation_current_ap,
        target=EffectTarget.TEAM,
        filters=(DamageTypeFilter(DamageType.DISORDER),),
        operation=EffectOperation.MULTIPLY,
    )
    mutation_rule = _rule(
        "core:anomaly-mutation-coefficient",
        mutation_rule_source,
        "核心被动：全队异常效果强度的异化系数",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(mutation_source, disorder_mutation_source),
    )
    three_anomaly_bonus = float(mutation_three_anomaly_match.group("value")) / 100.0
    three_anomaly_source = source_for(
        REMIELLE_ID,
        "core-three-anomaly-mutation-coefficient",
        EffectSourceType.CORE_PASSIVE,
        f"{core.name}（异常角色数量为3：异化系数+{three_anomaly_bonus * 100:g}%）",
        core.description,
    )
    three_anomaly_effects = (
        _modifier(
            "core:three-anomaly-mutation-coefficient",
            three_anomaly_source,
            CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
            Resolved(three_anomaly_bonus),
            target=EffectTarget.TEAM,
            filters=(
                DamageTypeFilter(DamageType.ANOMALY),
                DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
            ),
            operation=EffectOperation.ADD,
        ),
        _modifier(
            "core:three-anomaly-disorder-mutation-coefficient",
            three_anomaly_source,
            CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
            Resolved(three_anomaly_bonus),
            target=EffectTarget.TEAM,
            filters=(DamageTypeFilter(DamageType.DISORDER),),
            operation=EffectOperation.ADD,
        ),
    )
    three_anomaly_rule = _rule(
        "core:three-anomaly-mutation-coefficient",
        three_anomaly_source,
        "核心被动：三名异常角色时异化系数提升",
        core.description,
        (
            RuleEligibility.ELIGIBLE
            if config.anomaly_team_count == 3
            else RuleEligibility.INELIGIBLE
        ),
        effects=three_anomaly_effects,
    )

    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    _, attack_coefficient, attack_cap = _team_attack_bonus(raw_record, config)
    attack_value = PanelStatDerivedValue(
        source_character_id=REMIELLE_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
        coefficient=Resolved(attack_coefficient),
        cap_max=Resolved(attack_cap),
    )
    extra_team_attack = _rule(
        "extra-ability:team-initial-attack",
        extra_source,
        "额外能力：按异常角色数量提升全队攻击力",
        core.extra_ability_description,
        extra_eligibility,
        effects=(
            _modifier(
                "extra-ability:team-initial-attack",
                extra_source,
                CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                attack_value,
                target=EffectTarget.TEAM,
            ),
        ),
    )

    conditions = (
        _condition(
            REFLECTION_STATE_ACTIVE,
            "蕾米埃尔当前处于映曜状态",
            "普通攻击：惊鸿要求当前处于映曜状态；不模拟连携技或支援技对该状态的赋予。",
        ),
        _condition(
            PHASE_SHIFT_ACTIVE,
            "蕾米埃尔当前处于相变时流状态",
            "用于判断该状态下全队属性异常伤害提升；不模拟状态进入、持续时间或退出。",
        ),
        _condition(
            ENEMY_PRISM_ACTIVE,
            "目标当前带有幻色效果",
            "影画2对幻色目标的防御力无视仅在该状态当前有效时匹配。",
        ),
    )

    cinema1 = raw_record.mindscapes[0]
    cinema1_source = source_for(
        REMIELLE_ID,
        "cinema1",
        EffectSourceType.CINEMA,
        cinema1.name,
        cinema1.description,
    )
    cinema1_rule = _rule(
        "cinema1:team-anomaly-damage-in-phase-shift",
        cinema1_source,
        "影画1：相变时流期间队友属性异常伤害提升",
        cinema1.description,
        (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE
        ),
        condition_ids=(PHASE_SHIFT_ACTIVE,),
        effects=(
            _modifier(
                "cinema1:team-anomaly-damage-in-phase-shift",
                cinema1_source,
                CalculationNode.ANOMALY_DAMAGE_BONUS,
                Resolved(0.10),
                target=EffectTarget.TEAM,
                filters=(
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                ),
            ),
        ),
    )
    cinema1_luminance_source = source_for(
        REMIELLE_ID,
        "cinema1-luminance-flare-resistance-ignore",
        EffectSourceType.CINEMA,
        f"{cinema1.name}（耀变无视全属性抗性）",
        cinema1.description,
    )
    cinema1_luminance_rule = _rule(
        "cinema1:luminance-flare-resistance-ignore",
        cinema1_luminance_source,
        "影画1：耀变无视目标50%全属性抗性",
        cinema1.description,
        (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE
        ),
        effects=(
            _modifier(
                "cinema1:luminance-flare-resistance-ignore",
                cinema1_luminance_source,
                CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                Resolved(0.50),
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(REMIELLE_ID),
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.LUMINANCE),
                ),
            ),
        ),
    )

    cinema2 = raw_record.mindscapes[1]
    cinema2_source = source_for(
        REMIELLE_ID,
        "cinema2",
        EffectSourceType.CINEMA,
        cinema2.name,
        cinema2.description,
    )
    cinema2_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 2
        else RuleEligibility.INELIGIBLE
    )
    cinema2_mutation_increase = float(cinema2_mutation_match.group("value")) / 100.0
    cinema2_mutation_source = source_for(
        REMIELLE_ID,
        "cinema2-mutation-coefficient",
        EffectSourceType.CINEMA,
        f"{cinema2.name}（异化系数+{cinema2_mutation_increase * 100:g}%）",
        cinema2.description,
    )
    cinema2_mutation_rule = _rule(
        "cinema2:anomaly-mutation-coefficient",
        cinema2_mutation_source,
        "影画2：异化系数提升",
        cinema2.description,
        cinema2_eligibility,
        effects=(
            _modifier(
                "cinema2:anomaly-mutation-coefficient",
                cinema2_mutation_source,
                CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
                Resolved(cinema2_mutation_increase),
                target=EffectTarget.TEAM,
                filters=(
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                ),
                operation=EffectOperation.ADD,
            ),
            _modifier(
                "cinema2:disorder-source-anomaly-mutation-coefficient",
                cinema2_mutation_source,
                CalculationNode.ANOMALY_MUTATION_COEFFICIENT,
                Resolved(cinema2_mutation_increase),
                target=EffectTarget.TEAM,
                filters=(DamageTypeFilter(DamageType.DISORDER),),
                operation=EffectOperation.ADD,
            ),
        ),
    )
    cinema2_rule = _rule(
        "cinema2:team-anomaly-defense-ignore-on-prism",
        cinema2_source,
        "影画2：幻色目标受到异常角色的属性异常伤害时无视防御",
        cinema2.description,
        cinema2_eligibility,
        condition_ids=(ENEMY_PRISM_ACTIVE,),
        effects=(
            _modifier(
                "cinema2:team-anomaly-defense-ignore-on-prism",
                cinema2_source,
                CalculationNode.DAMAGE_DEFENSE_IGNORE,
                Resolved(0.15),
                target=EffectTarget.TEAM,
                filters=(
                    CharacterRoleFilter(CharacterRole.ANOMALY),
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                ),
            ),
        ),
    )

    flare_ap_match = re.search(
        r"异常精通的(?P<value>[\d.]+)%提升此伤害倍率",
        plain_core,
    )
    if flare_ap_match is None:
        raise ValueError("Remielle Core source is missing the Flare AP multiplier")
    flare_ap_coefficient = float(flare_ap_match.group("value")) / 100.0
    flare_ap_source = source_for(
        REMIELLE_ID,
        "core:flare-ap-multiplier",
        EffectSourceType.CORE_PASSIVE,
        f"{core.name}（耀变倍率按当前异常精通增加{float(flare_ap_match.group('value')):g}%）",
        core.description,
    )
    flare_ap_value = PanelStatDerivedValue(
        source_character_id=REMIELLE_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
        coefficient=Resolved(flare_ap_coefficient),
        base=Resolved(0.0),
    )
    flare_ap_rule = _rule(
        "core:flare-ap-multiplier",
        flare_ap_source,
        "核心被动：耀变倍率按当前异常精通提升",
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=(
            _modifier(
                "core:flare-ap-multiplier",
                flare_ap_source,
                CalculationNode.LUMINANCE_FLARE_AP_CONTRIBUTION,
                flare_ap_value,
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(REMIELLE_ID),
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.LUMINANCE),
                ),
            ),
        ),
    )

    cinema4 = raw_record.mindscapes[3]
    cinema4_source = source_for(
        REMIELLE_ID,
        "cinema4-flare-multiplier",
        EffectSourceType.CINEMA,
        cinema4.name,
        cinema4.description,
    )
    cinema4_rule = _rule(
        "cinema4:flare-multiplier",
        cinema4_source,
        "影画4：耀变伤害倍率提升12%",
        cinema4.description,
        (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE
        ),
        effects=(
            _modifier(
                "cinema4:flare-multiplier",
                cinema4_source,
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                Resolved(1.12),
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(REMIELLE_ID),
                    DamageTypeFilter(DamageType.ANOMALY),
                    DamageSubtypeFilter(DamageSubtype.LUMINANCE),
                ),
                operation=EffectOperation.MULTIPLY,
            ),
        ),
    )

    cinema6 = raw_record.mindscapes[5]
    cinema6_source = source_for(
        REMIELLE_ID,
        "cinema6-flare-repeat",
        EffectSourceType.CINEMA,
        cinema6.name,
        cinema6.description,
    )
    cinema6_rule = _rule(
        "cinema6:flare-repeat",
        cinema6_source,
        "影画6：垂虹与惊鸿的耀变额外触发一次",
        cinema6.description,
        (
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE
        ),
    )

    rules = (
        mutation_rule,
        three_anomaly_rule,
        cinema2_mutation_rule,
        extra_team_attack,
        cinema1_rule,
        cinema1_luminance_rule,
        cinema2_rule,
        flare_ap_rule,
        cinema4_rule,
        cinema6_rule,
    )
    return build_definition(
        character_id=REMIELLE_ID,
        role=CharacterRole.ANOMALY,
        element=Element.LUMINANCE,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        diagnostics=diagnostics,
    )


__all__ = ["compile_remielle", "load_raw_record"]
