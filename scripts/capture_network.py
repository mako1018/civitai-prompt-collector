import json, os, sys
from playwright.sync_api import sync_playwright

URL = "https://civitai.com/models/9173928"

def try_print_json(resp):
    try:
        ct = resp.headers.get("content-type","")
        if "application/json" in ct or resp.url.lower().find("api")!=-1 or resp.url.lower().find("models")!=-1:
            try:
                data = resp.json()
            except Exception:
                return
            print("=== JSON RESPONSE ===")
            print("status:", resp.status, "url:", resp.url)
            if isinstance(data, dict):
                print("top keys:", list(data.keys())[:50])
            elif isinstance(data, list):
                print("list len:", len(data))
            s = json.dumps(data, ensure_ascii=False)
            print(s[:4000])
    except Exception as e:
        print("resp error:", e)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    page.on("response", try_print_json)
    page.goto(URL, timeout=60000)
    page.wait_for_timeout(8000)
    browser.close()
