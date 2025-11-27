"""
Fenêtre de dialogue pour prévisualiser un short avant de l'enregistrer.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, QUrl
from .lecteur import VideoPlayer


class ShortPreviewDialog(QDialog):
    """
    Dialogue qui affiche un aperçu vidéo d'un short.
    """
    def __init__(self, temp_video_path, parent=None):
        super().__init__(parent)
        self.temp_video_path = temp_video_path
        self.setWindowTitle("Aperçu du Short")
        self.setFixedSize(640, 540)  # Augmenter la hauteur pour le champ de nom
        self.setStyleSheet("background-color: black; color: white;")

        self.init_ui()

        if not self.temp_video_path:
            QMessageBox.critical(self, "Erreur", "Le fichier d'aperçu est introuvable.")
            self.reject()
        else:
            # Charger et jouer la vidéo automatiquement avec le lecteur OpenCV
            self.video_player.load_video(self.temp_video_path, autoplay=True)
            # Activer la lecture en boucle
            self.video_player.video_thread.set_looping(True)

    def init_ui(self):
        """Initialise l'interface utilisateur du dialogue."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Lecteur vidéo
        self.video_player = VideoPlayer()
        main_layout.addWidget(self.video_player, stretch=1)

        # Champ pour le nom du short
        name_layout = QHBoxLayout()
        name_label = QLabel("Nom du short :")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Entrez le nom du short (sans extension)")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #222;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)


        # Boutons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setFixedSize(120, 40)
        btn_cancel.setStyleSheet("QPushButton { background-color: #333; color: white; border: 1px solid #555; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #444; }")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setFixedSize(120, 40)
        btn_save.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border: none; border-radius: 5px; font-weight: bold; } QPushButton:hover { background-color: #1E88E5; }")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.on_accept)
        button_layout.addWidget(btn_save)

        main_layout.addLayout(button_layout)

    def get_short_name(self):
        """Retourne le nom entré par l'utilisateur."""
        return self.name_input.text().strip()

    def on_accept(self):
        """Vérifie que le nom n'est pas vide avant d'accepter."""
        if not self.get_short_name():
            QMessageBox.warning(self, "Nom manquant", "Veuillez entrer un nom pour le short.")
            return
        self.accept()

    def cleanup(self):
        """Arrête proprement le lecteur vidéo et libère les ressources."""
        if self.video_player and self.video_player.video_thread:
            # Arrêter le thread vidéo pour libérer les ressources
            self.video_player.video_thread.set_looping(False) # Arrêter la boucle
            self.video_player.video_thread.stop()
            # Attendre que le thread se termine pour être sûr que le fichier est libéré
            self.video_player.video_thread.wait(1000) # Attendre max 1 seconde
            self.video_player.close() # S'assurer que le widget est détruit
            print("🗑️ Lecteur de l'aperçu arrêté et ressource libérée.")

    def reject(self):
        self.cleanup()
        super().reject()

    def accept(self):
        self.cleanup()
        super().accept()