#!/usr/bin/env python3
"""
Minimal collector skeleton.

Current status:
- Generates dummy records instead of calling a real API.
- Supports basic CLI arguments (--limit, --output, --format, --log-level, --strip-html, --page-start).
- Saves data as JSONL (default) or JSON.
- Can optionally strip simple HTML tags.
- Prints a simple execution summary.

Next steps after confirming this works:
1. Replace `fetch_dummy_data` with real API calls.
2. Add retry / rate limit control.
3. Add richer fields & duplication control.
"""

from __future__ import annotations
import argparse
import json
import logging
import os
import sys
import time
import datetime as dt
import re
from typing import List, Dict, Any

# ---------------------------
# Data fetching (dummy)
# ---------------------------

def fetch_dummy_data(limit: int, page_start: int) -> List[Dict[str, Any]]:
    """
    Simulate fetching `limit` items. Each item mimics a minimal record you might
    later get from a real API (id, text, created_at).
    page_start is included just to show how pagination might shift IDs.
    """
    base_id = (page_start - 1) * limit
    now_iso = dt.datetime.utcnow().isoformat() + "Z"
    records = []
    for i in range(limit):
        record_id = base_id + i + 1
        html_sample = f"<p>Hello <b>World {record_id}</b></p>"
        records.append(
            {
                "id": record_id,
                "text": html_sample,
                "created_at": now_iso,
                "source": "dummy",
            }
        )
    return records


# ---------------------------
# HTML stripping
# ---------------------------

TAG_RE = re.compile(r"<[^>]+>")

def strip_html(text: str) -> str:
    # Very naive HTML tag removal (sufficient for first milestone)
    return TAG_RE.sub("", text)


# ---------------------------
# Saving logic
# ---------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def save_jsonl(records: List[Dict[str, Any]], path: str) -> int:
    """
    Append records to a JSONL file. Returns number of lines written.
    """
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(records)

def save_json(records: List[Dict[str, Any]], path: str) -> int:
    """
    Overwrite JSON file with full list. Returns number of records written.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return len(records)

def count_jsonl_lines(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


# ---------------------------
# Core pipeline
# ---------------------------

def collect(args: argparse.Namespace) -> int:
    logger = logging.getLogger("collector")
    logger.debug(f"Args: {args}")

    ensure_dir(args.output)

    # 1. Fetch (dummy for now)
    logger.info(f"Fetching dummy data: limit={args.limit} page_start={args.page_start}")
    t0 = time.time()
    records = fetch_dummy_data(args.limit, args.page_start)

    # 2. Optional HTML strip
    if args.strip_html:
        for r in records:
            r["text"] = strip_html(r["text"])
        logger.info("Applied HTML stripping to text fields")

    # 3. Save
    if args.format == "jsonl":
        out_file = os.path.join(args.output, "data.jsonl")
        before = count_jsonl_lines(out_file)
        written = save_jsonl(records, out_file)
        after = before + written
        logger.info(f"Saved {written} records to {out_file} (lines before={before}, after={after})")
    else:
        out_file = os.path.join(args.output, "data.json")
        written = save_json(records, out_file)
        logger.info(f"Saved {written} records to {out_file} (JSON array)")

    # 4. Summary
    elapsed = time.time() - t0
    print(
        f"[SUMMARY] records={len(records)} format={args.format} "
        f"output={out_file} elapsed={elapsed:.2f}s"
    )

    return 0


# ---------------------------
# CLI
# ---------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Collect data (dummy implementation). Will be replaced with real API calls."
    )
    p.add_argument("--limit", type=int, default=5, help="Number of items to fetch (default: 5)")
    p.add_argument("--page-start", type=int, default=1, help="Starting page index (for future pagination)")
    p.add_argument(
        "--output",
        type=str,
        default="data",
        help="Output directory (created if absent) (default: data)",
    )
    p.add_argument(
        "--format",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Output format (default: jsonl)",
    )
    p.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging verbosity (default: info)",
    )
    p.add_argument(
        "--strip-html",
        action="store_true",
        help="Remove simple HTML tags from text fields",
    )
    return p


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    setup_logging(args.log_level)
    try:
        return collect(args)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as e:
        logging.exception("Unhandled error")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())