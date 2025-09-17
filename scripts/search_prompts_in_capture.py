import json
from pathlib import Path
p = Path("scripts/version_capture.jsonl")
if not p.exists():
    print("missing:", p)
    raise SystemExit(1)
post_ids = set()
found = []
for line in p.read_text(encoding="utf-8").splitlines():
    try:
        e = json.loads(line)
    except:
        continue
    txt = e.get("text_snip","")
    try:
        j = json.loads(txt)
    except:
        # try unwrap tRPC envelope
        try:
            j0 = json.loads(txt)
            if isinstance(j0, dict) and "result" in j0:
                d = j0["result"].get("data") or j0["result"]
                if isinstance(d, dict) and "json" in d:
                    j = d["json"]
                else:
                    j = d
            else:
                j = None
        except:
            j = None
    if not j:
        continue
    # collect postIds anywhere in structure
    def walk(o):
        if isinstance(o, dict):
            for k,v in o.items():
                if k.lower() == "postid" or k=="postId":
                    post_ids.add(str(v))
                if "prompt" in k.lower() and isinstance(v, str) and v.strip():
                    found.append((k,v))
                walk(v)
        elif isinstance(o, list):
            for it in o:
                walk(it)
    walk(j)
print("unique postIds:", sorted(x for x in post_ids if x and x!="None")[:200])
print("found prompt-like keys (sample):", found[:10])