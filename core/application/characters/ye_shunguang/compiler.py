"""Compile the supplied Ye Shunguang record into application contracts."""

from __future__ import annotations

from core.types import (
    CharacterFilter,
    CharacterId,
    CharacterRole,
    CalculationNode,
    CurrentAttackValueSource,
    DamageMultiplier,
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
    MoveIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    MoveId,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
    BattleEventKind,
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
    DamageEventTemplateRef as ApplicationDamageEventTemplateRef,
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
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
from .reviewed import (
    HAS_QINGMING_CONDITION_KEY,
    YE_SHUNGUANG_REVIEWED_SOURCE,
    YeElementMode,
    YeMoveSpec,
    YeShunguangReviewedSource,
    WITHOUT_QINGMING_CONDITION_KEY,
    PERFECT_DODGE_CONDITION_KEY,
    YIN_NORMAL_CONDITION_KEY,
)
from .config import YeShunguangCompileConfig
from .source import YeShunguangRawRecord


YE_ID = CharacterId("character:1431")
MINGXIN_CONDITION_ID = ScenarioConditionId("condition:ye:mingxin-active")
ENTRY_LINREN_CONDITION_ID = ScenarioConditionId(
    "condition:ye:entry-move-uses-linren"
)
MIE_WITH_QINGMING_CONDITION_ID = ScenarioConditionId(
    "condition:ye:variant:mingxin-zhanliuguang-mie:with-qingming"
)
MIE_WITHOUT_QINGMING_CONDITION_ID = ScenarioConditionId(
    "condition:ye:variant:mingxin-zhanliuguang-mie:without-qingming"
)
YIN_NORMAL_CONDITION_ID = ScenarioConditionId(
    "condition:ye:variant:yin-canglan:normal"
)
YIN_PERFECT_DODGE_CONDITION_ID = ScenarioConditionId(
    "condition:ye:variant:yin-canglan:perfect-dodge"
)
FLOWING_CLOUD_COUNT_PARAMETER_ID = ScenarioParameterId(
    "parameter:ye:flowing-cloud-sword-count"
)


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


def _effect_rule(
    effect_id: str,
    source: RuleSource,
    *,
    owner: CharacterId | None,
    target: EffectTarget,
    filters=(),
    condition=None,
) -> EffectRule:
    return EffectRule(
        effect_id=EffectId(effect_id),
        source=source,
        owner=owner,
        target=target,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        condition=condition,
        filters=filters,
    )


def _modifier(
    effect_id: str,
    source: RuleSource,
    path: CalculationNode,
    value: float,
    *,
    owner: CharacterId | None = YE_ID,
    target: EffectTarget = EffectTarget.SELF,
    operation: EffectOperation = EffectOperation.ADD,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id,
            source,
            owner=owner,
            target=target,
            filters=filters,
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=Resolved(value),
        ),
    )


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    original_text: str,
    value: bool | None,
    *,
    static: bool,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=(
            ConditionResolution.STATIC
            if static
            else ConditionResolution.USER_SELECTED
        ),
        value=value,
    )


def _parameter_value_for_level(
    spec: YeMoveSpec,
    level: int,
) -> tuple[tuple[MultiplierVariant, ...], tuple[CalculationDiagnostic, ...]]:
    variants: list[MultiplierVariant] = []
    diagnostics: list[CalculationDiagnostic] = []
    for parameter in spec.parameters:
        value = parameter.value_for_level(level)
        if value is None:
            multiplier: DamageMultiplier = Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=(
                    f"{spec.display_name} has no supplied value for skill level {level}"
                ),
                original_text=parameter.parameter_name,
            )
            diagnostics.append(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        f"data:{spec.entry_key}:skill-level-{level}"
                    ),
                    kind=DiagnosticKind.MISSING_DATA,
                    message=(
                        f"missing {parameter.parameter_name} at skill level {level}"
                    ),
                    blocking=True,
                    original_text=parameter.parameter_name,
                )
            )
        else:
            multiplier = FixedMultiplier(Resolved(value / 100.0))
        condition_ids = _parameter_conditions(
            spec.entry_key,
            parameter.condition_key,
        )
        variants.append(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    f"variant:ye:1431:{spec.entry_key}:{parameter.variant_key}"
                ),
                label=parameter.label,
                parameter_name=parameter.parameter_name,
                multiplier=multiplier,
                condition_ids=condition_ids,
                repeat_count_parameter_id=(
                    FLOWING_CLOUD_COUNT_PARAMETER_ID
                    if spec.repeat_parameter_key is not None
                    else None
                ),
            )
        )
    return tuple(variants), tuple(diagnostics)


