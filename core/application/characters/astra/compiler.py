"""Compile the supplied Astra record into the application contracts."""

from __future__ import annotations

from core.types import (
    AnyFilter,
    BattleEventKind,
    CreatedByEffectFilter,
    CharacterId,
    CharacterRoleFilter,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    DamageMultiplier,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DynamicIdentity,
    DynamicIdentityCondition,
    DynamicIdentityFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventCreationEffect,
    EventCreationResult,
    EventSelector,
    EventTemplateId,
    FixedMultiplier,
    ModifierEffect,
    MoveId,
    MoveIdFilter,
    ModifierResult,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SkillGroupFilter,
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
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..definition import CharacterCalculationDefinition
from ..templates import DirectDamageEventTemplate
from .config import AstraCompileConfig
from .reviewed import (
    ARIA_ACTIVE_CONDITION_KEY,
    ARIA_TEAM_BUFF_RULE_KEY,
    ASTRA_REVIEWED_MAPPING,
    CORE_ATTACK_BUFF_ACTIVE_CONDITION_KEY,
    ENERGY_AVAILABLE_CONDITION_KEY,
    RHAPSODY_STAGE3_FULL_CONDITION_KEY,
    RHAPSODY_STAGE3_MIN_CONDITION_KEY,
    AstraMoveSpec,
    AstraReviewedMapping,
    AstraTeamBuffSpec,
)
from .source import AstraRawMoveRecord, AstraRawRecord


ASTRA_ID = CharacterId("character:1311")
ARIA_ACTIVE_CONDITION_ID = ScenarioConditionId("condition:astra:aria-active")
CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID = ScenarioConditionId(
    "condition:astra:core-attack-buff-active"
)
ENERGY_AVAILABLE_CONDITION_ID = ScenarioConditionId(
    "condition:astra:energy-derived-active"
)
RHAPSODY_STAGE3_MIN_CONDITION_ID = ScenarioConditionId(
    "condition:astra:rhapsody-stage3-min"
)
RHAPSODY_STAGE3_FULL_CONDITION_ID = ScenarioConditionId(
    "condition:astra:rhapsody-stage3-full"
)
WIND_CHIME_COUNT_PARAMETER_ID = ScenarioParameterId(
    "parameter:astra:wind-chime-tremolo-count"
)

FINALE_MOVE_ID = MoveId("move:astra:finale")
RHAPSODY_MOVE_ID = MoveId("move:astra:rhapsody")
CINEMA6_RHAPSODY_EFFECT_ID = EffectId("effect:astra:1311:cinema6:rhapsody")


def _rule_source(
    source_id: str,
    source_type: EffectSourceType,
    label: str,
    text: str,
) -> RuleSource:
    return RuleSource(
        source_id=RuleSourceId(source_id),
        source_type=source_type,
        label=label,
        raw_text=text,
    )


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    original_text: str,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )


def _condition_ids(condition_key: str | None) -> tuple[ScenarioConditionId, ...]:
    if condition_key == ARIA_ACTIVE_CONDITION_KEY:
        return (ARIA_ACTIVE_CONDITION_ID,)
    if condition_key == CORE_ATTACK_BUFF_ACTIVE_CONDITION_KEY:
        return (CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID,)
    if condition_key == ENERGY_AVAILABLE_CONDITION_KEY:
        return (ENERGY_AVAILABLE_CONDITION_ID,)
    if condition_key == RHAPSODY_STAGE3_MIN_CONDITION_KEY:
        return (RHAPSODY_STAGE3_MIN_CONDITION_ID,)
    if condition_key == RHAPSODY_STAGE3_FULL_CONDITION_KEY:
        return (RHAPSODY_STAGE3_FULL_CONDITION_ID,)
    if condition_key is None:
        return ()
    raise ValueError(f"unsupported Astra condition key: {condition_key}")


def _move_condition_ids(spec: AstraMoveSpec) -> tuple[ScenarioConditionId, ...]:
    return (ARIA_ACTIVE_CONDITION_ID,) if spec.requires_aria else ()


def _raw_index(raw: AstraRawRecord) -> dict[str, AstraRawMoveRecord]:
    indexed: dict[str, AstraRawMoveRecord] = {}
    for move in raw.moves:
        if move.name in indexed:
            raise ValueError(f"raw Astra record contains duplicate move: {move.name}")
        indexed[move.name] = move
    return indexed


