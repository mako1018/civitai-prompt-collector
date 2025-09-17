from pathlib import Path
import sqlite3
ROOT = Path(__file__).resolve().parent
DB = str(ROOT / "test_collect.db")

def ensure_column(conn, table, column, coltype="TEXT"):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if column in cols:
        print(f"{table}.{column} exists, skipping")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
    conn.commit()
    print(f"Added column {table}.{column}")

def main():
    if not Path(DB).exists():
        print("DB not found:", DB)
        return
    conn = sqlite3.connect(DB)
    # 対象テーブルを安全に処理
    for t in ("civitai_prompts", "prompts"):
        try:
            ensure_column(conn, t, "categories", "TEXT")
        except sqlite3.OperationalError as e:
            print(f"Skipping {t}: {e}")
    conn.close()
    print("migration complete")

if __name__ == "__main__":
    main()