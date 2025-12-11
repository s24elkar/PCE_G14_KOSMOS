"""
CONTRÔLEUR - Page d'importation KOSMOS
Architecture MVC
"""
import sys
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ImportationKosmosController(QObject):
    """Contrôleur pour la page d'importation"""
    
    navigation_demandee = pyqtSignal(str)
    importation_terminee = pyqtSignal(dict)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None

    def set_view(self, view):
        """Associe la vue au contrôleur"""
        self.view = view
    
    def on_importer_dossier(self, chemin_dossier: str):
        """Importe le dossier sélectionné"""
        if not self.view: return

        if not chemin_dossier or not os.path.isdir(chemin_dossier):
            self.view.show_warning("Erreur", "Veuillez sélectionner un dossier valide.")
            return
        
        if not self.model.campagne_courante:
            self.view.show_error("Pas de campagne", "Créez d'abord une campagne depuis Fichier > Créer campagne.")
            return
        
        print(f"📁 Dossier à importer : {chemin_dossier}")
        
        try:
            contenu = os.listdir(chemin_dossier)
            sous_dossiers = [d for d in contenu if os.path.isdir(os.path.join(chemin_dossier, d))]
            dossiers_numerotes = [d for d in sous_dossiers if d.isdigit()]
            
            if not dossiers_numerotes:
                confirme = self.view.ask_confirmation(
                    "Confirmation",
                    f"Le dossier '{os.path.basename(chemin_dossier)}' ne contient pas de sous-dossiers numérotés.\n\nVoulez-vous quand même l'importer ?"
                )
                if not confirme:
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
                self.view.show_warning(
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
            
            self.view.show_info("Importation réussie", message)
            
            # Émettre le signal
            self.importation_terminee.emit(resultats)
            
            # Naviguer vers tri
            print("🔄 Navigation vers la page de tri...")
            self.navigation_demandee.emit('tri')
            
        except Exception as e:
            self.view.show_error(
                "Erreur d'importation",
                f"Une erreur s'est produite lors de l'importation :\n\n{str(e)}"
            )
            print(f"❌ Erreur : {e}")