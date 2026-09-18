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
    myjobmag,
    workable,
)

SOURCE_FETCHERS = {
    "myjobmag": myjobmag.fetch,
    "corporate_staffing": corporate_staffing.fetch,
    "devnetjobs": devnetjobs.fetch,
    "brightermonday": brightermonday.fetch,
    "workable": workable.fetch,
}


def collect(cfg: dict, keywords: list[str], skills: list[str]) -> list:
    session = requests.Session()
    today = datetime.date.today()
    jobs = []

    base_kwargs = {"keywords": keywords, "skills": skills, "session": session, "today": today}
    source_kwargs = {name: dict(base_kwargs) for name in SOURCE_FETCHERS}
    if "brightermonday" in cfg:
        source_kwargs["brightermonday"]["lists"] = cfg["brightermonday"].get("lists")
        source_kwargs["brightermonday"]["pages"] = cfg["brightermonday"].get("pages", 2)
    if "workable_accounts" in cfg:
        source_kwargs["workable"]["accounts"] = [
            tuple(a) for a in cfg["workable_accounts"]
        ]

    for name in cfg.get("sources", list(SOURCE_FETCHERS)):
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
    ranked = ranked[: cfg.get("max_results", 15)]

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