def _raw_multiplier(
    raw_moves: dict[str, AstraRawMoveRecord],
    move_name: str,
    parameter_name: str,
    level: int,
    subject: str,
    diagnostics: list[CalculationDiagnostic],
) -> float | Unresolved:
    raw_move = raw_moves.get(move_name)
    parameter = (
        next(
            (item for item in raw_move.parameters if item.name == parameter_name),
            None,
        )
        if raw_move is not None
        else None
    )
    value = (
        parameter.value_for_level(level)
        if parameter is not None and parameter.format == "%"
        else None
    )
    if value is None:
        message = (
            f"{subject}: missing {parameter_name} from {move_name} "
            f"at skill level {level}"
        )
        diagnostics.append(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(
                    f"data:astra:derived:{subject}:{parameter_name}"
                ),
                kind=DiagnosticKind.MISSING_DATA,
                message=message,
                blocking=True,
                original_text=parameter_name,
            )
        )
        return Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes=message,
            original_text=parameter_name,
        )
    return value / 100.0


def _resolved_ratio(value: float | Unresolved) -> Resolved | Unresolved:
    """Turn a raw percentage-table value into a calculator ratio."""

    return value if isinstance(value, Unresolved) else Resolved(value)


def _mindscape_value(
    raw_record: AstraRawRecord,
    level: int,
    key: str,
) -> float:
    mindscape = next(item for item in raw_record.mindscapes if item.level == level)
    value = mindscape.calculation_value(key)
    if value is None:
        raise ValueError(f"raw Astra mindscape {level} is missing {key}")
    return value


def _multiplier_variants(
    spec: AstraMoveSpec,
    raw_move: AstraRawMoveRecord | None,
    skill_level: int,
) -> tuple[tuple[MultiplierVariant, ...], tuple[CalculationDiagnostic, ...]]:
    diagnostics: list[CalculationDiagnostic] = []
    variants: list[MultiplierVariant] = []
    for parameter in spec.parameters:
        source_parameter = (
            next(
                (
                    item
                    for item in raw_move.parameters
                    if item.name == parameter.parameter_name
                ),
                None,
            )
            if raw_move is not None
            else None
        )
        value = (
            source_parameter.value_for_level(skill_level)
            if source_parameter is not None and source_parameter.format == "%"
            else None
        )
        if value is None:
            unresolved_notes = (
                f"{spec.display_name}: missing {parameter.parameter_name} "
                f"at skill level {skill_level}"
            )
            multiplier: DamageMultiplier = Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=unresolved_notes,
                original_text=parameter.parameter_name,
            )
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"data:astra:{spec.entry_key}:{parameter.variant_key}"
                    ),
                    kind=DiagnosticKind.MISSING_DATA,
                    message=unresolved_notes,
                    blocking=True,
                    original_text=parameter.parameter_name,
                )
            )
        else:
            multiplier = FixedMultiplier(Resolved(value / 100.0))
        variants.append(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    f"variant:astra:{spec.entry_key}:{parameter.variant_key}"
                ),
                label=(
                    source_parameter.name
                    if source_parameter is not None
                    else parameter.parameter_name
                ),
                parameter_name=parameter.parameter_name,
                multiplier=multiplier,
                condition_ids=_condition_ids(parameter.condition_key),
                repeat_count_parameter_id=(
                    WIND_CHIME_COUNT_PARAMETER_ID
                    if spec.repeat_parameter_key is not None
                    else None
                ),
            )
        )
    return tuple(variants), tuple(diagnostics)


def _template_ids(entry_key: str) -> tuple[EventTemplateId, DamageEventSemanticId]:
    return (
        EventTemplateId(f"template:astra:1311:{entry_key}:main"),
        DamageEventSemanticId(f"event:astra:1311:{entry_key}:main"),
    )


