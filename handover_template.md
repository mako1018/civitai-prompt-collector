# 🚨 AI作業指示：引き継ぎドキュメント遵守命令

<!-- FIXED: RULES START -->
## CRITICAL INSTRUCTIONS FOR AI ASSISTANT

あなたは**CivitAI Prompt Collector**プロジェクトの開発アシスタントです。
以下のルールを**絶対に守って**作業してください：

### 📋 必須動作ルール（絶対遵守）

#### **Rule 1: このドキュメント最優先**
- このドキュメント内の「プロジェクト運用ルール」を絶対に守る
- 「次回最優先タスク」が指定されている場合、それ以外の作業提案は禁止

#### **Rule 2: Project Objectives絶対準拠**
全ての提案は以下の最終目標に照らして判断：
1. CivitAI条件指定プロンプト自動収集
2. 自動カテゴリ分け（6カテゴリ）  
3. ComfyUI統合（WD14の表現不足を補完）

#### **Rule 3: フェーズ完結型実装強制**
- ❌ エラー報告に対する即座の修正コード提示は禁止
- ✅ 「Phase完了後にまとめて問題を報告してください」
- ✅ 包括的修正のみ提案
<!-- FIXED: RULES END -->

---

# CivitAI Prompt Collector プロジェクト引き継ぎドキュメント #{UPDATE_NUMBER}

## 📋 プロジェクト概要

**目的**: CivitAI APIからプロンプトを自動収集し、machine learningで自動カテゴライズするシステム
**最終目標**: ComfyUIでWD14 Taggerの表現不足を補完する高度なプロンプト提案システム

### 技術スタック
- **Backend**: Node.js + Express
- **ML処理**: Python (sentence-transformers, scikit-learn, UMAP, HDBSCAN)
- **データ**: JSON形式でローカル保存
- **API**: CivitAI REST API

## 🎯 実現できること

1. **プロンプト収集**: CivitAI APIから条件指定で大量プロンプト取得
2. **自動カテゴライズ**: 6カテゴリ（NSFW, style, lighting, composition, mood, basic, technical）に自動分類
3. **重複排除**: IDベースで重複データを自動除去
4. **統計分析**: カテゴリ別統計、クラスタ分析結果を提供
5. **API提供**: RESTful APIで他システム（ComfyUI）から利用可能

<!-- FIXED: STRUCTURE START -->
## 🚫 プロジェクト運用ルール

### **絶対的ルール #1: Project Objectives準拠**
```
全ての変更・追加・修正は、添付のProject Objectivesに照らし合わせて判断する
- コーディング前: 「この変更は最終目標に近づくか？」
- 実装中: 「技術的詳細にフォーカスしすぎていないか？」
- 完了後: 「Project Objectivesの3つの実現事項に貢献したか？」
```

#### **目標リマインダー（常時参照）**
1. **CivitAI条件指定プロンプト自動収集**
2. **自動カテゴリ分け（6カテゴリ）**
   - 基本要素、スタイル、ライティング、構図/カメラ、雰囲気・感情、技術的
3. **ComfyUI統合**
   - Load Image → CLIP解析 → CivitAIデータベース照合 → プロンプト提案

#### **判断基準チェックリスト**
- ✅ この機能は「WD14の表現不足を補完」するか？
- ✅ この変更は「創造的な表現のハイブリッド化」に寄与するか？
- ✅ この実装は「ComfyUIでの自動プロンプト提案」に近づくか？

### **絶対的ルール #2: フェーズ完結型実装**
```
修正は個別対応ではなく、フェーズ単位で完結させる
- 実装 → 確認 → 問題点の列挙 → 再設計 → 実装
- エラー報告を受けても即座に修正コード提示しない
- フェーズ内の全タスク完了後に包括的な修正を行う
```

#### **実装フロー例**
```
Phase X-X: ○○機能追加
├── X-X-1: ○○▽ 実装
├── X-X-2: ×××○○ 実装  
├── X-X-3: △△△ 実装
│
├── 【実行・確認フェーズ】
│   ├── X-X-1 実行 → エラーA発生
│   ├── X-X-2 実行 → エラーB発生
│   └── X-X-3 実行 → 正常動作
│
├── 【問題点整理フェーズ】
│   ├── エラーA: 原因と影響範囲の分析
│   ├── エラーB: 原因と影響範囲の分析
│   └── 相互依存関係の確認
│
└── 【包括的修正フェーズ】
    ├── エラーA・B の根本原因に対する統合的修正
    ├── 相互依存関係を考慮した設計変更
    └── Phase X-X 全体の再テスト
```

