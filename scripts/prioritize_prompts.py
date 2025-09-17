import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
CAND = Path("scripts/playwright_prompt_candidates.json")
OUT = Path("scripts/prioritized_prompts.json")

def load_capture():
    entries = []
    if not CAP.exists():
        return entries
    for line in CAP.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except:
            continue
        e_text = (e.get("text_snip") or e.get("text") or "")
        entries.append({"url": e.get("url",""), "status": e.get("status"), "text": e_text})
    return entries

def load_candidates():
    if not CAND.exists():
        return []
    try:
        return json.loads(CAND.read_text(encoding="utf-8"))
    except:
        return []

def score_candidate(cand, capture_entries):
    txt = (cand.get("text") or "").strip()
    if not txt:
        return 0, []
    hits = []
    score = 0
    # if candidate.path matches a captured url, boost
    for e in capture_entries:
        if cand.get("url") and cand.get("url") == e["url"]:
            hits.append(("url_match", e["url"]))
            score += 50
        # direct substring match
        if txt[:80] and txt[:80] in (e["text"] or ""):
            hits.append(("snippet_match", e["url"]))
            score += 40
        # hasPositivePrompt flag nearby
        if '"hasPositivePrompt":true' in (e["text"] or "").lower():
            # if the capture entry also includes the candidate snippet, big boost
            if txt[:40] and txt[:40] in (e["text"] or ""):
                hits.append(("hasPositivePrompt+match", e["url"]))
                score += 200
            else:
                hits.append(("hasPositivePrompt", e["url"]))
                score += 30
        # explicit key hint in path/key
        key = (cand.get("key") or "") + " " + (cand.get("path") or "")
        if re.search(r'prompt|positive|positiveprompt', key, re.I):
            hits.append(("key_hint", key))
            score += 20
    # heuristic length / commas
    commas = txt.count(',')
    words = len(re.findall(r'\w+', txt))
    if words >= 40:
        score += 25
    elif words >= 20:
        score += 10
    if commas >= 4:
        score += 10
    return score, hits

def main():
    cap = load_capture()
    cand = load_candidates()
    scored = []
    for it in cand:
        sc, hits = score_candidate(it, cap)
        scored.append({"text": it.get("text"), "key": it.get("key"), "path": it.get("url") or it.get("path"), "score": sc, "hits": hits})
    scored = sorted(scored, key=lambda x: -x["score"])
    OUT.write_text(json.dumps(scored, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", len(scored), "items to", OUT)
    for i,r in enumerate(scored[:20],1):
        print(f"---[{i}] score={r['score']} key={r.get('key')} path={r.get('path')}\n{r['text'][:400]}\n hits={r['hits']}\n")

if __name__ == "__main__":
    main()