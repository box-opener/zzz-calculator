from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.calculation import CalculationNode
from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_ELEMENTS,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    BASE_ELEMENT_BY_ELEMENT,
    AnomalyContribution,
    AnomalyRecord,
    AnomalyRecordId,
    AnomalyRecordValueSource,
    AttributeAnomalyDamageKind,
    AttributeAnomalyStateKind,
    BattleState,
    BattleStateId,
    Character,
    CharacterCombatState,
    CharacterId,
    CharacterPanelLayers,
    CharacterRef,
    CharacterRole,
    CharacterStats,
    CalculationNodeMultiplier,
    CurrentAttackValueSource,
    DamageEventId,
    DamageEventMetadata,
    DamageSubtype,
    DamageTag,
    DamageType,
    DirectDamageEvent,
    DynamicIdentity,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    Enemy,
    EnemyCombatState,
    EnemyId,
    FieldPosition,
    FixedMultiplier,
    IndependentAnomalyCrit,
    ModifierEffect,
    ModifierResult,
    NoAnomalyCrit,
    NoCritRule,
    Resolved,
    RuleSource,
    RuleSourceId,
    OperationState,
    SnapshotRule,
    StandardCritRule,
    State,
    StateId,
    StateKind,
    TurbulenceDamageEvent,
    Unresolved,
    UnresolvedReason,
    UnresolvedSharpExplosionDamageEvent,
)


def _contribution(
    contributor: CharacterId,
    *,
    occurred_at: float = 0.0,
) -> AnomalyContribution:
    return AnomalyContribution(
        contributor=contributor,
        actual_written_buildup=1.0,
        anomaly_effect_strength=Resolved(1000.0),
        impact_strength=Resolved(100.0),
        occurred_at=occurred_at,
    )


def _anomaly_record(
    *,
    element: Element,
    contributors: tuple[CharacterId, ...],
    anomaly_triggerer: CharacterId,
    contributions: tuple[AnomalyContribution, ...],
) -> AnomalyRecord:
    return AnomalyRecord(
        record_id=AnomalyRecordId(f"anomaly:{element.value}"),
        target_enemy=EnemyId("enemy:1"),
        element=element,
        damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[element],
        state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[element],
        weighted_anomaly_effect_strength=Resolved(1000.0),
        weighted_impact_strength=Resolved(100.0),
        anomaly_damage_bonus_region=Resolved(1.0),
        contributors=contributors,
        anomaly_triggerer=anomaly_triggerer,
        crit_capability=NoAnomalyCrit(),
        triggered_at=1.0,
        duration=Resolved(10.0),
        contributions=contributions,
    )


def test_damage_type_and_subtype_are_separate_closed_vocabularies() -> None:
    assert DamageType.ANOMALY.value == "anomaly"
    assert DamageSubtype.TURBULENCE.value == "turbulence"
    assert "disorder" not in {item.value for item in DamageSubtype}


def test_variant_element_identity_is_preserved_until_a_base_element_is_needed() -> None:
    assert Element.LIESHUANG in ANOMALY_ELEMENTS
    assert BASE_ELEMENT_BY_ELEMENT[Element.LIESHUANG] is Element.ICE
    assert Element.LIESHUANG is not Element.ICE
    assert Element.LUMINANCE not in ANOMALY_ELEMENTS


@pytest.mark.parametrize(
    ("element", "base_element", "damage_kind", "state_kind"),
    (
        (
            Element.LIESHUANG,
            Element.ICE,
            AttributeAnomalyDamageKind.SHATTER,
            AttributeAnomalyStateKind.LIESHUANG_FROSTBITE,
        ),
        (
            Element.XUANMO,
            Element.ETHER,
            AttributeAnomalyDamageKind.CORRUPTION,
            AttributeAnomalyStateKind.CORRUPTION,
        ),
        (
            Element.LINREN,
            Element.PHYSICAL,
            AttributeAnomalyDamageKind.ASSAULT,
            AttributeAnomalyStateKind.FLINCH,
        ),
    ),
)
def test_anomaly_record_preserves_each_variant_element_identity(
    element: Element,
    base_element: Element,
    damage_kind: AttributeAnomalyDamageKind,
    state_kind: AttributeAnomalyStateKind,
) -> None:
    contributor = CharacterId("character:variant")
    record = _anomaly_record(
        element=element,
        contributors=(contributor,),
        anomaly_triggerer=contributor,
        contributions=(_contribution(contributor),),
    )

    assert record.element is element
    assert BASE_ELEMENT_BY_ELEMENT[record.element] is base_element
    assert record.damage_kind is damage_kind
    assert record.state_kind is state_kind


