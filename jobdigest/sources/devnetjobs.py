import re

import requests
from bs4 import BeautifulSoup

from ..models import Job

BASE = "https://devnetjobs.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "DevNetJobs"


def _location(span) -> str:
    text = span.get_text(" ", strip=True) if span else ""
    m = re.search(r"Location:\s*(.+)", text, re.I)
    return m.group(1).strip() if m else ""


def _parse(page: BeautifulSoup, seen: set) -> list[Job]:
    jobs = []
    for anchor in page.select("a[href*='jobdescription.aspx']"):
        url = anchor.get("href", "").strip()
        if url in seen:
            continue
        seen.add(url)

        title_el = anchor.select_one("span[id$='lblJobTitle']")
        company_el = anchor.select_one("span[id$='lblJobCo']")
        location_el = anchor.select_one("span[id$='lblLocation']")
        apply_el = anchor.select_one("span[id$='lblApplyDate']")

        title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            continue

        jobs.append(
            Job(
                title=title,
                url=url,
                company=company_el.get_text(" ", strip=True) if company_el else "",
                location=_location(location_el),
                posted=apply_el.get_text(" ", strip=True) if apply_el else "",
                source=SOURCE_NAME,
            )
        )
    return jobs


def fetch(keywords: list[str], session: requests.Session) -> list[Job]:
    try:
        resp = session.get(f"{BASE}/standard_jobs.aspx", headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[devnetjobs] failed: {exc}")
        return []

    html = resp.text
    page = BeautifulSoup(html, "html.parser")
    return _parse(page, set())