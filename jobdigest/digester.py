import datetime
import re

from .models import Job


def _tokens(text: str) -> set[str]:
    return {t for t in re.sub(r"[^a-z0-9]+", " ", text.lower()).split() if len(t) >= 3}


def _bonus(text: str, terms: list[str]) -> int:
    return sum(1 for t in terms if t in text)


def _strong_match(title: str, body: str, keywords_l: list[str],
                  skills_l: list[str]) -> bool:
    """Require a real signal — keyword phrase/substring in title, a keyword
    phrase in the body, or a 2+ keyword-token overlap in the title."""
    title_toks = _tokens(title)
    kw_toks = {t for s in keywords_l for t in s.split() if len(t) >= 3}
    sk_toks = {t for s in skills_l for t in s.split() if len(t) >= 3}

    if any(k in title for k in keywords_l):
        return True
    if title_toks & kw_toks:
        return True
    if len(title_toks & sk_toks) >= 2:
        return True
    if any(k in body for k in keywords_l):
        return True
    return False


def _dedupe_tail(title: str) -> str:
    return title.lower().split("-")[0].strip()


def filter_and_rank(jobs: list[Job], keywords: list[str], skills: list[str],
                    locations: list[str],
                    today: datetime.date | None = None) -> list[Job]:
    today = today or datetime.date.today()
    keywords_l = [k.lower() for k in keywords if k]
    skills_l = [s.lower() for s in skills if s]
    locations_l = [loc.lower() for loc in locations if loc]

    scored = []
    seen_by_key = {}
    seen_by_tail = {}
    for job in jobs:
        title = job.title.lower()
        body = f"{job.snippet} {job.company} {job.location}".lower()
        text = f"{title} {body}"

        k_title = _bonus(title, keywords_l)
        k_body = _bonus(body, keywords_l)
        s_title = _bonus(title, skills_l)
        s_body = _bonus(body, skills_l)

        if not _strong_match(title, body, keywords_l, skills_l):
            continue
        if not (k_title or k_body or s_title):
            continue

        job.score = k_title * 3 + k_body + s_title * 2 + s_body

        if job.location:
            loc_text = job.location.lower()
            if any(l in loc_text for l in locations_l) or any(
                w in loc_text for w in ("remote", "online", "home based", "flexible")
            ):
                job.score += 2
            else:
                continue

        dedupe_key = job.key
        if dedupe_key in seen_by_key:
            existing = seen_by_key[dedupe_key]
            if existing.score < job.score:
                dedupe_key_use(job, existing, scored)
            continue

        tail_key = (job.source, job.company.lower(), _dedupe_tail(job.title))
        if tail_key in seen_by_tail:
            existing = seen_by_tail[tail_key]
            if existing.score < job.score and existing.source == job.source:
                dedupe_key_use(job, existing, scored)
            continue

        seen_by_key[dedupe_key] = job
        seen_by_tail[tail_key] = job
        scored.append(job)

    scored.sort(
        key=lambda j: (
            j.posted_date is None,
            -(today - j.posted_date).days if j.posted_date else 0,
            -j.score,
        )
    )
    return scored


def dedupe_key_use(job: Job, existing: Job, scored: list[Job]) -> None:
    idx = scored.index(existing)
    scored[idx] = job