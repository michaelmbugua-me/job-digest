import html as html_lib
import re

from ..models import Job


def strip_html(text: str, limit: int = 0) -> str:
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"</p>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def _bonus(text_norm: str, phrase: str) -> int:
    p = re.sub(r"[^a-z0-9]+", " ", phrase.lower()).strip()
    if not p:
        return 0
    if p in text_norm:
        return 2
    toks = [t for t in p.split() if len(t) >= 3]
    words = set(text_norm.split())
    return sum(1 for t in toks if t in words)


def select_for_enrich(jobs: list[Job], keywords: list[str], skills: list[str],
                      cap: int) -> list[Job]:
    """Rank candidates by title-match strength and return the top `cap`."""
    keys = list(dict.fromkeys(k for k in list(keywords) + list(skills) if k))

    def score(idx: int, job: Job) -> tuple:
        norm = _norm(job.title)
        s = 0
        hit = False
        for k in keys:
            b = _bonus(norm, k)
            if b == 2:
                hit = True
            s += b
        return (hit, s, idx)

    ranked = [score(i, j) for i, j in enumerate(jobs)]
    ranked.sort(key=lambda x: (-x[1], x[2]))  # only relevant, strongest first
    return [jobs[i] for hit, s, i in ranked if hit][:cap]