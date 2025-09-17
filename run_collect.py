from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
SRC = str(ROOT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from collector import CivitaiPromptCollector

c = CivitaiPromptCollector(db_path="test_collect.db")
print(c.collect_for_models({"test": None}, max_per_model=1))
