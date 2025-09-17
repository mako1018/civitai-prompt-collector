import json
from pathlib import Path

IN = Path("scripts/version_capture.jsonl")
ALT = Path("tmp_image_getInfinite.json")  # 手元で取ってあれば補助
out = []

def find_prompts(obj, ctx=None):
    results = []
    if isinstance(obj, dict):
        # まずこのオブジェクト自体にプロンプト臭いフィールドがあるか確認
        for k, v in obj.items():
            if isinstance(k, str) and "prompt" in k.lower():
                if isinstance(v, str) and v.strip():
                    results.append({"key": k, "prompt": v, "ctx": ctx or {}})
        # 再帰
        for v in obj.values():
            results.extend(find_prompts(v, ctx=obj if isinstance(obj, dict) else ctx))
    elif isinstance(obj, list):
        for it in obj:
            results.extend(find_prompts(it, ctx=ctx))
    return results

if not IN.exists():
    print("error: scripts/version_capture.jsonl が見つかりません")
    raise SystemExit(1)

with IN.open("r", encoding="utf-8") as f:
    for line in f:
        try:
            entry = json.loads(line)
        except Exception:
            continue
        url = entry.get("url","")
        if "image.getinfinite" not in url.lower() and not any(x in url.lower() for x in ("model","version","post","prompt","trpc")):
            continue
        text = entry.get("text_snip","")
        parsed = None
        try:
            parsed = json.loads(text)
        except Exception:
            # 部分しかない可能性があるので tmp ファイルを代替で試す
            parsed = None
        if parsed is None and ALT.exists():
            try:
                parsed = json.loads(ALT.read_text(encoding="utf-8"))
            except Exception:
                parsed = None
        if parsed is None:
            continue
        # tRPC のラップを外す common pattern
        if isinstance(parsed, dict) and "result" in parsed:
            try:
                d = parsed["result"].get("data") or parsed["result"]
                if isinstance(d, dict) and "json" in d:
                    parsed = d["json"]
                else:
                    parsed = d
            except Exception:
                pass
        found = find_prompts(parsed)
        if found:
            for it in found:
                # try to attach id/context hints
                ctx = it.get("ctx") or {}
                hint_id = ctx.get("id") or ctx.get("postId") or ctx.get("imageId") or ctx.get("modelVersionId")
                out.append({"url": url, "hint_id": hint_id, "key": it["key"], "prompt": it["prompt"]})

# dedupe by prompt
seen = set()
final = []
for item in out:
    p = item["prompt"].strip()
    if p and p not in seen:
        seen.add(p)
        final.append(item)

print(f"found {len(final)} unique prompts")
for i, it in enumerate(final[:200],1):
    print(f"---[{i}] id={it.get('hint_id')} key={it.get('key')}\n{it['prompt']}\n")