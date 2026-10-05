"""Instantiate application templates as pure domain DamageEvents."""

from __future__ import annotations

from dataclasses import replace

from core.types import (
    AnomalyRecordValueSource,
    AnomalyRecordId,
    AttributeAnomalyDamageEvent,
    BattleStateId,
    BattleTime,
    DamageEventId,
    DamageEventMetadata,
    DamageMultiplier,
    EventTemplateId,
    LuminanceSourceChoice,
    LuminanceSourceKind,
    LuminanceSpecialSourceId,
    LuminanceSpecialSourceSnapshot,
    LuminanceDamageEvent,
    SpecialLuminanceDamageEvent,
    DirectDamageEvent,
    DisorderDamageEvent,
    DischargeDamageEvent,
    RecordedAnomalyCritRule,
    DamageSubtype,
    CurrentAttributeAnomalyDamageEvent,
    PenetrationDamageEvent,
    SettledAnomalyDamageEvent,
    SettledDamageValueSource,
    EffectId,
    EnemyId,
    TurbulenceDamageEvent,
)

from ..characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    CurrentAttributeAnomalyDamageEventTemplate,
    DamageEventTemplate,
    DirectDamageEventTemplate,
    PenetrationDamageEventTemplate,
    DisorderDamageEventTemplate,
    DischargeDamageEventTemplate,
    LuminanceFlareDamageEventTemplate,
    SettledAnomalyDamageEventTemplate,
    TurbulenceDamageEventTemplate,
)
from ..ids import DamageEventSemanticId, RuleItemId
from .contracts import InstantiatedDamageEvent


def instantiate_direct_damage_event(
    template: DirectDamageEventTemplate,
    multiplier,
    *,
    battle_state_id: BattleStateId,
    target_enemy: EnemyId,
    created_at: BattleTime,
    source_rule_item_id: RuleItemId | None = None,
    created_by_effect_id: EffectId | None = None,
    repeat_count: int = 1,
) -> InstantiatedDamageEvent:
    """Create one direct event while keeping application provenance in a wrapper."""

    semantic_id: DamageEventSemanticId = template.ref.semantic_id
    event = DirectDamageEvent(
        metadata=template_metadata(
            template,
            battle_state_id=battle_state_id,
            target_enemy=target_enemy,
            created_at=created_at,
        ),
        base_settlement_data_source=template.base_source,
        multiplier=multiplier,
        crit_rule=template.crit_rule,
    )
    return InstantiatedDamageEvent(
        template_id=template.ref.template_id,
        semantic_id=semantic_id,
        label=template.ref.label,
        event=event,
        source_rule_item_id=(
            source_rule_item_id
            if source_rule_item_id is not None
            else template.ref.source_rule_item_id
        ),
        created_by_effect_id=created_by_effect_id,
        repeat_count=repeat_count,
    )


