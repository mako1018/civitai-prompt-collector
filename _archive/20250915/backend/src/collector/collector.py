from __future__ import annotations
import os, time, json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from backend.src.collector import state
from backend.src.logging.logger import get_logger
from backend.src.common.schema import make_record, validate_record

logger = get_logger()

API_BASE = "https://civitai.com/api/v1"
# TODO: Replace with the actual endpoint you intend to collect initially (e.g., "/images", "/models", etc.)
ENDPOINT = "/models" # placeholder path; adjust to real CivitAI API path
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

SAVE_BATCH_SIZE = 50  # flush threshold
REQUEST_TIMEOUT = 30

# TODO: Add exponential backoff strategy for 429 & transient 5xx

def api_fetch(limit: int, cursor: Optional[str]) -> Tuple[List[Dict], Optional[str]]:
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    headers = {}
    api_key = os.getenv("CIVITAI_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.get(API_BASE + ENDPOINT, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    status = resp.status_code
    if status == 429:
        raise RuntimeError("Rate limited (429)")  # TODO: implement retry/backoff
    if status >= 500:
        raise RuntimeError(f"Server error {status}")
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    # Common CivitAI patterns used metadata.nextCursor; adjust if actual differs
    next_cursor = (data.get("metadata") or {}).get("nextCursor")

    records = []
    for it in items:
        # まず prompt をそのまま試す（/models には通常無い）
        raw_prompt = it.get("prompt")

        # 無ければ name + description で代替
        if not raw_prompt:
            name = it.get("name") or ""
            desc = it.get("description") or ""
            raw_prompt = (name + "\n" + desc).strip()

        # それでも空ならスキップ
        if not raw_prompt:
            continue

        r = make_record(pid=it.get("id"), prompt=raw_prompt)
        if validate_record(r):
            records.append(r)
        else:
            logger.debug("Record failed validation", extra={"extra_data": {"id": it.get("id")}})
    return records, next_cursor

def run(max_batches: int = 5, batch_limit: int = 50, sleep_sec: float = 1.0):
    st = state.load_state()
    cursor = st.get("cursor")
    total = st.get("total_collected", 0)
    batch_index = 0
    buffer: List[Dict] = []

    logger.info("Collector start", extra={"extra_data": {"cursor": cursor, "already_collected": total}})

    while batch_index < max_batches:
        try:
            records, next_cursor = api_fetch(batch_limit, cursor)
        except Exception as e:
            logger.error("Fetch failed", extra={"extra_data": {"error": str(e), "cursor": cursor}})
            break

        if not records:
            logger.info("No records returned; stopping.")
            break

        buffer.extend(records)
        total += len(records)
        batch_index += 1
        cursor = next_cursor

        logger.info(
            "Batch collected",
            extra={"extra_data": {"batch": batch_index, "batch_size": len(records), "total": total, "cursor": cursor}}
        )

        if len(buffer) >= SAVE_BATCH_SIZE:
            _save_flush(buffer)
            buffer.clear()

        st.update({"cursor": cursor, "total_collected": total, "batches": batch_index})
        state.save_state(st)

        if not cursor:
            logger.info("No next cursor; stopping.")
            break

        time.sleep(sleep_sec)

    if buffer:
        _save_flush(buffer)
    logger.info("Collector finished", extra={"extra_data": st})

def _save_flush(records: List[Dict]):
    ts = int(time.time())
    filename = f"raw_{ts}_{len(records)}.json"
    path = RAW_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("Flushed records", extra={"extra_data": {"file": str(path), "count": len(records)}})

if __name__ == "__main__":
    run(max_batches=5, batch_limit=50, sleep_sec=1.0)