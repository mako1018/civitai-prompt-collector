import os

DB_DEFAULT = "civitai_dataset.db"
CIVITAI_API_ENV = "CIVITAI_API_KEY"

# 6カテゴリの辞書（例）
CATEGORIES = {
    "nsfw": ["nsfw", "adult"],
    "style": ["photorealistic", "anime", "cartoon"],
    "lighting": ["sunset", "studio lighting", "soft light"],
    "composition": ["close up", "wide angle", "rule of thirds"],
    "mood": ["happy", "sad", "mysterious"],
    "technical": ["high detail", "4k", "sharp"]
}
