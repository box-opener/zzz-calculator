"""Instantiate application templates as pure domain DamageEvents."""

from __future__ import annotations

from core.types import (
    AnomalyRecordValueSource,
    AttributeAnomalyDamageEvent,
    BattleStateId,
    BattleTime,
    DamageEventId,
    DamageEventMetadata,
    DirectDamageEvent,
    DisorderDamageEvent,
    CurrentAttributeAnomalyDamageEvent,
    SettledAnomalyDamageEvent,
    SettledDamageValueSource,
    EffectId,
    EnemyId,
)

from ..characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    CurrentAttributeAnomalyDamageEventTemplate,
    DamageEventTemplate,
    DirectDamageEventTemplate,
    DisorderDamageEventTemplate,
    SettledAnomalyDamageEventTemplate,
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
    metadata = template_metadata(
        template,
        battle_state_id=battle_state_id,
        target_enemy=target_enemy,
        created_at=created_at,
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
