"""
Composant Explorateur de Média
Affiche une liste de miniatures vidéo avec scrollbar
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor


class MediaThumbnail(QWidget):
    """Widget représentant une miniature vidéo"""
    
    clicked = pyqtSignal(str)  # Émet le nom de la vidéo
    
    def __init__(self, video_name, thumbnail_pixmap=None, thumbnail_color=None, parent=None):
        super().__init__(parent)
        self.video_name = video_name
        self.is_selected = False
        self.thumbnail_pixmap = thumbnail_pixmap
        self.thumbnail_color = thumbnail_color or "#00CBA9"
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)
        
        # Zone de la miniature (image ou placeholder coloré)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(120, 80)
        
        # Si on a une image, l'afficher, sinon utiliser la couleur
        if self.thumbnail_pixmap:
            # Redimensionner l'image en gardant le ratio et en remplissant le cadre
            scaled_pixmap = self.thumbnail_pixmap.scaled(
                120, 80,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Couper le pixmap aux dimensions exactes (centré)
            x_offset = (scaled_pixmap.width() - 120) // 2
            y_offset = (scaled_pixmap.height() - 80) // 2
            cropped_pixmap = scaled_pixmap.copy(x_offset, y_offset, 120, 80)
            
            self.thumbnail_label.setPixmap(cropped_pixmap)
        
        self.thumbnail_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.thumbnail_color};
                border: 2px solid #333;
                border-radius: 4px;
            }}
        """)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail_label)
        
        # Nom de la vidéo (CENTRÉ)
        name_label = QLabel(self.video_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10px;
                font-weight: 500;
            }
        """)
        layout.addWidget(name_label)
        
        self.setLayout(layout)
        
        # Retirer les bordures du widget thumbnail
        self.setStyleSheet("""
            MediaThumbnail {
                background-color: transparent;
                border: none;
            }
        """)
        
    def mousePressEvent(self, event):
        """Gère le clic sur la miniature"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_name)
            
    def set_selected(self, selected):
        """Change l'état de sélection"""
        self.is_selected = selected
        if selected:
            self.thumbnail_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.thumbnail_color};
                    border: 3px solid #2196F3;
                    border-radius: 4px;
                }}
            """)
        else:
            self.thumbnail_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.thumbnail_color};
                    border: 2px solid #333;
                    border-radius: 4px;
                }}
            """)


class MediaExplorer(QWidget):
    """
    Composant Explorateur de Média
    Affiche une liste scrollable de vidéos (2 par ligne)
    """
    
    video_selected = pyqtSignal(str)  # Émet le nom de la vidéo sélectionnée
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnails = []
        self.selected_thumbnail = None
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête
        header = QLabel("Explorateur de media")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-bottom: 2px solid #ddd;
            }
        """)
        main_layout.addWidget(header)
        
        # Zone scrollable pour les miniatures
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: black;
                border: 2px solid white;
            }
            QScrollBar:vertical {
                background-color: white;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a5a5a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Container pour les miniatures
        self.content_widget = QWidget()
        
        # CHANGEMENT: Utiliser QGridLayout au lieu de QVBoxLayout pour avoir 2 colonnes
        self.content_layout = QGridLayout()
        self.content_layout.setContentsMargins(5, 15, 5, 15)  # marges haut/bas augmentées
        self.content_layout.setHorizontalSpacing(8)
        self.content_layout.setVerticalSpacing(20)  # espacement vertical augmenté
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.content_widget.setLayout(self.content_layout)
        self.content_widget.setStyleSheet("background-color: black;")
        
        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        self.setObjectName("mediaExplorer")
        self.setStyleSheet("""
            #mediaExplorer {
                background-color: black;
                border: 2px solid white;
            }
        """)
        
    def add_video(self, video_name, thumbnail_pixmap=None, thumbnail_color=None):
        """
        Ajoute une vidéo à l'explorateur
        
        Args:
            video_name: Nom de la vidéo
            thumbnail_pixmap: QPixmap de la miniature (optionnel)
            thumbnail_color: Couleur de la miniature (hex) - fallback si pas d'image
        """
        thumbnail = MediaThumbnail(video_name, thumbnail_pixmap, thumbnail_color)
        thumbnail.clicked.connect(self.on_thumbnail_clicked)
        self.thumbnails.append(thumbnail)
        
        # Calculer la position dans la grille (2 colonnes)
        index = len(self.thumbnails) - 1
        row = index // 2  # Ligne (division entière)
        col = index % 2   # Colonne (0 ou 1)
        
        self.content_layout.addWidget(thumbnail, row, col)
        
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
        
        self.video_selected.emit(video_name)
        
    def clear_videos(self):
        """Supprime toutes les vidéos"""
        for thumb in self.thumbnails:
            self.content_layout.removeWidget(thumb)
            thumb.deleteLater()
        self.thumbnails.clear()
        self.selected_thumbnail = None


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