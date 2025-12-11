"""
VUE - Page d'accueil KOSMOS
Architecture MVC - Vue uniquement
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu,
    QDialog, QLineEdit, QPushButton, QFileDialog, QMessageBox,
    QFrame, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QAction

# Import du contrôleur
from controllers.accueil_controller import AccueilKosmosController
from components.navbar import NavBar
from components.fenetre_campagne import FenetreNouvelleCampagne


# ═══════════════════════════════════════════════════════════════
# DIALOGUE NOUVELLE CAMPAGNE
# ═══════════════════════════════════════════════════════════════
# (Déplacé dans components/fenetre_campagne.py)



# ═══════════════════════════════════════════════════════════════
# NAVBAR AVEC MENU FICHIER
# ═══════════════════════════════════════════════════════════════
# (Déplacé dans components/navbar.py)



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
        
        content = QFrame()
        content.setStyleSheet("background-color: black;")
        main_layout.addWidget(content)
        
        self.setLayout(main_layout)
    
    def connecter_signaux(self):
        """Connecte les signaux au contrôleur"""
        if not self.controller:
            return
        
        self.navbar.nouvelle_campagne_clicked.connect(
            self.controller.on_creer_campagne
        )
        self.navbar.ouvrir_campagne_clicked.connect(
            self.controller.on_ouvrir_campagne
        )
        self.navbar.enregistrer_clicked.connect(
            self.controller.on_enregistrer
        )
        self.navbar.enregistrer_sous_clicked.connect(
            self.controller.on_enregistrer_sous
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

    def open_new_campaign_dialog(self):
        """Ouvre le dialogue de création de nouvelle campagne"""
        dialogue = FenetreNouvelleCampagne(self)
        # On retourne l'instance pour que le contrôleur puisse connecter les signaux
        return dialogue


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from models.app_model import ApplicationModel
    except ImportError:
        print("❌ Impossible d'importer ApplicationModel")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    model = ApplicationModel()
    controller = AccueilKosmosController(model)
    
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1200, 700)
    
    view = AccueilKosmosView(controller)
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
