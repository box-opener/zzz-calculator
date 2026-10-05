"""Historical data produced by one completed anomaly gauge."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from .common import (
    AnomalyRecordId,
    BattleTime,
    CharacterId,
    EnemyId,
    Multiplier,
    Ratio,
    Resolvable,
    Seconds,
    Unresolved,
)
from .enums import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_ELEMENTS,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    AttributeAnomalyDamageKind,
    AttributeAnomalyStateKind,
    DamageSubtype,
    Element,
)


@dataclass(frozen=True, slots=True)
class AnomalyStrengthFactor:
    """One named input used by the anomaly effect-strength formula.

    This is deliberately a small calculation value object rather than an
    application/presentation type.  It lets a generated anomaly record retain
    the inputs that produced its strength without asking a later settlement to
    reconstruct them from the current character panel.
    """

    factor: str
    value: float | None
    source_id: str | None = None
    source_label: str | None = None
    owner_character_id: CharacterId | None = None
    unresolved: str | None = None


@dataclass(frozen=True, slots=True)
class AnomalyEffectStrengthTrace:
    """Provenance captured at the point anomaly effect strength is generated."""

    character_id: CharacterId
    level: int | None
    level_coefficient: float | None
    anomaly_proficiency: float | None
    anomaly_proficiency_factor: float | None
    attack: float | None
    element_bonus: float | None
    normal_bonus: float | None
    mutation: float | None
    final_strength: float | None
    element: Element | None = None
    factors: tuple[AnomalyStrengthFactor, ...] = ()
    unresolved: str | None = None
    contributor_traces: tuple[tuple[CharacterId, float, "AnomalyEffectStrengthTrace"], ...] = ()


@dataclass(frozen=True, slots=True)
class NoAnomalyCrit:
    kind: Literal["none"] = field(default="none", init=False)


@dataclass(frozen=True, slots=True)
class IndependentAnomalyCrit:
    """A special anomaly crit capability, never the ordinary panel crit."""

    crit_rate: Resolvable[Ratio]
    crit_damage: Resolvable[Ratio]
    inherited_by: tuple[DamageSubtype, ...] = ()
    kind: Literal["independent"] = field(default="independent", init=False)


AnomalyCritCapability: TypeAlias = NoAnomalyCrit | IndependentAnomalyCrit | Unresolved


@dataclass(frozen=True, slots=True)
class AnomalyContribution:
    contributor: CharacterId
    actual_written_buildup: float
    anomaly_effect_strength: Resolvable[float]
    impact_strength: Resolvable[float]
    occurred_at: BattleTime
    anomaly_effect_strength_trace: AnomalyEffectStrengthTrace | None = None

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.actual_written_buildup)
            or self.actual_written_buildup <= 0
        ):
            raise ValueError(
                "actual written anomaly buildup must be a finite positive number"
            )


@dataclass(frozen=True, slots=True)
class AnomalyRecord:
    record_id: AnomalyRecordId
    target_enemy: EnemyId
    element: Element
    damage_kind: AttributeAnomalyDamageKind
    state_kind: AttributeAnomalyStateKind
    weighted_anomaly_effect_strength: Resolvable[float]
    weighted_impact_strength: Resolvable[float]
    anomaly_damage_bonus_region: Resolvable[Multiplier]
    contributors: tuple[CharacterId, ...]
    anomaly_triggerer: CharacterId
    crit_capability: AnomalyCritCapability
    triggered_at: BattleTime
    duration: Resolvable[Seconds]
    contributions: tuple[AnomalyContribution, ...] = ()
    anomaly_effect_strength_trace: AnomalyEffectStrengthTrace | None = None
    # Penetration is captured with the historical effect-strength source for
    # Luminance settlement.  Legacy/explicit records may omit these values;
    # consumers must report missing data rather than substitute a live panel.
    penetration_rate: Resolvable[Ratio] | None = None
    penetration_flat: Resolvable[float] | None = None

    def __post_init__(self) -> None:
        if self.element not in ANOMALY_ELEMENTS:
            raise ValueError("luminance has no ordinary anomaly record")
        if self.damage_kind is not ANOMALY_DAMAGE_KIND_BY_ELEMENT[self.element]:
            raise ValueError("anomaly damage kind does not match the recorded element")
        if self.state_kind is not ANOMALY_STATE_KIND_BY_ELEMENT[self.element]:
            raise ValueError("anomaly state kind does not match the recorded element")
        if not self.contributors:
            raise ValueError("an anomaly record must have at least one contributor")
        if len(set(self.contributors)) != len(self.contributors):
            raise ValueError("anomaly contributors are unique identities")
        if self.anomaly_triggerer not in self.contributors:
            raise ValueError("the anomaly triggerer is also an anomaly contributor")
        contribution_ids = {item.contributor for item in self.contributions}
        if self.contributions:
            if self.anomaly_triggerer not in contribution_ids:
                raise ValueError(
                    "the anomaly triggerer must have a detailed contribution"
                )
            if contribution_ids != set(self.contributors):
                raise ValueError(
                    "detailed contribution identities must exactly match contributors"
                )
