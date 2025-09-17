import sqlite3
from typing import Optional, Dict, Any, Union

CREATE_PROMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY NOT NULL,
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

def save_prompt(conn: Union[str, sqlite3.Connection], record: Dict[str, Any]):
    if isinstance(conn, str):
        conn = sqlite3.connect(conn)

    # Validate input data
    if not record.get("id"):
        raise ValueError("The 'id' field is required and cannot be None.")

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

def count_prompts(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM prompts")
    n = cur.fetchone()[0]
    conn.close()
    return n
