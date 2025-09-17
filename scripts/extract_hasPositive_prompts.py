import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
OUT = Path("scripts/hasPositive_prompts.json")
KEYS = ("positivePrompt","positive_prompt","positivePromptText","fullPrompt","full_prompt","prompt","postBody","body","caption","text")

def unwrap_trpc(j):
    if isinstance(j, dict) and "result" in j:
        r = j["result"].get("data") or j["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return j

def find_prompts(obj, path=""):
    found = []
    if isinstance(obj, dict):
        # if this dict signals hasPositivePrompt, inspect it deeply
        if obj.get("hasPositivePrompt") is True:
            # search within this dict for keys
            for k,v in obj.items():
                if isinstance(v, str) and any(k.lower()==kk.lower() for kk in KEYS):
                    found.append({"key": k, "text": v, "ctx_path": path})
            # also search nested
            for k,v in obj.items():
                found.extend(find_prompts(v, path + "/" + str(k)))
            return found
        # otherwise continue walking
        for k,v in obj.items():
            found.extend(find_prompts(v, path + "/" + str(k)))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            found.extend(find_prompts(v, f"{path}[{i}]"))
    return found

def extract_long_texts(obj, path=""):
    # heuristic: long strings that look like prompts inside objects that have hasPositivePrompt nearby
    found = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, str) and len(v) > 60 and (v.count(",")>=3 or len(re.findall(r'\w+', v))>25):
                found.append({"key": k, "text": v, "ctx_path": path})
            found.extend(extract_long_texts(v, path + "/" + str(k)))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            found.extend(extract_long_texts(v, f"{path}[{i}]"))
    return found

def main():
    if not CAP.exists():
        print("missing capture:", CAP); return
    prompts = []
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt:
            continue
        # try parse JSON or find JSON fragments
        tried = False
        try:
            j = json.loads(txt)
            j = unwrap_trpc(j)
            tried = True
            p = find_prompts(j, path=e.get("url",""))
            for it in p:
                it.update({"source_url": e.get("url"), "status": e.get("status")})
            prompts.extend(p)
            # if no explicit prompts but this capture contains hasPositivePrompt true anywhere, extract long texts in same block
            if '"hasPositivePrompt":true' in txt.lower() and not p:
                longp = extract_long_texts(j, path=e.get("url",""))
                for it in longp:
                    it.update({"source_url": e.get("url"), "status": e.get("status"), "heuristic": True})
                prompts.extend(longp)
        except Exception:
            # try JSON fragments inside text
            for m in re.finditer(r'(\{(?:.|\n){60,4000}\})', txt):
                try:
                    jf = json.loads(m.group(1))
                    jf = unwrap_trpc(jf)
                    p = find_prompts(jf, path=e.get("url",""))
                    for it in p:
                        it.update({"source_url": e.get("url"), "status": e.get("status")})
                    prompts.extend(p)
                    if '"hasPositivePrompt":true' in m.group(1).lower() and not p:
                        longp = extract_long_texts(jf, path=e.get("url",""))
                        for it in longp:
                            it.update({"source_url": e.get("url"), "status": e.get("status"), "heuristic": True})
                        prompts.extend(longp)
                except:
                    continue
    # dedupe by normalized text
    uniq = {}
    for it in prompts:
        t = (it.get("text") or "").strip()
        if not t: continue
        norm = re.sub(r'\s+', ' ', t)
        if norm not in uniq:
            uniq[norm] = it
    out = list(uniq.values())
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "entries; saved to", OUT)
    for i,r in enumerate(out[:10],1):
        h = "(heuristic)" if r.get("heuristic") else ""
        print(f"---[{i}] {h} src={r.get('source_url')} key={r.get('key')}\n{r.get('text')[:400]}\n")

if __name__ == "__main__":
    main()