import urllib.request
import json
import os
import time

# Configurations
BASE_URL = "https://static.nanoka.cc/zzz/3.0.3+15825894/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
CACHE_DIR = ".cache"
DICT_DIR = "dict"
ARCHIVE_DIR = "archive"

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "zh", "character"), exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "zh", "monster"), exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "zh", "weapon"), exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "zh", "boss"), exist_ok=True)
os.makedirs(DICT_DIR, exist_ok=True)

def fetch_json(path):
    """
    Fetch a JSON file from the local cache if available,
    otherwise download it from the static database and cache it.
    """
    local_path = os.path.join(CACHE_DIR, path)
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    # Try reading from archive first if it was pre-downloaded there
    archive_path = os.path.join(ARCHIVE_DIR, path.replace("/", "_"))
    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Save to cache
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
            return data
            
    # Download from static database
    url = BASE_URL + path
    print(f"Downloading {url}...")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        # Write to cache
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "w", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
        # Sleep slightly to be polite to the host
        time.sleep(0.05)
        return data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def load_manifest(filename):
    """Load main manifest file from the archive folder."""
    path = os.path.join(ARCHIVE_DIR, f"full_{filename}")
    if not os.path.exists(path):
        # Fallback to downloading it
        data = fetch_json(filename)
        return data
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Element and Specialty Mappings
SPECIALTY_MAPPING = {
    1: "强攻", # Attack
    2: "击破", # Stun
    3: "异常", # Anomaly
    4: "支援", # Support
    5: "防护"  # Defense
}

ELEMENT_MAPPING = {
    200: "物理",
    201: "火属性",
    202: "冰属性",
    203: "电属性",
    204: "风属性",
    205: "以太"
}

