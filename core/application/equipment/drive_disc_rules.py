"""Reviewed damage-relevant Drive Disc rule compilation.

Every branch corresponds to one reviewed family in
``drive_disc_reviewed.py``.  This is intentionally deterministic authoring,
not natural-language parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.application.element_scope import element_scope_filter
from core.application.ids import RuleItemId, ScenarioConditionId
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import ConditionResolution, ScenarioCondition
from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterRole,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    DynamicIdentity,
    DynamicIdentityCondition,
    DynamicIdentityFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    EquipmentOwnerCapabilities,
    EventSelector,
    ModifierEffect,
    ModifierResult,
    PanelStatThresholdCondition,
    Resolved,
    RuleSource,
    RuleSourceId,
    RuleStackCondition,
    SkillGroup,
    SkillGroupFilter,
    SnapshotRule,
)

from .drive_disc_reviewed import DriveDiscReviewedMapping
from .drive_disc import DriveDiscRawRecord


@dataclass(frozen=True, slots=True)
class CompiledDriveDiscRules:
    rule_items: tuple[CalculationRuleItem, ...]
    scenario_conditions: tuple[ScenarioCondition, ...]


def _token(owner: CharacterId) -> str:
    return str(owner).replace(":", "_")


def _rule_id(
    raw: DriveDiscRawRecord,
    owner: CharacterId,
    pieces: int,
    suffix: str,
) -> RuleItemId:
    return RuleItemId(f"rule:{raw.set_id}:owner:{_token(owner)}:{pieces}pc:{suffix}")


def _effect_id(raw: DriveDiscRawRecord, owner: CharacterId, suffix: str) -> EffectId:
    return EffectId(f"effect:{raw.set_id}:owner:{_token(owner)}:{suffix}")


def _condition(
    raw: DriveDiscRawRecord,
    owner: CharacterId,
    suffix: str,
    label: str,
) -> tuple[ScenarioConditionId, ScenarioCondition]:
    condition_id = ScenarioConditionId(
        f"condition:{raw.set_id}:owner:{_token(owner)}:{suffix}"
    )
    return condition_id, ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=raw.four_piece_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _source(raw: DriveDiscRawRecord, pieces: int) -> RuleSource:
    text = raw.two_piece_text if pieces == 2 else raw.four_piece_text
    return RuleSource(
        source_id=RuleSourceId(f"{raw.set_id}:{pieces}pc"),
        source_type=EffectSourceType.DRIVE_DISC,
        label=f"{raw.name}·{pieces}件套",
        raw_text=text,
    )


def _effect(
    raw: DriveDiscRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    node: CalculationNode,
    value: float,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
    wearer_damage: bool = False,
    trigger: EventSelector | None = None,
) -> ModifierEffect:
    if wearer_damage:
        if condition is not None:
            raise ValueError("wearer damage helper owns its identity condition")
        condition = DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER)
    return ModifierEffect(
        rule=EffectRule(
            effect_id=_effect_id(raw, owner, suffix),
            source=source,
            owner=owner,
            target=target,
            snapshot_rule=SnapshotRule.LIVE,
            trigger=trigger,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(node, operation, Resolved(value)),
    )


def _rule(
    raw: DriveDiscRawRecord,
    owner: CharacterId,
    pieces: int,
    suffix: str,
    label: str,
    eligibility: RuleEligibility,
    effects: tuple[ModifierEffect, ...],
    *,
    condition_ids: tuple[ScenarioConditionId, ...] = (),
    stack: tuple[int, int, int] | None = None,
    non_stacking_group_id: str | None = None,
) -> CalculationRuleItem:
    current, minimum, maximum = stack or (None, None, None)
    return CalculationRuleItem(
        rule_id=_rule_id(raw, owner, pieces, suffix),
        owner=owner,
        source=_source(raw, pieces),
        display_name=f"{raw.name}·{label}",
        original_text=(raw.two_piece_text if pieces == 2 else raw.four_piece_text),
        eligibility=eligibility,
        condition_ids=condition_ids,
        effects=effects,
        stack_count=current,
        stack_min=minimum,
        stack_max=maximum,
        non_stacking_group_id=non_stacking_group_id,
    )


def _eligible(
    pieces: int,
    required: int,
    capabilities: EquipmentOwnerCapabilities,
    *,
    role: CharacterRole | None = None,
    element: Element | None = None,
    any_tags: tuple[DamageTag, ...] = (),
    any_groups: tuple[SkillGroup, ...] = (),
) -> RuleEligibility:
    if pieces < required:
        return RuleEligibility.INELIGIBLE
    if role is not None and capabilities.role is not role:
        return RuleEligibility.INELIGIBLE
    if element is not None and not capabilities.can_produce_element(element):
        return RuleEligibility.INELIGIBLE
    if any_tags and not any(capabilities.can_produce_tag(tag) for tag in any_tags):
        return RuleEligibility.INELIGIBLE
    if any_groups and not any(
        capabilities.can_use_skill_group(group) for group in any_groups
    ):
        return RuleEligibility.INELIGIBLE
    return RuleEligibility.ELIGIBLE


def _tag_scope(*tags: DamageTag):
    return (AnyFilter(tuple(DamageTagFilter(tag) for tag in tags)),)


def compile_reviewed_drive_disc_rules(
    raw: DriveDiscRawRecord,
    mapping: DriveDiscReviewedMapping,
    piece_count: int,
    owner: CharacterId,
    capabilities: EquipmentOwnerCapabilities,
) -> CompiledDriveDiscRules:
    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []
    two_source = _source(raw, 2)
    four_source = _source(raw, 4)

    def condition(suffix: str, label: str):
        condition_id, item = _condition(raw, owner, suffix, label)
        conditions.append(item)
        return condition_id

    def add(
        pieces: int,
        suffix: str,
        label: str,
        effects: tuple[ModifierEffect, ...],
        *,
        condition_ids=(),
        stack=None,
        eligibility: RuleEligibility | None = None,
        non_stacking: bool = False,
    ) -> CalculationRuleItem:
        item = _rule(
            raw,
            owner,
            pieces,
            suffix,
            label,
            eligibility or _eligible(piece_count, pieces, capabilities),
            effects,
            condition_ids=tuple(condition_ids),
            stack=stack,
            non_stacking_group_id=(
                f"{raw.set_id}:{pieces}pc:{suffix}" if non_stacking else None
            ),
        )
        rules.append(item)
        return item

    if mapping.two_piece_rule_family == "shadow-2pc":
        add(
            2,
            "follow-up-dash-damage",
            "追加攻击与冲刺攻击伤害",
            (
                _effect(
                    raw,
                    owner,
                    two_source,
                    "2pc-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.15,
                    filters=_tag_scope(
                        DamageTag.FOLLOW_UP_ATTACK, DamageTag.DASH_ATTACK
                    ),
                    wearer_damage=True,
                ),
            ),
        )
    elif mapping.two_piece_rule_family == "dawns-bloom-2pc":
        add(
            2,
            "basic-damage",
            "普通攻击伤害",
            (
                _effect(
                    raw,
                    owner,
                    two_source,
                    "2pc-basic",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.15,
                    filters=(DamageTagFilter(DamageTag.BASIC_ATTACK),),
                    wearer_damage=True,
                ),
            ),
        )

    family = mapping.four_piece_rule_family
    base_eligibility = _eligible(piece_count, 4, capabilities)
    if family is None:
        return CompiledDriveDiscRules(tuple(rules), tuple(conditions))

    if family == "woodpecker":
        maximum = sum(
            capabilities.can_produce_tag(tag)
            for tag in (
                DamageTag.BASIC_ATTACK,
                DamageTag.DODGE_COUNTER,
                DamageTag.EX_SPECIAL_ATTACK,
            )
        )
        add(
            4,
            "attack-stacks",
            "暴击触发攻击力",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.09,
                ),
            ),
            stack=(maximum, 0, maximum),
            eligibility=base_eligibility if maximum else RuleEligibility.INELIGIBLE,
        )
    elif family == "puffer":
        eligibility = _eligible(
            piece_count, 4, capabilities, any_tags=(DamageTag.ULTIMATE,)
        )
        add(
            4,
            "ultimate-damage",
            "终结技伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "ultimate-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.20,
                    filters=(DamageTagFilter(DamageTag.ULTIMATE),),
                    wearer_damage=True,
                ),
            ),
            eligibility=eligibility,
        )
        active = condition("ultimate-attack-active", "河豚电音：终结技攻击力增益已触发")
        add(
            4,
            "ultimate-attack",
            "终结技触发攻击力",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "ultimate-attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.15,
                ),
            ),
            condition_ids=(active,),
            eligibility=eligibility,
        )
    elif family == "hormone":
        active = condition(
            "active-character-attack", "激素朋克：当前操作攻击力增益已生效"
        )
        add(
            4,
            "active-character-attack",
            "当前操作攻击力",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.25,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "swing":
        active = condition("team-damage-active", "摇摆爵士：全队增伤已触发")
        eligibility = _eligible(
            piece_count,
            4,
            capabilities,
            any_groups=(SkillGroup.CHAIN_ATTACK, SkillGroup.ULTIMATE),
        )
        add(
            4,
            "team-damage",
            "全队伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "team-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.15,
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(active,),
            eligibility=eligibility,
            non_stacking=True,
        )
    elif family == "chaos-jazz":
        element_filters = (
            AnyFilter((ElementFilter(Element.FIRE), ElementFilter(Element.ELECTRIC))),
        )
        add(
            4,
            "fire-electric-damage",
            "火与电属性伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "fire-electric",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.15,
                    filters=element_filters,
                    wearer_damage=True,
                ),
            ),
        )
        active = condition("off-field-skill-damage", "混沌爵士：后场招式增伤有效")
        add(
            4,
            "off-field-skill-damage",
            "后场强化特殊技与支援攻击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "off-field-skill",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.20,
                    filters=_tag_scope(DamageTag.EX_SPECIAL_ATTACK, DamageTag.ASSIST),
                    wearer_damage=True,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "proto-punk":
        active = condition("team-damage-active", "原始朋克：全队增伤已触发")
        add(
            4,
            "team-damage",
            "全队伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "team-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.15,
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(active,),
            non_stacking=True,
        )
    elif family == "inferno":
        active = condition("burn-crit-active", "炎狱重金属：命中灼烧目标暴击增益已触发")
        add(
            4,
            "burn-crit",
            "灼烧目标暴击率",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.28,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "chaos-metal":
        add(
            4,
            "base-crit-damage",
            "基础暴击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "base-crit-damage",
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    0.20,
                ),
            ),
        )
        add(
            4,
            "corruption-crit-damage",
            "侵蚀触发暴击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "stack-crit-damage",
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    0.055,
                ),
            ),
            stack=(6, 0, 6),
        )
    elif family == "thunder":
        active = condition("shock-attack-active", "雷暴重金属：场上存在感电敌人")
        add(
            4,
            "shock-attack",
            "感电敌人攻击力",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.28,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "polar":
        filters = _tag_scope(DamageTag.BASIC_ATTACK, DamageTag.DASH_ATTACK)
        add(
            4,
            "basic-dash-damage",
            "普通攻击与冲刺攻击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "base-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.20,
                    filters=filters,
                    wearer_damage=True,
                ),
            ),
        )
        active = condition(
            "freeze-extra-active", "极地重金属：冻结或碎冰额外增伤已触发"
        )
        add(
            4,
            "freeze-extra",
            "冻结或碎冰额外伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "extra-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.20,
                    filters=filters,
                    wearer_damage=True,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "fanged":
        active = condition("assault-target-active", "獠牙重金属：目标强击增伤已触发")
        add(
            4,
            "assault-target-damage",
            "强击目标伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "target-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.35,
                    wearer_damage=True,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "branch-blade":
        add(
            4,
            "mastery-crit-damage",
            "异常掌控阈值暴击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "mastery-crit-damage",
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    0.30,
                    condition=PanelStatThresholdCondition(
                        owner, CalculationNode.CHARACTER_INITIAL_ANOMALY_MASTERY, 115
                    ),
                ),
            ),
        )
        active = condition("freeze-crit-active", "折枝剑歌：冻结或碎冰暴击率增益已触发")
        add(
            4,
            "freeze-crit",
            "冻结或碎冰暴击率",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "freeze-crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.12,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "astral-voice":
        active = condition(
            "quick-assist-entry-active", "静听嘉音：快速支援入场增伤已触发"
        )
        effect = _effect(
            raw,
            owner,
            four_source,
            "entry-damage",
            CalculationNode.DAMAGE_NORMAL_BONUS,
            0.08,
            target=EffectTarget.TEAM,
            filters=(DynamicIdentityFilter(DynamicIdentity.SUPPORT_ENTRY_CHARACTER),),
            trigger=EventSelector(BattleEventKind.SUPPORT_ENTRY),
        )
        add(
            4,
            "entry-damage",
            "快速支援入场角色伤害",
            (effect,),
            condition_ids=(active,),
            stack=(3, 0, 3),
            non_stacking=True,
        )
    elif family == "shadow-4pc":
        tags = (DamageTag.FOLLOW_UP_ATTACK, DamageTag.DASH_ATTACK)
        eligibility = _eligible(piece_count, 4, capabilities, any_tags=tags)
        add(
            4,
            "attack-crit-stacks",
            "追加攻击与冲刺攻击触发增益",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.04,
                ),
                _effect(
                    raw,
                    owner,
                    four_source,
                    "crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.04,
                ),
            ),
            stack=(3, 0, 3),
            eligibility=eligibility,
        )
    elif family == "phaethon":
        active = condition("ex-trigger-active", "法厄同之歌：强化特殊技触发增益已生效")
        add(
            4,
            "anomaly-proficiency",
            "异常精通",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "anomaly-proficiency",
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    45,
                ),
            ),
            condition_ids=(active,),
        )
        other = condition("other-ex-ether-active", "法厄同之歌：其他角色发动强化特殊技")
        add(
            4,
            "ether-damage",
            "其他角色触发以太伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "ether-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.25,
                    filters=(element_scope_filter(Element.ETHER),),
                    wearer_damage=True,
                ),
            ),
            condition_ids=(other,),
        )
    elif family == "yunkui":
        stack_rule = add(
            4,
            "crit-stacks",
            "招式触发暴击率",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.04,
                ),
            ),
            stack=(3, 0, 3),
        )
        full_stack_rule = add(
            4,
            "full-stack-penetration",
            "满层贯穿伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "penetration",
                    CalculationNode.PENETRATION_DAMAGE_BONUS,
                    0.10,
                    filters=(DamageTypeFilter(DamageType.PENETRATION),),
                    wearer_damage=True,
                ),
            ),
            eligibility=base_eligibility,
            condition_ids=(),
        )
        # The full-stack effect is tied to the same stack selection, not a second boolean.
        assert all(
            isinstance(effect, ModifierEffect) for effect in full_stack_rule.effects
        )
        rules[-1] = replace(
            full_stack_rule,
            effects=tuple(
                _replace_effect_condition(
                    effect,
                    RuleStackCondition(str(stack_rule.rule_id), 3),
                )
                for effect in full_stack_rule.effects
                if isinstance(effect, ModifierEffect)
            ),
        )
    elif family == "summit":
        active = condition("team-crit-damage-active", "山大王：全队暴击伤害增益已触发")
        eligibility = _eligible(piece_count, 4, capabilities, role=CharacterRole.STUN)
        add(
            4,
            "team-crit-damage",
            "全队暴击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "base-team-crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    0.15,
                    target=EffectTarget.TEAM,
                ),
                _effect(
                    raw,
                    owner,
                    four_source,
                    "threshold-team-crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    0.15,
                    target=EffectTarget.TEAM,
                    condition=PanelStatThresholdCondition(
                        owner, CalculationNode.CHARACTER_CURRENT_CRIT_RATE, 0.50
                    ),
                ),
            ),
            condition_ids=(active,),
            eligibility=eligibility,
            non_stacking=True,
        )
    elif family == "dawns-bloom-4pc":
        filters = (DamageTagFilter(DamageTag.BASIC_ATTACK),)
        add(
            4,
            "basic-damage",
            "普通攻击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "base-basic",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.20,
                    filters=filters,
                    wearer_damage=True,
                ),
            ),
        )
        active = condition("extra-basic-active", "拂晓生花：额外普通攻击增伤已触发")
        eligibility = _eligible(piece_count, 4, capabilities, role=CharacterRole.ATTACK)
        add(
            4,
            "extra-basic",
            "额外普通攻击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "extra-basic",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.20,
                    filters=filters,
                    wearer_damage=True,
                ),
            ),
            condition_ids=(active,),
            eligibility=eligibility,
        )
    elif family == "moonlight":
        active = condition("team-damage-active", "月光骑士颂：全队增伤已触发")
        eligibility = _eligible(
            piece_count, 4, capabilities, role=CharacterRole.SUPPORT
        )
        add(
            4,
            "team-damage",
            "全队伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "team-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.18,
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(active,),
            eligibility=eligibility,
            non_stacking=True,
        )
    elif family == "white-water":
        veil = condition("veil-crit-active", "沧浪行歌：处于或刚离开以太帷幕")
        add(
            4,
            "veil-crit",
            "以太帷幕暴击率",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "veil-crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.10,
                ),
            ),
            condition_ids=(veil,),
        )
        opened = condition("veil-opened-active", "沧浪行歌：开启或延长帷幕增益已触发")
        eligibility = _eligible(piece_count, 4, capabilities, role=CharacterRole.ATTACK)
        add(
            4,
            "veil-opened",
            "开启或延长帷幕增益",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "extra-crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.10,
                ),
                _effect(
                    raw,
                    owner,
                    four_source,
                    "attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.10,
                ),
            ),
            condition_ids=(opened,),
            eligibility=eligibility,
        )
    elif family == "shining-aria":
        basic = condition(
            "basic-proficiency-active", "流光咏叹：普通攻击异常精通增益已触发"
        )
        add(
            4,
            "basic-proficiency",
            "普通攻击触发异常精通",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "proficiency",
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    36,
                ),
            ),
            condition_ids=(basic,),
        )
        stun = condition("stun-damage-active", "流光咏叹：敌人进入失衡增伤已触发")
        add(
            4,
            "stun-damage",
            "敌人进入失衡伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.25,
                    wearer_damage=True,
                ),
            ),
            condition_ids=(stun,),
        )
    elif family == "bunny":
        eligibility = _eligible(
            piece_count, 4, capabilities, role=CharacterRole.DEFENSE
        )
        add(
            4,
            "team-damage-stacks",
            "全队伤害叠层",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "team-damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.06,
                    target=EffectTarget.TEAM,
                ),
            ),
            stack=(3, 0, 3),
            eligibility=eligibility,
            non_stacking=True,
        )
    elif family == "chained-notes":
        discharge = condition(
            "discharge-proficiency-active", "囚徒手记：异放异常精通增益已触发"
        )
        add(
            4,
            "discharge-proficiency",
            "异放触发异常精通",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "proficiency",
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    48,
                ),
            ),
            condition_ids=(discharge,),
        )
        freeze = condition(
            "freeze-anomaly-active", "囚徒手记：冻结触发异常伤害增益已生效"
        )
        add(
            4,
            "freeze-anomaly-damage",
            "冻结触发异常与紊乱伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "anomaly",
                    CalculationNode.ANOMALY_DAMAGE_BONUS,
                    0.16,
                    filters=(DamageTypeFilter(DamageType.ANOMALY),),
                    wearer_damage=True,
                ),
                _effect(
                    raw,
                    owner,
                    four_source,
                    "disorder",
                    CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                    0.16,
                    filters=(DamageTypeFilter(DamageType.DISORDER),),
                    wearer_damage=True,
                ),
            ),
            condition_ids=(freeze,),
        )
    elif family == "wuthering":
        add(
            4,
            "proficiency-stacks",
            "强化特殊技异常精通",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "proficiency",
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    25,
                ),
            ),
            stack=(2, 0, 2),
        )
        weathering = condition(
            "weathering-damage-active", "呼啸沙龙：风化触发增伤已生效"
        )
        add(
            4,
            "weathering-damage",
            "风化触发伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.18,
                    wearer_damage=True,
                ),
            ),
            condition_ids=(weathering,),
        )
    elif family == "sky-ablaze":
        eligibility = _eligible(piece_count, 4, capabilities, element=Element.ETHER)
        add(
            4,
            "ether-crit-damage",
            "以太属性暴击伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "ether-crit",
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    0.30,
                    filters=(element_scope_filter(Element.ETHER),),
                    wearer_damage=True,
                ),
            ),
            eligibility=eligibility,
        )
        active = condition("attack-active", "拂晓行纪：攻击力增益已触发")
        add(
            4,
            "attack",
            "强化特殊技或终结技攻击力",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "attack",
                    CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    0.10,
                ),
            ),
            condition_ids=(active,),
        )
    elif family == "feathered-fate":
        active = condition("panel-buff-active", "谶羽之誓：异常精通增益有效")
        add(
            4,
            "anomaly-proficiency",
            "异常精通",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "proficiency",
                    CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    50,
                ),
            ),
            condition_ids=(active,),
        )
        luminance = _eligible(piece_count, 4, capabilities, element=Element.LUMINANCE)
        add(
            4,
            "luminance-anomaly",
            "流明属性异常伤害",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "luminance-anomaly",
                    CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
                    0.15,
                    filters=(DamageSubtypeFilter(DamageSubtype.LUMINANCE),),
                    wearer_damage=True,
                ),
            ),
            condition_ids=(active,),
            eligibility=luminance,
        )
    elif family == "thorned-rose":
        add(
            4,
            "damage",
            "伤害提升",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "damage",
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    0.15,
                    wearer_damage=True,
                ),
            ),
        )
        add(
            4,
            "defense-1000-crit",
            "初始防御1000暴击率",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "crit-1000",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.08,
                    condition=PanelStatThresholdCondition(
                        owner, CalculationNode.CHARACTER_INITIAL_DEFENSE, 1000
                    ),
                ),
            ),
        )
        add(
            4,
            "defense-1800-crit",
            "初始防御1800额外暴击率",
            (
                _effect(
                    raw,
                    owner,
                    four_source,
                    "crit-1800",
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    0.08,
                    condition=PanelStatThresholdCondition(
                        owner, CalculationNode.CHARACTER_INITIAL_DEFENSE, 1800
                    ),
                ),
            ),
        )
    else:
        raise ValueError(f"unhandled reviewed Drive Disc rule family: {family}")

    return CompiledDriveDiscRules(tuple(rules), tuple(conditions))


def _replace_effect_condition(effect: ModifierEffect, condition) -> ModifierEffect:
    return replace(effect, rule=replace(effect.rule, condition=condition))


__all__ = ["CompiledDriveDiscRules", "compile_reviewed_drive_disc_rules"]
