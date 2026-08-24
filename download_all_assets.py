import os
import json
import urllib.request
import urllib.error
import time

# Directories
DICT_DIR = "dict"
ARCHIVE_DIR = "archive"
ASSET_DIR = "asset"

SUB_DIRS = {
    "character": os.path.join(ASSET_DIR, "character"),
    "weapon": os.path.join(ASSET_DIR, "weapon"),
    "drive_disc": os.path.join(ASSET_DIR, "drive_disc"),
    "monster": os.path.join(ASSET_DIR, "monster")
}

# Ensure directories exist
for folder in SUB_DIRS.values():
    os.makedirs(folder, exist_ok=True)

# CDN configurations
CDN_BASE = "https://static.nanoka.cc/assets/zzz/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_basename(path_str):
    """Extract basename without extension from a path string."""
    base = os.path.basename(path_str)
    name, _ = os.path.splitext(base)
    return name

def download_image(url, local_path):
    """Download image from url to local_path if it doesn't exist."""
    if os.path.exists(local_path):
        return True
    
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        with open(local_path, "wb") as f:
            f.write(data)
        print(f"Downloaded: {url} -> {local_path} ({len(data)} bytes)")
        time.sleep(0.05) # Polite delay
        return True
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for URL: {url}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

# =====================================================================
# 1. PROCESS CHARACTERS
# =====================================================================
def process_characters():
    print("\n--- Processing Characters ---")
    char_manifest_path = os.path.join(ARCHIVE_DIR, "full_character.json")
    char_dict_path = os.path.join(DICT_DIR, "zzz_characters.json")
    
    with open(char_manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(char_dict_path, "r", encoding="utf-8") as f:
        char_db = json.load(f)
        
    success_count = 0
    fail_count = 0
    
    for cid, char_info in char_db.items():
        manifest_item = manifest.get(cid, {})
        icon_name = manifest_item.get("icon")
        
        if not icon_name:
            print(f"Warning: No icon key in manifest for Character ID {cid} ({char_info.get('name')})")
            continue
            
        url = f"{CDN_BASE}{icon_name}.webp"
        local_filename = f"{icon_name}.webp"
        local_path = os.path.join(SUB_DIRS["character"], local_filename)
        
        if download_image(url, local_path):
            char_db[cid]["icon_path"] = f"asset/character/{local_filename}"
            success_count += 1
        else:
            fail_count += 1
            
    with open(char_dict_path, "w", encoding="utf-8") as f:
        json.dump(char_db, f, ensure_ascii=False, indent=2)
        
    char_js_path = char_dict_path.replace(".json", ".js")
    with open(char_js_path, "w", encoding="utf-8") as f_js:
        f_js.write(f"window.ZZZ_CHARACTERS = {json.dumps(char_db, ensure_ascii=False, indent=2)};")
        
    print(f"Characters: {success_count} successfully downloaded, {fail_count} failed.")

# =====================================================================
# 2. PROCESS WEAPONS
# =====================================================================
def process_weapons():
    print("\n--- Processing Weapons ---")
    weapon_manifest_path = os.path.join(ARCHIVE_DIR, "full_weapon.json")
    weapon_dict_path = os.path.join(DICT_DIR, "zzz_weapons.json")
    
    with open(weapon_manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(weapon_dict_path, "r", encoding="utf-8") as f:
        weapon_db = json.load(f)
        
    success_count = 0
    fail_count = 0
    
    for wid, weapon_info in weapon_db.items():
        manifest_item = manifest.get(wid, {})
        icon_name = manifest_item.get("icon")
        
        if not icon_name:
            print(f"Warning: No icon key in manifest for Weapon ID {wid} ({weapon_info.get('name')})")
            continue
            
        url = f"{CDN_BASE}{icon_name}.webp"
        local_filename = f"{icon_name}.webp"
        local_path = os.path.join(SUB_DIRS["weapon"], local_filename)
        
        if download_image(url, local_path):
            weapon_db[wid]["icon_path"] = f"asset/weapon/{local_filename}"
            success_count += 1
        else:
            fail_count += 1
            
    with open(weapon_dict_path, "w", encoding="utf-8") as f:
        json.dump(weapon_db, f, ensure_ascii=False, indent=2)
        
    weapon_js_path = weapon_dict_path.replace(".json", ".js")
    with open(weapon_js_path, "w", encoding="utf-8") as f_js:
        f_js.write(f"window.ZZZ_WEAPONS = {json.dumps(weapon_db, ensure_ascii=False, indent=2)};")
        
    print(f"Weapons: {success_count} successfully downloaded, {fail_count} failed.")

# =====================================================================
# 3. PROCESS DRIVE DISCS
# =====================================================================
def process_drive_discs():
    print("\n--- Processing Drive Discs ---")
    disc_dict_path = os.path.join(DICT_DIR, "zzz_drive_discs.json")
    
    with open(disc_dict_path, "r", encoding="utf-8") as f:
        disc_db = json.load(f)
        
    success_count = 0
    fail_count = 0
    
    # Drive discs have sets which is a dict of ID -> info containing "icon_path"
    sets = disc_db.get("sets", {})
    for eid, set_info in sets.items():
        raw_path = set_info.get("icon_path", "")
        if not raw_path:
            continue
            
        icon_base = get_basename(raw_path)
        url = f"{CDN_BASE}{icon_base}.webp"
        local_filename = f"{icon_base}.webp"
        local_path = os.path.join(SUB_DIRS["drive_disc"], local_filename)
        
        if download_image(url, local_path):
            sets[eid]["icon_path"] = f"asset/drive_disc/{local_filename}"
            success_count += 1
        else:
            fail_count += 1
            
    disc_db["sets"] = sets
    with open(disc_dict_path, "w", encoding="utf-8") as f:
        json.dump(disc_db, f, ensure_ascii=False, indent=2)
        
    disc_js_path = disc_dict_path.replace(".json", ".js")
    with open(disc_js_path, "w", encoding="utf-8") as f_js:
        f_js.write(f"window.ZZZ_DRIVE_DISCS = {json.dumps(disc_db, ensure_ascii=False, indent=2)};")
        
    print(f"Drive Discs: {success_count} successfully downloaded, {fail_count} failed.")

# =====================================================================
# 4. PROCESS MONSTERS
# =====================================================================
def process_monsters():
    print("\n--- Processing Monsters ---")
    monster_manifest_path = os.path.join(ARCHIVE_DIR, "full_monster.json")
    monster_dict_path = os.path.join(DICT_DIR, "zzz_monsters.json")
    
    with open(monster_manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(monster_dict_path, "r", encoding="utf-8") as f:
        monster_db = json.load(f)
        
    success_count = 0
    fail_count = 0
    
    for mid, monster_info in monster_db.items():
        manifest_item = manifest.get(mid, {})
        raw_icon = manifest_item.get("icon", "")
        
        if not raw_icon:
            print(f"Warning: No icon in manifest for Monster ID {mid} ({monster_info.get('name')})")
            continue
            
        icon_base = get_basename(raw_icon)
        url = f"{CDN_BASE}{icon_base}.webp"
        local_filename = f"{icon_base}.webp"
        local_path = os.path.join(SUB_DIRS["monster"], local_filename)
        
        if download_image(url, local_path):
            monster_db[mid]["icon_path"] = f"asset/monster/{local_filename}"
            success_count += 1
        else:
            fail_count += 1
            
    with open(monster_dict_path, "w", encoding="utf-8") as f:
        json.dump(monster_db, f, ensure_ascii=False, indent=2)
        
    monster_js_path = monster_dict_path.replace(".json", ".js")
    with open(monster_js_path, "w", encoding="utf-8") as f_js:
        f_js.write(f"window.ZZZ_MONSTERS = {json.dumps(monster_db, ensure_ascii=False, indent=2)};")
        
    print(f"Monsters: {success_count} successfully downloaded, {fail_count} failed.")

# =====================================================================
# MAIN RUNNER
# =====================================================================
if __name__ == "__main__":
    start_time = time.time()
    print("Starting ZZZ Game Asset Local Downloader...")
    
    process_characters()
    process_weapons()
    process_drive_discs()
    process_monsters()
    
    duration = time.time() - start_time
    print(f"\nAll asset downloads and local mapping updates completed in {duration:.1f}s!")
