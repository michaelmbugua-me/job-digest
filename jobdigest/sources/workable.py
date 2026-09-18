import datetime

import requests

from ..models import Job
from .utils import strip_html

API = "https://apply.workable.com/api/v1/widget/accounts/{slug}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "Workable"

DEFAULT_ACCOUNTS = [
    ("burn-manufacturing", "BURN Manufacturing"),
    ("cifor-icraf", "CIFOR-ICRAF"),
    ("ecolife-conservation", "ECOLIFE Conservation"),
    ("one-acre-fund", "One Acre Fund"),
    ("mercy-corps", "Mercy Corps"),
    ("the-nature-conservancy", "The Nature Conservancy"),
    ("african-wildlife-foundation", "African Wildlife Foundation"),
    ("international-rescue-committee", "International Rescue Committee"),
    ("creative-associates-international", "Creative Associates International"),
]


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None,
          accounts: list[tuple[str, str]] | None = None) -> list[Job]:
    today = today or datetime.date.today()
    accounts = accounts or DEFAULT_ACCOUNTS
    jobs = []

    for slug, name in accounts:
        try:
            resp = session.get(API.format(slug=slug), params={"details": "true"},
                               headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            print(f"[workable] {slug} failed: {exc}")
            continue
        except ValueError:
            continue

        for row in (data.get("jobs") or []):
            location = ", ".join(x for x in [
                row.get("city"), row.get("state"), row.get("country")
            ] if x)
            posted = row.get("published_on", "")
            posted_date = None
            if posted:
                try:
                    posted_date = datetime.date.fromisoformat(posted[:10])
                except ValueError:
                    posted_date = None

            jobs.append(
                Job(
                    title=row.get("title", "").strip(),
                    url=row.get("url") or row.get("application_url") or "",
                    company=name,
                    location=location,
                    posted=posted,
                    posted_date=posted_date,
                    snippet=strip_html(row.get("description", ""), 300),
                    source=SOURCE_NAME,
                )
            )

    print(f"[workable] {len(jobs)} jobs from {len(accounts)} accounts")
    return jobs