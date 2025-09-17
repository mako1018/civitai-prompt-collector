import pytest
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from collector.categorizer import keyword_categorize, categorize_prompts_batch

def test_keyword_categorize_basic():
    txt = "A photorealistic portrait with sunset lighting"
    cats = keyword_categorize(txt)
    assert isinstance(cats, list)

def test_batch_api_smoke():
    samples = ["photo smiling woman studio lighting", "anime big eyes character", "studio portrait"]
    res = categorize_prompts_batch(samples, use_clustering=False)
    assert "keyword" in res
    assert len(res["keyword"]) == 3
