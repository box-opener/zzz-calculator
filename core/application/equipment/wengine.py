"""Reviewed W-Engine vertical slices used by the build validation stages."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

from core.application.diagnostics import CalculationDiagnostic, DiagnosticKind
from core.application.element_scope import element_scope_filter
from core.application.ids import (
    DamageEventSemanticId,
    DiagnosticId,
    RuleItemId,
    ScenarioConditionId,
)
from core.application.moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import ConditionResolution, ScenarioCondition
from core.application.characters.templates import DamageEventTemplate, DirectDamageEventTemplate
from core.data.wengines.loader import load_wengine_record
from core.types import (
    AllCondition,
    AnyCondition,
    BuildContributionLayer,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterRole,
    CharacterStat,
    CurrentAttackValueSource,
    CurrentDefenseValueSource,
    DamageTag,
    DamageTagFilter,
    DamageSubtype,
    DamageSubtypeFilter,
    DamageDealerFilter,
    DamageType,
    DamageTypeFilter,
    CreatedByEffectFilter,
    EnemyStateFilter,
    DynamicIdentityCondition,
    DynamicIdentity,
    EffectId,
    EffectOperation,
    EventCreationEffect,
    EventCreationResult,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    EventTemplateId,
    EquipmentOwnerCapabilities,
    Element,
    ElementFilter,
    FixedMultiplier,
    NotCondition,
    NotFilter,
    ModifierEffect,
    ModifierResult,
    PanelStatDerivedValue,
    PanelStatThresholdCondition,
    Resolved,
    Unresolved,
    UnresolvedReason,
    RuleStackCondition,
    RuleSource,
    RuleSourceId,
    SkillGroup,
    SnapshotRule,
    StateId,
    StandardCritRule,
    WEngineBuildInput,
    WEngineId,
)
from .wengine_ids import (
    ALICE_ID,
    ANBY_ID,
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
    WENGINE_REEL_PROJECTOR_ID,
    WENGINE_CATTY_LUCK_ID,
    WENGINE_BOISTEROUS_ECHOES_ID,
    WENGINE_CAULDRON_OF_CLARITY_ID,
    WENGINE_SIMMERING_POT_ID,
    WENGINE_BLOODMARROW_COFFER_ID,
    WENGINE_DEMARA_BATTERY_II_ID,
    WENGINE_HOUSEKEEPER_ID,
    WENGINE_STARLIGHT_ENGINE_REPLICA_ID,
    WENGINE_DRILL_RIG_RED_AXIS_ID,
    WENGINE_BIG_CYLINDER_ID,
    WENGINE_BASHFUL_DEMON_ID,
    WENGINE_KABOOM_THE_CANNON_ID,
    WENGINE_PEACEKEEPER_SPECIALIZED_ID,
    WENGINE_ROARING_RIDE_ID,
    WENGINE_BOX_CUTTER_ID,
    WENGINE_TREMOR_TRIGRAM_VESSEL_ID,
    WENGINE_GRILL_O_WISP_ID,
    WENGINE_CANNON_ROTOR_ID,
    WENGINE_UNFETTERED_GAME_BALL_ID,
    WENGINE_SIX_SHOOTER_ID,
    WENGINE_KRAKENS_CRADLE_ID,
    WENGINE_TUSKS_OF_FURY_ID,
    WENGINE_HAILSTORM_SHRINE_ID,
    WENGINE_HELLFIRE_GEARS_ID,
    WENGINE_RESTRAINED_ID,
    WENGINE_BLAZING_LAUREL_ID,
    WENGINE_FLAMEMAKER_SHAKER_ID,
    WENGINE_FUSION_COMPILER_ID,
    WENGINE_TIMEWEAVER_ID,
    WENGINE_JADE_TEA_ID,
    WENGINE_STINGING_RAZOR_ID,
    WENGINE_SUNFALL_EDGE_ID,
    WENGINE_HELLHOUND_BOOMSTICK_ID,
    WENGINE_NIGHT_HARPS_ID,
    WENGINE_BIRD_DREAM_ID,
    WENGINE_SWEETBUNNY_ID,
    WENGINE_CYAN_CAGE_ID,
    WENGINE_FUYUAN_CLEAN_ID,
    WENGINE_FOX_FURNACE_ID,
    WENGINE_MACHINERY_SEED_ID,
    WENGINE_VAJRA_ID,
    WENGINE_LAST_NIGHT_ID,
    WENGINE_SOUL_IN_SHELL_ID,
    WENGINE_NEON_FANTASY_ID,
    WENGINE_SCALE_TOOTH_ID,
    WENGINE_GLOWING_HELM_ID,
    WENGINE_MOON_CUTS_FROST_ID,
    WENGINE_ECLIPSE_REMAINS_ID,
    WENGINE_LUXURY_CORE_ID,
    WENGINE_HEAD_ATTENDANT_ID,
    WENGINE_RETURNING_FEATHER_ID,
    WENGINE_CAVALRY_PRAISE_ID,
    WENGINE_CRIMSON_DESIRE_ID,
    WENGINE_SCARLET_MOON_COFFIN_ID,
    WENGINE_DREAM_FORGE_ID,
    WENGINE_STEEL_CUSHION_ID,
    WENGINE_BRIMSTONE_ID,
    NEKOMATA_C1_STUN_BACK_HIT_MECHANISM,
    WENGINE_TREASURE_CHEST_ID,
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
    ANBY_ID: WENGINE_DEMARA_BATTERY_II_ID,
    CharacterId("character:1031"): WENGINE_TREASURE_CHEST_ID,
    CharacterId("character:1021"): WENGINE_STEEL_CUSHION_ID,
    CharacterId("character:1041"): WENGINE_BRIMSTONE_ID,
    CharacterId("character:1051"): WENGINE_KRAKENS_CRADLE_ID,
    CharacterId("character:1091"): WENGINE_HAILSTORM_SHRINE_ID,
    CharacterId("character:1331"): WENGINE_BIRD_DREAM_ID,
    CharacterId("character:1371"): WENGINE_CYAN_CAGE_ID,
    # Nanoka 3.2 detail 14145 explicitly identifies Lucia in its description.
    CharacterId("character:1451"): WENGINE_DREAM_FORGE_ID,
    CharacterId("character:1481"): WENGINE_LAST_NIGHT_ID,
    CharacterId("character:1251"): WENGINE_JADE_TEA_ID,
    # The live detail for 14134 describes the engine as commissioned for Zhao.
    CharacterId("character:1341"): WENGINE_SWEETBUNNY_ID,
    # The live 3.2 engine detail names both code_name and icon as Weapon_S_1581.
    CharacterId("character:1581"): WENGINE_RETURNING_FEATHER_ID,
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
    damage_event_templates: tuple[DamageEventTemplate, ...] = ()
    derived_damage_events: tuple[DerivedDamageEventTemplateRef, ...] = ()

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
        damage_event_templates = ()
        derived_damage_events = ()
    else:
        contributions = _static_contributions(raw, build_input)
        rules, conditions = _reviewed_rules(
            raw,
            build_input,
            owner_capabilities,
        )
        damage_event_templates, derived_damage_events = (
            _resolved_extra_damage_artifacts(
                raw,
                build_input,
                owner_capabilities,
            )
        )
        diagnostics = _wengine_result_diagnostics(raw, build_input.refinement)
    return WEngineBuildResolution(
        build_input=build_input,
        raw=raw,
        contributions=contributions,
        rule_items=rules,
        scenario_conditions=conditions,
        diagnostics=diagnostics,
        damage_event_templates=damage_event_templates,
        derived_damage_events=derived_damage_events,
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
        WENGINE_REEL_PROJECTOR_ID: (
            "Damage taken and Malaise Infection reduction are preserved as source "
            "data because the current request has no incoming-damage or Malaise "
            "meter result."
        ),
        WENGINE_BOISTEROUS_ECHOES_ID: (
            "The Disorder-triggered Energy restoration is preserved in the source "
            "record because the current request has no Energy resource result; its "
            "anomalous-target damage bonus remains separately calculable."
        ),
        WENGINE_SIMMERING_POT_ID: (
            "The source's Assist Attack Daze modifier is typed and traced, but this "
            "damage request does not calculate Daze results."
        ),
        WENGINE_DEMARA_BATTERY_II_ID: (
            "Energy Recovery Efficiency after Dodge Counter or Assist Attack is "
            "preserved as a current-state source rule because the request has no "
            "Energy resource result."
        ),
        WENGINE_CATTY_LUCK_ID: (
            "The source is typed as a Vanguard W-Engine, but the current character "
            "registry has no Vanguard owner that can reach calculate_payload."
        ),
        WENGINE_BLOODMARROW_COFFER_ID: (
            "The source is typed as a Vanguard W-Engine, but the current character "
            "registry has no Vanguard owner that can reach calculate_payload."
        ),
        WENGINE_CAULDRON_OF_CLARITY_ID: (
            "The selected 0–3 active stack count is explicit current state. The "
            "20-second stack timing and 0.5-second trigger interval are not replayed."
        ),
        WENGINE_HOUSEKEEPER_ID: (
            "The selected 0–15 Physical damage stacks are current state; the "
            "one-second expiration and repeated EX hit timing are not replayed."
        ),
        WENGINE_DRILL_RIG_RED_AXIS_ID: (
            "The active Basic/Dash Electric damage buff is an explicit current state. "
            "The source's 15-second internal cooldown is not replayed."
        ),
        WENGINE_BIG_CYLINDER_ID: (
            "Damage taken reduction is preserved as a source-only effect because "
            "the current request has no incoming-damage result. The selected "
            "post-hit proc creates one guaranteed-Crit Direct component per source "
            "hit; the 7.5-second cooldown is not replayed."
        ),
        WENGINE_CANNON_ROTOR_ID: (
            "The selected current-hit Crit proc creates one Physical Direct child "
            "with the wearer's Attack and standard Crit. Its 6–8-second internal "
            "cooldown is not replayed."
        ),
        WENGINE_KABOOM_THE_CANNON_ID: (
            "The team Energy restoration is preserved in a source-linked RuleItem "
            "because the request has no Energy resource result. The active team "
            "stack count is explicit; per-teammate contributions and expiration "
            "timing are not replayed."
        ),
        WENGINE_TREMOR_TRIGRAM_VESSEL_ID: (
            "The damage/HP-loss-triggered Energy restoration is preserved as source "
            "data because the current request has no Energy resource result."
        ),
        WENGINE_BOX_CUTTER_ID: (
            "The source's follow-up Daze modifier is typed and traced, but this "
            "damage request does not calculate Daze results."
        ),
        WENGINE_ROARING_RIDE_ID: (
            "The source randomly selects one of three effects on EX hit; each "
            "effect's active state is explicit, and random selection/cooldown "
            "timing is not replayed."
        ),
        WENGINE_SIX_SHOOTER_ID: (
            "The EX Special charge-based Daze bonus is typed and traced, but this "
            "damage request does not calculate Daze results. Charge accrual and "
            "consumption are represented by the explicit current 0–6 count."
        ),
        WENGINE_TUSKS_OF_FURY_ID: (
            "The source's shield-strength increase and Daze increase are preserved "
            "because the request has no shield-value result and does not calculate "
            "Daze. The TEAM damage bonus remains active."
        ),
        WENGINE_RESTRAINED_ID: (
            "The ordinary-attack Daze modifier is typed and traced, but this damage "
            "request does not calculate Daze results. Its current 0–5 stack count "
            "is explicit; per-move hit ordering and expiry timing are not replayed."
        ),
        WENGINE_KRAKENS_CRADLE_ID: (
            "The Ice Penetration stack count and the half-HP Crit Rate trigger are "
            "explicit current-state inputs. HP-loss history, the 0.5-second trigger "
            "limit, and independent 25-second stack timers are not replayed."
        ),
        WENGINE_HAILSTORM_SHRINE_ID: (
            "The source's always-on Crit Damage is calculated. EX/Anomaly-triggered "
            "Ice bonus uses an explicit current 0–2 stack count; trigger history "
            "and independent 15-second stack timers are not replayed."
        ),
        WENGINE_HELLFIRE_GEARS_ID: (
            "Backline Energy Regeneration is gated by the owner's actual current "
            "operator status. The active 0–2 EX Special Impact stacks are explicit; "
            "their 10-second timers are not replayed."
        ),
        WENGINE_BLAZING_LAUREL_ID: (
            "The Assist-triggered Impact state and target's current 0–20 Depression "
            "stacks are explicit. Basic-hit history and independent 8/30-second "
            "timers are not replayed."
        ),
        WENGINE_FLAMEMAKER_SHAKER_ID: (
            "Backline Energy Regeneration is gated by the owner's actual current "
            "operator status. The active 0–10 damage stacks and the separate AP-buff "
            "active state are explicit; stack generation, doubled backline gain, "
            "0.3-second cooldown, and six-second timers are not replayed."
        ),
        WENGINE_FUSION_COMPILER_ID: (
            "The permanent Attack bonus and active 0–3 Anomaly Proficiency stacks "
            "are calculated from current state. Special-hit history and independent "
            "eight-second stack timers are not replayed."
        ),
        WENGINE_TIMEWEAVER_ID: (
            "The Electric buildup bonus is capability-gated; its accumulation is "
            "not simulated. The 15-second AP state after a Special hit on an "
            "anomalous target is explicit; the Disorder bonus compares against the "
            "wearer's formal current AP."
        ),
        WENGINE_JADE_TEA_ID: (
            "Tea Power is an explicit current 0–30 stack count. The separate team "
            "damage state records a qualifying stack gain at 15 or more, so it can "
            "remain active after stacks fall; stack history and 8/10-second timers "
            "are not replayed."
        ),
        WENGINE_STINGING_RAZOR_ID: (
            "The current 0–3 Hunter's Intent stacks are explicit; Dash hits, "
            "Perfect Dodge, entering combat, and 0.5-second trigger history are "
            "not replayed. Its buildup-efficiency modifier applies only at three "
            "selected current stacks."
        ),
        WENGINE_SUNFALL_EDGE_ID: (
            "The permanent Crit Damage panel bonus is calculated. The three-second "
            "execution-state trigger is explicit; its subsequent owner attacks use "
            "the active 0–1 state without retesting the triggering move."
        ),
        WENGINE_HELLHOUND_BOOMSTICK_ID: (
            "The permanent Crit Rate panel bonus is calculated. The current 0–2 "
            "Defense-ignore layers are explicit; Follow-up Fire triggers and the "
            "three/eight-second timing are not replayed."
        ),
        WENGINE_NIGHT_HARPS_ID: (
            "The permanent Crit Damage panel bonus is calculated. The current 0–2 "
            "Heartstrings layers are explicit; entry/Chain/Ultimate triggers and "
            "30-second expiry are not replayed. The resistance-ignore modifier is "
            "limited to the source-named Fire Chain/Ultimate events."
        ),
        WENGINE_BIRD_DREAM_ID: (
            "The permanent Anomaly Buildup Efficiency is applied to the wearer. "
            "The current 0–6 Ether-triggered AP stacks are explicit; Ether-hit "
            "history, the 0.5-second cooldown, and five-second expiry are not replayed."
        ),
        WENGINE_SWEETBUNNY_ID: (
            "The team Attack/HP passive is an always-on panel effect. The separate "
            "team Crit Damage state after the wearer opens or extends an Ether Veil "
            "is explicit and is limited to owners with the registered curtain "
            "mechanism; veil sequence and the 60-second timer are not replayed."
        ),
        WENGINE_CYAN_CAGE_ID: (
            "The current 0–2 Cyan Journey stacks are explicit. The EX Special and "
            "battle-entry triggers and 15-second expiry are not replayed; Ether "
            "ordinary and EX/Ultimate Penetration bonuses remain in separate lanes."
        ),
        WENGINE_FUYUAN_CLEAN_ID: (
            "The permanent Crit Damage panel bonus is calculated. The current 0–3 "
            "hit-category stack count is explicit; same-move hit history and "
            "30-second timers are not replayed. The Electric damage branch is "
            "capability-gated."
        ),
        WENGINE_FOX_FURNACE_ID: (
            "The Daze modifier is typed for EX Special, Chain, and Ultimate tags, "
            "but the damage request does not calculate Daze. The current 0–2 team "
            "damage stacks are explicit; eligible Fire Chain/Ultimate triggers, "
            "same-move limits, and 30-second timers are not replayed."
        ),
        WENGINE_MACHINERY_SEED_ID: (
            "Current stacks are explicit. Basic/EX hits can generate them regardless "
            "of element; the Electric bonus is filtered to Electric damage, while "
            "the full-stack Basic/Ultimate Defense ignore is not Electric-filtered. "
            "Per-type caps and 40-second timers are not replayed."
        ),
        WENGINE_VAJRA_ID: (
            "The current 0–2 Fire Penetration damage stacks are explicit. EX Special "
            "trigger history and 20-second stack timers are not replayed; its Fire "
            "branch is capability-gated."
        ),
        WENGINE_LAST_NIGHT_ID: (
            "Backline flat Energy Regeneration is structurally gated by the owner's "
            "current operator status. The current 0–3 EX Special/Daze stacks and "
            "separate team Crit Damage state at three stacks are explicit; Daze has "
            "no result and their 10/40-second timers are not replayed."
        ),
        WENGINE_SOUL_IN_SHELL_ID: (
            "The current active Ether-owner buff state is explicit. The anomalous-target "
            "condition is separate from activation, and event bonuses apply only while "
            "the owner is the actual current operator. Entry/Special triggers, returning "
            "to the backline, and the 15-second timer are not replayed."
        ),
        WENGINE_NEON_FANTASY_ID: (
            "The current 0–2 Ether-hit team damage layers are explicit. The additional "
            "Proficiency effect is applied at two layers; Ether-hit history, the "
            "same-move cap, and 40-second timers are not replayed."
        ),
        WENGINE_SCALE_TOOTH_ID: (
            "Energy spent and the duration/extension of the Electric Defense-ignore "
            "state have no resource-history result in this request. The current active "
            "state is explicit and is not forced to track current_operator, because "
            "the source preserves its duration while off field."
        ),
        WENGINE_MOON_CUTS_FROST_ID: (
            "The current 0–2 Ice damage stacks and the full-stack Discharge bonus are "
            "explicit, separate lanes. Special-hit history, 40-second timers, and "
            "same-move limits are not replayed."
        ),
        WENGINE_ECLIPSE_REMAINS_ID: (
            "The permanent Crit Rate is calculated. The timed Ether resistance-ignore "
            "state is exclusive to the named agent 佩洛伊斯, whose identity is absent "
            "from the current character registry. The state is retained as source data "
            "and is not enabled for another Attack owner."
        ),
        WENGINE_LUXURY_CORE_ID: (
            "The current 0–2 EX Special Wind stacks and full-stack TEAM Anomaly "
            "Proficiency state are explicit. The Turbulence and Wind Attribute Anomaly "
            "bonuses remain in their separate result lanes; EX-hit history and 40-second "
            "timers are not replayed. The stack branch is capability-gated for Wind."
        ),
        WENGINE_HEAD_ATTENDANT_ID: (
            "Backline flat Energy Regeneration uses the owner's actual current-operator "
            "relationship. The current 0–2 Fire EX Special team damage layers are "
            "explicit and unique; Fire-trigger history, same-move limits, and "
            "30-second timers are not replayed."
        ),
        WENGINE_RETURNING_FEATHER_ID: (
            "The current post-异化 buff state is explicit. Its owner Attribute Anomaly "
            "bonus has a separate Luminance Flare lane for Remielle, and its TEAM "
            "damage bonus is applied once when generating the selected source strength. "
            "The source trigger and "
            "30-second refresh timing are not replayed. It does not add a Disorder bonus."
        ),
        WENGINE_CAVALRY_PRAISE_ID: (
            "The current 0–2 Blade Edge stacks are explicit. The source's heavy-hit "
            "classification and independent 25-second layer timers are not replayed; "
            "the full-stack Ice resistance-ignore state applies only to Ice damage."
        ),
        WENGINE_CRIMSON_DESIRE_ID: (
            "The source is typed as a Vanguard engine, but the current character "
            "registry has no Vanguard owner. Its Defense Build value remains typed "
            "for direct domain validation. The Electric Sharp-damage effect stays in "
            "source data with a non-blocking diagnostic because the calculator has no "
            "Sharp Explosion result lane; it is not converted to Anomaly or Direct damage."
        ),
        WENGINE_SCARLET_MOON_COFFIN_ID: (
            "The Daze modifier is typed for the triggering EX Special. Its Daze result "
            "is outside this request. The separate 50-second TEAM_OTHER damage state "
            "excludes the holder's events and is capability-gated by the Wind EX Special trigger."
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


def _resolved_extra_damage_artifacts(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    owner_capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[DamageEventTemplate, ...], tuple[DerivedDamageEventTemplateRef, ...]]:
    owner = build_input.equipped_character_id
    talent = raw.talents[build_input.refinement - 1]
    if raw.wengine_id == WENGINE_BIG_CYLINDER_ID:
        element = owner_capabilities.native_element
        if element is None:
            return (), ()
        suffix = "defense-counter-extra-damage"
        multiplier_key = "extra_damage_defense_multiplier"
        base_source = CurrentDefenseValueSource(owner)
        crit_rule = StandardCritRule(owner, guaranteed=True)
    elif raw.wengine_id == WENGINE_CANNON_ROTOR_ID:
        suffix = "crit-triggered-extra-damage"
        element = Element.PHYSICAL
        multiplier_key = "extra_damage_attack_multiplier"
        base_source = CurrentAttackValueSource(owner)
        crit_rule = StandardCritRule(owner)
    else:
        return (), ()

    rule_item_id = RuleItemId(_instance_rule_id(raw.wengine_id, owner, suffix))
    template_id = _instance_event_template_id(raw.wengine_id, owner, suffix)
    template_ref = DamageEventTemplateRef(
        template_id=template_id,
        semantic_id=DamageEventSemanticId(
            f"event:{raw.wengine_id}:owner:{_owner_token(owner)}:{suffix}"
        ),
        label=f"{raw.name}·{('防御追击' if raw.wengine_id == WENGINE_BIG_CYLINDER_ID else '暴击触发')}额外伤害",
        damage_type=DamageType.DIRECT,
        skill_group=None,
        damage_tags=frozenset(),
        element=element,
        source_rule_item_id=rule_item_id,
    )
    template = DirectDamageEventTemplate(
        ref=template_ref,
        damage_dealer=owner,
        element=element,
        base_source=base_source,
        crit_rule=crit_rule,
        move_id=None,
    )
    multiplier = float(talent.numeric_values[multiplier_key])
    return (
        (template,),
        (
            DerivedDamageEventTemplateRef(
                template=template_ref,
                multiplier=FixedMultiplier(Resolved(multiplier)),
            ),
        ),
    )


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
    if effect_family == "defense-reel-projector":
        return _result_only_wengine_rules(
            raw, build_input, source, eligibility, "incoming-damage-and-malaise-reduction"
        ), ()
    if effect_family == "vanguard-cattery-luck":
        return _cattery_luck_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-boisterous-echoes":
        return _boisterous_echoes_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "rupture-cauldron-of-clarity":
        return _cauldron_of_clarity_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-simmering-pot":
        return _simmering_pot_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "vanguard-bloodmarrow-coffer":
        return _bloodmarrow_coffer_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-demara-battery-ii":
        return _demara_battery_ii_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-housekeeper":
        return _housekeeper_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-starlight-engine-replica":
        return _starlight_engine_replica_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-drill-rig-red-axis":
        return _drill_rig_red_axis_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "defense-big-cylinder":
        return _big_cylinder_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "support-bashful-demon":
        return _bashful_demon_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "support-kaboom-the-cannon":
        return _kaboom_the_cannon_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "defense-peacekeeper-specialized":
        return _peacekeeper_specialized_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "anomaly-roaring-ride":
        return _roaring_ride_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-box-cutter":
        return _box_cutter_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "defense-tremor-trigram-vessel":
        return _tremor_trigram_vessel_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "rupture-grill-o-wisp":
        return _grill_o_wisp_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-cannon-rotor":
        return _cannon_rotor_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "support-unfettered-game-ball":
        return _unfettered_game_ball_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-six-shooter":
        return _six_shooter_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "rupture-krakens-cradle":
        return _krakens_cradle_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "defense-tusks-of-fury":
        return _tusks_of_fury_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-hailstorm-shrine":
        return _hailstorm_shrine_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "stun-hellfire-gears":
        return _hellfire_gears_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-restrained":
        return _restrained_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-blazing-laurel":
        return _blazing_laurel_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-flamemaker-shaker":
        return _flamemaker_shaker_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-fusion-compiler":
        return _fusion_compiler_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-timeweaver":
        return _timeweaver_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "stun-jade-tea":
        return _jade_tea_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-stinging-razor":
        return _stinging_razor_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-sunfall-edge":
        return _sunfall_edge_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-hellhound-boomstick":
        return _hellhound_boomstick_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-night-harps":
        return _night_harps_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "anomaly-bird-dream":
        return _bird_dream_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "defense-sweetbunny":
        return _sweetbunny_rules(raw, build_input, talent, source, eligibility, owner_capabilities)
    if effect_family == "rupture-cyan-cage":
        return _cyan_cage_rules(raw, build_input, talent, source, eligibility, owner_capabilities)
    if effect_family == "attack-fuyuan-clean":
        return _fuyuan_clean_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "stun-fox-furnace":
        return _fox_furnace_rules(raw, build_input, talent, source, eligibility, owner_capabilities)
    if effect_family == "attack-machinery-seed":
        return _machinery_seed_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "rupture-vajra":
        return _vajra_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "stun-last-night":
        return _last_night_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "anomaly-soul-in-shell":
        return _soul_in_shell_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "stun-neon-fantasy":
        return _neon_fantasy_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-scale-tooth":
        return _scale_tooth_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "rupture-glowing-helm":
        return _glowing_helm_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "anomaly-moon-cuts-frost":
        return _moon_cuts_frost_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "attack-eclipse-remains":
        return _eclipse_remains_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "anomaly-luxury-core":
        return _luxury_core_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "stun-head-attendant":
        return _head_attendant_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
    if effect_family == "anomaly-returning-feather":
        return _returning_feather_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "attack-cavalry-praise":
        return _cavalry_praise_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "vanguard-crimson-desire":
        return _crimson_desire_rules(raw, build_input, talent, source, eligibility)
    if effect_family == "stun-scarlet-moon-coffin":
        return _scarlet_moon_coffin_rules(
            raw, build_input, talent, source, eligibility, owner_capabilities
        )
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
        return _steel_cushion_rules(
            raw,
            build_input,
            talent,
            source,
            eligibility,
            owner_capabilities,
        )
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
        default_value=True,
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
                label=f"{raw.name}·场上异常时对目标增伤",
                eligibility=eligibility,
                condition_ids=(field_anomaly_id,),
                effects=(target_damage_effect,),
            ),
        ),
        (field_anomaly_condition,),
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


def _cattery_luck_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    ex_id, ex_condition = _condition(
        raw,
        owner,
        "ex-special-defense-buff-active",
        f"{raw.name}：强化特殊技触发的额外防御力增益当前有效",
        "释放强化特殊技时，防御力额外提升，持续40秒",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="defense-percent",
            label=f"{raw.name}·防御力提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="defense-percent",
                    path=CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
                    value=float(values["defense_percent"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-special-defense-percent",
            label=f"{raw.name}·强化特殊技后额外防御力提升",
            eligibility=eligibility,
            condition_ids=(ex_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-special-defense-percent",
                    path=CalculationNode.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
                    value=float(values["ex_special_defense_percent"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (ex_condition,)


def _boisterous_echoes_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    anomaly_id, anomaly_condition = _condition(
        raw,
        owner,
        "target-anomaly-active",
        f"{raw.name}：本次伤害目标处于属性异常状态",
        "装备者攻击处于属性异常状态下的敌人时",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomalous-target-damage",
            label=f"{raw.name}·攻击异常目标时伤害提升",
            eligibility=eligibility,
            condition_ids=(anomaly_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomalous-target-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["damage_bonus_vs_anomalous_target"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _result_only_wengine_rules(
            raw, build_input, source, eligibility, "disorder-energy-restore"
        )[0],
    ), (anomaly_condition,)


def _cauldron_of_clarity_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    damage_rule_suffix = "ex-special-damage-per-stack"
    damage_rule_id = _instance_rule_id(raw.wengine_id, owner, damage_rule_suffix)
    damage_effect = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="ex-special-damage-per-stack",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(values["damage_bonus_per_stack"]),
    )
    crit_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="crit-rate-at-max-stacks",
        path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        value=float(values["crit_rate_at_max_stacks"]),
        condition=RuleStackCondition(
            damage_rule_id,
            int(values["max_stacks"]),
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=damage_rule_suffix,
            label=f"{raw.name}·当前增益层数伤害提升",
            eligibility=eligibility,
            effects=(damage_effect,),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-rate-at-max-stacks",
            label=f"{raw.name}·三层时暴击率提升",
            eligibility=eligibility,
            effects=(crit_effect,),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _simmering_pot_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    active_id, active_condition = _condition(
        raw,
        owner,
        "assist-attack-buffs-active",
        f"{raw.name}：支援突击触发的失衡与伤害增益当前有效",
        "发动支援突击时，装备者获得失衡值与伤害增益，持续30秒",
    )
    effects = (
        _wearer_modifier(
            raw=raw,
            owner=owner,
            source=source,
            suffix="assist-attack-daze",
            path=CalculationNode.DAZE_OUTGOING_BONUS,
            value=float(talent.numeric_values["daze_bonus"]),
        ),
        _wearer_modifier(
            raw=raw,
            owner=owner,
            source=source,
            suffix="assist-attack-damage",
            path=CalculationNode.DAMAGE_NORMAL_BONUS,
            value=float(talent.numeric_values["damage_bonus"]),
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="assist-attack-buffs",
                label=f"{raw.name}·支援突击后失衡值与伤害提升",
                eligibility=eligibility,
                condition_ids=(active_id,),
                effects=effects,
                diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
            ),
        ),
        (active_condition,),
    )


def _bloodmarrow_coffer_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "overcap-crit-damage"),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            condition=DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=PanelStatDerivedValue(
                source_character_id=owner,
                source_node=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                coefficient=Resolved(float(values["damage_bonus_per_crit_rate_ratio"])),
                cap_max=Resolved(float(values["damage_bonus_cap"])),
                threshold=Resolved(float(values["crit_rate_threshold"])),
            ),
        ),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="overcap-crit-damage",
                label=f"{raw.name}·超过100%暴击率的伤害加成",
                eligibility=eligibility,
                effects=(effect,),
            ),
        ),
        (),
    )


def _demara_battery_ii_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    recovery_id, recovery_condition = _condition(
        raw,
        owner,
        "energy-recovery-efficiency-active",
        f"{raw.name}：闪避反击或支援攻击触发的能量获得效率增益当前有效",
        "闪避反击或支援攻击命中敌人时，能量获得效率提升，持续8秒",
    )
    limitation = _wengine_result_diagnostics(raw, build_input.refinement)
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="electric-damage",
            label=f"{raw.name}·电属性伤害提升",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="electric-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["electric_damage_bonus"]),
                    filters=(element_scope_filter(Element.ELECTRIC),),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="energy-recovery-efficiency",
            label=f"{raw.name}·触发后的能量获得效率增益",
            eligibility=eligibility,
            condition_ids=(recovery_id,),
            effects=(),
            diagnostics=limitation,
        ),
    ), (recovery_condition,)


def _housekeeper_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    backline_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="backline-energy-regeneration",
        path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        value=float(values["energy_regen_flat_while_backline"]),
        condition=NotCondition(
            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="backline-energy-regeneration",
            label=f"{raw.name}·后场能量自动回复提升",
            eligibility=eligibility,
            effects=(backline_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="physical-damage-per-stack",
            label=f"{raw.name}·当前物理伤害增益层数",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="physical-damage-per-stack",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["physical_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.PHYSICAL),),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
        ),
    ), ()


def _starlight_engine_replica_rules(
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
        "distant-physical-hit-buff-active",
        f"{raw.name}：6米外普通或冲刺攻击触发的物理增益当前有效",
        "普通攻击或冲刺攻击命中6米外的敌人时，装备者对目标造成的物理伤害提升，持续8秒",
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="distant-physical-damage",
                label=f"{raw.name}·远距离命中后的物理伤害提升",
                eligibility=eligibility,
                condition_ids=(active_id,),
                effects=(
                    _wearer_modifier(
                        raw=raw,
                        owner=owner,
                        source=source,
                        suffix="distant-physical-damage",
                        path=CalculationNode.DAMAGE_NORMAL_BONUS,
                        value=float(
                            values["physical_damage_bonus_beyond_minimum_distance"]
                        ),
                        filters=(element_scope_filter(Element.PHYSICAL),),
                    ),
                ),
            ),
        ),
        (active_condition,),
    )


def _drill_rig_red_axis_rules(
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
        "ex-special-or-chain-electric-buff-active",
        f"{raw.name}：强化特殊技或连携技触发的普攻/冲刺电伤增益当前有效",
        "发动强化特殊技或连携技时，普通攻击和冲刺攻击造成的电属性伤害提升，持续10秒",
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="basic-dash-electric-damage",
                label=f"{raw.name}·普通攻击与冲刺攻击电伤提升",
                eligibility=_any_capability_eligibility(
                    eligibility,
                    capabilities,
                    scopes=(
                        (
                            Element.ELECTRIC,
                            SkillGroup.BASIC_ATTACK,
                            (DamageTag.BASIC_ATTACK,),
                        ),
                        (
                            Element.ELECTRIC,
                            SkillGroup.DODGE,
                            (DamageTag.DASH_ATTACK,),
                        ),
                    ),
                ),
                condition_ids=(active_id,),
                effects=(
                    _wearer_modifier(
                        raw=raw,
                        owner=owner,
                        source=source,
                        suffix="basic-dash-electric-damage",
                        path=CalculationNode.DAMAGE_NORMAL_BONUS,
                        value=float(values["electric_damage_bonus"]),
                        filters=(
                            AnyFilter(
                                (
                                    DamageTagFilter(DamageTag.BASIC_ATTACK),
                                    DamageTagFilter(DamageTag.DASH_ATTACK),
                                )
                            ),
                            element_scope_filter(Element.ELECTRIC),
                        ),
                    ),
                ),
            ),
        ),
        (active_condition,),
    )


def _wengine_extra_damage_effect(
    *,
    raw: WEngineRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    original_text: str,
    template_available: bool,
) -> EventCreationEffect:
    effect_id = EffectId(_instance_effect_id(raw.wengine_id, owner, suffix))
    if template_available:
        result = EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            event_template_id=_instance_event_template_id(raw.wengine_id, owner, suffix),
            unique_per_source_event=True,
        )
    else:
        result = EventCreationResult(
            event_kind=BattleEventKind.DAMAGE,
            unresolved_template=Unresolved(
                reason=UnresolvedReason.MISSING_DATA,
                notes=(
                    "The equipped character's native element is required to resolve "
                    "this standalone damage component."
                ),
                original_text=original_text,
            ),
            unique_per_source_event=True,
        )
    return EventCreationEffect(
        rule=_effect_rule(
            effect_id=str(effect_id),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM,
            filters=(
                DamageDealerFilter(owner),
                DamageTypeFilter(DamageType.DIRECT),
                NotFilter(CreatedByEffectFilter(effect_id)),
            ),
        ),
        result=result,
    )


def _big_cylinder_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    owner_capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    proc_id, proc_condition = _condition(
        raw,
        owner,
        "defense-counter-damage-ready",
        f"{raw.name}：受击后的防御追击伤害正由本次攻击触发",
        "受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者防御力倍率伤害",
    )
    extra_effect = _wengine_extra_damage_effect(
        raw=raw,
        owner=owner,
        source=source,
        suffix="defense-counter-extra-damage",
        original_text=talent.text,
        template_available=owner_capabilities.native_element is not None,
    )
    return (
        _result_only_wengine_rules(
            raw, build_input, source, eligibility, "incoming-damage-reduction"
        )[0],
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="defense-counter-extra-damage",
            label=f"{raw.name}·受击后的防御追击伤害",
            eligibility=eligibility,
            condition_ids=(proc_id,),
            effects=(extra_effect,),
        ),
    ), (proc_condition,)


def _bashful_demon_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    team_buff_id, team_buff_condition = _condition(
        raw,
        owner,
        "ex-special-team-attack-buff-active",
        f"{raw.name}：强化特殊技触发的全队攻击力增益当前有效",
        "发动强化特殊技时，全队角色攻击力提升，持续12秒",
    )
    ice_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ICE,
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ice-damage",
            label=f"{raw.name}·冰属性伤害提升",
            eligibility=ice_eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ice-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ice_damage_bonus"]),
                    filters=(element_scope_filter(Element.ICE),),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-attack-per-stack",
            label=f"{raw.name}·强化特殊技后的全队攻击力层数",
            eligibility=eligibility,
            condition_ids=(team_buff_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-attack-per-stack",
                    path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    value=float(values["team_attack_per_stack"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            non_stacking_group_id="wengine:13113:team-attack-buff",
        ),
    ), (team_buff_condition,)


def _kaboom_the_cannon_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    values = talent.numeric_values
    return (
        _rule(
            raw=raw,
            owner=build_input.equipped_character_id,
            source=source,
            suffix="team-attack-per-ally-stack",
            label=f"{raw.name}·当前全队攻击力增益层数",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=build_input.equipped_character_id,
                    source=source,
                    suffix="team-attack-per-ally-stack",
                    path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    value=float(values["team_attack_per_stack"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            non_stacking_group_id="wengine:13115:team-attack-stack-buff",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _peacekeeper_specialized_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    shield_id, shield_condition = _condition(
        raw,
        owner,
        "shield-active",
        f"{raw.name}：护盾当前有效",
        "拥有护盾时，装备者的能量自动回复提升",
    )
    can_use_ex = (
        capabilities.can_use_skill_group(SkillGroup.SPECIAL_ATTACK)
        and capabilities.can_produce_tag(DamageTag.EX_SPECIAL_ATTACK)
    )
    can_use_assist = (
        capabilities.can_use_skill_group(SkillGroup.ASSIST)
        and capabilities.can_produce_tag(DamageTag.ASSIST)
    )
    buildup_eligibility = (
        eligibility if can_use_ex or can_use_assist else RuleEligibility.INELIGIBLE
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="shielded-energy-regeneration",
            label=f"{raw.name}·护盾下能量自动回复",
            eligibility=eligibility,
            condition_ids=(shield_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="shielded-energy-regeneration",
                    path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
                    value=float(talent.numeric_values["energy_regen_flat_while_shielded"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-assist-anomaly-buildup",
            label=f"{raw.name}·强化特殊技与支援突击积蓄提升",
            eligibility=buildup_eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-assist-anomaly-buildup",
                    path=CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    value=float(talent.numeric_values["anomaly_buildup_bonus"]),
                    filters=(
                        AnyFilter(
                            (
                                DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                                DamageTagFilter(DamageTag.ASSIST),
                            )
                        ),
                    ),
                ),
            ),
        ),
    ), (shield_condition,)


def _roaring_ride_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    attack_id, attack_condition = _condition(
        raw,
        owner,
        "random-attack-buff-active",
        f"{raw.name}：随机攻击力增益当前有效",
        talent.text,
    )
    proficiency_id, proficiency_condition = _condition(
        raw,
        owner,
        "random-anomaly-proficiency-buff-active",
        f"{raw.name}：随机异常精通增益当前有效",
        talent.text,
    )
    buildup_id, buildup_condition = _condition(
        raw,
        owner,
        "random-anomaly-buildup-buff-active",
        f"{raw.name}：随机异常积蓄效率增益当前有效",
        talent.text,
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="random-attack-buff",
            label=f"{raw.name}·随机攻击力增益",
            eligibility=eligibility,
            condition_ids=(attack_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="random-attack-buff",
                    path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    value=float(values["attack_percent"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="random-anomaly-proficiency-buff",
            label=f"{raw.name}·随机异常精通增益",
            eligibility=eligibility,
            condition_ids=(proficiency_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="random-anomaly-proficiency-buff",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_flat"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="random-anomaly-buildup-buff",
            label=f"{raw.name}·随机异常积蓄效率增益",
            eligibility=eligibility,
            condition_ids=(buildup_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="random-anomaly-buildup-buff",
                    path=CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    value=float(values["anomaly_buildup_bonus"]),
                ),
            ),
        ),
    ), (attack_condition, proficiency_condition, buildup_condition)


def _box_cutter_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    active_id, active_condition = _condition(
        raw,
        owner,
        "follow-up-attack-buffs-active",
        f"{raw.name}：追击触发的物理伤害和失衡增益当前有效",
        "发动追加攻击时，装备者物理伤害和失衡值提升，持续10秒",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="follow-up-attack-damage-daze",
            label=f"{raw.name}·追击后的物理伤害与失衡提升",
            eligibility=eligibility,
            condition_ids=(active_id,),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="physical-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(talent.numeric_values["physical_damage_bonus"]),
                    filters=(element_scope_filter(Element.PHYSICAL),),
                ),
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="daze",
                    path=CalculationNode.DAZE_OUTGOING_BONUS,
                    value=float(talent.numeric_values["daze_bonus"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (active_condition,)


def _tremor_trigram_vessel_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    damage = _wearer_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="ex-ultimate-damage",
        path=CalculationNode.DAMAGE_NORMAL_BONUS,
        value=float(values["ex_special_ultimate_damage_bonus"]),
        filters=(
            AnyFilter(
                (
                    DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                    DamageTagFilter(DamageTag.ULTIMATE),
                )
            ),
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-ultimate-damage",
            label=f"{raw.name}·强化特殊技与终结技伤害提升",
            eligibility=eligibility,
            effects=(damage,),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _result_only_wengine_rules(
            raw, build_input, source, eligibility, "team-energy-restore"
        )[0],
    ), ()


def _grill_o_wisp_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    hp_loss_id, hp_loss_condition = _condition(
        raw,
        owner,
        "owner-hp-lowered-crit-buff-active",
        f"{raw.name}：装备者生命值降低触发的暴击率增益当前有效",
        "装备者的生命值降低时，暴击率提升，持续5秒",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="fire-damage",
            label=f"{raw.name}·火属性伤害提升",
            eligibility=_capability_eligibility(
                eligibility,
                capabilities,
                element=Element.FIRE,
            ),
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="fire-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["fire_damage_bonus"]),
                    filters=(element_scope_filter(Element.FIRE),),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-rate-after-hp-loss",
            label=f"{raw.name}·生命值降低后暴击率提升",
            eligibility=eligibility,
            condition_ids=(hp_loss_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-rate-after-hp-loss",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["crit_rate_after_hp_loss"]),
                ),
            ),
        ),
    ), (hp_loss_condition,)


def _cannon_rotor_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    proc_id, proc_condition = _condition(
        raw,
        owner,
        "crit-triggered-extra-damage-current-hit",
        f"{raw.name}：本次攻击触发暴击额外伤害",
        "攻击命中敌人并触发暴击时，额外造成200%攻击力的伤害",
    )
    extra_effect = _wengine_extra_damage_effect(
        raw=raw,
        owner=owner,
        source=source,
        suffix="crit-triggered-extra-damage",
        original_text=talent.text,
        template_available=True,
    )
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
            suffix="crit-triggered-extra-damage",
            label=f"{raw.name}·暴击触发的额外伤害",
            eligibility=eligibility,
            condition_ids=(proc_id,),
            effects=(extra_effect,),
        ),
    ), (proc_condition,)


def _unfettered_game_ball_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    active_id, active_condition = _condition(
        raw,
        owner,
        "attribute-counter-target-crit-buff-active",
        f"{raw.name}：触发属性克制后的目标暴击率增益当前有效",
        "装备者攻击命中敌人并触发属性克制效果后，所有单位对该目标的暴击率提升",
    )
    event_crit_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "target-crit-rate"),
            source=source,
            owner=owner,
            target=EffectTarget.ENEMY,
            filters=(
                AnyFilter(
                    (
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTypeFilter(DamageType.PENETRATION),
                    )
                ),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
            operation=EffectOperation.ADD,
            value=Resolved(float(talent.numeric_values["team_target_crit_rate_bonus"])),
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="target-crit-rate",
            label=f"{raw.name}·当前目标的全队暴击率提升",
            eligibility=eligibility,
            condition_ids=(active_id,),
            effects=(event_crit_effect,),
            non_stacking_group_id="wengine:14002:target-crit-rate",
        ),
    ), (active_condition,)


def _six_shooter_rules(
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
        suffix="ex-special-daze-per-charge",
        path=CalculationNode.DAZE_OUTGOING_BONUS,
        value=float(values["daze_bonus_per_charge"]),
        filters=(DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),),
    )
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="ex-special-daze-per-charge",
                label=f"{raw.name}·强化特殊技当前充能失衡值提升",
                eligibility=eligibility,
                effects=(effect,),
                stack_count=0,
                stack_min=0,
                stack_max=int(values["max_charges"]),
                diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
            ),
        ),
        (),
    )


def _krakens_cradle_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    half_hp_id, half_hp_condition = _condition(
        raw,
        owner,
        "owner-hp-at-or-below-half",
        f"{raw.name}：装备者生命值因降低达到50%或以下",
        "装备者生命值降低至最大值的50%时，暴击率提升",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ice-penetration-damage-per-stack",
            label=f"{raw.name}·当前叠层冰贯穿伤害",
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
                    suffix="ice-penetration-damage-per-stack",
                    path=CalculationNode.PENETRATION_DAMAGE_BONUS,
                    value=float(values["penetration_damage_bonus_per_stack"]),
                    filters=(
                        DamageTypeFilter(DamageType.PENETRATION),
                        element_scope_filter(Element.ICE),
                    ),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-rate-at-half-hp",
            label=f"{raw.name}·生命值降低至半时暴击率提升",
            eligibility=eligibility,
            condition_ids=(half_hp_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-rate-at-half-hp",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    value=float(values["crit_rate_at_half_hp"]),
                ),
            ),
        ),
    ), (half_hp_condition,)


def _tusks_of_fury_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    active_id, active_condition = _condition(
        raw,
        owner,
        "team-parry-perfect-dodge-buffs-active",
        f"{raw.name}：队伍触发破招或极限闪避后的增益当前有效",
        "队伍中任意角色触发破招或极限闪避时，全队伤害与失衡值提升，持续20秒",
    )
    values = talent.numeric_values
    team_damage_effect = _team_damage_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="team-damage-after-parry",
        value=float(values["team_damage_bonus"]),
        target=EffectTarget.TEAM,
    )
    team_daze_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "team-daze-after-parry"),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAZE_OUTGOING_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["team_daze_bonus"])),
        ),
    )
    return (
        _result_only_wengine_rules(
            raw, build_input, source, eligibility, "shield-strength-increase"
        )[0],
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-parry-perfect-dodge-buff",
            label=f"{raw.name}·全队破招/极限闪避增益",
            eligibility=eligibility,
            condition_ids=(active_id,),
            effects=(team_damage_effect, team_daze_effect),
            non_stacking_group_id="wengine:14107:team-parry-buff",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (active_condition,)


def _hailstorm_shrine_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-damage",
            label=f"{raw.name}·暴击伤害提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-damage",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ice-damage-per-stack",
            label=f"{raw.name}·当前叠层冰伤",
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
                    suffix="ice-damage-per-stack",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ice_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.ICE),),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
        ),
    ), ()


def _hellfire_gears_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    backline_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="backline-energy-regeneration",
        path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        value=float(values["energy_regen_flat_while_backline"]),
        condition=NotCondition(
            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)
        ),
    )
    impact_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="ex-special-impact-per-stack",
        path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
        value=float(values["impact_percent_per_stack"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="backline-energy-regeneration",
            label=f"{raw.name}·后场能量自动回复",
            eligibility=eligibility,
            effects=(backline_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-special-impact-per-stack",
            label=f"{raw.name}·当前强化特殊技冲击力层数",
            eligibility=eligibility,
            effects=(impact_effect,),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
        ),
    ), ()


def _restrained_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    basic_tag = (DamageTagFilter(DamageTag.BASIC_ATTACK),)
    return (
        (
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="basic-damage-daze-per-stack",
                label=f"{raw.name}·当前普通攻击命中层数",
                eligibility=eligibility,
                effects=(
                    _wearer_modifier(
                        raw=raw,
                        owner=owner,
                        source=source,
                        suffix="basic-damage-per-stack",
                        path=CalculationNode.DAMAGE_NORMAL_BONUS,
                        value=float(values["basic_damage_bonus_per_stack"]),
                        filters=basic_tag,
                    ),
                    _wearer_modifier(
                        raw=raw,
                        owner=owner,
                        source=source,
                        suffix="basic-daze-per-stack",
                        path=CalculationNode.DAZE_OUTGOING_BONUS,
                        value=float(values["basic_daze_bonus_per_stack"]),
                        filters=basic_tag,
                    ),
                ),
                stack_count=0,
                stack_min=0,
                stack_max=int(values["max_stacks"]),
                diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
            ),
        ),
        (),
    )


def _blazing_laurel_rules(
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
        "assist-impact-buff-active",
        f"{raw.name}：快速支援或极限支援触发的冲击力增益当前有效",
        "发动快速支援或极限支援时，装备者冲击力提升，持续8秒",
    )
    impact_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="assist-impact-buff",
        label=f"{raw.name}·支援触发冲击力提升",
        eligibility=eligibility,
        condition_ids=(impact_id,),
        effects=(
            _panel_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="assist-impact-buff",
                path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
                value=float(values["impact_percent_after_assist"]),
            ),
        ),
    )
    depression_stack_suffix = "depression-target-stacks"
    depression_rule_id = _instance_rule_id(raw.wengine_id, owner, depression_stack_suffix)
    crit_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "depression-crit-damage"),
            source=source,
            owner=owner,
            target=EffectTarget.ENEMY,
            filters=(
                AnyFilter(
                    (
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageTypeFilter(DamageType.PENETRATION),
                    )
                ),
                AnyFilter(
                    (
                        element_scope_filter(Element.ICE),
                        element_scope_filter(Element.FIRE),
                    )
                ),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["depression_crit_damage_bonus_per_stack"])),
        ),
    )
    depression_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix=depression_stack_suffix,
        label=f"{raw.name}·当前目标萎靡层数暴伤",
        eligibility=eligibility,
        effects=(crit_effect,),
        stack_count=0,
        stack_min=0,
        stack_max=int(values["depression_max_stacks"]),
        non_stacking_group_id="wengine:14116:depression-target-crit-damage",
    )
    return (impact_rule, depression_rule), (impact_condition,)


def _flamemaker_shaker_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    backline_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="backline-energy-regeneration",
        path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        value=float(values["energy_regen_flat_while_backline"]),
        condition=NotCondition(
            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)
        ),
    )
    damage_rule_suffix = "ex-assist-damage-per-stack"
    damage_rule_id = _instance_rule_id(raw.wengine_id, owner, damage_rule_suffix)
    ap_active_id, ap_active_condition = _condition(
        raw,
        owner,
        "anomaly-proficiency-buff-active",
        f"{raw.name}：获得伤害增益时层数达到5触发的异常精通提升当前有效",
        "获得伤害提升效果时，若叠加层数大于等于5层，则装备者的异常精通额外提升",
    )
    ap_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-proficiency-at-five-stacks",
        path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
        value=float(values["anomaly_proficiency_bonus_at_threshold"]),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="backline-energy-regeneration",
            label=f"{raw.name}·后场能量自动回复",
            eligibility=eligibility,
            effects=(backline_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=damage_rule_suffix,
            label=f"{raw.name}·当前EX/支援攻击增伤层数",
            eligibility=eligibility,
            effects=(
                _wearer_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="damage-per-stack",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["damage_bonus_per_stack"]),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-proficiency-at-five-stacks",
            label=f"{raw.name}·增伤层数达到5时异常精通提升",
            eligibility=eligibility,
            condition_ids=(ap_active_id,),
            effects=(ap_effect,),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (ap_active_condition,)


def _fusion_compiler_rules(
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
            suffix="anomaly-proficiency-per-stack",
            label=f"{raw.name}·当前异常精通层数",
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
        ),
    ), ()


def _timeweaver_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    anomaly_id, anomaly_condition = _condition(
        raw,
        owner,
        "special-hit-anomalous-target-ap-buff-active",
        f"{raw.name}：特殊技命中异常目标后的精通增益当前有效",
        "特殊技或强化特殊技命中处于属性异常状态下的敌人时，装备者异常精通提升，持续15秒",
    )
    electric_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ELECTRIC,
    )
    buildup_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "electric-buildup-efficiency"),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM,
            filters=(
                DamageDealerFilter(owner),
                element_scope_filter(Element.ELECTRIC),
            ),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["electric_buildup_efficiency"])),
        ),
    )
    disorder_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "over-threshold-disorder-damage"),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM,
            condition=AllCondition(
                (
                    DynamicIdentityCondition(DynamicIdentity.DISORDER_TRIGGER),
                    PanelStatThresholdCondition(
                        owner,
                        CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                        float(values["disorder_ap_threshold"]),
                    ),
                )
            ),
            filters=(DamageTypeFilter(DamageType.DISORDER),),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["disorder_damage_bonus"])),
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="electric-buildup-efficiency",
            label=f"{raw.name}·电属性异常积蓄效率提升",
            eligibility=electric_eligibility,
            effects=(buildup_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="special-hit-anomalous-target-ap-buff",
            label=f"{raw.name}·命中异常目标后异常精通提升",
            eligibility=eligibility,
            condition_ids=(anomaly_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="special-hit-anomalous-target-ap-buff",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_on_anomalous_target"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="over-threshold-disorder-damage",
            label=f"{raw.name}·异常精通达375后的紊乱伤害提升",
            eligibility=eligibility,
            effects=(disorder_effect,),
        ),
    ), (anomaly_condition,)


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
    requested_groups = (
        ((skill_group,) if skill_group is not None else ()) + skill_groups
    )
    if capabilities.damage_scopes is not None and (
        element is not None or requested_groups or tags
    ):
        if not capabilities.can_produce_damage_scope(
            element=element,
            skill_groups=requested_groups,
            tags=tags,
        ):
            return RuleEligibility.INELIGIBLE
    else:
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


def _any_capability_eligibility(
    base_eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
    *,
    scopes: tuple[tuple[Element | None, SkillGroup | None, tuple[DamageTag, ...]], ...],
) -> RuleEligibility:
    return (
        RuleEligibility.ELIGIBLE
        if any(
            _capability_eligibility(
                base_eligibility,
                capabilities,
                element=element,
                skill_group=skill_group,
                tags=tags,
            )
            is RuleEligibility.ELIGIBLE
            for element, skill_group, tags in scopes
        )
        else RuleEligibility.INELIGIBLE
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


def _owner_event_modifier(
    *,
    raw: WEngineRawRecord,
    owner: CharacterId,
    source: RuleSource,
    suffix: str,
    path: CalculationNode,
    value: float,
    filters=(),
    condition=None,
) -> ModifierEffect:
    """Apply a wearer's event effect to that dealer, including off-field events."""

    dealer_condition = DynamicIdentityCondition(DynamicIdentity.DAMAGE_DEALER)
    if condition is not None:
        dealer_condition = AllCondition((dealer_condition, condition))
    return ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, suffix),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM,
            condition=dealer_condition,
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
        stack_count=stack_max if stack_max is not None else stack_count,
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
    owner_capabilities: EquipmentOwnerCapabilities,
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
    automatic_stunned_back_hit = (
        NEKOMATA_C1_STUN_BACK_HIT_MECHANISM in owner_capabilities.mechanisms
    )
    back_filters = (
        (NotFilter(EnemyStateFilter(StateId("state:enemy:stunned"))),)
        if automatic_stunned_back_hit
        else ()
    )
    rules = [
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
                    filters=back_filters,
                ),
            ),
        ),
    ]
    if automatic_stunned_back_hit:
        rules.append(
            _rule(
                raw=raw,
                owner=owner,
                source=source,
                suffix="nekomata-c1-stunned-target-back-attack-damage",
                label=f"{raw.name}·猫又1影失衡目标背击增伤",
                eligibility=eligibility,
                effects=(
                    _wearer_modifier(
                        raw=raw,
                        owner=owner,
                        source=source,
                        suffix="c1-stunned-back-attack-damage",
                        path=CalculationNode.DAMAGE_NORMAL_BONUS,
                        value=float(values["back_attack_damage_bonus"]),
                        filters=(EnemyStateFilter(StateId("state:enemy:stunned")),),
                    ),
                ),
            )
        )
    return tuple(rules), (back_condition,)


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
            eligibility=_any_capability_eligibility(
                eligibility,
                capabilities,
                scopes=(
                    (
                        Element.ETHER,
                        SkillGroup.BASIC_ATTACK,
                        (DamageTag.BASIC_ATTACK,),
                    ),
                    (Element.ETHER, SkillGroup.DODGE, (DamageTag.DASH_ATTACK,)),
                ),
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
    energy_regen_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="energy-regen-flat",
        path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        value=float(talent.numeric_values["energy_regen_flat"]),
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
            non_stacking_group_id="wengine:13103:treasure-chest:team-damage",
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="energy-regen-flat",
            label=f"{raw.name}·装备者能量自动回复提升",
            eligibility=eligibility,
            condition_ids=(condition_id,),
            effects=(energy_regen_effect,),
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
    physical_eligible = _any_capability_eligibility(
        eligibility,
        owner_capabilities,
        scopes=(
            (
                Element.PHYSICAL,
                SkillGroup.SPECIAL_ATTACK,
                (DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
            ),
            (Element.PHYSICAL, SkillGroup.ULTIMATE, (DamageTag.ULTIMATE,)),
        ),
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


def _instance_event_template_id(
    wengine_id: WEngineId,
    owner: CharacterId,
    suffix: str,
) -> EventTemplateId:
    return EventTemplateId(
        f"template:{wengine_id}:owner:{_owner_token(owner)}:{suffix}"
    )


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


def _jade_tea_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    team_active_id, team_active_condition = _condition(
        raw,
        owner,
        "tea-threshold-team-damage-active",
        f"{raw.name}：达到15层时触发的全队伤害增益当前有效",
        "获得茶劲时，若装备者拥有的茶劲层数大于等于15层，全队角色造成的伤害提升，持续10秒",
    )
    impact_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="impact-per-tea-stack",
        label=f"{raw.name}·当前茶劲冲击力",
        eligibility=eligibility,
        effects=(
            _panel_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="impact-per-tea-stack",
                path=CalculationNode.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS,
                value=float(values["impact_percent_per_stack"]),
            ),
        ),
        stack_count=0,
        stack_min=0,
        stack_max=int(values["max_stacks"]),
    )
    team_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="tea-threshold-team-damage",
        label=f"{raw.name}·茶劲达到15层时的全队伤害提升",
        eligibility=eligibility,
        condition_ids=(team_active_id,),
        effects=(
            _team_damage_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="tea-threshold-team-damage",
                value=float(values["team_damage_bonus_at_threshold"]),
                target=EffectTarget.TEAM,
            ),
        ),
        non_stacking_group_id="wengine:14125:tea-threshold-team-damage",
        diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
    )
    return (impact_rule, team_rule), (team_active_condition,)


