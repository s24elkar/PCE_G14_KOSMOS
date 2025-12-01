"""
CONTRÔLEUR - Page d'extraction KOSMOS
Architecture MVC
Gère la logique de la page d'extraction (lecture, navigation, outils)
"""
import datetime
import csv # AJOUT
import json
import sys
import cv2
import numpy as np
import subprocess
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QInputDialog

# Ajout du chemin racine pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class UnderwaterFilters:
    """
    Collection de filtres rapides (vectorisés) pour améliorer des images sous-marines.
    Les méthodes opèrent sur des frames BGR (numpy.ndarray uint8).
    """

    @staticmethod
    def correct_blue_dominance(frame: np.ndarray, factor: float = 0.12) -> np.ndarray:
        """
        Réduit une dominante bleue en renforçant légèrement les canaux R et G.
        :param factor: intensité de correction (0.12 => +12% sur R/G).
        """
        r, g, b = cv2.split(frame)
        r = cv2.add(r, (r * factor).astype(np.uint8))
        g = cv2.add(g, (g * factor).astype(np.uint8))
        corrected = cv2.merge((r, g, b))
        return np.clip(corrected, 0, 255).astype(np.uint8)

    @staticmethod
    def apply_gamma(frame: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        """
        Correction gamma via table de correspondance.
        gamma > 1 éclaircit les tons moyens.
        """
        gamma = max(gamma, 0.01)
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]).astype("uint8")
        return cv2.LUT(frame, table)

    @staticmethod
    def enhance_contrast(frame: np.ndarray, clip_limit: float = 2.0, tile_grid: tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        Améliore le contraste local via CLAHE sur la luminance (Y dans YCrCb).
        """
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
        y = clahe.apply(y)
        merged = cv2.merge((y, cr, cb))
        return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)

    @staticmethod
    def denoise(frame: np.ndarray, h: float = 10.0) -> np.ndarray:
        return cv2.fastNlMeansDenoisingColored(frame, None, h, h, 7, 21)

    @staticmethod
    def sharpen(frame: np.ndarray) -> np.ndarray:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(frame, -1, kernel)

    @staticmethod
    def apply_contrast_brightness(frame: np.ndarray, contrast: int, brightness: int) -> np.ndarray:
        """Ajuste le contraste et la luminosité. contrast/brightness de -100 à 100."""
        alpha = 1.0 + contrast / 100.0  # Facteur de contraste
        beta = brightness  # Décalage de luminosité
        adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        return adjusted

    @staticmethod
    def apply_saturation(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la saturation. value de -100 à 100."""
        if value == 0: return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        factor = 1.0 + value / 100.0
        s = np.clip(s * factor, 0, 255).astype(np.uint8)
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_hue(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la teinte. value de -90 à 90."""
        if value == 0: return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        # L'échelle de teinte dans OpenCV est 0-179
        h = (h.astype(np.int32) + value) % 180
        hsv = cv2.merge([h.astype(np.uint8), s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_temperature(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la température de couleur. value de -100 (froid) à 100 (chaud)."""
        if value == 0: return frame
        # Convertir la valeur en un ajustement pour les canaux bleu et rouge
        blue_factor = 1.0 - (value / 200.0 if value < 0 else 0)
        red_factor = 1.0 + (value / 200.0 if value > 0 else 0)
        b, g, r = cv2.split(frame)
        b = np.clip(b * blue_factor, 0, 255).astype(np.uint8)
        r = np.clip(r * red_factor, 0, 255).astype(np.uint8)
        return cv2.merge([b, g, r])

    @staticmethod
    def apply_lut(frame: np.ndarray, lut: list) -> np.ndarray:
        """Applique une table de correspondance (Look-Up Table)."""
        if len(lut) != 256: return frame
        table = np.array(lut, dtype=np.uint8)
        return cv2.LUT(frame, table)

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
        self.detached_window = None
        
        # Connecter tous les signaux de la vue ici
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.detach_requested.connect(self.on_detach_player)
            
        # Afficher la première vidéo conservée au lancement de la page Extraction
        if self.view and hasattr(self.view, 'view_shown'):
            self.view.view_shown.connect(self.load_first_video)

    def load_first_video(self):
        """
        Charge la première vidéo marquée comme "conservée" dans le lecteur.
        Cette méthode est appelée lorsque la page d'extraction devient visible.
        """
        if not self.model.campagne_courante:
            return

        videos_conservees = self.model.campagne_courante.obtenir_videos_conservees()
        if videos_conservees:
            premiere_video = videos_conservees[0]
            print(f"📹 Chargement de la première vidéo conservée : {premiere_video.nom}")
            self.charger_video_dans_lecteur(premiere_video)

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
            # Générer la miniature de la vidéo
            thumbnail_pixmap = self._generer_miniature_video(vid.chemin)
            color = "#00CBA9" if vid.est_conservee else "#FF6B6B"
            videos_data.append({
                'name': vid.nom,
                'thumbnail_pixmap': thumbnail_pixmap,
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

    def _charger_donnees_timeseries_csv(self, video):
        """Charge les données temporelles (temp, pression...) depuis le CSV."""
        video.timeseries_data = [] # Réinitialiser les données
        try:
            csv_path = Path(video.chemin).parent / f"{video.dossier_numero}.csv"
            if not csv_path.exists():
                print(f"⚠️ Fichier CSV non trouvé pour la vidéo: {csv_path}")
                self.view.video_player.set_timeseries_data([])
                return False

            with open(csv_path, 'r', encoding='utf-8') as f:
                # Détecter le délimiteur en lisant la première ligne
                first_line = f.readline()
                delimiter = ';' if ';' in first_line else ','
                f.seek(0) # Revenir au début du fichier
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # --- NOUVELLE LOGIQUE DE SYNCHRONISATION BASÉE SUR HMS ---
                
                def hms_to_seconds(hms_str):
                    """Convertit une chaîne 'HHhMMmSSs' en secondes totales."""
                    try:
                        parts = hms_str.lower().replace('s', '').split('h')
                        h = int(parts[0])
                        parts = parts[1].split('m')
                        m = int(parts[0])
                        s = int(parts[1])
                        return h * 3600 + m * 60 + s
                    except (ValueError, IndexError):
                        return None

                # Lire la première ligne de données pour obtenir l'heure de début
                all_rows = list(reader)
                if not all_rows:
                    return False

                start_hms_str = all_rows[0].get('HMS')
                start_total_seconds = hms_to_seconds(start_hms_str)

                if start_total_seconds is None:
                    print("❌ Erreur: Impossible de lire l'heure de début (colonne HMS) dans le CSV.")
                    return False

                # Mapper les noms de colonnes possibles vers les noms standard
                column_mapping = {
                    'pression': 'Pression',
                    'temperature': 'TempC',
                    'lux': 'Lux'
                }
                
                for row in all_rows:
                    processed_row = {}
                    current_hms_str = row.get('HMS')
                    current_total_seconds = hms_to_seconds(current_hms_str)

                    for standard_name, csv_name in column_mapping.items():
                        if csv_name in row and row[csv_name] and row[csv_name].strip():
                            value = row[csv_name].strip().replace(',', '.')
                            processed_row[standard_name] = value
                    
                    if current_total_seconds is not None:
                        delta_seconds = current_total_seconds - start_total_seconds
                        processed_row['timestamp_ms'] = int(delta_seconds * 1000)
                        video.timeseries_data.append(processed_row)

            print(f"✅ Données CSV chargées pour {video.nom}: {len(video.timeseries_data)} points.")
            return True
        except Exception as e:
            print(f"❌ Erreur lecture CSV (extraction): {e}")
            return False

    def charger_video_dans_lecteur(self, video):
        """Prépare les données de la vidéo et met à jour le lecteur de la vue"""
        if not self.view:
            return

        # --- AJOUT IMPORTANT : Recharger les métadonnées depuis le JSON ---
        self._charger_metadonnees_propres_json(video)
        self._charger_metadonnees_communes_json(video)
        self._charger_donnees_timeseries_csv(video) # AJOUT
        # --- FIN AJOUT ---

        # Préparer les métadonnées STATIQUES pour l'affichage.
        # On ne passe QUE le temps de départ. Le reste (temp, pression, lux)
        # sera géré dynamiquement par le lecteur à partir des données CSV.
        metadata_display = {
            "time": video.start_time_str,
        }

        video_data = {
            'path': video.chemin,
            'metadata': metadata_display,
            'timeseries_data': video.timeseries_data # CORRECTION: Utiliser les données chargées
        }

        # Demander à la vue de charger cette vidéo
        self.view.update_video_player(video_data)

    # ═══════════════════════════════════════════════════════════════
    # CONTRÔLE DU LECTEUR
    # ═══════════════════════════════════════════════════════════════

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
        self.detached_window = DetachedPlayerWindow(video_player, parent=None)
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
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast_base', UnderwaterFilters.apply_contrast_brightness, value != 0 or self.brightness != 0, contrast=self.contrast, brightness=self.brightness)

    def on_brightness_changed(self, value):
        """Gère le slider de luminosité"""
        self.brightness = value
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast_base', UnderwaterFilters.apply_contrast_brightness, self.contrast != 0 or value != 0, contrast=self.contrast, brightness=self.brightness)

    def on_color_correction(self):
        """Ouvre ou applique la correction colorimétrique automatique"""
        if not self.view or not hasattr(self.view, 'video_player'):
            return

        # Appliquer une chaîne de filtres par défaut
        self.view.video_player.toggle_filter('gamma', UnderwaterFilters.apply_gamma, True, gamma=1.2)
        self.view.video_player.toggle_filter('blue_correction', UnderwaterFilters.correct_blue_dominance, True, factor=0.15)
        self.view.video_player.toggle_filter('contrast', UnderwaterFilters.enhance_contrast, True, clip_limit=1.5)
        
        # Mettre à jour l'état des boutons de filtre dans le composant ImageCorrection
        self.view.image_correction.update_filter_buttons_state({
            'gamma': True,
            'blue_correction': True,
            'contrast': True,
            'denoise': self.view.video_player.is_filter_active('denoise'),
            'sharpen': self.view.video_player.is_filter_active('sharpen')
        })
        self.view.show_message("Correction automatique appliquée.", "success")

    def on_toggle_gamma(self, toggled):
        """Active ou désactive la correction gamma."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('gamma', UnderwaterFilters.apply_gamma, toggled, gamma=1.2)

    def on_toggle_contrast(self, toggled):
        """Active ou désactive l'amélioration du contraste."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast', UnderwaterFilters.enhance_contrast, toggled, clip_limit=1.5)

    def on_toggle_denoise(self, toggled):
        """Active ou désactive la réduction de bruit."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('denoise', UnderwaterFilters.denoise, toggled, h=10.0)

    def on_toggle_sharpen(self, toggled):
        """Active ou désactive le filtre de netteté."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('sharpen', UnderwaterFilters.sharpen, toggled)

    def on_reset_filters(self):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.reset_filters()

    def on_saturation_changed(self, value):
        """Gère le slider de saturation."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('saturation', UnderwaterFilters.apply_saturation, value != 0, value=value)

    def on_hue_changed(self, value):
        """Gère le slider de teinte."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('hue', UnderwaterFilters.apply_hue, value != 0, value=value)

    def on_temperature_changed(self, value):
        """Gère le slider de température."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('temperature', UnderwaterFilters.apply_temperature, value != 0, value=value)

    def on_curve_changed(self, lut):
        """Gère le changement de la courbe tonale."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('curve', UnderwaterFilters.apply_lut, True, lut=lut)

    # ═══════════════════════════════════════════════════════════════
    # OUTILS D'EXTRACTION
    # ═══════════════════════════════════════════════════════════════

    def on_screenshot(self):
        from PyQt6.QtWidgets import QMessageBox
        """Active le mode de sélection sur le lecteur vidéo pour une capture d'écran."""
        if not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return
        
        if not self.view or not hasattr(self.view, 'video_player'):
            return
            
        # Créer une boîte de dialogue pour demander le type de capture
        msg_box = QMessageBox(self.view)
        msg_box.setWindowTitle("Type de capture")
        msg_box.setText("Quel type de capture d'écran souhaitez-vous effectuer ?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # Ajouter les boutons personnalisés
        btn_full = msg_box.addButton("Image complète", QMessageBox.ButtonRole.YesRole)
        btn_crop = msg_box.addButton("Sélectionner une zone", QMessageBox.ButtonRole.NoRole)
        msg_box.addButton("Annuler", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == btn_full:
            # Capture de l'image complète : on appelle directement grab_frame sans rectangle
            self.view.video_player.grab_frame(None)
        elif clicked_button == btn_crop:
            # Sélection d'une zone : on active le mode de recadrage
            self.view.show_message("Dessinez un rectangle sur la vidéo pour capturer une zone.", "info")
            self.view.video_player.start_cropping()

    def on_crop_area_selected(self, crop_rect):
        """Slot appelé lorsque l'utilisateur a sélectionné une zone à capturer."""
        # Demande au lecteur de capturer l'image, en lui passant la zone à recadrer.
        self.view.video_player.grab_frame(crop_rect)

    def save_captured_frame(self, frame: 'QPixmap'):
        """
        Reçoit le QPixmap (déjà recadré si nécessaire), demande un nom à l'utilisateur,
        puis sauvegarde l'image.
        """
        if not frame:
            self.view.show_message("Impossible de capturer l'image de la vidéo.", "error")
            return

        # 1. Demander le nom de la capture maintenant, après la sélection.
        capture_name, ok_pressed = QInputDialog.getText(
            self.view,
            "Nommer la capture",
            "Entrez le nom de la capture (sans extension) :",
        )

        if not ok_pressed or not capture_name:
            self.view.show_message("Capture annulée.", "info")
            return

        self.pending_capture_name = capture_name

        # 2. Définir le chemin de sauvegarde
        workspace = self.model.campagne_courante.workspace_extraction
        if not workspace:
            self.view.show_message("Dossier d'extraction non défini pour la campagne.", "error")
            return

        # Créer un sous-dossier "captures" pour une meilleure organisation
        captures_dir = Path(workspace) / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)

        # 3. Utiliser le nom fourni par l'utilisateur
        filename = f"{self.pending_capture_name}.png"
        save_path = captures_dir / filename

        # 4. Sauvegarder l'image (qui est déjà recadrée)
        try:
            frame.save(str(save_path), "png", -1)
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
        if not self.view or not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

        # Calculer la position actuelle en fonction de la frame courante
        video_thread = self.view.video_player.video_thread
        if video_thread.total_frames == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return
            
        current_pos_ms = int((video_thread.current_frame / video_thread.fps) * 1000)
        duration_ms = self.view.video_player.duration

        if duration_ms == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return

        # 1. Définir la plage de sélection initiale (position actuelle + 30s)
        initial_start_ms = current_pos_ms
        initial_end_ms = min(duration_ms, current_pos_ms + 30000)

        # 2. Ouvrir la nouvelle fenêtre d'édition
        from components.clip_editor_dialog import ClipEditorDialog
        dialog = ClipEditorDialog(
            self.model.video_selectionnee.chemin,
            initial_start_ms,
            initial_end_ms,
            self.view
        )
        
        accepted = dialog.exec()

        # 3. Si l'utilisateur a validé, créer l'extrait final
        if not accepted:
            self.view.show_message("Enregistrement annulé.", "info")
            return

        try:
            rec_name, final_start_ms, final_end_ms = dialog.get_values()
            
            final_start_str = str(datetime.timedelta(milliseconds=final_start_ms))
            final_duration_s = (final_end_ms - final_start_ms) / 1000

            recordings_dir = Path(self.model.campagne_courante.workspace_extraction) / "recordings"
            recordings_dir.mkdir(parents=True, exist_ok=True)
            final_output_path = recordings_dir / f"{rec_name}.mp4"

            self.view.show_message("Enregistrement de l'extrait final...", "info")
            cmd_final = [
                'ffmpeg', '-ss', final_start_str, '-i', self.model.video_selectionnee.chemin,
                '-t', str(final_duration_s), '-c', 'copy', '-y', str(final_output_path)
            ]
            subprocess.run(cmd_final, check=True, capture_output=True, text=True)
            self.view.show_message(f"Enregistrement '{rec_name}.mp4' sauvegardé !", "success")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = e.stderr if isinstance(e, subprocess.CalledProcessError) else "ffmpeg non trouvé."
            self.view.show_message(f"Erreur enregistrement final: {error_msg}", "error")
                    
    def on_create_short(self):
        """Crée un short (extrait court format vertical ou spécifique)"""
        if not self.view or not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

        # 1. Obtenir la position actuelle et la durée totale
        player = self.view.video_player
        video_thread = player.video_thread
        
        if video_thread.total_frames == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return
            
        current_pos_ms = int((video_thread.current_frame / video_thread.fps) * 1000)
        total_duration_ms = player.duration

        if total_duration_ms == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return

        # 2. NOUVEAU : Demander à l'utilisateur de choisir la durée du short
        durations = ["10 secondes", "20 secondes", "30 secondes"]
        selected_duration_str, ok = QInputDialog.getItem(
            self.view,
            "Choisir la durée du Short",
            "Quelle durée pour votre short ?",
            durations,
            0,  # index par défaut
            False # non-éditable
        )

        if not ok:
            self.view.show_message("Création du short annulée.", "info")
            return

        # Extraire la durée en secondes (ex: "10 secondes" -> 10)
        clip_duration_s = int(selected_duration_str.split()[0])

        # 3. Calculer les temps de début et de fin en fonction de la durée choisie
        start_ms = max(0, current_pos_ms - (clip_duration_s * 1000 // 2))
        end_ms = min(total_duration_ms, start_ms + (clip_duration_s * 1000))
        clip_duration_s = (end_ms - start_ms) / 1000

        # Convertir en format HH:MM:SS.ms pour ffmpeg
        start_time_str = str(datetime.timedelta(milliseconds=start_ms))

        # 3. Définir les chemins temporaires
        extraction_dir = Path(self.model.campagne_courante.workspace_extraction)
        shorts_dir = extraction_dir / "shorts"
        shorts_dir.mkdir(parents=True, exist_ok=True)
        temp_preview_path = shorts_dir / f"~preview_temp.mp4"

        # 4. Créer un aperçu accéléré avec ffmpeg
        try:
            self.view.show_message("Création de l'aperçu...", "info")
            # Commande ffmpeg pour créer un aperçu x2, basse qualité
            cmd_preview = [
                'ffmpeg',
                '-ss', start_time_str,
                '-i', self.model.video_selectionnee.chemin,
                '-t', str(clip_duration_s),
                # Filtre pour accélération x2 uniquement, sans recadrage vertical
                '-vf', 'setpts=0.5*PTS',
                '-af', 'atempo=2.0',      # Accélère l'audio x2
                '-preset', 'ultrafast',  # Encodage très rapide
                '-crf', '28',            # Qualité plus basse pour la vitesse,
                '-y', str(temp_preview_path)
            ]
            subprocess.run(cmd_preview, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_msg = e.stderr if isinstance(e, subprocess.CalledProcessError) else "ffmpeg non trouvé."
            self.view.show_message(f"Erreur création aperçu: {error_msg}", "error")
            return

        # 5. Afficher la boîte de dialogue d'aperçu
        from components.short_preview_dialog import ShortPreviewDialog
        preview_dialog = ShortPreviewDialog(str(temp_preview_path), self.view)
        
        accepted = preview_dialog.exec()

        try:
            # 6. Si l'utilisateur a cliqué sur "Enregistrer" et entré un nom
            if accepted:
                short_name = preview_dialog.get_short_name()

                # Le temps de début a déjà été calculé pour l'aperçu, nous le réutilisons.
                # La durée est 'clip_duration_s' définie au début.
                start_ms_final = start_ms
                start_time_str_final = str(datetime.timedelta(milliseconds=start_ms_final))

                try:
                    if not short_name:
                        self.view.show_message("Enregistrement annulé : nom vide.", "warning")
                        return # Ce return est maintenant à l'intérieur du try...except, donc le finally sera appelé.

                    self.view.show_message("Enregistrement du short final...", "info")
                    final_output_path = shorts_dir / f"{short_name}.mp4"
                    # Commande ffmpeg pour créer le clip final en qualité originale
                    cmd_final = [
                        'ffmpeg',
                        '-ss', start_time_str_final,
                        '-i', self.model.video_selectionnee.chemin,
                        '-t', str(clip_duration_s),
                        # On ne recadre plus, donc on peut copier le flux pour garder la qualité et la vitesse
                        '-c', 'copy',
                        '-y', str(final_output_path)
                    ]
                    subprocess.run(cmd_final, check=True, capture_output=True, text=True)
                    self.view.show_message(f"Short '{short_name}.mp4' enregistré !", "success")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    error_msg = e.stderr if isinstance(e, subprocess.CalledProcessError) else "ffmpeg non trouvé."
                    self.view.show_message(f"Erreur enregistrement final: {error_msg}", "error")

            else:
                self.view.show_message("Enregistrement annulé.", "info")

        finally:
            # 7. Nettoyer le fichier d'aperçu temporaire dans tous les cas
            if temp_preview_path.exists():
                try:
                    temp_preview_path.unlink()
                    print("🗑️ Fichier d'aperçu temporaire supprimé.")
                except OSError as e:
                    print(f"❌ Erreur suppression fichier temporaire: {e}")

    def on_crop(self):
        """Active l'outil de recadrage"""
        print("✂️ Outil de recadrage activé")

    def _generer_miniature_video(self, chemin_video):
        """
        Génère une miniature (QPixmap) à partir de la première frame d'une vidéo.
        Args:
            chemin_video: Chemin vers le fichier vidéo
        Returns:
            QPixmap ou None si échec
        """
        try:
            import cv2
            from PyQt6.QtGui import QImage, QPixmap
            cap = cv2.VideoCapture(chemin_video)
            if not cap.isOpened():
                print(f"⚠️ Impossible d'ouvrir la vidéo : {chemin_video}")
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                print(f"⚠️ Impossible de lire la première frame : {chemin_video}")
                return None
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame_rgb.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            return pixmap
        except Exception as e:
            print(f"❌ Erreur génération miniature pour {chemin_video}: {e}")
            return None