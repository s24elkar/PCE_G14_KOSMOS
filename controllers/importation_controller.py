"""
CONTRÔLEUR - Page d'importation KOSMOS
Architecture MVC

Responsabilités :
- Importation de nouveaux dossiers de vidéos dans une campagne existante
- Validation de la structure des dossiers (sous-dossiers numérotés)
- Gestion des erreurs d'importation
- Navigation automatique vers la page de tri après importation

Le contrôleur fait le pont entre la vue (ImportationView) et le modèle (AppModel)
"""
import sys
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ImportationKosmosController(QObject):
    """
    Contrôleur de la page d'importation.
    Gère l'ajout de nouvelles vidéos à une campagne existante.
    """
    
    # Signaux émis vers l'application principale
    navigation_demandee = pyqtSignal(str)  # Demande de navigation vers une autre page
    importation_terminee = pyqtSignal(dict)  # Résultats de l'importation (nb vidéos, erreurs, etc.)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None

    def set_view(self, view):
        self.view = view
    
    def on_importer_dossier(self, chemin_dossier: str):
        """Importe un dossier de vidéos dans la campagne courante et navigue vers le tri."""
        if not self.view: 
            return

        # Validation du chemin
        if not chemin_dossier or not os.path.isdir(chemin_dossier):
            self.view.show_warning("Erreur", "Veuillez sélectionner un dossier valide.")
            return
        
        # Vérification qu'une campagne est active
        if not self.model.campagne_courante:
            self.view.show_error(
                "Pas de campagne", 
                "Créez d'abord une campagne depuis Fichier > Créer campagne."
            )
            return
        
        print(f"📁 Dossier à importer : {chemin_dossier}")
        
        try:
            # Vérifier la présence de sous-dossiers numérotés (structure KOSMOS attendue)
            contenu = os.listdir(chemin_dossier)
            sous_dossiers = [d for d in contenu if os.path.isdir(os.path.join(chemin_dossier, d))]
            dossiers_numerotes = [d for d in sous_dossiers if d.isdigit()]
            
            if not dossiers_numerotes:
                # Demander confirmation si aucun sous-dossier numéroté trouvé
                confirme = self.view.ask_confirmation(
                    "Confirmation",
                    f"Le dossier '{os.path.basename(chemin_dossier)}' ne contient pas de sous-dossiers numérotés.\n\n"
                    f"Voulez-vous quand même l'importer ?"
                )
                if not confirme:
                    return
            
            print(f"📹 Lancement de l'importation...")
            
            # Importer les vidéos via le modèle
            resultats = self.model.importer_videos_kosmos(chemin_dossier)
            
            # Sauvegarder la campagne avec les nouvelles vidéos
            self.model.sauvegarder_campagne()
            
            # Préparer le rapport d'importation
            nb_importees = len(resultats['videos_importees'])
            nb_sans_meta = len(resultats['videos_sans_metadata'])
            nb_erreurs = len(resultats['erreurs'])
            
            if nb_importees == 0:
                self.view.show_warning(
                    "Aucune vidéo",
                    "Aucune vidéo n'a été trouvée dans ce dossier."
                )
                return
            
            # Afficher le rapport détaillé
            message = f"✅ Importation terminée !\n\n"
            message += f"📹 Vidéos importées : {nb_importees}\n"
            
            if nb_sans_meta > 0:
                message += f"⚠️  Vidéos sans métadonnées : {nb_sans_meta}\n"
            
            if nb_erreurs > 0:
                message += f"\n❌ Erreurs : {nb_erreurs}\n"
            
            self.view.show_info("Importation réussie", message)
            
            # Émettre le signal avec les résultats détaillés
            self.importation_terminee.emit(resultats)
            
            # Naviguer automatiquement vers la page de tri
            print("🔄 Navigation vers la page de tri...")
            self.navigation_demandee.emit('tri')
            
        except Exception as e:
            self.view.show_error(
                "Erreur d'importation",
                f"Une erreur s'est produite lors de l'importation :\n\n{str(e)}"
            )
            print(f"❌ Erreur : {e}")