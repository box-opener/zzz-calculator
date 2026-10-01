"""Typed damage-event templates emitted by reviewed character compilers."""

from dataclasses import dataclass

from core.types import (
    AnomalyRecordId,
    CurrentAnomalyEffectStrengthValueSource,
    CurrentAnomalyProficiencyValueSource,
    CurrentPenetrationForceValueSource,
    SettledDamageValueSource,
    CharacterId,
    CurrentAttackValueSource,
    DamageType,
    DamageSubtype,
    Element,
    MoveId,
    NoCritRule,
    RecordedAnomalyCritRule,
    Unresolved,
    StandardCritRule,
)

from ..moves import DamageEventTemplateRef


@dataclass(frozen=True, slots=True)
class DirectDamageEventTemplate:
    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    base_source: CurrentAttackValueSource | CurrentAnomalyProficiencyValueSource
    crit_rule: StandardCritRule
    move_id: MoveId | None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.DIRECT:
            raise ValueError("DirectDamageEventTemplate requires direct damage type")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.damage_dealer != self.base_source.character_id:
            raise ValueError("base attack source must match damage dealer")
        if self.damage_dealer != self.crit_rule.stat_owner:
            raise ValueError("crit stat owner must match damage dealer")
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

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.ANOMALY:
            raise ValueError("AttributeAnomalyDamageEventTemplate requires anomaly damage type")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.ref.damage_subtype is not DamageSubtype.ATTRIBUTE_ANOMALY:
            raise ValueError("attribute anomaly template requires attribute-anomaly subtype")


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


DamageEventTemplate = (
    DirectDamageEventTemplate
    | PenetrationDamageEventTemplate
    | AttributeAnomalyDamageEventTemplate
    | CurrentAttributeAnomalyDamageEventTemplate
    | DisorderDamageEventTemplate
    | SettledAnomalyDamageEventTemplate
)


__all__ = [
    "AttributeAnomalyDamageEventTemplate",
    "CurrentAttributeAnomalyDamageEventTemplate",
    "DamageEventTemplate",
    "DirectDamageEventTemplate",
    "PenetrationDamageEventTemplate",
    "DisorderDamageEventTemplate",
    "SettledAnomalyDamageEventTemplate",
]
