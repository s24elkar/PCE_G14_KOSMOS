"""
Contrôleur pour gérer les interactions média
"""
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import QFileDialog


class MediaController:
    """Contrôleur gérant les interactions entre le modèle et la vue"""
    
    def __init__(self, model, view):
        self.model = model
        self.view = view
        
        # Initialisation du lecteur multimédia
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.view.video_player.video_widget)
        
        self._is_playing = False
        
        # Connexion des signaux
        self._connect_signals()
    
    def _connect_signals(self):
        """Connecte les signaux de la vue aux slots du contrôleur"""
        
        # Signaux du panneau média explorer
        self.view.media_explorer.load_requested.connect(self.load_media)
        
        # Signaux du lecteur vidéo
        self.view.video_player.play_pause_clicked.connect(self.toggle_play_pause)
        self.view.video_player.restart_clicked.connect(self.restart)
        self.view.video_player.prev_clicked.connect(lambda: self.seek_relative(-5000))
        self.view.video_player.next_clicked.connect(lambda: self.seek_relative(5000))
        self.view.video_player.minus_10_clicked.connect(lambda: self.seek_relative(-10000))
        self.view.video_player.plus_10_clicked.connect(lambda: self.seek_relative(10000))
        self.view.video_player.position_changed.connect(self.set_position)
        
        # Signaux du panneau de correction
        self.view.correction_panel.brightness_changed.connect(self.update_brightness)
        self.view.correction_panel.contrast_changed.connect(self.update_contrast)
        self.view.correction_panel.saturation_changed.connect(self.update_saturation)
        
        # Signaux du lecteur multimédia
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        
        # Action menu
        self.view.open_action.triggered.connect(self.load_media)
        self.view.quit_action.triggered.connect(self.view.close)
    
    def load_media(self):
        """Charge un fichier média"""
        file_name, _ = QFileDialog.getOpenFileName(
            self.view,
            "Ouvrir un fichier vidéo",
            "",
            "Vidéos (*.mp4 *.avi *.mkv *.mov);;Tous les fichiers (*.*)"
        )
        
        if file_name:
            self.model.current_file = file_name
            self.player.setSource(QUrl.fromLocalFile(file_name))
            self.player.play()
            self._is_playing = True
            self.view.video_player.set_play_pause_text("⏸")
    
    def toggle_play_pause(self):
        """Bascule entre lecture et pause"""
        if self._is_playing:
            self.player.pause()
            self.view.video_player.set_play_pause_text("▶")
        else:
            self.player.play()
            self.view.video_player.set_play_pause_text("⏸")
        self._is_playing = not self._is_playing
    
    def restart(self):
        """Redémarre la vidéo"""
        self.player.setPosition(0)
    
    def seek_relative(self, ms):
        """Avance ou recule de ms millisecondes"""
        new_pos = self.player.position() + ms
        self.player.setPosition(max(0, min(new_pos, self.player.duration())))
    
    def set_position(self, position):
        """Définit la position de lecture"""
        self.player.setPosition(position)
    
    def on_position_changed(self, position):
        """Gère le changement de position"""
        self.view.video_player.update_slider_position(position)
    
    def on_duration_changed(self, duration):
        """Gère le changement de durée"""
        self.view.video_player.set_slider_range(0, duration)
    
    def update_brightness(self, value):
        """Met à jour la luminosité"""
        self.model.brightness = value
        self.view.correction_panel.update_brightness_label(value)
    
    def update_contrast(self, value):
        """Met à jour le contraste"""
        self.model.contrast = value
        self.view.correction_panel.update_contrast_label(value)
    
    def update_saturation(self, value):
        """Met à jour la saturation"""
        self.model.saturation = value
        self.view.correction_panel.update_saturation_label(value)