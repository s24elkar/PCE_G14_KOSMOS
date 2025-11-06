"""
CONTROLLER - Contrôleur pour la page de Tri des vidéos (ADAPTÉ)
Utilise le modèle unique ApplicationModel
Architecture MVC - Couche Contrôleur
"""
from typing import Optional
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from PyQt6.QtCore import QObject, pyqtSignal


class TriController(QObject):
    """
    Contrôleur pour la page de tri
    Utilise directement ApplicationModel (pas de modèle séparé)
    """
    
    # Signaux pour communication avec la vue
    videos_chargees = pyqtSignal(list)  # Liste des vidéos à afficher
    video_selectionnee = pyqtSignal(dict)  # Données de la vidéo sélectionnée
    video_renommee = pyqtSignal(str, str)  # ancien_nom, nouveau_nom
    video_supprimee = pyqtSignal(str)  # nom de la vidéo
    metadonnees_modifiees = pyqtSignal(str, dict)  # nom vidéo, nouvelles métadonnées
    
    def __init__(self, model):
        """
        Args:
            model: Instance de ApplicationModel
        """
        super().__init__()
        self.model = model
        
    def charger_donnees_initiales(self):
        """
        Charge les données initiales depuis le modèle
        et les affiche dans la vue
        """
        if not self.model.campagne_courante:
            print("⚠️ Aucune campagne chargée")
            return
        
        # Émettre le signal pour mettre à jour la vue
        self.videos_chargees.emit(self._formater_videos_pour_vue())
        
        print(f"✅ {len(self.model.campagne_courante.videos)} vidéos chargées dans la page de tri")
    
    def _formater_videos_pour_vue(self):
        """
        Formate les vidéos du modèle pour la vue
        
        Returns:
            Liste de dictionnaires pour l'affichage
        """
        if not self.model.campagne_courante:
            return []
        
        videos = self.model.campagne_courante.videos
        return [
            {
                'nom': v.nom,
                'taille': v.taille,
                'duree': v.duree,
                'date': v.date,
                'est_conservee': v.est_conservee,
                'thumbnail_color': '#00CBA9' if v.est_conservee else '#666666'
            }
            for v in videos
        ]
    
    def on_video_cliquee(self, nom_video: str):
        """
        Gère le clic sur une vidéo dans le tableau ou l'aperçu
        
        Args:
            nom_video: Nom de la vidéo cliquée
        """
        video = self.model.selectionner_video(nom_video)
        
        if video:
            # Formater les données pour la vue
            video_data = {
                'nom': video.nom,
                'taille': video.taille,
                'duree': video.duree,
                'date': video.date,
                'chemin': video.chemin,
                'metadata_communes': video.metadata_communes,
                'metadata_propres': video.metadata_propres
            }
            
            # Émettre le signal
            self.video_selectionnee.emit(video_data)
            print(f"📹 Vidéo sélectionnée: {nom_video}")
    
    def on_renommer_video(self, view_parent=None):
        """
        Gère le renommage d'une vidéo
        
        Args:
            view_parent: Widget parent pour la boîte de dialogue
        """
        if not self.model.video_selectionnee:
            if view_parent:
                QMessageBox.warning(
                    view_parent,
                    "Aucune sélection",
                    "Veuillez sélectionner une vidéo à renommer."
                )
            return
        
        video = self.model.video_selectionnee
        
        # Demander le nouveau nom
        nouveau_nom, ok = QInputDialog.getText(
            view_parent,
            "Renommer la vidéo",
            f"Nouveau nom pour '{video.nom}':",
            text=video.nom
        )
        
        if ok and nouveau_nom and nouveau_nom != video.nom:
            # Vérifier que le nom n'existe pas déjà
            if self.model.campagne_courante:
                for v in self.model.campagne_courante.videos:
                    if v.nom == nouveau_nom:
                        QMessageBox.warning(
                            view_parent,
                            "Nom existant",
                            f"Une vidéo nommée '{nouveau_nom}' existe déjà."
                        )
                        return
            
            # Renommer
            ancien_nom = video.nom
            if self.model.renommer_video(ancien_nom, nouveau_nom):
                # Sauvegarder
                self.model.sauvegarder_campagne()
                
                # Émettre le signal
                self.video_renommee.emit(ancien_nom, nouveau_nom)
                print(f"✅ Vidéo renommée: {ancien_nom} → {nouveau_nom}")
                
                # Recharger la vue
                self.videos_chargees.emit(self._formater_videos_pour_vue())
    
    def on_conserver_video(self, view_parent=None):
        """
        Marque la vidéo sélectionnée comme conservée
        
        Args:
            view_parent: Widget parent pour les messages
        """
        if not self.model.video_selectionnee:
            if view_parent:
                QMessageBox.warning(
                    view_parent,
                    "Aucune sélection",
                    "Veuillez sélectionner une vidéo."
                )
            return
        
        self.model.conserver_video(self.model.video_selectionnee.nom)
        print(f"✅ Vidéo conservée: {self.model.video_selectionnee.nom}")
        
        # Recharger la vue
        self.videos_chargees.emit(self._formater_videos_pour_vue())
    
    def on_supprimer_video(self, view_parent=None):
        """
        Marque la vidéo sélectionnée pour suppression
        
        Args:
            view_parent: Widget parent pour les dialogues
        """
        if not self.model.video_selectionnee:
            if view_parent:
                QMessageBox.warning(
                    view_parent,
                    "Aucune sélection",
                    "Veuillez sélectionner une vidéo à supprimer."
                )
            return
        
        video = self.model.video_selectionnee
        
        # Demander confirmation
        reponse = QMessageBox.question(
            view_parent,
            "Confirmer la suppression",
            f"Voulez-vous marquer '{video.nom}' pour suppression?\n\n"
            "La vidéo sera supprimée définitivement lors de la sauvegarde.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reponse == QMessageBox.StandardButton.Yes:
            self.model.marquer_video_pour_suppression(video.nom)
            print(f"🗑️ Vidéo marquée pour suppression: {video.nom}")
            
            # Émettre le signal
            self.video_supprimee.emit(video.nom)
            
            # Recharger la vue
            self.videos_chargees.emit(self._formater_videos_pour_vue())
    
    def on_modifier_metadonnees(self, nom_video: str, nouvelles_metadonnees: dict):
        """
        Modifie les métadonnées propres d'une vidéo
        
        Args:
            nom_video: Nom de la vidéo
            nouvelles_metadonnees: Dictionnaire avec les nouvelles métadonnées
        """
        success = self.model.modifier_metadonnees_propres(nom_video, nouvelles_metadonnees)
        
        if success:
            # Sauvegarder
            self.model.sauvegarder_campagne()
            
            # Émettre le signal
            self.metadonnees_modifiees.emit(nom_video, nouvelles_metadonnees)
            print(f"✅ Métadonnées modifiées pour: {nom_video}")
            
            # Recharger la vidéo sélectionnée
            self.on_video_cliquee(nom_video)
    
    def on_sauvegarder(self, view_parent=None):
        """
        Sauvegarde les modifications et supprime les vidéos marquées
        
        Args:
            view_parent: Widget parent pour les messages
        """
        if not self.model.campagne_courante:
            return
        
        videos_a_supprimer = self.model.campagne_courante.obtenir_videos_a_supprimer()
        
        if videos_a_supprimer:
            # Demander confirmation finale
            noms = "\n".join([f"- {v.nom}" for v in videos_a_supprimer])
            reponse = QMessageBox.question(
                view_parent,
                "Confirmer la suppression définitive",
                f"Les vidéos suivantes seront supprimées définitivement:\n\n{noms}\n\n"
                "Cette action est irréversible. Continuer?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reponse == QMessageBox.StandardButton.Yes:
                # Supprimer les vidéos marquées
                count = self.model.supprimer_videos_marquees()
                
                # Sauvegarder
                self.model.sauvegarder_campagne()
                
                QMessageBox.information(
                    view_parent,
                    "Sauvegarde réussie",
                    f"{count} vidéo(s) supprimée(s)."
                )
                
                # Recharger la vue
                self.videos_chargees.emit(self._formater_videos_pour_vue())
        else:
            # Juste sauvegarder les modifications
            self.model.sauvegarder_campagne()
            QMessageBox.information(
                view_parent,
                "Sauvegarde réussie",
                "Les modifications ont été sauvegardées."
            )
    
    def obtenir_statistiques(self) -> dict:
        """
        Retourne les statistiques sur les vidéos
        
        Returns:
            Dictionnaire avec les statistiques
        """
        return self.model.obtenir_statistiques()


# Test du contrôleur
if __name__ == '__main__':
    print("🧪 Test du contrôleur de tri adapté...")
    
    # Créer un modèle d'application
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from models.app_model import ApplicationModel, Video
    
    model = ApplicationModel()
    
    # Créer une campagne de test
    campagne = model.creer_campagne("Test", "./test")
    
    # Ajouter une vidéo
    video = Video("Test_Video.mp4", "/test/video.mp4", "1.2 Go", "15:01", "22/09/2025")
    video.metadata_communes = {'system': 'Kstereo', 'camera': 'imx477', 'model': 'Pi 5', 'version': '4.0'}
    video.metadata_propres = {'campaign': 'ATL', 'zone': 'CC', 'zone_dict': ''}
    campagne.ajouter_video(video)
    
    # Créer le contrôleur
    controller = TriController(model)
    
    # Tester la sélection
    controller.on_video_cliquee('Test_Video.mp4')
    
    # Tester les statistiques
    stats = controller.obtenir_statistiques()
    print(f"✅ Statistiques: {stats}")
    
    print("✅ Tests terminés!")