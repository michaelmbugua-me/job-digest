import json
import os
from datetime import datetime, timezone

STATE_FILE = ".digest_state.json"


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def already_sent_today() -> bool:
    """Return True if the digest was already sent today (UTC)."""
    if not os.path.exists(STATE_FILE):
        return False
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
        return data.get("last_sent") == _today_utc()
    except (json.JSONDecodeError, OSError):
        # Corrupt/unreadable state -> safer to send than to silently skip
        return False


def mark_sent_today() -> None:
    with open(STATE_FILE, "w") as f:
        json.dump({"last_sent": _today_utc()}, f)