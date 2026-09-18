import datetime
import os

import requests

from ..models import Job
from .utils import is_likely_english, strip_html

API = "https://api.adzuna.com/v1/api/jobs/int/search/{page}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "Adzuna"
DEFAULT_QUERY = "angular"
REMOTE_HINTS = ("remote", "anywhere", "worldwide", "global", "working from home")


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None,
          query: str = DEFAULT_QUERY, max_days_old: int = 14,
          results_per_page: int = 40, pages: int = 1) -> list[Job]:
    today = today or datetime.date.today()

    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        print("[adzuna] skipped — set ADZUNA_APP_ID and ADZUNA_APP_KEY env vars")
        return []

    jobs = []
    for page in range(1, pages + 1):
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "results_per_page": results_per_page,
            "max_days_old": max_days_old,
            "sort_by": "date",
            "content-type": "application/json",
        }
        try:
            resp = session.get(API.format(page=page), params=params,
                               headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            print(f"[adzuna] page {page} failed: {exc}")
            if page == 1:
                return []
            break
        except ValueError:
            return []

        for row in data.get("results") or []:
            location = ", ".join((row.get("location") or {}).get("area") or [])
            description = row.get("description", "")
            desc_head = strip_html(description, 600).lower()
            title = row.get("title", "").strip()

            remote = any(w in location.lower() for w in REMOTE_HINTS) or (
                "remote" in desc_head or "work from home" in desc_head or
                "work-from-home" in desc_head
            )
            if not remote:
                continue
            if query.lower() not in f"{title} {desc_head}".lower():
                continue

            snippet = strip_html(description, 260)
            if not is_likely_english(f"{title} {snippet}"):
                continue

            created = str(row.get("created", "") or "")
            posted_date = None
            if len(created) >= 10:
                try:
                    posted_date = datetime.date.fromisoformat(created[:10])
                except ValueError:
                    posted_date = None

            jobs.append(
                Job(
                    title=title,
                    url=row.get("redirect_url", ""),
                    company=(row.get("company") or {}).get("display_name", "").strip(),
                    location=f"Remote — {location}" if location else "Remote — Anywhere",
                    posted=created[:10] if posted_date else "",
                    posted_date=posted_date,
                    snippet=snippet,
                    source=SOURCE_NAME,
                )
            )

    print(f"[adzuna] {len(jobs)} remote jobs for query={query!r}")
    return jobs