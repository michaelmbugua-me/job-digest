import datetime
import re

import requests
from bs4 import BeautifulSoup

from ..dates import parse_posted_date
from ..models import Job
from .utils import select_for_enrich, strip_html

BASE = "https://devnetjobs.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "DevNetJobs"
ENRICH_CAP = 20


def _location(span) -> str:
    text = span.get_text(" ", strip=True) if span else ""
    m = re.search(r"Location:\s*(.+)", text, re.I)
    return m.group(1).strip() if m else ""


def _candidates(page: BeautifulSoup, seen: set) -> list[Job]:
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

        apply_text = apply_el.get_text(" ", strip=True) if apply_el else ""
        jobs.append(
            Job(
                title=title,
                url=url,
                company=company_el.get_text(" ", strip=True) if company_el else "",
                location=_location(location_el),
                deadline=apply_text,
                posted=apply_text,
                source=SOURCE_NAME,
            )
        )
    return jobs


def _enrich(job: Job, session: requests.Session, today) -> Job | None:
    try:
        resp = session.get(job.url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[devnetjobs] enrich failed: {exc}")
        return None

    text = resp.text

    m = re.search(r'"Posted"\s*:\s*"([\d-]+)"', text)
    if m:
        d = parse_posted_date(m.group(1), today)
        if d:
            job.posted_date = d
            job.posted = m.group(1)

    page = BeautifulSoup(text, "html.parser")
    body = page.select_one(".jobdescription, #ctl00_ContentPlaceHolder1, article")
    if body:
        job.snippet = strip_html(str(body), 300)
    return job


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None) -> list[Job]:
    today = today or datetime.date.today()

    try:
        resp = session.get(f"{BASE}/standard_jobs.aspx", headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[devnetjobs] failed: {exc}")
        return []

    page = BeautifulSoup(resp.text, "html.parser")
    candidates = _candidates(page, set())

    shortlisted = select_for_enrich(candidates, keywords, skills, ENRICH_CAP)
    print(f"[devnetjobs] {len(candidates)} candidates, "
          f"{len(shortlisted)} picked for enrichment")

    jobs = []
    for job in shortlisted[:ENRICH_CAP]:
        if _enrich(job, session, today):
            jobs.append(job)

    return jobs