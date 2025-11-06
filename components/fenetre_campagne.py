from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal


class FenetreNouvelleCampagne(QDialog):
    campagneCreee = pyqtSignal(str, str)  # signal : nom, chemin

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle étude campagne")
        self.setFixedSize(500, 250)

        # --- Layout principal
        layout = QVBoxLayout(self)

        # --- Ligne : Nom
        nom_layout = QHBoxLayout()
        nom_label = QLabel("Nom :")
        self.nom_edit = QLineEdit()
        nom_layout.addWidget(nom_label)
        nom_layout.addWidget(self.nom_edit)

        # --- Ligne : Emplacement
        emp_layout = QHBoxLayout()
        emp_label = QLabel("Emplacement :")
        self.emp_edit = QLineEdit()
        self.emp_browse = QPushButton("Parcourir")
        self.emp_browse.clicked.connect(self.parcourir_emplacement)
        emp_layout.addWidget(emp_label)
        emp_layout.addWidget(self.emp_edit)
        emp_layout.addWidget(self.emp_browse)

        # --- Boutons OK / Annuler
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.valider)
        self.button_box.rejected.connect(self.reject)

        # --- Ajout au layout principal
        layout.addLayout(nom_layout)
        layout.addLayout(emp_layout)
        layout.addStretch()
        layout.addWidget(self.button_box)

    def parcourir_emplacement(self):
        """Parcourir l'emplacement"""
        chemin = QFileDialog.getExistingDirectory(self, "Choisir un emplacement")
        if chemin:
            self.emp_edit.setText(chemin)

    def valider(self):
        """Validation"""
        nom = self.nom_edit.text().strip()
        chemin = self.emp_edit.text().strip()

        if not nom or not chemin:
            QMessageBox.warning(self, "Champs manquants", "Veuillez renseigner tous les champs.")
            return

        # Émission du signal
        self.campagneCreee.emit(nom, chemin)
        self.accept()


# --- Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    fen = FenetreNouvelleCampagne()
    fen.campagneCreee.connect(lambda nom, chemin: print(f"Nouvelle campagne : {nom} ({chemin})"))
    fen.exec()