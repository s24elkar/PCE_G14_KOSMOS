"""
CONTRÔLEUR - Page d'extraction KOSMOS
Architecture MVC
Gère la logique de la page d'extraction (lecture, navigation, outils)
"""
import datetime
import csv 
import json
import sys
import cv2
import numpy as np
import subprocess
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

# Ajout du chemin racine pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.app_model import UnderwaterFilters

class ExtractionKosmosController(QObject):
    """
    Contrôleur pour la page d'extraction.
    Gère les interactions entre la vue ExtractionView et le modèle ApplicationModel.
    """
    
    # Signal pour demander à l'application principale de changer de page
    navigation_demandee = pyqtSignal(str)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None # Sera défini lors de l'initialisation de la vue
        
        # État local pour les corrections
        self.brightness = 0
        self.contrast = 0
        self.pending_capture_name = None # Pour stocker le nom de la capture
        
    def set_view(self, view):
        """Associe la vue à ce contrôleur"""
        self.view = view
        
        # Afficher la première vidéo conservée au lancement de la page Extraction
        if self.view and hasattr(self.view, 'view_shown'):
            self.view.view_shown.connect(self.load_first_video)

    def load_first_video(self):
        """
        Charge la première vidéo marquée comme "conservée" dans le lecteur.
        Cette méthode est appelée lorsque la page d'extraction devient visible.
        """
        if not self.model.campagne_courante:
            return

        videos_conservees = self.model.campagne_courante.obtenir_videos_conservees()
        if videos_conservees:
            premiere_video = videos_conservees[0]
            print(f"📹 Chargement de la première vidéo conservée : {premiere_video.nom}")
            self.charger_video_dans_lecteur(premiere_video)

    def load_initial_data(self):
        """
        Charge les données initiales dans la vue au démarrage.
        Récupère la liste des vidéos du modèle et met à jour l'explorateur.
        """
        if not self.view:
            return

        # Récupérer les vidéos de la campagne courante
        videos = self.model.obtenir_videos()
        
        # Formater pour la vue (l'explorateur attend une liste de dicts)
        videos_data = []
        for vid in videos:
            # Générer la miniature de la vidéo
            thumbnail_pixmap = self._generer_miniature_video(vid.chemin)
            color = "#00CBA9" if vid.est_conservee else "#FF6B6B"
            videos_data.append({
                'name': vid.nom,
                'thumbnail_pixmap': thumbnail_pixmap,
                'thumbnail_color': color
            })
            
        # Mettre à jour la liste dans la vue
        self.view.update_video_list(videos_data)
        
        # Si une vidéo était déjà sélectionnée dans le modèle, on la charge
        if self.model.video_selectionnee:
            self.charger_video_dans_lecteur(self.model.video_selectionnee)

    # ═══════════════════════════════════════════════════════════════
    # GESTION DE LA NAVIGATION ET SÉLECTION
    # ═══════════════════════════════════════════════════════════════

    def on_tab_changed(self, tab_name):
        """Gère le changement d'onglet via la navbar"""
        # Mapping des noms d'onglets vers les IDs de pages
        tabs_map = {
            "Fichier": "accueil",
            "Tri": "tri",
            "Extraction": "extraction",
            "Évènements": "evenements"
        }
        if tab_name in tabs_map:
            self.navigation_demandee.emit(tabs_map[tab_name])

    def on_video_selected(self, video_name):
        """
        Appelé quand une vidéo est cliquée dans l'explorateur.
        Met à jour le modèle et demande à la vue de charger la vidéo.
        """
        # Mettre à jour le modèle
        video = self.model.selectionner_video(video_name)
        
        if video:
            self.charger_video_dans_lecteur(video)
        else:
            print(f"❌ Erreur: Vidéo '{video_name}' non trouvée dans le modèle.")

    def charger_video_dans_lecteur(self, video):
        """Prépare les données de la vidéo et met à jour le lecteur de la vue"""
        if not self.view:
            return

        # Utilisation des méthodes du modèle (Video) pour charger les données
        video.charger_metadonnees_propres_json()
        video.charger_metadonnees_communes_json()
        video.charger_donnees_timeseries_csv()
        

        # Préparer les métadonnées STATIQUES pour l'affichage.
        # On ne passe QUE le temps de départ. Le reste (temp, pression, lux)
        # sera géré dynamiquement par le lecteur à partir des données CSV.
        metadata_display = {
            "time": video.start_time_str,
        }

        video_data = {
            'path': video.chemin,
            'metadata': metadata_display,
            'timeseries_data': video.timeseries_data 
        }

        # Demander à la vue de charger cette vidéo
        self.view.update_video_player(video_data)

    # ═══════════════════════════════════════════════════════════════
    # CONTRÔLE DU LECTEUR
    # ═══════════════════════════════════════════════════════════════
        
    def on_play_pause(self):
        """Gère le bouton Play/Pause"""
        print("⏯️ Play/Pause demandé")

    def on_position_changed(self, position):
        """Gère le changement de position (slider)"""
        pass

    def on_previous_video(self):
        """Passe à la vidéo précédente dans la liste"""
        self._naviguer_video(-1)

    def on_next_video(self):
        """Passe à la vidéo suivante dans la liste"""
        self._naviguer_video(1)

    def on_rewind(self):
        """Recule de X secondes"""
        print("⏪ Retour arrière")

    def on_forward(self):
        """Avance de X secondes"""
        print("⏩ Avance rapide")

    def _naviguer_video(self, direction):
        """Logique interne pour changer de vidéo (précédente/suivante)"""
        videos = self.model.obtenir_videos()
        if not videos or not self.model.video_selectionnee:
            return

        current_name = self.model.video_selectionnee.nom
        
        # Trouver l'index actuel
        try:
            current_idx = -1
            for i, v in enumerate(videos):
                if v.nom == current_name:
                    current_idx = i
                    break
            
            if current_idx != -1:
                new_idx = (current_idx + direction) % len(videos)
                new_video = videos[new_idx]
                # Simuler un clic pour déclencher toute la chaîne de mise à jour
                self.on_video_selected(new_video.nom)
                
        except ValueError:
            pass

    # ═══════════════════════════════════════════════════════════════
    # CORRECTION D'IMAGE
    # ═══════════════════════════════════════════════════════════════

    def on_contrast_changed(self, value):
        """Gère le slider de contraste"""
        self.contrast = value
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast_base', UnderwaterFilters.apply_contrast_brightness, value != 0 or self.brightness != 0, contrast=self.contrast, brightness=self.brightness)

    def on_brightness_changed(self, value):
        """Gère le slider de luminosité"""
        self.brightness = value
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast_base', UnderwaterFilters.apply_contrast_brightness, self.contrast != 0 or value != 0, contrast=self.contrast, brightness=self.brightness)

    def on_color_correction(self):
        """Ouvre ou applique la correction colorimétrique automatique"""
        if not self.view or not hasattr(self.view, 'video_player'):
            return

        # Appliquer une chaîne de filtres par défaut
        self.view.video_player.toggle_filter('gamma', UnderwaterFilters.apply_gamma, True, gamma=1.2)
        self.view.video_player.toggle_filter('blue_correction', UnderwaterFilters.correct_blue_dominance, True, factor=0.15)
        self.view.video_player.toggle_filter('contrast', UnderwaterFilters.enhance_contrast, True, clip_limit=1.5)
        
        # Mettre à jour l'état des boutons de filtre dans le composant ImageCorrection
        self.view.image_correction.update_filter_buttons_state({
            'gamma': True,
            'blue_correction': True,
            'contrast': True,
            'denoise': self.view.video_player.is_filter_active('denoise'),
            'sharpen': self.view.video_player.is_filter_active('sharpen')
        })
        self.view.show_message("Correction automatique appliquée.", "success")

    def on_toggle_gamma(self, toggled):
        """Active ou désactive la correction gamma."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('gamma', UnderwaterFilters.apply_gamma, toggled, gamma=1.2)

    def on_toggle_contrast(self, toggled):
        """Active ou désactive l'amélioration du contraste."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast', UnderwaterFilters.enhance_contrast, toggled, clip_limit=1.5)

    def on_toggle_denoise(self, toggled):
        """Active ou désactive la réduction de bruit."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('denoise', UnderwaterFilters.denoise, toggled, h=10.0)

    def on_toggle_sharpen(self, toggled):
        """Active ou désactive le filtre de netteté."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('sharpen', UnderwaterFilters.sharpen, toggled)

    def on_reset_filters(self):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.reset_filters()

    def on_saturation_changed(self, value):
        """Gère le slider de saturation."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('saturation', UnderwaterFilters.apply_saturation, value != 0, value=value)

    def on_hue_changed(self, value):
        """Gère le slider de teinte."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('hue', UnderwaterFilters.apply_hue, value != 0, value=value)

    def on_temperature_changed(self, value):
        """Gère le slider de température."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('temperature', UnderwaterFilters.apply_temperature, value != 0, value=value)

    def on_curve_changed(self, lut):
        """Gère le changement de la courbe tonale."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('curve', UnderwaterFilters.apply_lut, True, lut=lut)

    # ═══════════════════════════════════════════════════════════════
    # OUTILS D'EXTRACTION
    # ═══════════════════════════════════════════════════════════════

    def on_screenshot(self):
        """Active le mode de sélection sur le lecteur vidéo pour une capture d'écran."""
        if not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return
        
        if not self.view or not hasattr(self.view, 'video_player'):
            return
            
        # Demander le type de capture à la vue
        capture_type = self.view.ask_screenshot_type()
        
        if capture_type == "full":
            # Capture de l'image complète
            self.view.video_player.grab_frame(None)
        elif capture_type == "crop":
            # Sélection d'une zone
            self.on_crop()

    def on_crop(self):
        """Active le mode de recadrage sur le lecteur vidéo."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.show_message("Dessinez un rectangle sur la vidéo pour capturer une zone.", "info")
            self.view.video_player.start_cropping()

    def on_crop_area_selected(self, crop_rect):
        """Slot appelé lorsque l'utilisateur a sélectionné une zone à capturer."""
        # Demande au lecteur de capturer l'image, en lui passant la zone à recadrer.
        self.view.video_player.grab_frame(crop_rect)

    def save_captured_frame(self, frame: 'QPixmap'):
        """
        Reçoit le QPixmap (déjà recadré si nécessaire), demande un nom à l'utilisateur,
        puis sauvegarde l'image.
        """
        if not frame:
            self.view.show_message("Impossible de capturer l'image de la vidéo.", "error")
            return

        # 1. Demander le nom de la capture à la vue
        capture_name = self.view.ask_capture_name()

        if not capture_name:
            self.view.show_message("Capture annulée.", "info")
            return

        self.pending_capture_name = capture_name

        # 2. Définir le chemin de sauvegarde
        workspace = self.model.campagne_courante.workspace_extraction
        if not workspace:
            self.view.show_message("Dossier d'extraction non défini pour la campagne.", "error")
            return

        # Créer un sous-dossier "captures" pour une meilleure organisation
        captures_dir = Path(workspace) / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)

        # 3. Utiliser le nom fourni par l'utilisateur
        filename = f"{self.pending_capture_name}.png"
        save_path = captures_dir / filename

        # 4. Sauvegarder l'image (qui est déjà recadrée)
        try:
            frame.save(str(save_path), "png", -1)
            self.view.show_message(f"Capture enregistrée : {filename}", "success")
            print(f"📸 Capture d'écran enregistrée sous : {save_path}")
        except Exception as e:
            self.view.show_message(f"Erreur lors de la sauvegarde : {e}", "error")
            print(f"❌ Erreur sauvegarde capture : {e}")
        finally:
            # Réinitialiser le nom pour la prochaine capture
            self.pending_capture_name = None
            
    def _export_video_with_filters(self, source_path, output_path, start_ms, end_ms):
        """
        Exporte une portion de vidéo en appliquant les filtres actifs via OpenCV
        et en encodant via FFmpeg (pipe).
        """
        import cv2
        
        cap = cv2.VideoCapture(str(source_path))
        if not cap.isOpened():
            raise Exception("Impossible d'ouvrir la vidéo source")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        cap.set(cv2.CAP_PROP_POS_MSEC, start_ms)
        
        duration_ms = end_ms - start_ms
        duration_s = duration_ms / 1000.0
        frames_to_process = int(duration_s * fps)
        
        start_str = str(datetime.timedelta(milliseconds=start_ms))

        cmd = [
            'ffmpeg', '-y',
            '-loglevel', 'error', # Réduire la verbosité pour éviter le blocage du pipe stderr
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'bgr24',
            '-r', str(fps),
            '-i', '-', 
            '-ss', start_str,
            '-i', str(source_path),
            '-t', str(duration_s),
            '-map', '0:v',
            '-map', '1:a?', # Audio optionnel
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ]
        
        print(f"🚀 Commande FFmpeg: {' '.join(cmd)}")
        
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
            
        process = subprocess.Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            creationflags=creation_flags
        )
        
        filters = []
        if self.view and hasattr(self.view, 'video_player'):
            filters = self.view.video_player.active_filters
            
        print(f"🎬 Export avec filtres ({len(filters)} actifs)...")
        
        try:
            count = 0
            while count < frames_to_process:
                # Garder l'interface réactive
                QApplication.processEvents()
                
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Appliquer les filtres
                if filters:
                    for name, (filter_func, kwargs) in filters.items():
                        try:
                            frame = filter_func(frame, **kwargs)
                        except Exception as e:
                            print(f"⚠️ Erreur filtre {name}: {e}")
                
                # Écrire dans le pipe
                try:
                    process.stdin.write(frame.tobytes())
                except IOError as e:
                    print(f"❌ Erreur écriture pipe: {e}")
                    break
                    
                count += 1
                
        finally:
            cap.release()
            if process.stdin:
                process.stdin.close()
            
            # Attendre la fin du processus et récupérer stderr
            stdout_data, stderr_data = process.communicate()
            
            if process.returncode != 0:
                stderr_output = stderr_data.decode('utf-8', errors='replace') if stderr_data else "Erreur inconnue"
                print(f"❌ Erreur FFmpeg (code {process.returncode}): {stderr_output}")
                raise Exception(f"Erreur lors de l'encodage FFmpeg: {stderr_output[-200:]}")
            else:
                print("✅ Export FFmpeg terminé avec succès.")

    def on_recording(self):
        """Démarre/Arrête l'enregistrement d'un extrait"""
        if not self.view or not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

        # Calculer la position actuelle en fonction de la frame courante
        video_thread = self.view.video_player.video_thread
        if video_thread.total_frames == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return
            
        current_pos_ms = int((video_thread.current_frame / video_thread.fps) * 1000)
        duration_ms = self.view.video_player.duration

        if duration_ms == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return

        # 1. Définir la plage de sélection initiale (position actuelle + 30s)
        initial_start_ms = current_pos_ms
        initial_end_ms = min(duration_ms, current_pos_ms + 30000)

        # 2. Ouvrir la fenêtre d'édition via la vue
        result = self.view.open_clip_editor(
            self.model.video_selectionnee.chemin,
            initial_start_ms,
            initial_end_ms
        )

        # 3. Si l'utilisateur a validé, créer l'extrait final
        if not result:
            self.view.show_message("Enregistrement annulé.", "info")
            return

        try:
            rec_name, final_start_ms, final_end_ms = result
            
            final_start_str = str(datetime.timedelta(milliseconds=final_start_ms))
            final_duration_s = (final_end_ms - final_start_ms) / 1000

            recordings_dir = Path(self.model.campagne_courante.workspace_extraction) / "recordings"
            recordings_dir.mkdir(parents=True, exist_ok=True)
            final_output_path = recordings_dir / f"{rec_name}.mp4"

            self.view.show_message("Enregistrement de l'extrait final...", "info")
            
            # Utiliser la nouvelle méthode d'export avec filtres
            self._export_video_with_filters(
                self.model.video_selectionnee.chemin,
                final_output_path,
                final_start_ms,
                final_end_ms
            )
            
            self.view.show_message(f"Enregistrement '{rec_name}.mp4' sauvegardé !", "success")
        except Exception as e:
            self.view.show_message(f"Erreur enregistrement final: {e}", "error")
                    
    def on_create_short(self):
        """Crée un short (extrait court format vertical ou spécifique)"""
        if not self.view or not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

        # 1. Obtenir la position actuelle et la durée totale
        player = self.view.video_player
        video_thread = player.video_thread
        
        if video_thread.total_frames == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return
            
        current_pos_ms = int((video_thread.current_frame / video_thread.fps) * 1000)
        total_duration_ms = player.duration

        if total_duration_ms == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return

        # 2. Demander à l'utilisateur de choisir la durée du short via la vue
        durations = ["10 secondes", "20 secondes", "30 secondes"]
        selected_duration_str = self.view.ask_short_duration(durations)

        if not selected_duration_str:
            self.view.show_message("Création du short annulée.", "info")
            return

        # Extraire la durée en secondes (ex: "10 secondes" -> 10)
        clip_duration_s = int(selected_duration_str.split()[0])

        # 3. Calculer les temps de début et de fin en fonction de la durée choisie
        start_ms = max(0, current_pos_ms - (clip_duration_s * 1000 // 2))
        end_ms = min(total_duration_ms, start_ms + (clip_duration_s * 1000))
        clip_duration_s = (end_ms - start_ms) / 1000

        # Convertir en format HH:MM:SS.ms pour ffmpeg
        start_time_str = str(datetime.timedelta(milliseconds=start_ms))

        # 3. Définir les chemins temporaires
        extraction_dir = Path(self.model.campagne_courante.workspace_extraction)
        shorts_dir = extraction_dir / "shorts"
        shorts_dir.mkdir(parents=True, exist_ok=True)
        
        temp_filtered_path = shorts_dir / f"~temp_filtered.mp4"
        temp_preview_path = shorts_dir / f"~preview_temp.mp4"

        # 4. Créer un aperçu accéléré avec filtres
        try:
            self.view.show_message("Génération de l'aperçu avec filtres...", "info")
            
            # Étape 1: Générer le clip filtré à vitesse normale
            end_ms = start_ms + int(clip_duration_s * 1000)
            self._export_video_with_filters(
                self.model.video_selectionnee.chemin,
                temp_filtered_path,
                start_ms,
                end_ms
            )
            
            # Étape 2: Accélérer ce clip pour l'aperçu (x2)
            cmd_preview = [
                'ffmpeg', '-y',
                '-i', str(temp_filtered_path),
                '-vf', 'setpts=0.5*PTS',
                '-af', 'atempo=2.0',
                '-preset', 'ultrafast',
                '-crf', '28',
                str(temp_preview_path)
            ]
            
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
                
            subprocess.run(cmd_preview, check=True, capture_output=True, text=True, creationflags=creation_flags)
            
        except Exception as e:
            self.view.show_message(f"Erreur création aperçu: {e}", "error")
            # Nettoyage en cas d'erreur
            if temp_filtered_path.exists(): temp_filtered_path.unlink()
            return

        # 5. Afficher la boîte de dialogue d'aperçu via la vue
        short_name = self.view.open_short_preview(str(temp_preview_path))

        try:
            # 6. Si l'utilisateur a cliqué sur "Enregistrer" et entré un nom
            if short_name:
                try:
                    if not short_name:
                        self.view.show_message("Enregistrement annulé : nom vide.", "warning")
                        return

                    self.view.show_message("Enregistrement du short final...", "info")
                    final_output_path = shorts_dir / f"{short_name}.mp4"
                    
                    
                    if temp_filtered_path.exists():
                        import shutil
                        shutil.move(str(temp_filtered_path), str(final_output_path))
                        self.view.show_message(f"Short '{short_name}.mp4' enregistré !", "success")
                    else:
                        raise Exception("Le fichier temporaire a disparu.")
                        
                except Exception as e:
                    self.view.show_message(f"Erreur enregistrement final: {e}", "error")

            else:
                self.view.show_message("Enregistrement annulé.", "info")

        finally:
            # 7. Nettoyer les fichiers temporaires
            if temp_preview_path.exists():
                try:
                    temp_preview_path.unlink()
                except OSError: pass
            # Si le fichier filtré n'a pas été déplacé (ex: annulé), on le supprime
            if temp_filtered_path.exists():
                try:
                    temp_filtered_path.unlink()
                except OSError: pass


    def _generer_miniature_video(self, chemin_video):
        """
        Génère une miniature (QPixmap) à partir de la première frame d'une vidéo.
        Args:
            chemin_video: Chemin vers le fichier vidéo
        Returns:
            QPixmap ou None si échec
        """
        try:
            import cv2
            from PyQt6.QtGui import QImage, QPixmap
            cap = cv2.VideoCapture(chemin_video)
            if not cap.isOpened():
                print(f"⚠️ Impossible d'ouvrir la vidéo : {chemin_video}")
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                print(f"⚠️ Impossible de lire la première frame : {chemin_video}")
                return None
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame_rgb.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            return pixmap
        except Exception as e:
            print(f"❌ Erreur génération miniature pour {chemin_video}: {e}")
            return None