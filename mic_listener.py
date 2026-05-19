#!/usr/bin/env python3
"""
Écoute le microphone en temps réel et détecte les gros mots.
Moteur STT : Vosk (offline, 100 % local, français natif)

Dépendances :
    pip install vosk pyaudio numpy sounddevice

Usage :
    python3 mic_listener.py               # démarre l'écoute
    python3 mic_listener.py --calibrer    # ajuste le micro avant de démarrer
    python3 mic_listener.py --modele grand  # modèle plus précis (1,4 Go)
"""
import argparse
import json
import os
import subprocess
import threading
import time
import urllib.request
import zipfile
from collections import Counter

import pyaudio
from vosk import Model, KaldiRecognizer, SetLogLevel

try:
    import matplotlib.pyplot as plt
    _MPL = True
except ImportError:
    _MPL = False

from gros_mot import detect
from gros_mot.wordlist import SEVERITY_COLOR

# ── ANSI ───────────────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD  = "\033[1m"
GREEN = "\033[32m"
RED   = "\033[31m"
GRAY  = "\033[90m"
CYAN  = "\033[36m"
YELLOW = "\033[33m"

# ── Modèles Vosk disponibles ───────────────────────────────────────────────────
MODELS = {
    "petit": {
        "dir": "vosk-model-small-fr-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip",
        "taille": "50 Mo",
    },
    "grand": {
        "dir": "vosk-model-fr-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip",
        "taille": "1,4 Go",
    },
}

RATE  = 16_000   # Hz requis par Vosk
CHUNK = 4_000    # frames par lecture (~0,25 s)

VOIX_DEFAUT = "Thomas"   # voix macOS fr_FR — alternatives : Jacques, Eddy (Français (France))

# ── Statistiques ───────────────────────────────────────────────────────────────
_stats_total:    int     = 0
_stats_words:    Counter = Counter()   # mot normalisé → nb occurrences
_stats_severity: Counter = Counter()   # gravité (1/2/3) → nb occurrences
_word_severity:  dict    = {}          # mot normalisé → gravité (pour colorier)

_SEV_COLOR_MPL = {1: "#f0b429", 2: "#e53e3e", 3: "#9b59b6"}
_SEV_LABEL     = {1: "Faible", 2: "Modéré", 3: "Élevé"}

_fig  = None
_axes = None


def _init_chart() -> None:
    global _fig, _axes
    if not _MPL:
        return
    plt.ion()
    _fig, _axes = plt.subplots(1, 2, figsize=(13, 5))
    _fig.suptitle("Statistiques — Détecteur de gros mots", fontweight="bold")
    _fig.canvas.manager.set_window_title("Gros mots détectés")
    _redessiner_chart()
    plt.tight_layout()
    plt.show(block=False)
    plt.pause(0.1)


def _redessiner_chart() -> None:
    if not _MPL or _fig is None:
        return

    ax_mots, ax_sev = _axes
    ax_mots.clear()
    ax_sev.clear()

    # ── Graphique gauche : top 10 mots ──
    ax_mots.set_title(f"Mots détectés  (total : {_stats_total})", fontweight="bold")
    if _stats_words:
        top = _stats_words.most_common(10)
        mots, counts = zip(*top)
        mots   = list(mots)[::-1]
        counts = list(counts)[::-1]
        colors = [_SEV_COLOR_MPL.get(_word_severity.get(m, 1), "#aaa") for m in mots]
        bars = ax_mots.barh(mots, counts, color=colors)
        for bar, val in zip(bars, counts):
            ax_mots.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                         str(val), va="center", fontweight="bold")
        ax_mots.set_xlabel("Occurrences")
        ax_mots.set_xlim(0, max(counts) + 2)
    else:
        ax_mots.text(0.5, 0.5, "En attente…", ha="center", va="center",
                     transform=ax_mots.transAxes, color="gray", fontsize=13)

    # ── Graphique droite : répartition par gravité ──
    ax_sev.set_title("Répartition par gravité", fontweight="bold")
    labels = [_SEV_LABEL[s] for s in [1, 2, 3]]
    values = [_stats_severity[s] for s in [1, 2, 3]]
    colors = [_SEV_COLOR_MPL[s] for s in [1, 2, 3]]
    bars = ax_sev.bar(labels, values, color=colors, width=0.5)
    for bar, val in zip(bars, values):
        ax_sev.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    str(val), ha="center", va="bottom", fontweight="bold")
    ax_sev.set_ylabel("Occurrences")
    ax_sev.set_ylim(0, max(max(values) + 2, 4))

    _fig.canvas.draw()
    plt.pause(0.001)


def _enregistrer(detections: list) -> None:
    global _stats_total
    for d in detections:
        _stats_total += 1
        _stats_words[d.matched] += 1
        _stats_severity[d.severity] += 1
        _word_severity[d.matched] = d.severity
    _redessiner_chart()


# ── Téléchargement du modèle ───────────────────────────────────────────────────

def _progress(block: int, block_size: int, total: int) -> None:
    done = block * block_size
    pct  = min(done * 100 // total, 100) if total > 0 else 0
    bar  = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"\r  [{bar}] {pct:3d}%", end="", flush=True)


