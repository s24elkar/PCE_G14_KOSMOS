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


# ═══════════════════════════════════════════════════════════════
# DIALOGUE NOUVELLE CAMPAGNE
# ═══════════════════════════════════════════════════════════════

class FenetreNouvelleCampagne(QDialog):
    """Dialogue pour créer une nouvelle campagne"""
    
    campagneCreee = pyqtSignal(str, str)  # signal : nom, emplacement (vide)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau répertoire de travail")
        self.setFixedSize(500, 200)  # Taille réduite
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Titre
        titre = QLabel("Nouveau répertoire de travail")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet("""
            QLabel {
                color: #1DA1FF;
                font-size: 20px;
                font-weight: bold;
                padding: 15px;
                background-color: white;
                border-radius: 5px;
            }
        """)
        layout.addWidget(titre)

        # Ligne : Nom uniquement
        nom_layout = QHBoxLayout()
        nom_label = QLabel("Nom du répertoire :")
        nom_label.setFixedWidth(150)
        nom_label.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; }")
        self.nom_edit = QLineEdit()
        self.nom_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 2px solid white;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        nom_layout.addWidget(nom_label)
        nom_layout.addWidget(self.nom_edit)

        # Message informatif
        info_label = QLabel("Le répertoire sera créé dans le dossier d'importation des vidéos")
        info_label.setStyleSheet("QLabel { color: #888; font-size: 11px; font-style: italic; }")
        info_label.setWordWrap(True)

        # Boutons OK / Annuler
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setFixedSize(120, 40)
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        btn_annuler.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Ok")
        btn_ok.setFixedSize(120, 40)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 2px solid white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        btn_ok.clicked.connect(self.valider)
        
        buttons_layout.addWidget(btn_annuler)
        buttons_layout.addWidget(btn_ok)

        # Ajout au layout principal
        layout.addLayout(nom_layout)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addLayout(buttons_layout)

    def valider(self):
        """Validation"""
        nom = self.nom_edit.text().strip()

        if not nom:
            QMessageBox.warning(self, "Champ manquant", "Veuillez renseigner le nom du répertoire.")
            return

        # Émission du signal avec emplacement vide
        self.campagneCreee.emit(nom, "")
        self.accept()


# ═══════════════════════════════════════════════════════════════
# NAVBAR AVEC MENU FICHIER
# ═══════════════════════════════════════════════════════════════

