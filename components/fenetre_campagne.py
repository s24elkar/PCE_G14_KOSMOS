"""
Composant Fenêtre Nouvelle Campagne
Permet de créer une nouvelle étude campagne en spécifiant un nom.
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal


class FenetreNouvelleCampagne(QDialog):
    """Dialogue pour créer une nouvelle campagne"""
    
    campagneCreee = pyqtSignal(str, str)  # signal : nom, emplacement (vide)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouveau répertoire de travail")
        self.setFixedSize(500, 200)  # Taille réduite
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Titre
        titre = QLabel("Nouveau répertoire de travail")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet("""
            QLabel {
                color: #1DA1FF;
                font-size: 20px;
                font-weight: bold;
                padding: 15px;
                background-color: white;
                border-radius: 5px;
            }
        """)
        layout.addWidget(titre)

        # Ligne : Nom uniquement
        nom_layout = QHBoxLayout()
        nom_label = QLabel("Nom du répertoire :")
        nom_label.setFixedWidth(150)
        nom_label.setStyleSheet("QLabel { color: white; font-size: 14px; font-weight: bold; }")
        self.nom_edit = QLineEdit()
        self.nom_edit.setStyleSheet("""
            QLineEdit {
                background-color: white;
                color: black;
                border: 2px solid white;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        nom_layout.addWidget(nom_label)
        nom_layout.addWidget(self.nom_edit)

        # Message informatif
        info_label = QLabel("Le répertoire sera créé dans le dossier d'importation des vidéos")
        info_label.setStyleSheet("QLabel { color: #888; font-size: 11px; font-style: italic; }")
        info_label.setWordWrap(True)

        # Boutons OK / Annuler
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_annuler = QPushButton("Annuler")
        btn_annuler.setFixedSize(120, 40)
        btn_annuler.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annuler.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        btn_annuler.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Ok")
        btn_ok.setFixedSize(120, 40)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: 2px solid white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        btn_ok.clicked.connect(self.valider)
        
        buttons_layout.addWidget(btn_annuler)
        buttons_layout.addWidget(btn_ok)

        # Ajout au layout principal
        layout.addLayout(nom_layout)
        layout.addWidget(info_label)
        layout.addStretch()
        layout.addLayout(buttons_layout)

    def valider(self):
        """Validation"""
        nom = self.nom_edit.text().strip()

        if not nom:
            QMessageBox.warning(self, "Champ manquant", "Veuillez renseigner le nom du répertoire.")
            return

        # Émission du signal avec emplacement vide
        self.campagneCreee.emit(nom, "")
        self.accept()
