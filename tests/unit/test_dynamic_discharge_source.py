from __future__ import annotations

from dataclasses import replace

import pytest

from core.application.characters.definition import CharacterCalculationDefinition
from core.application.characters.templates import (
    AttributeAnomalyDamageEventTemplate,
    DischargeDamageEventTemplate,
)
from core.application.diagnostics import DiagnosticKind
from core.application.execution.contracts import (
    HistoryRecordMode,
    MoveCalculationRequest,
)
from core.application.execution.event_factory import instantiate_damage_event
from core.application.execution.service import _prepare_dynamic_discharge_source
from core.application.ids import DamageEventSemanticId, MoveEntryId, MultiplierVariantId
from core.application.matching import (
    CharacterMatchProfile,
    EffectMatcher,
    EnemyMatchProfile,
)
from core.application.moves import (
    DamageEventTemplateRef,
    MoveCalculationEntry,
    MultiplierRelation,
    MultiplierVariant,
)
from core.application.scenario import CalculationScenario
from core.types import (
    AnomalyRecordId,
    AnomalySourceChoice,
    BASE_ELEMENT_BY_ELEMENT,
    BattleStateId,
    CharacterId,
    CharacterRole,
    CharacterSnapshot,
    CharacterStats,
    DamageSubtype,
    DamageType,
    DischargeDamageEvent,
    Element,
    EffectSourceType,
    EnemyId,
    EnemySnapshot,
    EventTemplateId,
    FixedMultiplier,
    NoCritRule,
    Resolved,
    RuleSource,
    RuleSourceId,
)
_OWNER = CharacterId("character:dynamic-discharge-owner")
_SOURCE = CharacterId("character:dynamic-discharge-source")
_OUTSIDER = CharacterId("character:dynamic-discharge-outsider")
_ENEMY = EnemyId("enemy:dynamic-discharge")

_BASE_RATIOS = {
    Element.PHYSICAL: 0.11,
    Element.FIRE: 0.22,
    Element.ELECTRIC: 0.33,
    Element.ICE: 0.44,
    Element.ETHER: 0.55,
    Element.WIND: 0.66,
}

_SOURCE_TICKS = {
    Element.PHYSICAL: 7.13,
    Element.LINREN: 7.13,
    Element.FIRE: 0.5,
    Element.ELECTRIC: 1.25,
    Element.ICE: 5.0,
    Element.LIESHUANG: 5.0,
    Element.ETHER: 0.625,
    Element.XUANMO: 0.625,
    Element.WIND: 12.5,
}


def _dynamic_template(*, uses_tick_profile: bool = True) -> DischargeDamageEventTemplate:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId("template:test:dynamic-discharge"),
        semantic_id=DamageEventSemanticId("event:test:dynamic-discharge"),
        label="Dynamic Discharge",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.DISCHARGE,
        element=Element.FIRE,
    )
    return DischargeDamageEventTemplate(
        ref=ref,
        damage_dealer=_OWNER,
        element=Element.FIRE,
        discharge_triggerer=_OWNER,
        history_record_source=None,
        crit_rule=NoCritRule(),
        move_id=None,
        source_multiplier_uses_tick_profile=uses_tick_profile,
        source_multiplier_by_element=tuple(_BASE_RATIOS.items()),
    )


def _anomaly_source_definition(
    *,
    character_id: CharacterId = _SOURCE,
    element: Element = Element.FIRE,
) -> CharacterCalculationDefinition:
    ref = DamageEventTemplateRef(
        template_id=EventTemplateId(f"template:{character_id}:ordinary-anomaly"),
        semantic_id=DamageEventSemanticId(f"event:{character_id}:ordinary-anomaly"),
        label="Ordinary anomaly source",
        damage_type=DamageType.ANOMALY,
        damage_subtype=DamageSubtype.ATTRIBUTE_ANOMALY,
        element=element,
    )
    template = AttributeAnomalyDamageEventTemplate(
        ref=ref,
        damage_dealer=character_id,
        element=element,
        anomaly_triggerer=character_id,
        history_record_source=AnomalyRecordId(
            f"anomaly:{character_id}:{element.value}"
        ),
        crit_rule=NoCritRule(),
        move_id=None,
    )
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId(f"move-entry:{character_id}:ordinary-anomaly"),
        character_id=character_id,
        move_id=None,
        display_name="Ordinary anomaly source",
        original_text="A compiled ordinary anomaly template for source validation.",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId(
                    f"variant:{character_id}:ordinary-anomaly"
                ),
                label="Default",
                parameter_name="Damage ratio",
                multiplier=FixedMultiplier(Resolved(1.0)),
            ),
        ),
        main_damage_event=ref,
    )
    return CharacterCalculationDefinition(
        character_id=character_id,
        role=CharacterRole.ANOMALY,
        base_element=element,
        source=RuleSource(
            RuleSourceId(f"source:{character_id}:test"),
            EffectSourceType.SKILL,
            "Dynamic-discharge source test",
        ),
        move_entries=(entry,),
        rule_items=(),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(template,),
    )


