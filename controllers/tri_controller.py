"""
CONTRÔLEUR - Page de tri KOSMOS
Architecture MVC
"""
import sys
import csv
import json
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
        # Fallback : essayer avec le nom de fichier de base si pas trouvé directement
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
    
    def supprimer_video(self, nom_video: str):
        """Marque une vidéo pour suppression"""
        return self.model.marquer_video_pour_suppression(nom_video)
    
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
            
            # Vérification que le fichier a bien été modifié
            if json_path.exists():
                file_size = json_path.stat().st_size
                mod_time = datetime.fromtimestamp(json_path.stat().st_mtime).strftime("%H:%M:%S")
                print(f"✅ Métadonnées vidéo sauvegardées dans: {json_path}")
                print(f"   📄 Taille du fichier: {file_size} octets")
                print(f"   🕒 Heure de modification: {mod_time}")
                
                # Vérifier que les données ont bien été écrites
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        verification_data = json.load(f)
                    
                    video_count = len(verification_data.get('video', {}))
                    print(f"   🔍 Sections video vérifiées: {video_count} sections trouvées")
                    
                    # Afficher quelques exemples de métadonnées sauvegardées
                    if 'video' in verification_data:
                        for section_name, section_data in list(verification_data['video'].items())[:3]:
                            if isinstance(section_data, dict) and section_data:
                                example_key = list(section_data.keys())[0]
                                example_value = section_data[example_key]
                                print(f"   📝 Exemple - {section_name}.{example_key}: {example_value}")
                
                except Exception as e:
                    print(f"   ⚠️ Erreur vérification: {e}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde JSON: {e}")
            return False
    
    def creer_structure_json_vide(self) -> dict:
        """Crée une structure JSON vide avec les sections par défaut"""
        return {
            "system": {
                "system": "",
                "camera": "",
                "model": "",
                "version": ""
            },
            "campaign": {
                "zoneDict": {
                    "campaign": "",
                    "zone": ""
                },
                "video": {
                    "analyseDict": {},
                    "astroDict": {},
                    "ctdDict": {},
                    "gpsDict": {},
                    "hourDict": {},
                    "meteoAirDict": {},
                    "meteoMerDict": {},
                    "stationDict": {}
                }
            }
        }
    
    def creer_json_defaut(self, json_path: Path):
        """Crée un fichier JSON par défaut s'il n'existe pas"""
        try:
            data = self.creer_structure_json_vide()
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"📄 Fichier JSON par défaut créé: {json_path}")
        except Exception as e:
            print(f"❌ Erreur création JSON par défaut: {e}")

    def modifier_metadonnees_propres(self, nom_video: str, metadonnees: dict, nom_utilisateur: str = "User"):
        """Modifie uniquement les métadonnées propres à la vidéo (section video du JSON)"""
        video = self.model.campagne_courante.obtenir_video(nom_video)
        if video:
            # Mettre à jour les métadonnées propres
            for key, value in metadonnees.items():
                video.metadata_propres[key] = value
            
            return self.sauvegarder_metadonnees_vers_json(video, nom_utilisateur)
        return False
    
    def get_video_by_name(self, nom_video: str):
        """Retourne l'objet vidéo via le modèle courant."""
        getter = getattr(self.model.campagne_courante, "obtenir_video", None)
        return getter(nom_video) if callable(getter) else None

    def get_metadata(self, nom_video: str):
        """Retourne (communes: dict, propres: dict) pour affichage dans la vue."""
        v = self.get_video_by_name(nom_video)
        if not v:
            return {}, {}
        commons = getattr(v, "metadata_communes", {}) or {}
        specifics = getattr(v, "metadata_propres", {}) or {}
        return commons, specifics
    
    def obtenir_premiere_video(self):
        """Retourne la première vidéo de la liste pour l'affichage initial"""
        videos = self.obtenir_videos()
        if videos:
            return videos[0]
        return None
    
    def obtenir_toutes_metadonnees(self, nom_video: str):
        """Retourne toutes les métadonnées (communes + propres) d'une vidéo"""
        video = self.get_video_by_name(nom_video)
        if not video:
            return {}
        
        # Fusionner toutes les métadonnées avec préfixe pour éviter les conflits
        toutes_meta = {}
        
        # Métadonnées communes
        meta_communes = getattr(video, "metadata_communes", {}) or {}
        for key, value in meta_communes.items():
            toutes_meta[f"communes_{key}"] = value
            
        # Métadonnées propres  
        meta_propres = getattr(video, "metadata_propres", {}) or {}
        for key, value in meta_propres.items():
            toutes_meta[f"propres_{key}"] = value
            
        # Informations de base de la vidéo
        toutes_meta["nom"] = getattr(video, "nom", "")
        toutes_meta["chemin"] = getattr(video, "chemin", "")
        toutes_meta["taille"] = getattr(video, "taille", "")
        toutes_meta["duree"] = getattr(video, "duree", "")
        toutes_meta["date"] = getattr(video, "date", "")
        
        return toutes_meta

    def get_angle_seek_times(self, nom_video: str):
        """
        Retourne une liste de 6 tuples (start_time_str, duration_sec)
        pour l'extraction des miniatures/GIFs côté vue.
        Par défaut : 1 point toutes les 30s, GIF de 3s.
        """
        seek = []
        for i in range(6):  # 0..5
            t = i * 30
            h = t // 3600
            m = (t % 3600) // 60
            s = t % 60
            seek.append((f"{h:02d}:{m:02d}:{s:02d}", 3))
        return seek
    
    def sauvegarder_csv(self, video, create_if_missing: bool = True) -> bool:
        """ Met à jour dans <dossier>/<dossier_numero>.csv UNIQUEMENT la ligne correspondant à 'video'.
        - Identifiant privilégié: colonne 'file' (nom de fichier). Fallbacks: 'filename', 'name', 'path', 'video'.
        - create_if_missing=True : crée un CSV minimal si absent (file, path, label + colonnes présentes dans les métadonnées).
        - Écriture atomique pour éviter la corruption.
        """
        try:
            if not getattr(video, "chemin", None):
                print("❌ Erreur sauvegarde CSV: video.chemin manquant")
                return False

            dossier = Path(video.chemin).parent
            dossier_num = getattr(video, "dossier_numero", None) or dossier.name
            csv_path = dossier / f"{dossier_num}.csv"

            meta_communes = getattr(video, "metadata_communes", {}) or {}
            meta_propres  = getattr(video, "metadata_propres", {}) or {}
            label_val     = getattr(video, "label", "") or ""

            # 1) Création si le CSV n'existe pas
            if not csv_path.exists():
                if not create_if_missing:
                    print(f"⚠️ CSV non trouvé: {csv_path}")
                    return False

                base_fields  = ["file", "path", "label"]
                extra_fields = sorted(set(list(meta_communes.keys()) + list(meta_propres.keys())))
                fieldnames   = base_fields + extra_fields

                from tempfile import NamedTemporaryFile
                tmp = NamedTemporaryFile("w", delete=False, encoding="utf-8", newline="")
                try:
                    with tmp as tf:
                        writer = csv.DictWriter(tf, fieldnames=fieldnames)
                        writer.writeheader()

                        row = {k: "" for k in fieldnames}
                        row["file"]  = Path(video.chemin).name
                        row["path"]  = str(Path(video.chemin).resolve())
                        row["label"] = str(label_val or "")

                        for k, v in meta_communes.items():
                            if k in row:
                                row[k] = str(v or "")
                        for k, v in meta_propres.items():
                            if k in row:
                                row[k] = str(v or "")

                        writer.writerow(row)

                    Path(tmp.name).replace(csv_path)
                finally:
                    try:
                        Path(tmp.name).unlink(missing_ok=True)
                    except Exception:
                        pass

                print(f"🆕 CSV créé: {csv_path}")
                return True

            # 2) Lecture & mise à jour d'un CSV existant
            with open(csv_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])  # Convertir en liste modifiable
                rows = list(reader)

            filename = Path(video.chemin).name
            path_abs = str(Path(video.chemin).resolve())
            # Priorité aux colonnes standards, puis colonnes spécialisées (HMS, TStamp, etc.)
            candidates = [
                ("file", filename),
                ("filename", filename),
                ("name", filename),
                ("video", filename),
                ("path", path_abs),
                ("HMS", ""),  # Colonne temps pour données scientifiques
                ("TStamp", ""), # Timestamp pour données d'acquisition
            ]

            key_field = key_value = None
            for k, v in candidates:
                if k in fieldnames:
                    if v:  # Si on a une valeur à chercher
                        key_field, key_value = k, v
                        break
                    elif k in ["HMS", "TStamp"]:  # Colonnes scientifiques : utiliser comme identifiant principal
                        key_field = k
                        # Pour les données scientifiques, on ajoute toujours une nouvelle ligne
                        key_value = f"nouvelle_entree_{len(rows)}"
                        break
            
            # Si aucun champ identifiant trouvé, ajouter la colonne 'file' au CSV
            if not key_field:
                print(f"⚠️ Aucun champ identifiant trouvé dans {csv_path}. Ajout de la colonne 'file'.")
                fieldnames.append('file')
                key_field, key_value = 'file', filename
                # Ajouter la colonne 'file' à toutes les lignes existantes
                for row in rows:
                    row['file'] = ""

            found = False
            new_rows = []
            for row in rows:
                if str(row.get(key_field, "")).strip() == str(key_value or "").strip():
                    # Mettre à jour uniquement les colonnes existantes
                    for k, v in meta_communes.items():
                        if k in row:
                            row[k] = str(v or "")
                    for k, v in meta_propres.items():
                        if k in row:
                            row[k] = str(v or "")
                    new_rows.append(row)
                    found = True
                else:
                    new_rows.append(row)

            # Si aucune ligne trouvée → en ajouter une
            if not found:
                base = {k: "" for k in fieldnames}
                base[key_field] = str(key_value or "")
                for k, v in meta_communes.items():
                    if k in base:
                        base[k] = str(v or "")
                for k, v in meta_propres.items():
                    if k in base:
                        base[k] = str(v or "")
                new_rows.append(base)

            # Écriture atomique
            from tempfile import NamedTemporaryFile
            tmp = NamedTemporaryFile("w", delete=False, encoding="utf-8", newline="")
            try:
                with tmp as tf:
                    writer = csv.DictWriter(tf, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(new_rows)
                Path(tmp.name).replace(csv_path)
            finally:
                try:
                    Path(tmp.name).unlink(missing_ok=True)
                except Exception:
                    pass

            print(f"✅ CSV sauvegardé: {csv_path}")
            return True

        except Exception as e:
            print(f"❌ Erreur sauvegarde CSV: {e}")
            return False

    def show_success_dialog(self, parent_view):
        """
        Affiche une boîte de dialogue de confirmation après modification des métadonnées.
        """
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            parent_view,
            "Succès",
            "Les métadonnées ont été modifiées avec succès !",
        )
