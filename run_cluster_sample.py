from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from collector.categorizer import categorize_prompts_batch

samples = [
    "A photo of a smiling woman in studio lighting",
    "anime style character with big eyes",
    "nude explicit content",
    "portrait with dramatic lighting and intricate details",
    "cartoonish character, bright colors, big eyes"
]

res = categorize_prompts_batch(samples, use_clustering=True, min_cluster_size=1)
print("cluster_info:", res.get("clusters", {}).get("cluster_info"))
print("summaries:", res.get("summaries"))