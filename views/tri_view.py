"""
VUE - Page de tri KOSMOS
Architecture MVC - Vue uniquement
Champs read-only par défaut / Suppression définitive des vidéos
"""
import sys
import os
import json
import subprocess
from pathlib import Path

# --- AJOUTS OPENCV ---
import cv2
import numpy as np
import time
# --- FIN AJOUTS ---

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QSplitter,
    QGridLayout, QLineEdit, QMenu, QMessageBox, QDialog, QScrollArea,
    QSizePolicy, QApplication
)
# --- AJOUT QTimer et QImage ---
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QThread, QTimer, QSize
from PyQt6.QtGui import QFont, QAction, QPalette, QColor, QPixmap, QMovie, QImage
# --- FIN AJOUT ---

# Import du contrôleur
from controllers.tri_controller import TriKosmosController


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

class AnimatedThumbnailLabel(QLabel):
    """QLabel personnalisé qui gère l'affichage d'un Pixmap statique et le remplace par une lecture OpenCV lors du survol"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.static_pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black; border: none; color: #888;")
        self.setText("🔄")
        
        self.video_path = None
        self.seek_time_sec = 0
        self.duration_sec = 0
        self.cap = None
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.update_frame)
        self.playback_start_time = 0
        
        self.setScaledContents(False) 
    
    def set_static_pixmap(self, pixmap):
        """Définit l'image statique (miniature)"""
        self.static_pixmap = pixmap
        if not self.playback_timer.isActive():
            self.setPixmap(self.static_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.setText("")
    
    def set_video_preview_info(self, video_path: str, seek_time_str: str, duration_sec: int):
        """Stocke les informations pour la lecture OpenCV"""
        self.video_path = video_path
        self.duration_sec = duration_sec
        
        if video_path and seek_time_str:
            try:
                h, m, s = map(int, seek_time_str.split(':'))
                self.seek_time_sec = h * 3600 + m * 60 + s
            except Exception as e:
                print(f"Erreur parsing seek time '{seek_time_str}': {e}")
                self.seek_time_sec = 0
        else:
            self.seek_time_sec = 0

    def enterEvent(self, event):
        """Survol : démarre la lecture OpenCV"""
        if self.video_path and not self.playback_timer.isActive():
            try:
                self.cap = cv2.VideoCapture(self.video_path)
                if not self.cap.isOpened():
                    print(f"Erreur ouverture vidéo: {self.video_path}")
                    self.cap = None
                    return
                
                self.cap.set(cv2.CAP_PROP_POS_MSEC, self.seek_time_sec * 1000)
                self.playback_start_time = time.time()
                self.playback_timer.start(33) 
            except Exception as e:
                print(f"Erreur démarrage OpenCV: {e}")
                self.cap = None
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Sortie survol : arrête la lecture OpenCV et remet l'image statique"""
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.static_pixmap:
            self.setPixmap(self.static_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.setPixmap(QPixmap())
            self.setText("🔄")
        
        super().leaveEvent(event)

    def update_frame(self):
        """Slot pour le QTimer, lit et affiche une frame vidéo (MODIFIÉ POUR x2)"""
        if not self.cap or not self.cap.isOpened():
            self.leaveEvent(None) 
            return

        elapsed = time.time() - self.playback_start_time
        if (elapsed * 2) > self.duration_sec:
            self.leaveEvent(None) 
            return

        ret, _ = self.cap.read() 
        if not ret:
            self.leaveEvent(None) 
            return
        
        ret, frame = self.cap.read() 
        if not ret:
            self.leaveEvent(None) 
            return

        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            self.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Erreur conversion frame: {e}")
            self.leaveEvent(None) 
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.static_pixmap and not self.playback_timer.isActive():
            self.setPixmap(self.static_pixmap.scaled(event.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))


# ═══════════════════════════════════════════════════════════════
# EXTRACTION DE MINIATURES (THREAD - SIMPLIFIÉ)
# ═══════════════════════════════════════════════════════════════

class PreviewExtractorThread(QThread):
    """Thread pour extraire une miniature STATIQUE"""
    thumbnail_ready = pyqtSignal(int, QPixmap)
    
    def __init__(self, video_path, seek_info: list, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.seek_info = seek_info 
        self.temp_dir = Path(video_path).parent / ".thumbnails"
        self.temp_dir.mkdir(exist_ok=True)
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        for idx, (seek_time, duration) in enumerate(self.seek_info):
            if not self._is_running:
                break
            try:
                safe_seek_time = seek_time.replace(':', '')
                thumb_path = self.temp_dir / f"thumb_{Path(self.video_path).stem}_{idx}_{safe_seek_time}.jpg"
                
                pixmap = self.extract_thumbnail(seek_time, thumb_path)
                if pixmap and self._is_running:
                    self.thumbnail_ready.emit(idx, pixmap)
                
            except Exception as e:
                print(f"⚠️ Erreur extraction preview {idx}: {e}")

    def extract_thumbnail(self, seek_time, output_path):
        if output_path.exists():
            pixmap = QPixmap(str(output_path))
            if not pixmap.isNull():
                return pixmap
        
        cmd = ['ffmpeg', '-ss', seek_time, '-i', self.video_path, '-vframes', '1', '-vf', 'scale=320:-1', '-q:v', '3', '-y', str(output_path)]
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=5, text=True, encoding='utf-8')
            if output_path.exists():
                return QPixmap(str(output_path))
        except FileNotFoundError:
            print("❌ ffmpeg n'est pas trouvé")
            self.stop()
        except Exception as e:
            print(f"Erreur extraction miniature: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# NAVBAR
# ═══════════════════════════════════════════════════════════════
class NavBarAvecMenu(QWidget):
    tab_changed = pyqtSignal(str)
    nouvelle_campagne_clicked = pyqtSignal()
    ouvrir_campagne_clicked = pyqtSignal()
    enregistrer_clicked = pyqtSignal()
    
    def __init__(self, tabs=None, default_tab=None, parent=None):
        super().__init__(parent)
        
        if tabs is None:
            self.tabs = ["Fichier", "Tri", "Téléchargement", "IA", "Extraction", "Évènements"]
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
            is_active = (tab_name == self.default_tab)
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
        
        self.setStyleSheet("NavBarAvecMenu { background-color: rgb(255, 255, 255); border-bottom: 1px solid #e0e0e0; }")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(50)
    
    def create_nav_button(self, text, is_active=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(is_active)
        
        if is_active:
            style = "QPushButton { background-color: #1DA1FF; color: white; border: none; padding: 8px 20px; font-size: 14px; border-radius: 4px; }"
        else:
            style = "QPushButton { background-color: transparent; color: black; border: none; padding: 8px 20px; font-size: 14px; border-radius: 4px; } QPushButton:hover { background-color: #f5f5f5; }"
        
        btn.setStyleSheet(style)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if text != "Fichier":
            btn.clicked.connect(lambda: self.on_tab_clicked(btn))
        else:
            btn.clicked.connect(self.show_fichier_menu)
        
        return btn
    
    def create_fichier_menu(self):
        self.fichier_menu = QMenu(self)
        self.fichier_menu.setStyleSheet("QMenu { background-color: #f5f5f5; border: 1px solid #ddd; padding: 5px; } QMenu::item { padding: 8px 30px 8px 20px; } QMenu::item:selected { background-color: #2196F3; color: white; }")
        
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
    
    def show_fichier_menu(self):
        button_pos = self.fichier_btn.mapToGlobal(QPoint(0, self.fichier_btn.height()))
        self.fichier_menu.exec(button_pos)
    
    def create_control_button(self, text, callback, hover_color):
        btn = QPushButton(text)
        btn.setFixedSize(40, 40)
        btn.setStyleSheet(f"QPushButton {{ background-color: transparent; border: none; color: #333; }} QPushButton:hover {{ background-color: {hover_color}; }}")
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


# ═══════════════════════════════════════════════════════════════
# VUE
# ═══════════════════════════════════════════════════════════════

class TriKosmosView(QWidget):
    def __init__(self, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.video_selectionnee = None
        self.preview_extractor = None 
        self.current_seek_info = []
        self.edit_propres = False
        self.edit_communes = False
        
        self.init_ui()
        self.connecter_signaux()
        self.charger_videos()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.navbar = NavBarAvecMenu(
            tabs=["Fichier", "Tri", "Téléchargement", "IA", "Extraction", "Évènements"],
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
        panel = QWidget()
        panel.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Noms", "Taille", "Durée", "Date"])
        
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 90)
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: black; color: white; border: 2px solid white; gridline-color: #555; font-size: 11px; }
            QTableWidget::item { padding: 4px; border-bottom: 1px solid #333; }
            QTableWidget::item:selected { background-color: #1DA1FF; }
            QHeaderView::section { background-color: white; color: black; padding: 6px; border: none; font-weight: bold; font-size: 12px; }
        """)
        
        layout.addWidget(self.table)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)
        buttons_layout.setContentsMargins(5, 5, 5, 5)
        
        for btn_text, callback in [("Renommer", self.on_renommer), ("Supprimer", self.on_supprimer)]:
            btn = QPushButton(btn_text)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); }")
            btn.clicked.connect(callback)
            buttons_layout.addWidget(btn)
        
        layout.addLayout(buttons_layout)
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        panel = QWidget()
        panel.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # APERÇU DES ANGLES
        apercu_container = QFrame()
        apercu_container.setStyleSheet("background-color: black; border: 2px solid white;")
        apercu_layout = QVBoxLayout()
        apercu_layout.setContentsMargins(0, 0, 0, 0)
        apercu_layout.setSpacing(0)
        
        label_apercu = QLabel("Aperçu des vidéos")
        label_apercu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_apercu.setStyleSheet("font-size: 12px; font-weight: bold; padding: 4px; border-bottom: 2px solid white; background-color: white; color: black;")
        apercu_layout.addWidget(label_apercu)
        
        thumbnails_widget = QWidget()
        thumbnails_layout = QGridLayout()
        thumbnails_layout.setSpacing(6)
        thumbnails_layout.setContentsMargins(8, 8, 8, 8) 
        
        self.thumbnails = []
        self.thumbnail_labels = [] 
        
        thumbnail_min_width = 300 
        thumbnail_min_height = int(thumbnail_min_width / 1.87)
        thumbnail_max_width = 550 
        thumbnail_max_height = int(thumbnail_max_width / 1.87)

        idx_counter = 1
        for row in range(2):
            for col in range(3):
                thumb = AnimatedThumbnailLabel() 
                thumb.setMinimumSize(thumbnail_min_width, thumbnail_min_height)
                thumb.setMaximumSize(thumbnail_max_width, thumbnail_max_height)
                thumb.setSizePolicy(
                    QSizePolicy.Policy.Expanding, 
                    QSizePolicy.Policy.Expanding
                )
                self.thumbnails.append(thumb) 

                label = QLabel(f"Angle de vue n°{idx_counter}")
                label.setStyleSheet("color: #aaa; font-size: 10px; font-weight: bold;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.thumbnail_labels.append(label) 

                item_layout = QVBoxLayout()
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(4) 
                
                item_layout.addStretch() 
                item_layout.addWidget(thumb, 1) 
                item_layout.addWidget(label, 0) 
                item_layout.addStretch() 
                
                item_widget = QWidget()
                item_widget.setStyleSheet("background-color: transparent; border: none;")
                item_widget.setLayout(item_layout)
                
                thumbnails_layout.addWidget(item_widget, row, col, Qt.AlignmentFlag.AlignCenter)
                
                idx_counter += 1

        for i in range(2):
            thumbnails_layout.setRowStretch(i, 1)
        for i in range(3):
            thumbnails_layout.setColumnStretch(i, 1)
        
        thumbnails_widget.setLayout(thumbnails_layout)
        
        apercu_layout.addWidget(thumbnails_widget, 1) 
        
        apercu_container.setLayout(apercu_layout)
        
        
        # MÉTADONNÉES
        meta_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Métadonnées communes (lecture seule toujours)
        meta_communes_widget = self.create_metadata_section("Métadonnées communes", readonly=True, type_meta="communes")
        meta_splitter.addWidget(meta_communes_widget)
        
        # Métadonnées propres (lecture seule par défaut, éditable avec bouton)
        meta_propres_widget = self.create_metadata_section("Métadonnées propres", readonly=True, type_meta="propres")
        meta_splitter.addWidget(meta_propres_widget)
        
        meta_splitter.setStretchFactor(0, 1)
        meta_splitter.setStretchFactor(1, 1)

        
        layout.addWidget(apercu_container, stretch=2) 
        layout.addWidget(meta_splitter, stretch=1)
        
        panel.setLayout(layout)
        return panel
    
    def create_metadata_section(self, title, readonly=True, type_meta="communes"):
        container = QFrame()
        container.setObjectName("metadata_section")
        container.setStyleSheet("#metadata_section { background-color: black; border: 2px solid white; }")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        label_titre = QLabel(title)
        label_titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titre.setStyleSheet("color: black; font-size: 11px; font-weight: bold; padding: 4px; border-bottom: 2px solid white; background-color: white;")
        layout.addWidget(label_titre)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: black;")
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(6, 6, 6, 6)
        
        # Structure dynamique pour les deux types
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(3)
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: black; }")
        content_layout.addWidget(scroll_area)
        
        if type_meta == "communes":
            self.meta_communes_scroll_layout = scroll_layout
            self.meta_communes_fields = {}
            self.meta_communes_widgets = {}

            btn_style_sheet = "QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); } QPushButton:disabled { color: #555; border-color: #555; }"
            
            btn_modifier_communes = QPushButton("Modifier")
            btn_modifier_communes.setFixedSize(90, 26)
            btn_modifier_communes.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier_communes.setStyleSheet(btn_style_sheet)
            btn_modifier_communes.clicked.connect(self.on_modifier_metadata_communes)
            btn_modifier_communes.setEnabled(False)
            self.btn_modifier_communes = btn_modifier_communes

            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(btn_modifier_communes)
            btn_layout.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_layout)

        else:
            self.meta_propres_scroll_layout = scroll_layout
            self.meta_propres_fields = {}
            self.meta_propres_widgets = {}
            
            btn_style_sheet = "QPushButton { background-color: transparent; color: white; border: 2px solid white; border-radius: 4px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.1); } QPushButton:disabled { color: #555; border-color: #555; }"
            
            btn_precalculer = QPushButton("Pré-calculer")
            btn_precalculer.setFixedSize(90, 26)
            btn_precalculer.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_precalculer.setStyleSheet(btn_style_sheet)
            btn_precalculer.clicked.connect(self.on_precalculer_metadata)
            btn_precalculer.setEnabled(False)
            self.btn_precalculer_propres = btn_precalculer
            
            btn_modifier = QPushButton("Modifier")
            btn_modifier.setFixedSize(90, 26)
            btn_modifier.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_modifier.setStyleSheet(btn_style_sheet)
            btn_modifier.clicked.connect(self.on_modifier_metadata_propres)
            btn_modifier.setEnabled(False) 
            self.btn_modifier_propres = btn_modifier
            
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(btn_precalculer)
            btn_layout.addWidget(btn_modifier)
            btn_layout.setContentsMargins(0, 4, 0, 4)
            content_layout.addLayout(btn_layout)
        
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget)
        container.setLayout(layout)
        
        return container
    
    def create_metadata_row(self, key, readonly=True):
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(3, 2, 3, 2)
        row_layout.setSpacing(6)
        
        label = QLabel(f"{key}:")
        label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")
        label.setFixedWidth(110) 
        row_layout.addWidget(label)
        
        value_widget = QLineEdit()
        value_widget.setReadOnly(readonly)
        value_widget.setStyleSheet("color: white; padding: 3px; background-color: #1a1a1a; border: 1px solid #555; font-size: 10px;")
        
        row_layout.addWidget(value_widget)
        row_widget.setLayout(row_layout)
        
        return {'container': row_widget, 'widget': value_widget}
    
    # --- NOUVELLE MÉTHODE: Remplir les communes dynamiquement ---
    def remplir_metadonnees_communes(self, metadata_communes: dict):
        self.vider_layout(self.meta_communes_scroll_layout)
        self.meta_communes_fields.clear()
        self.meta_communes_widgets.clear()
        
        # Traduction des clés
        KEY_LABELS = {
            'system_camera': 'Caméra',
            'system_model': 'Modèle',
            'system_system': 'Système',
            'system_version': 'Version',
            'campaign_zoneDict_campaign': 'Campagne',
            'campaign_zoneDict_zone': 'Zone',
            'campaign_zoneDict_locality': 'Localité',
            'campaign_zoneDict_protection': 'Protection',
            'campaign_dateDict_date': 'Date',
            'campaign_deploiementDict_boat': 'Bateau',
            'campaign_deploiementDict_pilot': 'Pilote',
            'campaign_deploiementDict_crew': 'Équipage',
            'campaign_deploiementDict_partners': 'Partenaires'
        }

        sections = {}
        for key, value in metadata_communes.items():
            if '_' in key:
                section_name = key.split('_')[0]
                if section_name not in sections: sections[section_name] = {}
                sections[section_name][key] = value

        ordered_sections = ['system', 'campaign']
        
        for section_name in ordered_sections:
            if section_name not in sections: continue
            
            section_label = QLabel(f"{section_name.upper()}")
            section_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; padding: 5px 0px 2px 0px;")
            self.meta_communes_scroll_layout.addWidget(section_label)
            
            for full_key, value in sections[section_name].items():
                display_label = KEY_LABELS.get(full_key, full_key)
                row = self.create_metadata_row(display_label, readonly=True)
                row['widget'].setText(str(value))
                self.meta_communes_fields[full_key] = row['widget']
                self.meta_communes_widgets[full_key] = row['container']
                self.meta_communes_scroll_layout.addWidget(row['container'])

    def remplir_metadonnees_propres(self, metadata_propres: dict):
        """Remplit dynamiquement la section des métadonnées propres"""
        
        KEY_LABELS = {
            # GPS
            'latitude': 'Latitude (°)',
            'longitude': 'Longitude (°)',
            'site': 'Site',
            # Météo Air
            'tempAir': 'Temp. Air (°C)',
            'wind': 'Vent (km/h)',
            'sky': 'Ciel',
            'atmPress': 'Pression (hPa)',
            'direction': 'Dir. Vent',
            # Météo Mer
            'seaState': 'État Mer',
            'swell': 'Houle (m)',
            # Astro
            'coefficient': 'Coeff. Marée',
            'moon': 'Phase Lune',
            'tide': 'Marée',
            # CTD
            'depth': 'Prof. (m)',
            'salinity': 'Salinité (PSU)',
            'temperature': 'Temp. Eau (°C)',
            # Heure
            'HMSOS': 'Heure Début',
            'hour': 'Heure (h)',
            'minute': 'Minute (m)',
            'second': 'Seconde (s)',
            'ymdOS': 'Date (YMD)',
            # Station
            'codestation': 'Code Station',
            'increment': 'Incrément',
            # Analyse
            'exploitability': 'Exploitabilité',
            'fauna': 'Faune',
            'habitat': 'Habitat',
            'visibility': 'Visibilité'
        }
        
        self.vider_layout(self.meta_propres_scroll_layout)
        self.meta_propres_fields.clear()
        self.meta_propres_widgets.clear()
        
        sections = {}
        for full_key, value in metadata_propres.items():
            if full_key.startswith('campaign_'):
                continue
            
            if '_' in full_key:
                section_name, field_name = full_key.split('_', 1)
                
                if section_name not in sections:
                    sections[section_name] = {}
                sections[section_name][field_name] = (full_key, value)
            else:
                if 'general' not in sections:
                    sections['general'] = {}
                sections['general'][full_key] = (full_key, value)

        ordered_sections = ['stationDict', 'hourDict', 'gpsDict', 'meteoAirDict', 'meteoMerDict', 'astroDict', 'ctdDict', 'analyseDict', 'general']

        for section_name in ordered_sections:
            if section_name not in sections:
                continue
            
            fields = sections[section_name]
            if not fields:
                continue
                
            section_label = QLabel(f"{section_name.replace('Dict', '').upper()}")
            section_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; padding: 5px 0px 2px 0px;")
            self.meta_propres_scroll_layout.addWidget(section_label)
            
            sorted_fields = sorted(fields.items(), key=lambda item: item[0])

            for field_name, (full_key, value) in sorted_fields:
                
                display_label = KEY_LABELS.get(field_name, field_name)
                
                row = self.create_metadata_row(display_label, readonly=True)
                
                if value in ["None", "null", "N/A (API)"]:
                    row['widget'].setText("")
                else:
                    row['widget'].setText(str(value))
                
                self.meta_propres_fields[full_key] = row['widget']
                self.meta_propres_widgets[full_key] = row['container']
                self.meta_propres_scroll_layout.addWidget(row['container'])
    
    def vider_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self.vider_layout(child.layout())
    
    def connecter_signaux(self):
        if self.controller:
            self.table.itemSelectionChanged.connect(self.on_video_selected)
            self.controller.video_selectionnee.connect(self.afficher_video)
    
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
        
        if len(videos) > 0:
            self.table.selectRow(0)
            self.controller.selectionner_video(videos[0].nom)
    
    def lancer_extraction_previews(self, video_path, seek_info):
        if self.preview_extractor and self.preview_extractor.isRunning():
            self.preview_extractor.stop()
            self.preview_extractor.wait()
        
        for thumb in self.thumbnails:
            thumb.setText("🔄")
            thumb.setPixmap(QPixmap())
            thumb.set_video_preview_info(None, "00:00:00", 0)
            thumb.static_pixmap = None

        print(f"🎬 Lancement extraction previews...")
        
        self.preview_extractor = PreviewExtractorThread(video_path, seek_info)
        self.preview_extractor.thumbnail_ready.connect(self.afficher_miniature)
        self.preview_extractor.start()

    def afficher_miniature(self, index, pixmap):
        if index < len(self.thumbnails):
            if self.thumbnails[index].size().isValid():
                self.thumbnails[index].set_static_pixmap(pixmap)
            else:
                self.thumbnails[index].static_pixmap = pixmap
                self.thumbnails[index].setText("") 
            print(f"✅ Miniature statique {index+1} affichée")
    
    def on_video_selected(self):
        selected = self.table.selectedItems()
        if selected and self.controller:
            row = selected[0].row()
            nom_video = self.table.item(row, 0).text()
            self.controller.selectionner_video(nom_video)
    
    def afficher_video(self, video):
        self.video_selectionnee = video
        print(f"\n📹 Vidéo sélectionnée : {video.nom}")
        
        if self.controller:
            self.controller.charger_metadonnees_depuis_json(video)
            self.controller.charger_metadonnees_communes_depuis_json(video)
        
        self.remplir_metadonnees_communes(video.metadata_communes)
        self.remplir_metadonnees_propres(video.metadata_propres)
        
        if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
            self.btn_modifier_propres.setEnabled(True)
        if hasattr(self, "btn_precalculer_propres") and self.btn_precalculer_propres:
            self.btn_precalculer_propres.setEnabled(True)
        if hasattr(self, "btn_modifier_communes") and self.btn_modifier_communes:
            self.btn_modifier_communes.setEnabled(True)
        
        self.edit_propres = False
        self.edit_communes = False
        if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
            self.btn_modifier_propres.setText("Modifier")
        if hasattr(self, "btn_modifier_communes") and self.btn_modifier_communes:
            self.btn_modifier_communes.setText("Modifier")
        
        if self.controller:
            self.current_seek_info = self.controller.get_angle_seek_times(video.nom)
            try:
                self.lancer_extraction_previews(video.chemin, self.current_seek_info)
                for idx, thumb in enumerate(self.thumbnails):
                    if idx < len(self.current_seek_info):
                        seek_time_str, duration = self.current_seek_info[idx]
                        thumb.set_video_preview_info(video.chemin, seek_time_str, duration)
                    else:
                        thumb.set_video_preview_info(None, "00:00:00", 0)
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
    
    def on_modifier_metadata_propres(self):
        if not (self.video_selectionnee and self.controller): return
        if not self.edit_propres:
            for w in self.meta_propres_fields.values(): w.setReadOnly(False)
            self.edit_propres = True
            if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres: self.btn_modifier_propres.setText("OK")
            if hasattr(self, "btn_precalculer_propres") and self.btn_precalculer_propres: self.btn_precalculer_propres.setEnabled(False)
            return

        nouvelles_meta = {}
        for key, widget in self.meta_propres_fields.items():
            nouvelles_meta[key] = widget.text()
        
        succes, message = self.controller.modifier_metadonnees_propres(self.video_selectionnee.nom, nouvelles_meta)

        if succes:
            self.controller.show_success_dialog(self)
            for w in self.meta_propres_fields.values(): w.setReadOnly(True)
            self.edit_propres = False
            if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres: self.btn_modifier_propres.setText("Modifier")
            if hasattr(self, "btn_precalculer_propres") and self.btn_precalculer_propres: self.btn_precalculer_propres.setEnabled(True)
        else:
            QMessageBox.warning(self, "Erreur", message)
    
    def on_modifier_metadata_communes(self):
        """Gère la modification des métadonnées communes"""
        
        if not (self.video_selectionnee and self.controller):
            return

        if not self.edit_communes:
            # Activer l'édition
            for w in self.meta_communes_fields.values():
                w.setReadOnly(False)
            self.edit_communes = True
            if hasattr(self, "btn_modifier_communes") and self.btn_modifier_communes:
                self.btn_modifier_communes.setText("OK")
            # Désactiver le bouton des métadonnées propres pendant l'édition
            if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
                self.btn_modifier_propres.setEnabled(False)
            if hasattr(self, "btn_precalculer_propres") and self.btn_precalculer_propres:
                self.btn_precalculer_propres.setEnabled(False)
            return

        # Sauvegarder
        nouvelles_meta = {}
        for key, widget in self.meta_communes_fields.items():
            nouvelles_meta[key] = widget.text()
        
        succes, message = self.controller.modifier_metadonnees_communes(self.video_selectionnee.nom, nouvelles_meta)

        if succes:
            self.controller.show_success_dialog(self)
            
            # Repasser en lecture seule
            for w in self.meta_communes_fields.values():
                w.setReadOnly(True)
            self.edit_communes = False
            if hasattr(self, "btn_modifier_communes") and self.btn_modifier_communes:
                self.btn_modifier_communes.setText("Modifier")
            
            # Réactiver les boutons des métadonnées propres
            if hasattr(self, "btn_modifier_propres") and self.btn_modifier_propres:
                self.btn_modifier_propres.setEnabled(True)
            if hasattr(self, "btn_precalculer_propres") and self.btn_precalculer_propres:
                self.btn_precalculer_propres.setEnabled(True)
        else:
            QMessageBox.warning(self, "Erreur", message)

    def on_precalculer_metadata(self):
        if not (self.video_selectionnee and self.controller): return
        self.btn_precalculer_propres.setEnabled(False)
        self.btn_modifier_propres.setEnabled(False)
        self.btn_precalculer_propres.setText("Calcul...")
        QApplication.processEvents() 
        try:
            success = self.controller.precalculer_metadonnees_externes(self.video_selectionnee.nom)
            if success: QMessageBox.information(self, "Succès", "Les métadonnées externes ont été récupérées et sauvegardées.")
            else: QMessageBox.warning(self, "Échec", "Impossible de récupérer les métadonnées externes. Vérifiez la console pour les erreurs.")
        except Exception as e: QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")
        self.btn_precalculer_propres.setText("Pré-calculer")
        self.controller.selectionner_video(self.video_selectionnee.nom)

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
