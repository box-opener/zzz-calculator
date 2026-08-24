import urllib.request
import urllib.error

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

urls_to_test = [
    # 1. Test Drive Disc sets path
    "https://static.nanoka.cc/assets/zzz/UI/Sprite/A1DynamicLoad/IconSuit/UnPacker/SuitWoodpeckerElectro.png",
    "https://static.nanoka.cc/assets/zzz/UI/Sprite/A1DynamicLoad/IconSuit/UnPacker/SuitWoodpeckerElectro.webp",
    "https://zzz.nanoka.cc/UI/Sprite/A1DynamicLoad/IconSuit/UnPacker/SuitWoodpeckerElectro.png",
    
    # 2. Test Character Avatar (Anby: IconRole01)
    "https://static.nanoka.cc/assets/zzz/IconRole01.png",
    "https://static.nanoka.cc/assets/zzz/IconRole01.webp",
    "https://zzz.nanoka.cc/assets/zzz/IconRole01.png",
    "https://zzz.nanoka.cc/assets/zzz/IconRole01.webp",
    "https://static.nanoka.cc/assets/zzz/IconRoleCircle/UnPacker/IconRoleCircle01.png",
    "https://static.nanoka.cc/assets/zzz/IconRoleCircle/UnPacker/IconRoleCircle01.webp",
    
    # 3. Test Weapon (Pleniluna: Weapon_B_Common_01)
    "https://static.nanoka.cc/assets/zzz/Weapon_B_Common_01.png",
    "https://static.nanoka.cc/assets/zzz/Weapon_B_Common_01.webp",
]

for url in urls_to_test:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"SUCCESS: {url} -> {resp.status}, length: {len(resp.read())} bytes")
    except urllib.error.HTTPError as e:
        print(f"FAILED : {url} -> {e.code}")
    except Exception as e:
        print(f"FAILED : {url} -> {type(e).__name__}: {e}")
