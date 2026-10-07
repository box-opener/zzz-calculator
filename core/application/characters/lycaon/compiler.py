"""Compile Lycaon's reviewed live Nanoka 3.2 record."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re

from core.types import (
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
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
    EnemyStateFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    NoCritRule,
    NotCondition,
    NotFilter,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    StateId,
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
from .config import LycaonCompileConfig
from .reviewed import (
    HUNT_OFF_FIELD_ACTIVE,
    ICE_ANOMALY_MOVE_ID,
    ICE_ANOMALY_RECORD_ID,
    ICE_DISORDER_MOVE_ID,
    ICE_RESISTANCE_DEBUFF_ACTIVE,
    LYCAON_ID,
    OTHER_ELEMENT_VULNERABILITY_ACTIVE,
    reviewed_mapping,
)


_ICE_DISORDER_REMAINING_SECONDS = ScenarioParameterId(
    "parameter:lycaon:ice-disorder-remaining-seconds"
)
_ENEMY_STUNNED = StateId("state:enemy:stunned")


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
    return source_for(LYCAON_ID, key, kind, label, text)


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
        rule_id=RuleItemId(f"rule:character:1141:{key}"),
        owner=LYCAON_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(conditions),
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
            effect_id=EffectId(f"effect:character:1141:{key}"),
            source=source,
            owner=LYCAON_ID,
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
        diagnostic_id=DiagnosticId(f"unsupported:character:1141:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _potential_view(data: Mapping[str, object], potential_level: int) -> dict[str, object]:
    if not 0 <= potential_level <= 6:
        raise ValueError("Lycaon potential level must be between 0 and 6")
    raw_details = data.get("potential_detail")
    if not isinstance(raw_details, Mapping):
        raise ValueError("Lycaon source has no potential_detail map")
    selected_id: int | None = None
    if potential_level:
        selected = next(
            (
                item
                for item in raw_details.values()
                if isinstance(item, Mapping)
                and item.get("level") == potential_level
                and isinstance(item.get("id"), int)
                and not isinstance(item.get("id"), bool)
            ),
            None,
        )
        if selected is None:
            raise ValueError(f"Lycaon source is missing Potential level {potential_level}")
        selected_id = int(selected["id"])

    def base_variant(value: object) -> bool:
        return value is None or (
            isinstance(value, (list, tuple)) and (not value or 0 in value)
        )

    def select_skill(value: object) -> bool:
        if base_variant(value):
            return True
        return (
            selected_id is not None
            and isinstance(value, (list, tuple))
            and selected_id in value
        )

    def select_passive(value: object) -> bool:
        if potential_level == 0:
            return base_variant(value)
        return (
            isinstance(value, (list, tuple))
            and selected_id is not None
            and selected_id in value
        )

    view = deepcopy(dict(data))
    skill = view.get("skill")
    if isinstance(skill, dict):
        for section in skill.values():
            if isinstance(section, dict) and isinstance(section.get("description"), list):
                section["description"] = [
                    item
                    for item in section["description"]
                    if isinstance(item, dict) and select_skill(item.get("potential"))
                ]
    passive = view.get("passive")
    if isinstance(passive, dict) and isinstance(passive.get("level"), dict):
        passive["level"] = {
            key: item
            for key, item in passive["level"].items()
            if isinstance(item, dict) and select_passive(item.get("potential"))
        }
    return view


def load_raw_record(
    data: Mapping[str, object], *, potential_level: int = 0
) -> NanokaRawRecord:
    return load_nanoka_raw_record(
        _potential_view(data, potential_level),
        expected_character_id=str(LYCAON_ID),
    )


def _direct_template(
    *,
    key: str,
    label: str,
    move_id: MoveId | None,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    element: Element,
) -> DirectDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:character:1141:{key}:main"),
        semantic_id=DamageEventSemanticId(f"event:character:1141:{key}:main"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=element,
    )
    return DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=LYCAON_ID,
        element=element,
        base_source=CurrentAttackValueSource(LYCAON_ID),
        crit_rule=StandardCritRule(LYCAON_ID),
        move_id=move_id,
    )


def _hunt_followup_templates_and_effects(
    raw_moves,
    config: LycaonCompileConfig,
    core_source: RuleSource,
):
    """Build the two source-defined Lycaon-owned Hunt sequences without replaying history."""

    if config.potential_level < 1:
        return (), (), (), ()

    def child_template_and_effect(
        *,
        key: str,
        label: str,
        parent_entry_key: str,
        rule_key: str,
        source_name: str,
        parameter_name: str,
        source_skill_id: str,
        skill_group: SkillGroup,
        damage_tag: DamageTag,
        element: Element,
    ):
        diagnostics: list[CalculationDiagnostic] = []
        multiplier = raw_multiplier(
            raw_moves,
            source_name,
            parameter_name,
            effective_skill_level(config, skill_group),
            f"character:1141:{key}",
            diagnostics,
            source_skill_id=source_skill_id,
        )
        if diagnostics or not isinstance(multiplier, float):
            raise ValueError(f"Lycaon Hunt child source is unresolved: {key}")
        source_rule_id = RuleItemId(f"rule:character:1141:{rule_key}")
        template_id = EventTemplateId(f"template:character:1141:{key}")
        ref = DamageEventTemplateRef(
            template_id=template_id,
            semantic_id=DamageEventSemanticId(f"event:character:1141:{key}"),
            label=label,
            damage_type=DamageType.DIRECT,
            skill_group=skill_group,
            damage_tags=frozenset({damage_tag}),
            element=element,
            source_rule_item_id=source_rule_id,
        )
        typed = DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=LYCAON_ID,
            element=element,
            base_source=CurrentAttackValueSource(LYCAON_ID),
            crit_rule=StandardCritRule(LYCAON_ID),
            move_id=None,
        )
        effect = EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId(f"effect:character:1141:{key}"),
                source=core_source,
                owner=LYCAON_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(LYCAON_ID),
                    EventTemplateIdFilter(
                        EventTemplateId(f"template:character:1141:{parent_entry_key}:main")
                    ),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=template_id,
                unique_per_source_event=True,
            ),
        )
        derived = DerivedDamageEventTemplateRef(
            template=ref,
            multiplier=FixedMultiplier(Resolved(multiplier)),
            repeat_count=1,
        )
        return typed, effect, derived

    basic_children = tuple(
        child_template_and_effect(
            key=f"hunt-basic-sequence-stage{stage}",
            label=f"围猎同步普通攻击（{('一', '二', '三')[stage - 1]}段）",
            parent_entry_key="hunt-off-field-basic-sequence",
            rule_key="core:hunt-basic-sequence",
            source_name="普通攻击：狩月舞步",
            parameter_name=f"{('一', '二', '三')[stage - 1]}段伤害倍率",
            source_skill_id=f"114100{2 * stage - 1}",
            skill_group=SkillGroup.BASIC_ATTACK,
            damage_tag=DamageTag.BASIC_ATTACK,
            element=Element.PHYSICAL,
        )
        for stage in (2, 3)
    )
    counter_followup = child_template_and_effect(
        key="hunt-counter-basic3-followup",
        label="围猎闪避反击后衔接普通攻击三段",
        parent_entry_key="hunt-counter-basic3-followup",
        rule_key="core:hunt-counter-basic3-followup",
        source_name="普通攻击：狩月舞步",
        parameter_name="三段伤害倍率",
        source_skill_id="1141005",
        skill_group=SkillGroup.BASIC_ATTACK,
        damage_tag=DamageTag.BASIC_ATTACK,
        element=Element.PHYSICAL,
    )
    return (
        tuple(item[0] for item in basic_children) + (counter_followup[0],),
        tuple(item[1] for item in basic_children),
        (counter_followup[1],),
        tuple(item[2] for item in basic_children) + (counter_followup[2],),
    )


def _static_anomaly_entries():
    """Expose only the anomaly/Disorder records enabled by Lycaon's Ice buildup."""

    ice_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1141:ice-anomaly"),
        semantic_id=DamageEventSemanticId("event:character:1141:ice-anomaly"),
        label="属性异常：碎冰（10秒满异常）",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ICE,
    )
    ice_template = AttributeAnomalyDamageEventTemplate(
        ref=ice_ref,
        damage_dealer=LYCAON_ID,
        element=Element.ICE,
        anomaly_triggerer=LYCAON_ID,
        history_record_source=ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ICE_ANOMALY_MOVE_ID,
    )
    ice_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1141:ice-anomaly"),
        character_id=LYCAON_ID,
        move_id=ICE_ANOMALY_MOVE_ID,
        display_name="属性异常：碎冰（10秒满异常）",
        original_text="按规范静态单人100%积蓄冰异常；10秒碎冰倍率500%，使用NoCrit。Lycaon的纯物理来源不生成物理异常记录。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1141:ice-anomaly"),
                label="碎冰500%（10秒）",
                parameter_name="碎冰倍率",
                multiplier=FixedMultiplier(Resolved(5.0)),
            ),
        ),
        main_damage_event=ice_ref,
    )

    disorder_ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:character:1141:ice-disorder"),
        semantic_id=DamageEventSemanticId("event:character:1141:ice-disorder"),
        label="紊乱：碎冰（默认最大剩余时间）",
        damage_type=DamageType.DISORDER,
        element=Element.ICE,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=LYCAON_ID,
        element=Element.ICE,
        disorder_triggerer=LYCAON_ID,
        history_record_source=ICE_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=ICE_DISORDER_MOVE_ID,
    )
    disorder_entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:character:1141:ice-disorder"),
        character_id=LYCAON_ID,
        move_id=ICE_DISORDER_MOVE_ID,
        display_name="紊乱：碎冰（默认最大剩余时间）",
        original_text="冰紊乱基础倍率450% + floor(t)×7.5%；t范围0–10秒，默认10秒，不模拟时序；使用NoCrit。",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:character:1141:ice-disorder"),
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
    remaining = ScenarioIntegerParameter(
        parameter_id=_ICE_DISORDER_REMAINING_SECONDS,
        label="冰异常剩余持续时间（秒）",
        original_text="按本次选定的剩余时间计算；范围0–10秒，默认10秒，不从战斗时序推断。",
        resolution=ParameterResolution.USER_SELECTED,
        value=10,
        minimum=0,
        maximum=10,
    )
    return (ice_entry, disorder_entry), (ice_template, disorder_template), (remaining,)


