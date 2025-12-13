"""
CONTRÔLEUR - Page d'accueil KOSMOS
Architecture MVC
"""
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal


class AccueilKosmosController(QObject):
    """Contrôleur pour la page d'accueil KOSMOS"""
    
    navigation_demandee = pyqtSignal(str)
    campagne_creee = pyqtSignal(str, str)
    campagne_ouverte = pyqtSignal(str)
    importation_terminee = pyqtSignal(dict)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None

    def set_view(self, view):
        """Associe la vue au contrôleur"""
        self.view = view
    
    def on_ouvrir_campagne(self):
        """
        Ouvre une campagne existante ou importe les vidéos si c'est la première fois.
        Fonction intelligente qui détecte automatiquement l'état de la campagne.
        """
        if not self.view: return

        # Sélectionner le dossier de la campagne
        dossier_campagne = self.view.ask_directory(
            "Ouvrir une campagne - Sélectionner le dossier"
        )
        
        if not dossier_campagne:
            return
        
        dossier_path = Path(dossier_campagne)
        nom_campagne = dossier_path.name
        
        # Chercher un fichier *_config.json dans le dossier
        config_files = list(dossier_path.glob("*_config.json"))
        
        # CAS 1 : Campagne déjà existante (fichier config trouvé)
        if config_files:
            print(f"ℹ️ Campagne existante détectée : {config_files[0].name}")
            
            # Charger la campagne depuis le fichier config
            if not self.model.ouvrir_campagne(str(config_files[0])):
                self.view.show_error(
                    "Erreur",
                    "Impossible d'ouvrir le fichier de configuration."
                )
                return
            
            campagne = self.model.campagne_courante
            print(f"✅ Campagne ouverte : {campagne.nom}")
            
            # Vérifier/créer le dossier extraction s'il n'existe pas
            if not campagne.workspace_extraction:
                dossier_extraction = dossier_path / "extraction"
                dossier_extraction.mkdir(exist_ok=True)
                campagne.workspace_extraction = str(dossier_extraction)
                print(f"✅ Dossier extraction créé : {dossier_extraction}")
            
            # Émettre le signal et naviguer vers la page tri
            self.campagne_ouverte.emit(str(dossier_path))
            self.navigation_demandee.emit('tri')
        
        # CAS 2 : Première ouverture (pas de fichier config)
        else:
            print(f"ℹ️ Nouvelle campagne détectée, importation des vidéos...")
            
            # Vérifier qu'il y a des sous-dossiers numérotés
            try:
                contenu = os.listdir(dossier_campagne)
                sous_dossiers = [d for d in contenu if os.path.isdir(os.path.join(dossier_campagne, d))]
                dossiers_numerotes = [d for d in sous_dossiers if d.isdigit()]
                
                if not dossiers_numerotes:
                    confirme = self.view.ask_confirmation(
                        "Confirmation",
                        f"Le dossier '{nom_campagne}' ne contient pas de sous-dossiers numérotés.\n\n"
                        f"Voulez-vous quand même créer une campagne avec ce dossier ?"
                    )
                    if not confirme:
                        return
            except Exception as e:
                self.view.show_error(
                    "Erreur",
                    f"Impossible de lire le contenu du dossier :\n{str(e)}"
                )
                return
            
            # Créer la campagne
            campagne = self.model.creer_campagne(nom_campagne, str(dossier_path))
            print(f"✅ Nouvelle campagne créée : {nom_campagne}")
            
            # Importer les vidéos depuis ce dossier
            print(f"📹 Importation des vidéos...")
            resultats = self.model.importer_videos_kosmos(str(dossier_path))
            nb_videos = len(resultats['videos_importees'])
            nb_sans_meta = len(resultats['videos_sans_metadata'])
            nb_erreurs = len(resultats['erreurs'])
            
            print(f"✅ {nb_videos} vidéo(s) importée(s)")
            
            # Créer le dossier 'extraction' 
            dossier_extraction = dossier_path / "extraction"
            dossier_extraction.mkdir(exist_ok=True)
            campagne.workspace_extraction = str(dossier_extraction)
            print(f"✅ Dossier extraction créé : {dossier_extraction}")
            
            # Sauvegarder la configuration
            self.model.sauvegarder_campagne()
            print(f"✅ Fichier config sauvegardé : {nom_campagne}_config.json")
            
            # Afficher un message de succès
            if nb_videos == 0:
                self.view.show_warning(
                    "Aucune vidéo",
                    "Aucune vidéo n'a été trouvée dans ce dossier."
                )
                return
            
            message = f"✅ Campagne créée et vidéos importées !\n\n"
            message += f"📹 Vidéos importées : {nb_videos}\n"
            
            if nb_sans_meta > 0:
                message += f"⚠️  Vidéos sans métadonnées : {nb_sans_meta}\n"
            
            if nb_erreurs > 0:
                message += f"\n❌ Erreurs : {nb_erreurs}\n"
            
            self.view.show_info("Importation réussie", message)
            
            # Émettre les signaux
            self.campagne_creee.emit(nom_campagne, str(dossier_path))
            self.importation_terminee.emit(resultats)
            
            # Naviguer vers la page tri
            print("🔄 Navigation vers la page de tri...")
            self.navigation_demandee.emit('tri')
