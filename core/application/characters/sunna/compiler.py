"""Compile reviewed Sunna source data into static calculation contracts."""

from __future__ import annotations

import re
from dataclasses import replace

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
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
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    GuaranteedCritEffect,
    InitialAttackValueSource,
    ModifierEffect,
    ModifierResult,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
)

from ...diagnostics import CalculationDiagnostic
from ...ids import DamageEventSemanticId, RuleItemId, ScenarioConditionId
from ...moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..nanoka_compiler import (
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..templates import DirectDamageEventTemplate
from .config import SUNNA_ID, SunnaCatGazeTriggerer, SunnaCompileConfig
from .reviewed import (
    ANGEL_CHORUS_ACTIVE,
    BAD_CAT_ACTIVE,
    CINEMA6_CREATING_ACTIVE,
    ETHER_VEIL_ACTIVE,
    EXTRA_STUN_VULNERABILITY_ACTIVE,
    COOPERATIVE_PHOTO_EXTRA,
    SUNNA_ETHER_VEIL_ACTIVE,
    SUNNA_REVIEWED_MAPPING,
)

# This condition says the selected primary target currently carries the mark.
# It is a static scenario choice; Core duration/refresh timing is not replayed.
CAT_GAZE_ON_TARGET_ACTIVE = ScenarioConditionId("condition:sunna:cat-gaze-on-target-active")
CINEMA4_TEAM_DAMAGE_ACTIVE = ScenarioConditionId("condition:sunna:cinema4-team-damage-active")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must have one source value, found {len(matches)}")
    return float(matches[0].group("value"))


def _condition(condition_id, label: str, text: str, value: bool) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(SUNNA_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
    diagnostics: tuple[CalculationDiagnostic, ...] = (),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1491:{key}"),
        owner=SUNNA_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        diagnostics=diagnostics,
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    recipient_character_id=None,
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1491:{key}"),
            source=source,
            owner=SUNNA_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
            recipient_character_id=recipient_character_id,
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=operation,
            value=value,
        ),
    )


def _cat_gaze_template_id(character_id) -> EventTemplateId:
    suffix = str(character_id).replace(":", "_")
    return EventTemplateId(f"template:character:1491:core:cat-gaze:{suffix}")


