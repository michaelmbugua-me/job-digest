import datetime
import re

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def parse_posted_date(s: str, today: datetime.date | None = None) -> datetime.date | None:
    """Best-effort parse of a posted date string. Returns date or None."""
    if not s:
        return None
    today = today or datetime.date.today()
    text = " ".join(s.split()).lower().strip(" .")

    rel = re.match(r"^(\d+)\s+(day|week|month|year)s?\s+ago$", text)
    if rel:
        n = int(rel.group(1))
        unit = rel.group(2)
        days = {"day": n, "week": n * 7, "month": n * 30, "year": n * 365}[unit]
        return today - datetime.timedelta(days=days)
    if text in ("today", "new"):
        return today
    if text == "yesterday":
        return today - datetime.timedelta(days=1)

    m = re.match(r"^(\d{1,2})\s+([a-z]{3,9})", text)
    if m:
        day, month = int(m.group(1)), MONTHS.get(m.group(2)[:3])
        if month:
            year = today.year
            try:
                d = datetime.date(year, month, day)
            except ValueError:
                return today
            if d > today:
                d = datetime.date(year - 1, month, day)
            return d

    m = re.match(r"^([a-z]{3,9})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})$", text)
    if m:
        month, day, year = MONTHS.get(m.group(1)[:3]), int(m.group(2)), int(m.group(3))
        if month:
            try:
                return datetime.date(year, month, day)
            except ValueError:
                return today

    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if m:
        try:
            return datetime.date(*map(int, m.groups()))
        except ValueError:
            return today

    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if m:
        try:
            return datetime.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            return today

    return None