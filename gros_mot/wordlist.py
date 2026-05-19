"""
Niveaux de gravité :
  1 — Juron courant (merde, putain…)
  2 — Insulte (connard, salope…)
  3 — Contenu sexuel / discriminatoire grave
"""
from .normalizer import normalize as _n

# (mot, gravité)  — stockés avec accents pour la lisibilité
_RAW_WORDS: list[tuple[str, int]] = [
    # Niveau 1 — jurons
    ("merde", 1), ("merdique", 1), ("merdeux", 1), ("merdeuse", 1),
    ("emmerdeur", 1), ("emmerdant", 1), ("emmerdante", 1),
    ("putain", 1), ("pute", 1), ("putes", 1), ("putains", 1),
    ("bordel", 1),
    ("foutre", 1), ("foutaise", 1),
    ("chier", 1), ("chiotte", 1), ("chiottes", 1), ("chieur", 1), ("chieuse", 1),
    ("ostie", 1), ("tabarnak", 1), ("câlice", 1), ("crisse", 1),  # québécois
    # Niveau 2 — insultes
    ("con", 2), ("conne", 2), ("connard", 2), ("connasse", 2),
    ("connerie", 2), ("conneries", 2),
    ("salaud", 2), ("salope", 2), ("salopard", 2), ("saloperie", 2),
    ("bâtard", 2), ("bâtarde", 2),
    ("abruti", 2), ("abrutie", 2),
    ("crétin", 2), ("crétine", 2),
    ("enfoiré", 2), ("enfoirée", 2),
    ("imbécile", 2), ("débile", 2),
    ("idiot", 2), ("idiote", 2),
    ("couillon", 2), ("couillonne", 2),
    ("minus", 2), ("minable", 2),
    ("ordure", 2), ("déchet", 2),
    ("pourriture", 2),
    ("raclure", 2),
    ("fumier", 2),
    ("gueux", 2), ("gueuse", 2), ("geuze", 2),
    ("traître", 2), ("lâche", 2),
    # Niveau 3 — sexuel / discriminatoire
    ("bite", 3), ("bites", 3),
    ("couille", 3), ("couilles", 3),
    ("cul", 3),
    ("chatte", 3),
    ("vagin", 3),
    ("pénis", 3),
    ("niquer", 3), ("nique", 3), ("niqueur", 3),
    ("baiser", 3),
    ("enculé", 3), ("enculée", 3), ("enculer", 3), ("enculeur", 3),
    ("sodomiser", 3),
    ("branleur", 3), ("branleuse", 3), ("branler", 3),
    ("pédé", 3), ("pédale", 3),
    ("tapette", 3),
    ("pd", 3),
    # Abréviations
    ("fdp", 3), ("tg", 2), ("vtff", 3),
    # Injures discriminatoires
    ("nègre", 3), ("negrillon", 3),
    ("bougnoule", 3),
    ("youpin", 3), ("youpine", 3),
    ("bicot", 3),
    ("raton", 3),
    ("crouille", 3),
    ("feuj", 3),
    ("paki", 3),
    ("bridé", 3),
    ("négresse", 3),
]

# Expressions multi-mots (gravité, expression)
_RAW_PHRASES: list[tuple[str, int]] = [
    ("ta gueule", 2),
    ("ferme ta gueule", 2),
    ("va te faire foutre", 3),
    ("va te faire enculer", 3),
    ("allez vous faire foutre", 3),
    ("fils de pute", 3),
    ("fils de putain", 3),
    ("fils de pute", 3),
    ("nique ta mère", 3),
    ("nique ta race", 3),
    ("sale con", 2),
    ("gros con", 2),
    ("pauvre con", 2),
    ("espèce de con", 2),
    ("espèce d'idiot", 2),
    ("va te faire", 2),
]

# Alias phonétiques : transcriptions erronées produites par Vosk (petit modèle)
# → mappées vers la gravité du mot qu'elles représentent
_PHONETIC_ALIASES: list[tuple[str, int]] = [
    ("gaze", 2),   # Vosk transcrit "gueuse" → "gaze"
]

# Dictionnaires finaux avec clés normalisées
WORDS: dict[str, int] = {_n(w): sev for w, sev in _RAW_WORDS}
WORDS.update({_n(w): sev for w, sev in _PHONETIC_ALIASES})
PHRASES: list[tuple[str, str, int]] = [
    (_n(p), p, sev) for p, sev in _RAW_PHRASES
]

SEVERITY_LABEL = {1: "faible", 2: "modéré", 3: "élevé"}
SEVERITY_COLOR = {1: "\033[33m", 2: "\033[31m", 3: "\033[35m"}  # jaune / rouge / magenta
