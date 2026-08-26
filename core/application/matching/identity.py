"""Derive dynamic identities from typed events and their history records."""

from dataclasses import dataclass

from core.types import (
    AnomalyRecord,
    AnomalyRecordId,
    AttributeAnomalyDamageEvent,
    CharacterId,
    DamageEvent,
    DisorderDamageEvent,
    DischargeDamageEvent,
    DynamicIdentity,
    LuminanceDamageEvent,
    TurbulenceDamageEvent,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from .context import EffectMatchContext


@dataclass(frozen=True, slots=True)
class IdentityResolution:
    identities: frozenset[CharacterId] | None
    diagnostic: CalculationDiagnostic | None = None


class DynamicIdentityResolver:
    def resolve(
        self,
        identity: DynamicIdentity,
        context: EffectMatchContext,
    ) -> IdentityResolution:
        event = context.current_event
        if identity is DynamicIdentity.DAMAGE_DEALER:
            return IdentityResolution(frozenset({event.metadata.damage_dealer}))

        if identity is DynamicIdentity.DISORDER_TRIGGER:
            if isinstance(event, DisorderDamageEvent):
                return IdentityResolution(frozenset({event.disorder_triggerer}))
            return IdentityResolution(frozenset())
        if identity is DynamicIdentity.WIND_ANOMALY_TRIGGER:
            if isinstance(event, TurbulenceDamageEvent):
                return IdentityResolution(frozenset({event.wind_anomaly_triggerer}))
            return IdentityResolution(frozenset())
        if identity is DynamicIdentity.LUMINANCE_TRIGGER:
            if isinstance(event, LuminanceDamageEvent):
                return IdentityResolution(frozenset({event.luminance_triggerer}))
            return IdentityResolution(frozenset())
        if identity is DynamicIdentity.DISCHARGE_TRIGGER:
            if isinstance(event, DischargeDamageEvent):
                return IdentityResolution(frozenset({event.discharge_triggerer}))
            return IdentityResolution(frozenset())

        record = self._record_for_event(event, context)
        if record is None:
            if self._event_has_history_source(event):
                return IdentityResolution(
                    identities=None,
                    diagnostic=CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(
                            f"missing-history-for-{identity.value}"
                        ),
                        kind=DiagnosticKind.MISSING_DATA,
                        message=(
                            f"cannot resolve {identity.value} without the event's "
                            "AnomalyRecord"
                        ),
                        blocking=True,
                    ),
                )
            return IdentityResolution(frozenset())

        if identity is DynamicIdentity.ANOMALY_TRIGGER:
            return IdentityResolution(frozenset({record.anomaly_triggerer}))
        if identity is DynamicIdentity.ANOMALY_CONTRIBUTORS:
            return IdentityResolution(frozenset(record.contributors))
        return IdentityResolution(frozenset())

    @staticmethod
    def _event_has_history_source(event: DamageEvent) -> bool:
        return isinstance(
            event,
            (
                AttributeAnomalyDamageEvent,
                DischargeDamageEvent,
                TurbulenceDamageEvent,
                LuminanceDamageEvent,
                DisorderDamageEvent,
            ),
        )

    @staticmethod
    def _record_for_event(
        event: DamageEvent,
        context: EffectMatchContext,
    ) -> AnomalyRecord | None:
        if isinstance(event, AttributeAnomalyDamageEvent):
            record_id: AnomalyRecordId = event.history_record_source
        elif isinstance(event, DischargeDamageEvent):
            record_id = event.history_record_source
        elif isinstance(event, TurbulenceDamageEvent):
            record_id = event.history_record_source
        elif isinstance(event, LuminanceDamageEvent):
            record_id = event.history_record_source
        elif isinstance(event, DisorderDamageEvent):
            record_id = event.history_record_source
        else:
            return None
        records = {}
        for record in context.history_records:
            if record.record_id in records:
                return None
            records[record.record_id] = record
        return records.get(record_id)
