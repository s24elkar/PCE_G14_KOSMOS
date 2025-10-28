from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QGridLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize
import os

from lecteur import LecteurVideo  # Réutilisation de ton composant existant


class ApercuVideos(QWidget):
    def __init__(self, dossier_videos: str, parent=None):
        super().__init__(parent)
        self.dossier_videos = dossier_videos
        self.videos = []
        self.video_selectionnee = None

        self.setWindowTitle("Aperçu des vidéos")
        self.setStyleSheet("background-color: #111; color: white;")

        # Layout principal
        layout_principal = QVBoxLayout(self)

        # Grille pour les 6 miniatures
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        layout_principal.addLayout(self.grid)

        # Lecteur vidéo (issu du composant lecteur.py)
        self.lecteur = LecteurVideo()
        self.lecteur.hide()  # caché tant qu’aucune vidéo n’est sélectionnée
        layout_principal.addWidget(self.lecteur)

        # Boutons de gestion
        boutons_layout = QHBoxLayout()
        self.bouton_renommer = QPushButton("Renommer")
        self.bouton_supprimer = QPushButton("Supprimer")

        boutons_layout.addWidget(self.bouton_renommer)
        boutons_layout.addWidget(self.bouton_supprimer)
        layout_principal.addLayout(boutons_layout)

        # Connexions
        self.bouton_renommer.clicked.connect(self.renommer_video)
        self.bouton_supprimer.clicked.connect(self.supprimer_video)

        # Chargement des miniatures
        self.charger_videos()

    def charger_videos(self):
        """Charge les 6 premières vidéos trouvées dans le dossier."""
        fichiers = [f for f in os.listdir(self.dossier_videos) if f.lower().endswith((".mp4", ".avi", ".mov"))]
        fichiers = fichiers[:6]
        self.videos = fichiers

        for i, fichier in enumerate(fichiers):
            chemin = os.path.join(self.dossier_videos, fichier)

            label = QLabel()
            pixmap = QPixmap("placeholder.jpg")  # image par défaut (miniature à remplacer si tu en as)
            pixmap = pixmap.scaled(QSize(200, 120), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
            label.setStyleSheet("border: 2px solid gray;")
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.mousePressEvent = lambda event, chemin=chemin: self.selectionner_video(chemin)

            self.grid.addWidget(label, i // 3, i % 3)

    def selectionner_video(self, chemin):
        """Affiche la vidéo sélectionnée dans le lecteur."""
        self.video_selectionnee = chemin
        self.lecteur.show()
        self.lecteur.charger_video(chemin)  # méthode à adapter selon ton lecteur
        self.highlight_selection(chemin)

    def highlight_selection(self, chemin_selectionne):
        """Met en évidence la miniature sélectionnée."""
        for i in range(self.grid.count()):
            widget = self.grid.itemAt(i).widget()
            if isinstance(widget, QLabel):
                if chemin_selectionne.endswith(os.path.basename(widget.toolTip() or "")):
                    widget.setStyleSheet("border: 3px solid #1E90FF;")
                else:
                    widget.setStyleSheet("border: 2px solid gray;")

    def renommer_video(self):
        """Renomme la vidéo sélectionnée."""
        if not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez d'abord sélectionner une vidéo.")
            return

        nouveau_nom, _ = QFileDialog.getSaveFileName(self, "Renommer la vidéo", self.video_selectionnee)
        if nouveau_nom:
            try:
                os.rename(self.video_selectionnee, nouveau_nom)
                QMessageBox.information(self, "Succès", "La vidéo a été renommée avec succès.")
                self.charger_videos()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de renommer la vidéo : {e}")

    def supprimer_video(self):
        """Demande confirmation avant de supprimer."""
        if not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez d'abord sélectionner une vidéo.")
            return

        reponse = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer la vidéo suivante ?\n\n{os.path.basename(self.video_selectionnee)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reponse == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.video_selectionnee)
                QMessageBox.information(self, "Supprimée", "La vidéo a été supprimée avec succès.")
                self.video_selectionnee = None
                self.lecteur.hide()
                self.charger_videos()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer la vidéo : {e}")
