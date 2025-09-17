import os
import sys
from pathlib import Path
import sqlite3

# Add the `src` directory to the Python module search path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Explicitly print the paths for debugging
print("sys.path:", sys.path)
print("src_path:", src_path)

import cProfile
import pstats
from io import StringIO
from src.collector.db import save_prompt as save_to_db

def profile_save_to_db():
    profiler = cProfile.Profile()
    profiler.enable()

    conn = sqlite3.connect('civitai_dataset.db')
    example_data_list = [
        {"id": i, "model_id": f"example_model_{i}", "prompt": f"This is test prompt {i}", "collected_at": "2025-09-17 12:00:00"}
        for i in range(1, 101)
    ]

    # Batch insert to optimize performance
    conn.executemany(
        "INSERT OR REPLACE INTO civitai_prompts (id, model_id, full_prompt, collected_at) VALUES (?, ?, ?, ?)",
        [(data["id"], data["model_id"], data["prompt"], data["collected_at"]) for data in example_data_list]
    )
    conn.commit()
    conn.close()

    profiler.disable()
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats()
    print(s.getvalue())

if __name__ == "__main__":
    profile_save_to_db()
