"""
MODEL - Gestion des données de l'application KOSMOS (ADAPTÉ)
Import depuis structure de dossiers numérotés (0113, 0114, etc.)
Architecture MVC - Couche Modèle
"""
import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


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
        
        # --- AJOUT ---
        # Heure de début de la vidéo (chargée du JSON, ex: "11:46:54")
        self.start_time_str: str = "00:00:00" 
        # --- FIN AJOUT ---
        
        # Métadonnées communes (système) - non modifiables
        self.metadata_communes = {
            'system': '',
            'camera': '',
            'model': '',
            'version': ''
        }
        
        # Métadonnées propres (campagne) - modifiables
        self.metadata_propres = {
            'campaign': '',
            'zone': '',
            'zone_dict': ''
        }
        
        # État de la vidéo
        self.est_selectionnee = False
        self.est_conservee = True
        
    def to_dict(self) -> Dict:
        """Convertit la vidéo en dictionnaire pour sauvegarde"""
        # --- MODIFIÉ ---
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
            'start_time_str': self.start_time_str  # Ajout de la sauvegarde
        }
        # --- FIN MODIFICATION ---
    
    @staticmethod
    def from_dict(data: Dict) -> 'Video':
        """Crée une vidéo depuis un dictionnaire"""
        video = Video(
            nom=data.get('nom', ''),
            chemin=data.get('chemin', ''),
            dossier_numero=data.get('dossier_numero', ''),
            taille=data.get('taille', ''),
            duree=data.get('duree', ''),
            date=data.get('date', '')
        )
        video.metadata_communes = data.get('metadata_communes', {})
        video.metadata_propres = data.get('metadata_propres', {})
        video.est_conservee = data.get('est_conservee', True)
        
        # --- AJOUT ---
        # Charge l'heure de début sauvegardée, sinon met une valeur par défaut
        video.start_time_str = data.get('start_time_str', "00:00:00")
        # --- FIN AJOUT ---
        
        return video


class Campagne:
    """
    Classe représentant une campagne (étude) avec ses vidéos
    """
    def __init__(self, nom: str, emplacement: str):
        self.nom = nom
        self.emplacement = emplacement
        self.videos: List[Video] = []
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
        campagne.date_creation = data.get('date_creation', '')
        campagne.date_modification = data.get('date_modification', '')
        campagne.videos = [Video.from_dict(v) for v in data.get('videos', [])]
        return campagne
    
    def sauvegarder(self) -> bool:
        """Sauvegarde la campagne dans un fichier JSON"""
        try:
            Path(self.emplacement).mkdir(parents=True, exist_ok=True)
            fichier_config = os.path.join(self.emplacement, f"{self.nom}_config.json")
            
            with open(fichier_config, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
            
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
    
    # ═══════════════════════════════════════════════════════════════
    # IMPORTATION DES VIDÉOS - STRUCTURE KOSMOS
    # ═══════════════════════════════════════════════════════════════
    
    def importer_videos_kosmos(self, dossier_principal: str) -> Dict:
        """
        Importe les vidéos depuis la structure KOSMOS
        """
        self.dossier_videos_import = dossier_principal
        
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
                        # (la valeur par défaut est déjà "00:00:00" grâce au __init__)
                        
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
        
        video = Video(
            nom=nom,
            chemin=chemin,
            dossier_numero=dossier_numero,
            taille=taille,
            duree="--:--",
            date=date_modif
        )
        
        return video
    
    def _charger_metadata_kosmos_csv(self, video: Video, chemin_csv: str) -> bool:
        """
        Charge les métadonnées depuis le CSV KOSMOS
        """
        try:
            with open(chemin_csv, 'r', encoding='utf-8') as f:
                contenu = f.read()
                f.seek(0)
                
                reader = csv.DictReader(f)
                
                for row in reader:
                    for key, value in row.items():
                        key_lower = key.lower()
                        
                        if 'system' in key_lower:
                            video.metadata_communes['system'] = value
                        elif 'camera' in key_lower or 'cam' in key_lower:
                            video.metadata_communes['camera'] = value
                        elif 'model' in key_lower or 'modèle' in key_lower:
                            video.metadata_communes['model'] = value
                        elif 'version' in key_lower:
                            video.metadata_communes['version'] = value
                        
                        elif 'campaign' in key_lower or 'campagne' in key_lower:
                            video.metadata_propres['campaign'] = value
                        elif 'zone' in key_lower:
                            video.metadata_propres['zone'] = value
                        
                        elif 'duree' in key_lower or 'duration' in key_lower:
                            video.duree = value
            
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
                if key in video.metadata_propres:
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

    # --- AJOUTÉ : Méthodes pour les miniatures d'angle ---

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
        premiers événements "START MOTEUR" trouvés...
        
        LOGIQUE CORRIGÉE (v5 - Règle simple) :
        1. Lit systemEvent.csv pour trouver le 'START ENCODER' (temps zéro).
        2. Lit systemEvent.csv à nouveau pour trouver tous les 'START MOTEUR'.
        3. Prend les 6 événements à partir du 10ÈME.
        4. Le temps de début est 5s APRÈS l'événement.
        5. La durée est FIXÉE à 30 secondes.
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
            
            # --- ÉTAPE 1 : Trouver le vrai début de la vidéo (CORRIGÉ) ---
            # On lit le CSV pour trouver le VRAI début (START ENCODER)
            # et on ignore le video.start_time_str (qui vient du JSON)
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

            # --- ÉTAPE 2 : Trouver TOUS les 'START MOTEUR' ---
            motor_event_times = []
            with open(event_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row.get('Event') == 'START MOTEUR':
                        event_seconds = self._parse_time_to_seconds(row['Heure'])
                        if event_seconds >= video_start_seconds:
                            motor_event_times.append(event_seconds)
            
            # --- ÉTAPE 3 : Sélectionner (à partir du 10e) et fixer la durée ---
            
            START_INDEX = 9 # (Index 9 = 10ème événement)
            NUM_PREVIEWS = 6
            PREVIEW_DURATION_SEC = 30 # Votre demande
            START_OFFSET_SEC = 5      # Votre demande
            
            if len(motor_event_times) < START_INDEX + 1:
                print(f"   ... Moins de 10 'START MOTEUR' trouvés (seulement {len(motor_event_times)}).")
                return default_result
                
            results = []
            
            # On prend les 6 événements à partir du 10e
            events_to_process = motor_event_times[START_INDEX : START_INDEX + NUM_PREVIEWS] 
            
            # S'il n'y a pas 6 événements (ex: on a le 10e, 11e mais c'est tout)
            if len(events_to_process) < NUM_PREVIEWS:
                print(f"   ... Info: Moins de 6 événements trouvés après le 10e. Duplication du dernier.")
                while len(events_to_process) < NUM_PREVIEWS:
                    events_to_process.append(events_to_process[-1])
            
            for event_abs_time in events_to_process:
                
                # Temps de début de l'extrait (avec +5s de décalage)
                seek_start_abs_time = event_abs_time + START_OFFSET_SEC
                
                # Calcul final du temps de début relatif à la vidéo
                seek_start_relative_sec = seek_start_abs_time - video_start_seconds
                if seek_start_relative_sec < 0: seek_start_relative_sec = 0
                
                m, s = divmod(seek_start_relative_sec, 60)
                h, m = divmod(m, 60)
                seek_start_str = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                
                # La durée est fixe
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
    
    # resultats = model.importer_videos_kosmos("/chemin/vers/dossier_principal")
    
    print("✅ Tests terminés!")