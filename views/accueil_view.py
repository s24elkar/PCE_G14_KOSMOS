"""
Fenêtre principale de l'application
"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QGridLayout
# Les imports des composants seraient ici normalement


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Éditeur de Médias - PyQt6 MVC")
        self.setGeometry(100, 100, 1400, 900)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configure l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Barre de menu
        self._create_menu_bar()
        
        # Grille principale
        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)
        
        # Instanciation des panneaux
        from components.explorateur import MediaExplorerPanel
        self.media_explorer = MediaExplorerPanel()
        grid_layout.addWidget(self.media_explorer, 0, 0)
        
        from components.lecteur import VideoPlayerPanel
        self.video_player = VideoPlayerPanel()
        grid_layout.addWidget(self.video_player, 0, 1, 1, 2)
        
        from components.outils.lodification import ToolsPanel
        self.tools_panel = ToolsPanel()
        grid_layout.addWidget(self.tools_panel, 1, 0)
        
        from components.correction import CorrectionPanel
        self.correction_panel = CorrectionPanel()
        grid_layout.addWidget(self.correction_panel, 1, 1)
        
        from components.histogramme import HistogramPanel
        self.histogram_panel = HistogramPanel()
        grid_layout.addWidget(self.histogram_panel, 1, 2)
    
    def _create_menu_bar(self):
        """Crée la barre de menu"""
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Fichier")
        self.open_action = file_menu.addAction("Ouvrir")
        file_menu.addSeparator()
        self.quit_action = file_menu.addAction("Quitter")
        
        menubar.addMenu("Tri")
        menubar.addMenu("Extraction")
        menubar.addMenu("Évènements")