"""
Composant NavBar réutilisable
"""
import sys
from PyQt6.QtWidgets import QPushButton, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QFontDatabase

from components.commons import COLORS, FONTS, SPACING


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
            tabs: Liste des noms d'onglets (par défaut: ["Fichier", "Tri", "Extraction", "Évènements"])
            default_tab: Onglet actif par défaut (par défaut: premier onglet)
            parent: Widget parent
        """
        super().__init__(parent)

        
        # Configuration des onglets
        if tabs is None:
            self.tabs = ["Fichier", "Tri", "Extraction", "Évènements"]
        else:
            self.tabs = tabs
            
        self.default_tab = default_tab if default_tab else (self.tabs[1] if len(self.tabs) > 1 else self.tabs[0])
        
        # Variables pour le drag & drop
        self.drag_position = None
        
        # Dictionnaire pour stocker les boutons
        self.tab_buttons = {}
        
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        # Layout principal horizontal
        layout = QHBoxLayout()
        layout.setContentsMargins(SPACING["lg"], 0, SPACING["lg"], 0)
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
        minimize_btn = self.create_control_button("─", self.minimize_window, COLORS["text_secondary"])
        layout.addWidget(minimize_btn)
        
        # Bouton de maximisation/restauration
        self.maximize_btn = self.create_control_button("□", self.toggle_maximize, COLORS["text_secondary"])
        layout.addWidget(self.maximize_btn)
        
        # Bouton de fermeture
        close_btn = self.create_control_button("✕", self.close_window, COLORS["danger"])
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Style de la barre de navigation - thème sombre cohérent
        self.setStyleSheet(
            f"QWidget {{"
            f"background-color: {COLORS['bg_secondary']};"
            f"border-bottom: 1px solid {COLORS['border']};"
            f"font-family: '{FONTS['primary']}';"
            f"color: {COLORS['text_primary']};"
            f"}}"
        )
        self.setFixedHeight(54)
    
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
        
        btn.setStyleSheet(self._nav_button_style(is_active))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self.on_tab_clicked(btn))
        
        return btn

    def _nav_button_style(self, active: bool) -> str:
        """Style uniforme pour les onglets."""
        return (
            f"QPushButton {{"
            f"background-color: {COLORS['accent_cyan'] if active else 'transparent'};"
            f"color: {COLORS['bg_primary'] if active else COLORS['text_primary']};"
            f"border: none;"
            f"padding: 10px 16px;"
            f"font-size: {FONTS['sizes']['base']}px;"
            f"font-weight: 700;"
            f"margin: 0px 4px;"
            f"border-radius: 10px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {COLORS['accent_cyan_light'] if active else COLORS['bg_tertiary']};"
            f"color: {COLORS['bg_primary'] if active else COLORS['text_primary']};"
            f"}}"
        )
    
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
        
        danger = hover_color == COLORS["danger"]
        fg = COLORS["text_primary"]
        style = (
            f"QPushButton {{"
            f"background-color: transparent;"
            f"border: none;"
            f"color: {fg};"
            f"font-size: {FONTS['sizes']['lg']}px;"
            f"font-weight: 600;"
            f"border-radius: 8px;"
            f"padding: 6px;"
            f"}}"
            f"QPushButton:hover {{"
            f"background-color: {hover_color};"
            f"color: {COLORS['bg_primary'] if danger else COLORS['bg_primary']};"
            f"}}"
        )
        
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
        for btn in self.tab_buttons.values():
            is_active = btn is clicked_btn
            btn.setChecked(is_active)
            btn.setStyleSheet(self._nav_button_style(is_active))
        
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
                tabs=["Fichier", "Tri", "Extraction", "Évènements"],
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
