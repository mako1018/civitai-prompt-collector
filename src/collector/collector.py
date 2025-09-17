import os
import time
import json
import sqlite3
from typing import Dict, Any, Optional, List
from . import config
from .db import init_db, save_prompt
from .categorizer import categorize_prompt
from .logger_utils import setup_logger

logger = setup_logger(__name__)

# 既存の v8 実装があれば取り込む（存在しない場合は代替スタブ）
try:
    from .civitai_collector_v8 import CivitaiPromptCollector as V8Collector  # type: ignore
except Exception:
    V8Collector = None  # 型: ignore

class CivitaiPromptCollector:
    """
    Civitai 用の汎用プロンプト取得＆保存クラス（堅牢化）。
    - API キーは .env の CIVITAI_API_KEY を利用するか、api_key 引数で渡す。
    - endpoint: API のパス（例 "/api/prompts"）。レスポンス形式に合わせて抽出ロジックは柔軟に対応。
    """
    def __init__(self, api_key: Optional[str] = None, db_path: str = "test_collect.db",
                 per_page: int = 50, base_url: str = "https://civitai.com", timeout: int = 30, conn = None):
        if not api_key:
            raise ValueError("API key must be provided.")
        if not db_path.endswith('.db'):
            raise ValueError("Database path must end with '.db'.")

        self.api_key = api_key
        self.db_path = db_path
        self.per_page = per_page
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.conn = conn or sqlite3.connect(db_path)  # Use provided connection or create a new one
        # ensure user_agent attribute for compatibility with V8Collector / other callers
        self.user_agent = self._get_headers().get("User-Agent", "civitai-prompt-collector/1.0")

        # v8 実装があればラップして利用（db_path / user_agent を渡す）
        if V8Collector is not None:
            try:
                self._v8 = V8Collector(db_path=self.db_path, user_agent=self.user_agent)
            except TypeError:
                # もし v8 の __init__ が異なるシグネチャなら引数無しでインスタンス化
                self._v8 = V8Collector()
        else:
            self._v8 = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "civitai-prompt-collector/1.0", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _requests_session(self):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        s = requests.Session()
        retries = Retry(total=5, backoff_factor=1,
                        status_forcelist=(429, 500, 502, 503, 504),
                        allowed_methods=frozenset(["GET", "POST"]))
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))
        return s

    def fetch_prompts(self, endpoint: str = "/api/prompts", params: Dict[str, Any] = None,
                      max_pages: int = 20, delay: float = 0.5) -> List[Dict[str, Any]]:
        """
        ページネーション対応でプロンプトを取得する（堅牢化）。
        フォールバック: API が JSON を返さない／Cloudflare 等で拒否される場合は
        HTML 内の埋め込み JSON を探して抽出を試みる。
        """
        import requests
        import re
        import json as _json

        session = self._requests_session()
        all_items: List[Dict[str, Any]] = []
        params = params.copy() if params else {}

        cursor = None

        for page in range(1, max_pages + 1):
            logger.debug(f"Fetching page {page} with params: {params}")
            if "cursor" in params:
                if cursor:
                    params["cursor"] = cursor
            else:
                params["page"] = page
                params["limit"] = self.per_page

            url = f"{self.base_url}{endpoint}"
            logger.debug(f"Requesting URL: {url}")
            data = None
            items = None

            try:
                resp = session.get(url, headers=self._get_headers(), params=params, timeout=self.timeout)
                # 明示的に 404 を処理してループを抜ける
                if resp.status_code == 404:
                    logger.info(f"[fetch_prompts] not found (404): {url}")
                    break
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning(f"[fetch_prompts] request failed page={page}: {e}")

                # まず HTML 埋め込み JSON を試す（Playwright フォールバック含む）
                parsed = self._handle_html_fallback(url, session)

                # もし version パスが含まれていれば tRPC で直接取得を試みる
                version_id = None
                try:
                    import re
                    m = re.search(r"/versions/([0-9]+)", url)
                    if m:
                        version_id = int(m.group(1))
                except Exception:
                    version_id = None

                # tRPC フォールバックを試みる
                if parsed is None and version_id:
                    parsed = self._handle_trpc_fallback(url, session, version_id)

                if parsed is not None:
                    found_items = self._find_prompt_items(parsed)
                    if found_items:
                        for it in found_items:
                            all_items.append(it)
                        break

                if data is None:
                    logger.info(f"[fetch_prompts] no data extracted for page={page}, stopping")
                    break

            # at this point data may be a dict or list
            if isinstance(data, dict):
                for k in ("items", "data", "results", "prompts"):
                    if k in data and isinstance(data[k], list):
                        items = data[k]; break
                if items is None:
                    # try to find first list value in dict
                    for v in data.values():
                        if isinstance(v, list):
                            items = v
                            break
            elif isinstance(data, list):
                items = data

            if not items:
                logger.info(f"[fetch_prompts] no items on page {page}, stopping")
                break

            for it in items:
                # handle cases where item is plain string (page scraped returned list of strings)
                if isinstance(it, str):
                    prompt_text = it
                    neg = ""
                    civitai_id = ""
                    metadata = {}
                elif isinstance(it, dict):
                    prompt_text = (it.get("fullPrompt") or it.get("full_prompt") or
                                   it.get("prompt") or it.get("text") or it.get("body") or "")
                    neg = it.get("negativePrompt") or it.get("negative_prompt") or ""
                    civitai_id = str(it.get("id") or it.get("postId") or it.get("civitaiId") or "")
                    metadata = {k: v for k, v in it.items() if k not in ("fullPrompt","full_prompt","prompt","text","body","negativePrompt","negative_prompt")}
                else:
                    # unknown item type: skip
                    continue
                all_items.append({
                    "civitai_id": civitai_id,
                    "full_prompt": prompt_text,
                    "negative_prompt": neg,
                    "raw_metadata": metadata
                })

            # detect next cursor if present
            next_cursor = None
            if isinstance(data, dict):
                for tok in ("nextCursor", "next_cursor", "cursor", "next"):
                    if tok in data and data[tok]:
                        next_cursor = data[tok]; break
                meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
                for tok in ("nextCursor", "next_cursor", "cursor", "next"):
                    if tok in meta and meta[tok]:
                        next_cursor = meta[tok]; break

            if next_cursor:
                cursor = next_cursor
                params["cursor"] = cursor

            if (len(items) < self.per_page) and not next_cursor:
                break

            time.sleep(delay)

        return all_items

    def save_to_db(self, items: List[Dict[str, Any]], dedupe_on: str = "civitai_id"):
        """
        テーブル作成＆重複を避けて保存。
        dedupe_on が空ならすべて挿入（注意：重複が増える）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS civitai_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                civitai_id TEXT,
                full_prompt TEXT,
                negative_prompt TEXT,
                raw_metadata TEXT,
                categories TEXT,
                collected_at TEXT DEFAULT (datetime('now'))
            )
            """)

            # Prepare bulk insert data
            insert_data = []
            for it in items:
                civ_id = (it.get(dedupe_on) or "").strip()
                if not civ_id:
                    logger.warning(f"Skipping item with missing {dedupe_on}: {it}")
                    continue  # Skip items with empty dedupe_on key

                logger.debug(f"Attempting to insert civitai_id: {civ_id}")
                logger.debug(f"Executing SELECT query for civitai_id: {civ_id}")
                exists = cur.execute("SELECT 1 FROM civitai_prompts WHERE civitai_id = ?", (str(civ_id),)).fetchone()

                # Debugging: Log database content before SELECT query
                cur.execute("SELECT civitai_id FROM civitai_prompts")
                all_ids_before = cur.fetchall()
                logger.debug(f"Database content before SELECT: {all_ids_before}")

                # Debugging: Log database content after SELECT query
                cur.execute("SELECT civitai_id FROM civitai_prompts")
                all_ids_after = cur.fetchall()
                logger.debug(f"Database content after SELECT: {all_ids_after}")

                if exists:
                    logger.info(f"Duplicate found, skipping civitai_id: {civ_id}")
                    continue  # Skip duplicates
                logger.debug(f"No duplicate found, adding civitai_id: {civ_id}")

                insert_data.append((
                    civ_id, it.get("full_prompt", ""), it.get("negative_prompt", ""),
                    json.dumps(it.get("raw_metadata", {})), json.dumps(it.get("categories", []))
                ))

            # Execute bulk insert
            cur.executemany(
                "INSERT INTO civitai_prompts (civitai_id, full_prompt, negative_prompt, raw_metadata, categories) VALUES (?, ?, ?, ?, ?)",
                insert_data
            )
            # Commit the transaction after bulk insert
            conn.commit()

            # Debugging: Log inserted data and SELECT query conditions
            for it in items:
                civ_id = (it.get(dedupe_on) or "").strip()
                if not civ_id:
                    continue  # Skip items with empty dedupe_on key
                logger.debug(f"Inserting civitai_id: {civ_id}")
                cur.execute("SELECT civitai_id FROM civitai_prompts")
                all_ids = cur.fetchall()
                logger.debug(f"Database civitai_ids with types: {[(row[0], type(row[0])) for row in all_ids]}")
                logger.debug(f"Querying for civitai_id: {civ_id} (type: {type(civ_id)})")

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            conn.close()

    def collect_for_models(self, models: Dict[str, Optional[str]], max_per_model: int = 5000):
        """
        v8 の collect_for_models が存在すればそれを優先して実行。
        なければ既存の個別保存フローで処理する。
        """
        # v8 による完全実装がある場合はそれを呼び出して終了
        if self._v8 is not None and hasattr(self._v8, "collect_for_models"):
            return self._v8.collect_for_models(models, max_per_model=max_per_model)

        # フォールバック（既存ロジック）
        results = {}
        for name, model_id in models.items():
            items = []
            if self._v8 is not None:
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

    def _fetch_page_via_playwright(self, url: str, wait_for: int = 5) -> str:
        """
        Playwright フォールバック: headless でページをレンダリングして HTML を返す。
        Playwright が未インストールの場合は空文字を返す。
        """
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            logger.debug("playwright not available")
            return ""
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
                page = browser.new_page()
                page.goto(url, timeout=30000)
                page.wait_for_timeout(wait_for * 1000)
                html = page.content()
                browser.close()
            return html
        except Exception as e:
            logger.warning(f"playwright fetch failed: {e}")
            return ""

    def _extract_embedded_json(self, html: str):
        import re, json
        if not html:
            return None
        m = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.S)
        js = m.group(1) if m else None
        if not js:
            m2 = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html, re.S)
            js = m2.group(1) if m2 else None
        if not js:
            return None
        try:
            return json.loads(js)
        except Exception:
            return None

    def _find_prompt_items(self, obj):
        results = []
        if isinstance(obj, dict):
            keys_l = {k.lower(): k for k in obj.keys()}
            if any(k in keys_l for k in ("fullprompt", "full_prompt", "prompt", "text", "body")):
                full = obj.get("fullPrompt") or obj.get("full_prompt") or obj.get("prompt") or obj.get("text") or obj.get("body") or ""
                neg = obj.get("negativePrompt") or obj.get("negative_prompt") or obj.get("negative") or ""
                civ_id = str(obj.get("id") or obj.get("postId") or obj.get("civitaiId") or obj.get("versionId") or "")
                meta = {k: v for k, v in obj.items() if k not in ("fullPrompt","full_prompt","prompt","text","body","negativePrompt","negative_prompt","negative")}
                results.append({
                    "civitai_id": civ_id,
                    "full_prompt": full,
                    "negative_prompt": neg,
                    "raw_metadata": meta
                })
            for v in obj.values():
                results.extend(self._find_prompt_items(v))
        elif isinstance(obj, list):
            for it in obj:
                results.extend(self._find_prompt_items(it))
        return results

    def _fetch_modelversion_via_trpc(self, session, version_id: int):
        import json
        url = f"https://civitai.com/api/trpc/modelVersion.getById?input={{%22json%22:%7B%22id%22:{version_id}%7D%7D}}"
        try:
            r = session.get(url, headers=self._get_headers(), timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return None
        # unwrap common tRPC envelope
        try:
            if isinstance(data, dict) and "result" in data:
                d = data["result"].get("data") or data["result"]
                if isinstance(d, dict) and "json" in d:
                    return d["json"]
                return d
        except Exception:
            pass
        return data

    def _fetch_images_for_version_via_trpc(self, session, version_id: int, limit: int = 50):
        import json, urllib.parse
        url_base = "https://civitai.com/api/trpc/image.getInfinite"
        payload = {
            "json": {
                "modelVersionId": version_id,
                "prioritizedUserIds": [],
                "period": "AllTime",
                "sort": "Most Reactions",
                "limit": limit,
                "pending": True,
                "include": [],
                "withMeta": False,
                "excludedTagIds": [],
                "disablePoi": True,
                "disableMinor": True,
                # cursor に null を送るとサーバーが拒否するため "undefined" を使う
                "cursor": "undefined"
            }
        }
        q = urllib.parse.quote(json.dumps(payload, separators=(",", ":")))
        url = f"{url_base}?input={q}"
        try:
            r = session.get(url, headers=self._get_headers(), timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return None
        # unwrap tRPC envelope
        try:
            if isinstance(data, dict) and "result" in data:
                d = data["result"].get("data") or data["result"]
                if isinstance(d, dict) and "json" in d:
                    return d["json"]
                return d
        except Exception:
            pass
        return data

    def _extract_prompts_from_image_payload(self, payload):
        """
        payload は list|dict など。返ってくる形式は配列のリスト [user, id, prompt, ...] の可能性があるので
        それらを探してプロンプト文字列を抽出して {civitai_id, full_prompt, negative_prompt, raw_metadata} のリストを返す。
        """
        results = []
        # list of lists (legacy capture)
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, list) and len(item) >= 3:
                    civ_id = item[1] or ""
                    prompt = item[2] or ""
                    if isinstance(prompt, str) and prompt.strip():
                        results.append({
                            "civitai_id": str(civ_id),
                            "full_prompt": prompt,
                            "negative_prompt": "",
                            "raw_metadata": {"source": "image.getInfinite", "raw": item}
                        })
                elif isinstance(item, dict):
                    # object form
                    prompt = item.get("prompt") or item.get("fullPrompt") or item.get("text") or ""
                    civ_id = item.get("id") or item.get("imageId") or ""
                    if isinstance(prompt, str) and prompt.strip():
                        results.append({
                            "civitai_id": str(civ_id),
                            "full_prompt": prompt,
                            "negative_prompt": "",
                            "raw_metadata": item
                        })
        elif isinstance(payload, dict):
            # try common keys
            # payload might contain items/list/rows
            for k in ("items", "rows", "data", "images", "results"):
                v = payload.get(k)
                if v:
                    results.extend(self._extract_prompts_from_image_payload(v))
            # or payload itself holds prompt fields
            prompt = payload.get("prompt") or payload.get("fullPrompt") or payload.get("text")
            if prompt:
                civ_id = payload.get("id") or payload.get("imageId") or ""
                results.append({
                    "civitai_id": str(civ_id),
                    "full_prompt": prompt,
                    "negative_prompt": "",
                    "raw_metadata": payload
                })
        return results

    def _handle_html_fallback(self, url: str, session) -> Optional[Dict[str, Any]]:
        """Handle fallback to extract JSON from HTML."""
        html = ""
        try:
            r2 = session.get(url, headers=self._get_headers(), timeout=self.timeout)
            html = r2.text if r2.ok else ""
        except Exception:
            html = ""

        if not html:
            html = self._fetch_page_via_playwright(url)

        if html:
            return self._extract_embedded_json(html)
        return None

    def _handle_trpc_fallback(self, url: str, session, version_id: int) -> Optional[Dict[str, Any]]:
        """Handle fallback using tRPC endpoints."""
        parsed = self._fetch_modelversion_via_trpc(session, version_id)
        if not parsed:
            try:
                img_payload = self._fetch_images_for_version_via_trpc(session, version_id, limit=50)
                if img_payload:
                    return self._extract_prompts_from_image_payload(img_payload)
            except Exception as e2:
                logger.debug(f"[fetch_prompts] image.getInfinite fallback failed: {e2}")
        return parsed
