import json, re, html
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
QUOTED = Path("scripts/hasPositive_quoted_long_strings.json")
OUT = Path("scripts/hasPositive_resolved_prompts.json")
KEYS = ("prompt","positivePrompt","positive_prompt","positivePromptText","fullPrompt","full_prompt","postBody","body","caption","text","positivePrompts","positive_prompt_text")

def clean(s):
    if not s: return ""
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def load_targets():
    if not QUOTED.exists():
        print("missing file:", QUOTED); return set()
    arr = json.loads(QUOTED.read_text(encoding="utf-8"))
    ids = set()
    for e in arr:
        t = e.get("text","")
        # if explicit array like "1,2,3,..."
        m = re.findall(r'\d{1,9}', t)
        for mm in m:
            try:
                ids.add(int(mm))
            except:
                pass
    return ids

def find_objs_with_id(o, target_ids, path=""):
    hits = []
    if isinstance(o, dict):
        # direct id field
        for k,v in o.items():
            if isinstance(v, int) and v in target_ids:
                hits.append((o, path))
                break
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, int) and item in target_ids:
                        hits.append((o, path))
                        break
        # recurse
        for k,v in o.items():
            hits.extend(find_objs_with_id(v, target_ids, path + "/" + str(k)))
    elif isinstance(o, list):
        for i,v in enumerate(o):
            hits.extend(find_objs_with_id(v, target_ids, f"{path}[{i}]"))
    return hits

def walk_find_prompts(o, path=""):
    results = []
    if isinstance(o, dict):
        if o.get("hasPositivePrompt") is True:
            # search inside this dict for keys
            for k,v in o.items():
                if isinstance(v, str) and any(k.lower()==kk.lower() for kk in KEYS):
                    results.append({"path": path + "/" + k, "key": k, "text": clean(v)})
            # also deep-search inside
            for k,v in o.items():
                results.extend(walk_find_prompts(v, path + "/" + str(k)))
            return results
        # otherwise keep walking
        for k,v in o.items():
            results.extend(walk_find_prompts(v, path + "/" + str(k)))
    elif isinstance(o, list):
        for i,v in enumerate(o):
            results.extend(walk_find_prompts(v, f"{path}[{i}]"))
    return results

def main():
    if not CAP.exists():
        print("missing capture:", CAP); return
    target_ids = load_targets()
    if not target_ids:
        print("no numeric targets found in", QUOTED); return
    found_candidates = []
    seen_texts = {}
    for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt: continue
        # try parse JSON fragments to search structured objects
        try:
            j = json.loads(txt)
            # unwrap trpc-like
            if isinstance(j, dict) and "result" in j:
                j = j["result"].get("data") or j["result"]
                if isinstance(j, dict) and "json" in j:
                    j = j["json"]
        except Exception:
            # can't parse whole text; skip structured search for this line
            j = None
        if j is not None:
            hits = find_objs_with_id(j, target_ids, path=e.get("url",""))
            for obj, pth in hits:
                # from each matched object, search for hasPositivePrompt flagged subobjects
                prompts = walk_find_prompts(obj, path=pth)
                for p in prompts:
                    t = p.get("text","").strip()
                    if not t: continue
                    norm = re.sub(r'\s+', ' ', t)
                    if norm not in seen_texts:
                        seen_texts[norm] = {"source_url": e.get("url"), "status": e.get("status"), **p}
        # fallback: search raw text for prompt-like key/value pairs near target numeric lists
        # if the line contains any target id as substring, run a regex extraction
        if any(str(i) in txt for i in list(target_ids)[:50]):
            for m in re.finditer(r'(?i)"(prompt|positivePrompt|positive_prompt|fullPrompt|postBody|body|caption|text|positivePrompts|positivePromptText)"\s*:\s*"((?:\\.|[^"\\]){20,10000})"', txt):
                key = m.group(1)
                rawv = m.group(2)
                try:
                    val = rawv.encode('utf-8').decode('unicode_escape', 'ignore')
                except:
                    val = rawv
                t = clean(val)
                if not t: continue
                norm = re.sub(r'\s+', ' ', t)
                if norm not in seen_texts:
                    seen_texts[norm] = {"source_url": e.get("url"), "status": e.get("status"), "path": e.get("url"), "key": key, "text": t, "heuristic": True}
    out = list(seen_texts.values())
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("resolved", len(out), "unique prompt-like strings; saved to", OUT)
    for i,v in enumerate(out[:10],1):
        h = "(heuristic)" if v.get("heuristic") else ""
        print(f"---[{i}] {h} src={v.get('source_url')} key={v.get('key')} path={v.get('path')}\n{v.get('text')[:500]}\n")

if __name__ == "__main__":
    main()