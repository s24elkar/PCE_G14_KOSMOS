"""
CONTRÔLEUR - Page de tri KOSMOS
Architecture MVC
Gère la suppression définitive des vidéos
"""
import sys
import csv
import json
import os
import re  
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

# --- AJOUT NÉCESSAIRE ---
try:
    import requests
except ImportError:
    print("ERREUR: La bibliothèque 'requests' est manquante. Veuillez l'installer avec : pip install requests")
    sys.exit(1)
# --- FIN AJOUT ---

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
        """Charge les métadonnées propres (sections 'video' et 'campaign') depuis le JSON."""
        try:
            dossier = Path(video.chemin).parent
            dossier_numero = getattr(video, "dossier_numero", None) or dossier.name
            json_path = dossier / f"{dossier_numero}.json"
            
            if not json_path.exists():
                print(f"⚠️ Fichier JSON non trouvé: {json_path}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video.metadata_propres.clear()
            
            # Fonction interne pour aplatir les dictionnaires
            def flatten_dict(section_data, prefix=''):
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        flatten_dict(value, prefix=f"{prefix}{key}_")
                    else:
                        full_key = f"{prefix}{key}"
                        video.metadata_propres[full_key] = str(value) if value is not None else ""

            # Charger la section "video"
            if 'video' in data:
                flatten_dict(data['video'])

            # Charger la section "campaign"
            if 'campaign' in data:
                flatten_dict(data['campaign'], prefix="campaign_") # Préfixe pour éviter les conflits
            
            print(f"✅ Métadonnées (vidéo + campagne) chargées depuis JSON pour {video.nom}")
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
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'video' not in data:
                data['video'] = {}
            
            video_section = data['video']
            
            sections = ['analyseDict', 'astroDict', 'ctdDict', 'gpsDict', 'hourDict', 'meteoAirDict', 'meteoMerDict', 'stationDict']
            for section in sections:
                if section not in video_section:
                    video_section[section] = {}
            
            for key, value in video.metadata_propres.items():
                if '_' in key:
                    if key.startswith('campaign_'):
                        continue
                        
                    section_name, field_name = key.split('_', 1)
                    if section_name in video_section:
                        if value == "" or value == "None":
                            video_section[section_name][field_name] = None
                        else:
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
            
            print(f"✅ Métadonnées vidéo sauvegardées dans: {json_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")
            return False

    def modifier_metadonnees_propres(self, nom_video: str, metadonnees: dict, nom_utilisateur: str = "User"):
        """Modifie uniquement les métadonnées propres à la vidéo (section video du JSON)"""
        video = self.model.campagne_courante.obtenir_video(nom_video) if self.model.campagne_courante else None
        if video:
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
        Récupère les temps de seek (start_time, duration) 
        directement depuis le modèle (qui lit le systemEvent.csv).
        """
        return self.model.get_angle_event_times(nom_video)

    # --- MÉTHODE MISE À JOUR (APPEL À DEUX APIS) ---
    def precalculer_metadonnees_externes(self, nom_video: str) -> bool:
        """
        Tente de récupérer les métadonnées (météo + astro) depuis Internet
        en utilisant Open-Meteo (météo) et wttr.in (astro).
        """
        print(f"🔄 Lancement du pré-calcul pour {nom_video}...")
        if not self.model.campagne_courante:
            return False
            
        video = self.model.campagne_courante.obtenir_video(nom_video)
        if not video:
            print(f"❌ Vidéo non trouvée pour pré-calcul: {nom_video}")
            return False

        # 1. Extraire les données nécessaires du JSON
        try:
            lat_str = video.metadata_propres.get('gpsDict_latitude', 'N/A')
            lon_str = video.metadata_propres.get('gpsDict_longitude', 'N/A')
            date_str = video.metadata_propres.get('campaign_dateDict_date', 'N/A') 
            heure_str = video.metadata_propres.get('hourDict_HMSOS', 'N/A')

            if date_str in ['N/A', '', 'None'] or heure_str in ['N/A', '', 'None']:
                print(f"❌ Données temporelles manquantes. Date: {date_str}, Heure: {heure_str}")
                return False
                
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                if lat == 0 or lon == 0:
                    print(f"❌ Données GPS invalides (0, 0) ou manquantes. Entrez-les manuellement.")
                    print(f"   Lat: {lat_str}, Lon: {lon_str}")
                    return False
            except (ValueError, TypeError):
                print(f"❌ Données GPS invalides (non numériques). Lat: {lat_str}, Lon: {lon_str}")
                return False
            
            try:
                heure_index = int(heure_str.split(':')[0])
            except:
                print(f"❌ Format d'heure invalide: {heure_str}. Doit être HH:MM:SS")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des métadonnées locales: {e}")
            return False

        
        data_meteo_trouvee = False
        data_astro_trouvee = False

        # 2. APPEL 1: Open-Meteo pour la MÉTÉO (Air ET Mer)
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            is_future = date_obj > datetime.now().date()
            
            # --- MODIFICATION: Appel à l'API Marine (pour passé et futur) ---
            if is_future:
                # API de prévision marine
                API_URL = "https://api.open-meteo.com/v1/forecast"
                params = {
                    "latitude": lat, "longitude": lon,
                    "start_date": date_str, "end_date": date_str,
                    "hourly": "temperature_2m,windspeed_10m,wave_height,swell_wave_height", # Données complètes
                    "timezone": "auto"
                }
                print(f"   Appel API Prévision Météo/Marine: {API_URL}")
            else:
                # API Marine Historique
                API_URL = "https://marine-api.open-meteo.com/v1/marine"
                params = {
                    "latitude": lat, "longitude": lon,
                    "start_date": date_str, "end_date": date_str,
                    "hourly": "wave_height,swell_wave_height", # Données marines
                    "timezone": "auto"
                }
                print(f"   Appel API Marine (Historique): {API_URL}")
            # --- FIN MODIFICATION ---

            response_meteo = requests.get(API_URL, params=params, timeout=10)
            response_meteo.raise_for_status() 
            data_meteo = response_meteo.json()
            
            hourly_data = data_meteo.get('hourly', {})

            # --- MODIFICATION: Logique de parsing séparée ---
            # Parser Météo Air (uniquement si non-historique, car l'API Marine ne le fournit pas)
            if is_future and 'temperature_2m' in hourly_data and hourly_data['temperature_2m'][heure_index] is not None:
                temp_air = hourly_data['temperature_2m'][heure_index]
                wind_speed_kmh = hourly_data['windspeed_10m'][heure_index]
                
                video.metadata_propres['meteoAirDict_tempAir'] = str(temp_air)
                video.metadata_propres['meteoAirDict_wind'] = str(round(wind_speed_kmh, 1))
                data_meteo_trouvee = True
                print(f"   ✅ Données Météo Air (Prévision) trouvées: Temp: {temp_air}°C, Vent: {wind_speed_kmh} km/h")
            elif not is_future:
                # Si c'est historique, on doit faire un 2e appel à l'API archive
                print("   ℹ️ Date historique, appel séparé pour la météo terrestre...")
                API_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
                params_archive = {
                    "latitude": lat, "longitude": lon,
                    "start_date": date_str, "end_date": date_str,
                    "hourly": "temperature_2m,windspeed_10m",
                    "timezone": "auto"
                }
                response_archive = requests.get(API_ARCHIVE_URL, params=params_archive, timeout=10)
                response_archive.raise_for_status()
                data_archive = response_archive.json()
                
                if 'hourly' in data_archive and data_archive['hourly']['temperature_2m'][heure_index] is not None:
                    temp_air = data_archive['hourly']['temperature_2m'][heure_index]
                    wind_speed_kmh = data_archive['hourly']['windspeed_10m'][heure_index]
                    
                    video.metadata_propres['meteoAirDict_tempAir'] = str(temp_air)
                    video.metadata_propres['meteoAirDict_wind'] = str(round(wind_speed_kmh, 1))
                    data_meteo_trouvee = True
                    print(f"   ✅ Données Météo Air (Archive) trouvées: Temp: {temp_air}°C, Vent: {wind_speed_kmh} km/h")
            else:
                print(f"   ⚠️ Données météo air non trouvées pour l'heure {heure_index}")

            # Parser Météo Mer (devrait fonctionner pour les 2 APIs)
            if 'wave_height' in hourly_data and hourly_data['wave_height'][heure_index] is not None:
                wave_height = hourly_data['wave_height'][heure_index]
                swell_height = hourly_data['swell_wave_height'][heure_index]

                video.metadata_propres['meteoMerDict_seaState'] = str(round(wave_height, 1)) # État mer = hauteur vagues
                video.metadata_propres['meteoMerDict_swell'] = str(round(swell_height, 1)) # Houle
                data_meteo_trouvee = True
                print(f"   ✅ Données Météo Mer trouvées: État Mer (H. Vagues): {wave_height}m, Houle: {swell_height}m")
            else:
                 print(f"   ⚠️ Données météo mer (houle/vagues) non trouvées.")
            # --- FIN MODIFICATION ---

        except Exception as e:
            print(f"❌ Erreur lors de l'appel à l'API Open-Meteo: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Réponse: {e.response.text}")
            else:
                print("   L'erreur n'a pas de corps de réponse (timeout ou erreur réseau).")


        # 3. APPEL 2: wttr.in pour l'ASTRO (Phase de lune)
        try:
            WTTR_URL = f"https://wttr.in/{lat},{lon}?format=j1&date={date_str}&lang=fr"
            print(f"   Appel API Astro: {WTTR_URL}")
            response_astro = requests.get(WTTR_URL, timeout=20) 
            response_astro.raise_for_status()
            data_astro = response_astro.json()
            
            moon_phase = data_astro.get('weather', [{}])[0].get('astronomy', [{}])[0].get('moon_phase')
            
            if moon_phase:
                video.metadata_propres['astroDict_moon'] = moon_phase
                data_astro_trouvee = True
                print(f"   ✅ Données Astro trouvées: Phase de lune: {moon_phase}")
            else:
                print("   ⚠️ Données de phase de lune non trouvées dans la réponse de wttr.in")

        except Exception as e:
            print(f"❌ Erreur lors de l'appel à l'API wttr.in: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Réponse: {e.response.text}")
            else:
                print("   L'erreur n'a pas de corps de réponse (timeout ou erreur réseau).")


        # 4. Sauvegarder si au moins une donnée a été trouvée
        if data_meteo_trouvee or data_astro_trouvee:
            # Ne pas écraser les champs de marée s'ils sont déjà remplis
            if 'astroDict_coefficient' not in video.metadata_propres or video.metadata_propres['astroDict_coefficient'] in [None, ""]:
                 video.metadata_propres['astroDict_coefficient'] = None # Reste vide pour saisie manuelle
            if 'astroDict_tide' not in video.metadata_propres or video.metadata_propres['astroDict_tide'] in [None, ""]:
                 video.metadata_propres['astroDict_tide'] = None # Reste vide pour saisie manuelle
            
            return self.sauvegarder_metadonnees_vers_json(video)
        else:
            print("❌ Aucune donnée externe n'a pu être récupérée.")
            return False
    
    
    def show_success_dialog(self, parent_view):
        """Affiche une boîte de dialogue de confirmation après modification des métadonnées"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            parent_view,
            "Succès",
            "Les métadonnées ont été modifiées avec succès !",
        )