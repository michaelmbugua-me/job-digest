import argparse
import datetime

import requests

from .config import load_config, require_env
from .digester import filter_and_rank
from .emailer import html_body, plain_text, send_email, today_str
from .sources import (
    brightermonday,
    corporate_staffing,
    devnetjobs,
    jobicy,
    myjobmag,
    remoteok,
    workable,
)

SOURCE_FETCHERS = {
    "myjobmag": myjobmag.fetch,
    "corporate_staffing": corporate_staffing.fetch,
    "devnetjobs": devnetjobs.fetch,
    "brightermonday": brightermonday.fetch,
    "workable": workable.fetch,
    "jobicy": jobicy.fetch,
    "remoteok": remoteok.fetch,
}

REMOTE_SOURCES = ("jobicy", "remoteok")


def collect(cfg: dict, keywords: list[str], skills: list[str]) -> list:
    session = requests.Session()
    today = datetime.date.today()
    jobs = []

    base_kwargs = {"keywords": keywords, "skills": skills, "session": session, "today": today}
    source_kwargs = {name: dict(base_kwargs) for name in SOURCE_FETCHERS}
    sources = list(cfg.get("sources", list(SOURCE_FETCHERS)))

    remote = cfg.get("remote") or {}
    if remote.get("enabled", False):
        query = remote.get("query", "angular")
        for name in REMOTE_SOURCES:
            source_kwargs[name]["query"] = query
            if name not in sources:
                sources.append(name)
        source_kwargs["jobicy"]["count"] = remote.get("count", 50)

    if "brightermonday" in cfg:
        source_kwargs["brightermonday"]["lists"] = cfg["brightermonday"].get("lists")
        source_kwargs["brightermonday"]["pages"] = cfg["brightermonday"].get("pages", 2)
    if "workable_accounts" in cfg:
        source_kwargs["workable"]["accounts"] = [
            tuple(a) for a in cfg["workable_accounts"]
        ]

    for name in sources:
        fetcher = SOURCE_FETCHERS.get(name)
        if not fetcher:
            continue
        kwargs = source_kwargs.get(name, base_kwargs)
        try:
            found = fetcher(**kwargs)
        except Exception as exc:  # one source must not kill the digest
            print(f"[{name}] error: {exc}")
            found = []
        jobs.extend(found)
        print(f"[{name}] kept {len(found)} enriched jobs")
    return jobs


def _is_remote(job) -> bool:
    if job.source in REMOTE_SOURCES:
        return True
    text = f"{job.source} {job.location}".lower()
    return any(w in text for w in ("remote", "anywhere", "worldwide", "global"))


def _sort_key(job, today: datetime.date) -> tuple:
    posted = job.posted_date
    return (
        posted is None,
        -(today - posted).days if posted else 0,
        -job.score,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily job digest for Kenya")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the digest instead of sending an email")
    parser.add_argument("--json", action="store_true",
                        help="print raw ranked jobs as JSON")
    args = parser.parse_args()

    cfg = load_config()
    keywords = cfg.get("keywords", [])
    if not keywords:
        raise SystemExit("No keywords in config.json")

    raw = collect(cfg, keywords, cfg.get("skills", []))
    ranked = filter_and_rank(
        raw,
        keywords,
        cfg.get("skills", []),
        cfg.get("locations", []),
    )
    max_results = cfg.get("max_results", 15)
    remote = cfg.get("remote") or {}
    remote_max = remote.get("max_results", max_results // 2) if remote.get("enabled") else 0

    remote_jobs = [j for j in ranked if _is_remote(j)]
    local_jobs = [j for j in ranked if not _is_remote(j)]
    picked = remote_jobs[:remote_max] + local_jobs[: max_results - min(len(remote_jobs), remote_max)]
    ranked = sorted(picked, key=lambda j: _sort_key(j, datetime.date.today()))[:max_results]

    print(f"Total {len(raw)} collected, {len(ranked)} matching jobs.")

    if args.json:
        import json
        print(json.dumps(
            [{  # noqa: E126
                "title": j.title, "url": j.url, "company": j.company,
                "location": j.location, "posted": j.posted,
                "deadline": j.deadline, "source": j.source, "score": j.score,
            } for j in ranked],
            indent=2, ensure_ascii=False,
        ))
        return

    date_str = today_str()
    if args.dry_run:
        print(plain_text(ranked, date_str))
        return

    if not ranked and not cfg.get("always_send_zero", False):
        print("No matching jobs; not sending email.")
        return

    if not ranked:
        print("No matching jobs; sending a zero-digest email.")
    else:
        send_email(
            require_env("GMAIL_SENDER"),
            require_env("GMAIL_APP_PASSWORD"),
            cfg["recipient"],
            ranked,
            date_str,
        )


if __name__ == "__main__":
    main()