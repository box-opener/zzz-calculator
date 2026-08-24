import json
import os

with open("dict/zzz_crisis_buffs.json", "r", encoding="utf-8") as f:
    db = json.load(f)

# Find all buffs
all_buffs = []
for group_id, group in db.items():
    if "stages" not in group:
        continue
    for stage_id, stage in group["stages"].items():
        if "selectable_buffs" not in stage:
            continue
        for idx, buff in enumerate(stage["selectable_buffs"]):
            all_buffs.append({
                "group_id": group_id,
                "group_name": group.get("name", ""),
                "stage_id": stage_id,
                "stage_name": stage.get("stage_name", ""),
                "buff_index": idx,
                "id": buff["id"],
                "title": buff["title"],
                "desc": buff["desc"]
            })

print(f"Total buffs found in database: {len(all_buffs)}")

# Group by title
by_title = {}
for b in all_buffs:
    by_title.setdefault(b["title"], []).append(b)

print(f"Unique buff titles: {len(by_title)}")

# Print titles with different descriptions or TBD
for title, list_of_buffs in by_title.items():
    # Check if there are different descriptions
    descs = set(b["desc"] for b in list_of_buffs)
    if len(descs) > 1 or title == "TBD" or "TBD" in title:
        print(f"\nTitle: {title} (has {len(list_of_buffs)} instances, {len(descs)} unique descriptions)")
        for b in list_of_buffs:
            print(f"  Group {b['group_id']} ({b['group_name']}) | Stage {b['stage_id']} ({b['stage_name']}) | Buff {b['buff_index']+1}")
            print(f"  Desc snippet: {b['desc'][:100]}...")
