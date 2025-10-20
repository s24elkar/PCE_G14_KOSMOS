"""
Panneau du lecteur vidéo
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QSlider
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, pyqtSignal


class VideoPlayerPanel(QFrame):
    """Panneau du lecteur vidéo avec contrôles"""
    
    play_pause_clicked = pyqtSignal()
    restart_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    minus_10_clicked = pyqtSignal()
    plus_10_clicked = pyqtSignal()
    position_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Widget vidéo
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        layout.addWidget(self.video_widget)
        
        # Barre de progression
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setObjectName("videoSlider")
        self.position_slider.sliderMoved.connect(self.position_changed.emit)
        layout.addWidget(self.position_slider)
        
        # Contrôles de lecture
        controls_layout = QHBoxLayout()
        
        self.btn_restart = QPushButton("⟲")
        self.btn_prev = QPushButton("⏮")
        self.btn_play_pause = QPushButton("▶")
        self.btn_next = QPushButton("⏭")
        self.btn_plus_10 = QPushButton("+10s")
        self.btn_minus_10 = QPushButton("-10s")
        
        # Connexion des signaux
        self.btn_restart.clicked.connect(self.restart_clicked.emit)
        self.btn_prev.clicked.connect(self.prev_clicked.emit)
        self.btn_play_pause.clicked.connect(self.play_pause_clicked.emit)
        self.btn_next.clicked.connect(self.next_clicked.emit)
        self.btn_plus_10.clicked.connect(self.plus_10_clicked.emit)
        self.btn_minus_10.clicked.connect(self.minus_10_clicked.emit)
        
        for btn in [self.btn_restart, self.btn_prev, self.btn_play_pause, 
                    self.btn_next, self.btn_plus_10, self.btn_minus_10]:
            btn.setObjectName("controlButton")
            controls_layout.addWidget(btn)
        
        layout.addLayout(controls_layout)
    
    def set_play_pause_text(self, text):
        """Définit le texte du bouton play/pause"""
        self.btn_play_pause.setText(text)
    
    def update_slider_position(self, position):
        """Met à jour la position du slider"""
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
    
    def set_slider_range(self, min_val, max_val):
        """Définit la plage du slider"""
        self.position_slider.setRange(min_val, max_val)