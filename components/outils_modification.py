"""
Composant Outils d'Extraction
Boutons pour capture d'écran, enregistrement, création de short, recadrage
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ExtractionButton(QPushButton):
    """Bouton d'extraction personnalisé avec icône"""
    
    def __init__(self, icon_text, label_text, parent=None):
        super().__init__(parent)
        self.icon_text = icon_text
        self.label_text = label_text
        self.init_ui()
        
    def init_ui(self):
        self.setText(f"  {self.icon_text}    {self.label_text}")
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                border: 2px solid white;
                border-radius: 8px;
                padding: 10px 15px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Montserrat';
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #0d0d0d;
            }
        """)


class ExtractionTools(QWidget):
    """
    Composant Outils d'Extraction
    Contient les boutons pour les différentes actions d'extraction
    """
    
    # Signaux pour chaque action
    screenshot_clicked = pyqtSignal()
    recording_clicked = pyqtSignal()
    short_clicked = pyqtSignal()
    crop_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête
        header = QLabel("Outils d'extraction")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                text-align: center;
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-bottom: 2px solid #ddd;
            }
        """)
        main_layout.addWidget(header)
        
        # Container pour les boutons
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout()
        buttons_layout.setContentsMargins(15, 15, 15, 15)
        buttons_layout.setSpacing(15)
        
        # Bouton Capture d'écran
        self.screenshot_btn = ExtractionButton("📷", "Capture d'écran")
        self.screenshot_btn.clicked.connect(self.screenshot_clicked.emit)
        buttons_layout.addWidget(self.screenshot_btn)
        
        # Bouton Enregistrement vidéo
        self.recording_btn = ExtractionButton("⏺", "Enregistrement vidéo")
        self.recording_btn.clicked.connect(self.recording_clicked.emit)
        buttons_layout.addWidget(self.recording_btn)
        
        # Bouton Créer un short
        self.short_btn = ExtractionButton("▶", "Créer un short")
        self.short_btn.clicked.connect(self.short_clicked.emit)
        buttons_layout.addWidget(self.short_btn)
        
        buttons_layout.addStretch()
        
        buttons_container.setLayout(buttons_layout)
        buttons_container.setStyleSheet("background-color: black;")
        
        main_layout.addWidget(buttons_container)
        
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                border: 2px solid white;
                font-family: 'Montserrat';
            }
        """)


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 430, 400)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    tools = ExtractionTools()
    
    # Connecter les signaux
    tools.screenshot_clicked.connect(lambda: print("📷 Capture d'écran"))
    tools.recording_clicked.connect(lambda: print("⏺ Enregistrement vidéo"))
    tools.short_clicked.connect(lambda: print("▶ Créer un short"))
    tools.crop_clicked.connect(lambda: print("⛶ Recadrer"))
    
    window.setCentralWidget(tools)
    window.show()
    
    sys.exit(app.exec())