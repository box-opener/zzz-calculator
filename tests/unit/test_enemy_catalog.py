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
    assert high['stun_vulnerability_bonus']==.5
    assert 'luminance' not in high['damage_resistance']


def test_catalog_preserves_enemy_variants_and_missing_source_fields():
    data=enemy_catalog()
    assert data['source_version']=='3.2'
    assert len(data['enemies'])==306
    assert all(e['source_url'].startswith('https://static.nanoka.cc/zzz/3.2/zh/monster/') for e in data['enemies'])
    guardian=next(e for e in data['enemies'] if e['enemy_id']=='enemy:300021')
    assert {v['variant_id'] for v in guardian['variants']}=={'11051','11052'}
    assert next(e for e in data['enemies'] if e['enemy_id']=='enemy:10021')['variants']==[]


def test_every_sourced_variant_adds_the_stun_unit_base_only_during_settlement():
    from core.calculation.regions.vulnerability import (
        BroadVulnerabilityRegionInput, calculate_broad_vulnerability_region,
    )
    for enemy in enemy_catalog()['enemies']:
        for variant in enemy['variants']:
            defaults = enemy_defaults(enemy['enemy_id'], variant['variant_id'], 70)
            bonus = defaults['stun_vulnerability_bonus']
            assert bonus == pytest.approx(variant['stun_multiplier'] - 1)
            stunned = calculate_broad_vulnerability_region(BroadVulnerabilityRegionInput(
                is_stunned=True, stun_vulnerability=bonus,
            ))
            assert stunned.value == pytest.approx(variant['stun_multiplier'])
            # Additional stun effects remain additive, alongside ordinary vulnerability.
            boosted = calculate_broad_vulnerability_region(BroadVulnerabilityRegionInput(
                is_stunned=True, stun_vulnerability=bonus + .3, normal_vulnerability=.2,
            ))
            assert boosted.value == pytest.approx(variant['stun_multiplier'] + .5)
            normal = calculate_broad_vulnerability_region(BroadVulnerabilityRegionInput(
                is_stunned=False, stun_vulnerability=bonus,
            ))
            assert normal.value == 1


@pytest.mark.parametrize('enemy,variant,level',[('enemy:none','11051',70),('enemy:300021','none',70),('enemy:300021','11051',81),('enemy:300021','11051',True)])
def test_unknown_identity_or_level_does_not_get_demo_defaults(enemy,variant,level):
    with pytest.raises(ValueError):enemy_defaults(enemy,variant,level)
