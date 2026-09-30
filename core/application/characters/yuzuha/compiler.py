"""Compile the supplied Nanoka Yuzuha record into application contracts."""

from __future__ import annotations

from core.types import (
    AnyFilter,
    BattleEventKind,
    CharacterId,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    DamageMultiplier,
    DamageTag,
    DamageTagFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageType,
    DamageTypeFilter,
    Element,
    ElementFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
)

from ...element_scope import element_scope_filter
from ...ids import DamageEventSemanticId, RuleItemId, ScenarioParameterId
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ...moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .config import YuzuhaCompileConfig
from ..templates import DirectDamageEventTemplate
from .reviewed import (
    SWEET_SCARE_ACTIVE_CONDITION_ID,
    TANUKI_ATTACK_CONDITION_ID,
    TANUKI_SELF_ATTACK_CONDITION_ID,
    TANUKI_WISH_ACTIVE_CONDITION_ID,
    YUZUHA_ID,
    YUZUHA_REVIEWED_MAPPING,
)


# The source descriptions expose one reviewed cap at each core level.  The
# values are kept as a level curve (rather than a single level-12 constant),
# and the compiler always selects the requested core level.
TANUKI_WISH_ATTACK_CAPS = (600.0, 700.0, 800.0, 900.0, 1000.0, 1100.0, 1200.0)
YUZUHA_C6_SHELL_COUNT_PARAMETER_ID = ScenarioParameterId(
    "parameter:yuzuha:cinema6:strong-shell-count"
)


def _independent_shell(
    source_rule_id: RuleItemId,
) -> tuple[DerivedDamageEventTemplateRef, DirectDamageEventTemplate]:
    """Compile one C6 charged strong-shell event.

    Shells are independent direct events with their own physical identity and
    no inherited tags/move ID.  The parent support-assault move is represented
    solely by the EventCreation filter.
    """

    ref = DamageEventTemplateRef(
        template_id="template:yuzuha:1411:cinema6:strong-shell",
        semantic_id=DamageEventSemanticId(
            "event:yuzuha:1411:cinema6:strong-shell"
        ),
        label="6影：强力炮弹",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
        source_rule_item_id=source_rule_id,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=FixedMultiplier(Resolved(3.0)),
        repeat_count=1,
        repeat_count_parameter_id=YUZUHA_C6_SHELL_COUNT_PARAMETER_ID,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=YUZUHA_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(YUZUHA_ID),
        crit_rule=StandardCritRule(YUZUHA_ID),
        move_id=None,
    )
    return derived, typed


def _independent_sweet_scare_fireworks(
    source_rule_id: RuleItemId,
    multiplier: DamageMultiplier,
) -> tuple[DerivedDamageEventTemplateRef, DirectDamageEventTemplate]:
    """Compile one per-shell copy of the reviewed polar fireworks move."""

    ref = DamageEventTemplateRef(
        template_id="template:yuzuha:1411:cinema6:sweet-scare-fireworks",
        semantic_id=DamageEventSemanticId(
            "event:yuzuha:1411:cinema6:sweet-scare-fireworks"
        ),
        label="6影：甜蜜惊吓追加彩糖花火·极",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=Element.PHYSICAL,
        source_rule_item_id=source_rule_id,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=multiplier,
        repeat_count=1,
        repeat_count_parameter_id=YUZUHA_C6_SHELL_COUNT_PARAMETER_ID,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=YUZUHA_ID,
        element=Element.PHYSICAL,
        base_source=CurrentAttackValueSource(YUZUHA_ID),
        crit_rule=StandardCritRule(YUZUHA_ID),
        move_id=None,
    )
    return derived, typed


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
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    effects=(),
    *,
    condition_ids=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    non_stacking_group_id: str | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(rule_id),
        owner=YUZUHA_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        non_stacking_group_id=non_stacking_group_id,
    )


