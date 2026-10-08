"""Instantiate application templates as pure domain DamageEvents."""

from __future__ import annotations

from dataclasses import replace

from core.types import (
    AnomalyRecordValueSource,
    AnomalyRecordId,
    AnomalySourceChoice,
    anomaly_source_record_id,
    AttributeAnomalyDamageEvent,
    BattleStateId,
    BattleTime,
    DamageEventId,
    DamageEventMetadata,
    DamageMultiplier,
    FixedMultiplier,
    EventTemplateId,
    LuminanceSourceChoice,
    LuminanceSourceKind,
    LuminanceSpecialSourceId,
    LuminanceSpecialSourceSnapshot,
    LuminanceDamageEvent,
    SpecialLuminanceDamageEvent,
    DirectDamageEvent,
    DisorderDamageEvent,
    PolarDisorderDamageEvent,
    DischargeDamageEvent,
    NoCritRule,
    RecordedAnomalyCritRule,
    DamageSubtype,
    CurrentAttributeAnomalyDamageEvent,
    PenetrationDamageEvent,
    SettledAnomalyDamageEvent,
    SettledDamageValueSource,
    EffectId,
    EnemyId,
    TurbulenceDamageEvent,
    Resolved,
)

from ..characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    CurrentAttributeAnomalyDamageEventTemplate,
    DamageEventTemplate,
    DirectDamageEventTemplate,
    PenetrationDamageEventTemplate,
    DisorderDamageEventTemplate,
    PolarDisorderDamageEventTemplate,
    DischargeDamageEventTemplate,
    LuminanceFlareDamageEventTemplate,
    SettledAnomalyDamageEventTemplate,
    TurbulenceDamageEventTemplate,
)
from ..ids import DamageEventSemanticId, RuleItemId
from .contracts import InstantiatedDamageEvent
from .anomaly_source_profiles import anomaly_source_tick_multiplier


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
    polarity_anomaly_source_choice: AnomalySourceChoice | None = None,
    burnice_anomaly_source_choice: AnomalySourceChoice | None = None,
    grace_anomaly_source_choice: AnomalySourceChoice | None = None,
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
    elif isinstance(template, PolarDisorderDamageEventTemplate):
        if polarity_anomaly_source_choice is None:
            raise ValueError("Polar Disorder requires one selected anomaly source")
        record_id = anomaly_source_record_id(polarity_anomaly_source_choice)
        event = PolarDisorderDamageEvent(
            metadata=replace(metadata, element=polarity_anomaly_source_choice.element),
            disorder_triggerer=template.disorder_triggerer,
            source_anomaly_character_id=polarity_anomaly_source_choice.source_character_id,
            base_settlement_data_source=AnomalyRecordValueSource(record_id),
            history_record_source=record_id,
            polarity_multiplier=template.base_polarity_multiplier,
            anomaly_proficiency_coefficient=template.anomaly_proficiency_coefficient,
            crit_rule=NoCritRule(),
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
        selected_dynamic_source = None
        if template.source_multiplier_by_element:
            owner_id = str(template.damage_dealer)
            if owner_id == "character:1171":
                selected_dynamic_source = burnice_anomaly_source_choice
            elif owner_id == "character:1181":
                selected_dynamic_source = grace_anomaly_source_choice
        record_id = (
            anomaly_source_record_id(selected_dynamic_source)
            if selected_dynamic_source is not None
            else template.history_record_source or source_history_record_id
        )
        if record_id is None:
            raise ValueError("discharge event requires a typed source anomaly record")
        discharge_metadata = metadata
        discharge_multiplier = multiplier
        if selected_dynamic_source is not None:
            choice = selected_dynamic_source
            discharge_metadata = replace(metadata, element=choice.element)
            if not isinstance(multiplier, FixedMultiplier) or not isinstance(
                multiplier.value, Resolved
            ):
                raise ValueError("Burnice Discharge requires a resolved selected multiplier")
            source_ratio = next(
                (
                    value
                    for element, value in template.source_multiplier_by_element
                    if element is choice.element
                ),
                None,
            )
            if source_ratio is None:
                raise ValueError(
                    "Selected Discharge source element has no reviewed multiplier"
                )
            discharge_multiplier = FixedMultiplier(
                Resolved(
                    multiplier.value.value
                    * source_ratio
                    * anomaly_source_tick_multiplier(choice.element)
                )
            )
        event = DischargeDamageEvent(
            metadata=discharge_metadata,
            discharge_triggerer=template.discharge_triggerer,
            base_settlement_data_source=AnomalyRecordValueSource(record_id),
            history_record_source=record_id,
            multiplier=(
                source_anomaly_multiplier
                if template.multiplier_from_source_event
                and selected_dynamic_source is None
                and source_anomaly_multiplier is not None
                else discharge_multiplier
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