def instantiate_damage_event(
    template: DamageEventTemplate,
    multiplier,
    *,
    battle_state_id: BattleStateId,
    target_enemy: EnemyId,
    created_at: BattleTime,
    source_rule_item_id: RuleItemId | None = None,
    created_by_effect_id: EffectId | None = None,
    repeat_count: int = 1,
    source_event_id: DamageEventId | None = None,
    source_history_record_id: AnomalyRecordId | None = None,
    source_anomaly_multiplier: DamageMultiplier | None = None,
    luminance_source_choice: LuminanceSourceChoice | None = None,
    luminance_special_source: LuminanceSpecialSourceSnapshot | None = None,
    turbulence_crit_rule=None,
    turbulence_element=None,
) -> InstantiatedDamageEvent:
    """Instantiate any typed template without collapsing anomaly identity."""

    if isinstance(template, DirectDamageEventTemplate):
        return instantiate_direct_damage_event(
            template,
            multiplier,
            battle_state_id=battle_state_id,
            target_enemy=target_enemy,
            created_at=created_at,
            source_rule_item_id=source_rule_item_id,
            created_by_effect_id=created_by_effect_id,
            repeat_count=repeat_count,
        )
    if isinstance(template, PenetrationDamageEventTemplate):
        event = PenetrationDamageEvent(
            metadata=template_metadata(
                template,
                battle_state_id=battle_state_id,
                target_enemy=target_enemy,
                created_at=created_at,
            ),
            base_settlement_data_source=template.base_source,
            multiplier=multiplier,
            crit_rule=template.crit_rule,
        )
        return InstantiatedDamageEvent(
            template_id=template.ref.template_id,
            semantic_id=template.ref.semantic_id,
            label=template.ref.label,
            event=event,
            source_rule_item_id=(
                source_rule_item_id
                if source_rule_item_id is not None
                else template.ref.source_rule_item_id
            ),
            created_by_effect_id=created_by_effect_id,
            repeat_count=repeat_count,
        )
    metadata = template_metadata(
        template,
        battle_state_id=battle_state_id,
        target_enemy=target_enemy,
        created_at=created_at,
    )
    if isinstance(template, LuminanceFlareDamageEventTemplate):
        if luminance_source_choice is None:
            raise ValueError("Luminance Flare event requires one selected source slot")
        semantic_id = DamageEventSemanticId(
            f"{template.ref.semantic_id}:source-slot:{luminance_source_choice.slot_id}"
        )
        template_id = EventTemplateId(
            f"{template.ref.template_id}:source-slot:{luminance_source_choice.slot_id}"
        )
        metadata = replace(
            metadata,
            event_id=DamageEventId(f"event:{battle_state_id}:{semantic_id}"),
            element=(
                luminance_source_choice.element
                if luminance_source_choice.kind is LuminanceSourceKind.ORDINARY_ANOMALY
                else template.element
            ),
        )
        if luminance_source_choice.kind is LuminanceSourceKind.ORDINARY_ANOMALY:
            record_id = AnomalyRecordId(
                f"anomaly:remielle:source-slot:{luminance_source_choice.slot_id}"
            )
            event = LuminanceDamageEvent(
                metadata=metadata,
                luminance_triggerer=template.luminance_triggerer,
                base_settlement_data_source=AnomalyRecordValueSource(record_id),
                history_record_source=record_id,
                multiplier=multiplier,
                crit_rule=template.crit_rule,
            )
        else:
            if luminance_special_source is None:
                raise ValueError("special Flare source snapshot is required")
            expected_source_id = LuminanceSpecialSourceId(
                f"luminance-special:remielle:{luminance_source_choice.slot_id}"
            )
            if luminance_special_source.source_id != expected_source_id:
                raise ValueError("special Flare source slot identity does not match")
            event = SpecialLuminanceDamageEvent(
                metadata=metadata,
                luminance_triggerer=template.luminance_triggerer,
                source_snapshot=luminance_special_source,
                multiplier=multiplier,
                crit_rule=template.crit_rule,
            )
        return InstantiatedDamageEvent(
            template_id=template_id,
            semantic_id=semantic_id,
            label=f"{template.ref.label} · 来源槽 {luminance_source_choice.slot_id}",
            event=event,
            source_rule_item_id=source_rule_item_id or template.ref.source_rule_item_id,
            created_by_effect_id=created_by_effect_id,
            repeat_count=repeat_count,
        )
    if isinstance(template, AttributeAnomalyDamageEventTemplate):
        event = AttributeAnomalyDamageEvent(
            metadata=metadata,
            anomaly_triggerer=template.anomaly_triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(
                template.history_record_source
            ),
            history_record_source=template.history_record_source,
            multiplier=multiplier,
            crit_rule=template.crit_rule,
        )
    elif isinstance(template, CurrentAttributeAnomalyDamageEventTemplate):
        event = CurrentAttributeAnomalyDamageEvent(
            metadata=metadata,
            anomaly_triggerer=template.anomaly_triggerer,
            base_settlement_data_source=template.base_source,
            multiplier=multiplier,
            crit_rule=template.crit_rule,
        )
    elif isinstance(template, DisorderDamageEventTemplate):
        event = DisorderDamageEvent(
            metadata=metadata,
            disorder_triggerer=template.disorder_triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(
                template.history_record_source
            ),
            history_record_source=template.history_record_source,
            multiplier=multiplier,
            crit_rule=template.crit_rule,
        )
    elif isinstance(template, DischargeDamageEventTemplate):
        record_id = template.history_record_source or source_history_record_id
        if record_id is None:
            raise ValueError("discharge event requires a typed source anomaly record")
        event = DischargeDamageEvent(
            metadata=metadata,
            discharge_triggerer=template.discharge_triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(record_id),
            history_record_source=record_id,
            multiplier=(
                source_anomaly_multiplier
                if template.multiplier_from_source_event
                and source_anomaly_multiplier is not None
                else multiplier
            ),
            crit_rule=template.crit_rule,
        )
    elif isinstance(template, TurbulenceDamageEventTemplate):
        record_id = template.history_record_source or source_history_record_id
        if record_id is None:
            raise ValueError("turbulence event requires a typed source anomaly record")
        event = TurbulenceDamageEvent(
            metadata=(
                replace(metadata, element=turbulence_element)
                if turbulence_element is not None
                else metadata
            ),
            wind_anomaly_triggerer=template.wind_anomaly_triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(record_id),
            history_record_source=record_id,
            multiplier=multiplier,
            crit_rule=(
                turbulence_crit_rule
                if turbulence_crit_rule is not None
                else template.crit_rule
            ),
        )
    elif isinstance(template, SettledAnomalyDamageEventTemplate):
        source = template.base_source
        if source_event_id is not None:
            source = SettledDamageValueSource(source_event_id)
        event = SettledAnomalyDamageEvent(
            metadata=metadata,
            base_settlement_data_source=source,
            multiplier=multiplier,
            crit_rule=template.crit_rule,
        )
    else:  # pragma: no cover - closed union guard
        raise TypeError(f"unsupported damage event template: {type(template).__name__}")
    return InstantiatedDamageEvent(
        template_id=template.ref.template_id,
        semantic_id=template.ref.semantic_id,
        label=template.ref.label,
        event=event,
        source_rule_item_id=(
            source_rule_item_id
            if source_rule_item_id is not None
            else template.ref.source_rule_item_id
        ),
        created_by_effect_id=created_by_effect_id,
        repeat_count=repeat_count,
    )


def template_metadata(
    template: DamageEventTemplate,
    *,
    battle_state_id: BattleStateId,
    target_enemy: EnemyId,
    created_at: BattleTime,
) -> DamageEventMetadata:
    return DamageEventMetadata(
        event_id=DamageEventId(f"event:{battle_state_id}:{template.ref.semantic_id}"),
        battle_state_id=battle_state_id,
        damage_dealer=template.damage_dealer,
        target_enemy=target_enemy,
        element=template.element,
        created_at=created_at,
        skill_group=template.ref.skill_group,
        move_id=template.move_id,
        damage_tags=template.ref.damage_tags,
    )