def _stinging_razor_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    stack_suffix = "physical-damage-per-hunter-intent"
    stack_rule_id = _instance_rule_id(raw.wengine_id, owner, stack_suffix)
    damage_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix=stack_suffix,
        label=f"{raw.name}·当前猎意物理伤害",
        eligibility=eligibility,
        effects=(
            _owner_event_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="physical-damage-per-hunter-intent",
                path=CalculationNode.DAMAGE_NORMAL_BONUS,
                value=float(values["physical_damage_bonus_per_stack"]),
                filters=(element_scope_filter(Element.PHYSICAL),),
            ),
        ),
        stack_count=0,
        stack_min=0,
        stack_max=int(values["max_stacks"]),
        diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
    )
    buildup_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="buildup-efficiency-at-max-hunter-intent",
        label=f"{raw.name}·猎意满层时属性异常积蓄效率",
        eligibility=eligibility,
        effects=(
            _owner_event_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="buildup-efficiency-at-max-hunter-intent",
                path=CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                value=float(values["anomaly_buildup_efficiency_at_max"]),
                condition=RuleStackCondition(stack_rule_id, int(values["max_stacks"])),
            ),
        ),
        diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
    )
    return (damage_rule, buildup_rule), ()


def _sunfall_edge_rules(
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
        "zero-degree-execution-active",
        f"{raw.name}：强化特殊技/连携技/终结技造成冰伤后零度处刑宣言当前有效",
        "强化特殊技、连携技或终结技造成冰属性伤害时，获得零度处刑宣言效果，持续3秒；效果期间角色命中敌人时无视防御力",
    )
    trigger_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ICE,
        skill_groups=(
            SkillGroup.SPECIAL_ATTACK,
            SkillGroup.CHAIN_ATTACK,
            SkillGroup.ULTIMATE,
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-damage",
            label=f"{raw.name}·暴击伤害提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-damage",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="zero-degree-execution-defense-ignore",
            label=f"{raw.name}·零度处刑宣言期间无视防御",
            eligibility=trigger_eligibility,
            condition_ids=(active_id,),
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="zero-degree-execution-defense-ignore",
                    path=CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    value=float(values["defense_ignore_bonus"]),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (active_condition,)


def _hellhound_boomstick_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    follow_up_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.FIRE,
        tags=(DamageTag.FOLLOW_UP_ATTACK,),
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
            suffix="defense-ignore-per-stack",
            label=f"{raw.name}·追击火伤触发的当前无视防御层数",
            eligibility=follow_up_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="defense-ignore-per-stack",
                    path=CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    value=float(values["defense_ignore_per_stack"]),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _night_harps_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    benefit_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.FIRE,
        skill_groups=(SkillGroup.CHAIN_ATTACK, SkillGroup.ULTIMATE),
    )
    fire_chain_ultimate = (
        AnyFilter(
            (
                DamageTagFilter(DamageTag.CHAIN_ATTACK),
                DamageTagFilter(DamageTag.ULTIMATE),
            )
        ),
        element_scope_filter(Element.FIRE),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-damage",
            label=f"{raw.name}·暴击伤害提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-damage",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="fire-resistance-ignore-per-stack",
            label=f"{raw.name}·当前羁绊层数的连携/终结火抗无视",
            eligibility=benefit_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="fire-resistance-ignore-per-stack",
                    path=CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    value=float(values["fire_resistance_ignore_per_stack"]),
                    filters=fire_chain_ultimate,
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _bird_dream_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    ap_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ETHER,
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-buildup-efficiency",
            label=f"{raw.name}·属性异常积蓄效率提升",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomaly-buildup-efficiency",
                    path=CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    value=float(values["anomaly_buildup_efficiency"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-proficiency-per-ether-stack",
            label=f"{raw.name}·以太伤害触发的当前异常精通层数",
            eligibility=ap_eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomaly-proficiency-per-ether-stack",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_per_stack"]),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _sweetbunny_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    veil_id, veil_condition = _condition(
        raw,
        owner,
        "ether-veil-team-crit-damage-active",
        f"{raw.name}：装备者开启或延长以太帷幕后全队暴伤提升当前有效",
        "装备者开启或延长以太帷幕时，使全队角色的暴击伤害提升，持续60秒",
    )
    veil_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        mechanism="zhao-ether-curtain",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="energy-regen-flat",
            label=f"{raw.name}·能量自动回复",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="energy-regen-flat",
                    path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
                    value=float(values["energy_regen_flat_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-attack-hp",
            label=f"{raw.name}·全队攻击力与最大生命值提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-attack",
                    path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
                    value=float(values["team_attack_percent"]),
                    target=EffectTarget.TEAM,
                ),
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-hp",
                    path=CalculationNode.CHARACTER_COMBAT_HP_PERCENT_BONUS,
                    value=float(values["team_hp_percent"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            non_stacking_group_id="wengine:14134:team-attack-hp",
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-crit-damage-after-ether-veil",
            label=f"{raw.name}·帷幕后全队暴击伤害提升",
            eligibility=veil_eligibility,
            condition_ids=(veil_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-crit-damage-after-ether-veil",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["team_crit_damage_bonus"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (veil_condition,)


def _cyan_cage_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    ether_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ETHER,
        skill_groups=(SkillGroup.SPECIAL_ATTACK, SkillGroup.ULTIMATE),
    )
    ex_ultimate_tags = AnyFilter(
        (
            DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
            DamageTagFilter(DamageTag.ULTIMATE),
        )
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
            suffix="ether-damage-per-cyan-journey-stack",
            label=f"{raw.name}·当前青溟同行以太伤害层数",
            eligibility=ether_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ether-damage-per-cyan-journey-stack",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ether_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.ETHER),),
                ),
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-ultimate-ether-penetration-per-cyan-journey-stack",
                    path=CalculationNode.PENETRATION_DAMAGE_BONUS,
                    value=float(
                        values["ultimate_ex_penetration_damage_bonus_per_stack"]
                    ),
                    filters=(ex_ultimate_tags, element_scope_filter(Element.ETHER)),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _fuyuan_clean_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    stack_suffix = "crit-damage-per-hit-category-stack"
    stack_rule_id = _instance_rule_id(raw.wengine_id, owner, stack_suffix)
    electric_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ELECTRIC,
    )
    full_stack_rule = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="electric-damage-at-three-stacks",
        label=f"{raw.name}·3层时电属性伤害提升",
        eligibility=electric_eligibility,
        effects=(
            _owner_event_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="electric-damage-at-three-stacks",
                path=CalculationNode.DAMAGE_NORMAL_BONUS,
                value=float(values["electric_damage_bonus_at_max_stacks"]),
                filters=(element_scope_filter(Element.ELECTRIC),),
                condition=RuleStackCondition(stack_rule_id, int(values["max_stacks"])),
            ),
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="crit-damage",
            label=f"{raw.name}·暴击伤害提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-damage",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=stack_suffix,
            label=f"{raw.name}·普通/特殊/追加攻击的当前暴伤层数",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-damage-per-hit-category-stack",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_per_stack"]),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
        ),
        full_stack_rule,
    ), ()


