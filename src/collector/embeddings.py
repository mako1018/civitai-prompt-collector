from typing import List
import numpy as np

def embed_texts(texts: List[str], model_name: str = "all-mpnet-base-v2"):
    """
    sentence-transformers を使ってテキストリストを埋め込み化して返す。
    実行前に sentence_transformers パッケージをインストールしてください。
    """
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise RuntimeError("sentence-transformers が必要です。pip install sentence-transformers") from e

    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return embeddings / norms