def _cat_gaze_for_triggerer(
    raw: NanokaRawRecord,
    config: SunnaCompileConfig,
    triggerer: SunnaCatGazeTriggerer,
    core_source: RuleSource,
    all_cat_gaze_template_ids: tuple[EventTemplateId, ...],
) -> tuple[CalculationRuleItem, DirectDamageEventTemplate, DerivedDamageEventTemplateRef]:
    """Make one explicit child template using the selected real teammate's panels."""

    core = raw.core_levels[config.core_level - 1]
    attack_ratio = _number(
        core.description,
        r"\[强攻\]角色触发时[^。\n]*?(?P<value>[\d.]+)%攻击力",
        "Sunna Core Attack-trigger Cat's Gaze multiplier",
    ) / 100.0
    anomaly_ratio = _number(
        core.description,
        r"\[异常\]角色触发时[^。\n]*?(?P<value>[\d.]+)%攻击力",
        "Sunna Core Anomaly-trigger Cat's Gaze multiplier",
    ) / 100.0
    role_ratio = attack_ratio if triggerer.role is CharacterRole.ATTACK else anomaly_ratio
    template_id = _cat_gaze_template_id(triggerer.character_id)
    rule_key = f"core:cat-gaze:triggerer:{str(triggerer.character_id).replace(':', '_')}"
    rule_id = RuleItemId(f"rule:character:1491:{rule_key}")
    label = f"核心被动：猫的凝视（{triggerer.character_id}触发）"
    template_ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId(str(template_id).replace("template:", "event:")),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=triggerer.element,
        source_rule_item_id=rule_id,
    )
    template = DirectDamageEventTemplate(
        ref=template_ref,
        damage_dealer=triggerer.character_id,
        element=triggerer.element,
        base_source=CurrentAttackValueSource(triggerer.character_id),
        crit_rule=StandardCritRule(
            triggerer.character_id,
            guaranteed=triggerer.role is CharacterRole.ANOMALY,
        ),
        move_id=None,
    )
    effect_filters = (
        DamageTypeFilter(DamageType.DIRECT),
        DamageDealerFilter(triggerer.character_id),
        # Cat's Gaze children must not trigger any Cat's Gaze child, including
        # one created for another teammate with the same damage dealer.
        *(NotFilter(EventTemplateIdFilter(item)) for item in all_cat_gaze_template_ids),
    )
    create_effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1491:{rule_key}"),
            source=core_source,
            owner=SUNNA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=effect_filters,
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_id,
            unique_per_source_event=True,
        ),
    )
    effects = [create_effect]
    if triggerer.role is CharacterRole.ANOMALY:
        crit_damage = _number(
            core.description,
            r"暴击伤害增加(?P<value>[\d.]+)%",
            "Sunna Core Anomaly-trigger Cat's Gaze Crit Damage",
        ) / 100.0
        effects.append(
            _modifier(
                f"{rule_key}:anomaly-crit-damage",
                core_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                Resolved(crit_damage),
                target=EffectTarget.RECIPIENT,
                recipient_character_id=triggerer.character_id,
                filters=(
                    DamageDealerFilter(triggerer.character_id),
                    EventTemplateIdFilter(template_id),
                ),
            )
        )
        effects.append(
            GuaranteedCritEffect(
                rule=EffectRule(
                    effect_id=EffectId(
                        f"effect:character:1491:{rule_key}:anomaly-guaranteed-crit"
                    ),
                    source=core_source,
                    owner=SUNNA_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageDealerFilter(triggerer.character_id),
                        EventTemplateIdFilter(template_id),
                    ),
                )
            )
        )
    condition_ids = [CAT_GAZE_ON_TARGET_ACTIVE]
    if triggerer.character_id == SUNNA_ID:
        condition_ids.append(CINEMA6_CREATING_ACTIVE)
    rule = _rule(
        rule_key,
        core_source,
        label,
        core.description,
        RuleEligibility.ELIGIBLE,
        effects=effects,
        condition_ids=condition_ids,
    )
    derived = DerivedDamageEventTemplateRef(
        template=template_ref,
        multiplier=FixedMultiplier(Resolved(role_ratio)),
    )
    return rule, template, derived


