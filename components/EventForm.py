from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt6.QtCore import pyqtSignal

class EventForm(QWidget):
    event_created = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un événement")
        self.resize(450, 200)
        self.init_ui()

    def init_ui(self):
        name_label = QLabel("Nom :")
        self.name_input = QLineEdit()

        type_label = QLabel("Type :")
        self.type_input = QComboBox()
        self.type_input.addItems(["Poisson", "Végétation", "Autre"])

        start_label = QLabel("Début (mm:ss) :")
        self.start_input = QLineEdit()
        end_label = QLabel("Fin (mm:ss) :")
        self.end_input = QLineEdit()

        self.btn_add = QPushButton("Ajouter")
        self.btn_cancel = QPushButton("Annuler")

        layout = QVBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(type_label)
        layout.addWidget(self.type_input)

        start_layout = QHBoxLayout()
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.start_input)
        layout.addLayout(start_layout)

        end_layout = QHBoxLayout()
        end_layout.addWidget(end_label)
        end_layout.addWidget(self.end_input)
        layout.addLayout(end_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_event)
        self.btn_cancel.clicked.connect(self.close)

    def mmss_to_seconds(self, mmss_str):
        """
        Convertit mm:ss ou ss en secondes
        """
        parts = mmss_str.strip().split(':')
        try:
            parts = [int(p) for p in parts]
        except ValueError:
            return None
        if len(parts) == 2:
            m, s = parts
        elif len(parts) == 1:
            m = 0
            s = parts[0]
        else:
            return None
        return m*60 + s

    def add_event(self):
        name = self.name_input.text().strip()
        type_ = self.type_input.currentText()
        start = self.start_input.text().strip()
        end = self.end_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Erreur", "Le nom de l'événement ne peut pas être vide.")
            return

        start_sec = self.mmss_to_seconds(start)
        end_sec = self.mmss_to_seconds(end)

        if start_sec is None or end_sec is None:
            QMessageBox.warning(self, "Erreur", "Format de temps invalide. Utilisez mm:ss ou ss.")
            return

        if start_sec > end_sec:
            QMessageBox.warning(self, "Erreur", "Le début ne peut pas être après la fin.")
            return

        self.event_created.emit({
            "name": name,
            "type": type_,
            "start": start_sec,
            "end": end_sec
        })
        self.close()

