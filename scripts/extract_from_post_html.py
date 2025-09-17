import requests, re, json
from pathlib import Path

POST_ID = 16613809
OUT = Path("scripts/post_html_extracted.json")
H = {"User-Agent":"Mozilla/5.0","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

def find_json_blocks(html):
    blocks = []
    # Next.js embedded state
    for m in re.finditer(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.S|re.I):
        blocks.append(m.group(1))
    # generic JSON script tags
    for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.S|re.I):
        blocks.append(m.group(1))
    # inline JSON-like assignments (window.__DATA__ = {...})
    for m in re.finditer(r'window\.[A-Za-z0-9_]+?\s*=\s*(\{.*?\});', html, re.S):
        blocks.append(m.group(1))
    return blocks

def search_prompt_keys(obj):
    prompts = []
    keys = ("prompt","positivePrompt","fullPrompt","positive_prompt","full_prompt","positivePromptText","postBody","body","caption","text")
    def walk(x, path=""):
        if isinstance(x, dict):
            for k,v in x.items():
                low = k.lower()
                if isinstance(v, str) and any(kk.lower() in low for kk in keys):
                    prompts.append({"path": path + "/" + k, "text": v})
                walk(v, path + "/" + k)
        elif isinstance(x, list):
            for i,v in enumerate(x):
                walk(v, f"{path}[{i}]")
    walk(obj)
    return prompts

def main():
    url = f"https://civitai.com/posts/{POST_ID}"
    try:
        r = requests.get(url, headers=H, timeout=20)
    except Exception as e:
        print("fetch failed:", e); return
    html = r.text
    blocks = find_json_blocks(html)
    all_prompts = []
    for b in blocks:
        try:
            j = json.loads(b)
        except Exception:
            # try to recover trailing semicolon or unexpected chars
            try:
                j = json.loads(re.sub(r';\s*$', '', b.strip()))
            except Exception:
                continue
        all_prompts.extend(search_prompt_keys(j))
    # fallback: raw regex search for "positivePrompt" etc.
    if not all_prompts:
        for key in ("positivePrompt","fullPrompt","prompt","postBody","body","caption"):
            m = re.search(rf'["\']{key}["\']\s*:\s*["\'](.{{30,4000}}?)["\']', html, re.S)
            if m:
                all_prompts.append({"path": f"raw/{key}", "text": m.group(1)})
    OUT.write_text(json.dumps(all_prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", len(all_prompts), "entries to", OUT)
    for i,p in enumerate(all_prompts[:10],1):
        print(f"---[{i}] {p['path']}\n{p['text'][:800]}\n")

if __name__ == "__main__":
    main()