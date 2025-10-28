"""
Composant Lecteur Vidéo
Lecteur avec timeline, contrôles et affichage des métadonnées
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect
from PyQt6.QtGui import QColor, QPalette, QPainter, QPen


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
        
        # Style pour les labels - fond rose semi-transparent
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
        
        self.time_label = QLabel("Time : 13:06")
        self.time_label.setStyleSheet(label_style)
        layout.addWidget(self.time_label)
        
        self.temp_label = QLabel("Temp : 15°C")
        self.temp_label.setStyleSheet(label_style)
        layout.addWidget(self.temp_label)
        
        self.salinity_label = QLabel("Salinity : xx")
        self.salinity_label.setStyleSheet(label_style)
        layout.addWidget(self.salinity_label)
        
        self.depth_label = QLabel("Depth : 10 m")
        self.depth_label.setStyleSheet(label_style)
        layout.addWidget(self.depth_label)
        
        self.pression_label = QLabel("Pression : xx bar")
        self.pression_label.setStyleSheet(label_style)
        layout.addWidget(self.pression_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
    def update_metadata(self, time=None, temp=None, salinity=None, depth=None, pression=None):
        """Met à jour les métadonnées affichées"""
        if time is not None:
            self.time_label.setText(f"Time : {time}")
        if temp is not None:
            self.temp_label.setText(f"Temp : {temp}")
        if salinity is not None:
            self.salinity_label.setText(f"Salinity : {salinity}")
        if depth is not None:
            self.depth_label.setText(f"Depth : {depth}")
        if pression is not None:
            self.pression_label.setText(f"Pression : {pression}")


class VideoTimeline(QWidget):
    """Timeline avec marqueurs rouges pour les points clés"""
    
    position_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.markers = []  # Positions des marqueurs (0-100)
        self.current_value = 0
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Slider personnalisé (invisible, juste pour la logique)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.setFixedHeight(30)
        
        # Style du slider avec marqueurs
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
        
        # Ajouter des marqueurs par défaut (positions en pourcentage)
        #self.add_marker(15)
        #self.add_marker(30)
        #self.add_marker(50)
        #self.add_marker(70)
        #self.add_marker(85)
        
    def _on_value_changed(self, value):
        """Gère le changement de valeur"""
        self.current_value = value
        self.update()
        self.position_changed.emit(value)
        
    def paintEvent(self, event):
        """Dessine les marqueurs rouges sur la timeline"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Récupérer les dimensions du groove
        groove_rect = self.slider.geometry()
        groove_y = groove_rect.height() // 2
        groove_left = 10  # Marge gauche
        groove_right = self.slider.width() - 10  # Marge droite
        groove_width = groove_right - groove_left
        
        # Dessiner les marqueurs rouges
        for marker_pos in self.markers:
            # Calculer la position X du marqueur
            x = groove_left + (marker_pos / 100.0) * groove_width
            
            # Dessiner un petit rectangle rouge
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 0, 0))
            marker_rect = QRect(int(x - 2), groove_y - 3, 4, 6)
            painter.drawRect(marker_rect)
        
    def add_marker(self, position):
        """Ajoute un marqueur à une position (0-100)"""
        if 0 <= position <= 100:
            self.markers.append(position)
            self.update()
            
    def clear_markers(self):
        """Supprime tous les marqueurs"""
        self.markers.clear()
        self.update()
        
    def get_position(self):
        """Retourne la position actuelle (0-1000)"""
        return self.slider.value()
        
    def set_position(self, position):
        """Définit la position (0-1000)"""
        self.slider.setValue(position)


