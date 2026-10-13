from copy import deepcopy
import runpy
from pathlib import Path

import pytest

from core.presentation.substat_analysis import calculate_with_substat_gains
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import registration_for
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import _stats_mapping
from core.types import DRIVE_DISC_SUBSTAT_VALUES, DriveDiscStatKey
from dataclasses import replace
from core.types import Unresolved, UnresolvedReason
from core.presentation import calculation_service


def payload():
    raw = runpy.run_path(str(Path(__file__).with_name('test_web_api.py')))['_valid_calculation_payload']()
    raw['character_builds'] = {'character:1431': {'level':60,'build_mode':'equipment-build','drive_discs':[]}}
    raw['substat_analysis'] = ['character:1431']
    return raw


def test_extra_roll_uses_white_attack_and_flat_layers_without_changing_the_build():
    raw=payload(); original=deepcopy(raw)
    result=calculate_with_substat_gains(raw)
    rows={r['stat']:r for r in result['substat_gains'][0]['rows']}
    assert raw == original
    assert len(rows) == len(DRIVE_DISC_SUBSTAT_VALUES)
    assert rows['attack-percent']['modes']['expected']['gain_ratio'] == pytest.approx(.03)
    assert 0 < rows['attack-flat']['modes']['expected']['gain_ratio'] < .03
    assert rows['penetration-flat']['modes']['expected']['gain_ratio'] > 0
    assert rows['anomaly-proficiency-flat']['modes']['expected']['delta'] == 0
    assert not any(p['source_type']=='manual-adjustment' for p in result['build_provenance'])


def test_comparison_can_add_to_a_full_disc_without_creating_an_illegal_tenth_roll():
    raw=payload()
    raw['character_builds']['character:1431']['drive_discs']=[{'slot':1,'set_id':'31000','main_stat':'hp-flat',
        'substats':[{'stat':'attack-flat','roll_count':5},{'stat':'crit-rate','roll_count':2},
                    {'stat':'crit-damage','roll_count':1},{'stat':'anomaly-proficiency-flat','roll_count':1}]}]
    result=calculate_with_substat_gains(raw)
    flat=next(r for r in result['substat_gains'][0]['rows'] if r['stat']=='attack-flat')
    assert flat['modes']['expected']['complete']
    assert flat['modes']['expected']['delta'] > 0
    assert sum(s['roll_count'] for s in raw['character_builds']['character:1431']['drive_discs'][0]['substats'])==9


def test_crit_cap_is_recomputed_and_does_not_report_a_fake_increase():
    raw=payload()
    raw['character_builds']['character:1431']['base_stats']={**_stats_mapping(character_base_stats('character:1431',level=60)), 'crit_rate':1}
    result=calculate_with_substat_gains(raw)
    crit=next(r for r in result['substat_gains'][0]['rows'] if r['stat']=='crit-rate')
    assert crit['modes']['expected']['gain_ratio'] == pytest.approx(0)


def test_rupture_has_no_penetration_flat_recommendation():
    raw=payload();cid='character:1531'
    definition=registration_for(cid).compile_definition({'core_level':7,'cinema_level':0},(cid,),False)
    raw.update(primary_character_id=cid, team_character_ids=[cid], compile_configs={cid:{'core_level':7,'cinema_level':0}},
        move_entry_id=str(definition.move_entries[0].entry_id), character_builds={cid:{'level':60,'build_mode':'equipment-build'}},substat_analysis=[cid])
    result=calculate_with_substat_gains(raw)
    assert 'penetration-flat' not in {r['stat'] for r in result['substat_gains'][0]['rows']}


@pytest.mark.parametrize('selection',[[],['character:9999'],['character:1431','character:1431'],True])
def test_only_unique_active_team_members_may_be_compared(selection):
    raw=payload();raw['substat_analysis']=selection
    with pytest.raises(ValueError): calculate_with_substat_gains(raw)


def test_legacy_calculation_without_analysis_stays_identical():
    raw=payload(); del raw['substat_analysis']
    assert calculate_with_substat_gains(raw)==calculate_payload(raw)


def test_zero_baseline_has_absolute_gain_but_no_percentage():
    raw=payload()
    raw['character_builds']['character:1431']['base_stats']={**_stats_mapping(character_base_stats('character:1431',level=60)), 'attack':0}
    result=calculate_with_substat_gains(raw)
    attack=next(r for r in result['substat_gains'][0]['rows'] if r['stat']=='attack-flat')['modes']['expected']
    assert attack['complete'] and attack['before']==0 and attack['delta'] > 0
    assert attack['gain_ratio'] is None


def test_missing_crit_data_does_not_fabricate_zero_gain(monkeypatch):
    original=calculation_service._build_records
    def missing_crit(builds,definitions,**kwargs):
        records=original(builds,definitions,**kwargs)
        return tuple(replace(r,snapshot=replace(r.snapshot,settlement_stats=replace(r.snapshot.settlement_stats,
            crit_damage=Unresolved(reason=UnresolvedReason.MISSING_DATA,notes='test missing Crit Damage')))) for r in records)
    monkeypatch.setattr(calculation_service,'_build_records',missing_crit)
    result=calculate_with_substat_gains(payload())
    attack=next(r for r in result['substat_gains'][0]['rows'] if r['stat']=='attack-flat')
    assert attack['modes']['expected']['complete'] is False
    assert attack['modes']['expected']['delta'] is None
    assert attack['modes']['expected']['gain_ratio'] is None
    assert len(result['substat_gains'][0]['rows']) == len(DRIVE_DISC_SUBSTAT_VALUES)
