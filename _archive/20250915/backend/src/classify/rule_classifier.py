import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
EXPORT_DIR = BASE_DIR / "data" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = {
    "NSFW": ["nsfw", "nude", "nudity", "explicit"],
    "style": ["anime", "watercolor", "oil painting", "sketch", "cyberpunk", "baroque"],
    "lighting": ["rim light", "backlight", "volumetric", "hdr lighting", "ambient light"],
    "composition": ["rule of thirds", "close-up", "wide shot", "portrait", "landscape"],
    "mood": ["melancholic", "dark", "vibrant", "dreamy", "energetic", "tranquil"],
    "technical": ["8k", "hdr", "ultra-detailed", "depth of field", "dof", "photorealistic", "highres"]
}

def score_prompt(prompt: str):
    text = prompt.lower()
    scores = defaultdict(float)
    matched = set()
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if kw in text:
                scores[cat] += 1.0
                matched.add(cat)
    if not matched:
        matched.add("basic")
        scores["basic"] = 1.0
    return list(matched), scores

def load_latest_raw():
    files = sorted(RAW_DIR.glob("prompts_*.json"))
    if not files:
        raise FileNotFoundError("raw データがありません。collector を先に実行。")
    return files[-1]

def main():
    latest = load_latest_raw()
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)

    output = []
    for rec in data:
        cats, cat_scores = score_prompt(rec.get("prompt", ""))
        output.append({
            "id": rec.get("id"),
            "prompt": rec.get("prompt"),
            "categories": cats,
            "scores": cat_scores,
            "meta": rec.get("meta", {})
        })

    out_file = EXPORT_DIR / "categorized_prompts.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Exported:", out_file, f"({len(output)} records)")

if __name__ == "__main__":
    main()