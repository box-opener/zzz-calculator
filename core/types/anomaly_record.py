"""Historical data produced by one completed anomaly gauge."""

from __future__ import annotations

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

    def __post_init__(self) -> None:
        if self.actual_written_buildup <= 0:
            raise ValueError("only non-zero actual written buildup is a contribution")


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
