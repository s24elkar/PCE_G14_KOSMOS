"""
VUE - Page d'importation KOSMOS
Architecture MVC - Vue uniquement
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QMessageBox, QPushButton, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QFont, QAction, QPalette, QColor

# Import du contrôleur
from controllers.importation_controller import ImportationKosmosController
from components.navbar import NavBar


# ═══════════════════════════════════════════════════════════════
# NAVBAR AVEC MENU FICHIER
# ═══════════════════════════════════════════════════════════════
# (Déplacé dans components/navbar.py)



# ═══════════════════════════════════════════════════════════════
# VUE
# ═══════════════════════════════════════════════════════════════

class ImportationKosmosView(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.auto_open = True
        self.init_ui()
    
    def showEvent(self, event):
        """Appelé quand la vue devient visible"""
        super().showEvent(event)
        if self.auto_open:
            self.auto_open = False
            QTimer.singleShot(100, self.on_select_folder)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBar(
            tabs=["Fichier", "Tri", "Extraction"],
            default_tab="Fichier"
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
        titre = QLabel("Importation des vidéos")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        center_layout.addWidget(titre)
        
        # Instruction
        instruction = QLabel("Sélectionnez le dossier contenant les vidéos et métadonnées")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 16px;
                margin-bottom: 30px;
            }
        """)
        center_layout.addWidget(instruction)
        
        # Bouton principal d'importation
        btn_select_folder = QPushButton("📁 Sélectionner le dossier")
        btn_select_folder.setFixedSize(400, 80)
        btn_select_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_folder.setStyleSheet("""
            QPushButton {
                background-color: #1DA1FF;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        btn_select_folder.clicked.connect(self.on_select_folder)
        center_layout.addWidget(btn_select_folder, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Zone d'info sur le dossier sélectionné
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 13px;
                margin-top: 20px;
            }
        """)
        self.info_label.setWordWrap(True)
        self.info_label.setMaximumWidth(600)
        center_layout.addWidget(self.info_label)
        
        center_widget.setLayout(center_layout)
        content_layout.addWidget(center_widget)
        
        content_frame.setLayout(content_layout)
        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)
    
    def on_select_folder(self):
        """Ouvre le dialogue de sélection de dossier Windows"""
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier contenant les vidéos",
            "",
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if dossier:
            self.info_label.setText(f"Dossier sélectionné : {dossier}")
            print(f"📁 Dossier sélectionné : {dossier}")
            
            # Lister le contenu pour debug
            print(f"📂 Contenu du dossier :")
            try:
                contenu = os.listdir(dossier)
                print(f"   Nombre d'éléments : {len(contenu)}")
                for item in contenu[:10]:
                    chemin_complet = os.path.join(dossier, item)
                    type_item = "📁" if os.path.isdir(chemin_complet) else "📄"
                    print(f"   {type_item} {item}")
                if len(contenu) > 10:
                    print(f"   ... et {len(contenu) - 10} autres éléments")
            except Exception as e:
                print(f"   ❌ Erreur lecture : {e}")
            
            # Lancer l'importation
            if self.controller:
                self.controller.on_importer_dossier(dossier)
        else:
            self.info_label.setText("Aucun dossier sélectionné")

    # ═══════════════════════════════════════════════════════════════
    # MÉTHODES UI (Appelées par le contrôleur)
    # ═══════════════════════════════════════════════════════════════

    def show_warning(self, title, message):
        """Affiche une boîte de dialogue d'avertissement"""
        QMessageBox.warning(self, title, message)

    def show_error(self, title, message):
        """Affiche une boîte de dialogue d'erreur"""
        QMessageBox.critical(self, title, message)

    def show_info(self, title, message):
        """Affiche une boîte de dialogue d'information"""
        QMessageBox.information(self, title, message)

    def ask_confirmation(self, title, message):
        """Demande une confirmation à l'utilisateur"""
        reponse = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reponse == QMessageBox.StandardButton.Yes


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from models.app_model import ApplicationModel
    except ImportError:
        print("❌ Erreur import")
        sys.exit(1)
    
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    model = ApplicationModel()
    model.creer_campagne("Test", "./test")
    
    controller = ImportationKosmosController(model)
    
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1400, 800)
    
    view = ImportationKosmosView(controller)
    window.setCentralWidget(view)
    
    controller.navigation_demandee.connect(lambda p: print(f"→ {p}"))
    
    window.show()
    sys.exit(app.exec())