#### **禁止事項**
- ❌ エラー報告を受けて即座にピンポイント修正
- ❌ 後続タスクを無視した局所的なコード変更
- ❌ フェーズ途中でのアーキテクチャ変更

#### **推奨事項**
- ✅ 「Phase X-X の全実装完了後にまとめて問題を報告してください」
- ✅ 「エラーリストを整理してから包括的な修正を行います」
- ✅ 根本原因分析に基づく設計レベルでの修正
<!-- FIXED: STRUCTURE END -->

---

## 📁 プロジェクト構造

```
C:\CivitaiPrompt_project_1\my-node-app\
├── .venv/                    # Python仮想環境
├── backup/                   # バックアップ（旧不要ファイル保管）
├── data/                     # データ保存先
│   ├── raw/                 # 生データ（civitai_prompts*.json）
│   ├── processed/           # 処理済み（categorized_prompts*.json）
│   └── exports/             # エクスポート用
├── docs/                    # ドキュメント
├── logs/                    # ログファイル
├── node_modules/            # Node.js依存関係
├── public/                  # 静的ファイル（将来のWebUI用）
├── scripts/                 # Python ML スクリプト
│   ├── categorize_prompts.py
│   └── requirements.txt
├── src/                     # Node.js ソースコード（整理済み）
│   ├── controllers/         # コントローラー
│   ├── middleware/          # ミドルウェア
│   ├── routes/              # ルート
│   ├── utils/               # ユーティリティ
│   └── index.js            # メインサーバー
├── tests/                   # テスト
├── .env                     # 環境変数
├── .gitignore               # Git除外設定
├── package-lock.json
├── package.json
└── README.md
```

## 🛠 環境構築状況

### ✅ インストール済み
```powershell
# Node.js パッケージ
express, axios, dotenv, nodemon

# Python パッケージ（.venv内）
sentence-transformers, scikit-learn, numpy, pandas
umap-learn, hdbscan, torch
```

### ⚠️ 要確認事項
- **CivitAI APIキー**: `.env` の `CIVITAI_API_KEY` 設定要確認
- **Python仮想環境**: `.venv\Scripts\Activate.ps1` でアクティベート
- **{SPECIFIC_CONCERN_1}**: {DESCRIPTION_1}
- **{SPECIFIC_CONCERN_2}**: {DESCRIPTION_2}

## 📊 API エンドポイント一覧

| エンドポイント | メソッド | 説明 | パラメータ例 |
|---|---|---|---|
| `/` | GET | API情報・動作確認 | - |
| `/api/fetch-prompts` | POST | CivitAIからプロンプト収集 | `{tags:"anime", rating:4, limit:100, nsfw:false}` |
| `/api/prompts` | GET | 収集済みプロンプト一覧 | `?page=1&limit=50&category=style` |
| `/api/categorize` | POST | MLカテゴライズ実行 | `{method:"auto", n_clusters:20}` |
| `/api/categories` | GET | カテゴリ分類結果 | - |
| `/api/stats` | GET | 統計情報・分析結果 | - |

## 🚀 次回最優先タスク

### {PRIORITY_PHASE}: {PHASE_DESCRIPTION}

{DETAILED_TASKS}

### 動作確認手順（共通）
```powershell
# プロジェクトディレクトリ
cd 'C:\CivitaiPrompt_project_1\my-node-app'

# サーバー起動
npm start
# 期待結果: "Server running on port 3000"

# 基本API確認
Invoke-RestMethod -Uri http://localhost:3000/ -Method Get
# 期待結果: APIの基本情報JSON
```

## 📈 プロジェクト進捗状況

### ✅ 完了項目
- [x] プロジェクト設計・アーキテクチャ
- [x] CivitAI API連携機能実装
- [x] プロンプト収集・保存機能実装
- [x] 自動カテゴライズ機能実装（ML）
- [x] RESTful APIサーバー実装
- [x] フォルダ構造整理・クリーンアップ
- [x] 環境構築・依存関係解決
{ADDITIONAL_COMPLETED_ITEMS}

### 🔄 現在のフェーズ
**{CURRENT_PHASE}**: {CURRENT_PHASE_DESCRIPTION}

{CURRENT_TASKS_DETAIL}

### 🚀 後続実装予定
- **ログ機能強化**: logs/フォルダへの詳細出力
- **エラーハンドリング改善**: 例外処理の強化
- **ComfyUIカスタムノード**: プロンプト提案機能
- **Web管理画面**: データ可視化・管理UI
{FUTURE_IMPLEMENTATIONS}