def _modifier(
    effect_key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1411:{effect_key}"),
            source=source,
            owner=YUZUHA_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("raw Yuzuha record must contain all seven core levels") from exc


def _raw_talent(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Yuzuha record is missing cinema {level}") from exc


def compile_yuzuha(
    config: YuzuhaCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = YUZUHA_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=YUZUHA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="yuzuha:1411",
    )
    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        YUZUHA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    conditions = (
        _condition(
            TANUKI_WISH_ACTIVE_CONDITION_ID,
            "当前已拥有狸之愿",
            "拥有[狸之愿]效果",
        ),
        _condition(
            TANUKI_ATTACK_CONDITION_ID,
            "狸猫阿釜协同柚叶攻击",
            "狸猫阿釜协同柚叶攻击",
        ),
        _condition(
            TANUKI_SELF_ATTACK_CONDITION_ID,
            "狸猫阿釜自主攻击",
            "狸猫阿釜自主攻击",
        ),
        _condition(
            SWEET_SCARE_ACTIVE_CONDITION_ID,
            "目标处于甜蜜惊吓",
            "处于[甜蜜惊吓]状态下的敌人",
        ),
    )

    rules: list[CalculationRuleItem] = []
    cap = TANUKI_WISH_ATTACK_CAPS[config.core_level - 1]
    core_effect = _modifier(
        "core:tanuki-wish-attack",
        core_source,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        PanelStatDerivedValue(
            source_character_id=YUZUHA_ID,
            source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
            coefficient=Resolved(0.40),
            cap_max=Resolved(cap),
        ),
        target=EffectTarget.TEAM,
    )
    core_damage = _modifier(
        "core:tanuki-wish-damage",
        core_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.15),
        target=EffectTarget.TEAM,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:core-passive",
            core_source,
            core.name,
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(core_effect, core_damage),
            condition_ids=(TANUKI_WISH_ACTIVE_CONDITION_ID,),
            non_stacking_group_id="yuzuha:tanuki-wish",
        )
    )

    extra_source = source_for(
        YUZUHA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_bonus_coefficient = 0.002 * (
        1.30 if config.cinema_level >= 1 else 1.0
    )
    extra_bonus_cap = 0.26 if config.cinema_level >= 1 else 0.20
    extra_mastery_value = PanelStatDerivedValue(
        source_character_id=YUZUHA_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
        threshold=Resolved(100.0),
        minimum=Resolved(100.0),
        coefficient=Resolved(extra_bonus_coefficient),
        cap_max=Resolved(extra_bonus_cap),
    )
    extra_buildup_value = PanelStatDerivedValue(
        source_character_id=YUZUHA_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_ANOMALY_MASTERY,
        threshold=Resolved(100.0),
        minimum=Resolved(100.0),
        coefficient=Resolved(0.002),
        cap_max=Resolved(0.20),
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:extra-ability",
            extra_source,
            raw_record.extra_ability_name,
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            # The real runtime gate is [狸之愿].  Static team eligibility is
            # represented by additional_ability_eligible; a second user
            # checkbox would create a contradictory duplicate truth value.
            condition_ids=(TANUKI_WISH_ACTIVE_CONDITION_ID,),
            effects=(
                _modifier(
                    "extra-ability:anomaly-buildup",
                    extra_source,
                    CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    extra_buildup_value,
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "extra-ability:anomaly-damage",
                    extra_source,
                    CalculationNode.ANOMALY_DAMAGE_BONUS,
                    extra_mastery_value,
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    ),
                ),
                _modifier(
                    "extra-ability:disorder-damage",
                    extra_source,
                    CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                    extra_mastery_value,
                    target=EffectTarget.TEAM,
                    filters=(DamageTypeFilter(DamageType.DISORDER),),
                ),
            ),
        )
    )

    # 1C adds a global resistance reduction while Sweet Scare is present.
    c1 = _raw_talent(raw_record, 1)
    c1_source = source_for(
        YUZUHA_ID,
        "cinema-1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema1",
            c1_source,
            f"1影：{c1.name}",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:sweet-scare-resistance",
                    c1_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(0.10),
                    target=EffectTarget.ENEMY,
                    condition=None,
                ),
            ),
            condition_ids=(SWEET_SCARE_ACTIVE_CONDITION_ID,),
        )
    )

    c2 = _raw_talent(raw_record, 2)
    c2_source = source_for(
        YUZUHA_ID,
        "cinema-2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema2",
            c2_source,
            f"2影：{c2.name}",
            c2.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:team-damage",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.15),
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "cinema2:team-buildup",
                    c2_source,
                    CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    Resolved(0.15),
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(TANUKI_WISH_ACTIVE_CONDITION_ID,),
        )
    )

    c3 = _raw_talent(raw_record, 3)
    c3_source = source_for(
        YUZUHA_ID,
        "cinema-3",
        EffectSourceType.CINEMA,
        f"3影：{c3.name}",
        c3.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema3",
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
        YUZUHA_ID,
        "cinema-4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema4",
            c4_source,
            f"4影：{c4.name}",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:assist-damage",
                    c4_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.30),
                    target=EffectTarget.SELF,
                    filters=(
                        AnyFilter(
                            (
                                MoveIdFilter(MoveId("move:yuzuha:cookie")),
                                MoveIdFilter(MoveId("move:yuzuha:stuffed-candy")),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    c5 = _raw_talent(raw_record, 5)
    c5_source = source_for(
        YUZUHA_ID,
        "cinema-5",
        EffectSourceType.CINEMA,
        f"5影：{c5.name}",
        c5.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema5",
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
        YUZUHA_ID,
        "cinema-6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    c6_shell_rule_id = RuleItemId("rule:yuzuha:1411:cinema6-shells")
    c6_shell_derived, c6_shell_template = _independent_shell(c6_shell_rule_id)
    polar_entry = next(
        item
        for item in entries
        if str(item.entry_id).endswith("basic-candy-fireworks-polar")
    )
    polar_multiplier = polar_entry.multiplier_variants[0].multiplier
    c6_fireworks_rule_id = RuleItemId(
        "rule:yuzuha:1411:cinema6:sweet-scare-fireworks"
    )
    c6_fireworks_derived, c6_fireworks_template = _independent_sweet_scare_fireworks(
        c6_fireworks_rule_id,
        polar_multiplier,
    )
    templates = (*templates, c6_shell_template, c6_fireworks_template)

    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    # Keep the stackable disorder multiplier separate from EventCreation:
    # Stage-015 intentionally rejects stacked EventCreation effects, while
    # the text gives the multiplier its own independent 0..3 stack count.
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema6",
            c6_source,
            f"6影：{c6.name}",
            c6.description,
            c6_eligibility,
            effects=(
                _modifier(
                    "cinema6:disorder-damage",
                    c6_source,
                    CalculationNode.DISORDER_EXTRA_MULTIPLIER,
                    Resolved(1.05),
                    target=EffectTarget.TEAM,
                    filters=(DamageTypeFilter(DamageType.DISORDER),),
                ),
            ),
            stack_count=3,
            stack_min=0,
            stack_max=3,
        )
    )
    rules.append(
        _rule(
            str(c6_shell_rule_id),
            c6_source,
            f"6影：{c6.name}（强力炮弹）",
            c6.description,
            c6_eligibility,
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1411:cinema6:strong-shell"
                        ),
                        source=c6_source,
                        owner=YUZUHA_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            MoveIdFilter(MoveId("move:yuzuha:stuffed-candy")),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=c6_shell_derived.template.template_id,
                    ),
                ),
            ),
        )
    )
    rules.append(
        _rule(
            str(c6_fireworks_rule_id),
            c6_source,
            f"6影：{c6.name}（甜蜜惊吓追加）",
            c6.description,
            c6_eligibility,
            effects=(
                EventCreationEffect(
                    rule=EffectRule(
                        effect_id=EffectId(
                            "effect:character:1411:cinema6:sweet-scare-fireworks"
                        ),
                        source=c6_source,
                        owner=YUZUHA_ID,
                        target=EffectTarget.TEAM,
                        snapshot_rule=SnapshotRule.SETTLEMENT,
                        filters=(
                            MoveIdFilter(MoveId("move:yuzuha:stuffed-candy")),
                        ),
                    ),
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        event_template_id=c6_fireworks_derived.template.template_id,
                    ),
                ),
            ),
            condition_ids=(SWEET_SCARE_ACTIVE_CONDITION_ID,),
        )
    )

    return build_definition(
        character_id=YUZUHA_ID,
        role=CharacterRole.SUPPORT,
        element=Element.PHYSICAL,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(
            ScenarioIntegerParameter(
                parameter_id=YUZUHA_C6_SHELL_COUNT_PARAMETER_ID,
                label="6影强力炮弹追加次数",
                original_text="每蓄能0.4秒消耗1点甜度点，最多追加2枚",
                resolution=ParameterResolution.USER_SELECTED,
                value=0,
                minimum=0,
                maximum=2,
            ),
        ),
        independent_derived_damage_events=(
            c6_shell_derived,
            c6_fireworks_derived,
        ),
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: YuzuhaCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "柚叶":
        raise ValueError("unexpected character name in raw Yuzuha record")
    if raw.code_name != "Yuzuha":
        raise ValueError("unexpected Yuzuha code name in raw record")
    if raw.specialty != "支援":
        raise ValueError("unexpected Yuzuha specialty in raw record")
    if raw.element != "物理":
        raise ValueError("unexpected Yuzuha element in raw record")
    if len(raw.core_levels) != 7:
        raise ValueError("raw Yuzuha record must contain all seven core levels")
    if len(raw.mindscapes) != 6:
        raise ValueError("raw Yuzuha record must contain all six mindscapes")


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(YUZUHA_ID))


__all__ = [
    "TANUKI_WISH_ATTACK_CAPS",
    "TANUKI_WISH_ACTIVE_CONDITION_ID",
    "YUZUHA_C6_SHELL_COUNT_PARAMETER_ID",
    "YUZUHA_ID",
    "compile_yuzuha",
    "load_raw_record",
]
