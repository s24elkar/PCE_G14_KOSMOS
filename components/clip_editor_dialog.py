"""
Fenêtre de dialogue pour éditer et enregistrer un extrait vidéo.
Affiche la vidéo complète avec une timeline et des poignées de sélection.
"""
import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit, QWidget
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from .lecteur import VideoPlayer


class ClipEditorDialog(QDialog):
    """
    Dialogue qui affiche la vidéo complète et permet de sélectionner
    une plage avec des poignées sur la timeline.
    """
    def __init__(self, video_path, initial_start_ms, initial_end_ms, filters=None, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.initial_start_ms = initial_start_ms
        self.initial_end_ms = initial_end_ms
        self.filters = filters or {}

        self.setWindowTitle("Éditeur d'Extrait Vidéo")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: black; color: white;")

        self.init_ui()

        if not self.video_path:
            QMessageBox.critical(self, "Erreur", "Aucun chemin de vidéo fourni.")
            self.reject()
        else:
            # Appliquer les filtres
            if self.filters:
                for name, (func, kwargs) in self.filters.items():
                    self.video_player.toggle_filter(name, func, True, **kwargs)

            # On charge la vidéo en demandant de ne pas la mettre en pause
            self.video_player.load_video(self.video_path)
            self.video_player.pause()
            # On connecte le signal duration_changed du thread vidéo.
            self.video_player.video_thread.duration_changed.connect(self.setup_selection_handles)
            # On connecte position_changed pour forcer la boucle dans la sélection.
            self.video_player.video_thread.position_changed.connect(self.check_playback_bounds)


    def init_ui(self):
        """Initialise l'interface utilisateur du dialogue."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Lecteur vidéo
        self.video_player = VideoPlayer()
        self.timeline = self.video_player.timeline

        # Connecter le signal de changement de sélection à deux slots
        self.timeline.selection_changed.connect(self.update_time_labels) # Pour les labels de temps
        self.timeline.selection_changed.connect(self.preview_frame_at_handle) # Pour l'aperçu visuel
        main_layout.addWidget(self.video_player, stretch=1)

        # Panneau de contrôle en bas de la fenêtre
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(10)

        # Champ pour renseigner le nom
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom de l'extrait :")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez le nom (sans extension)")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        control_layout.addLayout(name_layout)

        # Affichage des temps de début et de fin
        time_display_layout = QHBoxLayout()
        time_display_layout.addWidget(QLabel("Début :"))
        self.start_time_label = QLabel("00:00.000")
        self.start_time_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        time_display_layout.addWidget(self.start_time_label)
        time_display_layout.addStretch()
        time_display_layout.addWidget(QLabel("Fin :"))
        self.end_time_label = QLabel("00:00.000")
        self.end_time_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        time_display_layout.addWidget(self.end_time_label)
        control_layout.addLayout(time_display_layout)

        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)
        btn_save = QPushButton("Enregistrer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.on_accept)
        button_layout.addWidget(btn_save)
        control_layout.addLayout(button_layout)

        main_layout.addWidget(control_panel)


    def setup_selection_handles(self, duration_ms):
        """Configure les poignées de sélection une fois la durée de la vidéo connue."""
        if duration_ms <= 0: return

        # Initialiser la timeline avec les poignées de sélection
        self.timeline.selection_mode = True
        start_ratio = self.initial_start_ms / duration_ms
        end_ratio = self.initial_end_ms / duration_ms

        # Positionner les poignées de sélection
        self.timeline.start_handle_pos = int(start_ratio * 1000)
        self.timeline.end_handle_pos = int(end_ratio * 1000)
        self.timeline.update()

        # Mettre à jour les labels une première fois
        self.update_time_labels(self.timeline.start_handle_pos, self.timeline.end_handle_pos)
        
        # On attend un court instant que la fenêtre soit bien affichée avant de se positionner et de jouer
        QTimer.singleShot(100, self.start_playback_at_selection)


    def start_playback_at_selection(self):
        """Se positionne au début de la sélection et lance la lecture."""
        target_frame = int((self.initial_start_ms / self.video_player.duration) * self.video_player.video_thread.total_frames)
        self.video_player.video_thread.seek(target_frame)
        self.video_player.video_thread.play()
        

    def update_time_labels(self, start_pos_1000, end_pos_1000):
        """Met à jour les labels de temps quand les poignées bougent."""
        duration_ms = self.video_player.duration
        if duration_ms <= 0: return

        start_ms = int((start_pos_1000 / 1000.0) * duration_ms)
        end_ms = int((end_pos_1000 / 1000.0) * duration_ms)

        self.start_time_label.setText(f"{start_ms // 60000:02d}:{(start_ms % 60000) // 1000:02d}.{start_ms % 1000:03d}")
        self.end_time_label.setText(f"{end_ms // 60000:02d}:{(end_ms % 60000) // 1000:02d}.{end_ms % 1000:03d}")


    def preview_frame_at_handle(self, start_pos_1000, end_pos_1000):
        """
        Met à jour l'image affichée pour correspondre à la position de la poignée
        en cours de déplacement.
        """
        # Mettre la vidéo en pause si ce n'est pas déjà fait
        if not self.video_player.video_thread.is_paused:
            self.video_player.video_thread.pause()

        duration_ms = self.video_player.duration
        if duration_ms <= 0: return

        # Déterminer quelle poignée est en train d'être déplacée
        handle_being_dragged = self.timeline.dragging_handle # 'start' ou 'end'
        
        if handle_being_dragged == 'start':
            target_ms = int((start_pos_1000 / 1000.0) * duration_ms)
        elif handle_being_dragged == 'end':
            target_ms = int((end_pos_1000 / 1000.0) * duration_ms)
        else:
            return # Aucune poignée n'est déplacée
        
        # Calculer le frame correspondant à la position en ms
        target_frame = int((target_ms / duration_ms) * self.video_player.video_thread.total_frames)
        # Se positionner sur le frame correspondant
        self.video_player.video_thread.seek(target_frame)


    def check_playback_bounds(self, position_ms):
        """
        Vérifie que la tête de lecture reste dans la plage de sélection.
        Si elle dépasse la fin, elle revient au début pour créer un effet de boucle.
        """
        if not self.timeline.selection_mode or self.video_player.duration <= 0:
            return

        # Obtenir les bornes de la sélection en millisecondes
        _, start_ms, end_ms = self.get_values()

        if position_ms >= end_ms:
            # Si on dépasse la fin, on revient au début de la sélection
            target_frame = int((start_ms / self.video_player.duration) * self.video_player.video_thread.total_frames)
            self.video_player.video_thread.seek(target_frame)


    def get_values(self):
        """Retourne le nom, et les temps de début/fin en ms."""
        name = self.name_input.text().strip()
        duration_ms = self.video_player.duration
        start_ms = int((self.timeline.start_handle_pos / 1000.0) * duration_ms)
        end_ms = int((self.timeline.end_handle_pos / 1000.0) * duration_ms)
        return name, start_ms, end_ms
    

    def on_accept(self):
        """Vérifie le nom avant d'accepter."""
        name, start_ms, end_ms = self.get_values()
        if not name:
            QMessageBox.warning(self, "Nom manquant", "Veuillez entrer un nom pour l'enregistrement.")
            return
        if start_ms >= end_ms:
            QMessageBox.warning(self, "Plage invalide", "La borne de début doit être avant la borne de fin.")
            return
        self.accept()
        
        
    def closeEvent(self, event):
        """S'assure que le lecteur est arrêté à la fermeture."""
        if self.video_player and self.video_player.video_thread:
            self.video_player.video_thread.stop()
            self.video_player.video_thread.wait(500) # Attendre un peu que le thread se termine
        super().closeEvent(event)