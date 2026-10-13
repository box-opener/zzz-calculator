"""Typed damage-event templates emitted by reviewed character compilers."""

from dataclasses import dataclass
from enum import StrEnum

from core.types import (
    AnomalyRecordId,
    AnomalyRecordValueSource,
    DischargeDamageEvent,
    DamageMultiplier,
    CurrentAnomalyEffectStrengthValueSource,
    CurrentAnomalyProficiencyValueSource,
    CurrentMaxHPValueSource,
    CurrentPenetrationForceValueSource,
    SettledDamageValueSource,
    CharacterId,
    CurrentAttackValueSource,
    InitialAttackValueSource,
    CurrentDefenseValueSource,
    DamageType,
    DamageSubtype,
    Element,
    EffectId,
    MoveId,
    NoCritRule,
    RecordedAnomalyCritRule,
    Unresolved,
    StandardCritRule,
    RecordedAnomalyCritRule,
)

from ..ids import RuleItemId, ScenarioParameterId
from ..moves import DamageEventTemplateRef


class FriendlyActorPanelStat(StrEnum):
    ATTACK = "attack"
    IMPACT = "impact"
    ANOMALY_PROFICIENCY = "anomaly_proficiency"
    CRIT_RATE = "crit_rate"
    CRIT_DAMAGE = "crit_damage"


@dataclass(frozen=True, slots=True)
class DirectDamageEventTemplate:
    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    base_source: (
        CurrentAttackValueSource
        | InitialAttackValueSource
        | CurrentDefenseValueSource
        | CurrentMaxHPValueSource
        | CurrentAnomalyProficiencyValueSource
        | CurrentPenetrationForceValueSource
    )
    crit_rule: StandardCritRule
    move_id: MoveId | None
    allow_external_base_source: bool = False
    friendly_actor_owner_id: CharacterId | None = None
    friendly_actor_attack_bonus_effect_id: EffectId | None = None
    friendly_actor_attack_bonus_multiplier: float = 0.0
    friendly_actor_inherited_panel_stats: frozenset[FriendlyActorPanelStat] | None = None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.DIRECT:
            raise ValueError("DirectDamageEventTemplate requires direct damage type")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if (
            self.damage_dealer != self.base_source.character_id
            and not self.allow_external_base_source
        ):
            raise ValueError("base attack source must match damage dealer")
        if self.damage_dealer != self.crit_rule.stat_owner:
            raise ValueError("crit stat owner must match damage dealer")
        if self.friendly_actor_owner_id is None:
            if (
                self.friendly_actor_attack_bonus_effect_id is not None
                or self.friendly_actor_attack_bonus_multiplier != 0.0
                or self.friendly_actor_inherited_panel_stats is not None
            ):
                raise ValueError(
                    "friendly actor inheritance fields require a friendly actor owner"
                )
        else:
            if self.friendly_actor_owner_id == self.damage_dealer:
                raise ValueError("friendly actor identity must differ from its owner")
            if self.ref.skill_group is not None or self.ref.damage_tags or self.move_id is not None:
                raise ValueError(
                    "friendly actor damage must not borrow the owner's move identity"
                )
            if self.friendly_actor_attack_bonus_multiplier < 0:
                raise ValueError("friendly actor attack bonus multiplier must be non-negative")
            if (
                self.friendly_actor_attack_bonus_multiplier > 0
                and self.friendly_actor_attack_bonus_effect_id is None
            ):
                raise ValueError(
                    "friendly actor attack bonus multiplier requires a source effect"
                )
        if self.ref.skill_group is None and self.move_id is not None:
            raise ValueError(
                "a template with a move_id must have an explicit skill_group"
            )


