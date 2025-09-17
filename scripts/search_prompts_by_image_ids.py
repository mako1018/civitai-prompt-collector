import json, re, html
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
OUT_IDS = Path("scripts/hasPositive_image_ids.json")
OUT_PROMPTS = Path("scripts/hasPositive_prompts_from_id_search.json")
KEYS = ("prompt","positivePrompt","positive_prompt","positivePromptText","fullPrompt","full_prompt","postBody","body","caption","text","positivePrompts","positive_prompt_text")

def clean(s):
    if not s: return ""
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_json_fragments(txt):
    frags = []
    try:
        frags.append(json.loads(txt))
    except Exception:
        pass
    for m in re.finditer(r'(\{(?:.|\n){60,40000}\})', txt):
        f = m.group(1)
        try:
            frags.append(json.loads(f))
        except Exception:
            try:
                cleaned = re.sub(r',\s*}', '}', f)
                cleaned = re.sub(r',\s*\]', ']', cleaned)
                frags.append(json.loads(cleaned))
            except Exception:
                continue
    return frags

def walk_find_prompts(obj, path=""):
    out = []
    if isinstance(obj, dict):
        if obj.get("hasPositivePrompt") is True:
            for k,v in obj.items():
                if isinstance(v, str) and any(k.lower()==kk.lower() for kk in KEYS):
                    out.append({"path": path or "/", "key": k, "text": clean(v)})
            # deep search inside flagged object
            for k,v in obj.items():
                out.extend(walk_find_prompts(v, path + "/" + str(k)))
            return out
        for k,v in obj.items():
            out.extend(walk_find_prompts(v, path + "/" + str(k)))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            out.extend(walk_find_prompts(v, f"{path}[{i}]"))
    return out

def collect_ids():
    ids = set()
    uuids = set()
    if not CAP.exists():
        print("missing capture file"); return ids, uuids
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt: continue
        # try structured JSON fragments first (existing logic)
        for jf in extract_json_fragments(txt):
            def walk(o):
                if isinstance(o, dict):
                    if o.get("hasPositivePrompt") is True:
                        if isinstance(o.get("id"), int):
                            ids.add(o.get("id"))
                        if isinstance(o.get("url"), str) and re.match(r'^[0-9a-f\-]{20,}$', o.get("url")):
                            uuids.add(o.get("url"))
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(jf)
        # Fallback: regex search for hasPositivePrompt true and nearby id/url in raw text
        for m in re.finditer(r'hasPositivePrompt"\s*:\s*(true|false)', txt, flags=re.IGNORECASE):
            if m.group(1).lower() != "true":
                continue
            s = max(0, m.start()-500)
            e = min(len(txt), m.end()+500)
            window = txt[s:e]
            # numeric id
            for mm in re.finditer(r'"id"\s*:\s*([0-9]{4,})', window):
                try:
                    ids.add(int(mm.group(1)))
                except:
                    pass
            # uuid-like url
            for mm in re.finditer(r'"url"\s*:\s*"([0-9a-fA-F\-]{20,})"', window):
                uuids.add(mm.group(1))
            # also try patterns like "imageId":12345 or "imageId":"uuid"
            for mm in re.finditer(r'"imageId"\s*:\s*([0-9]{4,})', window):
                try:
                    ids.add(int(mm.group(1)))
                except:
                    pass
            for mm in re.finditer(r'"imageId"\s*:\s*"([0-9a-fA-F\-]{20,})"', window):
                uuids.add(mm.group(1))
    return ids, uuids

def search_for_prompts(target_ids, target_uuids):
    found = {}
    for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt: continue
        # quick substring check
        if not any((str(i) in txt) for i in list(target_ids)[:200]) and not any(u in txt for u in list(target_uuids)[:200]):
            continue
        for jf in extract_json_fragments(txt):
            # unwrap and search
            for p in walk_find_prompts(jf, path=e.get("url","")):
                t = p.get("text","").strip()
                if not t: continue
                norm = re.sub(r'\s+', ' ', t)
                if norm not in found:
                    found[norm] = {"source_url": e.get("url"), "status": e.get("status"), **p}
        # regex fallback: find key/value pairs near targets in raw txt
        for m in re.finditer(r'(?i)"(prompt|positivePrompt|positive_prompt|fullPrompt|postBody|body|caption|text)"\s*:\s*"((?:\\.|[^"\\]){20,10000})"', txt):
            key = m.group(1)
            rawv = m.group(2)
            try:
                val = rawv.encode('utf-8').decode('unicode_escape', 'ignore')
            except:
                val = rawv
            valc = clean(val)
            if not valc: continue
            # ensure this fragment is near a target id/uuid
            span = max(0, m.start()-200), min(len(txt), m.end()+200)
            context = txt[span[0]:span[1]]
            if any(str(i) in context for i in list(target_ids)[:200]) or any(u in context for u in list(target_uuids)[:200]):
                norm = re.sub(r'\s+', ' ', valc)
                if norm not in found:
                    found[norm] = {"source_url": e.get("url"), "status": e.get("status"), "path": e.get("url"), "key": key, "text": valc, "heuristic": True}
    return list(found.values())

def main():
    ids, uuids = collect_ids()
    OUT_IDS.write_text(json.dumps({"ids": sorted(ids), "uuids": sorted(list(uuids))}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("collected", len(ids), "numeric ids and", len(uuids), "uuids; saved to", OUT_IDS)
    if not ids and not uuids:
        print("no targets found; aborting search"); return
    prompts = search_for_prompts(ids, uuids)
    OUT_PROMPTS.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("extracted", len(prompts), "unique prompt-like entries; saved to", OUT_PROMPTS)
    for i,p in enumerate(prompts[:10],1):
        h = "(heuristic)" if p.get("heuristic") else ""
        print(f"---[{i}] {h} src={p.get('source_url')} key={p.get('key')} path={p.get('path')}\n{p.get('text')[:400]}\n")

if __name__ == "__main__":
    main()