def _build_move(
    spec: AstraMoveSpec,
    config: AstraCompileConfig,
    raw_moves: dict[str, AstraRawMoveRecord],
) -> tuple[
    MoveCalculationEntry, DirectDamageEventTemplate, tuple[CalculationDiagnostic, ...]
]:
    skill_level = config.skill_level_for(spec.skill_group) or 12
    raw_move = raw_moves.get(spec.source_name)
    variants, diagnostics = _multiplier_variants(spec, raw_move, skill_level)
    template_id, semantic_id = _template_ids(spec.entry_key)
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label=spec.display_name,
        damage_type=DamageType.DIRECT,
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        element=Element.ETHER,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=config.character_id,
        element=Element.ETHER,
        base_source=CurrentAttackValueSource(config.character_id),
        crit_rule=StandardCritRule(config.character_id),
        move_id=spec.move_id,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:astra:1311:{spec.entry_key}"),
        character_id=config.character_id,
        move_id=spec.move_id,
        display_name=spec.display_name,
        original_text=(
            raw_move.description if raw_move is not None else spec.source_name
        ),
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        multiplier_relation=spec.multiplier_relation,
        multiplier_variants=variants,
        main_damage_event=ref,
        condition_ids=_move_condition_ids(spec),
        stage_index=spec.stage_index,
        diagnostics=diagnostics,
    )
    return entry, typed, diagnostics


def _effect_rule(
    effect_id: str,
    source: RuleSource,
    *,
    owner: CharacterId | None,
    target: EffectTarget,
    trigger: EventSelector | None = None,
    condition=None,
    filters=(),
) -> EffectRule:
    return EffectRule(
        effect_id=EffectId(effect_id),
        source=source,
        owner=owner,
        target=target,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        trigger=trigger,
        condition=condition,
        filters=filters,
    )


def _modifier(
    effect_id: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    owner: CharacterId | None = ASTRA_ID,
    target: EffectTarget = EffectTarget.SELF,
    operation: EffectOperation = EffectOperation.ADD,
    trigger: EventSelector | None = None,
    condition=None,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id,
            source,
            owner=owner,
            target=target,
            trigger=trigger,
            condition=condition,
            filters=filters,
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def _event_creation(
    effect_id: str,
    source: RuleSource,
    template_id: EventTemplateId,
    *,
    owner: CharacterId | None = ASTRA_ID,
    target: EffectTarget = EffectTarget.TEAM,
    trigger: EventSelector | None = None,
    filters=(),
) -> EventCreationEffect:
    return EventCreationEffect(
        rule=_effect_rule(
            effect_id,
            source,
            owner=owner,
            target=target,
            trigger=trigger,
            filters=filters,
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_id,
        ),
    )


def _independent_event(
    event_key: str,
    label: str,
    source_rule_id: RuleItemId,
    multiplier: float | Unresolved,
    *,
    repeat_count: int = 1,
    skill_group: SkillGroup | None,
    damage_tags: frozenset[DamageTag],
    move_id: MoveId | None = None,
) -> tuple[DerivedDamageEventTemplateRef, DirectDamageEventTemplate]:
    template_id = EventTemplateId(f"template:astra:1311:{event_key}")
    semantic_id = DamageEventSemanticId(f"event:astra:1311:{event_key}")
    ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=semantic_id,
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=Element.ETHER,
        source_rule_item_id=source_rule_id,
    )
    derived = DerivedDamageEventTemplateRef(
        template=ref,
        multiplier=(
            multiplier
            if isinstance(multiplier, Unresolved)
            else FixedMultiplier(Resolved(multiplier))
        ),
        repeat_count=repeat_count,
    )
    typed = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=ASTRA_ID,
        element=Element.ETHER,
        base_source=CurrentAttackValueSource(ASTRA_ID),
        crit_rule=StandardCritRule(ASTRA_ID),
        move_id=move_id,
    )
    return derived, typed


