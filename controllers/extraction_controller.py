"""
CONTRÔLEUR - Page d'extraction KOSMOS
Architecture MVC
Gère la logique de la page d'extraction (lecture, navigation, outils)
"""
import datetime
import json
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QInputDialog

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
        self.pending_capture_name = None # Pour stocker le nom de la capture
        
    def set_view(self, view):
        """Associe la vue à ce contrôleur"""
        self.view = view
        # C'est le bon endroit pour connecter les signaux de la vue,
        # car nous sommes sûrs que self.view est défini.
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.frame_captured.connect(self.save_captured_frame)

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

    def _charger_metadonnees_propres_json(self, video):
        """Charge les métadonnées propres (section 'video') depuis le JSON."""
        try:
            json_path = Path(video.chemin).parent / f"{video.dossier_numero}.json"
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video.metadata_propres.clear()
            
            def flatten_dict(section_data, prefix=''):
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        flatten_dict(value, prefix=f"{prefix}{key}_")
                    else:
                        full_key = f"{prefix}{key}"
                        video.metadata_propres[full_key] = str(value) if value is not None else ""

            if 'video' in data:
                flatten_dict(data['video'])
            return True
        except Exception as e:
            print(f"❌ Erreur lecture JSON propres (extraction): {e}")
            return False

    def _charger_metadonnees_communes_json(self, video):
        """Charge les métadonnées communes ('system', 'campaign') depuis le JSON."""
        try:
            json_path = Path(video.chemin).parent / f"{video.dossier_numero}.json"
            if not json_path.exists(): return False

            with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
            video.metadata_communes.clear()

            def flatten_dict(d, p=''):
                for k, v in d.items():
                    if isinstance(v, dict): flatten_dict(v, f"{p}{k}_")
                    else: video.metadata_communes[f"{p}{k}"] = str(v) if v is not None else ""
            
            if 'system' in data: flatten_dict(data['system'], "system_")
            if 'campaign' in data: flatten_dict(data['campaign'], "campaign_")
            return True
        except Exception as e:
            print(f"❌ Erreur lecture JSON communes (extraction): {e}")
            return False

    def charger_video_dans_lecteur(self, video):
        """Prépare les données de la vidéo et met à jour le lecteur de la vue"""
        if not self.view:
            return

        # --- AJOUT IMPORTANT : Recharger les métadonnées depuis le JSON ---
        self._charger_metadonnees_propres_json(video)
        self._charger_metadonnees_communes_json(video)
        # --- FIN AJOUT ---

        # Préparer les métadonnées pour l'affichage dans le lecteur (overlay)
        # MODIFICATION : On mappe uniquement les champs acceptés par MetadataOverlay.update_metadata
        # Arguments acceptés : time, temp, salinity, depth, pression
        
        # Récupération sécurisée des valeurs (avec valeur par défaut '-')
        t_eau = video.metadata_propres.get('ctdDict_temperature', '-') # AJOUT DU _
        if t_eau != '-': t_eau = f"{t_eau}°C"
        
        depth = video.metadata_propres.get('ctdDict_depth', '-') # AJOUT DU _
        if depth != '-': depth = f"{depth} m"
        
        salinity = video.metadata_propres.get('ctdDict_salinity', '-') # AJOUT DU _
        
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

    def set_view(self, view):
        """Associe la vue à ce contrôleur"""
        self.view = view
        self.detached_window = None  # AJOUT
        
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.frame_captured.connect(self.save_captured_frame)
            # AJOUT : Connecter le signal de détachement
            self.view.video_player.detach_requested.connect(self.on_detach_player)

    def on_detach_player(self):
        """Détache le lecteur dans une nouvelle fenêtre"""
        if not self.view or not hasattr(self.view, 'video_player'):
            return
        
        # Importer la fenêtre détachée
        from components.detached_player import DetachedPlayerWindow
        
        # Sauvegarder la référence au layout parent
        if not hasattr(self, 'video_player_parent_layout'):
            # Trouver le parent layout (normalement center_right_layout)
            self.video_player_parent_layout = self.view.video_player.parent().layout()
            self.video_player_parent_index = self.video_player_parent_layout.indexOf(self.view.video_player)
        
        # Retirer le lecteur de la vue principale
        video_player = self.view.video_player
        self.video_player_parent_layout.removeWidget(video_player)
        video_player.setParent(None)
        
        # Créer la fenêtre détachée
        self.detached_window = DetachedPlayerWindow(video_player, self.view)
        self.detached_window.closed.connect(self.on_reattach_player)
        self.detached_window.show()
        
        print("🗗 Lecteur détaché dans une nouvelle fenêtre")

    def on_reattach_player(self):
        """Réattache le lecteur à la vue principale"""
        if not self.detached_window or not self.view:
            return
        
        # Récupérer le lecteur
        video_player = self.detached_window.video_player
        video_player.setParent(self.view)
        
        # Réinsérer dans le layout à la bonne position
        if hasattr(self, 'video_player_parent_layout') and hasattr(self, 'video_player_parent_index'):
            self.video_player_parent_layout.insertWidget(
                self.video_player_parent_index, 
                video_player, 
                stretch=5
            )
        
        # Nettoyer
        self.detached_window.deleteLater()
        self.detached_window = None
        
        print("🔗 Lecteur réattaché à la vue principale")
        
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
        """Demande un nom pour la capture, puis demande au lecteur de la prendre."""
        if not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

        # 1. Boîte de dialogue pour saisir le nom de la capture
        capture_name, ok_pressed = QInputDialog.getText(
            self.view,
            "Nommer la capture",
            "Entrez le nom de la capture (sans extension) :",
        )

        # 2. Si l'utilisateur a validé et entré un nom
        if ok_pressed and capture_name:
            self.pending_capture_name = capture_name
            # 3. Demande au lecteur de capturer l'image. La sauvegarde suivra.
            self.view.video_player.grab_frame()
        else:
            print("❌ Capture annulée ou nom vide.")

    def save_captured_frame(self, frame: 'QPixmap'):
        if not frame or not self.pending_capture_name:
            self.view.show_message("Impossible de capturer l'image de la vidéo.", "error")
            return

        # 2. Définir le chemin de sauvegarde
        save_dir = Path(self.model.campagne_courante.emplacement)
        
        if not save_dir:
            self.view.show_message("Emplacement de la campagne non défini.", "error")
            return

        # Créer un sous-dossier "captures" pour une meilleure organisation
        captures_dir = save_dir / "captures"
        captures_dir.mkdir(exist_ok=True)

        # 3. Utiliser le nom fourni par l'utilisateur
        filename = f"{self.pending_capture_name}.jpg"
        save_path = captures_dir / filename

        # 4. Sauvegarder l'image
        try:
            frame.save(str(save_path), "jpg", 95)
            self.view.show_message(f"Capture enregistrée : {filename}", "success")
            print(f"📸 Capture d'écran enregistrée sous : {save_path}")
        except Exception as e:
            self.view.show_message(f"Erreur lors de la sauvegarde : {e}", "error")
            print(f"❌ Erreur sauvegarde capture : {e}")
        finally:
            # Réinitialiser le nom pour la prochaine capture
            self.pending_capture_name = None
            
    def on_recording(self):
        """Démarre/Arrête l'enregistrement d'un extrait"""
        print("🔴 Enregistrement d'extrait activé/désactivé")

    def on_create_short(self):
        """Crée un short (extrait court format vertical ou spécifique)"""
        print("📱 Création de short demandée")

    def on_crop(self):
        """Active l'outil de recadrage"""
        print("✂️ Outil de recadrage activé")