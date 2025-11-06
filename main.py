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
from views.accueil_view import AccueilKosmosView, AccueilKosmosController
from views.importation_view import ImportationKosmosView, ImportationKosmosController
from views.tri_view import TriKosmosView, TriKosmosController


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
        self.importation_controller = None
        self.tri_controller = None
        
        # Vues
        self.accueil_view = None
        self.importation_view = None
        self.tri_view = None
        
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
        self.stack.addWidget(self.accueil_view)
        
        # PAGE D'IMPORTATION
        self.importation_controller = ImportationKosmosController(self.model)
        self.importation_view = ImportationKosmosView(self.importation_controller)
        self.stack.addWidget(self.importation_view)
        
        # PAGE DE TRI
        self.tri_controller = TriKosmosController(self.model)
        self.tri_view = TriKosmosView(self.tri_controller)
        self.stack.addWidget(self.tri_view)
        
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
        
        # Navigation depuis la page d'importation
        if self.importation_controller:
            self.importation_controller.navigation_demandee.connect(self.naviguer_vers)
        
        # Gérer les changements d'onglet dans la navbar
        if self.accueil_view and hasattr(self.accueil_view, 'navbar'):
            self.accueil_view.navbar.tab_changed.connect(self.on_navbar_tab_changed)
        
        if self.importation_view and hasattr(self.importation_view, 'navbar'):
            self.importation_view.navbar.tab_changed.connect(self.on_navbar_tab_changed)
        
        if self.tri_view and hasattr(self.tri_view, 'navbar'):
            self.tri_view.navbar.tab_changed.connect(self.on_navbar_tab_changed)
        
        print("✅ Navigation connectée")
    
    def naviguer_vers(self, nom_page: str):
        """
        Navigue vers une page spécifique
        
        Args:
            nom_page: Nom de la page ('accueil', 'importation', 'tri', 'extraction', 'evenements')
        """
        print(f"🔄 Navigation vers : {nom_page}")
        
        # Mettre à jour l'état dans le modèle
        self.model.page_courante = nom_page
        
        # Changer de vue
        if nom_page == "accueil":
            self.stack.setCurrentWidget(self.accueil_view)
            
        elif nom_page == "importation":
            self.stack.setCurrentWidget(self.importation_view)
            # Réinitialiser le flag pour rouvrir le dialogue
            self.importation_view.auto_open = True
            
        elif nom_page == "tri":
            if self.tri_view:
                # Recharger les vidéos
                self.tri_view.charger_videos()
                self.stack.setCurrentWidget(self.tri_view)
                print(f"📹 {len(self.model.obtenir_videos())} vidéo(s) affichée(s)")
            else:
                print("❌ Page de tri non disponible")
                
        elif nom_page == "extraction":
            print("⚠️ Page d'extraction pas encore implémentée")
            
        elif nom_page == "evenements":
            print("⚠️ Page d'événements pas encore implémentée")
        
        else:
            print(f"⚠️ Page inconnue : {nom_page}")
    
    def on_navbar_tab_changed(self, tab_name: str):
        """
        Gère le changement d'onglet dans la navbar
        
        Args:
            tab_name: Nom de l'onglet ('Fichier', 'Tri', 'Extraction', 'Évènements')
        """
        # Mapper les noms d'onglets vers les pages
        mapping = {
            'Fichier': 'accueil',
            'Tri': 'tri',
            'Extraction': 'extraction',
            'Évènements': 'evenements'
        }
        
        page = mapping.get(tab_name)
        if page:
            self.naviguer_vers(page)
    
    def on_campagne_creee(self, nom: str, emplacement: str):
        """
        Appelé quand une campagne est créée
        
        Args:
            nom: Nom de la campagne
            emplacement: Emplacement de la campagne
        """
        print(f"✅ Campagne créée : {nom} dans {emplacement}")
    
    def on_campagne_ouverte(self, chemin: str):
        """
        Appelé quand une campagne est ouverte
        
        Args:
            chemin: Chemin du fichier de campagne
        """
        print(f"✅ Campagne ouverte : {chemin}")
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        # Sauvegarder la campagne courante si nécessaire
        if self.model.campagne_courante:
            self.model.sauvegarder_campagne()
            print("💾 Campagne sauvegardée avant fermeture")
        
        event.accept()


# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE DE L'APPLICATION
# ═══════════════════════════════════════════════════════════════

def main():
    """Lance l'application KOSMOS"""
    print("=" * 60)
    print("🚀 LANCEMENT DE L'APPLICATION KOSMOS")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # Configuration de la police
    font = QFont("Montserrat", 10)
    app.setFont(font)
    
    # Créer et afficher la fenêtre principale
    window = KosmosApplication()
    window.show()
    
    print("\n✅ Application lancée avec succès!")
    print("\n📋 Pages disponibles:")
    print("   1. Accueil - Créer/Ouvrir une campagne")
    print("   2. Importation - Importer les vidéos et métadonnées")
    print("   3. Tri - Trier et organiser les vidéos")
    print("   4. Extraction - [À venir]")
    print("   5. Évènements - [À venir]")
    print("\n" + "=" * 60)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()