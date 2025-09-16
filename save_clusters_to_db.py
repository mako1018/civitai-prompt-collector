from pathlib import Path
import sys
import sqlite3

ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from collector.categorizer import categorize_prompts_batch

DB = "test_collect.db"  # 必要に応じて置き換えてください

def load_prompts(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, full_prompt FROM civitai_prompts")
    return cur.fetchall()

def save_categories(conn, prompt_id, categories):
    cur = conn.cursor()
    # prompts テーブルがある場合はそちらも更新
    cur.execute("UPDATE civitai_prompts SET categories = ? WHERE id = ?", (categories, prompt_id))
    if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'").fetchone():
        conn.execute("UPDATE prompts SET categories = ? WHERE id = ?", (categories, prompt_id))
    conn.commit()

def main():
    conn = sqlite3.connect(DB)
    items = load_prompts(conn)
    if not items:
        print("no prompts")
        return
    ids, texts = zip(*items)
    res = categorize_prompts_batch(list(texts), use_clustering=True, min_cluster_size=3)
    labels = res.get("clusters", {}).get("cluster_info")
    # res["clusters"]["labels"] はクラスタラベル配列
    cluster_labels = res.get("clusters", {}).get("labels")
    keyword_lists = res.get("keyword", [])
    for pid, kw, lbl in zip(ids, keyword_lists, cluster_labels):
        kw_str = ",".join(kw) if kw else ""
        cat = kw_str + (f"|cluster:{int(lbl)}" if lbl is not None else "")
        save_categories(conn, pid, cat)
    print("saved categories for", len(ids))
    conn.close()

if __name__ == "__main__":
    main()