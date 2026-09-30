"""Compile the Nanoka Trigger record into application contracts."""

from __future__ import annotations

from core.types import (
    AnyFilter,
    BattleEventKind,
    CharacterFilter,
    CharacterId,
    CharacterRole,
    CalculationNode,
    CreatedByEffectFilter,
    CurrentAttackValueSource,
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
    EventSelector,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    MoveIdFilter,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
)

from ...ids import DamageEventSemanticId, RuleItemId
from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import DiagnosticId
from ...moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import DirectDamageEventTemplate
from .config import TriggerCompileConfig
from .reviewed import (
    FOLLOW_UP_ACTIVE_CONDITION_ID,
    HUNTER_EYE_CONDITION_ID,
    SNIPER_STANCE_CONDITION_ID,
    TRIGGER_ID,
    TRIGGER_REVIEWED_MAPPING,
)


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )


def _rule(
    rule_id: str,
    source: RuleSource,
    name: str,
    text: str,
    eligibility: RuleEligibility,
    effects=(),
    *,
    condition_ids=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(rule_id),
        owner=TRIGGER_ID,
        source=source,
        display_name=name,
        original_text=text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
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
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1361:{key}"),
            source=source,
            owner=TRIGGER_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("raw Trigger record must contain all seven core levels") from exc


def _raw_talent(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Trigger record is missing cinema {level}") from exc


def _independent_bullet(
    source_rule_id: RuleItemId,
    source: RuleSource,
) -> tuple[DerivedDamageEventTemplateRef, DirectDamageEventTemplate]:
    template_id = "template:character:1361:cinema6:armor-piercing-round"
    semantic_id = "event:character:1361:cinema6:armor-piercing-round"
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label="6影：破甲凶弹",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.ELECTRIC,
        source_rule_item_id=source_rule_id,
    )
    return (
        DerivedDamageEventTemplateRef(
            template=ref,
            multiplier=FixedMultiplier(Resolved(12.0)),
            repeat_count=1,
        ),
        DirectDamageEventTemplate(
            ref=ref,
            damage_dealer=TRIGGER_ID,
            element=Element.ELECTRIC,
            base_source=CurrentAttackValueSource(TRIGGER_ID),
            crit_rule=StandardCritRule(TRIGGER_ID),
            move_id=None,
        ),
    )


def _independent_severance(
    source_rule_id: RuleItemId,
) -> tuple[DerivedDamageEventTemplateRef, DirectDamageEventTemplate]:
    """Build C4's independent 200%-ATK severance event.

    The parent concerto move identity is deliberately not copied onto this
    child.  C4's EventCreation filter is the only trigger boundary; keeping
    the child move-less also makes the explicit no-recursion contract clear.
    """

    ref = DamageEventTemplateRef(
        template_id="template:character:1361:cinema4:severance",
        semantic_id="event:character:1361:cinema4:severance",
        label="4影：断离额外伤害",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.ELECTRIC,
        source_rule_item_id=source_rule_id,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(2.0)),
        repeat_count=1,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=TRIGGER_ID,
        element=Element.ELECTRIC,
        base_source=CurrentAttackValueSource(TRIGGER_ID),
        crit_rule=StandardCritRule(TRIGGER_ID),
        move_id=None,
    )
    return derived, typed


