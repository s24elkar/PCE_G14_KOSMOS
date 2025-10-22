"""
Composant Lecteur Vidéo
Lecteur avec timeline, contrôles et affichage des métadonnées
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette


class MetadataOverlay(QWidget):
    """Overlay pour afficher les métadonnées de la vidéo"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Style pour les labels
        label_style = """
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 500;
                background-color: rgba(255, 105, 180, 0.8);
                padding: 2px 8px;
                border-radius: 3px;
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
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Slider personnalisé
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(0)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #1a1a1a;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid #2196F3;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2196F3;
            }
        """)
        self.slider.valueChanged.connect(self.position_changed.emit)
        
        layout.addWidget(self.slider)
        self.setLayout(layout)
        
        # Ajouter des marqueurs par défaut
        self.add_marker(15)
        self.add_marker(30)
        self.add_marker(45)
        self.add_marker(60)
        self.add_marker(75)
        
    def add_marker(self, position):
        """Ajoute un marqueur à une position (0-100)"""
        if 0 <= position <= 100:
            self.markers.append(position)
            
    def clear_markers(self):
        """Supprime tous les marqueurs"""
        self.markers.clear()
        
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
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Style des boutons
        button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """
        
        # Bouton précédent
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setStyleSheet(button_style)
        self.prev_btn.clicked.connect(self.previous_clicked.emit)
        layout.addWidget(self.prev_btn)
        
        # Bouton reculer 10s
        self.rewind_btn = QPushButton("-10s")
        self.rewind_btn.setStyleSheet(button_style)
        self.rewind_btn.clicked.connect(self.rewind_clicked.emit)
        layout.addWidget(self.rewind_btn)
        
        # Bouton play/pause
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setStyleSheet(button_style)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        layout.addWidget(self.play_pause_btn)
        
        # Bouton avancer 10s
        self.forward_btn = QPushButton("+10s")
        self.forward_btn.setStyleSheet(button_style)
        self.forward_btn.clicked.connect(self.forward_clicked.emit)
        layout.addWidget(self.forward_btn)
        
        # Bouton suivant
        self.next_btn = QPushButton("⏭")
        self.next_btn.setStyleSheet(button_style)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self.next_btn)
        
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
        video_container = QWidget()
        video_container.setMinimumHeight(400)
        video_layout = QVBoxLayout()
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame vidéo (placeholder avec image de fond simulée)
        self.video_frame = QLabel()
        self.video_frame.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a5568, stop:0.5 #667c99, stop:1 #8ba3c7);
                border: 2px solid white;
            }
        """)
        self.video_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Overlay de métadonnées
        self.metadata_overlay = MetadataOverlay(self.video_frame)
        
        video_layout.addWidget(self.video_frame)
        video_container.setLayout(video_layout)
        
        main_layout.addWidget(video_container)
        
        # Timeline
        self.timeline = VideoTimeline()
        self.timeline.position_changed.connect(self.position_changed.emit)
        timeline_container = QWidget()
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(10, 0, 10, 0)
        timeline_layout.addWidget(self.timeline)
        timeline_container.setLayout(timeline_layout)
        timeline_container.setStyleSheet("background-color: black;")
        main_layout.addWidget(timeline_container)
        
        # Contrôles
        self.controls = VideoControls()
        self.controls.play_pause_clicked.connect(self.play_pause_clicked.emit)
        main_layout.addWidget(self.controls)
        
        # Bouton plein écran en bas à droite
        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setFixedSize(30, 30)
        fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 1px solid white;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 200);
            }
        """)
        fullscreen_btn.setParent(self.video_frame)
        fullscreen_btn.move(self.video_frame.width() - 40, self.video_frame.height() - 40)
        
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: black;
                border: 2px solid white;
            }
        """)
        
    def resizeEvent(self, event):
        """Redimensionne l'overlay quand le widget change de taille"""
        super().resizeEvent(event)
        if hasattr(self, 'metadata_overlay'):
            self.metadata_overlay.setGeometry(0, 0, self.video_frame.width(), self.video_frame.height())
            
    def update_metadata(self, **kwargs):
        """Met à jour les métadonnées affichées"""
        self.metadata_overlay.update_metadata(**kwargs)
        
    def set_position(self, position):
        """Définit la position de lecture (0-1000)"""
        self.timeline.set_position(position)
        
    def get_position(self):
        """Retourne la position actuelle (0-1000)"""
        return self.timeline.get_position()


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 900, 600)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    player = VideoPlayer()
    
    # Connecter les signaux
    player.play_pause_clicked.connect(lambda: print("▶/⏸ Play/Pause"))
    player.position_changed.connect(lambda pos: print(f"Position: {pos}"))
    
    window.setCentralWidget(player)
    window.show()
    
    sys.exit(app.exec())