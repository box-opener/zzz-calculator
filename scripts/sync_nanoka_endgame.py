"""Download explicit formal endgame snapshots into a review directory.

python scripts/sync_nanoka_endgame.py --version 3.2
Review the staged sources and clause hashes before publishing them to core/data.
The script never rewrites reviewed-evidence.json or enables new effects.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://zzz.nanoka.cc/boss'}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=45) as response:
        data = response.read()
    json.loads(data)
    return data


def sync(version):
    if not re.fullmatch(r'\d+(?:\.\d+)*', version):
        raise ValueError('必须指定数字形式的数据版本')
    target = ROOT / '.cache/nanoka-endgame' / version
    target.mkdir(parents=True, exist_ok=True)
    base = f'https://static.nanoka.cc/zzz/{version}'
    manifest = {'version': version, 'fetched_at': datetime.now(timezone.utc).isoformat(), 'sources': {}}
    tasks = []
    for mode in ('boss', 'shiyu'):
        url = f'{base}/{mode}.json'
        data = fetch(url)
        name = f'{mode}-index.json'
        (target / name).write_bytes(data)
        manifest['sources'][name] = {'url': url, 'sha256': hashlib.sha256(data).hexdigest()}
        for sid in json.loads(data):
            if not sid.isdigit():
                raise ValueError('源期数 ID 不合法')
            tasks.append((f'{mode}/{sid}.json', f'{base}/zh/{mode}/{sid}.json'))

    def download(task):
        name, url = task
        data = fetch(url)
        path = target / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        return name, {'url': url, 'sha256': hashlib.sha256(data).hexdigest()}

    with ThreadPoolExecutor(max_workers=6) as pool:
        for name, source in pool.map(download, tasks):
            manifest['sources'][name] = source
    (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'已保存 {len(tasks)} 份期数快照到 {target}；审核后再发布到 core/data/endgame。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='3.2')
    sync(parser.parse_args().version)
