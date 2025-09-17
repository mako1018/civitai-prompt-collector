import requests, json, urllib.parse, sys
VERSION_ID = 1759168
MODEL_ID = 133005
H = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}

def call(endpoint, payload):
    q = urllib.parse.quote(json.dumps({"json": payload}, separators=(",", ":")))
    url = f"https://civitai.com/api/trpc/{endpoint}?input={q}"
    try:
        r = requests.get(url, headers=H, timeout=20)
    except Exception as e:
        print(f"[{endpoint}] request failed:", e)
        return
    print(f"[{endpoint}] status:", r.status_code, "content-type:", r.headers.get("content-type"))
    txt = r.text
    print("len_text:", len(txt))
    try:
        j = r.json()
        if isinstance(j, dict):
            print("top keys:", list(j.keys())[:20])
        s = json.dumps(j, ensure_ascii=False)[:4000]
        print(s)
    except Exception as e:
        print("json parse error:", e)
        print("raw start:", txt[:4000])
    print("-"*80)

tests = []

# image.getInfinite variants
tests.append(("image.getInfinite", {
    "modelVersionId": VERSION_ID, "prioritizedUserIds": [], "period":"AllTime",
    "sort":"Most Reactions","limit":20,"pending":False,"include":[],"withMeta":True,
    "excludedTagIds":[],"disablePoi":True,"disableMinor":True,"cursor":"undefined"
}))
tests.append(("image.getInfinite", {
    "modelVersionId": VERSION_ID, "prioritizedUserIds": [], "period":"AllTime",
    "sort":"Most Reactions","limit":20,"pending":True,"include":[],"withMeta":False,
    "excludedTagIds":[],"disablePoi":True,"disableMinor":False,"cursor":"undefined"
}))
tests.append(("image.getInfinite", {
    "modelVersionId": VERSION_ID, "prioritizedUserIds":[764940], "period":"AllTime",
    "sort":"Most Reactions","limit":20,"pending":False,"include":[],"withMeta":True,
    "excludedTagIds":[],"disablePoi":True,"disableMinor":True,"cursor":"undefined"
}))

# image.getImagesAsPostsInfinite (returns images as posts)
tests.append(("image.getImagesAsPostsInfinite", {
    "period":"AllTime","periodMode":"published","sort":"Newest","withMeta":True,
    "modelVersionId": VERSION_ID,"modelId": MODEL_ID,"hidden":False,"limit":50,"browsingLevel":1,"cursor":"undefined"
}))
tests.append(("image.getImagesAsPostsInfinite", {
    "period":"AllTime","periodMode":"published","sort":"Newest","withMeta":False,
    "modelVersionId": VERSION_ID,"modelId": MODEL_ID,"hidden":False,"limit":20,"browsingLevel":1,"cursor":"undefined"
}))

# modelVersion.getById (sanity)
tests.append(("modelVersion.getById", {"id": VERSION_ID}))
tests.append(("model.getById", {"id": MODEL_ID}))

for ep, payload in tests:
    call(ep, payload)