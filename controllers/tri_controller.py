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
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
    
    
    def obtenir_videos(self):
        return self.model.obtenir_videos()
    
    def selectionner_video(self, nom_video: str):
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
        return self.model.renommer_video(ancien_nom, nouveau_nom)
    
    def conserver_video(self, nom_video: str):
        return self.model.conserver_video(nom_video)
    
    def supprimer_video(self, nom_video: str) -> bool:
        try:
            video = self.model.campagne_courante.obtenir_video(nom_video) if self.model.campagne_courante else None
            if not video: return False
            chemin_fichier = Path(video.chemin)
            if chemin_fichier.exists():
                try:
                    os.remove(chemin_fichier)
                except Exception as e:
                    print(f"❌ Erreur suppression fichier: {e}")
                    return False
            self.model.campagne_courante.supprimer_video(nom_video)
            if self.model.video_selectionnee and self.model.video_selectionnee.nom == nom_video:
                self.model.video_selectionnee = None
            return True
        except Exception as e:
            print(f"❌ Erreur suppression vidéo: {e}")
            return False

   
    def charger_metadonnees_depuis_json(self, video) -> bool:
        """Charge les métadonnées propres (section 'video' uniquement) depuis le JSON."""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video.metadata_propres.clear()
            
            def flatten_dict(section_data, prefix=''):
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        flatten_dict(value, prefix=f"{prefix}{key}_")
                    else:
                        full_key = f"{prefix}{key}"
                        video.metadata_propres[full_key] = str(value) if value is not None else ""

            # Charger uniquement la section "video" ici (les autres vont dans 'communes')
            if 'video' in data:
                flatten_dict(data['video'])
            
            print(f"✅ Métadonnées propres (video) chargées: {len(video.metadata_propres)} champs")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture JSON propres: {e}")
            return False

    
    def charger_metadonnees_communes_depuis_json(self, video) -> bool:
        """Charge les métadonnées communes (sections 'system' et 'campaign') depuis le JSON."""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video.metadata_communes.clear()
            
            def flatten_dict(section_data, prefix=''):
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        flatten_dict(value, prefix=f"{prefix}{key}_")
                    else:
                        full_key = f"{prefix}{key}"
                        video.metadata_communes[full_key] = str(value) if value is not None else ""

            # 1. Charger System
            if 'system' in data:
                flatten_dict(data['system'], prefix="system_")
            
            # 2. Charger Campaign
            if 'campaign' in data:
                flatten_dict(data['campaign'], prefix="campaign_")

            print(f"✅ Métadonnées communes (system+campaign) chargées: {len(video.metadata_communes)} champs")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lecture JSON communes: {e}")
            return False

    def sauvegarder_metadonnees_vers_json(self, video, nom_utilisateur: str = "User") -> bool:
        """Sauvegarde les métadonnées propres (section video) dans le JSON"""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'video' not in data:
                data['video'] = {}
            
            video_section = data['video']
            
            # Initialiser les sous-sections si besoin
            sections = ['analyseDict', 'astroDict', 'ctdDict', 'gpsDict', 'hourDict', 'meteoAirDict', 'meteoMerDict', 'stationDict']
            for section in sections:
                if section not in video_section:
                    video_section[section] = {}
            
            for key, value in video.metadata_propres.items():
                if '_' in key:
                    section_name, field_name = key.split('_', 1)
                    if section_name in video_section:
                        if value == "" or value == "None":
                            video_section[section_name][field_name] = None
                        else:
                            # Tentative de conversion de type basique pour le JSON
                            try:
                                val_test = float(value)
                                if val_test.is_integer():
                                    video_section[section_name][field_name] = int(val_test)
                                else:
                                    video_section[section_name][field_name] = val_test
                            except ValueError:
                                video_section[section_name][field_name] = value
                            except Exception:
                                video_section[section_name][field_name] = value
            
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
            
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")
            return False

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
            return True, "Sauvegarde réussie."
        else:
            return False, "Erreur lors de l'écriture du fichier JSON."
    

    def modifier_metadonnees_communes(self, nom_video: str, metadonnees: dict, nom_utilisateur: str = "User"):
        """
        Modifie les métadonnées communes (sections 'system' et 'campaign') dans le JSON.
        Retourne un tuple (succès, message_erreur).
        """
        video = self.model.campagne_courante.obtenir_video(nom_video) if self.model.campagne_courante else None
        if not video:
            return False, "Vidéo introuvable."

        # Mise à jour en mémoire
        for key, value in metadonnees.items():
            video.metadata_communes[key] = value
        
        # Sauvegarde dans le JSON
        if self.sauvegarder_metadonnees_communes_vers_json(video, nom_utilisateur):
            return True, "Sauvegarde réussie."
        else:
            return False, "Erreur lors de l'écriture du fichier JSON."


    def sauvegarder_metadonnees_communes_vers_json(self, video, nom_utilisateur: str = "User") -> bool:
        """Sauvegarde les métadonnées communes (sections system et campaign) dans le JSON"""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Initialiser les sections si besoin
            if 'system' not in data:
                data['system'] = {}
            if 'campaign' not in data:
                data['campaign'] = {}
            
            # Fonction pour reconstruire la structure imbriquée
            def set_nested_value(d, key_path, value):
                """
                Définit une valeur dans un dictionnaire imbriqué.
                key_path format: "section_subsection_field" ou "section_field"
                """
                parts = key_path.split('_')
                section = parts[0]  # 'system' ou 'campaign'
                
                if section not in d:
                    d[section] = {}
                
                current = d[section]
                for part in parts[1:-1]:  # Naviguer dans les sous-sections
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Définir la valeur finale
                field_name = parts[-1]
                if value == "" or value == "None":
                    current[field_name] = None
                else:
                    current[field_name] = value
            
            # Appliquer toutes les modifications
            for key, value in video.metadata_communes.items():
                set_nested_value(data, key, value)
            
            # Sauvegarde atomique
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
            
            print(f"✅ Métadonnées communes sauvegardées dans: {json_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde communes JSON: {e}")
            return False
    
    def get_video_by_name(self, nom_video: str):
        if not self.model.campagne_courante: return None
        return self.model.campagne_courante.obtenir_video(nom_video)

    def get_angle_seek_times(self, nom_video: str):
        return self.model.get_angle_event_times(nom_video)

    def precalculer_metadonnees_externes(self, nom_video: str) -> bool:
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
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(parent_view, "Succès", "Les métadonnées ont été modifiées avec succès !")