class VideoControls(QWidget):
    """Contrôles de lecture vidéo"""
    
    play_pause_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    rewind_clicked = pyqtSignal()
    forward_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_playing = False
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Style des boutons - fond gris foncé avec bordure
        button_style = """
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """
        
        # Bouton précédent
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(45, 35)
        self.prev_btn.setStyleSheet(button_style)
        self.prev_btn.clicked.connect(self.previous_clicked.emit)
        layout.addWidget(self.prev_btn)
        
        # Bouton reculer 10s
        self.rewind_btn = QPushButton("-10s")
        self.rewind_btn.setFixedSize(55, 35)
        self.rewind_btn.setStyleSheet(button_style)
        self.rewind_btn.clicked.connect(self.rewind_clicked.emit)
        layout.addWidget(self.rewind_btn)
        
        # Bouton play/pause (plus grand)
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setFixedSize(45, 35)
        self.play_pause_btn.setStyleSheet(button_style + """
            QPushButton {
                font-size: 16px;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        layout.addWidget(self.play_pause_btn)
        
        # Bouton avancer 10s
        self.forward_btn = QPushButton("+10s")
        self.forward_btn.setFixedSize(55, 35)
        self.forward_btn.setStyleSheet(button_style)
        self.forward_btn.clicked.connect(self.forward_clicked.emit)
        layout.addWidget(self.forward_btn)
        
        # Espacement
        layout.addStretch()
        
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        
    def toggle_play_pause(self):
        """Bascule entre lecture et pause"""
        self.is_playing = not self.is_playing
        self.play_pause_btn.setText("⏸" if self.is_playing else "▶")
        self.play_pause_clicked.emit()


class VideoPlayer(QWidget):
    """
    Composant Lecteur Vidéo
    Lecteur avec overlay de métadonnées, timeline et contrôles
    """
    
    # Signaux
    play_pause_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Zone vidéo avec overlay
        video_container = QFrame()
        video_container.setMinimumHeight(400)
        video_container.setStyleSheet("""
            QFrame {
                background-color: black;
                border: 3px solid black;
            }
        """)
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame vidéo (placeholder avec dégradé)
        self.video_frame = QLabel()
        self.video_frame.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a5568, stop:0.5 #667c99, stop:1 #8ba3c7);
                border: none;
            }
        """)
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Overlay de métadonnées
        self.metadata_overlay = MetadataOverlay(self.video_frame)
        
        # Bouton plein écran en bas à droite
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
        self.fullscreen_btn.setParent(self.video_frame)
        
        video_layout.addWidget(self.video_frame)
        video_container.setLayout(video_layout)
        
        main_layout.addWidget(video_container)
        
        # Timeline avec fond noir
        timeline_container = QWidget()
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(15, 8, 15, 8)
        timeline_layout.setSpacing(0)
        
        self.timeline = VideoTimeline()
        self.timeline.position_changed.connect(self.position_changed.emit)
        timeline_layout.addWidget(self.timeline)
        
        timeline_container.setLayout(timeline_layout)
        timeline_container.setStyleSheet("background-color: black;")
        main_layout.addWidget(timeline_container)
        
        # Contrôles
        self.controls = VideoControls()
        self.controls.play_pause_clicked.connect(self.play_pause_clicked.emit)
        main_layout.addWidget(self.controls)
        
        self.setLayout(main_layout)
        self.setObjectName("VideoPlayer")
        self.setStyleSheet("""
            #VideoPlayer {
                background-color: black;
                border: 3px solid black;
            }
        """)
        
    def resizeEvent(self, event):
        """Redimensionne l'overlay et le bouton plein écran quand le widget change de taille"""
        super().resizeEvent(event)
        if hasattr(self, 'metadata_overlay'):
            self.metadata_overlay.setGeometry(0, 0, self.video_frame.width(), self.video_frame.height())
        if hasattr(self, 'fullscreen_btn'):
            # Positionner le bouton en bas à droite
            btn_x = self.video_frame.width() - self.fullscreen_btn.width() - 10
            btn_y = self.video_frame.height() - self.fullscreen_btn.height() - 10
            self.fullscreen_btn.move(btn_x, btn_y)
            
    def update_metadata(self, **kwargs):
        """Met à jour les métadonnées affichées"""
        self.metadata_overlay.update_metadata(**kwargs)
        
    def set_position(self, position):
        """Définit la position de lecture (0-1000)"""
        self.timeline.set_position(position)
        
    def get_position(self):
        """Retourne la position actuelle (0-1000)"""
        return self.timeline.get_position()
        
    def add_timeline_marker(self, position):
        """Ajoute un marqueur rouge sur la timeline (0-100)"""
        self.timeline.add_marker(position)
        
    def clear_timeline_markers(self):
        """Supprime tous les marqueurs de la timeline"""
        self.timeline.clear_markers()


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 700, 500)
    window.setStyleSheet("background-color: #1a1a1a;")
    
    player = VideoPlayer()
    
    # Connecter les signaux
    player.play_pause_clicked.connect(lambda: print("▶/⏸ Play/Pause"))
    player.position_changed.connect(lambda pos: print(f"Position: {pos}"))
    player.controls.previous_clicked.connect(lambda: print("⏮ Précédent"))
    player.controls.next_clicked.connect(lambda: print("⏭ Suivant"))
    player.controls.rewind_clicked.connect(lambda: print("◀ -10s"))
    player.controls.forward_clicked.connect(lambda: print("▶ +10s"))
    
    window.setCentralWidget(player)
    window.show()
    
    sys.exit(app.exec())