import requests
from bs4 import BeautifulSoup

from ..models import Job

BASE = "https://www.corporatestaffing.co.ke"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "Corporate Staffing"
MAX_PAGES = 3


def _parse(page: BeautifulSoup, seen: set) -> list[Job]:
    jobs = []
    for h2 in page.select("h2.entry-title"):
        anchor = h2.select_one("a[href]")
        if anchor is None:
            continue
        url = anchor.get("href", "").strip()
        if "/job/" not in url or url in seen:
            continue
        seen.add(url)
        jobs.append(
            Job(
                title=anchor.get_text(" ", strip=True),
                url=url,
                source=SOURCE_NAME,
            )
        )
    return jobs


def fetch(keywords: list[str], session: requests.Session) -> list[Job]:
    jobs = []
    seen = set()

    for page_num in range(1, MAX_PAGES + 1):
        url = f"{BASE}/jobs/"
        if page_num > 1:
            url = f"{BASE}/jobs/page/{page_num}/"
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            jobs.extend(_parse(BeautifulSoup(resp.text, "html.parser"), seen))
        except requests.RequestException as exc:
            if page_num == 1:
                print(f"[corporate_staffing] failed: {exc}")
            break

    return jobs