@dataclass(frozen=True, slots=True)
class PenetrationDamageEventTemplate:
    """Typed template for a move that uses the shared rupture formula."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    base_source: CurrentPenetrationForceValueSource
    crit_rule: StandardCritRule
    move_id: MoveId | None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.PENETRATION:
            raise ValueError("PenetrationDamageEventTemplate requires penetration damage")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.damage_dealer != self.base_source.character_id:
            raise ValueError("penetration-force source must match damage dealer")
        if self.damage_dealer != self.crit_rule.stat_owner:
            raise ValueError("crit stat owner must match damage dealer")
        if self.ref.skill_group is None and self.move_id is not None:
            raise ValueError(
                "a template with a move_id must have an explicit skill_group"
            )


@dataclass(frozen=True, slots=True)
class AttributeAnomalyDamageEventTemplate:
    """Typed template for an anomaly event backed by one history record.

    The record ID is explicit because anomaly settlement is historical data,
    not a hidden direct-damage flag.  The application layer may therefore
    reject a request that does not provide the matching ``AnomalyRecord``.
    """

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    anomaly_triggerer: CharacterId
    history_record_source: AnomalyRecordId
    crit_rule: RecordedAnomalyCritRule | NoCritRule | Unresolved
    move_id: MoveId | None
    requires_selected_anomaly_source: bool = False

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("AttributeAnomalyDamageEventTemplate requires anomaly damage type")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.ref.damage_subtype is not DamageSubtype.ATTRIBUTE_ANOMALY:
            raise ValueError("attribute anomaly template requires attribute-anomaly subtype")
        if self.requires_selected_anomaly_source and self.move_id is not None:
            raise ValueError("selected anomaly-source settlement cannot invent a move ID")


@dataclass(frozen=True, slots=True)
class CurrentAttributeAnomalyDamageEventTemplate:
    """Template for a typed anomaly event using the current panel snapshot."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    anomaly_triggerer: CharacterId
    base_source: CurrentAnomalyEffectStrengthValueSource
    crit_rule: NoCritRule
    move_id: MoveId | None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("CurrentAttributeAnomalyDamageEventTemplate requires anomaly damage type")
        if self.ref.damage_subtype is not DamageSubtype.ATTRIBUTE_ANOMALY:
            raise ValueError("current attribute anomaly template requires attribute-anomaly subtype")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.damage_dealer != self.base_source.character_id:
            raise ValueError("current anomaly source must match damage dealer")
        if self.damage_dealer != self.anomaly_triggerer:
            raise ValueError("current anomaly triggerer must match damage dealer")


@dataclass(frozen=True, slots=True)
class DisorderDamageEventTemplate:
    """Typed template for a disorder event backed by one history record."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    disorder_triggerer: CharacterId
    history_record_source: AnomalyRecordId
    crit_rule: NoCritRule
    move_id: MoveId | None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.DISORDER:
            raise ValueError("DisorderDamageEventTemplate requires disorder damage type")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.ref.damage_subtype is not None:
            raise ValueError("disorder template must not have a damage subtype")


@dataclass(frozen=True, slots=True)
class PolarDisorderDamageEventTemplate:
    """Typed Polar Disorder event with a request-selected anomaly record."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    disorder_triggerer: CharacterId
    element: Element | None
    base_polarity_multiplier: float
    anomaly_proficiency_coefficient: float
    move_id: MoveId | None = None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.DISORDER:
            raise ValueError("PolarDisorderDamageEventTemplate requires disorder damage type")
        if self.ref.damage_subtype is not None:
            raise ValueError("Polar Disorder template must not have a subtype")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.ref.skill_group is not None or self.ref.damage_tags:
            raise ValueError("synthetic Polar Disorder must not invent move tags")
        if self.base_polarity_multiplier < 0:
            raise ValueError("base polarity multiplier must be non-negative")
        if self.anomaly_proficiency_coefficient < 0:
            raise ValueError("AP coefficient must be non-negative")


@dataclass(frozen=True, slots=True)
class DischargeDamageEventTemplate:
    """Typed Discharge child tied to an explicitly selected anomaly record.

    ``multiplier_from_source_event`` controls whether the child inherits a
    static triggering event's multiplier.  It is independent of
    ``source_multiplier_by_element``: when that dynamic map is present, its
    values describe a pre-profile source rate and ``source_multiplier_uses_tick_profile``
    explicitly controls whether the selected source's ordinary anomaly tick
    profile is applied.
    """

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    discharge_triggerer: CharacterId
    history_record_source: AnomalyRecordId | None
    crit_rule: RecordedAnomalyCritRule | NoCritRule | Unresolved
    move_id: MoveId | None
    multiplier_from_source_event: bool = True
    source_multiplier_by_element: tuple[tuple[Element, float], ...] = ()
    source_multiplier_uses_tick_profile: bool = True

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("DischargeDamageEventTemplate requires anomaly damage type")
        if self.ref.damage_subtype is not DamageSubtype.DISCHARGE:
            raise ValueError("discharge template requires discharge subtype")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.ref.skill_group is not None or self.move_id is not None:
            raise ValueError("synthetic discharge damage must not invent a move identity")
        if not isinstance(self.multiplier_from_source_event, bool):
            raise ValueError("multiplier_from_source_event must be boolean")
        if not isinstance(self.source_multiplier_uses_tick_profile, bool):
            raise ValueError("source_multiplier_uses_tick_profile must be boolean")
        source_elements = tuple(element for element, _ in self.source_multiplier_by_element)
        if len(set(source_elements)) != len(source_elements):
            raise ValueError("discharge source multipliers must have unique elements")
        if any(value < 0 for _, value in self.source_multiplier_by_element):
            raise ValueError("discharge source multipliers must be non-negative")


