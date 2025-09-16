from typing import List
from .config import CATEGORIES

def categorize_prompt(text: str) -> List[str]:
    """
    単純キーワードマッチによるカテゴリ割当（暫定）。
    後で sentence-transformers 等で置き換えます。
    """
    text_lower = text.lower()
    hits = set()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                hits.add(cat)
                break
    return sorted(hits)
