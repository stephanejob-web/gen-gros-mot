import re
from dataclasses import dataclass
from .normalizer import normalize_token
from .wordlist import WORDS, PHRASES, SEVERITY_LABEL

# Tokenise le texte en gardant la position de chaque mot dans le texte source
_TOKEN_RE = re.compile(r'\S+')


def _tokenize(text: str):
    """Retourne [(match_object, normalized_str), ...]."""
    return [(m, normalize_token(m.group())) for m in _TOKEN_RE.finditer(text)]


@dataclass
class Detection:
    matched: str    # gros mot normalisé détecté
    original: str   # fragment du texte source
    start: int      # position dans le texte source
    end: int
    severity: int
    label: str


def detect(text: str) -> list[Detection]:
    tokens = _tokenize(text)
    results: list[Detection] = []
    covered: set[int] = set()  # indices de tokens déjà couverts

    # 1. Expressions multi-mots (priorité, du plus long au plus court)
    for norm_phrase, raw_phrase, sev in sorted(PHRASES, key=lambda x: -len(x[0])):
        phrase_parts = norm_phrase.split()
        n = len(phrase_parts)
        for i in range(len(tokens) - n + 1):
            window_norms = [tokens[i + j][1] for j in range(n)]
            span = set(range(i, i + n))
            # Ne pas matcher si la fenêtre chevauche une expression déjà couverte
            if window_norms == phrase_parts and not span & covered:
                covered |= span
                start = tokens[i][0].start()
                end = tokens[i + n - 1][0].end()
                results.append(Detection(
                    matched=norm_phrase,
                    original=text[start:end],
                    start=start,
                    end=end,
                    severity=sev,
                    label=SEVERITY_LABEL[sev],
                ))

    # 2. Mots isolés
    for idx, (m, norm) in enumerate(tokens):
        if idx in covered:
            continue
        if norm in WORDS:
            sev = WORDS[norm]
            results.append(Detection(
                matched=norm,
                original=m.group(),
                start=m.start(),
                end=m.end(),
                severity=sev,
                label=SEVERITY_LABEL[sev],
            ))

    return sorted(results, key=lambda d: d.start)


def is_clean(text: str) -> bool:
    return len(detect(text)) == 0


def censor(text: str, char: str = '*') -> str:
    """Remplace chaque gros mot détecté par des astérisques dans le texte source."""
    detections = detect(text)
    if not detections:
        return text

    parts = []
    prev = 0
    for d in sorted(detections, key=lambda x: x.start):
        parts.append(text[prev:d.start])
        parts.append(char * (d.end - d.start))
        prev = d.end
    parts.append(text[prev:])
    return ''.join(parts)
