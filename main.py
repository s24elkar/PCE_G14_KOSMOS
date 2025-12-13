"""
APPLICATION PRINCIPALE - KOSMOS
Application complète avec navigation entre les pages
Architecture MVC
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Import du modèle KOSMOS
from models.app_model import ApplicationModel

# Import des contrôleurs et vues
from views.accueil_view import AccueilKosmosView
from controllers.accueil_controller import AccueilKosmosController
from views.telechargement_view import TelechargementKosmosView
from controllers.telechargement_controller import TelechargementController
from views.tri_view import TriKosmosView
from controllers.tri_controller import TriKosmosController
from views.extraction_view import ExtractionView
from controllers.extraction_controller import ExtractionKosmosController


class KosmosApplication(QMainWindow):
    """
    Application principale KOSMOS
    Gère la navigation entre les différentes pages
    """
    
    def __init__(self):
        super().__init__()
        
        # Modèle unique de l'application
        self.model = ApplicationModel()
        
        # Contrôleurs pour chaque page
        self.accueil_controller = None
        self.telechargement_controller = None
        self.tri_controller = None
        self.extraction_controller = None 
        
        # Vues
        self.accueil_view = None
        self.telechargement_view = None
        self.tri_view = None
        self.extraction_view = None
        
        self.init_ui()
        self.init_controllers()
        self.connecter_navigation()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(50, 50, 1400, 850)
        self.setWindowTitle("KOSMOS - Dérushage Vidéo Sous-Marine")
        
        # Widget central avec stack pour gérer les pages
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        print("✅ Interface principale initialisée")
    
    def init_controllers(self):
        """Initialise les contrôleurs et les vues"""
        
        # PAGE D'ACCUEIL
        self.accueil_controller = AccueilKosmosController(self.model)
        self.accueil_view = AccueilKosmosView(self.accueil_controller)
        self.accueil_controller.set_view(self.accueil_view)
        self.stack.addWidget(self.accueil_view)

        # PAGE DE TÉLÉCHARGEMENT
        self.telechargement_controller = TelechargementController(self.model)
        self.telechargement_view = TelechargementKosmosView(self.telechargement_controller)
        self.stack.addWidget(self.telechargement_view)
        
        # PAGE DE TRI
        self.tri_controller = TriKosmosController(self.model)
        self.tri_view = TriKosmosView(self.tri_controller)
        self.stack.addWidget(self.tri_view)
        
        # PAGE D'EXTRACTION
        self.extraction_controller = ExtractionKosmosController(self.model)
        self.extraction_view = ExtractionView(self.extraction_controller)
        # Important : Lier la vue au contrôleur
        self.extraction_controller.set_view(self.extraction_view)

        # Charger les données uniquement lorsque la vue est réellement affichée
        self.extraction_view.view_shown.connect(self.extraction_controller.load_initial_data)
        self.stack.addWidget(self.extraction_view)

        # Afficher la page d'accueil par défaut
        self.stack.setCurrentWidget(self.accueil_view)
        
        print("✅ Contrôleurs et vues initialisés")
    
    def connecter_navigation(self):
        """Connecte les signaux de navigation entre les pages"""
        
        # Navigation depuis la page d'accueil
        if self.accueil_controller:
            self.accueil_controller.navigation_demandee.connect(self.naviguer_vers)
            self.accueil_controller.campagne_creee.connect(self.on_campagne_creee)
            self.accueil_controller.campagne_ouverte.connect(self.on_campagne_ouverte)

        # Navigation depuis la page de téléchargement
        if self.telechargement_controller:
            self.telechargement_controller.navigation_demandee.connect(self.naviguer_vers)
            
        # Navigation depuis la page de tri
        if self.tri_controller:
            self.tri_controller.navigation_demandee.connect(self.naviguer_vers)

        # Navigation depuis la page d'extraction
        if self.extraction_controller:
            self.extraction_controller.navigation_demandee.connect(self.naviguer_vers)

        # Gérer les changements d'onglet dans la navbar (Vue -> Main)
        for view in [self.accueil_view, self.telechargement_view,
                     self.tri_view, self.extraction_view]:
            if view and hasattr(view, 'navbar'):
                view.navbar.tab_changed.connect(self.on_navbar_tab_changed)
                # Connecter le signal de téléchargement si disponible (NavBarAvecMenu)
                if hasattr(view.navbar, 'telechargement_clicked'):
                    view.navbar.telechargement_clicked.connect(lambda: self.naviguer_vers('telechargement'))
        
        print("✅ Navigation connectée")
    
    def naviguer_vers(self, nom_page: str):
        """
        Navigue vers une page spécifique
        """
        print(f"🔄 Navigation vers : {nom_page}")
        
        # Mettre à jour l'état dans le modèle
        self.model.page_courante = nom_page
        
        # Changer de vue
        if nom_page == "accueil":
            self.stack.setCurrentWidget(self.accueil_view)

        elif nom_page == "telechargement":
            if self.telechargement_view:
                self.stack.setCurrentWidget(self.telechargement_view)
            else:
                print("❌ Page de téléchargement non disponible")

        elif nom_page == "tri":
            if self.tri_view:
                self.tri_view.charger_videos()
                self.stack.setCurrentWidget(self.tri_view)
                print(f"📹 {len(self.model.obtenir_videos())} vidéo(s) affichée(s)")
            else:
                print("❌ Page de tri non disponible")

        elif nom_page == "extraction":
            if self.extraction_view:
                self.stack.setCurrentWidget(self.extraction_view)
            else:
                print("❌ Page d'extraction non disponible")

        elif nom_page == "evenements":
            print("⚠️ Page d'événements pas encore implémentée")
        else:
            print(f"⚠️ Page inconnue : {nom_page}")
    
    def on_navbar_tab_changed(self, tab_name: str):
        """Gère le changement d'onglet dans la navbar"""
        mapping = {
            'Fichier': 'accueil',
            'Téléchargement': 'telechargement',
            'Tri': 'tri',
            'Extraction': 'extraction',
            'Évènements': 'evenements'
        }
        page = mapping.get(tab_name)
        if page:
            self.naviguer_vers(page)
    
    def on_campagne_creee(self, nom: str, emplacement: str):
        print(f"✅ Campagne créée : {nom} dans {emplacement}")
        # Recharger les données dans tous les contrôleurs
        if self.tri_controller:
            self.tri_view.charger_videos()
        if self.extraction_controller:
            self.extraction_controller.load_initial_data()
    
    def on_campagne_ouverte(self, chemin: str):
        print(f"✅ Campagne ouverte : {chemin}")
        # Recharger les données dans tous les contrôleurs
        if self.tri_controller:
            self.tri_view.charger_videos()
        if self.extraction_controller:
            self.extraction_controller.load_initial_data()
    
    def closeEvent(self, event):
        if self.model.campagne_courante:
            self.model.sauvegarder_campagne()
            print("💾 Campagne sauvegardée avant fermeture")
        event.accept()


def main():
    """Lance l'application KOSMOS"""
    print("=" * 60)
    print("🚀 LANCEMENT DE L'APPLICATION KOSMOS")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    window = KosmosApplication()
    window.show()
    
    print("\n✅ Application lancée avec succès!")
    print("\n" + "=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
