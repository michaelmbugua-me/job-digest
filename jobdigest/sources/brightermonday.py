import datetime
import json
import re

import requests
from bs4 import BeautifulSoup

from ..models import Job
from .utils import select_for_enrich, strip_html

BASE = "https://www.brightermonday.co.ke"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

SOURCE_NAME = "BrighterMonday"
SLUG_RE = re.compile(r'rel="prerender" href="[^"]*?/listings/([a-z0-9-]+)"')
DEFAULT_LISTS = [
    "/jobs",
    "/jobs/nairobi",
    "/jobs/community-social-services",
    "/jobs/product-project-management",
    "/jobs/research-teaching-training",
    "/jobs/software-data",
]
ENRICH_CAP = 25


def _clean_title(slug: str) -> str:
    parts = slug.split("-")
    if parts and 5 <= len(parts[-1]) <= 8 and re.search(r"\d", parts[-1]):
        parts = parts[:-1]
    return " ".join(parts)


def _collect_links(session: requests.Session, lists: list[str],
                   pages: int) -> list[str]:
    links = []
    for path in lists:
        for page_num in range(1, pages + 1):
            url = f"{BASE}{path}"
            if page_num > 1:
                url = f"{url}?page={page_num}"
            try:
                resp = session.get(url, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                links.extend(SLUG_RE.findall(resp.text.replace("\n", " ")))
            except requests.RequestException as exc:
                if page_num == 1:
                    print(f"[brightermonday] list {path} failed: {exc}")
                break
    return list(dict.fromkeys(links))


def _enrich(slug: str, session: requests.Session, today) -> Job | None:
    url = f"{BASE}/listings/{slug}"
    try:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[brightermonday] detail {slug} failed: {exc}")
        return None

    page = BeautifulSoup(resp.text, "html.parser")
    script = page.find("script", type="application/ld+json")
    if script is None:
        return None
    try:
        data = json.loads(script.get_text())
    except (ValueError, TypeError):
        return None

    nodes = data.get("@graph", []) if isinstance(data, dict) else []
    posting = next((n for n in nodes if n.get("@type") == "JobPosting"), None)
    if not posting:
        return None

    orgs = {n.get("@id"): n.get("name") for n in nodes if n.get("@type") == "Organization"}
    company = orgs.get((posting.get("hiringOrganization") or {}).get("@id"), "")

    loc_parts = []
    loc = (posting.get("jobLocation") or {}).get("address", {})
    for key in ("addressLocality", "addressRegion", "addressCountry"):
        if loc.get(key):
            loc_parts.append(loc[key])

    posted_date = None
    d = (posting.get("datePosted") or "")[:10]
    if d:
        posted_date = datetime.date.fromisoformat(d)

    deadline = posting.get("validThrough")
    deadline_str = ""
    if deadline:
        try:
            deadline_str = datetime.date.fromisoformat(deadline[:10]).strftime("%d %b %Y")
        except ValueError:
            deadline_str = str(deadline)[:10]

    return Job(
        title=posting.get("title", _clean_title(slug)),
        url=url,
        company=company,
        location=", ".join(loc_parts) or "",
        posted=d or "",
        posted_date=posted_date,
        deadline=deadline_str,
        snippet=strip_html(posting.get("description", ""), 300),
        source=SOURCE_NAME,
    )


def fetch(keywords: list[str], skills: list[str],
          session: requests.Session, today=None, lists=None, pages=2) -> list[Job]:
    today = today or datetime.date.today()
    lists = lists or DEFAULT_LISTS

    slugs = _collect_links(session, lists, pages)
    candidates = [Job(title=_clean_title(s), url="", source=SOURCE_NAME) for s in slugs]
    selected = select_for_enrich(candidates, keywords, skills, ENRICH_CAP)
    print(f"[brightermonday] {len(slugs)} slugs, {len(selected)} picked for enrichment")

    slug_map = {j.title: s for s, j in zip(slugs, candidates)}
    jobs = []
    for job in selected:
        slug = slug_map.get(job.title)
        if not slug:
            continue
        enriched = _enrich(slug, session, today)
        if enriched:
            jobs.append(enriched)
    return jobs