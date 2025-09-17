import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
IDS_FILE = Path("scripts/hasPositive_image_ids.json")
OUT = Path("scripts/hasPositive_id_contexts.jsonl")

WINDOW = 2000  # 前後の文字数

def main():
    if not CAP.exists():
        print("missing capture file:", CAP); return
    if not IDS_FILE.exists():
        print("missing ids file:", IDS_FILE); return
    data = json.loads(IDS_FILE.read_text(encoding="utf-8"))
    ids = set(str(i) for i in data.get("ids", []))
    uuids = set(data.get("uuids", []))
    targets = list(ids) + list(uuids)
    if not targets:
        print("no targets in ids file"); return

    out = []
    for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
        try:
            entry = json.loads(line)
        except:
            entry = {"raw": line}
        txt = entry.get("text_snip") or entry.get("text") or entry.get("raw","")
        if not txt:
            continue
        # quick filter
        if not any(t in txt for t in targets):
            continue
        for t in targets:
            for m in re.finditer(re.escape(t), txt):
                s = max(0, m.start() - WINDOW)
                e = min(len(txt), m.end() + WINDOW)
                snippet = txt[s:e]
                out.append({
                    "capture_index": idx,
                    "capture_url": entry.get("url"),
                    "status": entry.get("status"),
                    "target": t,
                    "pos": m.start(),
                    "snippet_head": snippet[:200],
                    "snippet": snippet
                })
    if not out:
        print("no occurrences found in captures")
        return
    OUT.write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in out), encoding="utf-8")
    print("wrote", len(out), "contexts to", OUT)
    print("examples:")
    for o in out[:5]:
        print(f" idx={o['capture_index']} target={o['target']} src={o.get('capture_url')}")
        print(" snippet head:", o['snippet_head'][:200].replace('\\n',' '))
        print("---")
if __name__ == '__main__':
    main()