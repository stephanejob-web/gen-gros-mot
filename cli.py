#!/usr/bin/env python3
"""
Détecteur de gros mots en français — outil CLI
Usage:
  echo "texte" | python cli.py
  python cli.py "texte à analyser"
  python cli.py -f fichier.txt
  python cli.py --censor "texte avec des merde dedans"
"""
import argparse
import sys
from gros_mot import detect, is_clean, censor
from gros_mot.wordlist import SEVERITY_COLOR

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"


def _color(text: str, code: str, use_color: bool) -> str:
    return f"{code}{text}{RESET}" if use_color else text


def analyze(text: str, use_color: bool = True) -> int:
    """Affiche l'analyse et renvoie le code de sortie (0=propre, 1=gros mots trouvés)."""
    detections = detect(text)

    if not detections:
        print(_color("✓ Aucun gros mot détecté.", GREEN, use_color))
        return 0

    count = len(detections)
    header = f"✗ {count} gros mot(s) détecté(s) :"
    print(_color(header, RED, use_color))
    print()

    for d in detections:
        sev_color = SEVERITY_COLOR.get(d.severity, "")
        badge = _color(f"[{d.label}]", sev_color, use_color)
        word = _color(f'"{d.matched}"', BOLD, use_color)
        print(f"  {badge}  {word}")

    return 1


def run_censor(text: str, use_color: bool = True) -> None:
    censored = censor(text)
    label = _color("Texte censuré :", BOLD, use_color)
    print(f"{label} {censored}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gros-mot",
        description="Détecteur de gros mots en français",
    )
    parser.add_argument(
        "texte",
        nargs="?",
        help="Texte à analyser (ou utilise stdin si absent)",
    )
    parser.add_argument(
        "-f", "--fichier",
        metavar="FICHIER",
        help="Lire le texte depuis un fichier",
    )
    parser.add_argument(
        "--censor",
        action="store_true",
        help="Afficher la version censurée (remplace les gros mots par ***)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Désactiver la couleur dans la sortie",
    )
    parser.add_argument(
        "--propre",
        action="store_true",
        help="Retourne uniquement le code de sortie (0=propre, 1=gros mots)",
    )

    args = parser.parse_args()
    use_color = not args.no_color and sys.stdout.isatty()

    # Lecture du texte
    if args.fichier:
        try:
            with open(args.fichier, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Erreur : fichier introuvable : {args.fichier}", file=sys.stderr)
            sys.exit(2)
    elif args.texte:
        text = args.texte
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(0)

    text = text.strip()
    if not text:
        print("Erreur : texte vide.", file=sys.stderr)
        sys.exit(2)

    if args.propre:
        sys.exit(0 if is_clean(text) else 1)

    if args.censor:
        run_censor(text, use_color)
    else:
        sys.exit(analyze(text, use_color))


if __name__ == "__main__":
    main()
