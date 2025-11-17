"""
CONTRÔLEUR - Page d'extraction KOSMOS
Architecture MVC
Gère la logique de la page d'extraction (lecture, navigation, outils)
"""
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

# Ajout du chemin racine pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ExtractionKosmosController(QObject):
    """
    Contrôleur pour la page d'extraction.
    Gère les interactions entre la vue ExtractionView et le modèle ApplicationModel.
    """
    
    # Signal pour demander à l'application principale de changer de page
    navigation_demandee = pyqtSignal(str)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None # Sera défini lors de l'initialisation de la vue
        
        # État local pour les corrections
        self.brightness = 0
        self.contrast = 0

    def set_view(self, view):
        """Associe la vue à ce contrôleur"""
        self.view = view

    def load_initial_data(self):
        """
        Charge les données initiales dans la vue au démarrage.
        Récupère la liste des vidéos du modèle et met à jour l'explorateur.
        """
        if not self.view:
            return

        # Récupérer les vidéos de la campagne courante
        videos = self.model.obtenir_videos()
        
        # Formater pour la vue (l'explorateur attend une liste de dicts)
        videos_data = []
        for vid in videos:
            # On peut définir une couleur différente si la vidéo est traitée ou non
            color = "#00CBA9" if vid.est_conservee else "#FF6B6B"
            videos_data.append({
                'name': vid.nom,
                'thumbnail_color': color
            })
            
        # Mettre à jour la liste dans la vue
        self.view.update_video_list(videos_data)
        
        # Si une vidéo était déjà sélectionnée dans le modèle, on la charge
        if self.model.video_selectionnee:
            self.charger_video_dans_lecteur(self.model.video_selectionnee)

    # ═══════════════════════════════════════════════════════════════
    # GESTION DE LA NAVIGATION ET SÉLECTION
    # ═══════════════════════════════════════════════════════════════

    def on_tab_changed(self, tab_name):
        """Gère le changement d'onglet via la navbar"""
        # Mapping des noms d'onglets vers les IDs de pages
        tabs_map = {
            "Fichier": "accueil",
            "Tri": "tri",
            "Extraction": "extraction",
            "Évènements": "evenements"
        }
        if tab_name in tabs_map:
            self.navigation_demandee.emit(tabs_map[tab_name])

    def on_video_selected(self, video_name):
        """
        Appelé quand une vidéo est cliquée dans l'explorateur.
        Met à jour le modèle et demande à la vue de charger la vidéo.
        """
        # Mettre à jour le modèle
        video = self.model.selectionner_video(video_name)
        
        if video:
            self.charger_video_dans_lecteur(video)
        else:
            print(f"❌ Erreur: Vidéo '{video_name}' non trouvée dans le modèle.")

    def charger_video_dans_lecteur(self, video):
        """Prépare les données de la vidéo et met à jour le lecteur de la vue"""
        if not self.view:
            return

        # Préparer les métadonnées pour l'affichage dans le lecteur (overlay)
        # MODIFICATION : On mappe uniquement les champs acceptés par MetadataOverlay.update_metadata
        # Arguments acceptés : time, temp, salinity, depth, pression
        
        # Récupération sécurisée des valeurs (avec valeur par défaut '-')
        t_eau = video.metadata_propres.get('ctdDict_temperature', '-')
        if t_eau != '-': t_eau = f"{t_eau}°C"
        
        depth = video.metadata_propres.get('ctdDict_depth', '-')
        if depth != '-': depth = f"{depth} m"
        
        salinity = video.metadata_propres.get('ctdDict_salinity', '-')
        
        metadata_display = {
            "time": video.start_time_str,
            "temp": t_eau,
            "salinity": str(salinity),
            "depth": depth,
            # On ne passe PAS 'date', 'lat', 'lon' car le composant lecteur ne les gère pas
        }

        video_data = {
            'path': video.chemin,
            'metadata': metadata_display
        }

        # Demander à la vue de charger cette vidéo
        self.view.update_video_player(video_data)
        
        # Réinitialiser l'histogramme (simulation)
        self.view.update_histogram()

    # ═══════════════════════════════════════════════════════════════
    # CONTRÔLE DU LECTEUR
    # ═══════════════════════════════════════════════════════════════

    def on_play_pause(self):
        """Gère le bouton Play/Pause"""
        print("⏯️ Play/Pause demandé")

    def on_position_changed(self, position):
        """Gère le changement de position (slider)"""
        pass

    def on_previous_video(self):
        """Passe à la vidéo précédente dans la liste"""
        self._naviguer_video(-1)

    def on_next_video(self):
        """Passe à la vidéo suivante dans la liste"""
        self._naviguer_video(1)

    def on_rewind(self):
        """Recule de X secondes"""
        print("⏪ Retour arrière")

    def on_forward(self):
        """Avance de X secondes"""
        print("⏩ Avance rapide")

    def _naviguer_video(self, direction):
        """Logique interne pour changer de vidéo (précédente/suivante)"""
        videos = self.model.obtenir_videos()
        if not videos or not self.model.video_selectionnee:
            return

        current_name = self.model.video_selectionnee.nom
        
        # Trouver l'index actuel
        try:
            current_idx = -1
            for i, v in enumerate(videos):
                if v.nom == current_name:
                    current_idx = i
                    break
            
            if current_idx != -1:
                new_idx = (current_idx + direction) % len(videos)
                new_video = videos[new_idx]
                # Simuler un clic pour déclencher toute la chaîne de mise à jour
                self.on_video_selected(new_video.nom)
                
        except ValueError:
            pass

    # ═══════════════════════════════════════════════════════════════
    # CORRECTION D'IMAGE
    # ═══════════════════════════════════════════════════════════════

    def on_contrast_changed(self, value):
        """Gère le slider de contraste"""
        self.contrast = value
        print(f"🌗 Contraste modifié : {value}")

    def on_brightness_changed(self, value):
        """Gère le slider de luminosité"""
        self.brightness = value
        print(f"🔆 Luminosité modifiée : {value}")

    def on_color_correction(self):
        """Ouvre ou applique la correction colorimétrique automatique"""
        print("🎨 Correction colorimétrique auto demandée")

    # ═══════════════════════════════════════════════════════════════
    # OUTILS D'EXTRACTION
    # ═══════════════════════════════════════════════════════════════

    def on_screenshot(self):
        """Prend une capture d'écran de la vidéo à l'instant T"""
        if self.model.video_selectionnee:
            print(f"📸 Capture d'écran pour {self.model.video_selectionnee.nom}")
            self.view.show_message("Capture d'écran enregistrée", "success")

    def on_recording(self):
        """Démarre/Arrête l'enregistrement d'un extrait"""
        print("🔴 Enregistrement d'extrait activé/désactivé")

    def on_create_short(self):
        """Crée un short (extrait court format vertical ou spécifique)"""
        print("📱 Création de short demandée")

    def on_crop(self):
        """Active l'outil de recadrage"""
        print("✂️ Outil de recadrage activé")