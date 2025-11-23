"""
Fenêtre de dialogue pour prévisualiser un enregistrement avant de le sauvegarder.
Permet de nommer l'extrait et d'ajuster les bornes de début et de fin.
"""
import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl
from .lecteur import VideoPlayer


class RecordingPreviewDialog(QDialog):
    """
    Dialogue qui affiche un aperçu vidéo et permet de configurer un enregistrement.
    """
    def __init__(self, temp_video_path, initial_start_ms, initial_end_ms, total_duration_ms, parent=None):
        super().__init__(parent)
        self.temp_video_path = temp_video_path
        self.total_duration_ms = total_duration_ms

        self.setWindowTitle("Aperçu de l'Enregistrement")
        self.setFixedSize(640, 600)
        self.setStyleSheet("background-color: black; color: white;")

        self.init_ui()

        # Pré-remplir les champs de temps
        self.start_input.setText(self.ms_to_mmss(initial_start_ms))
        self.end_input.setText(self.ms_to_mmss(initial_end_ms))

        if not self.temp_video_path:
            QMessageBox.critical(self, "Erreur", "Le fichier d'aperçu est introuvable.")
            self.reject()
        else:
            self.video_player.load_video(self.temp_video_path)
            self.video_player.media_player.setLoops(-1)
            self.video_player.media_player.play()

    def init_ui(self):
        """Initialise l'interface utilisateur du dialogue."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Lecteur vidéo
        self.video_player = VideoPlayer()
        main_layout.addWidget(self.video_player, stretch=1)

        # Champ pour le nom
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom de l'enregistrement :")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez le nom (sans extension)")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # Champs pour les bornes de temps
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Début :"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("mm:ss")
        time_layout.addWidget(self.start_input)
        time_layout.addStretch()
        time_layout.addWidget(QLabel("Fin :"))
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("mm:ss")
        time_layout.addWidget(self.end_input)
        main_layout.addLayout(time_layout)

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
        main_layout.addLayout(button_layout)

    def ms_to_mmss(self, ms):
        """Convertit des millisecondes en chaîne 'mm:ss'."""
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"

    def mmss_to_ms(self, mmss_str):
        """Convertit une chaîne 'mm:ss' en millisecondes. Retourne None en cas d'erreur."""
        try:
            parts = mmss_str.split(':')
            if len(parts) != 2: return None
            m, s = map(int, parts)
            return (m * 60 + s) * 1000
        except (ValueError, TypeError):
            return None

    def get_values(self):
        """Retourne le nom, et les temps de début/fin en ms."""
        name = self.name_input.text().strip()
        start_ms = self.mmss_to_ms(self.start_input.text())
        end_ms = self.mmss_to_ms(self.end_input.text())
        return name, start_ms, end_ms

    def on_accept(self):
        """Vérifie les champs avant d'accepter."""
        name, start_ms, end_ms = self.get_values()
        if not name:
            QMessageBox.warning(self, "Nom manquant", "Veuillez entrer un nom pour l'enregistrement.")
            return
        if start_ms is None or end_ms is None:
            QMessageBox.warning(self, "Format de temps invalide", "Veuillez utiliser le format 'mm:ss' pour le début et la fin.")
            return
        if start_ms >= end_ms:
            QMessageBox.warning(self, "Temps invalide", "Le temps de début doit être avant le temps de fin.")
            return
        if end_ms > self.total_duration_ms:
            QMessageBox.warning(self, "Temps invalide", "Le temps de fin dépasse la durée de la vidéo.")
            return
        self.accept()

    def closeEvent(self, event):
        """S'assure que le lecteur est arrêté à la fermeture."""
        if self.video_player and self.video_player.media_player:
            self.video_player.media_player.stop()
            self.video_player.media_player.setSource(QUrl())
        super().closeEvent(event)