def _fox_furnace_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    fire_trigger_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.FIRE,
        skill_groups=(SkillGroup.CHAIN_ATTACK, SkillGroup.ULTIMATE),
    )
    ex_chain_ultimate_tags = AnyFilter(
        (
            DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
            DamageTagFilter(DamageTag.CHAIN_ATTACK),
            DamageTagFilter(DamageTag.ULTIMATE),
        )
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-chain-ultimate-daze",
            label=f"{raw.name}·强化特殊技/连携技/终结技失衡提升",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-chain-ultimate-daze",
                    path=CalculationNode.DAZE_OUTGOING_BONUS,
                    value=float(values["ex_chain_ultimate_daze_bonus"]),
                    filters=(ex_chain_ultimate_tags,),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-per-fire-chain-ultimate-stack",
            label=f"{raw.name}·火伤连携/终结触发的全队伤害层数",
            eligibility=fire_trigger_eligibility,
            effects=(
                _team_damage_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-damage-per-fire-chain-ultimate-stack",
                    value=float(values["team_damage_bonus_per_stack"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            non_stacking_group_id="wengine:14139:team-damage",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _machinery_seed_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    stack_suffix = "electric-damage-per-stack"
    stack_rule_id = _instance_rule_id(raw.wengine_id, owner, stack_suffix)
    basic_ultimate = AnyFilter(
        (
            DamageTagFilter(DamageTag.BASIC_ATTACK),
            DamageTagFilter(DamageTag.ULTIMATE),
        )
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
            suffix=stack_suffix,
            label=f"{raw.name}·当前增益层数电伤",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="electric-damage-per-stack",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["electric_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.ELECTRIC),),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="basic-ultimate-defense-ignore-at-max-stacks",
            label=f"{raw.name}·满层普通攻击/终结技无视防御",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="defense-ignore-at-max-stacks",
                    path=CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    value=float(values["defense_ignore_at_max_stacks"]),
                    filters=(basic_ultimate,),
                    condition=RuleStackCondition(
                        stack_rule_id,
                        int(values["max_stacks"]),
                    ),
                ),
            ),
        ),
    ), ()


def _vajra_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    fire_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.FIRE,
        skill_group=SkillGroup.SPECIAL_ATTACK,
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
            suffix="fire-penetration-damage-per-stack",
            label=f"{raw.name}·当前火属性贯穿伤害层数",
            eligibility=fire_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="fire-penetration-damage-per-stack",
                    path=CalculationNode.PENETRATION_DAMAGE_BONUS,
                    value=float(values["fire_penetration_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.FIRE),),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _last_night_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    backline_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="backline-energy-regen-flat",
        path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        value=float(values["energy_regen_flat_while_backline"]),
        condition=NotCondition(
            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)
        ),
    )
    physical_ex_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.PHYSICAL,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tags=(DamageTag.EX_SPECIAL_ATTACK,),
    )
    stack_suffix = "ex-special-physical-daze-per-stack"
    stack_rule_id = _instance_rule_id(raw.wengine_id, owner, stack_suffix)
    team_active_id, team_active_condition = _condition(
        raw,
        owner,
        "full-stack-team-crit-damage-active",
        f"{raw.name}：离崖三层触发的全队暴伤增益当前有效",
        "叠加到3层时，全队角色暴击伤害提升，持续40秒",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="backline-energy-regen-flat",
            label=f"{raw.name}·后场能量自动回复",
            eligibility=eligibility,
            effects=(backline_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=stack_suffix,
            label=f"{raw.name}·强化特殊技物理命中的当前失衡层数",
            eligibility=physical_ex_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="daze-per-current-stack",
                    path=CalculationNode.DAZE_OUTGOING_BONUS,
                    value=float(values["daze_bonus_per_stack"]),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-crit-damage-at-max-daze-stacks",
            label=f"{raw.name}·三层时全队暴击伤害提升",
            eligibility=physical_ex_eligibility,
            condition_ids=(team_active_id,),
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-crit-damage-at-max-daze-stacks",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["team_crit_damage_at_max_stacks"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            non_stacking_group_id="wengine:14148:team-crit-damage",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (team_active_condition,)


def _soul_in_shell_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    ether_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ETHER,
    )
    buff_id, buff_condition = _condition(
        raw,
        owner,
        "ether-frontfield-boost-active",
        f"{raw.name}：以太装备者进入前场或发动特殊技后获得的增益当前有效",
        "以太属性的装备者进入前场或发动特殊技/强化特殊技时获得增益；换回后场时移除",
    )
    target_anomaly_id, target_anomaly_condition = _condition(
        raw,
        owner,
        "target-attribute-anomaly-active",
        f"{raw.name}：本次伤害目标当前处于属性异常状态",
        "对处于属性异常状态下的敌人造成的伤害提升",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-proficiency-flat",
            label=f"{raw.name}·异常精通提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomaly-proficiency-flat",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_flat_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomalous-target-damage",
            label=f"{raw.name}·异化增益对异常目标伤害提升",
            eligibility=ether_eligibility,
            condition_ids=(buff_id, target_anomaly_id),
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomalous-target-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["damage_bonus_vs_anomalous_target"]),
                    condition=DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="attribute-anomaly-damage",
            label=f"{raw.name}·异化期间属性异常伤害提升",
            eligibility=ether_eligibility,
            condition_ids=(buff_id,),
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="attribute-anomaly-damage",
                    path=CalculationNode.ANOMALY_DAMAGE_BONUS,
                    value=float(values["anomaly_damage_bonus"]),
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    ),
                    condition=AllCondition(
                        (
                            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR),
                            DynamicIdentityCondition(DynamicIdentity.ANOMALY_TRIGGER),
                        )
                    ),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="disorder-damage",
            label=f"{raw.name}·异化期间紊乱伤害提升",
            eligibility=ether_eligibility,
            condition_ids=(buff_id,),
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="disorder-damage",
                    path=CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
                    value=float(values["disorder_damage_bonus"]),
                    filters=(DamageTypeFilter(DamageType.DISORDER),),
                    condition=AllCondition(
                        (
                            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR),
                            DynamicIdentityCondition(DynamicIdentity.DISORDER_TRIGGER),
                        )
                    ),
                ),
            ),
        ),
    ), (buff_condition, target_anomaly_condition)


