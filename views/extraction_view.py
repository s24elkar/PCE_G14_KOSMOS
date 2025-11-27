"""
Vue Extraction - Page d'extraction vidéo
Architecture MVC pour logiciel de dérushage
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour pouvoir importer les modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget
from PyQt6.QtCore import Qt

# Import de vos composants depuis components/
from components.navbar import NavBar
from components.explorateur import MediaExplorer
from components.lecteur import VideoPlayer
from components.correction import ImageCorrection
from components.histogramme import Histogram
from components.outils_modification import ExtractionTools
from components.commons import COLORS, FONTS, SPACING, RoundedCard, IconButton, Toast


class ExtractionView(QWidget):
    """
    Vue pour la page Extraction
    Layout repensé :
    - Colonne gauche compacte (explorateur)
    - Colonne droite : lecteur dominant + onglets contextuels (correction/ analyse / outils)
    """
    
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()
        self.load_initial_data()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        main_layout.setSpacing(SPACING["lg"])

        # ============================================================
        # NAVBAR (Barre de navigation en haut)
        # ============================================================
        try:
            self.navbar = NavBar(
                tabs=["Fichier", "Tri", "Extraction", "Évènements"],
                default_tab="Extraction",
            )
            main_layout.addWidget(self.navbar)
        except Exception as e:
            print(f"⚠️ Erreur chargement navbar: {e}")
            navbar_placeholder = QLabel("NAVBAR")
            navbar_placeholder.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
            main_layout.addWidget(navbar_placeholder)

        self.toast = Toast(self)

        # ============================================================
        # CONTENU PRINCIPAL (layout 2 colonnes)
        # ============================================================
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(SPACING["lg"])

        # Colonne gauche : Explorateur
        left_card = RoundedCard(
            "Explorateur média",
            subtitle="Mode liste compact + filtres rapides",
            padding=SPACING["lg"],
        )
        try:
            self.media_explorer = MediaExplorer()
            left_card.body_layout.addWidget(self.media_explorer)
        except Exception as e:
            print(f"⚠️ Erreur chargement explorateur: {e}")
            explorer_placeholder = QLabel("Explorateur indisponible")
            explorer_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_card.body_layout.addWidget(explorer_placeholder)
        left_card.setMinimumWidth(320)
        content_layout.addWidget(left_card, stretch=1)

        # Colonne droite : Lecteur dominant + onglets outils
        right_layout = QVBoxLayout()
        right_layout.setSpacing(SPACING["lg"])

        # Lecteur vidéo
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(SPACING["sm"])
        toolbar_layout.addStretch()
        self.metadata_toggle_btn = IconButton("🛈", tooltip="Afficher/masquer l'overlay métadonnées")
        self.metadata_toggle_btn.clicked.connect(self.toggle_metadata_visibility)
        toolbar_layout.addWidget(self.metadata_toggle_btn)

        video_card = RoundedCard(
            "Lecture principale",
            subtitle="Overlay contextuel + timeline avec marqueurs",
            accent=True,
            padding=SPACING["lg"],
            toolbar=toolbar_widget,
        )
        try:
            self.video_player = VideoPlayer()
            video_card.body_layout.addWidget(self.video_player)
        except Exception as e:
            print(f"⚠️ Erreur chargement lecteur: {e}")
            player_placeholder = QLabel("Lecteur non disponible")
            player_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            video_card.body_layout.addWidget(player_placeholder)
        right_layout.addWidget(video_card, stretch=4)

        # Onglets bas (outils contextuels)
        tabs_card = RoundedCard(
            "Outils & analyse",
            subtitle="Corrections, histogramme, export et annotations",
            padding=SPACING["md"],
            transparent=True,
        )

        tabs = QTabWidget()
        tabs.setObjectName("ContextTabs")
        tabs.setDocumentMode(True)
        tabs.setStyleSheet(
            f"QTabWidget::pane {{"
            f"border: 1px solid {COLORS['border']};"
            f"background: {COLORS['bg_secondary']};"
            f"border-radius: 12px;"
            f"}}"
            f"QTabBar::tab {{"
            f"background: {COLORS['bg_secondary']};"
            f"color: {COLORS['text_secondary']};"
            f"padding: 8px 14px;"
            f"border: 1px solid {COLORS['border']};"
            f"border-bottom: none;"
            f"border-top-left-radius: 10px;"
            f"border-top-right-radius: 10px;"
            f"margin-right: 2px;"
            f"font-weight: 700;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"QTabBar::tab:selected {{"
            f"background: {COLORS['accent_cyan']};"
            f"color: {COLORS['bg_primary']};"
            f"border-color: {COLORS['accent_cyan_light']};"
            f"}}"
            f"QTabBar::tab:hover {{"
            f"background: {COLORS['bg_tertiary']};"
            f"color: {COLORS['text_primary']};"
            f"}}"
        )

        # Correction Tab
        correction_container = QWidget()
        correction_layout = QVBoxLayout()
        correction_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        correction_layout.setSpacing(SPACING["md"])
        try:
            self.image_correction = ImageCorrection()
            correction_layout.addWidget(self.image_correction)
        except Exception as e:
            print(f"⚠️ Erreur chargement correction: {e}")
            correction_placeholder = QLabel("Correction indisponible")
            correction_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            correction_layout.addWidget(correction_placeholder)
        correction_container.setLayout(correction_layout)
        tabs.addTab(correction_container, "Correction")

        # Analyse Tab (Histogramme)
        analyse_container = QWidget()
        analyse_layout = QVBoxLayout()
        analyse_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        analyse_layout.setSpacing(SPACING["md"])
        try:
            self.histogram = Histogram()
            analyse_layout.addWidget(self.histogram)
        except Exception as e:
            print(f"⚠️ Erreur chargement histogramme: {e}")
            histogram_placeholder = QLabel("Histogramme indisponible")
            histogram_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            analyse_layout.addWidget(histogram_placeholder)
        analyse_container.setLayout(analyse_layout)
        tabs.addTab(analyse_container, "Analyse")

        # Outils Tab (ExtractionTools)
        outils_container = QWidget()
        outils_layout = QVBoxLayout()
        outils_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        outils_layout.setSpacing(SPACING["md"])
        try:
            self.extraction_tools = ExtractionTools()
            outils_layout.addWidget(self.extraction_tools)
        except Exception as e:
            print(f"⚠️ Erreur chargement outils: {e}")
            tools_placeholder = QLabel("Outils indisponibles")
            tools_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outils_layout.addWidget(tools_placeholder)
        outils_container.setLayout(outils_layout)
        tabs.addTab(outils_container, "Outils")

        # Export Tab (placeholder)
        export_container = QWidget()
        export_layout = QVBoxLayout()
        export_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        export_layout.setSpacing(SPACING["md"])
        export_label = QLabel("Options d'export : clips, images, données.")
        export_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        export_layout.addWidget(export_label)
        export_layout.addStretch()
        export_container.setLayout(export_layout)
        tabs.addTab(export_container, "Export")

        # Annotations Tab (placeholder)
        annot_container = QWidget()
        annot_layout = QVBoxLayout()
        annot_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        annot_layout.setSpacing(SPACING["md"])
        annot_label = QLabel("Annotations synchronisées : marqueurs, tags.")
        annot_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        annot_layout.addWidget(annot_label)
        annot_layout.addStretch()
        annot_container.setLayout(annot_layout)
        tabs.addTab(annot_container, "Annotations")

        tabs_card.body_layout.addWidget(tabs)
        right_layout.addWidget(tabs_card, stretch=2)

        content_layout.addLayout(right_layout, stretch=3)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)
        self.setObjectName("ExtractionRoot")
        self._apply_theme()

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
            # ────────────────────────────────────────────────────────────
            # Signaux de la NAVBAR
            # ────────────────────────────────────────────────────────────
            if hasattr(self, 'navbar') and hasattr(self.navbar, 'tab_changed'):
                self.navbar.tab_changed.connect(
                    self.controller.on_tab_changed
                )
            
            # ────────────────────────────────────────────────────────────
            # Signaux de l'EXPLORATEUR DE MÉDIA
            # ────────────────────────────────────────────────────────────
            if hasattr(self, 'media_explorer') and hasattr(self.media_explorer, 'video_selected'):
                self.media_explorer.video_selected.connect(
                    self.controller.on_video_selected
                )
            if hasattr(self, 'media_explorer') and hasattr(self.media_explorer, 'directory_selected'):
                self.media_explorer.directory_selected.connect(
                    self.controller.load_directory
                )
            if hasattr(self, 'media_explorer') and hasattr(self.media_explorer, 'view_mode_changed'):
                self.media_explorer.view_mode_changed.connect(
                    self.controller.on_view_mode_changed
                )
            
            # ────────────────────────────────────────────────────────────
            # Signaux des OUTILS D'EXTRACTION
            # ────────────────────────────────────────────────────────────
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
            
            # ────────────────────────────────────────────────────────────
            # Signaux de la CORRECTION D'IMAGES
            # ────────────────────────────────────────────────────────────
            if hasattr(self, 'image_correction'):
                if hasattr(self.image_correction, 'color_correction_clicked'):
                    self.image_correction.color_correction_clicked.connect(
                        self.controller.on_color_correction
                    )
                if hasattr(self.image_correction, 'apply_clicked'):
                    self.image_correction.apply_clicked.connect(
                        self.controller.on_apply_corrections
                    )
                if hasattr(self.image_correction, 'undo_clicked'):
                    self.image_correction.undo_clicked.connect(
                        self.controller.on_undo_correction
                    )
                if hasattr(self.image_correction, 'contrast_changed'):
                    self.image_correction.contrast_changed.connect(
                        self.controller.on_contrast_changed
                    )
                if hasattr(self.image_correction, 'brightness_changed'):
                    self.image_correction.brightness_changed.connect(
                        self.controller.on_brightness_changed
                    )
                if hasattr(self.image_correction, 'saturation_changed'):
                    self.image_correction.saturation_changed.connect(
                        self.controller.on_saturation_changed
                    )
                if hasattr(self.image_correction, 'hue_changed'):
                    self.image_correction.hue_changed.connect(
                        self.controller.on_hue_changed
                    )
                if hasattr(self.image_correction, 'temperature_changed'):
                    self.image_correction.temperature_changed.connect(
                        self.controller.on_temperature_changed
                    )
                if hasattr(self.image_correction, 'sharpness_changed'):
                    self.image_correction.sharpness_changed.connect(
                        self.controller.on_sharpness_changed
                    )
                if hasattr(self.image_correction, 'gamma_changed'):
                    self.image_correction.gamma_changed.connect(
                        self.controller.on_gamma_changed
                    )
                if hasattr(self.image_correction, 'denoise_changed'):
                    self.image_correction.denoise_changed.connect(
                        self.controller.on_denoise_changed
                    )
                if hasattr(self.image_correction, 'curve_changed') and hasattr(self.controller, 'on_curve_changed'):
                    self.image_correction.curve_changed.connect(
                        self.controller.on_curve_changed
                    )
            
            # ────────────────────────────────────────────────────────────
            # Signaux du LECTEUR VIDÉO
            # ────────────────────────────────────────────────────────────
            if hasattr(self, 'video_player'):
                if hasattr(self.video_player, 'play_pause_clicked'):
                    self.video_player.play_pause_clicked.connect(
                        self.controller.on_play_pause
                    )
                if hasattr(self.video_player, 'position_changed'):
                    self.video_player.position_changed.connect(
                        self.controller.on_position_changed
                    )
                # Signaux des contrôles
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
            if hasattr(self, 'metadata_toggle_btn') and hasattr(self.controller, 'on_toggle_metadata'):
                self.metadata_toggle_btn.clicked.connect(
                    lambda: self.controller.on_toggle_metadata(already_toggled=True)
                )
                    
        except Exception as e:
            print(f"⚠️ Erreur lors de la connexion des signaux: {e}")
        
    def load_initial_data(self):
        """
        Charge les données initiales depuis le modèle via le contrôleur
        """
        if self.controller and hasattr(self.controller, 'load_initial_data'):
            self.controller.load_initial_data()
            
    def update_video_list(self, videos):
        """
        Met à jour la liste des vidéos dans l'explorateur
        Appelé par le contrôleur
        
        Args:
            videos: Liste de dictionnaires avec les infos des vidéos
        """
        if hasattr(self, 'media_explorer') and hasattr(self.media_explorer, 'add_video'):
            if hasattr(self.media_explorer, 'clear_videos'):
                self.media_explorer.clear_videos()
            for video in videos:
                self.media_explorer.add_video(
                    video['name'],
                    video.get('thumbnail_color', '#00CBA9'),
                    video.get('path')
                )
        
    def update_video_player(self, video_data, frame=None):
        """
        Met à jour le lecteur avec les données de la vidéo
        Appelé par le contrôleur
        
        Args:
            video_data: Dictionnaire avec les données de la vidéo
            frame: np.ndarray RGB optionnel pour afficher un aperçu
        """
        if hasattr(self, 'video_player'):
            if hasattr(self.video_player, 'update_metadata') and 'metadata' in video_data:
                self.video_player.update_metadata(**video_data['metadata'])
            if frame is not None and hasattr(self.video_player, 'set_frame'):
                self.video_player.set_frame(frame)
            elif hasattr(self.video_player, 'load_video') and 'path' in video_data:
                # Fallback vers un éventuel futur lecteur
                self.video_player.load_video(video_data['path'])
        
    def update_histogram(self, histogram_data=None):
        """
        Met à jour l'histogramme
        Appelé par le contrôleur
        
        Args:
            histogram_data: Données pour l'histogramme (optionnel)
        """
        if hasattr(self, 'histogram'):
            if histogram_data and hasattr(self.histogram, 'update_histogram'):
                self.histogram.update_histogram(**histogram_data)
            elif hasattr(self.histogram, 'refresh'):
                self.histogram.refresh()
        
    def show_message(self, message, message_type="info"):
        """
        Affiche un message à l'utilisateur
        
        Args:
            message: Message à afficher
            message_type: Type de message ("info", "success", "warning", "error")
        """
        if hasattr(self, "toast"):
            self.toast.show_message(message, message_type)
        print(f"[{message_type.upper()}] {message}")
        
    def get_correction_values(self):
        """
        Récupère les valeurs actuelles de correction d'image
        
        Returns:
            dict: Dictionnaire avec contraste et luminosité
        """
        if hasattr(self, 'image_correction'):
            return {
                'contrast': self.image_correction.get_contrast() if hasattr(self.image_correction, 'get_contrast') else 0,
                'brightness': self.image_correction.get_brightness() if hasattr(self.image_correction, 'get_brightness') else 0,
                'saturation': self.image_correction.get_saturation() if hasattr(self.image_correction, 'get_saturation') else 0,
                'hue': self.image_correction.get_hue() if hasattr(self.image_correction, 'get_hue') else 0,
                'temperature': self.image_correction.get_temperature() if hasattr(self.image_correction, 'get_temperature') else 0,
                'sharpness': self.image_correction.get_sharpness() if hasattr(self.image_correction, 'get_sharpness') else 0,
                'gamma': self.image_correction.get_gamma() if hasattr(self.image_correction, 'get_gamma') else 0,
                'denoise': self.image_correction.get_denoise() if hasattr(self.image_correction, 'get_denoise') else 0,
            }
        return {'contrast': 0, 'brightness': 0, 'saturation': 0, 'hue': 0, 'temperature': 0, 'sharpness': 0, 'gamma': 0, 'denoise': 0}

    def toggle_metadata_visibility(self) -> None:
        """Bascule l'affichage des métadonnées du lecteur."""
        if hasattr(self, 'video_player') and hasattr(self.video_player, 'toggle_metadata_overlay'):
            self.video_player.toggle_metadata_overlay()
            self._refresh_metadata_button()

    def _refresh_metadata_button(self) -> None:
        """Met à jour le libellé du bouton de métadonnées."""
        if not hasattr(self, 'metadata_toggle_btn') or not hasattr(self, 'video_player'):
            return
        visible = True
        if hasattr(self.video_player, 'metadata_is_visible'):
            visible = self.video_player.metadata_is_visible()
        self.metadata_toggle_btn.setText("🛈" if visible else "🙈")
        self.metadata_toggle_btn.setToolTip(
            "Masquer l'overlay métadonnées (M)" if visible else "Afficher l'overlay métadonnées (M)"
        )

    def _apply_theme(self) -> None:
        """Applique un thème unifié (fond sombre, accents cyan)."""
        self.setStyleSheet(
            f"#ExtractionRoot {{"
            f"background-color: {COLORS['bg_primary']};"
            f"color: {COLORS['text_primary']};"
            f"font-family: '{FONTS['primary']}', 'Segoe UI', sans-serif;"
            f"}}"
            f"QLabel {{ color: {COLORS['text_primary']}; }}"
            f"QPushButton {{ font-family: '{FONTS['primary']}', 'Segoe UI', sans-serif; }}"
        )

    def reset_corrections(self):
        """Réinitialise toutes les corrections d'image"""
        if hasattr(self, 'image_correction') and hasattr(self.image_correction, 'reset_all'):
            self.image_correction.reset_all()

    def set_correction_values(self, corrections: dict[str, int]):
        """Positionne les sliders sur des valeurs données (utilisé pour annulation)"""
        if hasattr(self, 'image_correction') and hasattr(self.image_correction, 'set_corrections'):
            self.image_correction.set_corrections(
                contrast=corrections.get('contrast', 0),
                brightness=corrections.get('brightness', 0),
                saturation=corrections.get('saturation', 0),
                hue=corrections.get('hue', 0),
                temperature=corrections.get('temperature', 0),
                sharpness=corrections.get('sharpness', 0),
                gamma=corrections.get('gamma', 0),
                denoise=corrections.get('denoise', 0),
            )

    def apply_corrections_to_preview(self, corrections: dict[str, int], curve_lut: list[int] | None = None):
        """
        Applique visuellement les corrections sur l'aperçu vidéo et l'histogramme.
        Cela reste un effet de prévisualisation (pas de traitement vidéo en temps réel).
        """
        if hasattr(self, 'video_player') and hasattr(self.video_player, 'apply_corrections'):
            self.video_player.apply_corrections(
                contrast=corrections.get('contrast', 0),
                brightness=corrections.get('brightness', 0),
                saturation=corrections.get('saturation', 0),
                hue=corrections.get('hue', 0),
                temperature=corrections.get('temperature', 0),
                sharpness=corrections.get('sharpness', 0),
                gamma=corrections.get('gamma', 0),
                denoise=corrections.get('denoise', 0),
                curve_lut=curve_lut,
            )

        if hasattr(self, 'histogram'):
            payload = self._build_histogram_payload(corrections)
            if curve_lut:
                payload = self._apply_curve_to_payload(payload, curve_lut)
            self.update_histogram(payload)

    def _build_histogram_payload(self, corrections: dict[str, int]) -> dict:
        """Génère des données d'histogramme simples à partir des corrections actuelles."""
        contrast = corrections.get('contrast', 0)
        brightness = corrections.get('brightness', 0)
        factor = 1 + (contrast / 200.0)
        shift = brightness * 0.8

        def scaled(channel_bias: int) -> list[int]:
            values = []
            for x in range(256):
                raw = (x + channel_bias) * factor + shift
                values.append(max(0, min(255, int(raw))))
            return values

        red = scaled(20)
        green = scaled(0)
        blue = scaled(-20)
        density = [int((r + g + b) / 3) for r, g, b in zip(red, green, blue)]
        return {'data_r': red, 'data_g': green, 'data_b': blue, 'data_density': density}

    def _apply_curve_to_payload(self, payload: dict, curve_lut: list[int]) -> dict:
        """Applique la LUT au payload d'histogramme pour prévisualiser la courbe."""
        if not curve_lut or len(curve_lut) < 256:
            return payload
        lut = [max(0, min(255, int(v))) for v in curve_lut[:256]]

        def remap(data: list[int]) -> list[int]:
            if not data:
                return data
            out = []
            max_val = max(data) if data else 1
            for idx, val in enumerate(data):
                # normaliser sur 0..255 pour indexer la LUT de manière simple
                normalized = int(idx / max(1, len(data) - 1) * 255)
                mapped = lut[normalized]
                # préserver l'amplitude originale
                out.append(int(mapped / 255 * val if max_val else 0))
            return out

        return {
            "data_r": remap(payload.get("data_r", [])),
            "data_g": remap(payload.get("data_g", [])),
            "data_b": remap(payload.get("data_b", [])),
            "data_density": remap(payload.get("data_density", [])),
        }


# ============================================================
# Exemple d'utilisation (pour tests)
# ============================================================
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtGui import QFont
    
    print("🚀 Démarrage de la vue Extraction...")
    print(f"📁 Répertoire du projet: {project_root}")
    
    # Créer une vue sans contrôleur pour tester
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1600, 900)
    window.setWindowTitle("Extraction View - Test")
    window.setStyleSheet("background-color: black;")
    
    print("📦 Chargement des composants...")
    view = ExtractionView()
    
    # Ajouter des vidéos de test
    if hasattr(view, 'media_explorer'):
        view.media_explorer.add_video("Video_1", "#00CBA9")
        view.media_explorer.add_video("Video_2", "#D4A574")
        view.media_explorer.add_video("Video_3", "#FF6B6B")
        view.media_explorer.add_video("Video_4", "#4ECDC4")
    
    window.setCentralWidget(view)
    print("✅ Interface chargée avec succès!")
    
    window.show()
    
    sys.exit(app.exec())
