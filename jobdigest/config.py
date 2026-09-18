import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(os.environ.get("JOB_DIGEST_CONFIG", ROOT / "config.json"))


def load_config() -> dict:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    data["recipient"] = os.environ.get("DIGEST_TO") or data["recipient"]
    return data


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value