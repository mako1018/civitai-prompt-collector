from typing import List, Dict
from .config import CATEGORIES

# キーワードマッチ実装
def keyword_categorize(text: str) -> List[str]:
    text_lower = (text or "").lower()
    hits = set()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                hits.add(cat)
                break
    return sorted(hits)

# 互換ラッパー
def categorize_prompt(text: str) -> List[str]:
    return keyword_categorize(text)

# 埋め込み/次元削減/クラスタリング
def cluster_prompts(prompts: List[str], min_cluster_size: int = 5, umap_n_neighbors: int = 15, umap_n_components: int = 5):
    if not prompts:
        return {"labels": [], "embedding": None, "cluster_info": {}}
    try:
        import numpy as np
        from .embeddings import embed_texts
        import umap
        import hdbscan
    except Exception as e:
        raise RuntimeError("必要な依存がありません: sentence-transformers, umap-learn, hdbscan") from e

    embs = embed_texts(prompts)
    n_samples = len(prompts)
    adj_components = max(1, min(umap_n_components, max(1, n_samples - 1)))

    try:
        reducer = umap.UMAP(n_neighbors=umap_n_neighbors, n_components=adj_components, metric="cosine", random_state=42)
        low = reducer.fit_transform(embs)
    except Exception as e:
        print(f"[cluster_prompts] UMAP failed ({e}), falling back to PCA/embeddings")
        try:
            from sklearn.decomposition import PCA
            pca_n = min(adj_components, embs.shape[1])
            low = PCA(n_components=pca_n, random_state=42).fit_transform(embs)
        except Exception:
            low = embs

    # --- 追加: 少数サンプルは KMeans にフォールバック（HDBSCAN は少数で noise にしやすい） ---
    labels = None
    try:
        if n_samples < 5:
            from sklearn.cluster import KMeans
            k = min(2, n_samples)
            km = KMeans(n_clusters=k, random_state=42)
            labels = km.fit_predict(low)
        else:
            # HDBSCAN の min_cluster_size は最低 2 にする（1 を渡すと例外になる）
            hdb_min_cluster = max(2, int(min_cluster_size))
            # min_samples を安全に設定（None だと自動、ここは半分を目安）
            hdb_min_samples = max(1, hdb_min_cluster // 2)
            clusterer = hdbscan.HDBSCAN(min_cluster_size=hdb_min_cluster, min_samples=hdb_min_samples, metric="euclidean")
            labels = clusterer.fit_predict(low)
    except Exception as e:
        print(f"[cluster_prompts] clustering failed ({e}), marking all as noise")
        import numpy as _np
        labels = _np.array([-1] * n_samples)
    # --- 追加終了 ---

    unique, counts = np.unique(labels, return_counts=True)
    cluster_info = {int(k): int(v) for k, v in zip(unique.tolist(), counts.tolist())}
    return {"labels": labels, "embedding": embs, "cluster_info": cluster_info}

# 代表キーワード抽出（簡易）
def summarize_clusters(prompts: List[str], labels) -> Dict[int, str]:
    from collections import Counter
    clusters = {}
    for lbl, txt in zip(labels, prompts):
        clusters.setdefault(int(lbl), []).append(txt)
    summaries = {}
    for lbl, items in clusters.items():
        if lbl == -1:
            summaries[lbl] = "noise"
            continue
        words = " ".join(items).lower().split()
        common = [w for w, _ in Counter(words).most_common(10) if len(w) > 3]
        summaries[lbl] = " ".join(common[:5]) if common else ""
    return summaries

# バッチ API
def categorize_prompts_batch(prompts: List[str], use_clustering: bool = False, **cluster_kwargs):
    keyword_results = [keyword_categorize(p) for p in prompts]
    if not use_clustering:
        return {"keyword": keyword_results}
    cluster_res = cluster_prompts(prompts, **cluster_kwargs)
    summaries = summarize_clusters(prompts, cluster_res["labels"])
    return {"keyword": keyword_results, "clusters": cluster_res, "summaries": summaries}
