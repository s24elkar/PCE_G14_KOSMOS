"""
Composant NavBar réutilisable 
Barre de navigation personnalisée avec onglets et contrôles de fenêtre
"""
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPalette, QColor, QAction

class NavBar(QWidget):
    """
    Barre de navigation personnalisée avec menu déroulant sur "Fichier"
    Gère les onglets, le drag & drop de la fenêtre et les contrôles (min/max/close)
    """
    
    tab_changed = pyqtSignal(str)
    ouvrir_campagne_clicked = pyqtSignal()
    telechargement_clicked = pyqtSignal()
    
    def __init__(self, tabs=None, default_tab=None, disable_tabs=False, parent=None):
        super().__init__(parent)
        
        if tabs is None:
            self.tabs = ["Fichier", "Tri", "Extraction", "IA"]
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
        
        """Créer les boutons d'onglets"""
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
            NavBar {
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
        
        action_ouvrir = QAction("Ouvrir campagne", self)
        action_ouvrir.triggered.connect(self.ouvrir_campagne_clicked.emit)
        self.fichier_menu.addAction(action_ouvrir)
        
        self.fichier_menu.addSeparator()

        action_telechargement = QAction("Téléchargement", self)
        action_telechargement.triggered.connect(self.telechargement_clicked.emit)
        self.fichier_menu.addAction(action_telechargement)
    
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
        """Maximise ou restaure la fenêtre"""   
        if self.window().isMaximized():
            self.window().showNormal()
            self.maximize_btn.setText("□")
        else:
            self.window().showMaximized()
            self.maximize_btn.setText("❐")
    
    def close_window(self):
        """Ferme la fenêtre"""
        self.window().close()
