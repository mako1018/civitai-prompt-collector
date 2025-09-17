import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
RAW_MATCHES = Path("scripts/hasPositive_raw_matches.json")

def try_parse_fragment(txt, max_expand=5):
    import json
    # try direct parse
    try:
        return json.loads(txt)
    except:
        pass
    # expand outward by balancing braces
    for _ in range(max_expand):
        # try to find a JSON object inside by locating first { and last }
        start = txt.find('{')
        end = txt.rfind('}')
        if start == -1 or end == -1 or end <= start:
            break
        frag = txt[start:end+1]
        try:
            return json.loads(frag)
        except:
            # remove outermost braces to try inner
            txt = frag[1:-1]
    return None

if not CAP.exists():
    print("missing capture:", CAP); raise SystemExit(1)
if not RAW_MATCHES.exists():
    print("missing raw matches:", RAW_MATCHES); raise SystemExit(1)

captures = CAP.read_text(encoding="utf-8").splitlines()
raw_matches = json.loads(RAW_MATCHES.read_text(encoding="utf-8"))

for m in raw_matches:
    idx = m.get("index")
    url = m.get("url")
    status = m.get("status")
    print("="*80)
    print(f"index={idx} url={url} status={status}")
    if not (1 <= idx <= len(captures)):
        print(" index out of range:", idx); continue
    line = captures[idx-1]
    try:
        entry = json.loads(line)
    except Exception as e:
        print(" failed to parse capture line as JSON:", e)
        entry = {"raw": line}
    txt = entry.get("text_snip") or entry.get("text") or entry.get("text_head") or entry.get("text") or entry.get("raw", "")
    L = len(txt)
    print("capture length:", L)
    print("\n--- head (first 2000 chars) ---\n")
    print(txt[:2000].replace("\n"," "))
    print("\n--- tail (last 1000 chars) ---\n")
    print(txt[-1000:].replace("\n"," "))
    print("\n--- hasPositivePrompt snippets ---\n")
    for mm in re.finditer(r'hasPositivePrompt"\s*:\s*(true|false)', txt, flags=re.IGNORECASE):
        s = max(0, mm.start()-300); e = min(len(txt), mm.end()+300)
        print(f"pos={mm.start()} match={mm.group(0)} snippet:\n{txt[s:e].replace('\\n',' ')}\n")
    print("\n--- array-like patterns :[digits,...] ---\n")
    for mm in re.finditer(r':\s*\[([0-9,\s]{40,4000})\]', txt):
        s = max(0, mm.start()-200); e = min(len(txt), mm.end()+200)
        arr = mm.group(1)
        print(f"pos={mm.start()} len={len(arr)} snippet:\n{txt[s:e].replace('\\n',' ')}\n")
        # try to extract surrounding JSON object
        # expand window around this match and attempt parse
        for pad in (200,500,1000,3000,8000):
            ss = max(0, mm.start()-pad)
            ee = min(len(txt), mm.end()+pad)
            frag = txt[ss:ee]
            parsed = try_parse_fragment(frag, max_expand=3)
            print(f" try pad={pad} chars window={ee-ss} parsed={bool(parsed)}")
            if parsed:
                # print any hasPositivePrompt in parsed
                def find_prompts(o, path=""):
                    out = []
                    if isinstance(o, dict):
                        if o.get("hasPositivePrompt") is True:
                            out.append((path,o))
                        for k,v in o.items():
                            out.extend(find_prompts(v, path + "/" + str(k)))
                    elif isinstance(o, list):
                        for i,v in enumerate(o):
                            out.extend(find_prompts(v, f"{path}[{i}]"))
                    return out
                hits = find_prompts(parsed)
                print("  hasPositivePrompt hits in parsed fragment:", len(hits))
                if hits:
                    for pth, obj in hits[:5]:
                        print("   path:", pth, "example keys:", list(obj.keys())[:10])
                break
    print("\n--- quoted long strings (first 10 matches) ---\n")
    for i,mm in enumerate(re.finditer(r'"((?:\\.|[^"\\]){80,8000})"', txt)):
        if i>=10: break
        s = max(0, mm.start()-200); e = min(len(txt), mm.end()+200)
        print(f"[{i}] pos={mm.start()} len={len(mm.group(1))} snippet:\n{txt[s:e].replace('\\n',' ')}\n")
    print("\n--- prompt-like key/value near hasPositivePrompt ---\n")
    for mm in re.finditer(r'(?i)"(prompt|positivePrompt|positive_prompt|fullPrompt|postBody|body|caption|text)"\s*:\s*"((?:\\.|[^"\\]){10,5000})"', txt):
        s = max(0, mm.start()-200); e = min(len(txt), mm.end()+200)
        val = mm.group(2).encode('utf-8').decode('unicode_escape','ignore')
        print(f"pos={mm.start()} key={mm.group(1)} len={len(val)} snippet:\n{txt[s:e].replace('\\n',' ')}\n")
    print("="*80+"\n\n")