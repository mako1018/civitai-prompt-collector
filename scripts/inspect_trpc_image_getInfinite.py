import requests, json, sys, urllib.parse

version_id = 1759168
payload = {
    "json": {
        "modelVersionId": version_id,
        "prioritizedUserIds": [],
        "period": "AllTime",
        "sort": "Most Reactions",
        "limit": 50,
        "pending": True,
        "include": [],
        "withMeta": False,
        "excludedTagIds": [],
        "disablePoi": True,
        "disableMinor": True,
        "cursor": None
    }
}
q = urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
URL = f"https://civitai.com/api/trpc/image.getInfinite?input={q}"
h = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
try:
    r = requests.get(URL, headers=h, timeout=20)
    print("status:", r.status_code)
    print("content-type:", r.headers.get("content-type"))
    txt = r.text
    print("len_text:", len(txt))
    with open("tmp_image_getInfinite.json","w",encoding="utf-8") as f:
        f.write(txt)
    try:
        j = r.json()
    except Exception as e:
        print("json parse error:", e)
        print("raw start:", txt[:4000])
        sys.exit(0)
    if isinstance(j, dict):
        print("top keys:", list(j.keys())[:50])
    print(json.dumps(j, ensure_ascii=False)[:8000])
except Exception as e:
    print("request failed:", e)