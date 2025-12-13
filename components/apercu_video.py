"""
Composant d'aperçu des vidéos avec miniatures animées au survol.
Utilise OpenCV pour la lecture vidéo lors du survol.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QPixmap, QImage



class AnimatedThumbnailLabel(QLabel):
    """QLabel personnalisé qui gère l'affichage d'un Pixmap statique et le remplace par une lecture OpenCV lors du survol"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.static_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black; border: none; color: #888;")
        self.setText("🔄")
        
        self.video_path = None
        self.seek_time_sec = 0
        self.duration_sec = 0
        self.cap = None
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.update_frame)
        self.playback_start_time = 0
        
        self.setScaledContents(False) 
    
    def set_static_pixmap(self, pixmap):
        """Définit l'image statique (miniature)"""
        self.static_pixmap = pixmap
        if not self.playback_timer.isActive():
            self.setPixmap(self.static_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.setText("")
    
    def set_video_preview_info(self, video_path: str, seek_time_str: str, duration_sec: int):
        """Stocke les informations pour la lecture OpenCV"""
        self.video_path = video_path
        self.duration_sec = duration_sec
        
        if video_path and seek_time_str:
            try:
                h, m, s = map(int, seek_time_str.split(':'))
                self.seek_time_sec = h * 3600 + m * 60 + s
            except Exception as e:
                print(f"Erreur parsing seek time '{seek_time_str}': {e}")
                self.seek_time_sec = 0
        else:
            self.seek_time_sec = 0

    def enterEvent(self, event):
        """Survol : démarre la lecture OpenCV"""
        if self.video_path and not self.playback_timer.isActive():
            try:
                self.cap = cv2.VideoCapture(self.video_path)
                if not self.cap.isOpened():
                    print(f"Erreur ouverture vidéo: {self.video_path}")
                    self.cap = None
                    return
                
                self.cap.set(cv2.CAP_PROP_POS_MSEC, self.seek_time_sec * 1000)
                self.playback_start_time = time.time()
                self.playback_timer.start(33) 
            except Exception as e:
                print(f"Erreur démarrage OpenCV: {e}")
                self.cap = None
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Sortie survol : arrête la lecture OpenCV et remet l'image statique"""
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.static_pixmap:
            self.setPixmap(self.static_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.setPixmap(QPixmap())
            self.setText("🔄")
        
        super().leaveEvent(event)

    def update_frame(self):
        """Slot pour le QTimer, lit et affiche une frame vidéo (MODIFIÉ POUR x2)"""
        if not self.cap or not self.cap.isOpened():
            self.leaveEvent(None) 
            return

        elapsed = time.time() - self.playback_start_time
        if (elapsed * 2) > self.duration_sec:
            self.leaveEvent(None) 
            return

        ret, _ = self.cap.read() 
        if not ret:
            self.leaveEvent(None) 
            return
        
        ret, frame = self.cap.read() 
        if not ret:
            self.leaveEvent(None) 
            return

        try:
            """ Convertit la frame BGR en QImage et l'affiche """
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Erreur conversion frame: {e}")
            self.leaveEvent(None) 
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.static_pixmap and not self.playback_timer.isActive():
            self.setPixmap(self.static_pixmap.scaled(event.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


# ═══════════════════════════════════════════════════════════════
# EXTRACTION DE MINIATURES
# ═══════════════════════════════════════════════════════════════

class PreviewExtractorThread(QThread):
    """Thread pour extraire une miniature STATIQUE"""
    thumbnail_ready = pyqtSignal(int, QPixmap)
    
    def __init__(self, video_path, seek_info: list, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.seek_info = seek_info 
        self.temp_dir = Path(video_path).parent / ".thumbnails"
        self.temp_dir.mkdir(exist_ok=True)
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        """Extrait les miniatures et émet un signal quand chacune est prête"""
        for idx, (seek_time, duration) in enumerate(self.seek_info):
            if not self._is_running:
                break
            try:
                safe_seek_time = seek_time.replace(':', '')
                thumb_path = self.temp_dir / f"thumb_{Path(self.video_path).stem}_{idx}_{safe_seek_time}.jpg"
                
                pixmap = self.extract_thumbnail(seek_time, thumb_path)
                if pixmap and self._is_running:
                    self.thumbnail_ready.emit(idx, pixmap)
                
            except Exception as e:
                print(f"⚠️ Erreur extraction preview {idx}: {e}")

    def extract_thumbnail(self, seek_time, output_path):
        """Utilise ffmpeg pour extraire une miniature à un temps donné"""
        if output_path.exists():
            pixmap = QPixmap(str(output_path))
            if not pixmap.isNull():
                return pixmap
        
        cmd = ['ffmpeg', '-ss', seek_time, '-i', self.video_path, '-vframes', '1', '-vf', 'scale=320:-1', '-q:v', '3', '-y', str(output_path)]
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=5, text=True, encoding='utf-8')
            if output_path.exists():
                return QPixmap(str(output_path))
        except FileNotFoundError:
            print("❌ ffmpeg n'est pas trouvé")
            self.stop()
        except Exception as e:
            print(f"Erreur extraction miniature: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# COMPOSANT PRINCIPAL
# ═══════════════════════════════════════════════════════════════

class ApercuVideos(QWidget):
    """
    Composant d'aperçu des vidéos avec miniatures animées au survol.
    Remplace la partie droite de TriKosmosView.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preview_extractor = None
        self.thumbnails = []
        self.thumbnail_labels = []
        
        self.init_ui()

    def init_ui(self):
        # Container principal avec style
        self.setStyleSheet("background-color: black; border: 2px solid white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Titre
        label_apercu = QLabel("Aperçu des vidéos")
        label_apercu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_apercu.setStyleSheet("font-size: 12px; font-weight: bold; padding: 4px; border-bottom: 2px solid white; background-color: white; color: black;")
        layout.addWidget(label_apercu)
        
        # Zone des miniatures
        thumbnails_widget = QWidget()
        thumbnails_widget.setStyleSheet("background-color: black; border: none;")
        thumbnails_layout = QGridLayout()
        thumbnails_layout.setSpacing(6)
        thumbnails_layout.setContentsMargins(8, 8, 8, 8) 
        
        # Configuration des miniatures
        thumbnail_min_width = 300 
        thumbnail_min_height = int(thumbnail_min_width / 1.87)
        thumbnail_max_width = 550 
        thumbnail_max_height = int(thumbnail_max_width / 1.87)

        # Ajout des 6 miniatures avec labels
        idx_counter = 1
        for row in range(2):
            for col in range(3):
                thumb = AnimatedThumbnailLabel() 
                thumb.setMinimumSize(thumbnail_min_width, thumbnail_min_height)
                thumb.setMaximumSize(thumbnail_max_width, thumbnail_max_height)
                thumb.setSizePolicy(
                    QSizePolicy.Policy.Expanding, 
                    QSizePolicy.Policy.Expanding
                )
                self.thumbnails.append(thumb) 

                label = QLabel(f"Angle de vue n°{idx_counter}")
                label.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.thumbnail_labels.append(label) 

                item_layout = QVBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(4) 
                
                item_layout.addStretch() 
                item_layout.addWidget(thumb, 1) 
                item_layout.addWidget(label, 0) 
                item_layout.addStretch() 
                
                item_widget = QWidget()
                item_widget.setStyleSheet("background-color: transparent; border: none;")
                item_widget.setLayout(item_layout)
                
                thumbnails_layout.addWidget(item_widget, row, col, Qt.AlignmentFlag.AlignCenter)
                
                idx_counter += 1

        for i in range(2):
            thumbnails_layout.setRowStretch(i, 1)
        for i in range(3):
            thumbnails_layout.setColumnStretch(i, 1)
        
        thumbnails_widget.setLayout(thumbnails_layout)
        layout.addWidget(thumbnails_widget, 1)

    def charger_previews(self, video_path, seek_info):
        """Lance l'extraction et l'affichage des miniatures pour une vidéo donnée"""
        # Arrêter le thread précédent s'il existe
        if self.preview_extractor and self.preview_extractor.isRunning():
            self.preview_extractor.stop()
            self.preview_extractor.wait()
        
        # Réinitialiser les miniatures
        for thumb in self.thumbnails:
            thumb.setText("🔄")
            thumb.setPixmap(QPixmap())
            thumb.set_video_preview_info(None, "00:00:00", 0)
            thumb.static_pixmap = None

        # Configurer les infos de survol pour chaque miniature
        for idx, thumb in enumerate(self.thumbnails):
            if idx < len(seek_info):
                seek_time_str, duration = seek_info[idx]
                thumb.set_video_preview_info(video_path, seek_time_str, duration)
            else:
                thumb.set_video_preview_info(None, "00:00:00", 0)

        print(f"🎬 Lancement extraction previews...")
        
        # Lancer le thread d'extraction
        self.preview_extractor = PreviewExtractorThread(video_path, seek_info)
        self.preview_extractor.thumbnail_ready.connect(self.afficher_miniature)
        self.preview_extractor.start()

    def afficher_miniature(self, index, pixmap):
        """Slot appelé quand une miniature est prête"""
        if index < len(self.thumbnails):
            if self.thumbnails[index].size().isValid():
                self.thumbnails[index].set_static_pixmap(pixmap)
            else:
                self.thumbnails[index].static_pixmap = pixmap
                self.thumbnails[index].setText("") 
            print(f"✅ Miniature statique {index+1} affichée")
