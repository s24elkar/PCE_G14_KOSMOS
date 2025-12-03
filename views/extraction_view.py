"""
Vue Extraction - Page d'extraction vidéo
Architecture MVC pour logiciel de dérushage
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QPushButton, QGroupBox, QVBoxLayout
# Ajouter le répertoire parent au path pour pouvoir importer les modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal

# Import des composants depuis components/
from components.navbar import NavBar
from components.explorateur import MediaExplorer
from components.lecteur import VideoPlayer
from components.correction import ImageCorrection
from components.histogramme import Histogram
from components.courbe_tonale import ToneCurveEditor # AJOUT
from components.outils_modification import ExtractionTools


class ExtractionView(QWidget):
    """
    Vue pour la page Extraction
    Layout en grille 3x2:
    - Col 1: Explorateur (haut) + Outils (bas)
    - Col 2-3: Lecteur (haut) + Correction (bas col 2) + Histogramme (bas col 3)
    """
    # Signal émis lorsque la vue est affichée pour la première fois
    view_shown = pyqtSignal()
    
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._is_first_show = True
        self.init_ui()
        
    def showEvent(self, event):
        """Surcharge de l'événement d'affichage."""
        super().showEvent(event)
        # Émettre le signal uniquement la première fois que la vue est montrée
        if self._is_first_show:
            self.view_shown.emit()
            self._is_first_show = False
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ============================================================
        # NAVBAR (Barre de navigation en haut)
        # ============================================================
        try:
            self.navbar = NavBar(
                tabs=["Fichier", "Tri", "Extraction", "Évènements"],
                default_tab="Extraction"
            )
            # Forcer le fond blanc de la navbar
            self.navbar.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-bottom: 1px solid #e0e0e0;
                    font-family: 'Montserrat';
                }
            """)
            main_layout.addWidget(self.navbar)
        except Exception as e:
            print(f"⚠️ Erreur chargement navbar: {e}")
            navbar_placeholder = QLabel("NAVBAR")
            navbar_placeholder.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
            main_layout.addWidget(navbar_placeholder)
        
        # ============================================================
        # CONTENU PRINCIPAL (Layout en GRILLE 3 colonnes x 2 lignes)
        # ============================================================
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: black;")
        
        # Utiliser QGridLayout pour la grille
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(10, 10, 10, 10)
        grid_layout.setSpacing(10)
        
        # ────────────────────────────────────────────────────────────
        # COLONNE 1 (Ligne 1 + 2) - Explorateur + Outils
        # ────────────────────────────────────────────────────────────
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        
        # Explorateur de média (en haut de la colonne 1)
        try:
            self.media_explorer = MediaExplorer()
            left_column.addWidget(self.media_explorer, stretch=1)
        except Exception as e:
            print(f"⚠️ Erreur chargement explorateur: {e}")
            explorer_placeholder = QLabel("EXPLORATEUR\nDE MÉDIA")
            explorer_placeholder.setStyleSheet("""
                background-color: #1a1a1a; 
                color: white; 
                padding: 20px;
                border: 2px solid white;
            """)
            explorer_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_column.addWidget(explorer_placeholder, stretch=1)
        
        # Outils d'extraction (en bas de la colonne 1)
        try:
            self.extraction_tools = ExtractionTools()
            left_column.addWidget(self.extraction_tools, stretch=1)
        except Exception as e:
            print(f"⚠️ Erreur chargement outils: {e}")
            tools_placeholder = QLabel("OUTILS\nD'EXTRACTION")
            tools_placeholder.setStyleSheet("""
                background-color: #1a1a1a; 
                color: white; 
                padding: 20px;
                border: 2px solid white;
            """)
            tools_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_column.addWidget(tools_placeholder, stretch=1)
        
        # Créer un widget container pour la colonne gauche
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        
        left_widget.setMinimumWidth(300)  
        left_widget.setMaximumWidth(380) 
    
        
        # Ajouter la colonne gauche à la grille (colonne 0, lignes 0-1)
        grid_layout.addWidget(left_widget, 0, 0, 2, 1)
        
        # ────────────────────────────────────────────────────────────
        # COLONNE 2-3 (Lecteur prend toute la hauteur)
        # ────────────────────────────────────────────────────────────
        
        center_right_layout = QVBoxLayout()
        center_right_layout.setSpacing(10)
        
        # Lecteur vidéo (prend environ 55% de la hauteur)
        try:
            self.video_player = VideoPlayer()
            center_right_layout.addWidget(self.video_player, stretch=5)
        except Exception as e:
            print(f"⚠️ Erreur chargement lecteur: {e}")
            player_placeholder = QLabel("LECTEUR VIDÉO")
            player_placeholder.setStyleSheet("""
                background-color: #2a2a2a; 
                color: white; 
                padding: 50px;
                border: 2px solid white;
            """)
            player_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            center_right_layout.addWidget(player_placeholder, stretch=5)
        
        # Zone du bas : Correction + Histogramme côte à côte (45% de la hauteur)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # Correction d'images (gauche)
        try:
            self.image_correction = ImageCorrection()
            self.image_correction.setStyleSheet("""
                    background-color: black;
                    border: 2px solid white;
            """)
            bottom_layout.addWidget(self.image_correction, stretch=1)
        except Exception as e:
            print(f"⚠️ Erreur chargement correction: {e}")
            correction_placeholder = QLabel("CORRECTION\nD'IMAGES")
            correction_placeholder.setStyleSheet("""
                    background-color: #1a1a1a; 
                    color: white; 
                    padding: 20px;
                    border: 2px solid white;
            """)
            correction_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bottom_layout.addWidget(correction_placeholder, stretch=1)
        
        # Colonne de droite sous le lecteur (Histogramme + Courbe Tonale)
        right_bottom_widget = QWidget()
        right_bottom_layout = QVBoxLayout(right_bottom_widget)
        right_bottom_layout.setContentsMargins(0, 0, 0, 0)
        right_bottom_layout.setSpacing(10)

        try:
            self.histogram = Histogram()
            self.histogram.setStyleSheet("""
                    background-color: #1a1a1a;
                    border: 2px solid white;
            """)
            right_bottom_layout.addWidget(self.histogram, stretch=1)
        except Exception as e:
            print(f"⚠️ Erreur chargement histogramme: {e}")
            # Placeholder

        try:
            self.tone_curve_editor = ToneCurveEditor()
            self.tone_curve_editor.setStyleSheet("border: 2px solid white;")
            right_bottom_layout.addWidget(self.tone_curve_editor, stretch=1)
        except Exception as e:
            print(f"⚠️ Erreur chargement courbe tonale: {e}")
            # Placeholder

        bottom_layout.addWidget(right_bottom_widget, stretch=1)
        
        center_right_layout.addLayout(bottom_layout, stretch=4)
        
        center_right_widget = QWidget()
        center_right_widget.setLayout(center_right_layout)
        
        # Ajouter à la grille : colonne 1-2, lignes 0-1 (toute la hauteur)
        grid_layout.addWidget(center_right_widget, 0, 1, 2, 1)
        
    
        # Colonne 0 (gauche) et colonne 1 (droite)
        grid_layout.setColumnStretch(0, 2) 
        grid_layout.setColumnStretch(1, 5)  
        
        
        content_widget.setLayout(grid_layout)
        main_layout.addWidget(content_widget)
        
        self.setLayout(main_layout)
        
        # Connecter les signaux au contrôleur
        self.connect_signals()
        
    def connect_signals(self):
        """
        Connecte les signaux des composants aux méthodes du contrôleur
        Pattern: Signal → Contrôleur → Modèle
        """
        if not self.controller:
            print("⚠️ Aucun contrôleur associé")
            return
            
        try:
            # NAVBAR
            if hasattr(self, 'navbar') and hasattr(self.navbar, 'tab_changed'):
                self.navbar.tab_changed.connect(
                    self.controller.on_tab_changed
                )
            
            # EXPLORATEUR
            if hasattr(self, 'media_explorer') and hasattr(self.media_explorer, 'video_selected'):
                self.media_explorer.video_selected.connect(
                    self.controller.on_video_selected
                )
            
            # OUTILS D'EXTRACTION
            if hasattr(self, 'extraction_tools'):
                if hasattr(self.extraction_tools, 'screenshot_clicked'):
                    self.extraction_tools.screenshot_clicked.connect(
                        self.controller.on_screenshot
                    )
                if hasattr(self.extraction_tools, 'recording_clicked'):
                    self.extraction_tools.recording_clicked.connect(
                        self.controller.on_recording
                    )
                if hasattr(self.extraction_tools, 'short_clicked'):
                    self.extraction_tools.short_clicked.connect(
                        self.controller.on_create_short
                    )
                if hasattr(self.extraction_tools, 'crop_clicked'):
                    self.extraction_tools.crop_clicked.connect(
                        self.controller.on_crop
                    )
            
            # CORRECTION
            if hasattr(self, 'image_correction'):
                if hasattr(self.image_correction, 'color_correction_clicked'):
                    self.image_correction.color_correction_clicked.connect(
                        self.controller.on_color_correction
                    )
                if hasattr(self.image_correction, 'contrast_changed'):
                    self.image_correction.contrast_changed.connect(
                        self.controller.on_contrast_changed
                    )
                if hasattr(self.image_correction, 'brightness_changed'):
                    self.image_correction.brightness_changed.connect(
                        self.controller.on_brightness_changed
                    )
                # Connexion des signaux des filtres de ImageCorrection
                self.image_correction.gamma_toggled.connect(self.controller.on_toggle_gamma)
                self.image_correction.contrast_clahe_toggled.connect(self.controller.on_toggle_contrast)
                self.image_correction.denoise_toggled.connect(self.controller.on_toggle_denoise)
                self.image_correction.sharpen_toggled.connect(self.controller.on_toggle_sharpen)
                self.image_correction.filters_reset_clicked.connect(self.controller.on_reset_filters)
                # Connexion des nouveaux sliders de couleur et de la courbe
                self.image_correction.saturation_changed.connect(self.controller.on_saturation_changed)
                self.image_correction.hue_changed.connect(self.controller.on_hue_changed)
                self.image_correction.temperature_changed.connect(self.controller.on_temperature_changed)

            # Connexion de l'éditeur de courbe séparé
            if hasattr(self, 'tone_curve_editor'):
                self.tone_curve_editor.curve_changed.connect(self.controller.on_curve_changed)

                
            # Connexion du signal de réinitialisation des filtres du lecteur
            if hasattr(self, 'video_player') and hasattr(self.video_player, 'filters_reset'):
                self.video_player.filters_reset.connect(self.on_filters_reset_by_player)

            # Connexion du signal de correction automatique du composant ImageCorrection
            if hasattr(self.image_correction, 'color_correction_clicked'):
                self.image_correction.color_correction_clicked.connect(self.controller.on_color_correction)
            
            
            # LECTEUR
            if hasattr(self, 'video_player'):
                if hasattr(self.video_player, 'play_pause_clicked'):
                    self.video_player.play_pause_clicked.connect(
                        self.controller.on_play_pause
                    )
                # Connecter les données de l'histogramme du lecteur à l'affichage
                if hasattr(self.video_player, 'histogram_data_ready') and hasattr(self, 'histogram'):
                    self.video_player.histogram_data_ready.connect(self.histogram.update_histogram)

                if hasattr(self.video_player, 'position_changed'):
                    self.video_player.position_changed.connect(
                        self.controller.on_position_changed
                    )
                # Connecter les signaux pour la capture d'écran
                if hasattr(self.video_player, 'frame_captured'):
                    self.video_player.frame_captured.connect(
                        self.controller.save_captured_frame
                    )
                # Le signal vient maintenant du widget enfant mais est exposé par VideoPlayer
                if hasattr(self.video_player, 'crop_area_selected'):
                    self.video_player.crop_area_selected.connect(self.controller.on_crop_area_selected)

                if hasattr(self.video_player, 'detach_requested'):
                    self.video_player.detach_requested.connect(
                        self.controller.on_detach_player
                    )
                if hasattr(self.video_player, 'controls'):
                    if hasattr(self.video_player.controls, 'previous_clicked'):
                        self.video_player.controls.previous_clicked.connect(
                            self.controller.on_previous_video
                        )
                    if hasattr(self.video_player.controls, 'next_clicked'):
                        self.video_player.controls.next_clicked.connect(
                            self.controller.on_next_video
                        )
                    if hasattr(self.video_player.controls, 'rewind_clicked'):
                        self.video_player.controls.rewind_clicked.connect(
                            self.controller.on_rewind
                        )
                    if hasattr(self.video_player.controls, 'forward_clicked'):
                        self.video_player.controls.forward_clicked.connect(
                            self.controller.on_forward
                        )
                    
        except Exception as e:
            print(f"⚠️ Erreur lors de la connexion des signaux: {e}")
        
    def update_video_list(self, videos):
        """
        Met à jour la liste des vidéos dans l'explorateur
        Appelé par le contrôleur
        """
        if hasattr(self, 'media_explorer') and hasattr(self.media_explorer, 'add_video'):
            if hasattr(self.media_explorer, 'clear_videos'):
                self.media_explorer.clear_videos()
            for video in videos:
                self.media_explorer.add_video(
                    video['name'],
                    video.get('thumbnail_pixmap'),
                    video.get('thumbnail_color', '#00CBA9')
                )
        
    def update_video_player(self, video_data):
        """
        Met à jour le lecteur avec les données de la vidéo
        """
        if hasattr(self, 'video_player'):
            if hasattr(self.video_player, 'update_metadata') and 'metadata' in video_data:
                self.video_player.update_metadata(**video_data['metadata'])
            # Transmettre les données temporelles au lecteur
            if hasattr(self.video_player, 'set_timeseries_data') and 'timeseries_data' in video_data:
                self.video_player.set_timeseries_data(video_data['timeseries_data'])
            if hasattr(self.video_player, 'load_video') and 'path' in video_data:
                self.video_player.load_video(video_data['path'])
        
    def update_histogram(self, histogram_data=None):
        """
        Met à jour l'histogramme
        """
        if hasattr(self, 'histogram'):
            if histogram_data and hasattr(self.histogram, 'update_histogram'):
                self.histogram.update_histogram(**histogram_data)
            elif hasattr(self.histogram, 'refresh'):
                self.histogram.refresh()
        
    def show_message(self, message, message_type="info"):
        """Affiche un message à l'utilisateur"""
        print(f"[{message_type.upper()}] {message}")
        
    def get_correction_values(self):
        """
        Récupère les valeurs actuelles de correction d'image
        """
        if hasattr(self, 'image_correction'):
            return {
                'contrast': self.image_correction.get_contrast() if hasattr(self.image_correction, 'get_contrast') else 0,
                'brightness': self.image_correction.get_brightness() if hasattr(self.image_correction, 'get_brightness') else 0
            }
        return {'contrast': 0, 'brightness': 0}
    
    def update_correction_buttons_state(self, states: dict):
        """
        Met à jour l'état (coché/décoché) des boutons de correction.
        Appelé par le contrôleur.
        """
        # Déléguer la mise à jour à l'ImageCorrection
        if hasattr(self, 'image_correction') and hasattr(self.image_correction, 'update_filter_buttons_state'):
            self.image_correction.update_filter_buttons_state(states)

    def on_filters_reset_by_player(self):
        """Réinitialise l'état des boutons de filtre lorsque le lecteur signale une réinitialisation."""
        # La réinitialisation est maintenant gérée par le composant ImageCorrection lui-même
        if hasattr(self, 'image_correction') and hasattr(self.image_correction, 'reset_all'):
            self.image_correction.reset_all()
        if hasattr(self, 'tone_curve_editor') and hasattr(self.tone_curve_editor, 'reset'):
            self.tone_curve_editor.reset()
        
    def reset_corrections(self):
        """Réinitialise toutes les corrections d'image"""
        if hasattr(self, 'image_correction') and hasattr(self.image_correction, 'reset_all'):
            self.image_correction.reset_all()
