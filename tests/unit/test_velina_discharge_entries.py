from copy import deepcopy

import pytest

from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import compile_registered_definition
from core.types import CharacterId
from tests.unit.test_web_api import _velina_payload


OWNER = 'character:1561'
ALLY = 'character:1261'


def payload(key, core=7, cinema=0):
    raw = _velina_payload(f'move-entry:{OWNER}:{key}')
    raw.update(team_character_ids=[OWNER, ALLY], supporting_character_ids=[ALLY],
               formation_character_ids=[OWNER, ALLY])
    raw['compile_configs'][OWNER] = {'core_level': core, 'cinema_level': cinema}
    raw['compile_configs'][ALLY] = {'core_level': 7, 'cinema_level': 0}
    raw['character_builds'][ALLY] = {'level': 60, 'build_mode': 'equipment-build'}
    raw['condition_values'] = {
        'condition:velina:enemy-wind-weathered': True,
        'condition:velina:micro-cyclone-dissipating': True,
        'condition:velina:broad-cyclone-dissipating': True,
    }
    definition = compile_registered_definition(OWNER, raw['compile_configs'][OWNER],
                                              (CharacterId(OWNER), CharacterId(ALLY)))
    raw['enabled_rule_item_ids'] = [str(rule.rule_id) for rule in definition.rule_items
                                    if rule.eligibility.value != 'ineligible']
    return raw


@pytest.mark.parametrize('core, micro, broad', [(1, .85, 1.35), (7, 1.45, 2.55)])
@pytest.mark.parametrize('key', ['micro-cyclone-dissipation', 'broad-cyclone-dissipation',
                                 'ultimate-wind-discharge'])
def test_selectable_discharge_uses_absolute_skill_multiplier_and_only_one_event(core, micro, broad, key):
    raw = payload(key, core)
    result = calculate_payload(raw)
    baseline = deepcopy(raw)
    baseline['move_entry_id'] = f'move-entry:{OWNER}:wind-weathering'
    weathering = calculate_payload(baseline)
    multiplier = {'micro-cyclone-dissipation': micro,
                  'broad-cyclone-dissipation': broad, 'ultimate-wind-discharge': 6.8}[key]
    assert result['totals']['expected']['complete']
    assert len(result['events']) == 1
    event = result['events'][0]
    assert event['damage_type'] == 'anomaly'
    assert event['damage_subtype'] == 'discharge'
    assert event['element'] == 'wind'
    assert event.get('skill_group') is None
    assert not event.get('damage_tags')
    nodes = {n['node']: n['value'] for n in event['modes']['expected']['calculation_breakdown']}
    assert nodes['anomaly.discharge.total-multiplier'] == pytest.approx(multiplier)
    weathering_nodes = {n['node']: n['value'] for n in
                       weathering['events'][0]['modes']['expected']['calculation_breakdown']}
    assert weathering_nodes['anomaly.attribute.multiplier'] == 12.5
    assert nodes['anomaly.effect-strength'] == weathering_nodes['anomaly.effect-strength']
    assert nodes['anomaly.attribute.damage-bonus-region'] == weathering_nodes['anomaly.attribute.damage-bonus-region']
    assert result['totals']['expected']['value'] == pytest.approx(
        weathering['totals']['expected']['value'] * multiplier / 12.5)


@pytest.mark.parametrize('key, condition', [
    ('micro-cyclone-dissipation', 'condition:velina:micro-cyclone-dissipating'),
    ('broad-cyclone-dissipation', 'condition:velina:broad-cyclone-dissipating'),
    ('ultimate-wind-discharge', 'condition:velina:enemy-wind-weathered'),
])
def test_standalone_discharge_requires_the_authored_current_state(key, condition):
    raw = payload(key)
    raw['condition_values'][condition] = False
    result = calculate_payload(raw)
    assert not result['totals']['expected']['complete']
    assert result['events'] == []


def test_ultimate_discharge_requires_additional_ability_team_eligibility():
    definition = compile_registered_definition(OWNER, {'core_level': 7, 'cinema_level': 0},
                                              (CharacterId(OWNER),))
    assert f'move-entry:{OWNER}:ultimate-wind-discharge' not in {
        str(entry.entry_id) for entry in definition.move_entries}


def test_standalone_micro_discharge_matches_existing_child_without_repeating_body_damage():
    raw = payload('micro-cyclone-dissipation', cinema=6)
    raw['parameter_values']['parameter:velina:wind-weathering-remaining-seconds'] = 12
    standalone = calculate_payload(raw)
    raw['move_entry_id'] = f'move-entry:{OWNER}:micro-cyclone'
    combined = calculate_payload(raw)
    children = [event for event in combined['events'] if event['damage_subtype'] == 'discharge']
    assert combined['totals']['expected']['complete']
    assert len(children) == 1
    assert standalone['events'][0]['modes']['expected']['value'] == pytest.approx(
        children[0]['modes']['expected']['value'])
