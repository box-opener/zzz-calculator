with open("archive/chunk_zzz_01.js", "r", encoding="utf-8") as f:
    js = f.read()

import re
matches = re.finditer(r'static\.nanoka\.cc/assets', js)
for m in matches:
    start = max(0, m.start() - 200)
    end = min(len(js), m.end() + 500)
    print(f"=== Match at {m.start()} ===")
    print(js[start:end])
    print("-" * 50)
