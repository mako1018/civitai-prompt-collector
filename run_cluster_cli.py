from pathlib import Path
import sys
import sqlite3
import argparse

ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from collector.categorizer import categorize_prompts_batch

def load_prompts(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, full_prompt FROM civitai_prompts")
    return cur.fetchall()

def main(db="test_collect.db", min_cluster_size=3):
    if not Path(db).exists():
        print("DB not found:", db); return
    conn = sqlite3.connect(db)
    items = load_prompts(conn)
    if not items:
        print("no prompts"); return
    ids, texts = zip(*items)
    res = categorize_prompts_batch(list(texts), use_clustering=True, min_cluster_size=min_cluster_size)
    labels = res.get("clusters", {}).get("labels", [])
    summaries = res.get("summaries", {})
    print("cluster_info:", res.get("clusters", {}).get("cluster_info"))
    print("summaries sample:", summaries)
    conn.close()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="test_collect.db")
    p.add_argument("--min-cluster-size", type=int, default=3)
    args = p.parse_args()
    main(db=args.db, min_cluster_size=args.min_cluster_size)