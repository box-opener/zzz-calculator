"""DamageEvent discriminated unions with mechanism-specific identities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, TypeAlias

from .anomaly_record import AnomalyCritCapability, IndependentAnomalyCrit
from .calculation_node import CalculationNode
from .common import (
    AnomalyRecordId,
    BattleStateId,
    BattleTime,
    CharacterId,
    DamageEventId,
    EnemyId,
    HitId,
    MoveId,
    Multiplier,
    Resolvable,
    Unresolved,
)
from .enums import DamageSubtype, DamageTag, DamageType, Element, SkillGroup


class AnomalyRecordValueField(StrEnum):
    WEIGHTED_ANOMALY_EFFECT_STRENGTH = "weighted-anomaly-effect-strength"
    WEIGHTED_IMPACT_STRENGTH = "weighted-impact-strength"


@dataclass(frozen=True, slots=True)
class CurrentAttackValueSource:
    character_id: CharacterId
    kind: Literal["current-attack"] = field(default="current-attack", init=False)


@dataclass(frozen=True, slots=True)
class CurrentDefenseValueSource:
    character_id: CharacterId
    kind: Literal["current-defense"] = field(default="current-defense", init=False)


@dataclass(frozen=True, slots=True)
class CurrentMaxHPValueSource:
    character_id: CharacterId
    kind: Literal["current-max-hp"] = field(default="current-max-hp", init=False)


@dataclass(frozen=True, slots=True)
class CurrentAnomalyProficiencyValueSource:
    """Current anomaly proficiency used by an explicitly typed event."""

    character_id: CharacterId
    kind: Literal["current-anomaly-proficiency"] = field(
        default="current-anomaly-proficiency", init=False
    )


@dataclass(frozen=True, slots=True)
class CurrentAnomalyEffectStrengthValueSource:
    """Current attack/anomaly-proficiency source for a synthetic anomaly event."""

    character_id: CharacterId
    kind: Literal["current-anomaly-effect-strength"] = field(
        default="current-anomaly-effect-strength", init=False
    )


@dataclass(frozen=True, slots=True)
class SettledDamageValueSource:
    """Reference to a previously settled damage result.

    This source is intentionally an identity only.  The application layer
    resolves the referenced result and passes it to the calculator through
    ``CalculationContext.settled_damage_values``; it must never rerun the
    source event's defense/resistance/vulnerability regions.
    """

    event_id: DamageEventId
    kind: Literal["settled-damage-value"] = field(
        default="settled-damage-value", init=False
    )


@dataclass(frozen=True, slots=True)
class CurrentPenetrationForceValueSource:
    """Current 0.25 ATK + 0.10 max-HP Force, optionally with resolved additions."""

    character_id: CharacterId
    additional_force: Resolvable[float] | None = None
    source_effect_ids: tuple[str, ...] = ()
    kind: Literal["current-penetration-force"] = field(
        default="current-penetration-force", init=False
    )


@dataclass(frozen=True, slots=True)
class AnomalyRecordValueSource:
    record_id: AnomalyRecordId
    value_field: AnomalyRecordValueField = (
        AnomalyRecordValueField.WEIGHTED_ANOMALY_EFFECT_STRENGTH
    )
    kind: Literal["anomaly-record"] = field(default="anomaly-record", init=False)


BaseSettlementDataSource: TypeAlias = (
    CurrentAttackValueSource
    | CurrentDefenseValueSource
    | CurrentMaxHPValueSource
    | CurrentAnomalyProficiencyValueSource
    | CurrentAnomalyEffectStrengthValueSource
    | CurrentPenetrationForceValueSource
    | AnomalyRecordValueSource
    | SettledDamageValueSource
    | Unresolved
)


@dataclass(frozen=True, slots=True)
class FixedMultiplier:
    value: Resolvable[Multiplier]
    kind: Literal["fixed"] = field(default="fixed", init=False)


@dataclass(frozen=True, slots=True)
class CalculationNodeMultiplier:
    node: CalculationNode
    kind: Literal["calculation-node"] = field(default="calculation-node", init=False)


DamageMultiplier: TypeAlias = FixedMultiplier | CalculationNodeMultiplier | Unresolved


@dataclass(frozen=True, slots=True)
class StandardCritRule:
    stat_owner: CharacterId
    guaranteed: bool = False
    kind: Literal["standard"] = field(default="standard", init=False)


@dataclass(frozen=True, slots=True)
class NoCritRule:
    kind: Literal["none"] = field(default="none", init=False)


@dataclass(frozen=True, slots=True)
class RecordedAnomalyCritRule:
    record_id: AnomalyRecordId
    capability: AnomalyCritCapability
    kind: Literal["recorded-anomaly"] = field(default="recorded-anomaly", init=False)


@dataclass(frozen=True, slots=True)
class IndependentAnomalyCritRule:
    crit_owner: CharacterId
    capability: IndependentAnomalyCrit
    kind: Literal["independent-anomaly"] = field(
        default="independent-anomaly", init=False
    )


CritRule: TypeAlias = (
    StandardCritRule
    | NoCritRule
    | RecordedAnomalyCritRule
    | IndependentAnomalyCritRule
    | Unresolved
)


def _validate_damage_record_source(
    source: AnomalyRecordValueSource,
    history_record_source: AnomalyRecordId,
) -> None:
    if source.record_id != history_record_source:
        raise ValueError(
            "base settlement and history record identities must be explicit and consistent"
        )
    if (
        source.value_field
        is not AnomalyRecordValueField.WEIGHTED_ANOMALY_EFFECT_STRENGTH
    ):
        raise ValueError(
            "damage events read weighted anomaly effect strength, not impact strength"
        )


@dataclass(frozen=True, slots=True)
class DamageEventMetadata:
    event_id: DamageEventId
    battle_state_id: BattleStateId
    damage_dealer: CharacterId
    target_enemy: EnemyId
    element: Element
    created_at: BattleTime
    skill_group: SkillGroup | None = None
    move_id: MoveId | None = None
    hit_id: HitId | None = None
    damage_tags: frozenset[DamageTag] = frozenset()


@dataclass(frozen=True, slots=True)
class DirectDamageEvent:
    metadata: DamageEventMetadata
    base_settlement_data_source: (
        CurrentAttackValueSource
        | CurrentDefenseValueSource
        | CurrentMaxHPValueSource
        | CurrentAnomalyProficiencyValueSource
        | CurrentPenetrationForceValueSource
    )
    multiplier: DamageMultiplier
    crit_rule: StandardCritRule | Unresolved
    damage_type: Literal[DamageType.DIRECT] = field(default=DamageType.DIRECT, init=False)
    damage_subtype: None = field(default=None, init=False)


@dataclass(frozen=True, slots=True)
class SettledAnomalyDamageEvent:
    """An anomaly-labelled child whose base is an already settled value."""

    metadata: DamageEventMetadata
    base_settlement_data_source: SettledDamageValueSource
    multiplier: DamageMultiplier
    crit_rule: NoCritRule | Unresolved
    damage_type: Literal[DamageType.ANOMALY] = field(
        default=DamageType.ANOMALY, init=False
    )
    damage_subtype: Literal[DamageSubtype.ATTRIBUTE_ANOMALY] = field(
        default=DamageSubtype.ATTRIBUTE_ANOMALY, init=False
    )


@dataclass(frozen=True, slots=True)
class CurrentAttributeAnomalyDamageEvent:
    """An attribute anomaly calculated from the current character panel."""

    metadata: DamageEventMetadata
    anomaly_triggerer: CharacterId
    base_settlement_data_source: CurrentAnomalyEffectStrengthValueSource
    multiplier: DamageMultiplier
    crit_rule: NoCritRule | Unresolved
    damage_type: Literal[DamageType.ANOMALY] = field(
        default=DamageType.ANOMALY, init=False
    )
    damage_subtype: Literal[DamageSubtype.ATTRIBUTE_ANOMALY] = field(
        default=DamageSubtype.ATTRIBUTE_ANOMALY, init=False
    )


@dataclass(frozen=True, slots=True)
class AttributeAnomalyDamageEvent:
    metadata: DamageEventMetadata
    anomaly_triggerer: CharacterId
    base_settlement_data_source: AnomalyRecordValueSource
    history_record_source: AnomalyRecordId
    multiplier: DamageMultiplier
    crit_rule: RecordedAnomalyCritRule | NoCritRule | Unresolved
    damage_type: Literal[DamageType.ANOMALY] = field(default=DamageType.ANOMALY, init=False)
    damage_subtype: Literal[DamageSubtype.ATTRIBUTE_ANOMALY] = field(
        default=DamageSubtype.ATTRIBUTE_ANOMALY, init=False
    )

    def __post_init__(self) -> None:
        _validate_damage_record_source(
            self.base_settlement_data_source, self.history_record_source
        )


@dataclass(frozen=True, slots=True)
class DischargeDamageEvent:
    metadata: DamageEventMetadata
    discharge_triggerer: CharacterId
    base_settlement_data_source: AnomalyRecordValueSource
    history_record_source: AnomalyRecordId
    multiplier: DamageMultiplier
    crit_rule: (
        RecordedAnomalyCritRule
        | IndependentAnomalyCritRule
        | NoCritRule
        | Unresolved
    )
    damage_type: Literal[DamageType.ANOMALY] = field(default=DamageType.ANOMALY, init=False)
    damage_subtype: Literal[DamageSubtype.DISCHARGE] = field(
        default=DamageSubtype.DISCHARGE, init=False
    )

    def __post_init__(self) -> None:
        _validate_damage_record_source(
            self.base_settlement_data_source, self.history_record_source
        )


@dataclass(frozen=True, slots=True)
class TurbulenceDamageEvent:
    metadata: DamageEventMetadata
    wind_anomaly_triggerer: CharacterId
    base_settlement_data_source: AnomalyRecordValueSource
    history_record_source: AnomalyRecordId
    multiplier: DamageMultiplier
    crit_rule: RecordedAnomalyCritRule | NoCritRule | Unresolved
    damage_type: Literal[DamageType.ANOMALY] = field(default=DamageType.ANOMALY, init=False)
    damage_subtype: Literal[DamageSubtype.TURBULENCE] = field(
        default=DamageSubtype.TURBULENCE, init=False
    )

    def __post_init__(self) -> None:
        _validate_damage_record_source(
            self.base_settlement_data_source, self.history_record_source
        )
        if self.metadata.damage_dealer != self.wind_anomaly_triggerer:
            raise ValueError("turbulence damage dealer must be the wind anomaly triggerer")


@dataclass(frozen=True, slots=True)
class LuminanceDamageEvent:
    metadata: DamageEventMetadata
    luminance_triggerer: CharacterId
    base_settlement_data_source: AnomalyRecordValueSource
    history_record_source: AnomalyRecordId
    multiplier: DamageMultiplier
    crit_rule: NoCritRule | Unresolved
    damage_type: Literal[DamageType.ANOMALY] = field(default=DamageType.ANOMALY, init=False)
    damage_subtype: Literal[DamageSubtype.LUMINANCE] = field(
        default=DamageSubtype.LUMINANCE, init=False
    )

    def __post_init__(self) -> None:
        _validate_damage_record_source(
            self.base_settlement_data_source, self.history_record_source
        )


@dataclass(frozen=True, slots=True)
class DisorderDamageEvent:
    metadata: DamageEventMetadata
    disorder_triggerer: CharacterId
    base_settlement_data_source: AnomalyRecordValueSource
    history_record_source: AnomalyRecordId
    multiplier: DamageMultiplier
    crit_rule: NoCritRule | Unresolved
    damage_type: Literal[DamageType.DISORDER] = field(default=DamageType.DISORDER, init=False)
    damage_subtype: None = field(default=None, init=False)

    def __post_init__(self) -> None:
        _validate_damage_record_source(
            self.base_settlement_data_source, self.history_record_source
        )


@dataclass(frozen=True, slots=True)
class PenetrationDamageEvent:
    metadata: DamageEventMetadata
    base_settlement_data_source: CurrentPenetrationForceValueSource
    multiplier: DamageMultiplier
    crit_rule: StandardCritRule | Unresolved
    damage_type: Literal[DamageType.PENETRATION] = field(
        default=DamageType.PENETRATION, init=False
    )
    damage_subtype: None = field(default=None, init=False)


@dataclass(frozen=True, slots=True)
class UnresolvedSharpExplosionDamageEvent:
    metadata: DamageEventMetadata
    unresolved: Unresolved
    damage_type: Literal[DamageType.SHARP_EXPLOSION] = field(
        default=DamageType.SHARP_EXPLOSION, init=False
    )
    damage_subtype: None = field(default=None, init=False)


DamageEvent: TypeAlias = (
    DirectDamageEvent
    | SettledAnomalyDamageEvent
    | CurrentAttributeAnomalyDamageEvent
    | AttributeAnomalyDamageEvent
    | DischargeDamageEvent
    | TurbulenceDamageEvent
    | LuminanceDamageEvent
    | DisorderDamageEvent
    | PenetrationDamageEvent
    | UnresolvedSharpExplosionDamageEvent
)
