from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import runpy

import pytest

from core.data.endgame.loader import CN_TIME, ROOT, seasons, season_detail
from core.application.endgame.reviewed import REVIEWED
from core.presentation.calculation_service import calculate_payload, _compile_definitions
from core.presentation.endgame import editor_payload, resolve_selection
from core.presentation.substat_analysis import calculate_with_substat_gains


def payload():
    raw = runpy.run_path(str(Path(__file__).with_name('test_web_api.py')))['_valid_calculation_payload']()
    raw['character_builds'] = {'character:1431': {'level': 60, 'build_mode': 'equipment-build'}}
    raw['enabled_rule_item_ids'] = []
    return raw


def selection(mode='shiyu', sid='62058', stage_index=-1, room_index=1):
    detail = season_detail(mode, sid)
    stage = detail['stages'][stage_index]
    room = stage['rooms'][room_index]
    return {'mode': mode, 'season_id': sid, 'stage_id': stage['stage_id'], 'room_id': room['room_id'], 'target_id': room['targets'][0]['target_id']}


def test_current_season_uses_china_time_and_formal_catalog():
    now = datetime(2026, 10, 13, 12, tzinfo=CN_TIME)
    assert next(r for r in seasons('boss', now)['seasons'] if r['status']=='current')['season_id']=='690471'
    assert next(r for r in seasons('shiyu', now)['seasons'] if r['status']=='current')['season_id']=='62058'
    assert seasons('shiyu', now)['source_version']=='3.2'
    with pytest.raises(ValueError): seasons('simulation')


def test_every_snapshot_hash_and_historical_room_can_be_read_offline():
    total = 0
    for mode in ('boss', 'shiyu'):
        for row in seasons(mode)['seasons']:
            detail = season_detail(mode, row['season_id'])
            assert len(detail['snapshot_sha256'])==64
            assert detail['stages']
            for stage in detail['stages']:
                for room in stage['rooms']:
                    assert room['targets']
                    assert all(1 <= t['level'] <= 80 for t in room['targets'])
            total += 1
    assert total==109


def test_third_room_is_retained_and_buffs_do_not_leak_between_rooms():
    rooms = season_detail('shiyu','62058')['stages'][-1]['rooms']
    assert len(rooms)==3
    ids=[{b['buff_id'] for b in room['buffs']} for room in rooms]
    assert '62001581' in ids[0] and '62001582' not in ids[0]
    assert '62001582' in ids[1] and '62001583' not in ids[1]


def test_reviewed_evidence_has_explicit_mapping_for_every_saved_buff():
    evidence=json.loads(Path('core/application/endgame/reviewed-evidence.json').read_text(encoding='utf-8'))
    assert len(evidence)==249
    assert set(evidence) <= set(REVIEWED)
    assert all(isinstance(v,tuple) for v in REVIEWED.values())


def test_no_enabled_field_rule_is_identical_to_same_ordinary_target():
    raw=payload();sel=selection();scene=resolve_selection(sel,_compile_definitions(raw))
    sel['disabled_rules']=[str(r.rule_id) for r in scene['compiled'].rules]
    ordinary={**raw,'enemy':scene['enemy']}
    endgame={**raw,'endgame_selection':sel}
    assert calculate_payload(ordinary)['totals']==calculate_payload(endgame)['totals']


def test_triggered_defense_reduction_uses_formal_defense_region():
    raw=payload();sel=selection();scene=resolve_selection(sel,_compile_definitions(raw))
    sel['states']={'buff:62001582:异常后的减防仍有效':1}
    buffed=calculate_payload({**raw,'endgame_selection':sel})
    enemy=deepcopy(scene['enemy']);enemy['initial_defense']*=.9
    ordinary=calculate_payload({**raw,'enemy':enemy})
    assert buffed['totals']['expected']['value']==pytest.approx(ordinary['totals']['expected']['value'])
    def sources(value):
        if isinstance(value,dict):
            yield value.get('source_type')
            for item in value.values(): yield from sources(item)
        elif isinstance(value,list):
            for item in value: yield from sources(item)
    assert 'environment' in set(sources(buffed['events']))


