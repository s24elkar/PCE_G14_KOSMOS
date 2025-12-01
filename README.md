<<<<<<< HEAD
# KOSMOS Video De-rush
=======
# KOSMOS Video De-rush ![CI](https://img.shields.io/github/actions/workflow/status/<OWNER>/<REPO>/ci.yml?branch=main)
>>>>>>> 501a24d (chore: ajouter packaging, docker, CI multi-OS et tests d’intégration)

## Visualisation rapide

Le module `kosmos_processing` se trouve dans `src/`.  
Depuis la racine du dépôt :

```bash
python -m kosmos_processing.visualize 250821_Kstereo/0122/0122.mp4 --frame 300
```

Vous pouvez aussi lancer le script directement :

```bash
python src/kosmos_processing/visualize.py 250821_Kstereo/0122/0122.mp4 --frame 300
```

Les fichiers `algos_correction.py` et `visualize.py` contiennent les fonctions de correction HE/DH, les outils de débruitage ainsi que la visualisation 4 panneaux (brut, déhaze, denoise, détections).
<<<<<<< HEAD
=======

## Tests d'intégration

Installer les dépendances puis lancer la suite :

```bash
python -m pip install -r requirements-dev.txt
pytest
```

Les tests couvrent la chaîne de correction d'image (déhaze + débruitage), la détection de mouvement et l'import KOSMOS (lecture JSON/CSV + calcul des seeks d'angles).  
Une pipeline GitHub Actions (`.github/workflows/ci.yml`) exécute automatiquement ces tests sur chaque push/PR pour Python 3.9, 3.10, 3.11 et 3.12 sur Ubuntu, macOS et Windows.

## Docker

Construire l'image (Python 3.11 par défaut, changeable via `--build-arg PYTHON_VERSION=3.9` par ex.) :

```bash
docker build -t kosmos .
```

Lancer la suite de tests en conteneur (commande par défaut) :

```bash
docker run --rm kosmos
```

Exécuter une commande différente, par exemple la visualisation ou l'appli :

```bash
docker run --rm kosmos python main.py
docker run --rm kosmos python -m kosmos_processing.visualize path/to/video.mp4 --frame 10
```

Note : le Dockerfile installe les dépendances graphiques minimales et force `QT_QPA_PLATFORM=offscreen` / `MPLBACKEND=Agg` pour tourner sans affichage. Pour un affichage natif, montez votre serveur X/Wayland ou désactivez `QT_QPA_PLATFORM`.

CD : lors d’un `push` (branches main/master ou tag `v*`), le workflow pousse l’image sur GHCR avec le tag `latest` ou le tag git (`ghcr.io/<OWNER>/kosmos:<tag>`), et publie les artefacts `sdist/wheel` en sortie de workflow.

## Installation et lancement GUI

Pré-requis système :
- Linux : `libgl1`, `libxext6`, `libxrender1`, `libxcb-cursor0`, `ffmpeg` (déjà installés dans l'image Docker).
- macOS : XQuartz ou environnement graphique standard (les wheels PyQt6 suffisent en général).
- Windows : rien de plus que Python 3.9+ (wheels PyQt6/Qt incluses).

Installation :
```bash
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt  # Windows: .venv\\Scripts\\pip ...
```

Lancement de l’app GUI :
```bash
QT_QPA_PLATFORM=offscreen MPLBACKEND=Agg python main.py    # mode headless (CI / conteneur)
# ou avec affichage natif si un serveur graphique est disponible :
python main.py
```

Fichiers d’exemple : `examples/sample_kosmos/0001/` contient un JSON, un CSV et un `systemEvent.csv` illustrant les formats attendus pour l’import KOSMOS.
>>>>>>> 501a24d (chore: ajouter packaging, docker, CI multi-OS et tests d’intégration)
