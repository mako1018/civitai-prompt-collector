import json, re, html
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
OUT = Path("scripts/hasPositive_quoted_long_strings.json")

def clean(s):
    s = html.unescape(s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

if not CAP.exists():
    print("missing file:", CAP); raise SystemExit(1)

found = {}
for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
    try:
        e = json.loads(line)
    except:
        continue
    txt = (e.get("text_snip") or e.get("text") or "")
    if not txt: continue
    if "haspositiveprompt" not in txt.lower():
        continue
    # find long quoted strings
    for m in re.finditer(r'"((?:\\.|[^"\\]){80,8000})"', txt):
        raw = m.group(1)
        # decode escape sequences conservatively
        try:
            dec = raw.encode('utf-8').decode('unicode_escape', 'ignore')
        except:
            dec = raw
        c = clean(dec)
        # filter out likely hashes/arrays by word/comma heuristics
        if c.count(",") < 2 and len(re.findall(r'\w+', c)) < 10:
            continue
        key = re.sub(r'\s+', ' ', c)[:1000]
        if key not in found:
            found[key] = {"source_url": e.get("url"), "status": e.get("status"), "text": c}
# also try to capture long unquoted fragments that look like prompt lists (e.g., colon+[digits,...])
for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
    try:
        e = json.loads(line)
    except:
        continue
    txt = (e.get("text_snip") or e.get("text") or "")
    if not txt: continue
    if "haspositiveprompt" not in txt.lower():
        continue
    for m in re.finditer(r':\s*\[([0-9,\s]{40,4000})\]', txt):
        arr = m.group(1)
        c = clean(arr)
        if len(re.findall(r'\d+', c)) < 5:
            continue
        key = "ARRAY:" + c[:1000]
        if key not in found:
            found[key] = {"source_url": e.get("url"), "status": e.get("status"), "text": c, "heuristic": True}

out = list(found.values())
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("found", len(out), "unique quoted/unquoted long strings; saved to", OUT)
for i, v in enumerate(out[:10], 1):
    h = "(heuristic)" if v.get("heuristic") else ""
    print(f"---[{i}] {h} src={v['source_url']} status={v['status']}\n{v['text'][:800]}\n")