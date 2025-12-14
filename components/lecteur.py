"""
Composant Lecteur Vidéo
Lecteur avec timeline, contrôles et affichage des métadonnées
Utilise OpenCV dans un QThread pour l'affichage vidéo avec overlay personnalisé
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedLayout,QPushButton, QSlider, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize, QPoint, QThread
from PyQt6.QtGui import QColor, QPalette, QPainter, QPen, QPixmap, QIcon, QBrush, QCursor, QImage
from pathlib import Path
import sys
import time
import cv2
import numpy as np
from collections import OrderedDict


class VideoThread(QThread):
    """Thread pour lire la vidéo avec OpenCV sans bloquer l'UI."""
    frame_ready = pyqtSignal(np.ndarray)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.cap = None
        self.video_path_to_load = None
        self._is_running = True
        self.is_paused = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 25
        self.seek_frame = -1
        self.loop = False #Attribut pour la lecture en boucle
        self.speed = 1.0
        self._last_frame_time = 0
        
    def stop(self):
        """Arrête proprement le thread."""
        self._is_running = False
        
    def load_video(self, video_path):
        """
        Demande au thread de charger une nouvelle vidéo.
        Ne manipule pas cv2.VideoCapture directement.
        """
        self.video_path_to_load = video_path
        
    def play(self):
        """Reprend la lecture."""
        self.is_paused = False
        self._last_frame_time = time.time()
        
    def pause(self):
        """Met en pause la lecture."""
        self.is_paused = True
        
    def seek(self, frame_number):
        """Aller à une frame spécifique."""
        if self.total_frames > 0:
            target_frame = max(0, min(frame_number, self.total_frames - 1))
            self.seek_frame = target_frame

    def set_looping(self, loop: bool):
        """Active ou désactive la lecture en boucle."""
        self.loop = loop
        
    def set_speed(self, speed):
        """Définit la vitesse de lecture."""
        self.speed = speed
        self._last_frame_time = time.time()
        
    def run(self):
        """Boucle principale du thread vidéo."""
        while self._is_running:
            # --- GESTION DU CHARGEMENT DE VIDÉO (Thread-safe) ---
            if self.video_path_to_load:
                if self.cap:
                    self.cap.release()
                self.cap = cv2.VideoCapture(str(self.video_path_to_load))
                
                """Vérifier si la vidéo a été ouverte correctement"""
                if self.cap.isOpened():
                    self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
                    duration_ms = int((self.total_frames / self.fps) * 1000)
                    self.duration_changed.emit(duration_ms)
                    
                    ret, frame = self.cap.read()
                    if ret:
                        self.current_frame = 0
                        self.frame_ready.emit(frame)
                        self.position_changed.emit(0)
                    print(f"Vidéo OpenCV chargée: {self.total_frames} frames à {self.fps} fps")
                else:
                    print(f"Erreur: Impossible d'ouvrir la vidéo {self.video_path_to_load}")
                    self.cap = None # S'assurer que cap est None en cas d'échec
                
                self.video_path_to_load = None # Réinitialiser la demande
                self._last_frame_time = time.time()

            # --- LECTURE DE LA VIDÉO ---
            if not self.cap or not self.cap.isOpened():
                self.msleep(100)
                continue

            # Gestion de la recherche
            if self.seek_frame != -1:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.seek_frame)
                self.current_frame = self.seek_frame
                self.seek_frame = -1
                
                ret, frame = self.cap.read()
                if ret:
                    self.frame_ready.emit(frame)
                    position_ms = int((self.current_frame / self.fps) * 1000)
                    self.position_changed.emit(position_ms)
                self._last_frame_time = time.time()

            # Lecture normale si pas en pause
            if not self.is_paused:
                current_time = time.time()
                elapsed_time = current_time - self._last_frame_time
                frames_to_advance = int(elapsed_time * self.fps * self.speed)

                if frames_to_advance >= 1:
                    if self.speed > 2.0 : 
                        frames_to_skip = frames_to_advance - 1
                        for _ in range(frames_to_skip):
                            ret = self.cap.grab()
                            if not ret:
                                break
                            self.current_frame += 1

                ret, frame = self.cap.read()
                if ret:
                    self.frame_ready.emit(frame)
                    self.current_frame += 1
                    position_ms = int((self.current_frame / self.fps) * 1000)
                    self.position_changed.emit(position_ms)
                    
                    delay = int((1000 / self.fps) / self.speed)
                    self.msleep(delay)
                else:
                    # Si la lecture en boucle est activée, on revient au début
                    if self.loop:
                        self.seek(0)
                        continue
                    self.is_paused = True # Fin de la vidéo
            else:
                self.msleep(50)
        
        if self.cap:
            self.cap.release()


