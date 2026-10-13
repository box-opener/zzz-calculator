import pytest
from core.presentation.enemy_catalog import enemy_catalog, enemy_defaults


def test_guardian_defaults_follow_source_growth_and_damage_resistance_not_buildup_resistance():
    enemy=next(e for e in enemy_catalog()['enemies'] if e['enemy_id']=='enemy:300021')
    assert enemy['display_name']=='「卫士Ⅱ型」'
    low=enemy_defaults('enemy:300021','11051',1)
    high=enemy_defaults('enemy:300021','11051',70)
    assert low['initial_defense']==54
    assert high['initial_defense']==pytest.approx(857.52)
    assert high['damage_resistance']['electric']==-.2
    assert high['damage_resistance']['fire']==.2
    assert high['stun_multiplier']==1.5
    assert 'luminance' not in high['damage_resistance']


def test_catalog_preserves_enemy_variants_and_missing_source_fields():
    data=enemy_catalog()
    assert data['source_version']=='3.2'
    assert len(data['enemies'])==306
    assert all(e['source_url'].startswith('https://static.nanoka.cc/zzz/3.2/zh/monster/') for e in data['enemies'])
    guardian=next(e for e in data['enemies'] if e['enemy_id']=='enemy:300021')
    assert {v['variant_id'] for v in guardian['variants']}=={'11051','11052'}
    assert next(e for e in data['enemies'] if e['enemy_id']=='enemy:10021')['variants']==[]


@pytest.mark.parametrize('enemy,variant,level',[('enemy:none','11051',70),('enemy:300021','none',70),('enemy:300021','11051',81),('enemy:300021','11051',True)])
def test_unknown_identity_or_level_does_not_get_demo_defaults(enemy,variant,level):
    with pytest.raises(ValueError):enemy_defaults(enemy,variant,level)
