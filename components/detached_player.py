"""
Fenêtre détachée pour le lecteur vidéo
Permet d'afficher le lecteur dans une fenêtre indépendante
"""
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon


class DetachedPlayerWindow(QMainWindow):
    """Fenêtre flottante pour le lecteur vidéo détaché"""
    
    closed = pyqtSignal()
    
    def __init__(self, video_player, parent=None):
        super().__init__(parent)
        self.video_player = video_player
        self.setWindowTitle("Lecteur Vidéo - Détaché")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: black;")
        
        # Fenêtre indépendante de premier niveau
        self.setWindowFlags(Qt.WindowType.Window)
        
        # Widget central
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Ajouter le lecteur vidéo
        layout.addWidget(self.video_player)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        print("Fenêtre détachée créée")
    
    def showEvent(self, event):
        """Appelé quand la fenêtre est affichée"""
        super().showEvent(event)
        # Forcer la mise à jour de la vidéo après l'affichage
        if hasattr(self.video_player, 'video_widget'):
            self.video_player.video_widget.update()
    
    def closeEvent(self, event):
        """Événement de fermeture de la fenêtre"""
        print("Fermeture de la fenêtre détachée")
        self.closed.emit()
        super().closeEvent(event)