import requests, re, json
from pathlib import Path

IMAGE_ID = 14368508
OUT = Path("scripts/image_html_extracted.json")
H = {"User-Agent":"Mozilla/5.0","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
KEYS = ("prompt","positivePrompt","fullPrompt","positive_prompt","full_prompt","postBody","body","caption","text","positivePromptText")

def find_json_blocks(html):
    blocks = []
    for m in re.finditer(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.S|re.I):
        blocks.append(m.group(1))
    for m in re.finditer(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.S|re.I):
        blocks.append(m.group(1))
    for m in re.finditer(r'window\.[A-Za-z0-9_]+?\s*=\s*(\{.*?\});', html, re.S):
        blocks.append(m.group(1))
    return blocks

def walk_search(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k,v in obj.items():
            kl = k.lower()
            if isinstance(v, str) and any(key.lower() in kl for key in KEYS):
                found.append({"path": path + "/" + k, "text": v})
            found.extend(walk_search(v, path + "/" + k))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            found.extend(walk_search(v, f"{path}[{i}]"))
    return found

def extract_from_html(html):
    results = []
    # try JSON blocks
    for block in find_json_blocks(html):
        try:
            j = json.loads(block)
        except Exception:
            try:
                j = json.loads(re.sub(r';\s*$', '', block.strip()))
            except Exception:
                continue
        results.extend(walk_search(j))
    # meta tags fallback
    for m in re.finditer(r'<meta[^>]+(?:name|property)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']{20,4000})["\']', html, re.I):
        name, content = m.group(1), m.group(2)
        if any(k.lower() in name.lower() for k in KEYS) or len(content) > 80:
            results.append({"path": f"meta/{name}", "text": content})
    # raw regex fallback for prompt-like long strings
    if not results:
        m = re.search(r'(["\']?(?:positivePrompt|fullPrompt|prompt|postBody|body|caption)["\']?\s*[:=]\s*["\'])(.{60,4000}?)["\']', html, re.S|re.I)
        if m:
            results.append({"path":"raw/prompt_guess","text": m.group(2)})
    return results

def main():
    url = f"https://civitai.com/images/{IMAGE_ID}"
    try:
        r = requests.get(url, headers=H, timeout=20)
    except Exception as e:
        print("fetch failed:", e); return
    print("status:", r.status_code, "ct:", r.headers.get("content-type"))
    html = r.text
    found = extract_from_html(html)
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", len(found), "entries to", OUT)
    for i,p in enumerate(found[:10],1):
        print(f"---[{i}] {p['path']}\n{p['text'][:800]}\n")

if __name__ == "__main__":
    main()