def test_attack_role_buff_and_personal_ultimate_do_not_default_to_triggered():
    raw=payload();sel=selection('boss','690471',0,0)
    baseline=calculate_payload({**raw,'endgame_selection':sel})
    sel['buff_ids']=['69014702']
    boosted=calculate_payload({**raw,'endgame_selection':sel})
    assert boosted['totals']['expected']['value']==pytest.approx(baseline['totals']['expected']['value']*1.2)
    controls=editor_payload(sel,_compile_definitions(raw))['controls']
    key=next(c['key'] for c in controls if '终结技' in c['key'])
    assert key.endswith(':character:1431')
    sel['states']={key:1}
    active=calculate_payload({**raw,'endgame_selection':sel})
    assert active['totals']['non-crit']['value']==boosted['totals']['non-crit']['value']
    assert active['totals']['full-crit']['value'] > boosted['totals']['full-crit']['value']


def test_boss_hp_tier_changes_hp_without_changing_combat_level_or_damage():
    raw=payload();sel=selection('boss','690471',0,0)
    low=calculate_payload({**raw,'endgame_selection':{**sel,'hp_tier':1}})
    high=calculate_payload({**raw,'endgame_selection':{**sel,'hp_tier':24}})
    assert low['totals']==high['totals']
    assert low['scenario_provenance']['maximum_hp'] < high['scenario_provenance']['maximum_hp']
    assert resolve_selection({**sel,'hp_tier':24},_compile_definitions(raw))['enemy']['level']==70


def test_substat_gains_use_same_field_scene_once_and_leave_payload_unchanged():
    raw=payload();raw['endgame_selection']={**selection('boss','690471',0,0),'buff_ids':['69014702']}
    raw['substat_analysis']=['character:1431'];before=deepcopy(raw)
    out=calculate_with_substat_gains(raw)
    rows={r['stat']:r for r in out['substat_gains'][0]['rows']}
    # Build rolls use white attack; in-combat percentages multiply initial attack (spec 8.4).
    assert rows['attack-percent']['modes']['expected']['gain_ratio']==pytest.approx(.03)
    assert rows['attack-percent']['modes']['expected']['before']==calculate_payload(raw)['totals']['expected']['value']
    assert rows['crit-rate']['modes']['expected']['complete']
    assert out['scenario_provenance']['season_id']=='690471'
    assert raw==before


def test_sharp_unknown_does_not_block_current_supported_damage():
    raw=payload();sel={**selection('shiyu','62058',-1,0)}
    out=calculate_payload({**raw,'endgame_selection':sel})
    assert out['totals']['expected']['complete']
    assert any(c['status']=='unresolved' for c in out['scenario_provenance']['clauses'])


def test_unknown_crit_clause_is_local_to_active_boss_phase():
    raw=payload();sel=selection('boss','690471',1,0)
    out=calculate_payload({**raw,'endgame_selection':sel})
    assert out['totals']['expected']['complete']
    sel['states']={'buff:69013601:赴火层数':1}
    active=calculate_payload({**raw,'endgame_selection':sel})
    assert not active['totals']['expected']['complete']
    assert any('乘区' in d['message'] for d in active['diagnostics'])


@pytest.mark.parametrize('change',[
    {'stage_id':'foreign'}, {'room_id':'foreign'}, {'target_id':'foreign'}, {'buff_ids':['69014701']},
    {'hp_tier':False}, {'states':{'foreign':1}}, {'disabled_rules':['foreign']},
    {'states':{'buff:62001582:异常后的减防仍有效':2}},
    {'enemy_overrides':{'enemy_id':'enemy:40009'}}, {'enemy_overrides':{'initial_defense':float('nan')}},
])
def test_foreign_selection_and_invalid_state_are_rejected(change):
    with pytest.raises(ValueError): resolve_selection({**selection(),**change},_compile_definitions(payload()))


def test_manual_field_overrides_are_explicit_and_restore_to_sourced_defaults():
    definitions=_compile_definitions(payload());sel=selection()
    original=resolve_selection(sel,definitions)
    changed=resolve_selection({**sel,'enemy_overrides':{'initial_defense':100,'damage_resistance':{'luminance':0}}},definitions)
    assert changed['enemy']['initial_defense']==100
    assert changed['defaults']['initial_defense']==original['enemy']['initial_defense']
    assert changed['provenance']['field_sources']['initial_defense']=='user-explicit-override'
    assert 'damage_resistance.luminance' not in changed['provenance']['missing_fields']