class CustomVideoWidget(QLabel):
    """Widget vidéo basé sur QLabel avec OpenCV pour un contrôle total de l'affichage."""
    
    # Signal émis lorsque l'utilisateur a fini de dessiner un rectangle
    crop_area_selected = pyqtSignal(QRect)
    # Signal pour demander au parent de reprendre la lecture si nécessaire
    cropping_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.metadata_lines = []
        self.show_metadata = True
        self.current_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black; border: none;")
        self.setMinimumSize(640, 360)

        # --- Attributs pour le mode capture ---
        self.is_cropping = False
        self.crop_start_point = QPoint()
        self.crop_end_point = QPoint()
        self.setMouseTracking(True) # Important pour suivre la souris même sans clic


    def set_metadata(self, metadata_dict):
        """Prépare les lignes de texte à afficher."""
        self.metadata_lines = []
        if not metadata_dict:
            self.update()
            return
            
        if 'time' in metadata_dict: self.metadata_lines.append(f"Time : {metadata_dict['time']}")
        if 'temp' in metadata_dict: self.metadata_lines.append(f"Temp : {metadata_dict['temp']}")
        # if 'salinity' in metadata_dict: self.metadata_lines.append(f"💧 Salinity : {metadata_dict['salinity']}") # Exemple
        # if 'depth' in metadata_dict: self.metadata_lines.append(f"📏 Depth : {metadata_dict['depth']}") # Exemple
        if 'pression' in metadata_dict: self.metadata_lines.append(f"Pression : {metadata_dict['pression']}")
        if 'lux' in metadata_dict: self.metadata_lines.append(f"Lux : {metadata_dict['lux']}")
        
        self.update() # Demande un redessinage

    def toggle_metadata(self, show):
        """Active ou désactive l'affichage des métadonnées."""
        self.show_metadata = show
        self.update()

    def update_frame(self, frame):
        """Met à jour l'affichage avec une nouvelle frame OpenCV."""
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        
        # Utiliser QPainter pour une conversion de haute qualité de QImage vers QPixmap
        # afin d'éviter la pixellisation potentielle de fromImage().
        pixmap = QPixmap(q_image.size())
        painter = QPainter(pixmap)
        painter.drawImage(0, 0, q_image)
        painter.end()
        self.current_pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        """Dessine le pixmap actuel avec les métadonnées et l'overlay de capture."""
        if not self.current_pixmap:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        
        # On ne redimensionne que si l'image est plus grande que le lecteur
        # pour éviter de la pixelliser en l'agrandissant.
        if self.current_pixmap.width() > self.width() or self.current_pixmap.height() > self.height():
            # Utiliser SmoothTransformation pour une meilleure qualité de réduction
            pixmap_to_draw = self.current_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            # Si l'image est plus petite, on l'affiche en qualité native (taille originale)
            pixmap_to_draw = self.current_pixmap
        
        # Centrer le pixmap
        x = (self.width() - pixmap_to_draw.width()) // 2
        y = (self.height() - pixmap_to_draw.height()) // 2
        painter.drawPixmap(x, y, pixmap_to_draw)

        if self.show_metadata and self.metadata_lines:
            self.draw_metadata(painter)
            
        # --- DESSIN DE L'OVERLAY DE CAPTURE ---
        # On dessine par-dessus la vidéo
        if self.is_cropping:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Dessiner le rectangle de sélection en cours
            if not self.crop_start_point.isNull() and not self.crop_end_point.isNull():
                crop_rect = QRect(self.crop_start_point, self.crop_end_point).normalized()
                
                if crop_rect.width() > 2 and crop_rect.height() > 2:
                    # Zone claire pour la sélection
                    painter.setBrush(QColor(255, 255, 255, 50))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRect(crop_rect)

                    # Bordure rouge très visible
                    pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRect(crop_rect)

                    # Afficher les dimensions
                    painter.setPen(QColor("white"))
                    painter.drawText(crop_rect.bottomLeft() + QPoint(5, 15), f"{crop_rect.width()}x{crop_rect.height()}")

    def start_cropping_mode(self):
        """Active le mode de sélection de zone de capture."""
        self.is_cropping = True
        self.crop_start_point = QPoint()
        self.crop_end_point = QPoint()
        self.setCursor(Qt.CursorShape.CrossCursor)

    def draw_metadata(self, painter):
        """Dessine les métadonnées sur le pixmap."""
        if not self.metadata_lines:
            return

        painter.setPen(QPen(QColor("white")))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)

        y_pos = 20
        for line in self.metadata_lines:
            painter.drawText(10, y_pos, line)
            y_pos += 20

    def get_current_pixmap_for_capture(self):
        """Retourne le pixmap actuel pour la capture."""
        return self.current_pixmap.copy() if self.current_pixmap else None

    # --- GESTION DES ÉVÉNEMENTS SOURIS POUR LA CAPTURE ---
    def mousePressEvent(self, event):
        """Démarre la sélection de zone de capture."""
        if self.is_cropping and event.button() == Qt.MouseButton.LeftButton:
            self.crop_start_point = event.pos()
            self.crop_end_point = self.crop_start_point
            print(f"🖱️ Début sélection: {self.crop_start_point}")
            self.update()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Met à jour le rectangle de sélection pendant le déplacement."""
        if self.is_cropping and (event.buttons() & Qt.MouseButton.LeftButton):
            self.crop_end_point = event.pos()
            self.update() # Redessine le rectangle
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Termine la sélection de zone de capture."""
        if self.is_cropping and event.button() == Qt.MouseButton.LeftButton:
            crop_rect = QRect(self.crop_start_point, self.crop_end_point).normalized()
            print(f"Fin sélection: {crop_rect}")
            
            self.is_cropping = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            self.cropping_finished.emit() # Informe le parent que c'est fini

            if crop_rect.width() > 5 and crop_rect.height() > 5:
                self.crop_area_selected.emit(crop_rect)
            else:
                print("Sélection trop petite, ignorée")
        else:
            super().mouseReleaseEvent(event)



