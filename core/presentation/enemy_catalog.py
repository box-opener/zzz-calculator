"""Sourced enemy identities, variants and level curves for the target picker."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def enemy_catalog() -> dict:
    data = json.loads((Path(__file__).parents[1] / 'data/enemies/catalog.json').read_text(encoding='utf-8'))
    if data['schema_version'] != 'zzz-enemy-catalog-v1':
        raise ValueError('unsupported enemy catalog version')
    return data


def enemy_defaults(enemy_id: str, variant_id: str, level: int) -> dict:
    if type(level) is not int or not 1 <= level <= 80:
        raise ValueError('怪物等级范围为 1–80')
    enemy = next((e for e in enemy_catalog()['enemies'] if e['enemy_id'] == enemy_id), None)
    if enemy is None:
        raise ValueError('未知怪物')
    variant = next((v for v in enemy['variants'] if v['variant_id'] == variant_id), None)
    if variant is None:
        raise ValueError('未知怪物变体或属性未提供')
    return {'enemy_id':enemy_id, 'variant_id':variant_id, 'level':level,
        'initial_defense': variant['base_defense'] * variant['defense_curve'][level - 1] / variant['curve_ratio'],
        'damage_resistance':variant['damage_resistance'], 'stun_multiplier':variant['stun_multiplier'],
        'can_stun':variant['can_stun'], 'source_url':enemy['source_url']}