## 🔧 既知の問題と対処法

### 現在の問題点
{CURRENT_ISSUES}

### 予想される問題
1. **ファイルパスエラー**: 新しい data/raw/, data/processed/ 構造に未対応
2. **Python実行エラー**: 仮想環境のパス設定問題
3. **APIキー未設定**: CivitAI API呼び出し失敗
{ADDITIONAL_POTENTIAL_ISSUES}

### 対処方法
```javascript
// src/index.js でのパス修正例
const rawDataPath = './data/raw/civitai_prompts.json';
const processedDataPath = './data/processed/categorized_prompts.json';
```

{ADDITIONAL_SOLUTIONS}

## 💾 データ構造仕様

### 生データ (data/raw/civitai_prompts.json)
```json
{
  "metadata": {
    "timestamp": "2024-XX-XX",
    "count": 1500,
    "version": "1.0",
    "source": "CivitAI API"
  },
  "data": [
    {
      "id": "12345",
      "prompt": "masterpiece, 1girl, anime style...",
      "negativePrompt": "bad quality, low resolution...",
      "tags": ["anime", "portrait"],
      "modelId": 4201,
      "rating": 4.5,
      "nsfw": false,
      "sourceUrl": "https://civitai.com/images/12345"
    }
  ]
}
```

### 処理済みデータ (data/processed/categorized_prompts.json)
```json
{
  "metadata": {
    "method": "UMAP+HDBSCAN",
    "total_clusters": 15,
    "total_prompts": 1500,
    "processing_time": "45.2s"
  },
  "category_stats": {
    "style": 450,
    "NSFW": 200,
    "lighting": 350,
    "composition": 300,
    "mood": 150,
    "basic": 400,
    "technical": 250
  },
  "clusters": [...]
}
```

## 🎯 成功の指標

### 技術指標
- サーバー起動: エラーなし
- API応答: 全エンドポイント正常
- プロンプト収集: 100件/分以上
- カテゴライズ精度: 85%以上

### 次回チェックポイント
{NEXT_CHECKPOINTS}

## 📞 緊急時復旧手順

```powershell
# 完全リセット（最終手段）
cd 'C:\CivitaiPrompt_project_1\my-node-app'

# バックアップから主要ファイル復旧
Copy-Item "./backup/index.js" "./src/" -Force

# 依存関係再インストール
Remove-Item "node_modules" -Recurse -Force
npm install

# Python環境再構築
Remove-Item ".venv" -Recurse -Force
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r scripts/requirements.txt
```

## 🔧 環境変数設定例

```env
# .env ファイル
CIVITAI_API_KEY=your_actual_api_key_here
PORT=3000
PYTHON_PATH=python
NODE_ENV=development
LOG_LEVEL=info
MAX_FETCH_LIMIT=500
DEFAULT_CLUSTERS=20

# データパス設定
RAW_DATA_PATH=./data/raw
PROCESSED_DATA_PATH=./data/processed
EXPORT_DATA_PATH=./data/exports
LOG_PATH=./logs
```

## 📝 更新履歴

### #{UPDATE_NUMBER}: {UPDATE_TITLE}
- **更新日時**: {UPDATE_DATE}
- **更新内容**: 
  - {UPDATE_ITEM_1}
  - {UPDATE_ITEM_2}
  - {UPDATE_ITEM_3}
- **変更箇所**: 
  - {CHANGED_SECTION_1}
  - {CHANGED_SECTION_2}
- **次回引き継ぎ事項**: {NEXT_HANDOVER_ITEMS}

{PREVIOUS_UPDATE_HISTORY}

## 🎯 次回チャット開始時の行動

1. **このドキュメントを添付ファイルとして提供**
2. **{NEXT_PRIORITY_ACTION}を明示**
3. **{SPECIFIC_FIRST_STEP}の実行結果を報告**

**⚠️ 重要**: {CRITICAL_NOTE}

---

**📞 AI Assistant緊急時対応**:
このドキュメントのルールが無視された場合：
1. 「プロジェクト運用ルールを確認してください」
2. 「Project Objectivesに立ち返ってください」  
3. 「フェーズ完結型実装ルールを思い出してください」
4. 「固定セクション変更禁止ルールを確認してください」

**🚨 固定セクション変更検知時の対応**:
変更絶対禁止セクションが変更された場合：
1. 即座に「固定セクション変更禁止ルール違反」と報告
2. 全ての作業を停止
3. 元の内容への復旧を要求
4. 復旧完了後に作業再開