def compile_astra(
    config: AstraCompileConfig,
    raw_record: AstraRawRecord,
    reviewed_mapping: AstraReviewedMapping = ASTRA_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    raw_moves = _raw_index(raw_record)
    level = raw_record.core_levels[config.core_level - 1]

    conditions = (
        _condition(
            ARIA_ACTIVE_CONDITION_ID,
            "当前处于咏叹华彩",
            "咏叹华彩状态",
        ),
        _condition(
            CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID,
            "当前场景中如歌的行板攻击力增益已生效",
            "核心被动攻击力增益当前生效",
        ),
        _condition(
            ENERGY_AVAILABLE_CONDITION_ID,
            "本次场景能量足够触发追加伤害",
            "能量足够",
        ),
        _condition(
            RHAPSODY_STAGE3_MIN_CONDITION_ID,
            "随想曲第三段：最小蓄力",
            "三段最小伤害倍率",
        ),
        _condition(
            RHAPSODY_STAGE3_FULL_CONDITION_ID,
            "随想曲第三段：蓄力完成",
            "三段最大伤害倍率",
        ),
    )
    parameters = (
        ScenarioIntegerParameter(
            parameter_id=WIND_CHIME_COUNT_PARAMETER_ID,
            label="风铃震音数量",
            original_text="根据蓄力时长追加释放1~4道震音",
            resolution=ParameterResolution.USER_SELECTED,
            value=None,
            minimum=1,
            maximum=5,
        ),
    )

    entries: list[MoveCalculationEntry] = []
    templates: list[DirectDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for spec in reviewed_mapping.moves:
        entry, typed, entry_diagnostics = _build_move(spec, config, raw_moves)
        entries.append(entry)
        templates.append(typed)
        diagnostics.extend(entry_diagnostics)

    core_source = _rule_source(
        "source:astra:1311:core-passive",
        EffectSourceType.CORE_PASSIVE,
        level.name,
        level.description,
    )
    basic_skill_level = config.skill_level_for(SkillGroup.BASIC_ATTACK) or 12
    special_skill_level = config.skill_level_for(SkillGroup.SPECIAL_ATTACK) or 12
    chord_tremolo_multiplier = _raw_multiplier(
        raw_moves,
        "和弦",
        "追加震音伤害倍率",
        special_skill_level,
        "和弦震音",
        diagnostics,
    )
    chord_cluster_multiplier = _raw_multiplier(
        raw_moves,
        "和弦",
        "追加音簇伤害倍率",
        special_skill_level,
        "和弦音簇",
        diagnostics,
    )
    cinema4_damage_multiplier = (
        _mindscape_value(
            raw_record,
            4,
            "attack_extra_damage_percent",
        )
        / 100.0
    )
    cinema6_multiplier_factor = _mindscape_value(
        raw_record,
        6,
        "damage_multiplier_factor",
    )
    cinema6_crit_rate_bonus = (
        _mindscape_value(
            raw_record,
            6,
            "crit_rate_bonus",
        )
        / 100.0
    )
    cinema1_resistance_reduction = (
        _mindscape_value(
            raw_record,
            1,
            "resistance_reduction",
        )
        / 100.0
    )
    cinema1_max_stacks = int(_mindscape_value(raw_record, 1, "max_stacks"))
    cinema2_coefficient_add = (
        _mindscape_value(
            raw_record,
            2,
            "core_coefficient_add",
        )
        / 100.0
    )
    cinema2_attack_cap_add = _mindscape_value(
        raw_record,
        2,
        "attack_cap_add",
    )
    cinema6_rhapsody_multiplier = _raw_multiplier(
        raw_moves,
        "普通攻击：《随想曲》",
        "三段最大伤害倍率",
        basic_skill_level,
        "6影随想曲第三段",
        diagnostics,
    )
    coefficient = level.attack_bonus_percent / 100.0
    cap = level.attack_bonus_cap
    if config.cinema_level >= 2:
        coefficient += cinema2_coefficient_add
        cap += cinema2_attack_cap_add
    core_value = PanelStatDerivedValue(
        source_character_id=ASTRA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
        coefficient=Resolved(coefficient),
        cap_max=Resolved(cap),
    )
    core_team_rule = CalculationRuleItem(
        rule_id=RuleItemId("rule:astra:1311:core-passive-self"),
        owner=ASTRA_ID,
        source=core_source,
        display_name="核心被动：《如歌的行板》（全队攻击力）",
        original_text=level.description,
        eligibility=RuleEligibility.ELIGIBLE,
        condition_ids=(CORE_ATTACK_BUFF_ACTIVE_CONDITION_ID,),
        effects=(
            _modifier(
                "effect:astra:1311:core-self-attack",
                core_source,
                CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                core_value,
                target=EffectTarget.TEAM,
            ),
        ),
    )
    rule_items: list[CalculationRuleItem] = [core_team_rule]

    aria_team_spec = _team_buff_spec(reviewed_mapping, ARIA_TEAM_BUFF_RULE_KEY)
    aria_source_move = raw_moves.get(aria_team_spec.source_name)
    if aria_source_move is None:
        raise ValueError(
            f"raw Astra record is missing reviewed team buff source: "
            f"{aria_team_spec.source_name}"
        )
    aria_damage_bonus = _raw_multiplier(
        raw_moves,
        aria_team_spec.source_name,
        aria_team_spec.damage_parameter_name,
        special_skill_level,
        "咏叹华彩全队伤害",
        diagnostics,
    )
    aria_crit_damage_bonus = _raw_multiplier(
        raw_moves,
        aria_team_spec.source_name,
        aria_team_spec.crit_damage_parameter_name,
        special_skill_level,
        "咏叹华彩全队暴击伤害",
        diagnostics,
    )
    aria_source = _rule_source(
        "source:astra:1311:aria-team-buff",
        EffectSourceType.SKILL,
        aria_source_move.name,
        aria_source_move.description,
    )
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:astra:1311:aria-team-buff"),
            owner=ASTRA_ID,
            source=aria_source,
            display_name=aria_team_spec.display_name,
            original_text=aria_source_move.description,
            eligibility=RuleEligibility.ELIGIBLE,
            condition_ids=(ARIA_ACTIVE_CONDITION_ID,),
            effects=(
                _modifier(
                    "effect:astra:1311:aria-team-damage",
                    aria_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    _resolved_ratio(aria_damage_bonus),
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "effect:astra:1311:aria-team-crit-damage",
                    aria_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    _resolved_ratio(aria_crit_damage_bonus),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    c1_source = _mindscape_source(raw_record, 1)
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:astra:1311:cinema1"),
            owner=ASTRA_ID,
            source=c1_source,
            display_name="1影：十二平均律",
            original_text=c1_source.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 1
                else RuleEligibility.INELIGIBLE
            ),
            stack_count=cinema1_max_stacks,
            stack_min=0,
            stack_max=cinema1_max_stacks,
            effects=(
                _modifier(
                    "effect:astra:1311:cinema1:resistance",
                    c1_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(cinema1_resistance_reduction),
                    target=EffectTarget.ENEMY,
                ),
            ),
        )
    )

    derived_specs: dict[
        str,
        tuple[
            RuleItemId,
            str,
            float | Unresolved,
            int,
            SkillGroup | None,
            frozenset[DamageTag],
        ],
    ] = {
        "finale-tremolo": (
            RuleItemId("rule:astra:1311:finale-derived"),
            "终曲追加震音",
            chord_tremolo_multiplier,
            1,
            SkillGroup.SPECIAL_ATTACK,
            frozenset(
                {
                    DamageTag.SPECIAL_ATTACK,
                    DamageTag.EX_SPECIAL_ATTACK,
                    DamageTag.TREMOLO,
                }
            ),
        ),
        "finale-cluster": (
            RuleItemId("rule:astra:1311:finale-derived"),
            "终曲追加音簇",
            chord_cluster_multiplier,
            3,
            None,
            frozenset({DamageTag.CLUSTER}),
        ),
        "extra-finale-tremolo": (
            RuleItemId("rule:astra:1311:extra-ability"),
            "额外能力追加震音",
            chord_tremolo_multiplier,
            1,
            SkillGroup.SPECIAL_ATTACK,
            frozenset(
                {
                    DamageTag.SPECIAL_ATTACK,
                    DamageTag.EX_SPECIAL_ATTACK,
                    DamageTag.TREMOLO,
                }
            ),
        ),
        "extra-finale-cluster": (
            RuleItemId("rule:astra:1311:extra-ability"),
            "额外能力追加音簇",
            chord_cluster_multiplier,
            3,
            None,
            frozenset({DamageTag.CLUSTER}),
        ),
        "entry-tremolo": (
            RuleItemId("rule:astra:1311:extra-ability-entry"),
            "入场追加震音",
            chord_tremolo_multiplier,
            1,
            SkillGroup.SPECIAL_ATTACK,
            frozenset(
                {
                    DamageTag.SPECIAL_ATTACK,
                    DamageTag.EX_SPECIAL_ATTACK,
                    DamageTag.TREMOLO,
                }
            ),
        ),
        "entry-cluster": (
            RuleItemId("rule:astra:1311:extra-ability-entry"),
            "入场追加音簇",
            chord_cluster_multiplier,
            3,
            None,
            frozenset({DamageTag.CLUSTER}),
        ),
        "cinema2-entry-tremolo": (
            RuleItemId("rule:astra:1311:cinema2"),
            "2影追加震音",
            chord_tremolo_multiplier,
            1,
            SkillGroup.SPECIAL_ATTACK,
            frozenset(
                {
                    DamageTag.SPECIAL_ATTACK,
                    DamageTag.EX_SPECIAL_ATTACK,
                    DamageTag.TREMOLO,
                }
            ),
        ),
        "cinema2-entry-cluster": (
            RuleItemId("rule:astra:1311:cinema2"),
            "2影追加音簇",
            chord_cluster_multiplier,
            3,
            None,
            frozenset({DamageTag.CLUSTER}),
        ),
        "cinema4-attack-extra": (
            RuleItemId("rule:astra:1311:cinema4"),
            "4影强攻支援额外伤害",
            cinema4_damage_multiplier,
            1,
            None,
            frozenset(),
        ),
        "cinema6-rhapsody": (
            RuleItemId("rule:astra:1311:cinema6"),
            "6影蓄力完成随想曲第三段",
            cinema6_rhapsody_multiplier,
            1,
            SkillGroup.BASIC_ATTACK,
            frozenset({DamageTag.BASIC_ATTACK}),
        ),
    }
    derived_refs: dict[str, DerivedDamageEventTemplateRef] = {}
    for event_key, (
        _,
        label,
        multiplier,
        repeat_count,
        skill_group,
        tags,
    ) in derived_specs.items():
        derived, typed = _independent_event(
            event_key,
            label,
            derived_specs[event_key][0],
            multiplier,
            repeat_count=repeat_count,
            skill_group=skill_group,
            damage_tags=tags,
            move_id=RHAPSODY_MOVE_ID if event_key == "cinema6-rhapsody" else None,
        )
        derived_refs[event_key] = derived
        templates.append(typed)

    entry_filter = AnyFilter(
        (
            SkillGroupFilter(SkillGroup.ASSIST),
            SkillGroupFilter(SkillGroup.CHAIN_ATTACK),
            DamageTagFilter(DamageTag.DODGE_COUNTER),
            DamageTagFilter(DamageTag.DASH_ATTACK),
        )
    )
    finale_filter = (MoveIdFilter(FINALE_MOVE_ID),)
    energy_conditions = (ARIA_ACTIVE_CONDITION_ID, ENERGY_AVAILABLE_CONDITION_ID)

    # The authored Finale tremolo and cluster have their own damage ratios,
    # but no separate MoveId. Expose each typed damage component directly while
    # retaining its reviewed Tremolo/Cluster classification and repeat count.
    for event_key, entry_key, label in (
        ("finale-tremolo", "finale-tremolo", "终曲追加震音"),
        ("finale-cluster", "finale-cluster", "终曲追加音簇"),
    ):
        child = derived_refs[event_key]
        ref = child.template
        relation = (
            MultiplierRelation.UNIT_REPEAT
            if child.repeat_count != 1
            or child.repeat_count_parameter_id is not None
            else MultiplierRelation.COMPLETE
        )
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(
                    f"move-entry:astra:1311:selectable-{entry_key}"
                ),
                character_id=ASTRA_ID,
                move_id=None,
                display_name=f"核心被动：{label}",
                original_text=ref.label,
                skill_group=ref.skill_group,
                damage_tags=ref.damage_tags,
                multiplier_relation=relation,
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId(
                            f"variant:astra:1311:selectable-{entry_key}"
                        ),
                        label=ref.label,
                        parameter_name=f"{ref.label}倍率",
                        multiplier=child.multiplier,
                        repeat_count=(
                            child.repeat_count
                            if relation is MultiplierRelation.UNIT_REPEAT
                            else None
                        ),
                        repeat_count_parameter_id=child.repeat_count_parameter_id,
                    ),
                ),
                main_damage_event=ref,
                condition_ids=energy_conditions,
            )
        )

    finale_source = _rule_source(
        "source:astra:1311:finale-derived",
        EffectSourceType.SKILL,
        (
            raw_moves["普通攻击：终曲"].name
            if "普通攻击：终曲" in raw_moves
            else "普通攻击：终曲"
        ),
        (
            raw_moves["普通攻击：终曲"].description
            if "普通攻击：终曲" in raw_moves
            else ""
        ),
    )
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:astra:1311:finale-derived"),
            owner=ASTRA_ID,
            source=finale_source,
            display_name="终曲追加震音与音簇",
            original_text=finale_source.raw_text or "",
            eligibility=RuleEligibility.ELIGIBLE,
            condition_ids=energy_conditions,
            effects=(
                _event_creation(
                    "effect:astra:1311:finale-tremolo",
                    finale_source,
                    derived_refs["finale-tremolo"].template.template_id,
                    target=EffectTarget.TEAM,
                    filters=finale_filter,
                ),
                _event_creation(
                    "effect:astra:1311:finale-cluster",
                    finale_source,
                    derived_refs["finale-cluster"].template.template_id,
                    target=EffectTarget.TEAM,
                    filters=finale_filter,
                ),
            ),
        )
    )

    extra_source = _rule_source(
        "source:astra:1311:extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    rule_items.extend(
        (
            CalculationRuleItem(
                rule_id=RuleItemId("rule:astra:1311:extra-ability"),
                owner=ASTRA_ID,
                source=extra_source,
                display_name=raw_record.extra_ability_name,
                original_text=raw_record.extra_ability_description,
                eligibility=extra_eligibility,
                condition_ids=energy_conditions,
                effects=(
                    _event_creation(
                        "effect:astra:1311:extra-finale-tremolo",
                        extra_source,
                        derived_refs["extra-finale-tremolo"].template.template_id,
                        filters=finale_filter,
                    ),
                    _event_creation(
                        "effect:astra:1311:extra-finale-cluster",
                        extra_source,
                        derived_refs["extra-finale-cluster"].template.template_id,
                        filters=finale_filter,
                    ),
                ),
            ),
            CalculationRuleItem(
                rule_id=RuleItemId("rule:astra:1311:extra-ability-entry"),
                owner=ASTRA_ID,
                source=extra_source,
                display_name=f"{raw_record.extra_ability_name}：入场追加",
                original_text=raw_record.extra_ability_description,
                eligibility=extra_eligibility,
                condition_ids=energy_conditions,
                effects=(
                    _event_creation(
                        "effect:astra:1311:extra-entry-tremolo",
                        extra_source,
                        derived_refs["entry-tremolo"].template.template_id,
                        trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
                        filters=(entry_filter,),
                    ),
                    _event_creation(
                        "effect:astra:1311:extra-entry-cluster",
                        extra_source,
                        derived_refs["entry-cluster"].template.template_id,
                        trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
                        filters=(entry_filter,),
                    ),
                ),
            ),
        )
    )

    c2_source = _mindscape_source(raw_record, 2)
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:astra:1311:cinema2"),
            owner=ASTRA_ID,
            source=c2_source,
            display_name="2影：贪心艺术",
            original_text=c2_source.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 2
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(ARIA_ACTIVE_CONDITION_ID,),
            effects=(
                _event_creation(
                    "effect:astra:1311:cinema2-entry-tremolo",
                    c2_source,
                    derived_refs["cinema2-entry-tremolo"].template.template_id,
                    trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
                    filters=(entry_filter,),
                ),
                _event_creation(
                    "effect:astra:1311:cinema2-entry-cluster",
                    c2_source,
                    derived_refs["cinema2-entry-cluster"].template.template_id,
                    trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
                    filters=(entry_filter,),
                ),
            ),
        )
    )

    c4_source = _mindscape_source(raw_record, 4)
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:astra:1311:cinema4"),
            owner=ASTRA_ID,
            source=c4_source,
            display_name="4影：《后颈的碎发》",
            original_text=c4_source.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 4
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(ARIA_ACTIVE_CONDITION_ID,),
            effects=(
                _event_creation(
                    "effect:astra:1311:cinema4-attack-extra",
                    c4_source,
                    derived_refs["cinema4-attack-extra"].template.template_id,
                    trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
                    filters=(
                        SkillGroupFilter(SkillGroup.ASSIST),
                        CharacterRoleFilter(CharacterRole.ATTACK),
                    ),
                ),
            ),
        )
    )

    c6_source = _mindscape_source(raw_record, 6)
    tremolo_cluster_filter = (
        AnyFilter(
            (
                DamageTagFilter(DamageTag.TREMOLO),
                DamageTagFilter(DamageTag.CLUSTER),
            )
        ),
    )
    cinema6_rhapsody_filter = (
        MoveIdFilter(RHAPSODY_MOVE_ID),
        CreatedByEffectFilter(CINEMA6_RHAPSODY_EFFECT_ID),
    )
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:astra:1311:cinema6"),
            owner=ASTRA_ID,
            source=c6_source,
            display_name="6影：我们即是世界",
            original_text=c6_source.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 6
                else RuleEligibility.INELIGIBLE
            ),
            condition_ids=(ARIA_ACTIVE_CONDITION_ID,),
            effects=(
                _modifier(
                    "effect:astra:1311:cinema6:multiplier",
                    c6_source,
                    CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                    Resolved(cinema6_multiplier_factor),
                    target=EffectTarget.TEAM,
                    operation=EffectOperation.MULTIPLY,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=tremolo_cluster_filter,
                ),
                _modifier(
                    "effect:astra:1311:cinema6:crit-rate",
                    c6_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(cinema6_crit_rate_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=tremolo_cluster_filter,
                ),
                _modifier(
                    "effect:astra:1311:cinema6:rhapsody-crit-rate",
                    c6_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(cinema6_crit_rate_bonus),
                    target=EffectTarget.TEAM,
                    condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                    filters=cinema6_rhapsody_filter,
                ),
                _event_creation(
                    str(CINEMA6_RHAPSODY_EFFECT_ID),
                    c6_source,
                    derived_refs["cinema6-rhapsody"].template.template_id,
                    trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
                    filters=(entry_filter,),
                ),
            ),
        )
    )

    return CharacterCalculationDefinition(
        character_id=raw_record.character_id,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=core_source,
        move_entries=tuple(entries),
        rule_items=tuple(rule_items),
        scenario_conditions=conditions,
        scenario_parameters=parameters,
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=tuple(derived_refs.values()),
        diagnostics=tuple(diagnostics),
    )


