"""
Panneau d'outils de modification
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class ToolsPanel(QFrame):
    """Panneau d'outils de modification"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("Outils de modification")
        title.setObjectName("panelTitle")
        layout.addWidget(title)
        
        layout.addStretch()