def _owner_definition() -> CharacterCalculationDefinition:
    template = _dynamic_template()
    entry = MoveCalculationEntry(
        entry_id=MoveEntryId("move-entry:test:dynamic-discharge"),
        character_id=_OWNER,
        move_id=None,
        display_name="Dynamic Discharge",
        original_text="Static source selection test.",
        skill_group=None,
        damage_tags=frozenset(),
        multiplier_relation=MultiplierRelation.COMPLETE,
        multiplier_variants=(
            MultiplierVariant(
                variant_id=MultiplierVariantId("variant:test:dynamic-discharge"),
                label="Default",
                parameter_name="Damage ratio",
                multiplier=FixedMultiplier(Resolved(1.0)),
            ),
        ),
        main_damage_event=template.ref,
    )
    return CharacterCalculationDefinition(
        character_id=_OWNER,
        role=CharacterRole.STUN,
        base_element=Element.FIRE,
        source=RuleSource(
            RuleSourceId("source:dynamic-discharge-owner:test"),
            EffectSourceType.SKILL,
            "Dynamic-discharge owner test",
        ),
        move_entries=(entry,),
        rule_items=(),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=(template,),
    )


def _stats() -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.5),
        crit_damage=Resolved(0.5),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.FIRE: Resolved(0.0)},
    )


def _request(
    *,
    choice: AnomalySourceChoice,
    source_definition: CharacterCalculationDefinition | None = None,
) -> MoveCalculationRequest:
    owner = _owner_definition()
    source = source_definition or _anomaly_source_definition()
    scenario = CalculationScenario(
        scenario_id="scenario:dynamic-discharge-test",
        current_operator=_OWNER,
    )
    return MoveCalculationRequest(
        definition=owner,
        supporting_definitions=(source,),
        move_entry_id=MoveEntryId("move-entry:test:dynamic-discharge"),
        scenario=scenario,
        battle_state_id=BattleStateId("battle:dynamic-discharge-test"),
        battle_time=0.0,
        base_character_snapshots=(
            CharacterSnapshot(_OWNER, 60, _stats()),
            CharacterSnapshot(source.character_id, 60, _stats()),
        ),
        target_snapshot=EnemySnapshot(
            enemy_id=_ENEMY,
            level=60,
            initial_defense=Resolved(1000.0),
            damage_resistance={},
            anomaly_buildup_resistance={},
            daze_resistance=Resolved(0.0),
            damage_reduction=Resolved(0.0),
        ),
        team_profiles=(
            CharacterMatchProfile(_OWNER, CharacterRole.STUN),
            CharacterMatchProfile(source.character_id, CharacterRole.ANOMALY),
        ),
        target_profile=EnemyMatchProfile(_ENEMY),
        discharge_anomaly_source_choice=choice,
    )


@pytest.mark.parametrize("element", tuple(_SOURCE_TICKS))
def test_dynamic_discharge_uses_base_curve_and_preserves_all_nine_source_elements(
    element: Element,
) -> None:
    choice = AnomalySourceChoice(_SOURCE, element)
    event = instantiate_damage_event(
        _dynamic_template(),
        FixedMultiplier(Resolved(2.0)),
        battle_state_id=BattleStateId("battle:dynamic-discharge-variants"),
        target_enemy=_ENEMY,
        created_at=0.0,
        discharge_anomaly_source_choice=choice,
    ).event

    assert isinstance(event, DischargeDamageEvent)
    base_element = BASE_ELEMENT_BY_ELEMENT[element]
    assert event.metadata.element is element
    assert event.discharge_triggerer == _OWNER
    assert event.history_record_source == AnomalyRecordId(
        f"anomaly:static-source:{_SOURCE}:{element.value.replace(':', '-')}"
    )
    assert event.base_settlement_data_source.record_id == event.history_record_source
    assert isinstance(event.multiplier, FixedMultiplier)
    assert isinstance(event.multiplier.value, Resolved)
    assert event.multiplier.value.value == pytest.approx(
        2.0 * _BASE_RATIOS[base_element] * _SOURCE_TICKS[element]
    )