def telecharger_modele(nom: str) -> str:
    info = MODELS[nom]
    model_dir = info["dir"]
    if os.path.isdir(model_dir):
        return model_dir

    print(f"Modèle « {nom} » introuvable — téléchargement ({info['taille']})…")
    zip_path = model_dir + ".zip"
    urllib.request.urlretrieve(info["url"], zip_path, reporthook=_progress)
    print()
    print("  Extraction…", end=" ", flush=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(".")
    os.remove(zip_path)
    print("OK")
    return model_dir


# ── Calibration micro ──────────────────────────────────────────────────────────

def calibrer(duree: float = 3.0) -> None:
    try:
        import numpy as np
    except ImportError:
        print("numpy non installé — calibration ignorée.")
        return

    print(f"Calibration : restez silencieux {duree:.0f} s…", flush=True)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    energies: list[float] = []
    t0 = time.time()
    while time.time() - t0 < duree:
        data = stream.read(CHUNK, exception_on_overflow=False)
        arr = np.frombuffer(data, np.int16).astype(np.float32)
        energies.append(float(np.sqrt(np.mean(arr ** 2))))
    stream.stop_stream()
    stream.close()
    pa.terminate()

    bruit = float(np.mean(energies))
    print(f"  Bruit ambiant moyen : {bruit:.0f} (amplitude RMS)")
    print(f"  Tout va bien — Vosk gère le seuil automatiquement.\n")


# ── Synthèse vocale (macOS say) ────────────────────────────────────────────────

_tts_lock = threading.Lock()   # évite que deux alertes se chevauchent


def _dire(message: str, voix: str) -> None:
    """Joue le message via la voix macOS — bloquant, à lancer dans un thread."""
    with _tts_lock:
        subprocess.run(["say", "-v", voix, message], check=False)


def alerter(nom: str, voix: str) -> None:
    """Lance l'alerte vocale dans un thread pour ne pas bloquer l'écoute micro."""
    message = "S'il te plaît, surveille ton langage."
    t = threading.Thread(target=_dire, args=(message, voix), daemon=True)
    t.start()


# ── Affichage résultats ────────────────────────────────────────────────────────

def afficher(text: str, nom: str, voix: str) -> None:
    print(f"\r{BOLD}Entendu :{RESET} {text}")
    detections = detect(text)
    if detections:
        for d in detections:
            color = SEVERITY_COLOR.get(d.severity, "")
            print(f"  {color}{BOLD}⚠  [{d.label}]{RESET}  « {d.original} »")
        _enregistrer(detections)
        print(f"  {GRAY}Total session : {_stats_total} gros mot(s){RESET}")
        alerter(nom, voix)
    else:
        print(f"  {GREEN}✓  Texte propre{RESET}")
    print()


# ── Boucle d'écoute principale ─────────────────────────────────────────────────

def ecouter(model_dir: str, nom: str, voix: str) -> None:
    SetLogLevel(-1)  # silence les logs de Vosk
    print("Chargement du modèle…", end=" ", flush=True)
    model = Model(model_dir)
    rec   = KaldiRecognizer(model, RATE)
    rec.SetWords(True)
    print("OK")

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    stream.start_stream()
    _init_chart()

    print(
        f"\n{GREEN}{BOLD}Microphone actif{RESET} — "
        f"nom : {BOLD}{nom}{RESET}  voix : {BOLD}{voix}{RESET}  "
        f"— Ctrl+C pour quitter.\n"
    )

    _tick = 0
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)

            if rec.AcceptWaveform(data):
                # Résultat final (silence détecté après la parole)
                result = json.loads(rec.Result())
                text   = result.get("text", "").strip()
                if text:
                    afficher(text, nom, voix)
            else:
                # Résultat partiel (parole en cours)
                partial = json.loads(rec.PartialResult()).get("partial", "").strip()
                if partial:
                    print(f"\r{GRAY}⬤ {partial}{RESET}   ", end="", flush=True)

            # Garder la fenêtre matplotlib réactive (toutes les ~2 s)
            _tick += 1
            if _MPL and _tick % 8 == 0:
                plt.pause(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        print(f"\n{GRAY}Arrêt.{RESET}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mic-listener",
        description="Détection de gros mots en temps réel via microphone (Vosk, offline)",
    )
    parser.add_argument(
        "--modele",
        default="petit",
        choices=["petit", "grand"],
        help="Modèle Vosk : 'petit' (50 Mo, recommandé) ou 'grand' (1,4 Go, plus précis).",
    )
    parser.add_argument(
        "--nom",
        default="Jean",
        metavar="PRENOM",
        help="Prénom prononcé dans l'alerte vocale (défaut : Jean).",
    )
    parser.add_argument(
        "--voix",
        default=VOIX_DEFAUT,
        metavar="VOIX",
        help=f"Voix macOS fr_FR (défaut : {VOIX_DEFAUT}). Autres : Jacques, 'Eddy (Français (France))'.",
    )
    parser.add_argument(
        "--calibrer",
        action="store_true",
        help="Mesure le bruit ambiant avant de démarrer.",
    )
    args = parser.parse_args()

    if args.calibrer:
        calibrer()

    model_dir = telecharger_modele(args.modele)
    ecouter(model_dir, nom=args.nom, voix=args.voix)


if __name__ == "__main__":
    main()
