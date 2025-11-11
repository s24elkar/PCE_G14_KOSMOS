"""
CONTRÔLEUR - Page de tri KOSMOS
Architecture MVC
Gère la suppression définitive des vidéos
"""
import sys
import csv
import json
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

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
        else:
            try:
                base = Path(str(nom_video)).name
                if base and base != nom_video:
                    video = self.model.selectionner_video(base)
                    if video:
                        self.video_selectionnee.emit(video)
            except Exception:
                pass
    
    def renommer_video(self, ancien_nom: str, nouveau_nom: str):
        """Renomme une vidéo"""
        return self.model.renommer_video(ancien_nom, nouveau_nom)
    
    def conserver_video(self, nom_video: str):
        """Marque une vidéo comme conservée"""
        return self.model.conserver_video(nom_video)
    
    def supprimer_video(self, nom_video: str) -> bool:
        """Supprime définitivement une vidéo (fichier + liste)"""
        try:
            # Récupérer la vidéo
            video = self.model.campagne_courante.obtenir_video(nom_video) if self.model.campagne_courante else None
            
            if not video:
                print(f"❌ Vidéo non trouvée: {nom_video}")
                return False
            
            chemin_fichier = Path(video.chemin)
            
            # 1. Supprimer le fichier physique
            if chemin_fichier.exists():
                try:
                    os.remove(chemin_fichier)
                    print(f"🗑️ Fichier supprimé: {chemin_fichier}")
                except Exception as e:
                    print(f"❌ Erreur suppression fichier: {e}")
                    return False
            else:
                print(f"⚠️ Fichier déjà supprimé ou introuvable: {chemin_fichier}")
            
            # 2. Supprimer de la liste de la campagne
            self.model.campagne_courante.supprimer_video(nom_video)
            print(f"✅ Vidéo retirée de la campagne: {nom_video}")
            
            # 3. Désélectionner si c'était la vidéo sélectionnée
            if self.model.video_selectionnee and self.model.video_selectionnee.nom == nom_video:
                self.model.video_selectionnee = None
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression vidéo: {e}")
            return False
    
    def charger_metadonnees_depuis_json(self, video) -> bool:
        """Charge uniquement les métadonnées propres à la vidéo depuis le fichier JSON existant"""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                print(f"⚠️ Fichier JSON non trouvé: {json_path}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger UNIQUEMENT la section "video" (métadonnées propres)
            video.metadata_propres.clear()
            
            if 'video' in data:
                video_section = data['video']
                
                # Parcourir toutes les sections de métadonnées vidéo
                for section_name, section_data in video_section.items():
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            # Préfixer avec le nom de la section pour éviter les conflits
                            full_key = f"{section_name}_{key}"
                            video.metadata_propres[full_key] = str(value) if value is not None else ""
                    else:
                        video.metadata_propres[section_name] = str(section_data) if section_data is not None else ""
            
            print(f"✅ Métadonnées vidéo chargées depuis JSON pour {video.nom}")
            print(f"   {len(video.metadata_propres)} champs chargés")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture JSON: {e}")
            return False
    
    def charger_metadonnees_communes_depuis_json(self, video) -> bool:
        """Charge les métadonnées communes depuis le fichier JSON (lecture seule)"""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                print(f"⚠️ Fichier JSON non trouvé: {json_path}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Charger les métadonnées communes depuis les sections system et campaign
            video.metadata_communes.clear()
            
            if 'system' in data:
                system = data['system']
                video.metadata_communes['system'] = system.get('system', '')
                video.metadata_communes['camera'] = system.get('camera', '')
                video.metadata_communes['model'] = system.get('model', '')
                video.metadata_communes['version'] = system.get('version', '')
            
            print(f"✅ Métadonnées communes chargées depuis JSON pour {video.nom}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture JSON communes: {e}")
            return False

    def sauvegarder_metadonnees_vers_json(self, video, nom_utilisateur: str = "User") -> bool:
        """Sauvegarde uniquement les métadonnées propres à la vidéo dans le fichier JSON existant"""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                print(f"❌ Fichier JSON non trouvé pour sauvegarde: {json_path}")
                return False
            
            # Charger les données existantes (préserver system et campaign)
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Créer la section video si elle n'existe pas
            if 'video' not in data:
                data['video'] = {}
            
            # Réorganiser les métadonnées propres par section dans la section video
            video_section = data['video']
            
            # Initialiser les sections si elles n'existent pas
            sections = ['analyseDict', 'astroDict', 'ctdDict', 'gpsDict', 'hourDict', 'meteoAirDict', 'meteoMerDict', 'stationDict']
            for section in sections:
                if section not in video_section:
                    video_section[section] = {}
            
            # Distribuer les métadonnées dans les bonnes sections
            for key, value in video.metadata_propres.items():
                if '_' in key:
                    section_name, field_name = key.split('_', 1)
                    if section_name in video_section:
                        # Convertir les valeurs vides en null pour respecter le format JSON
                        if value == "" or value == "None":
                            video_section[section_name][field_name] = None
                        else:
                            # Tenter de convertir les valeurs numériques
                            try:
                                if '.' in value:
                                    video_section[section_name][field_name] = float(value)
                                elif value.isdigit():
                                    video_section[section_name][field_name] = int(value)
                                else:
                                    video_section[section_name][field_name] = value
                            except:
                                video_section[section_name][field_name] = value
                else:
                    # Si pas de préfixe, mettre dans analyseDict par défaut
                    if value == "" or value == "None":
                        video_section['analyseDict'][key] = None
                    else:
                        video_section['analyseDict'][key] = value
            
            # Sauvegarde atomique (préserve le fichier original si erreur)
            from tempfile import NamedTemporaryFile
            tmp = NamedTemporaryFile("w", delete=False, encoding="utf-8")
            try:
                with tmp as tf:
                    json.dump(data, tf, indent=4, ensure_ascii=False)
                Path(tmp.name).replace(json_path)
            finally:
                try:
                    Path(tmp.name).unlink(missing_ok=True)
                except Exception:
                    pass
            
            print(f"✅ Métadonnées vidéo sauvegardées dans: {json_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")
            return False

    def modifier_metadonnees_propres(self, nom_video: str, metadonnees: dict, nom_utilisateur: str = "User"):
        """Modifie uniquement les métadonnées propres à la vidéo (section video du JSON)"""
        video = self.model.campagne_courante.obtenir_video(nom_video) if self.model.campagne_courante else None
        if video:
            # Mettre à jour les métadonnées propres
            for key, value in metadonnees.items():
                video.metadata_propres[key] = value
            
            return self.sauvegarder_metadonnees_vers_json(video, nom_utilisateur)
        return False
    
    def get_video_by_name(self, nom_video: str):
        """Retourne l'objet vidéo via le modèle courant."""
        if not self.model.campagne_courante:
            return None
        return self.model.campagne_courante.obtenir_video(nom_video)

    def get_angle_seek_times(self, nom_video: str):
        """
        Retourne une liste de 6 tuples (start_time_str, duration_sec)
        pour l'extraction des miniatures/GIFs côté vue.
        Par défaut : 1 point toutes les 30s, GIF de 3s.
        """
        seek = []
        for i in range(6):
            t = i * 30
            h = t // 3600
            m = (t % 3600) // 60
            s = t % 60
            seek.append((f"{h:02d}:{m:02d}:{s:02d}", 3))
        return seek

    def show_success_dialog(self, parent_view):
        """Affiche une boîte de dialogue de confirmation après modification des métadonnées"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            parent_view,
            "Succès",
            "Les métadonnées ont été modifiées avec succès !",
        )