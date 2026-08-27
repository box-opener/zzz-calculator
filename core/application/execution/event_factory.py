"""Instantiate application templates as pure domain DamageEvents."""

from __future__ import annotations

from core.types import (
    BattleStateId,
    BattleTime,
    DamageEventId,
    DamageEventMetadata,
    DirectDamageEvent,
    EffectId,
    EnemyId,
)

from ..characters.templates import DirectDamageEventTemplate
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


def template_metadata(
    template: DirectDamageEventTemplate,
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
