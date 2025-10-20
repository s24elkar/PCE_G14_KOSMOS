"""
Panneau d'exploration de médias
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal


class MediaExplorerPanel(QFrame):
    """Panneau d'exploration de médias"""
    
    load_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Explorateur de media")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        
        self.btn_load = QPushButton("📁 Charger une vidéo")
        self.btn_load.setObjectName("loadButton")
        self.btn_load.clicked.connect(self.load_requested.emit)
        layout.addWidget(self.btn_load)
        
        layout.addStretch()