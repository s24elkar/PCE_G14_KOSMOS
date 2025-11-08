"""
CONTRÔLEUR - Page de tri KOSMOS
Architecture MVC
"""
import sys
import csv
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TriKosmosController(QObject):
    """Contrôleur pour la page de tri"""
    
    navigation_demandee = pyqtSignal(str)
    video_selectionnee = pyqtSignal(object)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
    
    def obtenir_videos(self):
        """Retourne la liste des vidéos"""
        return self.model.obtenir_videos()
    
    def selectionner_video(self, nom_video: str):
        """Sélectionne une vidéo"""
        video = self.model.selectionner_video(nom_video)
        if video:
            self.video_selectionnee.emit(video)
    
    def renommer_video(self, ancien_nom: str, nouveau_nom: str):
        """Renomme une vidéo"""
        return self.model.renommer_video(ancien_nom, nouveau_nom)
    
    def conserver_video(self, nom_video: str):
        """Marque une vidéo comme conservée"""
        return self.model.conserver_video(nom_video)
    
    def supprimer_video(self, nom_video: str):
        """Marque une vidéo pour suppression"""
        return self.model.marquer_video_pour_suppression(nom_video)
    
    def modifier_metadonnees_communes(self, nom_video: str, metadonnees: dict):
        """Modifie les métadonnées communes"""
        video = self.model.campagne_courante.obtenir_video(nom_video)
        if video:
            for key, value in metadonnees.items():
                if key in video.metadata_communes:
                    video.metadata_communes[key] = value
            return self.sauvegarder_csv(video)
        return False
    
    def modifier_metadonnees_propres(self, nom_video: str, metadonnees: dict):
        """Modifie les métadonnées propres"""
        success = self.model.modifier_metadonnees_propres(nom_video, metadonnees)
        
        if success:
            video = self.model.campagne_courante.obtenir_video(nom_video)
            if video:
                return self.sauvegarder_csv(video)
        
        return success
    
    def sauvegarder_csv(self, video):
        """Sauvegarde les métadonnées dans le fichier CSV"""
        try:
            dossier = Path(video.chemin).parent
            csv_path = dossier / f"{video.dossier_numero}.csv"
            
            if not csv_path.exists():
                print(f"⚠️ CSV non trouvé: {csv_path}")
                return False
            
            # Lire le CSV existant
            lignes = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                
                for row in reader:
                    # Mettre à jour les métadonnées communes
                    for key, value in video.metadata_communes.items():
                        if key in row:
                            row[key] = value
                    
                    # Mettre à jour les métadonnées propres
                    for key, value in video.metadata_propres.items():
                        if key in row:
                            row[key] = value
                    
                    lignes.append(row)
            
            # Réécrire le CSV
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(lignes)
            
            print(f"✅ CSV sauvegardé: {csv_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde CSV: {e}")
            return False