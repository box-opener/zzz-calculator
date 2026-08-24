import os
import json

cache_monster_dir = ".cache/zh/monster"
if os.path.exists(cache_monster_dir):
    files = [f for f in os.listdir(cache_monster_dir) if f.endswith(".json")]
    if files:
        sample_path = os.path.join(cache_monster_dir, files[0])
        print(f"Loading cached details from: {sample_path}")
        with open(sample_path, "r", encoding="utf-8") as f:
            detail = json.load(f)
        
        variants = detail.get("monster_info", {})
        if variants:
            p_var = list(variants.values())[0]
            print(f"Monster Name: {p_var.get('name')}, Code: {p_var.get('code_name')}")
            curves = p_var.get("curves", {})
            for stat, curve_info in curves.items():
                curve_list = curve_info.get("curve", [])
                print(f"  {stat} curve length: {len(curve_list)}")
                # Print every 10th level up to 100
                samples = [f"Lv{i+1}: {curve_list[i]}" for i in range(0, min(100, len(curve_list)), 10)]
                print(f"    Sample values: {', '.join(samples)}")
        else:
            print("No variants found in detail.")
    else:
        print("No files found in cache monster dir.")
else:
    print("Cache monster dir does not exist.")
