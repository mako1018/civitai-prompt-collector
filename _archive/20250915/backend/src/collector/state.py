from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

STATE_DIR = Path("data/state")
STATE_FILE = STATE_DIR / "collector_state.json"

def load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {"cursor": None, "total_collected": 0, "batches": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)