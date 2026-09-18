import datetime
from dataclasses import dataclass, field


@dataclass
class Job:
    title: str
    url: str
    company: str = ""
    location: str = ""
    posted: str = ""
    deadline: str = ""
    posted_date: datetime.date | None = None
    source: str = "unknown"
    snippet: str = ""
    score: int = 0

    @property
    def key(self):
        return f"{self.title.strip().lower()}|{self.company.strip().lower()}"

    @property
    def search_text(self):
        return f"{self.title} {self.snippet}".lower()