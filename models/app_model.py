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
        return {
            'nom': self.nom,
            'chemin': self.chemin,
            'dossier_numero': self.dossier_numero,
            'taille': self.taille,
            'duree': self.duree,
            'date': self.date,
            'metadata_communes': self.metadata_communes,
            'metadata_propres': self.metadata_propres,
            'est_conservee': self.est_conservee
        }
    
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
        
        Structure attendue:
        dossier_principal/
        ├── 0113/
        │   ├── 0113.csv
        │   ├── 0113.json
        │   ├── 0113.txt
        │   ├── systemEvent.csv
        │   └── video.mp4 (ou autre)
        ├── 0114/
        │   └── ...
        
        Args:
            dossier_principal: Dossier contenant les sous-dossiers numérotés
            
        Returns:
            Dictionnaire avec les résultats de l'importation
        """
        self.dossier_videos_import = dossier_principal
        
        resultats = {
            'videos_importees': [],
            'videos_sans_metadata': [],
            'erreurs': []
        }
        
        # Extensions vidéo supportées (minuscules et majuscules)
        extensions_video = ('.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI', '.MOV', '.MKV', 
                           '.h264', '.H264', '.mpg', '.MPG', '.mpeg', '.MPEG')
        
        print(f"\n{'='*60}")
        print(f"📹 IMPORTATION KOSMOS")
        print(f"{'='*60}")
        print(f"📁 Dossier principal : {dossier_principal}")
        
        try:
            # Lister tous les éléments du dossier principal
            tous_elements = os.listdir(dossier_principal)
            print(f"📂 {len(tous_elements)} éléments trouvés dans le dossier principal")
            
            # Filtrer les sous-dossiers
            sous_dossiers = [d for d in tous_elements 
                           if os.path.isdir(os.path.join(dossier_principal, d))]
            
            print(f"📁 {len(sous_dossiers)} sous-dossiers identifiés")
            
            # Afficher les 5 premiers dossiers
            for i, dossier in enumerate(sous_dossiers[:5]):
                print(f"   {i+1}. {dossier}")
            if len(sous_dossiers) > 5:
                print(f"   ... et {len(sous_dossiers) - 5} autres")
            
            if not sous_dossiers:
                # Peut-être que les vidéos sont directement dans le dossier principal ?
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
            
            # Parcourir chaque sous-dossier
            for nom_dossier in sous_dossiers:
                chemin_dossier = os.path.join(dossier_principal, nom_dossier)
                print(f"\n🔍 Analyse de : {nom_dossier}")
                
                try:
                    # Lister tous les fichiers du sous-dossier
                    fichiers = os.listdir(chemin_dossier)
                    print(f"   📄 {len(fichiers)} fichier(s) trouvé(s)")
                    
                    # Afficher tous les fichiers pour debug
                    for fichier in fichiers[:10]:
                        ext = os.path.splitext(fichier)[1]
                        print(f"      - {fichier} [{ext}]")
                    if len(fichiers) > 10:
                        print(f"      ... et {len(fichiers) - 10} autres fichiers")
                    
                    # Chercher les vidéos avec n'importe quelle extension
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
                        print(f"      📹 {nom_video}")
                        chemin_video = os.path.join(chemin_dossier, nom_video)
                        
                        # Créer l'objet vidéo
                        video = self._creer_video_depuis_fichier(chemin_video, nom_dossier)
                        
                        # Charger les métadonnées depuis le CSV du dossier
                        chemin_csv = os.path.join(chemin_dossier, f"{nom_dossier}.csv")
                        
                        if os.path.exists(chemin_csv):
                            print(f"         📊 CSV trouvé : {nom_dossier}.csv")
                            if self._charger_metadata_kosmos_csv(video, chemin_csv):
                                resultats['videos_importees'].append(video.nom)
                            else:
                                resultats['videos_sans_metadata'].append(video.nom)
                        else:
                            print(f"         ⚠️ Pas de CSV trouvé")
                            resultats['videos_sans_metadata'].append(video.nom)
                        
                        # Ajouter la vidéo à la campagne
                        if self.campagne_courante:
                            self.campagne_courante.ajouter_video(video)
                
                except Exception as e:
                    print(f"   ❌ Erreur dans {nom_dossier} : {e}")
                    resultats['erreurs'].append(f"Erreur dans {nom_dossier}: {e}")
            
            print(f"\n{'='*60}")
            print(f"📊 RÉSULTATS")
            print(f"{'='*60}")
            print(f"✅ Vidéos importées : {len(resultats['videos_importees'])}")
            print(f"⚠️  Sans métadonnées : {len(resultats['videos_sans_metadata'])}")
            print(f"❌ Erreurs : {len(resultats['erreurs'])}")
            print(f"{'='*60}\n")
                        
        except Exception as e:
            resultats['erreurs'].append(f"Erreur globale : {e}")
            print(f"❌ Erreur globale : {e}")
        
        return resultats
    
    def _creer_video_depuis_fichier(self, chemin: str, dossier_numero: str) -> Video:
        """Crée un objet Video à partir d'un fichier"""
        nom = os.path.basename(chemin)
        
        # Informations du fichier
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
        
        Le format du CSV KOSMOS peut varier. On essaie de parser intelligemment.
        
        Args:
            video: Objet Video à enrichir
            chemin_csv: Chemin vers le fichier CSV
            
        Returns:
            True si succès, False sinon
        """
        try:
            with open(chemin_csv, 'r', encoding='utf-8') as f:
                # Essayer de détecter le format
                contenu = f.read()
                f.seek(0)
                
                # Si le CSV a un header
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Adapter selon les colonnes présentes
                    # Exemple de mapping possible
                    for key, value in row.items():
                        key_lower = key.lower()
                        
                        # Métadonnées communes
                        if 'system' in key_lower:
                            video.metadata_communes['system'] = value
                        elif 'camera' in key_lower or 'cam' in key_lower:
                            video.metadata_communes['camera'] = value
                        elif 'model' in key_lower or 'modèle' in key_lower:
                            video.metadata_communes['model'] = value
                        elif 'version' in key_lower:
                            video.metadata_communes['version'] = value
                        
                        # Métadonnées propres
                        elif 'campaign' in key_lower or 'campagne' in key_lower:
                            video.metadata_propres['campaign'] = value
                        elif 'zone' in key_lower:
                            video.metadata_propres['zone'] = value
                        
                        # Durée
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


# Test du modèle
if __name__ == '__main__':
    print("🧪 Test du modèle KOSMOS adapté...")
    
    model = ApplicationModel()
    
    # Créer une campagne
    campagne = model.creer_campagne("Test_KOSMOS", "./test_campagne")
    print(f"✅ Campagne créée : {campagne.nom}")
    
    # Simuler l'import (nécessite un vrai dossier pour tester)
    # resultats = model.importer_videos_kosmos("/chemin/vers/dossier_principal")
    
    print("✅ Tests terminés!")