def test_dynamic_identity_cannot_be_used_as_an_effect_target() -> None:
    assert DynamicIdentity.DAMAGE_DEALER.value not in {item.value for item in EffectTarget}
    with pytest.raises(ValueError):
        EffectTarget(DynamicIdentity.DAMAGE_DEALER.value)


def test_direct_damage_has_no_anomaly_subtype() -> None:
    dealer = CharacterId("character:direct")
    event = DirectDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:direct"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=dealer,
            target_enemy=EnemyId("enemy:1"),
            element=Element.FIRE,
            created_at=0.0,
            damage_tags=frozenset({DamageTag.BASIC_ATTACK}),
        ),
        base_settlement_data_source=CurrentAttackValueSource(dealer),
        multiplier=FixedMultiplier(Resolved(1.0)),
        crit_rule=StandardCritRule(dealer),
    )

    assert event.damage_type is DamageType.DIRECT
    assert event.damage_subtype is None


def test_anomaly_record_keeps_contributors_triggerer_and_weighted_sources() -> None:
    contributor = CharacterId("character:non-wind")
    triggerer = CharacterId("character:triggerer")
    record = AnomalyRecord(
        record_id=AnomalyRecordId("anomaly:1"),
        target_enemy=EnemyId("enemy:1"),
        element=Element.PHYSICAL,
        damage_kind=AttributeAnomalyDamageKind.ASSAULT,
        state_kind=AttributeAnomalyStateKind.FLINCH,
        weighted_anomaly_effect_strength=Resolved(4321.0),
        weighted_impact_strength=Resolved(222.0),
        anomaly_damage_bonus_region=Resolved(1.2),
        contributors=(contributor, triggerer),
        anomaly_triggerer=triggerer,
        crit_capability=IndependentAnomalyCrit(
            crit_rate=Resolved(1.0),
            crit_damage=Resolved(0.5),
            inherited_by=(DamageSubtype.TURBULENCE,),
        ),
        triggered_at=4.0,
        duration=Resolved(10.0),
        contributions=(
            AnomalyContribution(
                contributor=contributor,
                actual_written_buildup=75.0,
                anomaly_effect_strength=Resolved(4000.0),
                impact_strength=Resolved(200.0),
                occurred_at=2.0,
            ),
            AnomalyContribution(
                contributor=triggerer,
                actual_written_buildup=25.0,
                anomaly_effect_strength=Resolved(5284.0),
                impact_strength=Resolved(288.0),
                occurred_at=4.0,
            ),
        ),
    )

    assert record.anomaly_triggerer is triggerer
    assert record.contributors == (contributor, triggerer)
    assert record.weighted_anomaly_effect_strength == Resolved(4321.0)
    assert record.weighted_impact_strength == Resolved(222.0)


def test_anomaly_record_rejects_missing_detailed_contributor_identity() -> None:
    contributor_a = CharacterId("character:a")
    contributor_b = CharacterId("character:b")
    contributor_c = CharacterId("character:c")

    with pytest.raises(ValueError, match="exactly match contributors"):
        _anomaly_record(
            element=Element.PHYSICAL,
            contributors=(contributor_a, contributor_b, contributor_c),
            anomaly_triggerer=contributor_a,
            contributions=(
                _contribution(contributor_a),
                _contribution(contributor_b),
            ),
        )


def test_anomaly_record_rejects_triggerer_without_detailed_contribution() -> None:
    contributor = CharacterId("character:contributor")
    triggerer = CharacterId("character:triggerer")

    with pytest.raises(ValueError, match="triggerer must have a detailed contribution"):
        _anomaly_record(
            element=Element.PHYSICAL,
            contributors=(contributor, triggerer),
            anomaly_triggerer=triggerer,
            contributions=(_contribution(contributor),),
        )


def test_anomaly_record_allows_multiple_contributions_from_one_identity() -> None:
    contributor = CharacterId("character:repeated")

    record = _anomaly_record(
        element=Element.PHYSICAL,
        contributors=(contributor,),
        anomaly_triggerer=contributor,
        contributions=(
            _contribution(contributor, occurred_at=1.0),
            _contribution(contributor, occurred_at=2.0),
        ),
    )

    assert len(record.contributions) == 2


