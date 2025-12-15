"""
MODEL - Gestion des données de l'application KOSMOS (ADAPTÉ)
Import depuis structure de dossiers numérotés (0113, 0114, etc.)
Architecture MVC - Couche Modèle
"""
import os
import json
import csv
import cv2
import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Labels pour l'affichage des métadonnées
METADATA_COMMUNES_LABELS = {
    'system_camera': 'Caméra',
    'system_model': 'Modèle',
    'system_system': 'Système',
    'system_version': 'Version',
    'campaign_zoneDict_campaign': 'Campagne',
    'campaign_zoneDict_zone': 'Zone',
    'campaign_zoneDict_locality': 'Localité',
    'campaign_zoneDict_protection': 'Protection',
    'campaign_dateDict_date': 'Date',
    'campaign_deploiementDict_boat': 'Bateau',
    'campaign_deploiementDict_pilot': 'Pilote',
    'campaign_deploiementDict_crew': 'Équipage',
    'campaign_deploiementDict_partners': 'Partenaires'
}

METADATA_PROPRES_LABELS = {
    # GPS
    'latitude': 'Latitude (°)',
    'longitude': 'Longitude (°)',
    'site': 'Site',
    # Météo Air
    'tempAir': 'Temp. Air (°C)',
    'wind': 'Vent (km/h)',
    'sky': 'Ciel',
    'atmPress': 'Pression (hPa)',
    'direction': 'Dir. Vent',
    # Météo Mer
    'seaState': 'État Mer',
    'swell': 'Houle (m)',
    # Astro
    'coefficient': 'Coeff. Marée',
    'moon': 'Phase Lune',
    'tide': 'Marée',
    # CTD
    'depth': 'Prof. (m)',
    'salinity': 'Salinité (PSU)',
    'temperature': 'Temp. Eau (°C)',
    # Heure
    'HMSOS': 'Heure Début',
    'hour': 'Heure (h)',
    'minute': 'Minute (m)',
    'second': 'Seconde (s)',
    'ymdOS': 'Date (YMD)',
    # Station
    'codestation': 'Code Station',
    'increment': 'Incrément',
    # Analyse
    'exploitability': 'Exploitabilité',
    'fauna': 'Faune',
    'habitat': 'Habitat',
    'visibility': 'Visibilité'
}