def _mindscape_source(raw_record: AstraRawRecord, level: int) -> RuleSource:
    mindscape = next(item for item in raw_record.mindscapes if item.level == level)
    return _rule_source(
        f"source:astra:1311:cinema-{level}",
        EffectSourceType.CINEMA,
        f"{level}影：{mindscape.name}",
        mindscape.description,
    )


def _team_buff_spec(
    reviewed_mapping: AstraReviewedMapping,
    rule_key: str,
) -> AstraTeamBuffSpec:
    specs = tuple(
        item for item in reviewed_mapping.team_buffs if item.rule_key == rule_key
    )
    if len(specs) != 1:
        raise ValueError(
            f"reviewed Astra mapping must contain exactly one team buff spec: {rule_key}"
        )
    return specs[0]


def _validate_raw_record(
    raw_record: AstraRawRecord,
    config: AstraCompileConfig,
) -> None:
    if raw_record.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw_record.name != "耀嘉音":
        raise ValueError("unexpected character name in raw Astra record")
    if raw_record.code_name != "Astra":
        raise ValueError("unexpected Astra code name in raw record")
    if raw_record.specialty != "支援":
        raise ValueError("unexpected Astra specialty in raw record")
    if raw_record.element != "以太":
        raise ValueError("unexpected Astra element in raw record")
    if len(raw_record.core_levels) != 7:
        raise ValueError("raw Astra record must contain all seven core levels")
    if len(raw_record.mindscapes) != 4:
        raise ValueError("raw Astra record must contain 1/2/4/6 mindscapes")


__all__ = [
    "ASTRA_ID",
    "ARIA_ACTIVE_CONDITION_ID",
    "CINEMA6_RHAPSODY_EFFECT_ID",
    "RHAPSODY_MOVE_ID",
    "ENERGY_AVAILABLE_CONDITION_ID",
    "RHAPSODY_STAGE3_FULL_CONDITION_ID",
    "RHAPSODY_STAGE3_MIN_CONDITION_ID",
    "WIND_CHIME_COUNT_PARAMETER_ID",
    "compile_astra",
]
