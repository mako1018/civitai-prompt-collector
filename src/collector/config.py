import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートの .env をロード（無ければ何もしない）
ROOT = Path(__file__).resolve().parents[2]
env_path = ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DB_DEFAULT = "civitai_dataset.db"
CIVITAI_API_ENV = "CIVITAI_API_KEY"

CATEGORIES = {
    "nsfw": ["nsfw", "adult"],
    "style": ["photorealistic", "anime", "cartoon"],
    "lighting": ["sunset", "studio lighting", "soft light"],
    "composition": ["close up", "wide angle", "rule of thirds"],
    "mood": ["happy", "sad", "mysterious"],
    "technical": ["high detail", "4k", "sharp"]
}
