"""Offline, version-pinned Nanoka endgame snapshots; never interpret buff prose."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

VERSION = '3.2'
ROOT = Path(__file__).parent / VERSION
MODES = ('shiyu', 'boss')
CN_TIME = timezone(timedelta(hours=8), name='Asia/Shanghai')


def plain_text(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


@lru_cache(maxsize=None)
def _read(name: str) -> dict:
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    if name not in manifest['sources']:
        raise ValueError('终局数据不属于已保存的正式版本')
    raw = (ROOT / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['sources'][name]['sha256']:
        raise ValueError('终局数据摘要不一致，请重新同步并审核')
    return json.loads(raw)


def seasons(mode: str, now: datetime | None = None) -> dict:
    if mode not in MODES:
        raise ValueError('终局模式仅支持危局和式舆')
    now = (now or datetime.now(CN_TIME)).astimezone(CN_TIME)
    rows = []
    for sid, item in _read(f'{mode}-index.json').items():
        begin, end = item.get('live_begin', item.get('begin', '')), item.get('live_end', item.get('end', ''))
        def time(value):
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(tzinfo=CN_TIME)
        status = 'permanent' if not begin or not end else 'current' if time(begin) <= now <= time(end) else 'future' if time(begin) > now else 'history'
        rows.append({'season_id': sid, 'name': item.get('zh', sid), 'begin': begin, 'end': end, 'status': status})
    rows.sort(key=lambda r: (r['begin'], int(r['season_id'])), reverse=True)
    return {'mode': mode, 'source_version': VERSION, 'timezone': 'Asia/Shanghai', 'seasons': rows}


@lru_cache(maxsize=None)
def _detail(mode: str, season_id: str) -> dict:
    if mode not in MODES or season_id not in _read(f'{mode}-index.json'):
        raise ValueError('未知终局期数')
    raw = _read(f'{mode}/{season_id}.json')
    source = f'https://static.nanoka.cc/zzz/{VERSION}/zh/{mode}/{season_id}.json'
    stages = []
    modes = raw.get('modes') or [{'id': season_id, 'zone_type': raw.get('zone_type', 0), 'zone': raw.get('zone', {})}]
    for group in modes:
        zones = group['zone']
        children = {str(child) for z in zones.values() for child in z.get('child', [])}
        for sid, stage in zones.items():
            if sid in children:
                continue
            room_stages = [(str(c), zones[str(c)]) for c in stage.get('child', [])] or [(sid, stage)]
            rooms = []
            for child_id, child in room_stages:
                for rid, room in child['layer_room'].items():
                    targets = []
                    for variant_id, target in room['monster_list'].items():
                        targets.append({'target_id': variant_id, 'enemy_id': f"enemy:{target['id']}", 'variant_id': variant_id,
                            'name': target['name'], 'level': child['monster_level'], 'stats': target['stats'], 'element_hints': target.get('element', {})})
                    def buffs(items, selectable=False):
                        return [{'buff_id': str(bid), 'title': b['title'] or f'场地条款 {bid}', 'text': plain_text(b['desc']),
                            'selectable': selectable} for bid, b in items.items() if b['desc']]
                    rooms.append({'room_id': rid, 'child_stage_id': child_id, 'name': child.get('name') or stage.get('name') or f'防线 {stage["stage_num"]}',
                        'waves': room.get('waves_num', 1), 'targets': targets,
                        'buffs': buffs(child.get('layer_buff', {})), 'selectable_buffs': buffs(child.get('selectable_buff', {}), True)})
            tiers = []
            # Source site's BossAdjust table: combat level is independent of HP tier.
            start = {1001: 1001, 1002: 1301}.get(group.get('zone_type'), 1001)
            for offset in range(29):
                adjustment = raw.get('boss_adjust', {}).get(str(start + offset))
                if adjustment is None:
                    break
                tiers.append({'tier': offset + 1, 'hp_rate': adjustment['hp'] / 10000, 'points': adjustment['points']})
            stages.append({'stage_id': sid, 'name': stage.get('name') or f'剧变节点第 {stage["stage_num"]} 防线',
                'difficulty': '困难' if group.get('zone_type') == 1002 else '普通' if mode == 'boss' else '防线',
                'difficulty_id': str(group['id']), 'rooms': rooms, 'hp_tiers': tiers})
    metadata = _read(f'{mode}-index.json')[season_id]
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    return {'mode': mode, 'season_id': season_id, 'source_version': VERSION, 'begin': metadata.get('live_begin', metadata.get('begin', '')),
        'end': metadata.get('live_end', metadata.get('end', '')), 'source_url': source, 'page_url': f'https://zzz.nanoka.cc/{mode}/{season_id}',
        'snapshot_sha256': manifest['sources'][f'{mode}/{season_id}.json']['sha256'], 'stages': stages}


def season_detail(mode: str, season_id: str) -> dict:
    return deepcopy(_detail(mode, season_id))
