# KOSMOS Video De‑rush

Suite de dérushage vidéo pour campagnes sous‑marines : navigation par projet, tri des prises, visualisation multi‑angles et correction d’image, le tout orchestré via PyQt6 et un modèle MVC léger.

## ✨ Points clés

- **Accueil Campagne** – sélection ou création rapide de missions avec sauvegarde de l’historique.
- **Tri vidéo** – liste des clips, détails chronologiques verrouillés, renommage/suppression sécurisés et formulaires de métadonnées communes & propres.
- **Extraction** – explorateur de médias, lecteur vidéo instrumenté, histogrammes, outils d’export (capture, enregistrement, short, crop) et module de correction.
- **Traitement scientifique** – algos OpenCV/MoviePy dans `kosmos_processing` pour débruitage, HE/DH et visualisation multi‑panneaux.
- **Tests automatisés** – couverture unitaire sur les contrôleurs/vue principaux (PyTest).
- **Docker prêt à l’emploi** – image slim contenant Qt, OpenCV, MoviePy, etc., pour exécuter tests ou modules en environnement maîtrisé.

## 🧭 Architecture rapide

```
controllers/         Logique entre vues et modèles (accueil, tri, extraction…)
components/          Widgets PyQt6 réutilisables (explorateur, lecteur, formulaires…)
models/              State management (campagnes, vidéos, métadonnées, processing)
views/               Pages complètes (accueil, tri, extraction)
kosmos_processing/   Algorithmes vidéo et scripts de visualisation scientifique
tests/               Suite PyTest couvrant contrôleurs + composants critiques
```

Chaque écran suit un schéma MVC léger :
- **View** émet des signaux (`save_requested`, `video_selected`…)
- **Controller** écoute ces signaux, met à jour les **Model(s)** puis notifie la vue (refresh, dialogs)
- Les tests valident ces interactions sans devoir lancer l’UI.

## 🚀 Démarrage rapide

1. **Cloner et créer l’environnement**
   ```bash
   git clone https://github.com/sohaibelkarmi/Projet-KOSMOS.git
   cd Projet-KOSMOS
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Lancer les tests**
   ```bash
   pytest
   ```
3. **Essayer une vue (extraction)**
   ```bash
   python - <<'PY'
   import sys
   from PyQt6.QtWidgets import QApplication, QMainWindow
   from controllers import ExtractionController
   from models import MediaModel
   from views.extraction_view import ExtractionView

   app = QApplication.instance() or QApplication(sys.argv)
   view = ExtractionView()
   controller = ExtractionController(view, MediaModel())
   window = QMainWindow()
   window.setCentralWidget(view)
   window.resize(1600, 900)
   window.show()
   sys.exit(app.exec())
   PY
   ```

> Sur WSL/remote, assurez-vous d’avoir un serveur X11 (XQuartz, vcXsrv…) pour afficher l’UI.

## 🧪 Scripts scientifiques rapides

Visualisation 4 panneaux (brut/déhaze/denoise/détections) à partir de `kosmos_processing` :

```bash
python -m kosmos_processing.visualize 250821_Kstereo/0122/0122.mp4 --frame 300
```

ou depuis la racine :

```bash
python kosmos_processing/visualize.py 250821_Kstereo/0122/0122.mp4 --frame 300
```

## 📦 Requirements détaillés

Les dépendances Python sont listées dans `requirements.txt`. Principaux blocs :

- **PyQt6** – interface graphique (widgets, signaux/slots).
- **OpenCV (`opencv-python`)** – lecture vidéo, traitements d’image bas niveau.
- **NumPy / matplotlib** – manipulation de matrices et graphiques scientifiques.
- **MoviePy / imageio / imageio-ffmpeg** – encodage, export de clips, gestion audio/vidéo.
- **Ephem / pandas / pyqtgraph** – calculs astronomiques, manipulation de données tabulaires, graphiques interactifs.
- **PyTest** – exécution de la suite de tests.

> **Version Python recommandée :** 3.11 ou 3.12 (les tests locaux tournent avec 3.12).  
> **Dépendances système minimales :**
> - Linux (Debian/Ubuntu) : `sudo apt install python3-dev libgl1 ffmpeg`
> - macOS : `brew install python@3.11 ffmpeg`
> - Windows : privilégiez WSL2 ou la venv fournie ; assurez-vous d’avoir les Visual C++ redistributables.

## 🐍 Gestion des environnements

- **Venv locale** (défaut) : `python -m venv venv && source venv/bin/activate`.  
  Sur WSL, créez la venv sur le disque Linux (`/home/...`) pour éviter les problèmes de permissions lors de l’installation de PyQt6.
- **Gestionnaires alternatifs** : Poetry/Pipenv fonctionnent aussi en important `requirements.txt`.
- **Tests headless** : `tests/conftest.py` force `QT_QPA_PLATFORM=offscreen` pour pouvoir lancer PyQt6 sans serveur graphique pendant les tests.

## 🐳 Exécution via Docker

L’image Docker (basée sur `python:3.11-slim`) embarque :

- librairies système nécessaires (`ffmpeg`, `libgl1`, `libglib2.0-0`)
- toutes les dépendances Python de `requirements.txt`
- le code du projet copié dans `/app`
- la commande par défaut `pytest` (pour vérifier rapidement les régressions)

### Construire l’image

```bash
docker build -t projet-kosmos .
```

### Lancer les tests

```bash
docker run --rm projet-kosmos
```

### Exécuter un module interactif

```bash
docker run --rm -it projet-kosmos python main.py
```

> Qt requiert un affichage : sur Linux exportez `DISPLAY`, sur Windows/macOS utilisez un serveur X11 (XQuartz, vcXsrv) ou exécutez l’application en dehors du conteneur.

## 🛣️ Pistes à venir

- Finaliser l’intégration complète des écrans (workflow import → tri → extraction).
- Brancher la persistance (BD légère ou fichiers) pour métadonnées et campagnes.
- Ajouter des tests d’intégration (workflow multi-étapes) et génération de rapports d’export.
- Préparer un empaquetage utilisateur (Installer Windows / AppImage Linux).

---

### 💡 FAQ rapide

**Q : Puis-je modifier les champs “Nom / Date / Durée” directement ?**  
A : Non, ils sont verrouillés côté contrôleur pour garantir la cohérence. Utilisez le bouton *Renommer* ou les formulaires de métadonnées.

**Q : PyQt se plaint du plugin “xcb” ou du serveur d’affichage ?**  
A : Installez `libgl1` (Linux) et assurez-vous que `DISPLAY` est défini ou que `QT_QPA_PLATFORM=offscreen` est posé (c’est déjà fait pour les tests).

**Q : Comment contribuer ?**  
- Forkez le repo  
- Créez une branche (`feat/ma-fonctionnalite`)  
- Lancez `pytest` avant vos commits  
- Ouvrez une Pull Request descriptive (screenshots bienvenus)

---

👋 Besoin de contribuer ? Ouvrez une issue/PR ou lancez `pytest` avant vos commits pour garder la suite verte. Bonne exploration sous-marine ! 