@pytest.mark.parametrize('move,suffix', [('electric-anomaly','anom'),('electric-disorder','disorder')])
def test_triggered_anomaly_and_disorder_buffs_use_their_own_regions(move,suffix):
    raw=payload();cid='character:1251'
    raw.update(primary_character_id=cid,team_character_ids=[cid],compile_configs={cid:{'core_level':7,'cinema_level':0}},
        character_builds={cid:{'level':60,'build_mode':'equipment-build'}},move_entry_id=f'move-entry:{cid}:{move}')
    sel={**selection('boss','690471',0,0),'buff_ids':['69014701']}
    baseline=calculate_payload({**raw,'endgame_selection':sel})
    sel['states']={'buff:69014701:异放或紊乱后的增益仍有效':1}
    active=calculate_payload({**raw,'endgame_selection':sel})
    assert baseline['totals']['expected']['complete']
    assert active['totals']['expected']['complete']
    assert active['totals']['expected']['value']==pytest.approx(baseline['totals']['expected']['value']*1.25)


def test_role_specific_buff_has_no_effect_on_support_character():
    raw=payload();cid='character:1411'
    raw.update(primary_character_id=cid,team_character_ids=[cid],compile_configs={cid:{'core_level':7,'cinema_level':0}},
        character_builds={cid:{'level':60,'build_mode':'equipment-build'}},move_entry_id='move-entry:yuzuha:1411:dodge-dash')
    sel=selection('boss','690471',0,0)
    plain=calculate_payload({**raw,'endgame_selection':sel})
    buffed=calculate_payload({**raw,'endgame_selection':{**sel,'buff_ids':['69014702']}})
    assert plain['totals']['expected']['complete']
    assert plain['totals']==buffed['totals']


def test_personal_buff_stays_on_its_recipient_after_switching_operator():
    raw=payload();support='character:1411'
    raw['team_character_ids'].append(support)
    raw['supporting_character_ids']=[support]
    raw['compile_configs'][support]={'core_level':7,'cinema_level':0}
    raw['character_builds'][support]={'level':60,'build_mode':'equipment-build'}
    sel={**selection('boss','690471',0,0),'buff_ids':['69014702']}
    plain=calculate_payload({**raw,'endgame_selection':sel})
    sel['states']={'buff:69014702:该角色终结技后的增益仍有效:character:1431':1}
    boosted=calculate_payload({**raw,'endgame_selection':sel})
    assert boosted['totals']['full-crit']['value'] > plain['totals']['full-crit']['value']
    raw.update(primary_character_id=support,team_character_ids=[support,'character:1431'],supporting_character_ids=['character:1431'],move_entry_id='move-entry:yuzuha:1411:dodge-dash')
    support_plain=calculate_payload({**raw,'endgame_selection':{**sel,'states':{}}})
    support_active=calculate_payload({**raw,'endgame_selection':sel})
    assert support_plain['totals']['expected']['complete']
    assert support_plain['totals']==support_active['totals']


def test_calculate_rejects_bypassing_named_field_selection():
    raw=payload();raw['endgame_selection']=selection()
    compiled=resolve_selection(raw['endgame_selection'],_compile_definitions(raw))['compiled']
    raw['enabled_rule_item_ids']=[str(compiled.rules[0].rule_id)]
    with pytest.raises(ValueError,match='任意场地'):calculate_payload(raw)
    raw['enabled_rule_item_ids']=[]
    raw['condition_values']={str(compiled.conditions[0].condition_id):True}
    with pytest.raises(ValueError,match='场地状态'):calculate_payload(raw)


def test_endgame_api_is_offline_and_invalid_selection_is_a_client_error():
    from fastapi.testclient import TestClient
    from web.api import app
    client=TestClient(app)
    assert client.get('/api/v1/endgame/seasons?mode=boss').status_code==200
    assert client.get('/api/v1/endgame/seasons/shiyu/62058').json()['stages'][-1]['rooms'][2]['name']=='房间三'
    assert client.get('/api/v1/endgame/seasons/boss/foreign').status_code==400
    raw=payload();raw['endgame_selection']=selection()
    assert client.post('/api/v1/endgame/editor',json=raw).status_code==200
    raw['endgame_selection']['target_id']='foreign'
    assert client.post('/api/v1/endgame/editor',json=raw).status_code==400
