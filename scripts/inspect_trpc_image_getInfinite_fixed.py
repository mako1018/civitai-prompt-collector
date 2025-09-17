import requests, json, urllib.parse, sys

version_id = 1759168
headers = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}

templates = [
    {"cursor": "undefined", "pending": True},
    {"cursor": "undefined", "pending": False},
    {"cursor": "", "pending": True},
    {"cursor": None, "pending": True}
]

for t in templates:
    payload = {
        "json": {
            "modelVersionId": version_id,
            "prioritizedUserIds": [],
            "period": "AllTime",
            "sort": "Most Reactions",
            "limit": 50,
            "pending": t["pending"],
            "include": [],
            "withMeta": False,
            "excludedTagIds": [],
            "disablePoi": True,
            "disableMinor": True,
            "cursor": t["cursor"]
        }
    }
    q = urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
    url = f"https://civitai.com/api/trpc/image.getInfinite?input={q}"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print("=== TRY ===", t)
        print("status:", r.status_code, "content-type:", r.headers.get("content-type"))
        txt = r.text
        print("len_text:", len(txt))
        try:
            j = r.json()
            print("top keys:", list(j.keys())[:50] if isinstance(j, dict) else type(j))
            s = json.dumps(j, ensure_ascii=False)
            print(s[:4000])
        except Exception as e:
            print("json parse error:", e)
            print("raw start:", txt[:4000])
    except Exception as e:
        print("request failed:", e)
    print("-"*80)