def _neon_fantasy_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    ether_trigger_eligibility = _any_capability_eligibility(
        eligibility,
        capabilities,
        scopes=(
            (Element.ETHER, SkillGroup.BASIC_ATTACK, (DamageTag.BASIC_ATTACK,)),
            (
                Element.ETHER,
                SkillGroup.SPECIAL_ATTACK,
                (DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK),
            ),
        ),
    )
    team_stack_suffix = "team-damage-per-ether-hit-stack"
    team_stack_rule_id = _instance_rule_id(raw.wengine_id, owner, team_stack_suffix)
    full_stack_ap = _rule(
        raw=raw,
        owner=owner,
        source=source,
        suffix="anomaly-proficiency-at-max-stacks",
        label=f"{raw.name}·两层时装备者异常精通提升",
        eligibility=ether_trigger_eligibility,
        effects=(
            _panel_modifier(
                raw=raw,
                owner=owner,
                source=source,
                suffix="anomaly-proficiency-at-max-stacks",
                path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                value=float(values["anomaly_proficiency_bonus_at_max_stacks"]),
                condition=RuleStackCondition(team_stack_rule_id, int(values["max_stacks"])),
            ),
        ),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-proficiency-flat",
            label=f"{raw.name}·异常精通提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomaly-proficiency-flat",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_flat_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-per-ether-hit-stack",
            label=f"{raw.name}·以太命中后的当前全队伤害层数",
            eligibility=ether_trigger_eligibility,
            effects=(
                _team_damage_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-damage-per-ether-hit-stack",
                    value=float(values["team_damage_bonus_per_stack"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            non_stacking_group_id="wengine:14151:team-damage",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        full_stack_ap,
    ), ()


def _scale_tooth_rules(
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
        "electric-defense-ignore-active",
        f"{raw.name}：能量消耗/接战触发的电属性无视防御增益当前有效",
        "达到能量消耗门槛后获得电伤无视防御增益，接战时直接获得该效果",
    )
    electric_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ELECTRIC,
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
            suffix="electric-defense-ignore",
            label=f"{raw.name}·增益期间电伤无视防御",
            eligibility=electric_eligibility,
            condition_ids=(active_id,),
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="electric-defense-ignore",
                    path=CalculationNode.DAMAGE_DEFENSE_IGNORE,
                    value=float(values["defense_ignore_electric_damage"]),
                    filters=(element_scope_filter(Element.ELECTRIC),),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (active_condition,)


def _glowing_helm_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    physical_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.PHYSICAL,
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
            suffix="physical-penetration-damage-per-stack",
            label=f"{raw.name}·当前物理贯穿伤害层数",
            eligibility=physical_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="physical-penetration-damage-per-stack",
                    path=CalculationNode.PENETRATION_DAMAGE_BONUS,
                    value=float(values["physical_penetration_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.PHYSICAL),),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _moon_cuts_frost_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    ice_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.ICE,
        skill_group=SkillGroup.SPECIAL_ATTACK,
    )
    ice_rule_suffix = "ice-damage-per-special-stack"
    ice_rule_id = _instance_rule_id(raw.wengine_id, owner, ice_rule_suffix)
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=ice_rule_suffix,
            label=f"{raw.name}·当前冰伤层数",
            eligibility=ice_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ice-damage-per-special-stack",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(values["ice_damage_bonus_per_stack"]),
                    filters=(element_scope_filter(Element.ICE),),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="discharge-damage-at-max-stacks",
            label=f"{raw.name}·冰伤两层后的异放伤害提升",
            eligibility=ice_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="discharge-damage-at-max-stacks",
                    path=CalculationNode.DISCHARGE_DAMAGE_BONUS,
                    value=float(values["discharge_damage_bonus_at_max_stacks"]),
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.DISCHARGE),
                    ),
                    condition=RuleStackCondition(ice_rule_id, int(values["max_stacks"])),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _eclipse_remains_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
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
                    value=float(talent.numeric_values["crit_rate_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="pellois-eclipse-ether-resistance-ignore-source-only",
            label=f"{raw.name}·佩洛伊斯专属日蚀效果",
            eligibility=RuleEligibility.INELIGIBLE,
            effects=(),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _luxury_core_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    wind_ex_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.WIND,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tags=(DamageTag.EX_SPECIAL_ATTACK,),
    )
    stack_suffix = "turbulence-weathering-damage-per-stack"
    stack_rule_id = _instance_rule_id(raw.wengine_id, owner, stack_suffix)
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-proficiency-flat",
            label=f"{raw.name}·异常精通提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomaly-proficiency-flat",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_flat_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=stack_suffix,
            label=f"{raw.name}·强化特殊技风属性后的当前乱流/风化层数",
            eligibility=wind_ex_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="turbulence-damage-per-stack",
                    path=CalculationNode.TURBULENCE_DAMAGE_BONUS,
                    value=float(values["turbulence_damage_bonus_per_stack"]),
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.TURBULENCE),
                    ),
                ),
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="wind-attribute-anomaly-damage-per-stack",
                    path=CalculationNode.ANOMALY_DAMAGE_BONUS,
                    value=float(values["wind_anomaly_damage_bonus_per_stack"]),
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                        element_scope_filter(Element.WIND),
                    ),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-anomaly-proficiency-at-max-stacks",
            label=f"{raw.name}·两层时全队异常精通提升",
            eligibility=wind_ex_eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-anomaly-proficiency-at-max-stacks",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["team_anomaly_proficiency_at_max_stacks"]),
                    target=EffectTarget.TEAM,
                    condition=RuleStackCondition(stack_rule_id, int(values["max_stacks"])),
                ),
            ),
            non_stacking_group_id="wengine:14156:team-anomaly-proficiency",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _head_attendant_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    fire_ex_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.FIRE,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tags=(DamageTag.EX_SPECIAL_ATTACK,),
    )
    backline_effect = _panel_modifier(
        raw=raw,
        owner=owner,
        source=source,
        suffix="backline-energy-regen-flat",
        path=CalculationNode.CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS,
        value=float(values["energy_regen_flat_while_backline"]),
        condition=NotCondition(DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR)),
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="impact-flat",
            label=f"{raw.name}·冲击力提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="impact-flat",
                    path=CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
                    value=float(values["impact_flat_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="fire-resistance-ignore",
            label=f"{raw.name}·火属性伤害抗性无视",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="fire-resistance-ignore",
                    path=CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    value=float(values["fire_resistance_ignore"]),
                    filters=(element_scope_filter(Element.FIRE),),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="backline-energy-regen-flat",
            label=f"{raw.name}·后场能量自动回复",
            eligibility=eligibility,
            effects=(backline_effect,),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-per-fire-ex-stack",
            label=f"{raw.name}·火属性强化特殊技后的全队伤害层数",
            eligibility=fire_ex_eligibility,
            effects=(
                _team_damage_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="team-damage-per-fire-ex-stack",
                    value=float(values["team_damage_bonus_per_stack"]),
                    target=EffectTarget.TEAM,
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_team_damage_stacks"]),
            non_stacking_group_id="wengine:14157:team-damage",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), ()


def _returning_feather_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    buff_id, buff_condition = _condition(
        raw,
        owner,
        "mutation-reaction-buffs-active",
        f"{raw.name}：装备者触发异化反应后获得的增益当前有效",
        "装备者触发异化反应时获得自身属性异常伤害与全队伤害提升，持续30秒",
    )
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="anomaly-proficiency-flat",
            label=f"{raw.name}·异常精通提升",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="anomaly-proficiency-flat",
                    path=CalculationNode.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
                    value=float(values["anomaly_proficiency_flat_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-damage-after-mutation-reaction",
            label=f"{raw.name}·异化反应增益期间全队伤害提升",
            eligibility=eligibility,
            condition_ids=(buff_id,),
            effects=(
                ModifierEffect(
                    rule=_effect_rule(
                        effect_id=_instance_effect_id(
                            raw.wengine_id, owner, "team-damage-after-mutation-reaction"
                        ),
                        source=source,
                        owner=owner,
                        target=EffectTarget.TEAM,
                    ),
                    result=ModifierResult(
                        modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
                        operation=EffectOperation.ADD,
                        value=Resolved(float(values["team_damage_bonus"])),
                    ),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="attribute-anomaly-damage",
            label=f"{raw.name}·异化反应增益期间属性异常伤害提升",
            eligibility=eligibility,
            condition_ids=(buff_id,),
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="attribute-anomaly-damage",
                    path=CalculationNode.ANOMALY_DAMAGE_BONUS,
                    value=float(values["anomaly_damage_bonus"]),
                    filters=(
                        DamageTypeFilter(DamageType.ANOMALY),
                        DamageSubtypeFilter(DamageSubtype.ATTRIBUTE_ANOMALY),
                    ),
                    condition=AllCondition(
                        (
                            DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR),
                            DynamicIdentityCondition(DynamicIdentity.ANOMALY_TRIGGER),
                        )
                    ),
                ),
            ),
        ),
        *(
            (
                _rule(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="luminance-attribute-anomaly-damage",
                    label=f"{raw.name}·异化反应增益期间流明耀变伤害提升",
                    eligibility=eligibility,
                    condition_ids=(buff_id,),
                    effects=(
                        _owner_event_modifier(
                            raw=raw,
                            owner=owner,
                            source=source,
                            suffix="luminance-attribute-anomaly-damage",
                            path=CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS,
                            value=float(values["anomaly_damage_bonus"]),
                            filters=(
                                DamageTypeFilter(DamageType.ANOMALY),
                                DamageSubtypeFilter(DamageSubtype.LUMINANCE),
                            ),
                            condition=AllCondition(
                                (
                                    DynamicIdentityCondition(DynamicIdentity.CURRENT_OPERATOR),
                                    DynamicIdentityCondition(DynamicIdentity.LUMINANCE_TRIGGER),
                                )
                            ),
                        ),
                    ),
                ),
            )
            if owner == CharacterId("character:1581")
            else ()
        ),
    ), (buff_condition,)


def _cavalry_praise_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    stack_suffix = "crit-damage-per-blade-edge-stack"
    stack_rule_id = _instance_rule_id(raw.wengine_id, owner, stack_suffix)
    return (
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix=stack_suffix,
            label=f"{raw.name}·当前兵锋暴击伤害层数",
            eligibility=eligibility,
            effects=(
                _panel_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="crit-damage-per-blade-edge-stack",
                    path=CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    value=float(values["crit_damage_bonus_per_stack"]),
                ),
            ),
            stack_count=0,
            stack_min=0,
            stack_max=int(values["max_stacks"]),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ice-resistance-ignore-at-max-stacks",
            label=f"{raw.name}·两层兵锋后冰属性伤害抗性无视",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ice-resistance-ignore-at-max-stacks",
                    path=CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    value=float(values["ice_resistance_ignore_at_max_stacks"]),
                    filters=(element_scope_filter(Element.ICE),),
                    condition=RuleStackCondition(stack_rule_id, int(values["max_stacks"])),
                ),
            ),
        ),
    ), ()


