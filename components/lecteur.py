"""
Composant Lecteur Vidéo
Lecteur avec timeline, contrôles et affichage des métadonnées
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QUrl, QSize, QRectF
from PyQt6.QtGui import QColor, QPalette, QPainter, QPen, QPixmap, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoFrame
from PyQt6.QtMultimediaWidgets import QVideoWidget
from pathlib import Path


class MetadataOverlay(QWidget):
    """Overlay pour afficher les métadonnées de la vidéo"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setSpacing(2)
        
        # Style pour les labels
        label_style = """
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 3px 10px;
                border-radius: 0px;
                font-family: Arial;
            }
        """
        
        self.time_label = QLabel("⏰ Time : 13:06")
        self.time_label.setStyleSheet(label_style)
        layout.addWidget(self.time_label)
        
        self.temp_label = QLabel("🌡️ Temp : 15°C")
        self.temp_label.setStyleSheet(label_style)
        layout.addWidget(self.temp_label)
        
        self.salinity_label = QLabel("💧 Salinity : xx")
        self.salinity_label.setStyleSheet(label_style)
        layout.addWidget(self.salinity_label)
        
        self.depth_label = QLabel("📏 Depth : 10 m")
        self.depth_label.setStyleSheet(label_style)
        layout.addWidget(self.depth_label)
        
        self.pression_label = QLabel("⚖️ Pression : xx bar")
        self.pression_label.setStyleSheet(label_style)
        layout.addWidget(self.pression_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
    def update_metadata(self, time=None, temp=None, salinity=None, depth=None, pression=None):
        """Met à jour les métadonnées affichées"""
        if time is not None:
            self.time_label.setText(f"⏰ Time : {time}")
        if temp is not None:
            self.temp_label.setText(f"🌡️ Temp : {temp}")
        if salinity is not None:
            self.salinity_label.setText(f"💧 Salinity : {salinity}")
        if depth is not None:
            self.depth_label.setText(f"📏 Depth : {depth}")
        if pression is not None:
            self.pression_label.setText(f"⚖️ Pression : {pression}")


class VideoTimeline(QWidget):
    """Timeline avec marqueurs rouges pour les points clés"""
    
    position_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.markers = []
        self.current_value = 0
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.setFixedHeight(30)
        
        self.slider.setStyleSheet("""
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
        
        layout.addWidget(self.slider)
        self.setLayout(layout)
        
    def _on_value_changed(self, value):
        self.current_value = value
        self.update()
        self.position_changed.emit(value)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        groove_rect = self.slider.geometry()
        groove_y = groove_rect.height() // 2
        groove_left = 10
        groove_right = self.slider.width() - 10
        groove_width = groove_right - groove_left
        
        for marker_pos in self.markers:
            x = groove_left + (marker_pos / 100.0) * groove_width
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0))
            marker_rect = QRect(int(x - 2), groove_y - 3, 4, 6)
            painter.drawRect(marker_rect)
        
    def add_marker(self, position):
        if 0 <= position <= 100:
            self.markers.append(position)
            self.update()
            
    def clear_markers(self):
        self.markers.clear()
        self.update()
        
    def get_position(self):
        return self.slider.value()
        
    def set_position(self, position):
        self.slider.setValue(position)


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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_speed = 1.0
        self.is_playing = False
        
        # Chemins des icônes
        self.icons_path = Path(__file__).parent.parent / "assets" / "icons"
        self.play_icon_path = self.icons_path / "start.png"
        self.pause_icon_path = self.icons_path / "Pause.png"
        self.speed_icon_path = self.icons_path / "vitesse.png"
        
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
        self.btn_previous = QPushButton("⏮️")
        self.btn_previous.setFixedSize(45, 45)
        self.btn_previous.setStyleSheet(button_style)
        self.btn_previous.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_previous.setToolTip("Vidéo précédente")
        self.btn_previous.clicked.connect(self.previous_clicked.emit)
        layout.addWidget(self.btn_previous)
        
        # Bouton Reculer
        self.btn_rewind = QPushButton("-10s")
        self.btn_rewind.setFixedSize(45, 45)
        self.btn_rewind.setStyleSheet(button_style)
        self.btn_rewind.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rewind.setToolTip("Reculer de 10 secondes")
        self.btn_rewind.clicked.connect(self.rewind_clicked.emit)
        layout.addWidget(self.btn_rewind)
        
        # Bouton Play/Pause avec icône personnalisée
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(45, 45)  # Réduit de 55 à 45
        self.play_pause_btn.setStyleSheet(button_style)
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_pause_btn.setToolTip("Lecture / Pause")
        self.play_pause_btn.clicked.connect(self.on_play_pause_clicked)
        self.update_play_pause_icon()
        layout.addWidget(self.play_pause_btn)
        
        # Bouton Avancer
        self.btn_forward = QPushButton("+10s")
        self.btn_forward.setFixedSize(45, 45)
        self.btn_forward.setStyleSheet(button_style)
        self.btn_forward.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_forward.setToolTip("Avancer de 10 secondes")
        self.btn_forward.clicked.connect(self.forward_clicked.emit)
        layout.addWidget(self.btn_forward)
        
        # Bouton Vidéo suivante
        self.btn_next = QPushButton("⏭️")
        self.btn_next.setFixedSize(45, 45)
        self.btn_next.setStyleSheet(button_style)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setToolTip("Vidéo suivante")
        self.btn_next.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self.btn_next)
        
        layout.addSpacing(20)
        
        # Bouton de vitesse avec icône personnalisée
        self.btn_speed = QPushButton(f"{self.current_speed}x")
        self.btn_speed.setFixedSize(70, 45)
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
        self.btn_detach.setFixedSize(45, 45)
        self.btn_detach.setStyleSheet(button_style)
        self.btn_detach.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detach.setToolTip("Détacher dans une nouvelle fenêtre")
        self.btn_detach.clicked.connect(self.detach_clicked.emit)
        layout.addWidget(self.btn_detach)
        
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
        self.is_playing = not self.is_playing
        self.update_play_pause_icon()
        self.play_pause_clicked.emit()
    
    def toggle_speed(self):
        speeds = [1.0, 1.5, 2.0, 0.5]
        current_index = speeds.index(self.current_speed)
        next_index = (current_index + 1) % len(speeds)
        self.current_speed = speeds[next_index]
        
        self.btn_speed.setText(f"{self.current_speed}x")
        self.speed_changed.emit(self.current_speed)
        print(f"⚡ Vitesse changée : {self.current_speed}x")
    
    def update_play_pause_button(self, is_playing):
        self.is_playing = is_playing
        self.update_play_pause_icon()


class VideoPlayer(QWidget):
    """Composant Lecteur Vidéo"""
    
    # Signaux
    play_pause_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)
    frame_captured = pyqtSignal(QPixmap)
    detach_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0
        self.media_player = None
        self.audio_output = None
        self._player_initialized = False
        self.playback_speed = 1.0
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone vidéo avec overlay
        video_container = QFrame()
        video_container.setMinimumHeight(300)  # Réduit de 350 à 300
        video_container.setStyleSheet("""
            QFrame {
                background-color: black;
                border: 3px solid black;
            }
        """)
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget vidéo réel
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        
        # Overlay de métadonnées
        self.metadata_overlay = MetadataOverlay(self.video_widget)
        
        # Bouton plein écran
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedSize(35, 35)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(42, 42, 42, 200);
                color: white;
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(58, 58, 58, 220);
                border-color: rgba(255, 255, 255, 150);
            }
        """)
        self.fullscreen_btn.setParent(self.video_widget)
        
        video_layout.addWidget(self.video_widget)
        video_container.setLayout(video_layout)
        
        # Utiliser stretch pour que la vidéo s'adapte mais laisse de la place aux contrôles
        main_layout.addWidget(video_container, stretch=1)
        
        # Timeline avec hauteur fixe réduite pour rester visible
        timeline_container = QWidget()
        timeline_container.setFixedHeight(35)  # Réduit de 45 à 35
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(10, 5, 10, 5)  # Marges réduites
        timeline_layout.setSpacing(0)
        
        self.timeline = VideoTimeline()
        self.timeline.position_changed.connect(self.on_timeline_moved)
        timeline_layout.addWidget(self.timeline)
        
        timeline_container.setLayout(timeline_layout)
        timeline_container.setStyleSheet("background-color: black;")
        main_layout.addWidget(timeline_container, stretch=0)
        
        # Contrôles avec hauteur fixe réduite pour rester visibles
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
        
        controls_layout.addWidget(self.controls)
        controls_container.setLayout(controls_layout)
        main_layout.addWidget(controls_container, stretch=0)
        
        self.setLayout(main_layout)
        self.setObjectName("VideoPlayer")
        self.setStyleSheet("""
            #VideoPlayer {
                background-color: black;
                border: 3px solid black;
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._player_initialized:
            self.setup_player()

    def setup_player(self):
        if self._player_initialized:
            return
            
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self._player_initialized = True
        
        print("✅ Lecteur vidéo initialisé")

    def load_video(self, file_path):
        if not self._player_initialized:
            self.setup_player()
            
        url = QUrl.fromLocalFile(file_path)
        self.media_player.setSource(url)
        self.media_player.setPlaybackRate(self.playback_speed)
        self.media_player.pause()
        self.controls.update_play_pause_button(False)
        
        print(f"📹 Vidéo chargée : {file_path}")

    def on_speed_changed(self, speed: float):
        self.playback_speed = speed
        if self.media_player:
            self.media_player.setPlaybackRate(speed)
            print(f"⚡ Vitesse appliquée : {speed}x")
    
    def on_detach_player(self):
        print("🗗 Détachement demandé")
        self.detach_requested.emit()

    def toggle_play_pause(self):
        if not self._player_initialized:
            return

        if self.controls.is_playing:
            self.media_player.play()
        else:
            self.media_player.pause()
        
        self.play_pause_clicked.emit()

    def grab_frame(self) -> None:
        if not self._player_initialized:
            print("❌ Lecteur non initialisé")
            return

        if not self.video_widget.isVisible() or self.video_widget.size().isEmpty():
            print("❌ Widget vidéo non visible")
            return

        was_playing = self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if was_playing:
            self.media_player.pause()

        QTimer.singleShot(150, lambda: self._capture_and_resume(was_playing))

    def _capture_and_resume(self, resume_playing):
        video_frame = self.media_player.videoSink().videoFrame()
        if video_frame.isValid():
            image = video_frame.toImage()
            pixmap = QPixmap.fromImage(image)
            self.frame_captured.emit(pixmap)
            print("✅ Frame capturée")
        else:
            print("❌ Frame invalide")

        if resume_playing:
            self.media_player.play()

    def on_position_changed(self, position):
        if not self._player_initialized:
            return

        if self.duration > 0:
            slider_pos = int((position / self.duration) * 1000)
            self.timeline.slider.blockSignals(True)
            self.timeline.set_position(slider_pos)
            self.timeline.slider.blockSignals(False)
            
        self.position_changed.emit(position)

    def on_duration_changed(self, duration):
        self.duration = duration

    def on_timeline_moved(self, value):
        if not self._player_initialized:
            return

        if self.duration > 0:
            position = int((value / 1000) * self.duration)
            self.media_player.setPosition(position)

    def seek_backward(self):
        if not self._player_initialized:
            return
        self.media_player.setPosition(max(0, self.media_player.position() - 10000))
        print("⏪ Recul de 10s")

    def seek_forward(self):
        if not self._player_initialized:
            return
        self.media_player.setPosition(min(self.duration, self.media_player.position() + 10000))
        print("⏩ Avance de 10s")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'metadata_overlay'):
            self.metadata_overlay.setGeometry(0, 0, self.video_widget.width(), self.video_widget.height())
        if hasattr(self, 'fullscreen_btn'):
            btn_x = self.video_widget.width() - self.fullscreen_btn.width() - 10
            btn_y = self.video_widget.height() - self.fullscreen_btn.height() - 10
            self.fullscreen_btn.move(btn_x, btn_y)
            
    def update_metadata(self, **kwargs):
        self.metadata_overlay.update_metadata(**kwargs)
        
    def add_timeline_marker(self, position):
        self.timeline.add_marker(position)
        
    def clear_timeline_markers(self):
        self.timeline.clear_markers()
    
    def on_media_status_changed(self, status):
        if not self._player_initialized:
            return

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.controls.update_play_pause_button(False)
            print("📹 Fin de la vidéo")


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