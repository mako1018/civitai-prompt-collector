import requests, json, re
from pathlib import Path

CAP = Path("scripts/version_capture.jsonl")
OUT = Path("scripts/image_fetch_trials.json")
H = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
TIMEOUT = 15

def load_first_image():
    if not CAP.exists():
        print("missing capture file:", CAP); return None
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt:
            continue
        try:
            j = json.loads(txt)
        except:
            # try unwrap trpc envelope
            try:
                j0 = json.loads(txt)
                j = j0.get("result", {}).get("data", {}).get("json") or j0.get("result", {}).get("data") or j0.get("result")
            except:
                j = None
        if not j:
            continue
        # find image object
        def walk(o):
            if isinstance(o, dict):
                if "id" in o and ("hash" in o or "url" in o) and o.get("type") in (None, "image"):
                    return o
                for v in o.values():
                    r = walk(v)
                    if r: return r
            elif isinstance(o, list):
                for it in o:
                    r = walk(it)
                    if r: return r
            return None
        img = walk(j)
        if img:
            return img
    return None

def try_urls(img):
    tries = []
    # gather candidates
    img_id = img.get("id")
    img_url_token = img.get("url") or img.get("hash") or img.get("name")
    candidates = []
    if img_id:
        candidates += [
            f"https://civitai.com/api/images/{img_id}",
            f"https://civitai.com/api/images/by-id/{img_id}",
            f"https://civitai.com/images/{img_id}",
            f"https://civitai.com/api/image/{img_id}"
        ]
    if img_url_token:
        candidates += [
            f"https://civitai.com/api/images/{img_url_token}",
            f"https://civitai.com/api/images/by-url/{img_url_token}",
            f"https://civitai.com/images/{img_url_token}",
            f"https://civitai.com/api/file/{img_url_token}",
            f"https://civitai.com/api/file/{img_url_token}/metadata",
            f"https://images.civitai.com/{img_url_token}/metadata"
        ]
    # also try trpc GET for image.getById (may 404)
    if img_id:
        payload = {"json": {"id": img_id}}
        q = requests.utils.quote(json.dumps(payload, separators=(",", ":")))
        candidates.append(f"https://civitai.com/api/trpc/image.getById?input={q}")
        candidates.append(f"https://civitai.com/api/trpc/image.getById?input={requests.utils.quote(json.dumps({'json':{'id':int(img_id)}}))}")
    # unique
    seen = set()
    for url in candidates:
        if url in seen: continue
        seen.add(url)
        try:
            r = requests.get(url, headers=H, timeout=TIMEOUT)
            content = r.text[:4000]
            tries.append({"url": url, "status": r.status_code, "ct": r.headers.get("content-type"), "sample": content})
        except Exception as e:
            tries.append({"url": url, "error": str(e)})
    return tries

def main():
    img = load_first_image()
    if not img:
        print("no image found in capture"); return
    print("using image candidate:", json.dumps({"id": img.get("id"), "url": img.get("url"), "hash": img.get("hash"), "modelVersionId": img.get("modelVersionId")}, ensure_ascii=False))
    tries = try_urls(img)
    OUT.write_text(json.dumps({"image": img, "tries": tries}, ensure_ascii=False, indent=2), encoding="utf-8")
    for t in tries:
        if "error" in t:
            print("[ERR] ", t["url"], t["error"])
        else:
            print("[OK] ", t["url"], "status:", t["status"], "ct:", t["ct"])
            print(t["sample"][:1000])
            print("-"*80)
    print("saved trial results to", OUT)

if __name__ == "__main__":
    main()