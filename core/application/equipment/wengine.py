"""Reviewed W-Engine vertical slices used by the build validation stages."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from core.application.diagnostics import CalculationDiagnostic, DiagnosticKind
from core.application.element_scope import element_scope_filter
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
    DamageSubtype,
    DamageSubtypeFilter,
    DamageDealerFilter,
    DamageType,
    DamageTypeFilter,
    DynamicIdentityCondition,
    DynamicIdentity,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    EquipmentOwnerCapabilities,
    Element,
    ElementFilter,
    ModifierEffect,
    ModifierResult,
    Resolved,
    Unresolved,
    UnresolvedReason,
    RuleStackCondition,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SnapshotRule,
    WEngineBuildInput,
    WEngineId,
)
from .wengine_ids import (
    ALICE_ID,
    ASTRA_ID,
    TRIGGER_ID,
    YE_ID,
    YUZUHA_ID,
    WENGINE_ALICE_ID,
    WENGINE_ASTRA_ID,
    WENGINE_ELECTRO_STORM_I_ID,
    WENGINE_ELECTRO_STORM_II_ID,
    WENGINE_ELECTRO_STORM_III_ID,
    WENGINE_ASH_COBALT_BLUE_ID,
    WENGINE_IDENTITY_ALTERNATE_ID,
    WENGINE_IDENTITY_STANDARD_ID,
    WENGINE_LUNAR_STRING_ID,
    WENGINE_LUNAR_DECRESCENT_ID,
    WENGINE_LUNAR_NOVILUNA_ID,
    WENGINE_TIME_SLICE_ID,
    WENGINE_HUMAN_IS_MEAT_ID,
    WENGINE_RAINFOREST_GOURMAND_ID,
    WENGINE_REVERB_MARK_I_ID,
    WENGINE_REVERB_MARK_II_ID,
    WENGINE_TURBULENCE_ARROW_ID,
    WENGINE_TURBULENCE_AXE_ID,
    WENGINE_TURBULENCE_CANNON_ID,
    WENGINE_STREET_SUPERSTAR_ID,
    WENGINE_STARLIGHT_ENGINE_ID,
    WENGINE_TRIGGER_ID,
    WENGINE_YE_ID,
    WENGINE_YUZUHA_ID,
    WENGINE_PRECIOUS_FOSSIL_ID,
    WENGINE_PRECISE_TRANSFORMER_ID,
    WENGINE_TWIN_CRYING_STARS_ID,
    WENGINE_ELECTRIC_LIP_GLOSS_ID,
    WENGINE_BUNNY_BAND_ID,
    WENGINE_SPRING_WARMTH_ID,
    WENGINE_FANTASY_CUBE_ID,
    WENGINE_GILDED_BLOSSOM_ID,
    WENGINE_RADIO_WAVE_WALK_ID,
    WENGINE_STRONG_ENOUGH_ID,
)
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
    ALICE_ID: WENGINE_ALICE_ID,
    YUZUHA_ID: WENGINE_YUZUHA_ID,
    TRIGGER_ID: WENGINE_TRIGGER_ID,
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
    """Lossless normalized source values for one supported level-60 engine.

    ``base_attack`` remains for existing Attack-primary fixtures. The typed
    ``base_stat``/``base_value`` pair identifies the actual white primary value
    when the source names a different stat.
    """

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
    base_stat: CharacterStat = CharacterStat.ATTACK
    base_value: float | None = None

    def __post_init__(self) -> None:
        if not self.source_version.strip() or not self.source_url.strip():
            raise ValueError("W-Engine source metadata is required")
        if not self.name.strip() or not self.icon.strip():
            raise ValueError("W-Engine display metadata is required")
        if self.rarity not in {"S", "A", "B"}:
            raise ValueError("reviewed W-Engine rarity must be S, A, or B")
        if self.max_level != 60:
            raise ValueError("Stage18-2.5 W-Engine max level must be 60")
        if (
            not math.isfinite(self.base_attack)
            or not math.isfinite(self.static_base_value)
            or not math.isfinite(self.advanced_stat_value)
        ):
            raise ValueError("W-Engine static values must be finite")
        if tuple(item.refinement for item in self.talents) != (1, 2, 3, 4, 5):
            raise ValueError("W-Engine raw talents must contain refinements 1 through 5")

    @property
    def static_base_value(self) -> float:
        return self.base_value if self.base_value is not None else self.base_attack


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
        base_stat = _base_stat(str(resolved.get("base_stat_key", "attack")))
        base_value = float(resolved.get("base_stat_value", resolved["base_attack"]))
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
            base_stat=base_stat,
            base_value=base_value,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid W-Engine raw record: {wengine_id}") from exc


def compile_wengine(
    build_input: WEngineBuildInput,
    *,
    equipped_character_role: CharacterRole | None = None,
    owner_capabilities: EquipmentOwnerCapabilities | None = None,
) -> WEngineBuildResolution:
    """Compile one equipped instance with reviewed owner capabilities.

    ``equipped_character_role`` remains a compatibility input for the early
    signature slice; capability-dependent effects are conservatively
    ineligible when only that legacy role is supplied.
    """

    if owner_capabilities is None:
        if equipped_character_role is None:
            raise ValueError(
                "compile_wengine requires equipped_character_role or owner_capabilities"
            )
        owner_capabilities = EquipmentOwnerCapabilities(
            character_id=build_input.equipped_character_id,
            role=equipped_character_role,
        )
    elif owner_capabilities.character_id != build_input.equipped_character_id:
        raise ValueError("owner capabilities must match equipped character")
    if (
        equipped_character_role is not None
        and owner_capabilities.role is not equipped_character_role
    ):
        raise ValueError("equipped character role disagrees with owner capabilities")
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
            owner_capabilities,
        )
        diagnostics = _wengine_result_diagnostics(raw, build_input.refinement)
    return WEngineBuildResolution(
        build_input=build_input,
        raw=raw,
        contributions=contributions,
        rule_items=rules,
        scenario_conditions=conditions,
        diagnostics=diagnostics,
    )


def _wengine_result_diagnostics(
    raw: WEngineRawRecord,
    refinement: int,
) -> tuple[CalculationDiagnostic, ...]:
    limitations = {
        WENGINE_LUNAR_NOVILUNA_ID: (
            "One-shot Energy restoration is retained in the source record, but the "
            "current calculation request has no Energy resource result. It is not "
            "approximated as Energy Regeneration."
        ),
        WENGINE_TURBULENCE_CANNON_ID: (
            "The damage request pipeline does not calculate Daze values. The typed "
            "EX Special Daze modifier is preserved for matching and trace, but no "
            "Daze result is included in damage totals."
        ),
        WENGINE_TURBULENCE_ARROW_ID: (
            "The damage request pipeline does not calculate Daze values. The typed "
            "owner Daze modifier is preserved for matching and trace, but no Daze "
            "result is included in damage totals."
        ),
        WENGINE_ELECTRO_STORM_III_ID: (
            "One-shot Energy restoration after a teammate applies an Attribute "
            "Anomaly is preserved in the source record, but the current calculation "
            "request has no Energy resource result."
        ),
        WENGINE_IDENTITY_ALTERNATE_ID: (
            "This passive reduces the attacking enemy's outgoing damage, but the "
            "current calculation request has no incoming enemy-damage result. "
            "It is retained as source data instead of changing player outgoing "
            "damage or enemy damage reduction against the player."
        ),
        WENGINE_TIME_SLICE_ID: (
            "Decibel gains and one-shot Energy restoration are retained in the "
            "source record, but neither resource has a result field in the current "
            "calculation request."
        ),
        WENGINE_HUMAN_IS_MEAT_ID: (
            "The source assigns Impact tiers from current Energy and retains them "
            "after Energy use. The active 0–8 tier count is an explicit current-state "
            "input because Energy history and tier expiry timing are not modeled."
        ),
        WENGINE_LUNAR_STRING_ID: (
            "The source is typed as a Vanguard W-Engine, but the current character "
            "registry has no Vanguard owner that can reach calculate_payload."
        ),
        WENGINE_PRECIOUS_FOSSIL_ID: (
            "The damage request pipeline does not calculate Daze values. The "
            "target-HP-gated outgoing Daze bonuses remain typed for matching and "
            "trace, but no Daze result is included in damage totals."
        ),
        WENGINE_TWIN_CRYING_STARS_ID: (
            "The number of active Anomaly Proficiency stacks is an explicit current "
            "state. Stack expiry, target cleanup, and battle timing are not replayed."
        ),
        WENGINE_SPRING_WARMTH_ID: (
            "Received damage reduction and Energy Recovery Efficiency are preserved "
            "as source-only effects because this request has no incoming-damage or "
            "resource result, and no typed recipient for the swap-transfer effect."
        ),
    }
    message = limitations.get(raw.wengine_id)
    if message is None:
        return ()
    return (
        CalculationDiagnostic(
            diagnostic_id=DiagnosticId(f"wengine:{raw.wengine_id}:result-scope"),
            kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
            message=message,
            blocking=False,
            original_text=raw.talents[refinement - 1].text,
        ),
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
                f":base-{raw.base_stat.value}"
            ),
            source=source,
            stat=raw.base_stat,
            layer=BuildContributionLayer.WHITE_VALUE,
            value=Resolved(raw.static_base_value),
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
    owner_capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    eligible = raw.specialty is owner_capabilities.role
    eligibility = RuleEligibility.ELIGIBLE if eligible else RuleEligibility.INELIGIBLE
    talent = raw.talents[build_input.refinement - 1]
    source = RuleSource(
        source_id=RuleSourceId(f"{raw.wengine_id}:talent:{build_input.refinement}"),
        source_type=EffectSourceType.WEAPON,
        label=f"{raw.name}·{talent.name}",
        raw_text=talent.text,
    )
    effect_family = reviewed_mapping_for(raw.wengine_id).effect_family
    if effect_family == "attack-lunar-pleniluna":
        return _lunar_pleniluna_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-lunar-decrescent":
        return _lunar_decrescent_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-lunar-noviluna":
        return _lunar_noviluna_rules(
            raw, build_input, source, eligibility
        ), ()
    if effect_family == "support-reverb-mark-i":
        return _reverb_mark_i_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-reverb-mark-ii":
        return _reverb_mark_ii_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-turbulence-cannon":
        return _turbulence_cannon_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-turbulence-arrow":
        return _turbulence_arrow_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-turbulence-axe":
        return _turbulence_axe_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-electro-storm-i":
        return _electro_storm_i_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-electro-storm-ii":
        return _electro_storm_ii_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-electro-storm-iii":
        return _result_only_wengine_rules(
            raw, build_input, source, eligibility, "anomaly-energy-restore"
        ), ()
    if effect_family == "defense-identity-standard":
        return _identity_standard_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "defense-identity-alternate":
        return _result_only_wengine_rules(
            raw, build_input, source, eligibility, "enemy-outgoing-damage-reduction"
        ), ()
    if effect_family == "rupture-ash-cobalt-blue":
        return _ash_cobalt_blue_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "vanguard-lunar-string":
        return _lunar_string_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-street-superstar":
        return _street_superstar_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-time-slice":
        return _result_only_wengine_rules(
            raw, build_input, source, eligibility, "resource-gains"
        ), ()
    if effect_family == "anomaly-rainforest-gourmand":
        return _rainforest_gourmand_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-precious-fossil":
        return _precious_fossil_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "defense-precise-transformer":
        return _precise_transformer_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-twin-crying-stars":
        return _twin_crying_stars_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-electric-lip-gloss":
        return _electric_lip_gloss_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "defense-bunny-band":
        return _bunny_band_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "defense-spring-warmth":
        return _result_only_wengine_rules(
            raw, build_input, source, eligibility, "incoming-damage-and-resource-effects"
        ), ()
    if effect_family == "rupture-fantasy-cube":
        return _fantasy_cube_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-gilded-blossom":
        return _gilded_blossom_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "rupture-radio-wave-walk":
        return _radio_wave_walk_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-strong-enough":
        return _strong_enough_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-starlight-engine":
        return _starlight_engine_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-human-is-meat":
        return _human_is_meat_rules(raw, build_input, talent, source, eligibility)
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
        return _deep_sea_visitor_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-heart-of-sword":
        return _heart_of_sword_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-defense-patrol":
        return _defense_patrol_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "support-resonab-3":
        return _resonab_three_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-treasure-chest":
        return _treasure_chest_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-crying-cradle":
        return _crying_cradle_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-dream-forge":
        return _dream_forge_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "support-song-of-noise":
        return _song_of_noise_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "alice-practiced-perfection":
        return _alice_practiced_perfection_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "yuzuha-metanukimorphosis":
        return _yuzuha_metanukimorphosis_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "trigger-spectral-gaze":
        return _trigger_spectral_gaze_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    raise ValueError(f"no reviewed W-Engine rule mapping for {raw.wengine_id}")


def _lunar_pleniluna_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    tags = (
        DamageTag.BASIC_ATTACK,
        DamageTag.DASH_ATTACK,
        DamageTag.DODGE_COUNTER,
    )
    effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "basic-dash-counter-damage"),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM,
            filters=(
                DamageDealerFilter(owner),
                AnyFilter(tuple(DamageTagFilter(tag) for tag in tags)),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(float(talent.numeric_values["direct_damage_bonus"])),
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="basic-dash-counter-damage",
                label=f"{raw.name}·普通、冲刺、闪避反击伤害提升",
                eligibility=eligibility,
                effects=(effect,),
            ),
        ),
        (),
    )


def _lunar_decrescent_rules(
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
        "damage-buff-active",
        f"{raw.name}：连携技/终结技触发后的增伤已生效",
        talent.text,
    )
    effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="damage-buff",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(talent.numeric_values["damage_bonus"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="damage-buff",
                label=f"{raw.name}·触发后伤害提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _lunar_noviluna_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[CalculationRuleItem, ...]:
    owner = build_input.equipped_character_id
    limitation = _wengine_result_diagnostics(raw, build_input.refinement)
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="energy-restore",
            label=f"{raw.name}·强化特殊技触发能量回复",
            eligibility=eligibility,
            effects=(),
            diagnostics=limitation,
        ),
    )


def _result_only_wengine_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    source: RuleSource,
    eligibility: RuleEligibility,
    suffix: str,
) -> tuple[CalculationRuleItem, ...]:
    limitation = _wengine_result_diagnostics(raw, build_input.refinement)
    return (
        _rule(
            raw=raw,
            owner=build_input.equipped_character_id,
            source=source,
            suffix=suffix,
            label=f"{raw.name}·当前请求外效果",
            eligibility=eligibility,
            effects=(),
            diagnostics=limitation,
        ),
    )


def _reverb_mark_i_rules(
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
        "team-impact-active",
        f"{raw.name}：强化特殊技触发的全队冲击力提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-impact",
        path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        value=float(talent.numeric_values["team_impact_percent"]),
        target=EffectTarget.TEAM,
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="team-impact",
                label=f"{raw.name}·全队冲击力提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
                non_stacking_group_id="wengine:12004:tidal-team-impact",
            ),
        ),
        (condition,),
    )


def _reverb_mark_ii_rules(
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
        "team-anomaly-stats-active",
        f"{raw.name}：强化特殊技/连携技触发的全队异常属性提升已生效",
        talent.text,
    )
    effects = (
        _panel_modifier(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-anomaly-mastery",
            path=CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
            value=float(talent.numeric_values["team_anomaly_mastery_flat"]),
            target=EffectTarget.TEAM,
        ),
        _panel_modifier(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-anomaly-proficiency",
            path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
            value=float(talent.numeric_values["team_anomaly_proficiency_flat"]),
            target=EffectTarget.TEAM,
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="team-anomaly-stats",
                label=f"{raw.name}·全队异常掌控/精通提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=effects,
                non_stacking_group_id="wengine:12005:sound-wave-team-anomaly-stats",
            ),
        ),
        (condition,),
    )


def _turbulence_cannon_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="ex-daze",
        path=CalculationNode.DAZE_OUTGOING_BONUS,
        value=float(talent.numeric_values["ex_daze_bonus"]),
        filters=(DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="ex-daze",
                label=f"{raw.name}·强化特殊技失衡值提升",
                eligibility=eligibility,
                effects=(effect,),
                diagnostics=_wengine_result_diagnostics(
                    raw, build_input.refinement
                ),
            ),
        ),
        (),
    )


def _turbulence_arrow_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="primary-target-daze",
        path=CalculationNode.DAZE_OUTGOING_BONUS,
        value=float(talent.numeric_values["primary_target_daze_bonus"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="primary-target-daze",
                label=f"{raw.name}·主要目标失衡值提升",
                eligibility=eligibility,
                effects=(effect,),
                diagnostics=_wengine_result_diagnostics(
                    raw, build_input.refinement
                ),
            ),
        ),
        (),
    )


def _turbulence_axe_rules(
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
        "impact-active",
        f"{raw.name}：接战切入操作角色后冲击力提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="impact",
        path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        value=float(talent.numeric_values["impact_percent"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="impact",
                label=f"{raw.name}·冲击力提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _electro_storm_i_rules(
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
        "anomaly-mastery-active",
        f"{raw.name}：异常积蓄触发的掌控提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-mastery",
        path=CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
        value=float(talent.numeric_values["anomaly_mastery_flat"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="anomaly-mastery",
                label=f"{raw.name}·异常掌控提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _electro_storm_ii_rules(
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
        "anomaly-proficiency-active",
        f"{raw.name}：异常积蓄触发的精通提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-proficiency",
        path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
        value=float(talent.numeric_values["anomaly_proficiency_flat"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="anomaly-proficiency",
                label=f"{raw.name}·异常精通提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _identity_standard_rules(
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
        "defense-active",
        f"{raw.name}：受到攻击后的防御力提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="defense",
        path=CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
        value=float(talent.numeric_values["defense_percent"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="defense",
                label=f"{raw.name}·防御力提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _ash_cobalt_blue_rules(
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
        "attack-active",
        f"{raw.name}：接战切入操作角色后的攻击力提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="attack",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(talent.numeric_values["attack_percent"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="attack",
                label=f"{raw.name}·攻击力提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _lunar_string_rules(
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
        "basic-damage-active",
        f"{raw.name}：强化特殊技后的普通攻击增伤已生效",
        talent.text,
    )
    effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="basic-damage",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(talent.numeric_values["basic_damage_bonus"]),
        filters=(DamageTagFilter(DamageTag.BASIC_ATTACK),),
    )
    limitation = _wengine_result_diagnostics(raw, build_input.refinement)
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="basic-damage",
                label=f"{raw.name}·普通攻击伤害提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
                diagnostics=limitation,
            ),
        ),
        (condition,),
    )


def _street_superstar_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="ultimate-damage-per-charge",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(values["ultimate_bonus_per_charge"]),
        filters=(DamageTagFilter(DamageTag.ULTIMATE),),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="ultimate-damage-per-charge",
                label=f"{raw.name}·终结技每层充能增伤",
                eligibility=eligibility,
                effects=(effect,),
                stack_count=0,
                stack_min=0,
                stack_max=int(values["max_charges"]),
            ),
        ),
        (),
    )


def _rainforest_gourmand_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="attack-per-energy-stack",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(values["attack_percent_per_stack"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="attack-per-energy-stack",
                label=f"{raw.name}·当前能量消耗增益层数",
                eligibility=eligibility,
                effects=(effect,),
                stack_count=0,
                stack_min=0,
                stack_max=int(values["max_stacks"]),
            ),
        ),
        (),
    )


def _electric_lip_gloss_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    field_anomaly_id, field_anomaly_condition = _condition(
        raw,
        owner,
        "anomaly-in-field-active",
        f"{raw.name}：场上任一敌人的属性异常状态存在",
        "当场上存在处于属性异常状态下的敌人时",
    )
    target_anomaly_id, target_anomaly_condition = _condition(
        raw,
        owner,
        "damage-target-anomaly-active",
        f"{raw.name}：本次伤害目标处于属性异常状态",
        "对目标造成的伤害额外提升",
    )
    attack_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="attack",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(values["attack_percent"]),
    )
    target_damage_effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="target-damage",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(values["target_damage_bonus"]),
    )
    unresolved_scope = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_TEXT,
        notes=(
            "The source states that an anomalous enemy exists on the field, then "
            "increases damage to 'the target'. It does not specify whether that "
            "bonus also applies to a different, currently normal target."
        ),
        original_text=talent.text,
        candidates=(
            "The extra target damage bonus applies only when the current target is anomalous.",
            "The extra target damage bonus applies to any current target while an anomalous enemy exists elsewhere.",
        ),
    )
    unresolved_scope_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(
                raw.wengine_id, owner, "unresolved-target-damage-scope"
            ),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            filters=(DamageDealerFilter(owner),),
            condition=unresolved_scope,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.0),
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="field-anomaly-attack",
                label=f"{raw.name}·场上存在异常敌人时攻击力提升",
                eligibility=eligibility,
                condition_ids=(field_anomaly_id,),
                effects=(attack_effect,),
            ),
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="target-anomaly-damage",
                label=f"{raw.name}·异常目标额外伤害",
                eligibility=eligibility,
                condition_ids=(field_anomaly_id, target_anomaly_id),
                effects=(target_damage_effect,),
            ),
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="target-damage-scope-ambiguous",
                label=f"{raw.name}·异常状态与当前目标归属未决分支",
                eligibility=eligibility,
                condition_ids=(field_anomaly_id,),
                condition_not_ids=(target_anomaly_id,),
                effects=(unresolved_scope_effect,),
            ),
        ),
        (field_anomaly_condition, target_anomaly_condition),
    )


def _precious_fossil_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    half_id, half_condition = _condition(
        raw,
        owner,
        "target-hp-at-least-50-percent",
        f"{raw.name}：当前目标生命值至少50%",
        "敌方生命值大于等于50%时",
    )
    three_quarters_id, three_quarters_condition = _condition(
        raw,
        owner,
        "target-hp-at-least-75-percent",
        f"{raw.name}：当前目标生命值至少75%",
        "敌方生命值大于等于75%时",
    )
    rules = (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="daze-bonus-at-50",
            label=f"{raw.name}·目标生命值≥50%时失衡值提升",
            eligibility=eligibility,
            condition_ids=(half_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="daze-bonus-at-50",
                    path=CalculationNode.DAZE_OUTGOING_BONUS,
                    value=float(values["daze_bonus_at_50"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="daze-extra-bonus-at-75",
            label=f"{raw.name}·目标生命值≥75%时失衡值额外提升",
            eligibility=eligibility,
            condition_ids=(half_id, three_quarters_id),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="daze-extra-bonus-at-75",
                    path=CalculationNode.DAZE_OUTGOING_BONUS,
                    value=float(values["daze_extra_bonus_at_75"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    )
    return rules, (half_condition, three_quarters_condition)


def _precise_transformer_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    impact_id, impact_condition = _condition(
        raw,
        owner,
        "impact-buff-after-hit-active",
        f"{raw.name}：受击后冲击力增益当前有效",
        "受到敌方攻击时，装备者的冲击力提升，持续12秒",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="hp-percent",
            label=f"{raw.name}·生命值提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="hp-percent",
                    path=CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                    value=float(values["hp_percent"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="impact-after-hit",
            label=f"{raw.name}·受击后冲击力提升",
            eligibility=eligibility,
            condition_ids=(impact_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="impact-after-hit",
                    path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
                    value=float(values["impact_percent_after_hit"]),
                ),
            ),
        ),
    ), (impact_condition,)


def _bunny_band_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    return _hp_and_shield_attack_rules(
        raw,
        build_input,
        talent,
        source,
        eligibility,
        hp_key="hp_percent",
        shield_attack_key="attack_percent_with_shield",
        shield_path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        shield_label="攻击力",
    )


def _hp_and_shield_attack_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    *,
    hp_key: str,
    shield_attack_key: str,
    shield_path: CalculationNode,
    shield_label: str,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    shield_id, shield_condition = _condition(
        raw,
        owner,
        "shield-active",
        f"{raw.name}：护盾当前有效",
        "处于护盾下时",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="hp-percent",
            label=f"{raw.name}·生命值提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="hp-percent",
                    path=CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                    value=float(values[hp_key]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="shield-stat",
            label=f"{raw.name}·护盾下{shield_label}提升",
            eligibility=eligibility,
            condition_ids=(shield_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="shield-stat",
                    path=shield_path,
                    value=float(values[shield_attack_key]),
                ),
            ),
        ),
    ), (shield_condition,)


def _twin_crying_stars_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-proficiency-per-stack",
        label=f"{raw.name}·当前有效异常精通层数",
        eligibility=eligibility,
        effects=(
            _panel_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="anomaly-proficiency-per-stack",
                path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                value=float(values["anomaly_proficiency_per_stack"]),
            ),
        ),
        stack_count=0,
        stack_min=0,
        stack_max=int(values["max_stacks"]),
        diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
    )
    return (rule,), ()


def _fantasy_cube_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    crit_buff_id, crit_buff_condition = _condition(
        raw,
        owner,
        "ex-special-crit-damage-active",
        f"{raw.name}：强化特殊技触发的暴击伤害增益当前有效",
        "发动强化特殊技后，暴击伤害提升，持续12秒",
    )
    half_hp_id, half_hp_condition = _condition(
        raw,
        owner,
        "target-hp-below-50-percent",
        f"{raw.name}：本次强化特殊技命中时目标生命值低于50%",
        "强化特殊技命中生命值低于50%的目标时",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-special-crit-damage-buff",
            label=f"{raw.name}·暴击伤害提升",
            eligibility=eligibility,
            condition_ids=(crit_buff_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-special-crit-damage-buff",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-special-low-hp-damage",
            label=f"{raw.name}·强化特殊技对低生命目标伤害提升",
            eligibility=eligibility,
            condition_ids=(half_hp_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-special-low-hp-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ex_damage_bonus_below_half_hp"]),
                    filters=(DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),),
                ),
            ),
        ),
    ), (crit_buff_condition, half_hp_condition)


def _gilded_blossom_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="attack-percent",
            label=f"{raw.name}·攻击力提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="attack-percent",
                    path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    value=float(values["attack_percent"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-special-damage",
            label=f"{raw.name}·强化特殊技伤害提升",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-special-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ex_damage_bonus"]),
                    filters=(DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),),
                ),
            ),
        ),
    ), ()


def _radio_wave_walk_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="penetration-force-per-stack",
        path=CalculationNode.PENETRATION_FORCE_BONUS,
        value=float(values["penetration_force_per_stack"]),
        filters=(DamageTypeFilter(DamageType.PENETRATION),),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="penetration-force-per-stack",
            label=f"{raw.name}·当前贯穿力层数",
            eligibility=eligibility,
            effects=(effect,),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
        ),
    ), ()


def _strong_enough_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    attack_buff_id, attack_buff_condition = _condition(
        raw,
        owner,
        "ex-special-or-chain-attack-buff-active",
        f"{raw.name}：强化特殊技或连携技命中触发的攻击力增益当前有效",
        "发动强化特殊技或连携技命中敌人时，攻击力提升，持续8秒",
    )
    anomalous_target_bonus_id, anomalous_target_bonus_condition = _condition(
        raw,
        owner,
        "anomalous-target-attack-bonus-active",
        f"{raw.name}：目标异常触发的额外攻击力增益当前有效",
        "命中处于属性异常状态下的敌人时，该攻击力提升额外提高",
    )
    common_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="attack-buff",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(values["attack_percent"]),
    )
    extra_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomalous-target-extra-attack-buff",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(values["extra_attack_percent_if_target_anomalous"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="attack-buff",
            label=f"{raw.name}·攻击力提升",
            eligibility=eligibility,
            condition_ids=(attack_buff_id,),
            effects=(common_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomalous-target-extra-attack-buff",
            label=f"{raw.name}·命中异常目标后的额外攻击力提升",
            eligibility=eligibility,
            condition_ids=(attack_buff_id, anomalous_target_bonus_id),
            effects=(extra_effect,),
        ),
    ), (attack_buff_condition, anomalous_target_bonus_condition)


def _starlight_engine_rules(
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
        "attack-active",
        f"{raw.name}：闪避反击/快速支援触发的攻击力提升已生效",
        talent.text,
    )
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="attack",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(talent.numeric_values["attack_percent"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="attack",
                label=f"{raw.name}·攻击力提升",
                eligibility=eligibility,
                condition_ids=(condition_id,),
                effects=(effect,),
            ),
        ),
        (condition,),
    )


def _human_is_meat_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="impact-per-energy-tier",
        path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        value=float(values["impact_percent_per_energy_stack"]),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="impact-per-energy-tier",
                label=f"{raw.name}·当前能量冲击力层数",
                eligibility=eligibility,
                effects=(effect,),
                stack_count=0,
                stack_min=0,
                stack_max=int(values["max_stacks"]),
                diagnostics=_wengine_result_diagnostics(
                    raw, build_input.refinement
                ),
            ),
        ),
        (),
    )


def _ye_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[CalculationRuleItem, ...]:
    values = talent.numeric_values
    owner = build_input.equipped_character_id
    physical_scope = element_scope_filter(Element.PHYSICAL)
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
    *,
    default_value: bool = False,
) -> tuple[ScenarioConditionId, ScenarioCondition]:
    condition_id = _instance_condition_id(raw, owner, suffix)
    return condition_id, ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=default_value,
    )


def _capability_eligibility(
    base_eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
    *,
    element: Element | None = None,
    skill_group: SkillGroup | None = None,
    skill_groups: tuple[SkillGroup, ...] = (),
    tags: tuple[DamageTag, ...] = (),
    mechanism: str | None = None,
) -> RuleEligibility:
    if base_eligibility is RuleEligibility.INELIGIBLE:
        return RuleEligibility.INELIGIBLE
    if element is not None and not capabilities.can_produce_element(element):
        return RuleEligibility.INELIGIBLE
    if skill_group is not None and not capabilities.can_use_skill_group(skill_group):
        return RuleEligibility.INELIGIBLE
    if skill_groups and not any(
        capabilities.can_use_skill_group(group) for group in skill_groups
    ):
        return RuleEligibility.INELIGIBLE
    if any(not capabilities.can_produce_tag(tag) for tag in tags):
        return RuleEligibility.INELIGIBLE
    if mechanism is not None and not capabilities.has_mechanism(mechanism):
        return RuleEligibility.INELIGIBLE
    return base_eligibility


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
    condition=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, suffix),
            source=source,
            owner=owner,
            target=target,
            condition=condition,
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
    target: EffectTarget = EffectTarget.ENEMY,
) -> ModifierEffect:
    return ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, suffix),
            source=source,
            owner=owner,
            target=target,
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
    non_stacking_group_id: str | None = None,
    diagnostics: tuple[CalculationDiagnostic, ...] = (),
    condition_not_ids: tuple[ScenarioConditionId, ...] = (),
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
        non_stacking_group_id=non_stacking_group_id,
        diagnostics=diagnostics,
        condition_not_ids=condition_not_ids,
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
    physical_scope = (element_scope_filter(Element.PHYSICAL),)
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
    capabilities: EquipmentOwnerCapabilities,
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
    ice_scope = (element_scope_filter(Element.ICE),)
    rules = (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ice-damage",
            label=f"{raw.name}·冰属性伤害提升",
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                element=Element.ICE,
            ),
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
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                skill_group=SkillGroup.BASIC_ATTACK,
                tags=(DamageTag.BASIC_ATTACK,),
            ),
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
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                element=Element.ICE,
                skill_group=SkillGroup.DODGE,
                tags=(DamageTag.DASH_ATTACK,),
            ),
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
    capabilities: EquipmentOwnerCapabilities,
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
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                element=Element.ELECTRIC,
                skill_group=SkillGroup.DODGE,
                tags=(DamageTag.DASH_ATTACK,),
            ),
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
    capabilities: EquipmentOwnerCapabilities,
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
        element_scope_filter(Element.ETHER),
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
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                element=Element.ETHER,
                tags=(DamageTag.BASIC_ATTACK, DamageTag.DASH_ATTACK),
            ),
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
    capabilities: EquipmentOwnerCapabilities,
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
        target=EffectTarget.TEAM,
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-buff",
            label=f"{raw.name}·全队伤害提升",
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                mechanism="ether-veil",
            ),
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
    capabilities: EquipmentOwnerCapabilities,
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
    damage_effect = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-damage-buff",
        value=float(values["team_damage_per_stack"]),
        target=EffectTarget.TEAM,
    )
    attack_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-attack-buff",
        path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
        value=float(values["team_attack_at_max"]),
        target=EffectTarget.TEAM,
        condition=RuleStackCondition(
            _instance_rule_id(raw.wengine_id, owner, "team-damage-buff"),
            int(values["max_stacks"]),
        ),
    )
    damage_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-damage-buff",
        label=f"{raw.name}·全队伤害提升",
        eligibility=_capability_eligibility(
            eligibility,
            capabilities,
            element=Element.PHYSICAL,
            skill_group=SkillGroup.SPECIAL_ATTACK,
            tags=(DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
        ),
        condition_ids=(active_id,),
        effects=(damage_effect,),
        stack_count=int(values["max_stacks"]),
        stack_min=0,
        stack_max=int(values["max_stacks"]),
    )
    attack_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-attack-buff",
        label=f"{raw.name}·2层全队攻击力提升",
        eligibility=_capability_eligibility(
            eligibility,
            capabilities,
            element=Element.PHYSICAL,
            skill_group=SkillGroup.SPECIAL_ATTACK,
            tags=(DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
        ),
        condition_ids=(active_id,),
        effects=(attack_effect,),
    )
    return (damage_rule, attack_rule), (active_condition,)


def _alice_practiced_perfection_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    owner_capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    physical_eligible = _capability_eligibility(
        eligibility,
        owner_capabilities,
        element=Element.PHYSICAL,
    )
    strong_id, strong_condition = _condition(
        raw,
        owner,
        "strong-assault-active",
        "十方锻星：强击增伤已触发",
        "装备者触发强击时",
    )
    mastery_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-mastery",
        path=CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
        value=float(values["anomaly_mastery_flat"]),
    )
    physical_damage_effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="physical-damage",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(values["physical_damage_bonus"]),
        # This weapon's reviewed scope is physical damage in the three
        # calculator lanes that can represent Alice's strong-attack chain:
        # direct damage, attribute-anomaly damage, and disorder.  Keep the
        # damage-type/subtype restriction explicit so the passive does not
        # leak onto other anomaly subtypes merely because they share the
        # physical element.
        filters=(
            element_scope_filter(Element.PHYSICAL),
            AnyFilter(
                (
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    DamageTypeFilter(DamageType.DISORDER),
                )
            ),
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="anomaly-mastery",
                label=f"{raw.name}·异常掌控提升",
                eligibility=eligibility,
                effects=(mastery_effect,),
            ),
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="physical-damage",
                label=f"{raw.name}·强击后物理伤害提升",
                eligibility=physical_eligible,
                condition_ids=(strong_id,),
                effects=(physical_damage_effect,),
                stack_count=int(values["max_stacks"]),
                stack_min=0,
                stack_max=int(values["max_stacks"]),
            ),
        ),
        (strong_condition,),
    )


def _yuzuha_metanukimorphosis_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    owner_capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    physical_id, physical_condition = _condition(
        raw,
        owner,
        "physical-ex-ultimate-active",
        "狸法七变化：物理强化特殊技/终结技增益已触发",
        "装备者的强化特殊技或终结技造成物理伤害时",
    )
    follow_up_id, follow_up_condition = _condition(
        raw,
        owner,
        "team-anomaly-proficiency-active",
        "狸法七变化：全队异常精通增益已触发",
        "装备者的追加攻击命中敌人时",
    )
    physical_eligible = _capability_eligibility(
        eligibility,
        owner_capabilities,
        element=Element.PHYSICAL,
        skill_groups=(SkillGroup.SPECIAL_ATTACK, SkillGroup.ULTIMATE),
        tags=(DamageTag.EX_SPECIAL_ATTACK,),
    )
    follow_up_eligible = _capability_eligibility(
        eligibility,
        owner_capabilities,
        tags=(DamageTag.FOLLOW_UP_ATTACK,),
    )
    mastery_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-mastery",
        path=CalculationNode.CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS,
        value=float(values["anomaly_mastery_flat"]),
        condition=None,
    )
    team_proficiency_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-anomaly-proficiency",
        path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
        value=float(values["team_anomaly_proficiency_flat"]),
        target=EffectTarget.TEAM,
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="anomaly-mastery",
                label=f"{raw.name}·强化特殊技/终结技异常掌控",
                eligibility=physical_eligible,
                condition_ids=(physical_id,),
                effects=(mastery_effect,),
            ),
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="team-anomaly-proficiency",
                label=f"{raw.name}·全队异常精通",
                eligibility=follow_up_eligible,
                condition_ids=(follow_up_id,),
                effects=(team_proficiency_effect,),
            ),
        ),
        (physical_condition, follow_up_condition),
    )


def _trigger_spectral_gaze_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    owner_capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    electric_follow_up_eligible = _capability_eligibility(
        eligibility,
        owner_capabilities,
        element=Element.ELECTRIC,
        tags=(DamageTag.FOLLOW_UP_ATTACK,),
        mechanism="trigger-follow-up",
    )
    defense_active_id, defense_active_condition = _condition(
        raw,
        owner,
        "defense-reduction-active",
        "索魂影眸·目标防御降低",
        "装备者的追加攻击造成电属性伤害后，索魂影眸减防效果已生效",
        default_value=True,
    )
    defense_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "defense-reduction"),
            source=source,
            owner=owner,
            target=EffectTarget.ENEMY,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.ENEMY_DEFENSE_REDUCTION,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["defense_reduction"])),
        ),
    )
    soul_lock_id, soul_lock_condition = _condition(
        raw,
        owner,
        "soul-lock-active",
        "索魂影眸：魂锁层数已生效",
        "装备者触发被动且自身不是当前操作角色时获得魂锁",
    )
    soul_lock_rule_id = _instance_rule_id(
        raw.wengine_id, owner, "soul-lock-impact"
    )
    soul_lock_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="soul-lock-impact",
        path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        value=float(values["impact_percent_per_stack"]),
    )
    max_soul_lock_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="soul-lock-max-impact",
        path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        value=float(values["impact_percent_at_max"]),
        condition=RuleStackCondition(
            soul_lock_rule_id,
            int(values["max_stacks"]),
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="defense-reduction",
                label=f"{raw.name}·目标防御降低",
                eligibility=electric_follow_up_eligible,
                condition_ids=(defense_active_id,),
                effects=(defense_effect,),
            ),
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="soul-lock-impact",
                label=f"{raw.name}·魂锁冲击力",
                eligibility=eligibility,
                condition_ids=(soul_lock_id,),
                effects=(soul_lock_effect,),
                stack_count=int(values["max_stacks"]),
                stack_min=0,
                stack_max=int(values["max_stacks"]),
            ),
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="soul-lock-max-impact",
                label=f"{raw.name}·魂锁满层冲击力",
                eligibility=eligibility,
                condition_ids=(soul_lock_id,),
                effects=(max_soul_lock_effect,),
            ),
        ),
        (defense_active_condition, soul_lock_condition),
    )


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
        "anomaly": CharacterRole.ANOMALY,
        "stun": CharacterRole.STUN,
        "defense": CharacterRole.DEFENSE,
        "rupture": CharacterRole.RUPTURE,
        "vanguard": CharacterRole.VANGUARD,
        "击破": CharacterRole.STUN,
        "异常": CharacterRole.ANOMALY,
        "支援": CharacterRole.SUPPORT,
        "强攻": CharacterRole.ATTACK,
        "防护": CharacterRole.DEFENSE,
        "命破": CharacterRole.RUPTURE,
        "锋御": CharacterRole.VANGUARD,
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unsupported W-Engine specialty: {value}") from exc


def _base_stat(value: str) -> CharacterStat:
    mapping = {
        "attack": CharacterStat.ATTACK,
        "defense": CharacterStat.DEFENSE,
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unsupported W-Engine base stat: {value}") from exc


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
    "ALICE_ID",
    "TRIGGER_ID",
    "YUZUHA_ID",
    "SIGNATURE_WENGINE_BY_CHARACTER",
    "WENGINE_ASTRA_ID",
    "WENGINE_ALICE_ID",
    "WENGINE_TRIGGER_ID",
    "WENGINE_YE_ID",
    "WENGINE_YUZUHA_ID",
    "WEngineBuildResolution",
    "WEngineRawRecord",
    "YE_MINGXIN_CONDITION_ID",
    "YE_ID",
    "YE_VEIL_ACTIVE_CONDITION_ID",
    "compile_wengine",
    "load_wengine_raw_record",
    "signature_wengine_id_for",
]
