"""
Adapter skeleton for legacy civitai_collector_v8 (to be integrated later).
Later steps:
  - Import legacy logic
  - Map to new schema via make_record
  - Handle any legacy-specific error translation
"""
from typing import List, Tuple, Optional, Dict
from backend.src.common.schema import make_record

try:
    from legacy.collector.civitai_collector_v8 import fetch_legacy_batch  # placeholder import name
except ImportError:
    fetch_legacy_batch = None

def collect_batch(limit: int = 50, cursor: Optional[str] = None
                  ) -> Tuple[List[Dict], Optional[str]]:
    if fetch_legacy_batch is None:
        raise RuntimeError("Legacy collector not available yet.")
    raw_resp = fetch_legacy_batch(limit=limit, cursor=cursor)
    items = raw_resp.get("items", [])
    next_cursor = raw_resp.get("nextCursor")
    records = []
    for it in items:
        rec = make_record(
            pid=it.get("id"),
            prompt=it.get("prompt") or it.get("promptText") or ""
        )
        records.append(rec)
    return records, next_cursor