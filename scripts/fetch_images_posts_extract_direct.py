import requests, json, urllib.parse, time
from pathlib import Path

OUT = Path("scripts/found_prompts.json")
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

def find_prompt_texts(obj):
    keys = ("positivePrompt","positive_prompt","positivePromptText","fullPrompt","full_prompt",
            "prompt","text","body","caption","postBody","positivePrompts")
    found = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, str) and any(k.lower()==kk.lower() for kk in keys):
                val = v.strip()
                if val:
                    found.append((k, val))
        for v in obj.values():
            found.extend(find_prompt_texts(v))
    elif isinstance(obj, list):
        for it in obj:
            found.extend(find_prompt_texts(it))
    return found

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

def main():
    cursor = "undefined"
    prompts = {}
    tries = 0
    while True:
        tries += 1
        try:
            data = fetch_images_as_posts(cursor)
        except Exception as e:
            print("fetch failed:", e)
            break
        # data expected to contain items and nextCursor
        items = data.get("items") or data.get("rows") or data.get("results") or []
        for it in items:
            # inspect item-level
            for k,txt in find_prompt_texts(it):
                prompts.setdefault(txt, []).append({"source":"image_item", "key":k, "hint": it.get("postId") or it.get("images") and it.get("images")[0].get("postId")})
            # inspect nested images
            imgs = it.get("images") or it.get("imagesAsPosts") or []
            for img in imgs:
                for k,txt in find_prompt_texts(img):
                    prompts.setdefault(txt, []).append({"source":"image_obj", "key":k, "hint": img.get("id")})
                # metadata / meta
                for k,txt in find_prompt_texts(img.get("metadata") or img.get("meta") or {}):
                    prompts.setdefault(txt, []).append({"source":"image_meta", "key":k, "hint": img.get("id")})
        next_cursor = data.get("nextCursor") or data.get("cursor")
        if not next_cursor or tries>6:
            break
        cursor = next_cursor
        time.sleep(0.2)
    out = [{"prompt":k, "hits":v} for k,v in prompts.items()]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "unique prompts; saved to", OUT)
    for i,r in enumerate(out[:10],1):
        print(f"---[{i}] ({len(r['hits'])} hits)\n{r['prompt'][:400]}\n")

if __name__ == "__main__":
    main()