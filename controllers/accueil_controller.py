"""
CONTRÔLEUR - Page d'accueil KOSMOS
Architecture MVC
"""
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AccueilKosmosController(QObject):
    """Contrôleur pour la page d'accueil KOSMOS"""
    
    navigation_demandee = pyqtSignal(str)
    campagne_creee = pyqtSignal(str, str)
    campagne_ouverte = pyqtSignal(str)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None

    def set_view(self, view):
        """Associe la vue au contrôleur"""
        self.view = view
    
    def on_creer_repertoire(self):
        """
        Crée un nouveau répertoire de travail en sélectionnant un dossier de vidéos.
        Importe les vidéos, crée le fichier config et le dossier extraction.
        """
        if not self.view: return

        # Sélectionner le dossier contenant les vidéos via la vue
        dossier_videos = self.view.ask_directory(
            "Créer un répertoire de travail - Sélectionner le dossier contenant les vidéos"
        )
        
        if not dossier_videos:
            return
        
        dossier_path = Path(dossier_videos)
        nom_campagne = dossier_path.name
        
        # Créer la campagne
        campagne = self.model.creer_campagne(nom_campagne, str(dossier_path))
        print(f"✅ Nouveau répertoire de travail créé : {nom_campagne}")
        
        # Importer les vidéos depuis ce dossier
        resultats = self.model.importer_videos_kosmos(str(dossier_path))
        nb_videos = len(resultats['videos_importees'])
        print(f"✅ {nb_videos} vidéo(s) importée(s)")
        
        # Créer le dossier 'extraction' 
        dossier_extraction = dossier_path / "extraction"
        dossier_extraction.mkdir(exist_ok=True)
        campagne.workspace_extraction = str(dossier_extraction)
        print(f"✅ Dossier extraction créé : {dossier_extraction}")
        
        # Sauvegarder la configuration
        self.model.sauvegarder_campagne()
        print(f"✅ Fichier config sauvegardé : {nom_campagne}_config.json")
        
        # Afficher un message de succès via la vue
        self.view.show_info(
            "Répertoire de travail créé",
            f"Répertoire de travail '{nom_campagne}' créé avec succès.\n{nb_videos} vidéo(s) importée(s)."
        )
        
        # Émettre le signal et naviguer vers la page tri
        self.campagne_creee.emit(nom_campagne, str(dossier_path))
        self.navigation_demandee.emit('tri')
    
    def on_ouvrir_repertoire(self):
        """
        Ouvre un répertoire de travail existant en sélectionnant son dossier.
        Cherche le fichier *_config.json pour charger la configuration.
        """
        if not self.view: return

        # Sélectionner le dossier du répertoire de travail via la vue
        dossier_campagne = self.view.ask_directory(
            "Ouvrir un répertoire de travail - Sélectionner le dossier"
        )
        
        if not dossier_campagne:
            return
        
        dossier_path = Path(dossier_campagne)
        
        # Chercher un fichier *_config.json dans le dossier
        config_files = list(dossier_path.glob("*_config.json"))
        
        if not config_files:
            self.view.show_warning(
                "Aucun répertoire de travail trouvé",
                f"Aucun fichier de configuration trouvé dans ce dossier.\n\n"
                f"Utilisez 'Créer un répertoire de travail' pour initialiser un nouveau répertoire."
            )
            return
        
        # Utiliser le premier fichier config trouvé
        chemin_config = config_files[0]
        print(f"ℹ️ Fichier config trouvé : {chemin_config.name}")
        
        # Charger la campagne depuis ce fichier
        if not self.model.ouvrir_campagne(str(chemin_config)):
            self.view.show_error(
                "Erreur",
                "Impossible d'ouvrir le fichier de configuration."
            )
            return
        
        campagne = self.model.campagne_courante
        print(f"✅ Répertoire de travail ouvert : {campagne.nom}")
        
        # Vérifier/créer le dossier extraction s'il n'existe pas
        if not campagne.workspace_extraction:
            dossier_extraction = dossier_path / "extraction"
            dossier_extraction.mkdir(exist_ok=True)
            campagne.workspace_extraction = str(dossier_extraction)
            print(f"✅ Dossier extraction créé : {dossier_extraction}")
        
        # Émettre le signal et naviguer vers la page tri
        self.campagne_ouverte.emit(str(dossier_path))
        self.navigation_demandee.emit('tri')
    
    # Alias pour compatibilité avec l'ancien code
    def on_creer_campagne(self):
        """Alias pour on_creer_repertoire (compatibilité)"""
        return self.on_creer_repertoire()
    
    def on_ouvrir_campagne(self):
        """Alias pour on_ouvrir_repertoire (compatibilité)"""
        return self.on_ouvrir_repertoire()
    
    def on_enregistrer(self):
        """Enregistre la campagne courante"""
        if not self.view: return

        if self.model.campagne_courante:
            if self.model.sauvegarder_campagne():
                self.view.show_info(
                    "Sauvegarde réussie",
                    f"Campagne '{self.model.campagne_courante.nom}' sauvegardée."
                )
            else:
                self.view.show_error("Erreur", "Impossible de sauvegarder.")
        else:
            self.view.show_warning("Aucune campagne", "Aucune campagne ouverte.")
    
    def on_enregistrer_sous(self):
        """Enregistre sous un nouveau nom"""
        if not self.view: return

        if not self.model.campagne_courante:
            self.view.show_warning("Aucune campagne", "Aucune campagne ouverte.")
            return
        
        # Demander à la vue d'ouvrir le dialogue
        dialogue = self.view.open_new_campaign_dialog()
        
        if dialogue:
            # Connecter le signal du dialogue à une fonction locale
            def on_nouvelle_campagne(nom, emplacement):
                self.model.campagne_courante.nom = nom
                self.model.campagne_courante.emplacement = emplacement
                self.model.sauvegarder_campagne()
                self.view.show_info("Succès", "Campagne enregistrée sous un nouveau nom.")
            
            dialogue.campagneCreee.connect(on_nouvelle_campagne)
            dialogue.exec()