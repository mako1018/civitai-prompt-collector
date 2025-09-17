import json, re, html
from pathlib import Path

CAP_PLAY = Path("scripts/version_capture_playwright.jsonl")
CAND = Path("scripts/playwright_prompt_candidates.json")
OUT = Path("scripts/final_prompts.json")

KEYWORDS = ("prompt","positive","negative","fullprompt","positive_prompt","full_prompt","positivePromptText","postBody","body","caption","text")

def unwrap_trpc(obj):
    if isinstance(obj, dict) and "result" in obj:
        r = obj["result"].get("data") or obj["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return obj

def walk_find_prompts(obj, path=""):
    res = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kk = k.lower()
            if isinstance(v, str) and any(w in kk for w in KEYWORDS):
                res.append({"key": k, "text": v, "path": path + "/" + k})
            res.extend(walk_find_prompts(v, path + "/" + k))
    elif isinstance(obj, list):
        for i,it in enumerate(obj):
            res.extend(walk_find_prompts(it, f"{path}[{i}]"))
    return res

def clean_text(s):
    if not s: return ""
    s = html.unescape(s)
    # remove simple HTML tags
    s = re.sub(r'<[^>]+>', '', s)
    # remove excessive whitespace and leading/trailing quotes
    s = s.strip()
    s = re.sub(r'^[\'"\u201c\u201d]+', '', s)
    s = re.sub(r'[\'"\u201c\u201d]+$', '', s)
    s = re.sub(r'\s+', ' ', s)
    # remove backslash escapes like \n, \"
    s = s.replace(r'\n', ' ').replace(r'\"', '"').replace(r"\'", "'")
    s = s.strip()
    return s

def extract_from_capture():
    results = []
    if not CAP_PLAY.exists():
        return results
    for line in CAP_PLAY.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt:
            continue
        # try parse JSON and walk
        try:
            j = json.loads(txt)
            j = unwrap_trpc(j)
            results.extend(walk_find_prompts(j, path=e.get("url","")))
        except:
            # find JSON fragments
            for m in re.finditer(r'(\{(?:.|\n){60,4000}\})', txt):
                try:
                    jf = json.loads(m.group(1))
                    jf = unwrap_trpc(jf)
                    results.extend(walk_find_prompts(jf, path=e.get("url","")))
                except:
                    pass
    return results

def extract_from_candidates():
    results = []
    if not CAND.exists():
        return results
    try:
        cand = json.loads(CAND.read_text(encoding="utf-8"))
    except:
        return results
    for it in cand:
        txt = it.get("text") or ""
        key = it.get("key") or it.get("path") or "candidate"
        results.append({"key": key, "text": txt, "path": it.get("url","")})
    return results

def main():
    found = []
    found.extend(extract_from_capture())
    found.extend(extract_from_candidates())
    # clean & dedupe
    uniq = {}
    for it in found:
        t = clean_text(it.get("text",""))
        if not t or len(t) < 30: continue
        # normalize for dedupe
        norm = re.sub(r'\s+', ' ', t).strip()
        # prefer entries with explicit prompt-like keys
        score = 0
        if any(k.lower() in (it.get("key") or "").lower() for k in ("prompt","positive")):
            score += 10
        score += len(norm)
        if norm not in uniq or score > uniq[norm]["score"]:
            uniq[norm] = {"text": norm, "key": it.get("key"), "path": it.get("path"), "score": score}
    out = [{"text": v["text"], "key": v.get("key"), "path": v.get("path")} for v in sorted(uniq.values(), key=lambda x:-x["score"])]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "prompts; saved to", OUT)
    for i,r in enumerate(out[:20],1):
        print(f"---[{i}] key={r.get('key')} path={r.get('path')}\n{r['text'][:500]}\n")

if __name__ == "__main__":
    main()