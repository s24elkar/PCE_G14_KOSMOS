"""
Composant Explorateur de Média
Affiche une liste de miniatures vidéo avec scrollbar
"""
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QGridLayout,
    QFileDialog,
    QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from components.commons import COLORS, FONTS, SPACING


class MediaThumbnail(QWidget):
    """Widget représentant une miniature vidéo"""
    
    clicked = pyqtSignal(str)  # Émet le nom de la vidéo
    
    def __init__(self, video_name, thumbnail_color=None, parent=None):
        super().__init__(parent)
        self.video_name = video_name
        self.is_selected = False
        self.thumbnail_color = thumbnail_color or "#00CBA9"
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Zone de la miniature (placeholder coloré)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(150, 100)
        self.thumbnail_label.setStyleSheet(
            f"QLabel {{"
            f"background-color: {self.thumbnail_color};"
            f"border: 2px solid {COLORS['border']};"
            f"border-radius: 8px;"
            f"}}"
        )
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label)
        
        # Nom de la vidéo (CENTRÉ)
        name_label = QLabel(self.video_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # ← Changé de AlignLeft à AlignCenter
        name_label.setStyleSheet(
            f"QLabel {{"
            f"color: {COLORS['text_primary']};"
            f"font-size: {FONTS['sizes']['sm']}px;"
            f"font-weight: 600;"
            f"}}"
        )
        layout.addWidget(name_label)
        
        self.setLayout(layout)
        
        # Retirer les bordures du widget thumbnail
        self.setStyleSheet("MediaThumbnail { background-color: transparent; border: none; }")
        
    def mousePressEvent(self, event):
        """Gère le clic sur la miniature"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_name)
            
    def set_selected(self, selected):
        """Change l'état de sélection"""
        self.is_selected = selected
        if selected:
            self.thumbnail_label.setStyleSheet(
                f"QLabel {{"
                f"background-color: {self.thumbnail_color};"
                f"border: 3px solid {COLORS['accent_cyan']};"
                f"border-radius: 8px;"
                f"}}"
            )
        else:
            self.thumbnail_label.setStyleSheet(
                f"QLabel {{"
                f"background-color: {self.thumbnail_color};"
                f"border: 2px solid {COLORS['border']};"
                f"border-radius: 8px;"
                f"}}"
            )


class MediaExplorer(QWidget):
    """
    Composant Explorateur de Média
    Affiche une liste scrollable de vidéos (2 par ligne)
    """
    
    video_selected = pyqtSignal(str)  # Émet le nom de la vidéo sélectionnée
    view_mode_changed = pyqtSignal(str)  # Émet "grid" ou "list"
    directory_selected = pyqtSignal(str)  # Émet le chemin d'un dossier choisi
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnails = []
        self.selected_thumbnail = None
        self.view_mode = "grid"
        self._video_paths: dict[str, str] = {}  # map nom -> chemin complet
        self._filter_text: str = ""
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête avec bouton d'alternance d'affichage
        header = QFrame()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        header_layout.setSpacing(SPACING["sm"])

        title = QLabel("Explorateur de media")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet(
            f"QLabel {{"
            f"color: {COLORS['text_primary']};"
            f"font-size: {FONTS['sizes']['lg']}px;"
            f"font-weight: 700;"
            f"}}"
        )
        header_layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher (nom, date, durée)")
        self.search_input.textChanged.connect(self._apply_filter)
        self.search_input.setStyleSheet(
            f"QLineEdit {{"
            f"background-color: {COLORS['bg_tertiary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 10px;"
            f"padding: 6px 10px;"
            f"font-family: '{FONTS['primary']}';"
            f"}}"
            f"QLineEdit:focus {{ border-color: {COLORS['accent_cyan']}; }}"
        )
        header_layout.addWidget(self.search_input, stretch=1)

        self.folder_button = QPushButton("Ouvrir un dossier")
        self.folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_button.setFixedHeight(32)
        self.folder_button.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['accent_cyan']};"
            f"color: {COLORS['bg_primary']};"
            f"border: 1px solid {COLORS['accent_cyan_light']};"
            f"border-radius: 10px;"
            f"padding: 6px 12px;"
            f"font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLORS['accent_cyan_light']}; border-color: {COLORS['accent_cyan_light']}; }}"
        )
        self.folder_button.clicked.connect(self._choose_directory)
        header_layout.addWidget(self.folder_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.view_toggle = QPushButton("Afficher en liste")
        self.view_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_toggle.setFixedHeight(32)
        self.view_toggle.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {COLORS['bg_tertiary']};"
            f"color: {COLORS['text_primary']};"
            f"border: 1px solid {COLORS['accent_cyan_light']};"
            f"border-radius: 10px;"
            f"padding: 6px 14px;"
            f"font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{ background-color: {COLORS['bg_secondary']}; border-color: {COLORS['accent_cyan_light']}; }}"
        )
        self.view_toggle.clicked.connect(self.toggle_view_mode)
        header_layout.addWidget(self.view_toggle, alignment=Qt.AlignmentFlag.AlignRight)

        header.setLayout(header_layout)
        header.setStyleSheet(
            f"QFrame {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 12px;"
            f"}}"
        )
        main_layout.addWidget(header)
        
        # Zone scrollable pour les miniatures
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(
            f"QScrollArea {{"
            f"background-color: transparent;"
            f"border: 1px solid {COLORS['border']};"
            f"border-radius: 12px;"
            f"}}"
            f"QScrollBar:vertical {{"
            f"background-color: {COLORS['bg_primary']};"
            f"width: 12px;"
            f"border-radius: 6px;"
            f"}}"
            f"QScrollBar::handle:vertical {{"
            f"background-color: {COLORS['bg_tertiary']};"
            f"border-radius: 6px;"
            f"min-height: 20px;"
            f"}}"
            f"QScrollBar::handle:vertical:hover {{"
            f"background-color: {COLORS['accent_cyan']};"
            f"}}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{"
            f"height: 0px;"
            f"}}"
        )
        
        # Container pour les miniatures
        self.content_widget = QWidget()
        
        # CHANGEMENT: Utiliser QGridLayout au lieu de QVBoxLayout pour avoir 2 colonnes
        self.content_layout = QGridLayout()
        self.content_layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        self.content_layout.setSpacing(SPACING["md"])
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setStyleSheet("background-color: transparent;")
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setObjectName("mediaExplorer")
        self.setStyleSheet("""
            #mediaExplorer {
                background-color: transparent;
            }
        """)

    def _choose_directory(self):
        """Ouvre un QFileDialog pour sélectionner un dossier contenant des vidéos."""
        directory = QFileDialog.getExistingDirectory(self, "Choisir un dossier vidéo")
        if directory:
            self.directory_selected.emit(directory)
        
    def add_video(self, video_name, thumbnail_color=None, video_path: str | None = None):
        """
        Ajoute une vidéo à l'explorateur
        
        Args:
            video_name: Nom de la vidéo
            thumbnail_color: Couleur de la miniature (hex)
        """
        thumbnail = MediaThumbnail(video_name, thumbnail_color)
        thumbnail.clicked.connect(self.on_thumbnail_clicked)
        self.thumbnails.append(thumbnail)
        if video_path:
            self._video_paths[video_name] = video_path
        
        self._place_thumbnail(len(self.thumbnails) - 1)
        self._apply_filter()
        
    def on_thumbnail_clicked(self, video_name):
        """Gère le clic sur une miniature"""
        # Désélectionner l'ancienne miniature
        if self.selected_thumbnail:
            self.selected_thumbnail.set_selected(False)
        
        # Sélectionner la nouvelle
        for thumb in self.thumbnails:
            if thumb.video_name == video_name:
                thumb.set_selected(True)
                self.selected_thumbnail = thumb
                break
        
        # Émet soit le chemin complet si connu, soit le nom
        self.video_selected.emit(self._video_paths.get(video_name, video_name))

    def _apply_filter(self, text: str | None = None):
        """Filtre les miniatures selon le texte recherché."""
        if text is not None:
            self._filter_text = text.lower()
        for thumb in self.thumbnails:
            visible = self._filter_text in thumb.video_name.lower()
            thumb.setVisible(visible)
        
    def clear_videos(self):
        """Supprime toutes les vidéos"""
        self._clear_layout_items(delete_widgets=True)
        self.thumbnails.clear()
        self.selected_thumbnail = None
        self._video_paths.clear()

    # ------------------------------------------------------------------ #
    # View mode handling
    # ------------------------------------------------------------------ #
    def toggle_view_mode(self):
        next_mode = "list" if self.view_mode == "grid" else "grid"
        self.set_view_mode(next_mode)

    def set_view_mode(self, mode: str):
        """Basculer entre affichage grille (2 colonnes) et liste (1 colonne)."""
        if mode not in {"grid", "list"}:
            return
        if mode == self.view_mode and self.thumbnails:
            return
        self.view_mode = mode
        self._update_toggle_label()
        self._reflow_thumbnails()
        self.view_mode_changed.emit(self.view_mode)

    def _update_toggle_label(self):
        if self.view_mode == "grid":
            self.view_toggle.setText("Afficher en liste")
        else:
            self.view_toggle.setText("Afficher en grille")

    def _reflow_thumbnails(self):
        """Réorganise les miniatures selon le mode courant."""
        self._clear_layout_items(delete_widgets=False)
        for index in range(len(self.thumbnails)):
            self._place_thumbnail(index)
        self._apply_filter()

    def _place_thumbnail(self, index: int):
        """Place une miniature dans la grille selon le mode courant."""
        if index < 0 or index >= len(self.thumbnails):
            return
        columns = 1 if self.view_mode == "list" else 2
        row = index // columns
        col = index % columns
        self.content_layout.addWidget(self.thumbnails[index], row, col)

    def _clear_layout_items(self, delete_widgets: bool):
        """Retire les widgets du layout sans forcément les détruire."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(self.content_widget)
                if delete_widgets:
                    widget.deleteLater()


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 400, 500)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    explorer = MediaExplorer()
    
    # Ajouter des vidéos de test (maintenant affichées 2 par ligne)
    explorer.add_video("Video_1", "#00CBA9")
    explorer.add_video("Video_2", "#D4A574")
    explorer.add_video("Video_3", "#FF6B6B")
    explorer.add_video("Video_4", "#4ECDC4")
    explorer.add_video("Video_5", "#9B59B6")
    explorer.add_video("Video_6", "#F39C12")
    
    # Connecter le signal
    explorer.video_selected.connect(lambda name: print(f"Vidéo sélectionnée: {name}"))
    
    window.setCentralWidget(explorer)
    window.show()
    
    sys.exit(app.exec())
