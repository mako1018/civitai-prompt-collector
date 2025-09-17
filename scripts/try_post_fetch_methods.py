import requests, json, re
from pathlib import Path

POST_ID = 16613809
H = {"User-Agent":"Mozilla/5.0","Accept":"application/json, text/plain, */*"}
TIMEOUT = 20

def try_get_trpc(path, payload):
    q = requests.utils.quote(json.dumps({"json": payload}, separators=(",", ":")))
    url = f"https://civitai.com/api/trpc/{path}?input={q}"
    try:
        r = requests.get(url, headers=H, timeout=TIMEOUT)
        print("[GET]", path, "status:", r.status_code, "ct:", r.headers.get("content-type"))
        print(r.text[:3000])
    except Exception as e:
        print("[GET]", path, "failed:", e)

def try_post_trpc(path, payload):
    url = f"https://civitai.com/api/trpc/{path}"
    body = {"input": {"json": payload}}
    try:
        r = requests.post(url, headers=H, json=body, timeout=TIMEOUT)
        print("[POST json body]", path, "status:", r.status_code, "ct:", r.headers.get("content-type"))
        print(r.text[:3000])
    except Exception as e:
        print("[POST json body]", path, "failed:", e)
    # also try raw encoded input in body
    try:
        encoded = requests.utils.quote(json.dumps({"json": payload}, separators=(",", ":")))
        r2 = requests.post(url, headers=H, data=encoded, timeout=TIMEOUT)
        print("[POST data(encoded)]", path, "status:", r2.status_code, "ct:", r2.headers.get("content-type"))
        print(r2.text[:3000])
    except Exception as e:
        print("[POST data(encoded)]", path, "failed:", e)

def try_fetch_html(post_id):
    url = f"https://civitai.com/posts/{post_id}"
    try:
        r = requests.get(url, headers=H, timeout=TIMEOUT)
        print("[HTML GET] status:", r.status_code, "ct:", r.headers.get("content-type"))
        html = r.text
        print(html[:4000])
        return html
    except Exception as e:
        print("[HTML GET] failed:", e)
        return ""

def extract_from_html(html):
    keys = ["positivePrompt","positive_prompt","fullPrompt","full_prompt","prompt","postBody","body","caption"]
    found = {}
    for k in keys:
        # simple JSON-like extraction after key
        m = re.search(rf'["\']{re.escape(k)}["\']\s*:\s*["\'](.{{20,4000}}?)["\']', html, re.S)
        if m:
            found[k] = m.group(1)[:4000]
    # fallback: find long blocks that look like prompts (long comma/word sequences)
    if not found:
        m2 = re.search(r'(["\']?prompt["\']?\s*[:=]\s*["\'])(.{50,4000})["\']', html, re.S|re.I)
        if m2:
            found["prompt_guess"] = m2.group(2)[:4000]
    return found

if __name__ == "__main__":
    payload = {"id": int(POST_ID)}
    print("=== TRY tRPC GET/POST for post.getById ===")
    try_get_trpc("post.getById", payload)
    try_post_trpc("post.getById", payload)

    print("\n=== TRY other likely endpoints ===")
    try_get_trpc("post.get", payload)
    try_post_trpc("post.get", payload)
    try_get_trpc("image.getById", {"id": int(POST_ID)})
    try_post_trpc("image.getById", {"id": int(POST_ID)})

    print("\n=== FETCH HTML FALLBACK ===")
    html = try_fetch_html(POST_ID)
    found = extract_from_html(html)
    print("\n--- extracted keys ---")
    print(json.dumps(found, ensure_ascii=False, indent=2))