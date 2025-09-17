import sqlite3
from typing import Optional, Dict, Any

CREATE_PROMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    model_id TEXT,
    prompt TEXT,
    categories TEXT,
    created_at TEXT
);
"""

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_PROMPTS_TABLE)
    conn.commit()
    conn.close()

def save_prompt(db_path: str, record: Dict[str, Any]):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO prompts (id, model_id, prompt, categories, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            record.get("id"),
            record.get("model_id"),
            record.get("prompt"),
            record.get("categories"),
            record.get("created_at"),
        ),
    )
    conn.commit()
    conn.close()

def count_prompts(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM prompts")
    n = cur.fetchone()[0]
    conn.close()
    return n