@pytest.mark.parametrize(
    ("element", "uses_tick_profile", "expected"),
    (
        (Element.ETHER, True, 2.0 * 0.55 * 0.625),
        (Element.ETHER, False, 2.0 * 0.55),
        (Element.PHYSICAL, False, 2.0 * 0.11),
    ),
)
def test_dynamic_discharge_tick_profile_is_independent_of_source_multiplier_inheritance(
    element: Element,
    uses_tick_profile: bool,
    expected: float,
) -> None:
    template = _dynamic_template(uses_tick_profile=uses_tick_profile)
    event = instantiate_damage_event(
        template,
        FixedMultiplier(Resolved(2.0)),
        battle_state_id=BattleStateId("battle:dynamic-discharge-profile-flag"),
        target_enemy=_ENEMY,
        created_at=0.0,
        discharge_anomaly_source_choice=AnomalySourceChoice(_SOURCE, element),
    ).event

    assert isinstance(event, DischargeDamageEvent)
    assert isinstance(event.multiplier, FixedMultiplier)
    assert isinstance(event.multiplier.value, Resolved)
    assert event.multiplier.value.value == pytest.approx(expected)


@pytest.mark.parametrize(
    ("element", "uses_tick_profile", "expected"),
    (
        (Element.ETHER, True, 6.35 * 0.625),
        (Element.ETHER, False, 6.35),
        (Element.PHYSICAL, False, 6.35),
    ),
)
def test_dynamic_discharge_can_use_a_fixed_rate_without_applying_anomaly_tick_profile(
    element: Element,
    uses_tick_profile: bool,
    expected: float,
) -> None:
    template = replace(
        _dynamic_template(uses_tick_profile=uses_tick_profile),
        source_multiplier_by_element=((element, 6.35),),
    )
    event = instantiate_damage_event(
        template,
        FixedMultiplier(Resolved(1.0)),
        battle_state_id=BattleStateId("battle:dynamic-discharge-fixed-rate"),
        target_enemy=_ENEMY,
        created_at=0.0,
        discharge_anomaly_source_choice=AnomalySourceChoice(_SOURCE, element),
    ).event

    assert isinstance(event, DischargeDamageEvent)
    assert isinstance(event.multiplier, FixedMultiplier)
    assert isinstance(event.multiplier.value, Resolved)
    assert event.multiplier.value.value == pytest.approx(expected)


def test_source_choice_requires_team_and_compiled_anomaly_template() -> None:
    fire_choice = AnomalySourceChoice(_SOURCE, Element.FIRE)
    request = _request(choice=fire_choice)
    assert request.discharge_anomaly_source_choice == fire_choice

    with pytest.raises(ValueError, match="active teammate"):
        _request(
            choice=AnomalySourceChoice(_OUTSIDER, Element.FIRE),
        )

    with pytest.raises(
        ValueError,
        match="not backed by an active ordinary anomaly template",
    ):
        _request(
            choice=AnomalySourceChoice(_SOURCE, Element.ICE),
        )


def test_missing_explicit_discharge_source_is_local_diagnostic() -> None:
    request = _request(
        choice=AnomalySourceChoice(_SOURCE, Element.FIRE),
    )
    updated, diagnostics = _prepare_dynamic_discharge_source(
        request,
        request.base_character_snapshots,
        (),
        EffectMatcher(),
        frozenset(),
    )

    assert request.history_record_mode is HistoryRecordMode.EXPLICIT
    assert updated is request
    assert len(diagnostics) == 1
    assert diagnostics[0].kind is DiagnosticKind.MISSING_DATA
    assert diagnostics[0].blocking is True
    assert str(diagnostics[0].diagnostic_id).endswith(
        ":discharge-source-record-missing"
    )
