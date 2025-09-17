import sqlite3
from pathlib import Path

DB = "test_collect.db"  # 実運用DBを使う場合はファイル名を置き換えてください

def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ensure target table exists (same schema as db.py expects)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS prompts (
        id TEXT PRIMARY KEY,
        model_id TEXT,
        prompt TEXT,
        categories TEXT,
        created_at TEXT
    );
    """)

    # read v8 prompts
    cur.execute("SELECT id, civitai_id, full_prompt, collected_at, model_id FROM civitai_prompts")
    rows = cur.fetchall()
    for row in rows:
        row_id, civitai_id, full_prompt, collected_at, model_id = row
        # collect categories for this prompt_id
        cur.execute("SELECT category FROM prompt_categories WHERE prompt_id = ?", (row_id,))
        cats = [r[0] for r in cur.fetchall()]
        categories = ",".join(sorted(set(cats))) if cats else None

        # upsert into prompts (use civitai_id as id if available, otherwise civitai_prompts.id)
        target_id = civitai_id or str(row_id)
        cur.execute("""
        INSERT INTO prompts (id, model_id, prompt, categories, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            model_id=excluded.model_id,
            prompt=excluded.prompt,
            categories=excluded.categories,
            created_at=excluded.created_at
        """, (target_id, model_id, full_prompt, categories, collected_at))

    conn.commit()
    conn.close()
    print("migration complete")

if __name__ == "__main__":
    dbfile = DB
    if not Path(dbfile).exists():
        print("DB not found:", dbfile)
    else:
        migrate(dbfile)