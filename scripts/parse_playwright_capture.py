import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
OUT = Path("scripts/version_prompts_playwright.json")
KEYWORDS = ("prompt","positivePrompt","fullPrompt","positive_prompt","full_prompt","positivePromptText","postBody","body","caption","text")

def unwrap_trpc(j):
    if isinstance(j, dict) and "result" in j:
        r = j["result"].get("data") or j["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return j

def walk_find_prompts(obj, ctx=None):
    ctx = ctx or {}
    res = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kl = k.lower()
            if isinstance(v, str) and any(kw.lower() in kl for kw in KEYWORDS):
                txt = v.strip()
                if txt:
                    res.append({"key": k, "text": txt, "ctx": ctx})
            res.extend(walk_find_prompts(v, {**ctx, k: True}))
    elif isinstance(obj, list):
        for it in obj:
            res.extend(walk_find_prompts(it, ctx))
    return res

def extract_from_text_snip(txt):
    results = []
    if not txt:
        return results
    # try parse JSON
    try:
        j = json.loads(txt)
        j = unwrap_trpc(j)
        results.extend(walk_find_prompts(j, {"source":"json"}))
    except Exception:
        # fallback: simple regex for long prompt-like strings
        for m in re.finditer(r'(?:"|\\\')?(positivePrompt|fullPrompt|prompt|postBody|body|caption|positive_prompt|full_prompt)["\']?\s*[:=]\s*["\'](.{30,4000}?)["\']', txt, re.I|re.S):
            results.append({"key": m.group(1), "text": m.group(2).strip(), "ctx":{"source":"regex"}})
    return results

def main():
    if not CAP.exists():
        print("missing capture:", CAP); return
    found = []
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        # attach some hints
        hint = {"url": e.get("url"), "status": e.get("status")}
        for r in extract_from_text_snip(txt):
            r["ctx"].update(hint)
            found.append(r)
    # dedupe by text
    uniq = {}
    for it in found:
        t = it["text"].strip()
        if t:
            uniq[t] = it
    out = [{"text": t, "key": uniq[t]["key"], "ctx": uniq[t]["ctx"]} for t in uniq]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "unique prompts; saved to", OUT)
    for i,r in enumerate(out[:10],1):
        print(f"---[{i}] key={r['key']} src={r['ctx'].get('url')}\n{r['text'][:400]}\n")

if __name__ == "__main__":
    main()