def compile_trigger(
    config: TriggerCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = TRIGGER_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=TRIGGER_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="trigger:1361",
    )
    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        TRIGGER_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    conditions = (
        _condition(
            SNIPER_STANCE_CONDITION_ID,
            "当前处于狙击姿态",
            "[狙击姿态]",
        ),
        _condition(
            HUNTER_EYE_CONDITION_ID,
            "当前存在猎眸层数",
            "拥有[猎眸]",
        ),
        _condition(
            FOLLOW_UP_ACTIVE_CONDITION_ID,
            "当前触发扳机追加攻击",
            "[追加攻击]",
        ),
    )
    follow_up_filter = (DamageTagFilter(DamageTag.FOLLOW_UP_ATTACK),)

    # The source event activates an enemy debuff, but the active debuff is a
    # settlement fact that any teammate's current event may consume.  It must
    # therefore not be filtered by the current settlement event's
    # FOLLOW_UP tag.  The non-stun lane preserves the text's explicit promise
    # that the bonus works before the enemy enters daze; the enemy's ordinary
    # base stun vulnerability remains in its own stun lane.
    rules: list[CalculationRuleItem] = [
        _rule(
            "rule:trigger:1361:core-passive",
            core_source,
            core.name,
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "core:stun-vulnerability",
                    core_source,
                    CalculationNode.ENEMY_NORMAL_VULNERABILITY,
                    Resolved(0.20 + 0.025 * (config.core_level - 1)),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    ]

    extra_source = source_for(
        TRIGGER_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    rules.append(
        _rule(
            "rule:trigger:1361:extra-ability",
            extra_source,
            raw_record.extra_ability_name,
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "extra-ability:follow-up-daze",
                    extra_source,
                    CalculationNode.DAZE_OUTGOING_BONUS,
                    Resolved(0.75),
                    target=EffectTarget.SELF,
                    filters=follow_up_filter,
                ),
            ),
        )
    )

    c1 = _raw_talent(raw_record, 1)
    c1_source = source_for(
        TRIGGER_ID,
        "cinema-1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    rules.append(
        _rule(
            "rule:trigger:1361:cinema1",
            c1_source,
            f"1影：{c1.name}",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:stun-vulnerability",
                    c1_source,
                    CalculationNode.ENEMY_NORMAL_VULNERABILITY,
                    Resolved(0.20),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    )

    c2 = _raw_talent(raw_record, 2)
    c2_source = source_for(
        TRIGGER_ID,
        "cinema-2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    rules.append(
        _rule(
            "rule:trigger:1361:cinema2",
            c2_source,
            f"2影：{c2.name}",
            c2.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:team-crit-damage",
                    c2_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(0.06),
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(HUNTER_EYE_CONDITION_ID,),
            stack_count=4,
            stack_min=0,
            stack_max=4,
        )
    )

    c3 = _raw_talent(raw_record, 3)
    c3_source = source_for(
        TRIGGER_ID,
        "cinema-3",
        EffectSourceType.CINEMA,
        f"3影：{c3.name}",
        c3.description,
    )
    rules.append(
        _rule(
            "rule:trigger:1361:cinema3",
            c3_source,
            f"3影：{c3.name}",
            c3.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 3
            else RuleEligibility.INELIGIBLE,
        )
    )

    c4 = _raw_talent(raw_record, 4)
    c4_source = source_for(
        TRIGGER_ID,
        "cinema-4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    c4_rule_id = RuleItemId("rule:trigger:1361:cinema4")
    c4_derived, c4_template = _independent_severance(c4_rule_id)
    templates = (*templates, c4_template)
    c4_effect_id = EffectId("effect:character:1361:cinema4:severance")
    rules.append(
        _rule(
            str(c4_rule_id),
            c4_source,
            f"4影：{c4.name}",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=c4_effect_id,
                        source=c4_source,
                        owner=TRIGGER_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            AnyFilter(
                                (
                                    # C4 is tied to the actual concerto
                                    # attack identity, including its Hell
                                    # variant, rather than to Trigger being
                                    # the current operator.
                                    MoveIdFilter(MoveId("move:trigger:concerto-sniping")),
                                    MoveIdFilter(
                                        MoveId("move:trigger:concerto-sniping-hell")
                                    ),
                                )
                            ),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=c4_derived.template.template_id,
                    ),
                ),
            ),
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        "unsupported:trigger:1361:cinema4:impact-daze"
                    ),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message=(
                        "C4 断离额外120%冲击力失衡值 is retained in source text "
                        "but this static calculator scope does not model the daze result"
                    ),
                    blocking=False,
                    original_text="额外累积「扳机」120%冲击力的失衡值",
                ),
            ),
        )
    )

    c5 = _raw_talent(raw_record, 5)
    c5_source = source_for(
        TRIGGER_ID,
        "cinema-5",
        EffectSourceType.CINEMA,
        f"5影：{c5.name}",
        c5.description,
    )
    rules.append(
        _rule(
            "rule:trigger:1361:cinema5",
            c5_source,
            f"5影：{c5.name}",
            c5.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 5
            else RuleEligibility.INELIGIBLE,
        )
    )

    c6 = _raw_talent(raw_record, 6)
    c6_source = source_for(
        TRIGGER_ID,
        "cinema-6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    c6_rule_id = RuleItemId("rule:trigger:1361:cinema6")
    derived, derived_template = _independent_bullet(c6_rule_id, c6_source)
    templates = (*templates, derived_template)
    rules.append(
        _rule(
            str(c6_rule_id),
            c6_source,
            f"6影：{c6.name}",
            c6.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema6:armor-piercing-round-damage",
                    c6_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.50),
                    target=EffectTarget.TEAM,
                    filters=(
                        # The 50% is specific to the independently-created
                        # bullet; ordinary Trigger attacks keep their normal
                        # multiplier lane untouched.
                        CreatedByEffectFilter(
                            EffectId(
                                "effect:character:1361:cinema6:armor-piercing-round"
                            )
                        ),
                    ),
                ),
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1361:cinema6:armor-piercing-round"
                        ),
                        source=c6_source,
                        owner=TRIGGER_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            CharacterFilter(TRIGGER_ID),
                            DamageTagFilter(DamageTag.BASIC_ATTACK),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=derived.template.template_id,
                    ),
                ),
            ),
            condition_ids=(SNIPER_STANCE_CONDITION_ID,),
        )
    )

    return build_definition(
        character_id=TRIGGER_ID,
        role=CharacterRole.STUN,
        element=Element.ELECTRIC,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        independent_derived_damage_events=(c4_derived, derived),
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: TriggerCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "「扳机」":
        raise ValueError("unexpected character name in raw Trigger record")
    if raw.code_name != "Trigger":
        raise ValueError("unexpected Trigger code name in raw record")
    if raw.specialty != "击破":
        raise ValueError("unexpected Trigger specialty in raw record")
    if raw.element != "电属性":
        raise ValueError("unexpected Trigger element in raw record")
    if len(raw.core_levels) != 7:
        raise ValueError("raw Trigger record must contain all seven core levels")
    if len(raw.mindscapes) != 6:
        raise ValueError("raw Trigger record must contain all six mindscapes")


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(TRIGGER_ID))


__all__ = [
    "FOLLOW_UP_ACTIVE_CONDITION_ID",
    "HUNTER_EYE_CONDITION_ID",
    "SNIPER_STANCE_CONDITION_ID",
    "TRIGGER_ID",
    "compile_trigger",
    "load_raw_record",
]
