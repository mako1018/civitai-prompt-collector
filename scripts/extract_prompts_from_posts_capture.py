import json, urllib.parse, requests
from pathlib import Path

CAP = Path("scripts/version_capture.jsonl")
OUT = Path("scripts/version_prompts_from_posts.json")
H = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
TIMEOUT = 20

def unwrap_trpc(j):
    if isinstance(j, dict) and "result" in j:
        r = j["result"].get("data") or j["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return j

def walk_find_prompts(obj):
    res = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kl = k.lower()
            if isinstance(v, str) and any(x in kl for x in ("prompt","positive","negative","body","text")):
                res.append({"key":k, "text":v})
        for v in obj.values():
            res.extend(walk_find_prompts(v))
    elif isinstance(obj, list):
        for it in obj:
            res.extend(walk_find_prompts(it))
    return res

def load_post_ids_from_capture():
    post_ids = set()
    if not CAP.exists():
        print("missing capture:", CAP)
        return post_ids
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        url = e.get("url","").lower()
        if "image.getimagesaspostsinfinite" in url or "image.getimagesaspostsinfinite" in url or "image.getinfinite" in url:
            txt = e.get("text_snip","")
            try:
                j = json.loads(txt)
            except:
                # try unwrap if trpc envelope present
                try:
                    j0 = json.loads(txt)
                    j = unwrap_trpc(j0)
                except:
                    j = None
            if not j:
                continue
            # j expected to contain items
            data = unwrap_trpc(j)
            items = None
            if isinstance(data, dict):
                for k in ("items","rows","data","results"):
                    if k in data and isinstance(data[k], list):
                        items = data[k]; break
            if isinstance(data, list):
                items = data
            if not items:
                continue
            for it in items:
                if isinstance(it, dict):
                    pid = it.get("postId") or (it.get("images") and isinstance(it.get("images"), list) and it.get("images")[0].get("postId"))
                    if pid:
                        post_ids.add(int(pid))
    return post_ids

def fetch_post(post_id):
    payload = {"json":{"id":int(post_id)}}
    url = "https://civitai.com/api/trpc/post.getById?input=" + urllib.parse.quote(json.dumps(payload, separators=(",",":")))
    r = requests.get(url, headers=H, timeout=TIMEOUT)
    r.raise_for_status()
    return unwrap_trpc(r.json())

def main():
    post_ids = sorted(load_post_ids_from_capture())
    if not post_ids:
        print("no post ids found in capture")
        return
    results = []
    for pid in post_ids:
        try:
            p = fetch_post(pid)
        except Exception as e:
            print("post.getById failed", pid, e)
            continue
        prompts = walk_find_prompts(p)
        if prompts:
            for pr in prompts:
                results.append({"postId": pid, "key": pr["key"], "text": pr["text"], "raw_post": p})
    # dedupe by text
    uniq = {}
    for it in results:
        t = it["text"].strip()
        if t:
            uniq[t] = it
    out = list(uniq.values())
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "unique prompts; saved to", OUT)
    for i,r in enumerate(out[:20],1):
        print(f"---[{i}] postId={r['postId']} key={r['key']}\n{r['text'][:400]}\n")

if __name__ == "__main__":
    main()