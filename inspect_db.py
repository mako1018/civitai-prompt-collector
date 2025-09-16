from pathlib import Path
import sys
import sqlite3
import json

ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

DB = "test_collect.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
# テーブル存在確認と件数
try:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("tables:", [r[0] for r in cur.fetchall()])
    cur.execute("SELECT COUNT(*) FROM civitai_prompts")
    print("prompts count:", cur.fetchone()[0])
    cur.execute("SELECT civitai_id, model_name, prompt_length, full_prompt FROM civitai_prompts LIMIT 1")
    row = cur.fetchone()
    if row:
        print("sample:", {"civitai_id": row[0], "model_name": row[1], "prompt_length": row[2], "full_prompt_preview": (row[3] or "")[:200]})
    else:
        print("no prompt rows found")
except Exception as e:
    print("DB inspect error:", e)
finally:
    conn.close()