def test_turbulence_separates_dealer_trigger_and_historical_value_source() -> None:
    wind_triggerer = CharacterId("character:wind")
    record_id = AnomalyRecordId("anomaly:non-wind")
    event = TurbulenceDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:turbulence"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=wind_triggerer,
            target_enemy=EnemyId("enemy:1"),
            element=Element.PHYSICAL,
            created_at=6.0,
        ),
        wind_anomaly_triggerer=wind_triggerer,
        base_settlement_data_source=AnomalyRecordValueSource(record_id),
        history_record_source=record_id,
        multiplier=CalculationNodeMultiplier(
            CalculationNode.TURBULENCE_TOTAL_MULTIPLIER
        ),
        crit_rule=NoCritRule(),
    )

    assert event.metadata.damage_dealer is wind_triggerer
    assert event.wind_anomaly_triggerer is wind_triggerer
    assert event.base_settlement_data_source.record_id is record_id
    assert event.history_record_source is record_id
    assert event.damage_subtype is DamageSubtype.TURBULENCE


def test_state_and_effect_remain_distinct_objects() -> None:
    owner = CharacterId("character:owner")
    source = RuleSource(
        source_id=RuleSourceId("source:core-passive"),
        source_type=EffectSourceType.CORE_PASSIVE,
        label="core passive",
    )
    effect = ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId("effect:attack"),
            source=source,
            owner=owner,
            target=EffectTarget.SELF,
            snapshot_rule=SnapshotRule.LIVE,
        ),
        result=ModifierResult(
            modifier_path=CalculationNode.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
            operation=EffectOperation.ADD,
            value=Resolved(0.2),
        ),
    )
    state = State(
        state_id=StateId("state:buff"),
        kind=StateKind.BUFF,
        holder=CharacterRef(owner),
        source=source,
        duration=None,
        stacking=None,
        current_stacks=1,
        effects=(effect,),
    )

    assert state.effects == (effect,)
    assert state is not effect
    assert effect.result_kind == "modifier"


def _stats(*, hp: float = 10000.0) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(hp),
        attack=Resolved(1000.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.05),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={},
    )


def test_battle_state_keeps_current_hp_position_and_operation_state_separate() -> None:
    character_id = CharacterId("character:1")
    enemy_id = EnemyId("enemy:1")
    character = Character(
        character_id=character_id,
        name="character",
        role=CharacterRole.ATTACK,
        element=Element.FIRE,
        level=60,
        panels=CharacterPanelLayers(base=_stats(), initial=_stats(hp=12000.0)),
    )
    enemy = Enemy(
        enemy_id=enemy_id,
        name="enemy",
        level=80,
        initial_defense=Resolved(1000.0),
    )
    battle = BattleState(
        state_id=BattleStateId("battle:1"),
        time=0.0,
        characters={character_id: character},
        character_combat={
            character_id: CharacterCombatState(
                current_stats=_stats(hp=12000.0),
                current_hp=Resolved(8000.0),
                field_position=FieldPosition.FRONT,
                operation_state=OperationState.OPERATED,
            )
        },
        enemies={enemy_id: enemy},
        enemy_combat={enemy_id: EnemyCombatState(current_daze=Resolved(0.0))},
    )

    combat = battle.character_combat[character_id]
    assert combat.current_hp == Resolved(8000.0)
    assert combat.current_stats.hp == Resolved(12000.0)
    assert combat.field_position is FieldPosition.FRONT
    assert combat.operation_state is OperationState.OPERATED


def test_unimplemented_sharp_explosion_is_explicitly_unresolved() -> None:
    unresolved = Unresolved(
        reason=UnresolvedReason.NOT_IMPLEMENTED_IN_SPEC,
        notes="spec-v1 states that sharp explosion is not implemented",
    )
    event = UnresolvedSharpExplosionDamageEvent(
        metadata=DamageEventMetadata(
            event_id=DamageEventId("damage:sharp-explosion"),
            battle_state_id=BattleStateId("battle:1"),
            damage_dealer=CharacterId("character:1"),
            target_enemy=EnemyId("enemy:1"),
            element=Element.PHYSICAL,
            created_at=0.0,
        ),
        unresolved=unresolved,
    )

    assert event.damage_type is DamageType.SHARP_EXPLOSION
    assert event.unresolved is unresolved


def test_type_layer_does_not_import_calculation_layer() -> None:
    types_dir = Path(__file__).parents[2] / "core" / "types"
    violations: list[str] = []
    for path in types_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "core.calculation"
            ):
                violations.append(f"{path.name}:{node.lineno}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("core.calculation"):
                        violations.append(f"{path.name}:{node.lineno}")

    assert violations == []
