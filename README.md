# Détecteur de gros mots — Français

Bibliothèque Python et outils CLI pour détecter, classifier et censurer les gros mots en français.  
Fonctionne en deux modes : **analyse de texte** (CLI) et **écoute microphone en temps réel** (Vosk, 100 % offline).

---

## Fonctionnalités

- Détection de mots isolés **et** d'expressions multi-mots (`"va te faire foutre"`, `"fils de pute"`, …)
- **3 niveaux de gravité** : faible · modéré · élevé
- Normalisation robuste : accents, casse, ponctuation collée
- Support du français québécois (`tabarnak`, `câlice`, `ostie`, …)
- Censure intégrée : `"va te faire foutre"` → `"va te faire ******"`
- Mode microphone : transcription Vosk offline + alerte vocale
- Graphiques de statistiques en direct (matplotlib)
- Téléchargement automatique du modèle Vosk au premier lancement
- Aucune dépendance externe pour le cœur de détection (bibliothèque standard uniquement)

---

## Structure du projet

```
gen-gros-mot/
├── gros_mot/           # Bibliothèque de détection (pas de dépendances)
│   ├── __init__.py     # API publique : detect, is_clean, censor
│   ├── detector.py     # Moteur de détection
│   ├── normalizer.py   # Normalisation unicode / casse
│   └── wordlist.py     # Liste de mots et expressions avec niveaux de gravité
├── cli.py              # Outil CLI (analyse de texte)
├── mic_listener.py     # Écoute microphone en temps réel (Vosk)
└── requirements.txt
```

---

## Installation

### Prérequis communs

- Python 3.10 ou supérieur
- `pip` à jour : `pip install --upgrade pip`

---

### macOS

```bash
# 1. Dépendance système pour l'audio
brew install portaudio

# 2. Cloner le projet
git clone https://github.com/stephanejob-web/gen-gros-mot.git
cd gen-gros-mot

# 3. Environnement virtuel (recommandé)
python3 -m venv .venv && source .venv/bin/activate

# 4. Dépendances Python
pip install -r requirements.txt
```

---

### Linux (Debian / Ubuntu)

```bash
# 1. Dépendances système
sudo apt update
sudo apt install portaudio19-dev python3-dev espeak

# 2. Cloner le projet
git clone https://github.com/stephanejob-web/gen-gros-mot.git
cd gen-gros-mot

# 3. Environnement virtuel (recommandé)
python3 -m venv .venv && source .venv/bin/activate

# 4. Dépendances Python
pip install -r requirements.txt
```

> **Note Linux :** l'alerte vocale utilise `espeak` (inclus dans la commande d'installation ci-dessus).  
> Les voix disponibles sont `fr`, `fr+m1`, `fr+f1`, `fr+m3`, etc.

---

### Windows

```powershell
# 1. Cloner le projet
git clone https://github.com/stephanejob-web/gen-gros-mot.git
cd gen-gros-mot

# 2. Environnement virtuel (recommandé)
python -m venv .venv
.venv\Scripts\activate

# 3. Dépendances Python
pip install -r requirements.txt
```

> **Note Windows :** si l'installation de `pyaudio` échoue, téléchargez le wheel précompilé depuis  
> [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)  
> puis installez-le avec `pip install PyAudio‑*.whl`.

---

## Utilisation

### CLI — Analyse de texte

```bash
# Analyser une phrase directement
python cli.py "c'est quoi ce bordel de merde"

# Lire depuis un fichier
python cli.py -f mon_texte.txt

# Lire depuis stdin (pipeline)
echo "putain c'est nul" | python cli.py

# Afficher le texte censuré
python cli.py --censor "va te faire foutre connard"

# Code de sortie uniquement (0 = propre, 1 = gros mots détectés)
python cli.py --propre "texte à vérifier"

# Désactiver les couleurs (logs, CI)
python cli.py --no-color "texte à vérifier"
```

Exemple de sortie :

```
✗ 2 gros mot(s) détecté(s) :

  [faible]   "bordel"
  [faible]   "merde"
```

---

### Microphone — Écoute en temps réel

Le modèle Vosk (~50 Mo) est téléchargé automatiquement au premier lancement.

```bash
# Démarrer l'écoute (modèle léger, recommandé)
python mic_listener.py

# Calibrer le microphone avant de démarrer
python mic_listener.py --calibrer

# Utiliser le grand modèle (1,4 Go, plus précis)
python mic_listener.py --modele grand

# Personnaliser le prénom dans l'alerte vocale
python mic_listener.py --nom Marie

# Toutes les options
python mic_listener.py --help
```

En cours d'écoute, chaque phrase reconnue est analysée en temps réel et un graphique matplotlib affiche les statistiques de session (top 10 mots, répartition par gravité).

---

## API Python

La bibliothèque `gros_mot` peut être importée directement dans vos projets.

```python
from gros_mot import detect, is_clean, censor

# Détection avec métadonnées
detections = detect("c'est quoi ce bordel de connard")
for d in detections:
    print(d.matched, d.severity, d.label)
    # bordel  1  faible
    # connard 2  modéré

# Vérification rapide
print(is_clean("bonjour tout le monde"))  # True
print(is_clean("putain c'est nul"))       # False

# Censure
print(censor("va te faire foutre"))
# va te faire ******
```

### Objet `Detection`

| Champ      | Type  | Description                              |
|------------|-------|------------------------------------------|
| `matched`  | `str` | Mot ou expression normalisé(e) détecté(e)|
| `original` | `str` | Fragment exact du texte source           |
| `start`    | `int` | Position de début dans le texte          |
| `end`      | `int` | Position de fin dans le texte            |
| `severity` | `int` | Niveau de gravité (1, 2 ou 3)            |
| `label`    | `str` | Libellé : `"faible"`, `"modéré"`, `"élevé"` |

---

## Niveaux de gravité

| Niveau | Label    | Exemples                                      |
|--------|----------|-----------------------------------------------|
| 1      | Faible   | merde, putain, bordel, tabarnak               |
| 2      | Modéré   | connard, salope, ta gueule, abruti            |
| 3      | Élevé    | insultes sexuelles, injures discriminatoires  |

---

## Modèles Vosk disponibles

| Nom     | Taille | Précision   | Utilisation                        |
|---------|--------|-------------|-------------------------------------|
| `petit` | ~50 Mo | Correcte    | Usage quotidien, machines modestes  |
| `grand` | 1,4 Go | Élevée      | Environnements silencieux, serveurs |

Les modèles sont fournis par [alphacephei.com/vosk](https://alphacephei.com/vosk/models) et téléchargés automatiquement dans le répertoire courant.

---

## Licence

MIT — libre d'utilisation, de modification et de distribution.
