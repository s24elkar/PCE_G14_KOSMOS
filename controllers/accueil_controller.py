"""
CONTRÔLEUR - Page d'accueil KOSMOS
Architecture MVC

Rôle du contrôleur :
    - Reçoit les actions de l'utilisateur depuis la vue (AccueilView)
    - Interagit avec le modèle (ApplicationModel) pour manipuler les données
    - Met à jour la vue en fonction des résultats
    - Émet des signaux pour coordonner la navigation entre les pages

Ce contrôleur gère spécifiquement :
    - La création de nouvelles campagnes
    - L'ouverture de campagnes existantes
    - L'importation automatique des vidéos KOSMOS
"""
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal


class AccueilKosmosController(QObject):
    """
    Contrôleur pour la page d'accueil KOSMOS.
    
    Responsabilités :
        - Orchestrer la création et l'ouverture des campagnes
        - Détecter automatiquement si une campagne existe déjà
        - Déclencher l'importation des vidéos si nécessaire
        - Coordonner la navigation vers les autres pages
    
    Signaux émis :
        - navigation_demandee : Demande de changement de page (str: nom_page)
        - campagne_creee : Nouvelle campagne créée (str: nom, str: emplacement)
        - campagne_ouverte : Campagne existante ouverte (str: emplacement)
        - importation_terminee : Import vidéos terminé (dict: résultats)
    """
    
    # Signaux pour la communication avec l'application principale
    navigation_demandee = pyqtSignal(str)      # Changement de page demandé
    campagne_creee = pyqtSignal(str, str)      # Nouvelle campagne créée
    campagne_ouverte = pyqtSignal(str)         # Campagne existante ouverte
    importation_terminee = pyqtSignal(dict)    # Résultats de l'import vidéos
    
    def __init__(self, model, parent=None):
        """
        Initialise le contrôleur.
        
        Args:
            model (ApplicationModel): Référence au modèle de données global
            parent (QObject, optional): Parent Qt pour la hiérarchie d'objets
        """
        super().__init__(parent)
        self.model = model  # Référence au modèle de données
        self.view = None    # Sera défini par set_view()

    def set_view(self, view):
        """
        Associe une vue à ce contrôleur.
        
        Pattern MVC : La vue et le contrôleur se connaissent mutuellement
        pour permettre la communication bidirectionnelle.
        
        Args:
            view (AccueilView): La vue à associer à ce contrôleur
        """
        self.view = view
    
    def on_ouvrir_campagne(self):
        """
        Gère l'ouverture d'une campagne de manière intelligente.
        
        Cette méthode analyse le dossier sélectionné et décide automatiquement :
            - Si c'est une campagne existante (fichier *_config.json présent)
              -> Charge la campagne et navigue vers la page Tri
            
            - Si c'est une nouvelle campagne (pas de fichier config)
              -> Crée la campagne, importe les vidéos, sauvegarde, puis navigue
        
        Flux d'exécution :
            1. L'utilisateur sélectionne un dossier via dialogue
            2. Recherche d'un fichier *_config.json dans ce dossier
            3. Branchement selon le cas (existante ou nouvelle)
            4. Navigation automatique vers la page Tri
        
        Note technique :
            Cette approche simplifie l'UX en évitant à l'utilisateur
            de choisir entre "Créer" et "Ouvrir" - le système détecte automatiquement.
        """
        # Vérification de sécurité : la vue doit être définie
        if not self.view:
            return

        # Étape 1 : Demander à l'utilisateur de sélectionner un dossier
        # La vue gère l'affichage du dialogue système (séparation MVC)
        dossier_campagne = self.view.ask_directory(
            "Ouvrir une campagne - Sélectionner le dossier"
        )
        
        # L'utilisateur a annulé la sélection
        if not dossier_campagne:
            return
        
        # Conversion en objet Path pour manipulation plus facile
        dossier_path = Path(dossier_campagne)
        nom_campagne = dossier_path.name  # Nom du dossier = nom de la campagne
        
        # Étape 2 : Détecter si c'est une campagne existante
        # Recherche de fichiers *_config.json (ex: "MaCampagne_config.json")
        config_files = list(dossier_path.glob("*_config.json"))
        
        # ========================================================================
        # CAS 1 : CAMPAGNE EXISTANTE (fichier config détecté)
        # ========================================================================
        if config_files:
            print(f"Campagne existante détectée : {config_files[0].name}")
            
            # Charger la campagne depuis le fichier JSON via le modèle
            # Le modèle gère la désérialisation JSON -> objets Python
            if not self.model.ouvrir_campagne(str(config_files[0])):
                # Échec du chargement : afficher une erreur via la vue
                self.view.show_error(
                    "Erreur",
                    "Impossible d'ouvrir le fichier de configuration."
                )
                return
            
            # Récupération de la campagne chargée depuis le modèle
            campagne = self.model.campagne_courante
            print(f"Campagne ouverte : {campagne.nom}")
            
            # Vérification/Création du dossier 'extraction' si absent
            # (peut arriver si créé avec une version antérieure)
            if not campagne.workspace_extraction:
                dossier_extraction = dossier_path / "extraction"
                dossier_extraction.mkdir(exist_ok=True)
                campagne.workspace_extraction = str(dossier_extraction)
                print(f"Dossier extraction créé : {dossier_extraction}")
            
            # Communication avec l'application principale via signaux Qt
            self.campagne_ouverte.emit(str(dossier_path))
            
            # Navigation automatique vers la page Tri
            self.navigation_demandee.emit('tri')
        
        # ========================================================================
        # CAS 2 : NOUVELLE CAMPAGNE (pas de fichier config)
        # ========================================================================
        else:
            print(f"Nouvelle campagne détectée, importation des vidéos...")
            
            # Validation : Vérifier la présence de sous-dossiers numérotés
            # Structure KOSMOS attendue : 0001/, 0002/, 0003/, etc.
            try:
                contenu = os.listdir(dossier_campagne)
                sous_dossiers = [
                    d for d in contenu 
                    if os.path.isdir(os.path.join(dossier_campagne, d))
                ]
                dossiers_numerotes = [d for d in sous_dossiers if d.isdigit()]
                
                # Avertissement si aucun dossier numéroté trouvé
                if not dossiers_numerotes:
                    confirme = self.view.ask_confirmation(
                        "Confirmation",
                        f"Le dossier '{nom_campagne}' ne contient pas de sous-dossiers numérotés.\n\n"
                        f"Voulez-vous quand même créer une campagne avec ce dossier ?"
                    )
                    if not confirme:
                        return  # L'utilisateur annule
                        
            except Exception as e:
                # Erreur système (permissions, disque, etc.)
                self.view.show_error(
                    "Erreur",
                    f"Impossible de lire le contenu du dossier :\n{str(e)}"
                )
                return
            
            # Création de la nouvelle campagne via le modèle
            # Le modèle initialise l'objet Campagne avec ses attributs par défaut
            campagne = self.model.creer_campagne(nom_campagne, str(dossier_path))
            print(f"Nouvelle campagne créée : {nom_campagne}")
            
            # Importation des vidéos depuis la structure KOSMOS
            # Le modèle parcourt les dossiers numérotés et charge les métadonnées
            print(f"Importation des vidéos...")
            resultats = self.model.importer_videos_kosmos(str(dossier_path))
            
            # Extraction des statistiques d'import pour affichage
            nb_videos = len(resultats['videos_importees'])
            nb_sans_meta = len(resultats['videos_sans_metadata'])
            nb_erreurs = len(resultats['erreurs'])
            
            print(f"{nb_videos} vidéo(s) importée(s)")
            
            # Création du dossier 'extraction' pour les exports futurs
            # Structure : /campagne/extraction/captures/, /recordings/, /shorts/
            dossier_extraction = dossier_path / "extraction"
            dossier_extraction.mkdir(exist_ok=True)
            campagne.workspace_extraction = str(dossier_extraction)
            print(f"Dossier extraction créé : {dossier_extraction}")
            
            # Sauvegarde de la configuration en JSON
            # Crée le fichier NomCampagne_config.json dans le dossier
            self.model.sauvegarder_campagne()
            print(f"Fichier config sauvegardé : {nom_campagne}_config.json")
            
            # Gestion du cas où aucune vidéo n'a été trouvée
            if nb_videos == 0:
                self.view.show_warning(
                    "Aucune vidéo",
                    "Aucune vidéo n'a été trouvée dans ce dossier."
                )
                return  # Arrêt du processus
            
            # Construction du message de succès avec statistiques
            message = f"Campagne créée et vidéos importées !\n\n"
            message += f"Vidéos importées : {nb_videos}\n"
            
            # Ajout d'avertissements si nécessaire
            if nb_sans_meta > 0:
                message += f"Vidéos sans métadonnées : {nb_sans_meta}\n"
            
            if nb_erreurs > 0:
                message += f"\nErreurs : {nb_erreurs}\n"
            
            # Affichage du message de succès via la vue
            self.view.show_info("Importation réussie", message)
            
            # Communication avec l'application via signaux
            self.campagne_creee.emit(nom_campagne, str(dossier_path))
            self.importation_terminee.emit(resultats)
            
            # Navigation automatique vers la page Tri
            print("Navigation vers la page de tri...")
            self.navigation_demandee.emit('tri')