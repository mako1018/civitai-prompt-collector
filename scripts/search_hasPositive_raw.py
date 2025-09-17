import re, json
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")

if not CAP.exists():
    print("missing file:", CAP); raise SystemExit(1)

hits = []
for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
    try:
        e = json.loads(line)
    except:
        continue
    txt = (e.get("text_snip") or e.get("text") or "")
    low = txt.lower()
    for m in re.finditer(r'"haspositiveprompt"\s*:\s*(true|false)', low):
        start = max(0, m.start() - 200)
        end = min(len(txt), m.end() + 200)
        snippet = txt[start:end].replace("\n", " ").replace("\r", " ")
        hits.append({
            "index": idx,
            "url": e.get("url"),
            "status": e.get("status"),
            "len": len(txt),
            "match": m.group(0),
            "snippet": snippet
        })

print("found", len(hits), "matches")
for i,h in enumerate(hits,1):
    print(f"---[{i}] idx={h['index']} status={h['status']} url={h['url']} len={h['len']} match={h['match']}")
    print(" snippet:", h['snippet'][:800])
    print()