def compile_sunna(
    config: SunnaCompileConfig,
    raw_record: NanokaRawRecord,
):
    if raw_record.character_id != SUNNA_ID:
        raise ValueError("Sunna compiler requires character:1491 raw data")
    if raw_record.element != "物理":
        raise ValueError("Sunna raw data must identify Physical as its base element")

    entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=SUNNA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=SUNNA_REVIEWED_MAPPING,
        id_namespace="character:1491",
    )
    # Bad Cat's source explicitly bases this auto-attack on Sunna's immutable
    # Initial ATK panel, unlike her ordinary Basic Attack stages.
    direct_templates = tuple(
        replace(template, base_source=InitialAttackValueSource(SUNNA_ID))
        if str(template.ref.template_id).endswith(":bad-cat:main")
        else template
        for template in direct_templates
    )
    raw_moves = raw_move_index(raw_record)
    photo_level = effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    photo_base = raw_multiplier(
        raw_moves,
        "强化特殊技：特别拍照技巧",
        "伤害倍率",
        photo_level,
        "character:1491:ex-special-photo-technique",
        [],
        source_skill_id="1491008",
    )
    photo_extra = raw_multiplier(
        raw_moves,
        "强化特殊技：特别拍照技巧",
        "伤害倍率（协同）",
        photo_level,
        "character:1491:ex-special-photo-technique-cooperative",
        [],
        source_skill_components=(("1491019", 1.0),),
    )
    if not isinstance(photo_base, float) or not isinstance(photo_extra, float):
        raise ValueError("Sunna Photo Technique source curves are required")
    cooperative_photo_parameter = ScenarioIntegerParameter(
        parameter_id=COOPERATIVE_PHOTO_EXTRA,
        label="特别拍照技巧协同倍率",
        original_text="伤害倍率（协同）",
        resolution=ParameterResolution.USER_SELECTED,
        value=config.cooperative_photo_extra,
        minimum=0,
        maximum=1,
    )
    photo_entries: list = []
    for entry in entries:
        if str(entry.entry_id).endswith(":ex-special-photo-technique"):
            variant = replace(
                entry.multiplier_variants[0],
                label=f"{entry.multiplier_variants[0].label} + 协同倍率",
                parameter_value_id=COOPERATIVE_PHOTO_EXTRA,
                parameter_base_value=photo_base,
                parameter_coefficient=photo_extra,
            )
            entry = replace(entry, multiplier_variants=(variant,))
        photo_entries.append(entry)
    entries = tuple(photo_entries)
    raw_core = raw_record.core_levels[config.core_level - 1]
    core_source = _source(
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        raw_core.name,
        raw_core.description,
    )
    c1, c2, c3, c4, c5, c6 = raw_record.mindscapes
    c1_source = _source("cinema-1", EffectSourceType.CINEMA, c1.name, c1.description)
    c2_source = _source("cinema-2", EffectSourceType.CINEMA, c2.name, c2.description)
    c3_source = _source("cinema-3", EffectSourceType.CINEMA, c3.name, c3.description)
    c4_source = _source("cinema-4", EffectSourceType.CINEMA, c4.name, c4.description)
    c5_source = _source("cinema-5", EffectSourceType.CINEMA, c5.name, c5.description)
    c6_source = _source("cinema-6", EffectSourceType.CINEMA, c6.name, c6.description)

    conditions = (
        _condition(
            ANGEL_CHORUS_ACTIVE,
            "当前队伍处于天使协律",
            raw_record.moves[0].description,
            config.angel_chorus_active,
        ),
        _condition(
            ETHER_VEIL_ACTIVE,
            "当前存在以太帷幕",
            c2.description,
            config.ether_veil_active,
        ),
        _condition(
            CAT_GAZE_ON_TARGET_ACTIVE,
            "当前主要目标持有猫的凝视",
            raw_core.description,
            config.cat_gaze_target_mark_active,
        ),
        _condition(
            BAD_CAT_ACTIVE,
            "当前满足后场、无猫凝视目标且泡泡持有磨爪器，坏猫自动攻击触发",
            raw_moves["普通攻击：坏猫出没"].description,
            config.bad_cat_active,
        ),
        _condition(
            CINEMA4_TEAM_DAMAGE_ACTIVE,
            "4影终结技后的全队增伤当前生效",
            c4.description,
            config.cinema4_team_damage_active,
        ),
        _condition(
            CINEMA6_CREATING_ACTIVE,
            "6影潜心创作中当前生效",
            c6.description,
            config.cinema6_creating_active,
        ),
        _condition(
            SUNNA_ETHER_VEIL_ACTIVE,
            "当前千夏的以太帷幕·妄想重奏生效",
            raw_moves["强化特殊技：特别拍照技巧"].description,
            config.sunna_ether_veil_active,
        ),
        _condition(
            EXTRA_STUN_VULNERABILITY_ACTIVE,
            "额外能力的失衡易伤当前生效",
            raw_record.extra_ability_description,
            config.extra_stun_vulnerability_active,
        ),
    )
    rules: list[CalculationRuleItem] = []
    templates = list(direct_templates)
    derived_events: list[DerivedDamageEventTemplateRef] = []
    core_cap = _number(
        raw_core.description,
        r"最高不超过(?P<value>[\d.]+)点",
        "Sunna Core Angel Chorus Attack cap",
    )
    attack_buff = PanelStatDerivedValue(
        source_character_id=SUNNA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
        coefficient=Resolved(0.30),
        cap_max=Resolved(core_cap),
    )
    rules.append(
        _rule(
            "core:angel-chorus-attack",
            core_source,
            f"核心被动：天使协律攻击力+初始攻×30%（上限{core_cap:g}）",
            raw_core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(ANGEL_CHORUS_ACTIVE,),
            effects=(
                _modifier(
                    "core:angel-chorus-attack",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    attack_buff,
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    photo_text = raw_moves["强化特殊技：特别拍照技巧"].description
    photo_veil_attack = _number(
        photo_text,
        r"攻击力额外提升(?P<value>[\d.]+)点",
        "Sunna Photo Technique Ether Veil flat Attack bonus",
    )
    photo_veil_source = _source(
        "special-photo-technique:ether-veil-attack",
        EffectSourceType.SPECIAL_MECHANISM,
        "强化特殊技：特别拍照技巧",
        photo_text,
    )
    rules.append(
        _rule(
            "special-photo-technique:sunna-ether-veil-attack",
            photo_veil_source,
            f"特别拍照技巧：妄想重奏以太帷幕全队攻击力+{photo_veil_attack:g}",
            photo_text,
            RuleEligibility.ELIGIBLE,
            condition_ids=(SUNNA_ETHER_VEIL_ACTIVE,),
            effects=(
                _modifier(
                    "special-photo-technique:sunna-ether-veil-attack",
                    photo_veil_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    Resolved(photo_veil_attack),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    # A child template is emitted for each actual Attack/Anomaly teammate.
    # Identity, native element, ATK source, and Crit owner all remain that
    # teammate. C6 lets Sunna join this list as an Attack triggerer, but only
    # while its current creation state is selected.
    triggerers = list(config.cat_gaze_triggerers)
    if config.cinema_level >= 6 and all(
        item.character_id != SUNNA_ID for item in triggerers
    ):
        triggerers.append(SunnaCatGazeTriggerer(SUNNA_ID, CharacterRole.ATTACK, Element.PHYSICAL))
    all_cat_gaze_template_ids = tuple(
        _cat_gaze_template_id(item.character_id) for item in triggerers
    )
    for triggerer in triggerers:
        rule, template, derived = _cat_gaze_for_triggerer(
            raw_record,
            config,
            triggerer,
            core_source,
            all_cat_gaze_template_ids,
        )
        rules.append(rule)
        templates.append(template)
        derived_events.append(derived)

    # Cinema 2 modifies each exact Core child template; it does not broaden to
    # every direct hit produced by those Attack/Anomaly teammates.
    c2_attack_ratio = _number(
        c2.description,
        r"\[强攻\]角色触发时.*?伤害倍率增加(?P<value>[\d.]+)%",
        "Sunna Cinema 2 Attack Cat's Gaze multiplier increase",
    ) / 100.0
    c2_anomaly_ratio = _number(
        c2.description,
        r"\[异常\]角色触发时.*?伤害倍率增加(?P<value>[\d.]+)%",
        "Sunna Cinema 2 Anomaly Cat's Gaze multiplier increase",
    ) / 100.0
    core_attack_ratio = _number(
        raw_core.description,
        r"\[强攻\]角色触发时[^。\n]*?(?P<value>[\d.]+)%攻击力",
        "Sunna Core Attack-trigger Cat's Gaze multiplier",
    ) / 100.0
    core_anomaly_ratio = _number(
        raw_core.description,
        r"\[异常\]角色触发时[^。\n]*?(?P<value>[\d.]+)%攻击力",
        "Sunna Core Anomaly-trigger Cat's Gaze multiplier",
    ) / 100.0
    c2_ratio_effects = []
    child_ids = []
    for triggerer in triggerers:
        template_id = _cat_gaze_template_id(triggerer.character_id)
        child_ids.append(template_id)
        bonus = c2_attack_ratio if triggerer.role is CharacterRole.ATTACK else c2_anomaly_ratio
        base_ratio = core_attack_ratio if triggerer.role is CharacterRole.ATTACK else core_anomaly_ratio
        c2_ratio_effects.append(
            _modifier(
                f"cinema2:cat-gaze-ratio:{str(triggerer.character_id).replace(':', '_')}",
                c2_source,
                CalculationNode.DAMAGE_SKILL_MULTIPLIER,
                Resolved((base_ratio + bonus) / base_ratio),
                target=EffectTarget.TEAM,
                filters=(
                    DamageDealerFilter(triggerer.character_id),
                    EventTemplateIdFilter(template_id),
                ),
                operation=EffectOperation.MULTIPLY,
            )
        )
    c2_atk_percent = _number(
        c2.description,
        r"全队角色攻击力提升(?P<value>[\d.]+)%",
        "Sunna Cinema 2 team Attack bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema2:ether-veil-team-attack",
            c2_source,
            f"2影：处于任意以太帷幕内时全队攻击力+{c2_atk_percent:.0%}",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:team-attack",
                    c2_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    Resolved(c2_atk_percent),
                    target=EffectTarget.TEAM,
                ),
            ) if config.cinema_level >= 2 else (),
            condition_ids=(ETHER_VEIL_ACTIVE,),
        )
    )
    rules.append(
        _rule(
            "cinema2:cat-gaze-ratio",
            c2_source,
            f"2影：猫凝视倍率按强攻/异常触发者+{c2_attack_ratio:.0%}/{c2_anomaly_ratio:.0%}",
            c2.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 2 else RuleEligibility.INELIGIBLE,
            effects=c2_ratio_effects if config.cinema_level >= 2 else (),
        )
    )

    ability_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    stun_bonus = _number(
        raw_record.extra_ability_description,
        r"失衡易伤倍率提升(?P<value>[\d.]+)%",
        "Sunna Additional Ability enemy Stun vulnerability",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:ether-veil-stun-vulnerability",
            ability_source,
            f"额外能力：以太帷幕命中后目标失衡易伤+{stun_bonus:.0%}",
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE if config.additional_ability_eligible else RuleEligibility.INELIGIBLE,
            condition_ids=(EXTRA_STUN_VULNERABILITY_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:ether-veil-stun-vulnerability",
                    ability_source,
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(stun_bonus),
                    target=EffectTarget.ENEMY,
                ),
            ) if config.additional_ability_eligible else (),
        )
    )

    c1_defense_reduction = _number(
        c1.description,
        r"防御力降低(?P<value>[\d.]+)%",
        "Sunna Cinema 1 enemy Defense reduction",
    ) / 100.0
    rules.append(
        _rule(
            "cinema1:enemy-defense-reduction",
            c1_source,
            f"1影：目标防御力降低{c1_defense_reduction:.0%}×{config.cinema1_defense_reduction_stacks}层",
            c1.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 1 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:enemy-defense-reduction",
                    c1_source,
                    CalculationNode.ENEMY_DEFENSE_REDUCTION,
                    Resolved(c1_defense_reduction),
                    target=EffectTarget.ENEMY,
                ),
            ) if config.cinema_level >= 1 else (),
            stack_count=config.cinema1_defense_reduction_stacks,
            stack_min=0,
            stack_max=3,
        )
    )

    c4_team_damage = _number(
        c4.description,
        r"全队角色造成的伤害提升(?P<value>[\d.]+)%",
        "Sunna Cinema 4 team damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema4:team-damage-after-ultimate",
            c4_source,
            f"4影：终结技后全队造成的伤害+{c4_team_damage:.0%}",
            c4.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 4 else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:team-damage-after-ultimate",
                    c4_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c4_team_damage),
                    target=EffectTarget.TEAM,
                ),
            ) if config.cinema_level >= 4 else (),
            condition_ids=(CINEMA4_TEAM_DAMAGE_ACTIVE,),
        )
    )

    c6_cd_rate = _number(
        c6.description,
        r"初始攻击力的(?P<value>[\d.]+)%提升自身的暴击伤害",
        "Sunna Cinema 6 Initial ATK to Crit Damage coefficient",
    ) / 100.0
    c6_cd_cap = _number(
        c6.description,
        r"最多提升(?P<value>[\d.]+)%",
        "Sunna Cinema 6 self Crit Damage cap",
    ) / 100.0
    c6_damage_bonus = _number(
        c6.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Sunna Cinema 6 Cat's Gaze damage bonus",
    ) / 100.0
    c6_self_effects = (
        _modifier(
            "cinema6:self-crit-damage-from-initial-attack",
            c6_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            PanelStatDerivedValue(
                source_character_id=SUNNA_ID,
                source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
                coefficient=Resolved(c6_cd_rate),
                cap_max=Resolved(c6_cd_cap),
            ),
            target=EffectTarget.SELF,
        ),
        GuaranteedCritEffect(
            rule=EffectRule(
                effect_id=EffectId("effect:character:1491:cinema6:self-guaranteed-crit"),
                source=c6_source,
                owner=SUNNA_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(SUNNA_ID),
                ),
            )
        ),
    )
    rules.append(
        _rule(
            "cinema6:self-crit-and-cat-gaze-state",
            c6_source,
            f"6影潜心创作中：自身攻击必暴、初始攻击转暴伤（上限{c6_cd_cap:.0%}）",
            c6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            effects=c6_self_effects if config.cinema_level >= 6 else (),
            condition_ids=(CINEMA6_CREATING_ACTIVE,),
        )
    )
    c6_filters = tuple(EventTemplateIdFilter(item) for item in child_ids)
    c6_effects = (
        (
            _modifier(
                "cinema6:cat-gaze-damage-bonus",
                c6_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(c6_damage_bonus),
                target=EffectTarget.TEAM,
                filters=(AnyFilter(c6_filters),),
            ),
        )
        if c6_filters
        else ()
    )
    rules.append(
        _rule(
            "cinema6:cat-gaze-damage-bonus",
            c6_source,
            f"6影潜心创作中：全队猫的凝视伤害+{c6_damage_bonus:.0%}",
            c6.description,
            RuleEligibility.ELIGIBLE if config.cinema_level >= 6 else RuleEligibility.INELIGIBLE,
            effects=c6_effects if config.cinema_level >= 6 else (),
            condition_ids=(CINEMA6_CREATING_ACTIVE,),
        )
    )

    for level, source in ((3, c3_source), (5, c5_source)):
        cinema = raw_record.mindscapes[level - 1]
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：技能等级提升",
                cinema.description,
                RuleEligibility.ELIGIBLE if config.cinema_level >= level else RuleEligibility.INELIGIBLE,
            )
        )

    return build_definition(
        character_id=SUNNA_ID,
        role=CharacterRole.SUPPORT,
        element=Element.PHYSICAL,
        source=_source(
            "nanoka-3.2",
            EffectSourceType.SPECIAL_MECHANISM,
            "Nanoka 3.2",
            raw_record.source_url,
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        parameters=(cooperative_photo_parameter,),
        independent_derived_damage_events=derived_events,
        diagnostics=diagnostics,
    )


def load_raw_record(record):
    """Parse the packaged Nanoka detail after checking its stable character ID."""

    return load_nanoka_raw_record(
        record,
        expected_character_id=str(SUNNA_ID),
    )


__all__ = ["compile_sunna", "CAT_GAZE_ON_TARGET_ACTIVE", "CINEMA4_TEAM_DAMAGE_ACTIVE"]
