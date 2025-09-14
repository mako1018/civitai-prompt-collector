import json
import time
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone
import requests

API_BASE = "https://civitai.com/api/v1"
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("CIVITAI_API_KEY")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

def fetch_prompts(limit=50, cursor=None):
    # TODO: 実際のエンドポイント仕様に合わせて修正
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor

    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    r = requests.get(f"{API_BASE}/prompts", params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def run_collect(batches=2, limit_per_batch=50, sleep_sec=0.7):
    all_items = []
    cursor = None
    for _ in range(batches):
        try:
            data = fetch_prompts(limit=limit_per_batch, cursor=cursor)
        except requests.HTTPError as e:
            print("HTTP Error:", e)
            break
        items = data.get("items") or []
        if not items:
            print("No more items.")
            break

        for it in items:
            pid = it.get("id") or str(uuid.uuid4())
            prompt_text = it.get("prompt") or it.get("text") or ""
            all_items.append({
                "id": str(pid),
                "prompt": prompt_text,
                "meta": {
                    "source": "civitai",
                    "collected_at": datetime.now(timezone.utc).isoformat()
                }
            })

        cursor = data.get("nextCursor")
        print(f"Fetched {len(items)} items. nextCursor={cursor}")
        time.sleep(sleep_sec)
        if not cursor:
            break

    if all_items:
        out_file = RAW_DIR / f"prompts_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        print("Saved:", out_file)
    else:
        print("No items collected.")

if __name__ == "__main__":
    run_collect()