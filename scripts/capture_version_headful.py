import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "version_capture.jsonl"
URL = "https://civitai.com/models/133005/versions/1759168"

def handle_response(resp, out_f):
    try:
        ct = resp.headers.get("content-type","")
        if "application/json" in ct or any(k in resp.url.lower() for k in ("api","trpc","version","post","model","prompt")):
            try:
                data = resp.json()
            except Exception:
                return
            entry = {
                "url": resp.url,
                "status": resp.status,
                "keys": list(data.keys()) if isinstance(data, dict) else None,
                "text_snip": json.dumps(data, ensure_ascii=False)[:20000]
            }
            out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print("SAVED:", resp.status, resp.url)
    except Exception as e:
        print("resp handler error:", e)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, args=["--no-sandbox"])
    page = browser.new_page()
    with open(OUT, "w", encoding="utf-8") as f:
        page.on("response", lambda r: handle_response(r, f))
        page.goto(URL, timeout=60000)
        print("Browser opened. Interact if needed. 60s interaction window.")
        page.wait_for_timeout(60000)
        print("Done; closing.")
    browser.close()
    print("Saved to:", OUT)