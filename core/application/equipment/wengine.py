"""Reviewed W-Engine vertical slice for the two current characters."""

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
    "condition:wengine:14131:damage-buff-active"
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
        if self.rarity != "S":
            raise ValueError("Stage18-2 only contains S-rank W-Engines")
        if self.max_level != 60:
            raise ValueError("Stage18-2 W-Engine max level must be 60")
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
            "Stage18-2 only carries reviewed max-level W-Engine values",
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
            contribution_id=f"{raw.wengine_id}:base-attack",
            source=source,
            stat=CharacterStat.ATTACK,
            layer=BuildContributionLayer.WHITE_VALUE,
            value=Resolved(raw.base_attack),
        )
    ]
    stat, layer = _advanced_stat(raw)
    contributions.append(
        BuildStatContribution(
            contribution_id=f"{raw.wengine_id}:advanced-stat",
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
        return _astra_rules(raw, build_input, talent, source, eligibility), (
            ScenarioCondition(
                condition_id=ASTRA_DAMAGE_BUFF_CONDITION_ID,
                label="玲珑妆匣增伤已触发",
                original_text="装备者消耗25点或以上能量时",
                resolution=ConditionResolution.USER_SELECTED,
                value=False,
            ),
        )
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
            effect_id=f"effect:{raw.wengine_id}:resistance-ignore",
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            filters=(physical_scope,),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_RESISTANCE_IGNORE,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["physical_resistance_ignore"])),
        ),
    )
    veil_damage_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=f"effect:{raw.wengine_id}:veil-damage",
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
            effect_id=f"effect:{raw.wengine_id}:veil-crit-damage",
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
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
        rule_id=RuleItemId(f"rule:{raw.wengine_id}:veil"),
        owner=owner,
        source=source,
        display_name=f"{raw.name}·以太帷幕效果",
        original_text=talent.text,
        eligibility=eligibility,
        condition_ids=(YE_MINGXIN_CONDITION_ID,),
        effects=(veil_damage_effect, veil_crit_effect),
    )
    resistance_rule = CalculationRuleItem(
        rule_id=RuleItemId(f"rule:{raw.wengine_id}:resistance-ignore"),
        owner=owner,
        source=source,
        display_name=f"{raw.name}·物理抗性无视",
        original_text=talent.text,
        eligibility=eligibility,
        effects=(resistance_effect,),
    )
    return resistance_rule, veil_rule


def _astra_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[CalculationRuleItem, ...]:
    effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=f"effect:{raw.wengine_id}:team-damage",
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
            rule_id=RuleItemId(f"rule:{raw.wengine_id}:team-damage"),
            owner=build_input.equipped_character_id,
            source=source,
            display_name=f"{raw.name}·全队增伤",
            original_text=talent.text,
            eligibility=eligibility,
            condition_ids=(ASTRA_DAMAGE_BUFF_CONDITION_ID,),
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
