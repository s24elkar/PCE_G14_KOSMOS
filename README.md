# KOSMOS 

Logiciel de derushage pour vidéos sous-marines.

Aperçu du logiciel 

<img width="1919" height="1137" alt="Capture d&#39;écran 2025-12-14 164431" src="https://github.com/user-attachments/assets/52f4d56e-e292-4786-8a30-9df2c53b3b61" />


<img width="1919" height="1134" alt="Capture d&#39;écran 2025-12-14 164616" src="https://github.com/user-attachments/assets/96e9cfb7-6f7e-4457-8537-e6f01122428e" />

## Architecture

### Structure MVC
- **Model** (`models/`) : Gestion des données (campagnes, vidéos, métadonnées)
- **View** (`views/`) : Interfaces graphiques PyQt6
- **Controller** (`controllers/`) : Logique métier et orchestration
- **Components** (`components/`) : Composants réutilisables (lecteur, explorateur, outils)


  <img width="1892" height="2044" alt="Architecture_kosmos_finale" src="https://github.com/user-attachments/assets/4259ab63-52bd-4ebb-8575-234f2038b895" />


### Technologies
- **Interface** : PyQt6
- **Vidéo** : OpenCV (lecture, filtres)
- **Export** : FFmpeg (encodage H.264 + AAC)
- **Métadonnées** : JSON (statiques), CSV (temporelles)
- **Réseau** : Paramiko (SSH/SFTP)

## Fonctionnalités

### Page Accueil
- Création et ouverture de campagnes
- Importation automatique depuis structure KOSMOS (dossiers numérotés)
- Détection intelligente (config JSON existant ou nouvelle campagne)

### Page Tri
- Marquage vidéos (conservées/supprimées)
- Édition métadonnées (propres/communes)
- Enrichissement via APIs externes (météo Open-Meteo, astronomie wttr.in)
- Propagation automatique des métadonnées communes

### Page Extraction
- **Lecteur vidéo** : OpenCV avec overlay métadonnées synchronisées
- **Filtres temps réel** : Gamma, contraste CLAHE, netteté, débruitage, correction bleue, saturation, teinte, température
- **Outils d'extraction** :
  - Screenshots (complète ou zone sélectionnée)
  - Recordings (extrait avec éditeur de plage)
  - Shorts (format vertical 9:16, aperçu accéléré x2)
- **Export avec filtres** : Pipeline OpenCV → FFmpeg (stdin)
- **Détachement lecteur** : Fenêtre flottante pour second écran

### Page Téléchargement
- Transfert SSH/SFTP depuis matériel KOSMOS embarqué
- Suppression distante après transfert
- Workers Qt asynchrones (interface non bloquante)

## Structure Données KOSMOS
```
Campagne/
├── 0113/
│   ├── 0113.mp4              # Vidéo
│   ├── 0113.json             # Métadonnées statiques (GPS, CTD, campagne)
│   ├── 0113.csv              # Métadonnées temporelles (HMS, TempC, Pression, Lux)
│   └── systemEvent.csv       # Événements (START MOTEUR, START ENCODER)
├── extraction/
│   ├── captures/             # Screenshots PNG
│   ├── recordings/           # Extraits MP4
│   └── shorts/               # Shorts 9:16 MP4
└── NomCampagne_config.json   # Configuration campagne
```

## Installation

### Prérequis
- Python 3.10+
- FFmpeg (accessible dans PATH)
- VLC media player pour éviter les problèmes d'encodage 

### Dépendances
```bash
pip install PyQt6 opencv-python numpy paramiko requests
```
```installer ffmpeg
winget install ffmpeg
```


### Lancement
```bash
python main.py
```

### Docker

Construire l'image (Python 3.11 par défaut, changeable via `--build-arg PYTHON_VERSION=3.9` par ex.) :

```bash
docker build -t kosmos .
```

Lancer la suite de tests en conteneur (commande par défaut) :

```bash
docker run --rm kosmos
```

Exécuter l'appli :

```bash
docker run --rm kosmos python main.py
```

## Création d'un exécutable 

### Installer pyinstaller 
```bash
pip install pyinstaller
```
### Créer l'exécutable 
```bash
python -m PyInstaller --noconsole --onedir --name "KosmosExpert" --add-data "assets;assets" --collect-all ultralytics --hidden-import="sklearn.utils._typedefs" --hidden-import="sklearn.neighbors._partition_nodes" main.py
```

## Auteur 
Projet développé dans un cadre académique par : 
- Inès OUALDI-DJEBRIL
- Junior BINI
- Romain CHRISTOL
- Divine BANON
- Sohaib EL KARMI
