import json, re, html
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
OUT_RAW = Path("scripts/hasPositive_raw_matches.json")
OUT_EX = Path("scripts/hasPositive_extracted_prompts.json")
# 拡張キー一覧（ケース無視）
KEYS = ("prompt","positivePrompt","positive_prompt","positivePromptText","fullPrompt","full_prompt","postBody","body","caption","text","positivePrompts","positive_prompt_text","negativePrompt","negative_prompt")

def unwrap_trpc(obj):
    if isinstance(obj, dict) and "result" in obj:
        r = obj["result"].get("data") or obj["result"]
        if isinstance(r, dict) and "json" in r:
            return r["json"]
        return r
    return obj

def walk_find_keys(obj, path=""):
    results = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kp = f"{path}/{k}" if path else k
            if isinstance(v, str) and any(k.lower()==kk.lower() for kk in KEYS):
                results.append({"path": kp, "key": k, "text": v})
            results.extend(walk_find_keys(v, kp))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            results.extend(walk_find_keys(v, f"{path}[{i}]"))
    return results

def extract_json_fragments(txt):
    fragments = []
    # try whole text
    try:
        fragments.append(json.loads(txt))
    except Exception:
        pass
    # find JSON-like fragments and try parse
    for m in re.finditer(r'(\{(?:.|\n){60,40000}\})', txt):
        frag = m.group(1)
        try:
            fragments.append(json.loads(frag))
        except Exception:
            # try simple cleanup (remove trailing commas)
            try:
                cleaned = re.sub(r',\s*}', '}', frag)
                cleaned = re.sub(r',\s*\]', ']', cleaned)
                fragments.append(json.loads(cleaned))
            except Exception:
                continue
    return fragments

def clean_text(s):
    if not s: return ""
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', '', s)
    s = s.strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def regex_find_prompts(raw):
    out = []
    # JSON-style key/value pairs in raw text
    for m in re.finditer(r'(?i)"(prompt|positivePrompt|positive_prompt|fullPrompt|full_prompt|postBody|body|caption|text|positivePrompts|positivePromptText|negativePrompt|negative_prompt)"\s*:\s*"((?:\\.|[^"\\]){20,8000})"', raw):
        key = m.group(1)
        txt = m.group(2).encode('utf-8').decode('unicode_escape', 'ignore')
        out.append({"key": key, "text": txt})
    # loose heuristic: long quoted strings (likely prompts)
    for m in re.finditer(r'"((?:\\.|[^"\\]){80,8000})"', raw):
        s = m.group(1)
        # filter out hashes/urls by word count/comma count
        if s.count(",")>=2 or len(re.findall(r'\w+', s))>25:
            out.append({"key":"quoted_long", "text": s})
    return out

def extract_long_texts(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, str) and len(v) > 60 and (v.count(",")>=3 or len(re.findall(r'\w+', v))>25):
                found.append({"key": k, "text": v, "path": path + "/" + str(k)})
            found.extend(extract_long_texts(v, path + "/" + str(k)))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            found.extend(extract_long_texts(v, f"{path}[{i}]"))
    return found

def main():
    if not CAP.exists():
        print("missing capture:", CAP); return
    raw_matches = []
    extracted = []
    for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        if not txt: continue
        if "haspositiveprompt" in txt.lower():
            raw_matches.append({"index": idx, "url": e.get("url"), "status": e.get("status"), "len": len(txt), "text_head": txt[:4000]})
            frags = extract_json_fragments(txt)
            # try extracting from parsed fragments first
            for jf in frags:
                try:
                    jf_un = unwrap_trpc(jf)
                except:
                    jf_un = jf
                # find objects explicitly flagged
                def find_subobjs_with_flag(o, path=""):
                    hits = []
                    if isinstance(o, dict):
                        if o.get("hasPositivePrompt") is True:
                            hits.append((o, path))
                        for k,v in o.items():
                            hits.extend(find_subobjs_with_flag(v, path + "/" + str(k)))
                    elif isinstance(o, list):
                        for i,v in enumerate(o):
                            hits.extend(find_subobjs_with_flag(v, f"{path}[{i}]"))
                    return hits
                flagged = find_subobjs_with_flag(jf_un, "")
                if flagged:
                    for subobj, pth in flagged:
                        for found in walk_find_keys(subobj, path=pth):
                            t = clean_text(found["text"])
                            if t:
                                extracted.append({"source_url": e.get("url"), "status": e.get("status"), **found, "text_clean": t})
                        # also long-text heuristic inside flagged subobj
                        for lt in extract_long_texts(subobj, path=pth):
                            t = clean_text(lt["text"])
                            if t:
                                extracted.append({"source_url": e.get("url"), "status": e.get("status"), "path": lt.get("path"), "key": lt.get("key"), "text": lt.get("text"), "text_clean": t, "heuristic": True})
                else:
                    # fallback: scan all known keys
                    for found in walk_find_keys(jf_un, path=""):
                        t = clean_text(found["text"])
                        if t:
                            extracted.append({"source_url": e.get("url"), "status": e.get("status"), **found, "text_clean": t})
                    # regex-based extraction from raw fragment text
                    try:
                        raw_fragment = json.dumps(jf_un, ensure_ascii=False)
                    except:
                        raw_fragment = str(jf_un)
                    for rfound in regex_find_prompts(raw_fragment):
                        t = clean_text(rfound["text"])
                        if t:
                            extracted.append({"source_url": e.get("url"), "status": e.get("status"), "path": "", "key": rfound.get("key"), "text": rfound.get("text"), "text_clean": t, "heuristic": True})
                    # final fallback: long text anywhere
                    for lt in extract_long_texts(jf_un, path=""):
                        t = clean_text(lt["text"])
                        if t:
                            extracted.append({"source_url": e.get("url"), "status": e.get("status"), "path": lt.get("path"), "key": lt.get("key"), "text": lt.get("text"), "text_clean": t, "heuristic": True})
            # also run regex on the raw capture text (captures fragments that failed JSON parse)
            for rfound in regex_find_prompts(txt):
                t = clean_text(rfound["text"])
                if t:
                    extracted.append({"source_url": e.get("url"), "status": e.get("status"), "path": "", "key": rfound.get("key"), "text": rfound.get("text"), "text_clean": t, "heuristic": True})
    # dedupe by normalized text
    uniq = {}
    for it in extracted:
        k = it["text_clean"].strip()
        if not k: continue
        norm = re.sub(r'\s+', ' ', k)
        if norm not in uniq:
            uniq[norm] = it
    OUT_RAW.write_text(json.dumps(raw_matches, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_EX.write_text(json.dumps(list(uniq.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"found {len(raw_matches)} raw matches; extracted {len(uniq)} unique prompt-like strings")
    for i, v in enumerate(list(uniq.values())[:10], 1):
        h = "(heuristic)" if v.get("heuristic") else ""
        print(f"---[{i}] {h} src={v.get('source_url')} key={v.get('key')} path={v.get('path')}\n{v.get('text_clean')[:500]}\n")

if __name__ == "__main__":
    main()