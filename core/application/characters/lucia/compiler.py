"""Compile Lucia's raw record into reviewed Direct, HP, and anomaly events."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CharacterRole,
    CalculationNode,
    CreatedByEffectFilter,
    CurrentAttackValueSource,
    CurrentMaxHPValueSource,
    DamageDealerFilter,
    DamageSubtype,
    DamageTag,
    DamageType,
    DamageTypeFilter,
    DynamicIdentityFilter,
    EventTemplateIdFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventCreationEffect,
    EventCreationResult,
    FixedMultiplier,
    GuaranteedCritEffect,
    DynamicIdentity,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    NoCritRule,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    StandardCritRule,
    Unresolved,
    UnresolvedReason,
    SkillGroup,
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
    DerivedDamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ScenarioCondition,
)
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, NanokaRawMoveRecord, load_nanoka_raw_record
from ..templates import (
    AttributeAnomalyDamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
)
from .config import LuciaCompileConfig
from .reviewed import (
    ADDITIONAL_ATTACK_READY,
    ANY_ETHER_CURTAIN_ACTIVE,
    BASIC_CHORUS_MOVE_ID,
    BREAK_DARK_ACTIVE,
    CHAIN_CHORUS_MOVE_ID,
    DODGE_COUNTER_CHORUS_MOVE_ID,
    DREAM_ACTIVE,
    DREAM_INACTIVE,
    DREAM_SONG_ACTIVE,
    EX_SPECIAL_CHORUS_MOVE_ID,
    LUCIA_ADDITIONAL_ATTACK_CURVES,
    LUCIA_CHORUS_MOVE_IDS,
    LUCIA_ID,
    LUCIA_ETHER_ANOMALY_RECORD_ID,
    LUCIA_REVIEWED_MAPPING,
    QUICK_ASSIST_CHORUS_MOVE_ID,
    SPRING_CURTAIN_ACTIVE,
    SPECIAL_CHORUS_MOVE_ID,
    SUPPORT_FOLLOW_UP_CHORUS_MOVE_ID,
    ULTIMATE_CHORUS_MOVE_ID,
    ULTIMATE_RUSH_HIT_MOVE_ID,
    CORE_ADDITIONAL_ATTACK_EFFECT_ID,
)


_EX_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK})
_ULTIMATE = frozenset({DamageTag.ULTIMATE})
_BASIC = frozenset({DamageTag.BASIC_ATTACK})
_COUNTER = frozenset({DamageTag.DODGE_COUNTER})
_SPECIAL = frozenset({DamageTag.SPECIAL_ATTACK})
_CHAIN = frozenset({DamageTag.CHAIN_ATTACK})
_ASSIST = frozenset({DamageTag.ASSIST})
_FOLLOW_UP = frozenset({DamageTag.ASSIST, DamageTag.FOLLOW_UP_ATTACK})
_EX_HP_COMPONENT_EFFECT_ID = EffectId(
    "effect:character:1451:ex-special:chorus-hp-final-hit"
)
_CHORUS_FINAL_HP_RULE_ID = RuleItemId(
    "rule:character:1451:ex-special:chorus-hp-final-hit"
)
_ULTIMATE_FINAL_HP_EFFECT_ID = EffectId(
    "effect:character:1451:chorus-hp-final-hit:ultimate-chorus-hp-finisher"
)

_CHORUS_FINAL_HP_COMPONENTS = (
    (
        "basic-chorus-fifth-hp",
        BASIC_CHORUS_MOVE_ID,
        "普通攻击：星轨连击（五段·合唱）",
        SkillGroup.BASIC_ATTACK,
        _BASIC,
    ),
    (
        "dodge-counter-chorus-hp",
        DODGE_COUNTER_CHORUS_MOVE_ID,
        "闪避反击：星尘回响（合唱）",
        SkillGroup.DODGE,
        _COUNTER,
    ),
    (
        "special-chorus-hp",
        SPECIAL_CHORUS_MOVE_ID,
        "特殊技：死神协奏曲·风暴（合唱）",
        SkillGroup.SPECIAL_ATTACK,
        _SPECIAL,
    ),
    (
        "ex-special-chorus-hp-final-hit",
        EX_SPECIAL_CHORUS_MOVE_ID,
        "强化特殊技：死神协奏曲·破晓（合唱）",
        SkillGroup.SPECIAL_ATTACK,
        _EX_SPECIAL,
    ),
    (
        "chain-chorus-hp",
        CHAIN_CHORUS_MOVE_ID,
        "连携技：璀色剧场（合唱）",
        SkillGroup.CHAIN_ATTACK,
        _CHAIN,
    ),
    (
        "ultimate-chorus-hp-finisher",
        ULTIMATE_CHORUS_MOVE_ID,
        "终结技：进击，大铠甲！（合唱收尾）",
        SkillGroup.ULTIMATE,
        _ULTIMATE,
    ),
    (
        "quick-assist-chorus-hp",
        QUICK_ASSIST_CHORUS_MOVE_ID,
        "快速支援：迷雾重击（合唱）",
        SkillGroup.ASSIST,
        _ASSIST,
    ),
    (
        "support-follow-up-chorus-hp",
        SUPPORT_FOLLOW_UP_CHORUS_MOVE_ID,
        "支援突击：绘梦和声（合唱）",
        SkillGroup.ASSIST,
        _FOLLOW_UP,
    ),
)


def _condition(
    condition_id,
    label: str,
    original_text: str,
    value: bool | None = None,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _rule(
    rule_key: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1451:{rule_key}"),
        owner=LUCIA_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
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
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1451:{effect_key}"),
            source=source,
            owner=LUCIA_ID,
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


def _number(text: str, pattern: str, *, subject: str) -> float:
    matches = tuple(re.finditer(pattern, text, re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one reviewed value; found {len(matches)}")
    return float(matches[0].group("value"))


def _ratio(text: str, pattern: str, *, subject: str) -> float:
    return _number(text, pattern, subject=subject) / 100.0


def _calc_skill_formula(
    text: str,
    pattern: str,
    *,
    skill_level: int,
    divisor: float,
    subject: str,
) -> float:
    matches = tuple(re.finditer(pattern, text, re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one reviewed CAL formula; found {len(matches)}")
    match = matches[0]
    base = float(match.group("base"))
    level_coefficient = float(match.group("level_coefficient"))
    formula_skill_ref = match.group("skill_ref")
    if formula_skill_ref != "1":
        raise ValueError(f"{subject} references unsupported AvatarSkillLevel({formula_skill_ref})")
    return (base + level_coefficient * skill_level) / divisor


def _mindscape(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"Lucia raw record is missing mindscape {level}") from exc


def _raw_move(raw_moves: dict[str, NanokaRawMoveRecord], name: str):
    try:
        return raw_moves[name]
    except KeyError as exc:
        raise ValueError(f"Lucia raw record is missing move {name!r}") from exc


def _raw_curve(raw_move, parameter_name: str, source_skill_id: str, level: int):
    parameter = next(
        (item for item in raw_move.parameters if item.name == parameter_name),
        None,
    )
    if parameter is None or parameter.format != "%":
        return None
    return parameter.value_for_level(level, source_skill_id)


def _direct_template(
    *,
    key: str,
    label: str,
    move_id: MoveId,
    skill_group: SkillGroup,
    damage_tags: frozenset[DamageTag],
    base_source=None,
    source_rule_item_id: RuleItemId | None = None,
) -> DirectDamageEventTemplate:
    chosen_source = base_source or CurrentAttackValueSource(LUCIA_ID)
    ref = DamageEventTemplateRef(
        template_id=f"template:character:1451:{key}",
        semantic_id=DamageEventSemanticId(f"event:character:1451:{key}"),
        label=label,
        damage_type=DamageType.DIRECT,
        skill_group=skill_group,
        damage_tags=damage_tags,
        element=Element.ETHER,
        source_rule_item_id=source_rule_item_id,
    )
    return DirectDamageEventTemplate(
        ref=ref,
        damage_dealer=LUCIA_ID,
        element=Element.ETHER,
        base_source=chosen_source,
        crit_rule=StandardCritRule(LUCIA_ID),
        move_id=move_id,
    )


def _special_entry(
    *,
    entry_key: str,
    move_id: MoveId,
    label: str,
    ref: DamageEventTemplateRef,
    multiplier: FixedMultiplier,
    original_text: str,
    relation: MultiplierRelation = MultiplierRelation.COMPLETE,
    repeat_count: int | None = None,
) -> MoveCalculationEntry:
    variants = (
        MultiplierVariant(
            variant_id=MultiplierVariantId(f"variant:character:1451:{entry_key}"),
            label="完整伤害",
            parameter_name="特殊伤害倍率",
            multiplier=multiplier,
            repeat_count=repeat_count,
        ),
    )
    return MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:character:1451:{entry_key}"),
        character_id=LUCIA_ID,
        move_id=move_id,
        display_name=label,
        original_text=original_text,
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=relation,
        multiplier_variants=variants,
        main_damage_event=ref,
    )


def _anomaly_disorder_pair(raw: NanokaRawRecord):
    anomaly_ref = DamageEventTemplateRef(
        template_id="template:character:1451:ether-anomaly",
        semantic_id=DamageEventSemanticId("event:character:1451:ether-anomaly"),
        label="属性异常：以太侵蚀",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=Element.ETHER,
    )
    anomaly_template = AttributeAnomalyDamageEventTemplate(
        ref=anomaly_ref,
        damage_dealer=LUCIA_ID,
        element=Element.ETHER,
        anomaly_triggerer=LUCIA_ID,
        history_record_source=LUCIA_ETHER_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=MoveId("move:lucia:ether-corruption-anomaly"),
    )
    anomaly_entry = _special_entry(
        entry_key="ether-anomaly",
        move_id=MoveId("move:lucia:ether-corruption-anomaly"),
        label="属性异常：以太侵蚀",
        ref=anomaly_ref,
        multiplier=FixedMultiplier(Resolved(0.625)),
        relation=MultiplierRelation.UNIT_REPEAT,
        repeat_count=20,
        original_text=(
            f"{raw.name}造成以太属性积蓄；按规范10秒满持续时间结算，"
            "共20次62.5%侵蚀伤害。"
        ),
    )
    disorder_ref = DamageEventTemplateRef(
        template_id="template:character:1451:ether-disorder",
        semantic_id=DamageEventSemanticId("event:character:1451:ether-disorder"),
        label="紊乱：以太侵蚀",
        damage_type=DamageType.DISORDER,
        element=Element.ETHER,
    )
    disorder_template = DisorderDamageEventTemplate(
        ref=disorder_ref,
        damage_dealer=LUCIA_ID,
        element=Element.ETHER,
        disorder_triggerer=LUCIA_ID,
        history_record_source=LUCIA_ETHER_ANOMALY_RECORD_ID,
        crit_rule=NoCritRule(),
        move_id=MoveId("move:lucia:ether-corruption-disorder"),
    )
    disorder_entry = _special_entry(
        entry_key="ether-disorder",
        move_id=MoveId("move:lucia:ether-corruption-disorder"),
        label="紊乱：以太侵蚀",
        ref=disorder_ref,
        multiplier=FixedMultiplier(Resolved(17.0)),
        original_text=(
            "按10秒最大剩余时间结算：450%紊乱基础倍率 + "
            "20次侵蚀补偿（每次62.5%）= 1700%。"
        ),
    )
    return (anomaly_entry, disorder_entry), (anomaly_template, disorder_template)


def _unresolved_additional_attack(
    raw: NanokaRawRecord,
    raw_moves: dict[str, NanokaRawMoveRecord],
    config: LuciaCompileConfig,
    source: RuleSource,
) -> tuple[EventCreationEffect, DirectDamageEventTemplate, DerivedDamageEventTemplateRef]:
    level = effective_skill_level(config, SkillGroup.BASIC_ATTACK)
    candidates: list[tuple[str, float | None]] = []
    for move_name, source_skill_id in LUCIA_ADDITIONAL_ATTACK_CURVES:
        move = _raw_move(raw_moves, move_name)
        candidates.append(
            (source_skill_id, _raw_curve(move, "追加攻击伤害倍率", source_skill_id, level))
        )
    resolved = [value for _, value in candidates if value is not None]
    if len(resolved) != len(candidates) or len(set(resolved)) != 1:
        raise ValueError(
            "Lucia's confirmed additional-attack source curves must resolve to the same value"
        )
    multiplier = float(resolved[0]) / 100.0
    rule_id = RuleItemId("rule:character:1451:core:additional-attack")
    template_ref = DamageEventTemplateRef(
        template_id="template:character:1451:core:additional-attack",
        semantic_id=DamageEventSemanticId("event:character:1451:core:additional-attack"),
        label="核心被动：梦境追加攻击（合唱）",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset({DamageTag.FOLLOW_UP_ATTACK}),
        element=Element.ETHER,
        source_rule_item_id=rule_id,
    )
    template = DirectDamageEventTemplate(
        ref=template_ref,
        damage_dealer=LUCIA_ID,
        element=Element.ETHER,
        base_source=CurrentAttackValueSource(LUCIA_ID),
        crit_rule=StandardCritRule(LUCIA_ID),
        move_id=None,
    )
    effect = EventCreationEffect(
        rule=EffectRule(
            effect_id=EffectId(CORE_ADDITIONAL_ATTACK_EFFECT_ID),
            source=source,
            owner=LUCIA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(
                AnyFilter(
                    (
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTypeFilter(DamageType.PENETRATION),
                    )
                ),
                DynamicIdentityFilter(DynamicIdentity.DAMAGE_DEALER),
                NotFilter(DamageDealerFilter(LUCIA_ID)),
            ),
        ),
        result=EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=template_ref.template_id,
            unique_per_source_event=True,
        ),
    )
    derived = DerivedDamageEventTemplateRef(
        template=template_ref,
        multiplier=FixedMultiplier(Resolved(multiplier)),
    )
    return effect, template, derived


def _unique_conditions(conditions):
    seen = set()
    result = []
    for item in conditions:
        if item.condition_id in seen:
            continue
        seen.add(item.condition_id)
        result.append(item)
    return tuple(result)


def compile_lucia(
    config: LuciaCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    if raw_record.character_id != LUCIA_ID:
        raise ValueError("Lucia compiler requires character:1451 raw data")
    if raw_record.element != "以太":
        raise ValueError("Lucia raw data must identify 以太 as its base element")

    move_entries, direct_templates, diagnostics = compile_direct_moves(
        character_id=LUCIA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=LUCIA_REVIEWED_MAPPING,
        id_namespace="character:1451",
    )
    entries = list(move_entries)
    templates = list(direct_templates)
    rules: list[CalculationRuleItem] = []
    conditions = [
        _condition(
            DREAM_ACTIVE,
            "卢西娅当前处于梦境状态",
            "发动随想或合唱时，梦境值达到100会进入梦境；状态来源按当前状态输入。",
        ),
        _condition(
            DREAM_INACTIVE,
            "卢西娅当前不处于梦境状态",
            "梦境值不足或离开以太帷幕后，卢西娅退出梦境状态。",
        ),
        _condition(
            ANY_ETHER_CURTAIN_ACTIVE,
            "当前有任意以太帷幕生效",
            "影画6允许卢西娅处于任意以太帷幕内时获得效果。",
        ),
        _condition(
            SPRING_CURTAIN_ACTIVE,
            "当前处于以太帷幕·涌泉内",
            "影画效果指定以太帷幕·涌泉内生效。",
        ),
        _condition(
            DREAM_SONG_ACTIVE,
            "全队当前处于巡梦童谣状态",
            "卢西娅招式升级或追加攻击后，为全队施加巡梦童谣12秒。",
        ),
        _condition(
            BREAK_DARK_ACTIVE,
            "全队当前处于破暗状态",
            "卢西娅发动合唱后施加破暗，持续时间按当前状态输入。",
        ),
        _condition(
            ADDITIONAL_ATTACK_READY,
            "追加攻击当前可触发（8秒间隔已就绪）",
            "其他操作中角色攻击命中时触发追加攻击；每次触发后8秒内不会再次触发。",
        ),
    ]
    raw_moves = raw_move_index(raw_record)
    core = raw_record.core_levels[config.core_level - 1]
    core_source = source_for(
        LUCIA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    core_team_bonus = _ratio(
        core.description,
        r"巡梦童谣\]</color>状态下，角色造成的伤害提升<color=[^>]+>(?P<value>\d+(?:\.\d+)?)%</color>",
        subject="Lucia Core Dream Song team damage bonus",
    )
    curtain_hp_bonus = _ratio(
        core.description,
        r"\[以太帷幕·涌泉\]</color>生效期间，全队角色最大生命值提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Lucia Core Curtain team HP bonus",
    )
    core_rule = _rule(
        "core:dream-song-team-damage",
        core_source,
        "核心被动：巡梦童谣全队增伤",
        core.description,
        RuleEligibility.ELIGIBLE,
        condition_ids=(DREAM_SONG_ACTIVE,),
        effects=(
            _modifier(
                "core:dream-song-team-damage",
                core_source,
                CalculationNode.DAMAGE_NORMAL_BONUS,
                Resolved(core_team_bonus),
                target=EffectTarget.TEAM,
            ),
        ),
    )
    rules.append(core_rule)
    rules.append(
        _rule(
            "core:ether-curtain-team-hp",
            core_source,
            "核心被动：以太帷幕全队生命值提升",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(SPRING_CURTAIN_ACTIVE,),
            effects=(
                _modifier(
                    "core:ether-curtain-team-hp",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                    Resolved(curtain_hp_bonus),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )
    follow_up_effect, follow_up_template, follow_up_derived = _unresolved_additional_attack(
        raw_record,
        raw_moves,
        config,
        core_source,
    )
    rules.append(
        _rule(
            "core:additional-attack",
            core_source,
            "核心被动：梦境追加攻击",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(DREAM_ACTIVE, ADDITIONAL_ATTACK_READY),
            effects=(follow_up_effect,),
        )
    )
    templates.append(follow_up_template)

    extra_source = source_for(
        LUCIA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.additional_ability_eligible
        else RuleEligibility.INELIGIBLE
    )
    extra_crit_damage = _ratio(
        raw_record.extra_ability_description,
        r"额外附加暴击伤害提升(?P<value>\d+(?:\.\d+)?)%效果",
        subject="Lucia additional ability Break Dark crit damage",
    )
    rules.append(
        _rule(
            "extra-ability:break-dark-team-crit-damage",
            extra_source,
            "额外能力：破暗全队暴击伤害",
            raw_record.extra_ability_description,
            extra_eligibility,
            condition_ids=(BREAK_DARK_ACTIVE,),
            effects=(
                _modifier(
                    "extra-ability:break-dark-team-crit-damage",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(extra_crit_damage),
                    target=EffectTarget.TEAM,
                ),
            ),
        )
    )

    # Dark Break adds force from Lucia's INITIAL maximum HP, not her current
    # max-HP panel (which the Curtain can increase independently).
    ex_text = raw_moves["强化特殊技：死神协奏曲·破晓"].description
    special_level = effective_skill_level(config, SkillGroup.SPECIAL_ATTACK)
    hp_step = _number(
        ex_text,
        r"卢西娅每拥有(?P<value>\d+(?:\.\d+)?)点初始最大生命值",
        subject="Lucia Break Dark initial-HP step",
    )
    force_per_hp_base = _number(
        ex_text,
        r"可使贯穿力额外提升<color=[^>]+>\{CAL:(?P<value>[\d.]+)\+AvatarSkillLevel\(1\)\*[\d.]+,1,1\}</color>点",
        subject="Lucia Break Dark initial-HP force formula base",
    )
    force_skill_coefficient = _number(
        ex_text,
        r"可使贯穿力额外提升<color=[^>]+>\{CAL:[\d.]+\+AvatarSkillLevel\(1\)\*(?P<value>[\d.]+),1,1\}</color>点",
        subject="Lucia Break Dark per-level penetration-force coefficient",
    )
    force_cap_base = _number(
        ex_text,
        r"最多可提升<color=[^>]+>\{CAL:(?P<value>[\d.]+)\+AvatarSkillLevel\(1\)\*[\d.]+,1,2\}</color>点贯穿力",
        subject="Lucia Break Dark penetration-force cap base",
    )
    force_cap_skill_coefficient = _number(
        ex_text,
        r"最多可提升<color=[^>]+>\{CAL:[\d.]+\+AvatarSkillLevel\(1\)\*(?P<value>[\d.]+),1,2\}</color>点贯穿力",
        subject="Lucia Break Dark penetration-force cap per-level coefficient",
    )
    force_flat = _number(
        ex_text,
        r"状态下，贯穿力提升(?P<value>\d+(?:\.\d+)?)点",
        subject="Lucia Break Dark flat penetration force",
    )
    break_dark_total_cap = force_cap_base + force_cap_skill_coefficient * special_level
    extra_force_cap = break_dark_total_cap - force_flat
    force_scaling = PanelStatDerivedValue(
        source_character_id=LUCIA_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_HP,
        coefficient=Resolved(
            (force_per_hp_base + force_skill_coefficient * special_level) / hp_step
        ),
        cap_max=Resolved(extra_force_cap),
    )
    break_dark_source = source_for(
        LUCIA_ID,
        "ex-special:break-dark-force",
        EffectSourceType.SKILL,
        "强化特殊技：死神协奏曲·破晓·破暗贯穿力",
        ex_text,
    )
    break_dark_rule = _rule(
        "ex-special:break-dark-penetration-force",
        break_dark_source,
        "破暗：全队贯穿力提升",
        ex_text,
        RuleEligibility.ELIGIBLE,
        condition_ids=(BREAK_DARK_ACTIVE,),
        diagnostics=(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId(
                    "missing-data:character:1451:ex-special:energy-cost"
                ),
                kind=DiagnosticKind.MISSING_DATA,
                message=(
                    "The EX Special raw record contains an energy-cost field with "
                    "no numeric value; this static damage calculator does not "
                    "model energy balance or move availability."
                ),
                blocking=False,
                original_text=ex_text,
            ),
        ),
        effects=(
            _modifier(
                "ex-special:break-dark-penetration-force-base",
                break_dark_source,
                CalculationNode.PENETRATION_FORCE_BONUS,
                Resolved(force_flat),
                target=EffectTarget.TEAM,
                filters=(DamageTypeFilter(DamageType.PENETRATION),),
            ),
            _modifier(
                "ex-special:break-dark-penetration-force-from-initial-hp",
                break_dark_source,
                CalculationNode.PENETRATION_FORCE_BONUS,
                force_scaling,
                target=EffectTarget.TEAM,
                filters=(DamageTypeFilter(DamageType.PENETRATION),),
            ),
        ),
    )
    rules.append(break_dark_rule)

    chorus_final_hp_multiplier_value = _calc_skill_formula(
        ex_text,
        r"根据最大生命值的<color=[^>]+>\{CAL:(?P<base>[\d.]+)\+AvatarSkillLevel\((?P<skill_ref>\d+)\)\*(?P<level_coefficient>[\d.]+),100,2\}%</color>额外提升最后一段攻击的伤害",
        skill_level=special_level,
        divisor=1.0,
        subject="Lucia Chorus current-max-HP final-hit multiplier",
    )
    chorus_hp_source = source_for(
        LUCIA_ID,
        "chorus:final-hit-max-hp",
        EffectSourceType.SKILL,
        "合唱末段攻击的最大生命值追加伤害",
        ex_text,
    )
    chorus_hp_templates: list[DirectDamageEventTemplate] = []
    chorus_hp_derived: list[DerivedDamageEventTemplateRef] = []
    chorus_hp_effects: list[EventCreationEffect] = []
    chorus_hp_multiplier = FixedMultiplier(Resolved(chorus_final_hp_multiplier_value))
    for key, move_id, move_label, skill_group, damage_tags in _CHORUS_FINAL_HP_COMPONENTS:
        effect_id = (
            _EX_HP_COMPONENT_EFFECT_ID
            if key == "ex-special-chorus-hp-final-hit"
            else _ULTIMATE_FINAL_HP_EFFECT_ID
            if key == "ultimate-chorus-hp-finisher"
            else EffectId(f"effect:character:1451:chorus-hp-final-hit:{key}")
        )
        template = _direct_template(
            key=key,
            label=f"{move_label}（末段生命值追加伤害）",
            move_id=move_id,
            skill_group=skill_group,
            damage_tags=damage_tags,
            base_source=CurrentMaxHPValueSource(LUCIA_ID),
            source_rule_item_id=_CHORUS_FINAL_HP_RULE_ID,
        )
        filters = [
            DamageDealerFilter(LUCIA_ID),
            DamageTypeFilter(DamageType.DIRECT),
            MoveIdFilter(move_id),
            NotFilter(CreatedByEffectFilter(effect_id)),
        ]
        if move_id == ULTIMATE_CHORUS_MOVE_ID:
            # Only the raw stop-time Ultimate damage entry receives the final
            # max-HP component. A separately selectable collision entry does not.
            filters.append(
                EventTemplateIdFilter(
                    "template:character:1451:ultimate-charge-armor-finisher:main"
                )
            )
        effect = EventCreationEffect(
            rule=EffectRule(
                effect_id=effect_id,
                source=chorus_hp_source,
                owner=LUCIA_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=tuple(filters),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=template.ref.template_id,
            ),
        )
        chorus_hp_templates.append(template)
        chorus_hp_effects.append(effect)
        chorus_hp_derived.append(
            DerivedDamageEventTemplateRef(
                template=template.ref,
                multiplier=chorus_hp_multiplier,
            )
        )
    rules.append(
        _rule(
            "ex-special:chorus-hp-final-hit",
            chorus_hp_source,
            "合唱：末段攻击的最大生命值追加伤害",
            ex_text,
            RuleEligibility.ELIGIBLE,
            effects=tuple(chorus_hp_effects),
        )
    )
    templates.extend(chorus_hp_templates)

    # The Ultimate has an instant stop-time hit and one collision hit. Neither
    # event's damage uses its movement duration as a repeat-count input.
    ultimate_raw = _raw_move(raw_moves, "终结技：进击，大铠甲！")
    ultimate_collision_value = _raw_curve(
        ultimate_raw,
        "突进单次撞击伤害倍率",
        "1451024",
        effective_skill_level(config, SkillGroup.ULTIMATE),
    )
    if ultimate_collision_value is None:
        collision_multiplier = Unresolved(
            reason=UnresolvedReason.MISSING_DATA,
            notes="Lucia Ultimate source curve 1451024 is missing.",
            original_text="突进单次撞击伤害倍率",
        )
        diagnostics.append(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId("data:character:1451:ultimate-rush-hit-multiplier"),
                kind=DiagnosticKind.MISSING_DATA,
                message="Lucia Ultimate source curve 1451024 is missing.",
                blocking=True,
                original_text="突进单次撞击伤害倍率",
            )
        )
    else:
        collision_multiplier = FixedMultiplier(Resolved(ultimate_collision_value / 100.0))
    collision_template = _direct_template(
        key="ultimate-rush-hit",
        label="终结技：进击，大铠甲！（单次突进撞击）",
        move_id=ULTIMATE_RUSH_HIT_MOVE_ID,
        skill_group=SkillGroup.ULTIMATE,
        damage_tags=_ULTIMATE,
    )
    collision_variant = MultiplierVariant(
        variant_id=MultiplierVariantId(
            "variant:character:1451:ultimate-charge-armor-single-collision"
        ),
        label="突进单次撞击伤害倍率",
        parameter_name="突进单次撞击伤害倍率",
        multiplier=collision_multiplier,
    )
    collision_entry = MoveCalculationEntry(
        entry_id=MoveEntryId(
            "move-entry:character:1451:ultimate-charge-armor-single-collision"
        ),
        character_id=LUCIA_ID,
        move_id=ULTIMATE_RUSH_HIT_MOVE_ID,
        display_name="终结技：进击，大铠甲！（单次突进撞击）",
        original_text=(
            f"{ultimate_raw.description}\n"
            "本条只结算原文突进单次撞击伤害倍率一次；终结技瞬发伤害另选。"
        ),
        skill_group=SkillGroup.ULTIMATE,
        damage_tags=_ULTIMATE,
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(collision_variant,),
        main_damage_event=collision_template.ref,
    )
    entries.append(collision_entry)
    templates = [*templates, collision_template]

    c1 = _mindscape(raw_record, 1)
    c1_source = source_for(
        LUCIA_ID,
        "cinema1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    c1_resistance_ignore = _ratio(
        c1.description,
        r"造成伤害时无视敌人(?P<value>\d+(?:\.\d+)?)%全属性伤害抗性",
        subject="Lucia Cinema 1 All-Element resistance ignore",
    )
    c1_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 1
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema1:dream-song-resistance-ignore",
            c1_source,
            "1影：巡梦童谣全属性抗性无视",
            c1.description,
            c1_eligibility,
            condition_ids=(DREAM_SONG_ACTIVE,),
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        "unsupported:character:1451:cinema1:decibel-gain"
                    ),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message=(
                        "Cinema 1's 5% decibel-gain effect and Echo stack refresh "
                        "are not represented by the static damage calculator."
                    ),
                    blocking=False,
                    original_text=c1.description,
                ),
            ),
            effects=(
                _modifier(
                    "cinema1:dream-song-resistance-ignore",
                    c1_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(c1_resistance_ignore),
                    target=EffectTarget.TEAM,
                    filters=(
                        AnyFilter(
                            (
                                DamageTypeFilter(DamageType.DIRECT),
                                DamageTypeFilter(DamageType.PENETRATION),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    c2 = _mindscape(raw_record, 2)
    c2_source = source_for(
        LUCIA_ID,
        "cinema2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    c2_chorus_bonus = _ratio(
        c2.description,
        r"\[合唱\]</color>造成的伤害提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Lucia Cinema 2 Chorus damage bonus",
    )
    c2_penetration_bonus = _ratio(
        c2.description,
        r"额外获得贯穿伤害提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Lucia Cinema 2 Break Dark penetration damage bonus",
    )
    c2_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 2
        else RuleEligibility.INELIGIBLE
    )
    rules.append(
        _rule(
            "cinema2:chorus-damage-in-spring-curtain",
            c2_source,
            "2影：以太帷幕·涌泉内合唱增伤",
            c2.description,
            c2_eligibility,
            condition_ids=(SPRING_CURTAIN_ACTIVE,),
            effects=(
                _modifier(
                    "cinema2:chorus-damage-in-spring-curtain",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c2_chorus_bonus),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(LUCIA_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        AnyFilter(
                            (
                                *(MoveIdFilter(item) for item in LUCIA_CHORUS_MOVE_IDS),
                                CreatedByEffectFilter(EffectId(CORE_ADDITIONAL_ATTACK_EFFECT_ID)),
                            )
                        ),
                    ),
                ),
            ),
        )
    )
    rules.append(
        _rule(
            "cinema2:break-dark-penetration-damage",
            c2_source,
            "2影：涌泉内破暗角色贯穿伤害提升",
            c2.description,
            c2_eligibility,
            condition_ids=(SPRING_CURTAIN_ACTIVE, BREAK_DARK_ACTIVE),
            effects=(
                _modifier(
                    "cinema2:break-dark-penetration-damage",
                    c2_source,
                    CalculationNode.PENETRATION_DAMAGE_BONUS,
                    Resolved(c2_penetration_bonus),
                    target=EffectTarget.TEAM,
                    filters=(DamageTypeFilter(DamageType.PENETRATION),),
                ),
            ),
        )
    )

    for level in (3, 5):
        mindscape = _mindscape(raw_record, level)
        source = source_for(
            LUCIA_ID,
            f"cinema{level}",
            EffectSourceType.CINEMA,
            f"{level}影：{mindscape.name}",
            mindscape.description,
        )
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                source,
                f"{level}影：{mindscape.name}",
                mindscape.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= level
                else RuleEligibility.INELIGIBLE,
            )
        )

    c4 = _mindscape(raw_record, 4)
    c4_source = source_for(
        LUCIA_ID,
        "cinema4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    rules.append(
        _rule(
            "cinema4:curtain-decibel",
            c4_source,
            f"4影：{c4.name}（喧响值）",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            diagnostics=(
                CalculationDiagnostic(
                    diagnostic_id=DiagnosticId(
                        "unsupported:character:1451:cinema4:decibel-gain"
                    ),
                    kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
                    message=(
                        "Cinema 4's 100-decibel team resource effect is not "
                        "represented by the static damage calculator."
                    ),
                    blocking=False,
                    original_text=c4.description,
                ),
            ),
        )
    )

    c6 = _mindscape(raw_record, 6)
    c6_source = source_for(
        LUCIA_ID,
        "cinema6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    c6_eligibility = (
        RuleEligibility.ELIGIBLE
        if config.cinema_level >= 6
        else RuleEligibility.INELIGIBLE
    )
    c6_attack_bonus = _ratio(
        c6.description,
        r"根据自身初始最大生命值的(?P<value>\d+(?:\.\d+)?)%提升自身攻击力",
        subject="Lucia Cinema 6 initial-HP attack bonus",
    )
    c6_crit_damage = _ratio(
        c6.description,
        r"造成暴击时暴击伤害提升(?P<value>\d+(?:\.\d+)?)%",
        subject="Lucia Cinema 6 Chorus crit-damage bonus",
    )
    c6_chorus_filters = (
        DamageDealerFilter(LUCIA_ID),
        DamageTypeFilter(DamageType.DIRECT),
        AnyFilter(
            (
                *(MoveIdFilter(item) for item in LUCIA_CHORUS_MOVE_IDS),
                CreatedByEffectFilter(EffectId(CORE_ADDITIONAL_ATTACK_EFFECT_ID)),
            )
        ),
    )
    c6_guaranteed_crit = GuaranteedCritEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:character:1451:cinema6:chorus-guaranteed-crit"),
            source=c6_source,
            owner=LUCIA_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=c6_chorus_filters,
        )
    )
    rules.append(
        _rule(
            "cinema6:veil-chorus-crit-and-attack",
            c6_source,
            "6影：帷幕内合唱必暴、暴伤提升与生命转攻击",
            c6.description,
            c6_eligibility,
            condition_ids=(ANY_ETHER_CURTAIN_ACTIVE,),
            effects=(
                _modifier(
                    "cinema6:initial-hp-attack",
                    c6_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    PanelStatDerivedValue(
                        source_character_id=LUCIA_ID,
                        source_node=CalculationNode.CHARACTER_INITIAL_HP,
                        coefficient=Resolved(c6_attack_bonus),
                    ),
                    target=EffectTarget.SELF,
                ),
                c6_guaranteed_crit,
                _modifier(
                    "cinema6:chorus-crit-damage",
                    c6_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c6_crit_damage),
                    target=EffectTarget.TEAM,
                    filters=c6_chorus_filters,
                ),
            ),
        )
    )

    anomaly_entries, anomaly_templates = _anomaly_disorder_pair(raw_record)
    entries.extend(anomaly_entries)
    templates.extend(anomaly_templates)
    derived_refs = (*chorus_hp_derived, follow_up_derived)

    return CharacterCalculationDefinition(
        character_id=LUCIA_ID,
        role=CharacterRole.SUPPORT,
        base_element=Element.ETHER,
        source=source_for(
            LUCIA_ID,
            "raw-record",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            raw_record.source_url,
        ),
        move_entries=tuple(entries),
        rule_items=tuple(rules),
        scenario_conditions=_unique_conditions(conditions),
        scenario_parameters=(),
        damage_event_templates=tuple(templates),
        independent_derived_damage_events=derived_refs,
        diagnostics=tuple(diagnostics),
    )


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(LUCIA_ID))


__all__ = ["compile_lucia", "load_raw_record"]
