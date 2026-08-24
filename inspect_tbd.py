import json

with open("dict/zzz_crisis_buffs.json", "r", encoding="utf-8") as f:
    db = json.load(f)

tbd_count = 0
for group_id, group in db.items():
    if "stages" not in group:
        continue
    for stage_id, stage in group["stages"].items():
        if "selectable_buffs" not in stage:
            continue
        for idx, buff in enumerate(stage["selectable_buffs"]):
            if "TBD" in buff["title"] or "TBD" in buff["desc"] or buff["title"] == "TBD":
                tbd_count += 1
                print(f"Group: {group_id} | Stage: {stage_id} ({stage['stage_name']}) | Index: {idx} | Title: {buff['title']} | Desc: {buff['desc']}")

print(f"Total TBD buffs found: {tbd_count}")
