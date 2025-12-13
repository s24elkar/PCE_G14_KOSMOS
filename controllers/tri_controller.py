"""
CONTRÔLEUR - Page de tri KOSMOS
Architecture MVC
Gère la suppression définitive des vidéos et la validation des données
"""
import sys
import csv
import json
import os
import re  
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime


try:
    import requests
except ImportError:
    print("ERREUR: La bibliothèque 'requests' est manquante. Veuillez l'installer avec : pip install requests")
    sys.exit(1)


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TriKosmosController(QObject):
    """Contrôleur pour la page de tri"""
    
    navigation_demandee = pyqtSignal(str)
    video_selectionnee = pyqtSignal(object)
    succes_operation = pyqtSignal(str) # Signal pour notifier le succès d'une opération
    erreur_operation = pyqtSignal(str) # Signal pour notifier une erreur
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
    
    
    def obtenir_videos(self):
        """Retourne la liste des vidéos de la campagne courante."""
        return self.model.obtenir_videos()
    
    def selectionner_video(self, nom_video: str):
        """Sélectionne une vidéo par son nom et émet un signal."""
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
        """Renomme une vidéo dans la campagne courante."""
        return self.model.renommer_video(ancien_nom, nouveau_nom)
    
    def conserver_video(self, nom_video: str):
        """Marque une vidéo comme conservée (non supprimée)."""
        return self.model.conserver_video(nom_video)
    
    def supprimer_video(self, nom_video: str) -> bool:
        """Supprime définitivement une vidéo de la campagne courante."""
        return self.model.supprimer_fichier_video(nom_video)

   
    def charger_metadonnees_depuis_json(self, video) -> bool:
        """Charge les métadonnées propres (section 'video' uniquement) depuis le JSON."""
        return video.charger_metadonnees_propres_json()

    
    def charger_metadonnees_communes_depuis_json(self, video) -> bool:
        """Charge les métadonnées communes (sections 'system' et 'campaign') depuis le JSON."""
        return video.charger_metadonnees_communes_json()

    def sauvegarder_metadonnees_vers_json(self, video, nom_utilisateur: str = "User") -> bool:
        """Sauvegarde les métadonnées propres (section video) dans le JSON"""
        return video.sauvegarder_metadonnees_propres_json()

    def modifier_metadonnees_propres(self, nom_video: str, metadonnees: dict, nom_utilisateur: str = "User"):
        """
        Vérifie les types et modifie les métadonnées.
        Retourne un tuple (succès, message_erreur).
        """
        video = self.model.campagne_courante.obtenir_video(nom_video) if self.model.campagne_courante else None
        if not video:
            return False, "Vidéo introuvable."

        # Liste des champs qui doivent être numériques (float ou int)
        numeric_fields = [
            'latitude', 'longitude', 'depth', 'temperature', 'salinity', 'pressure', 
            'seaState', 'swell', 'wind', 'tempAir', 'atmPress', 'coefficient',
            'hour', 'minute', 'second', 'increment'
        ]

        # 1. Validation
        for key, value in metadonnees.items():
            # Obtenir le nom du champ seul (ex: 'gpsDict_latitude' -> 'latitude')
            field_name = key.split('_')[-1]
            
            if field_name in numeric_fields and value and value not in ["", "None", "N/A", "N/A (API)"]:
                # Remplacer la virgule par un point pour la vérification
                val_check = value.replace(',', '.')
                try:
                    float(val_check)
                except ValueError:
                    return False, f"Erreur de type pour le champ '{key}' :\nLa valeur '{value}' n'est pas un nombre valide."

        # 2. Mise à jour (si tout est valide)
        for key, value in metadonnees.items():
            video.metadata_propres[key] = value
        
        if self.sauvegarder_metadonnees_vers_json(video, nom_utilisateur):
            self.succes_operation.emit("Les métadonnées ont été modifiées avec succès !")
            return True, "Sauvegarde réussie."
        else:
            return False, "Erreur lors de l'écriture du fichier JSON."
    

    def modifier_metadonnees_communes(self, nom_video: str, metadonnees: dict, nom_utilisateur: str = "User"):
        """
        Modifie les métadonnées communes (sections 'system' et 'campaign') dans le JSON.
        PROPAGE les modifications à TOUTES les vidéos de la campagne.
        Retourne un tuple (succès, message_erreur).
        """
        if not self.model.campagne_courante:
             return False, "Aucune campagne ouverte."

        # 1. Récupérer la vidéo source pour vérification
        video_source = self.model.campagne_courante.obtenir_video(nom_video)
        if not video_source:
            return False, "Vidéo introuvable."

        succes_global = True
        nb_videos_maj = 0

        # 2. Itérer sur toutes les vidéos de la campagne pour propager les changements
        for video in self.model.campagne_courante.videos:
            # Mise à jour en mémoire
            for key, value in metadonnees.items():
                video.metadata_communes[key] = value
            
            # Sauvegarde dans le JSON individuel
            if not self.sauvegarder_metadonnees_communes_vers_json(video, nom_utilisateur):
                succes_global = False
                print(f"❌ Échec sauvegarde communes pour {video.nom}")
            else:
                nb_videos_maj += 1
        
        if succes_global:
            self.succes_operation.emit(f"Sauvegarde réussie et propagée à {nb_videos_maj} vidéos.")
            return True, f"Sauvegarde réussie et propagée à {nb_videos_maj} vidéos."
        else:
            return False, f"Sauvegarde partielle ({nb_videos_maj} vidéos mises à jour). Vérifiez les logs."


    def sauvegarder_metadonnees_communes_vers_json(self, video, nom_utilisateur: str = "User") -> bool:
        """Sauvegarde les métadonnées communes (sections system et campaign) dans le JSON"""
        return video.sauvegarder_metadonnees_communes_json()
    
    def get_video_by_name(self, nom_video: str):
        """Retourne une vidéo par son nom."""
        if not self.model.campagne_courante: return None
        return self.model.campagne_courante.obtenir_video(nom_video)

    def get_angle_seek_times(self, nom_video: str):
        """Retourne les temps d'angle pour une vidéo donnée."""
        return self.model.get_angle_event_times(nom_video)

    def precalculer_metadonnees_externes(self, nom_video: str) -> bool:
        """Pré-calcul des métadonnées externes (météo, astronomie) et mise à jour du JSON."""
        print(f"🔄 Lancement du pré-calcul pour {nom_video}...")
        if not self.model.campagne_courante: return False
        video = self.model.campagne_courante.obtenir_video(nom_video)
        if not video: return False

        try:
            lat_str = video.metadata_propres.get('gpsDict_latitude', 'N/A')
            lon_str = video.metadata_propres.get('gpsDict_longitude', 'N/A')
            date_str = video.metadata_communes.get('campaign_dateDict_date', 'N/A') 
            
            # Si date pas trouvée dans communes, chercher dans propres (au cas où)
            if date_str == 'N/A':
                 date_str = video.metadata_propres.get('campaign_dateDict_date', 'N/A')

            heure_str = video.metadata_propres.get('hourDict_HMSOS', 'N/A')

            if date_str in ['N/A', '', 'None'] or heure_str in ['N/A', '', 'None']:
                print(f"❌ Données temporelles manquantes.")
                return False
                
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                if lat == 0 or lon == 0: return False
            except: return False
            
            try:
                heure_index = int(heure_str.split(':')[0])
            except: return False

        except Exception as e:
            print(f"❌ Erreur extraction: {e}")
            return False

        data_meteo_trouvee = False
        data_astro_trouvee = False

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            is_future = date_obj > datetime.now().date()
            
            if is_future:
                API_URL = "https://api.open-meteo.com/v1/forecast"
                params = {"latitude": lat, "longitude": lon, "start_date": date_str, "end_date": date_str, "hourly": "temperature_2m,windspeed_10m,wave_height,swell_wave_height", "timezone": "auto"}
            else:
                API_URL = "https://marine-api.open-meteo.com/v1/marine"
                params = {"latitude": lat, "longitude": lon, "start_date": date_str, "end_date": date_str, "hourly": "wave_height,swell_wave_height", "timezone": "auto"}

            response_meteo = requests.get(API_URL, params=params, timeout=10)
            response_meteo.raise_for_status() 
            data_meteo = response_meteo.json()
            hourly_data = data_meteo.get('hourly', {})

            if is_future and 'temperature_2m' in hourly_data and hourly_data['temperature_2m'][heure_index] is not None:
                video.metadata_propres['meteoAirDict_tempAir'] = str(hourly_data['temperature_2m'][heure_index])
                video.metadata_propres['meteoAirDict_wind'] = str(round(hourly_data['windspeed_10m'][heure_index], 1))
                data_meteo_trouvee = True
            elif not is_future:
                API_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
                params_archive = {"latitude": lat, "longitude": lon, "start_date": date_str, "end_date": date_str, "hourly": "temperature_2m,windspeed_10m", "timezone": "auto"}
                resp_archive = requests.get(API_ARCHIVE_URL, params=params_archive, timeout=10)
                d_arch = resp_archive.json()
                if 'hourly' in d_arch and d_arch['hourly']['temperature_2m'][heure_index] is not None:
                     video.metadata_propres['meteoAirDict_tempAir'] = str(d_arch['hourly']['temperature_2m'][heure_index])
                     video.metadata_propres['meteoAirDict_wind'] = str(round(d_arch['hourly']['windspeed_10m'][heure_index], 1))
                     data_meteo_trouvee = True

            if 'wave_height' in hourly_data and hourly_data['wave_height'][heure_index] is not None:
                video.metadata_propres['meteoMerDict_seaState'] = str(round(hourly_data['wave_height'][heure_index], 1))
                video.metadata_propres['meteoMerDict_swell'] = str(round(hourly_data['swell_wave_height'][heure_index], 1))
                data_meteo_trouvee = True

        except Exception as e:
            print(f"❌ Erreur Météo: {e}")

        try:
            WTTR_URL = f"https://wttr.in/{lat},{lon}?format=j1&date={date_str}&lang=fr"
            response_astro = requests.get(WTTR_URL, timeout=20) 
            response_astro.raise_for_status()
            moon_phase = response_astro.json().get('weather', [{}])[0].get('astronomy', [{}])[0].get('moon_phase')
            if moon_phase:
                video.metadata_propres['astroDict_moon'] = moon_phase
                data_astro_trouvee = True
        except Exception as e:
            print(f"❌ Erreur Astro: {e}")

        if data_meteo_trouvee or data_astro_trouvee:
            return self.sauvegarder_metadonnees_vers_json(video)
        return False
    
    def show_success_dialog(self, parent_view):
        # Cette méthode ne devrait pas être ici, mais pour l'instant on la garde pour compatibilité
        # Idéalement, le contrôleur devrait émettre un signal et la vue afficherait le dialogue
        pass