class VideoTimeline(QSlider):
    """Timeline avec marqueurs rouges pour les points clés"""
    
    selection_changed = pyqtSignal(int, int) # Émis quand les poignées de sélection bougent
    
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.markers = []
        self.current_value = 0
        
        
        self.selection_mode = False
        self.start_handle_pos = 0  # Position de la poignée de début (0-1000)
        self.end_handle_pos = 1000   # Position de la poignée de fin (0-1000)
        self.dragging_handle = None  # 'start', 'end', ou None
        
        
        self.init_ui()
        
    def init_ui(self):
        
        self.setMouseTracking(True) # Pour détecter le survol des poignées
        self.setMinimum(0)
        self.setMaximum(1000)
        self.setValue(0)
        self.setFixedHeight(30)
        
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
                margin: 0px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: none;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #e0e0e0;
            }
        """)
        
    def paintEvent(self, event):
        """Dessine les marqueurs et la sélection par-dessus le slider."""
        # On demande au QSlider de se dessiner d'abord
        super().paintEvent(event)
        
        # Maintenant, on dessine nos poignées par-dessus
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        groove_rect = self.geometry()
        groove_y = groove_rect.height() // 2
        groove_left = 10
        groove_right = self.width() - 10
        groove_width = groove_right - groove_left

        # Dessiner la plage de sélection si en mode sélection
        if self.selection_mode and groove_width > 0:
            start_x = groove_left + (self.start_handle_pos / 1000.0) * groove_width
            end_x = groove_left + (self.end_handle_pos / 1000.0) * groove_width
            
            # Zone sélectionnée
            selection_rect = QRect(int(start_x), groove_y - 4, int(end_x - start_x), 8)
            painter.fillRect(selection_rect, QColor(33, 150, 243, 150)) # Bleu semi-transparent

            # Poignée de début
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.setBrush(QColor("#2196F3"))
            start_handle_rect = QRect(int(start_x) - 5, groove_y - 10, 10, 20)
            painter.drawRoundedRect(start_handle_rect, 3, 3)

            # Poignée de fin
            end_handle_rect = QRect(int(end_x) - 5, groove_y - 10, 10, 20)
            painter.drawRoundedRect(end_handle_rect, 3, 3)

        for marker_pos in self.markers:
            x = groove_left + (marker_pos / 100.0) * groove_width
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0))
            marker_rect = QRect(int(x - 2), groove_y - 3, 4, 6)
            painter.drawRect(marker_rect)

    
    def mousePressEvent(self, event):
        """Démarre la sélection de zone si en mode sélection."""
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        if self.selection_mode:
            pos_x = event.position().x()
            groove_width = self.width() - 20
            start_x = 10 + (self.start_handle_pos / 1000.0) * groove_width
            end_x = 10 + (self.end_handle_pos / 1000.0) * groove_width

            # Si on clique sur une poignée, on la capture et on arrête le traitement ici.
            # Sinon, on laisse l'événement au QSlider parent pour qu'il gère le déplacement du rond.
            if abs(pos_x - start_x) < 10:
                self.dragging_handle = 'start'
                return
            elif abs(pos_x - end_x) < 10:
                self.dragging_handle = 'end'
                return
        
        # Si on n'est pas en mode sélection, ou si on n'a pas cliqué sur une poignée, on laisse le slider de base faire son travail.
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Met à jour la position des poignées si en mode sélection."""
        if self.selection_mode and self.dragging_handle:
            pos_x = event.position().x()
            groove_width = self.width() - 20
            new_pos = int(((pos_x - 10) / groove_width) * 1000)
            new_pos = max(0, min(1000, new_pos)) # borner entre 0 et 1000

            if self.dragging_handle == 'start':
                self.start_handle_pos = min(new_pos, self.end_handle_pos)
            elif self.dragging_handle == 'end':
                self.end_handle_pos = max(new_pos, self.start_handle_pos)
            
            self.selection_changed.emit(self.start_handle_pos, self.end_handle_pos)
            self.update() # Redessiner
        elif self.selection_mode:
            # Changer le curseur si on survole une poignée
            pos_x = event.position().x()
            groove_width = self.width() - 20
            start_x = 10 + (self.start_handle_pos / 1000.0) * groove_width
            end_x = 10 + (self.end_handle_pos / 1000.0) * groove_width
            if abs(pos_x - start_x) < 10 or abs(pos_x - end_x) < 10:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Arrête le déplacement des poignées."""
        self.dragging_handle = None
        super().mouseReleaseEvent(event)
    
        
    def add_marker(self, position):
        """Ajoute un marqueur rouge à la position donnée (0-100)."""
        if 0 <= position <= 100:
            self.markers.append(position)
            self.update()
            
    def clear_markers(self):
        """Supprime tous les marqueurs."""
        self.markers.clear()
        self.update()
        
    def get_position(self):
        """Retourne la position actuelle du slider."""
        return self.value()
        
    def set_position(self, position):
        """Définit la position actuelle du slider."""
        self.setValue(position)


class VideoControls(QWidget):
    """Contrôles de lecture vidéo avec icônes personnalisées"""
    
    # Signaux
    play_pause_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    rewind_clicked = pyqtSignal()
    forward_clicked = pyqtSignal()
    speed_changed = pyqtSignal(float)
    detach_clicked = pyqtSignal()    
    toggle_metadata_clicked = pyqtSignal(bool) 
    fullscreen_clicked = pyqtSignal()  
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speed = 1.0
        self.is_playing = False
        
        # Chemins des icônes
        self.icons_path = Path(__file__).parent.parent / "assets" / "icons"
        self.play_icon_path = self.icons_path / "start.png"
        self.pause_icon_path = self.icons_path / "Pause.png"
        self.speed_icon_path = self.icons_path / "vitesse.png"
        self.next_icon_path = self.icons_path / "bouton-suivant.png"
        self.previous_icon_path = self.icons_path / "precedent.png"
        
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(8)
        
        # Style uniforme pour tous les boutons
        button_style = """
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 2px solid #444;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """
        
        # Bouton Vidéo précédente
        self.btn_previous = QPushButton(QIcon(str(self.previous_icon_path)), "")
        self.btn_previous.setFixedSize(25, 25)
        self.btn_previous.setStyleSheet(button_style)
        self.btn_previous.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_previous.setToolTip("Vidéo précédente")
        self.btn_previous.clicked.connect(self.previous_clicked.emit)
        layout.addWidget(self.btn_previous)
        
        # Bouton Reculer
        self.btn_rewind = QPushButton("-10s")
        self.btn_rewind.setFixedSize(45, 25)
        self.btn_rewind.setStyleSheet(button_style)
        self.btn_rewind.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rewind.setToolTip("Reculer de 10 secondes")
        self.btn_rewind.clicked.connect(self.rewind_clicked.emit)
        layout.addWidget(self.btn_rewind)
        
        # Bouton Play/Pause avec icône personnalisée
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(25, 25)  # Réduit de 55 à 45
        self.play_pause_btn.setStyleSheet(button_style)
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause_btn.setToolTip("Lecture / Pause")
        self.play_pause_btn.clicked.connect(self.on_play_pause_clicked)
        self.update_play_pause_icon()
        layout.addWidget(self.play_pause_btn)
        
        # Bouton Avancer
        self.btn_forward = QPushButton("+10s")
        self.btn_forward.setFixedSize(45, 25)
        self.btn_forward.setStyleSheet(button_style)
        self.btn_forward.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_forward.setToolTip("Avancer de 10 secondes")
        self.btn_forward.clicked.connect(self.forward_clicked.emit)
        layout.addWidget(self.btn_forward)
        
        # Bouton Vidéo suivante
        self.btn_next = QPushButton(QIcon(str(self.next_icon_path)), "")
        self.btn_next.setFixedSize(25, 25)
        self.btn_next.setStyleSheet(button_style)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setToolTip("Vidéo suivante")
        self.btn_next.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self.btn_next)
        
        layout.addSpacing(20)
        
        # Bouton de vitesse avec icône personnalisée
        self.btn_speed = QPushButton(f"{self.current_speed}x")
        self.btn_speed.setFixedSize(70, 25)
        self.btn_speed.setStyleSheet(button_style)
        self.btn_speed.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_speed.setToolTip("Changer la vitesse de lecture")
        self.btn_speed.clicked.connect(self.toggle_speed)
        
        # Ajouter l'icône de vitesse si elle existe
        if self.speed_icon_path.exists():
            icon = QIcon(str(self.speed_icon_path))
            self.btn_speed.setIcon(icon)
            self.btn_speed.setIconSize(QSize(24, 24))
        
        layout.addWidget(self.btn_speed)
        
        layout.addSpacing(20)
        
        # Bouton détacher
        self.btn_detach = QPushButton("🪟")
        self.btn_detach.setFixedSize(25, 25)
        self.btn_detach.setStyleSheet(button_style)
        self.btn_detach.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detach.setToolTip("Détacher dans une nouvelle fenêtre")
        self.btn_detach.clicked.connect(self.detach_clicked.emit)
        layout.addWidget(self.btn_detach)

        # Bouton afficher/cacher métadonnées
        self.btn_toggle_metadata = QPushButton("ℹ️")
        self.btn_toggle_metadata.setFixedSize(25, 25)
        self.btn_toggle_metadata.setStyleSheet(button_style)
        self.btn_toggle_metadata.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_metadata.setToolTip("Afficher / Cacher les métadonnées")
        self.btn_toggle_metadata.setCheckable(True)
        self.btn_toggle_metadata.setChecked(True)
        self.btn_toggle_metadata.toggled.connect(self.toggle_metadata_clicked)
        layout.addWidget(self.btn_toggle_metadata)

        # Bouton plein écran
        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setFixedSize(25, 25)
        self.btn_fullscreen.setStyleSheet(button_style)
        self.btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fullscreen.setToolTip("Plein écran (F ou Échap pour quitter)")
        self.btn_fullscreen.clicked.connect(self.fullscreen_clicked.emit)
        layout.addWidget(self.btn_fullscreen)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: #1a1a1a;")
    
    def update_play_pause_icon(self):
        """Met à jour l'icône du bouton play/pause"""
        icon_path = self.pause_icon_path if self.is_playing else self.play_icon_path
        
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.play_pause_btn.setIcon(icon)
            self.play_pause_btn.setIconSize(QSize(32, 32))
            self.play_pause_btn.setText("")
        else:
            # Fallback sur les emoji si les images n'existent pas
            self.play_pause_btn.setText("⏸️" if self.is_playing else "▶️")
            self.play_pause_btn.setIcon(QIcon())
    
    def on_play_pause_clicked(self):
        """Gère le clic sur le bouton play/pause."""
        self.is_playing = not self.is_playing
        self.update_play_pause_icon()
        self.play_pause_clicked.emit()
    
    def toggle_speed(self):
        """Change la vitesse de lecture cycliquement."""
        speeds = [1.0, 1.5, 2.0, 5.0]
        try:
            current_index = speeds.index(self.current_speed)
            next_index = (current_index + 1) % len(speeds)
            self.current_speed = speeds[next_index]
        except ValueError:
            self.current_speed = 1.0
        
        self.btn_speed.setText(f"{self.current_speed}x")
        self.speed_changed.emit(self.current_speed)
        print(f"⚡ Vitesse changée : {self.current_speed}x")
    
    def update_play_pause_button(self, is_playing):
        """Met à jour l'état du bouton play/pause."""
        self.is_playing = is_playing
        self.update_play_pause_icon()
    
    def update_position(self, current_ms, total_ms):
        """Met à jour l'affichage de la position (optionnel pour les contrôles)."""
        # Cette méthode peut être utilisée pour afficher la position dans les contrôles
        # Pour l'instant, nous n'affichons pas la position dans les contrôles
        pass


