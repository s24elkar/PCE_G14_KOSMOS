"""
VUE - Page de tri KOSMOS
Architecture MVC - Vue uniquement
Champs read-only par défaut / Suppression définitive des vidéos
"""
import sys
import os
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QSplitter,
    QGridLayout, QLineEdit, QMenu, QMessageBox, QDialog, QScrollArea,
    QSizePolicy, QApplication
)

from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QTimer, QSize
from PyQt6.QtGui import QFont, QAction, QPalette, QColor, QPixmap, QMovie, QImage


# Import du contrôleur
from controllers.tri_controller import TriKosmosController
from components.formulaire_metadonnees import FormulaireMetadonnees
from components.apercu_video import ApercuVideos
from components.navbar import NavBar
from components.Explorateur_dossier import VideoList # Import du nouveau composant


# ═══════════════════════════════════════════════════════════════
# DIALOGUE DE RENOMMAGE
# ═══════════════════════════════════════════════════════════════

class DialogueRenommer(QDialog):
    """Dialogue pour renommer une vidéo"""
    
    def __init__(self, nom_actuel, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renommer la vidéo")
        self.setFixedSize(500, 200)
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        titre = QLabel("Renommer la vidéo")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet("color: white; font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(titre)
        
        label_actuel = QLabel(f"Nom actuel : {nom_actuel}")
        label_actuel.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(label_actuel)
        
        nom_layout = QHBoxLayout()
        nom_label = QLabel("Nouveau nom :")
        nom_label.setFixedWidth(120)
        nom_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        
        self.nom_edit = QLineEdit()
        self.nom_edit.setText(nom_actuel)
        self.nom_edit.setStyleSheet("background-color: white; color: black; border: 2px solid white; border-radius: 4px; padding: 6px; font-size: 13px;")
        nom_layout.addWidget(nom_label)
        nom_layout.addWidget(self.nom_edit)
        layout.addLayout(nom_layout)
        
        layout.addStretch()
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setFixedSize(100, 35)
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
        btn_annuler.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Renommer")
        btn_ok.setFixedSize(100, 35)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("QPushButton { background-color: white; color: black; border: 2px solid white; border-radius: 4px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #f0f0f0; }")
        btn_ok.clicked.connect(self.accept)
        
        buttons_layout.addWidget(btn_annuler)
        buttons_layout.addWidget(btn_ok)
        layout.addLayout(buttons_layout)
    
    def get_nouveau_nom(self):
        return self.nom_edit.text().strip()


# ═══════════════════════════════════════════════════════════════
# WIDGET MINIATURE
# ═══════════════════════════════════════════════════════════════

# (Déplacé dans components/apercu_video.py)



# ═══════════════════════════════════════════════════════════════
# EXTRACTION DE MINIATURES (THREAD - SIMPLIFIÉ)
# ═══════════════════════════════════════════════════════════════

# (Déplacé dans components/apercu_video.py)



# ═══════════════════════════════════════════════════════════════
# NAVBAR
# ═══════════════════════════════════════════════════════════════
# (Déplacé dans components/navbar.py)



# ═══════════════════════════════════════════════════════════════
# VUE
# ═══════════════════════════════════════════════════════════════

class TriKosmosView(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.video_selectionnee = None
        self.current_seek_info = []
        
        self.init_ui()
        self.connecter_signaux()
        self.charger_videos()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBar(
            tabs=["Fichier", "Tri", "Extraction"],
            default_tab="Tri"
        )
        main_layout.addWidget(self.navbar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_left_panel(self):
        # Utilisation du composant VideoList
        self.video_list = VideoList()
        
        # Connexion des signaux du composant
        self.video_list.video_selected.connect(self.on_video_selected_from_list)
        self.video_list.rename_requested.connect(self.on_renommer)
        self.video_list.delete_requested.connect(self.on_supprimer)
        
        return self.video_list
    
    def create_right_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # APERÇU DES ANGLES (Nouveau composant)
        self.apercu_videos = ApercuVideos()
        layout.addWidget(self.apercu_videos, stretch=2)
        
        # MÉTADONNÉES
        self.formulaire_metadata = FormulaireMetadonnees()
        self.formulaire_metadata.modification_communes_demandee.connect(self.on_modifier_metadata_communes)
        self.formulaire_metadata.modification_propres_demandee.connect(self.on_modifier_metadata_propres)
        self.formulaire_metadata.precalcul_demande.connect(self.on_precalculer_metadata)
        
        layout.addWidget(self.formulaire_metadata, stretch=1)
        
        panel.setLayout(layout)
        return panel
    
    
    def connecter_signaux(self):
        if self.controller:
            # Le signal video_selected est déjà connecté dans create_left_panel
            self.controller.video_selectionnee.connect(self.afficher_video)
            # Connexion des signaux de succès/erreur
            if hasattr(self.controller, 'succes_operation'):
                self.controller.succes_operation.connect(self.afficher_succes)
            if hasattr(self.controller, 'erreur_operation'):
                self.controller.erreur_operation.connect(self.afficher_erreur)
    
    def afficher_succes(self, message):
        QMessageBox.information(self, "Succès", message)

    def afficher_erreur(self, message):
        QMessageBox.critical(self, "Erreur", message)

    def charger_videos(self):
        if not self.controller:
            return
        
        videos = self.controller.obtenir_videos()
        
        # Mise à jour via le composant
        if hasattr(self, 'video_list'):
            self.video_list.update_video_list(videos)
            
            if len(videos) > 0:
                self.video_list.select_first_row()
                self.controller.selectionner_video(videos[0].nom)
    
    # Méthodes d'extraction déplacées dans ApercuVideos

    
    def on_video_selected_from_list(self, nom_video):
        """Callback appelé quand le composant VideoList émet une sélection"""
        if self.controller:
            self.controller.selectionner_video(nom_video)
    
    def afficher_video(self, video):
        self.video_selectionnee = video
        print(f"\n📹 Vidéo sélectionnée : {video.nom}")
        
        if self.controller:
            self.controller.charger_metadonnees_depuis_json(video)
            self.controller.charger_metadonnees_communes_depuis_json(video)
        
        # Utilisation du nouveau composant pour afficher les métadonnées
        self.formulaire_metadata.remplir_communes(video.get_formatted_metadata_communes())
        self.formulaire_metadata.remplir_propres(video.get_formatted_metadata_propres())
        
        if self.controller:
            self.current_seek_info = self.controller.get_angle_seek_times(video.nom)
            try:
                self.apercu_videos.charger_previews(video.chemin, self.current_seek_info)
            except Exception as e:
                print(f"⚠️ Aperçus vidéo non disponibles: {e}")
    
    def on_renommer(self):
        if not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune vidéo", "Veuillez sélectionner une vidéo à renommer.")
            return
        dialogue = DialogueRenommer(self.video_selectionnee.nom, self)
        if dialogue.exec() == QDialog.DialogCode.Accepted:
            nouveau_nom = dialogue.get_nouveau_nom()
            if not nouveau_nom:
                QMessageBox.warning(self, "Nom vide", "Le nouveau nom ne peut pas être vide.")
                return
            if nouveau_nom == self.video_selectionnee.nom: return
            reponse = QMessageBox.question(self, "Confirmer le renommage", f"Voulez-vous vraiment renommer :\n\n'{self.video_selectionnee.nom}'\n\nen\n\n'{nouveau_nom}' ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reponse == QMessageBox.StandardButton.Yes:
                if self.controller.renommer_video(self.video_selectionnee.nom, nouveau_nom):
                    QMessageBox.information(self, "Succès", f"Vidéo renommée en '{nouveau_nom}'")
                    self.charger_videos()
                else: QMessageBox.critical(self, "Erreur", "Impossible de renommer la vidéo.")
    
    def on_supprimer(self):
        if not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune vidéo", "Veuillez sélectionner une vidéo à supprimer.")
            return
        reponse = QMessageBox.question(self, "Confirmer la suppression", f"⚠️ ATTENTION : Cette action est IRRÉVERSIBLE !\n\nLa vidéo sera DÉFINITIVEMENT supprimée de votre disque dur :\n\n'{self.video_selectionnee.nom}'\n\nVoulez-vous continuer ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reponse == QMessageBox.StandardButton.Yes:
            if self.controller.supprimer_video(self.video_selectionnee.nom):
                QMessageBox.information(self, "Succès", f"✅ Vidéo '{self.video_selectionnee.nom}' supprimée définitivement")
                self.video_selectionnee = None
                self.charger_videos()
            else: QMessageBox.critical(self, "Erreur", "❌ Impossible de supprimer la vidéo.")
    
    def on_modifier_metadata_propres(self, nouvelles_meta):
        """Reçoit les modifications du composant et appelle le contrôleur"""
        if not (self.video_selectionnee and self.controller): return

        succes, message = self.controller.modifier_metadonnees_propres(self.video_selectionnee.nom, nouvelles_meta)

        if succes:
            # Le message de succès est géré par le signal succes_operation
            self.formulaire_metadata.reset_edit_propres()
        else:
            QMessageBox.warning(self, "Erreur", message)
    
    def on_modifier_metadata_communes(self, nouvelles_meta):
        """Reçoit les modifications du composant et appelle le contrôleur"""
        if not (self.video_selectionnee and self.controller): return

        succes, message = self.controller.modifier_metadonnees_communes(self.video_selectionnee.nom, nouvelles_meta)

        if succes:
            # Le message de succès est géré par le signal succes_operation
            self.formulaire_metadata.reset_edit_communes()
        else:
            QMessageBox.warning(self, "Erreur", message)

    def on_precalculer_metadata(self):
        if not (self.video_selectionnee and self.controller): return
        
        QApplication.processEvents() 
        try:
            success = self.controller.precalculer_metadonnees_externes(self.video_selectionnee.nom)
            if success: 
                QMessageBox.information(self, "Succès", "Les métadonnées externes ont été récupérées et sauvegardées.")
                self.controller.selectionner_video(self.video_selectionnee.nom)
            else: 
                QMessageBox.warning(self, "Échec", "Impossible de récupérer les métadonnées externes. Vérifiez la console pour les erreurs.")
        except Exception as e: 
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

# TEST
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QMainWindow
    sys.path.insert(0, str(Path(__file__).parent))
    try: from models.app_model import ApplicationModel
    except ImportError: sys.exit(1)
    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)
    model = ApplicationModel()
    campagne = model.creer_campagne("Test_Tri", "./test_campagne")
    controller = TriKosmosController(model)
    window = QMainWindow()
    window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    window.setGeometry(50, 50, 1400, 900)
    view = TriKosmosView(controller)
    window.setCentralWidget(view)
    window.show()
    sys.exit(app.exec())
