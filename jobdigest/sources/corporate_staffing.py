import datetime

import requests
from bs4 import BeautifulSoup

from ..dates import parse_posted_date
from ..models import Job
from .utils import strip_html

BASE = "https://www.corporatestaffing.co.ke"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "Corporate Staffing"
MAX_PAGES = 3


def _parse(page: BeautifulSoup, seen: set, today) -> list[Job]:
    jobs = []
    for wrap in page.select(".entry-content-wrap, article"):
        header = wrap.select_one("h2.entry-title a[href]")
        if header is None:
            continue
        url = header.get("href", "").strip()
        if "/job/" not in url or url in seen:
            continue
        seen.add(url)

        time_el = wrap.select_one("time.published[datetime]") or wrap.select_one(
            "time[datetime]"
        )
        posted_date = None
        dated = ""
        if time_el:
            dt = time_el.get("datetime", "")
            dated = time_el.get_text(" ", strip=True)
            try:
                iso = dt.split("T")[0]
                posted_date = datetime.date.fromisoformat(iso)
            except ValueError:
                posted_date = parse_posted_date(dt, today)

        summary = wrap.select_one(".entry-summary")
        snippet = strip_html(str(summary), 300) if summary else ""

        jobs.append(
            Job(
                title=header.get_text(" ", strip=True),
                url=url,
                snippet=snippet,
                posted=dated,
                posted_date=posted_date,
                source=SOURCE_NAME,
            )
        )
    return jobs


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None) -> list[Job]:
    today = today or datetime.date.today()
    jobs = []
    seen = set()

    for page_num in range(1, MAX_PAGES + 1):
        url = f"{BASE}/jobs/"
        if page_num > 1:
            url = f"{BASE}/jobs/page/{page_num}/"
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            jobs.extend(_parse(BeautifulSoup(resp.text, "html.parser"), seen, today))
        except requests.RequestException as exc:
            if page_num == 1:
                print(f"[corporate_staffing] failed: {exc}")
            break

    return jobs