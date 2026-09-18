import datetime

import requests

from ..models import Job
from .utils import is_likely_english, strip_html

API = "https://jobicy.com/api/v2/remote-jobs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "Jobicy"
DEFAULT_QUERY = "angular"


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None,
          query: str = DEFAULT_QUERY, count: int = 50) -> list[Job]:
    today = today or datetime.date.today()
    jobs = []

    try:
        resp = session.get(
            API,
            params={"tag": query, "count": count},
            headers=HEADERS, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print(f"[jobicy] failed: {exc}")
        return []
    except ValueError:
        return []

    for row in data.get("jobs") or []:
        geo = (row.get("jobGeo") or "Anywhere").strip() or "Anywhere"
        snippet = strip_html(row.get("jobDescription", ""), 260)

        full = f"{row.get('jobTitle', '')} {strip_html(row.get('jobDescription', ''), 600)}".lower()
        if query.lower() not in full or not is_likely_english(f"{row.get('jobTitle', '')} {snippet}"):
            continue

        pub = str(row.get("pubDate", "") or "")
        posted_date = None
        if len(pub) >= 10:
            try:
                posted_date = datetime.date.fromisoformat(pub[:10])
            except ValueError:
                posted_date = None

        jobs.append(
            Job(
                title=row.get("jobTitle", "").strip(),
                url=row.get("url", ""),
                company=row.get("companyName", "").strip(),
                location=f"Remote — {geo}",
                posted=pub[:10] if posted_date else "",
                posted_date=posted_date,
                snippet=snippet,
                source=SOURCE_NAME,
            )
        )

    print(f"[jobicy] {len(jobs)} jobs for tag={query!r}")
    return jobs