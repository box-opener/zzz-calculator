import os
import json

cache_monster_dir = ".cache/zh/monster"
files = [f for f in os.listdir(cache_monster_dir) if f.endswith(".json")]
path = os.path.join(cache_monster_dir, files[0])
with open(path, "r", encoding="utf-8") as f:
    detail = json.load(f)
variants = detail.get("monster_info", {})
p_var = list(variants.values())[0]
curves = p_var.get("curves", {})

for stat in ["hp", "attack", "defence", "stun"]:
    curve_list = curves.get(stat, {}).get("curve", [])
    print(f"{stat.upper()}_CURVE = {curve_list}")
