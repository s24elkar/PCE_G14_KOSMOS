"""
CONTRÔLEUR - Page d'extraction KOSMOS
Architecture MVC

Orchestre le chargement des vidéos, l'application des filtres OpenCV en temps réel,
et l'export des extraits (screenshots, recordings, shorts) via FFmpeg.
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

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.app_model import UnderwaterFilters


class ExtractionKosmosController(QObject):
    """
    Contrôleur pour la page d'extraction KOSMOS.
    
    Responsabilités :
        - Chargement vidéo avec métadonnées JSON/CSV
        - Gestion des filtres OpenCV temps réel
        - Export avec filtres via pipeline OpenCV→FFmpeg
        - Navigation entre vidéos et pages
    """
    
    navigation_demandee = pyqtSignal(str)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.view = None
        
        # État local pour corrections d'image
        self.brightness = 0
        self.contrast = 0
        self.pending_capture_name = None
        
    def set_view(self, view):
        """Associe la vue et configure les connexions initiales."""
        self.view = view
        
        if self.view and hasattr(self.view, 'view_shown'):
            self.view.view_shown.connect(self.load_first_video)

    def load_first_video(self):
        """Charge automatiquement la première vidéo conservée au démarrage."""
        if not self.model.campagne_courante:
            return

        videos_conservees = self.model.campagne_courante.obtenir_videos_conservees()
        
        if videos_conservees:
            premiere_video = videos_conservees[0]
            print(f"Chargement de la première vidéo conservée : {premiere_video.nom}")
            self.charger_video_dans_lecteur(premiere_video)

    def load_initial_data(self):
        """
        Charge la liste des vidéos dans l'explorateur.
        
        Génère les miniatures et définit les couleurs (vert=conservée, rouge=supprimée).
        """
        if not self.view:
            return

        videos = self.model.obtenir_videos()
        
        videos_data = []
        for vid in videos:
            thumbnail_pixmap = self._generer_miniature_video(vid.chemin)
            color = "#00CBA9" if vid.est_conservee else "#FF6B6B"
            
            videos_data.append({
                'name': vid.nom,
                'thumbnail_pixmap': thumbnail_pixmap,
                'thumbnail_color': color
            })
            
        self.view.update_video_list(videos_data)
        
        if self.model.video_selectionnee:
            self.charger_video_dans_lecteur(self.model.video_selectionnee)

    # ===========================================================================
    # NAVIGATION
    # ===========================================================================

    def on_tab_changed(self, tab_name):
        """Convertit le nom d'onglet en ID de page et émet le signal de navigation."""
        tabs_map = {
            "Fichier": "accueil",
            "Tri": "tri",
            "Extraction": "extraction",
            "Évènements": "evenements"
        }
        
        if tab_name in tabs_map:
            self.navigation_demandee.emit(tabs_map[tab_name])

    def on_video_selected(self, video_name):
        """Sélectionne une vidéo et la charge dans le lecteur."""
        video = self.model.selectionner_video(video_name)
        
        if video:
            self.charger_video_dans_lecteur(video)
        else:
            print(f"Erreur: Vidéo '{video_name}' non trouvée dans le modèle.")

    def charger_video_dans_lecteur(self, video):
        """
        Charge une vidéo avec toutes ses métadonnées (JSON + CSV).
        
        Les métadonnées dynamiques (température, pression) sont synchronisées
        automatiquement avec la position de lecture via timeseries_data.
        """
        if not self.view:
            return

        video.charger_metadonnees_propres_json()
        video.charger_metadonnees_communes_json()
        video.charger_donnees_timeseries_csv()

        metadata_display = {
            "time": video.start_time_str,
        }

        video_data = {
            'path': video.chemin,
            'metadata': metadata_display,
            'timeseries_data': video.timeseries_data
        }

        self.view.update_video_player(video_data)

    # ===========================================================================
    # CONTRÔLE LECTEUR
    # ===========================================================================
        
    def on_play_pause(self):
        print("Play/Pause demandé")

    def on_position_changed(self, position):
        pass

    def on_previous_video(self):
        self._naviguer_video(-1)

    def on_next_video(self):
        self._naviguer_video(1)

    def on_rewind(self):
        print("Retour arrière")

    def on_forward(self):
        print("Avance rapide")

    def _naviguer_video(self, direction):
        """
        Navigation circulaire entre vidéos.
        
        Args:
            direction : -1 pour précédente, +1 pour suivante
        """
        videos = self.model.obtenir_videos()
        
        if not videos or not self.model.video_selectionnee:
            return

        current_name = self.model.video_selectionnee.nom
        
        try:
            current_idx = -1
            for i, v in enumerate(videos):
                if v.nom == current_name:
                    current_idx = i
                    break
            
            if current_idx != -1:
                new_idx = (current_idx + direction) % len(videos)
                new_video = videos[new_idx]
                self.on_video_selected(new_video.nom)
                
        except ValueError:
            pass

    # ===========================================================================
    # FILTRES OPENCV
    # ===========================================================================

    def on_contrast_changed(self, value):
        """Gère le slider de contraste (-100 à 100)."""
        self.contrast = value
        
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter(
                'contrast_base',
                UnderwaterFilters.apply_contrast_brightness,
                value != 0 or self.brightness != 0,
                contrast=self.contrast,
                brightness=self.brightness
            )

    def on_brightness_changed(self, value):
        """Gère le slider de luminosité (-100 à 100)."""
        self.brightness = value
        
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter(
                'contrast_base',
                UnderwaterFilters.apply_contrast_brightness,
                self.contrast != 0 or value != 0,
                contrast=self.contrast,
                brightness=self.brightness
            )

    def on_color_correction(self):
        """
        Applique un preset de filtres pour vidéos sous-marines.
        
        Active : gamma (1.2), correction bleue (15%), contraste CLAHE (1.5)
        """
        if not self.view or not hasattr(self.view, 'video_player'):
            return

        self.view.video_player.toggle_filter('gamma', UnderwaterFilters.apply_gamma, True, gamma=1.2)
        self.view.video_player.toggle_filter('blue_correction', UnderwaterFilters.correct_blue_dominance, True, factor=0.15)
        self.view.video_player.toggle_filter('contrast', UnderwaterFilters.enhance_contrast, True, clip_limit=1.5)
        
        self.view.image_correction.update_filter_buttons_state({
            'gamma': True,
            'blue_correction': True,
            'contrast': True,
            'denoise': self.view.video_player.is_filter_active('denoise'),
            'sharpen': self.view.video_player.is_filter_active('sharpen')
        })
        
        self.view.show_message("Correction automatique appliquée.", "success")

    def on_toggle_gamma(self, toggled):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('gamma', UnderwaterFilters.apply_gamma, toggled, gamma=1.2)

    def on_toggle_contrast(self, toggled):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('contrast', UnderwaterFilters.enhance_contrast, toggled, clip_limit=1.5)

    def on_toggle_denoise(self, toggled):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('denoise', UnderwaterFilters.denoise, toggled, h=10.0)

    def on_toggle_sharpen(self, toggled):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('sharpen', UnderwaterFilters.sharpen, toggled)

    def on_reset_filters(self):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.reset_filters()

    def on_saturation_changed(self, value):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('saturation', UnderwaterFilters.apply_saturation, value != 0, value=value)

    def on_hue_changed(self, value):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('hue', UnderwaterFilters.apply_hue, value != 0, value=value)

    def on_temperature_changed(self, value):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('temperature', UnderwaterFilters.apply_temperature, value != 0, value=value)

    def on_curve_changed(self, lut):
        if self.view and hasattr(self.view, 'video_player'):
            self.view.video_player.toggle_filter('curve', UnderwaterFilters.apply_lut, True, lut=lut)

    # ===========================================================================
    # OUTILS D'EXTRACTION
    # ===========================================================================

    def on_screenshot(self):
        """Demande le type de capture (complète ou zone) et exécute."""
        if not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return
        
        if not self.view or not hasattr(self.view, 'video_player'):
            return
        
        capture_type = self.view.ask_screenshot_type()
        
        if capture_type == "full":
            self.view.video_player.grab_frame(None)
        elif capture_type == "crop":
            self.on_crop()

    def on_crop(self):
        """Active le mode sélection de zone sur le lecteur."""
        if self.view and hasattr(self.view, 'video_player'):
            self.view.show_message("Dessinez un rectangle sur la vidéo pour capturer une zone.", "info")
            self.view.video_player.start_cropping()

    def on_crop_area_selected(self, crop_rect):
        """Callback appelé après sélection de zone."""
        self.view.video_player.grab_frame(crop_rect)

    def save_captured_frame(self, frame: QPixmap):
        """
        Sauvegarde une capture d'écran en PNG haute qualité.
        
        Structure : /campagne/extraction/captures/nom.png
        """
        if not frame:
            self.view.show_message("Impossible de capturer l'image de la vidéo.", "error")
            return

        capture_name = self.view.ask_capture_name()

        if not capture_name:
            self.view.show_message("Capture annulée.", "info")
            return

        self.pending_capture_name = capture_name

        workspace = self.model.campagne_courante.workspace_extraction
        if not workspace:
            self.view.show_message("Dossier d'extraction non défini pour la campagne.", "error")
            return

        captures_dir = Path(workspace) / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.pending_capture_name}.png"
        save_path = captures_dir / filename

        try:
            frame.save(str(save_path), "png", -1)
            self.view.show_message(f"Capture enregistrée : {filename}", "success")
            print(f"Capture d'écran enregistrée sous : {save_path}")
            
        except Exception as e:
            self.view.show_message(f"Erreur lors de la sauvegarde : {e}", "error")
            print(f"Erreur sauvegarde capture : {e}")
            
        finally:
            self.pending_capture_name = None
            
    def _export_video_with_filters(self, source_path, output_path, start_ms, end_ms):
        """
        Exporte un extrait vidéo avec filtres OpenCV via pipeline FFmpeg.
        
        Pipeline :
            1. OpenCV lit et filtre les frames
            2. Frames envoyées dans stdin de FFmpeg
            3. FFmpeg encode H.264 + AAC depuis stdin (vidéo) + fichier (audio)
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
            '-loglevel', 'error',
            '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}', '-pix_fmt', 'bgr24',
            '-r', str(fps), '-i', '-',
            '-ss', start_str, '-i', str(source_path),
            '-t', str(duration_s),
            '-map', '0:v', '-map', '1:a?',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            str(output_path)
        ]
        
        print(f"Commande FFmpeg: {' '.join(cmd)}")
        
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
        
        print(f"Export avec filtres ({len(filters)} actifs)...")
        
        try:
            count = 0
            while count < frames_to_process:
                QApplication.processEvents()
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                if filters:
                    for name, (filter_func, kwargs) in filters.items():
                        try:
                            frame = filter_func(frame, **kwargs)
                        except Exception as e:
                            print(f"Erreur filtre {name}: {e}")
                
                try:
                    process.stdin.write(frame.tobytes())
                except IOError as e:
                    print(f"Erreur écriture pipe: {e}")
                    break
                
                count += 1
        
        finally:
            cap.release()
            if process.stdin:
                process.stdin.close()
            
            stdout_data, stderr_data = process.communicate()
            
            if process.returncode != 0:
                stderr_output = stderr_data.decode('utf-8', errors='replace') if stderr_data else "Erreur inconnue"
                print(f"Erreur FFmpeg (code {process.returncode}): {stderr_output}")
                raise Exception(f"Erreur lors de l'encodage FFmpeg: {stderr_output[-200:]}")
            else:
                print("Export FFmpeg terminé avec succès.")

    def on_recording(self):
        """
        Crée un extrait vidéo avec éditeur de plage et export avec filtres.
        
        Workflow : Position actuelle → Plage 30s → Éditeur → Export filtré
        """
        if not self.view or not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

        video_thread = self.view.video_player.video_thread
        if video_thread.total_frames == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return
        
        current_pos_ms = int((video_thread.current_frame / video_thread.fps) * 1000)
        duration_ms = self.view.video_player.duration

        if duration_ms == 0:
            self.view.show_message("La durée de la vidéo est inconnue.", "error")
            return

        initial_start_ms = current_pos_ms
        initial_end_ms = min(duration_ms, current_pos_ms + 30000)

        result = self.view.open_clip_editor(
            self.model.video_selectionnee.chemin,
            initial_start_ms,
            initial_end_ms
        )

        if not result:
            self.view.show_message("Enregistrement annulé.", "info")
            return

        try:
            rec_name, final_start_ms, final_end_ms = result
            
            recordings_dir = Path(self.model.campagne_courante.workspace_extraction) / "recordings"
            recordings_dir.mkdir(parents=True, exist_ok=True)
            final_output_path = recordings_dir / f"{rec_name}.mp4"

            self.view.show_message("Enregistrement de l'extrait final...", "info")
            
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
        """
        Crée un short avec aperçu accéléré x2.
        
        Workflow : Choix durée → Export filtré → Aperçu x2 → Validation → Fichier final
        """
        if not self.view or not self.model.video_selectionnee:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return

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

        durations = ["10 secondes", "20 secondes", "30 secondes"]
        selected_duration_str = self.view.ask_short_duration(durations)

        if not selected_duration_str:
            self.view.show_message("Création du short annulée.", "info")
            return

        clip_duration_s = int(selected_duration_str.split()[0])

        start_ms = max(0, current_pos_ms - (clip_duration_s * 1000 // 2))
        end_ms = min(total_duration_ms, start_ms + (clip_duration_s * 1000))
        clip_duration_s = (end_ms - start_ms) / 1000

        extraction_dir = Path(self.model.campagne_courante.workspace_extraction)
        shorts_dir = extraction_dir / "shorts"
        shorts_dir.mkdir(parents=True, exist_ok=True)
        
        temp_filtered_path = shorts_dir / f"~temp_filtered.mp4"
        temp_preview_path = shorts_dir / f"~preview_temp.mp4"

        try:
            self.view.show_message("Génération de l'aperçu avec filtres...", "info")
            
            end_ms = start_ms + int(clip_duration_s * 1000)
            self._export_video_with_filters(
                self.model.video_selectionnee.chemin,
                temp_filtered_path,
                start_ms,
                end_ms
            )
            
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
            if temp_filtered_path.exists():
                temp_filtered_path.unlink()
            return

        short_name = self.view.open_short_preview(str(temp_preview_path))

        try:
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
            if temp_preview_path.exists():
                try:
                    temp_preview_path.unlink()
                except OSError:
                    pass
            
            if temp_filtered_path.exists():
                try:
                    temp_filtered_path.unlink()
                except OSError:
                    pass

    def _generer_miniature_video(self, chemin_video):
        """Génère une miniature depuis la première frame avec OpenCV."""
        try:
            import cv2
            from PyQt6.QtGui import QImage, QPixmap
            
            cap = cv2.VideoCapture(chemin_video)
            if not cap.isOpened():
                print(f"Impossible d'ouvrir la vidéo : {chemin_video}")
                return None
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret or frame is None:
                print(f"Impossible de lire la première frame : {chemin_video}")
                return None
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame_rgb.shape
            bytes_per_line = 3 * width
            
            q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            return pixmap
            
        except Exception as e:
            print(f"Erreur génération miniature pour {chemin_video}: {e}")
            return None