def _crimson_desire_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    sharp_id, sharp_condition = _condition(
        raw,
        owner,
        "electric-sharp-damage-active",
        f"{raw.name}：强化特殊技/毁伤触发的电属性锐化伤害提升当前有效",
        "装备者发动强化特殊技或触发毁伤时，造成的电属性锐化伤害提升，持续40秒",
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
                    value=float(talent.numeric_values["crit_rate_bonus"]),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="electric-damage",
            label=f"{raw.name}·电属性伤害提升",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="electric-damage",
                    path=CalculationNode.DAMAGE_NORMAL_BONUS,
                    value=float(talent.numeric_values["electric_damage_bonus"]),
                    filters=(element_scope_filter(Element.ELECTRIC),),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="electric-sharp-damage-source-only",
            label=f"{raw.name}·电属性锐化伤害提升（暂不结算）",
            eligibility=eligibility,
            condition_ids=(sharp_id,),
            effects=(),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (sharp_condition,)


def _scarlet_moon_coffin_rules(
    raw: WEngineRawRecord,
    build_input: WEngineBuildInput,
    talent: WEngineRawTalent,
    source: RuleSource,
    eligibility: RuleEligibility,
    capabilities: EquipmentOwnerCapabilities,
) -> tuple[tuple[CalculationRuleItem, ...], tuple[ScenarioCondition, ...]]:
    owner = build_input.equipped_character_id
    values = talent.numeric_values
    wind_ex_eligibility = _capability_eligibility(
        eligibility,
        capabilities,
        element=Element.WIND,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        tags=(DamageTag.EX_SPECIAL_ATTACK,),
    )
    team_buff_id, team_buff_condition = _condition(
        raw,
        owner,
        "team-other-wind-ex-damage-active",
        f"{raw.name}：风属性强化特殊技触发的其他队员伤害提升当前有效",
        "发动强化特殊技造成风属性伤害时，全队其他角色造成的伤害提升，持续50秒；该伤害提升效果全队唯一",
    )
    other_team_effect = ModifierEffect(
        rule=_effect_rule(
            effect_id=_instance_effect_id(raw.wengine_id, owner, "team-other-damage"),
            source=source,
            owner=owner,
            target=EffectTarget.TEAM_OTHER,
            filters=(NotFilter(DamageDealerFilter(owner)),),
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.DAMAGE_NORMAL_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(float(values["team_other_damage_bonus"])),
        ),
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
            suffix="wind-resistance-ignore",
            label=f"{raw.name}·风属性伤害抗性无视",
            eligibility=eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="wind-resistance-ignore",
                    path=CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    value=float(values["wind_resistance_ignore"]),
                    filters=(element_scope_filter(Element.WIND),),
                ),
            ),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="ex-special-wind-daze",
            label=f"{raw.name}·强化特殊技风属性失衡提升",
            eligibility=wind_ex_eligibility,
            effects=(
                _owner_event_modifier(
                    raw=raw,
                    owner=owner,
                    source=source,
                    suffix="ex-special-wind-daze",
                    path=CalculationNode.DAZE_OUTGOING_BONUS,
                    value=float(values["ex_special_daze_bonus"]),
                    filters=(
                        DamageTagFilter(DamageTag.EX_SPECIAL_ATTACK),
                        element_scope_filter(Element.WIND),
                    ),
                ),
            ),
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
        _rule(
            raw=raw,
            owner=owner,
            source=source,
            suffix="team-other-damage-after-wind-ex-special",
            label=f"{raw.name}·其他队员当前风伤触发全队伤害提升",
            eligibility=wind_ex_eligibility,
            condition_ids=(team_buff_id,),
            effects=(other_team_effect,),
            non_stacking_group_id="wengine:14162:team-other-damage",
            diagnostics=_wengine_result_diagnostics(raw, build_input.refinement),
        ),
    ), (team_buff_condition,)


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
