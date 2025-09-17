import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
OUT = Path("scripts/playwright_prompt_candidates.json")
KEY_HINT = ("prompt", "positive", "negative", "body", "caption", "post", "text", "fullPrompt")

def strip_html(s):
    return re.sub(r'<[^>]+>', '', s).strip()

def is_prompt_like(s, key_hint=False):
    s2 = s.strip()
    if len(s2) < 60:
        return False
    words = len(re.findall(r'\w+', s2))
    commas = s2.count(',')
    # heuristic: either explicit key hint OR many commas OR long word count
    if key_hint:
        return True
    if commas >= 3:
        return True
    if words >= 20 and commas >= 1:
        return True
    if words >= 30:
        return True
    return False

def walk_json(obj, path="", results=None, url_hint=""):
    if results is None:
        results = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kp = f"{path}/{k}" if path else k
            if isinstance(v, str):
                txt = strip_html(v)
                key_hint = any(h.lower() in k.lower() for h in KEY_HINT)
                if txt and is_prompt_like(txt, key_hint):
                    results.append({"text": txt, "path": kp, "url": url_hint, "key": k, "reason": "key_hint" if key_hint else "heuristic"})
            else:
                walk_json(v, kp, results, url_hint)
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            walk_json(v, f"{path}[{i}]", results, url_hint)
    return results

def extract_from_snip(txt, url="", status=None):
    found = []
    if not txt:
        return found
    # try parse JSON
    try:
        j = json.loads(txt)
        # unwrap trpc envelope if present
        if isinstance(j, dict) and "result" in j:
            r = j["result"].get("data") or j["result"]
            if isinstance(r, dict) and "json" in r:
                j = r["json"]
        found.extend(walk_json(j, "", [], url))
    except Exception:
        # look for JSON-like fragments inside text
        for m in re.finditer(r'(\{(?:.|\n){60,4000}\})', txt):
            fragment = m.group(1)
            try:
                jf = json.loads(fragment)
                found.extend(walk_json(jf, "", [], url))
            except Exception:
                pass
        # fallback: extract long HTML text segments (comments/content)
        for m in re.finditer(r'(<p>.*?</p>|<div[^>]*>.*?</div>|<pre>.*?</pre>)', txt, re.S|re.I):
            t = strip_html(m.group(1))
            if is_prompt_like(t):
                found.append({"text": t, "path": "html_snippet", "url": url, "key": None, "reason": "html"})
        # last fallback: long plain substrings separated by quotes
        for m in re.finditer(r'["\'](.{60,4000}?)["\']', txt, re.S):
            t = strip_html(m.group(1))
            if is_prompt_like(t):
                found.append({"text": t, "path": "quoted", "url": url, "key": None, "reason": "quoted"})
    return found

def main():
    if not CAP.exists():
        print("missing capture:", CAP); return
    all_found = []
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        txt = e.get("text_snip") or e.get("text") or ""
        url = e.get("url") or ""
        status = e.get("status")
        all_found.extend(extract_from_snip(txt, url=url, status=status))
    # dedupe by normalized text
    uniq = {}
    for it in all_found:
        t = it["text"].strip()
        if t:
            uniq[t] = it
    out = list(uniq.values())
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("found", len(out), "candidates; saved to", OUT)
    for i,r in enumerate(out[:20], 1):
        print(f"---[{i}] reason={r.get('reason')} path={r.get('path')} url={r.get('url')}\n{r['text'][:600]}\n")

if __name__ == "__main__":
    main()