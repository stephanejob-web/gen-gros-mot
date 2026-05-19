import re
import unicodedata

LEET: dict[str, str] = {
    '@': 'a', '4': 'a',
    '3': 'e', '€': 'e',
    '1': 'i', '!': 'i',
    '0': 'o',
    '5': 's', '$': 's',
    '7': 't',
    '9': 'g',
    '2': 'z',
    '8': 'b',
}

# Separators used for obfuscation WITHIN a word: "c.o.n", "c-o-n", "c_o_n"
# N.B.: l'espace n'est PAS inclus ici — on le gère au niveau de la tokenisation
_SEP_BETWEEN_CHARS = re.compile(r'(?<=\w)[.\-_*,;|\\]+(?=\w)')
_REPEATED_CHAR = re.compile(r'(.)\1+')


def normalize_token(token: str) -> str:
    """Normalise un seul token (mot ou groupe de chars sans espace)."""
    token = token.lower()
    # Decompose Unicode and strip combining marks (accents)
    nfd = unicodedata.normalize('NFD', token)
    token = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    # Leet substitution
    token = ''.join(LEET.get(c, c) for c in token)
    # Remove obfuscation separators: "c.o.n" → "con"
    token = _SEP_BETWEEN_CHARS.sub('', token)
    # Collapse ALL repeated chars: "connnard" → "conard", "merddde" → "merde"
    # La même règle s'applique à la wordlist → cohérence garantie
    token = _REPEATED_CHAR.sub(r'\1', token)
    # Ne garder que les caractères alphanumériques
    token = re.sub(r'[^a-z0-9]', '', token)
    return token


def normalize(text: str) -> str:
    """Normalise un texte complet (conserve les espaces entre les mots)."""
    return ' '.join(normalize_token(t) for t in text.split())
