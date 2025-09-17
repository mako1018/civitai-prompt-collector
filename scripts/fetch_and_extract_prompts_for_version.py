import requests, json, urllib.parse, sys
from pathlib import Path

VERSION_ID = 1759168
HEADERS = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
OUT = Path("scripts/version_prompts_extracted.json")

def unwrap_trpc(j):
    if not isinstance(j, dict):
        return j
    if "result" in j:
        r = j["result"].get("data") or j["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return j

def walk_find_prompts(obj):
    results = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kl = k.lower()
            if isinstance(v, str) and ("prompt" in kl or "positive" in kl or "negative" in kl or "body" in kl):
                results.append({"key": k, "text": v, "ctx": {k: True}})
        for v in obj.values():
            results.extend(walk_find_prompts(v))
    elif isinstance(obj, list):
        for it in obj:
            results.extend(walk_find_prompts(it))
    return results

def fetch_trpc(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return unwrap_trpc(r.json())

def fetch_image_infinite(version_id):
    payload = {
        "json": {
            "modelVersionId": version_id,
            "prioritizedUserIds": [],
            "period": "AllTime",
            "sort": "Most Reactions",
            "limit": 100,
            "pending": False,
            "include": [],
            "withMeta": True,
            "excludedTagIds": [],
            "disablePoi": True,
            "disableMinor": True,
            "cursor": "undefined"
        }
    }
    q = urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
    url = f"https://civitai.com/api/trpc/image.getInfinite?input={q}"
    return fetch_trpc(url)

def fetch_post_by_id(post_id):
    payload = {"json": {"id": int(post_id)}}
    url = "https://civitai.com/api/trpc/post.getById?input=" + urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
    return fetch_trpc(url)

def extract():
    found = []
    try:
        img_payload = fetch_image_infinite(VERSION_ID)
    except Exception as e:
        print("image.getInfinite failed:", e)
        return []
    # collect images/posts
    images = []
    if isinstance(img_payload, dict):
        for k in ("items","rows","images","data","results"):
            if k in img_payload and isinstance(img_payload[k], list):
                images = img_payload[k]; break
        if not images and isinstance(img_payload.get("images") , list):
            images = img_payload.get("images")
    if not images and isinstance(img_payload, list):
        images = img_payload
    # gather postIds and inline prompts
    post_ids = set()
    for im in images or []:
        if isinstance(im, dict):
            if im.get("postId"):
                post_ids.add(im.get("postId"))
            # check inline prompt fields on image/meta
            found.extend(walk_find_prompts(im))
            # metadata might contain prompts
            if im.get("metadata"):
                found.extend(walk_find_prompts(im["metadata"]))
    # fetch posts
    for pid in sorted(x for x in post_ids if x):
        try:
            p = fetch_post_by_id(pid)
        except Exception as e:
            print("post.getById failed", pid, e)
            continue
        found.extend(walk_find_prompts(p))
    # dedupe by text
    uniq = {}
    for it in found:
        t = it.get("text","").strip()
        if t:
            uniq[t] = it
    out = [{"text": t, "key": uniq[t]["key"], "ctx": uniq[t].get("ctx",{})} for t in uniq]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out

if __name__ == "__main__":
    res = extract()
    print("found", len(res), "unique prompts. saved to", OUT)
    for i,r in enumerate(res[:50],1):
        print(f"---[{i}] key={r['key']}\n{r['text']}\n")