def compile_lycaon(
    config: LycaonCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    mapping = reviewed_mapping(config.potential_level)
    entries, direct_templates, direct_diagnostics = compile_direct_moves(
        character_id=LYCAON_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=mapping,
        id_namespace="character:1141",
    )
    entries = list(entries)
    templates = list(direct_templates)
    diagnostics = list(direct_diagnostics)
    hunt_derived_damage_events = ()

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    conditions: list[ScenarioCondition] = []
    rules: list[CalculationRuleItem] = []
    if config.potential_level >= 1:
        conditions.append(
            _condition(
                HUNT_OFF_FIELD_ACTIVE,
                "莱卡恩当前处于围猎状态且为非当前操作角色",
                core.description,
            )
        )

    core_ice_res_condition = _condition(
        ICE_RESISTANCE_DEBUFF_ACTIVE,
        "目标当前受莱卡恩的冰抗降低影响",
        core.description,
    )
    core_ice_res = _number(
        core.description,
        r"冰属性伤害抗性降低(?P<value>[\d.]+)%",
        "Lycaon Core Ice resistance reduction",
    ) / 100.0
    rules.append(
        _rule(
            "core:enemy-ice-resistance-reduction",
            core_source,
            f"核心被动：狂猎时刻／支援突击命中后冰抗降低{core_ice_res:.0%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            conditions=(ICE_RESISTANCE_DEBUFF_ACTIVE,),
            effects=(
                _modifier(
                    "core:enemy-ice-resistance-reduction",
                    core_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(core_ice_res),
                    target=EffectTarget.ENEMY,
                    filters=(element_scope_filter(Element.ICE),),
                ),
            ),
        )
    )
    if config.potential_level >= 1:
        hunt_child_templates, hunt_basic_effects, hunt_counter_effects, hunt_derived_damage_events = (
            _hunt_followup_templates_and_effects(
                raw_move_index(raw_record),
                config,
                core_source,
            )
        )
        templates.extend(hunt_child_templates)
        rules.append(
            _rule(
                "core:hunt-basic-sequence",
                core_source,
                "潜能核心：围猎同步普通攻击二至三段",
                core.description,
                RuleEligibility.ELIGIBLE,
                conditions=(HUNT_OFF_FIELD_ACTIVE,),
                effects=hunt_basic_effects,
                diagnostics=(
                    _note(
                        "core:hunt-automatic-link-limit",
                        "This selectable Lycaon-owned Basic1–3 sequence is explicit. The calculator does not automatically synthesize it from a different teammate's Basic/EX history.",
                        core.description,
                    ),
                ),
            )
        )
        rules.append(
            _rule(
                "core:hunt-counter-basic3-followup",
                core_source,
                "潜能核心：围猎闪避反击后衔接普通攻击三段",
                core.description,
                RuleEligibility.ELIGIBLE,
                conditions=(HUNT_OFF_FIELD_ACTIVE,),
                effects=hunt_counter_effects,
            )
        )
    rules.append(
        _rule(
            "core:source-only-daze",
            core_source,
            "核心被动：蓄力普通攻击失衡值提升（当前结果无失衡值输出）",
            core.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                _note(
                    "core:daze-source-only",
                    "The Core lists Daze increases for charged Basic and, in the Potential view, Dash/Counter. The calculation result has no Daze value, so only the source text is retained.",
                    core.description,
                ),
                *(
                    (
                        _note(
                            "core:ice-dance-quick-assist-source-only",
                            "Potential Ice Dance can trigger the previous teammate's Quick Assist. That other agent's action/resource history is not synthesized; Ice Dance remains selectable as Lycaon's own Direct hit.",
                            core.description,
                        ),
                    )
                    if config.potential_level >= 1
                    else ()
                ),
            ),
        )
    )
    conditions.append(core_ice_res_condition)

    other_element_vulnerability = re.search(
        r"受到的其他属性伤害提升(?P<value>[\d.]+)%",
        _plain(core.description),
        re.DOTALL,
    )
    if config.potential_level >= 1 and other_element_vulnerability is not None:
        bonus = float(other_element_vulnerability.group("value")) / 100.0
        conditions.append(
            _condition(
                OTHER_ELEMENT_VULNERABILITY_ACTIVE,
                "目标当前受潜能核心的其他属性伤害易伤影响",
                core.description,
            )
        )
        rules.append(
            _rule(
                "potential-core:other-element-vulnerability",
                core_source,
                f"潜能核心：目标受到其他属性伤害提升{bonus:.0%}",
                core.description,
                RuleEligibility.ELIGIBLE,
                conditions=(OTHER_ELEMENT_VULNERABILITY_ACTIVE,),
                effects=(
                    _modifier(
                        "potential-core:other-element-vulnerability",
                        core_source,
                        CalculationNode.ENEMY_NORMAL_VULNERABILITY,
                        Resolved(bonus),
                        target=EffectTarget.ENEMY,
                        filters=(NotFilter(element_scope_filter(Element.ICE)),),
                    ),
                ),
            )
        )

    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    enemy_stun_vulnerability = _number(
        core.extra_ability_description,
        r"失衡易伤倍率提升(?P<value>[\d.]+)%",
        "Lycaon Additional Ability enemy Stun vulnerability",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:enemy-stun-vulnerability",
            extra_source,
            f"额外能力：失衡目标的失衡易伤倍率+{enemy_stun_vulnerability:.0%}",
            core.extra_ability_description,
            extra_eligibility,
            effects=(
                _modifier(
                    "extra-ability:enemy-stun-vulnerability",
                    extra_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(enemy_stun_vulnerability),
                    target=EffectTarget.ENEMY,
                    filters=(EnemyStateFilter(_ENEMY_STUNNED),),
                ),
            ),
        )
    )

    if config.potential_level >= 2:
        potential = next(
            item for item in raw_record.potential_details if item.level == config.potential_level
        )
        impact_bonus = _number(
            potential.description,
            r"冲击力提升(?P<value>[\d.]+)%",
            f"Lycaon Potential {config.potential_level} off-field Impact bonus",
        ) / 100.0
        rules.append(
            _rule(
                f"potential{config.potential_level}:off-field-impact",
                _source(
                    f"potential-{config.potential_level}",
                    EffectSourceType.SPECIAL_MECHANISM,
                    potential.name or potential.level_show_name,
                    potential.description,
                ),
                f"潜能{config.potential_level}：围猎期间后台冲击力+{impact_bonus:.1%}",
                potential.description,
                RuleEligibility.ELIGIBLE,
                conditions=(HUNT_OFF_FIELD_ACTIVE,),
                effects=(
                    _modifier(
                        f"potential{config.potential_level}:off-field-impact",
                        _source(
                            f"potential-{config.potential_level}",
                            EffectSourceType.SPECIAL_MECHANISM,
                            potential.name or potential.level_show_name,
                            potential.description,
                        ),
                        CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
                        Resolved(impact_bonus),
                        target=EffectTarget.SELF,
                        condition=NotCondition(
                            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)
                        ),
                    ),
                ),
            )
        )

    cinema1 = raw_record.mindscapes[0]
    rules.append(
        _rule(
            "cinema1:source-only-daze",
            _source("cinema-1", EffectSourceType.CINEMA, cinema1.name, cinema1.description),
            "1影：强化特殊技失衡值提升（当前结果无失衡值输出）",
            cinema1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            diagnostics=(
                _note(
                    "cinema1:daze-source-only",
                    "Cinema 1 modifies Daze on the EX hit/charged state; Daze and timing results are not emitted.",
                    cinema1.description,
                ),
            ),
        )
    )
    for level in (2, 3, 4, 5):
        cinema = raw_record.mindscapes[level - 1]
        source = _source(f"cinema-{level}", EffectSourceType.CINEMA, cinema.name, cinema.description)
        if level in {3, 5}:
            rules.append(
                _rule(
                    f"cinema{level}:skill-levels",
                    source,
                    f"{level}影：技能等级提升",
                    cinema.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                )
            )
        else:
            source_notes = ()
            if level == 2:
                source_notes = (
                    _note(
                        "cinema2:energy-source-only",
                        "Cinema 2's Energy gain is source-only; the calculator does not model Energy or the one-second trigger limit.",
                        cinema.description,
                    ),
                )
            elif level == 4:
                source_notes = (
                    _note(
                        "cinema4:shield-source-only",
                        "Cinema 4's shield capacity, incoming damage, and interruption-resistance effects have no output in the current calculator.",
                        cinema.description,
                    ),
                )
            rules.append(
                _rule(
                    f"cinema{level}:source-only",
                    source,
                    f"{level}影：能量／护盾效果不在当前结果中模拟",
                    cinema.description,
                    RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
                    diagnostics=source_notes,
                )
            )

    cinema6 = raw_record.mindscapes[5]
    c6_bonus = _number(
        cinema6.description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Lycaon Cinema 6 damage bonus per stack",
    ) / 100.0
    rules.append(
        _rule(
            "cinema6:current-damage-bonus-stacks",
            _source("cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description),
            f"6影：当前目标伤害增益+{c6_bonus:.0%}×层数",
            cinema6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            stack_count=5,
            stack_min=0,
            stack_max=5,
            effects=(
                _modifier(
                    "cinema6:current-damage-bonus-stacks",
                    _source("cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description),
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c6_bonus),
                    target=EffectTarget.SELF,
                    filters=(DamageDealerFilter(LYCAON_ID),),
                ),
            ) if config.cinema_level >= 6 else (),
            diagnostics=(
                _note(
                    "cinema6:duration-and-per-move-cap",
                    "Cinema 6 uses the selected current 0–5 stack count; the calculator does not simulate duration, refreshes, or one-stack-per-move history.",
                    cinema6.description,
                ),
            ),
        )
    )

    static_entries, static_templates, static_parameters = _static_anomaly_entries()
    entries = (*entries, *static_entries)
    templates = (*templates, *static_templates)

    source_only_assist = next(
        item for item in raw_record.moves if item.name == "招架支援：狩猎干预"
    )
    rules.append(
        _rule(
            "assist-parry:daze-source-only",
            _source(
                "assist-parry:daze-source-only",
                EffectSourceType.SKILL,
                source_only_assist.name,
                source_only_assist.description,
            ),
            "招架支援：狩猎干预（来源仅列失衡倍率）",
            source_only_assist.description,
            RuleEligibility.ELIGIBLE,
            diagnostics=(
                _note(
                    "assist-parry:daze-only",
                    "This Defense Assist source contains Daze values but no damage ratio; no damage event is fabricated.",
                    source_only_assist.description,
                ),
            ),
        )
    )

    return build_definition(
        character_id=LYCAON_ID,
        role=CharacterRole.STUN,
        element=Element.ICE,
        source=_source("character", EffectSourceType.SKILL, raw_record.name, raw_record.code_name),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=tuple(conditions),
        parameters=static_parameters,
        independent_derived_damage_events=hunt_derived_damage_events,
        diagnostics=tuple(diagnostics),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: LycaonCompileConfig) -> None:
    if raw.character_id != LYCAON_ID or raw.name != "莱卡恩" or raw.code_name != "Lycaon":
        raise ValueError("unexpected identity in Lycaon raw record")
    if raw.specialty != "击破" or raw.element != "冰属性" or raw.rarity != 4:
        raise ValueError("Lycaon raw role, element, or rank changed from reviewed source")
    if raw.faction != "维多利亚家政":
        raise ValueError("Lycaon raw faction changed from reviewed source")
    if (
        raw.source_version != "3.2"
        or raw.source_url != "https://static.nanoka.cc/zzz/3.2/zh/character/1141.json"
    ):
        raise ValueError("Lycaon provenance must identify live Nanoka 3.2 character 1141")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Lycaon compile view must contain seven Core levels and six Cinemas")
    if config.potential_level > 0 and not any(
        item.level == config.potential_level for item in raw.potential_details
    ):
        raise ValueError(f"Lycaon source is missing Potential level {config.potential_level}")
    expected_core_source = "1141501" if config.potential_level == 0 else "1141508"
    if raw.core_levels[0].source_id != expected_core_source:
        raise ValueError("Lycaon source potential projection does not match its compile config")


__all__ = ["compile_lycaon", "load_raw_record"]
