"""
Panneau d'histogramme
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class HistogramPanel(QFrame):
    """Panneau d'affichage de l'histogramme"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Histogramme")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        
        self.content_label = QLabel("Aucune vidéo")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setObjectName("noVideoLabel")
        layout.addWidget(self.content_label)
        
        layout.addStretch()