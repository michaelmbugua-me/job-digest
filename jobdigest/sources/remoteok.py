import datetime

import requests

from ..models import Job
from .utils import strip_html

API = "https://remoteok.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "RemoteOK"
DEFAULT_QUERY = "angular"


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None,
          query: str = DEFAULT_QUERY) -> list[Job]:
    today = today or datetime.date.today()
    jobs = []

    try:
        resp = session.get(API, params={"tags": query}, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print(f"[remoteok] failed: {exc}")
        return []
    except ValueError:
        return []

    rows = data[1:] if isinstance(data, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        location = (row.get("location") or "Anywhere").strip() or "Anywhere"
        tags = row.get("tags") or []
        snippet = strip_html(row.get("description", ""), 260)
        if tags:
            snippet += " | tags: " + ", ".join(tags)

        full = f"{row.get('position', '')} {strip_html(row.get('description', ''), 600)}".lower()
        if query.lower() not in full:
            continue

        ts = row.get("date") or 0
        posted_date = None
        if isinstance(ts, (int, float)) and ts > 0:
            try:
                posted_date = datetime.date.fromtimestamp(ts)
            except (OverflowError, OSError, ValueError):
                posted_date = None
        elif isinstance(ts, str) and len(ts) >= 10:
            try:
                posted_date = datetime.date.fromisoformat(ts[:10])
            except ValueError:
                posted_date = None

        jobs.append(
            Job(
                title=row.get("position", "").strip(),
                url=row.get("url", ""),
                company=row.get("company", "").strip(),
                location=f"Remote — {location}",
                posted=posted_date.isoformat() if posted_date else "",
                posted_date=posted_date,
                snippet=snippet,
                source=SOURCE_NAME,
            )
        )

    print(f"[remoteok] {len(jobs)} jobs for tag={query!r}")
    return jobs