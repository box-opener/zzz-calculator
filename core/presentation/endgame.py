"""Validate named endgame selection; resolve sourced target and reviewed rules."""
from copy import deepcopy
import math

from core.data.endgame.loader import season_detail
from core.presentation.enemy_catalog import enemy_defaults
from core.application.endgame.compiler import compile_endgame


def resolve_selection(selection: dict, definitions: tuple) -> dict:
    if not isinstance(selection, dict):
        raise ValueError('endgame_selection 必须是对象')
    allowed = {'mode', 'season_id', 'stage_id', 'room_id', 'target_id', 'buff_ids', 'states', 'disabled_rules', 'hp_tier', 'enemy_overrides'}
    if set(selection) - allowed:
        raise ValueError('终局选择包含未知字段')
    detail = season_detail(str(selection.get('mode', '')), str(selection.get('season_id', '')))
    def choose(rows, field):
        value = str(selection.get(field, ''))
        item = next((r for r in rows if r[field] == value), None)
        if item is None:
            raise ValueError(f'终局 {field} 不属于当前期数或关卡')
        return item
    stage = choose(detail['stages'], 'stage_id')
    room = choose(stage['rooms'], 'room_id')
    target = choose(room['targets'], 'target_id')
    ids = selection.get('buff_ids', [])
    if not isinstance(ids, list) or any(not isinstance(v, str) for v in ids) or len(set(ids)) != len(ids):
        raise ValueError('可选增益必须为不重复的 ID 数组')
    # This version compares one optional buff per trial; zero is a deliberate control scene.
    if len(ids) > 1:
        raise ValueError('本版每次计算最多比较一个可选场地增益')
    available = {b['buff_id']: b for b in room['selectable_buffs']}
    if set(ids) - set(available):
        raise ValueError('所选增益不属于当前关卡')
    buffs = room['buffs'] + [available[bid] for bid in ids]
    states = selection.get('states', {})
    if not isinstance(states, dict):
        raise ValueError('终局状态必须为命名整数对象')
    context = {**detail, 'stage_id': stage['stage_id'], 'room_id': room['room_id'],
        'mode_label': '危局强袭战' if detail['mode'] == 'boss' else '式舆防卫战'}
    compiled = compile_endgame(context, buffs, definitions, states)
    disabled = selection.get('disabled_rules', [])
    known = {str(r.rule_id) for r in compiled.rules}
    if not isinstance(disabled, list) or len(set(disabled)) != len(disabled) or set(disabled) - known:
        raise ValueError('被排除的场地规则不属于当前场景')
    try:
        base = enemy_defaults(target['enemy_id'], target['variant_id'], target['level'])
    except ValueError:
        base = {'damage_resistance': {}, 'stun_vulnerability_bonus': None}
    enemy = {'enemy_id': target['enemy_id'], 'variant_id': target['variant_id'], 'level': target['level'],
        'initial_defense': target['stats'].get('defence'), 'damage_resistance': dict(base['damage_resistance']),
        'stun_vulnerability_bonus': base['stun_vulnerability_bonus'], 'damage_reduction': 0, 'is_stunned': False}
    field_sources = {'level': detail['source_url'], 'initial_defense': detail['source_url'],
        'damage_resistance': base.get('source_url'), 'stun_vulnerability_bonus': base.get('source_url')}
    default_enemy = deepcopy(enemy)
    tier = selection.get('hp_tier', len(stage['hp_tiers']) or 1)
    if type(tier) is not int or not 1 <= tier <= (len(stage['hp_tiers']) or 1):
        raise ValueError('危局生命档位不合法')
    hp_rate = stage['hp_tiers'][tier - 1]['hp_rate'] if stage['hp_tiers'] else 1
    max_hp = math.floor(target['stats'].get('hp', 0) * hp_rate)
    overrides = selection.get('enemy_overrides', {})
    if not isinstance(overrides, dict) or set(overrides) - set(enemy):
        raise ValueError('目标覆写字段不合法')
    if {'enemy_id', 'variant_id'} & set(overrides):
        raise ValueError('终局目标身份不可通过属性覆写改变')
    for key, value in overrides.items():
        if key == 'damage_resistance':
            if not isinstance(value, dict) or set(value) - {'fire', 'ice', 'electric', 'physical', 'ether', 'wind', 'luminance'}:
                raise ValueError('目标抗性覆写字段不合法')
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in value.values()):
                raise ValueError('目标抗性必须为有限数值')
            enemy[key].update(value)
        elif key == 'is_stunned':
            if not isinstance(value, bool):
                raise ValueError('敌人失衡状态必须为布尔值')
            enemy[key] = value
        elif type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('目标覆写属性必须为有限数值')
        else:
            if key == 'level' and (type(value) is not int or not 1 <= value <= 80):
                raise ValueError('目标等级必须为 1–80 的整数')
            if key == 'initial_defense' and value < 0:
                raise ValueError('目标防御不可为负数')
            enemy[key] = value
        field_sources[key] = 'user-explicit-override'
    missing = [key for key in ('initial_defense', 'stun_vulnerability_bonus') if enemy[key] is None]
    missing.extend(f'damage_resistance.{element}' for element in ('fire', 'ice', 'electric', 'physical', 'ether', 'wind', 'luminance') if element not in enemy['damage_resistance'])
    provenance = {k: detail[k] for k in ('mode', 'season_id', 'source_version', 'snapshot_sha256', 'source_url', 'page_url')}
    provenance.update(stage_id=stage['stage_id'], room_id=room['room_id'], target_id=target['target_id'],
        stage_name=stage['name'], room_name=room['name'],
        target_name=target['name'], difficulty=stage['difficulty'], hp_tier=tier, maximum_hp=max_hp,
        buff_ids=[b['buff_id'] for b in buffs], states=deepcopy(states), disabled_rules=disabled,
        enemy_overrides=deepcopy(overrides), field_sources=field_sources, missing_fields=missing, clauses=list(compiled.clauses))
    return {'compiled': compiled, 'enemy': enemy, 'defaults': default_enemy, 'provenance': provenance, 'buffs': buffs, 'disabled': frozenset(disabled)}


def editor_payload(selection: dict, definitions: tuple) -> dict:
    scene = resolve_selection(selection, definitions)
    compiled = scene['compiled']
    return {'enemy': scene['enemy'], 'defaults': scene['defaults'], 'provenance': scene['provenance'], 'buffs': scene['buffs'],
        'controls': list(compiled.controls), 'clauses': list(compiled.clauses),
        'rules': [{'rule_id': str(r.rule_id), 'label': r.display_name, 'source_label': r.source.label,
            'source_type': 'environment', 'enabled': str(r.rule_id) not in scene['disabled']} for r in compiled.rules]}
