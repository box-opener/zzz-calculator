from __future__ import annotations

import pytest

from core.types import (
    BattleEventId,
    BattleEventMetadata,
    BattleStateId,
    CharacterId,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DamageTag,
    DamageTagFilter,
    DirectDamageEvent,
    Element,
    EnemyId,
    FixedMultiplier,
    HitId,
    MoveId,
    Resolved,
    SkillGroup,
    SkillGroupFilter,
    SkillHitEvent,
    StandardCritRule,
)


@pytest.mark.parametrize(
    ("move_name", "damage_tag"),
    (
        ("dash-attack", DamageTag.DASH_ATTACK),
        ("dodge-counter", DamageTag.DODGE_COUNTER),
    ),
)
def test_dodge_moves_share_group_but_keep_independent_damage_tags(
    move_name: str,
    damage_tag: DamageTag,
) -> None:
    actor = CharacterId("character:dodge")
    enemy = EnemyId("enemy:target")
    move_id = MoveId(f"move:{move_name}")
    skill_hit = SkillHitEvent(
        metadata=BattleEventMetadata(
            event_id=BattleEventId(f"event:{move_name}"),
            battle_state_id=BattleStateId("battle:1"),
            occurred_at=1.0,
        ),
        actor=actor,
        target_enemy=enemy,
        element=Element.PHYSICAL,
        skill_group=SkillGroup.DODGE,
        move_id=move_id,
        hit_id=HitId(f"hit:{move_name}"),
    )
    damage = DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId(f"damage:{move_name}"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=actor,
            target_enemy=enemy,
            element=Element.PHYSICAL,
            created_at=1.0,
            skill_group=SkillGroup.DODGE,
            move_id=move_id,
            damage_tags=frozenset({damage_tag}),
        ),
        base_settlement_data_source=CurrentAttackValueSource(actor),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(actor),
    )

    assert skill_hit.skill_group is SkillGroup.DODGE
    assert damage.metadata.skill_group is SkillGroup.DODGE
    assert damage.metadata.damage_tags == frozenset({damage_tag})
    assert DamageTag.BASIC_ATTACK not in damage.metadata.damage_tags


def test_dodge_group_and_move_specific_filter_axes_remain_distinct() -> None:
    group_filter = SkillGroupFilter(SkillGroup.DODGE)
    dash_filter = DamageTagFilter(DamageTag.DASH_ATTACK)
    counter_filter = DamageTagFilter(DamageTag.DODGE_COUNTER)

    assert group_filter.skill_group is SkillGroup.DODGE
    assert dash_filter.damage_tag is DamageTag.DASH_ATTACK
    assert counter_filter.damage_tag is DamageTag.DODGE_COUNTER
    assert dash_filter != counter_filter
    assert DamageTag.DASH_ATTACK is not DamageTag.DODGE_COUNTER
    assert SkillGroup.DODGE.value not in {tag.value for tag in DamageTag}
