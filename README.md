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

## Intégration U-Net DeepSeaEnhance

L’onglet *Extraction* embarque désormais le modèle U-Net de `DeepSeaEnhance`. Pour que le bouton **Améliorer (U-Net)** fonctionne :

1. Placez le dépôt DeepSeaEnhance à côté du présent projet ou définissez la variable d’environnement `KOSMOS_DEEPSEA_ROOT` vers son chemin absolu (le wrapper cherchera `config/config.yaml` et `weights/best_model.pt`).
2. Installez les dépendances nécessaires :
   ```bash
   pip install torch torchvision opencv-python pyyaml
   ```
   (ajoutez `onnxruntime` et `tensorrt` si vous comptez activer d’autres moteurs d’inférence).
3. Lancez ensuite l’application PyQt6 (`python src/main.py`) ; le bouton d’amélioration ouvre un sélecteur d’image, exécute le modèle et affiche le résultat ainsi que la latence mesurée.
