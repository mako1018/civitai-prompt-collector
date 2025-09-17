import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")

def snippet_around(s, pat, width=120):
    i = s.lower().find(pat.lower())
    if i<0:
        return ""
    start = max(0, i-width//2)
    end = min(len(s), i+width//2)
    return s[start:end].replace("\n"," ").replace("\r"," ")

def check_has_positive(s):
    # look for explicit flags or keys
    if '"hasPositivePrompt":' in s:
        m = re.search(r'"hasPositivePrompt"\s*:\s*(true|false)', s, re.I)
        if m:
            return m.group(1)
    return ""

if not CAP.exists():
    print("missing file:", CAP); raise SystemExit(1)

for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
    try:
        e = json.loads(line)
    except Exception as ex:
        print(f"---[{idx}] parse error:", ex); continue
    url = e.get("url") or e.get("headers", {}).get("referer") or ""
    status = e.get("status")
    txt = (e.get("text_snip") or e.get("text") or "")
    L = len(txt)
    has_pos = check_has_positive(txt)
    p_snip = ""
    if re.search(r'prompt', txt, re.I):
        p_snip = snippet_around(txt, "prompt", width=300)
    print(f"---[{idx}] url={url} status={status} len={L} hasPositive={has_pos}")
    if p_snip:
        print(" prompt-snippet:", p_snip)
    # show first 600 chars if short
    if L<2000:
        print(" text_snip head:", txt[:600].replace('\n',' ') )
    print()
print("done; inspected", idx, "entries")