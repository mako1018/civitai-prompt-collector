# CivitAI Prompt Collector (Rebuild)

CivitAI からプロンプトを収集し、6カテゴリに自動分類して API で提供、将来 ComfyUI と連携するための土台です。

## フェーズ
1. 収集 (Collector)
2. 前処理 & 重複排除
3. ルール分類 (初期)
4. API 提供 (Node.js)
5. クラスタリング高度化 (UMAP + HDBSCAN)
6. ComfyUI 連携

## 構造
```
backend/
  src/
    collector/
    preprocess/
    classify/
  data/
    raw/
    processed/
    exports/
api/
  src/
docs/
  classification_spec.md
.env.example
```

## 最短動作
```
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

python backend/src/collector/collector.py
python backend/src/classify/rule_classifier.py
node api/src/index.js
```

## TODO
- CivitAI API 正式エンドポイント調整
- 前処理（正規化/重複排除）
- キーワード拡張
- Embedding + クラスタリング
- ComfyUI 連携仕様 doc 化