class VideoPlayer(QWidget):
    """Composant Lecteur Vidéo avec OpenCV"""
    
    # Signaux
    play_pause_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)
    frame_captured = pyqtSignal(QPixmap)
    detach_requested = pyqtSignal()
    histogram_data_ready = pyqtSignal(list, list, list, list) # AJOUT: R, G, B, Densité
    
    filters_reset = pyqtSignal() # Signal pour notifier que les filtres ont été réinitialisés
    

    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0
        
        # --- OpenCV Video Thread ---
        self.video_thread = VideoThread()
        self.video_thread.position_changed.connect(self.on_position_changed)
        self.video_thread.position_changed.connect(self.update_timeseries_metadata)  # AJOUT pour métadonnées
        self.video_thread.duration_changed.connect(self.on_duration_changed)
        self.video_thread.start() # Démarrer le thread une seule fois
        
        # --- DONNÉES TEMPORELLES ---
        self.static_metadata = {} # Pour stocker les métadonnées du JSON
        self.timeseries_data = []
        self.last_timeseries_index = 0
        
        self.current_cv_frame = None # Pour stocker la dernière frame brute OpenCV
        self._player_initialized = False # Attribut pour savoir si une vidéo est chargée
        self._was_playing_before_crop = False
        self._capture_in_progress = False

        # --- GESTION DES FILTRES D'IMAGE ---
        self.active_filters = OrderedDict()
        self.video_thread.frame_ready.connect(self.on_frame_ready)

        #fullscreen 
        self.is_fullscreen = False
        self.normal_parent = None 
        self.normal_geometry = None
        
        self.init_ui()

    # --- MÉTHODES DE GESTION DES FILTRES ---
    def toggle_filter(self, name: str, filter_func: callable, activate: bool, **kwargs):
        """Active ou désactive un filtre."""
        if activate:
            self.active_filters[name] = (filter_func, kwargs)
        elif name in self.active_filters:
            del self.active_filters[name]
        
        # Appliquer immédiatement le changement sur l'image actuelle
        self._apply_filters_to_current_frame()

    def reset_filters(self):
        """Réinitialise tous les filtres actifs."""
        self.active_filters.clear()
        self._apply_filters_to_current_frame()
        self.filters_reset.emit() # Notifier la vue pour décocher les boutons

    def is_filter_active(self, name: str) -> bool:
        """Vérifie si un filtre est actif."""
        return name in self.active_filters

    def _apply_filters_to_current_frame(self):
        """Applique la chaîne de filtres à la frame actuelle et met à jour l'affichage."""
        if self.current_cv_frame is not None:
            self.on_frame_ready(self.current_cv_frame)

    def _calculate_and_emit_histogram(self, frame: np.ndarray):
        """Calcule l'histogramme de la frame et émet le signal."""
        try:
            # Calculer l'histogramme pour chaque canal
            b_hist = cv2.calcHist([frame], [0], None, [256], [0, 256]).flatten().tolist()
            g_hist = cv2.calcHist([frame], [1], None, [256], [0, 256]).flatten().tolist()
            r_hist = cv2.calcHist([frame], [2], None, [256], [0, 256]).flatten().tolist()

            # Calculer l'histogramme de luminance pour la densité
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            density_hist = cv2.calcHist([gray_frame], [0], None, [256], [0, 256]).flatten().tolist()

            self.histogram_data_ready.emit(r_hist, g_hist, b_hist, density_hist)
        except Exception as e:
            print(f"❌ Erreur calcul histogramme: {e}")

    def closeEvent(self, event):
        """S'assure que le thread est bien arrêté à la fermeture."""
        self.video_thread.stop()
        self.video_thread.wait()

    def on_frame_ready(self, frame):
        """Reçoit la frame brute, applique les filtres et l'affiche."""
        self.current_cv_frame = frame.copy() # Stocker la frame brute originale
        
        processed_frame = frame
        if self.active_filters:
            for name, (filter_func, kwargs) in self.active_filters.items():
                try:
                    processed_frame = filter_func(processed_frame, **kwargs)
                except Exception as e:
                    print(f"❌ Erreur en appliquant le filtre '{name}': {e}")
        
        # Calculer et émettre les données de l'histogramme de l'image traitée
        self._calculate_and_emit_histogram(processed_frame)

        self.video_widget.update_frame(processed_frame)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone vidéo avec overlay
        self.video_widget = CustomVideoWidget()
        # Connecter le signal de capture du widget enfant au contrôleur (via la vue)
        # C'est le widget enfant qui émettra le signal, pas le VideoPlayer
        self.crop_area_selected = self.video_widget.crop_area_selected
        self.video_widget.cropping_finished.connect(self.on_cropping_finished_by_child)

        main_layout.addWidget(self.video_widget, stretch=1)
        
        # Timeline
        timeline_container = QWidget()
        timeline_container.setFixedHeight(35)  # Réduit de 45 à 35
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(10, 5, 10, 5)  # Marges réduites
        timeline_layout.setSpacing(0)
        
        self.timeline = VideoTimeline()
        self.timeline.sliderPressed.connect(self.on_timeline_pressed)
        self.timeline.sliderMoved.connect(self.on_timeline_moved)
        self.timeline.sliderReleased.connect(self.on_timeline_released)
        timeline_layout.addWidget(self.timeline)
        
        timeline_container.setLayout(timeline_layout)
        timeline_container.setStyleSheet("background-color: black;")
        self.timeline_container = timeline_container
        main_layout.addWidget(timeline_container, stretch=0)
        
        # Contrôles
        controls_container = QWidget()
        controls_container.setFixedHeight(55)  # Réduit de 70 à 55
        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.controls = VideoControls()
        self.controls.play_pause_clicked.connect(self.toggle_play_pause)
        self.controls.rewind_clicked.connect(self.seek_backward)
        self.controls.forward_clicked.connect(self.seek_forward)
        self.controls.speed_changed.connect(self.on_speed_changed)
        self.controls.detach_clicked.connect(self.on_detach_player)
        self.controls.toggle_metadata_clicked.connect(self.toggle_metadata_overlay) 

        if hasattr(self.controls, 'fullscreen_clicked'):
            self.controls.fullscreen_clicked.connect(self.toggle_fullscreen)
        
        controls_layout.addWidget(self.controls)
        controls_container.setLayout(controls_layout)
        self.controls_container = controls_container
        main_layout.addWidget(controls_container, stretch=0)
        
        self.setLayout(main_layout)
        self.setObjectName("VideoPlayer")
        self.setStyleSheet("""
            #VideoPlayer {
                background-color: black;
                border: 3px solid black;
            }
        """)

    def toggle_fullscreen(self):
        """Bascule entre le mode plein écran et le mode fenêtre normale."""
        if not self.is_fullscreen:
            self.normal_parent = self.parent()
            self.normal_geometry = self.geometry()
            self.setParent(None)
            self.showFullScreen()
            self.is_fullscreen = True
            print("Passage en mode plein écran")
        else:
            self.showNormal()
            if self.normal_parent:
                self.setParent(self.normal_parent)
                self.setGeometry(self.normal_geometry)
                self.show()
            self.is_fullscreen = False
            print("Retour au mode fenêtre normale")

    # --- MÉTHODES DE CONTRÔLE DU LECTEUR  ---

    def load_video(self, video_path):
        """Charge une vidéo dans le thread."""
        self.video_thread.load_video(video_path)
        self._player_initialized = True
        self.controls.update_play_pause_button(True) # Met l'icône en pause (car ça joue auto)

    def toggle_play_pause(self):
        """Bascule entre lecture et pause."""
        if not self._player_initialized:
            return
        
        if self.video_thread.is_paused:
            self.play()
        else:
            self.pause()
        
        self.play_pause_clicked.emit()

    def play(self):
        """Lance la lecture."""
        if self._player_initialized:
            self.video_thread.play()
            self.controls.update_play_pause_button(True)

    def pause(self):
        """Met en pause."""
        if self._player_initialized:
            self.video_thread.pause()
            self.controls.update_play_pause_button(False)

    def on_speed_changed(self, speed):
        """Change la vitesse de lecture."""
        self.video_thread.set_speed(speed)

    def on_detach_player(self):
        """Demande le détachement du lecteur."""
        self.detach_requested.emit()
    
    def keyPressEvent(self, event):
        """Gestion des touches clavier."""
        # Échapper du mode capture
        if self.video_widget.is_cropping and event.key() == Qt.Key.Key_Escape:
            self.video_widget.is_cropping = False
            self.on_cropping_finished_by_child()
            print("🖱️ Sélection de zone annulée.")
            self.video_widget.update()
        # Échapper du plein écran
        elif self.is_fullscreen and event.key() == Qt.Key.Key_Escape:
            self.toggle_fullscreen()
        # Espace pour play/pause
        elif event.key() == Qt.Key.Key_Space:
            self.toggle_play_pause()
        # F pour plein écran
        elif event.key() == Qt.Key.Key_F:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def on_timeline_pressed(self):
        """Appelé quand l'utilisateur clique sur la timeline."""
        if self._player_initialized:
            self.video_thread.pause()

    def on_timeline_moved(self, value):
        """Appelé quand l'utilisateur déplace le slider de la timeline."""
        if self._player_initialized and self.duration > 0:
            target_frame = int((value / self.timeline.maximum()) * self.video_thread.total_frames)
            self.video_thread.seek(target_frame)

    def on_cropping_finished_by_child(self):
        """Slot appelé par le widget enfant quand la capture (réussie ou non) est terminée."""
        print("🛑 Fin du mode capture (signal enfant)")
        # Reprendre la lecture si elle était en cours avant la capture
        if hasattr(self, '_was_playing_before_crop') and self._was_playing_before_crop:
            if hasattr(self.video_thread, 'is_paused') and self.video_thread.is_paused:
                self.video_thread.play()
                print("▶️ Reprise de la lecture")
        self._was_playing_before_crop = False

    def on_timeline_released(self):
        """Appelé quand l'utilisateur relâche le slider de la timeline."""
        if self._player_initialized and self.controls.is_playing:
            self.video_thread.play()

    def start_cropping(self):
        """Passe le lecteur en mode sélection."""
        print("🎯 Démarrage du mode capture")
        self._capture_in_progress = False
        # Mémoriser l'état et mettre en pause
        self._was_playing_before_crop = not self.video_thread.is_paused
        if self._was_playing_before_crop:
            self.video_thread.pause()
            print("⏸️ Vidéo mise en pause pour la capture")
        self.video_widget.start_cropping_mode()
        print("✅ Mode capture activé - dessinez un rectangle sur la vidéo")

    def grab_frame(self, crop_rect: QRect = None) -> None:
        """Capture la frame actuelle avec OpenCV."""
        print(f"📸 Capture frame OpenCV: zone={crop_rect}")
        
        # Protection contre les captures multiples
        if hasattr(self, '_capture_in_progress') and self._capture_in_progress:
            print("⚠️ Capture déjà en cours, annulation")
            return

        pixmap_to_capture = self.video_widget.get_current_pixmap_for_capture()
        self._capture_in_progress = True
        
        # Utiliser la frame OpenCV stockée dans VideoPlayer (self.current_cv_frame)
        # et non une frame inexistante sur le widget d'affichage.
        if self.current_cv_frame is None:
            print("❌ Aucune frame OpenCV disponible pour la capture.")
            return
        frame = self.current_cv_frame.copy()
        
        # Appliquer les filtres actifs sur la capture pour qu'elle corresponde à ce qui est affiché
        if self.active_filters:
            for name, (filter_func, kwargs) in self.active_filters.items():
                try:
                    frame = filter_func(frame, **kwargs)
                except Exception as e:
                    print(f"❌ Erreur en appliquant le filtre '{name}' lors de la capture: {e}")
        
        if crop_rect:
            # Calculer les proportions entre le widget et la frame originale
            widget_size = self.video_widget.size()
            frame_height, frame_width = frame.shape[:2]
            
            # Facteurs d'échelle
            scale_x = frame_width / widget_size.width()
            scale_y = frame_height / widget_size.height()
            
            # Convertir les coordonnées du widget vers la frame originale
            x1 = int(crop_rect.x() * scale_x)
            y1 = int(crop_rect.y() * scale_y)
            x2 = int((crop_rect.x() + crop_rect.width()) * scale_x)
            y2 = int((crop_rect.y() + crop_rect.height()) * scale_y)
            
            # S'assurer que les coordonnées sont dans les limites
            x1 = max(0, min(x1, frame_width))
            y1 = max(0, min(y1, frame_height))
            x2 = max(0, min(x2, frame_width))
            y2 = max(0, min(y2, frame_height))
            
            # Extraire la zone
            if x2 > x1 and y2 > y1:
                # Forcer une copie contiguë de la mémoire après le découpage.
                # Le slicing NumPy peut retourner une "vue" non contiguë, ce qui cause une
                # TypeError avec QImage. .copy() résout ce problème.
                frame = frame[y1:y2, x1:x2].copy()
                print(f"✂️ Zone extraite: ({x1},{y1}) -> ({x2},{y2})")
            else:
                print("❌ Zone de capture invalide")
                self._capture_in_progress = False
                return
        
        # Convertir la frame (potentiellement recadrée) en QPixmap
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        final_pixmap = QPixmap.fromImage(q_image)
        
        self.frame_captured.emit(final_pixmap)
        print(f"✅ Frame OpenCV capturée: {final_pixmap.size()}")
        
        # Marquer la capture terminée
        self._capture_in_progress = False

    def keyPressEvent(self, event):
        # Transférer l'événement d'échappement à l'enfant s'il est en mode capture
        if self.video_widget.is_cropping and event.key() == Qt.Key.Key_Escape:
            self.video_widget.is_cropping = False # Arrêter le mode capture
            self.on_cropping_finished_by_child()
            print("🖱️ Sélection de zone annulée.")
            self.video_widget.update()
        else:
            super().keyPressEvent(event)

    def on_position_changed(self, position_ms):
        """Appelé quand la position change dans OpenCV (en millisecondes)."""
        if not self._player_initialized:
            return

        if not self.timeline.isSliderDown():
            self.timeline.blockSignals(True)
            self.timeline.setValue(position_ms)
            self.timeline.blockSignals(False)
            self.position_changed.emit(position_ms)

    def on_duration_changed(self, duration_ms):
        """Appelé quand la durée est connue (en millisecondes)."""
        self.duration = duration_ms
        self.timeline.setMaximum(duration_ms)
        print(f"⏱️ Durée OpenCV: {duration_ms}ms")

    def seek_forward(self):
        if not self._player_initialized:
            print("seek_forward: Player not initialized")
            return
        if self.video_thread.total_frames > 0:
            new_frame = min(self.video_thread.total_frames - 1, self.video_thread.current_frame + int(10 * self.video_thread.fps))
            self.video_thread.seek(new_frame)
            print("⏩ Avance de 10s")
    def seek_backward(self):
        if not self._player_initialized:
            print("seek_backward: Player not initialized")
            return
        if self.video_thread.total_frames > 0:
            new_frame = max(0, self.video_thread.current_frame - int(10 * self.video_thread.fps))
            self.video_thread.seek(new_frame)
        print("⏪ Recul de 10s")

    def resizeEvent(self, event):
        """Redessine lors du redimensionnement."""
        super().resizeEvent(event)
        self.update()

    def toggle_metadata_overlay(self, checked):
        """Affiche ou cache le panneau des métadonnées sur la vidéo."""
        self.video_widget.toggle_metadata(checked)

    def set_timeseries_data(self, data):
        """Définit les données temporelles (issues du CSV)."""
        self.timeseries_data = data
        self.last_timeseries_index = 0
        print(f"📈 Données temporelles reçues : {len(data)} points")

    def update_timeseries_metadata(self, position_ms):
        """Met à jour les métadonnées affichées en fonction de la position temporelle."""
        current_metadata = self.static_metadata.copy()
        
        if self.timeseries_data:
            # Réinitialiser si on a reculé
            if self.last_timeseries_index > 0 and self.last_timeseries_index < len(self.timeseries_data):
                if self.timeseries_data[self.last_timeseries_index].get('timestamp_ms', 0) > position_ms:
                    self.last_timeseries_index = 0
            
            # Avancer jusqu'au bon point
            while self.last_timeseries_index < len(self.timeseries_data) - 1:
                next_point = self.timeseries_data[self.last_timeseries_index + 1]
                if next_point.get('timestamp_ms', 0) <= position_ms:
                    self.last_timeseries_index += 1
                else:
                    break
            
            # Récupérer les données du point courant
            if 0 <= self.last_timeseries_index < len(self.timeseries_data):
                point = self.timeseries_data[self.last_timeseries_index]
                # Mapper les clés pour l'affichage
                if 'temperature' in point: current_metadata['temp'] = f"{point['temperature']}°C"
                if 'pression' in point: current_metadata['pression'] = f"{point['pression']} Bar"
                if 'lux' in point: current_metadata['lux'] = f"{point['lux']} Lux"

        self.video_widget.set_metadata(current_metadata)

    def update_metadata(self, **kwargs):
        """Reçoit les métadonnées STATIQUES (du JSON) et les stocke."""
        self.static_metadata = kwargs
        # On ne met pas à jour le widget directement, update_timeseries_metadata s'en charge
        print(f"ℹ️ Métadonnées statiques reçues: {self.static_metadata}")
        
    def add_timeline_marker(self, position):
        """Ajoute un marqueur rouge à la timeline à la position donnée (0-100)."""
        self.timeline.add_marker(position)
        
    def clear_timeline_markers(self):
        """Supprime tous les marqueurs de la timeline."""
        self.timeline.clear_markers()


# Test
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 700, 500)
    window.setStyleSheet("background-color: #1a1a1a;")
    
    player = VideoPlayer()
    
    player.play_pause_clicked.connect(lambda: print("▶️/⏸️ Play/Pause"))
    player.position_changed.connect(lambda pos: print(f"Position: {pos}ms"))
    player.controls.previous_clicked.connect(lambda: print("⏮️ Précédent"))
    player.controls.next_clicked.connect(lambda: print("⏭️ Suivant"))
    player.controls.speed_changed.connect(lambda s: print(f"⚡ Vitesse: {s}x"))
    player.detach_requested.connect(lambda: print("🪟 Détachement"))
    
    window.setCentralWidget(player)
    window.show()
    
    sys.exit(app.exec())