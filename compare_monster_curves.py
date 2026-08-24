import os
import json

cache_monster_dir = ".cache/zh/monster"
if os.path.exists(cache_monster_dir):
    files = [f for f in os.listdir(cache_monster_dir) if f.endswith(".json")]
    
    curves_by_stat = {}
    
    for f_name in files[:5]: # Compare the first 5 monsters
        path = os.path.join(cache_monster_dir, f_name)
        with open(path, "r", encoding="utf-8") as f:
            detail = json.load(f)
        variants = detail.get("monster_info", {})
        if not variants:
            continue
        p_var = list(variants.values())[0]
        curves = p_var.get("curves", {})
        
        for stat, curve_info in curves.items():
            curve_list = curve_info.get("curve", [])
            if stat not in curves_by_stat:
                curves_by_stat[stat] = []
            curves_by_stat[stat].append((f_name, curve_list))
            
    print("Comparing curves across files:")
    for stat, list_of_curves in curves_by_stat.items():
        first_name, first_curve = list_of_curves[0]
        identical = True
        for name, curve in list_of_curves[1:]:
            if curve != first_curve:
                identical = False
                print(f"  Stat '{stat}': DIFFERENT between {first_name} and {name}!")
                break
        if identical:
            print(f"  Stat '{stat}': IDENTICAL across all tested files!")
            print(f"    Curve values: {first_curve[:15]} ... (length {len(first_curve)})")
else:
    print("Cache monster dir does not exist.")
