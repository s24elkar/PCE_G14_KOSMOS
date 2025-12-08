"""
IA tab view.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread
from PyQt6.QtGui import QAction, QFont, QImage, QPalette, QColor, QPixmap

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ia_module.ia_controller import IAKosmosController


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def frame_to_pixmap(frame: np.ndarray) -> Optional[QPixmap]:
    """Convert a BGR frame into a QPixmap."""
    try:
        if frame is None or frame.size == 0:
            return None
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_image)
    except Exception as exc:
        print(f"⚠️ Impossible de convertir la frame: {exc}")
        return None


def time_to_seconds(time_str: str) -> int:
    if not time_str:
        return 0
    try:
        h, m, s = time_str.split(":")
        return int(h) * 3600 + int(m) * 60 + int(float(s))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Threads
# ---------------------------------------------------------------------------

class PreviewExtractorThread(QThread):
    preview_ready = pyqtSignal(int, QPixmap)

    def __init__(self, video_path: str, seek_points: List[int], parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.seek_points = seek_points
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"⚠️ Impossible d'ouvrir la vidéo {self.video_path}")
            return

        try:
            for idx, seconds in enumerate(self.seek_points):
                if not self._running:
                    break
                cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
                ret, frame = cap.read()
                if not ret or frame is None:
                    continue
                pixmap = frame_to_pixmap(frame)
                if pixmap and self._running:
                    self.preview_ready.emit(idx, pixmap)
        finally:
            cap.release()


class IAVideoProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, controller: IAKosmosController, input_path: str, output_path: str, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.input_path = input_path
        self.output_path = output_path

    def run(self):
        try:
            self.controller.traiter_video(self.input_path, self.output_path, progress_cb=self.progress.emit)
            self.finished.emit(self.output_path)
        except Exception as exc:  # pragma: no cover - runtime feedback
            self.failed.emit(str(exc))


class FishDetectionThread(QThread):
    progress = pyqtSignal(int)
    preview = pyqtSignal(object)
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, controller: IAKosmosController, input_path: str, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.input_path = input_path

    def run(self):
        try:
            output_path = self.controller.run_fish_detection(
                self.input_path, progress_cb=self.progress.emit, preview_cb=self.preview.emit
            )
            self.finished.emit(output_path)
        except Exception as exc:  # pragma: no cover - runtime feedback
            self.failed.emit(str(exc))


# ---------------------------------------------------------------------------
# NavBar
# ---------------------------------------------------------------------------

class NavBarAvecMenu(QWidget):
    tab_changed = pyqtSignal(str)
    nouvelle_campagne_clicked = pyqtSignal()
    ouvrir_campagne_clicked = pyqtSignal()
    enregistrer_clicked = pyqtSignal()
    enregistrer_sous_clicked = pyqtSignal()

    def __init__(self, tabs=None, default_tab=None, parent=None):
        super().__init__(parent)

        if tabs is None:
            self.tabs = ["Fichier", "Téléchargement", "Tri", "Extraction", "IA"]
        else:
            self.tabs = tabs

        self.default_tab = default_tab if default_tab else self.tabs[0]
        self.drag_position = None
        self.tab_buttons = {}

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        for tab_name in self.tabs:
            is_active = tab_name == self.default_tab
            btn = self.create_nav_button(tab_name, is_active)
            self.tab_buttons[tab_name] = btn
            layout.addWidget(btn)

            if tab_name == "Fichier":
                self.fichier_btn = btn
                self.create_fichier_menu()

        layout.addStretch()

        minimize_btn = self.create_control_button("─", self.minimize_window, "#e0e0e0")
        layout.addWidget(minimize_btn)

        self.maximize_btn = self.create_control_button("□", self.toggle_maximize, "#e0e0e0")
        layout.addWidget(self.maximize_btn)

        close_btn = self.create_control_button("✕", self.close_window, "#ff4444")
        layout.addWidget(close_btn)

        self.setLayout(layout)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.setStyleSheet(
            "NavBarAvecMenu { background-color: rgb(255, 255, 255); border-bottom: 1px solid #e0e0e0; }"
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(50)

    def create_nav_button(self, text, is_active=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(is_active)

        if is_active:
            style = (
                "QPushButton { background-color: #1DA1FF; color: white; border: none; padding: 8px 20px; font-size: 14px; "
                "border-radius: 4px; }"
            )
        else:
            style = (
                "QPushButton { background-color: transparent; color: black; border: none; padding: 8px 20px; font-size: 14px; "
                "border-radius: 4px; } QPushButton:hover { background-color: #f5f5f5; }"
            )

        btn.setStyleSheet(style)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if text != "Fichier":
            btn.clicked.connect(lambda: self.on_tab_clicked(btn))
        else:
            btn.clicked.connect(self.show_fichier_menu)

        return btn

    def create_fichier_menu(self):
        self.fichier_menu = QMenu(self)
        self.fichier_menu.setStyleSheet(
            "QMenu { background-color: #f5f5f5; border: 1px solid #ddd; padding: 5px; } QMenu::item { padding: 8px 30px 8px 20px; } QMenu::item:selected { background-color: #2196F3; color: white; }"
        )

        action_creer = QAction("Créer campagne", self)
        action_creer.triggered.connect(self.nouvelle_campagne_clicked.emit)
        self.fichier_menu.addAction(action_creer)

        action_ouvrir = QAction("Ouvrir campagne", self)
        action_ouvrir.triggered.connect(self.ouvrir_campagne_clicked.emit)
        self.fichier_menu.addAction(action_ouvrir)

        self.fichier_menu.addSeparator()

        action_enregistrer = QAction("Enregistrer", self)
        action_enregistrer.triggered.connect(self.enregistrer_clicked.emit)
        self.fichier_menu.addAction(action_enregistrer)

        action_enregistrer_sous = QAction("Enregistrer sous", self)
        action_enregistrer_sous.triggered.connect(self.enregistrer_sous_clicked.emit)
        self.fichier_menu.addAction(action_enregistrer_sous)

    def show_fichier_menu(self):
        button_pos = self.fichier_btn.mapToGlobal(QPoint(0, self.fichier_btn.height()))
        self.fichier_menu.exec(button_pos)

    def create_control_button(self, text, callback, hover_color):
        btn = QPushButton(text)
        btn.setFixedSize(40, 40)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; border: none; color: #333; }} QPushButton:hover {{ background-color: {hover_color}; }}"
        )
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def on_tab_clicked(self, clicked_btn):
        for btn in self.tab_buttons.values():
            if btn != clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)
        self.tab_changed.emit(clicked_btn.text())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def minimize_window(self):
        self.window().showMinimized()

    def toggle_maximize(self):
        if self.window().isMaximized():
            self.window().showNormal()
            self.maximize_btn.setText("□")
        else:
            self.window().showMaximized()
            self.maximize_btn.setText("❐")

    def close_window(self):
        self.window().close()


# ---------------------------------------------------------------------------
# Main IA View
# ---------------------------------------------------------------------------

class IAKosmosView(QWidget):
    def __init__(self, controller: Optional[IAKosmosController] = None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.video_selectionnee = None
        self.preview_thread: Optional[PreviewExtractorThread] = None
        self.processing_thread: Optional[QThread] = None
        self.last_output_path: Optional[str] = None

        self.init_ui()
        self.connecter_signaux()
        self.charger_videos()

    def is_yolo_mode(self) -> bool:
        return self.combo_modele.currentText() == "Détection Poissons (YOLO)"

    def _update_action_button_label(self):
        if self.is_yolo_mode():
            self.btn_traiter.setText("Lancer détection vidéo")
        else:
            self.btn_traiter.setText("Lancer le traitement")

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.navbar = NavBarAvecMenu(tabs=["Fichier", "Tri", "Extraction", "IA"], default_tab="IA")
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
        self._update_action_button_label()

    def create_left_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Noms", "Taille", "Durée", "Date"])

        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 100)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.table.setStyleSheet(
            """
            QTableWidget { background-color: black; color: white; border: 2px solid white; gridline-color: #555; font-size: 11px; }
            QTableWidget::item { padding: 4px; border-bottom: 1px solid #333; }
            QTableWidget::item:selected { background-color: #1DA1FF; }
            QHeaderView::section { background-color: white; color: black; padding: 6px; border: none; font-weight: bold; font-size: 12px; }
        """
        )

        layout.addWidget(self.table)

        panel.setLayout(layout)
        return panel

    def create_preview_grid(self):
        container = QFrame()
        container.setStyleSheet("background-color: black; border: 2px solid white;")
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        label = QLabel("Aperçu IA")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "font-size: 12px; font-weight: bold; padding: 4px; border-bottom: 2px solid white; background-color: white; color: black;"
        )
        outer_layout.addWidget(label)

        grid_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(6)
        grid_layout.setContentsMargins(8, 8, 8, 8)

        self.thumbnails: List[QLabel] = []
        idx_counter = 1
        for row in range(2):
            for col in range(3):
                thumb = QLabel()
                thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb.setText("🔄")
                thumb.setStyleSheet("background-color: black; border: 1px dashed #555; color: #777;")
                thumb.setMinimumSize(240, 140)
                thumb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                self.thumbnails.append(thumb)

                angle_label = QLabel(f"Angle {idx_counter}")
                angle_label.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
                angle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                item_layout = QVBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(4)
                item_layout.addWidget(thumb, 1)
                item_layout.addWidget(angle_label, 0)

                item_widget = QWidget()
                item_widget.setStyleSheet("background-color: transparent; border: none;")
                item_widget.setLayout(item_layout)

                grid_layout.addWidget(item_widget, row, col, Qt.AlignmentFlag.AlignCenter)
                idx_counter += 1

        for i in range(2):
            grid_layout.setRowStretch(i, 1)
        for i in range(3):
            grid_layout.setColumnStretch(i, 1)

        grid_widget.setLayout(grid_layout)
        outer_layout.addWidget(grid_widget, 1)
        container.setLayout(outer_layout)
        return container

    def create_traitement_panel(self):
        container = QFrame()
        container.setStyleSheet("background-color: black; border: 2px solid white;")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        titre = QLabel("Traitement IA")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(
            "color: black; font-size: 12px; font-weight: bold; padding: 6px; border: 2px solid white; background-color: white;"
        )
        layout.addWidget(titre)

        row_modele = QHBoxLayout()
        row_modele.setSpacing(10)
        lbl_modele = QLabel("Modèle :")
        lbl_modele.setStyleSheet("color: white; font-weight: bold;")
        self.combo_modele = QComboBox()
        self.combo_modele.addItem("U-Net (milesial/Pytorch-UNet)")
        self.combo_modele.addItem("Détection Poissons (YOLO)")
        self.combo_modele.setStyleSheet(
            "QComboBox { background-color: #111; color: white; border: 1px solid white; padding: 6px; } QComboBox::drop-down { border: none; }"
        )
        row_modele.addWidget(lbl_modele)
        row_modele.addWidget(self.combo_modele, 1)
        layout.addLayout(row_modele)

        row_btns = QHBoxLayout()
        row_btns.setSpacing(10)

        self.btn_charger = QPushButton("Charger modèle")
        self.btn_traiter = QPushButton("Lancer le traitement")
        for btn in (self.btn_charger, self.btn_traiter):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 12px; font-weight: bold; padding: 6px 10px; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }"
            )

        row_btns.addWidget(self.btn_charger)
        row_btns.addWidget(self.btn_traiter)
        layout.addLayout(row_btns)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet(
            "QProgressBar { border: 1px solid #555; border-radius: 4px; text-align: center; color: white; background-color: #1a1a1a; }"
            "QProgressBar::chunk { background-color: #1DA1FF; }"
        )
        layout.addWidget(self.progress)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(10)
        self.label_avant = self.create_preview_label("Avant", "label_avant")
        self.label_apres = self.create_preview_label("Après", "label_apres")
        preview_row.addWidget(self.label_avant, 1)
        preview_row.addWidget(self.label_apres, 1)
        layout.addLayout(preview_row)

        self.label_status = QLabel("")
        self.label_status.setStyleSheet("color: #1DA1FF;")
        layout.addWidget(self.label_status)

        container.setLayout(layout)
        return container

    def create_preview_label(self, title: str, object_name: str) -> QFrame:
        wrapper = QFrame()
        wrapper.setStyleSheet("background-color: black; border: 1px solid #444;")
        vbox = QVBoxLayout()
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("color: white; font-weight: bold;")

        label = QLabel("Aucune image")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(180)
        label.setStyleSheet("background-color: #111; color: #777; border: 1px dashed #555;")
        label.setObjectName(object_name)

        vbox.addWidget(lbl_title)
        vbox.addWidget(label)
        wrapper.setLayout(vbox)
        return wrapper

    def create_right_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.preview_container = self.create_preview_grid()
        self.traitement_container = self.create_traitement_panel()

        layout.addWidget(self.preview_container, stretch=2)
        layout.addWidget(self.traitement_container, stretch=1)
        panel.setLayout(layout)
        return panel

    # ------------------------------------------------------------------
    # Data handling
    # ------------------------------------------------------------------

    def connecter_signaux(self):
        if not self.controller:
            return
        self.table.itemSelectionChanged.connect(self.on_video_selected)
        self.controller.video_selectionnee.connect(self.afficher_video)
        self.controller.modele_charge.connect(self.on_modele_charge)
        self.controller.modele_fish_charge.connect(self.on_fish_modele_charge)
        self.btn_charger.clicked.connect(self.on_charger_modele)
        self.btn_traiter.clicked.connect(self.on_lancer_traitement)
        self.combo_modele.currentTextChanged.connect(self.on_mode_changed)

    def charger_videos(self):
        if not self.controller:
            return
        videos = self.controller.obtenir_videos()
        self.table.setRowCount(len(videos))
        for row, video in enumerate(videos):
            self.table.setItem(row, 0, QTableWidgetItem(video.nom))
            self.table.setItem(row, 1, QTableWidgetItem(video.taille))
            self.table.setItem(row, 2, QTableWidgetItem(video.duree))
            self.table.setItem(row, 3, QTableWidgetItem(video.date))

        if videos:
            self.table.selectRow(0)
            self.controller.selectionner_video(videos[0].nom)

    def on_video_selected(self):
        selected = self.table.selectedItems()
        if selected and self.controller:
            row = selected[0].row()
            nom_video = self.table.item(row, 0).text()
            self.controller.selectionner_video(nom_video)

    def _build_seek_points(self, video):
        seek_info = []
        if self.controller:
            seek_info = self.controller.get_angle_seek_times(video.nom)
        if not seek_info:
            seek_info = [("00:00:01", 2)] * 6
        seconds = [time_to_seconds(s) for s, _ in seek_info][:6]
        if len(seconds) < 6:
            seconds.extend([seconds[-1] if seconds else 1] * (6 - len(seconds)))
        return seconds

    def _reset_thumbnails(self):
        for thumb in getattr(self, "thumbnails", []):
            thumb.setPixmap(QPixmap())
            thumb.setText("🔄")

    def afficher_video(self, video):
        self.video_selectionnee = video
        self._reset_thumbnails()

        seek_points = self._build_seek_points(video)
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop()
            self.preview_thread.wait()
        self.preview_thread = PreviewExtractorThread(video.chemin, seek_points)
        self.preview_thread.preview_ready.connect(self.on_preview_ready)
        self.preview_thread.start()

        avant_label = self.label_avant.findChild(QLabel, "label_avant")
        apres_label = self.label_apres.findChild(QLabel, "label_apres")

        first_frame = self._load_first_frame(video.chemin)
        if first_frame and avant_label:
            avant_label.setPixmap(
                first_frame.scaled(
                    480, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )
            avant_label.setText("")
        elif avant_label:
            avant_label.setText("Aucune image")

        if apres_label:
            apres_label.setPixmap(QPixmap())
            apres_label.setText("Aucun résultat")

    def on_preview_ready(self, index: int, pixmap: QPixmap):
        if index < len(self.thumbnails):
            target = self.thumbnails[index]
            target.setText("")
            target.setPixmap(
                pixmap.scaled(
                    target.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            )

    def _load_first_frame(self, video_path: str) -> Optional[QPixmap]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return None
        return frame_to_pixmap(frame)

    def on_detection_preview(self, frame: np.ndarray):
        target = self.label_apres.findChild(QLabel, "label_apres")
        pix = frame_to_pixmap(frame)
        if pix and target:
            target.setText("")
            target.setPixmap(
                pix.scaled(
                    max(target.width(), 480),
                    max(target.height(), 320),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    # ------------------------------------------------------------------
    # IA actions
    # ------------------------------------------------------------------

    def on_mode_changed(self):
        self._update_action_button_label()
        self.progress.setValue(0)
        self.label_status.setText("")

    def on_modele_charge(self, ok: bool, message: str):
        if ok:
            self.label_status.setText(message)
            self.btn_traiter.setEnabled(True)
        else:
            self.label_status.setText(f"Erreur: {message}")
            self.btn_traiter.setEnabled(False)

    def on_fish_modele_charge(self, ok: bool, message: str):
        if ok:
            self.label_status.setText(message)
            self.btn_traiter.setEnabled(True)
        else:
            self.label_status.setText(f"Erreur: {message}")
            self.btn_traiter.setEnabled(False)

    def on_charger_modele(self):
        if not self.controller:
            return
        if self.is_yolo_mode():
            self.label_status.setText("Chargement du modèle YOLO...")
        else:
            self.label_status.setText("Chargement du modèle...")
        self.btn_traiter.setEnabled(False)
        # Option to choose a custom weights file
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Fichiers PyTorch (*.pth *.pt)")
        if file_dialog.exec():
            selected = file_dialog.selectedFiles()
            path = selected[0] if selected else None
        else:
            path = None
        if self.is_yolo_mode():
            self.controller.load_fish_model(path)
        else:
            self.controller.charger_modele(path)

    def on_lancer_traitement(self):
        if not self.controller or not self.video_selectionnee:
            QMessageBox.warning(self, "Aucune vidéo", "Veuillez sélectionner une vidéo à traiter.")
            return
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.information(self, "Traitement en cours", "Un traitement est déjà en cours.")
            return

        if self.is_yolo_mode():
            self._lancer_detection_poisson()
        else:
            self._lancer_unet()

    def _lancer_unet(self):
        entree = self.video_selectionnee.chemin
        sortie = self.controller.get_output_path(entree)
        self.progress.setValue(0)
        self.btn_traiter.setEnabled(False)
        self.btn_charger.setEnabled(False)
        self.label_status.setText("Traitement IA en cours...")

        self.processing_thread = IAVideoProcessThread(self.controller, entree, sortie)
        self.processing_thread.progress.connect(self.progress.setValue)
        self.processing_thread.finished.connect(self.on_traitement_termine)
        self.processing_thread.failed.connect(self.on_traitement_erreur)
        self.processing_thread.start()

    def _lancer_detection_poisson(self):
        entree = self.video_selectionnee.chemin
        self.progress.setValue(0)
        self.btn_traiter.setEnabled(False)
        self.btn_charger.setEnabled(False)
        self.label_status.setText("Détection poissons en cours...")
        self.processing_thread = FishDetectionThread(self.controller, entree)
        self.processing_thread.progress.connect(self.progress.setValue)
        self.processing_thread.preview.connect(self.on_detection_preview)
        self.processing_thread.finished.connect(self.on_traitement_termine)
        self.processing_thread.failed.connect(self.on_traitement_erreur)
        self.processing_thread.start()

    def on_traitement_termine(self, output_path: str):
        self.progress.setValue(100)
        self.label_status.setText(f"Résultat enregistré : {output_path}")
        self.btn_traiter.setEnabled(True)
        self.btn_charger.setEnabled(True)
        self.processing_thread = None
        self.last_output_path = output_path

        pix = self._load_first_frame(output_path)
        target = self.label_apres.findChild(QLabel, "label_apres")
        if pix and target:
            target.setPixmap(
                pix.scaled(480, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
            target.setText("")
        elif target:
            target.setText("Aucun résultat")

    def on_traitement_erreur(self, message: str):
        self.label_status.setText(f"Erreur: {message}")
        QMessageBox.critical(self, "Erreur IA", message)
        self.btn_traiter.setEnabled(True)
        self.btn_charger.setEnabled(True)
        self.processing_thread = None


# Test rapide
if __name__ == "__main__":
    from models.app_model import ApplicationModel

    app = QApplication(sys.argv)
    font = QFont("Montserrat", 10)
    app.setFont(font)

    model = ApplicationModel()
    controller = IAKosmosController(model)
    view = IAKosmosView(controller)
    view.resize(1200, 700)
    view.show()

    sys.exit(app.exec())
