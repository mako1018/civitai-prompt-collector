from __future__ import annotations
from typing import Optional, Any, Dict
from datetime import datetime, timezone

RAW_SCHEMA_VERSION = "raw.v1"

REQUIRED_FIELDS = ["id", "prompt"]

def make_record(
    *,
    pid: str,
    prompt: str,
    source: str = "civitai",
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "id": str(pid),
        "prompt": prompt,
        "meta": {
            "source": source,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": RAW_SCHEMA_VERSION
        },
        "extra": extra or {}
    }

def validate_record(r: Dict[str, Any]) -> bool:
    for f in REQUIRED_FIELDS:
        if f not in r or r[f] in (None, ""):
            return False
    return True