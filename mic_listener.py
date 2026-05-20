#!/usr/bin/env python3
"""
Écoute le microphone en temps réel et détecte les gros mots.
Moteur STT : faster-whisper (large-v3, offline, 97% précision FR)

Dépendances :
    pip install faster-whisper pyaudio numpy

Usage :
    python3 mic_listener.py                    # démarre l'écoute
    python3 mic_listener.py --list-devices     # liste les micros disponibles
    python3 mic_listener.py --device 2         # choisir Blue Yeti (index 2)
    python3 mic_listener.py --modele medium    # modèle plus léger (~1.5 Go)
    python3 mic_listener.py --calibrer         # mesure le bruit ambiant
"""
import argparse
import os
import platform
import subprocess
import struct
import threading
import time
from collections import Counter

import numpy as np
import pyaudio
from faster_whisper import WhisperModel

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    _MPL = True
except Exception:
    _MPL = False

from gros_mot import detect
from gros_mot.wordlist import SEVERITY_COLOR

_OS = platform.system()

# ── ANSI ───────────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
RED    = "\033[31m"
GRAY   = "\033[90m"
CYAN   = "\033[36m"
YELLOW = "\033[33m"

# Voix TTS par OS
if _OS == "Darwin":
    VOIX_DEFAUT = "Thomas"
elif _OS == "Linux":
    VOIX_DEFAUT = "fr"
else:
    VOIX_DEFAUT = ""

# ── Audio ──────────────────────────────────────────────────────────────────────
RATE          = 16_000   # Hz — requis par Whisper
CHUNK         = 1_024    # frames par lecture
RMS_SILENCE   = 80       # amplitude RMS : en dessous = silence
SILENCE_SECS  = 0.8      # secondes de silence avant envoi à Whisper
MIN_SPEECH_SECS = 0.3    # durée minimale de parole à transcrire

# ── Statistiques & graphique ───────────────────────────────────────────────────
_stats_total:    int     = 0
_stats_words:    Counter = Counter()
_stats_severity: Counter = Counter()
_word_severity:  dict    = {}

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


# ── TTS ────────────────────────────────────────────────────────────────────────
_tts_lock = threading.Lock()


def _dire(message: str, voix: str) -> None:
    with _tts_lock:
        if _OS == "Darwin":
            subprocess.run(["say", "-v", voix, message], check=False)
        elif _OS == "Linux":
            subprocess.run(["espeak", "-v", voix, message], check=False)


def alerter(nom: str, voix: str) -> None:
    message = f"{nom}, surveille ton langage."
    t = threading.Thread(target=_dire, args=(message, voix), daemon=True)
    t.start()


# ── Affichage ──────────────────────────────────────────────────────────────────
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


# ── Audio utils ────────────────────────────────────────────────────────────────
def _rms(data: bytes) -> float:
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0


def calibrer(duree: float = 3.0) -> None:
    print(f"Calibration : restez silencieux {duree:.0f} s…", flush=True)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    energies = []
    t0 = time.time()
    while time.time() - t0 < duree:
        data = stream.read(CHUNK, exception_on_overflow=False)
        energies.append(_rms(data))
    stream.stop_stream()
    stream.close()
    pa.terminate()
    bruit = float(np.mean(energies))
    seuil = bruit * 2.5
    print(f"  Bruit ambiant RMS : {bruit:.0f}")
    print(f"  Seuil recommandé  : {seuil:.0f}  (lancez avec --seuil {seuil:.0f})\n")


# ── Boucle d'écoute principale ─────────────────────────────────────────────────
def ecouter(model_name: str, nom: str, voix: str,
            device_index: int | None, seuil: float) -> None:

    print(f"Chargement du modèle Whisper {BOLD}{model_name}{RESET}…", flush=True)
    print("  (premier lancement = téléchargement automatique ~quelques Go)\n")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    print(f"{GREEN}Modèle chargé.{RESET}\n")

    pa = pyaudio.PyAudio()
    open_kwargs: dict = dict(
        format=pyaudio.paInt16,
        channels=1,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    if device_index is not None:
        open_kwargs["input_device_index"] = device_index
    stream = pa.open(**open_kwargs)
    stream.start_stream()
    _init_chart()

    print(
        f"{GREEN}{BOLD}Microphone actif{RESET} — "
        f"nom : {BOLD}{nom}{RESET}  voix : {BOLD}{voix}{RESET}  "
        f"seuil RMS : {BOLD}{seuil:.0f}{RESET}  "
        f"— Ctrl+C pour quitter.\n"
    )

    speech_buffer: list[bytes] = []
    silence_chunks = 0
    silence_limit   = int(SILENCE_SECS * RATE / CHUNK)
    min_speech_chunks = int(MIN_SPEECH_SECS * RATE / CHUNK)
    speaking = False
    _tick = 0

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            level = _rms(data)

            if level >= seuil:
                speech_buffer.append(data)
                silence_chunks = 0
                if not speaking:
                    speaking = True
                    print(f"\r{CYAN}● Parole détectée…{RESET}   ", end="", flush=True)
            else:
                if speaking:
                    silence_chunks += 1
                    speech_buffer.append(data)
                    if silence_chunks >= silence_limit:
                        # Fin de segment — transcrire si assez long
                        if len(speech_buffer) >= min_speech_chunks:
                            audio_data = b"".join(speech_buffer)
                            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                            print(f"\r{GRAY}Transcription…{RESET}   ", end="", flush=True)
                            segments, _ = model.transcribe(
                                audio_np,
                                language="fr",
                                beam_size=5,
                                vad_filter=True,
                                vad_parameters={"min_silence_duration_ms": 300},
                            )
                            text = " ".join(s.text.strip() for s in segments).strip()
                            if text:
                                print("\r" + " " * 40 + "\r", end="")
                                afficher(text, nom, voix)
                        speech_buffer.clear()
                        silence_chunks = 0
                        speaking = False

            # Garder fenêtre matplotlib réactive
            _tick += 1
            if _MPL and _tick % 20 == 0:
                plt.pause(0.001)

    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        print(f"\n{GRAY}Arrêt.  Total session : {_stats_total} gros mot(s).{RESET}")


# ── CLI ────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mic-listener",
        description="Détection de gros mots en temps réel via microphone (faster-whisper, offline)",
    )
    parser.add_argument(
        "--modele",
        default="large-v3",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Modèle Whisper (défaut : large-v3, précision maximale).",
    )
    parser.add_argument("--nom",    default="Jean", metavar="PRENOM")
    parser.add_argument("--voix",   default=VOIX_DEFAUT, metavar="VOIX")
    parser.add_argument("--seuil",  type=float, default=RMS_SILENCE, metavar="RMS",
                        help=f"Seuil énergie micro (défaut : {RMS_SILENCE}). Utiliser --calibrer pour ajuster.")
    parser.add_argument("--device", type=int, default=None, metavar="INDEX",
                        help="Index du périphérique audio (voir --list-devices).")
    parser.add_argument("--list-devices", action="store_true",
                        help="Affiche les micros disponibles et quitte.")
    parser.add_argument("--calibrer", action="store_true",
                        help="Mesure le bruit ambiant pour ajuster --seuil.")
    args = parser.parse_args()

    if args.list_devices:
        pa = pyaudio.PyAudio()
        print("Périphériques audio disponibles :")
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(f"  [{i:2d}] {info['name']}")
        pa.terminate()
        return

    if args.calibrer:
        calibrer()
        return

    ecouter(
        model_name=args.modele,
        nom=args.nom,
        voix=args.voix,
        device_index=args.device,
        seuil=args.seuil,
    )


if __name__ == "__main__":
    main()
