from __future__ import annotations

from core.application.characters.lucy import LUCY_ID, LucyCompileConfig, compile_lucy, load_raw_record
from core.application.characters.templates import DirectDamageEventTemplate
from core.application.execution.contracts import PanelModifierExecutionTrace
from core.application.execution.modifiers import ModifierApplicationResult
from core.application.execution.service import _friendly_actor_snapshot
from core.data.loader import load_character_record
from core.types import (
    CalculationNode,
    CharacterId,
    CharacterSnapshot,
    CharacterStats,
    EffectId,
    EffectOperation,
    Resolved,
)


def test_lucy_friendly_actor_uses_current_owner_panel_plus_two_cheer_increments() -> None:
    raw = load_raw_record(load_character_record(str(LUCY_ID)))
    definition = compile_lucy(
        LucyCompileConfig(additional_ability_eligible=True),
        raw,
    )
    template = next(
        item
        for item in definition.damage_event_templates
        if isinstance(item, DirectDamageEventTemplate)
        and item.friendly_actor_owner_id == LUCY_ID
    )
    owner = CharacterSnapshot(
        character_id=LUCY_ID,
        level=60,
        settlement_stats=CharacterStats(
            hp=Resolved(10000.0),
            attack=Resolved(1300.0),
            defense=Resolved(600.0),
            impact=Resolved(100.0),
            crit_rate=Resolved(0.25),
            crit_damage=Resolved(0.5),
            anomaly_mastery=Resolved(100.0),
            anomaly_proficiency=Resolved(100.0),
            penetration_rate=Resolved(0.0),
            penetration_flat=Resolved(0.0),
            energy_regen=Resolved(1.0),
            element_damage_bonus={},
        ),
    )
    cheer_effect_id = EffectId("effect:character:1151:cheer-on:team-attack")
    cheer_trace = PanelModifierExecutionTrace(
        recipient_character_id=LUCY_ID,
        owner_character_id=LUCY_ID,
        rule_item_id=None,
        effect_id=cheer_effect_id,
        modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        operation=EffectOperation.ADD,
        resolved_value=300.0,
    )
    application = ModifierApplicationResult(
        character_snapshots=(owner,),
        event_modifiers=(),
        panel_traces=(cheer_trace,),
    )

    actor = _friendly_actor_snapshot(template, application)

    assert actor is not None
    assert actor.character_id == CharacterId("friendly-actor:character:1151:bodyguard-pig")
    assert actor.settlement_stats.attack == Resolved(1900.0)
    assert actor.settlement_stats.impact == owner.settlement_stats.impact
    assert actor.settlement_stats.anomaly_proficiency == owner.settlement_stats.anomaly_proficiency
    assert actor.settlement_stats.crit_rate == owner.settlement_stats.crit_rate
    assert actor.settlement_stats.crit_damage == owner.settlement_stats.crit_damage
    assert actor.settlement_stats.element_damage_bonus == {}
    assert actor.settlement_stats.penetration_rate != owner.settlement_stats.penetration_rate
