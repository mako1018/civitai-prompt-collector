import json, re
from pathlib import Path

CAP = Path("scripts/version_capture_playwright.jsonl")
SRC = Path("scripts/hasPositive_quoted_long_strings.json")
OUT = Path("scripts/hasPositive_id_objects.json")

def load_ids():
    if not SRC.exists():
        print("missing:", SRC); raise SystemExit(1)
    data = json.loads(SRC.read_text(encoding="utf-8"))
    ids = set()
    for item in data:
        txt = item.get("text","")
        # find numbers (likely ids)
        for m in re.finditer(r'\b(\d{2,10})\b', txt):
            ids.add(int(m.group(1)))
    return ids

def find_matches_in_obj(obj, ids):
    matches = []
    if isinstance(obj, dict):
        # direct id match
        if "id" in obj:
            try:
                if int(obj["id"]) in ids:
                    matches.append(obj)
            except Exception:
                pass
        # any key value equal to an id (int/str)
        for k,v in obj.items():
            if isinstance(v, (int,)) and v in ids:
                matches.append(obj); break
            if isinstance(v, str):
                try:
                    if int(v) in ids:
                        matches.append(obj); break
                except:
                    pass
        # recurse into children
        for k,v in obj.items():
            matches.extend(find_matches_in_obj(v, ids))
    elif isinstance(obj, list):
        # if list directly contains ids
        for v in obj:
            if isinstance(v, int) and v in ids:
                # try to return parent list as context => no parent here, skip
                pass
        for v in obj:
            matches.extend(find_matches_in_obj(v, ids))
    return matches

def main():
    ids = load_ids()
    if not CAP.exists():
        print("missing capture:", CAP); return
    found = []
    uniq = {}
    for idx, line in enumerate(CAP.read_text(encoding="utf-8").splitlines(), 1):
        try:
            e = json.loads(line)
        except:
            continue
        # inspect whole parsed line object and any JSON fragments inside text fields
        candidates = [e]
        for key in ("text","text_snip","body"):
            txt = e.get(key)
            if isinstance(txt,str) and "{" in txt:
                # try parse embedded JSON fragments
                for m in re.finditer(r'(\{(?:.|\n){40,40000}\})', txt):
                    try:
                        candidates.append(json.loads(m.group(1)))
                    except:
                        pass
        for c in candidates:
            for match in