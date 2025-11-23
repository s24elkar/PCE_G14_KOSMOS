"""
Fenêtre détachée pour le lecteur vidéo
Permet d'afficher le lecteur dans une fenêtre indépendante
"""
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon


class DetachedPlayerWindow(QMainWindow):
    """Fenêtre flottante pour le lecteur vidéo détaché"""
    
    closed = pyqtSignal()  # Signal émis quand la fenêtre est fermée
    
    def __init__(self, video_player, parent=None):
        super().__init__(parent)
        self.video_player = video_player
        self.setWindowTitle("🎬 Lecteur Vidéo - Détaché")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: black;")
        
        # Rendre la fenêtre indépendante et non modale.
        # Qt.WindowType.Window crée une fenêtre de premier niveau.
        # Ne pas mettre de parent à la création et ne pas utiliser WindowStaysOnTopHint.
        self.setWindowFlags(Qt.WindowType.Window)
        
        # Widget central
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Ajouter le lecteur vidéo
        layout.addWidget(self.video_player)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        print("🗗 Fenêtre détachée créée")
    
    def closeEvent(self, event):
        """Événement de fermeture de la fenêtre"""
        print("🔗 Fermeture de la fenêtre détachée")
        self.closed.emit()
        super().closeEvent(event)