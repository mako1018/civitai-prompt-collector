import json
from pathlib import Path
P = Path("scripts/version_capture.jsonl")
if not P.exists():
    print("missing", P); raise SystemExit(1)
cnt = 0
for line in P.read_text(encoding="utf-8").splitlines():
    try:
        e = json.loads(line)
    except:
        continue
    url = (e.get("url") or "").lower()
    if any(k in url for k in ("image.getimagesaspostsinfinite","image.getinfinite","image.getimagesasposts","post.getbyid")):
        cnt += 1
        print("=== ENTRY", cnt, "status=", e.get("status"), "url=", e.get("url"))
        # print full stored snip (may be large)
        txt = e.get("text_snip") or e.get("text") or ""
        print(txt)
        print("-"*120)
print("done; printed", cnt, "entries")