def _parameter_conditions(
    entry_key: str,
    condition_key: str | None,
) -> tuple[ScenarioConditionId, ...]:
    if condition_key is None:
        return ()
    condition_ids = {
        ("basic-mingxin-zhanliuguang-mie", HAS_QINGMING_CONDITION_KEY): (
            MIE_WITH_QINGMING_CONDITION_ID,
        ),
        ("basic-mingxin-zhanliuguang-mie", WITHOUT_QINGMING_CONDITION_KEY): (
            MIE_WITHOUT_QINGMING_CONDITION_ID,
        ),
        ("special-yin-canglan", YIN_NORMAL_CONDITION_KEY): (
            YIN_NORMAL_CONDITION_ID,
        ),
        ("special-yin-canglan", PERFECT_DODGE_CONDITION_KEY): (
            YIN_PERFECT_DODGE_CONDITION_ID,
        ),
    }
    try:
        return condition_ids[(entry_key, condition_key)]
    except KeyError as error:
        raise ValueError(
            f"unsupported Ye Shunguang condition key: {condition_key}"
        ) from error


def _move_element(spec: YeMoveSpec, config: YeShunguangCompileConfig) -> Element:
    if spec.requires_mingxin:
        return Element.LINREN
    if spec.element_mode is YeElementMode.LINREN:
        return Element.LINREN
    if spec.element_mode is YeElementMode.ENTRY:
        return Element.LINREN if config.entry_move_uses_linren else Element.PHYSICAL
    return Element.PHYSICAL


def _move_conditions(spec: YeMoveSpec) -> tuple[ScenarioConditionId, ...]:
    return (MINGXIN_CONDITION_ID,) if spec.requires_mingxin else ()


def _template_ids(entry_key: str) -> tuple[str, str]:
    return (
        f"template:ye:1431:{entry_key}:main",
        f"damage:ye:1431:{entry_key}:main",
    )


def _build_move(
    spec: YeMoveSpec,
    config: YeShunguangCompileConfig,
    source: YeShunguangReviewedSource,
) -> tuple[MoveCalculationEntry, DirectDamageEventTemplate, tuple[CalculationDiagnostic, ...]]:
    level = config.skill_level_for(spec.skill_group) or 12
    variants, diagnostics = _parameter_value_for_level(spec, level)
    element = _move_element(spec, config)
    template_id, semantic_id = _template_ids(spec.entry_key)
    ref = ApplicationDamageEventTemplateRef(
        template_id=EventTemplateId(template_id),
        semantic_id=DamageEventSemanticId(semantic_id),
        label=spec.display_name,
        damage_type=DamageType.DIRECT,
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        element=element,
    )
    typed_template = DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=source.character_id,
        element=element,
        base_source=CurrentAttackValueSource(source.character_id),
        crit_rule=StandardCritRule(source.character_id),
        move_id=spec.move_id,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:ye:1431:{spec.entry_key}"),
        character_id=source.character_id,
        move_id=spec.move_id,
        display_name=spec.display_name,
        original_text=spec.original_text,
        skill_group=spec.skill_group,
        damage_tags=spec.damage_tags,
        multiplier_relation=spec.multiplier_relation,
        multiplier_variants=variants,
        main_damage_event=ref,
        stage_index=spec.stage_index,
        condition_ids=_move_conditions(spec),
        diagnostics=diagnostics,
    )
    return entry, typed_template, diagnostics