def save_db(filename, var_name, data):
    # Save as JSON
    json_path = os.path.join(DICT_DIR, filename)
    with open(json_path, "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2)
    
    # Save as JS
    js_path = json_path.replace(".json", ".js")
    with open(js_path, "w", encoding="utf-8") as out:
        out.write(f"window.{var_name} = ")
        json.dump(data, out, ensure_ascii=False, indent=2)
        out.write(";\n")

# -------------------------------------------------------------
# 1. CHARACTER DICTIONARY GENERATION
# -------------------------------------------------------------
def build_characters():
    print("Building Characters Dictionary...")
    chars_manifest = load_manifest("character.json")
    characters_db = {}
    
    for cid, cinfo in chars_manifest.items():
        detail = fetch_json(f"zh/character/{cid}.json")
        if not detail:
            continue
            
        # 1. Base metadata
        name = detail.get("name", "")
        code_name = detail.get("code_name", "")
        rarity = "S" if detail.get("rarity", 3) >= 4 else "A"
        
        weapon_type_val = detail.get("weapon_type", {})
        if isinstance(weapon_type_val, dict) and weapon_type_val:
            specialty = list(weapon_type_val.values())[0]
        else:
            specialty = SPECIALTY_MAPPING.get(weapon_type_val, str(weapon_type_val))
        
        element_type_val = detail.get("element_type", {})
        if isinstance(element_type_val, dict) and element_type_val:
            element = list(element_type_val.values())[0]
        else:
            element = ELEMENT_MAPPING.get(element_type_val, str(element_type_val))
        
        # 2. Base stats calculations (Level 60, Rank 6)
        stats = detail.get("stats", {})
        level_6 = detail.get("level", {}).get("6", {})
        extra_6 = detail.get("extra_level", {}).get("6", {}).get("extra", {})
        
        def get_extra_val(prop_code):
            return extra_6.get(str(prop_code), {}).get("value", 0)
            
        d = 59 # Level 60 - 1
        
        # Compute scaled attributes
        hp = stats.get("hp_max", 0) + d * (stats.get("hp_growth", 0) / 10000.0) + level_6.get("hp_max", 0) + get_extra_val(11101)
        atk = stats.get("attack", 0) + d * (stats.get("attack_growth", 0) / 10000.0) + level_6.get("attack", 0) + get_extra_val(12101)
        defence = stats.get("defence", 0) + d * (stats.get("defence_growth", 0) / 10000.0) + level_6.get("defence", 0)
        impact = stats.get("break_stun", 0) + get_extra_val(12201)
        
        # Crit/PEN Rate represented in percentage values (e.g. 5.0 meaning 5.0%)
        crit_rate = (stats.get("crit", 0) + get_extra_val(20101)) / 100.0
        crit_dmg = (stats.get("crit_damage", 0) + get_extra_val(21101)) / 100.0
        pen_rate = stats.get("pen_rate", 0) / 100.0 + d * (stats.get("pen_delta", 0) / 10000.0) + get_extra_val(23101) / 100.0
        
        anomaly_proficiency = stats.get("element_mystery", 0) + get_extra_val(31201)
        anomaly_mastery = stats.get("element_abnormal_power", 0) + get_extra_val(31401)
        
        sp_recovery = (stats.get("sp_recover", 0) + get_extra_val(30501)) / 100.0
        rp_recovery = stats.get("rp_recover", 0) / 100.0
        
        computed_stats = {
            "hp": round(hp, 2),
            "atk": round(atk, 2),
            "def": round(defence, 2),
            "impact": round(impact, 2),
            "crit_rate": round(crit_rate, 2),
            "crit_dmg": round(crit_dmg, 2),
            "pen_rate": round(pen_rate, 2),
            "anomaly_proficiency": round(anomaly_proficiency, 2),
            "anomaly_mastery": round(anomaly_mastery, 2),
            "sp_recovery": round(sp_recovery, 2),
            "rp_recovery": round(rp_recovery, 2)
        }
        
        # 3. Skill calculations (Levels 12, 14, 16)
        skills_db = {}
        skill_dict = detail.get("skill", {})
        
        for category in ["basic", "dodge", "special", "chain", "assist"]:
            cat_skills = []
            descriptions = skill_dict.get(category, {}).get("description", [])
            
            # Map sub-skill name to description text
            desc_map = {}
            for item in descriptions:
                if "desc" in item and "name" in item:
                    desc_map[item["name"]] = item["desc"]
                    
            for item in descriptions:
                # We only process skill sub-items that contain parameter values
                if "param" not in item:
                    continue
                
                sub_skill_name = item.get("name", "")
                sub_skill_desc = desc_map.get(sub_skill_name, "")
                sub_skill_params = []
                
                for p in item.get("param", []):
                    p_name = p.get("name", "")
                    p_dict = p.get("param", {})
                    # Usually maps to one skill ID key
                    for sid, sid_data in p_dict.items():
                        main_val = sid_data.get("main", 0)
                        growth_val = sid_data.get("growth", 0)
                        
                        # Compute for Levels 12, 14, 16
                        lv12 = (main_val + 11 * growth_val) / 100.0
                        lv14 = (main_val + 13 * growth_val) / 100.0
                        lv16 = (main_val + 15 * growth_val) / 100.0
                        
                        sub_skill_params.append({
                            "param_name": p_name,
                            "format": sid_data.get("format", "%"),
                            "values": {
                                "lv12": round(lv12, 2),
                                "lv14": round(lv14, 2),
                                "lv16": round(lv16, 2)
                            }
                        })
                
                cat_skills.append({
                    "sub_skill_name": sub_skill_name,
                    "sub_skill_desc": sub_skill_desc,
                    "parameters": sub_skill_params
                })
                
            skills_db[category] = cat_skills
            
        # 4. Core Passive and Extra Ability Calculations
        passive_dict = detail.get("passive", {}).get("level", {})
        passive_levels = {}
        
        sorted_passive_keys = sorted(passive_dict.keys(), key=lambda k: passive_dict[k].get("level", 0))
        for pkey in sorted_passive_keys:
            p_data = passive_dict[pkey]
            lv = p_data.get("level", 0)
            p_names = p_data.get("name", [])
            p_descs = p_data.get("desc", [])
            
            core_name = p_names[0] if len(p_names) > 0 else "核心被动"
            core_desc = p_descs[0] if len(p_descs) > 0 else ""
            
            extra_name = p_names[1] if len(p_names) > 1 else "额外能力"
            extra_desc = p_descs[1] if len(p_descs) > 1 else ""
            
            passive_levels[f"level_{lv}"] = {
                "core_passive": {
                    "name": core_name,
                    "desc": core_desc
                },
                "extra_ability": {
                    "name": extra_name,
                    "desc": extra_desc
                }
            }
            
        # 5. Mindscape Cinemas 1, 2, 4, 6
        talent = detail.get("talent", {})
        mindscapes = {}
        for idx in ["1", "2", "4", "6"]:
            t_data = talent.get(idx, {})
            mindscapes[f"cinema_{idx}"] = {
                "name": t_data.get("name", f"影画 {idx}"),
                "desc": t_data.get("desc", "")
            }
            
        icon_name = cinfo.get("icon")
        icon_path = f"asset/character/{icon_name}.webp" if icon_name else "asset/character/Unknown.webp"
        
        characters_db[cid] = {
            "id": cid,
            "name": name,
            "code_name": code_name,
            "rarity": rarity,
            "specialty": specialty,
            "element": element,
            "stats": computed_stats,
            "skills": skills_db,
            "passive": passive_levels,
            "mindscapes": mindscapes,
            "icon_path": icon_path
        }
        
    # Save Character Dictionary
    save_db("zzz_characters.json", "ZZZ_CHARACTERS", characters_db)
    print(f"Characters database successfully written. Count: {len(characters_db)}")
    return characters_db

# -------------------------------------------------------------
# 2. MONSTER DICTIONARY GENERATION
# -------------------------------------------------------------
def build_monsters():
    print("Building Monsters Dictionary...")
    monster_manifest = load_manifest("monster.json")
    monsters_db = {}
    
    for mid, minfo in monster_manifest.items():
        detail = fetch_json(f"zh/monster/{mid}.json")
        if not detail:
            continue
            
        primary_variant_id = str(detail.get("monster_id", ""))
        variants = detail.get("monster_info", {})
        
        # Get primary variant
        p_variant = variants.get(primary_variant_id)
        if not p_variant and variants:
            p_variant = list(variants.values())[0]
            
        if not p_variant:
            continue
            
        name = p_variant.get("name", detail.get("name", ""))
        code_name = p_variant.get("code_name", "")
        rarity = p_variant.get("rarity", detail.get("rarity", 1))
        
        # Level 70 Scaling Calculations (index 69 of curves)
        stats = p_variant.get("stats", {})
        curves = p_variant.get("curves", {})
        
        def scale_stat(stat_name, base_val):
            curve_list = curves.get(stat_name, {}).get("curve", [])
            if len(curve_list) > 69:
                multiplier = curve_list[69] / 100.0
                return base_val * multiplier
            return base_val
            
        hp = scale_stat("hp", stats.get("hp", 0))
        atk = scale_stat("attack", stats.get("attack", 0))
        defence = scale_stat("defence", stats.get("defence", 0))
        stun = scale_stat("stun", stats.get("stun", 0))
        
        # Resistances (divided by 100.0 to represent as percentage floats, e.g. -20.0 for -20%)
        def parse_resistance(val):
            return round(val / 100.0, 2)
            
        resistances = {
            "damage_res": {
                "physical": parse_resistance(stats.get("physical_damage_res", 0)),
                "fire": parse_resistance(stats.get("fire_damage_res", 0)),
                "ice": parse_resistance(stats.get("ice_damage_res", 0)),
                "electric": parse_resistance(stats.get("electric_damage_res", 0)),
                "wind": parse_resistance(stats.get("wind_damage_res", 0)),
                "ether": parse_resistance(stats.get("ether_damage_res", 0))
            },
            "anomaly_res": {
                "physical": parse_resistance(stats.get("physical_buildup_res", 0)),
                "fire": parse_resistance(stats.get("fire_buildup_res", 0)),
                "ice": parse_resistance(stats.get("ice_buildup_res", 0)),
                "electric": parse_resistance(stats.get("electric_buildup_res", 0)),
                "wind": parse_resistance(stats.get("wind_buildup_res", 0)),
                "ether": parse_resistance(stats.get("ether_buildup_res", 0))
            },
            "daze_res": {
                "physical": parse_resistance(stats.get("physical_stun_res", 0)),
                "fire": parse_resistance(stats.get("fire_stun_res", 0)),
                "ice": parse_resistance(stats.get("ice_stun_res", 0)),
                "electric": parse_resistance(stats.get("electric_stun_res", 0)),
                "wind": parse_resistance(stats.get("wind_stun_res", 0)),
                "ether": parse_resistance(stats.get("ether_stun_res", 0))
            }
        }
        
        # Extra stun damage multiplier
        stun_extra_mult = stats.get("stun_damage_taken_ratio", 5000) / 100.0
        
        raw_icon = minfo.get("icon", "")
        if raw_icon:
            icon_base = os.path.splitext(os.path.basename(raw_icon))[0]
            icon_path = f"asset/monster/{icon_base}.webp"
        else:
            icon_path = "asset/monster/Unknown.webp"
            
        monsters_db[mid] = {
            "id": mid,
            "name": name,
            "code_name": code_name,
            "rarity": rarity,
            "stats_lv70": {
                "hp": round(hp, 2),
                "atk": round(atk, 2),
                "def": round(defence, 2),
                "stun": round(stun, 2)
            },
            "resistances": resistances,
            "stun_extra_damage_taken_pct": stun_extra_mult,
            "icon_path": icon_path
        }
        
    # Save Monsters Dictionary
    save_db("zzz_monsters.json", "ZZZ_MONSTERS", monsters_db)
    print(f"Monsters database successfully written. Count: {len(monsters_db)}")
    return monsters_db

# -------------------------------------------------------------
# 3. DRIVE DISC DICTIONARY GENERATION
# -------------------------------------------------------------
def build_drive_discs():
    print("Building Drive Discs Dictionary...")
    equip_manifest = load_manifest("equipment.json")
    drive_discs_db = {}
    
    # 1. Drive disc sets from equipment manifest
    for eid, einfo in equip_manifest.items():
        zh_data = einfo.get("zh", {})
        name = zh_data.get("name", "")
        desc2 = zh_data.get("desc2", "")
        desc4 = zh_data.get("desc4", "")
        icon = einfo.get("icon", "")
        
        if icon:
            icon_base = os.path.splitext(os.path.basename(icon))[0]
            icon_path = f"asset/drive_disc/{icon_base}.webp"
        else:
            icon_path = "asset/drive_disc/Unknown.webp"
            
        drive_discs_db[eid] = {
            "id": eid,
            "name": name,
            "desc2": desc2,
            "desc4": desc4,
            "icon_path": icon_path
        }
        
    # 2. Hardcoded partition slot main stats (+15 max)
    slot_main_stats = {
        "partition_1": {
            "main_stat": "生命值 (固定值)",
            "value": 2200
        },
        "partition_2": {
            "main_stat": "攻击力 (固定值)",
            "value": 316
        },
        "partition_3": {
            "main_stat": "防御力 (固定值)",
            "value": 184
        },
        "partition_4": {
            "options": {
                "生命值百分比": "30.0%",
                "攻击力百分比": "30.0%",
                "防御力百分比": "48.0%",
                "暴击率": "24.0%",
                "暴击伤害": "48.0%",
                "异常精通": "92"
            }
        },
        "partition_5": {
            "options": {
                "生命值百分比": "30.0%",
                "攻击力百分比": "30.0%",
                "防御力百分比": "48.0%",
                "穿透率": "24.0%",
                "属性伤害加成": "30.0%"
            }
        },
        "partition_6": {
            "options": {
                "生命值百分比": "30.0%",
                "攻击力百分比": "30.0%",
                "防御力百分比": "48.0%",
                "冲击力": "18.0%",
                "能量自动回复": "60.0%",
                "异常掌控": "30.0%"
            }
        }
    }
    
    final_output = {
        "sets": drive_discs_db,
        "max_level_main_stats": slot_main_stats
    }
    
    # Save Drive Discs Dictionary
    save_db("zzz_drive_discs.json", "ZZZ_DRIVE_DISCS", final_output)
    print(f"Drive Discs database successfully written. Sets count: {len(drive_discs_db)}")
    return final_output

# -------------------------------------------------------------
# 4. WEAPON DICTIONARY GENERATION
# -------------------------------------------------------------
def build_weapons():
    print("Building Weapons Dictionary...")
    weapon_manifest = load_manifest("weapon.json")
    weapons_db = {}
    
    for wid, winfo in weapon_manifest.items():
        detail = fetch_json(f"zh/weapon/{wid}.json")
        if not detail:
            continue
            
        name = detail.get("name", "")
        rarity_val = detail.get("rarity", 2)
        rarity = "S" if rarity_val >= 4 else ("A" if rarity_val == 3 else "B")
        
        weapon_type_val = detail.get("weapon_type", {})
        if isinstance(weapon_type_val, dict) and weapon_type_val:
            specialty = list(weapon_type_val.values())[0]
        else:
            specialty = SPECIALTY_MAPPING.get(weapon_type_val, str(weapon_type_val))
        
        # Level 60 Breakthrough 5 stars stats scaling
        level_60 = detail.get("level", {}).get("60", {})
        stars_5 = detail.get("stars", {}).get("5", {})
        
        level_rate = level_60.get("rate", 0)
        level_rate2 = level_60.get("rate2", 0)
        
        star_rate = stars_5.get("star_rate", 0)
        star_rand_rate = stars_5.get("rand_rate", 0)
        
        base_prop = detail.get("base_property", {})
        rand_prop = detail.get("rand_property", {})
        
        base_val = base_prop.get("value", 0)
        rand_val = rand_prop.get("value", 0)
        
        computed_atk = base_val * (10000 + level_rate + star_rate) / 10000.0
        computed_sec = rand_val * (10000 + level_rate2 + star_rand_rate) / 10000.0
        
        format_str = rand_prop.get("format", "")
        sec_name = rand_prop.get("name", "")
        sec_name2 = rand_prop.get("name2", "")
        
        # Calibrate weapon secondary stats based on Drive Disc main stats and rarity rules (User Request 9)
        WEAPON_SEC_STAT_BASES = {
            "暴击率": 24.0,
            "暴击伤害": 48.0,
            "穿透率": 24.0,
            "攻击力": 30.0,
            "生命值": 30.0,
            "防御力": 48.0,
            "异常精通": 92.0,
            "异常掌控": 30.0,
            "能量自动回复": 60.0,
            "冲击力": 18.0
        }
        
        sec_name_to_match = sec_name or sec_name2 or ""
        calibrated_val = None
        for key_name, base_s in WEAPON_SEC_STAT_BASES.items():
            if key_name in sec_name_to_match:
                if rarity == "S":
                    calibrated_val = base_s
                elif rarity == "A":
                    calibrated_val = base_s * 5.0 / 6.0
                else: # B
                    calibrated_val = base_s * 4.0 / 6.0
                break
                
        if calibrated_val is not None:
            sec_val_formatted = calibrated_val
        else:
            # Decide formatting representation for secondary stat value
            if "%" in format_str or "0.0%" in format_str or "百分比" in sec_name2:
                sec_val_formatted = computed_sec / 100.0 # Percentage float (e.g. 25.6 for 25.6%)
            else:
                sec_val_formatted = computed_sec
            
        computed_stats = {
            "base_atk": round(computed_atk, 2),
            "secondary_stat": {
                "name": sec_name,
                "name2": sec_name2,
                "value": round(sec_val_formatted, 2),
                "format": format_str
            }
        }
        
        # Refinements (talents 1 to 5)
        talents = detail.get("talents", {})
        refinements = {}
        for r_idx in ["1", "2", "3", "4", "5"]:
            t_data = talents.get(r_idx, {})
            refinements[f"refinement_{r_idx}"] = {
                "name": t_data.get("name", ""),
                "desc": t_data.get("desc", "")
            }
            
        icon_name = winfo.get("icon")
        icon_path = f"asset/weapon/{icon_name}.webp" if icon_name else "asset/weapon/Unknown.webp"
        
        weapons_db[wid] = {
            "id": wid,
            "name": name,
            "rarity": rarity,
            "specialty": specialty,
            "stats_lv60_star5": computed_stats,
            "refinements": refinements,
            "icon_path": icon_path
        }
        
    # Save Weapons Dictionary
    save_db("zzz_weapons.json", "ZZZ_WEAPONS", weapons_db)
    print(f"Weapons database successfully written. Count: {len(weapons_db)}")
    return weapons_db

# -------------------------------------------------------------
# 5. CRISIS BUFFS DICTIONARY GENERATION
# -------------------------------------------------------------
def build_crisis_buffs():
    print("Building Crisis Buffs Dictionary...")
    # Load boss manifest
    boss_manifest = load_manifest("boss.json")
    boss_db = {}
    
    for bid, binfo in boss_manifest.items():
        # Fetch detailed boss page payload
        detail = fetch_json(f"zh/boss/{bid}.json")
        if not detail:
            continue
            
        name = detail.get("name", binfo.get("zh", ""))
        zone_dict = detail.get("zone", {})
        
        # Buffs dictionary mapping stage -> buffs
        stages_buffs = {}
        for zid, zinfo in zone_dict.items():
            stage_name = zinfo.get("name", "")
            selectable = zinfo.get("selectable_buff", {})
            
            buff_list = []
            for buff_id, buff_info in selectable.items():
                buff_list.append({
                    "id": buff_id,
                    "title": buff_info.get("title", ""),
                    "desc": buff_info.get("desc", "").replace("\n", " ")
                })
                
            stages_buffs[zid] = {
                "stage_name": stage_name,
                "selectable_buffs": buff_list
            }
            
        boss_db[bid] = {
            "id": bid,
            "name": name,
            "stages": stages_buffs
        }
        
    # Save Crisis Buffs Dictionary
    save_db("zzz_crisis_buffs.json", "ZZZ_CRISIS_BUFFS", boss_db)
    print(f"Crisis Buffs database successfully written. Count: {len(boss_db)}")
    return boss_db

# -------------------------------------------------------------
# CORE SELF-VERIFICATION RUN
# -------------------------------------------------------------
def verify_databases(characters_db, monsters_db, drive_discs_db, weapons_db, boss_db):
    print("\n" + "="*50)
    print("RUNNING AUTOMATED SELF-VERIFICATION CHECKS...")
    print("="*50)
    
    # 1. Verify Anby stats (ID 1011)
    print("1. Checking character stats (Anby, ID 1011)...")
    assert "1011" in characters_db, "Anby (1011) must exist in characters dictionary!"
    anby = characters_db["1011"]
    anby_stats = anby["stats"]
    print(f"   computed HP: {anby_stats['hp']}, expected: ~7501")
    print(f"   computed ATK: {anby_stats['atk']}, expected: ~659")
    print(f"   computed DEF: {anby_stats['def']}, expected: ~613")
    print(f"   computed Impact: {anby_stats['impact']}, expected: 136")
    
    assert abs(anby_stats["hp"] - 7501) < 2.0, "Anby HP scaling mismatch!"
    assert abs(anby_stats["atk"] - 659) < 2.0, "Anby ATK scaling mismatch!"
    assert abs(anby_stats["def"] - 613) < 2.0, "Anby DEF scaling mismatch!"
    assert abs(anby_stats["impact"] - 136) < 1.0, "Anby Impact scaling mismatch!"
    print("   [PASS] Anby base stats are exactly correct!")
    
    # 2. Check Anby Level 12 skill multipliers & descriptions & passives
    print("2. Checking character skills and passives (Anby)...")
    basic_skills = anby["skills"].get("basic", [])
    found_first_hit = False
    for sub in basic_skills:
        if sub["sub_skill_name"] == "普通攻击：伏特速攻":
            # Check description is not empty
            sub_desc = sub.get("sub_skill_desc", "")
            print(f"   Ordinary attack description length: {len(sub_desc)} chars")
            assert len(sub_desc) > 0, "Ordinary attack description is missing!"
            assert "斩击" in sub_desc or "伏特速攻" in sub_desc, "Ordinary attack description content mismatch!"
            
            for param in sub["parameters"]:
                if param["param_name"] == "一段伤害倍率":
                    lv12_val = param["values"]["lv12"]
                    print(f"   computed ordinary attack Lv12 first hit: {lv12_val}%, expected: 63.1%")
                    assert abs(lv12_val - 63.1) < 0.2, "Ordinary attack Lv12 multiplier mismatch!"
                    found_first_hit = True
                    break
    assert found_first_hit, "Ordinary first hit parameter not found in Anby skill dict!"
    
    # Check core passive and extra ability are populated
    assert "passive" in anby, "Anby passive levels dict must exist!"
    p_lv1 = anby["passive"].get("level_1", {})
    assert "core_passive" in p_lv1 and "extra_ability" in p_lv1, "Passive level 1 must have core_passive and extra_ability!"
    print(f"   computed Core Passive Level 1 Name: {p_lv1['core_passive']['name']}")
    print(f"   computed Extra Ability Level 1 Name: {p_lv1['extra_ability']['name']}")
    assert p_lv1["core_passive"]["name"] == "核心被动：波动电压", "Core passive name mismatch!"
    assert p_lv1["extra_ability"]["name"] == "额外能力：并联电路", "Extra ability name mismatch!"
    assert len(p_lv1["core_passive"]["desc"]) > 0, "Core passive desc is empty!"
    assert len(p_lv1["extra_ability"]["desc"]) > 0, "Extra ability desc is empty!"
    print("   [PASS] Anby skill multipliers, descriptions, and passive levels are exactly correct!")
    
    # 3. Check W-Engine Pleniluna (ID 12001)
    print("3. Checking W-Engine stats (Pleniluna, ID 12001)...")
    assert "12001" in weapons_db, "Pleniluna (12001) must exist in weapons dictionary!"
    pleniluna = weapons_db["12001"]
    pleni_stats = pleniluna["stats_lv60_star5"]
    print(f"   computed Base ATK: {pleni_stats['base_atk']}, expected: ~475")
    print(f"   computed ATK% secondary: {pleni_stats['secondary_stat']['value']}%, expected: 20.0%")
    
    assert abs(pleni_stats["base_atk"] - 475) < 2.0, "Pleniluna Base ATK scaling mismatch!"
    assert abs(pleni_stats["secondary_stat"]["value"] - 20.0) < 0.2, "Pleniluna secondary stat scaling mismatch!"
    print("   [PASS] Pleniluna W-Engine stats are exactly correct!")
    
    # 4. Check Crisis Buffs for Boss 690421
    print("4. Checking Crisis Buffs (Deadly Assault, ID 690421)...")
    assert "690421" in boss_db, "Deadly Assault (690421) must exist in crisis buffs dictionary!"
    boss = boss_db["690421"]
    stage_id = "6904201"
    assert stage_id in boss["stages"], f"Stage {stage_id} must exist under boss 690421!"
    buffs = boss["stages"][stage_id]["selectable_buffs"]
    print(f"   extracted buffs: {[b['title'] for b in buffs]}, expected: ['乘流', '威震', '异变']")
    titles = [b["title"] for b in buffs]
    assert "乘流" in titles and "威震" in titles and "异变" in titles, "Crisis buffs title mismatch!"
    print("   [PASS] Crisis Buffs are exactly correct!")
    
    print("\n" + "="*50)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("="*50 + "\n")

# Main execution pipeline
if __name__ == "__main__":
    print("Starting ZZZ Calculator Database Construction Pipeline...")
    
    # Build dictionaries
    chars_db = build_characters()
    monsters_db = build_monsters()
    drive_db = build_drive_discs()
    weapons_db = build_weapons()
    boss_db = build_crisis_buffs()
    
    # Run assertions
    verify_databases(chars_db, monsters_db, drive_db, weapons_db, boss_db)
    
    print("ZZZ Calculator Database successfully constructed and verified!")
