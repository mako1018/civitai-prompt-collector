import logging, json, sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs/collector")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "run.log"

class JsonFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
            "name": record.name
        }
        if record.__dict__.get("extra_data"):
            base["extra"] = record.__dict__["extra_data"]
        return json.dumps(base, ensure_ascii=False)

def get_logger(name="collector"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(JsonFormatter())
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(JsonFormatter())
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger