import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("scripts/version_capture_playwright.jsonl")
URL = "https://civitai.com/models/133005/versions/1759168"  # open this; interact manually if needed
FILTERS = ("/api/trpc/", "/api/images", "/images/", "/posts/", "/api/file/", "image.get", "post.get")

def should_save(url: str):
    u = url.lower()
    return any(p in u for p in FILTERS)

def run():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headful
        ctx = browser.new_context()
        page = ctx.new_page()
        captured = []

        def on_response(resp):
            try:
                url = resp.url
                if not should_save(url):
                    return
                status = resp.status
                headers = dict(resp.headers)
                text = ""
                try:
                    text = resp.text()
                except Exception:
                    try:
                        # binary fallback
                        text = resp.body().decode("utf-8", errors="ignore")
                    except Exception:
                        text = ""
                snippet = text[:20000]
                entry = {"url": url, "status": status, "headers": headers, "text_snip": snippet}
                captured.append(entry)
                # write incrementally
                OUT.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in captured), encoding="utf-8")
            except Exception:
                pass

        page.on("response", on_response)
        page.goto(URL)
        # wait for initial load
        time.sleep(2)
        # optionally auto-scroll to load more resources
        for _ in range(6):
            page.evaluate("window.scrollBy(0, window.innerHeight);")
            time.sleep(1)
        # allow manual interaction time (click images/posts in browser)
        print("Playwright: open page. You may now click images/posts in the browser. Waiting 30s...")
        time.sleep(30)
        # final save
        OUT.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in captured), encoding="utf-8")
        print("saved", len(captured), "entries to", OUT)
        browser.close()

if __name__ == "__main__":
    run()