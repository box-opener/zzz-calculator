from dataclasses import replace

from core.presentation.calculation_service import (
    _build_records,
    _resolve_seed_core_partner,
)
from core.presentation.registry import compile_registered_definition
from core.presentation.requests import CharacterBuildInput
from core.types import CharacterId, Resolved


SEED = CharacterId("character:1461")
ANTON = CharacterId("character:1111")
BILLY = CharacterId("character:1081")


def _panel(attack: float, element: str) -> dict[str, object]:
    return {
        "hp": 9000.0,
        "attack": attack,
        "defense": 800.0,
        "impact": 120.0,
        "crit_rate": 0.5,
        "crit_damage": 0.5,
        "anomaly_mastery": 100.0,
        "anomaly_proficiency": 100.0,
        "energy_regen": 1.2,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: 0.0},
    }


def test_seed_partner_resolution_uses_initial_attack_not_current_attack() -> None:
    team = (SEED, ANTON, BILLY)
    definitions = tuple(
        compile_registered_definition(
            character_id,
            {"core_level": 7, "cinema_level": 0} if character_id == SEED else {},
            team,
            strict=False,
        )
        for character_id in team
    )
    builds = tuple(
        CharacterBuildInput(
            character_id=str(character_id),
            level=60,
            out_of_combat_stats=_panel(attack, element),
        )
        for character_id, attack, element in (
            (SEED, 1200.0, "electric"),
            (ANTON, 1900.0, "electric"),
            (BILLY, 2100.0, "physical"),
        )
    )
    records = _build_records(builds, definitions)
    records_with_current_buff = tuple(
        replace(
            record,
            snapshot=replace(
                record.snapshot,
                settlement_stats=replace(
                    record.snapshot.settlement_stats,
                    attack=Resolved(99999.0),
                ),
            ),
        )
        if record.snapshot.character_id == ANTON
        else record
        for record in records
    )

    resolved = _resolve_seed_core_partner(
        definitions,
        team,
        records_with_current_buff,
        {str(SEED): {"core_level": 7, "cinema_level": 0}},
    )
    partner_rule = next(
        item
        for item in resolved[0].rule_items
        if str(item.rule_id) == "rule:character:1461:core:partner-bright-attack"
    )

    assert {effect.rule.recipient_character_id for effect in partner_rule.effects} == {
        BILLY
    }


def test_seed_partner_resolution_keeps_placeholder_when_any_candidate_panel_is_missing() -> None:
    team = (SEED, ANTON, BILLY)
    definitions = tuple(
        compile_registered_definition(
            character_id,
            {"core_level": 7, "cinema_level": 0} if character_id == SEED else {},
            team,
            strict=False,
        )
        for character_id in team
    )
    incomplete = _panel(1500.0, "physical")
    del incomplete["attack"]
    builds = tuple(
        CharacterBuildInput(
            character_id=str(character_id),
            level=60,
            out_of_combat_stats=stats,
        )
        for character_id, stats in (
            (SEED, _panel(1200.0, "electric")),
            (ANTON, _panel(1900.0, "electric")),
            (BILLY, incomplete),
        )
    )
    records = _build_records(builds, definitions)

    resolved = _resolve_seed_core_partner(
        definitions,
        team,
        records,
        {str(SEED): {"core_level": 7, "cinema_level": 0}},
    )
    partner_rule = next(
        item
        for item in resolved[0].rule_items
        if str(item.rule_id) == "rule:character:1461:core:partner-bright-attack"
    )

    assert partner_rule.effects
    assert all(effect.result_kind == "unresolved" for effect in partner_rule.effects)
    assert any(
        str(item.diagnostic_id)
        == "ambiguous:character:1461:core-partner-selection"
        for item in resolved[0].diagnostics
    )
