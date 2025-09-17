# 不要ファイルリスト

以下は、プロジェクト内で不要と判断されたファイルのリストです。それぞれのカテゴリと削除理由を記載しています。

## 1. バックアップファイル
- `civitai_sample copy.db`: 古いデータベースのバックアップ。
- `test_collect.db.before_cluster.bak`: クラスタリング前のバックアップ。
- `test_collect.db.pre_deploy.bak`: デプロイ前のバックアップ。
- `test_collect.db.prod_bak`: 本番環境のバックアップ。
- `civitai_collector_v8.py.bak`: 古いスクリプトのバックアップ。

## 2. テンポラリファイル
- `tmp_check_url.py`: 一時的なスクリプト。
- `tmp_extract_json.py`: JSON抽出用の一時スクリプト。
- `tmp_extract_props.py`: プロパティ抽出用の一時スクリプト。
- `tmp_fetch_html.py`: HTML取得用の一時スクリプト。
- `tmp_fetch_html_version.py`: HTMLバージョン取得用の一時スクリプト。
- `tmp_image_getInfinite.json`: 一時的なJSONデータ。
- `tmp_modelversion_trpc.json`: 一時的なJSONデータ。
- `tmp_page.html`: 一時的なHTMLファイル。

## 3. 古いスクリプト
- `legacy/collector/.gitkeep`: 不要なプレースホルダーファイル。

## 4. ログファイル
- `logs/collector/run.log`: 古いログファイル。

## 5. キャッシュファイル
- `__pycache__/`: Pythonキャッシュディレクトリ。
- `.pytest_cache/`: テストキャッシュディレクトリ。

## 6. その他
- `repo.bundle`: リポジトリのバックアップファイル。

## 推奨アクション
これらのファイルは、プロジェクトの進行に不要であるため、削除を検討してください。ただし、必要に応じてバックアップを取得してから削除を行ってください。
