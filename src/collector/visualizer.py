import sqlite3
import matplotlib.pyplot as plt
from typing import List, Optional

def _load_counts(db_path: str, models_to_plot: Optional[List[str]] = None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT categories FROM prompts")
    rows = cur.fetchall()
    conn.close()
    counts = {}
    for (cats,) in rows:
        if not cats:
            continue
        for c in cats.split(","):
            counts[c] = counts.get(c, 0) + 1
    return counts

def visualize_category_distribution(db_path: str, models_to_plot: Optional[List[str]] = None, normalize_percent: bool = True, show: bool = True):
    counts = _load_counts(db_path, models_to_plot)
    if not counts:
        print("可視化対象のデータが見つかりません")
        return counts
    labels = list(counts.keys())
    values = list(counts.values())
    if normalize_percent:
        total = sum(values)
        values = [v * 100.0 / total for v in values]
        ylabel = "割合 (%)"
    else:
        ylabel = "件数"
    plt.figure(figsize=(8, 4))
    plt.bar(labels, values)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel(ylabel)
    plt.title("カテゴリ分布")
    plt.tight_layout()
    if show:
        plt.show()
    return counts
