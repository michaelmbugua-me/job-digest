import datetime

import requests

from ..models import Job
from .utils import strip_html

API = "https://remotive.com/api/remote-jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "Remotive"
DEFAULT_QUERY = "angular"


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None,
          query: str = DEFAULT_QUERY, pages: int = 1) -> list[Job]:
    today = today or datetime.date.today()
    jobs = []

    for page in range(1, pages + 1):
        try:
            resp = session.get(
                API,
                params={"search": query, "limit": 100, "page": page},
                headers=HEADERS, timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            print(f"[remotive] page {page} failed: {exc}")
            if page == 1:
                return []
            break
        except ValueError:
            break

        for row in data.get("jobs") or []:
            location = (row.get("candidate_required_location") or "Anywhere").strip()
            tags = row.get("tags") or []
            snippet = strip_html(row.get("description", ""), 260)
            if tags:
                snippet += " | tags: " + ", ".join(tags)

            full = f"{row.get('title', '')} {strip_html(row.get('description', ''), 600)}".lower()
            if query.lower() not in full:
                continue

            posted = str(row.get("publication_date", "") or "")
            posted_date = None
            if len(posted) >= 10:
                try:
                    posted_date = datetime.date.fromisoformat(posted[:10])
                except ValueError:
                    posted_date = None

            jobs.append(
                Job(
                    title=row.get("title", "").strip(),
                    url=row.get("url", ""),
                    company=row.get("company_name", "").strip(),
                    location=f"Remote — {location}",
                    posted=posted[:10] if posted_date else "",
                    posted_date=posted_date,
                    snippet=snippet,
                    source=SOURCE_NAME,
                )
            )

    print(f"[remotive] {len(jobs)} jobs for query={query!r}")
    return jobs