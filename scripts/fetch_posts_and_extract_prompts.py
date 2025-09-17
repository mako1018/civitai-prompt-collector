import requests, json, urllib.parse, time
from pathlib import Path

OUT = Path("scripts/fetched_prompts.json")
H = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
VERSION_ID = 1759168
MODEL_ID = 133005
TIMEOUT = 20

def unwrap_trpc(j):
    if isinstance(j, dict) and "result" in j:
        r = j["result"].get("data") or j["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return j

def walk_prompts(obj):
    res = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, str) and any(s in k.lower() for s in ("prompt","positive","negative","body","text","full")):
                res.append({"key":k, "text":v})
        for v in obj.values():
            res.extend(walk_prompts(v))
    elif isinstance(obj, list):
        for it in obj:
            res.extend(walk_prompts(it))
    return res

def call_trpc(endpoint, payload):
    q = urllib.parse.quote(json.dumps({"json": payload}, separators=(",", ":")))
    url = f"https://civitai.com/api/trpc/{endpoint}?input={q}"
    r = requests.get(url, headers=H, timeout=TIMEOUT)
    r.raise_for_status()
    return unwrap_trpc(r.json())

def fetch_images_as_posts(cursor="undefined"):
    payload = {
        "period":"AllTime","periodMode":"published","sort":"Newest","withMeta":True,
        "modelVersionId": VERSION_ID,"modelId": MODEL_ID,"hidden":False,"limit":50,"browsingLevel":1,"cursor": cursor
    }
    return call_trpc("image.getImagesAsPostsInfinite", payload)

def fetch_post(post_id):
    payload = {"id": int(post_id)}
    return call_trpc("post.getById", payload)

def main():
    prompts = {}
    try:
        data = fetch_images_as_posts("undefined")
    except Exception as e:
        print("image.getImagesAsPostsInfinite failed:", e)
        return
    # items may be in data["items"]
    items = []
    if isinstance(data, dict):
        items = data.get("items") or data.get("rows") or []
    if not items and isinstance(data, list):
        items = data
    post_ids = set()
    for it in items:
        if isinstance(it, dict):
            pid = it.get("postId")
            if pid:
                post_ids.add(int(pid))
            # try inline prompts on item
            for p in walk_prompts(it):
                prompts.setdefault(p["text"].strip(), []).append({"source":"image_item","key":p["key"]})
    # fetch each post
    for pid in sorted(post_ids):
        try:
            p = fetch_post(pid)
        except Exception as e:
            print("post.getById failed", pid, e)
            continue
        for pr in walk_prompts(p):
            txt = pr["text"].strip()
            if txt:
                prompts.setdefault(txt, []).append({"source":"post.getById","postId":pid,"key":pr["key"]})
        time.sleep(0.1)
    out = [{"prompt":k, "hits":v} for k,v in prompts.items()]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "unique prompts; saved to", OUT)
    for i,r in enumerate(out[:10],1):
        print(f"---[{i}] ({len(r['hits'])} hits)\n{r['prompt'][:400]}\n")

if __name__ == "__main__":
    main()