import argparse

import requests

from .config import load_config, require_env
from .digester import filter_and_rank
from .emailer import html_body, plain_text, send_email, today_str
from .sources import corporate_staffing, devnetjobs, myjobmag

SOURCE_FETCHERS = {
    "myjobmag": myjobmag.fetch,
    "corporate_staffing": corporate_staffing.fetch,
    "devnetjobs": devnetjobs.fetch,
}


def collect(cfg: dict, keywords: list[str]) -> list:
    session = requests.Session()
    jobs = []
    for name in cfg.get("sources", list(SOURCE_FETCHERS)):
        fetcher = SOURCE_FETCHERS.get(name)
        if not fetcher:
            continue
        try:
            found = fetcher(keywords, session)
        except Exception as exc:  # one source must not kill the digest
            print(f"[{name}] error: {exc}")
            found = []
        jobs.extend(found)
        print(f"[{name}] fetched {len(found)} raw jobs")
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

    raw = collect(cfg, keywords)
    ranked = filter_and_rank(
        raw,
        keywords,
        cfg.get("skills", []),
        cfg.get("locations", []),
    )
    ranked = ranked[: cfg.get("max_results", 15)]

    print(f"Total {len(raw)} raw, {len(ranked)} matching jobs.")

    if args.json:
        import json
        print(json.dumps(
            [{  # noqa: E126
                "title": j.title, "url": j.url, "company": j.company,
                "location": j.location, "posted": j.posted, "source": j.source,
                "score": j.score,
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