import os
from typing import Dict, Any, Optional
from . import config
from .db import init_db, save_prompt
from .categorizer import categorize_prompt

# 既存の v8 実装があれば取り込む（存在しない場合は代替スタブ）
try:
    from .civitai_collector_v8 import CivitaiPromptCollector as V8Collector  # type: ignore
except Exception:
    V8Collector = None  # 型: ignore

class CivitaiPromptCollector:
    def __init__(self, db_path: Optional[str] = None, user_agent: str = "CivitaiPromptCollector/1.0"):
        self.db_path = db_path or config.DB_DEFAULT
        self.user_agent = user_agent
        self.api_key = os.getenv(config.CIVITAI_API_ENV, None)
        init_db(self.db_path)

        # v8 実装があるならラップして利用
        self._v8 = V8Collector() if V8Collector is not None else None

    def collect_for_models(self, models: Dict[str, Optional[str]], max_per_model: int = 5000):
        """
        models: {"model_name": "model_id" or None}
        簡易的に v8 実装があれば呼び出し、なければ空の結果を返す。
        各プロンプトは DB に保存され、カテゴリ付与を行う（暫定）。
        """
        results = {}
        for name, model_id in models.items():
            items = []
            if self._v8 is not None:
                # v8 の collect メソッド名は未知のため想定して呼び出し
                if hasattr(self._v8, "collect_for_model"):
                    items = self._v8.collect_for_model(model_id, max_items=max_per_model)
                elif hasattr(self._v8, "collect"):
                    items = self._v8.collect(model_id, max_items=max_per_model)
                else:
                    items = []
            # items は dict のリストを想定（id, model_id, prompt, created_at）
            for it in items:
                categories = categorize_prompt(it.get("prompt", ""))
                rec = {
                    "id": it.get("id"),
                    "model_id": it.get("model_id", model_id),
                    "prompt": it.get("prompt"),
                    "categories": ",".join(categories),
                    "created_at": it.get("created_at"),
                }
                save_prompt(self.db_path, rec)
            results[name] = {"count": len(items)}
        return results

    def visualize_category_distribution(self, *args, **kwargs):
        # visualizer を遅延インポート（循環回避）
        from .visualizer import visualize_category_distribution as viz
        return viz(db_path=self.db_path, *args, **kwargs)
