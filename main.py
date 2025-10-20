"""
Point d'entrée principal de l'application
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Imports des composants (à décommenter quand les fichiers sont séparés)
from src.models.media_model import MediaModel
from src.views.accueil_view import MainWindow
from src.controllers.accueil_controller import MediaController
from utils.style_loader import apply_stylesheet_from_string
# from styles.style import QSS_CONTENT


def main():
    """Fonction principale"""
    # Configuration de l'application
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    
    # Création du modèle
    model = MediaModel()
    
    # Création de la vue
    view = MainWindow()
    
    # Application du style
    apply_stylesheet_from_string(app, QSS_CONTENT)
    
    # Création du contrôleur
    controller = MediaController(model, view)
    
    # Affichage de la fenêtre
    view.show()
    
    # Lancement de la boucle d'événements
    sys.exit(app.exec())


if __name__ == "__main__":
    main()