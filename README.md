# KOSMOS Video De-rush

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

## Installation locale

1. Créez un environnement virtuel (optionnel mais recommandé) :
   ```bash
   python -m venv venv
   source venv/bin/activate  # sous Windows: venv\Scripts\activate
   ```
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Exécutez la batterie de tests :
   ```bash
   pytest
   ```

## Exécution via Docker

Une image Docker est fournie pour garantir un environnement reproductible (Qt, OpenCV, MoviePy, etc.).

### Construire l'image

```bash
docker build -t projet-kosmos .
```

### Lancer les tests automatisés

```bash
docker run --rm projet-kosmos
```

### Lancer l'application dans le conteneur

L'image installe toutes les dépendances nécessaires. Pour démarrer un module spécifique :

```bash
docker run --rm -it projet-kosmos python main.py
```

> **Remarque :** les interfaces PyQt nécessitent un serveur d'affichage. Sur Linux, partagez votre `DISPLAY`. Sous Windows ou macOS, utilisez une solution X11 adaptée (XQuartz, vcXsrv, etc.) ou exécutez l'application en dehors du conteneur.
