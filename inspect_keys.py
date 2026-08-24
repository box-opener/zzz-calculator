import json

def search_nested_keys(data, path=""):
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else k
            if isinstance(v, (str, bool, int, float)) or v is None:
                v_str = str(v)
                if any(x in k.lower() or x in v_str.lower() for x in ["icon", "img", "image", "path", ".png", ".jpg", ".webp"]):
                    results.append((current_path, v_str))
            else:
                results.extend(search_nested_keys(v, current_path))
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = f"{path}[{idx}]"
            results.extend(search_nested_keys(item, current_path))
    return results

files = {
    "characters": "dict/zzz_characters.json",
    "weapons": "dict/zzz_weapons.json",
    "drive_discs": "dict/zzz_drive_discs.json",
    "monsters": "dict/zzz_monsters.json"
}

for name, filepath in files.items():
    print(f"=== {name} ===")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        first_key = list(data.keys())[0]
        first_item = data[first_key]
        print(f"Found {len(data)} items. Deep inspection of the first item (key: {first_key}):")
        found = search_nested_keys(first_item)
        for p, val in found[:20]:
            print(f"  {p}: {val}")
        if len(found) > 20:
            print(f"  ... and {len(found) - 20} more keys")
    elif isinstance(data, list) and data:
        print(f"Found list of {len(data)} items. Deep inspection of the first item:")
        found = search_nested_keys(data[0])
        for p, val in found[:20]:
            print(f"  {p}: {val}")
        if len(found) > 20:
            print(f"  ... and {len(found) - 20} more keys")
    print("\n")
