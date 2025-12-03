"""Aperçu des vidéos avec miniatures
Affiche jusqu'à 6 vidéos avec possibilité de sélection, renommage et suppression."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,QFileDialog, QMessageBox, QGridLayout)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import os
import sys

# from components.lecteur import VideoPlayer  # Décommenter si vous avez le lecteur


class ApercuVideos(QWidget):
    """
    Composant d'aperçu des vidéos avec miniatures
    Affiche jusqu'à 6 vidéos avec possibilité de sélection, renommage et suppression
    """
    
    # Signaux
    videoSelectionnee = pyqtSignal(str)  # Émet le chemin de la vidéo
    videoRenommee = pyqtSignal(str, str)  # Émet ancien_nom, nouveau_nom
    videoSupprimee = pyqtSignal(str)  # Émet le chemin de la vidéo
    
    def __init__(self, dossier_videos: str = "", parent=None):
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

        # Boutons de gestion
        boutons_layout = QHBoxLayout()
        self.bouton_renommer = QPushButton("Renommer")
        self.bouton_supprimer = QPushButton("Supprimer")
        
        # Style des boutons
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """

        #Application du style
        self.bouton_renommer.setStyleSheet(button_style)
        self.bouton_supprimer.setStyleSheet(button_style.replace("#2196F3", "#f44336").replace("#1976D2", "#d32f2f").replace("#0D47A1", "#b71c1c"))

        # Ajout des boutons au layout
        boutons_layout.addWidget(self.bouton_renommer)
        boutons_layout.addWidget(self.bouton_supprimer)
        layout_principal.addLayout(boutons_layout)

        # Connexions
        self.bouton_renommer.clicked.connect(self.renommer_video)
        self.bouton_supprimer.clicked.connect(self.supprimer_video)

        # Chargement des miniatures si un dossier est fourni
        if self.dossier_videos:
            self.charger_videos()

    def charger_videos(self):
        """Charge les 6 premières vidéos trouvées dans le dossier."""
        if not os.path.exists(self.dossier_videos):
            print(f"⚠️ Le dossier {self.dossier_videos} n'existe pas")
            return
            
        # Liste des fichiers vidéo
        fichiers = [f for f in os.listdir(self.dossier_videos) if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))]
        fichiers = fichiers[:6]
        self.videos = fichiers

        # Nettoyer la grille
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for i, fichier in enumerate(fichiers):
            chemin = os.path.join(self.dossier_videos, fichier)

            # Container pour miniature + nom
            container = QWidget()
            container_layout = QVBoxLayout()
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)

            # Label pour l'image
            label = QLabel()
            
            # Essayer de charger une vraie miniature ou utiliser un placeholder
            pixmap = QPixmap(200, 120)
            pixmap.fill(Qt.GlobalColor.darkGray)
            label.setPixmap(pixmap)
            label.setFixedSize(200, 120)
            label.setStyleSheet("border: 2px solid gray; background-color: #333;")
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Stocker le chemin dans le label
            label.setProperty("chemin", chemin)
            label.mousePressEvent = lambda event, c=chemin: self.selectionner_video(c)

            # Nom de la vidéo
            nom_label = QLabel(fichier)
            nom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nom_label.setStyleSheet("color: white; font-size: 11px;")
            nom_label.setWordWrap(True)

            container_layout.addWidget(label)
            container_layout.addWidget(nom_label)
            container.setLayout(container_layout)

            # Ajouter à la grille (2 lignes de 3 colonnes)
            self.grid.addWidget(container, i // 3, i % 3)


    def selectionner_video(self, chemin):
        """Affiche la vidéo sélectionnée dans le lecteur."""
        self.video_selectionnee = chemin
        print(f"✅ Vidéo sélectionnée : {os.path.basename(chemin)}")
        
        # Si vous avez un lecteur vidéo
        # self.lecteur.show()
        # self.lecteur.charger_video(chemin)
        
        self.highlight_selection(chemin)
        self.videoSelectionnee.emit(chemin)


    def highlight_selection(self, chemin_selectionne):
        """Met en évidence la miniature sélectionnée."""
        for i in range(self.grid.count()):
            item = self.grid.itemAt(i)
            if item:
                container = item.widget()
                if container:
                    # Trouver le QLabel (image) dans le container
                    label = container.findChild(QLabel)
                    if label and label.property("chemin"):
                        if label.property("chemin") == chemin_selectionne:
                            label.setStyleSheet("border: 3px solid #1E90FF; background-color: #333;")
                        else:
                            label.setStyleSheet("border: 2px solid gray; background-color: #333;")


    def renommer_video(self):
        """Renomme la vidéo sélectionnée."""
        if not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez d'abord sélectionner une vidéo.")
            return

        ancien_nom = os.path.basename(self.video_selectionnee)
        nouveau_nom, ok = QFileDialog.getSaveFileName(
            self, 
            "Renommer la vidéo", 
            self.video_selectionnee,
            "Vidéos (*.mp4 *.avi *.mov *.mkv)"
        )
        
        if ok and nouveau_nom:
            try:
                os.rename(self.video_selectionnee, nouveau_nom)
                QMessageBox.information(self, "Succès", "La vidéo a été renommée avec succès.")
                self.videoRenommee.emit(ancien_nom, os.path.basename(nouveau_nom))
                self.video_selectionnee = nouveau_nom
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
                nom_supprime = os.path.basename(self.video_selectionnee)
                os.remove(self.video_selectionnee)
                QMessageBox.information(self, "Supprimée", "La vidéo a été supprimée avec succès.")
                self.videoSupprimee.emit(nom_supprime)
                self.video_selectionnee = None
                # self.lecteur.hide()  # Décommenter si vous avez le lecteur
                self.charger_videos()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer la vidéo : {e}")


# --- Exemple d'utilisation (HORS de la classe, au niveau du module)
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 900, 600)
    window.setWindowTitle("Test - Aperçu des vidéos")
    window.setStyleSheet("background-color: #2a2a2a;")
    
    # Création du composant d'aperçu (avec un dossier de test)
    # Remplacez par un vrai chemin de dossier contenant des vidéos
    apercu = ApercuVideos(dossier_videos="./videos")  # ou "" pour un dossier vide
    
    # Exemple : connexion des signaux pour tests
    apercu.videoSelectionnee.connect(lambda chemin: print(f"🎥 Vidéo sélectionnée : {os.path.basename(chemin)}"))
    apercu.videoRenommee.connect(lambda ancien, nouveau: print(f"✏️ {ancien} renommée en {nouveau}"))
    apercu.videoSupprimee.connect(lambda nom: print(f"🗑️ Vidéo supprimée : {nom}"))
    
    window.setCentralWidget(apercu)
    window.show()
    
    sys.exit(app.exec())