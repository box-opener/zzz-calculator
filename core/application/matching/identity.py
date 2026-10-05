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
    BattleEventKind,
    LuminanceDamageEvent,
    SpecialLuminanceDamageEvent,
    TurbulenceDamageEvent,
)

from ..diagnostics import CalculationDiagnostic, DiagnosticKind
from ..ids import DiagnosticId
from .context import EffectMatchContext


@dataclass(frozen=True, slots=True)
class IdentityResolution:
    identities: frozenset[CharacterId] | None
    diagnostic: CalculationDiagnostic | None = None


@dataclass(frozen=True, slots=True)
class HistoryRecordResolution:
    record: AnomalyRecord | None
    diagnostic: CalculationDiagnostic | None = None


class DynamicIdentityResolver:
    def resolve(
        self,
        identity: DynamicIdentity,
        context: EffectMatchContext,
        effect_id: str | None = None,
    ) -> IdentityResolution:
        event = context.current_event
        if identity is DynamicIdentity.CURRENT_OPERATOR:
            return IdentityResolution(frozenset({context.current_operator}))
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
            if isinstance(event, (LuminanceDamageEvent, SpecialLuminanceDamageEvent)):
                return IdentityResolution(frozenset({event.luminance_triggerer}))
            return IdentityResolution(frozenset())
        if identity is DynamicIdentity.DISCHARGE_TRIGGER:
            if isinstance(event, DischargeDamageEvent):
                return IdentityResolution(frozenset({event.discharge_triggerer}))
            return IdentityResolution(frozenset())

        if isinstance(event, SpecialLuminanceDamageEvent):
            # A stored special virtual void has its own source snapshot; it is
            # not an ordinary AnomalyRecord and therefore does not acquire an
            # ANOMALY_TRIGGER identity.
            return IdentityResolution(frozenset())

        if identity is DynamicIdentity.SUPPORT_ENTRY_CHARACTER:
            facts = tuple(
                fact
                for fact in context.trigger_facts
                if (effect_id is None or str(fact.effect_id) == effect_id)
                and fact.event_kind is BattleEventKind.SUPPORT_ENTRY
                and fact.actor is not None
            )
            if not facts:
                return IdentityResolution(
                    identities=None,
                    diagnostic=CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(
                            f"support-entry:{effect_id or 'unknown'}"
                        ),
                        kind=DiagnosticKind.MISSING_DATA,
                        message=(
                            "support-entry character identity requires a matching "
                            "scenario trigger fact"
                        ),
                        blocking=True,
                    ),
                )
            actors = frozenset(fact.actor for fact in facts if fact.actor is not None)
            if len(actors) != 1:
                return IdentityResolution(
                    identities=None,
                    diagnostic=CalculationDiagnostic(
                        diagnostic_id=DiagnosticId(
                            f"support-entry:{effect_id or 'unknown'}:ambiguous"
                        ),
                        kind=DiagnosticKind.DATA_QUALITY,
                        message=(
                            "support-entry identity has multiple scenario actors"
                        ),
                        blocking=True,
                    ),
                )
            return IdentityResolution(actors)

        if (
            identity is DynamicIdentity.ANOMALY_TRIGGER
            and isinstance(event, AttributeAnomalyDamageEvent)
        ):
            history = self._record_for_event(event, context)
            if history.diagnostic is not None and (
                history.diagnostic.kind is DiagnosticKind.DATA_QUALITY
            ):
                return IdentityResolution(None, history.diagnostic)
            if (
                history.record is not None
                and history.record.anomaly_triggerer != event.anomaly_triggerer
            ):
                return IdentityResolution(
                    identities=None,
                    diagnostic=self._history_diagnostic(
                        event,
                        "anomaly triggerer differs between event and record",
                        DiagnosticKind.DATA_QUALITY,
                    ),
                )
            return IdentityResolution(frozenset({event.anomaly_triggerer}))

        history = self._record_for_event(event, context)
        if history.record is None:
            if history.diagnostic is not None:
                return IdentityResolution(
                    identities=None,
                    diagnostic=history.diagnostic,
                )
            return IdentityResolution(frozenset())

        if identity is DynamicIdentity.ANOMALY_TRIGGER:
            return IdentityResolution(
                frozenset({history.record.anomaly_triggerer})
            )
        if identity is DynamicIdentity.ANOMALY_CONTRIBUTORS:
            return IdentityResolution(frozenset(history.record.contributors))
        return IdentityResolution(frozenset())

    @staticmethod
    def _record_for_event(
        event: DamageEvent,
        context: EffectMatchContext,
    ) -> HistoryRecordResolution:
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
            return HistoryRecordResolution(None)
        records = tuple(
            record
            for record in context.history_records
            if record.record_id == record_id
        )
        if not records:
            return HistoryRecordResolution(
                None,
                DynamicIdentityResolver._history_diagnostic(
                    event,
                    "required AnomalyRecord is missing",
                    DiagnosticKind.MISSING_DATA,
                ),
            )
        if len(records) > 1:
            return HistoryRecordResolution(
                None,
                DynamicIdentityResolver._history_diagnostic(
                    event,
                    "duplicate AnomalyRecord identities",
                    DiagnosticKind.DATA_QUALITY,
                ),
            )
        record = records[0]
        if record.target_enemy != event.metadata.target_enemy:
            return HistoryRecordResolution(
                None,
                DynamicIdentityResolver._history_diagnostic(
                    event,
                    "AnomalyRecord target differs from event target",
                    DiagnosticKind.DATA_QUALITY,
                ),
            )
        if record.element != event.metadata.element:
            return HistoryRecordResolution(
                None,
                DynamicIdentityResolver._history_diagnostic(
                    event,
                    "AnomalyRecord element differs from event element",
                    DiagnosticKind.DATA_QUALITY,
                ),
            )
        return HistoryRecordResolution(record)

    @staticmethod
    def _history_diagnostic(
        event: DamageEvent,
        message: str,
        kind: DiagnosticKind,
    ) -> CalculationDiagnostic:
        return CalculationDiagnostic(
            diagnostic_id=DiagnosticId(
                f"history-{event.metadata.event_id}-{kind.value}"
            ),
            kind=kind,
            message=message,
            blocking=True,
        )
