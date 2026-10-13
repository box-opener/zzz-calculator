"""Refresh the offline enemy catalog from an explicitly selected Nanoka version.

Run from the repository root: python scripts/sync_nanoka_enemies.py --version 3.2
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import re
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {'User-Agent':'Mozilla/5.0', 'Referer':'https://zzz.nanoka.cc/monster'}


def read_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def sync(version):
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*',version):
        raise ValueError('Use an explicit numeric source version')
    base = f'https://static.nanoka.cc/zzz/{version}'
    index = read_json(f'{base}/monster.json')
    cache = ROOT / '.cache/nanoka-enemies' / version
    cache.mkdir(parents=True, exist_ok=True)

    def fetch(pair):
        key, summary = pair
        url = f'{base}/zh/monster/{key}.json'
        # Cache raw source for review; the app consumes only the normalized catalog.
        data = read_json(url)
        (cache / f'{key}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        variants = []
        for variant_id, variant in data.get('monster_info',{}).items():
            stats = variant.get('stats',{})
            curve = variant.get('curves',{}).get('defence',{})
            if not isinstance(stats.get('defence'),(int,float)) or not curve.get('ratio') or len(curve.get('curve',[])) < 80:
                continue
            resistances = {element:stats[f'{element}_damage_res']/10000
                for element in ('physical','fire','ice','electric','ether','wind','luminance')
                if f'{element}_damage_res' in stats}
            variants.append({'variant_id':str(variant_id),'code_name':variant.get('code_name',''),
                'base_defense':stats['defence'],'defense_curve':curve['curve'][:80],'curve_ratio':curve['ratio'],
                'damage_resistance':resistances,'stun_multiplier':1+stats.get('stun_damage_taken_ratio',0)/10000,
                'can_stun':stats.get('is_stun',False)})
        return {'enemy_id':f'enemy:{key}','display_name':data.get('name') or summary.get('zh') or f'怪物 {key}',
            'rank':{1:'C',2:'B',3:'A',4:'S'}.get(summary['rarity'],str(summary['rarity'])),
            'faction':data.get('group_desc',''),'default_variant_id':str(data.get('monster_id','')),
            'variants':variants,'source_url':url,'page_url':f'https://zzz.nanoka.cc/monster/{key}'}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        entries = list(pool.map(fetch,index.items()))
    payload = {'schema_version':'zzz-enemy-catalog-v1','source_version':version,
        'source_index':f'{base}/monster.json','fetched_at':datetime.now(timezone.utc).isoformat(),'enemies':entries}
    # Only publish after every source fetch succeeds, preserving the old catalog on error.
    target = ROOT / 'core/data/enemies/catalog.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    temporary.replace(target)
    print(f"Updated {len(entries)} enemies / {sum(len(e['variants']) for e in entries)} variants from {version}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default='3.2')
    sync(parser.parse_args().version)