@dataclass(frozen=True, slots=True)
class TurbulenceDamageEventTemplate:
    """Wind-triggered turbulence borrowing a declared non-wind history record."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    wind_anomaly_triggerer: CharacterId
    history_record_source: AnomalyRecordId | None = None
    crit_rule: RecordedAnomalyCritRule | NoCritRule | Unresolved = NoCritRule()
    move_id: MoveId | None = None
    core_turbulence_bonus: float = 0.0
    wind_erosion_stack_parameter_id: ScenarioParameterId | None = None
    enhanced_at_stack_count: int = 2

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("TurbulenceDamageEventTemplate requires anomaly damage type")
        if self.ref.damage_subtype is not DamageSubtype.TURBULENCE:
            raise ValueError("turbulence template requires turbulence subtype")
        if self.element is not Element.WIND or self.ref.element is not Element.WIND:
            raise ValueError("turbulence damage element must be Wind")
        if self.damage_dealer != self.wind_anomaly_triggerer:
            raise ValueError("turbulence triggerer must be its damage dealer")
        if self.ref.skill_group is not None or self.ref.damage_tags or self.move_id is not None:
            raise ValueError("synthetic turbulence must not invent move or tag identities")
        if self.core_turbulence_bonus < 0:
            raise ValueError("core turbulence bonus must be non-negative")
        if self.enhanced_at_stack_count < 1:
            raise ValueError("enhanced turbulence stack threshold must be positive")


@dataclass(frozen=True, slots=True)
class LuminanceFlareDamageEventTemplate:
    """Reviewed Remielle Flare event whose source is selected per request."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    luminance_triggerer: CharacterId
    crit_rule: NoCritRule
    move_id: MoveId | None = None
    repeat_count_rule_item_id: RuleItemId | None = None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("Luminance Flare template requires anomaly damage type")
        if self.ref.damage_subtype is not DamageSubtype.LUMINANCE:
            raise ValueError("Luminance Flare template requires luminance subtype")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.damage_dealer != self.luminance_triggerer:
            raise ValueError("Luminance triggerer must be the damage dealer")
        if self.ref.skill_group is not None or self.move_id is not None:
            raise ValueError("synthetic Luminance Flare must not invent a move identity")


@dataclass(frozen=True, slots=True)
class SettledAnomalyDamageEventTemplate:
    """Template for an anomaly child based on a prior final damage result."""

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    base_source: SettledDamageValueSource
    crit_rule: NoCritRule
    move_id: MoveId | None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("SettledAnomalyDamageEventTemplate requires anomaly damage type")
        if self.ref.damage_subtype is not DamageSubtype.ATTRIBUTE_ANOMALY:
            raise ValueError("settled anomaly template requires attribute-anomaly subtype")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.damage_dealer == CharacterId(""):
            raise ValueError("settled anomaly template requires a damage dealer")


@dataclass(frozen=True, slots=True)
class UnresolvedDamageEventTemplate:
    """Entry reference for a direct source whose event identity is unresolved.

    This carries the known source label and actor for a partial move entry, but
    deliberately cannot be instantiated as a damage event until its typed
    element/event identity is reviewed.
    """

    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    move_id: MoveId | None
    unresolved: Unresolved

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.DIRECT:
            raise ValueError("unresolved direct template requires direct damage metadata")
        if self.ref.element is not None:
            raise ValueError("unresolved direct template must not guess an element")


DamageEventTemplate = (
    DirectDamageEventTemplate
    | PenetrationDamageEventTemplate
    | AttributeAnomalyDamageEventTemplate
    | CurrentAttributeAnomalyDamageEventTemplate
    | DisorderDamageEventTemplate
    | PolarDisorderDamageEventTemplate
    | DischargeDamageEventTemplate
    | TurbulenceDamageEventTemplate
    | LuminanceFlareDamageEventTemplate
    | SettledAnomalyDamageEventTemplate
    | UnresolvedDamageEventTemplate
)


__all__ = [
    "AttributeAnomalyDamageEventTemplate",
    "CurrentAttributeAnomalyDamageEventTemplate",
    "DamageEventTemplate",
    "DirectDamageEventTemplate",
    "PenetrationDamageEventTemplate",
    "DisorderDamageEventTemplate",
    "PolarDisorderDamageEventTemplate",
    "DischargeDamageEventTemplate",
    "TurbulenceDamageEventTemplate",
    "LuminanceFlareDamageEventTemplate",
    "SettledAnomalyDamageEventTemplate",
    "UnresolvedDamageEventTemplate",
]
