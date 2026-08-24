import urllib.request
import urllib.error

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

urls_to_test = [
    # Drive disc set icon flat path tests
    "https://static.nanoka.cc/assets/zzz/SuitWoodpeckerElectro.webp",
    "https://static.nanoka.cc/assets/zzz/SuitWoodpeckerElectro.png",
    
    # Monster icon flat path tests
    "https://static.nanoka.cc/assets/zzz/Monster_ClaymoreGrey.webp",
    "https://static.nanoka.cc/assets/zzz/Monster_ClaymoreGrey.png",
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
