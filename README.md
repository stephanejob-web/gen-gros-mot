<div align="center">

# 🤬 Détecteur de Gros Mots

**Un outil de prise de conscience pour mieux maîtriser son langage au quotidien**  
*Analyse de texte · Écoute microphone temps réel · 100 % offline*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Licence MIT](https://img.shields.io/badge/Licence-MIT-green?style=flat-square)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-supported-black?style=flat-square&logo=apple)](https://www.apple.com/macos/)
[![Linux](https://img.shields.io/badge/Linux-supported-FCC624?style=flat-square&logo=linux&logoColor=black)](https://kernel.org/)
[![Vosk](https://img.shields.io/badge/STT-Vosk-blue?style=flat-square)](https://alphacephei.com/vosk/)

</div>

---

## Pourquoi ce projet ?

On dit souvent des gros mots sans même s'en rendre compte. C'est devenu un réflexe, une habitude inconsciente dans la conversation de tous les jours. Ce projet est né d'une conviction simple : **on ne peut pas changer ce qu'on ne voit pas**.

L'objectif n'est pas de juger ou de censurer, mais de **rendre visible ce qui passe inaperçu**. En signalant chaque mot problématique en temps réel — à l'écrit comme à l'oral — l'outil aide les utilisateurs à prendre conscience de la fréquence et de la gravité de leur langage, pour leur permettre d'évoluer à leur propre rythme, s'ils le souhaitent.

> *"La prise de conscience est la première étape du changement."*

---

## Aperçu

Ce projet propose deux outils complémentaires pour analyser le langage en français :

- **`cli.py`** — Analyse un texte (argument, fichier ou stdin) et retourne les gros mots détectés avec leur niveau de gravité, ou une version censurée.
- **`mic_listener.py`** — Écoute le microphone en continu, transcrit la parole via [Vosk](https://alphacephei.com/vosk/) (moteur offline, aucune donnée envoyée sur Internet) et déclenche une alerte vocale douce dès qu'un gros mot est prononcé — comme un rappel bienveillant.

```
$ python cli.py "c'est quoi ce bordel de connard"

✗ 2 gros mot(s) détecté(s) :

  [faible]   "bordel"
  [modéré]   "connard"
```

```
$ python cli.py --censor "va te faire foutre espèce de con"

Texte censuré : va te faire ****** espèce de ***
```

---

## Fonctionnalités

### Détection de texte
- ✅ Mots isolés **et** expressions multi-mots (`"ta gueule"`, `"fils de pute"`, `"va te faire foutre"`, …)
- ✅ **3 niveaux de gravité** : faible, modéré, élevé
- ✅ Normalisation robuste : accents, casse, ponctuation collée (`"C'estMERDE!"` → détecté)
- ✅ Support du français québécois (`tabarnak`, `câlice`, `ostie`, `crisse`)
- ✅ Censure intégrée avec remplacement caractère par caractère
- ✅ Code de sortie shell (`0` = propre, `1` = gros mots) — intégrable dans des scripts CI/CD

### Écoute microphone
- ✅ Transcription **100 % locale** via Vosk (aucune donnée envoyée sur Internet)
- ✅ Résultats partiels affichés en temps réel pendant que vous parlez
- ✅ Alerte vocale automatique (macOS : `say`, Linux : `espeak`)
- ✅ Téléchargement automatique du modèle Vosk au premier lancement
- ✅ Calibration du microphone intégrée
- ✅ Graphiques de statistiques live (top 10 mots, répartition par gravité)

---

## Architecture

```
gen-gros-mot/
│
├── gros_mot/               # Bibliothèque de détection — aucune dépendance externe
│   ├── __init__.py         # API publique : detect, is_clean, censor
│   ├── detector.py         # Moteur principal de détection
│   ├── normalizer.py       # Normalisation unicode, accents, casse
│   └── wordlist.py         # Liste de mots + expressions avec niveaux de gravité
│
├── cli.py                  # Outil CLI — analyse de texte
├── mic_listener.py         # Écoute microphone en temps réel (Vosk)
└── requirements.txt        # Dépendances Python
```

> Le cœur de détection (`gros_mot/`) ne dépend d'**aucune bibliothèque externe**.  
> Il peut être utilisé seul dans n'importe quel projet Python.

---

## Installation

### Prérequis

- Python **3.10** ou supérieur
- `pip` à jour : `pip install --upgrade pip`

---

### 🍎 macOS

```bash
# 1. Installer la dépendance audio système
brew install portaudio

# 2. Cloner le dépôt
git clone https://github.com/stephanejob-web/gen-gros-mot.git
cd gen-gros-mot

# 3. Créer et activer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 4. Installer les dépendances Python
pip install -r requirements.txt
```

---

### 🐧 Linux (Debian / Ubuntu / Mint)

```bash
# 1. Installer les dépendances système
sudo apt update
sudo apt install portaudio19-dev python3-dev espeak

# 2. Cloner le dépôt
git clone https://github.com/stephanejob-web/gen-gros-mot.git
cd gen-gros-mot

# 3. Créer et activer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# 4. Installer les dépendances Python
pip install -r requirements.txt
```

> **Arch Linux / Manjaro :** remplacer l'étape 1 par  
> `sudo pacman -S portaudio espeak-ng`

> **Fedora / RHEL :** remplacer l'étape 1 par  
> `sudo dnf install portaudio-devel espeak`

---

### 🪟 Windows

```powershell
# 1. Cloner le dépôt
git clone https://github.com/stephanejob-web/gen-gros-mot.git
cd gen-gros-mot

# 2. Créer et activer un environnement virtuel
python -m venv .venv
.venv\Scripts\activate

# 3. Installer les dépendances Python
pip install -r requirements.txt
```

> **Si l'installation de `pyaudio` échoue**, téléchargez le wheel précompilé depuis  
> [lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)  
> puis installez-le manuellement : `pip install PyAudio‑*.whl`

> **Note :** l'alerte vocale n'est pas supportée sur Windows. La détection et l'affichage fonctionnent normalement.

---

## Utilisation

### CLI — Analyse de texte

#### Syntaxe générale

```bash
python cli.py [OPTIONS] [TEXTE]
```

| Option | Description |
|--------|-------------|
| `TEXTE` | Texte à analyser en argument direct |
| `-f FICHIER` | Lire le texte depuis un fichier |
| `--censor` | Afficher la version censurée (remplace par `***`) |
| `--propre` | Code de sortie uniquement : `0` = propre, `1` = gros mots |
| `--no-color` | Désactiver les couleurs ANSI (utile pour les logs) |

#### Exemples

```bash
# Analyse directe
python cli.py "putain c'est quoi ce bordel"

# Depuis un fichier
python cli.py -f discours.txt

# Depuis stdin (pipeline)
cat message.txt | python cli.py

# Version censurée
python cli.py --censor "va te faire foutre connard"
# → Texte censuré : va te faire ****** *******

# Intégration dans un script shell
python cli.py --propre "texte à vérifier"
echo $?   # 0 si propre, 1 si gros mots détectés
```

---

### Microphone — Écoute en temps réel

#### Syntaxe générale

```bash
python mic_listener.py [OPTIONS]
```

| Option | Valeur par défaut | Description |
|--------|-------------------|-------------|
| `--modele` | `petit` | Modèle Vosk : `petit` (50 Mo) ou `grand` (1,4 Go) |
| `--nom` | `Jean` | Prénom utilisé dans l'alerte vocale |
| `--voix` | `Thomas` (macOS) / `fr` (Linux) | Voix TTS |
| `--calibrer` | — | Mesurer le bruit ambiant avant de démarrer |

#### Exemples

```bash
# Démarrage rapide
python mic_listener.py

# Avec calibration du microphone
python mic_listener.py --calibrer

# Modèle haute précision
python mic_listener.py --modele grand

# Personnaliser l'alerte vocale
python mic_listener.py --nom Marie

# macOS — changer la voix
python mic_listener.py --voix Jacques

# Linux — changer la voix espeak
python mic_listener.py --voix fr+f1
```

#### Ce qui s'affiche

```
Microphone actif — nom : Jean  voix : Thomas  — Ctrl+C pour quitter.

⬤ putain c'est...
Entendu : putain c'est quoi ce bordel
  ⚠  [faible]  « putain »
  ⚠  [faible]  « bordel »
  Total session : 2 gros mot(s)
```

Le modèle Vosk est **téléchargé automatiquement** au premier lancement si absent.

---

## API Python

La bibliothèque `gros_mot` s'intègre directement dans n'importe quel projet Python.

### Installation (sans cloner le dépôt)

```bash
# Copier le dossier gros_mot/ dans votre projet, puis :
# Aucune dépendance à installer — bibliothèque standard uniquement
```

### Utilisation

```python
from gros_mot import detect, is_clean, censor

# ── Détection complète ──────────────────────────────────────────────────────
detections = detect("c'est quoi ce bordel de connard")

for d in detections:
    print(f"{d.original!r:20} → gravité {d.severity} ({d.label})")

# 'bordel'             → gravité 1 (faible)
# 'connard'            → gravité 2 (modéré)


# ── Vérification rapide ─────────────────────────────────────────────────────
is_clean("bonjour tout le monde")   # True
is_clean("putain c'est nul")        # False


# ── Censure ─────────────────────────────────────────────────────────────────
print(censor("va te faire foutre espèce de con"))
# va te faire ****** espèce de ***


# ── Filtrer par niveau de gravité ───────────────────────────────────────────
grave = [d for d in detect(texte) if d.severity >= 2]
```

### Objet `Detection`

```python
@dataclass
class Detection:
    matched:  str   # mot/expression normalisé(e) détecté(e) — ex: "connard"
    original: str   # fragment exact dans le texte source    — ex: "Connard!"
    start:    int   # index de début dans le texte source
    end:      int   # index de fin dans le texte source
    severity: int   # niveau de gravité : 1, 2 ou 3
    label:    str   # libellé : "faible", "modéré" ou "élevé"
```

---

## Niveaux de gravité

| Niveau | Label | Exemples |
|--------|-------|----------|
| **1** | Faible | `merde`, `putain`, `bordel`, `tabarnak`, `câlice` |
| **2** | Modéré | `connard`, `salope`, `abruti`, `enfoiré`, `ta gueule` |
| **3** | Élevé | insultes sexuelles, injures racistes, expressions très violentes |

---

## Modèles Vosk

| Identifiant | Taille | Précision | Recommandé pour |
|-------------|--------|-----------|-----------------|
| `petit` | ~50 Mo | Correcte | Usage quotidien, machines modestes |
| `grand` | ~1,4 Go | Élevée | Environnements silencieux, serveurs |

Les modèles sont fournis par [alphacephei.com/vosk](https://alphacephei.com/vosk/models)  
et téléchargés automatiquement dans le répertoire courant au premier lancement.

---

## Compatibilité

| Fonctionnalité | macOS | Linux | Windows |
|----------------|:-----:|:-----:|:-------:|
| Analyse de texte (CLI) | ✅ | ✅ | ✅ |
| Écoute microphone | ✅ | ✅ | ✅ |
| Alerte vocale | ✅ (`say`) | ✅ (`espeak`) | ❌ |
| Graphiques matplotlib | ✅ | ✅ | ✅ |

---

## Licence

Ce projet est distribué sous licence **MIT** — libre d'utilisation, de modification et de distribution.  
Voir le fichier [LICENSE](LICENSE) pour les détails.

---

<div align="center">

Fait avec ❤️ en Python · Propulsé par [Vosk](https://alphacephei.com/vosk/)

</div>
