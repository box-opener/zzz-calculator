"""Reviewed W-Engine vertical slices used by the build validation stages."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from core.application.diagnostics import CalculationDiagnostic, DiagnosticKind
from core.application.ids import DiagnosticId, RuleItemId, ScenarioConditionId
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import ConditionResolution, ScenarioCondition
from core.data.wengines.loader import load_wengine_record
from core.types import (
    BuildContributionLayer,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    AnyFilter,
    CalculationNode,
    CharacterId,
    CharacterRole,
    CharacterStat,
    DamageTag,
    DamageTagFilter,
    DynamicIdentityCondition,
    DynamicIdentity,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    ElementFilter,
    ModifierEffect,
    ModifierResult,
    Resolved,
    RuleSource,
    RuleSourceId,
    SnapshotRule,
    WEngineBuildInput,
    WEngineId,
)
from .wengine_ids import ASTRA_ID, YE_ID, WENGINE_ASTRA_ID, WENGINE_YE_ID
from .wengine_reviewed import reviewed_mapping_for


ASTRA_DAMAGE_BUFF_CONDITION_ID = ScenarioConditionId(
    "condition:wengine:14131:owner:1311:damage-buff-active"
)
YE_MINGXIN_CONDITION_ID = ScenarioConditionId(
    "condition:ye:mingxin-active"
)
# Backward-compatible semantic name for callers describing the weapon text.
YE_VEIL_ACTIVE_CONDITION_ID = YE_MINGXIN_CONDITION_ID

SIGNATURE_WENGINE_BY_CHARACTER: Mapping[CharacterId, WEngineId] = {
    ASTRA_ID: WENGINE_ASTRA_ID,
    YE_ID: WENGINE_YE_ID,
}


@dataclass(frozen=True, slots=True)
class WEngineRawTalent:
    refinement: int
    name: str
    text: str
    numeric_values: Mapping[str, float | int]

    def __post_init__(self) -> None:
        if not 1 <= self.refinement <= 5:
            raise ValueError("W-Engine talent refinement must be between 1 and 5")
        if not self.name.strip() or not self.text.strip():
            raise ValueError("W-Engine talent name and text are required")
        for key, value in self.numeric_values.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("W-Engine talent numeric keys must be non-empty")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("W-Engine talent numeric values must be numbers")
            if not math.isfinite(float(value)):
                raise ValueError("W-Engine talent numeric values must be finite")


@dataclass(frozen=True, slots=True)
class WEngineRawRecord:
    source_version: str
    source_url: str
    wengine_id: WEngineId
    name: str
    rarity: str
    specialty: CharacterRole
    icon: str
    max_level: int
    base_attack: float
    advanced_stat_name: str
    advanced_stat_value: float
    talents: tuple[WEngineRawTalent, ...]

    def __post_init__(self) -> None:
        if not self.source_version.strip() or not self.source_url.strip():
            raise ValueError("W-Engine source metadata is required")
        if not self.name.strip() or not self.icon.strip():
            raise ValueError("W-Engine display metadata is required")
        if self.rarity not in {"S", "A", "B"}:
            raise ValueError("reviewed W-Engine rarity must be S, A, or B")
        if self.max_level != 60:
            raise ValueError("Stage18-2.5 W-Engine max level must be 60")
        if not math.isfinite(self.base_attack) or not math.isfinite(
            self.advanced_stat_value
        ):
            raise ValueError("W-Engine static values must be finite")
        if tuple(item.refinement for item in self.talents) != (1, 2, 3, 4, 5):
            raise ValueError("W-Engine raw talents must contain refinements 1 through 5")


@dataclass(frozen=True, slots=True)
class WEngineBuildResolution:
    build_input: WEngineBuildInput
    raw: WEngineRawRecord
    contributions: tuple[BuildStatContribution, ...]
    rule_items: tuple[CalculationRuleItem, ...]
    scenario_conditions: tuple[ScenarioCondition, ...] = ()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    @property
    def complete(self) -> bool:
        return not any(item.blocking for item in self.diagnostics)


def load_wengine_raw_record(wengine_id: str) -> WEngineRawRecord:
    payload = load_wengine_record(wengine_id)
    try:
        catalog = payload["catalog"]
        resolved = payload["resolved_level_60"]
        details = payload["nanoka_detail_fields"]
        talents = payload["talents"]
        specialty = _role(str(payload["specialty"]))
        advanced_name = str(details["rand_property"]["name"])
        return WEngineRawRecord(
            source_version=str(payload["source_version"]),
            source_url=str(payload["source_url"]),
            wengine_id=WEngineId(f"wengine:{payload['id']}"),
            name=str(payload["name"]),
            rarity=str(payload["rarity"]),
            specialty=specialty,
            icon=str(catalog["icon"]),
            max_level=60,
            base_attack=float(resolved["base_attack"]),
            advanced_stat_name=advanced_name,
            advanced_stat_value=float(resolved["advanced_stat_value"]),
            talents=tuple(
                WEngineRawTalent(
                    refinement=int(refinement),
                    name=str(item["name"]),
                    text=str(item["text"]),
                    numeric_values=item["numeric_values"],
                )
                for refinement, item in sorted(talents.items(), key=lambda item: int(item[0]))
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid W-Engine raw record: {wengine_id}") from exc


def compile_wengine(
    build_input: WEngineBuildInput,
    *,
    equipped_character_role: CharacterRole,
) -> WEngineBuildResolution:
    raw = load_wengine_raw_record(str(build_input.wengine_id))
    if raw.wengine_id != build_input.wengine_id:
        raise ValueError("W-Engine build input and raw record IDs do not match")
    if build_input.level != raw.max_level:
        diagnostic = _diagnostic(
            str(build_input.wengine_id),
            "level",
            DiagnosticKind.MISSING_DATA,
            "Stage18-2.5 only carries reviewed max-level W-Engine values",
        )
        contributions = ()
        rules = ()
        conditions = ()
        diagnostics = (diagnostic,)
    else:
        contributions = _static_contributions(raw, build_input)
        rules, conditions = _reviewed_rules(
            raw,
            build_input,
            equipped_character_role,
        )
        diagnostics = ()
    return WEngineBuildResolution(
        build_input=build_input,
        raw=raw,
        contributions=contributions,
        rule_items=rules,
        scenario_conditions=conditions,
        diagnostics=diagnostics,
    )


def signature_wengine_id_for(character_id: CharacterId) -> WEngineId:
    try:
        return SIGNATURE_WENGINE_BY_CHARACTER[character_id]
    except KeyError as exc:
        raise ValueError(
            f"no reviewed signature W-Engine mapping for {character_id}"
        ) from exc


def astra_damage_buff_condition_id_for(owner: CharacterId) -> ScenarioConditionId:
    """Return the condition identity for one equipped Elegant Vanity instance."""

    return ScenarioConditionId(
        f"condition:wengine:14131:owner:{_owner_token(owner)}:damage-buff-active"
    )


def _static_contributions(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
) -> tuple[BuildStatContribution, ...]:
    source = BuildSource(
        source_id=str(raw.wengine_id),
        source_type=BuildSourceType.WENGINE,
        label=raw.name,
    )
    contributions = [
        BuildStatContribution(
            contribution_id=(
                f"{raw.wengine_id}:owner:{_owner_token(build_input.equipped_character_id)}"
                ":base-attack"
            ),
            source=source,
            stat=CharacterStat.ATTACK,
            layer=BuildContributionLayer.WHITE_VALUE,
            value=Resolved(raw.base_attack),
        )
    ]
    stat, layer = _advanced_stat(raw)
    contributions.append(
        BuildStatContribution(
            contribution_id=(
                f"{raw.wengine_id}:owner:{_owner_token(build_input.equipped_character_id)}"
                ":advanced-stat"
            ),
            source=source,
            stat=stat,
            layer=layer,
            value=Resolved(raw.advanced_stat_value),
        )
    )
    return tuple(contributions)


def _advanced_stat(
    raw: WEngineRawRecord,
) -> tuple[CharacterStat, BuildContributionLayer]:
    mapping = reviewed_mapping_for(raw.wengine_id)
    return mapping.advanced_stat, mapping.advanced_layer


def _reviewed_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    equipped_character_role: CharacterRole,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    eligible = raw.specialty is equipped_character_role
    eligibility = RuleEligibility.ELIGIBLE if eligible else RuleEligibility.INELIGIBLE
    talent = raw.talents[build_input.refinement - 1]
    source = RuleSource(
        source_id=RuleSourceId(f"{raw.wengine_id}:talent:{build_input.refinement}"),
        source_type=EffectSourceType.WEAPON,
        label=f"{raw.name}·{talent.name}",
        raw_text=talent.text,
    )
    effect_family = reviewed_mapping_for(raw.wengine_id).effect_family
    if effect_family == "ye-cloudcleave-radiance":
        return _ye_rules(raw, build_input, talent, source, eligibility), ()
    if effect_family == "astra-elegant-vanity":
        condition_id = astra_damage_buff_condition_id_for(
            build_input.equipped_character_id
        )
        return _astra_rules(
            raw,
            build_input,
            talent,
            source,
            eligibility,
            condition_id,
        ), (
            ScenarioCondition(
                condition_id=condition_id,
                label="玲珑妆匣增伤已触发",
                original_text="装备者消耗25点或以上能量时",
                resolution=ConditionResolution.USER_SELECTED,
                value=False,
            ),
        )
    if effect_family == "attack-steel-cushion":
        return _steel_cushion_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-brimstone":
        return _brimstone_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-deep-sea-visitor":
        return _deep_sea_visitor_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-heart-of-sword":
        return _heart_of_sword_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-defense-patrol":
        return _defense_patrol_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-resonab-3":
        return _resonab_three_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-treasure-chest":
        return _treasure_chest_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-crying-cradle":
        return _crying_cradle_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-dream-forge":
        return _dream_forge_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-song-of-noise":
        return _song_of_noise_rules(raw, build_input, talent, source, eligibility)
    raise ValueError(f"no reviewed W-Engine rule mapping for {raw.wengine_id}")


def _ye_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[CalculationRuleItem, ...]:
    values = talent.numeric_values
    owner = build_input.equipped_character_id
    physical_scope = AnyFilter(
        (
            ElementFilter(Element.PHYSICAL),
            ElementFilter(Element.LINREN),
        )
    )
    resistance_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(
                raw.wengine_id, owner, "resistance-ignore"
            ),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            filters=(physical_scope,),
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_RESISTANCE_IGNORE,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["physical_resistance_ignore"])),
        ),
    )
    veil_damage_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "veil-damage"),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["veil_damage_bonus"])),
        ),
    )
    veil_crit_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(
                raw.wengine_id, owner, "veil-crit-damage"
            ),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["veil_crit_damage_bonus"])),
        ),
    )
    # The veil condition reuses Ye's existing MINGXIN scenario condition.  It
    # is deliberately not a second W-Engine-specific state value.
    veil_rule = CalculationRuleItem(
        rule_id=RuleItemId(_instance_rule_id(raw.wengine_id, owner, "veil")),
        owner=owner,
        source=source,
        display_name=f"{raw.name}·以太帷幕效果",
        original_text=talent.text,
        eligibility=eligibility,
        condition_ids=(YE_MINGXIN_CONDITION_ID,),
        effects=(veil_damage_effect, veil_crit_effect),
    )
    resistance_rule = CalculationRuleItem(
        rule_id=RuleItemId(
            _instance_rule_id(raw.wengine_id, owner, "resistance-ignore")
        ),
        owner=owner,
        source=source,
        display_name=f"{raw.name}·物理抗性无视",
        original_text=talent.text,
        eligibility=eligibility,
        effects=(resistance_effect,),
    )
    return resistance_rule, veil_rule


def _instance_condition_id(
    raw: WEngineRawRecord,
    owner: CharacterId,
    suffix: str,
) -> ScenarioConditionId:
    return ScenarioConditionId(
        f"condition:{raw.wengine_id}:owner:{_owner_token(owner)}:{suffix}"
    )


def _condition(
    raw: WEngineRawRecord,
    owner: CharacterId,
    suffix: str,
    label: str,
    original_text: str,
) -> tuple[ScenarioConditionId, ScenarioCondition]:
    condition_id = _instance_condition_id(raw, owner, suffix)
    return condition_id, ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _wearer_modifier(
    *,
    raw: WEngineRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    path: CalculationNode,
    value: float,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, suffix),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
            filters=filters,
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=Resolved(value),
        ),
    )


def _panel_modifier(
    *,
    raw: WEngineRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    path: CalculationNode,
    value: float,
    target: EffectTarget = EffectTarget.SELF,
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, suffix),
            source=source,
            owner=owner,
            target=target,
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=Resolved(value),
        ),
    )


def _team_damage_modifier(
    *,
    raw: WEngineRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    value: float,
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, suffix),
            source=source,
            owner=owner,
            target=EffectTarget.ENEMY,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(value),
        ),
    )


def _rule(
    *,
    raw: WEngineRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    label: str,
    eligibility: RuleEligibility,
    effects: tuple[ModifierEffect, ...],
    condition_ids: tuple[ScenarioConditionId, ...] = (),
    stack_count: int | None = None,
    stack_min: int | None = None,
    stack_max: int | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(_instance_rule_id(raw.wengine_id, owner, suffix)),
        owner=owner,
        source=source,
        display_name=label,
        original_text=source.raw_text or label,
        eligibility=eligibility,
        condition_ids=condition_ids,
        effects=effects,
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
    )


def _steel_cushion_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    back_id, back_condition = _condition(
        raw,
        owner,
        "back-attack-active",
        "钢铁肉垫：从背后攻击已成立",
        "从背后攻击命中敌人",
    )
    physical_scope = (
        AnyFilter(
            (
                ElementFilter(Element.PHYSICAL),
                ElementFilter(Element.LINREN),
            )
        ),
    )
    rules = (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="physical-damage",
            label=f"{raw.name}·物理伤害提升",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="physical-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["physical_damage_bonus"]),
                    filters=physical_scope,
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="back-attack-damage",
            label=f"{raw.name}·背后攻击伤害提升",
            eligibility=eligibility,
            condition_ids=(back_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="back-attack-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["back_attack_damage_bonus"]),
                ),
            ),
        ),
    )
    return rules, (back_condition,)


def _brimstone_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    condition_id, condition = _condition(
        raw,
        owner,
        "attack-buff-active",
        "硫磺石攻击力增益已触发",
        "普通攻击、冲刺攻击或闪避反击命中敌人后获得攻击力提升",
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="attack-buff",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(talent.numeric_values["attack_percent_per_stack"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="attack-buff",
            label=f"{raw.name}·炽烈吐息攻击力增益",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(effect,),
            stack_count=int(talent.numeric_values["max_stacks"]),
            stack_min=0,
            stack_max=int(talent.numeric_values["max_stacks"]),
        ),
    ), (condition,)


def _deep_sea_visitor_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    basic_id, basic_condition = _condition(
        raw,
        owner,
        "basic-crit-buff-active",
        "深海访客：普通攻击暴击率增益已触发",
        "普通攻击命中敌人时",
    )
    dash_id, dash_condition = _condition(
        raw,
        owner,
        "dash-crit-buff-active",
        "深海访客：冲刺攻击暴击率增益已触发",
        "冲刺攻击造成冰属性伤害时",
    )
    ice_scope = (
        AnyFilter((ElementFilter(Element.ICE),)),
    )
    rules = (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ice-damage",
            label=f"{raw.name}·冰属性伤害提升",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ice-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ice_damage_bonus"]),
                    filters=ice_scope,
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="basic-crit-buff",
            label=f"{raw.name}·普通攻击暴击率增益",
            eligibility=eligibility,
            condition_ids=(basic_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="basic-crit-buff",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["basic_crit_rate_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="dash-crit-buff",
            label=f"{raw.name}·冲刺攻击暴击率增益",
            eligibility=eligibility,
            condition_ids=(dash_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="dash-crit-buff",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["dash_crit_rate_bonus"]),
                ),
            ),
        ),
    )
    return rules, (basic_condition, dash_condition)


def _heart_of_sword_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    trigger_id, trigger_condition = _condition(
        raw,
        owner,
        "anomaly-or-daze-buff-active",
        "残心青囊：异常或失衡触发的暴击率增益已生效",
        "队伍中任意角色对敌人施加属性异常效果或造成失衡时",
    )
    electric_dash = (
        DamageTagFilter(DamageTag.DASH_ATTACK),
        ElementFilter(Element.ELECTRIC),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-rate",
            label=f"{raw.name}·暴击率提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-rate",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["crit_rate_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="electric-dash-damage",
            label=f"{raw.name}·冲刺攻击电属性伤害提升",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="electric-dash-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["electric_dash_damage_bonus"]),
                    filters=electric_dash,
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="triggered-crit-rate",
            label=f"{raw.name}·触发后额外暴击率",
            eligibility=eligibility,
            condition_ids=(trigger_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="triggered-crit-rate",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["triggered_crit_rate_bonus"]),
                ),
            ),
        ),
    ), (trigger_condition,)


def _defense_patrol_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    charge_id, charge_condition = _condition(
        raw,
        owner,
        "charge-available",
        "防暴者Ⅵ型：当前招式有可消耗充能",
        "普通攻击或冲刺攻击造成以太伤害时消耗1层充能",
    )
    attack_scope = (
        AnyFilter(
            (
                DamageTagFilter(DamageTag.BASIC_ATTACK),
                DamageTagFilter(DamageTag.DASH_ATTACK),
            )
        ),
        ElementFilter(Element.ETHER),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-rate",
            label=f"{raw.name}·暴击率提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-rate",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["crit_rate_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="charged-ether-damage",
            label=f"{raw.name}·充能以太伤害提升",
            eligibility=eligibility,
            condition_ids=(charge_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="charged-ether-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ether_attack_damage_bonus"]),
                    filters=attack_scope,
                ),
            ),
        ),
    ), (charge_condition,)


def _resonab_three_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    condition_id, condition = _condition(
        raw,
        owner,
        "team-attack-buff-active",
        "「残响」-Ⅲ型：全队攻击力增益已触发",
        "发动连携技或终结技时",
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-attack-buff",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(talent.numeric_values["team_attack_percent"]),
        target=EffectTarget.TEAM,
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-attack-buff",
            label=f"{raw.name}·全队攻击力提升",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(effect,),
        ),
    ), (condition,)


def _treasure_chest_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    condition_id, condition = _condition(
        raw,
        owner,
        "ether-triggered-buff-active",
        "聚宝箱：以太伤害触发的增益已生效",
        "强化特殊技、连携技或终结技造成以太伤害时",
    )
    effect = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="all-damage-buff",
        value=float(talent.numeric_values["all_damage_bonus"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="all-damage-buff",
            label=f"{raw.name}·全队伤害提升",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(effect,),
        ),
    ), (condition,)


def _crying_cradle_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    condition_id, condition = _condition(
        raw,
        owner,
        "damage-buff-active",
        "啜泣摇篮：攻击命中后的全队增益已生效",
        "装备者攻击命中敌人时",
    )
    base = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="damage-buff-base",
        value=float(values["damage_bonus_base"]),
    )
    increment = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="damage-buff-increment",
        value=float(values["damage_bonus_per_tick"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="damage-buff-base",
            label=f"{raw.name}·基础全队伤害提升",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(base,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="damage-buff-increment",
            label=f"{raw.name}·持续期间额外伤害提升",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(increment,),
            stack_count=int(values["max_ticks"]),
            stack_min=0,
            stack_max=int(values["max_ticks"]),
        ),
    ), (condition,)


def _dream_forge_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    condition_id, condition = _condition(
        raw,
        owner,
        "veil-triggered-buff-active",
        "铸梦炉歌：以太帷幕触发的全队增益已生效",
        "当装备者开启或延长以太帷幕的持续时间时",
    )
    effect = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-damage-buff",
        value=float(talent.numeric_values["team_damage_bonus"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-buff",
            label=f"{raw.name}·全队伤害提升",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(effect,),
        ),
    ), (condition,)


def _song_of_noise_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    active_id, active_condition = _condition(
        raw,
        owner,
        "team-damage-buff-active",
        "思络成歌：全队伤害增益已生效",
        "装备者发动强化特殊技造成物理伤害时",
    )
    full_id, full_condition = _condition(
        raw,
        owner,
        "full-stacks-attack-buff-active",
        "思络成歌：2层时全队攻击力增益已生效",
        "拥有2层效果时",
    )
    damage_effect = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-damage-buff",
        value=float(values["team_damage_per_stack"]),
    )
    attack_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-attack-buff",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(values["team_attack_at_max"]),
        target=EffectTarget.TEAM,
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-buff",
            label=f"{raw.name}·全队伤害提升",
            eligibility=eligibility,
            condition_ids=(active_id,),
            effects=(damage_effect,),
            stack_count=int(values["max_stacks"]),
            stack_min=0,
            stack_max=int(values["max_stacks"]),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-attack-buff",
            label=f"{raw.name}·2层全队攻击力提升",
            eligibility=eligibility,
            condition_ids=(full_id,),
            effects=(attack_effect,),
        ),
    ), (active_condition, full_condition)


def _astra_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    condition_id: ScenarioConditionId,
) -> tuple[CalculationRuleItem, ...]:
    effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(
                raw.wengine_id,
                build_input.equipped_character_id,
                "team-damage",
            ),
            source=source,
            owner=build_input.equipped_character_id,
            target=EffectTarget.TEAM,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(float(talent.numeric_values["team_damage_bonus"])),
        ),
    )
    return (
        CalculationRuleItem(
            rule_id=RuleItemId(
                _instance_rule_id(
                    raw.wengine_id,
                    build_input.equipped_character_id,
                    "team-damage",
                )
            ),
            owner=build_input.equipped_character_id,
            source=source,
            display_name=f"{raw.name}·全队增伤",
            original_text=talent.text,
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(effect,),
            stack_count=int(talent.numeric_values["max_stacks"]),
            stack_min=0,
            stack_max=int(talent.numeric_values["max_stacks"]),
        ),
    )


def _effect_rule(
    *,
    effect_id: str,
    source: RuleSource,
    owner: CharacterId,
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


def _owner_token(owner: CharacterId) -> str:
    """Return a stable compact owner token for instantiated equipment IDs."""

    return str(owner).rsplit(":", 1)[-1]


def _instance_rule_id(
    wengine_id: WEngineId,
    owner: CharacterId,
    suffix: str,
) -> str:
    return f"rule:{wengine_id}:owner:{_owner_token(owner)}:{suffix}"


def _instance_effect_id(
    wengine_id: WEngineId,
    owner: CharacterId,
    suffix: str,
) -> str:
    return f"effect:{wengine_id}:owner:{_owner_token(owner)}:{suffix}"


def _role(value: str) -> CharacterRole:
    mapping = {
        "attack": CharacterRole.ATTACK,
        "support": CharacterRole.SUPPORT,
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unsupported W-Engine specialty: {value}") from exc


def _diagnostic(
    source: str,
    suffix: str,
    kind: DiagnosticKind,
    message: str,
) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"wengine:{source}:{suffix}"),
        kind=kind,
        message=message,
        blocking=True,
    )


__all__ = [
    "ASTRA_DAMAGE_BUFF_CONDITION_ID",
    "astra_damage_buff_condition_id_for",
    "ASTRA_ID",
    "SIGNATURE_WENGINE_BY_CHARACTER",
    "WENGINE_ASTRA_ID",
    "WENGINE_YE_ID",
    "WEngineBuildResolution",
    "WEngineRawRecord",
    "YE_MINGXIN_CONDITION_ID",
    "YE_ID",
    "YE_VEIL_ACTIVE_CONDITION_ID",
    "compile_wengine",
    "load_wengine_raw_record",
    "signature_wengine_id_for",
]
