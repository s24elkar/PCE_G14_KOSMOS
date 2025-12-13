"""
VUE - Page d'accueil KOSMOS
Architecture MVC - Vue uniquement
"""
from pathlib import Path

project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

# Import des composants
from components.navbar import NavBar


# ═══════════════════════════════════════════════════════════════
# VUE
# ═══════════════════════════════════════════════════════════════

class AccueilKosmosView(QWidget):
    """Vue de la page d'accueil KOSMOS - FOND NOIR"""
    
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.init_ui()
        self.connecter_signaux()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBar(
            tabs=["Fichier", "Tri", "Extraction"],
            default_tab="Fichier",
            disable_tabs=True
        )
        main_layout.addWidget(self.navbar)
        
        # CONTENU NOIR
        content_frame = QFrame()
        content_frame.setStyleSheet("background-color: black;")
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # ZONE CENTRALE
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(30)
        
        # Titre
        titre = QLabel("KOSMOS")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        center_layout.addWidget(titre)
        
        # Sous-titre
        sous_titre = QLabel("Dérushage Vidéo Sous-Marine")
        sous_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sous_titre.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 18px;
                margin-bottom: 40px;
            }
        """)
        center_layout.addWidget(sous_titre)
        
        # Instruction
        instruction = QLabel("Utilisez le menu Fichier pour ouvrir une campagne")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
            }
        """)
        center_layout.addWidget(instruction)
        
        center_widget.setLayout(center_layout)
        content_layout.addWidget(center_widget)
        
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)
    
    def connecter_signaux(self):
        """Connecte les signaux au contrôleur"""
        if not self.controller:
            return
        
        self.navbar.ouvrir_campagne_clicked.connect(
            self.controller.on_ouvrir_campagne
        )

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES UI (Appelées par le contrôleur)
    # ═══════════════════════════════════════════════════════════════

    def ask_directory(self, title):
        """Ouvre une boîte de dialogue pour sélectionner un dossier"""
        return QFileDialog.getExistingDirectory(self, title, "")

    def show_info(self, title, message):
        """Affiche une boîte de dialogue d'information"""
        QMessageBox.information(self, title, message)

    def show_warning(self, title, message):
        """Affiche une boîte de dialogue d'avertissement"""
        QMessageBox.warning(self, title, message)

    def show_error(self, title, message):
        """Affiche une boîte de dialogue d'erreur"""
        QMessageBox.critical(self, title, message)

    def ask_confirmation(self, title, message):
        """Demande une confirmation à l'utilisateur"""
        reponse = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reponse == QMessageBox.StandardButton.Yes



# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    from pathlib import Path
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from models.app_model import ApplicationModel
    from controllers.accueil_controller import AccueilKosmosController
    
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    model = ApplicationModel()
    controller = AccueilKosmosController(model)
    
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1200, 700)
    
    view = AccueilKosmosView(controller)
    controller.set_view(view)
    window.setCentralWidget(view)
    
    controller.navigation_demandee.connect(
        lambda page: print(f"🔄 Navigation vers : {page}")
    )
    
    controller.campagne_creee.connect(
        lambda nom, chemin: print(f"✅ Campagne créée : {nom} dans {chemin}")
    )
    
    window.show()
    print("✅ Page d'accueil KOSMOS chargée!")
    
    sys.exit(app.exec())
