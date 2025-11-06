"""
VUE + CONTRÔLEUR - Page d'importation KOSMOS (CONFORME MAQUETTE FINALE)
Avec explorateur de fichiers complet comme Windows Explorer
Architecture MVC
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
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint
from PyQt6.QtGui import QFont, QAction, QPalette, QColor


# ═══════════════════════════════════════════════════════════════
# NAVBAR AVEC MENU FICHIER
# ═══════════════════════════════════════════════════════════════

class NavBarAvecMenu(QWidget):
    tab_changed = pyqtSignal(str)
    nouvelle_campagne_clicked = pyqtSignal()
    ouvrir_campagne_clicked = pyqtSignal()
    enregistrer_clicked = pyqtSignal()
    enregistrer_sous_clicked = pyqtSignal()
    
    def __init__(self, tabs=None, default_tab=None, parent=None):
        super().__init__(parent)
        
        if tabs is None:
            self.tabs = ["Fichier", "Tri", "Extraction", "Évènements"]
        else:
            self.tabs = tabs
            
        self.default_tab = default_tab if default_tab else self.tabs[0]
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
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        self.setStyleSheet("""
            NavBarAvecMenu {
                background-color: rgb(255, 255, 255);
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(50)
    
    def create_nav_button(self, text, is_active=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(is_active)
        
        if is_active:
            style = "QPushButton { background-color: #1DA1FF; color: white; border: none; padding: 8px 20px; font-size: 14px; border-radius: 4px; }"
        else:
            style = "QPushButton { background-color: transparent; color: black; border: none; padding: 8px 20px; font-size: 14px; border-radius: 4px; } QPushButton:hover { background-color: #f5f5f5; }"
        
        btn.setStyleSheet(style)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if text != "Fichier":
            btn.clicked.connect(lambda: self.on_tab_clicked(btn))
        else:
            btn.clicked.connect(self.show_fichier_menu)
        
        return btn
    
    def create_fichier_menu(self):
        self.fichier_menu = QMenu(self)
        self.fichier_menu.setStyleSheet("QMenu { background-color: #f5f5f5; border: 1px solid #ddd; padding: 5px; } QMenu::item { padding: 8px 30px 8px 20px; } QMenu::item:selected { background-color: #2196F3; color: white; }")
        
        action_creer = QAction("Créer campagne", self)
        action_creer.triggered.connect(self.nouvelle_campagne_clicked.emit)
        self.fichier_menu.addAction(action_creer)
        
        action_ouvrir = QAction("Ouvrir campagne", self)
        action_ouvrir.triggered.connect(self.ouvrir_campagne_clicked.emit)
        self.fichier_menu.addAction(action_ouvrir)
        
        self.fichier_menu.addSeparator()
        
        action_enregistrer = QAction("Enregistrer", self)
        action_enregistrer.triggered.connect(self.enregistrer_clicked.emit)
        self.fichier_menu.addAction(action_enregistrer)
    
    def show_fichier_menu(self):
        button_pos = self.fichier_btn.mapToGlobal(QPoint(0, self.fichier_btn.height()))
        self.fichier_menu.exec(button_pos)
    
    def create_control_button(self, text, callback, hover_color):
        btn = QPushButton(text)
        btn.setFixedSize(40, 40)
        btn.setStyleSheet(f"QPushButton {{ background-color: transparent; border: none; color: #333; }} QPushButton:hover {{ background-color: {hover_color}; }}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn
    
    def on_tab_clicked(self, clicked_btn):
        for btn in self.tab_buttons.values():
            if btn != clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)
        self.tab_changed.emit(clicked_btn.text())
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None
    
    def minimize_window(self):
        self.window().showMinimized()
    
    def toggle_maximize(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.maximize_btn.setText("□")
        else:
            self.window().showMaximized()
            self.maximize_btn.setText("❐")
    
    def close_window(self):
        self.window().close()


# ═══════════════════════════════════════════════════════════════
# CONTRÔLEUR
# ═══════════════════════════════════════════════════════════════

class ImportationKosmosController(QObject):
    navigation_demandee = pyqtSignal(str)
    importation_terminee = pyqtSignal(dict)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
    
    def on_importer_dossier(self, chemin_dossier: str, view_parent=None):
        """Importe le dossier sélectionné"""
        if not chemin_dossier or not os.path.isdir(chemin_dossier):
            QMessageBox.warning(view_parent, "Erreur", "Veuillez sélectionner un dossier valide.")
            return
        
        if not self.model.campagne_courante:
            QMessageBox.critical(view_parent, "Pas de campagne", "Créez d'abord une campagne depuis Fichier > Créer campagne.")
            return
        
        print(f"📁 Dossier à importer : {chemin_dossier}")
        
        # Vérifier si le dossier contient des sous-dossiers numérotés
        try:
            contenu = os.listdir(chemin_dossier)
            sous_dossiers = [d for d in contenu if os.path.isdir(os.path.join(chemin_dossier, d))]
            dossiers_numerotes = [d for d in sous_dossiers if d.isdigit()]
            
            if not dossiers_numerotes:
                reponse = QMessageBox.question(
                    view_parent,
                    "Confirmation",
                    f"Le dossier '{os.path.basename(chemin_dossier)}' ne contient pas de sous-dossiers numérotés.\n\nVoulez-vous quand même l'importer ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reponse == QMessageBox.StandardButton.No:
                    return
            
            print(f"📹 Lancement de l'importation...")
            
            # Importer les vidéos
            resultats = self.model.importer_videos_kosmos(chemin_dossier)
            
            # Sauvegarder
            self.model.sauvegarder_campagne()
            
            # Afficher les résultats
            nb_importees = len(resultats['videos_importees'])
            nb_sans_meta = len(resultats['videos_sans_metadata'])
            nb_erreurs = len(resultats['erreurs'])
            
            if nb_importees == 0:
                QMessageBox.warning(
                    view_parent,
                    "Aucune vidéo",
                    "Aucune vidéo n'a été trouvée dans ce dossier."
                )
                return
            
            message = f"✅ Importation terminée !\n\n"
            message += f"📹 Vidéos importées : {nb_importees}\n"
            
            if nb_sans_meta > 0:
                message += f"⚠️  Vidéos sans métadonnées : {nb_sans_meta}\n"
            
            if nb_erreurs > 0:
                message += f"\n❌ Erreurs : {nb_erreurs}\n"
            
            QMessageBox.information(view_parent, "Importation réussie", message)
            
            # Émettre le signal
            self.importation_terminee.emit(resultats)
            
            # Naviguer vers tri
            print("🔄 Navigation vers la page de tri...")
            self.navigation_demandee.emit('tri')
            
        except Exception as e:
            QMessageBox.critical(
                view_parent,
                "Erreur d'importation",
                f"Une erreur s'est produite lors de l'importation :\n\n{str(e)}"
            )
            print(f"❌ Erreur : {e}")


# ═══════════════════════════════════════════════════════════════
# VUE
# ═══════════════════════════════════════════════════════════════

class ImportationKosmosView(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.auto_open = True  # Flag pour ouvrir automatiquement
        self.init_ui()
    
    def showEvent(self, event):
        """Appelé quand la vue devient visible"""
        super().showEvent(event)
        if self.auto_open:
            self.auto_open = False  # Ne déclencher qu'une fois
            # Ouvrir le dialogue après un court délai
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.on_select_folder)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBarAvecMenu(tabs=["Fichier", "Tri", "Extraction", "Évènements"], default_tab="Fichier")
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
        from PyQt6.QtWidgets import QFileDialog
        
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
                for item in contenu[:10]:  # Afficher les 10 premiers
                    chemin_complet = os.path.join(dossier, item)
                    type_item = "📁" if os.path.isdir(chemin_complet) else "📄"
                    print(f"   {type_item} {item}")
                if len(contenu) > 10:
                    print(f"   ... et {len(contenu) - 10} autres éléments")
            except Exception as e:
                print(f"   ❌ Erreur lecture : {e}")
            
            # Lancer l'importation
            if self.controller:
                self.controller.on_importer_dossier(dossier, self)
        else:
            self.info_label.setText("Aucun dossier sélectionné")


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from app_model_kosmos import ApplicationModel
    except ImportError:
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