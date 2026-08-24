import json

files = {
    "character": "archive/full_character.json",
    "weapon": "archive/full_weapon.json",
    "monster": "archive/full_monster.json",
    "equipment": "archive/full_equipment.json"
}

for name, path in files.items():
    print(f"=== Manifest: {name} ===")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Type: {type(data).__name__}")
    if isinstance(data, dict):
        keys = list(data.keys())
        print(f"Keys count: {len(keys)}, sample keys: {keys[:5]}")
        first_key = keys[0]
        item = data[first_key]
        print(f"Sample item '{first_key}':")
        print(json.dumps(item, ensure_ascii=False, indent=2)[:500])
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
        if data:
            print("Sample item 0:")
            print(json.dumps(data[0], ensure_ascii=False, indent=2)[:500])
    print("\n")
