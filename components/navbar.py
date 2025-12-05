"""
Composant NavBar réutilisable 
"""
import sys
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QFontDatabase


class NavBar(QWidget):
    """
    Barre de navigation personnalisée avec contrôles de fenêtre
    
    Signaux:
        tab_changed: Émis quand un onglet est sélectionné (str: nom de l'onglet)
    """
    
    tab_changed = pyqtSignal(str)
    
    def __init__(self, tabs=None, default_tab=None, parent=None):
        """
        Args:
            tabs: Liste des noms d'onglets (par défaut: ["Fichier", "Tri", "IA", "Extraction", "Évènements"])
            default_tab: Onglet actif par défaut (par défaut: premier onglet)
            parent: Widget parent
        """
        super().__init__(parent)


        # Configuration des onglets
        if tabs is None:
            self.tabs = ["Fichier", "Tri", "Téléchargement", "IA", "Extraction", "Évènements"]
        else:
            self.tabs = tabs
            
        # Rendre l'onglet Tri par défaut si aucun onglet précisé
        if default_tab:
            self.default_tab = default_tab
        else:
            self.default_tab = "Tri" if "Tri" in self.tabs else (self.tabs[0] if self.tabs else "")
        
        # Variables pour le drag & drop
        self.drag_position = None
        
        # Dictionnaire pour stocker les boutons
        self.tab_buttons = {}
        
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        # Layout principal horizontal
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)
        
        # Créer les boutons de navigation
        for tab_name in self.tabs:
            is_active = (tab_name == self.default_tab)
            btn = self.create_nav_button(tab_name, is_active)
            self.tab_buttons[tab_name] = btn
            layout.addWidget(btn)
        
        # Ajouter un stretch pour pousser les boutons de contrôle à droite
        layout.addStretch()
        
        # Bouton de réduction
        minimize_btn = self.create_control_button("─", self.minimize_window, "#e0e0e0")
        layout.addWidget(minimize_btn)
        
        # Bouton de maximisation/restauration
        self.maximize_btn = self.create_control_button("□", self.toggle_maximize, "#e0e0e0")
        layout.addWidget(self.maximize_btn)
        
        # Bouton de fermeture
        close_btn = self.create_control_button("✕", self.close_window, "#ff4444")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Style de la barre de navigation - FOND BLANC
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                font-family: 'Montserrat';
            }
        """)
        self.setFixedHeight(50)
    
    def create_nav_button(self, text, is_active=False):
        """
        Crée un bouton de navigation avec le style approprié
        
        Args:
            text: Texte du bouton
            is_active: Si le bouton est actif par défaut
            
        Returns:
            QPushButton: Le bouton créé
        """
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(is_active)
        
        # Style pour les boutons
        if is_active:
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
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.on_tab_clicked(btn))
        
        return btn
    
    def create_control_button(self, text, callback, hover_color):
        """
        Crée un bouton de contrôle (minimiser, maximiser, fermer)
        
        Args:
            text: Texte/icône du bouton
            callback: Fonction à appeler au clic
            hover_color: Couleur au survol
            
        Returns:
            QPushButton: Le bouton créé
        """
        btn = QPushButton(text)
        btn.setFixedSize(40, 40)
        
        if hover_color == "#ff4444":  # Bouton fermer
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
        """
        Gère le clic sur un onglet
        
        Args:
            clicked_btn: Le bouton cliqué
        """
        # Décocher tous les autres boutons
        for btn in self.tab_buttons.values():
            if btn != clicked_btn:
                btn.setChecked(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #333;
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
                """)
        
        # Activer le bouton cliqué
        clicked_btn.setChecked(True)
        clicked_btn.setStyleSheet("""
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
        """)
        
        # Émettre le signal avec le nom de l'onglet
        tab_name = clicked_btn.text()
        self.tab_changed.emit(tab_name)
        print(f"Onglet sélectionné: {tab_name}")
    
    def get_active_tab(self):
        """
        Retourne le nom de l'onglet actif
        
        Returns:
            str: Nom de l'onglet actif
        """
        for name, btn in self.tab_buttons.items():
            if btn.isChecked():
                return name
        return None
    
    def set_active_tab(self, tab_name):
        """
        Active un onglet spécifique
        
        Args:
            tab_name: Nom de l'onglet à activer
        """
        if tab_name in self.tab_buttons:
            self.on_tab_clicked(self.tab_buttons[tab_name])
    
    def mousePressEvent(self, event):
        """Permet de déplacer la fenêtre en cliquant sur la navbar"""
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


# Exemple d'utilisation
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.init_ui()
            
        def init_ui(self):
            # Fenêtre sans bordures (frameless)
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.setGeometry(100, 100, 1000, 700)
            
            # Widget central
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout principal
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # Ajouter la navbar personnalisée
            # Vous pouvez personnaliser les onglets ici
            self.navbar = NavBar(
                tabs=["Fichier", "Tri", "IA", "Extraction", "Évènements"],
                default_tab="Tri"
            )
            
            # Connecter le signal pour réagir aux changements d'onglet
            self.navbar.tab_changed.connect(self.on_tab_changed)
            
            main_layout.addWidget(self.navbar)
            
            # Zone de contenu
            self.content_label = QLabel("Contenu de l'application - Onglet: Tri")
            self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_label.setStyleSheet("""
                font-size: 24px; 
                color: #666; 
                background-color: #f9f9f9;
            """)
            main_layout.addWidget(self.content_label)
            
            central_widget.setLayout(main_layout)
        
        def on_tab_changed(self, tab_name):
            """Réagit au changement d'onglet"""
            self.content_label.setText(f"Contenu de l'application - Onglet: {tab_name}")
            # Ici vous pouvez charger différents widgets selon l'onglet sélectionné
    
    app = QApplication(sys.argv)
    
    # Configuration de la police par défaut
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