class NavBarAvecMenu(QWidget):
    """NavBar avec menu déroulant sur "Fichier" - FOND BLANC FORCÉ"""
    
    tab_changed = pyqtSignal(str)
    nouvelle_campagne_clicked = pyqtSignal()
    ouvrir_campagne_clicked = pyqtSignal()
    enregistrer_clicked = pyqtSignal()
    enregistrer_sous_clicked = pyqtSignal()
    
    def __init__(self, tabs=None, default_tab=None, disable_tabs=False, parent=None):
        super().__init__(parent)
        
        if tabs is None:
            self.tabs = ["Fichier", "Tri", "Extraction", "Évènements"]
        else:
            self.tabs = tabs
            
        self.default_tab = default_tab if default_tab else self.tabs[0]
        self.disable_tabs = disable_tabs
        self.drag_position = None
        self.tab_buttons = {}
        
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)
        
        for tab_name in self.tabs:
            is_active = (tab_name == self.default_tab)
            btn = self.create_nav_button(tab_name, is_active)
            self.tab_buttons[tab_name] = btn
            layout.addWidget(btn)
            
            if tab_name == "Fichier":
                self.fichier_btn = btn
                self.create_fichier_menu()
        
        layout.addStretch()
        
        minimize_btn = self.create_control_button("─", self.minimize_window, "#e0e0e0")
        layout.addWidget(minimize_btn)
        
        self.maximize_btn = self.create_control_button("□", self.toggle_maximize, "#e0e0e0")
        layout.addWidget(self.maximize_btn)
        
        close_btn = self.create_control_button("✕", self.close_window, "#ff4444")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        from PyQt6.QtGui import QPalette, QColor
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        self.setStyleSheet("""
            NavBarAvecMenu {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                font-family: 'Montserrat', 'Arial', sans-serif;
            }
        """)
        self.setFixedHeight(50)
    
    def create_nav_button(self, text, is_active=False):
        """Crée un bouton de navigation"""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(is_active)
        
        if self.disable_tabs and text != "Fichier":
            btn.setEnabled(False)
            style = """
                QPushButton {
                    background-color: transparent;
                    color: #999;
                    border: none;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    margin: 0px 2px;
                    border-radius: 4px;
                }
            """
        elif is_active:
            style = """
                QPushButton {
                    background-color: #1DA1FF;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    margin: 0px 2px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1E88E5;
                }
            """
        else:
            style = """
                QPushButton {
                    background-color: transparent;
                    color: black;
                    border: none;
                    padding: 8px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    margin: 0px 2px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f5f5f5;
                }
                QPushButton:checked {
                    background-color: #2196F3;
                    color: white;
                }
            """
        
        btn.setStyleSheet(style)
        
        if not (self.disable_tabs and text != "Fichier"):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if text != "Fichier":
            btn.clicked.connect(lambda: self.on_tab_clicked(btn))
        else:
            btn.clicked.connect(self.show_fichier_menu)
        
        return btn
    
    def create_fichier_menu(self):
        """Crée le menu déroulant pour "Fichier" """
        self.fichier_menu = QMenu(self)
        self.fichier_menu.setStyleSheet("""
            QMenu {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                color: black;
                padding: 8px 30px 8px 20px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        
        action_creer = QAction("Créer un repertoire de travail", self)
        action_creer.triggered.connect(self.nouvelle_campagne_clicked.emit)
        self.fichier_menu.addAction(action_creer)
        
        action_ouvrir = QAction("Ouvrir un repertoire de travail", self)
        action_ouvrir.triggered.connect(self.ouvrir_campagne_clicked.emit)
        self.fichier_menu.addAction(action_ouvrir)
        
        self.fichier_menu.addSeparator()
        
        action_enregistrer = QAction("Enregistrer", self)
        action_enregistrer.triggered.connect(self.enregistrer_clicked.emit)
        self.fichier_menu.addAction(action_enregistrer)
        
        action_enregistrer_sous = QAction("Enregistrer sous", self)
        action_enregistrer_sous.triggered.connect(self.enregistrer_sous_clicked.emit)
        self.fichier_menu.addAction(action_enregistrer_sous)
    
    def show_fichier_menu(self):
        """Affiche le menu déroulant "Fichier" """
        button_pos = self.fichier_btn.mapToGlobal(QPoint(0, self.fichier_btn.height()))
        self.fichier_menu.exec(button_pos)
    
    def create_control_button(self, text, callback, hover_color):
        """Crée un bouton de contrôle"""
        btn = QPushButton(text)
        btn.setFixedSize(40, 40)
        
        if hover_color == "#ff4444":
            style = f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: #333;
                    font-size: 20px;
                    font-weight: normal;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                    color: white;
                }}
            """
        else:
            style = f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: #333;
                    font-size: 18px;
                    font-weight: normal;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """
        
        btn.setStyleSheet(style)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        
        return btn
    
    def on_tab_clicked(self, clicked_btn):
        """Gère le clic sur un onglet"""
        for btn in self.tab_buttons.values():
            if btn != clicked_btn:
                btn.setChecked(False)
        
        clicked_btn.setChecked(True)
        tab_name = clicked_btn.text()
        self.tab_changed.emit(tab_name)
    
    def mousePressEvent(self, event):
        """Permet de déplacer la fenêtre"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Déplace la fenêtre"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Fin du déplacement"""
        self.drag_position = None
    
    def minimize_window(self):
        """Minimise la fenêtre"""
        self.window().showMinimized()
    
    def toggle_maximize(self):
        """Bascule entre maximisé et restauré"""
        if self.window().isMaximized():
            self.window().showNormal()
            self.maximize_btn.setText("□")
        else:
            self.window().showMaximized()
            self.maximize_btn.setText("❐")
    
    def close_window(self):
        """Ferme la fenêtre"""
        self.window().close()


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
        
        self.navbar = NavBarAvecMenu(
            tabs=["Fichier", "Tri", "Extraction", "Évènements"],
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
            lambda: self.controller.on_creer_campagne(self)
        )
        self.navbar.ouvrir_campagne_clicked.connect(
            lambda: self.controller.on_ouvrir_campagne(self)
        )
        self.navbar.enregistrer_clicked.connect(
            lambda: self.controller.on_enregistrer(self)
        )
        self.navbar.enregistrer_sous_clicked.connect(
            lambda: self.controller.on_enregistrer_sous(self)
        )


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