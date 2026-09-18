import requests
from bs4 import BeautifulSoup

from ..dates import parse_posted_date
from ..models import Job

BASE = "https://www.myjobmag.co.ke"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "MyJobMag"
LISTING_PAGES = 5


def _parse(page: BeautifulSoup, seen: set, today) -> list[Job]:
    jobs = []
    for li in page.select("li.job-list-li"):
        anchor = li.select_one("h2 a[href]")
        if anchor is None:
            continue
        rel = anchor.get("href", "")
        if not rel.startswith("/job/"):
            continue
        url = BASE + rel
        url_key = url.split("?")[0]
        if url_key in seen:
            continue
        seen.add(url_key)
        desc = li.select_one("li.job-desc")
        date_li = li.select_one("#job-date")
        dated = date_li.get_text(" ", strip=True) if date_li else ""
        jobs.append(
            Job(
                title=anchor.get_text(" ", strip=True),
                url=url,
                snippet=desc.get_text(" ", strip=True) if desc else "",
                posted=dated,
                posted_date=parse_posted_date(dated, today),
                source=SOURCE_NAME,
            )
        )
    return jobs


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None) -> list[Job]:
    today = today or __import__("datetime").date.today()
    jobs = []
    seen = set()

    for page_num in range(1, LISTING_PAGES + 1):
        url = f"{BASE}/jobs"
        if page_num > 1:
            url = f"{BASE}/jobs/page/{page_num}"
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            jobs.extend(_parse(BeautifulSoup(resp.text, "html.parser"), seen, today))
        except requests.RequestException as exc:
            if page_num == 1:
                print(f"[myjobmag] listings failed: {exc}")
            break

    for kw in keywords:
        try:
            resp = session.get(
                f"{BASE}/search/jobs", params={"q": kw}, headers=HEADERS, timeout=30
            )
            resp.raise_for_status()
            jobs.extend(_parse(BeautifulSoup(resp.text, "html.parser"), seen, today))
        except requests.RequestException as exc:
            print(f"[myjobmag] search '{kw}' failed: {exc}")

    return jobs