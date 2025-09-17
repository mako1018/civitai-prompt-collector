import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from collector.collector import CivitaiPromptCollector

def main():
    api_key = os.getenv("CIVITAI_API_KEY")  # .env に設定済みならここで読み込まれる
    coll = CivitaiPromptCollector(api_key=api_key, db_path=str(ROOT / "test_collect.db"), per_page=50)

    # 実際のエンドポイントと params は環境に合わせて変更してください。
    # 例: 新しい順で取得、最大5ページ
    items = coll.fetch_prompts(endpoint="/api/prompts", params={"sort":"new"}, max_pages=5, delay=0.5)
    print("fetched:", len(items))
    if items:
        coll.save_to_db(items)
        print("saved to DB")

if __name__ == "__main__":
    main()
