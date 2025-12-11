"""
Vue Téléchargement - KOSMOS
Permet de rapatrier ou supprimer les données vidéo via SSH/SCP.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QTextEdit,
    QFrame,
    QGridLayout,
)
from PyQt6.QtCore import Qt

from components.navbar import NavBar


class TelechargementKosmosView(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.destination = str(Path.home())
        self._init_ui()
        self._connecter_signaux()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # NAVBAR
        try:
            self.navbar = NavBar(
                tabs=["Fichier", "Tri", "Extraction", "IA"],
                default_tab="Fichier",
            )
            self.navbar.setStyleSheet(
                """
                QWidget {
                    background-color: white;
                    border-bottom: 1px solid #e0e0e0;
                    font-family: 'Montserrat';
                }
            """
            )
            main_layout.addWidget(self.navbar)
        except Exception as e:
            print(f"⚠️ Erreur navbar Téléchargement: {e}")
            placeholder = QLabel("NAVBAR")
            placeholder.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
            main_layout.addWidget(placeholder)

        # CONTENU PRINCIPAL
        content = QWidget()
        content.setStyleSheet("background-color: black;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(60, 40, 60, 40)
        content_layout.setSpacing(20)

        titre = QLabel("Téléchargement des données KOSMOS")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 26px;
                font-weight: bold;
            }
        """
        )
        content_layout.addWidget(titre)

        sous_titre = QLabel("Rapatriez les vidéos sur l'ordinateur puis importez-les depuis l'onglet Importation/Tri.")
        sous_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sous_titre.setWordWrap(True)
        sous_titre.setStyleSheet("color: #bbbbbb; font-size: 14px;")
        content_layout.addWidget(sous_titre)

        # CARD PARAMÈTRES
        card = QFrame()
        card.setStyleSheet(
            """
            QFrame {
                background-color: #111;
                border: 1px solid #222;
                border-radius: 12px;
            }
            QLabel { color: white; }
            QLineEdit {
                background: #1b1b1b;
                color: white;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px;
            }
        """
        )
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        form_layout = QGridLayout()
        form_layout.setVerticalSpacing(12)
        form_layout.setHorizontalSpacing(10)

        # Ligne 1 : IP / Utilisateur / Mot de passe
        form_layout.addWidget(QLabel("Adresse IP KOSMOS"), 0, 0)
        self.input_ip = QLineEdit("192.168.10.2")
        form_layout.addWidget(self.input_ip, 0, 1)

        form_layout.addWidget(QLabel("Utilisateur"), 1, 0)
        self.input_user = QLineEdit("kosmos15")
        form_layout.addWidget(self.input_user, 1, 1)

        form_layout.addWidget(QLabel("Mot de passe"), 2, 0)
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("projet15")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.input_password, 2, 1)

        # Ligne 2 : Chemin distant
        form_layout.addWidget(QLabel("Chemin distant (vidéos)"), 3, 0)
        self.input_remote = QLineEdit("/media/kosmos15")
        form_layout.addWidget(self.input_remote, 3, 1)

        # Ligne 3 : Dossier local
        form_layout.addWidget(QLabel("Dossier local de destination"), 4, 0)
        dest_layout = QHBoxLayout()
        self.input_dest = QLineEdit(self.destination)
        self.input_dest.setReadOnly(True)
        
        btn_choose = QPushButton("Choisir...")
        btn_choose.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_choose.clicked.connect(self._choisir_destination)
        dest_layout.addWidget(self.input_dest, stretch=1)
        dest_layout.addWidget(btn_choose)
        form_layout.addLayout(dest_layout, 4, 1)

        card_layout.addLayout(form_layout)

        # Boutons d'action
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.btn_download = QPushButton("Télécharger les données")
        self.btn_download.setFixedHeight(48)
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.setStyleSheet(
            """
            QPushButton {
                background-color: #1DA1FF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1E88E5; }
            QPushButton:disabled { background-color: #555; color: #ccc; }
        """
        )
        self.btn_download.clicked.connect(self._on_download_clicked)
        buttons_layout.addWidget(self.btn_download)

        self.btn_delete = QPushButton("Supprimer les données du KOSMOS")
        self.btn_delete.setFixedHeight(48)
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet(
            """
            QPushButton {
                background-color: #b71c1c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9a0007; }
            QPushButton:disabled { background-color: #555; color: #ccc; }
        """
        )
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        buttons_layout.addWidget(self.btn_delete)

        card_layout.addLayout(buttons_layout)
        card.setLayout(card_layout)
        content_layout.addWidget(card)

        # Zone de log
        log_label = QLabel("Journal des opérations")
        log_label.setStyleSheet("color: white; font-weight: bold;")
        content_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #0c0c0c;
                color: #d0d0d0;
                border: 1px solid #222;
                border-radius: 8px;
            }
        """
        )
        self.log_text.setMinimumHeight(220)
        content_layout.addWidget(self.log_text)

        content.setLayout(content_layout)
        main_layout.addWidget(content)
        self.setLayout(main_layout)

    def _connecter_signaux(self):
        if not self.controller:
            return
        self.controller.log_emis.connect(self._append_log)
        self.controller.telechargement_termine.connect(self._on_download_finished)
        self.controller.suppression_terminee.connect(self._on_delete_finished)

    def _append_log(self, message: str):
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()

    def _collect_params(self):
        ip = self.input_ip.text().strip()
        user = self.input_user.text().strip()
        password = self.input_password.text().strip() or self.input_password.placeholderText()
        remote_path = self.input_remote.text().strip()
        destination = self.destination.strip()
        return {
            "ip": ip,
            "user": user,
            "password": password,
            "remote_path": remote_path,
            "destination": destination,
        }

    def _valider_params(self, params) -> bool:
        if not params["ip"] or not params["user"] or not params["remote_path"]:
            QMessageBox.warning(self, "Champs requis", "IP, utilisateur et chemin distant sont obligatoires.")
            return False
        if not params["destination"]:
            QMessageBox.warning(self, "Dossier local manquant", "Choisissez un dossier local de destination.")
            return False
        return True

    def _choisir_destination(self):
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier où stocker les vidéos téléchargées",
            self.destination,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        if dossier:
            self.destination = dossier
            self.input_dest.setText(dossier)

    def _set_actions_enabled(self, enabled: bool):
        self.btn_download.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)

    def _on_download_clicked(self):
        # Demander le dossier de destination au moment du clic
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de destination",
            self.destination,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        
        if dossier:
            self.destination = dossier
            self.input_dest.setText(dossier)
        else:
            # Si l'utilisateur annule la sélection, on annule le téléchargement
            return

        params = self._collect_params()
        if not self._valider_params(params):
            return
        self.log_text.clear()
        self._append_log("Démarrage du téléchargement...")
        self._set_actions_enabled(False)
        if self.controller:
            started = self.controller.lancer_telechargement(params)
            if not started:
                self._set_actions_enabled(True)

    def _on_delete_clicked(self):
        params = self._collect_params()
        if not self._valider_params(params):
            return
        confirmation = QMessageBox.question(
            self,
            "Supprimer les données ?",
            f"Supprimer le dossier distant \"{params['remote_path']}\" sur {params['ip']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return
        self._append_log("Suppression distante en cours...")
        self._set_actions_enabled(False)
        if self.controller:
            started = self.controller.supprimer_donnees(params)
            if not started:
                self._set_actions_enabled(True)

    def _on_download_finished(self, success: bool, message: str):
        self._set_actions_enabled(True)
        self._append_log(message)
        if success:
            QMessageBox.information(self, "Téléchargement", message)
        else:
            QMessageBox.critical(self, "Téléchargement", message)

    def _on_delete_finished(self, success: bool, message: str):
        self._set_actions_enabled(True)
        self._append_log(message)
        if success:
            QMessageBox.information(self, "Suppression distante", message)
        else:
            QMessageBox.critical(self, "Suppression distante", message)