class Video:
    """
    Classe représentant une vidéo avec ses métadonnées
    """
    def __init__(self, nom: str, chemin: str, dossier_numero: str, taille: str = "", duree: str = "", date: str = ""):
        self.nom = nom
        self.chemin = chemin
        self.dossier_numero = dossier_numero  # Numéro du dossier (ex: "0113")
        self.taille = taille
        self.duree = duree
        self.date = date
        
        self.start_time_str: str = "00:00:00" 
        
        self.metadata_communes = {
            'system': '',
            'camera': '',
            'model': '',
            'version': ''
        }
        
        # Métadonnées propres (campagne) - modifiables
        self.metadata_propres = {
            # Tous les champs (gpsDict_Latitude, etc.) sont ajoutés dynamiquement
        }
        
        self.est_selectionnee = False
        self.est_conservee = True
        
    def get_formatted_metadata_communes(self) -> Dict[str, Dict[str, str]]:
        """Retourne les métadonnées communes organisées par section pour l'affichage."""
        sections = {}
        for key, value in self.metadata_communes.items():
            if '_' in key:
                section_name = key.split('_')[0]
                if section_name not in sections: sections[section_name] = {}
                sections[section_name][key] = value
        return sections

    def get_formatted_metadata_propres(self) -> Dict[str, Dict[str, tuple]]:
        """Retourne les métadonnées propres organisées par section pour l'affichage."""
        sections = {}
        for full_key, value in self.metadata_propres.items():
            if full_key.startswith('campaign_'):
                continue
            
            if '_' in full_key:
                section_name, field_name = full_key.split('_', 1)
                
                if section_name not in sections:
                    sections[section_name] = {}
                sections[section_name][field_name] = (full_key, value)
            else:
                if 'general' not in sections:
                    sections['general'] = {}
                sections['general'][full_key] = (full_key, value)
        return sections

    def to_dict(self) -> Dict:
        """Convertit la vidéo en dictionnaire pour sauvegarde"""
        return {
            'nom': self.nom,
            'chemin': self.chemin,
            'dossier_numero': self.dossier_numero,
            'taille': self.taille,
            'duree': self.duree,
            'date': self.date,
            'metadata_communes': self.metadata_communes,
            'metadata_propres': self.metadata_propres,
            'est_conservee': self.est_conservee,
            'start_time_str': self.start_time_str
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Video':
        """Crée une vidéo depuis un dictionnaire"""
        duree = data.get('duree', '')
        chemin = data.get('chemin', '')
        
        # Si la durée est manquante ou invalide, on tente de la recalculer
        if (not duree or duree == "--:--") and chemin and os.path.exists(chemin):
            try:
                cap = cv2.VideoCapture(chemin)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    if fps > 0:
                        duration_sec = frame_count / fps
                        m, s = divmod(duration_sec, 60)
                        h, m = divmod(m, 60)
                        duree = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                cap.release()
            except Exception:
                pass

        video = Video(
            nom=data.get('nom', ''),
            chemin=chemin,
            dossier_numero=data.get('dossier_numero', ''),
            taille=data.get('taille', ''),
            duree=duree,
            date=data.get('date', '')
        )
        video.metadata_communes = data.get('metadata_communes', {})
        video.metadata_propres = data.get('metadata_propres', {})
        video.est_conservee = data.get('est_conservee', True)
        video.start_time_str = data.get('start_time_str', "00:00:00")
        
        return video

    def charger_metadonnees_propres_json(self) -> bool:
        """Charge les métadonnées propres (section 'video') depuis le JSON."""
        try:
            json_path = Path(self.chemin).parent / f"{self.dossier_numero}.json"
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.metadata_propres.clear()
            
            def flatten_dict(section_data, prefix=''):
                for key, value in section_data.items():
                    if isinstance(value, dict):
                        flatten_dict(value, prefix=f"{prefix}{key}_")
                    else:
                        full_key = f"{prefix}{key}"
                        self.metadata_propres[full_key] = str(value) if value is not None else ""

            if 'video' in data:
                flatten_dict(data['video'])
            return True
        except Exception as e:
            print(f"❌ Erreur lecture JSON propres (model): {e}")
            return False

    def charger_metadonnees_communes_json(self) -> bool:
        """Charge les métadonnées communes ('system', 'campaign') depuis le JSON."""
        try:
            json_path = Path(self.chemin).parent / f"{self.dossier_numero}.json"
            if not json_path.exists(): return False

            with open(json_path, 'r', encoding='utf-8') as f: data = json.load(f)
            self.metadata_communes.clear()

            def flatten_dict(d, p=''):
                for k, v in d.items():
                    if isinstance(v, dict): flatten_dict(v, f"{p}{k}_")
                    else: self.metadata_communes[f"{p}{k}"] = str(v) if v is not None else ""
            
            if 'system' in data: flatten_dict(data['system'], "system_")
            if 'campaign' in data: flatten_dict(data['campaign'], "campaign_")
            return True
        except Exception as e:
            print(f"❌ Erreur lecture JSON communes (model): {e}")
            return False

    def charger_donnees_timeseries_csv(self) -> bool:
        """Charge les données temporelles (temp, pression...) depuis le CSV."""
        self.timeseries_data = [] # Réinitialiser les données
        try:
            csv_path = Path(self.chemin).parent / f"{self.dossier_numero}.csv"
            if not csv_path.exists():
                print(f"⚠️ Fichier CSV non trouvé pour la vidéo: {csv_path}")
                return False

            with open(csv_path, 'r', encoding='utf-8') as f:
                # Détecter le délimiteur en lisant la première ligne
                first_line = f.readline()
                delimiter = ';' if ';' in first_line else ','
                f.seek(0) # Revenir au début du fichier
                reader = csv.DictReader(f, delimiter=delimiter)
                
                def hms_to_seconds(hms_str):
                    """Convertit une chaîne 'HHhMMmSSs' en secondes totales."""
                    try:
                        parts = hms_str.lower().replace('s', '').split('h')
                        h = int(parts[0])
                        parts = parts[1].split('m')
                        m = int(parts[0])
                        s = int(parts[1])
                        return h * 3600 + m * 60 + s
                    except (ValueError, IndexError):
                        return None

                # Lire la première ligne de données pour obtenir l'heure de début
                all_rows = list(reader)
                if not all_rows:
                    return False

                start_hms_str = all_rows[0].get('HMS')
                start_total_seconds = hms_to_seconds(start_hms_str)

                if start_total_seconds is None:
                    print("❌ Erreur: Impossible de lire l'heure de début (colonne HMS) dans le CSV.")
                    return False

                # Mapper les noms de colonnes possibles vers les noms standard
                column_mapping = {
                    'pression': 'Pression',
                    'temperature': 'TempC',
                    'lux': 'Lux'
                }
                
                for row in all_rows:
                    processed_row = {}
                    current_hms_str = row.get('HMS')
                    current_total_seconds = hms_to_seconds(current_hms_str)

                    for standard_name, csv_name in column_mapping.items():
                        if csv_name in row and row[csv_name] and row[csv_name].strip():
                            value = row[csv_name].strip().replace(',', '.')
                            processed_row[standard_name] = value
                    
                    if current_total_seconds is not None:
                        delta_seconds = current_total_seconds - start_total_seconds
                        processed_row['timestamp_ms'] = int(delta_seconds * 1000)
                        self.timeseries_data.append(processed_row)

            print(f"✅ Données CSV chargées pour {self.nom}: {len(self.timeseries_data)} points.")
            return True
        except Exception as e:
            print(f"❌ Erreur lecture CSV (model): {e}")
            return False

    def sauvegarder_metadonnees_propres_json(self) -> bool:
        """Sauvegarde les métadonnées propres dans le fichier JSON."""
        try:
            json_path = Path(self.chemin).parent / f"{self.dossier_numero}.json"
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
            
            for key, value in self.metadata_propres.items():
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
            print(f"❌ Erreur sauvegarde JSON propres (model): {e}")
            return False

    def sauvegarder_metadonnees_communes_json(self) -> bool:
        """Sauvegarde les métadonnées communes dans le fichier JSON."""
        try:
            json_path = Path(self.chemin).parent / f"{self.dossier_numero}.json"
            if not json_path.exists():
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. System
            if 'system' not in data: data['system'] = {}
            
            # 2. Campaign
            if 'campaign' not in data: data['campaign'] = {}
            
            for key, value in self.metadata_communes.items():
                # Déterminer la section (system_ ou campaign_)
                section = None
                field = None
                
                if key.startswith("system_"):
                    section = data['system']
                    field = key.replace("system_", "")
                elif key.startswith("campaign_"):
                    section = data['campaign']
                    field = key.replace("campaign_", "")
                
                if section is not None and field:
                    if value == "" or value == "None":
                        section[field] = None
                    else:
                        try:
                            val_test = float(value)
                            if val_test.is_integer():
                                section[field] = int(val_test)
                            else:
                                section[field] = val_test
                        except ValueError:
                            section[field] = value
            
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
            print(f"❌ Erreur sauvegarde JSON communes (model): {e}")
            return False


class Campagne:
    """
    Classe représentant une campagne (étude) avec ses vidéos
    """
    def __init__(self, nom: str, emplacement: str):
        self.nom = nom
        self.emplacement = emplacement
        self.videos: List[Video] = []
        self.workspace_extraction = ""  # Chemin vers le dossier extraction
        self.date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.date_modification = self.date_creation
        
    def ajouter_video(self, video: Video):
        """Ajoute une vidéo à la campagne"""
        self.videos.append(video)
        self.date_modification = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def supprimer_video(self, nom_video: str):
        """Supprime une vidéo de la campagne"""
        self.videos = [v for v in self.videos if v.nom != nom_video]
        self.date_modification = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def obtenir_video(self, nom: str) -> Optional[Video]:
        """Récupère une vidéo par son nom"""
        for video in self.videos:
            if video.nom == nom:
                return video
        return None
    
    def obtenir_videos_conservees(self) -> List[Video]:
        """Retourne uniquement les vidéos conservées"""
        return [v for v in self.videos if v.est_conservee]
    
    def obtenir_videos_a_supprimer(self) -> List[Video]:
        """Retourne les vidéos marquées pour suppression"""
        return [v for v in self.videos if not v.est_conservee]
    
    def to_dict(self) -> Dict:
        """Convertit la campagne en dictionnaire pour sauvegarde"""
        return {
            'nom': self.nom,
            'emplacement': self.emplacement,
            'workspace_extraction': self.workspace_extraction,
            'date_creation': self.date_creation,
            'date_modification': self.date_modification,
            'videos': [v.to_dict() for v in self.videos]
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Campagne':
        """Crée une campagne depuis un dictionnaire"""
        campagne = Campagne(
            nom=data.get('nom', ''),
            emplacement=data.get('emplacement', '')
        )
        campagne.workspace_extraction = data.get('workspace_extraction', '')
        campagne.date_creation = data.get('date_creation', '')
        campagne.date_modification = data.get('date_modification', '')
        campagne.videos = [Video.from_dict(v) for v in data.get('videos', [])]
        return campagne
    
    def sauvegarder(self) -> bool:
        """Sauvegarde la campagne dans un fichier JSON"""
        try:
            # Si emplacement est vide, utiliser le dossier d'import
            if not self.emplacement and hasattr(self, 'dossier_import'):
                self.emplacement = self.dossier_import
            
            Path(self.emplacement).mkdir(parents=True, exist_ok=True)
            fichier_config = os.path.join(self.emplacement, f"{self.nom}_config.json")
            
            with open(fichier_config, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
            
            print(f"💾 Configuration sauvegardée : {fichier_config}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")
            return False
        
    @staticmethod
    def charger(chemin_fichier: str) -> Optional['Campagne']:
        """Charge une campagne depuis un fichier JSON"""
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Campagne.from_dict(data)
        except Exception as e:
            print(f"❌ Erreur lors du chargement : {e}")
            return None


class ApplicationModel:
    """
    Modèle principal unique de l'application KOSMOS
    """
    def __init__(self):
        self.campagne_courante: Optional[Campagne] = None
        self.dossier_videos_import: str = ""
        self.page_courante: str = "accueil"
        self.video_selectionnee: Optional[Video] = None
    
    # ═══════════════════════════════════════════════════════════════
    # GESTION DES CAMPAGNES
    # ═══════════════════════════════════════════════════════════════
    
    def creer_campagne(self, nom: str, emplacement: str) -> Campagne:
        """Crée une nouvelle campagne"""
        self.campagne_courante = Campagne(nom, emplacement)
        return self.campagne_courante
    
    def ouvrir_campagne(self, chemin_fichier: str) -> bool:
        """Ouvre une campagne existante"""
        campagne = Campagne.charger(chemin_fichier)
        if campagne:
            self.campagne_courante = campagne
            return True
        return False
    
    def sauvegarder_campagne(self) -> bool:
        """Sauvegarde la campagne courante"""
        if self.campagne_courante:
            return self.campagne_courante.sauvegarder()
        return False
    
    def fermer_campagne(self):
        """Ferme la campagne courante"""
        self.campagne_courante = None
        self.video_selectionnee = None
        self.page_courante = "accueil"
    
    def supprimer_fichier_video(self, nom_video: str) -> bool:
        """
        Supprime physiquement le fichier vidéo et le retire de la campagne.
        """
        if not self.campagne_courante:
            return False
            
        video = self.campagne_courante.obtenir_video(nom_video)
        if not video:
            return False
            
        try:
            chemin_fichier = Path(video.chemin)
            if chemin_fichier.exists():
                os.remove(chemin_fichier)
                print(f"🗑️ Fichier supprimé : {chemin_fichier}")
            
            self.campagne_courante.supprimer_video(nom_video)
            
            if self.video_selectionnee and self.video_selectionnee.nom == nom_video:
                self.video_selectionnee = None
                
            return True
        except Exception as e:
            print(f"❌ Erreur suppression fichier vidéo (model): {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # IMPORTATION DES VIDÉOS - STRUCTURE KOSMOS
    # ═══════════════════════════════════════════════════════════════
    
    def importer_videos_kosmos(self, dossier_principal: str) -> Dict:
        """
        Importe les vidéos depuis la structure KOSMOS
        """
        self.dossier_videos_import = dossier_principal
    
        # Mettre à jour l'emplacement de la campagne avec le dossier d'import
        if self.campagne_courante:
            self.campagne_courante.emplacement = dossier_principal
            self.campagne_courante.dossier_import = dossier_principal
        
        resultats = {
            'videos_importees': [],
            'videos_sans_metadata': [],
            'erreurs': []
        }
        
        extensions_video = ('.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI', '.MOV', '.MKV', 
                            '.h264', '.H264', '.mpg', '.MPG', '.mpeg', '.MPEG')
        
        print(f"\n{'='*60}")
        print(f"📹 IMPORTATION KOSMOS")
        print(f"{'='*60}")
        print(f"📁 Dossier principal : {dossier_principal}")
        
        # Vérifier que le dossier principal existe
        try:
            tous_elements = os.listdir(dossier_principal)
            print(f"📂 {len(tous_elements)} éléments trouvés dans le dossier principal")
            
            sous_dossiers = [d for d in tous_elements 
                             if os.path.isdir(os.path.join(dossier_principal, d))]
            
            print(f"📁 {len(sous_dossiers)} sous-dossiers identifiés")
            
            for i, dossier in enumerate(sous_dossiers[:5]):
                print(f"   {i+1}. {dossier}")
            if len(sous_dossiers) > 5:
                print(f"   ... et {len(sous_dossiers) - 5} autres")
            
            if not sous_dossiers:
                print(f"⚠️ Aucun sous-dossier trouvé, recherche des vidéos directement...")
                videos_directes = [f for f in tous_elements 
                                   if any(f.lower().endswith(ext.lower()) for ext in extensions_video)]
                
                if videos_directes:
                    print(f"✅ {len(videos_directes)} vidéo(s) trouvée(s) directement dans le dossier")
                    for nom_video in videos_directes:
                        chemin_video = os.path.join(dossier_principal, nom_video)
                        video = self._creer_video_depuis_fichier(chemin_video, "racine")
                        
                        if self.campagne_courante:
                            self.campagne_courante.ajouter_video(video)
                            resultats['videos_importees'].append(video.nom)
                
                    return resultats
                else:
                    print(f"❌ Aucune vidéo trouvée dans le dossier")
                    return resultats
            
            for nom_dossier in sous_dossiers:
                chemin_dossier = os.path.join(dossier_principal, nom_dossier)
                print(f"\n🔍 Analyse de : {nom_dossier}")
                
                try:
                    fichiers = os.listdir(chemin_dossier)
                    print(f"   📄 {len(fichiers)} fichier(s) trouvé(s)")
                    
                    for fichier in fichiers[:10]:
                        ext = os.path.splitext(fichier)[1]
                        print(f"       - {fichier} [{ext}]")
                    if len(fichiers) > 10:
                        print(f"       ... et {len(fichiers) - 10} autres fichiers")
                    
                    videos_trouvees = []
                    for fichier in fichiers:
                        ext = os.path.splitext(fichier)[1].lower()
                        if any(ext == e.lower() for e in extensions_video):
                            videos_trouvees.append(fichier)
                    
                    if not videos_trouvees:
                        print(f"   ⚠️ Aucune vidéo avec extensions reconnues")
                        continue
                    
                    print(f"   ✅ {len(videos_trouvees)} vidéo(s) trouvée(s)")
                    
                    for nom_video in videos_trouvees:
                        print(f"       📹 {nom_video}")
                        chemin_video = os.path.join(chemin_dossier, nom_video)
                        
                        # Créer l'objet vidéo
                        video = self._creer_video_depuis_fichier(chemin_video, nom_dossier)
                        
                        # --- BLOC LECTURE JSON ---
                        json_path = Path(video.chemin).parent / f"{video.dossier_numero}.json"
                        
                        if json_path.exists():
                            try:
                                with open(json_path, 'r', encoding='utf-8') as f:
                                    meta_json = json.load(f)
                                    hmsos = meta_json.get('video', {}).get('hourDict', {}).get('HMSOS', None)
                                    if hmsos:
                                        video.start_time_str = hmsos
                                        print(f"       ... Heure début JSON chargée : {hmsos}")
                                    else:
                                        print(f"       ... Clé 'HMSOS' non trouvée dans {json_path}")
                            except Exception as e:
                                print(f"       ... Erreur lecture JSON {json_path}: {e}")
                        else:
                             print(f"       ... Fichier JSON non trouvé : {json_path}")
                        # --- FIN BLOC LECTURE JSON ---

                        # Charger les métadonnées depuis le CSV du dossier
                        chemin_csv = os.path.join(chemin_dossier, f"{nom_dossier}.csv")
                        
                        if os.path.exists(chemin_csv):
                            print(f"       📊 CSV trouvé : {nom_dossier}.csv")
                            if self._charger_metadata_kosmos_csv(video, chemin_csv):
                                resultats['videos_importees'].append(video.nom)
                            else:
                                resultats['videos_sans_metadata'].append(video.nom)
                        else:
                            print(f"       ⚠️ Pas de CSV trouvé")
                            resultats['videos_sans_metadata'].append(video.nom)
                        
                        if self.campagne_courante:
                            self.campagne_courante.ajouter_video(video)
                
                except Exception as e:
                    print(f"   ❌ Erreur dans {nom_dossier} : {e}")
                    resultats['erreurs'].append(f"Erreur dans {nom_dossier}: {e}")
            
            print(f"\n{'='*60}")
            print(f"📊 RÉSULTATS")
            print(f"{'='*60}")
            print(f"✅ Vidéos importées : {len(resultats['videos_importees'])}")
            print(f"⚠️   Sans métadonnées : {len(resultats['videos_sans_metadata'])}")
            print(f"❌ Erreurs : {len(resultats['erreurs'])}")
            print(f"{'='*60}\n")
                            
        except Exception as e:
            resultats['erreurs'].append(f"Erreur globale : {e}")
            print(f"❌ Erreur globale : {e}")
        
        return resultats
    
    def _creer_video_depuis_fichier(self, chemin: str, dossier_numero: str) -> Video:
        """Crée un objet Video à partir d'un fichier"""
        nom = os.path.basename(chemin)
        
        taille = self._formater_taille(os.path.getsize(chemin))
        date_modif = datetime.fromtimestamp(
            os.path.getmtime(chemin)
        ).strftime("%d/%m/%Y")
        
        # Calcul de la durée via OpenCV
        duree = "--:--"
        try:
            cap = cv2.VideoCapture(chemin)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if fps > 0:
                    duration_sec = frame_count / fps
                    m, s = divmod(duration_sec, 60)
                    h, m = divmod(m, 60)
                    duree = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            cap.release()
        except Exception as e:
            print(f"⚠️ Impossible de calculer la durée pour {nom}: {e}")

        video = Video(
            nom=nom,
            chemin=chemin,
            dossier_numero=dossier_numero,
            taille=taille,
            duree=duree,
            date=date_modif
        )
        
        return video
    
    def _charger_metadata_kosmos_csv(self, video: Video, chemin_csv: str) -> bool:
        """
        Charge les métadonnées DE BASE (Communes + Durée) depuis le CSV KOSMOS.
        Toutes les autres métadonnées (GPS, CTD...) doivent provenir du JSON.
        """
        try:
            with open(chemin_csv, 'r', encoding='utf-8') as f:
                # Détecter le délimiteur (gère ; et ,)
                try:
                    dialect = csv.Sniffer().sniff(f.read(1024), delimiters=';,')
                    f.seek(0)
                    reader = csv.DictReader(f, dialect=dialect)
                except csv.Error:
                    f.seek(0)
                    print(f"       ... Avertissement: Délimiteur CSV non détecté, utilisation de ';' par défaut.")
                    reader = csv.DictReader(f, delimiter=';')
                
                
                # Lire la première ligne de données
                row = next(reader, None)
                if not row:
                    print(f"       ... Avertissement: CSV {chemin_csv} est vide.")
                    return False

                # Créer un dictionnaire de clés normalisées (minuscules)
                normalized_row = {key.lower(): value for key, value in row.items()}

                # Remplir les métadonnées communes
                video.metadata_communes['system'] = normalized_row.get('system', '')
                video.metadata_communes['camera'] = normalized_row.get('camera', '')
                video.metadata_communes['model'] = normalized_row.get('model', '')
                video.metadata_communes['version'] = normalized_row.get('version', '')
                
                # Remplir la durée si elle existe et est valide dans le CSV
                csv_duree = normalized_row.get('duree', normalized_row.get('duration', ''))
                if csv_duree and csv_duree != "--:--" and csv_duree.strip() != "":
                    video.duree = csv_duree
                
                

                print(f"       ... Données communes (Système, Durée) chargées depuis CSV.")

            return True
            
        except Exception as e:
            print(f"⚠️ Erreur lecture CSV {chemin_csv}: {e}")
            return False
    
    
    def _formater_taille(self, taille_bytes: int) -> str:
        """Formate une taille en octets"""
        for unite in ['o', 'Ko', 'Mo', 'Go']:
            if taille_bytes < 1024.0:
                return f"{taille_bytes:.1f} {unite}"
            taille_bytes /= 1024.0
        return f"{taille_bytes:.1f} To"
    
    # ═══════════════════════════════════════════════════════════════
    # GESTION DU TRI
    # ═══════════════════════════════════════════════════════════════
    
    def selectionner_video(self, nom_video: str) -> Optional[Video]:
        """Sélectionne une vidéo par son nom"""
        if not self.campagne_courante:
            return None
        
        if self.video_selectionnee:
            self.video_selectionnee.est_selectionnee = False
        
        video = self.campagne_courante.obtenir_video(nom_video)
        if video:
            video.est_selectionnee = True
            self.video_selectionnee = video
            return video
        
        return None
    
    def renommer_video(self, ancien_nom: str, nouveau_nom: str) -> bool:
        """Renomme une vidéo"""
        if not self.campagne_courante:
            return False
        
        video = self.campagne_courante.obtenir_video(ancien_nom)
        if video:
            video.nom = nouveau_nom
            return True
        return False
    
    def marquer_video_pour_suppression(self, nom_video: str) -> bool:
        """Marque une vidéo pour suppression"""
        if not self.campagne_courante:
            return False
        
        video = self.campagne_courante.obtenir_video(nom_video)
        if video:
            video.est_conservee = False
            return True
        return False
    
    def conserver_video(self, nom_video: str) -> bool:
        """Marque une vidéo comme conservée"""
        if not self.campagne_courante:
            return False
        
        video = self.campagne_courante.obtenir_video(nom_video)
        if video:
            video.est_conservee = True
            return True
        return False
    
    def supprimer_videos_marquees(self) -> int:
        """Supprime définitivement les vidéos marquées"""
        if not self.campagne_courante:
            return 0
        
        videos_a_supprimer = self.campagne_courante.obtenir_videos_a_supprimer()
        count = len(videos_a_supprimer)
        
        for video in videos_a_supprimer:
            self.campagne_courante.supprimer_video(video.nom)
        
        if self.video_selectionnee and not self.video_selectionnee.est_conservee:
            self.video_selectionnee = None
        
        return count
    
    def modifier_metadonnees_propres(self, nom_video: str, nouvelles_meta: Dict) -> bool:
        """Modifie les métadonnées propres d'une vidéo"""
        if not self.campagne_courante:
            return False
        
        video = self.campagne_courante.obtenir_video(nom_video)
        if video:
            for key, value in nouvelles_meta.items():
                video.metadata_propres[key] = value
            return True
        return False
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════════════════
    
    def obtenir_statistiques(self) -> Dict:
        """Retourne des statistiques sur la campagne courante"""
        if not self.campagne_courante:
            return {
                'total': 0,
                'conservees': 0,
                'a_supprimer': 0,
                'selectionnee': None
            }
        
        return {
            'total': len(self.campagne_courante.videos),
            'conservees': len(self.campagne_courante.obtenir_videos_conservees()),
            'a_supprimer': len(self.campagne_courante.obtenir_videos_a_supprimer()),
            'selectionnee': self.video_selectionnee.nom if self.video_selectionnee else None
        }
    
    def obtenir_videos(self) -> List[Video]:
        """Retourne la liste des vidéos de la campagne courante"""
        if self.campagne_courante:
            return self.campagne_courante.videos
        return []

    # --- MÉTHODES POUR LES MINIATURES D'ANGLE ---

    def _parse_time_to_seconds(self, time_str: str) -> int:
        """
        Convertit un temps "HHhMMmSSs" (CSV) ou "HH:MM:SS" (JSON) en secondes totales.
        """
        if time_str is None: return 0
        try:
            # Format CSV : "11h46m54s"
            if 'h' in time_str and 'm' in time_str and 's' in time_str:
                parts = time_str.replace('s', '').split('m')
                h_part = parts[0].split('h')
                h = int(h_part[0])
                m = int(h_part[1])
                s = int(parts[1])
                return h * 3600 + m * 60 + s
            
            # Format JSON : "11:46:54"
            elif ':' in time_str:
                parts = time_str.split(':')
                h = int(parts[0])
                m = int(parts[1])
                s = int(float(parts[2])) # float() gère les secondes avec décimales
                return h * 3600 + m * 60 + s
                
            print(f"⚠️ Format temps non reconnu: {time_str}")
            return 0
        except Exception as e:
            print(f"❌ Erreur parsing temps '{time_str}': {e}")
            return 0


    def get_angle_event_times(self, nom_video: str) -> list[tuple[str, int]]:
        """
        Calcule les temps de "seek" et les DURÉES pour les 6 
        premiers événements "START MOTEUR" trouvés depuis le systemEvent.csv
        """
        if not self.campagne_courante:
            return []
            
        video = self.campagne_courante.obtenir_video(nom_video)
        if not video:
            return []

        # Valeurs par défaut
        default_seek = "00:00:01"
        default_duration = 2
        default_result = [(default_seek, default_duration)] * 6

        try:
            event_csv_path = Path(video.chemin).parent / "systemEvent.csv"
            
            if not event_csv_path.exists():
                print(f"⚠️ Fichier systemEvent.csv introuvable pour {nom_video}")
                return default_result

            video_start_seconds = 0
            video_base_name = video.dossier_numero
            
            with open(event_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row.get('Event') == 'START ENCODER':
                        csv_filename = row.get('Fichier', '')
                        if video_base_name in csv_filename:
                            video_start_seconds = self._parse_time_to_seconds(row['Heure'])
                            print(f"   ... Heure début (START ENCODER) trouvée : {row['Heure']}")
                            break
            
            if video_start_seconds == 0:
                print(f"❌ Erreur: 'START ENCODER' non trouvé pour {video_base_name}. Fallback vers 1er 'START MOTEUR'.")
                with open(event_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                         if row.get('Event') == 'START MOTEUR':
                            video_start_seconds = self._parse_time_to_seconds(row['Heure'])
                            print(f"   ... Fallback : Utilisation du 1er 'START MOTEUR' comme heure de début.")
                            break
            
            if video_start_seconds == 0:
                 print(f"❌ Erreur: Aucun event de démarrage trouvé.")
                 return default_result

            motor_event_times = []
            with open(event_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row.get('Event') == 'START MOTEUR':
                        event_seconds = self._parse_time_to_seconds(row['Heure'])
                        if event_seconds >= video_start_seconds:
                            motor_event_times.append(event_seconds)
            
            START_INDEX = 9 
            NUM_PREVIEWS = 6
            PREVIEW_DURATION_SEC = 30 
            START_OFFSET_SEC = 5      
            
            if len(motor_event_times) < START_INDEX + 1:
                print(f"   ... Moins de 10 'START MOTEUR' trouvés (seulement {len(motor_event_times)}).")
                return default_result
                
            results = []
            
            events_to_process = motor_event_times[START_INDEX : START_INDEX + NUM_PREVIEWS] 
            
            if len(events_to_process) < NUM_PREVIEWS:
                print(f"   ... Info: Moins de 6 événements trouvés après le 10e. Duplication du dernier.")
                while len(events_to_process) < NUM_PREVIEWS:
                    events_to_process.append(events_to_process[-1])
            
            for event_abs_time in events_to_process:
                
                seek_start_abs_time = event_abs_time + START_OFFSET_SEC
                
                seek_start_relative_sec = seek_start_abs_time - video_start_seconds
                if seek_start_relative_sec < 0: seek_start_relative_sec = 0
                
                m, s = divmod(seek_start_relative_sec, 60)
                h, m = divmod(m, 60)
                seek_start_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                
                results.append( (seek_start_str, PREVIEW_DURATION_SEC) )

            print(f"✅ 6 angles (dès le 10e) trouvés. Infos (start_time, duration=30s) : {results}")
            return results

        except Exception as e:
            print(f"❌ Erreur calcul seek times: {e}")
            return default_result


# Test du modèle
if __name__ == '__main__':
    print("🧪 Test du modèle KOSMOS adapté...")
    
    model = ApplicationModel()
    
    campagne = model.creer_campagne("Test_KOSMOS", "./test_campagne")
    print(f"✅ Campagne créée : {campagne.nom}")
    
    test_import_dir = Path("./test_import")
    test_import_dir.mkdir(exist_ok=True)
    dossier_0001 = test_import_dir / "0001"
    dossier_0001.mkdir(exist_ok=True)
    
    (dossier_0001 / "0001.mp4").touch()
    
    faux_json_path = dossier_0001 / "0001.json"
    faux_json_data = {
        "video": {
            "hourDict": {
                "HMSOS": "12:00:00"
            }
        }
    }
    with open(faux_json_path, 'w') as f:
        json.dump(faux_json_data, f)

    faux_csv_path = dossier_0001 / "0001.csv"
    with open(faux_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Date', 'Heure', 'Latitude', 'Longitude', 'Campaign', 'Zone', 'Duration', 'System', 'Pressure', 'Temperature', 'Salinity'])
        writer.writerow(['2024-01-01', '12:00:00', '48.1234', '-4.5678', 'TestCamp', 'ZoneA', '00:30:00', 'KOSMOS_v3', '15.5', '14.2', '35.1'])
        
    print(f"📁 Faux dossier d'import créé à: {test_import_dir.resolve()}")

    resultats = model.importer_videos_kosmos(str(test_import_dir.resolve()))
    
    if model.campagne_courante and model.campagne_courante.videos:
        video_test = model.campagne_courante.videos[0]
        print(f"Vérification des métadonnées chargées pour {video_test.nom}:")
        print(f"  Lat (attendu None): {video_test.metadata_propres.get('gpsDict_latitude')}")
        print(f"  Lon (attendu None): {video_test.metadata_propres.get('gpsDict_longitude')}")
        print(f"  Date (attendu None): {video_test.metadata_propres.get('campaign_dateDict_date')}")
        print(f"  Durée (attendu 00:30:00): {video_test.duree}")
        print(f"  Pression/Prof (attendu None): {video_test.metadata_propres.get('ctdDict_depth')}")
        print(f"  Temp Eau (attendu None): {video_test.metadata_propres.get('ctdDict_temperature')}")
        print(f"  Salinité (attendu None): {video_test.metadata_propres.get('ctdDict_salinity')}")
    else:
        print("❌ Échec de l'importation test.")

    import shutil
    try:
        shutil.rmtree(test_import_dir)
        shutil.rmtree(Path("./test_campagne"))
        print("🧹 Nettoyage des dossiers de test effectué.")
    except Exception as e:
        print(f"🧹 Erreur lors du nettoyage: {e}")

    print("✅ Tests terminés!")


##############################################
## Scripts généraux
##############################################


def Float2BGR(I):
    """Conversion d'un float (0 - 1) à nb sur 8 bits (0 - 255)"""
    erf = I * 255
    src = erf.astype("uint8")
    return src


def BGR2Float(src):
    """Conversion d'un nb sur 8 bits (0 - 255) vers un float"""
    a = src.astype("float64") / 255
    return a


def AnalyseHisto(I, mask=None):
    """Médiane et écart type de chaque canal, avec masque optionnel."""
    img = I.astype(np.float64)
    if mask is not None:
        valid = mask.astype(bool)
        if img.ndim == 3:
            pixels = img[valid]
        else:
            pixels = img[valid, ...]
    else:
        if img.ndim == 3:
            pixels = img.reshape(-1, img.shape[-1])
        else:
            pixels = img.reshape(-1, 1)

    mean = np.median(pixels, axis=0)
    square = np.std(pixels, axis=0, ddof=0)
    return mean, square


def PlotHistogram(I):
    """Fonction qui donne l'histogramme d'une image"""
    plt.figure()
    color = ("b", "g", "r")
    for i, col in enumerate(color):
        histr = cv2.calcHist([I], [i], None, [256], [0, 256])
        plt.plot(histr, color=col)
    plt.xlim([0, 256])
    plt.legend(color)
    plt.title("Histogramme des canaux RGB")


##############################################
## Egalisation d'histogramme
##############################################


def process_image_HE(I, vB, vG, vR):
    """Egalisation d'histogramme avec des valeurs données pour chaque canal."""
    (MeanB, MeanG, MeanR), (SquareB, SquareG, SquareR) = AnalyseHisto(I)
    II = np.zeros(I.shape, dtype=np.float64)
    eps = 1e-6
    II[:, :, 0] = (I[:, :, 0] - MeanB + vB * SquareB) / (2 * max(vB * SquareB, eps))
    II[:, :, 1] = (I[:, :, 1] - MeanG + vG * SquareG) / (2 * max(vG * SquareG, eps))
    II[:, :, 2] = (I[:, :, 2] - MeanR + vR * SquareR) / (2 * max(vR * SquareR, eps))

    III = np.clip(II, 0, 1)
    IV = np.uint8(III * 255)
    return IV


##############################################
## Debrumage
##############################################


def DarkChannel(im, sz):
    """Determine le canal sombre de l'image"""
    b, g, r = cv2.split(im)  # Séparation des 3 canaux
    dc = cv2.min(cv2.min(r, g), b)  # La couleur minimale entre le canal bleu et vert.
    median_ksize = sz if sz % 2 == 1 else sz + 1
    dc8 = np.clip(dc * 255, 0, 255).astype(np.uint8)
    dc = cv2.medianBlur(dc8, median_ksize).astype(np.float32) / 255.0
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (sz, sz))  # Élément structurant pour l'érosion
    dark = cv2.erode(dc, kernel)  # Érosion de l'image en fonction de la couleur minimale
    return dark


def DarkChannelWater(im, sz):
    """Determine le canal sombre de l'image"""
    b, g, r = cv2.split(im)  # Séparation des 3 canaux
    dc = cv2.min(g, b)  # La couleur minimale entre le canal bleu et vert
    median_ksize = sz if sz % 2 == 1 else sz + 1
    dc8 = np.clip(dc * 255, 0, 255).astype(np.uint8)
    dc = cv2.medianBlur(dc8, median_ksize).astype(np.float32) / 255.0
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (sz, sz))  # Élément structurant pour l'érosion
    dark = cv2.erode(dc, kernel)  # Érosion de l'image en fonction de la couleur minimale
    return dark


def AtmLight(im, dark):
    """Estimation de la lumière atmosphérique"""
    [h, w] = im.shape[:2]
    imsz = h * w
    numpx = int(max(math.floor(imsz / 100), 1))  # Définition du nombre de valeurs à garder (0.1%)
    darkvec = dark.reshape(imsz)  # Façonne le tableau dark sans modification de données
    imvec = im.reshape(imsz, 3)
    indices = darkvec.argsort()  # Tri croissant des indices du tableau
    indices = indices[imsz - numpx :]  # Suppression des indices les plus faibles
    brightest = imvec[indices]
    A = np.mean(brightest, axis=0, keepdims=True)
    return A


def TransmissionEstimate(im, A, sz, omega=0.6):
    """Estimation de la transmission de l'image"""
    im3 = np.empty(im.shape, im.dtype)  # Initialisation du tableau correspondant à la transmission

    for ind in range(0, 3):
        denom = max(A[0, ind], 1e-6)
        im3[:, :, ind] = im[:, :, ind] / denom  # im3 = im/A (voir formule)
    transmission = 1 - omega * DarkChannel(im3, sz)  # Formule pour trouver la transmission
    return transmission


def Guidedfilter(im, p, r=60, eps=0.0001):
    """Filtre l'image d'entrée (p) sous la direction d'une autre image (im).
    Recherche les coefficients a et b qui minimisent la différence entre la sortie q et l'entrée p."""
    mean_I = cv2.boxFilter(im, cv2.CV_64F, (r, r))
    mean_p = cv2.boxFilter(p, cv2.CV_64F, (r, r))
    mean_Ip = cv2.boxFilter(im * p, cv2.CV_64F, (r, r))
    cov_Ip = mean_Ip - mean_I * mean_p

    mean_II = cv2.boxFilter(im * im, cv2.CV_64F, (r, r))
    var_I = mean_II - mean_I * mean_I

    a = cov_Ip / (var_I + eps)  # calcul de a selon la formule (voir doc)
    b = mean_p - a * mean_I  # calcul de b selon la formule (voir doc)

    mean_a = cv2.boxFilter(a, cv2.CV_64F, (r, r))  # moyenne de a
    mean_b = cv2.boxFilter(b, cv2.CV_64F, (r, r))  # moyenne de b

    q = mean_a * im + mean_b  # transmission affinée
    return q


def TransmissionRefine(im, et, r=60, eps=0.0001):
    """Affinement de la transmission estimée"""
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)  # Image en teinte de gris
    gray = np.float64(gray) / 255
    t = Guidedfilter(gray, et, r, eps)
    return t


def Recover(im, t, A, tx=1.0):
    """Fonction servant à retrouver l'éclat"""
    res = np.empty(im.shape, im.dtype)  # Initialisation du tableau correspondant à l'éclat
    tt = np.zeros((t.shape[0], t.shape[1], 3))  # Initialisation du tableau tt

    tt[:, :, 0] = cv2.max(t, tx)  # blue
    tt[:, :, 1] = cv2.max(t, tx)  # green
    tt[:, :, 2] = cv2.max(t, tx)  # red

    for ind in range(0, 3):
        res[:, :, ind] = (im[:, :, ind] - A[0, ind]) / tt[:, :, ind] + A[0, ind]
    return res


def atm_calculation(II):
    """Calcul de la lumière atmosphérique"""
    srcc = BGR2Float(II)
    dark = DarkChannel(srcc, 15)
    A = AtmLight(srcc, dark)
    return A


def water_calculation(II):
    """Calcul de la lumière atmosphérique pour l'eau"""
    srcc = BGR2Float(II)
    dark = DarkChannelWater(srcc, 15)
    A = AtmLight(srcc, dark)
    return A


def process_image_dehaze(II, A, window=15, omega=0.6, guided_radius=60, guided_eps=0.0001, tx=0.1):
    """Débrumage de l'image"""
    srcc = BGR2Float(II)
    te = TransmissionEstimate(srcc, A, window, omega=omega)
    t = TransmissionRefine(II, te, r=guided_radius, eps=guided_eps)
    III = Recover(srcc, t, A, tx)
    IV = np.clip(III * 255, 0, 255)
    V = np.uint8(IV)
    return V


##############################################
## Denoising et évaluations
##############################################


def denoise_image(image, method="nlm", **kwargs):
    """
    Applique un filtre de débruitage sur l'image d'entrée.
    method -> "nlm" (Fast Non-Local Means) ou "bilateral".
    kwargs sont directement passés à l'appel OpenCV.
    """
    if method == "nlm":
        h = kwargs.get("h", 10)
        h_color = kwargs.get("hColor", 10)
        template_window_size = kwargs.get("templateWindowSize", 7)
        search_window_size = kwargs.get("searchWindowSize", 21)
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h,
            h_color,
            template_window_size,
            search_window_size,
        )
    if method == "bilateral":
        diameter = kwargs.get("diameter", 9)
        sigma_color = kwargs.get("sigmaColor", 75)
        sigma_space = kwargs.get("sigmaSpace", 75)
        return cv2.bilateralFilter(image, diameter, sigma_color, sigma_space)
    raise ValueError(f"Unknown denoise method: {method}")


def denoise_batch(frames, method="nlm", **kwargs):
    """
    Exécute un débruitage image par image pour une série de frames
    (utile pour traiter un dossier de captures).
    """
    return [denoise_image(frame, method=method, **kwargs) for frame in frames]


def tenengrad_contrast(image):
    """Renvoie une mesure de netteté basée sur le gradient de Sobel."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return np.mean(gx**2 + gy**2)


##############################################
## Détection simple (espèces / événements)
##############################################


def init_motion_detector(history=500, var_threshold=16, detect_shadows=True):
    """
    Initialise un soustracteur de fond OpenCV.
    Utile pour repérer des sujets mobiles (poissons, plongeur...).
    """
    return cv2.createBackgroundSubtractorMOG2(
        history=history, varThreshold=var_threshold, detectShadows=detect_shadows
    )


def detect_moving_subjects(frame, subtractor, min_area=400):
    """
    Retourne les contours détectés comme sujets mobiles.
    Renvoie une liste de dictionnaires avec bounding boxes et surfaces.
    """
    fg_mask = subtractor.apply(frame)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        detections.append({"bbox": (x, y, w, h), "area": area})
    return detections


def annotate_detections(frame, detections, color=(0, 255, 0)):
    """Dessine les bounding boxes sur une copie de l'image fournie."""
    annotated = frame.copy()
    for detection in detections:
        x, y, w, h = detection["bbox"]
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
    return annotated


##############################################
## Filtres rapides (Vectorisés)
##############################################


class UnderwaterFilters:
    """
    Collection de filtres rapides (vectorisés) pour améliorer des images sous-marines.
    Les méthodes opèrent sur des frames BGR (numpy.ndarray uint8).
    """

    @staticmethod
    def correct_blue_dominance(frame: np.ndarray, factor: float = 0.12) -> np.ndarray:
        """
        Réduit une dominante bleue en renforçant légèrement les canaux R et G.
        :param factor: intensité de correction (0.12 => +12% sur R/G).
        """
        r, g, b = cv2.split(frame)
        # Optimisation : Utilisation de convertScaleAbs (C++) pour éviter les allocations float lentes
        r = cv2.convertScaleAbs(r, alpha=(1.0 + factor), beta=0)
        g = cv2.convertScaleAbs(g, alpha=(1.0 + factor), beta=0)
        return cv2.merge((r, g, b))

    @staticmethod
    def apply_gamma(frame: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        """
        Correction gamma via table de correspondance.
        gamma > 1 éclaircit les tons moyens.
        """
        gamma = max(gamma, 0.01)
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]).astype("uint8")
        return cv2.LUT(frame, table)

    @staticmethod
    def enhance_contrast(frame: np.ndarray, clip_limit: float = 2.0, tile_grid: tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        Améliore le contraste local via CLAHE sur la luminance (Y dans YCrCb).
        """
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
        y = clahe.apply(y)
        merged = cv2.merge((y, cr, cb))
        return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)

    @staticmethod
    def denoise(frame: np.ndarray, h: float = 10.0) -> np.ndarray:
        """
        Réduit le bruit dans l'image en utilisant la méthode fastNlMeansDenoisingColored de OpenCV.
        """
        # Optimisation : searchWindowSize réduit de 21 à 11 pour tripler la vitesse de calcul
        return cv2.fastNlMeansDenoisingColored(frame, None, h, h, 7, 11)
        # Optimisation extrême : réduction des fenêtres (5, 9) pour maximiser la vitesse
        return cv2.fastNlMeansDenoisingColored(frame, None, h, h, 5, 9)

    @staticmethod
    def sharpen(frame: np.ndarray) -> np.ndarray:
        """Applique un filtre de netteté simple."""
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(frame, -1, kernel)

    @staticmethod
    def apply_contrast_brightness(frame: np.ndarray, contrast: int, brightness: int) -> np.ndarray:
        """Ajuste le contraste et la luminosité. contrast/brightness de -100 à 100."""
        alpha = 1.0 + contrast / 100.0  # Facteur de contraste
        beta = brightness  # Décalage de luminosité
        adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        return adjusted

    @staticmethod
    def apply_saturation(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la saturation. value de -100 à 100."""
        if value == 0: return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        factor = 1.0 + value / 100.0
        s = np.clip(s * factor, 0, 255).astype(np.uint8)
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_hue(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la teinte. value de -90 à 90."""
        if value == 0: return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        # L'échelle de teinte dans OpenCV est 0-179
        h = (h.astype(np.int32) + value) % 180
        hsv = cv2.merge([h.astype(np.uint8), s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_temperature(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la température de couleur. value de -100 (froid) à 100 (chaud)."""
        if value == 0: return frame
        # Convertir la valeur en un ajustement pour les canaux bleu et rouge
        blue_factor = 1.0 - (value / 200.0 if value < 0 else 0)
        red_factor = 1.0 + (value / 200.0 if value > 0 else 0)
        b, g, r = cv2.split(frame)
        b = np.clip(b * blue_factor, 0, 255).astype(np.uint8)
        r = np.clip(r * red_factor, 0, 255).astype(np.uint8)
        return cv2.merge([b, g, r])

    @staticmethod
    def apply_lut(frame: np.ndarray, lut: list) -> np.ndarray:
        """Applique une table de correspondance (Look-Up Table)."""
        if len(lut) != 256: return frame
        table = np.array(lut, dtype=np.uint8)
        return cv2.LUT(frame, table)