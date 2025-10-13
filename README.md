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
