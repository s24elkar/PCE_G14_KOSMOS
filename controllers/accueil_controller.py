"""
CONTRÔLEUR - Page d'accueil KOSMOS
Architecture MVC

Responsabilités :
- Création d'un nouveau répertoire de travail (campagne)
- Ouverture d'un répertoire existant
- Navigation vers les autres pages de l'application
- Gestion des dialogues de sélection de dossiers

Le contrôleur fait le pont entre la vue (AccueilView) et le modèle (AppModel)
"""
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AccueilKosmosController(QObject):
    """
    Contrôleur de la page d'accueil.
    Gère la création et l'ouverture des campagnes (répertoires de travail).
    """
    
    # Signaux émis vers l'application principale
    navigation_demandee = pyqtSignal(str)  # Demande de navigation vers une autre page
    campagne_creee = pyqtSignal(str, str)  # Nouvelle campagne créée (nom, chemin)
    campagne_ouverte = pyqtSignal(str)  # Campagne existante ouverte (chemin)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None

    def set_view(self, view):
        self.view = view
    
    def on_creer_repertoire(self):
        """Crée un nouveau répertoire de travail à partir d'un dossier de vidéos."""
        if not self.view: 
            return

        # Demander à l'utilisateur de sélectionner le dossier contenant les vidéos
        dossier_videos = self.view.ask_directory(
            "Créer un répertoire de travail - Sélectionner le dossier contenant les vidéos"
        )
        
        if not dossier_videos:
            return
        
        dossier_path = Path(dossier_videos)
        nom_campagne = dossier_path.name
        
        # Créer la campagne dans le modèle
        campagne = self.model.creer_campagne(nom_campagne, str(dossier_path))
        print(f"✅ Nouveau répertoire de travail créé : {nom_campagne}")
        
        # Importer toutes les vidéos du dossier sélectionné
        resultats = self.model.importer_videos_kosmos(str(dossier_path))
        nb_videos = len(resultats['videos_importees'])
        print(f"✅ {nb_videos} vidéo(s) importée(s)")
        
        # Créer le sous-dossier 'extraction' pour les captures d'écran et vidéos extraites
        dossier_extraction = dossier_path / "extraction"
        dossier_extraction.mkdir(exist_ok=True)
        campagne.workspace_extraction = str(dossier_extraction)
        print(f"✅ Dossier extraction créé : {dossier_extraction}")
        
        # Sauvegarder la configuration dans un fichier JSON
        self.model.sauvegarder_campagne()
        print(f"✅ Fichier config sauvegardé : {nom_campagne}_config.json")
        
        # Informer l'utilisateur du succès de l'opération
        self.view.show_info(
            "Répertoire de travail créé",
            f"Répertoire de travail '{nom_campagne}' créé avec succès.\n{nb_videos} vidéo(s) importée(s)."
        )
        
        # Émettre les signaux et naviguer vers la page de tri
        self.campagne_creee.emit(nom_campagne, str(dossier_path))
        self.navigation_demandee.emit('tri')
    
    def on_ouvrir_repertoire(self):
        """Ouvre un répertoire de travail existant depuis son fichier *_config.json."""
        if not self.view: 
            return

        # Demander à l'utilisateur de sélectionner le dossier de la campagne
        dossier_campagne = self.view.ask_directory(
            "Ouvrir un répertoire de travail - Sélectionner le dossier"
        )
        
        if not dossier_campagne:
            return
        
        dossier_path = Path(dossier_campagne)
        
        # Rechercher un fichier de configuration dans le dossier
        config_files = list(dossier_path.glob("*_config.json"))
        
        if not config_files:
            self.view.show_warning(
                "Aucun répertoire de travail trouvé",
                f"Aucun fichier de configuration trouvé dans ce dossier.\n\n"
                f"Utilisez 'Créer un répertoire de travail' pour initialiser un nouveau répertoire."
            )
            return
        
        # Charger le premier fichier de configuration trouvé
        chemin_config = config_files[0]
        print(f"ℹ️ Fichier config trouvé : {chemin_config.name}")
        
        # Charger la campagne depuis le fichier JSON
        if not self.model.ouvrir_campagne(str(chemin_config)):
            self.view.show_error(
                "Erreur",
                "Impossible d'ouvrir le fichier de configuration."
            )
            return
        
        campagne = self.model.campagne_courante
        print(f"✅ Répertoire de travail ouvert : {campagne.nom}")
        
        # Vérifier que le dossier extraction existe, sinon le créer
        if not campagne.workspace_extraction:
            dossier_extraction = dossier_path / "extraction"
            dossier_extraction.mkdir(exist_ok=True)
            campagne.workspace_extraction = str(dossier_extraction)
            print(f"✅ Dossier extraction créé : {dossier_extraction}")
        
        # Émettre les signaux et naviguer vers la page de tri
        self.campagne_ouverte.emit(str(dossier_path))
        self.navigation_demandee.emit('tri')
    
    # Alias pour compatibilité avec l'ancien code
    def on_creer_campagne(self):
        """Alias vers on_creer_repertoire() pour compatibilité."""
        return self.on_creer_repertoire()
    
    def on_ouvrir_campagne(self):
        """Alias vers on_ouvrir_repertoire() pour compatibilité."""
        return self.on_ouvrir_repertoire()
    
    def on_enregistrer(self):
        """Sauvegarde la campagne courante."""
        if not self.view: 
            return

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
        """Sauvegarde la campagne sous un nouveau nom."""
        if not self.view: 
            return

        if not self.model.campagne_courante:
            self.view.show_warning("Aucune campagne", "Aucune campagne ouverte.")
            return
        
        # Ouvrir le dialogue de création avec le nom actuel pré-rempli
        dialogue = self.view.open_new_campaign_dialog()
        
        if dialogue:
            def on_nouvelle_campagne(nom, emplacement):
                """Callback appelé lors de la validation du dialogue."""
                self.model.campagne_courante.nom = nom
                self.model.campagne_courante.emplacement = emplacement
                self.model.sauvegarder_campagne()
                self.view.show_info("Succès", "Campagne enregistrée sous un nouveau nom.")
            
            dialogue.campagneCreee.connect(on_nouvelle_campagne)
            dialogue.exec()