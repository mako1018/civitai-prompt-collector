import pytest
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

def test_embed_texts_importable():
    st = pytest.importorskip("sentence_transformers")
    from collector.embeddings import embed_texts
    samples = ["hello world", "another sample"]
    embs = embed_texts(samples, model_name="all-mpnet-base-v2")
    assert embs.shape[0] == 2
    assert embs.shape[1] > 0