def _cinema_rule_items(
    config: YeShunguangCompileConfig,
    source: YeShunguangReviewedSource,
    guichen_template_id,
    zhanwang_template_id,
) -> tuple[CalculationRuleItem, ...]:
    rule_items: list[CalculationRuleItem] = []
    cinema_sources = {
        level: _rule_source(
            f"source:ye:1431:cinema-{level}",
            EffectSourceType.CINEMA,
            f"{level}影",
            text,
        )
        for level, text in source.cinema_texts
    }

    source_c1 = cinema_sources[1]
    c1_effects = (
        _modifier(
            "effect:ye:1431:cinema1:damage",
            source_c1,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            0.10,
        ),
        _modifier(
            "effect:ye:1431:cinema1:defense-ignore",
            source_c1,
            CalculationNode.DAMAGE_DEFENSE_IGNORE,
            0.20,
        ),
    )
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:ye:1431:cinema1"),
            owner=source.character_id,
            source=source_c1,
            display_name="1影：梦中身",
            original_text=source_c1.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 1
                else RuleEligibility.INELIGIBLE
            ),
            effects=c1_effects,
        )
    )

    source_c2 = cinema_sources[2]
    c2_effects = (
        _modifier(
            "effect:ye:1431:cinema2:feiguang-defense-ignore",
            source_c2,
            CalculationNode.DAMAGE_DEFENSE_IGNORE,
            0.40,
            filters=(MoveIdFilter(MoveId("move:special-mingxin-feiguang")),),
        ),
        _modifier(
            "effect:ye:1431:cinema2:zhanwang-defense-ignore",
            source_c2,
            CalculationNode.DAMAGE_DEFENSE_IGNORE,
            0.40,
            filters=(MoveIdFilter(MoveId("move:ultimate-zhanwangkaitian")),),
        ),
    )
    rule_items.append(
        CalculationRuleItem(
            rule_id=RuleItemId("rule:ye:1431:cinema2"),
            owner=source.character_id,
            source=source_c2,
            display_name="2影：光与影",
            original_text=source_c2.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 2
                else RuleEligibility.INELIGIBLE
            ),
            effects=c2_effects,
        )
    )

    source_c6 = cinema_sources[6]
    c6_rule_id = RuleItemId("rule:ye:1431:cinema6")
    c6_effects = (
        EventCreationEffect(
            rule=_effect_rule(
                "effect:ye:1431:cinema6:guichen-extra",
                source_c6,
                owner=source.character_id,
                target=EffectTarget.SELF,
                filters=(MoveIdFilter(MoveId("move:special-mingxin-guichen")),),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=guichen_template_id,
            ),
        ),
        EventCreationEffect(
            rule=_effect_rule(
                "effect:ye:1431:cinema6:zhanwang-extra",
                source_c6,
                owner=source.character_id,
                target=EffectTarget.SELF,
                filters=(MoveIdFilter(MoveId("move:ultimate-zhanwangkaitian")),),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=zhanwang_template_id,
            ),
        ),
    )
    rule_items.append(
        CalculationRuleItem(
            rule_id=c6_rule_id,
            owner=source.character_id,
            source=source_c6,
            display_name="6影：明灯愿",
            original_text=source_c6.raw_text or "",
            eligibility=(
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 6
                else RuleEligibility.INELIGIBLE
            ),
            effects=c6_effects,
        )
    )
    return tuple(rule_items)


