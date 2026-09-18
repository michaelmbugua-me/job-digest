import html as html_lib
import re

from ..models import Job

_NON_EN_MARKERS = {
    "desarrollador", "desarrolladora", "desenvolvedor", "desenvolvedora",
    "entwickler", "entwicklerin", "développeur", "développeuse",
    "sviluppatore", "sviluppatrice", "ontwikkelaar", "programador",
    "programadora", "programmeren", "ingeniero", "ingeniera", "ingenieur",
    "engenheiro", "engenheira", "requisitos", "experiencia", "experiência",
    "unternehmen", "bewerbung", "karriere", "stellenangebot", "platz",
    "puesto", "puestos", "vaga", "vagas", "remoto", "remota", "remotamente",
    "equipe", "equipo", "equipa", "empresa", "empresas", "trabajo",
    "trabalho", "acerca", "podrás", "serás", "salário", "salario", "missão",
    "missio", "rejoindre", "poste", "postes", "équipe", "notre", "nous",
    "recherchons", "buscamos", "estamos", "candidatos", "candidatura",
    "anuncio", "anuncios", "oferta", "ofertas", "prácticas", "becario",
    "sviluppo", "desenvolvimento", "buchhaltung", "zusammenarbeit",
}
_ACCENTED = "áàâäãéèêëíìîïóòôöõúùûüçñýÿščžěń"


def is_likely_english(text: str) -> bool:
    """Reject postings that are clearly not in English."""
    t = (text or "").strip().lower()
    if not t:
        return True
    head = t[:400]

    for ch in head:
        o = ord(ch)
        if (0x0400 <= o <= 0x04FF or 0x0600 <= o <= 0x06FF or
                0x0E00 <= o <= 0x0EFF or 0x4E00 <= o <= 0x9FFF or
                0xAC00 <= o <= 0xD7AF):
            return False

    tokens = set(re.findall(r"[a-zà-ÿ]{5,}", head))
    if tokens & _NON_EN_MARKERS:
        return False

    accented = sum(1 for ch in head if ch in _ACCENTED)
    if len(head) >= 60 and accented / len(head) > 0.03:
        return False
    return True


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