def compile_ye_shunguang(
    config: YeShunguangCompileConfig,
    source: YeShunguangReviewedSource = YE_SHUNGUANG_REVIEWED_SOURCE,
    raw_record: YeShunguangRawRecord | None = None,
) -> CharacterCalculationDefinition:
    if source.character_id != config.character_id:
        raise ValueError("Ye source and compile config character IDs must match")
    if raw_record is not None:
        _validate_raw_record(raw_record, source)

    static_conditions = (
        _condition(
            MINGXIN_CONDITION_ID,
            "当前处于明心境",
            "明心境状态",
            config.mingxin_active,
            static=True,
        ),
        _condition(
            ENTRY_LINREN_CONDITION_ID,
            "入场招式伤害结算为凛刃",
            "入场招式与明心境创建的结算先后",
            config.entry_move_uses_linren,
            static=True,
        ),
    )
    user_conditions = (
        _condition(
            MIE_WITH_QINGMING_CONDITION_ID,
            "明心境·斩流光灭：拥有青溟剑势",
            "有青溟剑势时的招式版本",
            None,
            static=False,
        ),
        _condition(
            MIE_WITHOUT_QINGMING_CONDITION_ID,
            "明心境·斩流光灭：未拥有青溟剑势",
            "无青溟剑势时的招式版本",
            None,
            static=False,
        ),
        _condition(
            YIN_NORMAL_CONDITION_ID,
            "引沧澜：未触发极限闪避",
            "未触发极限闪避时的招式版本",
            None,
            static=False,
        ),
        _condition(
            YIN_PERFECT_DODGE_CONDITION_ID,
            "引沧澜：触发极限闪避",
            "触发极限闪避时的招式版本",
            None,
            static=False,
        ),
    )
    parameters = (
        ScenarioIntegerParameter(
            parameter_id=FLOWING_CLOUD_COUNT_PARAMETER_ID,
            label="流云剑意剑气次数",
            original_text="每道剑气",
            resolution=ParameterResolution.USER_SELECTED,
            value=None,
            minimum=0,
            maximum=None,
        ),
    )

    move_entries: list[MoveCalculationEntry] = []
    typed_templates: list[DirectDamageEventTemplate] = []
    diagnostics: list[CalculationDiagnostic] = []
    for spec in source.moves:
        entry, template, entry_diagnostics = _build_move(spec, config, source)
        move_entries.append(entry)
        typed_templates.append(template)
        diagnostics.extend(entry_diagnostics)

    c6_rule_id = RuleItemId("rule:ye:1431:cinema6")
    derived_specs = {
        "special-mingxin-guichen": (
            "template:ye:1431:cinema6:guichen-extra",
            "damage:ye:1431:cinema6:guichen-extra",
            "归尘最后一击额外伤害",
        ),
        "ultimate-zhanwangkaitian": (
            "template:ye:1431:cinema6:zhanwang-extra",
            "damage:ye:1431:cinema6:zhanwang-extra",
            "斩妄开天最后一击额外伤害",
        ),
    }
    derived_refs: dict[str, DerivedDamageEventTemplateRef] = {}
    for entry_key, (template_id, semantic_id, label) in derived_specs.items():
        ref = ApplicationDamageEventTemplateRef(
            template_id=EventTemplateId(template_id),
            semantic_id=DamageEventSemanticId(semantic_id),
            label=label,
            damage_type=DamageType.DIRECT,
            skill_group=None,
            damage_tags=frozenset(),
            element=Element.LINREN,
            source_rule_item_id=c6_rule_id,
        )
        derived_refs[entry_key] = DerivedDamageEventTemplateRef(
            template=ref,
            multiplier=FixedMultiplier(Resolved(15.0)),
        )
        typed_templates.append(
            DirectDamageEventTemplate(
                ref=ref,
                damage_dealer=source.character_id,
                element=Element.LINREN,
                base_source=CurrentAttackValueSource(source.character_id),
                crit_rule=StandardCritRule(source.character_id),
                move_id=None,
            )
        )

    updated_entries: list[MoveCalculationEntry] = []
    for entry in move_entries:
        derived: tuple[DerivedDamageEventTemplateRef, ...] = ()
        if str(entry.entry_id).endswith("special-mingxin-guichen"):
            derived = (derived_refs["special-mingxin-guichen"],)
        elif str(entry.entry_id).endswith("ultimate-zhanwangkaitian"):
            derived = (derived_refs["ultimate-zhanwangkaitian"],)
        updated_entries.append(
            MoveCalculationEntry(
                entry_id=entry.entry_id,
                character_id=entry.character_id,
                move_id=entry.move_id,
                display_name=entry.display_name,
                original_text=entry.original_text,
                skill_group=entry.skill_group,
                damage_tags=entry.damage_tags,
                multiplier_relation=entry.multiplier_relation,
                multiplier_variants=entry.multiplier_variants,
                main_damage_event=entry.main_damage_event,
                derived_damage_events=derived,
                stage_index=entry.stage_index,
                condition_ids=entry.condition_ids,
                diagnostics=entry.diagnostics,
            )
        )

    core_source = _rule_source(
        "source:ye:1431:core-passive",
        EffectSourceType.CORE_PASSIVE,
        source.core_passive_name,
        source.core_passive_text,
    )
    core_damage, core_bonus = source.core_damage_levels[config.core_level - 1]
    rule_items: list[CalculationRuleItem] = [
        CalculationRuleItem(
            rule_id=RuleItemId("rule:ye:1431:hedao"),
            owner=source.character_id,
            source=core_source,
            display_name="合道",
            original_text=source.core_passive_text,
            eligibility=RuleEligibility.ELIGIBLE,
            effects=(
                _modifier(
                    "effect:ye:1431:hedao:crit-rate",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    core_damage,
                ),
                _modifier(
                    "effect:ye:1431:hedao:damage-bonus",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    core_bonus,
                ),
            ),
        ),
        CalculationRuleItem(
            rule_id=RuleItemId("rule:ye:1431:veil"),
            owner=source.character_id,
            source=core_source,
            display_name="以太帷幕·决裁",
            original_text=source.core_passive_text,
            eligibility=RuleEligibility.ELIGIBLE,
            condition_ids=(MINGXIN_CONDITION_ID,),
            effects=(
                _modifier(
                    "effect:ye:1431:veil:vulnerability",
                    core_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    min(
                        config.enemy_stun_vulnerability_bonus,
                        2.0 if config.cinema_level >= 4 else 1.10,
                    ),
                    owner=source.character_id,
                    target=EffectTarget.ENEMY,
                    operation=EffectOperation.OVERRIDE,
                    filters=(CharacterFilter(source.character_id),),
                ),
            ),
        ),
    ]
    rule_items.extend(
        _cinema_rule_items(
            config,
            source,
            derived_refs["special-mingxin-guichen"].template.template_id,
            derived_refs["ultimate-zhanwangkaitian"].template.template_id,
        )
    )
    diagnostics.extend(
        CalculationDiagnostic(
            diagnostic_id=DiagnosticId("data:ye:1431:feiguang"),
            kind=DiagnosticKind.DATA_QUALITY,
            message=note,
            blocking=False,
            original_text=note,
        )
        for note in source.data_quality_notes
    )
    return CharacterCalculationDefinition(
        character_id=source.character_id,
        role=CharacterRole.ATTACK,
        base_element=source.element,
        source=core_source,
        move_entries=tuple(updated_entries),
        rule_items=tuple(rule_items),
        scenario_conditions=static_conditions + user_conditions,
        scenario_parameters=parameters,
        damage_event_templates=tuple(typed_templates),
        diagnostics=tuple(diagnostics),
    )


def _validate_raw_record(
    raw_record: YeShunguangRawRecord,
    reviewed_source: YeShunguangReviewedSource,
) -> None:
    if raw_record.character_id != reviewed_source.character_id:
        raise ValueError("raw record and reviewed source character IDs must match")
    if raw_record.name != reviewed_source.name:
        raise ValueError("raw record and reviewed source names must match")
    if raw_record.code_name != "Ye Shunguang":
        raise ValueError("unexpected Ye Shunguang code name in raw record")
    if raw_record.specialty != reviewed_source.role:
        raise ValueError("raw record specialty does not match reviewed source")
    if raw_record.element != "物理":
        raise ValueError("unexpected Ye Shunguang element in raw record")
    if raw_record.core_passive_name != reviewed_source.core_passive_name:
        raise ValueError("raw record core passive does not match reviewed source")
    if raw_record.extra_ability_name != reviewed_source.extra_ability_name:
        raise ValueError("raw record extra ability does not match reviewed source")
    if raw_record.cinema_names != reviewed_source.cinema_names:
        raise ValueError("raw record cinema names do not match reviewed source")
    if not raw_record.moves:
        raise ValueError("raw record must contain at least one move")
